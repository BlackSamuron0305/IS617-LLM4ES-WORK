"""Build ``stimuli/cvs.csv``: compose genuinely different synthetic base CVs from
curated building blocks (``stimuli/building_blocks/*.csv``) with a fixed seed.

This is how the table was built (``python scripts/build_cv_table.py``). After the
build the TABLE is the source of truth; the experiment runtime never imports
this module or reads the pools.

Setting (user request 2026-10-01): every CV is set entirely in ONE Arab League
country, its base country (``stimuli/base_countries.csv``). The two CVs of a
forced-choice pair (same occupation, same tier; ``fc_pair`` in
``building_blocks/cv_slots.csv``) share their base country. The Location, work
authorization and driving-licence lines are derived from the base country
(``stimuli/setting.py``); the most recent employer is in the base city, earlier
employers in any city of the base country; the qualification is from a real
institution of the base country.

Qualification tier is built as a real difference relative to the job ad
(``required_years`` in stimuli/jobs.csv; rubric in stimuli/README.md):
years of relevant experience, number and seniority of roles, preferred skills,
level of the qualification, certificates and key achievements. A borderline CV
clearly misses one must-have (relevant experience 12-18 months below the
minimum); its earlier job is in a genuinely unrelated role and its total
experience stays below the minimum, hence below every adequate CV of the
occupation. Length (bullets per role, skills, certificates, achievements,
profile sentences) is fixed within a tier.

Bullets are drawn conditional on the job: relevant roles use the occupation's
core/senior bullets; each unrelated role has its own title, employers, bullets
and profile phrase, so a CV reads coherently.

Output: one table row per base CV. It contains NO nationality; the nationality
line is added only when a prompt is built. Each row records which rendered lines
satisfy the positive-control requirement (A7: every qualification line, e.g. a
master's and its preceding bachelor's) and, per job, whether the job counts as
relevant experience (not rendered).
"""

from __future__ import annotations

import random
from collections import Counter
from pathlib import Path
from typing import Any

from ..config import JobAd, load_jobs
from ..utils import derive_int
from .building_blocks import load_building_blocks
from .dates import fmt_month, format_duration, reference_month
from .setting import BaseCountry, load_base_countries

BUILDER_VERSION = 7

# Fixed per tier so that CV length is comparable within a tier.
SKILLS_PER_TIER = {"strong": 12, "adequate": 10, "borderline": 8}
ACHIEVEMENTS_PER_TIER = {"strong": 3, "adequate": 2, "borderline": 2}
CERTS_PER_TIER = {"strong": 3, "adequate": None, "borderline": 0}   # total; adequate = required + 1 optional
# bullets per relevant role level: (senior bullets, core bullets)
BULLETS = {"senior": (2, 3), "mid_recent": (0, 4), "mid": (0, 3), "junior": (0, 3)}
UNRELATED_BULLETS = 3


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def _key(item: Any) -> str:
    if isinstance(item, dict):
        return str(item.get("name") or item.get("degree") or item.get("title"))
    return str(item)


class Usage:
    """Usage counters that steer sampling towards variety.

    Items not yet used by another CV of the SAME tier are preferred (so the two
    CVs paired in a forced-choice trial look different), then items least used
    overall; remaining ties are broken by the seeded RNG.
    """

    def __init__(self) -> None:
        self.overall: Counter = Counter()
        self.by_tier: dict[str, Counter] = {}
        self.tier = ""

    def key(self, item: Any) -> tuple[int, int]:
        k = _key(item)
        return self.by_tier.setdefault(self.tier, Counter())[k], self.overall[k]

    def bump(self, item: Any) -> None:
        k = _key(item)
        self.overall[k] += 1
        self.by_tier.setdefault(self.tier, Counter())[k] += 1


def _pick(rng: random.Random, items: list, usage: Usage, k: int, exclude=()) -> list:
    """Pick ``k`` distinct items, preferring the least used (see :class:`Usage`)."""
    excluded = {_key(e) for e in exclude}
    cands = [i for i in items if _key(i) not in excluded]
    if k > len(cands):
        raise ValueError(f"pool too small: need {k}, have {len(cands)}")
    rng.shuffle(cands)
    cands.sort(key=usage.key)  # stable sort: the shuffle breaks ties
    chosen = cands[:k]
    for c in chosen:
        usage.bump(c)
    return chosen


# --------------------------------------------------------------------------- #
# tier rubric -> job segments
# --------------------------------------------------------------------------- #
def job_plan(tier: str, req_years: int, rng: random.Random) -> list[dict]:
    """Chronological job segments (oldest first): level and duration in months."""
    req = req_years * 12
    if tier == "strong":
        total = req + 12 * rng.randint(3, 6) + rng.randint(0, 5)
        while True:  # four roles: junior, mid, mid (most recent mid), senior; every mid role >= 12 months
            senior = 24 + rng.randint(0, 17)
            junior = 12 + rng.randint(0, 11)
            rest = total - senior - junior
            if rest >= 24:
                break
        mid1 = rng.randint(12, rest - 12)
        return [{"level": "junior", "months": junior}, {"level": "mid", "months": mid1},
                {"level": "mid_recent", "months": rest - mid1}, {"level": "senior", "months": senior}]
    if tier == "adequate":
        total = req + 12 * rng.randint(0, 1) + rng.randint(1, 8)
        junior = min(total - 12, 12 + rng.randint(0, 8))
        return [{"level": "junior", "months": junior}, {"level": "mid_recent", "months": total - junior}]
    if tier == "borderline":
        gap = rng.randint(12, 18)                  # months short of the minimum
        relevant = req - gap
        if relevant < 6:
            raise ValueError("required_years too small for a borderline CV (needs >= 2 years)")
        unrelated = rng.randint(6, gap - 1)        # keeps total experience below the minimum
        return [{"level": "unrelated", "months": unrelated}, {"level": "junior", "months": relevant}]
    raise ValueError(f"unknown tier {tier}")


def _title_level(level: str) -> str:
    return "mid" if level in ("mid", "mid_recent") else level


# --------------------------------------------------------------------------- #
# base-country allocation
# --------------------------------------------------------------------------- #
def base_country_of(pools: dict, occupation: str, base_countries: dict[str, BaseCountry]) -> dict[int, str]:
    """{position: base country code} for one occupation (positions of a pair share it)."""
    pairs = pools["fc_pairs"]
    alloc = pools["base_country_allocation"][occupation]
    tiers = pools["tier_sequence"]
    pilot = set(pools.get("pilot_positions", []))
    n = pools["n_per_occupation"]
    if len(alloc) != len(pairs):
        raise ValueError(f"{occupation}: base_country_allocation needs one country per fc pair")
    covered = sorted(p for pair in pairs for p in pair)
    if covered != list(range(1, n + 1)):
        raise ValueError(f"fc_pairs must cover positions 1..{n} exactly once, got {covered}")
    out = {}
    for (a, b), code in zip(pairs, alloc):
        if tiers[a - 1] != tiers[b - 1] or ((a in pilot) != (b in pilot)):
            raise ValueError(f"fc pair {a, b} must have one tier and one pilot status")
        if code not in base_countries:
            raise ValueError(f"{occupation}: base country {code} is not in stimuli/base_countries.csv")
        out[a] = out[b] = code
    return out


def check_allocation_balance(pools: dict) -> list[str]:
    """Design rule: 3 pairs per base country, each in a different occupation."""
    problems = []
    per_country: dict[str, list[str]] = {}
    for occ, codes in pools["base_country_allocation"].items():
        for code in codes:
            per_country.setdefault(code, []).append(occ)
    for code, occs in sorted(per_country.items()):
        if len(occs) != 3 or len(set(occs)) != 3:
            problems.append(f"base country {code}: {len(occs)} pairs in occupations {occs} (need 3 distinct)")
    return problems


# --------------------------------------------------------------------------- #
# one CV
# --------------------------------------------------------------------------- #
def generate_cv(*, occupation: str, position: int, tier: str, pilot: bool, applicant_reference: str,
                job: JobAd, pool: dict, base: BaseCountry, held_constant: dict, school: str,
                reference_date: str, rng: random.Random, usage: Usage, seed: int) -> dict:
    usage.tier = tier
    ref_year = int(reference_date.split("-")[0])
    present = reference_month(reference_date)
    plan = job_plan(tier, job.required_years, rng)

    # --- roles: title, employer, city and bullets drawn together ---
    used_employers: list = []
    used_bullets: list = []
    used_titles: list = []
    jobs_chrono = []
    unrelated_role = None
    for seg in plan:
        level = seg["level"]
        if level == "unrelated":
            unrelated_role = _pick(rng, pool["unrelated_roles"], usage, 1)[0]
            emp = _pick(rng, unrelated_role["employers"], usage, 1)[0]
            title = unrelated_role["title"]
            bullets = list(unrelated_role["bullets"])
            rng.shuffle(bullets)
            bullets = bullets[:UNRELATED_BULLETS]
        else:
            emp = _pick(rng, pool["employers"], usage, 1, exclude=used_employers)[0]
            title = _pick(rng, pool["titles"][_title_level(level)], usage, 1, exclude=used_titles)[0]
            used_titles.append(title)
            n_senior, n_core = BULLETS[level]
            bullets = []
            for kind, k in (("senior", n_senior), ("core", n_core)):
                if k:
                    chosen = _pick(rng, pool["bullets"][kind], usage, k, exclude=used_bullets)
                    used_bullets.extend(chosen)
                    bullets += chosen
        used_employers.append(emp)
        jobs_chrono.append({"level": level, "title": title, "employer": emp, "city": rng.choice(base.cities),
                            "months": seg["months"], "bullets": bullets, "relevant": level != "unrelated"})
    jobs_chrono[-1]["city"] = base.base_city      # the current job is in the city the applicant lives in

    # --- timeline, backwards from the reference date ---
    end = present
    for i, j in enumerate(reversed(jobs_chrono)):
        start = end - j["months"]
        j["start_idx"] = start
        j["end"] = "present" if i == 0 else fmt_month(end)
        j["start"] = fmt_month(start)
        end = start - rng.randint(1, 3)
    first_start = jobs_chrono[0]["start_idx"]
    relevant_months = sum(j["months"] for j in jobs_chrono if j["relevant"])
    total_months = sum(j["months"] for j in jobs_chrono)

    # --- education: the qualification (a master's with its preceding bachelor's),
    #     most recent first, then the school-leaving line; dates without gaps ---
    level = "advanced" if tier == "strong" else "relevant"
    qual = _pick(rng, pool["qualifications"][level], usage, 1)[0]

    def institution(kind: str) -> str:
        institutions = base.institutions.get(kind) or ()
        if not institutions:
            raise ValueError(f"base country {base.code} has no institution of kind {kind!r}")
        return _pick(rng, list(institutions), usage, 1)[0]

    q_end = (first_start - rng.randint(1, 4)) // 12
    q_start = q_end - qual["years"]
    education = [{"degree": qual["degree"], "institution": institution(qual["kind"]), "start": str(q_start),
                  "end": str(q_end)}]
    next_start = q_start
    if qual.get("bachelor"):                      # a master's follows a bachelor's in the same base country
        relevant = {q["degree"]: q for q in pool["qualifications"]["relevant"]}
        bach = relevant[_pick(rng, list(qual["bachelor"]), usage, 1)[0]]
        b_end = q_start - rng.randint(0, 1)
        b_start = b_end - bach["years"]
        education.append({"degree": bach["degree"], "institution": institution(bach["kind"]),
                          "start": str(b_start), "end": str(b_end)})
        next_start = b_start
    education.append({"degree": school, "institution": None, "start": None,
                      "end": str(next_start - rng.randint(0, 1))})

    # --- skills: required + preferred (tier) + neutral tools, fixed count per tier ---
    required = list(pool["skills"]["required"])
    n_nice = {"strong": rng.randint(4, 5), "adequate": rng.randint(1, 2), "borderline": 0}[tier]
    n_tools = SKILLS_PER_TIER[tier] - len(required) - n_nice
    skills = required + _pick(rng, pool["skills"]["nice"], usage, n_nice) + _pick(rng, pool["skills"]["tools"],
                                                                                  usage, n_tools)
    rng.shuffle(skills)

    # --- certifications (never dated after the reference year, never before a cert existed) ---
    first_rel = next(j for j in jobs_chrono if j["relevant"])
    lo = first_rel["start_idx"] // 12
    certs = [{"name": c["name"], "year": max(lo, int(c.get("since", lo)))}
             for c in pool["certifications"].get("required", [])]
    n_total = CERTS_PER_TIER[tier]
    n_opt = (n_total - len(certs)) if n_total is not None else 1
    for c in _pick(rng, pool["certifications"]["optional"], usage, max(0, n_opt)):
        certs.append({"name": c["name"], "year": rng.randint(max(lo, int(c.get("since", lo))), ref_year)})
    certs.sort(key=lambda c: (-(c["year"] or 0), c["name"]))

    # --- key achievements (tier pool) ---
    achievements = _pick(rng, pool["achievements"][tier], usage, ACHIEVEMENTS_PER_TIER[tier])

    # --- profile (mentions the unrelated role for borderline CVs) ---
    tpl = _pick(rng, pool["profiles"][tier], usage, 1)[0]
    profile = tpl.format(experience=format_duration(relevant_months),
                         unrelated=unrelated_role["as"] if unrelated_role else "")

    experience = [{"title": j["title"], "employer": j["employer"], "city": j["city"], "start": j["start"],
                   "end": j["end"], "bullets": j["bullets"], "relevant": j["relevant"]}
                  for j in reversed(jobs_chrono)]
    from .render import education_line  # local import avoids a cycle

    return {
        "cv_id": f"{pool['short']}_{position:02d}",
        "occupation": occupation,
        "qualification_tier": tier,
        "pilot": pilot,
        "base_country": base.code,
        "base_city": base.base_city,
        "applicant_reference": applicant_reference,
        "reference_date": reference_date,
        "relevant_experience_months": relevant_months,
        "total_experience_months": total_months,
        # A7: every education entry (and its rendered line) that satisfies the job ad's
        # positive-control requirement
        "positive_control_education": [f"edu{i + 1}" for i, e in enumerate(education) if e["institution"]],
        "positive_control_lines": [education_line(e) for e in education if e["institution"]],
        **base.personal_lines(),
        **{k: held_constant[k] for k in ("availability", "languages")},
        "profile": profile,
        "achievements": achievements,
        "experience": experience,
        "education": education,
        "skills": skills,
        "certifications": certs,
    }


# --------------------------------------------------------------------------- #
# all CVs
# --------------------------------------------------------------------------- #
def generate_base_cvs(pools: dict, jobs: dict[str, JobAd], seed: int, base_countries: dict[str, BaseCountry],
                      occupations: list[str] | None = None, n_per_occupation: int | None = None) -> list[dict]:
    """Generate base CVs (default: every occupation in the pools, n_per_occupation each)."""
    occs = occupations or list(pools["occupations"].keys())
    n = n_per_occupation or pools["n_per_occupation"]
    tiers = pools["tier_sequence"]
    if n > len(tiers):
        raise ValueError(f"tier_sequence has only {len(tiers)} entries, need {n}")
    pilot_positions = set(pools.get("pilot_positions", []))
    missing = [o for o in occs if o not in jobs]
    if missing:
        raise KeyError(f"occupations without a job ad in stimuli/jobs.csv: {missing}")
    problems = check_allocation_balance(pools)
    if problems:
        raise ValueError("base-country allocation is unbalanced: " + "; ".join(problems))

    # Applicant references are fixed per (occupation, position) over the whole
    # pool, so generating a subset yields the same references as the full set.
    all_occs = list(pools["occupations"].keys())
    ref_rng = random.Random(derive_int(seed, "applicant_references"))
    refs = iter(ref_rng.sample(range(1000, 10000), len(all_occs) * len(tiers)))
    ref_of = {(o, p): f"APP-{next(refs)}" for o in all_occs for p in range(1, len(tiers) + 1)}

    out = []
    for occ in occs:
        pool = pools["occupations"][occ]
        base_of = base_country_of(pools, occ, base_countries)
        rng = random.Random(derive_int(seed, "cv", occ))
        usage = Usage()
        for pos in range(1, n + 1):
            out.append(generate_cv(
                occupation=occ, position=pos, tier=tiers[pos - 1], pilot=pos in pilot_positions,
                applicant_reference=ref_of[(occ, pos)], job=jobs[occ], pool=pool,
                base=base_countries[base_of[pos]], held_constant=pools["held_constant"], school=pools["school"],
                reference_date=pools["reference_date"], rng=rng, usage=usage, seed=seed))
    return out


def build_cv_table(blocks_dir: str | Path, jobs_path: str | Path, base_countries_path: str | Path,
                   out_path: str | Path, force: bool = False) -> list[dict]:
    """Build all base CVs from ``stimuli/building_blocks/`` and write ``stimuli/cvs.csv``
    (refuses to overwrite unless ``force``). The base countries come from
    ``stimuli/base_countries.csv`` and ``building_blocks/institutions.csv``."""
    from ..tables import write_cv_table

    out_path = Path(out_path)
    if out_path.exists() and not force:
        raise FileExistsError(f"{out_path} exists; it is the frozen source of truth. Use --force to rebuild it.")
    blocks_dir = Path(blocks_dir)
    pools = load_building_blocks(blocks_dir)
    bases = load_base_countries(base_countries_path, blocks_dir / "institutions.csv")
    cvs = generate_base_cvs(pools, load_jobs(jobs_path), pools["seed"], bases)
    write_cv_table(cvs, out_path)
    return cvs
