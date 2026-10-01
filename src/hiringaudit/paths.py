"""Project directory layout. Every directory can be overridden (tests use tmp dirs)."""

from __future__ import annotations

import os
from dataclasses import dataclass, replace
from pathlib import Path


def find_repo_root(start: str | Path | None = None) -> Path:
    """Locate the repository root.

    Order: ``$HIRINGAUDIT_ROOT``; the first parent of ``start`` (default: cwd)
    containing ``pyproject.toml`` and ``stimuli/nationalities.csv``; finally the
    directory two levels above this package (``src/hiringaudit/..``).
    """
    env = os.environ.get("HIRINGAUDIT_ROOT")
    if env:
        return Path(env).resolve()
    here = Path(start or Path.cwd()).resolve()
    for p in [here, *here.parents]:
        if (p / "pyproject.toml").exists() and (p / "stimuli" / "nationalities.csv").exists():
            return p
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class ProjectPaths:
    root: Path
    config_dir: Path
    prompts_dir: Path
    stimuli_dir: Path
    data_dir: Path
    results_dir: Path

    @classmethod
    def from_root(cls, root: str | Path | None = None) -> "ProjectPaths":
        r = Path(root).resolve() if root else find_repo_root()
        return cls(
            root=r,
            config_dir=r / "config",
            prompts_dir=r / "prompts",
            stimuli_dir=r / "stimuli",
            data_dir=r / "data",
            results_dir=r / "results",
        )

    def with_overrides(self, **kwargs: str | Path) -> "ProjectPaths":
        return replace(self, **{k: Path(v) for k, v in kwargs.items()})

    # --- derived locations ---
    @property
    def nationalities_file(self) -> Path:
        return self.stimuli_dir / "nationalities.csv"

    @property
    def cv_table_file(self) -> Path:
        return self.stimuli_dir / "cvs.csv"

    @property
    def jobs_file(self) -> Path:
        return self.stimuli_dir / "jobs.csv"

    @property
    def base_countries_file(self) -> Path:
        return self.stimuli_dir / "base_countries.csv"

    @property
    def building_blocks_dir(self) -> Path:
        """CV building blocks: the input of scripts/build_cv_table.py (and of the
        title-bullet coherence check); institutions.csv is also the validator whitelist."""
        return self.stimuli_dir / "building_blocks"

    @property
    def institutions_file(self) -> Path:
        return self.building_blocks_dir / "institutions.csv"

    @property
    def cv_template_file(self) -> Path:
        return self.stimuli_dir / "cv_template.txt"

    @property
    def models_file(self) -> Path:
        return self.config_dir / "models.csv"

    @property
    def runs_file(self) -> Path:
        return self.config_dir / "runs.csv"

    @property
    def text_flags_file(self) -> Path:
        return self.config_dir / "text_flags.csv"

    @property
    def leak_terms_file(self) -> Path:
        return self.config_dir / "leak_terms.csv"

    @property
    def analysis_settings_file(self) -> Path:
        return self.config_dir / "analysis_settings.csv"

    @property
    def prompt_parts_file(self) -> Path:
        return self.prompts_dir / "prompt_parts.csv"

    @property
    def prompt_recipes_file(self) -> Path:
        return self.prompts_dir / "prompt_recipes.csv"

    @property
    def principle_items_file(self) -> Path:
        return self.prompts_dir / "principle_items.csv"

    def raw_run_dir(self, run_id: str) -> Path:
        return self.data_dir / "raw" / run_id

    def processed_run_dir(self, run_id: str) -> Path:
        return self.data_dir / "processed" / run_id

    def results_run_dir(self, run_id: str) -> Path:
        return self.results_dir / run_id
