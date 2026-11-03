"""Stage 3: prepare what the judge sees, with every nationality word hidden.

Reads data/processed/<batch>/answers.csv (written by parse_answers). For each answer that was
read, has a reason and whose prompt still is the one the experiment files give now (prompt_matches
is 1), the nationality words in the reason are replaced by placeholders, the
application is rebuilt with [NATIONALITY] in its two nationality lines, and the judge's two
messages are put together. The judge never sees the score.
Identical judge inputs are written once. Writes data/processed/<batch>/judge_items.jsonl
(one line per unique input) and judge_links.csv (which answer belongs to which input). Both
are written fresh on every run. Never calls a model.

The words that are masked come from the two nationality tables of the experiment and from
experiment/judge/mask_terms.csv; experiment/judge/README.md explains the rule and its leaks.

Usage:
    python -m pipeline.judge_build --batch mock_x
    python -m pipeline.judge_build --batch pilot1 --data-root data
"""

import argparse
import json
import re
import sys
from pathlib import Path

from pipeline.build_runs import application_template, build_application
from pipeline.common import DATA, EXPERIMENT, read_table, read_text, sha256_text, write_csv

JUDGE = EXPERIMENT / "judge"
JUDGE_CODES = ("mentions_nationality", "nationality_as_risk", "passport_country_conditions", "doubts_residence",
               "contradicts_application", "names_legal_ground")
MASK_KINDS = ("alias", "capital", "region", "keep")
NATIONALITY_MASK = "[NATIONALITY]"
PASSPORT_MASK = "[PASSPORT COUNTRY]"
LINK_COLUMNS = ["key", "run_id", "repetition", "item_id", "n_masked"]


def masking_terms(nationalities, mask_rows, own):
    # Lower-cased term -> replacement; None means "keep as written". Later entries override earlier ones.
    terms = {}
    for nationality in nationalities:
        terms[nationality["demonym"].lower()] = NATIONALITY_MASK
    for nationality in nationalities:
        terms[nationality["country"].lower()] = PASSPORT_MASK
    keep = set()
    for row in mask_rows:
        if row["kind"] not in MASK_KINDS:
            raise ValueError(f"mask_terms.csv: unknown kind {row['kind']!r} for {row['term']!r}")
        term = row["term"].strip().lower()
        if row["kind"] == "keep":
            keep.add(term)
            terms[term] = None
        else:
            terms[term] = row["replacement"]
    # The applicant's own demonym is always masked. The own country too, unless it is a keep term
    # (the United Arab Emirates, the country of residence, stays visible for an Emirati applicant).
    terms[own["demonym"].lower()] = NATIONALITY_MASK
    if own["country"].lower() not in keep:
        terms[own["country"].lower()] = PASSPORT_MASK
    return terms


def compile_masker(terms):
    # One pattern for all terms, longest first so that "Saudi Arabian" wins over "Saudi"; an
    # optional trailing "s" is part of the match, so "Syrians" is masked as one word. Matching is
    # ASCII-only: under Unicode case folding a long s (U+017F) would match "s" but not lower-case to
    # it, and the lookup in mask() would fail.
    ordered = sorted(terms, key=lambda term: (-len(term), term))
    alternatives = "|".join(re.escape(term) for term in ordered)
    return re.compile(r"\b(?P<term>" + alternatives + r")s?\b", re.IGNORECASE | re.ASCII), terms


def mask(text, masker):
    # The masked text and the number of replacements. A keep term stays as written and is not counted.
    pattern, terms = masker
    count = 0

    def replace(match):
        nonlocal count
        replacement = terms[match.group("term").lower()]
        if replacement is None:
            return match.group(0)
        count += 1
        return replacement

    return pattern.sub(replace, text), count


def write_jsonl(path, records):
    # Processed files are rebuilt from scratch on every run, so this overwrites (unlike the raw files).
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def build_judge_items(batch, data_root, blocks=None, variants=None):
    data_root = Path(data_root)
    answers_path = data_root / "processed" / batch / "answers.csv"
    if not answers_path.exists():
        raise FileNotFoundError(f"no parsed answers for batch {batch!r}: {answers_path} does not exist "
                                "(run parse_answers first)")
    answers = read_table(answers_path)
    nationalities = read_table(EXPERIMENT / "countries/applicant_nationalities.csv")
    by_country = {n["country"]: n for n in nationalities}
    applicants = {a["applicant_id"]: a for a in read_table(EXPERIMENT / "applicants/applicants.csv")}
    mask_rows = read_table(JUDGE / "mask_terms.csv")
    system = read_text(JUDGE / "judge_prompt.txt")
    task = read_text(JUDGE / "judge_task.txt")
    placeholder = {"demonym": NATIONALITY_MASK, "travel_document": f"{NATIONALITY_MASK} passport"}

    maskers = {}       # country -> masker
    applications = {}  # (applicant_id, savings) -> application text with the placeholder
    items = {}         # item_id -> item; insertion order is first-seen order
    links = []
    for row in answers:
        if row["parse_status"] != "ok" or not row["reason"].strip():
            continue
        if blocks is not None and row["block"] not in blocks:
            continue  # the judge is exploratory: it may be run on some blocks only
        if variants is not None and row["variant"] not in variants:
            continue
        if row["prompt_matches"] != "1":
            continue  # the files of the experiment changed after the run: the application cannot be rebuilt
        country, applicant = by_country.get(row["country"]), applicants.get(row["applicant_id"])
        if country is None or applicant is None:
            continue  # the run is not in today's experiment files, so its application cannot be rebuilt
        if row["country"] not in maskers:
            maskers[row["country"]] = compile_masker(masking_terms(nationalities, mask_rows, country))
        reason, n_masked = mask(row["reason"], maskers[row["country"]])
        application_key = (row["applicant_id"], row["savings"])
        if application_key not in applications:
            applications[application_key] = build_application(application_template(applicant), applicant, placeholder, row["savings"])
        user = task.replace("{application}", applications[application_key]).replace("{reason}", reason)
        item_id = sha256_text(system + "\n" + user)[:16]
        if item_id not in items:
            items[item_id] = {"item_id": item_id, "applicant_id": row["applicant_id"], "reason_masked": reason,
                              "n_masked": n_masked, "system": system, "user": user}
        links.append({"key": row["key"], "run_id": row["run_id"], "repetition": row["repetition"],
                      "item_id": item_id, "n_masked": n_masked})

    out_dir = data_root / "processed" / batch
    out_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(out_dir / "judge_items.jsonl", items.values())
    write_csv(out_dir / "judge_links.csv", links, LINK_COLUMNS)
    return {"answers": len(answers), "linked": len(links), "items": len(items),
            "skipped": len(answers) - len(links)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--batch", required=True, help="name of the batch under data/processed")
    parser.add_argument("--data-root", default=str(DATA))
    parser.add_argument("--block", action="append", help="only the answers of this block (repeatable)")
    parser.add_argument("--variant", action="append", help="only the answers of this prompt variant (repeatable)")
    args = parser.parse_args(argv)
    try:
        summary = build_judge_items(args.batch, Path(args.data_root), args.block, args.variant)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    out_dir = Path(args.data_root) / "processed" / args.batch
    print(f"{summary['answers']} answers: {summary['linked']} linked to {summary['items']} unique judge inputs, "
          f"{summary['skipped']} skipped (answer not read, empty reason, prompt changed since the run, "
          "or run not in the experiment files)")
    print(f"written: {out_dir / 'judge_items.jsonl'}, {out_dir / 'judge_links.csv'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
