"""Raw JSONL -> processed CSV tables (contract section 7 + v0.2 A11/A18). Never modifies raw.

Outputs in ``data/processed/<run_id>/``:
    evaluations.csv, forced_choice.csv, principle.csv   (column order: src/hiringaudit/schemas.py)
    parse_summary.json                                  counts and provenance

Every raw record is re-parsed from ``raw_output``. To stop a parser change after
unblinding from silently changing the analysed sample (review M11), ``parse``
refuses when PARSER_VERSION or the parser fingerprint (source of the parser
modules + config/text_flags.csv) differs from the one recorded in the run
manifest, unless ``exploratory=True``: then the tables go to
``data/processed/<run_id>__exploratory/``, marked as exploratory.

Records per record_id (review M7): api_error records may be followed by a later
attempt in a resumed session. The table keeps the single non-api_error record
(two non-api_error records for one id are an error) or, if every attempt
failed, the last api_error record. Corrupt raw lines are reported, never
silently dropped.
"""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd

from .config import NationalitySet
from .parsing import PARSER_VERSION, ParseResult, parse_response
from .schemas import EVALUATION_COLUMNS, FORCED_CHOICE_COLUMNS, PRINCIPLE_COLUMNS, TEXT_FLAG_COLUMNS
from .utils import atomic_write_json, iter_jsonl, sha256_file, sha256_text, utc_now_iso

EXPLORATORY_SUFFIX = "__exploratory"
_PARSER_MODULES = ("parsing.py", "schemas.py", "parse_outputs.py")


class DuplicateRecordError(RuntimeError):
    pass


class ParserMismatch(RuntimeError):
    pass


def parser_fingerprint(text_flags_path: str | Path) -> str:
    """SHA-256 over the parser source files and the text-flag table (config/text_flags.csv)."""
    here = Path(__file__).resolve().parent
    parts = [(here / f).read_text(encoding="utf-8").replace("\r\n", "\n") for f in _PARSER_MODULES]
    parts.append(Path(text_flags_path).read_text(encoding="utf-8").replace("\r\n", "\n"))
    return sha256_text("\n\x00\n".join(parts))


# --------------------------------------------------------------------------- #
# text flags and pronouns (exploratory, crude)
# --------------------------------------------------------------------------- #
def compile_text_flags(flag_table: dict, nationalities: NationalitySet) -> dict[str, re.Pattern]:
    compiled = {}
    for flag in TEXT_FLAG_COLUMNS:
        spec = flag_table["flags"].get(flag, {"patterns": []})
        pats = list(spec.get("patterns", []))
        exclude = set(spec.get("exclude", []))
        countries = [n.country for n in nationalities.conditions if n.country]
        for n in nationalities.conditions:
            if spec.get("include_demonyms") and n.demonym and n.demonym not in exclude:
                # a demonym that starts a country name ("Saudi" in "Saudi Arabia") is
                # matched only where it is not part of that name (base-country locations)
                rests = [c[len(n.demonym):] for c in countries if c.startswith(n.demonym + " ")]
                pats.append(re.escape(n.demonym) + (f"(?!{'|'.join(map(re.escape, rests))})" if rests else ""))
            if spec.get("include_country_names") and n.country and n.country not in exclude:
                pats.append(re.escape(n.country))
        wrapped = [p if r"\b" in p else rf"\b(?:{p})\b" for p in pats]
        compiled[flag] = re.compile("|".join(wrapped), re.IGNORECASE) if wrapped else re.compile(r"(?!x)x")
    return compiled


def text_flags(reason, patterns: dict[str, re.Pattern]) -> dict:
    if not isinstance(reason, str):
        return {f: pd.NA for f in TEXT_FLAG_COLUMNS}
    return {f: int(bool(p.search(reason))) for f, p in patterns.items()}


_PRONOUNS = {
    "he": re.compile(r"\b(he|him|his|himself)\b", re.IGNORECASE),
    "she": re.compile(r"\b(she|her|hers|herself)\b", re.IGNORECASE),
    "they": re.compile(r"\b(they|them|their|theirs|themselves|themself)\b", re.IGNORECASE),
}


def pronoun_gender(reason) -> object:
    """he | she | they | none by the most frequent pronoun family in the reason (A18).

    Crude: "they" may refer to other people; an exact he/she tie gives "none".
    """
    if not isinstance(reason, str):
        return pd.NA
    counts = {k: len(p.findall(reason)) for k, p in _PRONOUNS.items()}
    if counts["he"] or counts["she"]:
        if counts["he"] == counts["she"]:
            return "none"
        return "he" if counts["he"] > counts["she"] else "she"
    return "they" if counts["they"] else "none"


# --------------------------------------------------------------------------- #
# reading raw
# --------------------------------------------------------------------------- #
def read_raw(raw_dir: str | Path) -> tuple[list[dict], list[int]]:
    path = Path(raw_dir) / "responses.jsonl"
    if not path.exists():
        raise FileNotFoundError(f"no raw responses at {path}")
    records, corrupt = [], []
    for lineno, obj, _ in iter_jsonl(path):
        (corrupt.append(lineno) if obj is None else records.append(obj))
    return records, corrupt


def select_records(records: list[dict]) -> tuple[list[dict], int]:
    """One record per record_id (see module docstring). Returns (records, n superseded)."""
    by_id: dict[str, list[dict]] = defaultdict(list)
    for r in records:
        by_id[r["record_id"]].append(r)
    out, superseded = [], 0
    for rid, recs in by_id.items():
        good = [r for r in recs if r.get("parse_status") != "api_error" and r.get("api_error") is None]
        if len(good) > 1:
            raise DuplicateRecordError(f"record_id {rid} has {len(good)} non-api_error records")
        out.append(good[0] if good else recs[-1])
        superseded += len(recs) - 1
    return out, superseded


# --------------------------------------------------------------------------- #
# row builders
# --------------------------------------------------------------------------- #
def _reparse(rec: dict) -> ParseResult:
    if rec.get("api_error") is not None or rec.get("parse_status") == "api_error":
        return ParseResult("api_error")
    return parse_response(rec.get("raw_output"), rec["task_type"])


def _reason(res: ParseResult):
    src = res.parsed or res.extracted
    r = src.get("reason") if isinstance(src, dict) else None
    return r if isinstance(r, str) else pd.NA


def _val(res: ParseResult, key: str):
    """Outcome values are taken ONLY from schema-valid responses (never coerced)."""
    return res.parsed[key] if res.parse_status == "ok" else pd.NA


def host_national(code, base_country):
    """Nationality code == the CV's base country (user request 2026-10-01); NA when
    the record has no base country (records written before the setting existed)."""
    if not base_country or code is None:
        return pd.NA
    return code == base_country


def endorses_neutrality(answer, keying: str | None):
    """Derived from answer x keying (A11); NA for control items or missing answers."""
    if answer is pd.NA or answer is None or keying not in ("pro", "reverse"):
        return pd.NA
    if keying == "pro":
        return answer
    return "no" if answer == "yes" else "yes"


def build_tables(records: list[dict], nationalities: NationalitySet, flag_patterns: dict[str, re.Pattern]):
    ev_rows, fc_rows, pr_rows = [], [], []
    statuses: Counter = Counter()
    for rec in records:
        res = _reparse(rec)
        statuses[(rec["model_alias"], rec["prompt_condition"], res.parse_status)] += 1
        common = {"run_id": rec["run_id"], "record_id": rec["record_id"], "is_mock": bool(rec["is_mock"]),
                  "provider": rec["provider"], "model_id": rec["model_id"], "model_alias": rec["model_alias"]}
        tail = {"parse_status": res.parse_status, "refusal": res.parse_status == "refusal",
                "api_error": res.parse_status == "api_error"}
        meta = {"execution_index": rec.get("execution_index"), "seed": rec.get("seed"),
                "model_revision": rec.get("model_revision")}
        prov = {"prompt_sha256": rec.get("prompt_sha256"), "user_prompt_version": rec.get("user_prompt_version"),
                "n_json_objects": res.n_json_objects, "near_miss": bool(res.near_miss)}
        reason = _reason(res)
        task = rec["task_type"]
        if task == "independent":
            code = rec["nationalities"][0]
            try:
                nat = nationalities.by_code(code)
            except KeyError as e:
                raise ValueError(f"record {rec['record_id']}: nationality code {code!r} is not in "
                                 f"stimuli/nationalities.csv") from e
            interview = _val(res, "interview")
            ev_rows.append({
                **common, "trial_id": rec["trial_id"], "prompt_condition": rec["prompt_condition"],
                "occupation": rec["occupation"], "base_cv_id": rec["base_cv_ids"][0],
                "qualification_tier": rec["qualification_tier"], "nationality": code,
                "nationality_group": nat.group, "subregion": nat.subregion,
                "arab_identity_contested": nat.arab_identity_contested, "repetition": rec["repetition"],
                "overall_fit": _val(res, "overall_fit"),
                "interview": pd.NA if interview is pd.NA else int(interview == "yes"),
                "confidence": _val(res, "confidence"), "reason": reason, **tail,
                **text_flags(reason, flag_patterns), "pronoun_gender": pronoun_gender(reason),
                "prompt_variant": rec.get("prompt_variant"), "clone_type": rec.get("clone_type"), **meta,
                "arm": rec.get("arm", "primary"), "temperature": rec.get("temperature"), **prov,
                "base_country": rec.get("base_country"),
                "host_national": host_national(code, rec.get("base_country")),
            })
        elif task == "forced_choice":
            choice = _val(res, "choice")
            cv_a, cv_b = rec["base_cv_ids"]
            nat_a, nat_b = rec["nationalities"]
            fc_rows.append({
                **common, "trial_id": rec["trial_id"], "quad_id": rec["quad_id"],
                "prompt_condition": rec["prompt_condition"], "occupation": rec["occupation"],
                "qualification_tier": rec["qualification_tier"], "cv_a": cv_a, "cv_b": cv_b,
                "nationality_a": nat_a, "nationality_b": nat_b, "fc_order": rec["fc_order"], "choice": choice,
                "chosen_nationality": pd.NA if choice is pd.NA else (nat_a if choice == "A" else nat_b),
                "chosen_cv": pd.NA if choice is pd.NA else (cv_a if choice == "A" else cv_b),
                "confidence": _val(res, "confidence"), "reason": reason, **tail,
                "prompt_variant": rec.get("prompt_variant"), **meta, "repetition": rec["repetition"], **prov,
                "base_country": rec.get("base_country"),
                "host_national_a": host_national(nat_a, rec.get("base_country")),
                "host_national_b": host_national(nat_b, rec.get("base_country")),
            })
        elif task == "principle_probe":
            answer = _val(res, "answer")
            pr_rows.append({
                **common, "probe_id": rec.get("item_id"), "occupation": rec["occupation"],
                "repetition": rec["repetition"],
                "endorses_neutrality": endorses_neutrality(answer, rec.get("keying")),
                "agreement": _val(res, "agreement"), "reason": reason, **tail,
                "item_id": rec.get("item_id"), "keying": rec.get("keying"), "item_type": rec.get("item_type"),
                "context": rec.get("context"), "answer": answer, "prompt_variant": rec.get("prompt_variant"),
                **meta, **prov,
            })
        else:
            raise ValueError(f"record {rec['record_id']}: unknown task_type {task}")

    ev = pd.DataFrame(ev_rows, columns=list(EVALUATION_COLUMNS))
    fc = pd.DataFrame(fc_rows, columns=list(FORCED_CHOICE_COLUMNS))
    pr = pd.DataFrame(pr_rows, columns=list(PRINCIPLE_COLUMNS))
    int_cols = {
        "ev": ["repetition", "overall_fit", "interview", "confidence", "execution_index", "seed", "n_json_objects",
               *TEXT_FLAG_COLUMNS],
        "fc": ["confidence", "execution_index", "seed", "repetition", "n_json_objects"],
        "pr": ["repetition", "agreement", "execution_index", "seed", "n_json_objects"],
    }
    for key, df in (("ev", ev), ("fc", fc), ("pr", pr)):
        for c in int_cols[key]:
            df[c] = pd.array(df[c].tolist(), dtype="Int64") if len(df) else df[c].astype("Int64")
    return ev, fc, pr, statuses


def _write_csv(df: pd.DataFrame, path: Path) -> None:
    df.to_csv(path, index=False, lineterminator="\n", encoding="utf-8", na_rep="")


def recorded_parser(raw_dir: Path) -> dict:
    man = Path(raw_dir) / "run_manifest.json"
    if not man.exists():
        return {}
    m = json.loads(man.read_text(encoding="utf-8"))
    return {"parser_version": m.get("parser_version"), "parser_fingerprint": m.get("parser_fingerprint")}


def parse_outputs(raw_dir: str | Path, processed_dir: str | Path, nationalities: NationalitySet,
                  flag_table: dict, text_flags_path: str | Path | None = None,
                  exploratory: bool = False) -> dict:
    raw_dir, processed_dir = Path(raw_dir), Path(processed_dir)
    current = {"parser_version": PARSER_VERSION,
               "parser_fingerprint": parser_fingerprint(text_flags_path) if text_flags_path else None}
    recorded = recorded_parser(raw_dir)
    mismatch = [k for k in current if recorded.get(k) is not None and current[k] is not None
                and recorded[k] != current[k]]
    if mismatch and not exploratory:
        raise ParserMismatch(
            f"the parser differs from the one recorded for this run ({', '.join(mismatch)}: recorded "
            f"{[recorded[k] for k in mismatch]}, current {[current[k] for k in mismatch]}). Re-parsing would "
            f"change the analysed sample; use --exploratory to write clearly marked exploratory tables.")
    if exploratory:
        processed_dir = processed_dir.with_name(processed_dir.name + EXPLORATORY_SUFFIX)

    records, corrupt = read_raw(raw_dir)
    selected, superseded = select_records(records)
    ev, fc, pr, statuses = build_tables(selected, nationalities, compile_text_flags(flag_table, nationalities))
    processed_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(ev, processed_dir / "evaluations.csv")
    _write_csv(fc, processed_dir / "forced_choice.csv")
    _write_csv(pr, processed_dir / "principle.csv")
    by_status: Counter = Counter()
    for (_, _, s), n in statuses.items():
        by_status[s] += n
    summary = {
        "run_id": records[0]["run_id"] if records else None,
        "processed_dir": str(processed_dir),
        "parse_mode": "exploratory" if exploratory else "confirmatory",
        "parsed_utc": utc_now_iso(),
        **current,
        "recorded_parser": recorded,
        "raw_file": str(raw_dir / "responses.jsonl"),
        "raw_sha256": sha256_file(raw_dir / "responses.jsonl"),
        "n_raw_records": len(records),
        "n_records": len(selected),
        "n_superseded_api_error_records": superseded,
        "corrupt_raw_lines": corrupt,
        "is_mock": sorted({bool(r["is_mock"]) for r in records}),
        "rows": {"evaluations": len(ev), "forced_choice": len(fc), "principle": len(pr)},
        "parse_status_counts": dict(sorted(by_status.items())),
        "parse_status_by_model_condition": [
            {"model_alias": m, "prompt_condition": c, "parse_status": s, "n": n}
            for (m, c, s), n in sorted(statuses.items())],
    }
    warnings = []
    if any(summary["is_mock"]):
        warnings.append("SYNTHETIC MOCK DATA - NOT RESULTS")
    if exploratory:
        warnings.append("EXPLORATORY PARSE: parser differs from the recorded one or was re-run as exploratory")
        (processed_dir / "EXPLORATORY_PARSE.txt").write_text(
            "These tables were produced by `parse --exploratory` and are NOT the confirmatory processed data.\n"
            f"Recorded parser: {recorded}\nCurrent parser: {current}\n", encoding="utf-8")
    if warnings:
        summary["WARNING"] = " | ".join(warnings)
    atomic_write_json(processed_dir / "parse_summary.json", summary)
    return summary
