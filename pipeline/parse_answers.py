"""Stage 2: turn the raw answers of a batch into one clean table.

Reads data/raw/<batch>/answers.jsonl (the last record per key wins), reads the answer out of
each text, joins the metadata of the prompt and writes data/processed/<batch>/answers.csv,
one row per call. A row whose answer cannot be read is kept, with the reason in
parse_status. prompt_matches says whether the prompt behind the record is still the one
build_runs builds today (1) or not (0). Never calls a model.

Usage:
    python -m pipeline.parse_answers --batch mock_x
    python -m pipeline.parse_answers --batch pilot1 --data-root data
"""

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

from pipeline.build_runs import ANSWER_KEYS, CHECK_LETTERS, build_runs
from pipeline.common import DATA, last_by_key, messages_sha256, read_jsonl, write_csv

RATINGS = ("low", "medium", "high")
RECOMMENDATIONS = ("grant", "refer", "refuse")

# The shape of an answer, sent to the server when the setting json_schema is yes.
ANSWER_SCHEMA = {
    "type": "object",
    "properties": {
        "risk_score": {"type": "integer", "minimum": 0, "maximum": 100},
        "risk_rating": {"type": "string", "enum": list(RATINGS)},
        "further_checks": {"type": "array", "items": {"type": "string", "enum": list(CHECK_LETTERS)}},
        "recommendation": {"type": "string", "enum": list(RECOMMENDATIONS)},
        "reason": {"type": "string"},
    },
    "required": list(ANSWER_KEYS),
    "additionalProperties": False,
}

RUN_COLUMNS = ["policy_version", "applicant_id", "file_profile", "indicator", "savings", "country", "demonym",
               "group", "wealth_group", "wording"]
ANSWER_COLUMNS = ["batch", "model_alias", "key", "run_id", "repetition", "block", *RUN_COLUMNS, "prompt_matches",
                  "parse_status", "risk_score", "risk_rating", "further_checks", "n_checks", "recommendation",
                  "reason", "finish_reason", "error"]
VALUE_FIELDS = ("risk_score", "risk_rating", "further_checks", "n_checks", "recommendation")


def extract_json(text):
    # The first JSON object in the text, or None. Handles code fences, prose around the object
    # and <think> blocks that contain braces.
    if not isinstance(text, str):
        return None
    try:
        whole = json.loads(text.strip())
        if isinstance(whole, dict):
            return whole
    except ValueError:
        pass
    decoder = json.JSONDecoder()
    position = text.find("{")
    while position != -1:
        try:
            found, _ = decoder.raw_decode(text, position)
            if isinstance(found, dict):
                return found
        except (ValueError, RecursionError):
            pass
        position = text.find("{", position + 1)
    return None


def _score(value):
    # An integer 0..100; a float with an integer value is accepted, a bool or a string is not.
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    if isinstance(value, float):
        if not value.is_integer():
            return None
        value = int(value)
    return value if 0 <= value <= 100 else None


def _checks(value):
    # The sorted unique letters, or None if the value is not a list of single letters from the menu.
    if not isinstance(value, list):
        return None
    letters = set()
    for item in value:
        letter = item.strip().upper() if isinstance(item, str) else ""
        # A letter is exactly one character: "" and "AB" are substrings of the menu but not letters.
        if len(letter) != 1 or letter not in CHECK_LETTERS:
            return None
        letters.add(letter)
    return sorted(letters)


def _choice(value, allowed):
    value = value.strip().lower() if isinstance(value, str) else None
    return value if value in allowed else None


def parse_answer(text, error):
    # The five answer fields plus parse_status; first status that applies wins.
    # When the status is not ok every value field is "" except reason (kept if it was a string).
    blank = {"parse_status": "", **dict.fromkeys(VALUE_FIELDS, ""), "reason": ""}
    if error:
        return {**blank, "parse_status": "call_error"}
    answer = extract_json(text)
    if answer is None:
        return {**blank, "parse_status": "no_json"}
    reason = answer.get("reason")
    kept = {**blank, "reason": reason if isinstance(reason, str) else ""}
    if any(key not in answer for key in ANSWER_KEYS):
        return {**kept, "parse_status": "missing_key"}
    score = _score(answer["risk_score"])
    rating = _choice(answer["risk_rating"], RATINGS)
    checks = _checks(answer["further_checks"])
    recommendation = _choice(answer["recommendation"], RECOMMENDATIONS)
    if score is None or rating is None or checks is None or recommendation is None or not isinstance(reason, str):
        return {**kept, "parse_status": "bad_value"}
    return {"parse_status": "ok", "risk_score": score, "risk_rating": rating, "further_checks": ";".join(checks),
            "n_checks": len(checks), "recommendation": recommendation, "reason": reason}


def parse_batch(batch, data_root):
    # Imported here: run_models imports ANSWER_SCHEMA from this module.
    from pipeline.run_models import plan_items

    raw_path = Path(data_root) / "raw" / batch / "answers.jsonl"
    if not raw_path.exists():
        raise FileNotFoundError(f"no raw answers for batch {batch!r}: {raw_path} does not exist")
    runs = {run["run_id"]: run for run in build_runs()[0]}
    expected = {}  # run_id -> hash of the messages build_runs builds today
    rows = []
    for key, record in sorted(last_by_key(read_jsonl(raw_path)).items()):
        run = runs.get(record["run_id"])
        if run is not None and record["run_id"] not in expected:
            # Same construction as the run itself, so the hashes can be compared.
            expected[record["run_id"]] = messages_sha256(plan_items([run], None, None)[0]["messages"])
        matches = run is not None and record.get("prompt_sha256") == expected[record["run_id"]]
        row = {"batch": batch, "model_alias": record["model_alias"], "key": key, "run_id": record["run_id"],
               "repetition": record["repetition"], "block": record["block"],
               **{column: run[column] if run is not None else "" for column in RUN_COLUMNS},
               "prompt_matches": int(matches), **parse_answer(record["text"], record["error"]),
               "finish_reason": record["finish_reason"], "error": record["error"]}
        rows.append(row)
    out_path = Path(data_root) / "processed" / batch / "answers.csv"
    write_csv(out_path, rows, ANSWER_COLUMNS)
    counts = Counter(row["parse_status"] for row in rows)
    print(f"{len(rows)} rows in {out_path}")
    for status in ("ok", "call_error", "no_json", "missing_key", "bad_value"):
        print(f"  {status}: {counts.get(status, 0)}")
    print(f"  rows with prompt_matches = 0: {sum(row['prompt_matches'] == 0 for row in rows)}")
    return out_path


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--batch", required=True, help="name of the batch under data/raw")
    parser.add_argument("--data-root", default=str(DATA))
    args = parser.parse_args(argv)
    try:
        parse_batch(args.batch, Path(args.data_root))
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
