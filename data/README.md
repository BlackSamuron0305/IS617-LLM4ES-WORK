# data

The output of our model runs is saved here. The runs of 2026-11-01 to 2026-11-03 are in `raw/`, one folder per batch (about
87 folders, 792 MB; stored as `.jsonl.gz`, 77 MB; `pipeline/core/common.py` reads them like the plain files, or unpack them with `gunzip -k`).
`processed/` is rebuilt with the pipeline and is not committed; the summary tables are in `../results/`.

Everything is kept by **batch**: one batch is one named group of calls to one model, for
example `pilot1`. The stages that write these files are in `pipeline/` (`pipeline/README.md`
lists what each reads and writes).

## raw/

The model responses exactly as they came back. Never edited by hand. The `.jsonl` files are
append-only: a call is added as one line, and when a key appears twice the last line wins.

Batches are grouped by run, then by model (the rule is `batch_subpath` in `pipeline/core/common.py`; a
name that follows no rule, such as a mock run, stays directly in `raw/`):

```
raw/
  00_smoke_tests/<model>/smoke_<model>/        first tries of each model, before any pilot
  01_pilots/pilot1/, pilot2/                   the two pilots of the audited design (Qwen3 32B)
  02_audited_main_run/<model>/main_<model>[_s<k>]/    blocks 1 to 3 of the three audited models (_s<k>: one shard)
  03_audited_boundary_applicants/<model>/bnd_<model>[_s<k>]/    blocks 5 and 6 (deviation D4)
  04_audited_prompt_variants/<model>/var_<model>[_s<k>]/        the twelve prompt variants (block 4)
  05_extra_models/round_1_small_and_mid/<model>/x2_<model>[_s<k>]/   deviation D5
  05_extra_models/round_2_large/<model>/x3_<model>[_s<k>]/           deviation D7
  06_deep_dive/qwen_family/<model>/dd_fam_<model>[_s<k>]/            Qwen2, Qwen2.5 and Qwen3 sizes
  06_deep_dive/negative_applicants/<model>/dd_neg_<model>[_s<k>]/    blocks 7 and 8
  06_deep_dive/new_prompt_variants/<model>/dd_var_<model>[_s<k>]/    the eleven new variants
  06_deep_dive/five_repetitions/<model>/dd_rep_<model>[_s<k>]/       key variants with five repetitions
  06_deep_dive/conflict_nationalities/<model>/dd_conf_<model>[_s<k>]/  conflict countries outside the Arab League
  07_thinking_and_temperature/thinking_on/<model>/tt_think_<model>[_s<k>]/    thinking on / reasoning effort high (block 1, one repetition)
  07_thinking_and_temperature/temperature/<model>/tt_temp_<model>_t<T>[_s<k>]/ temperatures 0.0, 0.3, 1.0, 1.5 (t00, t03, t10, t15)
```

`processed/` has the same folders. Inside one batch folder:

```
<batch>/
  answers.jsonl                 one line per call to the audited model
  manifest.json                 model, revision, settings, commit, server and summary of every session
  judge_<alias>.jsonl           one line per call to the judge model <alias>
  judge_<alias>_manifest.json   the same for the judge
```

## processed/

The tables built from the raw responses. They can be rebuilt at any time.

```
processed/.../<batch>/
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
