"""Parse one raw model output: extract JSON, validate, classify. Never coerces.

Classification (``parse_status``):
    api_error         no output because the call failed (set by the runner)
    empty             output is empty or whitespace (after removing <think> blocks)
    refusal           no schema-valid JSON AND the text matches a refusal pattern
    malformed_json    no JSON object could be extracted
    schema_violation  a JSON object was found but it does not match the schema
    ok                a JSON object matching the schema was found

Extraction rule (documented, review L4): the FIRST JSON object in the output is
the answer (whole text, else first fenced block, else first decodable ``{``). A
later "correction" in the same output is ignored. ``n_json_objects`` counts the
objects found so such cases can be inspected.

Diagnostics that never change the classification:
    n_json_objects    number of top-level JSON objects found in the output
    near_miss         True when a schema-violating object WOULD validate after a
                      trivial normalisation (enum case, integral float/string
                      numbers, extra keys dropped). Diagnostic only: the value is
                      never used as an outcome.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

from jsonschema import Draft202012Validator

from .schemas import SCHEMA_BY_TASK

PARSER_VERSION = 2

_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)
_FENCE_RE = re.compile(r"```(?:json|JSON)?\s*(.*?)```", re.DOTALL)
REFUSAL_RE = re.compile(
    r"(I['’]m sorry|I am sorry|I apologi[sz]e|"
    r"\bI (?:can(?:no|['’])t|cannot|won['’]t|will not|am (?:not able|unable)|must decline|refuse|decline)\b|"
    r"\bI['’]m not (?:comfortable|able|willing)\b|\bI am not (?:comfortable|willing)\b|"
    r"\bunable to (?:help|assist|comply|choose|decide|evaluate|provide|make)\b|"
    r"\bnot (?:appropriate|possible|able) (?:for me )?to (?:choose|decide|rank|evaluate|assess|compare)\b|"
    r"\bas an AI\b|\bas a (?:large )?language model\b|\bI (?:do not|don['’]t) feel comfortable\b)",
    re.IGNORECASE,
)

_VALIDATORS = {task: Draft202012Validator(schema) for task, schema in SCHEMA_BY_TASK.items()}


@dataclass
class ParseResult:
    parse_status: str
    parsed: dict | None = None          # schema-valid object (only when ok)
    extracted: dict | None = None       # the first JSON object found (for inspection)
    refusal: bool = False
    errors: list[str] = field(default_factory=list)
    n_json_objects: int = 0
    near_miss: bool = False


def strip_think(text: str) -> str:
    return _THINK_RE.sub("", text)


def all_json_objects(text: str) -> list[dict]:
    """Every top-level JSON object in ``text``, in order of appearance."""
    t = strip_think(text).strip()
    if not t:
        return []
    try:
        obj = json.loads(t)
        return [obj] if isinstance(obj, dict) else []
    except json.JSONDecodeError:
        pass
    decoder = json.JSONDecoder()
    out, i = [], 0
    while i < len(t):
        if t[i] == "{":
            try:
                obj, end = decoder.raw_decode(t, i)
            except json.JSONDecodeError:
                i += 1
                continue
            if isinstance(obj, dict):
                out.append(obj)
            i = end
        else:
            i += 1
    return out


def extract_json_object(text: str) -> dict | None:
    """The first JSON object (whole text, else first fenced block, else first decodable ``{``)."""
    t = strip_think(text).strip()
    if not t:
        return None
    try:
        obj = json.loads(t)
        if isinstance(obj, dict):
            return obj
    except json.JSONDecodeError:
        pass
    for m in _FENCE_RE.finditer(t):
        try:
            obj = json.loads(m.group(1).strip())
            if isinstance(obj, dict):
                return obj
        except json.JSONDecodeError:
            continue
    objs = all_json_objects(t)
    return objs[0] if objs else None


def looks_like_refusal(text: str) -> bool:
    return bool(REFUSAL_RE.search(text or ""))


def _normalise(obj: dict, task_type: str) -> dict:
    """Trivial normalisation for the near-miss diagnostic ONLY."""
    schema = SCHEMA_BY_TASK[task_type]
    out = {}
    for k, spec in schema["properties"].items():
        if k not in obj:
            continue
        v = obj[k]
        if "enum" in spec and isinstance(v, str):
            low = {e.lower(): e for e in spec["enum"]}
            v = low.get(v.strip().lower(), v)
        if spec.get("type") == "integer":
            if isinstance(v, str) and re.fullmatch(r"\s*-?\d+(\.0+)?\s*", v):
                v = int(float(v))
            elif isinstance(v, float) and v.is_integer():
                v = int(v)
        out[k] = v
    return out


def parse_response(raw_output: str | None, task_type: str) -> ParseResult:
    if task_type not in _VALIDATORS:
        raise ValueError(f"unknown task_type {task_type}")
    if raw_output is None or not strip_think(raw_output).strip():
        return ParseResult("empty")
    n_obj = len(all_json_objects(raw_output))
    obj = extract_json_object(raw_output)
    refusal_hit = looks_like_refusal(raw_output)
    if obj is None:
        if refusal_hit:
            return ParseResult("refusal", refusal=True, n_json_objects=n_obj)
        return ParseResult("malformed_json", errors=["no JSON object found"], n_json_objects=n_obj)
    n_obj = max(n_obj, 1)
    validator = _VALIDATORS[task_type]
    errors = sorted(e.message for e in validator.iter_errors(obj))
    if errors:
        near = not list(validator.iter_errors(_normalise(obj, task_type)))
        status = "refusal" if refusal_hit else "schema_violation"
        return ParseResult(status, extracted=obj, refusal=refusal_hit, errors=errors, n_json_objects=n_obj,
                           near_miss=near)
    return ParseResult("ok", parsed=obj, extracted=obj, n_json_objects=n_obj)
