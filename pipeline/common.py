"""Shared helpers for the pipeline: paths, tables, JSON lines, models, hashes, git state.

Nothing here calls a model. Standard library only.
"""

import csv
import gzip
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXPERIMENT = ROOT / "experiment"
DATA = ROOT / "data"


def read_text(path):
    return Path(path).read_text(encoding="utf-8")


def read_table(path):
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def raw_exists(path):
    # A raw file exists if it is there as plain text or compressed (path + ".gz").
    path = Path(path)
    return path.exists() or path.with_name(path.name + ".gz").exists()


def read_jsonl(path):
    # A raw file that does not exist yet is an empty file. A line that cannot be read (a record torn
    # by a killed job) is skipped and counted; its key is simply called again on the next start.
    path = Path(path)
    # A raw file may be kept compressed (answers.jsonl.gz, as in the repository); it is read the same way.
    compressed = path.with_name(path.name + ".gz")
    if path.exists():
        opener = open(path, "rb")
    elif compressed.exists():
        opener = gzip.open(compressed, "rb")
    else:
        return []
    records, skipped = [], 0
    with opener as f:
        for line in f:
            if not line.strip():
                continue
            try:
                records.append(json.loads(line.decode("utf-8")))
            except ValueError:  # JSONDecodeError and UnicodeDecodeError are both ValueErrors
                skipped += 1
    if skipped:
        print(f"skipped {skipped} unreadable line(s) in {path}", file=sys.stderr)
    return records


def append_jsonl(path, record):
    # Raw files are append-only: one record per line, written and flushed at once. If a killed job
    # left the last line without its newline, a newline goes first, so the torn fragment stays on
    # its own line and cannot swallow this record.
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    lead = ""
    if path.exists() and path.stat().st_size > 0:
        with open(path, "rb") as f:
            f.seek(-1, 2)
            lead = "" if f.read(1) == b"\n" else "\n"
    with open(path, "a", encoding="utf-8", newline="\n") as f:
        f.write(lead + json.dumps(record, ensure_ascii=False) + "\n")
        f.flush()


def write_csv(path, rows, columns):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def load_models(path):
    # experiment/models.csv, keyed by alias; extra_body is JSON, an empty cell means {}.
    models = {}
    for row in read_table(path):
        row["extra_body"] = json.loads(row["extra_body"]) if row["extra_body"].strip() else {}
        models[row["alias"]] = row
    return models


def load_settings(kind, path=EXPERIMENT / "run_settings.csv"):
    # The sampling settings for "answers" (the audited model) or "judge", from run_settings.csv.
    if kind not in ("answers", "judge"):
        raise ValueError(f"kind must be 'answers' or 'judge', not {kind!r}")
    raw = {row["setting"]: row[kind].strip() for row in read_table(path)}
    seed = raw["seed"]
    json_schema = raw["json_schema"]
    if json_schema not in ("yes", "no"):
        raise ValueError(f"json_schema must be yes or no, not {json_schema!r}")
    return {"temperature": float(raw["temperature"]), "top_p": float(raw["top_p"]),
            "max_tokens": int(raw["max_tokens"]), "seed": seed if seed == "per_call" else int(seed),
            "json_schema": json_schema == "yes"}


def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def messages_sha256(messages):
    return sha256_text(json.dumps(messages, ensure_ascii=False, sort_keys=True))


def utc_now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _git(root, *args):
    try:
        return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, encoding="utf-8")
    except OSError:
        return None


def git_commit(root=ROOT):
    # The commit the code was run at; "" when git cannot say.
    result = _git(root, "rev-parse", "HEAD")
    return result.stdout.strip() if result is not None and result.returncode == 0 else ""


def dirty_files(root=ROOT, paths=("experiment", "pipeline")):
    # Lines of `git status --porcelain` for the given paths. A real run is refused if any.
    result = _git(root, "status", "--porcelain", "--", *paths)
    if result is None or result.returncode != 0:
        # Git cannot say, so the state is not known to be clean.
        return ["git status failed"]
    return [line for line in result.stdout.splitlines() if line.strip()]


def last_by_key(records):
    # Raw files are append-only; the last record per key wins.
    latest = {}
    for record in records:
        latest[record["key"]] = record
    return latest
