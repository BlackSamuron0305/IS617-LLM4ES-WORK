"""Processed tables in the exact column layout written by the engineer's parser (v0.2 output).

Deviations from design_contract.md §7 that the analysis must accept: evaluations carry ``arm``
(primary | greedy) and ``temperature``; forced_choice carries
``repetition``; principle carries ``answer``, ``probe_id``, ``occupation``, ``prompt_variant`` and
string ``endorses_neutrality`` (NA for control items); replicates are numbered from 1; text flags are 0/1.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from hiringaudit.schemas import EVALUATION_COLUMNS, FORCED_CHOICE_COLUMNS, PRINCIPLE_COLUMNS
from hiringaudit.analysis import run_analysis
from hiringaudit.analysis.schema import load_processed
from hiringaudit.analysis.simulate import SimDesign, SimParams, make_nationality_effects, simulate_all

ROOT = Path(__file__).resolve().parents[1]
# Single source of truth for the engineer's processed-table layout.
EV_COLS = list(EVALUATION_COLUMNS)
FC_COLS = list(FORCED_CHOICE_COLUMNS)
PR_COLS = list(PRINCIPLE_COLUMNS)
FAST = dict(n_boot=49, n_perm=199, n_perm_secondary=49, n_boot_bt=15, n_perm_bt=0, concordance_splits=5,
            n_cal=19, n_boot_cal=9, n_boot_vc=9, run_mixedlm=False)


def _engineer_fixture(path: Path) -> None:
    design = SimDesign(models=("mock",), cvs_per_occupation=4, tier_pattern=("strong", "adequate", "adequate",
                                                                            "borderline"),
                       occupations=("software_developer", "retail_sales_associate"), repetitions=1,
                       fc_pair_offsets=(1, 2), principle_repetitions=1, robustness_arms=("greedy",))
    t = simulate_all(design, SimParams(nationality_effects=make_nationality_effects(arab_sd=2, seed=2),
                                       p_refusal=0.03, p_malformed=0.02), seed=12)
    ev = t["evaluations"].copy()
    for f in [c for c in ev.columns if c.startswith("mentions_")]:
        ev[f] = pd.array([None if v is None else int(v) for v in ev[f]], dtype="Int64")
    ev["interview"] = pd.array([None if np.isnan(v) else int(v) for v in ev["interview"]], dtype="Int64")
    fc = t["forced_choice"].copy()
    pr = t["principle"].copy()
    pr["seed"] = np.arange(len(pr))
    path.mkdir(parents=True, exist_ok=True)
    for df, cols, name in ((ev, EV_COLS, "evaluations"), (fc, FC_COLS, "forced_choice"), (pr, PR_COLS, "principle")):
        assert set(cols) <= set(df.columns), set(cols) - set(df.columns)
        df[cols].to_csv(path / f"{name}.csv", index=False, lineterminator="\n", na_rep="")


@pytest.fixture(scope="module")
def fixture_dir(tmp_path_factory):
    d = tmp_path_factory.mktemp("engineer") / "processed"
    _engineer_fixture(d)
    return d


def test_exact_engineer_columns_load(fixture_dir):
    assert pd.read_csv(fixture_dir / "evaluations.csv", nrows=0).columns.tolist() == EV_COLS
    assert pd.read_csv(fixture_dir / "forced_choice.csv", nrows=0).columns.tolist() == FC_COLS
    assert pd.read_csv(fixture_dir / "principle.csv", nrows=0).columns.tolist() == PR_COLS
    t = load_processed(fixture_dir)
    assert set(t["evaluations"]["arm"]) == {"primary", "greedy"}
    assert t["principle"]["endorses_neutrality"].isna().sum() > 0          # control items


def test_full_run_uses_primary_arm_and_reports_arms_as_robustness(fixture_dir, tmp_path):
    root = tmp_path / "root"
    (root / "config").mkdir(parents=True)
    shutil.copy(ROOT / "config" / "analysis_settings.csv", root / "config")
    res = run_analysis(fixture_dir, tmp_path / "out", dict(FAST, unblind=True), root=root)
    R = res["results"]
    d = R["design"]
    assert set(d.loc[d["task"] == "independent", "arm"]) == {"primary", "greedy"}
    n_primary_cvs = d.loc[(d["arm"] == "primary") & (d["condition"] == "baseline"), "base_cvs"].iloc[0]
    assert (R["heterogeneity"]["n_cv"] <= n_primary_cvs).all()
    checks = set(R["robustness"]["check"])
    assert "R4" in checks and "HX" in checks                       # host-national exclusion sensitivity
    assert R["host_effect"]["identified"].all()
    assert not R["confirmatory"].empty
    assert any("robustness arms analysed separately" in n for n in res["notes"])


def test_blind_run(fixture_dir, tmp_path):
    res = run_analysis(fixture_dir, tmp_path / "blind", FAST)
    assert res["blind"] and "heterogeneity" not in res["results"]
    assert "host_effect" not in res["results"] and not any("host" in p for p in res["outputs"])


def test_host_columns_validated(fixture_dir):
    t = load_processed(fixture_dir)
    ev, fc = t["evaluations"], t["forced_choice"]
    assert (ev["host_national"] == (ev["nationality"] == ev["base_country"])).all()
    assert ev.loc[ev["host_national"], "nationality_group"].eq("arab").all()
    assert (fc["host_national_a"] == (fc["nationality_a"] == fc["base_country"])).all()


def test_duplicate_key_includes_arm(fixture_dir, tmp_path):
    ev = pd.read_csv(fixture_dir / "evaluations.csv", keep_default_na=False, na_values=[""])
    g = ev[ev["arm"] == "greedy"].copy()
    g["record_id"] = g["record_id"] + "_dup"
    g["arm"] = "primary"                                                   # now collides with primary rows
    bad = tmp_path / "bad"
    bad.mkdir()
    pd.concat([ev, g]).to_csv(bad / "evaluations.csv", index=False)
    from hiringaudit.analysis.schema import SchemaError
    with pytest.raises(SchemaError, match="duplicated \\(arm"):
        load_processed(bad)


@pytest.mark.skipif(not (ROOT / "data" / "processed" / "mock_pipeline_test" / "evaluations.csv").exists(),
                    reason="engineer mock run not present")
def test_real_engineer_mock_output_loads():
    t = load_processed(ROOT / "data" / "processed" / "mock_pipeline_test")
    assert t["evaluations"]["is_mock"].all()
