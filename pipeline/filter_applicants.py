"""Filter the simulated applicant dossiers down to what the model is allowed to see.

experiment/applicants/applicants_full.csv holds a complete, realistic record for each
applicant, including fields a real visa application carries (name, sex, date of birth, ...).
experiment/applicants/field_filter.csv says, for every field, whether the model sees it. This
script writes experiment/applicants/applicants.csv with the fields marked yes or analysis_only.
build_runs checks that applicants.csv is exactly what this filter gives and that no value of a
removed field occurs in any prompt. Never calls a model.

Usage:
    python -m pipeline.filter_applicants            write applicants.csv
    python -m pipeline.filter_applicants --check    only check that applicants.csv is up to date
"""

import argparse
import sys

from pipeline import common
from pipeline.common import EXPERIMENT

APPLICANTS = EXPERIMENT / "applicants"
SHOWN = ("yes", "analysis_only")


def load_filter():
    rules = {row["field"]: row["shown_to_model"] for row in common.read_table(APPLICANTS / "field_filter.csv")}
    bad = {field: value for field, value in rules.items() if value not in (*SHOWN, "no")}
    if bad:
        raise ValueError(f"field_filter.csv: shown_to_model must be yes, no or analysis_only: {bad}")
    return rules


def filter_rows(full_rows, rules):
    # Returns (kept columns, filtered rows, removed columns). A field without a rule is an error.
    columns = list(full_rows[0])
    missing = [c for c in columns if c not in rules]
    if missing:
        raise ValueError(f"applicants_full.csv has fields without a rule in field_filter.csv: {missing}")
    kept = [c for c in columns if rules[c] in SHOWN]
    removed = [c for c in columns if rules[c] == "no"]
    return kept, [{c: row[c] for c in kept} for row in full_rows], removed


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--check", action="store_true", help="do not write; fail if applicants.csv is out of date")
    args = parser.parse_args(argv)
    full = common.read_table(APPLICANTS / "applicants_full.csv")
    kept, rows, removed = filter_rows(full, load_filter())
    target = APPLICANTS / "applicants.csv"
    if args.check:
        if common.read_table(target) != rows:
            print("applicants.csv is not what the filter gives; run python -m pipeline.filter_applicants")
            return 1
        print("applicants.csv is up to date")
        return 0
    common.write_csv(target, rows, kept)
    print(f"{len(rows)} applicants; {len(kept)} fields kept; removed: {', '.join(removed)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
