"""(f) Schema validation of the processed tables fails loudly and specifically."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from hiringaudit.analysis.schema import (
    SchemaError,
    load_processed,
    validate_evaluations,
    validate_forced_choice,
    validate_principle,
)
from hiringaudit.analysis.simulate import NATIONALITIES, SimDesign, SimParams, simulate_all, write_processed

ROOT = Path(__file__).resolve().parents[1]
SMALL = SimDesign(cvs_per_occupation=2, tier_pattern=("adequate",), repetitions=1, variants=("k1", "k2"),
                  fc_pair_offsets=(1,), principle_repetitions=1)


@pytest.fixture(scope="module")
def tables():
    return simulate_all(SMALL, SimParams(p_refusal=0.02), seed=3)


def _problems(fn, df):
    with pytest.raises(SchemaError) as ei:
        fn(df)
    return " | ".join(ei.value.problems)


def test_valid_tables_pass(tables, tmp_path):
    write_processed(tables, tmp_path)
    out = load_processed(tmp_path)
    assert len(out["evaluations"]) == len(tables["evaluations"])
    assert out["forced_choice"] is not None and out["principle"] is not None
    assert out["evaluations"]["is_mock"].all()


def test_missing_column(tables):
    df = tables["evaluations"].drop(columns=["prompt_variant"])
    assert "missing required column" in _problems(validate_evaluations, df)


def test_bad_parse_status_and_range(tables):
    df = tables["evaluations"].copy()
    df.loc[0, "parse_status"] = "weird"
    df.loc[1, "overall_fit"] = 140
    msg = _problems(validate_evaluations, df)
    assert "parse_status" in msg and "outside [0, 100]" in msg


def test_ok_row_without_outcome(tables):
    df = tables["evaluations"].copy()
    i = df.index[df["parse_status"] == "ok"][0]
    df.loc[i, "interview"] = np.nan
    assert "missing 'interview'" in _problems(validate_evaluations, df)


def test_duplicate_cells_and_records(tables):
    df = pd.concat([tables["evaluations"], tables["evaluations"].iloc[[0]]], ignore_index=True)
    msg = _problems(validate_evaluations, df)
    assert "duplicated record_id" in msg and "duplicated (arm" in msg


def test_positive_control_rules(tables):
    df = tables["evaluations"].copy()
    i = df.index[df["clone_type"] == "positive_control"][0]
    df.loc[i, "nationality"] = "DEU"
    assert "positive_control rows must have nationality" in _problems(validate_evaluations, df)


def test_non_boolean_mock_flag(tables):
    df = tables["evaluations"].copy()
    df["is_mock"] = df["is_mock"].astype(object)
    df.loc[0, "is_mock"] = "maybe"
    assert "is_mock" in _problems(validate_evaluations, df)


def test_missing_reference(tables):
    df = tables["evaluations"]
    df = df[df["nationality"] != "DEU"]
    assert "reference nationality 'DEU'" in _problems(validate_evaluations, df)


def test_forced_choice_rules(tables):
    fc = tables["forced_choice"].copy()
    i = fc.index[fc["choice"] == "A"][0]
    fc.loc[i, "chosen_nationality"] = fc.loc[i, "nationality_b"]
    fc.loc[fc.index[1], "nationality_a"] = "NONE"
    msg = _problems(validate_forced_choice, fc)
    assert "chosen_nationality does not match" in msg and "NONE" in msg


def test_principle_keying_consistency(tables):
    pr = tables["principle"].copy()
    i = pr.index[(pr["keying"] == "reverse") & (pr["answer"] == "yes")][0]
    pr.loc[i, "endorses_neutrality"] = "yes"          # reverse-keyed "yes" must be "no"
    assert "answer x keying" in _problems(validate_principle, pr)


def test_header_only_optional_tables_are_absent(tables, tmp_path):
    write_processed({"evaluations": tables["evaluations"]}, tmp_path)
    tables["forced_choice"].iloc[:0].to_csv(tmp_path / "forced_choice.csv", index=False)
    out = load_processed(tmp_path)
    assert out["forced_choice"] is None and out["principle"] is None


def test_missing_directory_and_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_processed(tmp_path / "nope")
    with pytest.raises(FileNotFoundError):
        load_processed(tmp_path)


def test_mixed_model_revision_fails(tables):
    df = tables["evaluations"].copy()
    df.loc[df.index[:5], "model_revision"] = "other-revision"
    assert "more than one model_revision" in _problems(validate_evaluations, df)


def test_mixed_user_prompt_version_fails(tables):
    df = tables["evaluations"].copy()
    df.loc[df.index[:5], "user_prompt_version"] = "baseline_k1@edited"
    assert "more than one user_prompt_version" in _problems(validate_evaluations, df)


def test_prompt_hash_differs_between_replicates_fails():
    design = SimDesign(cvs_per_occupation=2, tier_pattern=("adequate",), repetitions=2, variants=("k1",),
                       eval_conditions=("baseline",))
    df = simulate_all(design, SimParams(), seed=4, forced_choice=False, principle=False)["evaluations"].copy()
    i = df.index[df["repetition"] == 2][0]
    df.loc[i, "prompt_sha256"] = "deadbeef"
    assert "more than one prompt" in _problems(validate_evaluations, df)


def test_model_revision_mismatch_across_tables_fails(tables, tmp_path):
    t = dict(tables)
    fc = t["forced_choice"].copy()
    fc["model_revision"] = "another"
    t["forced_choice"] = fc
    write_processed(t, tmp_path)
    with pytest.raises(SchemaError, match="across tables"):
        load_processed(tmp_path)


def test_placebo_outside_baseline_fails():
    design = SimDesign(cvs_per_occupation=2, tier_pattern=("adequate",), repetitions=1, variants=("k1",),
                       placebo=("URY",))
    df = simulate_all(design, SimParams(), seed=5, forced_choice=False, principle=False)["evaluations"].copy()
    i = df.index[df["nationality"] == "URY"][0]
    df.loc[i, "prompt_condition"] = "neutrality"
    assert "placebo nationalities may only appear" in _problems(validate_evaluations, df)


def test_simulator_nationalities_match_config():
    import csv

    with open(ROOT / "stimuli" / "nationalities.csv", encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    conf = {r["code"]: (r["group"], r["subregion"], r["arab_identity_contested"].strip().lower() == "true")
            for r in rows}
    sim = {d["code"]: (d["group"], d["subregion"], d["contested"]) for d in NATIONALITIES}
    assert conf == sim
    from hiringaudit.analysis.schema import PLACEBO_CODES
    assert set(PLACEBO_CODES) == {c for c, v in conf.items() if v[0] == "placebo"}
