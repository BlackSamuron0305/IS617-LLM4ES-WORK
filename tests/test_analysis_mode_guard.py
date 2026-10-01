"""Blind and unblinded analysis outputs must never share a directory."""

from __future__ import annotations

import pytest

from hiringaudit.analysis.pipeline import _refuse_mode_mixing


def _write_summary(d, blind: bool) -> None:
    d.mkdir(parents=True, exist_ok=True)
    (d / "summary.md").write_text(f"- is_mock rows present: True; blind mode: {blind}\n", encoding="utf-8")


def test_empty_dir_is_allowed(tmp_path):
    _refuse_mode_mixing(tmp_path / "out", blind=True)
    _refuse_mode_mixing(tmp_path / "out", blind=False)


@pytest.mark.parametrize("blind", [True, False])
def test_same_mode_rerun_is_allowed(tmp_path, blind):
    _write_summary(tmp_path, blind)
    _refuse_mode_mixing(tmp_path, blind=blind)


@pytest.mark.parametrize("previous, requested", [(True, False), (False, True)])
def test_mode_mixing_is_refused(tmp_path, previous, requested):
    _write_summary(tmp_path, previous)
    with pytest.raises(RuntimeError, match="refusing"):
        _refuse_mode_mixing(tmp_path, blind=requested)


def test_blind_refuses_non_empty_dir_without_summary(tmp_path):
    stale = tmp_path / "out" / "tables"
    stale.mkdir(parents=True)
    (stale / "origin_deviations.csv").write_text("x\n1\n", encoding="utf-8")   # left by a crashed unblinded run
    with pytest.raises(RuntimeError, match="no summary.md"):
        _refuse_mode_mixing(tmp_path / "out", blind=True)
    _refuse_mode_mixing(tmp_path / "out", blind=False)          # an unblinded run may overwrite it


def test_blind_allows_existing_empty_dirs(tmp_path):
    (tmp_path / "out" / "tables").mkdir(parents=True)
    (tmp_path / "out" / "figures").mkdir(parents=True)
    _refuse_mode_mixing(tmp_path / "out", blind=True)


def test_run_analysis_blind_refuses_stale_directory(tmp_path):
    import shutil

    from hiringaudit.analysis import run_analysis
    from hiringaudit.analysis.settings import PACKAGE_ROOT
    from hiringaudit.analysis.simulate import SimDesign, SimParams, simulate_all, write_processed

    root = tmp_path / "root"
    (root / "config").mkdir(parents=True)
    shutil.copy(PACKAGE_ROOT / "config" / "analysis_settings.csv", root / "config")
    d = SimDesign(cvs_per_occupation=2, tier_pattern=("adequate",), repetitions=1, variants=("k1",))
    write_processed(simulate_all(d, SimParams(), seed=1, forced_choice=False, principle=False), tmp_path / "p")
    (tmp_path / "out").mkdir()
    (tmp_path / "out" / "heterogeneity.csv").write_text("stale\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="no summary.md"):
        run_analysis(tmp_path / "p", tmp_path / "out", {"make_figures": False}, root=root)
