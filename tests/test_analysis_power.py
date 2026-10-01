"""Smoke tests for analysis/power_analysis.py (both engines, placeholder warning, output files)."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def _load():
    spec = importlib.util.spec_from_file_location("power_analysis", ROOT / "analysis" / "power_analysis.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_fast_engine_runs_and_warns(tmp_path, capsys):
    pa = _load()
    out = tmp_path / "p.csv"
    rc = pa.main(["--engine", "fast", "--n-sims", "40", "--cvs", "8", "16", "--reps", "1", "--sd-at", "3",
                  "--sesoi", "1", "--out", str(out)])
    assert rc == 0
    printed = capsys.readouterr().out
    assert "PLACEHOLDER" in printed
    lines = out.read_text(encoding="utf-8").splitlines()
    assert lines[0].startswith("# WARNING") and "PLACEHOLDER" in lines[0]
    df = pd.read_csv(out, comment="#")
    assert list(df["cvs_per_occupation"]) == [8, 16]
    assert df["power_H1a"].iloc[1] >= df["power_H1a"].iloc[0] - 0.1      # more CVs, not less power
    assert (df["size_H1a"] <= 0.2).all()
    assert df["mean_se_delta"].iloc[1] < df["mean_se_delta"].iloc[0]
    assert out.with_suffix(".json").exists()


def test_schema_and_fast_engines_agree_on_precision(tmp_path):
    pa = _load()
    common = ["--n-sims", "8", "--cvs", "8", "--reps", "1", "--seed", "3"]
    pa.main(["--engine", "fast", *common, "--out", str(tmp_path / "f.csv")])
    pa.main(["--engine", "schema", *common, "--out", str(tmp_path / "s.csv")])
    f = pd.read_csv(tmp_path / "f.csv", comment="#")["mean_se_delta"].iloc[0]
    s = pd.read_csv(tmp_path / "s.csv", comment="#")["mean_se_delta"].iloc[0]
    assert abs(f - s) / s < 0.15


def test_pilot_json_replaces_placeholders(tmp_path, capsys):
    pa = _load()
    js = tmp_path / "vc.json"
    js.write_text('{"is_mock": true, "pooled": {"overall_fit": {"sd_at": 1.5, "sd_atk": 0.5, "sd_eps": 4.0,'
                  ' "rho_eps": 0.1, "sd_cv": 5.0, "sd_ak": 0.5, "grand_mean": 60}}, "upper": {"overall_fit":'
                  ' {"sd_at": 1.8, "sd_atk": 0.6, "sd_eps": 4.5}}}', encoding="utf-8")
    pa.main(["--engine", "fast", "--n-sims", "5", "--cvs", "8", "--reps", "1", "--pilot-json", str(js),
             "--out", str(tmp_path / "o.csv")])
    printed = capsys.readouterr().out
    assert "SYNTHETIC" in printed and "'sd_at': 1.8" in printed
    assert "PLACEHOLDER values" not in printed
