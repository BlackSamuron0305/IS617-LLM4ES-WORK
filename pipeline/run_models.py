"""Stage 1: send the prompts of the experiment to one model and store the raw answers.

The default is a mock run, which needs no server. A real run is refused unless every
condition in pipeline/client.py holds; it is started only with the team's explicit
approval (CLAUDE.md, "Compute and models"). Raw answers are appended to
data/raw/<batch>/answers.jsonl; a run that stopped can be started again with the same
command and continues where it ended.

Usage:
    python -m pipeline.run_models --batch mock_x --model qwen3-8b --mock --block 1 --limit 30
    python -m pipeline.run_models --batch pilot1 --model qwen3-8b --base-url URL --allow-real-calls
"""

import argparse
import json
import sys
from pathlib import Path

from pipeline.build_runs import build_runs
from pipeline.calls import record_summary, run_calls, update_manifest
from pipeline.client import MockClient, RunRefused, check_mock_batch, make_client
from pipeline.common import DATA, EXPERIMENT, dirty_files, git_commit, load_models, load_settings, utc_now


def plan_items(runs, blocks, limit):
    # One item per repetition of every run, in build order; the key names run and repetition.
    items = []
    for run in runs:
        if blocks is not None and run["block"] not in blocks:
            continue
        messages = [{"role": "system", "content": run["system"]}, {"role": "user", "content": run["user"]}]
        for repetition in range(1, run["repetitions"] + 1):
            items.append({"key": f"{run['run_id']}__r{repetition}", "messages": messages,
                          "meta": {"run_id": run["run_id"], "repetition": repetition, "block": run["block"]}})
    return items if limit is None else items[:limit]


def run_answers(batch, model_alias, client, data_root, blocks=None, limit=None, workers=8, mock=False):
    models = load_models(EXPERIMENT / "models.csv")
    if model_alias not in models:
        raise RunRefused(f"unknown model alias {model_alias!r}; experiment/models.csv has: {', '.join(models)}")
    model = models[model_alias]
    # The label "mock" must match the client, or mock output would pass for a result (or the reverse).
    if isinstance(client, MockClient) != mock:
        raise RunRefused("mock=True needs the mock client, and the mock client needs mock=True")
    if mock:
        check_mock_batch(batch)
    runs, _, _, problems = build_runs()
    if problems:
        raise RunRefused("build_runs reports problems: " + "; ".join(problems[:5]))
    settings = load_settings("answers")
    items = plan_items(runs, blocks, limit)
    batch_dir = Path(data_root) / "raw" / batch
    header = {"batch": batch, "kind": "answers", "model_alias": model_alias, "model_id": model["model_id"],
              "revision": model["revision"], "mock": mock}
    session = {"started_utc": utc_now(), "git_commit": git_commit(), "dirty": dirty_files(), "blocks": blocks,
               "limit": limit, "settings": settings, "summary": None}
    # The manifest comes first: a batch that belongs to another model is refused before any call.
    update_manifest(batch_dir / "manifest.json", header, session)
    fixed_fields = {"batch": batch, "model_alias": model_alias, "model_id": model["model_id"], "kind": "answers",
                    "mock": mock}
    summary = run_calls(items, client, settings, model["extra_body"], None, batch_dir / "answers.jsonl", workers,
                        fixed_fields)
    record_summary(batch_dir / "manifest.json", summary)
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description="Send the experiment's prompts to one model (mock by default).")
    parser.add_argument("--batch", required=True, help="name of the batch; a mock batch starts with 'mock'")
    parser.add_argument("--model", required=True, help="alias in experiment/models.csv")
    parser.add_argument("--block", type=int, action="append", help="only this block (repeatable)")
    parser.add_argument("--limit", type=int, help="only the first N calls")
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--mock", action="store_true", help="use the mock client, no server needed")
    parser.add_argument("--base-url", help="address of the server, for example http://localhost:8000/v1")
    parser.add_argument("--allow-real-calls", action="store_true",
                        help="give only with the team's explicit approval of real model calls")
    parser.add_argument("--data-root", default=str(DATA))
    args = parser.parse_args(argv)

    models = load_models(EXPERIMENT / "models.csv")
    if args.model not in models:
        print(f"error: unknown model {args.model!r}; experiment/models.csv has: {', '.join(models)}",
              file=sys.stderr)
        return 2
    try:
        client = make_client("answers", models[args.model], args.batch, args.mock, args.base_url,
                             args.allow_real_calls)
        summary = run_answers(args.batch, args.model, client, Path(args.data_root), args.block, args.limit,
                              args.workers, args.mock)
    except RunRefused as exc:
        print(f"refusing: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
