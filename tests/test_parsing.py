"""Single-response parsing and classification (never coerces)."""

from __future__ import annotations

import pytest

from hiringaudit.parsing import extract_json_object, parse_response

VALID = '{"overall_fit": 72, "interview": "yes", "confidence": 80, "reason": "Good match."}'


def test_valid():
    r = parse_response(VALID, "independent")
    assert r.parse_status == "ok" and r.parsed["overall_fit"] == 72 and not r.refusal


def test_code_fenced():
    r = parse_response(f"```json\n{VALID}\n```", "independent")
    assert r.parse_status == "ok"
    assert parse_response(f"```\n{VALID}\n```", "independent").parse_status == "ok"


def test_prose_wrapped():
    r = parse_response(f"Here is my assessment:\n{VALID}\nLet me know if you need more.", "independent")
    assert r.parse_status == "ok" and r.parsed["interview"] == "yes"


def test_think_block_is_ignored():
    assert parse_response(f"<think>\nhmm {{ not json\n</think>\n{VALID}", "independent").parse_status == "ok"
    assert parse_response("<think>only thinking</think>", "independent").parse_status == "empty"


def test_malformed():
    r = parse_response('{"overall_fit": 72, "interview": "yes", "confid', "independent")
    assert r.parse_status == "malformed_json" and r.parsed is None


@pytest.mark.parametrize("bad", [
    '{"overall_fit": 150, "interview": "yes", "confidence": 80, "reason": "x"}',      # out of range
    '{"overall_fit": 70, "interview": "Yes", "confidence": 80, "reason": "x"}',       # enum case: not coerced
    '{"overall_fit": "70", "interview": "yes", "confidence": 80, "reason": "x"}',     # string number
    '{"overall_fit": 70, "interview": "yes", "reason": "x"}',                         # missing key
    '{"overall_fit": 70, "interview": "yes", "confidence": 80, "reason": "x", "extra": 1}',  # extra key
    '{"overall_fit": 70.5, "interview": "yes", "confidence": 80, "reason": "x"}',     # non-integer
])
def test_schema_violations(bad):
    r = parse_response(bad, "independent")
    assert r.parse_status == "schema_violation" and r.parsed is None and r.extracted is not None


def test_forced_choice_tie_is_schema_violation():
    r = parse_response('{"choice": "both", "confidence": 50, "reason": "Equal."}', "forced_choice")
    assert r.parse_status == "schema_violation"
    assert parse_response('{"choice": "B", "confidence": 50, "reason": "x"}', "forced_choice").parse_status == "ok"


def test_principle_schema_v02():
    ok = parse_response('{"answer": "no", "agreement": 10, "reason": "x"}', "principle_probe")
    assert ok.parse_status == "ok"
    old = parse_response('{"endorses_neutrality": "yes", "agreement": 90, "reason": "x"}', "principle_probe")
    assert old.parse_status == "schema_violation"


def test_refusal():
    r = parse_response("I'm sorry, but I can't help with evaluating candidates based on this.", "independent")
    assert r.parse_status == "refusal" and r.refusal
    r2 = parse_response('{"choice": null, "confidence": 0, "reason": "I cannot choose based on nationality."}',
                        "forced_choice")
    assert r2.parse_status == "refusal"


def test_schema_valid_answer_is_not_a_refusal_even_if_reluctant():
    txt = '{"choice": "A", "confidence": 50, "reason": "I cannot see a big difference, but A fits slightly better."}'
    assert parse_response(txt, "forced_choice").parse_status == "ok"


@pytest.mark.parametrize("empty", ["", "   \n\t", None])
def test_empty(empty):
    assert parse_response(empty, "independent").parse_status == "empty"


def test_integer_valued_float_is_accepted_as_integer():
    r = parse_response('{"overall_fit": 70.0, "interview": "no", "confidence": 60, "reason": "x"}', "independent")
    assert r.parse_status == "ok"


def test_extract_first_object_among_several():
    assert extract_json_object('noise {"a": 1} more {"b": 2}') == {"a": 1}
    assert extract_json_object("no braces here") is None


@pytest.mark.parametrize("text", [
    "I refuse to rank people in this way.",
    "I'm not comfortable making this decision.",
    "As a language model, I should not choose between applicants.",
    "As an AI, I cannot do this.",
])
def test_extended_refusal_phrases(text):  # review L4
    assert parse_response(text, "forced_choice").parse_status == "refusal"


def test_first_object_rule_and_object_count():  # review L4: documented first-object rule
    txt = '{"choice": "A", "confidence": 60, "reason": "draft"} Actually: {"choice": "B", "confidence": 70, "reason": "final"}'
    r = parse_response(txt, "forced_choice")
    assert r.parse_status == "ok" and r.parsed["choice"] == "A" and r.n_json_objects == 2


@pytest.mark.parametrize("bad,near", [
    ('{"overall_fit": 70, "interview": "Yes", "confidence": 80, "reason": "x"}', True),
    ('{"overall_fit": "70", "interview": "yes", "confidence": 80, "reason": "x"}', True),
    ('{"overall_fit": 70, "interview": "yes", "confidence": 80, "reason": "x", "extra": 1}', True),
    ('{"overall_fit": 70.5, "interview": "yes", "confidence": 80, "reason": "x"}', False),
    ('{"overall_fit": 70, "interview": "maybe", "confidence": 80, "reason": "x"}', False),
])
def test_near_miss_is_diagnostic_only(bad, near):
    r = parse_response(bad, "independent")
    assert r.parse_status == "schema_violation" and r.parsed is None and r.near_miss is near
