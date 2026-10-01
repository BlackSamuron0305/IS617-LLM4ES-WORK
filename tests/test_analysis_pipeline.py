"""(e) Mock watermarking, blind default, override stamps, and end-to-end smoke tests of run_analysis / the CLI."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pandas as pd
import pytest

from hiringaudit.analysis import MOCK_BANNER, OVERRIDE_BANNER, run_analysis
from hiringaudit.analysis import figures as figs
from hiringaudit.analysis.__main__ import main as cli_main
from hiringaudit.analysis.simulate import (PLACEBO_CODES, SimDesign, SimParams, make_nationality_effects,
                                           simulate_all, write_processed)
from hiringaudit.analysis.settings import PACKAGE_ROOT, PARSE_BANNER
from hiringaudit.analysis.tables import read_csv

FAST = dict(n_boot=49, n_perm=199, n_perm_secondary=49, n_boot_bt=15, n_perm_bt=0, concordance_splits=5,
            n_cal=29, n_boot_cal=19, n_boot_vc=9, run_mixedlm=False)
DESIGN = SimDesign(models=("m-a", "m-b"), cvs_per_occupation=4, tier_pattern=("strong", "adequate", "adequate",
                                                                             "borderline"),
                   repetitions=2, variants=("k1", "k2"), fc_pair_offsets=(1, 2), principle_repetitions=2,
                   placebo=PLACEBO_CODES, robustness_arms=("greedy",))
PARAMS = SimParams(nationality_effects=make_nationality_effects(arab_sd=2, seed=1), p_refusal=0.02,
                   host_national_effect=3.0, fc_host_effect=0.5)


def temp_root(base: Path) -> Path:
    """Project root with the confirmatory config (not under git: mock-only unblinding is exempt)."""
    root = base / "root"
    (root / "config").mkdir(parents=True, exist_ok=True)
    for f in ("analysis_settings.csv", "country_covariates.csv"):
        shutil.copy(PACKAGE_ROOT / "config" / f, root / "config")
    return root


@pytest.fixture(scope="module")
def mock_run(tmp_path_factory):
    base = tmp_path_factory.mktemp("mock")
    write_processed(simulate_all(DESIGN, PARAMS, seed=4, is_mock=True), base / "processed")
    figs.FIGURE_TEXT_REGISTRY.clear()
    res = run_analysis(base / "processed", base / "out", dict(FAST, unblind=True), root=temp_root(base))
    return base, res, dict(figs.FIGURE_TEXT_REGISTRY)


def test_every_figure_carries_mock_and_override_banners(mock_run):
    base, res, registry = mock_run
    fig_files = [p for p in res["outputs"] if p.startswith("figures/")]
    assert fig_files, "no figures written"
    stems = {str(base / "out" / Path(p).with_suffix("")) for p in fig_files}
    assert stems <= set(registry), "figure without registered text"
    for s in stems:
        assert sum(MOCK_BANNER in t for t in registry[s]) >= 2, f"{s}: mock banner missing (title + watermark)"
        assert sum(OVERRIDE_BANNER in t for t in registry[s]) >= 2, f"{s}: override banner missing"
    for p in fig_files:
        assert (base / "out" / p).stat().st_size > 0


def test_every_table_and_report_carries_banners(mock_run):
    base, res, _ = mock_run
    out = base / "out"
    csvs = [p for p in res["outputs"] if p.endswith(".csv")]
    texs = [p for p in res["outputs"] if p.endswith(".tex")]
    assert csvs and texs
    for p in csvs:
        head = (out / p).read_text(encoding="utf-8").splitlines()[:2]
        assert head == [f"# {MOCK_BANNER}", f"# {OVERRIDE_BANNER}"], p
        assert not read_csv(out / p).empty
    for p in texs:
        txt = (out / p).read_text(encoding="utf-8")
        assert txt.startswith(f"% {MOCK_BANNER}") and "SYNTHETIC MOCK DATA --- NOT RESULTS" in txt
        assert "EXPLORATORY OVERRIDE" in txt
    summary = (out / "summary.md").read_text(encoding="utf-8")
    assert summary.startswith(f"# {MOCK_BANNER}") and OVERRIDE_BANNER in summary
    for key in ("Confirmatory config", "SHA-256", "git commit", "Analysis code repository commit",
                "Analysis code SHA-256", "Preregistration SHA-256"):
        assert key in summary
    for p in res["outputs"]:
        assert f"`{p}`" in summary
    assert '"is_mock": true' in (out / "variance_components.json").read_text(encoding="utf-8")


def test_unblinded_mock_run_is_logged(mock_run):
    base, res, _ = mock_run
    lines = (base / "root" / "results" / "unblinding_log.jsonl").read_text(encoding="utf-8").strip().splitlines()
    e = json.loads(lines[-1])
    assert e["all_rows_mock"] is True and e["freeze_ok"] is False
    assert len(e["confirmatory_config_sha256"]) == 64 and e["overrides"]


def test_core_outputs_present(mock_run):
    _, res, _ = mock_run
    R = res["results"]
    for name in ("heterogeneity", "contrasts", "confirmatory", "rq1_decision", "rq3", "bt", "principle",
                 "variance_components", "variance_components_upper80", "positive_control", "robust_labels",
                 "placebo", "subregion_net", "host_effect", "host_sensitivity_deltas"):
        assert name in R and not R[name].empty, name
    fams = set(R["confirmatory"]["family"])
    assert {"F1 primary (H1a)", "F1 primary (H1a, 19 origins)", "F1-eq primary (H1b)", "F1-eq sphericity-free (H1b-sf)",
            "F1-min (minimum effect)", "F2 H1e", "F2 H2", "F2 H3"} <= fams
    assert set(R["heterogeneity"]["origins"]) == {"22", "19"}
    assert "headline_label" in R["rq1_decision"]


def test_host_status_handled(mock_run):
    """Host-national adjustment (setting 2026-10-01): host effect is secondary (never in a confirmatory family),
    the HX exclusion check is part of the robustness table and of the 'robust' label."""
    _, res, _ = mock_run
    R = res["results"]
    he = R["host_effect"]
    assert he["identified"].all() and set(he["status"]) == {"secondary / descriptive (not confirmatory)"}
    assert not R["confirmatory"]["estimand"].astype(str).str.contains("host").any()
    assert R["heterogeneity"]["host_adjusted"].all()
    rob = R["robustness"]
    assert (rob["check"] == "HX").sum() >= 2 and set(rob.loc[rob["check"] == "HX", "host_handling"]) == {"excluded"}
    assert "HX" in R["robust_labels"].columns
    assert R["host_sensitivity_deltas"]["is_base_country"].any()
    assert {"host_effect_logit", "sigma_A_fc_host_excluded"} <= set(R["bt_summary"].columns)
    ms = R["sensitivity_models"]
    assert (ms["term"] == "host_national").any()


def test_placebo_never_enters_main_analyses(mock_run):
    _, res, _ = mock_run
    R = res["results"]
    plc = set(PLACEBO_CODES)
    for name, col in (("coefficients", "nationality"), ("origin_deviations", "nationality"),
                      ("heterogeneity_effects", "nationality"), ("bt", "nationality"),
                      ("missing_by_nat", "nationality")):
        assert not (set(R[name][col]) & plc), name
    assert set(R["placebo"]["placebo_codes"].iloc[0].split("|")) == plc


def test_blind_is_default_and_outputs_no_origin_level_results(tmp_path):
    write_processed(simulate_all(DESIGN, PARAMS, seed=5, is_mock=True), tmp_path / "processed")
    res = run_analysis(tmp_path / "processed", tmp_path / "out", FAST, root=temp_root(tmp_path))
    assert res["blind"]
    forbidden = {"heterogeneity", "contrasts", "coefficients", "origin_deviations", "bt", "confirmatory",
                 "missing_by_nat", "text_flag_tests", "rq3", "placebo", "subregion_net", "rq1_decision",
                 "host_effect", "host_sensitivity_deltas", "bt_host_excluded", "bt_summary", "robustness",
                 "robust_labels"}
    names = {Path(p).stem for p in res["outputs"]}
    assert not (names & forbidden), names & forbidden
    assert not any("host" in k for k in res["results"]), "blind mode must not compute the host effect"
    for p in res["outputs"]:
        if p.endswith(".csv"):
            assert not any("host_effect" in c for c in read_csv(tmp_path / "out" / p).columns), p
    assert {"variance_components", "positive_control", "status", "design"} <= names
    dm = read_csv(tmp_path / "out" / "tables" / "diff_missing.csv")
    assert "arab_minus_deu_pp" not in dm.columns
    rates = read_csv(tmp_path / "out" / "tables" / "text_flag_rates.csv")
    assert "nationality_group" not in rates.columns
    assert "BLIND MODE" in (tmp_path / "out" / "summary.md").read_text(encoding="utf-8")


def test_exploratory_parse_is_stamped(tmp_path):
    d = tmp_path / "run__exploratory"
    write_processed(simulate_all(DESIGN, PARAMS, seed=6, is_mock=True, forced_choice=False, principle=False), d)
    res = run_analysis(d, tmp_path / "out", dict(FAST, make_figures=False), root=temp_root(tmp_path))
    assert any("EXPLORATORY PARSE" in n for n in res["notes"])
    assert PARSE_BANNER in (tmp_path / "out" / "tables" / "design.csv").read_text(encoding="utf-8")
    d2 = tmp_path / "plain"
    write_processed(simulate_all(DESIGN, PARAMS, seed=6, is_mock=True, forced_choice=False, principle=False), d2)
    (d2 / "parse_summary.json").write_text(json.dumps({"parse_mode": "exploratory"}), encoding="utf-8")
    run_analysis(d2, tmp_path / "out2", dict(FAST, make_figures=False), root=temp_root(tmp_path))
    assert PARSE_BANNER in (tmp_path / "out2" / "summary.md").read_text(encoding="utf-8")


def test_cli_quick_is_blind_by_default(tmp_path, capsys):
    write_processed(simulate_all(DESIGN, PARAMS, seed=7), tmp_path / "p")
    rc = cli_main(["--processed-dir", str(tmp_path / "p"), "--out-dir", str(tmp_path / "o"), "--quick"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "SYNTHETIC MOCK DATA" in out and "BLIND MODE" in out and "EXPLORATORY OVERRIDE" in out


def test_cli_unblind_mock_with_root(tmp_path, capsys):
    write_processed(simulate_all(DESIGN, PARAMS, seed=9, forced_choice=False, principle=False), tmp_path / "p")
    cfgp = tmp_path / "c.json"
    cfgp.write_text(json.dumps({"run_robustness": False, "make_figures": False}), encoding="utf-8")
    root = temp_root(tmp_path)
    rc = cli_main(["--processed-dir", str(tmp_path / "p"), "--out-dir", str(tmp_path / "o"), "--quick", "--unblind",
                   "--config", str(cfgp), "--root", str(root)])
    assert rc == 0 and "BLIND MODE" not in capsys.readouterr().out
    assert (root / "results" / "unblinding_log.jsonl").exists()


def test_cli_rejects_path_keys_in_config(tmp_path, capsys):
    write_processed(simulate_all(DESIGN, PARAMS, seed=9, forced_choice=False, principle=False), tmp_path / "p")
    cfgp = tmp_path / "c.json"
    cfgp.write_text(json.dumps({"unblinding_log": str(tmp_path / "x.jsonl")}), encoding="utf-8")
    rc = cli_main(["--processed-dir", str(tmp_path / "p"), "--out-dir", str(tmp_path / "o"), "--config", str(cfgp)])
    assert rc == 4 and "not allowed" in capsys.readouterr().err


def test_cli_schema_error_exit_code(tmp_path, capsys):
    tabs = simulate_all(DESIGN, PARAMS, seed=8, forced_choice=False, principle=False)
    tabs["evaluations"] = tabs["evaluations"].drop(columns=["clone_type"])
    write_processed(tabs, tmp_path / "p")
    rc = cli_main(["--processed-dir", str(tmp_path / "p"), "--out-dir", str(tmp_path / "o"), "--quick"])
    assert rc == 2 and "SCHEMA ERROR" in capsys.readouterr().err
