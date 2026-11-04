"""Stage 1: send the prompts of the experiment to one model and store the raw answers.

The default is a mock run, which needs no server. A real run is refused unless every
condition in pipeline/core/client.py holds; it is started only with the team's explicit
approval (CLAUDE.md, "Compute and models"). Raw answers are appended to
data/raw/<batch>/answers.jsonl; a run that stopped can be started again with the same
command and continues where it ended.

Usage:
    python -m pipeline.answers.run_models --batch mock_x --model qwen3-32b --mock --block 1 --limit 30
    python -m pipeline.answers.run_models --batch pilot1 --model qwen3-32b --base-url URL --allow-real-calls
"""

import argparse
import json
import sys
from pathlib import Path

from pipeline.design.build_runs import build_runs
from pipeline.core.calls import begin_stage, done_keys, check_mock_label, record_summary, run_calls
from pipeline.core.client import RunRefused, make_client
from pipeline.core.common import DATA, EXPERIMENT, batch_dir, load_models, load_settings
from pipeline.answers.parse_answers import answer_schema


def plan_items(runs, blocks, limit, variants=None, wordings=None, max_repetitions=None, shard=None):
    # One item per repetition of every run, in build order; the key names run and repetition.
    items = []
    for run in runs:
        if blocks is not None and run["block"] not in blocks:
            continue
        if variants is not None and run["variant"] not in variants:
            continue
        if wordings is not None and run["wording"] not in wordings:
            continue
        messages = [{"role": "system", "content": run["system"]}, {"role": "user", "content": run["user"]}]
        for repetition in range(1, min(run["repetitions"], max_repetitions or run["repetitions"]) + 1):
            items.append({"key": f"{run['run_id']}__r{repetition}", "messages": messages,
                          "meta": {"run_id": run["run_id"], "repetition": repetition, "block": run["block"]}})
    if shard is not None:
        # (k, n): every n-th item starting at k, so that n jobs can share one list without overlap.
        k, n = shard
        items = items[k::n]
    return items if limit is None else items[:limit]


def run_answers(batch, model_alias, client, data_root, blocks=None, limit=None, workers=8, mock=False,
                variants=("base",), wordings=None, max_repetitions=None, shard=None):
    models = load_models(EXPERIMENT / "config/models.csv")
    if model_alias not in models:
        raise RunRefused(f"unknown model alias {model_alias!r}; experiment/config/models.csv has: {', '.join(models)}")
    model = models[model_alias]
    check_mock_label(client, mock, batch)
    runs, _, _, problems = build_runs(list(variants))
    if problems:
        raise RunRefused("build_runs reports problems: " + "; ".join(problems[:5]))
    settings = load_settings("answers")
    items = plan_items(runs, blocks, limit, list(variants), wordings, max_repetitions, shard)
    keys = {run["answer_keys"] for run in runs if run["variant"] in variants}
    if len(keys) > 1 and settings["json_schema"]:
        raise RunRefused("the chosen variants ask for different answer keys; with json_schema yes run one variant at a time")
    folder = batch_dir(Path(data_root), "raw", batch)
    # The manifest comes first: a batch that belongs to another model is refused before any call.
    fixed_fields = begin_stage(folder / "manifest.json", "answers", batch, model_alias, model, mock, settings,
                               {"blocks": blocks, "limit": limit, "variants": list(variants), "wordings": wordings,
                                "max_repetitions": max_repetitions, "shard": shard}, client)
    summary = run_calls(items, client, settings, model["extra_body"], answer_schema(next(iter(keys))), folder / "answers.jsonl",
                        workers, fixed_fields)
    record_summary(folder / "manifest.json", summary)
    return summary


def count_remaining(batch, data_root, blocks=None, variants=("base",), wordings=None, max_repetitions=None, shard=None):
    # How many calls of the plan are not done in the batch's raw file. Calls no model and needs no server.
    runs, _, _, problems = build_runs(list(variants))
    if problems:
        raise RunRefused("build_runs reports problems: " + "; ".join(problems[:5]))
    items = plan_items(runs, blocks, None, list(variants), wordings, max_repetitions, shard)
    done = done_keys(batch_dir(Path(data_root), "raw", batch) / "answers.jsonl")
    return {"planned": len(items), "remaining": sum(item["key"] not in done for item in items)}


def parse_shard(text):
    if text is None:
        return None
    k, _, n = text.partition("/")
    if not (k.isdigit() and n.isdigit() and 0 <= int(k) < int(n)):
        raise ValueError(f"--shard must be K/N with 0 <= K < N, not {text!r}")
    return int(k), int(n)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Send the experiment's prompts to one model (mock by default).")
    parser.add_argument("--batch", required=True, help="name of the batch; a mock batch starts with 'mock'")
    parser.add_argument("--model", required=True, help="alias in experiment/config/models.csv")
    parser.add_argument("--block", type=int, action="append", help="only this block (repeatable)")
    parser.add_argument("--variant", action="append", help="only this prompt variant (repeatable; default: base). "
                        "See experiment/prompts/variants.csv")
    parser.add_argument("--wording", type=int, action="append", choices=(1, 2, 3),
                        help="only this task wording (repeatable); a pilot uses --wording 1")
    parser.add_argument("--max-repetitions", type=int,
                        help="at most N repetitions of each prompt; a pilot uses 1")
    parser.add_argument("--shard", help="K/N: only every N-th call, starting at K (0 <= K < N); one batch name per shard")
    parser.add_argument("--remaining", action="store_true",
                        help="only print how many calls of the plan are not done yet (calls no model, needs no server)")
    parser.add_argument("--limit", type=int, help="only the first N calls")
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--mock", action="store_true", help="use the mock client, no server needed")
    parser.add_argument("--base-url", help="address of the server, for example http://localhost:8000/v1")
    parser.add_argument("--allow-real-calls", action="store_true",
                        help="give only with the team's explicit approval of real model calls")
    parser.add_argument("--data-root", default=str(DATA))
    args = parser.parse_args(argv)

    models = load_models(EXPERIMENT / "config/models.csv")
    if args.model not in models:
        print(f"error: unknown model {args.model!r}; experiment/config/models.csv has: {', '.join(models)}",
              file=sys.stderr)
        return 2
    try:
        shard = parse_shard(args.shard)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if args.remaining:
        try:
            summary = count_remaining(args.batch, Path(args.data_root), args.block, tuple(args.variant or ("base",)),
                                      args.wording, args.max_repetitions, shard)
        except RunRefused as exc:
            print(f"refusing: {exc}", file=sys.stderr)
            return 2
        print(json.dumps(summary))
        return 0
    try:
        client = make_client("answers", models[args.model], args.batch, args.mock, args.base_url,
                             args.allow_real_calls)
        summary = run_answers(args.batch, args.model, client, Path(args.data_root), args.block, args.limit,
                              args.workers, args.mock, tuple(args.variant or ("base",)), args.wording,
                              args.max_repetitions, shard)
    except RunRefused as exc:
        print(f"refusing: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
