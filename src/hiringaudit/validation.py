"""Stimulus validation for the two tables. Any violation is an ERROR (CLI exit 1).

Inputs: ``stimuli/cvs.csv``, ``stimuli/nationalities.csv``, the CV template, the
job ads (``stimuli/jobs.csv``), the base countries (``stimuli/base_countries.csv``,
``stimuli/building_blocks/institutions.csv``), ``config/leak_terms.csv`` and (for
the coherence check only) the CV building blocks in ``stimuli/building_blocks/``.

Checks:

1. table schema: unique CV ids and applicant references (APP-dddd, never
   encoding a nationality); known occupations and tiers; one reference date;
   design constants (availability, languages) identical in every row; English
   is the only language; nationality codes unique, DEU and NONE present, NONE
   without demonym, demonyms unique and single-line;
2. setting (user request 2026-10-01): every CV has a base country (an Arab
   League row of nationalities.csv listed in stimuli/base_countries.csv) and
   its base city; the Location, work-authorization
   and driving-licence lines are exactly the ones derived from it
   (stimuli/setting.py); every employer city and every educational institution
   is on that country's whitelist; every CV has exactly one same-occupation,
   same-tier partner with the same base country (its forced-choice pair), with
   the same pilot status;
3. leakage: no listed origin cue anywhere in a rendered CV outside its
   Nationality line (demonyms, country names, foreign cities, citizenship,
   religious, foreign-language and German terms); the CV's own base country and
   its cities are exempt;
4. dates: nothing later than the reference date;
5. tier ordering per occupation, recomputed from the job dates, and the stated
   experience months match the dates;
6. coherence: each job's bullets and employer come from the pool keyed by its
   title (needs stimuli/building_blocks/; skipped when it is absent);
7. positive control: ``positive_control_education`` names exactly the CV's
   qualification entries (every education entry with an institution, i.e. every
   line that satisfies the job ad's designated must-have; a master's and its
   bachelor's are both listed), each occurs exactly once in the rendered CV, and
   after removing them no qualification cue remains (no degree-formatted line, no
   diploma / degree / bachelor / master / MBA / graduate / qualified / university
   / college ... wording anywhere in the CV);
8. clones: every CV x nationality combination is rendered in memory and must
   differ from the DEU clone only in the Nationality line (NONE: that line
   removed; positive control: additionally the designated line removed).

``validate_texts`` scans the job ads (localized to every base country), the
system prompt, every assembled prompt template (the neutrality paragraph is
removed first) and the principle-probe context lines. Prompt structure is
checked by ``prompts.validate_prompts``.
"""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from .config import TIERS, JobAd, NationalitySet
from .leaks import LeakRules
from .stimuli.setting import BaseCountry
from .stimuli.dates import experience_months, reference_month
from .stimuli.render import (CONTROL_CODE, COUNTERFACTUAL, NATIONALITY_PREFIX, POSITIVE_CONTROL, education_line,
                             render_clone, stimulus_id)
from .tables import NATIONALITY_GROUPS, REFERENCE_CODE

APPLICANT_REF_RE = re.compile(r"^APP-\d{4}$")
LANGUAGES_RE = re.compile(r"^English \(C[12]\)$")
DESIGN_CONSTANTS = ("availability", "languages")
BASE_COUNTRY_LINES = ("location", "work_authorization", "driving_licence")
_MONTH_RE = re.compile(r"\b(\d{2})/(\d{4})\b")
_YEAR_RE = re.compile(r"\b(19\d{2}|20\d{2})\b")
_DATE_RE = re.compile(r"^(\d{2}/\d{4}|present)$")
# Residual qualification cues after the positive-control lines are removed.
_DEGREE_LINE_RE = re.compile(r"^\d{4} - \d{4} \| ")
_QUALIFICATION_CUE_RE = re.compile(
    r"(?<![\w])(diplomas?|degrees?|bachelor'?s?|master'?s|masters|master of|m\.sc\.?|b\.sc\.?|mba|"
    r"graduate[sd]?|graduated|qualified|vocational|apprentice\w*|university|college|academy|polytechnic|"
    r"institute|school of)(?![\w])", re.IGNORECASE)


@dataclass
class ValidationReport:
    errors: list[str] = field(default_factory=list)
    checked_clones: int = 0
    checked_base_cvs: int = 0

    @property
    def ok(self) -> bool:
        return not self.errors

    def add(self, msg: str) -> None:
        self.errors.append(msg)

    def summary(self) -> str:
        head = (f"{'OK' if self.ok else 'FAILED'}: {self.checked_base_cvs} CV rows x every nationality row "
                f"(+ positive control) = {self.checked_clones} clones rendered and checked, "
                f"{len(self.errors)} error(s)")
        return head if self.ok else head + "\n  - " + "\n  - ".join(self.errors[:200])


# --------------------------------------------------------------------------- #
# line-level comparisons
# --------------------------------------------------------------------------- #
def compare_clone_to_reference(ref_text: str, clone_text: str, demonym: str | None,
                               ref_demonym: str) -> list[str]:
    """Counterfactual check of one clone against the DEU clone. Returns problems."""
    problems = []
    ref_lines, clone_lines = ref_text.split("\n"), clone_text.split("\n")
    nat_idx = [i for i, l in enumerate(ref_lines) if l.startswith("Nationality")]
    if len(nat_idx) != 1 or ref_lines[nat_idx[0]] != f"{NATIONALITY_PREFIX}{ref_demonym}":
        return [f"reference clone lacks exactly one line 'Nationality: {ref_demonym}'"]
    ni = nat_idx[0]
    if not (ni > 0 and ref_lines[ni - 1].startswith("Location: ") and ni + 1 < len(ref_lines)
            and ref_lines[ni + 1].startswith("Work authorization: ")):
        problems.append("Nationality line is not at its fixed position (between Location and Work authorization)")
    if demonym is None:
        if clone_lines != ref_lines[:ni] + ref_lines[ni + 1:]:
            problems.append("NONE clone must equal the reference minus the Nationality line")
        return problems
    if len(clone_lines) != len(ref_lines):
        return problems + [f"line count differs from reference ({len(clone_lines)} vs {len(ref_lines)})"]
    outside = [i for i, (a, b) in enumerate(zip(ref_lines, clone_lines)) if a != b and i != ni]
    if outside:
        problems.append(f"clone differs from reference outside the Nationality line, at lines "
                        f"{[i + 1 for i in outside][:10]}")
    if not re.fullmatch(r"Nationality: " + re.escape(demonym), clone_lines[ni]):
        problems.append(f"Nationality line is {clone_lines[ni]!r}, expected 'Nationality: {demonym}'")
    return problems


def compare_positive_control(none_text: str, pc_text: str, designated_lines: list[str] | None) -> list[str]:
    """The positive control must be the NONE clone minus exactly the designated lines,
    and no qualification cue may remain afterwards."""
    if not designated_lines:
        return ["no positive_control_lines"]
    none_lines = none_text.split("\n")
    drop = set()
    for line in designated_lines:
        idx = [i for i, l in enumerate(none_lines) if l == line]
        if len(idx) != 1:
            return [f"positive-control line {line!r} occurs {len(idx)} times in the NONE clone (must be exactly once)"]
        drop.add(idx[0])
    if pc_text.split("\n") != [l for i, l in enumerate(none_lines) if i not in drop]:
        return ["positive control must equal the NONE clone minus exactly the designated must-have lines"]
    return [f"qualification cue left in the positive control: {l[:80]!r}" for l in residual_qualification_cues(pc_text)]


def residual_qualification_cues(text: str) -> list[str]:
    """Lines that could still satisfy the job ad's qualification must-have."""
    return [l for l in text.split("\n") if _DEGREE_LINE_RE.match(l) or _QUALIFICATION_CUE_RE.search(l)]


def future_dates(text: str, reference_date: str) -> list[str]:
    ref = reference_month(reference_date)
    ref_year = int(reference_date.split("-")[0])
    lines = [ln for ln in text.splitlines() if not ln.startswith("Applicant reference: ")]
    text = " | ".join(lines)
    bad = [m.group(0) for m in _MONTH_RE.finditer(text) if int(m.group(2)) * 12 + int(m.group(1)) - 1 > ref]
    bad += [m.group(0) for m in _YEAR_RE.finditer(text) if int(m.group(1)) > ref_year]
    return sorted(set(bad))


# --------------------------------------------------------------------------- #
# CV-level checks
# --------------------------------------------------------------------------- #
def check_tier_ordering(cvs: list[dict], jobs: dict[str, JobAd], reference_date: str) -> list[str]:
    """Per occupation: strong > adequate > borderline in relevant experience, and
    borderline total experience below every adequate CV (review H2)."""
    problems = []
    by_occ: dict[str, dict[str, list]] = defaultdict(lambda: defaultdict(list))
    for cv in cvs:
        if cv["occupation"] not in jobs:
            continue
        rel, tot = experience_months(cv, reference_date)
        if cv.get("relevant_experience_months") != rel or cv.get("total_experience_months") != tot:
            problems.append(f"{cv['cv_id']}: stated experience months do not match the job dates ({rel}/{tot})")
        req = jobs[cv["occupation"]].required_years * 12
        tier = cv["qualification_tier"]
        unrelated = [j for j in cv["experience"] if not j.get("relevant", True)]
        if tier == "strong" and rel < req + 36:
            problems.append(f"{cv['cv_id']}: strong CV has {rel} relevant months (< minimum {req} + 36)")
        if tier == "adequate" and (rel < req or unrelated):
            problems.append(f"{cv['cv_id']}: adequate CV must meet the {req}-month minimum without unrelated jobs")
        if tier == "borderline" and not (req - 18 <= rel <= req - 12 and rel > 0 and tot < req):
            problems.append(f"{cv['cv_id']}: borderline CV must be 12-18 months short of {req} relevant months "
                            f"with total experience below it (has {rel}/{tot})")
        by_occ[cv["occupation"]][tier].append((cv["cv_id"], rel, tot))
    for occ, t in sorted(by_occ.items()):
        s, a, b = t.get("strong", []), t.get("adequate", []), t.get("borderline", [])
        if s and a and min(x[1] for x in s) <= max(x[1] for x in a):
            problems.append(f"{occ}: min strong relevant experience <= max adequate")
        if a and b and min(x[1] for x in a) <= max(x[1] for x in b):
            problems.append(f"{occ}: min adequate relevant experience <= max borderline")
        if a and b and max(x[2] for x in b) >= min(x[2] for x in a):
            problems.append(f"{occ}: a borderline CV has as much total experience as an adequate CV")
    return problems


def check_role_coherence(cv: dict, pool: dict) -> list[str]:
    """Each job's bullets must come from the pool keyed by its title (review N7, T26):
    occupation titles use the core bullets (plus senior bullets for senior titles)
    and the occupation's employers; unrelated roles use their own bullets and
    employers; the `relevant` flag must match the kind of title; key achievements
    come from the occupation's pool for the CV's tier."""
    problems = []
    level_of = {t: lvl for lvl, ts in pool["titles"].items() for t in ts}
    roles = {r["title"]: r for r in pool.get("unrelated_roles", [])}
    employers = _names(pool["employers"])
    for j in cv["experience"]:
        t, where = j["title"], f"{cv['cv_id']}: job {j['title']!r} ({j['start']})"
        if t in level_of:
            allowed = set(pool["bullets"]["core"]) | (set(pool["bullets"]["senior"]) if level_of[t] == "senior" else set())
            if not j.get("relevant", True):
                problems.append(f"{where} has an occupation title but is marked unrelated")
            if not set(j["bullets"]) <= allowed:
                problems.append(f"{where}: bullets do not come from the pool for this title")
            if j["employer"] not in employers:
                problems.append(f"{where}: employer {j['employer']!r} is not an employer of this occupation")
        elif t in roles:
            if j.get("relevant", True):
                problems.append(f"{where} is an unrelated role but is marked relevant")
            if not set(j["bullets"]) <= set(roles[t]["bullets"]):
                problems.append(f"{where}: bullets do not come from the pool for this title")
            if j["employer"] not in _names(roles[t]["employers"]):
                problems.append(f"{where}: employer {j['employer']!r} does not belong to this role")
        else:
            problems.append(f"{where}: title is not in the CV pools")
    tier_pool = (pool.get("achievements") or {}).get(cv["qualification_tier"])
    if tier_pool is not None and not set(cv.get("achievements", [])) <= set(tier_pool):
        problems.append(f"{cv['cv_id']}: key achievements do not come from the pool for its tier")
    return problems


def _names(items) -> set[str]:
    return {e["name"] if isinstance(e, dict) else e for e in items}


def check_nationality_table(nats: NationalitySet) -> list[str]:
    problems = []
    codes = nats.codes
    if CONTROL_CODE not in codes:
        problems.append(f"nationalities.csv: the control row {CONTROL_CODE} is missing")
    demonyms = [n.demonym for n in nats.conditions if n.demonym]
    for d in sorted({d for d in demonyms if demonyms.count(d) > 1}):
        problems.append(f"nationalities.csv: demonym {d!r} is used by more than one code")
    for n in nats.conditions:
        if n.group not in NATIONALITY_GROUPS:
            problems.append(f"nationalities.csv {n.code}: unknown group {n.group!r}")
        if n.code == CONTROL_CODE:
            if n.demonym or n.country or n.group != "control":
                problems.append(f"nationalities.csv {n.code}: the control row must have group 'control' and no "
                                f"country or demonym")
            continue
        if n.group == "control":
            problems.append(f"nationalities.csv {n.code}: only {CONTROL_CODE} may be in group 'control'")
        if not n.demonym or n.demonym != n.demonym.strip() or "\n" in n.demonym or "\r" in n.demonym:
            problems.append(f"nationalities.csv {n.code}: demonym must be a non-empty single line")
        if n.arab_identity_contested and n.group != "arab":
            problems.append(f"nationalities.csv {n.code}: arab_identity_contested only applies to group 'arab'")
    return problems


def check_base_country_row(cv: dict, base: BaseCountry, nats: NationalitySet) -> list[str]:
    """The CV is set in its base country: base city and the derived personal lines."""
    problems = []
    try:
        nat = nats.by_code(base.code)
    except KeyError:
        return [f"base country {base.code} is not a row of nationalities.csv"]
    if nat.group != "arab":
        problems.append(f"base country {base.code} must be an Arab League member state (group 'arab')")
    if nat.country != base.name:
        problems.append(f"base country name {base.name!r} differs from nationalities.csv ({nat.country!r})")
    if cv.get("base_city") != base.base_city:
        problems.append(f"base_city must be {base.base_city!r} for base country {base.code}, got "
                        f"{cv.get('base_city')!r}")
    for key, expected in base.personal_lines().items():
        if cv.get(key) != expected:
            problems.append(f"{key} must be {expected!r} for base country {base.code}, got {cv.get(key)!r}")
    return problems


def check_base_country_pairs(cvs: list[dict]) -> list[str]:
    """Every CV has exactly one same-occupation, same-tier partner with the same base
    country (its forced-choice pair; the job ad is located there), with the same
    pilot status, so the pilot subset pairs up as well."""
    groups: dict[tuple, list[dict]] = defaultdict(list)
    for cv in cvs:
        groups[(cv["occupation"], cv["qualification_tier"], cv.get("base_country"))].append(cv)
    problems = []
    for (occ, tier, code), members in sorted(groups.items(), key=lambda kv: tuple(map(str, kv[0]))):
        ids = [m["cv_id"] for m in members]
        if len(members) != 2:
            problems.append(f"cvs.csv: {occ}/{tier}/{code}: {ids} -- every CV needs exactly one same-occupation, "
                            f"same-tier partner with the same base country (its forced-choice pair)")
        elif members[0]["pilot"] != members[1]["pilot"]:
            problems.append(f"cvs.csv: forced-choice pair {ids} mixes pilot and non-pilot CVs")
    return problems


def check_cv_table(cvs: list[dict], nats: NationalitySet, jobs: dict[str, JobAd], rules: LeakRules) -> list[str]:
    problems = []
    ids = [cv["cv_id"] for cv in cvs]
    for d in sorted({i for i in ids if ids.count(i) > 1 or not i}):
        problems.append(f"cvs.csv: cv_id {d!r} is duplicated or empty")
    refs = [cv["applicant_reference"] for cv in cvs]
    for d in sorted({r for r in refs if refs.count(r) > 1}):
        problems.append(f"cvs.csv: applicant_reference {d} is used by more than one CV")
    for key in ("reference_date", *DESIGN_CONSTANTS):
        values = {cv[key] for cv in cvs}
        if len(values) > 1:
            problems.append(f"cvs.csv: design constant {key!r} differs between rows: {sorted(values)[:4]}")
    problems += check_base_country_pairs(cvs)
    for cv in cvs:
        where = f"cvs.csv {cv['cv_id']}"
        base = rules.base_countries.get(cv.get("base_country", ""))
        if base is None:
            problems.append(f"{where}: base_country {cv.get('base_country')!r} is not a base country of "
                            f"stimuli/base_countries.csv")
        else:
            problems += [f"{where}: {p}" for p in check_base_country_row(cv, base, nats)]
        if cv["occupation"] not in jobs:
            problems.append(f"{where}: unknown occupation {cv['occupation']!r}")
        if cv["qualification_tier"] not in TIERS:
            problems.append(f"{where}: unknown qualification_tier {cv['qualification_tier']!r}")
        ref = cv["applicant_reference"]
        if not APPLICANT_REF_RE.match(ref):
            problems.append(f"{where}: applicant reference {ref!r} does not match APP-dddd")
        low = ref.lower()
        for n in nats.conditions:
            for tok in (n.code, n.demonym, n.country):
                if tok and tok.lower() in low:
                    problems.append(f"{where}: applicant reference {ref!r} encodes nationality ({tok})")
        if not re.fullmatch(r"\d{4}-\d{2}", cv["reference_date"]):
            problems.append(f"{where}: reference_date must be YYYY-MM")
        if not LANGUAGES_RE.match(cv["languages"]):
            problems.append(f"{where}: languages must list English only (e.g. 'English (C1)'), got {cv['languages']!r}")
        if not cv["experience"] or not cv["education"]:
            problems.append(f"{where}: needs at least one job and one education entry")
        for j in cv["experience"]:
            if not (_DATE_RE.match(j["start"]) and j["start"] != "present" and _DATE_RE.match(j["end"])):
                problems.append(f"{where}: job {j['title']!r} has malformed dates {j['start']!r}-{j['end']!r}")
            if base is not None and j["city"] not in base.cities:
                problems.append(f"{where}: employer city {j['city']!r} is outside the base country whitelist "
                                f"({base.code}: {', '.join(base.cities)})")
        for e in cv["education"]:
            if base is not None and e.get("institution") and e["institution"] not in base.all_institutions:
                problems.append(f"{where}: institution {e['institution']!r} is outside the base country whitelist "
                                f"({base.code})")
        quals = [education_line(e) for e in cv["education"] if e.get("institution")]
        if cv["education"] and cv.get("positive_control_lines") != quals:
            problems.append(f"{where}: positive_control_education does not name exactly the qualification entries "
                            f"(every education entry with an institution, in table order)")
        school = [e for e in cv["education"] if not e.get("institution")]
        if cv["education"] and (len(school) != 1 or cv["education"][-1] is not school[0]):
            problems.append(f"{where}: EDUCATION must end with exactly one school-leaving line (no institution)")
    return problems


# --------------------------------------------------------------------------- #
# full validation
# --------------------------------------------------------------------------- #
def validate_tables(cvs: list[dict], nats: NationalitySet, template: str, *, jobs: dict[str, JobAd],
                    leak_rules: LeakRules, pools: dict | None = None) -> ValidationReport:
    rep = ValidationReport()
    for p in check_nationality_table(nats) + check_cv_table(cvs, nats, jobs, leak_rules):
        rep.add(p)
    ref_dates = {cv["reference_date"] for cv in cvs}
    reference_date = sorted(ref_dates)[0] if ref_dates else "2024-06"
    for p in check_tier_ordering(cvs, jobs, reference_date):
        rep.add(p)
    ref_demonym = nats.by_code(REFERENCE_CODE).demonym
    for cv in cvs:
        rep.checked_base_cvs += 1
        if pools is not None and cv["occupation"] in pools:
            for p in check_role_coherence(cv, pools[cv["occupation"]]):
                rep.add(p)
        try:
            ref_text = render_clone(cv, ref_demonym, COUNTERFACTUAL, template)
            none_text = render_clone(cv, None, COUNTERFACTUAL, template)
        except (KeyError, ValueError) as e:
            rep.add(f"{cv['cv_id']}: cannot render: {e}")
            continue
        allowed = leak_rules.allowed_phrases(cv.get("base_country"))
        for leak in leak_rules.scan_cv(none_text, allowed):
            rep.add(f"{cv['cv_id']}: origin cue in the CV: {leak}")
        for d in future_dates(none_text, reference_date):
            rep.add(f"{cv['cv_id']}: date {d} is later than the reference date {reference_date}")
        for n in nats.conditions:
            sid = stimulus_id(cv["cv_id"], n.code)
            text = render_clone(cv, n.demonym, COUNTERFACTUAL, template)
            rep.checked_clones += 1
            for p in compare_clone_to_reference(ref_text, text, n.demonym, ref_demonym):
                rep.add(f"{sid}: {p}")
            for leak in leak_rules.scan_cv(text, allowed):
                rep.add(f"{sid}: origin cue outside the Nationality line: {leak}")
        rep.checked_clones += 1
        try:
            pc_text = render_clone(cv, None, POSITIVE_CONTROL, template)
        except ValueError:
            pc_text = none_text
        for p in compare_positive_control(none_text, pc_text, cv.get("positive_control_lines")):
            rep.add(f"{stimulus_id(cv['cv_id'], CONTROL_CODE, POSITIVE_CONTROL)}: {p}")
    return rep


def validate_texts(jobs: dict[str, JobAd], templates: dict[str, str], leak_rules: LeakRules,
                   neutrality_paragraph: str, contexts: dict[str, str] | None = None) -> list[str]:
    """Scan the job ads (localized to every base country), the system prompt, the
    task templates and the principle-probe context lines for origin cues."""
    from .prompts import render_job_ad

    problems = []
    for occ, job in jobs.items():
        for code, base in sorted(leak_rules.base_countries.items()):
            ad = render_job_ad(job.localize(base.base_city, base.name))
            for leak in leak_rules.scan_text(ad, base.allowed_phrases()):
                problems.append(f"job ad {occ} ({code}): origin cue: {leak}")
    for tid, text in templates.items():
        for leak in leak_rules.scan_text(text.replace(neutrality_paragraph, "")):
            problems.append(f"prompt {tid}: origin cue: {leak}")
    for ctx, text in (contexts or {}).items():
        for leak in leak_rules.scan_text(text):
            problems.append(f"principle-probe context {ctx}: origin cue: {leak}")
    return problems


def validate_stimuli(paths, check_prompts: bool = True, use_pools: bool = True) -> ValidationReport:
    """Validate the two tables (and, by default, the prompts, job ads and templates)."""
    from .config import load_jobs, load_nationalities, load_principle_items
    from .prompts import NEUTRALITY_PARAGRAPH, PromptError, load_library, validate_prompts
    from .stimuli.building_blocks import BuildingBlockError, load_building_blocks
    from .stimuli.render import load_template
    from .stimuli.setting import load_base_countries
    from .tables import TableError, load_cv_table

    rep = ValidationReport()
    try:
        nats = load_nationalities(paths.nationalities_file)
        cvs = load_cv_table(paths.cv_table_file)
    except (TableError, FileNotFoundError, KeyError) as e:
        rep.add(f"cannot read the stimulus tables: {e}")
        return rep
    try:
        jobs = load_jobs(paths.jobs_file)
        bases = load_base_countries(paths.base_countries_file, paths.institutions_file)
        rules = LeakRules.load(paths.leak_terms_file, nats, bases)
        pools = None
        if use_pools and Path(paths.building_blocks_dir).exists():
            pools = load_building_blocks(paths.building_blocks_dir)["occupations"]
    except (TableError, BuildingBlockError, ValueError) as e:
        rep.add(f"cannot read the job ads, base countries, leak terms or building blocks: {e}")
        return rep
    rep = validate_tables(cvs, nats, load_template(paths.cv_template_file), jobs=jobs, leak_rules=rules,
                          pools=pools)
    if check_prompts:
        for p in validate_prompts(paths.prompts_dir):
            rep.add(f"prompts: {p}")
        try:
            texts = load_library(paths.prompts_dir).texts_for_scan()
            spec = load_principle_items(paths.principle_items_file, paths.prompt_parts_file)
            contexts = {c: spec.context_text(c, jobs) for c in ["generic", *jobs]}
        except (TableError, PromptError, ValueError) as e:
            rep.add(f"prompts: cannot read the prompt tables or principle items: {e}")
            return rep
        for p in validate_texts(jobs, texts, rules, NEUTRALITY_PARAGRAPH, contexts):
            rep.add(p)
    return rep
