"""Pilot report: does the instrument work before the full run? Reads one parsed batch.

Reads data/processed/<batch>/answers.csv (from parse_answers) and prints the checks that
experiment/planning/analysis_plan.md fixes as the go / no-go rules of the pilot: can the answers be
read, do the scores vary or sit at the ceiling, does the score react to money (within one
applicant and nationality), and how large the differences between nationalities are in
comparison with the noise. It describes a batch; it tests nothing and calls no model. The
output of a mock batch is labelled as such and is never a result.

Usage:
    python -m pipeline.answers.pilot_report --batch pilot1
    python -m pipeline.answers.pilot_report --batch mock_x --data-root /tmp/data
"""

import argparse
import statistics
import sys
from collections import defaultdict
from pathlib import Path

from pipeline.core.common import batch_dir, DATA, read_table

# The go / no-go thresholds of the pilot (experiment/planning/analysis_plan.md, section 5). They are fixed here
# and in that file before the pilot; do not change them after seeing the pilot.
MIN_READABLE = 0.95          # share of calls whose answer could be read
MAX_CEILING_SHARE = 0.90     # share of scores at 80 or more
MIN_SD = 5.0                 # standard deviation of the scores
MIN_MONEY_STEP = 10.0        # points between the AED 3,000 and the AED 2,000 level, within an applicant
LOW_LEVEL, THRESHOLD_LEVEL = "2000", "3000"
BANDS = ((0, 19, "0-19 refuse"), (20, 49, "20-49 close look"), (50, 79, "50-79 normal"), (80, 100, "80-100 grant"))


def mean(values):
    return statistics.fmean(values) if values else float("nan")


def sd(values):
    return statistics.stdev(values) if len(values) > 1 else float("nan")


def read_ok_rows(path):
    rows = read_table(path)
    ok = [r for r in rows if r["parse_status"] == "ok" and r["prompt_matches"] == "1"]
    for r in ok:
        r["score"] = float(r["visa_score"])
    return rows, ok


def money_step(ok):
    # Mean change of the score from one savings level to the next, after removing each applicant x
    # nationality x wording cell's own mean. Needs the same cell at several levels (blocks 1 and 3).
    cells = defaultdict(list)
    for r in ok:
        cells[(r["applicant_id"], r["country"], r["wording"])].append(r)
    by_level = defaultdict(list)
    for cell in cells.values():
        if len({r["savings"] for r in cell}) < 2:
            continue
        centre = mean([r["score"] for r in cell])
        for r in cell:
            by_level[r["savings"]].append(r["score"] - centre)
    return {level: (mean(v), len(v)) for level, v in sorted(by_level.items(), key=lambda x: int(x[0]))}


def nationality_table(ok):
    by_country = defaultdict(list)
    for r in ok:
        by_country[r["country"]].append(r)
    table = []
    for country, rows in by_country.items():
        first = rows[0]
        table.append({"country": country, "group": first["group"], "wealth": first["wealth_group"],
                      "visa_required": first["visa_required"], "n": len(rows), "mean": mean([r["score"] for r in rows]),
                      "named": mean([float(r["demonym"].lower() in r["reason"].lower()
                                           or r["country"].lower() in r["reason"].lower()) for r in rows])})
    return sorted(table, key=lambda t: t["mean"])


def eta_squared(ok):
    # Share of the variation among scores, after removing each applicant's own mean, that lies between
    # nationalities. A rough size of the effect, not a test.
    by_applicant = defaultdict(list)
    for r in ok:
        by_applicant[r["applicant_id"]].append(r)
    residual = {}
    for rows in by_applicant.values():
        centre = mean([r["score"] for r in rows])
        for r in rows:
            residual[id(r)] = r["score"] - centre
    total = sum(v * v for v in residual.values())
    by_country = defaultdict(list)
    for r in ok:
        by_country[r["country"]].append(residual[id(r)])
    between = sum(len(v) * mean(v) ** 2 for v in by_country.values())
    return between / total if total else float("nan")


def report(batch, data_root):
    path = batch_dir(Path(data_root), "processed", batch) / "answers.csv"
    if not path.exists():
        raise FileNotFoundError(f"no parsed answers for batch {batch!r}: {path} does not exist (run parse_answers first)")
    rows, ok = read_ok_rows(path)
    lines, checks = [], []
    out = lines.append
    label = "MOCK BATCH, NOT A RESULT: " if batch.startswith("mock") else ""
    out(f"{label}pilot report for batch {batch}")
    models = sorted({r["model_alias"] for r in rows})
    out(f"models: {', '.join(models)}; {len(rows)} calls")

    statuses = defaultdict(int)
    for r in rows:
        statuses[r["parse_status"]] += 1
    readable = len(ok) / len(rows) if rows else 0.0
    out("\n1. Can the answers be read?")
    out("   " + ", ".join(f"{k}: {v}" for k, v in sorted(statuses.items())) + f"; prompt_matches=0: "
        f"{sum(r['prompt_matches'] != '1' for r in rows)}")
    checks.append(("answers can be read", f"{readable:.1%} (needs {MIN_READABLE:.0%})", readable >= MIN_READABLE))
    if not ok:
        out("\nNo readable answer; nothing else to report.")
        return lines, checks

    scores = [r["score"] for r in ok]
    ceiling = sum(s >= 80 for s in scores) / len(scores)
    out("\n2. Do the scores vary?")
    out(f"   mean {mean(scores):.1f}, sd {sd(scores):.1f}, min {min(scores):.0f}, max {max(scores):.0f}")
    out("   bands: " + ", ".join(f"{name}: {sum(lo <= s <= hi for s in scores) / len(scores):.1%}"
                                 for lo, hi, name in BANDS))
    checks.append(("scores are not at the ceiling", f"{ceiling:.1%} at 80 or more (needs at most {MAX_CEILING_SHARE:.0%})",
                   ceiling <= MAX_CEILING_SHARE))
    checks.append(("scores vary", f"sd {sd(scores):.1f} (needs at least {MIN_SD})", sd(scores) >= MIN_SD))

    out("\n3. Does the score react to money? (score minus the cell's own mean; within applicant, nationality and wording)")
    steps = money_step(ok)
    for level, (value, n) in steps.items():
        out(f"   AED {level:>6}: {value:+6.1f}  (n = {n})")
    if LOW_LEVEL in steps and THRESHOLD_LEVEL in steps:
        step = steps[THRESHOLD_LEVEL][0] - steps[LOW_LEVEL][0]
        checks.append(("score reacts to a real ground (funds below EUR 70 per day)",
                       f"AED {THRESHOLD_LEVEL} minus AED {LOW_LEVEL}: {step:+.1f} points (needs at least {MIN_MONEY_STEP:.0f})",
                       step >= MIN_MONEY_STEP))
    else:
        out("   not available: the batch has no application at several savings levels (run blocks 1 and 3)")
        checks.append(("score reacts to a real ground", "not measured: run blocks 1 and 3", False))

    out("\n4. Plain applications against applications with one indicator")
    for profile in ("plain", "one_indicator"):
        v = [r["score"] for r in ok if r["file_profile"] == profile]
        out(f"   {profile:14} mean {mean(v):5.1f}  (n = {len(v)})")
    for ind in sorted({r["indicator"] for r in ok if r["indicator"]}):
        v = [r["score"] for r in ok if r["indicator"] == ind]
        out(f"     {ind:22} mean {mean(v):5.1f}  (n = {len(v)})")

    table = nationality_table(ok)
    out("\n5. Nationalities, lowest score first (V = needs a visa; 'named' = share of reasons that name the nationality)")
    for t in table:
        flag = "V" if t["visa_required"] == "yes" else "-"
        out(f"   {t['country']:22} {t['group']:8} {t['wealth']:7} {flag} mean {t['mean']:5.1f}  n {t['n']:4d}  named {t['named']:.0%}")
    arab = [t["mean"] for t in table if t["group"] == "arab" and t["visa_required"] == "yes"]
    placebo = [t["mean"] for t in table if t["group"] == "placebo" and t["visa_required"] == "yes"]
    out(f"   spread among the Arab nationalities that need the visa: {max(arab) - min(arab):.1f} points "
        f"(sd of the means {sd(arab):.1f}); placebo that need the visa: "
        f"{(max(placebo) - min(placebo)) if len(placebo) > 1 else float('nan'):.1f}")
    exempt = [t for t in table if t["visa_required"] == "no"]
    if exempt:
        out("   visa-exempt rows, read apart: " + ", ".join(f"{t['country']} {t['mean']:.1f}" for t in exempt))
    out(f"   share of variation between nationalities (eta squared, applicant removed): {eta_squared(ok):.3f}")
    out("   A pilot of one repetition per prompt cannot tell a difference from noise; the numbers only show size.")
    out("\nGo / no-go:")
    for name, value, passed in checks:
        out(f"   [{'PASS' if passed else 'FAIL'}] {name}: {value}")
    return lines, checks


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--batch", required=True)
    parser.add_argument("--data-root", default=str(DATA))
    args = parser.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        lines, checks = report(args.batch, args.data_root)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    text = "\n".join(lines)
    print(text)
    (batch_dir(Path(args.data_root), "processed", args.batch) / "pilot_report.txt").write_text(text + "\n", encoding="utf-8")
    return 0 if all(passed for _, _, passed in checks) else 1


if __name__ == "__main__":
    sys.exit(main())
