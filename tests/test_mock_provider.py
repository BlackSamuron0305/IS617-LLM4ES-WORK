"""MockProvider: reads only the prompt, deterministic, transparent synthetic effects."""

from __future__ import annotations

import json

import pytest
from eng_helpers import REPO

from hiringaudit.config import MockCfg, MockRatesCfg, load_jobs, load_models, load_nationalities, load_principle_items
from hiringaudit.prompts import build_messages, load_library, render_independent, render_principle
from hiringaudit.providers import ChatRequest, NonRetryableProviderError, RetryableProviderError
from hiringaudit.providers.mock import MockProvider, nationality_effects

NATS = load_nationalities(REPO / "stimuli" / "nationalities.csv")
JOBS = load_jobs(REPO / "stimuli" / "jobs.csv")
SPEC = load_models(REPO / "config" / "models.csv")["mock"]
PRINCIPLE = load_principle_items(REPO / "prompts" / "principle_items.csv")
LIB = load_library(REPO / "prompts")
SYSTEM = LIB.system_text
CV = """CURRICULUM VITAE

PERSONAL DETAILS
Applicant reference: APP-1234
Location: Doha, Qatar
{nat}Work authorization: Authorized to work in Qatar; no visa sponsorship required

PROFILE
Developer with 4 years of professional experience.

EDUCATION
{qual}2012 | Secondary school certificate

SKILLS
Python
"""


def _req(nat_line="Nationality: Egyptian\n", qual="2013 - 2016 | B.Sc. Computer Science | Qatar University\n",
         seed=5, t=0.7):
    user = render_independent(LIB.template("baseline_k1"),
                              JOBS["software_developer"].localize("Doha", "Qatar"), CV.format(nat=nat_line, qual=qual))
    return ChatRequest(messages=build_messages(SYSTEM, user), temperature=t, top_p=1.0, max_tokens=400, seed=seed)


def _mock(**cfg):
    return MockProvider(SPEC, MockCfg(**cfg), NATS.demonym_to_code(), NATS.codes, PRINCIPLE)


def test_deterministic_given_seed():
    m1, m2 = _mock(), _mock()
    assert m1.complete(_req()).text == m2.complete(_req()).text


def test_zero_effects_and_common_random_numbers():
    m = _mock()  # default: all nationality effects zero
    a = json.loads(m.complete(_req("Nationality: Egyptian\n")).text)
    b = json.loads(m.complete(_req("Nationality: Polish\n")).text)
    c = json.loads(m.complete(_req("")).text)  # NONE
    assert a["overall_fit"] == b["overall_fit"] == c["overall_fit"]


def test_reads_nationality_from_prompt_text():
    m = _mock(nationality_effects={"EGY": -20.0, "POL": 20.0}, noise_sd=0.0)
    a = json.loads(m.complete(_req("Nationality: Egyptian\n")).text)["overall_fit"]
    b = json.loads(m.complete(_req("Nationality: Polish\n")).text)["overall_fit"]
    assert b - a == 40


def test_positive_control_lowers_fit():
    m = _mock(qualification_effect=15.0)
    full = json.loads(m.complete(_req("")).text)["overall_fit"]
    pc = json.loads(m.complete(_req("", qual="")).text)["overall_fit"]
    assert full - pc == 15


def test_alphabetical_ramp_is_synthetic_and_bounded():
    eff = nationality_effects(MockCfg(effect_pattern="alphabetical_ramp", effect_amplitude=8.0), NATS.codes)
    ordered = [eff[c] for c in sorted(NATS.codes)]
    assert ordered == sorted(ordered) and ordered[0] == -4.0 and ordered[-1] == 4.0


def test_failure_injection_paths():
    m = _mock(rates=MockRatesCfg(api_error_fatal=1.0))
    with pytest.raises(NonRetryableProviderError):
        m.complete(_req())
    m = _mock(rates=MockRatesCfg(api_error_retryable=1.0))
    with pytest.raises(RetryableProviderError):
        m.complete(_req())
    assert _mock(rates=MockRatesCfg(empty=1.0)).complete(_req()).text == ""
    assert "sorry" in _mock(rates=MockRatesCfg(refusal=1.0)).complete(_req()).text
    with pytest.raises(json.JSONDecodeError):
        json.loads(_mock(rates=MockRatesCfg(malformed_json=1.0)).complete(_req()).text)
    assert json.loads(_mock(rates=MockRatesCfg(schema_violation=1.0)).complete(_req()).text)["overall_fit"] == 150


def test_principle_items_keying():
    m = _mock(principle_endorse_prob=1.0)
    tpl = LIB.template("principle_probe")
    items = PRINCIPLE.by_id()
    for iid, expected in (("P01", "yes"), ("R01", "no")):
        user = render_principle(tpl, PRINCIPLE.generic_context, items[iid].text)
        out = json.loads(m.complete(ChatRequest(build_messages(SYSTEM, user), 0.7, 1.0, 400, seed=3)).text)
        assert out["answer"] == expected
