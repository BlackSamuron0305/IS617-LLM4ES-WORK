"""The three cost measures of experiment/inputs/costs/README.md, from the tables in results/<name>/.

Illustrations of model behaviour, never forecasts. Reads by_country.csv and by_savings.csv (written by
pipeline.analysis.summarize), writes costs.csv next to them and prints the figures.

1. Savings a passport costs: the gap in score points between a nationality and the best-scored one
   (block 1), divided by the rise of the score per step of 1.5 times the savings (AED 3,000 to 4,500, the
   first step above the threshold), turned into dirhams from a starting amount of AED 3,000. Only meaningful
   for a model whose score reacts to savings (a rise of at least 1 point per step).
2. Fees lost per 1,000 identical applications: the share of scores below 20 (refusal line) and below 50 (doubt
   line), difference to the best-scored nationality, times 1,000, times EUR 90 (fee, not refunded).
3. Applications sent to a closer look: the share of scores below 50 (band 20 to 49 and below).

Usage:
    python -m pipeline.analysis.costs --name audited_models
"""

import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path

from pipeline.core.common import ROOT, write_csv

FEE_EUR = 90
START_AED = 3000
STEP = 1.5


def read(path):
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--name", default="audited_models")
    args = parser.parse_args(argv)
    res = ROOT / "results" / args.name
    country = [r for r in read(res / "by_country.csv") if r["block"] == "1" and r["variant"] == "base" and r["visa_required"] == "yes" and r["group"] == "arab"]
    savings = read(res / "by_savings.csv")
    out = []
    for model in sorted({r["model"] for r in country}):
        s = {int(r["savings_aed"]): float(r["centred_mean"]) for r in savings if r["model"] == model}
        slope = s[4500] - s[3000]  # points per step of 1.5 times the savings, first step above the threshold
        rows = [r for r in country if r["model"] == model]
        best = max(rows, key=lambda r: float(r["centred_mean"]))
        print(f"\n{model}: score rises {slope:+.2f} points when the savings go from AED 3,000 to 4,500")
        for r in sorted(rows, key=lambda r: float(r["centred_mean"]))[:5]:
            gap = float(best["centred_mean"]) - float(r["centred_mean"])
            aed = ""
            if slope >= 1.0:
                steps = gap / slope
                aed = round(START_AED * (STEP ** steps - 1))
            fees20 = (float(r["share_lt20"]) - float(best["share_lt20"])) * 1000 * FEE_EUR
            fees50 = (float(r["share_lt50"]) - float(best["share_lt50"])) * 1000 * FEE_EUR
            out.append({"model": model, "country": r["country"], "best_country": best["country"], "gap_points": round(gap, 2),
                        "score_step_points": round(slope, 2), "savings_cost_aed": aed,
                        "fees_lost_per_1000_lt20_eur": round(fees20), "fees_lost_per_1000_lt50_eur": round(fees50),
                        "share_lt50": r["share_lt50"]})
            print(f"  {r['country']:12} gap to {best['country']} {gap:4.2f} points; savings cost "
                  f"{'AED ' + str(aed) if aed != '' else 'not defined (score does not react to savings)'}; "
                  f"fees per 1,000: EUR {fees20:,.0f} (below 20), EUR {fees50:,.0f} (below 50)")
    write_csv(res / "costs.csv", out, list(out[0]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
