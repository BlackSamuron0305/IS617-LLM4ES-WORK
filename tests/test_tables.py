"""The two stimulus tables, the table builder (from the building blocks), and rendering CV row x nationality row."""

from __future__ import annotations

import re
from collections import Counter, defaultdict

import pytest
from eng_helpers import REPO

from hiringaudit.config import load_jobs, load_nationalities
from hiringaudit.leaks import LeakRules
from hiringaudit.prompts import render_job_ad
from hiringaudit.stimuli.build_table import build_cv_table, check_allocation_balance, generate_base_cvs
from hiringaudit.stimuli.building_blocks import BuildingBlockError, load_building_blocks
from hiringaudit.stimuli.dates import experience_months
from hiringaudit.stimuli.render import (COUNTERFACTUAL, NATIONALITY_PREFIX, POSITIVE_CONTROL, load_template,
                                        render_clone)
from hiringaudit.stimuli.setting import load_base_countries
from hiringaudit.tables import TableError, load_cv_table, write_cv_table
from hiringaudit.validation import check_tier_ordering, future_dates

STIM = REPO / "stimuli"
BLOCKS = STIM / "building_blocks"
POOLS = load_building_blocks(BLOCKS)
JOBS = load_jobs(STIM / "jobs.csv")
NATS = load_nationalities(STIM / "nationalities.csv")
TEMPLATE = load_template(STIM / "cv_template.txt")
BASES = load_base_countries(STIM / "base_countries.csv", BLOCKS / "institutions.csv")
RULES = LeakRules.load(REPO / "config" / "leak_terms.csv", NATS, BASES)
CVS = load_cv_table(STIM / "cvs.csv")


# ---- nationalities.csv ----
def test_nationality_table():
    assert len(NATS.codes) == 34 and NATS.reference == "DEU"
    groups = defaultdict(list)
    for n in NATS.conditions:
        groups[n.group].append(n.code)
    assert len(groups["arab"]) == 22 and set(groups["benchmark"]) == {"DEU", "POL", "TUR"}
    assert len(groups["placebo"]) == 8 and groups["control"] == ["NONE"]
    none = NATS.by_code("NONE")
    assert none.demonym is None and none.country is None
    assert {n.code for n in NATS.conditions if n.arab_identity_contested} == {"COM", "DJI", "SOM"}
    assert NATS.by_code("SYR").arab_league_joined == 1945 and "2023" in NATS.by_code("SYR").note


# ---- cvs.csv and its builder ----
def test_table_is_what_the_builder_produced(tmp_path):
    out = tmp_path / "cvs.csv"
    build_cv_table(BLOCKS, STIM / "jobs.csv", STIM / "base_countries.csv", out)
    assert out.read_bytes() == (STIM / "cvs.csv").read_bytes()
    with pytest.raises(FileExistsError):
        build_cv_table(BLOCKS, STIM / "jobs.csv", STIM / "base_countries.csv", out)


def test_building_blocks_are_one_entity_per_row():
    occs = list(POOLS["occupations"])
    assert occs == list(JOBS) and POOLS["n_per_occupation"] == 8 and POOLS["fc_pairs"] == [[1, 4], [2, 5], [3, 6], [7, 8]]
    assert POOLS["tier_sequence"][:6] == ["strong", "adequate", "borderline"] * 2 and POOLS["pilot_positions"] == [1, 2, 3, 4, 5, 6]
    for occ, pool in POOLS["occupations"].items():
        assert pool["titles"]["senior"] and pool["bullets"]["core"] and pool["employers"]
        assert all(r["bullets"] and r["employers"] and r["as"] for r in pool["unrelated_roles"])
        assert all(q["kind"] in ("computing", "business", "engineering", "college") for lvl in pool["qualifications"].values() for q in lvl)
        masters = [q for q in pool["qualifications"]["advanced"] if q["degree"].startswith(("M.Sc.", "MBA"))]
        assert all(q.get("bachelor") for q in masters)


def test_building_block_errors_are_clear(tmp_path):
    import shutil

    from eng_helpers import read_table, write_table

    d = tmp_path / "blocks"
    shutil.copytree(BLOCKS, d)
    cols, rows = read_table(d / "skills.csv")
    rows[0]["kind"] = "preferred"
    write_table(d / "skills.csv", cols, rows)
    with pytest.raises(BuildingBlockError, match="unknown value 'preferred'"):
        load_building_blocks(d)
    shutil.copy(BLOCKS / "skills.csv", d / "skills.csv")
    cols, rows = read_table(d / "cv_slots.csv")
    rows[1]["base_country"] = "EGY"            # swdev_02 no longer shares its pair's base country
    write_table(d / "cv_slots.csv", cols, rows)
    with pytest.raises(BuildingBlockError, match="must share one base country"):
        load_building_blocks(d)


def test_positive_control_column_names_education_entries(tmp_path):
    from eng_helpers import read_table, write_table

    cols, rows = read_table(STIM / "cvs.csv")
    assert "positive_control_education" in cols and "positive_control_lines" not in cols
    assert {r["positive_control_education"] for r in rows} == {"edu1", "edu1 | edu2"}
    rows[0]["positive_control_education"] = "edu1 | edu7"
    write_table(tmp_path / "cvs.csv", cols, rows)
    with pytest.raises(TableError, match="edu7"):
        load_cv_table(tmp_path / "cvs.csv")


def test_table_round_trip(tmp_path):
    write_cv_table(CVS, tmp_path / "again.csv")
    assert load_cv_table(tmp_path / "again.csv") == CVS
    assert generate_base_cvs(POOLS, JOBS, POOLS["seed"], BASES) == generate_base_cvs(POOLS, JOBS, POOLS["seed"], BASES)


def test_counts_tiers_and_pilot_subset():
    assert len(CVS) == 48
    by_occ = defaultdict(list)
    for cv in CVS:
        by_occ[cv["occupation"]].append(cv)
    assert set(by_occ) == set(JOBS)
    for cvs in by_occ.values():
        tiers = [c["qualification_tier"] for c in cvs]
        assert tiers.count("strong") == 2 and tiers.count("adequate") == 4 and tiers.count("borderline") == 2
        assert sorted(c["qualification_tier"] for c in cvs if c["pilot"]) == sorted(["strong", "adequate", "borderline"] * 2)
    assert len({cv["applicant_reference"] for cv in CVS}) == 48


def test_english_only_and_base_country_coherence():
    """User request 2026-10-01: every CV is set entirely in its base country."""
    for cv in CVS:
        assert cv["languages"] == "English (C1)"
        base = BASES[cv["base_country"]]
        assert NATS.by_code(base.code).group == "arab" and NATS.by_code(base.code).country == base.name
        assert cv["base_city"] == base.base_city
        assert {k: cv[k] for k in ("location", "work_authorization", "driving_licence")} == base.personal_lines()
        assert cv["location"] == f"{base.base_city}, {base.name}"
        assert all(j["city"] in base.cities for j in cv["experience"])
        assert cv["experience"][0]["city"] == base.base_city            # current job where the applicant lives
        insts = [e["institution"] for e in cv["education"] if e["institution"]]
        assert 1 <= len(insts) <= 2 and set(insts) <= base.all_institutions
        assert not any(n.demonym and n.demonym in i for n in NATS.conditions for i in insts)
        assert cv["education"][-1]["degree"] == "Secondary school certificate"
    for job in JOBS.values():
        assert job.location == "{city}, {country}"
        langs = [r for r in job.requirements if "English" in r or "German" in r]
        assert langs == ["Fluent English (C1 or higher)"]
        for base in BASES.values():
            ad = render_job_ad(job.localize(base.base_city, base.name))
            assert f"Location: {base.base_city}, {base.name}" in ad and "{" not in ad
            assert RULES.scan_text(ad, base.allowed_phrases()) == []


def test_forced_choice_pairs_share_a_base_country_and_allocation_is_balanced():
    groups = defaultdict(list)
    for cv in CVS:
        groups[(cv["occupation"], cv["qualification_tier"], cv["base_country"])].append(cv)
    assert len(groups) == 24 and all(len(g) == 2 for g in groups.values())
    assert all(a["pilot"] == b["pilot"] for a, b in groups.values())
    per_country = defaultdict(list)
    for occ, tier, code in groups:
        per_country[code].append((occ, tier))
    assert set(per_country) == set(BASES) and len(BASES) == 8
    for cells in per_country.values():   # 3 pairs per country, in 3 different occupations, >= 2 tiers
        assert len(cells) == 3 and len({o for o, _ in cells}) == 3 and len({t for _, t in cells}) >= 2
    pilot = Counter(code for (occ, tier, code), g in groups.items() if g[0]["pilot"] and JOBS[occ].pilot)
    assert set(pilot) == set(BASES) and sum(pilot.values()) == 9 and max(pilot.values()) == 2
    assert check_allocation_balance(POOLS) == []


def test_cv_length_is_comparable_within_a_tier():
    shape = defaultdict(set)
    for cv in CVS:
        key = (cv["occupation"], cv["qualification_tier"])
        shape[key].add((tuple(len(j["bullets"]) for j in cv["experience"]), len(cv["achievements"]),
                        len(cv["skills"]), len(cv["certifications"]), cv["profile"].count(". ") + 1,
                        len(cv["education"])))
    assert all(len(s) == 1 for s in shape.values()), {k: v for k, v in shape.items() if len(v) > 1}
    for cv in CVS:
        tier = cv["qualification_tier"]
        n_roles = {"strong": 4, "adequate": 2, "borderline": 2}[tier]
        assert len(cv["experience"]) == n_roles
        assert 2 <= len(cv["achievements"]) <= 3 and 8 <= len(cv["skills"]) <= 12 and len(cv["certifications"]) <= 3
        assert 2 <= cv["profile"].count(". ") + 1 <= 3
        for j in cv["experience"]:
            assert (2 <= len(j["bullets"]) <= 3) if not j["relevant"] else (3 <= len(j["bullets"]) <= 5)
        assert set(cv["achievements"]) <= set(POOLS["occupations"][cv["occupation"]]["achievements"][tier])


def test_nothing_german_in_any_cv_or_job_ad():
    german = RULES.categories["german"] + RULES.categories["german_currency"] + ["German", "Germany"]
    pat = re.compile(r"(?<![\w])(" + "|".join(re.escape(t) for t in german) + r")(?![\w])", re.IGNORECASE)
    texts = [render_clone(cv, None, COUNTERFACTUAL, TEMPLATE) for cv in CVS]
    texts += [render_job_ad(j.localize(b.base_city, b.name)) for j in JOBS.values() for b in BASES.values()]
    for text in texts:
        hits = [m.group(0) for m in pat.finditer(text)]
        assert hits == [] and not set("äöüÄÖÜß€") & set(text), hits


def test_tier_is_a_real_difference_in_qualifications():
    assert check_tier_ordering(CVS, JOBS, "2024-06") == []
    for cv in CVS:
        req = JOBS[cv["occupation"]].required_years * 12
        rel, tot = experience_months(cv, cv["reference_date"])
        assert (rel, tot) == (cv["relevant_experience_months"], cv["total_experience_months"])
        required = POOLS["occupations"][cv["occupation"]]["skills"]["required"]
        assert all(s in cv["skills"] for s in required)
        if cv["qualification_tier"] == "borderline":
            assert req - 18 <= rel <= req - 12 and rel >= 6 and tot < req
            assert [j["relevant"] for j in cv["experience"]] == [True, False]
        else:
            assert all(j["relevant"] for j in cv["experience"])


def test_unrelated_role_is_coherent_and_satisfies_no_must_have():
    for cv in CVS:
        pool = POOLS["occupations"][cv["occupation"]]
        roles = {r["title"]: r for r in pool["unrelated_roles"]}
        for job in cv["experience"]:
            if job["relevant"]:
                assert set(job["bullets"]) <= set(pool["bullets"]["core"]) | set(pool["bullets"]["senior"])
                continue
            role = roles[job["title"]]
            assert set(job["bullets"]) <= set(role["bullets"]) and role["as"] in cv["profile"]
            text = " ".join(job["bullets"]).lower()
            assert not [s for s in pool["skills"]["required"] if s.lower() in text]


def test_same_tier_cvs_are_genuinely_different():
    groups = defaultdict(list)
    for cv in CVS:
        if cv["pilot"]:
            groups[(cv["occupation"], cv["qualification_tier"])].append(cv)
    for a, b in groups.values():
        assert not ({e["employer"] for e in a["experience"] if e["relevant"]}
                    & {e["employer"] for e in b["experience"] if e["relevant"]})
        assert a["profile"] != b["profile"]


# ---- rendering: CV row x nationality row ----
def test_rendering_field_order_no_leak_no_future_dates():
    for cv in CVS:
        text = render_clone(cv, "Egyptian", COUNTERFACTUAL, TEMPLATE)
        lines = text.split("\n")
        keys = [l.split(": ")[0] for l in lines[lines.index("PERSONAL DETAILS") + 1:lines.index("PROFILE") - 1]]
        assert keys == ["Applicant reference", "Location", "Nationality", "Work authorization",
                        "Driving licence", "Availability", "Languages"]
        heads = [l for l in lines if l.isupper() and l]
        assert heads == ["CURRICULUM VITAE", "PERSONAL DETAILS", "PROFILE", "KEY ACHIEVEMENTS",
                         "PROFESSIONAL EXPERIENCE", "EDUCATION", "SKILLS", "CERTIFICATIONS"]
        none = render_clone(cv, None, COUNTERFACTUAL, TEMPLATE)
        assert NATIONALITY_PREFIX not in none and RULES.scan_cv(none, BASES[cv["base_country"]].allowed_phrases()) == []
        assert RULES.scan_cv(none) != []        # its own base-country place names are only allowed for it
        assert not re.search(r"(?<![A-Za-z])German", none)  # nothing German anywhere (also not "Germany")
        assert future_dates(text, cv["reference_date"]) == []
        assert max(int(y) for y in re.findall(r"\b(20\d{2})\b", text.split("PROFILE", 1)[1])) <= 2024


def test_every_clone_differs_only_in_the_nationality_line():
    for cv in CVS:
        ref = render_clone(cv, "German", COUNTERFACTUAL, TEMPLATE).split("\n")
        for n in NATS.conditions:
            clone = render_clone(cv, n.demonym, COUNTERFACTUAL, TEMPLATE).split("\n")
            if n.demonym is None:
                assert clone == [l for l in ref if not l.startswith(NATIONALITY_PREFIX)]
            else:
                assert [(a, b) for a, b in zip(ref, clone) if a != b] == (
                    [] if n.code == "DEU" else [("Nationality: German", f"Nationality: {n.demonym}")])
        none = render_clone(cv, None, COUNTERFACTUAL, TEMPLATE).split("\n")
        pc = render_clone(cv, None, POSITIVE_CONTROL, TEMPLATE).split("\n")
        lines = cv["positive_control_lines"]
        assert [l for l in none if l not in pc] == lines and len(pc) == len(none) - len(lines)


def test_education_has_no_gaps_and_positive_control_drops_every_qualification():
    """Lead request 2026-10-01: a master's is preceded by its bachelor's (same base
    country, coherent dates); the positive control removes ALL qualification lines
    and leaves no qualification cue."""
    from hiringaudit.validation import residual_qualification_cues

    for cv in CVS:
        edu = cv["education"]
        quals = [e for e in edu if e["institution"]]
        masters = [e for e in quals if e["degree"].startswith("M.Sc.") or e["degree"] == "MBA"]
        if masters:
            assert len(quals) == 2 and quals[1]["degree"].startswith("B.Sc.")
            assert int(quals[1]["end"]) <= int(quals[0]["start"]) <= int(quals[1]["end"]) + 1
            assert int(quals[1]["end"]) - int(quals[1]["start"]) == 4
        else:
            assert len(quals) == 1
        # school leaving -> first qualification -> ... without a gap of more than a year
        assert int(quals[-1]["start"]) - 1 <= int(edu[-1]["end"]) <= int(quals[-1]["start"])
        assert cv["positive_control_lines"] == [f"{e['start']} - {e['end']} | {e['degree']} | {e['institution']}"
                                                for e in quals]
        pc = render_clone(cv, None, POSITIVE_CONTROL, TEMPLATE)
        assert residual_qualification_cues(pc) == []
        assert pc.split("EDUCATION\n", 1)[1].split("\n\n", 1)[0] == f"{edu[-1]['end']} | Secondary school certificate"
    assert any(len(cv["positive_control_lines"]) == 2 for cv in CVS)
