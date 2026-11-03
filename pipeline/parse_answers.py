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
import re
import sys
from collections import Counter
from pathlib import Path

from pipeline.build_runs import DEFAULT_ANSWER_KEYS, SCORE_KEYS, build_runs
from pipeline.common import raw_exists, DATA, last_by_key, messages_sha256, read_jsonl, write_csv


def answer_schema(answer_keys=DEFAULT_ANSWER_KEYS):
    # The shape of an answer, sent to the server when the setting json_schema is yes.
    properties = {}
    for key in answer_keys:
        properties[key] = {"type": "integer", "minimum": 0, "maximum": 100} if key in SCORE_KEYS else {"type": "string"}
    return {"type": "object", "properties": properties, "required": list(answer_keys), "additionalProperties": False}


ANSWER_SCHEMA = answer_schema()

RUN_COLUMNS = ["variant", "policy_version", "applicant_id", "file_profile", "indicator", "savings", "country", "demonym",
               "group", "wealth_group", "visa_required", "wording"]
# score_raw is the number the model gave; score_scale says what it means (visa: 100 = grant, risk: 100 = refuse);
# visa_score is the same on the grant scale for every row (100 - score_raw when the scale is risk).
ANSWER_COLUMNS = ["batch", "model_alias", "key", "run_id", "repetition", "block", *RUN_COLUMNS, "prompt_matches",
                  "parse_status", "score_raw", "score_scale", "visa_score", "reasoning", "reason", "finish_reason",
                  "error"]
VALUE_FIELDS = ("score_raw", "score_scale", "visa_score", "reasoning")


def extract_json(text):
    # The first JSON object in the text, or None. Handles code fences, prose around the object
    # and <think> blocks that contain braces.
    if not isinstance(text, str):
        return None
    try:
        whole = json.loads(text.strip())
        if isinstance(whole, dict):
            return whole
    except (ValueError, RecursionError):  # endless nesting is "no JSON", not a crash
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
    if isinstance(value, str) and re.fullmatch(r"\s*\d{1,3}\s*", value):
        value = int(value)  # a whole number written as text ("80"): small models do this; the intended value is clear
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    if isinstance(value, float):
        if not value.is_integer():
            return None
        value = int(value)
    return value if 0 <= value <= 100 else None


def parse_answer(text, error, answer_keys=DEFAULT_ANSWER_KEYS):
    # The answer fields plus parse_status; first status that applies wins.
    # When the status is not ok every value field is "" except reason (kept if it was a string).
    blank = {"parse_status": "", **dict.fromkeys(VALUE_FIELDS, ""), "reason": ""}
    if error:
        return {**blank, "parse_status": "call_error"}
    answer = extract_json(text)
    if answer is None:
        return {**blank, "parse_status": "no_json"}
    reason = answer.get("reason")
    kept = {**blank, "reason": reason if isinstance(reason, str) else ""}
    if any(key not in answer for key in answer_keys):
        return {**kept, "parse_status": "missing_key"}
    score_key = next(key for key in answer_keys if key in SCORE_KEYS)
    score = _score(answer[score_key])
    reasoning = answer.get("reasoning", "")
    # The reasoning variant asks for a walk through points (a) to (g): models answer with a text, a list or an
    # object keyed by the points. All three are kept (an object or a list as JSON text).
    if isinstance(reasoning, (list, dict)):
        reasoning = json.dumps(reasoning, ensure_ascii=False)
    if score is None or not isinstance(reason, str) or not isinstance(reasoning, str):
        return {**kept, "parse_status": "bad_value"}
    scale = SCORE_KEYS[score_key]
    return {"parse_status": "ok", "score_raw": score, "score_scale": scale,
            "visa_score": score if scale == "visa" else 100 - score, "reasoning": reasoning, "reason": reason}


def parse_batch(batch, data_root):
    # Imported here: run_models imports ANSWER_SCHEMA from this module.
    from pipeline.run_models import plan_items

    raw_path = Path(data_root) / "raw" / batch / "answers.jsonl"
    if not raw_exists(raw_path):
        raise FileNotFoundError(f"no raw answers for batch {batch!r}: {raw_path} does not exist")
    runs = {run["run_id"]: run for run in build_runs("all")[0]}
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
               "prompt_matches": int(matches), **parse_answer(record["text"], record["error"],
                                                    run["answer_keys"] if run is not None else DEFAULT_ANSWER_KEYS),
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
