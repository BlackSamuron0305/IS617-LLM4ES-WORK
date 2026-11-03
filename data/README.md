# data

The output of our model runs is saved here. The runs of 2026-11-01 to 2026-11-03 are in `raw/`, one folder per batch (about
87 folders, 792 MB; stored as `.jsonl.gz`, 77 MB; `pipeline/common.py` reads them like the plain files, or unpack them with `gunzip -k`).
`processed/` is rebuilt with the pipeline and is not committed; the summary tables are in `../results/`.

Everything is kept by **batch**: one batch is one named group of calls to one model, for
example `pilot1`. The stages that write these files are in `pipeline/` (`pipeline/README.md`
lists what each reads and writes).

## raw/

The model responses exactly as they came back. Never edited by hand. The `.jsonl` files are
append-only: a call is added as one line, and when a key appears twice the last line wins.

```
raw/<batch>/
  answers.jsonl                 one line per call to the audited model
  manifest.json                 model, revision, settings, commit, server and summary of every session
  judge_<alias>.jsonl           one line per call to the judge model <alias>
  judge_<alias>_manifest.json   the same for the judge
```

## processed/

The tables built from the raw responses. They can be rebuilt at any time.

```
processed/<batch>/
  answers.csv                   one row per call, with the answer read into columns
  judge_items.jsonl             what the judge sees: one line per unique masked input
  judge_links.csv               which answer belongs to which judge input
  judge_codes_<alias>.csv       the codes of judge <alias>, one row per judge input
  answers_judged_<alias>.csv    answers.csv plus the codes of judge <alias>
  validation_sample.csv         the items the team codes by hand (kept unless --force)
  validation_agreement_*.csv    agreement of two sets of codes
```

The judge's codes are exploratory, and only the codes that pass the validation are used
(`experiment/judge/README.md`).

## Mock runs

Output of real runs is committed to git. Output of mock or test runs (batch name starts
with `mock`) is ignored by git and must never be reported as a result.
