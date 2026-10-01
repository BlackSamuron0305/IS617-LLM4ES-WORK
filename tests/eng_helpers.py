"""Shared helpers for the engineering tests (not a conftest, so the analysis tests stay independent).

The repository's two stimulus tables, config/ and prompts/ are used read-only;
tests that edit inputs work on copies in a temporary directory. Run outputs
always go to temporary directories.
"""

from __future__ import annotations

import csv
import shutil
from pathlib import Path

import pytest

from hiringaudit.paths import ProjectPaths

REPO = Path(__file__).resolve().parents[1]


def make_paths(tmp: Path) -> ProjectPaths:
    """Repo config/prompts/stimuli, tmp data/results."""
    return ProjectPaths.from_root(REPO).with_overrides(data_dir=tmp / "data", results_dir=tmp / "results")


def copy_stimuli(tmp: Path, paths: ProjectPaths) -> ProjectPaths:
    """A writable copy of stimuli/ (the two tables, the CV template, jobs, base countries, building blocks)."""
    dst = tmp / "stimuli_copy"
    shutil.copytree(REPO / "stimuli", dst)
    return paths.with_overrides(stimuli_dir=dst)


def copy_config(tmp: Path, paths: ProjectPaths) -> ProjectPaths:
    """A writable copy of config/ (for tests that edit inputs)."""
    dst = tmp / "config_copy"
    shutil.copytree(REPO / "config", dst)
    return paths.with_overrides(config_dir=dst)


def make_root_copy(tmp: Path) -> Path:
    """A self-contained repo root (config, prompts, stimuli) for CLI tests."""
    root = tmp / "root"
    for d in ("config", "prompts", "stimuli"):
        shutil.copytree(REPO / d, root / d)
    (root / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")
    return root


def read_table(path: Path) -> tuple[list[str], list[dict]]:
    with open(path, encoding="utf-8", newline="") as fh:
        r = csv.DictReader(fh)
        return list(r.fieldnames), [dict(x) for x in r]


def write_table(path: Path, columns: list[str], rows: list[dict]) -> None:
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=columns, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def edit_cv_row(paths: ProjectPaths, cv_id: str, **cells) -> None:
    cols, rows = read_table(paths.cv_table_file)
    for r in rows:
        if r["cv_id"] == cv_id:
            r.update(cells)
    write_table(paths.cv_table_file, cols, rows)


def tiny_config(**overrides) -> dict:
    """A small mock experiment covering every condition (a few hundred calls)."""
    cfg = {
        "experiment_id": "mock_unit",
        "occupations": ["software_developer"],
        "base_cvs": {"software_developer": ["swdev_01", "swdev_02", "swdev_04", "swdev_05"]},
        "nationalities": ["DEU", "EGY", "SYR", "POL", "TUR", "NONE", "URY", "MWI"],   # URY, MWI = placebo
        "models": ["mock"],
        "prompt_variants": ["k1", "k2"],
        "conditions": {
            "baseline": {"enabled": True, "repetitions": 2},
            "neutrality": {"enabled": True, "repetitions": 1},
            "forced_choice": {"enabled": True, "repetitions": 1},
            "forced_choice_neutrality": {"enabled": True, "repetitions": 1},
            "principle_probe": {"enabled": True, "repetitions": 1, "contexts": ["generic"],
                                "items": ["P01", "R01", "C01"]},
        },
        "forced_choice_design": {"tiers": ["strong", "adequate"], "nationality_pairs": {"n_cycles": 1, "copies": 1}},
        "retry": {"max_attempts": 3, "backoff_base_s": 0.0, "backoff_max_s": 0.0, "max_consecutive_api_errors": 1000},
        "stop_rule": {"enabled": False},   # the failure rates below are deliberately high
        "mock": {"effect_pattern": "alphabetical_ramp", "effect_amplitude": 8.0,
                 "rates": {"malformed_json": 0.05, "schema_violation": 0.05, "refusal": 0.05, "empty": 0.05,
                           "api_error_retryable": 0.1, "api_error_fatal": 0.03, "code_fence": 0.2,
                           "leading_prose": 0.1}},
    }
    cfg.update(overrides)
    return cfg


@pytest.fixture
def stim_paths(tmp_path) -> ProjectPaths:
    return make_paths(tmp_path)
