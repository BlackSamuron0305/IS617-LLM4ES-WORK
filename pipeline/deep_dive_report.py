"""Tables for the deep-dive (branch bias-deep-dive): negative applicants, ablations, reference nationalities, Qwen family.

Reads data/processed/<batch>/answers.csv for the batches given and writes CSV tables and a markdown summary to
results/<name>/. Standard library only; exploratory (nothing here is a confirmatory test).

    negative.csv        per model, ground, nationality group: n, mean score, share below 20, share at 10 or less
    negative_effect.csv per model: the effect of the passport group on the score for the negative applicants (block 7)
                        and for the main applicants (block 1), and their difference
    ablation.csv        per model, variant: the spread of the 21 nationalities (one repetition) and Syria's effect
    reference.csv       per model, nationality of the reference variant: mean score
    family.csv          per model: gap, Syria effect and money step for blocks 1 and 7 (for the Qwen family curve)

Usage:
    python -m pipeline.deep_dive_report --batch dd_neg_qwen3-32b main_qwen3-32b ... --name dd
"""

import argparse
import statistics
import sys
from collections import defaultdict
from pathlib import Path

from pipeline.common import DATA, ROOT, read_table, write_csv

GROUPS = {
    "Syria": lambda r: r["country"] == "Syria",
    "poor (4)": lambda r: r["group"] == "arab" and r["wealth_group"] == "poor",
    "Gulf (5)": lambda r: r["group"] == "arab" and r["wealth_group"] == "rich" and r["visa_required"] == "yes",
    "normal (12)": lambda r: r["group"] == "arab" and r["wealth_group"] == "normal",
    "placebo (3)": lambda r: r["group"] == "placebo" and r["visa_required"] == "yes",
}


def mean(v):
    return statistics.fmean(v) if v else float("nan")


def load(batches, data_root):
    rows = []
    for batch in batches:
        path = Path(data_root) / "processed" / batch / "answers.csv"
        if path.exists():
            rows += [r for r in read_table(path) if r["parse_status"] == "ok" and r["prompt_matches"] == "1"]
    for r in rows:
        r["s"] = float(r["visa_score"])
    return rows


def centre(rows):
    cells = defaultdict(list)
    for r in rows:
        cells[(r["model_alias"], r["applicant_id"], r["savings"], r["wording"], r["repetition"], r["block"], r["variant"])].append(r)
    for c in cells.values():
        m = mean([x["s"] for x in c])
        for x in c:
            x["d"] = x["s"] - m


def group_effect(rows, block, variant="base"):
    # mean cell-centred score of each group of nationalities, in one block
    out = {}
    sel = [r for r in rows if r["block"] == block and r["variant"] == variant]
    for g, fn in GROUPS.items():
        v = [r["d"] for r in sel if fn(r)]
        out[g] = (mean(v), len(v))
    return out


def tables(rows, out_dir):
    centre(rows)
    models = sorted({r["model_alias"] for r in rows})
    neg, eff, abl, ref, fam = [], [], [], [], []
    for m in models:
        rs = [r for r in rows if r["model_alias"] == m]
        # negative applicants by ground and group
        by = defaultdict(list)
        for r in rs:
            if r["block"] == "7":
                for g, fn in GROUPS.items():
                    if fn(r):
                        by[(r["indicator"], g)].append(r["s"])
        for (ground, g), v in sorted(by.items()):
            neg.append({"model": m, "ground": ground, "group": g, "n": len(v), "mean": round(mean(v), 2),
                        "share_lt20": round(mean([x < 20 for x in v]), 3), "share_le10": round(mean([x <= 10 for x in v]), 3)})
        e7, e1 = group_effect(rs, "7"), group_effect(rs, "1")
        for g in GROUPS:
            eff.append({"model": m, "group": g, "effect_negative_block7": round(e7[g][0], 2), "n7": e7[g][1],
                        "effect_main_block1": round(e1[g][0], 2), "n1": e1[g][1],
                        "difference": round(e7[g][0] - e1[g][0], 2) if e7[g][1] and e1[g][1] else ""})
        # ablations: spread of the 21 nationalities and Syria's effect per variant (one repetition)
        for variant in sorted({r["variant"] for r in rs if r["block"] in ("1", "4")}):
            sel = [r for r in rs if r["variant"] == variant and r["block"] in ("1", "4") and r["repetition"] == "1"
                   and r["group"] == "arab" and r["visa_required"] == "yes"]
            if not sel:
                continue
            nat = defaultdict(list)
            for r in sel:
                nat[r["country"]].append(r["d"])
            means = [mean(v) for v in nat.values()]
            abl.append({"model": m, "variant": variant, "n": len(sel), "range": round(max(means) - min(means), 2),
                        "sd_of_means": round(statistics.stdev(means), 2) if len(means) > 1 else "",
                        "syria": round(mean(nat["Syria"]), 2) if nat.get("Syria") else "", "mean_score": round(mean([r["s"] for r in sel]), 2)})
        # reference nationalities
        for country in sorted({r["country"] for r in rs if r["variant"] == "reference_nationalities"}):
            v = [r["s"] for r in rs if r["variant"] == "reference_nationalities" and r["country"] == country]
            ref.append({"model": m, "country": country, "n": len(v), "mean": round(mean(v), 2)})
        # family curve numbers
        b1 = [r for r in rs if r["block"] == "1" and r["variant"] == "base" and r["group"] == "arab" and r["visa_required"] == "yes"]
        if b1:
            nat = defaultdict(list)
            for r in b1:
                nat[r["country"]].append(r["d"])
            means = {c: mean(v) for c, v in nat.items()}
            lvl = defaultdict(list)
            for r in rs:
                if r["block"] in ("1", "3") and r["variant"] == "base":
                    lvl[int(r["savings"])].append(r["s"])
            fam.append({"model": m, "n_block1": len(b1), "mean_score": round(mean([r["s"] for r in b1]), 2),
                        "gap_21": round(max(means.values()) - min(means.values()), 2), "syria": round(means.get("Syria", float("nan")), 2),
                        "somalia": round(means.get("Somalia", float("nan")), 2),
                        "money_step_3000_minus_2000": round(mean(lvl[3000]) - mean(lvl[2000]), 2) if lvl.get(3000) and lvl.get(2000) else ""})
    for name, rows_ in (("negative", neg), ("negative_effect", eff), ("ablation", abl), ("reference", ref), ("family", fam)):
        if rows_:
            write_csv(out_dir / f"{name}.csv", rows_, list(rows_[0]))
    return {"negative": len(neg), "effect": len(eff), "ablation": len(abl), "reference": len(ref), "family": len(fam)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--batch", required=True, nargs="+")
    parser.add_argument("--name", default="dd")
    parser.add_argument("--data-root", default=str(DATA))
    args = parser.parse_args(argv)
    rows = load(args.batch, args.data_root)
    if not rows:
        print("error: no readable answers in the batches given", file=sys.stderr)
        return 2
    out = ROOT / "results" / args.name
    print(tables(rows, out), "->", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
