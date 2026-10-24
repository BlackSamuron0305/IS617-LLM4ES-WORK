"""The call loop shared by the stages that talk to a model (run_models and run_judge).

It sends a list of items through a client, appends one record per call to a raw JSON
lines file and skips what is already done, so an interrupted run can be started again.
The manifest next to the raw file ties a batch to one audited model and lists every session.
Whether a real call is allowed is decided by make_client (pipeline/client.py); the stages here
only refuse a real client that did not come from it. Standard library only.

Usage:
    check_mock_label(client, mock, batch)
    fixed_fields = begin_stage(manifest_path, kind, batch, model_alias, model, mock, settings, session_extra, client)
    summary = run_calls(items, client, settings, extra_body, schema, out_path, workers, fixed_fields)
    record_summary(manifest_path, summary)
"""

import json
import os
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from pipeline.client import MockClient, RunRefused, check_mock_batch
from pipeline.common import (append_jsonl, dirty_files, git_commit, last_by_key, messages_sha256, read_jsonl,
                             sha256_text, utc_now)


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
    # Written to a temp file next to the manifest and then moved over it, so that a job killed
    # during the write leaves the old manifest, never half of a new one.
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    try:
        temp.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
        os.replace(temp, path)
    except BaseException:
        temp.unlink(missing_ok=True)
        raise


def update_manifest(path, header, session):
    # A manifest belongs to one model and one kind of run: a changed header field is refused. (A batch
    # belongs to one audited model; each judge that codes it has a manifest of its own.)
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


def check_mock_label(client, mock, batch):
    # The label "mock" must match the client, or mock output would pass for a result (or the reverse).
    if isinstance(client, MockClient) != mock:
        raise RunRefused("mock=True needs the mock client, and the mock client needs mock=True")
    if mock:
        check_mock_batch(batch)
    elif getattr(client, "approved", False) is not True:
        # make_client is where the conditions for a real run are checked; a client made any other way skipped them.
        raise RunRefused("a real client must come from make_client, which checks every condition for a real run; "
                         "this client was not approved by it")


def server_facts(client, mock):
    # What the manifest records about the server of a session. MODEL_PATH and VLLM_ARGS are set by the
    # Slurm script (cluster/run_vllm.sbatch) that starts vLLM; empty when it did not set them. A mock
    # run has no server.
    if mock:
        return {"model_path": "", "vllm_args": "", "base_url": None}
    return {"model_path": os.environ.get("MODEL_PATH", ""), "vllm_args": os.environ.get("VLLM_ARGS", ""),
            "base_url": client.base_url}


def begin_stage(manifest_path, kind, batch, model_alias, model, mock, settings, session_extra, client):
    # Writes the manifest header and a new session before any call, so that a batch that belongs to
    # another model is refused first. Returns the fields every raw record of the stage carries.
    header = {"batch": batch, "kind": kind, "model_alias": model_alias, "model_id": model["model_id"],
              "revision": model["revision"], "mock": mock}
    session = {"started_utc": utc_now(), "git_commit": git_commit(), "dirty": dirty_files(), **session_extra,
               **server_facts(client, mock), "settings": settings, "summary": None}
    update_manifest(manifest_path, header, session)
    return {"batch": batch, "model_alias": model_alias, "model_id": model["model_id"], "kind": kind, "mock": mock}
