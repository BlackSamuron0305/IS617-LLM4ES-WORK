"""CLI: python -m hiringaudit.analysis --processed-dir DIR --out-dir DIR [--unblind] [--config JSON] [--quick].

Blind by default (A15). --unblind requires a frozen preregistration unless every input row is mock.
--quick and any --config key that changes a confirmatory setting stamp outputs "EXPLORATORY OVERRIDE".
"""

from __future__ import annotations

import argparse
import json
import sys

from .pipeline import BLIND_BANNER, run_analysis
from .schema import MOCK_BANNER, SchemaError
from .settings import OVERRIDE_BANNER, PARSE_BANNER, UnblindingError


def _ascii(s: str) -> str:
    return s.replace("—", "-")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m hiringaudit.analysis",
                                 description="Run the pre-registered analysis on processed tables (blind by default).")
    ap.add_argument("--processed-dir", required=True, help="directory with evaluations.csv etc.")
    ap.add_argument("--out-dir", required=True, help="output directory (tables/, figures/, summary.md)")
    ap.add_argument("--unblind", action="store_true",
                    help="unblinded analysis; real data require config/prereg_freeze.json matching preregistration.md")
    ap.add_argument("--config", help="optional JSON file with run settings (confirmatory keys => EXPLORATORY OVERRIDE)")
    ap.add_argument("--root", default=None,
                    help="project root holding config/, preregistration.md and results/ (default: this repository)")
    ap.add_argument("--quick", action="store_true",
                    help="small bootstrap/permutation counts, no mixed models (smoke runs; EXPLORATORY OVERRIDE)")
    a = ap.parse_args(argv)
    cfg = {}
    if a.config:
        with open(a.config, encoding="utf-8") as fh:
            cfg = json.load(fh)
    if a.quick:
        cfg.update(n_boot=199, n_perm=999, n_perm_secondary=199, n_boot_bt=49, n_perm_bt=19, n_cal=99,
                   n_boot_cal=49, n_boot_vc=49, concordance_splits=20, run_mixedlm=False)
    if a.unblind:
        cfg["unblind"] = True
    try:
        res = run_analysis(a.processed_dir, a.out_dir, cfg, root=a.root)
    except SchemaError as e:
        print(f"SCHEMA ERROR: {e}", file=sys.stderr)
        return 2
    except UnblindingError as e:
        print(f"UNBLINDING REFUSED: {e}", file=sys.stderr)
        return 3
    except (ValueError, RuntimeError) as e:
        print(f"ANALYSIS REFUSED: {e}", file=sys.stderr)
        return 4
    if res["mock"]:
        print(f"*** {_ascii(MOCK_BANNER)} ***")
    if any("EXPLORATORY OVERRIDE" in n for n in res["notes"]):
        print(f"*** {_ascii(OVERRIDE_BANNER)} ***")
    if any("EXPLORATORY PARSE" in n for n in res["notes"]):
        print(f"*** {_ascii(PARSE_BANNER)} ***")
    if res["blind"]:
        print(f"*** {BLIND_BANNER} ***")
    print(f"wrote {len(res['outputs'])} outputs to {a.out_dir} (see summary.md)")
    for n in res["notes"]:
        print(f"note: {_ascii(n)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
