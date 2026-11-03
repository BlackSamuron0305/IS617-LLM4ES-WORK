"""Stage 5: turn the judge's raw answers into codes and put them on every answer.

Reads data/raw/<batch>/judge_<alias>.jsonl (the last record per item wins), reads the five codes
and the evidence out of each text and writes two tables in data/processed/<batch>/:
judge_codes_<alias>.csv (one row per judge input) and answers_judged_<alias>.csv (every row of
answers.csv, followed by item_id, n_masked, judge_status and the five codes). judge_status says
what happened to a row: ok, inconsistent (the judge says the reason treats the nationality as a
risk but does not mention it; codes kept), call_error, no_json, missing_key, bad_value (codes
blank), not_run (the item has no record from this judge yet) or not_judged (the answer has no
judge input: it was not read or had no reason). The tables are rebuilt on every run. Never calls
a model.

Usage:
    python -m pipeline.judge_parse --batch mock_x --judge olmo-3.1-32b-instruct
    python -m pipeline.judge_parse --batch pilot1 --judge olmo-3.1-32b-instruct --data-root data
"""

import argparse
import sys
from collections import Counter
from pathlib import Path

from pipeline.common import raw_exists, DATA, last_by_key, load_models, read_jsonl, read_table, write_csv
from pipeline.judge_build import JUDGE, JUDGE_CODES
from pipeline.parse_answers import ANSWER_COLUMNS, extract_json

YES_NO = ("yes", "no")

# The shape of the judge's answer, sent to the server when the setting json_schema is yes.
JUDGE_SCHEMA = {
    "type": "object",
    "properties": {**{code: {"type": "string", "enum": list(YES_NO)} for code in JUDGE_CODES},
                   "evidence": {"type": "string"}},
    "required": [*JUDGE_CODES, "evidence"],
    "additionalProperties": False,
}

JUDGE_CODE_COLUMNS = ["item_id", "applicant_id", "n_masked", "reason_masked", "judge_status", *JUDGE_CODES,
                      "evidence"]
JUDGED_COLUMNS = [*ANSWER_COLUMNS, "item_id", "n_masked", "judge_status", *JUDGE_CODES]
STATUS_ORDER = ("ok", "inconsistent", "call_error", "no_json", "missing_key", "bad_value", "not_run", "not_judged")


def blank_result(status):
    return {"judge_status": status, **dict.fromkeys(JUDGE_CODES, ""), "evidence": ""}


def parse_judge_answer(text, error):
    # The five codes (1, 0 or "") and the evidence, plus judge_status; first status that applies wins.
    # Codes are blank unless the status is ok or inconsistent: a partly coded reason is not used.
    if error:
        return blank_result("call_error")
    answer = extract_json(text)
    if answer is None:
        return blank_result("no_json")
    # A missing or non-text evidence is a blank one, not an error; the codes are what matters.
    evidence = answer.get("evidence")
    kept = {**blank_result(""), "evidence": evidence if isinstance(evidence, str) else ""}
    if any(code not in answer for code in JUDGE_CODES):
        return {**kept, "judge_status": "missing_key"}
    values = {}
    for code in JUDGE_CODES:
        value = answer[code].strip().lower() if isinstance(answer[code], str) else None
        if value not in YES_NO:
            return {**kept, "judge_status": "bad_value"}
        values[code] = int(value == "yes")
    # Treating the nationality as a risk without mentioning it cannot be right; the codes stay for inspection.
    inconsistent = values["nationality_as_risk"] == 1 and values["mentions_nationality"] == 0
    return {**kept, **values, "judge_status": "inconsistent" if inconsistent else "ok"}


def check_inputs(batch, data_root):
    # The processed files the judge stage depends on; the first missing one is named.
    folder = Path(data_root) / "processed" / batch
    for name in ("answers.csv", "judge_links.csv", "judge_items.jsonl"):
        if not (folder / name).exists():
            raise FileNotFoundError(f"missing {folder / name} (run parse_answers and judge_build first)")


def parse_judge(batch, judge_alias, data_root):
    data_root = Path(data_root)
    check_inputs(batch, data_root)
    folder = data_root / "processed" / batch
    answers, links, items = (read_table(folder / "answers.csv"), read_table(folder / "judge_links.csv"),
                             read_jsonl(folder / "judge_items.jsonl"))
    # An item without a record from this judge has not been run (or its file is missing).
    records = last_by_key(read_jsonl(data_root / "raw" / batch / f"judge_{judge_alias}.jsonl"))
    coded = {}  # item_id -> row of judge_codes
    for item in items:
        record = records.get(item["item_id"])
        result = blank_result("not_run") if record is None else parse_judge_answer(record["text"], record["error"])
        coded[item["item_id"]] = {"item_id": item["item_id"], "applicant_id": item["applicant_id"],
                                  "n_masked": item["n_masked"], "reason_masked": item["reason_masked"], **result}
    by_key = {link["key"]: link for link in links}
    judged = []
    for answer in answers:
        link = by_key.get(answer["key"])
        if link is None:
            judged.append({**answer, "item_id": "", "n_masked": "", "judge_status": "not_judged",
                           **dict.fromkeys(JUDGE_CODES, "")})
            continue
        row = coded[link["item_id"]]
        judged.append({**answer, "item_id": link["item_id"], "n_masked": link["n_masked"],
                       "judge_status": row["judge_status"], **{code: row[code] for code in JUDGE_CODES}})
    out_dir = data_root / "processed" / batch
    codes_path = out_dir / f"judge_codes_{judge_alias}.csv"
    judged_path = out_dir / f"answers_judged_{judge_alias}.csv"
    write_csv(codes_path, coded.values(), JUDGE_CODE_COLUMNS)
    write_csv(judged_path, judged, JUDGED_COLUMNS)
    print_counts(f"{len(coded)} judge inputs in {codes_path}", [row["judge_status"] for row in coded.values()])
    print_counts(f"{len(judged)} answers in {judged_path}", [row["judge_status"] for row in judged])
    return codes_path, judged_path


def print_counts(title, statuses):
    counts = Counter(statuses)
    print(title)
    for status in STATUS_ORDER:
        print(f"  {status}: {counts.get(status, 0)}")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--batch", required=True, help="name of the batch under data/raw and data/processed")
    parser.add_argument("--judge", required=True, help="alias in experiment/judge/judge_models.csv")
    parser.add_argument("--data-root", default=str(DATA))
    args = parser.parse_args(argv)
    judges = load_models(JUDGE / "judge_models.csv")
    if args.judge not in judges:
        print(f"error: unknown judge {args.judge!r}; experiment/judge/judge_models.csv has: {', '.join(judges)}",
              file=sys.stderr)
        return 2
    raw_path = Path(args.data_root) / "raw" / args.batch / f"judge_{args.judge}.jsonl"
    try:
        check_inputs(args.batch, Path(args.data_root))
        if not raw_exists(raw_path):
            raise FileNotFoundError(f"no raw judge answers for batch {args.batch!r}: {raw_path} does not exist "
                                    "(run run_judge first)")
        parse_judge(args.batch, args.judge, Path(args.data_root))
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
