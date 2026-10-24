"""Shared helpers for the pipeline: paths, tables, JSON lines, models, hashes, git state.

Nothing here calls a model. Standard library only.
"""

import csv
import hashlib
import json
import subprocess
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


def read_jsonl(path):
    # A raw file that does not exist yet is an empty file.
    path = Path(path)
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def append_jsonl(path, record):
    # Raw files are append-only: one record per line, written and flushed at once.
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
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
