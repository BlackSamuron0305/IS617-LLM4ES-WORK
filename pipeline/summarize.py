"""Summary tables of the parsed batches, small enough to copy off the cluster.

Reads data/processed/<batch>/answers.csv (and answers_judged_<judge>.csv where it exists) and writes
CSV tables to results/<name>/. Standard library only; calls no model. The tables describe; the
tests of experiment/analysis_plan.md are in pipeline/analyze_main.py.

    by_country.csv         model, block, nationality: n, mean score, sd, share below 20 / below 50 / at 80 or more,
                           mean after removing the cell mean (the effect of the passport alone)
    by_profile.csv         model, block, applicant profile and indicator: mean score
    by_savings.csv         model, savings level: mean score after removing the cell mean (blocks 1 and 3)
    by_variant.csv         model, variant: mean score, spread (sd of the 21 nationality means, cell-centred)
    unreadable.csv         model, nationality: answers that could not be read
    judged_by_country.csv  model, block, nationality: share of reasons with each judge code (if judged)

Usage:
    python -m pipeline.summarize --batch main_qwen3-32b main_gemma-4-31b-it --name main
"""

import argparse
import csv
import statistics
import sys
from collections import defaultdict
from pathlib import Path

from pipeline.common import DATA, ROOT, read_table, write_csv
from pipeline.build_runs import load_variants
from pipeline.judge_build import JUDGE_CODES
from pipeline.pilot_report import money_step

CELL = ("model_alias", "applicant_id", "savings", "wording", "repetition", "variant", "block")


def read_batches(batches, data_root):
    rows = []
    for batch in batches:
        path = Path(data_root) / "processed" / batch / "answers.csv"
        if not path.exists():
            raise FileNotFoundError(path)
        rows += read_table(path)
    return rows


def mean(v):
    return statistics.fmean(v) if v else float("nan")


def sd(v):
    return statistics.stdev(v) if len(v) > 1 else float("nan")


def centre(rows, key=CELL):
    # Adds "centred": the score minus the mean of its cell (same applicant, savings, wording, repetition, block and variant).
    cells = defaultdict(list)
    for r in rows:
        cells[tuple(r[k] for k in key)].append(r)
    for cell in cells.values():
        m = mean([r["score"] for r in cell])
        for r in cell:
            r["centred"] = r["score"] - m


def tables(rows, out_dir, judged_rows):
    ok = [r for r in rows if r["parse_status"] == "ok" and r["prompt_matches"] == "1"]
    for r in ok:
        r["score"] = float(r["visa_score"])
    centre(ok)
    by_model = defaultdict(list)
    for r in ok:
        by_model[r["model_alias"]].append(r)

    out = {"by_country": [], "by_profile": [], "by_savings": [], "by_variant": [], "unreadable": []}
    for model, rs in sorted(by_model.items()):
        groups = defaultdict(list)
        for r in rs:
            groups[(r["block"], r["variant"], r["country"])].append(r)
        for (block, variant, country), g in sorted(groups.items()):
            s = [r["score"] for r in g]
            out["by_country"].append({
                "model": model, "block": block, "variant": variant, "country": country, "group": g[0]["group"],
                "wealth_group": g[0]["wealth_group"], "visa_required": g[0]["visa_required"], "n": len(g),
                "mean": round(mean(s), 3), "sd": round(sd(s), 3), "share_lt20": round(mean([x < 20 for x in s]), 4),
                "share_lt50": round(mean([x < 50 for x in s]), 4), "share_ge80": round(mean([x >= 80 for x in s]), 4),
                "centred_mean": round(mean([r["centred"] for r in g]), 3)})
        prof = defaultdict(list)
        for r in rs:
            prof[(r["block"], r["variant"], r["file_profile"], r["indicator"])].append(r["score"])
        for (block, variant, fp, ind), s in sorted(prof.items()):
            out["by_profile"].append({"model": model, "block": block, "variant": variant, "file_profile": fp,
                                      "indicator": ind, "n": len(s), "mean": round(mean(s), 3)})
        # The money effect: within one applicant x nationality x wording, over the five savings levels.
        for level, (value, n) in money_step([r for r in rs if r["variant"] == "base" and r["block"] in ("1", "3")]).items():
            out["by_savings"].append({"model": model, "savings_aed": level, "n": n, "centred_mean": round(value, 3)})
        for (block, variant), _ in sorted({(b, v): 0 for (b, v, _c) in groups}.items()):
            g = [r for r in rs if r["block"] == block and r["variant"] == variant
                 and r["group"] == "arab" and r["visa_required"] == "yes"]
            by_c = defaultdict(list)
            for r in g:
                by_c[r["country"]].append(r["centred"])
            means = [mean(v) for v in by_c.values()]
            out["by_variant"].append({"model": model, "block": block, "variant": variant, "n": len(g),
                                      "mean": round(mean([r["score"] for r in rs if r["block"] == block and r["variant"] == variant]), 3),
                                      "spread_sd": round(sd(means), 3), "range": round(max(means) - min(means), 3) if means else ""})
    bad = defaultdict(int)
    for r in rows:
        if r["parse_status"] != "ok":
            bad[(r["model_alias"], r["country"], r["parse_status"])] += 1
    out["unreadable"] = [{"model": m, "country": c, "status": s, "n": n} for (m, c, s), n in sorted(bad.items())]
    for name, rows_ in out.items():
        if rows_:
            write_csv(out_dir / f"{name}.csv", rows_, list(rows_[0]))
    judged = [r for r in judged_rows if r.get("judge_status") == "ok"]
    if judged:
        g = defaultdict(list)
        for r in judged:
            g[(r["model_alias"], r["block"], r["country"])].append(r)
        table = [{"model": m, "block": b, "country": c, "n": len(rs), **{code: round(mean([float(r[code]) for r in rs]), 4) for code in JUDGE_CODES}}
                 for (m, b, c), rs in sorted(g.items())]
        write_csv(out_dir / "judged_by_country.csv", table, list(table[0]))
    return {name: len(r) for name, r in out.items()}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--batch", required=True, nargs="+")
    parser.add_argument("--name", default="main", help="results go to results/<name>/")
    parser.add_argument("--judge", default="olmo-3.1-32b-instruct")
    parser.add_argument("--data-root", default=str(DATA))
    args = parser.parse_args(argv)
    try:
        rows = read_batches(args.batch, args.data_root)
    except FileNotFoundError as exc:
        print(f"error: no parsed answers at {exc}", file=sys.stderr)
        return 2
    judged = []
    for batch in args.batch:
        path = Path(args.data_root) / "processed" / batch / f"answers_judged_{args.judge}.csv"
        if path.exists():
            judged += read_table(path)
    out_dir = ROOT / "results" / args.name
    print(tables(rows, out_dir, judged), "->", out_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
