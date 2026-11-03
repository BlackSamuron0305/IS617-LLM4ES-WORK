"""Judge lab: other versions of the judge, to see how much the judge's findings depend on the judge.

The judge of experiment/judge/ (version v1) codes only the reason, blinded, with six codes, by one model. The lab
runs other versions on the same answers: another codebook (v2, v3: the judge checks the reason against the numbers
of the application), the same codebook without the blinding (v1_unmasked: does the judge code differently when it
knows the nationality?), and any judge model of experiment/judge/judge_models.csv. A version is a row of
experiment/judge/lab/versions.csv plus two prompt files. Exploratory; nothing here replaces the hand-coded validation.

Usage:
    python -m pipeline.judge_lab build   --batch B --version v2 [--block 1] [--sample 3000] [--country Syria]
    python -m pipeline.judge_lab run     --batch B --version v2 --judge olmo-3.1-32b-instruct --base-url URL --allow-real-calls
    python -m pipeline.judge_lab parse   --batch B --version v2 --judge olmo-3.1-32b-instruct
    python -m pipeline.judge_lab compare --batch B --a v2:olmo-3.1-32b-instruct --b v2:gpt-oss-120b
"""

import argparse
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

from pipeline.build_runs import application_template, build_application
from pipeline.calls import begin_stage, check_mock_label, record_summary, run_calls
from pipeline.client import RunRefused, make_client
from pipeline.common import DATA, EXPERIMENT, load_models, load_settings, read_jsonl, read_table, read_text, sha256_text, write_csv
from pipeline.judge_build import JUDGE, NATIONALITY_MASK, compile_masker, mask, masking_terms, write_jsonl
from pipeline.judge_validate import cohen_kappa
from pipeline.parse_answers import extract_json

LAB = JUDGE / "lab"
YES_NO = ("yes", "no")


def versions():
    out = {}
    for row in read_table(LAB / "versions.csv"):
        row["codes"] = row["codes"].split(";")
        out[row["version"]] = row
    return out


def schema(codes):
    return {"type": "object", "properties": {**{c: {"type": "string", "enum": list(YES_NO)} for c in codes}, "evidence": {"type": "string"}},
            "required": [*codes, "evidence"], "additionalProperties": False}


def lab_dir(data_root, batch):
    return Path(data_root) / "processed" / batch


def build(batch, version, data_root, blocks=None, variants=None, sample=None, seed=617, countries=None):
    cfg = versions()[version]
    folder = lab_dir(data_root, batch)
    answers = [r for r in read_table(folder / "answers.csv") if r["parse_status"] == "ok" and r["reason"].strip() and r["prompt_matches"] == "1"]
    if blocks:
        answers = [r for r in answers if r["block"] in blocks]
    if variants:
        answers = [r for r in answers if r["variant"] in variants]
    if countries:
        answers = [r for r in answers if r["country"] in countries]
    if sample and len(answers) > sample:
        answers = random.Random(seed).sample(answers, sample)
    nationalities = read_table(EXPERIMENT / "countries/applicant_nationalities.csv")
    by_country = {n["country"]: n for n in nationalities}
    applicants = {a["applicant_id"]: a for a in read_table(EXPERIMENT / "applicants/applicants.csv")}
    mask_rows = read_table(JUDGE / "mask_terms.csv")
    system = read_text(LAB / f"{version}_prompt.txt")
    task = read_text(LAB / f"{version}_task.txt")
    masked = cfg["masked"] == "yes"
    placeholder = {"demonym": NATIONALITY_MASK, "travel_document": f"{NATIONALITY_MASK} passport"}
    maskers, items, links = {}, {}, []
    for row in answers:
        country, applicant = by_country.get(row["country"]), applicants.get(row["applicant_id"])
        if country is None or applicant is None or row["variant"] != "base":
            continue  # the lab judges the base design only: a variant may change the application itself
        if masked:
            if row["country"] not in maskers:
                maskers[row["country"]] = compile_masker(masking_terms(nationalities, mask_rows, country))
            reason, n_masked = mask(row["reason"], maskers[row["country"]])
            application = build_application(application_template(applicant), applicant, placeholder, row["savings"])
        else:
            reason, n_masked = row["reason"], 0
            application = build_application(application_template(applicant), applicant, country, row["savings"])
        user = task.replace("{application}", application).replace("{reason}", reason)
        item_id = sha256_text(system + "\n" + user)[:16]
        items.setdefault(item_id, {"item_id": item_id, "applicant_id": row["applicant_id"], "system": system, "user": user})
        links.append({"key": row["key"], "run_id": row["run_id"], "item_id": item_id, "country": row["country"],
                      "model_alias": row["model_alias"], "block": row["block"], "visa_score": row["visa_score"]})
    write_jsonl(folder / f"lab_{version}_items.jsonl", items.values())
    write_csv(folder / f"lab_{version}_links.csv", links, ["key", "run_id", "item_id", "country", "model_alias", "block", "visa_score"])
    return {"answers": len(answers), "items": len(items), "linked": len(links)}


def run(batch, version, judge_alias, client, data_root, limit=None, workers=8, mock=False):
    judges = load_models(JUDGE / "judge_models.csv")
    if judge_alias not in judges:
        raise RunRefused(f"unknown judge {judge_alias!r}; judge_models.csv has: {', '.join(judges)}")
    cfg = versions()[version]
    check_mock_label(client, mock, batch)
    folder = lab_dir(data_root, batch)
    records = read_jsonl(folder / f"lab_{version}_items.jsonl")
    if not records:
        raise FileNotFoundError(f"no lab items for {batch} {version} (run build first)")
    items = [{"key": r["item_id"], "messages": [{"role": "system", "content": r["system"]}, {"role": "user", "content": r["user"]}],
              "meta": {"item_id": r["item_id"]}} for r in records]
    if limit:
        items = items[:limit]
    settings = load_settings("judge")
    raw = Path(data_root) / "raw" / batch
    manifest = raw / f"lab_{version}_{judge_alias}_manifest.json"
    fixed = begin_stage(manifest, "judge", batch, judge_alias, judges[judge_alias], mock, settings, {"limit": limit, "lab_version": version}, client)
    summary = run_calls(items, client, settings, judges[judge_alias]["extra_body"], schema(cfg["codes"]),
                        raw / f"lab_{version}_{judge_alias}.jsonl", workers, fixed)
    record_summary(manifest, summary)
    return summary


def parse(batch, version, judge_alias, data_root):
    cfg = versions()[version]
    codes = cfg["codes"]
    folder = lab_dir(data_root, batch)
    latest = {}
    for rec in read_jsonl(Path(data_root) / "raw" / batch / f"lab_{version}_{judge_alias}.jsonl"):
        latest[rec["key"]] = rec
    coded = {}
    status = defaultdict(int)
    for item_id, rec in latest.items():
        ans = extract_json(rec["text"]) if rec.get("error") is None else None
        row = {"item_id": item_id, "status": "call_error" if rec.get("error") else "no_json", **dict.fromkeys(codes, "")}
        if ans is not None:
            vals = {c: (ans.get(c).strip().lower() if isinstance(ans.get(c), str) else None) for c in codes}
            if all(v in YES_NO for v in vals.values()):
                row.update({c: int(v == "yes") for c, v in vals.items()}, status="ok")
            else:
                row["status"] = "bad_value"
        status[row["status"]] += 1
        coded[item_id] = row
    links = read_table(folder / f"lab_{version}_links.csv")
    out = []
    for link in links:
        row = coded.get(link["item_id"])
        out.append({**link, "status": row["status"] if row else "not_run", **{c: (row[c] if row else "") for c in codes}})
    write_csv(folder / f"lab_{version}_{judge_alias}_codes.csv", out, ["key", "run_id", "item_id", "country", "model_alias", "block", "visa_score", "status", *codes])
    return dict(status)


def compare(batch, a, b, data_root):
    folder = lab_dir(data_root, batch)
    (va, ja), (vb, jb) = a.split(":"), b.split(":")
    ra = {r["key"]: r for r in read_table(folder / f"lab_{va}_{ja}_codes.csv") if r["status"] == "ok"}
    rb = {r["key"]: r for r in read_table(folder / f"lab_{vb}_{jb}_codes.csv") if r["status"] == "ok"}
    shared = sorted(set(ra) & set(rb))
    codes = [c for c in versions()[va]["codes"] if c in versions()[vb]["codes"]]
    out = []
    for c in codes:
        x, y = [int(ra[k][c]) for k in shared], [int(rb[k][c]) for k in shared]
        out.append({"code": c, "n": len(shared), "share_a": round(sum(x) / len(x), 4) if x else "", "share_b": round(sum(y) / len(y), 4) if y else "",
                    "agreement": round(sum(i == j for i, j in zip(x, y)) / len(x), 4) if x else "",
                    "kappa": "" if not x or cohen_kappa(x, y) is None else round(cohen_kappa(x, y), 3)})
    write_csv(folder / f"lab_compare_{va}_{ja}__{vb}_{jb}.csv", out, ["code", "n", "share_a", "share_b", "agreement", "kappa"])
    return out


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    for name in ("build", "run", "parse", "compare"):
        p = sub.add_parser(name)
        p.add_argument("--batch", required=True)
        p.add_argument("--data-root", default=str(DATA))
        if name != "compare":
            p.add_argument("--version", required=True)
        if name == "build":
            p.add_argument("--block", action="append")
            p.add_argument("--variant", action="append")
            p.add_argument("--sample", type=int)
            p.add_argument("--country", action="append")
        if name in ("run", "parse"):
            p.add_argument("--judge", required=True)
        if name == "run":
            p.add_argument("--limit", type=int)
            p.add_argument("--workers", type=int, default=8)
            p.add_argument("--mock", action="store_true")
            p.add_argument("--base-url")
            p.add_argument("--allow-real-calls", action="store_true")
        if name == "compare":
            p.add_argument("--a", required=True, help="version:judge")
            p.add_argument("--b", required=True, help="version:judge")
    args = parser.parse_args(argv)
    try:
        if args.cmd == "build":
            print(build(args.batch, args.version, args.data_root, args.block, args.variant, args.sample, countries=args.country))
        elif args.cmd == "run":
            judges = load_models(JUDGE / "judge_models.csv")
            client = make_client("judge", judges[args.judge], args.batch, args.mock, args.base_url, args.allow_real_calls)
            print(json.dumps(run(args.batch, args.version, args.judge, client, args.data_root, args.limit, args.workers, args.mock)))
        elif args.cmd == "parse":
            print(parse(args.batch, args.version, args.judge, args.data_root))
        else:
            for row in compare(args.batch, args.a, args.b, args.data_root):
                print(row)
    except (RunRefused, FileNotFoundError, KeyError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
