"""The call loop shared by the stages that talk to a model (run_models, later the judge).

It sends a list of items through a client, appends one record per call to a raw JSON
lines file and skips what is already done, so an interrupted run can be started again.
The manifest next to the raw file ties a batch to one model and lists every session.
Nothing here decides whether a call is allowed; that is the client's job
(pipeline/client.py). Standard library only.

Usage:
    summary = run_calls(items, client, settings, extra_body, schema, out_path, workers, fixed_fields)
    update_manifest(manifest_path, header, session)
"""

import json
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from pipeline.client import RunRefused
from pipeline.common import append_jsonl, last_by_key, messages_sha256, read_jsonl, sha256_text, utc_now


def request_params(settings, key, extra_body, schema):
    params = {"temperature": settings["temperature"], "top_p": settings["top_p"],
              "max_tokens": settings["max_tokens"]}
    # per_call: the seed comes from the key, so the same call gives the same answer again.
    params["seed"] = int(sha256_text(key)[:8], 16) if settings["seed"] == "per_call" else settings["seed"]
    params.update(extra_body)
    if settings["json_schema"] and schema is not None:
        params["response_format"] = {"type": "json_schema", "json_schema": {"name": "answer", "schema": schema}}
    return params


def done_keys(path):
    # A key is done when its last record is not an error; keys whose last record is an error are tried again.
    return {key for key, record in last_by_key(read_jsonl(path)).items() if record["error"] is None}


def run_calls(items, client, settings, extra_body, schema, out_path, workers, fixed_fields):
    done = done_keys(out_path)
    todo = [item for item in items if item["key"] not in done]
    lock = threading.Lock()
    errors = 0

    def call_one(item):
        nonlocal errors
        params = request_params(settings, item["key"], extra_body, schema)
        started = utc_now()
        fields = {"text": None, "finish_reason": None, "served_model": None, "usage": None, "error": None}
        try:
            out = client.complete(item["messages"], params)
            for name in ("text", "finish_reason", "served_model", "usage"):
                fields[name] = out[name]
        except Exception as exc:  # one failed call is recorded and retried on the next start
            fields = dict.fromkeys(fields)
            fields["error"] = f"{type(exc).__name__}: {exc}"
        record = {**fixed_fields, **item["meta"], "key": item["key"],
                  "prompt_sha256": messages_sha256(item["messages"]), "params": params, **fields,
                  "started_utc": started, "finished_utc": utc_now()}
        with lock:
            append_jsonl(out_path, record)
            if record["error"] is not None:
                errors += 1

    pool = ThreadPoolExecutor(workers)
    try:
        list(pool.map(call_one, todo))
    finally:
        # On Ctrl-C the calls not yet started are dropped; the file stays valid and the run can resume.
        pool.shutdown(wait=True, cancel_futures=True)
    return {"planned": len(items), "already_done": len(items) - len(todo), "called": len(todo),
            "errors": errors}


def _write_manifest(path, manifest):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def update_manifest(path, header, session):
    # A batch belongs to one model and one kind of run: a changed header field is refused.
    path = Path(path)
    manifest = {**header, "sessions": []}
    if path.exists():
        manifest = json.loads(path.read_text(encoding="utf-8"))
        for field, value in header.items():
            if manifest.get(field) != value:
                raise RunRefused(f"batch {header.get('batch')!r} was started with {field}={manifest.get(field)!r}; "
                                 f"this run has {field}={value!r}; use a new batch name")
    manifest["sessions"].append(session)
    _write_manifest(path, manifest)


def record_summary(path, summary):
    # Puts the summary of the calls into the session update_manifest has just written.
    manifest = json.loads(Path(path).read_text(encoding="utf-8"))
    manifest["sessions"][-1]["summary"] = summary
    _write_manifest(path, manifest)
