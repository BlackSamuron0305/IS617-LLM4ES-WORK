"""Report of the judge lab: parse every (batch, version, judge), compare judges and versions, and show the codes by nationality group.

    python -m pipeline.judge_lab_report --batch x2_qwen2.5-7b-instruct main_qwen3-32b --name dd_judge
Writes results/<name>/agreement.csv (agreement and kappa between judge models and between versions) and
results/<name>/by_group.csv (share of each code for Syria, the other poor countries, the Gulf states, the normal countries, the placebos).
"""

import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path

from pipeline import judge_lab
from pipeline.common import DATA, ROOT, raw_exists, read_table, write_csv

GROUPS = (("Syria", lambda r: r["country"] == "Syria"),
          ("other poor (3)", lambda r: r["country"] in ("Somalia", "Sudan", "Yemen")),
          ("Gulf (5)", lambda r: r["country"] in ("Bahrain", "Kuwait", "Oman", "Qatar", "Saudi Arabia")),
          ("normal (12)", lambda r: r["country"] in ("Algeria", "Comoros", "Djibouti", "Egypt", "Iraq", "Jordan", "Lebanon", "Libya", "Mauritania", "Morocco", "Palestine", "Tunisia")),
          ("placebo (3)", lambda r: r["country"] in ("Malawi", "Maldives", "Cambodia")))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--batch", nargs="+", required=True)
    parser.add_argument("--name", default="dd_judge")
    parser.add_argument("--data-root", default=str(DATA))
    args = parser.parse_args(argv)
    vers = judge_lab.versions()
    judges = [r["alias"] for r in read_table(judge_lab.JUDGE / "judge_models.csv")]
    out_dir = ROOT / "results" / args.name
    agree, shares = [], []
    for batch in args.batch:
        have = []
        for v in vers:
            for j in judges:
                if raw_exists(Path(args.data_root) / "raw" / batch / f"lab_{v}_{j}.jsonl"):
                    st = judge_lab.parse(batch, v, j, args.data_root)
                    print(batch, v, j, st)
                    have.append((v, j))
        folder = Path(args.data_root) / "processed" / batch
        for v, j in have:
            rows = [r for r in read_table(folder / f"lab_{v}_{j}_codes.csv") if r["status"] == "ok"]
            for code in vers[v]["codes"]:
                for g, fn in GROUPS:
                    sel = [r for r in rows if fn(r)]
                    if sel:
                        shares.append({"batch": batch, "version": v, "judge": j, "code": code, "group": g, "n": len(sel),
                                       "share": round(sum(int(r[code]) for r in sel) / len(sel), 4)})
        pairs = []
        for v in vers:                                       # the same version, other judge models
            js = [j for (vv, j) in have if vv == v]
            pairs += [((v, js[0]), (v, other)) for other in js[1:]]
        for a, b in (("v1", "v1_unmasked"),):               # the same judge model, with and without the blinding
            for j in judges:
                if (a, j) in have and (b, j) in have:
                    pairs.append(((a, j), (b, j)))
        for (va, ja), (vb, jb) in pairs:
            for row in judge_lab.compare(batch, f"{va}:{ja}", f"{vb}:{jb}", args.data_root):
                agree.append({"batch": batch, "a": f"{va}:{ja}", "b": f"{vb}:{jb}", **row})
    if agree:
        write_csv(out_dir / "agreement.csv", agree, list(agree[0]))
    if shares:
        write_csv(out_dir / "by_group.csv", shares, list(shares[0]))
    print(len(agree), "agreement rows;", len(shares), "share rows ->", out_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
