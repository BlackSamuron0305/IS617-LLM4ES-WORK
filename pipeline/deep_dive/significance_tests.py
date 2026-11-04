"""Significance tests for the deep-dive (branch bias-deep-dive). Exploratory; standard library only.

Two kinds of test, both on the scores of identical applications that differ only in the nationality:

  pairs.csv  per model and variant: a named comparison of two nationalities (or two groups), for example
             Germany - India or conflict countries - peaceful countries. The difference is taken inside each
             cell (same applicant, savings, wording, repetition), averaged over wordings and repetitions, and
             the unit of the test is the applicant x savings pair. Columns: mean difference in score points,
             95% interval (bootstrap over those pairs) and a sign-flip p value.
  gaps.csv   per model and variant: the gap between the highest and the lowest of the 21 Arab nationalities that need
             a visa, and the gap that label shuffles inside each cell give by chance (the 95th percentile and the
             p value). With 5 repetitions the chance range is narrow, so a gap of 1 to 2 points can still be real;
             whether it matters is a separate question.

    python -m pipeline.deep_dive.significance_tests --batch main_qwen3-32b dd_rep_qwen3-32b_s0 ... --name deep_dive/significance_tests
"""

import argparse
import random
import statistics
import sys
from collections import defaultdict
from pathlib import Path

from pipeline.core.common import batch_dir, DATA, ROOT, read_table, write_csv

BOOT, FLIPS, SHUFFLES = 2000, 5000, 200

COMPARISONS = {
    "reference_nationalities": [
        ("Germany - India", {"c": "Germany"}, {"c": "India"}), ("Germany - Pakistan", {"c": "Germany"}, {"c": "Pakistan"}),
        ("United States - India", {"c": "United States"}, {"c": "India"}), ("United States - Philippines", {"c": "United States"}, {"c": "Philippines"}),
        ("Germany - Not stated", {"c": "Germany"}, {"c": "Not stated"}), ("Germany - Syria", {"c": "Germany"}, {"c": "Syria"}),
        ("Germany - Qatar", {"c": "Germany"}, {"c": "Qatar"}), ("Syria - Jordan", {"c": "Syria"}, {"c": "Jordan"}),
        ("Syria - Qatar", {"c": "Syria"}, {"c": "Qatar"}), ("Somalia - Jordan", {"c": "Somalia"}, {"c": "Jordan"}),
        ("Syria - India", {"c": "Syria"}, {"c": "India"}), ("Pakistan - India", {"c": "Pakistan"}, {"c": "India"})],
    "conflict_nationalities": [
        ("conflict (4) - peaceful (3)", {"g": "conflict"}, {"g": "peaceful"}), ("Syria - conflict (4)", {"c": "Syria"}, {"g": "conflict"}),
        ("Syria - peaceful (3)", {"c": "Syria"}, {"g": "peaceful"}), ("Somalia - conflict (4)", {"c": "Somalia"}, {"g": "conflict"}),
        ("Syria - Jordan", {"c": "Syria"}, {"c": "Jordan"}), ("Syria - Qatar", {"c": "Syria"}, {"c": "Qatar"}),
        ("Venezuela - peaceful (3)", {"c": "Venezuela"}, {"g": "peaceful"}), ("Germany - India", {"c": "Germany"}, {"c": "India"}),
        ("Afghanistan - Nepal", {"c": "Afghanistan"}, {"c": "Nepal"}), ("Ukraine - Vietnam", {"c": "Ukraine"}, {"c": "Vietnam"})],
}
SYRIA_OTHERS = ("Syria - the other 20", {"c": "Syria"}, {"c": "OTHERS21"})
GAP_VARIANTS = ("base", "no_nationality_line", "no_document_line", "home_country_line", "reason_first", "strict_officer", "lenient_officer",
                "fairness_first", "fairness_last", "reference_nationalities")


def mean(v):
    return statistics.fmean(v) if v else float("nan")


def load(batches, data_root):
    rows = []
    for batch in batches:
        path = batch_dir(Path(data_root), "processed", batch) / "answers.csv"
        if path.exists():
            rows += [r for r in read_table(path) if r["parse_status"] == "ok" and r["prompt_matches"] == "1"]
    for r in rows:
        r["s"] = float(r["visa_score"])
    return rows


def selector(spec):
    if "c" in spec and spec["c"] == "OTHERS21":
        return lambda r: r["group"] == "arab" and r["visa_required"] == "yes" and r["country"] != "Syria"
    if "c" in spec:
        return lambda r: r["country"] == spec["c"]
    return lambda r: r["group"] == spec["g"]


def pair_test(rows, fa, fb, rng):
    cells = defaultdict(lambda: ([], []))
    for r in rows:
        k = (r["applicant_id"], r["savings"], r["wording"], r["repetition"])
        if fa(r):
            cells[k][0].append(r["s"])
        elif fb(r):
            cells[k][1].append(r["s"])
    clusters = defaultdict(list)
    for (applicant, savings, _w, _rep), (a, b) in cells.items():
        if a and b:
            clusters[(applicant, savings)].append(mean(a) - mean(b))
    d = [mean(v) for v in clusters.values()]
    if len(d) < 5:
        return None
    est = mean(d)
    boots = sorted(mean(rng.choices(d, k=len(d))) for _ in range(BOOT))
    flips = sum(abs(mean([x if rng.random() < 0.5 else -x for x in d])) >= abs(est) - 1e-12 for _ in range(FLIPS))
    return {"n_pairs": len(d), "diff": round(est, 2), "ci_lo": round(boots[int(0.025 * BOOT)], 2), "ci_hi": round(boots[int(0.975 * BOOT) - 1], 2),
            "p": round((1 + flips) / (1 + FLIPS), 4)}


def gap_test(rows, rng):
    sel = [r for r in rows if r["group"] == "arab" and r["visa_required"] == "yes"]
    cells = defaultdict(list)
    for r in sel:
        cells[(r["applicant_id"], r["savings"], r["wording"], r["repetition"])].append(r)
    countries = sorted({r["country"] for r in sel})
    if len(countries) < 3:
        return None
    index = {c: i for i, c in enumerate(countries)}
    data = []
    for c in cells.values():
        m = mean([x["s"] for x in c])
        data.append([(index[x["country"]], x["s"] - m) for x in c])

    def gap(assign):
        tot, cnt = [0.0] * len(countries), [0] * len(countries)
        for cell, perm in assign:
            for (_i, d), j in zip(cell, perm):
                tot[j] += d
                cnt[j] += 1
        means = [t / n for t, n in zip(tot, cnt) if n]
        return max(means) - min(means), dict(zip(countries, [t / n if n else float("nan") for t, n in zip(tot, cnt)]))

    observed, means = gap([(cell, [i for i, _d in cell]) for cell in data])
    null = []
    for _ in range(SHUFFLES):
        assign = []
        for cell in data:
            labels = [i for i, _d in cell]
            rng.shuffle(labels)
            assign.append((cell, labels))
        null.append(gap(assign)[0])
    null.sort()
    lowest, highest = min(means, key=means.get), max(means, key=means.get)
    return {"n": len(sel), "gap": round(observed, 2), "chance_p95": round(null[int(0.95 * len(null)) - 1], 2),
            "p": round((1 + sum(x >= observed for x in null)) / (1 + SHUFFLES), 4), "lowest": lowest, "highest": highest}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--batch", nargs="+", required=True)
    parser.add_argument("--name", default="deep_dive/significance_tests")
    parser.add_argument("--data-root", default=str(DATA))
    parser.add_argument("--no-gaps", action="store_true", help="skip the (slow) label-shuffle test of the gaps")
    args = parser.parse_args(argv)
    rows = load(args.batch, args.data_root)
    if not rows:
        print("error: no readable answers in the batches given", file=sys.stderr)
        return 2
    rng = random.Random(617)
    pairs, gaps = [], []
    for model in sorted({r["model_alias"] for r in rows}):
        rs = [r for r in rows if r["model_alias"] == model]
        for variant in sorted({r["variant"] for r in rs}):
            vs = [r for r in rs if r["variant"] == variant and r["block"] in ("1", "4")]
            if not vs:
                continue
            comps = list(COMPARISONS.get(variant, [])) + ([SYRIA_OTHERS] if variant in GAP_VARIANTS and variant != "reference_nationalities" else [])
            for name, a, b in comps:
                res = pair_test(vs, selector(a), selector(b), rng)
                if res:
                    pairs.append({"model": model, "variant": variant, "comparison": name, **res})
            if not args.no_gaps and variant in GAP_VARIANTS and variant != "reference_nationalities":
                res = gap_test(vs, rng)
                if res:
                    gaps.append({"model": model, "variant": variant, **res})
            print(model, variant, len(vs), flush=True)
    out = ROOT / "results" / args.name
    if pairs:
        write_csv(out / "pairs.csv", pairs, list(pairs[0]))
    if gaps:
        write_csv(out / "gaps.csv", gaps, list(gaps[0]))
    print(len(pairs), "comparisons,", len(gaps), "gap tests ->", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
