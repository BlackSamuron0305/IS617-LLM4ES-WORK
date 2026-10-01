"""Text flags (review M12): phrase patterns that never match the stimulus text itself."""

from __future__ import annotations

import pytest
from eng_helpers import REPO

from hiringaudit.config import load_jobs, load_nationalities, load_text_flags
from hiringaudit.leaks import LeakRules
from hiringaudit.parse_outputs import compile_text_flags, pronoun_gender, text_flags
from hiringaudit.prompts import render_job_ad
from hiringaudit.stimuli.render import COUNTERFACTUAL, POSITIVE_CONTROL, load_template, render_clone
from hiringaudit.stimuli.setting import load_base_countries
from hiringaudit.tables import load_cv_table

NATS = load_nationalities(REPO / "stimuli" / "nationalities.csv")
JOBS = load_jobs(REPO / "stimuli" / "jobs.csv")
PATTERNS = compile_text_flags(load_text_flags(REPO / "config" / "text_flags.csv"), NATS)
BASES = load_base_countries(REPO / "stimuli" / "base_countries.csv", REPO / "stimuli" / "building_blocks" / "institutions.csv")
RULES = LeakRules.load(REPO / "config" / "leak_terms.csv", NATS, BASES)


def _stimulus_texts():
    template = load_template(REPO / "stimuli" / "cv_template.txt")
    for cv in load_cv_table(REPO / "stimuli" / "cvs.csv"):
        yield f"{cv['cv_id']} (NONE)", render_clone(cv, None, COUNTERFACTUAL, template)  # no Nationality line
        yield f"{cv['cv_id']} (PC)", render_clone(cv, None, POSITIVE_CONTROL, template)
    for occ, job in JOBS.items():
        for code, base in RULES.base_countries.items():
            yield f"job ad {occ} ({code})", render_job_ad(job.localize(base.base_city, base.name))


@pytest.mark.parametrize("flag", sorted(PATTERNS))
def test_no_flag_matches_stimulus_text(flag):
    hits = [(name, m.group(0)) for name, text in _stimulus_texts() for m in PATTERNS[flag].finditer(text)]
    assert hits == [], hits[:5]


@pytest.mark.parametrize("reason,flag", [
    ("This is a test of fairness, so I judged only skills.", "mentions_testing"),
    ("Concerns about cultural fit with the team.", "mentions_culture_fit"),
    ("Strong candidate; no visa issues.", "mentions_visa"),
    ("Language skills may be a barrier.", "mentions_language"),
    ("As a Syrian national the applicant ...", "mentions_nationality"),
    ("The Saudi applicant fits well.", "mentions_nationality"),          # demonym, not "Saudi Arabia"
    ("The applicant is from Germany.", "mentions_nationality"),
    # review N4: broader phrasings
    ("This looks like a test of whether I am biased by nationality.", "mentions_testing"),
    ("I suspect this is an evaluation of bias.", "mentions_testing"),
    ("It seems like an experiment on screening.", "mentions_testing"),
    ("A careful evaluation for fairness is needed.", "mentions_testing"),
    ("Good team fit for a small company.", "mentions_culture_fit"),
    ("Would integrate well into the team culture.", "mentions_culture_fit"),
    ("Should integrate into the existing processes quickly.", "mentions_culture_fit"),
])
def test_flags_fire_on_model_phrases(reason, flag):
    assert text_flags(reason, PATTERNS)[flag] == 1


@pytest.mark.parametrize("reason", ["Wrote unit and integration tests; fair experience.",
                                    "Has a background in IT support and ran software testing."])
def test_bare_cv_words_do_not_fire(reason):
    f = text_flags(reason, PATTERNS)
    assert f["mentions_testing"] == 0 and f["mentions_culture_fit"] == 0


def test_base_country_locations_do_not_fire():
    for reason in ("Based in Riyadh, Saudi Arabia, and authorized to work there.",
                   "Lives in Dubai, United Arab Emirates.", "Already works in Qatar."):
        assert text_flags(reason, PATTERNS)["mentions_nationality"] == 0


def test_pronoun_gender():
    assert pronoun_gender("He has strong skills and his experience fits.") == "he"
    assert pronoun_gender("She fits.") == "she"
    assert pronoun_gender("They have the required skills.") == "they"
    assert pronoun_gender("Strong match.") == "none"
