"""Build stimuli/cvs.csv from the CV building blocks, the job ads and the base countries.

Inputs: stimuli/building_blocks/*.csv (the curated pools, fixed seed in
build_settings.csv), stimuli/jobs.csv and stimuli/base_countries.csv (with
stimuli/building_blocks/institutions.csv). This documents how the CV table was
built. After the build, stimuli/cvs.csv is the source of truth and may be edited
by hand; the experiment runtime never reads the building blocks. Re-running
refuses to overwrite the table unless --force is given.

Usage:
    PYTHONPATH=src python scripts/build_cv_table.py [--force]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hiringaudit.stimuli.build_table import build_cv_table  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", default=str(ROOT))
    ap.add_argument("--force", action="store_true", help="overwrite an existing stimuli/cvs.csv")
    args = ap.parse_args(argv)
    stimuli = Path(args.root) / "stimuli"
    try:
        cvs = build_cv_table(stimuli / "building_blocks", stimuli / "jobs.csv", stimuli / "base_countries.csv",
                             stimuli / "cvs.csv", force=args.force)
    except FileExistsError as e:
        print(f"REFUSED: {e}", file=sys.stderr)
        return 2
    print(f"wrote {len(cvs)} base CVs to {stimuli / 'cvs.csv'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
