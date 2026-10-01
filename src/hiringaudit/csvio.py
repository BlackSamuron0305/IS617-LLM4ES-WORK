"""Reading the project's CSV files (conventions: DATA_FORMAT.md).

Every input table is UTF-8 CSV with a header row and one entity per row. Cells
follow four conventions, implemented here once:

* lists inside a cell are separated by ``" | "`` (LIST_SEP);
* booleans are ``true`` / ``false``;
* an empty cell means missing / not applicable;
* placeholders inside text are ``{name}``.

Readers accept a UTF-8 byte-order mark and CRLF line endings (Excel), so a file
saved from Excel loads the same; hashes of input files are computed after
normalising line endings (``utils.sha256_text_file``).
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

LIST_SEP = " | "
TRUE, FALSE = "true", "false"


class TableError(ValueError):
    """An input table cannot be read (missing file or columns, malformed cells)."""


def read_rows(path: str | Path, required: tuple[str, ...] | list[str] = (), *,
              allowed: tuple[str, ...] | list[str] | None = None) -> list[dict[str, str]]:
    """Rows of ``path`` as dicts of raw (unstripped) cell strings.

    ``required`` columns must be present; with ``allowed`` no other column may be.
    Blank lines are skipped. Errors name the file (and line) concerned.
    """
    p = Path(path)
    if not p.exists():
        raise TableError(f"{p}: file not found")
    with open(p, encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        columns = list(reader.fieldnames or [])
        rows = []
        for r in reader:
            if None in r:
                raise TableError(f"{p.name} line {reader.line_num}: more cells than header columns")
            if not any((v or "").strip() for v in r.values()):
                continue
            rows.append({k: (v if v is not None else "") for k, v in r.items()})
    missing = [c for c in required if c not in columns]
    if missing:
        raise TableError(f"{p}: missing columns {missing}")
    if allowed is not None:
        extra = [c for c in columns if c not in allowed]
        if extra:
            raise TableError(f"{p}: unknown columns {extra}")
    dup = sorted({c for c in columns if columns.count(c) > 1})
    if dup:
        raise TableError(f"{p}: duplicate columns {dup}")
    return rows


def where(path: str | Path, key: str) -> str:
    return f"{Path(path).name} [{key}]"


def text(value: str | None) -> str:
    return (value or "").strip()


def optional(value: str | None) -> str | None:
    """Stripped text, or None for an empty cell."""
    v = text(value)
    return v or None


def boolean(value: str | None, at: str) -> bool:
    v = text(value).lower()
    if v == TRUE:
        return True
    if v == FALSE:
        return False
    raise TableError(f"{at}: expected true or false, got {value!r}")


def integer(value: str | None, at: str) -> int:
    try:
        return int(text(value))
    except ValueError as e:
        raise TableError(f"{at}: expected a whole number, got {value!r}") from e


def number(value: str | None, at: str) -> float:
    try:
        return float(text(value))
    except ValueError as e:
        raise TableError(f"{at}: expected a number, got {value!r}") from e


def items(value: str | None) -> list[str]:
    """A ``" | "``-separated list cell (empty cell = empty list)."""
    v = text(value)
    if not v:
        return []
    return [x.strip() for x in v.split(LIST_SEP.strip()) if x.strip()]


def keyword_or_items(value: str | None, keywords: tuple[str, ...], at: str) -> str | list[str]:
    """A keyword such as ``all`` / ``pilot``, or a list of items."""
    v = text(value)
    if not v:
        raise TableError(f"{at}: empty cell (expected {' / '.join(keywords)} or a ' | '-separated list)")
    return v if v in keywords else items(v)


def json_object(value: str | None, at: str) -> dict[str, Any]:
    """A JSON object cell (empty cell = {})."""
    v = text(value)
    if not v:
        return {}
    try:
        obj = json.loads(v)
    except json.JSONDecodeError as e:
        raise TableError(f"{at}: not valid JSON ({e.msg}): {v!r}") from e
    if not isinstance(obj, dict):
        raise TableError(f"{at}: expected a JSON object, got {v!r}")
    return obj


def write_rows(path: str | Path, columns: list[str], rows: list[dict]) -> None:
    """Write a table with the project conventions (UTF-8, LF, header row)."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=columns, lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: _cell(r.get(k)) for k in columns})


def _cell(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, bool):
        return TRUE if v else FALSE
    if isinstance(v, (list, tuple)):
        return LIST_SEP.join(str(x) for x in v)
    if isinstance(v, dict):
        return json.dumps(v) if v else ""
    return str(v)
