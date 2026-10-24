"""Stage 6: check the judge against a human. Draw items for hand-coding, then measure agreement.

sample: draws items from data/processed/<batch>/judge_items.jsonl and writes validation_sample.csv
in the same folder: item_id, applicant_id, the masked reason, the masked application as the judge
saw it, five empty code columns, coder and note. It holds none of the judge's codes, so the person
who fills it in stays blind to them. About half of the items are ones where a nationality word was
hidden (n_masked > 0), the rest are drawn from the others. The same batch, n and seed give the same
file. sample refuses to overwrite an existing file (the hand-coding may be in it) unless --force is
given; code a copy.

agreement: reads the hand-coded file (cells yes, no, 1, 0 or empty) and either the judge's codes,
judge_codes_<alias>.csv (rows with judge_status ok or inconsistent), or a second hand-coded file. For
each of the five codes it compares the two sides on the items that have a value on both and prints
n, the share of items they agree on and Cohen's kappa. A code passes when kappa is at least
KAPPA_MIN. The table is also written to validation_agreement_<alias or file stem>.csv. A kappa is
n/a when chance alone would give complete agreement (a code that is constant on both sides). Below
the table it prints how many item ids have codes on one side only, so that ids a spreadsheet program
has changed do not drop out unnoticed. Never calls a model.

Usage:
    python -m pipeline.judge_validate sample --batch pilot1 [--n 200] [--seed 617] [--force]
    python -m pipeline.judge_validate agreement --batch pilot1 --human coded.csv --judge gpt-oss-120b
    python -m pipeline.judge_validate agreement --batch pilot1 --human coded.csv --other-human coded2.csv
Both take --data-root (default: the data folder of the repo).
"""

import argparse
import csv
import random
import sys
from collections import Counter
from pathlib import Path

from pipeline.client import JUDGE_MARKER
from pipeline.common import DATA, read_jsonl, write_csv
from pipeline.judge_build import JUDGE_CODES

# Provisional: the team confirms this threshold before the first real run.
KAPPA_MIN = 0.7
# The line of experiment/judge/judge_task.txt that precedes the application.
APPLICATION_MARKER = "APPLICATION"
SAMPLE_COLUMNS = ["item_id", "applicant_id", "reason_masked", "application_masked", *JUDGE_CODES, "coder", "note"]
AGREEMENT_COLUMNS = ["code", "n", "agree_share", "kappa", "passes"]
CODE_VALUES = {"yes": 1, "1": 1, "no": 0, "0": 0}
# Rows of a judge file with another status have blank codes (judge_parse leaves them blank).
USABLE_STATUS = ("ok", "inconsistent")


def cohen_kappa(a, b):
    # Agreement of two coders beyond chance: 1 is perfect, 0 is what chance gives. None when chance
    # alone would give complete agreement (both sides constant and equal), as kappa is then 0 / 0.
    if len(a) == 0 or len(a) != len(b):
        raise ValueError(f"need two lists of the same, non-zero length, got {len(a)} and {len(b)}")
    n = len(a)
    agree = sum(1 for x, y in zip(a, b) if x == y)
    count_a, count_b = Counter(a), Counter(b)
    # Chance agreement is chance / n**2; kappa = (agree / n - chance / n**2) / (1 - chance / n**2).
    chance = sum(count_a[value] * count_b[value] for value in count_a)
    if chance == n * n:
        return None
    return (agree * n - chance) / (n * n - chance)


def agreement(a, b):
    # a, b: item_id -> {code: 1/0}. One row per code, over the items with a 0/1 value on both sides.
    rows = []
    for code in JUDGE_CODES:
        ids = sorted(item_id for item_id in a.keys() & b.keys()
                     if a[item_id].get(code) in (0, 1) and b[item_id].get(code) in (0, 1))
        if not ids:
            rows.append({"code": code, "n": 0, "agree_share": None, "kappa": None, "passes": False})
            continue
        left, right = [a[item_id][code] for item_id in ids], [b[item_id][code] for item_id in ids]
        kappa = cohen_kappa(left, right)
        rows.append({"code": code, "n": len(ids), "agree_share": sum(x == y for x, y in zip(left, right)) / len(ids),
                     "kappa": kappa, "passes": kappa is not None and kappa >= KAPPA_MIN})
    return rows


def application_of(item):
    # The masked application exactly as the judge saw it: the text of the user message between the
    # line APPLICATION and the line that precedes the reason, without the newlines around it.
    head, marker, _ = item["user"].partition(JUDGE_MARKER)
    if not marker or not head.startswith(APPLICATION_MARKER + "\n"):
        raise ValueError(f"item {item['item_id']}: the judge input does not have the form "
                         f"{APPLICATION_MARKER} ... {JUDGE_MARKER} ...")
    return head[len(APPLICATION_MARKER):].strip("\n")


def draw_sample(batch, n, seed, data_root, force=False):
    if n < 1:
        raise ValueError(f"n must be at least 1, not {n}")
    items_path = Path(data_root) / "processed" / batch / "judge_items.jsonl"
    if not items_path.exists():
        raise FileNotFoundError(f"no judge inputs for batch {batch!r}: {items_path} does not exist "
                                "(run judge_build first)")
    path = Path(data_root) / "processed" / batch / "validation_sample.csv"
    if path.exists() and not force:
        raise FileExistsError(f"{path} already exists and may hold hand-coding: code a copy of it, "
                              "or pass --force to overwrite it")
    # Sorted, so that the sample does not depend on the order of the file.
    items = sorted(read_jsonl(items_path), key=lambda item: item["item_id"])
    masked = [item for item in items if item["n_masked"] > 0]
    others = [item for item in items if item["n_masked"] == 0]
    # Half from the masked items, the rest from the others; if one pool runs short the other fills up.
    take_masked = min(n // 2, len(masked))
    take_others = min(n - take_masked, len(others))
    take_masked = min(n - take_others, len(masked))
    rng = random.Random(seed)
    chosen = rng.sample(masked, take_masked) + rng.sample(others, take_others)
    rng.shuffle(chosen)
    rows = [{"item_id": item["item_id"], "applicant_id": item["applicant_id"],
             "reason_masked": item["reason_masked"], "application_masked": application_of(item),
             **dict.fromkeys(JUDGE_CODES, ""), "coder": "", "note": ""} for item in chosen]
    write_csv(path, rows, SAMPLE_COLUMNS)
    return path


def read_codes(path):
    # item_id -> {code: 1/0}. Blank cells are skipped; an item with no value at all is left out.
    codes = {}
    # utf-8-sig: a spreadsheet program may have put a byte order mark in front of the first column name.
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if "item_id" not in (reader.fieldnames or []):
            raise ValueError(f"{path} has no item_id column (it must be a comma-separated CSV)")
        for row in reader:
            item_id = (row["item_id"] or "").strip()
            if not item_id or ("judge_status" in row and row["judge_status"] not in USABLE_STATUS):
                continue
            for code in JUDGE_CODES:
                cell = (row.get(code) or "").strip().lower()
                if cell == "":
                    continue
                if cell not in CODE_VALUES:
                    raise ValueError(f"{path}: item {item_id}, {code} is {row[code]!r}; "
                                     "use yes, no, 1, 0 or leave it empty")
                codes.setdefault(item_id, {})[code] = CODE_VALUES[cell]
    return codes


def format_number(value):
    return "n/a" if value is None else f"{value:.3f}"


def print_agreement(rows, left, right):
    print(f"agreement of {left} with {right} (a code passes at kappa >= {KAPPA_MIN}, a provisional threshold)")
    for row in rows:
        print(f"  {row['code']:<28} n={row['n']:<5} agree={format_number(row['agree_share'])}  "
              f"kappa={format_number(row['kappa'])}  {'pass' if row['passes'] else 'FAIL'}")


def run_agreement(args):
    folder = Path(args.data_root) / "processed" / args.batch
    if args.judge:
        other_path, name = folder / f"judge_codes_{args.judge}.csv", args.judge
        if not other_path.exists():
            raise FileNotFoundError(f"no judge codes for judge {args.judge!r}: {other_path} does not exist "
                                    "(run judge_parse first)")
    else:
        other_path, name = Path(args.other_human), Path(args.other_human).stem
    for path in (Path(args.human), other_path):
        if not path.exists():
            raise FileNotFoundError(f"{path} does not exist")
    human, other = read_codes(args.human), read_codes(other_path)
    rows = agreement(human, other)
    out_path = folder / f"validation_agreement_{name}.csv"
    write_csv(out_path, rows, AGREEMENT_COLUMNS)  # None is written as an empty cell
    print_agreement(rows, args.human, other_path)
    # Ids that a spreadsheet changed find no partner and would drop out of the table without a word.
    print(f"item ids with codes only in the human file: {len(human.keys() - other.keys())} "
          "(if not 0, check that the ids are unchanged)")
    print(f"item ids with codes only on the other side: {len(other.keys() - human.keys())}")
    print(f"written: {out_path}")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    commands = parser.add_subparsers(dest="command", required=True)
    sample = commands.add_parser("sample", help="draw the items to be coded by hand")
    sample.add_argument("--batch", required=True, help="name of the batch under data/processed")
    sample.add_argument("--n", type=int, default=200, help="number of items (default 200)")
    sample.add_argument("--seed", type=int, default=617, help="seed of the draw (default 617)")
    sample.add_argument("--force", action="store_true", help="overwrite an existing validation_sample.csv")
    sample.add_argument("--data-root", default=str(DATA))
    check = commands.add_parser("agreement", help="compare hand codes with the judge or with a second coder")
    check.add_argument("--batch", required=True, help="name of the batch under data/processed")
    check.add_argument("--human", required=True, help="the hand-coded file")
    side = check.add_mutually_exclusive_group(required=True)
    side.add_argument("--judge", help="alias of the judge whose judge_codes_<alias>.csv is compared")
    side.add_argument("--other-human", help="a second hand-coded file")
    check.add_argument("--data-root", default=str(DATA))
    args = parser.parse_args(argv)
    try:
        if args.command == "sample":
            path = draw_sample(args.batch, args.n, args.seed, Path(args.data_root), force=args.force)
            print(f"written: {path}")
            print("code a copy of it: sample will not overwrite this file again without --force")
        else:
            run_agreement(args)
    except (FileNotFoundError, FileExistsError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
