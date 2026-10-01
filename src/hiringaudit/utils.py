"""Small, dependency-free helpers: hashing, stable JSON, JSONL I/O, time."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Iterator


def normalize_newlines(text: str) -> str:
    """Return ``text`` with CRLF / CR line endings converted to LF."""
    return text.replace("\r\n", "\n").replace("\r", "\n")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    """SHA-256 of the UTF-8 encoding of ``text`` (no newline normalisation)."""
    return sha256_bytes(text.encode("utf-8"))


def sha256_file(path: str | Path) -> str:
    """SHA-256 of the raw bytes of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_text_file(path: str | Path) -> str:
    """SHA-256 of a text file after LF normalisation (robust to git autocrlf)."""
    return sha256_text(normalize_newlines(Path(path).read_text(encoding="utf-8")))


def stable_json(obj: Any) -> str:
    """Canonical JSON: sorted keys, no whitespace, UTF-8 characters kept."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)


def stable_hash(obj: Any, length: int | None = None) -> str:
    digest = sha256_text(stable_json(obj))
    return digest[:length] if length else digest


def derive_int(*parts: Any, bits: int = 31) -> int:
    """Deterministic non-negative integer derived from ``parts`` (for seeds)."""
    digest = sha256_text("|".join(str(p) for p in parts))
    return int(digest[:16], 16) % (1 << bits)


def utc_now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def write_text_lf(path: str | Path, text: str) -> None:
    """Write UTF-8 text with LF line endings on every platform."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def atomic_write_json(path: str | Path, data: Any) -> None:
    """Write JSON via a temporary file and an atomic rename."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False, default=str)
        fh.write("\n")
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


def iter_jsonl(path: str | Path) -> Iterator[tuple[int, dict | None, str]]:
    """Yield ``(line_number, parsed_or_None, raw_line)`` for each non-blank line.

    A line that is not valid JSON (e.g. truncated by a crash) yields ``None``
    so callers can report it instead of silently skipping it.
    """
    with open(path, encoding="utf-8") as fh:
        for i, line in enumerate(fh, start=1):
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                yield i, None, line
                continue
            yield i, obj if isinstance(obj, dict) else None, line
