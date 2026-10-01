"""validate-stimuli: passes on the repository tables and FAILS on tampered table rows.

Covers the adversarial review's tamper cases, now applied to stimuli/cvs.csv and
stimuli/nationalities.csv (every clone is rendered from these at prompt time).
"""

from __future__ import annotations

import pytest
from eng_helpers import REPO, copy_stimuli, edit_cv_row, make_paths, make_root_copy, read_table, write_table

from hiringaudit.cli import main
from hiringaudit.config import load_jobs, load_nationalities
from hiringaudit.leaks import LeakRules
from hiringaudit.prompts import NEUTRALITY_PARAGRAPH, load_library
from hiringaudit.stimuli.setting import load_base_countries
from hiringaudit.validation import validate_stimuli, validate_texts

NATS = load_nationalities(REPO / "stimuli" / "nationalities.csv")
BASES = load_base_countries(REPO / "stimuli" / "base_countries.csv",
                            REPO / "stimuli" / "building_blocks" / "institutions.csv")
RULES = LeakRules.load(REPO / "config" / "leak_terms.csv", NATS, BASES)
JOBS_CSV = REPO / "stimuli" / "jobs.csv"


@pytest.fixture
def paths(tmp_path):
    """Writable copies of the two tables for each tampering test."""
    return copy_stimuli(tmp_path, make_paths(tmp_path))


def _errors(paths):
    rep = validate_stimuli(paths)
    assert not rep.ok, "validation should have failed"
    return "\n".join(rep.errors)


def test_repository_tables_pass():
    rep = validate_stimuli(make_paths(REPO / "unused"))
    assert rep.ok, rep.summary()
    assert rep.checked_base_cvs == 48 and rep.checked_clones == 48 * (len(NATS.codes) + 1)


# ---- tampered CV rows (swdev_01 is set in the United Arab Emirates) ----
@pytest.mark.parametrize("cells,expect", [
    ({"exp1_city": "Beirut"}, "outside the base country whitelist"),                            # T4
    ({"exp1_city": "Riyadh"}, "outside the base country whitelist"),                            # other base country
    ({"exp2_city": "Stuttgart"}, "'Stuttgart'"),                                                # nothing German
    ({"edu1_institution": "Goethe University Frankfurt"}, "institution"),                       # setting rule
    ({"edu1_institution": "King Saud University"}, "outside the base country whitelist"),       # other base country
    ({"exp1_employer": "Brightmere Technologies GmbH"}, "'GmbH'"),                              # German legal form
    ({"exp1_bullets": "Managed a budget of EUR 2 million"}, "'EUR'"),                           # euro
    ({"profile": "Developer who holds the Abitur."}, "'Abitur'"),                               # German credential
    ({"exp1_bullets": "Prepared statements under HGB"}, "'HGB'"),
    ({"exp1_bullets": "Worked in Mannheim for two years"}, "'Mannheim'"),
    ({"exp1_bullets": "Organised the Bürgerfest"}, "'ü'"),                                      # umlauts
    ({"profile": "Developer who moved from Doha."}, "'Doha'"),                                  # other base city
    ({"profile": "Saudi developer."}, "'Saudi'"),                                               # demonym, not a place
    ({"location": "Mannheim, Germany"}, "location must be 'Dubai, United Arab Emirates'"),
    ({"work_authorization": "Unrestricted right to work in Germany; no visa sponsorship required"},
     "work_authorization must be"),
    ({"base_city": "Abu Dhabi"}, "base_city must be 'Dubai'"),
    ({"base_country": "DEU"}, "is not a base country"),
    ({"base_country": "SAU"}, "every CV needs exactly one same-occupation, same-tier partner"),
    ({"skills": "Python | Java | SQL | REST APIs | Git | Arabic"}, "'Arabic'"),                 # T5
    ({"skills": "Python | Java | SQL | REST APIs | Git | French"}, "'French'"),                 # T8
    ({"languages": "German (C2), English (C1)"}, "languages must list English only"),          # English only
    ({"profile": "Backend developer. EU citizen."}, "citizen"),                                  # T19
    ({"exp1_bullets": "Organised halal catering during Ramadan"}, "halal"),                     # T6
    ({"cert1_name": "Extra course", "cert1_year": "2026"}, "later than the reference date"),    # L7
    ({"positive_control_education": "edu3"},                                                     # the school line
     "positive_control_education does not name exactly the qualification entries"),            # T22 / L3
    ({"profile": "Qualified backend developer with 6 years of professional experience."},
     "qualification cue left in the positive control"),                                         # residual cue
    ({"cert1_name": "Diploma in Cloud Computing"}, "qualification cue left in the positive control"),
    ({"achievement1": "Fixed more than 40 reported bugs in the customer portal"},
     "key achievements do not come from the pool for its tier"),                               # tier coherence
    ({"applicant_reference": "APP-EGY1"}, "encodes nationality"),
    ({"availability": "Three months' notice"}, "design constant 'availability' differs"),
    ({"relevant_experience_months": "99"}, "stated experience months do not match"),
])
def test_tampered_cv_row_fails(paths, cells, expect):
    edit_cv_row(paths, "swdev_01", **cells)
    assert expect in _errors(paths)


def test_positive_control_must_drop_every_qualification_line(paths):
    """swdev_01 has an M.Sc. and the preceding B.Sc.: listing only one of them fails."""
    cols, rows = read_table(paths.cv_table_file)
    row = next(r for r in rows if r["cv_id"] == "swdev_01")
    assert row["positive_control_education"] == "edu1 | edu2"
    assert "M.Sc." in row["edu1_degree"] and "B.Sc." in row["edu2_degree"]
    row["positive_control_education"] = "edu1"
    write_table(paths.cv_table_file, cols, rows)
    err = _errors(paths)
    assert "positive_control_education does not name exactly the qualification entries" in err
    assert "qualification cue left in the positive control" in err


def test_tier_ordering_violation_fails(paths):  # H2: borderline CV with far more experience
    edit_cv_row(paths, "swdev_03", exp1_start="01/2015")
    err = _errors(paths)
    assert "borderline CV must be 12-18 months short" in err or "min adequate relevant experience" in err


def test_title_bullet_coherence(paths):  # N7 / T26: unrelated job retitled, its bullets kept
    cols, rows = read_table(paths.cv_table_file)
    row = next(r for r in rows if r["cv_id"] == "swdev_03")
    unrelated = next(i for i in (1, 2, 3) if row[f"exp{i}_relevant"] == "false")
    row[f"exp{unrelated}_title"] = "Senior Backend Developer"
    write_table(paths.cv_table_file, cols, rows)
    err = _errors(paths)
    assert "bullets do not come from the pool for this title" in err and "marked unrelated" in err


def test_duplicate_ids_fail(paths):
    cols, rows = read_table(paths.cv_table_file)
    rows[1] = {**rows[1], "cv_id": rows[0]["cv_id"], "applicant_reference": rows[0]["applicant_reference"]}
    write_table(paths.cv_table_file, cols, rows)
    err = _errors(paths)
    assert "is duplicated" in err and "used by more than one CV" in err


def test_unreadable_cell_is_a_clean_error(paths):
    edit_cv_row(paths, "swdev_01", pilot="maybe")
    assert "cannot read the stimulus tables" in _errors(paths)


# ---- tampered nationality rows ----
def _edit_nat(paths, which, **cells):
    cols, rows = read_table(paths.nationalities_file)
    for r in rows:
        if r["code"] == which:
            r.update(cells)
    write_table(paths.nationalities_file, cols, rows)


def test_multiline_demonym_breaks_the_clone_rule(paths):
    _edit_nat(paths, "EGY", demonym="Egyptian\nReligion: Muslim")
    err = _errors(paths)
    assert "clone differs from reference outside the Nationality line" in err or "line count differs" in err


def test_duplicate_demonym_fails(paths):
    _edit_nat(paths, "MAR", demonym="Egyptian")
    assert "demonym 'Egyptian' is used by more than one code" in _errors(paths)


def test_control_row_rules(paths):
    _edit_nat(paths, "NONE", demonym="Stateless")
    assert "the control row must have group 'control'" in _errors(paths)


def test_duplicate_code_fails(paths):
    _edit_nat(paths, "MAR", code="EGY")
    assert "duplicate nationality codes" in _errors(paths)


def test_placebo_demonym_is_checked_for_leaks(paths):
    edit_cv_row(paths, "swdev_02", profile="Worked with Malawian partners.")
    assert "'Malawian'" in _errors(paths)


# ---- template, job ads and prompts ----
def test_template_must_have_one_nationality_line(paths):
    t = paths.cv_template_file.read_text(encoding="utf-8")
    paths.cv_template_file.write_text(t.replace("{{NATIONALITY_LINE}}\n", "{{NATIONALITY_LINE}}\n{{NATIONALITY_LINE}}\n"),
                                      encoding="utf-8")
    with pytest.raises(ValueError):
        validate_stimuli(paths)


def _texts(prompts_dir):
    return load_library(prompts_dir).texts_for_scan()


def test_repository_job_ads_and_prompts_are_clean():
    jobs = load_jobs(JOBS_CSV)
    assert validate_texts(jobs, _texts(REPO / "prompts"), RULES, NEUTRALITY_PARAGRAPH) == []


def test_job_ad_and_prompt_leaks_are_caught():
    jobs = load_jobs(JOBS_CSV)
    bad = jobs["software_developer"].model_copy(update={"requirements": [*jobs["software_developer"].requirements,
                                                                         "EU citizenship required",
                                                                         "Fluent German"]})
    texts = _texts(REPO / "prompts")
    texts["baseline_k1"] += "\nCheck the cultural fit with our German team."
    texts["system"] += " Candidates from countries with weaker education systems need extra scrutiny."
    probs = "\n".join(validate_texts({**jobs, "software_developer": bad}, texts, RULES, NEUTRALITY_PARAGRAPH))
    assert "job ad software_developer" in probs and "citizenship" in probs and "'German'" in probs
    assert "prompt baseline_k1" in probs and "prompt system" in probs


def test_job_ad_german_terms_and_other_cities_are_caught():
    jobs = load_jobs(JOBS_CSV)
    acct = jobs["financial_accountant"]
    bad = acct.model_copy(update={"requirements": [*acct.requirements, "Sound knowledge of HGB"],
                                  "about": acct.about + " Our second office is in Riyadh.",
                                  "offer": [*acct.offer, "Salary from EUR 50,000"]})
    probs = validate_texts({"financial_accountant": bad}, {}, RULES, NEUTRALITY_PARAGRAPH)
    joined = "\n".join(probs)
    assert "'HGB'" in joined and "'EUR'" in joined
    riyadh = [p for p in probs if "'Riyadh'" in p]
    assert riyadh and not any("(SAU)" in p for p in riyadh)        # allowed only in the ad located in Riyadh
    assert len({p.split(")")[0] for p in riyadh}) == len(RULES.base_countries) - 1


@pytest.mark.parametrize("phrase", ["Preference for native speakers.", "A native speaker would be ideal."])
def test_native_speaker_wording_is_caught(phrase):
    # Regression: the term used to be matched literally ("native speakers?") and never fired.
    assert RULES.scan_text(phrase)


def test_principle_contexts_are_scanned():
    jobs = load_jobs(JOBS_CSV)
    probs = validate_texts(jobs, {}, RULES, NEUTRALITY_PARAGRAPH,
                           {"generic": "A company in Mannheim, Germany, is screening applications."})
    assert any("principle-probe context generic" in p and "'Mannheim'" in p for p in probs)


def test_prompt_part_leaks_are_caught(tmp_path):
    root = make_root_copy(tmp_path)
    cols, rows = read_table(root / "prompts" / "prompt_parts.csv")
    for r in rows:
        if r["part_id"] == "probe_context_generic":
            r["text"] = "A company in Mannheim is screening applications."
        if r["part_id"] == "independent_task_k3":
            r["text"] += " Consider the cultural fit."
    write_table(root / "prompts" / "prompt_parts.csv", cols, rows)
    rep = validate_stimuli(make_paths(tmp_path).with_overrides(prompts_dir=root / "prompts"))
    err = "\n".join(rep.errors)
    assert "principle-probe context generic" in err and "'Mannheim'" in err
    assert "prompt baseline_k3" in err and "'cultural'" in err


def test_cli_exit_codes(tmp_path):
    root = make_root_copy(tmp_path)
    assert main(["--root", str(root), "validate-stimuli"]) == 0
    p = make_paths(tmp_path).with_overrides(stimuli_dir=root / "stimuli")
    edit_cv_row(p, "whse_02", driving_licence="Class C")
    assert main(["--root", str(root), "validate-stimuli"]) == 1
