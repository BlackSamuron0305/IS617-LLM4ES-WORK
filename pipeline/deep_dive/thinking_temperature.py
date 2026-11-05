"""Thinking on and other temperatures (branch bias-deep-dive, 2026-11-04). Exploratory; standard library only.

Two tables, both on block 1 of the base design (30 applicants x 26 nationalities x 3 wordings, repetition 1, five savings
levels as in the audited runs), always against the audited run of the same weights at temperature 0.7:

  thinking.csv     the same weights with thinking off (audited run) and with thinking on (qwen3-32b, qwen3-14b) or with
                   reasoning effort low and high (gpt-oss-120b)
  temperature.csv  the audited temperature 0.7 and the extra temperatures 0.0, 0.3, 1.0 and 1.5

Columns: answers read, answers that could not be read, mean score, spread of the scores (standard deviation), the savings
effect (mean score at the lowest minus at the highest savings level: does the model react to a real ground), the gap
between the highest and the lowest of the 21 Arab nationalities that need a visa with the label-shuffle chance range
(95th percentile) and p value, the mean score of Syria minus the other 20 with its 95% interval, and the mean score of
the rich, normal and poor group.

    python -m pipeline.deep_dive.thinking_temperature --name deep_dive/thinking_and_temperature
"""

import argparse
import csv
import random
import statistics
import sys
from collections import defaultdict
from pathlib import Path

from pipeline.core.common import DATA, ROOT, batch_dir, read_table, write_csv
from pipeline.deep_dive.significance_tests import SYRIA_OTHERS, gap_test, pair_test, selector

# (model family, setting label, batch, the sampling setting it stands for)
THINKING = [
    ("qwen3-32b", "thinking off (audited run)", "main_qwen3-32b"),
    ("qwen3-32b", "thinking on", "tt_think_qwen3-32b-think"),
    ("qwen3-14b", "thinking off", "dd_fam_qwen3-14b"),
    ("qwen3-14b", "thinking on", "tt_think_qwen3-14b-think"),
    ("gpt-oss-120b", "reasoning effort low (audited extension)", "x2_gpt-oss-120b"),
    ("gpt-oss-120b", "reasoning effort high", "tt_think_gpt-oss-120b-high"),
]
TEMPERATURES = {  # family: [(temperature, batch)]
    "qwen3-32b": [(0.0, "tt_temp_qwen3-32b_t00"), (0.3, "tt_temp_qwen3-32b_t03"), (0.7, "main_qwen3-32b"),
                  (1.0, "tt_temp_qwen3-32b_t10"), (1.5, "tt_temp_qwen3-32b_t15")],
    "gemma-4-31b-it": [(0.0, "tt_temp_gemma-4-31b-it_t00"), (0.3, "tt_temp_gemma-4-31b-it_t03"), (0.7, "main_gemma-4-31b-it"),
                       (1.0, "tt_temp_gemma-4-31b-it_t10"), (1.5, "tt_temp_gemma-4-31b-it_t15")],
    "mistral-small-3.2-24b-instruct": [(0.0, "tt_temp_mistral-small-3.2-24b-instruct_t00"), (0.3, "tt_temp_mistral-small-3.2-24b-instruct_t03"),
                                       (0.7, "main_mistral-small-3.2-24b-instruct"), (1.0, "tt_temp_mistral-small-3.2-24b-instruct_t10"),
                                       (1.5, "tt_temp_mistral-small-3.2-24b-instruct_t15")],
    "qwen2.5-7b-instruct": [(0.0, "tt_temp_qwen2.5-7b-instruct_t00"), (0.3, "tt_temp_qwen2.5-7b-instruct_t03"), (0.7, "x2_qwen2.5-7b-instruct"),
                            (1.0, "tt_temp_qwen2.5-7b-instruct_t10"), (1.5, "tt_temp_qwen2.5-7b-instruct_t15")],
}


def rows_of(batch, data_root):
    """Block 1, base, repetition 1: every answer read, and the number planned (readable or not)."""
    path = batch_dir(Path(data_root), "processed", batch) / "answers.csv"
    if not path.exists():
        return None, 0
    allrows = [r for r in read_table(path) if r["block"] == "1" and r["variant"] == "base" and r["repetition"] == "1"
               and r["prompt_matches"] == "1"]
    ok = [r for r in allrows if r["parse_status"] == "ok"]
    for r in ok:
        r["s"] = float(r["visa_score"])
    return ok, len(allrows)


def summarize(batch, data_root, rng):
    ok, planned = rows_of(batch, data_root)
    if not ok:
        return None
    scores = [r["s"] for r in ok]
    low = [r["s"] for r in ok if r["savings"] == min(x["savings"] for x in ok)]
    high = [r["s"] for r in ok if r["savings"] == max(x["savings"] for x in ok)]
    arab = [r for r in ok if r["group"] == "arab" and r["visa_required"] == "yes"]
    gap = gap_test(arab, rng) if arab else None
    syria = pair_test(ok, selector(SYRIA_OTHERS[1]), selector(SYRIA_OTHERS[2]), rng)
    by_wealth = {w: statistics.fmean([r["s"] for r in arab if r["wealth_group"] == w] or [float("nan")])
                 for w in ("rich", "normal", "poor")}
    return {"answers_planned": planned, "answers_read": len(ok), "share_unreadable": round(1 - len(ok) / planned, 3),
            "mean_score": round(statistics.fmean(scores), 1), "sd_score": round(statistics.pstdev(scores), 1),
            "savings_effect": round(statistics.fmean(low) - statistics.fmean(high), 1) if low and high else "",
            "gap_21": gap["gap"] if gap else "", "gap_chance_p95": gap["chance_p95"] if gap else "",
            "gap_p": gap["p"] if gap else "", "gap_lowest": gap["lowest"] if gap else "", "gap_highest": gap["highest"] if gap else "",
            "syria_minus_other_20": syria["diff"] if syria else "",
            "syria_ci_lo": syria["ci_lo"] if syria else "", "syria_ci_hi": syria["ci_hi"] if syria else "",
            "mean_rich": round(by_wealth["rich"], 1), "mean_normal": round(by_wealth["normal"], 1),
            "mean_poor": round(by_wealth["poor"], 1)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--name", default="deep_dive/thinking_and_temperature")
    parser.add_argument("--data-root", default=str(DATA))
    args = parser.parse_args(argv)
    rng = random.Random(617)
    thinking, temperature = [], []
    for family, label, batch in THINKING:
        res = summarize(batch, args.data_root, rng)
        if res:
            thinking.append({"model": family, "setting": label, "batch": batch, **res})
        print("thinking", family, label, bool(res), flush=True)
    for family, series in TEMPERATURES.items():
        for temp, batch in series:
            res = summarize(batch, args.data_root, rng)
            if res:
                temperature.append({"model": family, "temperature": temp, "batch": batch, **res})
            print("temperature", family, temp, bool(res), flush=True)
    out = ROOT / "results" / args.name
    for name, rows in (("thinking.csv", thinking), ("temperature.csv", temperature)):
        if rows:
            write_csv(out / name, rows, list(rows[0]))
    print(len(thinking), "thinking rows,", len(temperature), "temperature rows ->", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
