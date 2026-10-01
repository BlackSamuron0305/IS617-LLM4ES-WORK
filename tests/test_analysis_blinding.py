"""Blinding gate, confirmatory settings, override detection and unblinding log (review H1, round-2 N1, L12).

Freeze validity is tested in temporary git repositories.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path

import pytest

from hiringaudit.analysis import MOCK_BANNER, OVERRIDE_BANNER, UnblindingError, run_analysis
from hiringaudit.analysis.settings import (PACKAGE_ROOT, blind_requested, check_unblinding, provenance,
                                           resolve_config, sha256_text)
from hiringaudit.analysis.simulate import SimDesign, SimParams, simulate_all, write_processed

DESIGN = SimDesign(models=("m",), eval_conditions=("baseline",), cvs_per_occupation=4,
                   tier_pattern=("strong", "adequate", "adequate", "borderline"), repetitions=1,
                   variants=("k1", "k2"))
FAST = dict(n_boot=29, n_perm=99, n_perm_secondary=29, n_boot_bt=9, n_perm_bt=0, concordance_splits=3,
            n_cal=19, n_boot_cal=9, n_boot_vc=9, run_mixedlm=False, run_gee=False, run_robustness=False,
            make_figures=False)
PREREG = b"# Preregistration\r\nfrozen text\r\n"


def _git(root: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(root), "-c", "user.name=t", "-c", "user.email=t@t", *args],
                   check=True, capture_output=True)


def make_root(tmp_path: Path, *, prereg: bytes = PREREG, freeze: str | None = "auto", git: bool = True,
              commit: tuple[str, ...] = ("preregistration.md", "config/prereg_freeze.json",
                                         "config/analysis_settings.csv")) -> Path:
    root = tmp_path / "repo"
    (root / "config").mkdir(parents=True)
    shutil.copy(PACKAGE_ROOT / "config" / "analysis_settings.csv", root / "config")
    shutil.copy(PACKAGE_ROOT / "config" / "country_covariates.csv", root / "config")
    (root / "preregistration.md").write_bytes(prereg)
    if freeze is not None:
        h = hashlib.sha256(prereg.replace(b"\r\n", b"\n")).hexdigest() if freeze == "auto" else freeze
        (root / "config" / "prereg_freeze.json").write_text(json.dumps({"preregistration_sha256": h}),
                                                             encoding="utf-8")
    if git:
        _git(root, "init", "-q")
        files = [f for f in commit if (root / f).exists()]
        if files:
            _git(root, "add", *files)
            _git(root, "commit", "-q", "-m", "freeze")
    return root


def _data(tmp_path: Path, mock: bool = False) -> Path:
    d = tmp_path / ("mock" if mock else "real")
    write_processed(simulate_all(DESIGN, SimParams(), seed=1, is_mock=mock, forced_choice=False, principle=False), d)
    return d


# ----------------------------------------------------------------- config handling
def test_hash_normalises_line_endings(tmp_path):
    a, b = tmp_path / "a.md", tmp_path / "b.md"
    a.write_bytes(b"x\r\ny\r\n")
    b.write_bytes(b"x\ny\n")
    assert sha256_text(a) == sha256_text(b) == hashlib.sha256(b"x\ny\n").hexdigest()


def test_blind_is_default():
    cfg, _ = resolve_config(None)
    assert blind_requested(cfg)
    assert not blind_requested(resolve_config({"unblind": True})[0])
    assert blind_requested(resolve_config({"unblind": True, "blind": True})[0])


@pytest.mark.parametrize("key", ["repo_root", "unblinding_log", "confirmatory_config", "r4_processed_dir"])
def test_path_keys_cannot_be_set_in_config(key):
    with pytest.raises(ValueError, match=f"not allowed: '{key}'"):
        resolve_config({key: "somewhere"})


def test_unknown_key_rejected():
    with pytest.raises(ValueError, match="unknown analysis config key"):
        resolve_config({"sesio": 1})


def test_confirmatory_overrides_detected(tmp_path):
    root = make_root(tmp_path)
    cfg, info = resolve_config(None, root)
    assert cfg["sesoi"]["overall_fit"] == 1.0 and info["overrides"] == [] and info["confirmatory_committed"]
    _, info2 = resolve_config({"sesoi": {"overall_fit": 2.0}, "n_boot": 10, "make_figures": False}, root)
    assert info2["overrides"] == ["n_boot", "sesoi.overall_fit"]
    assert resolve_config({"sesoi": {"overall_fit": 1.0}}, root)[1]["overrides"] == []   # same value


def test_modified_or_uncommitted_confirmatory_file_is_an_override(tmp_path):
    root = make_root(tmp_path)
    y = root / "config" / "analysis_settings.csv"
    text = y.read_text(encoding="utf-8")
    assert "sesoi.overall_fit,1.0,float" in text
    y.write_text(text.replace("sesoi.overall_fit,1.0,float", "sesoi.overall_fit,3.0,float"), encoding="utf-8")
    cfg, info = resolve_config(None, root)
    assert cfg["sesoi"]["overall_fit"] == 3.0
    assert any("differs from the committed version" in o for o in info["overrides"])
    root2 = make_root(tmp_path / "b", git=False)
    assert any("not committed" in o or "git" in o for o in resolve_config(None, root2)[1]["overrides"])


# ----------------------------------------------------------------- freeze validity
def test_valid_freeze_unblinds_real_data_and_logs(tmp_path):
    root = make_root(tmp_path)
    gate = check_unblinding(root, all_mock=False)
    assert gate["freeze_ok"], gate["reason"]
    res = run_analysis(_data(tmp_path), tmp_path / "out", dict(FAST, unblind=True), root=root)
    assert not res["blind"] and not res["mock"]
    entry = json.loads((root / "results" / "unblinding_log.jsonl").read_text(encoding="utf-8").splitlines()[-1])
    assert entry["freeze_ok"] and entry["prereg_sha256"] == gate["prereg_sha256"] and not entry["all_rows_mock"]
    summary = (tmp_path / "out" / "summary.md").read_text(encoding="utf-8")
    assert MOCK_BANNER not in summary and "freeze valid: True" in summary
    first = (tmp_path / "out" / "tables" / "heterogeneity.csv").read_text(encoding="utf-8").splitlines()[0]
    assert first == f"# {OVERRIDE_BANNER}"                    # FAST overrides the resampling counts


@pytest.mark.parametrize("case, match", [
    ("no_freeze", "prereg_freeze.json not found"),
    ("freeze_uncommitted", "prereg_freeze.json is not committed"),
    ("prereg_uncommitted", "preregistration.md is not committed"),
    ("prereg_edited", "differs from the committed version"),
    ("stale_hash", "hash mismatch"),
    ("markers", "unresolved markers"),
    ("confirmatory_edited", "analysis_settings.csv differs"),
    ("no_git", "not committed"),
])
def test_invalid_freeze_refused_for_real_data(tmp_path, case, match):
    kw = {}
    if case == "no_freeze":
        kw["freeze"] = None
    elif case == "freeze_uncommitted":
        kw["commit"] = ("preregistration.md", "config/analysis_settings.csv")
    elif case == "prereg_uncommitted":
        kw["commit"] = ("config/prereg_freeze.json", "config/analysis_settings.csv")
    elif case == "stale_hash":
        kw["freeze"] = "0" * 64
    elif case == "markers":
        kw["prereg"] = b"# Prereg\n| SESOI | `[TEAM DECISION REQUIRED BEFORE FREEZE]` |\n"
    elif case == "no_git":
        kw["git"] = False
    root = make_root(tmp_path, **kw)
    if case == "prereg_edited":
        (root / "preregistration.md").write_bytes(PREREG + b"late edit\n")
        h = hashlib.sha256((PREREG + b"late edit\n").replace(b"\r\n", b"\n")).hexdigest()
        (root / "config" / "prereg_freeze.json").write_text(json.dumps({"preregistration_sha256": h}),
                                                             encoding="utf-8")
    if case == "confirmatory_edited":
        y = root / "config" / "analysis_settings.csv"
        y.write_text(y.read_text(encoding="utf-8").replace("significance level", "Significance level"),
                     encoding="utf-8")
    with pytest.raises(UnblindingError, match=match):
        run_analysis(_data(tmp_path), tmp_path / "out", dict(FAST, unblind=True), root=root)
    assert not (root / "results" / "unblinding_log.jsonl").exists()


def test_mock_only_data_keeps_exemption(tmp_path):
    root = make_root(tmp_path, freeze=None, git=False)
    res = run_analysis(_data(tmp_path, mock=True), tmp_path / "out", dict(FAST, unblind=True), root=root)
    assert not res["blind"] and res["mock"]
    entry = json.loads((root / "results" / "unblinding_log.jsonl").read_text(encoding="utf-8").splitlines()[-1])
    assert entry["all_rows_mock"] and not entry["freeze_ok"]


def test_blind_real_data_needs_no_freeze_and_writes_no_log(tmp_path):
    root = make_root(tmp_path, freeze=None)
    res = run_analysis(_data(tmp_path), tmp_path / "out", dict(FAST), root=root)
    assert res["blind"] and not (root / "results" / "unblinding_log.jsonl").exists()


def test_blind_run_with_committed_settings_has_no_override_stamp(tmp_path):
    root = make_root(tmp_path)
    res = run_analysis(_data(tmp_path, mock=True), tmp_path / "out", {"make_figures": False, "n_boot_vc": 200},
                       root=root)
    assert res["blind"] and not any("EXPLORATORY OVERRIDE" in n for n in res["notes"])
    head = (tmp_path / "out" / "tables" / "design.csv").read_text(encoding="utf-8").splitlines()[:2]
    assert head[0] == f"# {MOCK_BANNER}" and not head[1].startswith("#")


def test_provenance_records_code_hash():
    p = provenance(PACKAGE_ROOT)
    assert len(p["analysis_code_sha256"]) == 64 and "code_git_commit" in p
