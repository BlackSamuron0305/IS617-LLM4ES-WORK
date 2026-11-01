"""Stage 4: send the judge inputs of a batch to the judge model and store the raw answers.

Reads data/processed/<batch>/judge_items.jsonl (written by judge_build). The default is a mock
run, which needs no server. A real run is refused unless every condition in pipeline/client.py
holds; it is started only with the team's explicit approval (CLAUDE.md, "Compute and models"),
and not before the judge's revision is pinned in experiment/judge/judge_models.csv. Raw answers
are appended to data/raw/<batch>/judge_<alias>.jsonl, the sessions are listed in
judge_<alias>_manifest.json next to it; a run that stopped can be started again with the same
command and continues where it ended.

Usage:
    python -m pipeline.run_judge --batch mock_x --judge olmo-3.1-32b-instruct --mock --limit 30
    python -m pipeline.run_judge --batch pilot1 --judge olmo-3.1-32b-instruct --base-url URL --allow-real-calls
"""

import argparse
import json
import sys
from pathlib import Path

from pipeline.calls import begin_stage, check_mock_label, record_summary, run_calls
from pipeline.client import RunRefused, make_client
from pipeline.common import DATA, load_models, load_settings, read_jsonl
from pipeline.judge_build import JUDGE
from pipeline.judge_parse import JUDGE_SCHEMA


def plan_items(records, limit):
    # One item per judge input, in file order; the key is the item_id.
    items = [{"key": record["item_id"],
              "messages": [{"role": "system", "content": record["system"]},
                           {"role": "user", "content": record["user"]}],
              "meta": {"item_id": record["item_id"]}} for record in records]
    return items if limit is None else items[:limit]


def run_judge(batch, judge_alias, client, data_root, limit=None, workers=8, mock=False):
    judges = load_models(JUDGE / "judge_models.csv")
    if judge_alias not in judges:
        raise RunRefused(f"unknown judge alias {judge_alias!r}; experiment/judge/judge_models.csv has: "
                         f"{', '.join(judges)}")
    judge = judges[judge_alias]
    check_mock_label(client, mock, batch)
    items_path = Path(data_root) / "processed" / batch / "judge_items.jsonl"
    if not items_path.exists():
        raise FileNotFoundError(f"no judge inputs for batch {batch!r}: {items_path} does not exist "
                                "(run judge_build first)")
    settings = load_settings("judge")
    items = plan_items(read_jsonl(items_path), limit)
    batch_dir = Path(data_root) / "raw" / batch
    manifest_path = batch_dir / f"judge_{judge_alias}_manifest.json"
    # The manifest comes first: a batch that belongs to another model is refused before any call.
    fixed_fields = begin_stage(manifest_path, "judge", batch, judge_alias, judge, mock, settings, {"limit": limit},
                               client)
    summary = run_calls(items, client, settings, judge["extra_body"], JUDGE_SCHEMA,
                        batch_dir / f"judge_{judge_alias}.jsonl", workers, fixed_fields)
    record_summary(manifest_path, summary)
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description="Send the judge inputs of a batch to the judge model "
                                                 "(mock by default).")
    parser.add_argument("--batch", required=True, help="name of the batch; a mock batch starts with 'mock'")
    parser.add_argument("--judge", required=True, help="alias in experiment/judge/judge_models.csv")
    parser.add_argument("--limit", type=int, help="only the first N calls")
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--mock", action="store_true", help="use the mock client, no server needed")
    parser.add_argument("--base-url", help="address of the server, for example http://localhost:8000/v1")
    parser.add_argument("--allow-real-calls", action="store_true",
                        help="give only with the team's explicit approval of real model calls")
    parser.add_argument("--data-root", default=str(DATA))
    args = parser.parse_args(argv)

    judges = load_models(JUDGE / "judge_models.csv")
    if args.judge not in judges:
        print(f"error: unknown judge {args.judge!r}; experiment/judge/judge_models.csv has: {', '.join(judges)}",
              file=sys.stderr)
        return 2
    try:
        client = make_client("judge", judges[args.judge], args.batch, args.mock, args.base_url,
                             args.allow_real_calls)
        summary = run_judge(args.batch, args.judge, client, Path(args.data_root), args.limit, args.workers,
                            args.mock)
    except RunRefused as exc:
        print(f"refusing: {exc}", file=sys.stderr)
        return 2
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
