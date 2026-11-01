"""Put the parsed answers of several shard batches into one batch.

A big run is split into shards (python -m pipeline.run_models --shard K/N), one batch per shard,
named <name>_s0 to <name>_s<N-1>, so that several jobs can run at the same time without writing
to the same file. After parse_answers has been run on each shard batch, this puts the rows
together in data/processed/<name>/answers.csv, which the later stages read. Rows are unique by
key; the same key in two shards is an error. Never calls a model.

Usage:
    python -m pipeline.merge_batches --into main_qwen3-32b_b1 [--data-root data]
"""

import argparse
import csv
import sys
from pathlib import Path

from pipeline.common import DATA
from pipeline.parse_answers import ANSWER_COLUMNS


def merge(into, data_root):
    processed = Path(data_root) / "processed"
    parts = sorted(p for p in processed.glob(f"{into}_s*") if (p / "answers.csv").exists())
    if not parts:
        raise FileNotFoundError(f"no parsed shard batches {into}_s* under {processed}")
    rows, seen = [], {}
    for part in parts:
        with open(part / "answers.csv", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames != ANSWER_COLUMNS:
                raise ValueError(f"{part.name}: the columns are not the ones parse_answers writes")
            for row in reader:
                if row["key"] in seen:
                    raise ValueError(f"key {row['key']} is in both {seen[row['key']]} and {part.name}")
                seen[row["key"]] = part.name
                row["batch"] = into
                rows.append(row)
    out = processed / into / "answers.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=ANSWER_COLUMNS)
        writer.writeheader()
        writer.writerows(sorted(rows, key=lambda r: r["key"]))
    print(f"{len(rows)} rows from {len(parts)} shard batches in {out}")
    return out


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--into", required=True, help="name of the merged batch; the shards are <name>_s*")
    parser.add_argument("--data-root", default=str(DATA))
    args = parser.parse_args(argv)
    try:
        merge(args.into, args.data_root)
    except (FileNotFoundError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
