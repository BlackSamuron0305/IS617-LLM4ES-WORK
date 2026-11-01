"""The confirmatory analysis of experiment/analysis_plan.md (H1 to H4), one model at a time.

Reads data/processed/<batch>/answers.csv (from parse_answers). Standard library only. It
describes and tests; it calls no model. Output of a mock batch is labelled and is never a result.

H1  spread among the nationalities that need a visa (block 1), permutation test
H2  order rich > normal > poor among the same countries, permutation test
H3  does the paragraph on nationality (block 2) reduce the spread, paired permutation test
H4  does the score fall when the funds are below the amount the rules ask for

Usage:
    python -m pipeline.analyze_main --batch main_qwen3-32b --permutations 10000
"""

import argparse
import random
import statistics
import sys
from collections import defaultdict
from pathlib import Path

from pipeline.common import DATA, read_table
from pipeline.pilot_report import LOW_LEVEL, MIN_MONEY_STEP, THRESHOLD_LEVEL, money_step

WEALTH_RANK = {"rich": 1, "normal": 2, "poor": 3}
SEED = 617


def load(batch, data_root, models=None):
    rows = read_table(Path(data_root) / "processed" / batch / "answers.csv")
    ok = [r for r in rows if r["parse_status"] == "ok" and r["prompt_matches"] == "1"]
    if models:
        ok = [r for r in ok if r["model_alias"] in models]
    for r in ok:
        r["score"] = float(r["visa_score"])
    return rows, ok


def sample(ok, block):
    # The Arab League nationalities that need a visa, in one block of the base design.
    return [r for r in ok if r["block"] == str(block) and r["variant"] == "base" and r["group"] == "arab"
            and r["visa_required"] == "yes"]


def centred(rows):
    # Score minus the mean of its cell (applicant, savings, wording, repetition): the applicant,
    # the wording and the repetition cancel, only the nationality is left.
    cells = defaultdict(list)
    for i, r in enumerate(rows):
        cells[(r["applicant_id"], r["savings"], r["wording"], r["repetition"])].append(i)
    values = [0.0] * len(rows)
    for idx in cells.values():
        centre = statistics.fmean(rows[i]["score"] for i in idx)
        for i in idx:
            values[i] = rows[i]["score"] - centre
    return values, list(cells.values())


def spread(values, labels):
    by = defaultdict(list)
    for v, label in zip(values, labels):
        by[label].append(v)
    means = {label: statistics.fmean(v) for label, v in by.items()}
    return statistics.stdev(means.values()), means


def ranks(values):
    order = sorted(range(len(values)), key=lambda i: values[i])
    out = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        for k in range(i, j + 1):
            out[order[k]] = (i + j) / 2 + 1
        i = j + 1
    return out


def spearman(x, y):
    rx, ry = ranks(x), ranks(y)
    mx, my = statistics.fmean(rx), statistics.fmean(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = (sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry)) ** 0.5
    return num / den if den else 0.0


def three_way_split(means):
    # Cut the sorted means at the two largest gaps; the lowest group is "poor", the highest "rich".
    order = sorted(means, key=means.get)
    gaps = sorted(range(1, len(order)), key=lambda k: means[order[k]] - means[order[k - 1]], reverse=True)[:2]
    low, high = sorted(gaps)
    return {c: (3 if k < low else 2 if k < high else 1) for k, c in enumerate(order)}


def adjusted_rand(a, b):
    n = len(a)
    pairs = lambda k: k * (k - 1) / 2
    table = defaultdict(int)
    for x, y in zip(a, b):
        table[(x, y)] += 1
    rows_, cols_ = defaultdict(int), defaultdict(int)
    for (x, y), k in table.items():
        rows_[x] += k
        cols_[y] += k
    index = sum(pairs(k) for k in table.values())
    expected = sum(pairs(k) for k in rows_.values()) * sum(pairs(k) for k in cols_.values()) / pairs(n)
    maximum = (sum(pairs(k) for k in rows_.values()) + sum(pairs(k) for k in cols_.values())) / 2
    return (index - expected) / (maximum - expected) if maximum != expected else 0.0


def statistic_h2(means, wealth):
    countries = sorted(means)
    rho = spearman([WEALTH_RANK[wealth[c]] for c in countries], [means[c] for c in countries])
    split = three_way_split(means)
    ari = adjusted_rand([WEALTH_RANK[wealth[c]] for c in countries], [split[c] for c in countries])
    return rho, ari


def holm(pvalues):
    order = sorted(range(len(pvalues)), key=lambda i: pvalues[i])
    adjusted, running = [0.0] * len(pvalues), 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (len(pvalues) - rank) * pvalues[i]))
        adjusted[i] = running
    return adjusted


def analyse_model(model, ok, permutations, rng):
    lines, out = [], {}
    b1 = sample(ok, 1)
    if not b1:
        return [f"{model}: no readable block 1 answers"], {"h1_p": 1.0}
    values, cells = centred(b1)
    labels = [r["country"] for r in b1]
    wealth = {r["country"]: r["wealth_group"] for r in b1}
    observed, means = spread(values, labels)
    rho, ari = statistic_h2(means, wealth)
    ge_spread = le_rho = ge_ari = 0
    for _ in range(permutations):
        shuffled = labels[:]
        for idx in cells:
            picked = [labels[i] for i in idx]
            rng.shuffle(picked)
            for i, label in zip(idx, picked):
                shuffled[i] = label
        s, m = spread(values, shuffled)
        r_, a_ = statistic_h2(m, wealth)
        ge_spread += s >= observed
        le_rho += r_ <= rho
        ge_ari += a_ >= ari
    p1, p2, p2b = (1 + ge_spread) / (1 + permutations), (1 + le_rho) / (1 + permutations), (1 + ge_ari) / (1 + permutations)
    out["h1_p"] = p1
    lines.append(f"[{model}] H1 spread among {len(means)} nationalities: sd of the means {observed:.2f} points, "
                 f"range {max(means.values()) - min(means.values()):.2f}; p = {p1:.4f} (one-sided, {permutations} shuffles)")
    lines.append(f"[{model}] H2 Spearman(wealth rank, mean) = {rho:+.2f}, p = {p2:.4f} (expected negative); "
                 f"adjusted Rand index of a three-way split against the wealth groups = {ari:+.2f}, p = {p2b:.4f}")
    ordered = sorted(means.items(), key=lambda kv: kv[1])
    lines.append("   ordered means (centred, points): " + ", ".join(f"{c} {v:+.1f}" for c, v in ordered))
    placebo = [r for r in ok if r["block"] == "1" and r["variant"] == "base" and r["group"] == "placebo"
               and r["visa_required"] == "yes"]
    if len({r["country"] for r in placebo}) > 1:
        pv, pc = centred(placebo)
        ps, _ = spread(pv, [r["country"] for r in placebo])
        lines.append(f"   reference: sd of the means of the {len({r['country'] for r in placebo})} placebo nationalities "
                     f"that need a visa = {ps:.2f}")

    # H3: block 2 against block 1, the same units, paired.
    b2 = sample(ok, 2)
    key = lambda r: (r["applicant_id"], r["savings"], r["wording"], r["repetition"], r["country"])
    one, two = {key(r): r for r in b1}, {key(r): r for r in b2}
    common = sorted(set(one) & set(two))
    if common:
        pairs = [(one[k], two[k]) for k in common]

        def spread_of(rows):
            v, _ = centred(rows)
            return spread(v, [r["country"] for r in rows])[0]

        diff = spread_of([b for _, b in pairs]) - spread_of([a for a, _ in pairs])
        ge = 0
        for _ in range(permutations):
            first, second = [], []
            for a, b in pairs:
                if rng.random() < 0.5:
                    a, b = b, a
                first.append(a)
                second.append(b)
            ge += (spread_of(second) - spread_of(first)) <= diff
        p3 = (1 + ge) / (1 + permutations)
        lines.append(f"[{model}] H3 spread with the paragraph minus spread without it: {diff:+.2f} points "
                     f"({len(common)} paired answers); p = {p3:.4f} (expected negative)")
    else:
        lines.append(f"[{model}] H3 not available: no paired answers in blocks 1 and 2")

    # H4: the instrument reacts to a real ground.
    steps = money_step([r for r in ok if r["variant"] == "base"])
    if LOW_LEVEL in steps and THRESHOLD_LEVEL in steps:
        step = steps[THRESHOLD_LEVEL][0] - steps[LOW_LEVEL][0]
        lines.append(f"[{model}] H4 score at AED {THRESHOLD_LEVEL} minus AED {LOW_LEVEL}: {step:+.1f} points "
                     f"({'meets' if step >= MIN_MONEY_STEP else 'does NOT meet'} the {MIN_MONEY_STEP:.0f}-point rule)")
    else:
        lines.append(f"[{model}] H4 not available: run blocks 1 and 3")
    return lines, out


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--batch", required=True, nargs="+", help="one or more batches under data/processed")
    parser.add_argument("--permutations", type=int, default=10000)
    parser.add_argument("--data-root", default=str(DATA))
    args = parser.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    rng = random.Random(SEED)
    results, all_lines = {}, []
    for batch in args.batch:
        try:
            _, ok = load(batch, args.data_root)
        except FileNotFoundError:
            print(f"error: no parsed answers for batch {batch!r}", file=sys.stderr)
            return 2
        for model in sorted({r["model_alias"] for r in ok}):
            lines, out = analyse_model(model, [r for r in ok if r["model_alias"] == model], args.permutations, rng)
            all_lines += (["MOCK BATCH, NOT A RESULT"] if batch.startswith("mock") else []) + lines
            results[f"{batch}/{model}"] = out
    adjusted = holm([v["h1_p"] for v in results.values()])
    all_lines.append("\nH1 p-values after Holm correction over the models: " +
                     ", ".join(f"{name} {p:.4f}" for name, p in zip(results, adjusted)))
    print("\n".join(all_lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
