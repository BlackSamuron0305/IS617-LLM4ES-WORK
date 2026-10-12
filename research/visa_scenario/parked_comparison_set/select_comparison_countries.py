"""Pick the comparison nationalities by a fixed rule, before any model is run.

For each of the 22 Arab League countries the rule picks one country that is not an Arab
League member, lies outside the Middle East and North Africa, has a Muslim population
share below 20%, needs the same Australian visitor visa at the same fee, and is as close
as possible in passport strength (Henley Passport Index). The five benchmark countries
are the most populous non-Arab countries with a Muslim population share of at least 80%
that need the same visa. The rule is described in experiment/countries/README.md.

The script only reads experiment/countries/. It never calls a model.

Usage:
    python scripts/select_comparison_countries.py            print the selection
    python scripts/select_comparison_countries.py --check    also compare it with applicant_nationalities.csv
"""

import argparse
import csv
import math
import sys
from pathlib import Path

COUNTRIES = Path(__file__).resolve().parent.parent / "experiment" / "countries"
MENA = "Middle East, North Africa, Afghanistan & Pakistan"
SAME_VISA = "visitor_600"
MAX_MUSLIM_SHARE_COMPARISON = 20.0
MIN_MUSLIM_SHARE_BENCHMARK = 80.0
EXCLUDED = {
    "North Korea": "its citizens can hardly travel; no comparable group of residents abroad",
    "Iran": "holders of this visa with an Iranian passport were barred from travelling to Australia from "
            "26 March to 25 September 2026 (LIN 26/040): a rule by nationality, which the design avoids",
}
BENCHMARKS = 5


def read_world():
    with open(COUNTRIES / "world_reference.csv", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    for row in rows:
        row["henley"] = int(row["henley_visa_free_2026"])
        row["muslim"] = float(row["muslim_share_2020"]) if row["muslim_share_2020"] else None
        row["population"] = float(row["population_2020_million"]) if row["population_2020_million"] else 0.0
        row["log_gdp"] = math.log(float(row["gdp_pc_ppp_2022"])) if row["gdp_pc_ppp_2022"] else None
    return rows


def distance(arab, other):
    """Difference in visa-free destinations; income per person only breaks ties."""
    gap = abs(arab["henley"] - other["henley"])
    if arab["log_gdp"] is not None and other["log_gdp"] is not None:
        gap += 0.001 * abs(arab["log_gdp"] - other["log_gdp"])
    return gap


def match(arab, pool):
    """One-to-one matching with the smallest total distance (both lists sorted by passport strength)."""
    arab = sorted(arab, key=lambda r: (r["henley"], r["country"]))
    pool = sorted(pool, key=lambda r: (r["henley"], r["country"]))
    n, m = len(arab), len(pool)
    best = [[math.inf] * (m + 1) for _ in range(n + 1)]
    best[0] = [0.0] * (m + 1)
    for i in range(1, n + 1):
        for j in range(i, m + 1):
            best[i][j] = min(best[i][j - 1], best[i - 1][j - 1] + distance(arab[i - 1], pool[j - 1]))
    pairs, i, j = [], n, m
    while i > 0:
        if best[i][j] == best[i][j - 1]:
            j -= 1
        else:
            pairs.append((arab[i - 1], pool[j - 1]))
            i, j = i - 1, j - 1
    return pairs[::-1]


def select():
    world = read_world()
    arab = [r for r in world if r["arab_league"] == "yes"]
    pool = [r for r in world
            if r["arab_league"] == "no"
            and r["australia_visitor_route"] == SAME_VISA
            and r["wb_region"] != MENA
            and r["muslim"] is not None and r["muslim"] < MAX_MUSLIM_SHARE_COMPARISON
            and r["country"] not in EXCLUDED]
    pairs = match(arab, pool)
    candidates = [r for r in world
                  if r["arab_league"] == "no"
                  and r["australia_visitor_route"] == SAME_VISA
                  and r["muslim"] is not None and r["muslim"] >= MIN_MUSLIM_SHARE_BENCHMARK
                  and r["country"] not in EXCLUDED]
    benchmarks = sorted(candidates, key=lambda r: -r["population"])[:BENCHMARKS]
    return arab, pool, pairs, benchmarks


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--check", action="store_true", help="compare with applicant_nationalities.csv")
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    arab, pool, pairs, benchmarks = select()
    not_same_visa = [r["country"] for r in arab if r["australia_visitor_route"] != SAME_VISA]
    print(f"Arab League countries: {len(arab)}; not on the same visa: {not_same_visa or 'none'}")
    print(f"countries the comparison set is picked from: {len(pool)}\n")
    print(f"{'Arab League':24}{'visa-free':>9}   {'comparison':34}{'visa-free':>9}{'gap':>6}{'Muslim %':>10}")
    for a, c in pairs:
        print(f"{a['country']:24}{a['henley']:>9}   {c['country']:34}{c['henley']:>9}{c['henley'] - a['henley']:>+6}{c['muslim']:>10.1f}")
    gaps = [abs(c["henley"] - a["henley"]) for a, c in pairs]
    print(f"\nmean gap: {sum(gaps) / len(gaps):.1f} destinations; largest: {max(gaps)}")
    print("benchmark (non-Arab, Muslim share of at least 80%, most populous):",
          ", ".join(f"{r['country']} ({r['henley']})" for r in benchmarks))

    if args.check:
        with open(COUNTRIES / "applicant_nationalities.csv", encoding="utf-8", newline="") as f:
            table = list(csv.DictReader(f))
        expected = {"arab": {r["country"] for r in arab},
                    "comparison": {c["country"] for _, c in pairs},
                    "muslim_benchmark": {r["country"] for r in benchmarks}}
        problems = []
        for group, countries in expected.items():
            in_table = {r["country"] for r in table if r["group"] == group}
            if in_table != countries:
                problems.append(f"{group}: table has {sorted(in_table - countries)} extra and lacks {sorted(countries - in_table)}")
        partner = {c["country"]: a["country"] for a, c in pairs}
        for row in table:
            if row["group"] == "comparison" and row["matched_to"] != partner.get(row["country"]):
                problems.append(f"{row['country']}: matched_to is {row['matched_to']!r}, the rule gives {partner.get(row['country'])!r}")
        if problems:
            print(f"\n{len(problems)} PROBLEM(S):")
            for problem in problems:
                print("  -", problem)
            return 1
        print("\napplicant_nationalities.csv agrees with the rule")
    return 0


if __name__ == "__main__":
    sys.exit(main())
