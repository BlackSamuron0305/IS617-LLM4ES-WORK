# pipeline

The code that builds the prompts, sends them to a model, reads the answers and runs the
judge. Written on 2026-10-24. Python 3.11 or newer, standard library only. Every stage is
run from the repo root as `python -m pipeline.<stage>`.

**Nothing has been run with a real model.** Every stage runs as a mock, which needs no
server. The output of a mock run is labelled as such and is never a result.

## The stages, in order

| # | stage | what it does | command |
|---|---|---|---|
| 0 | `build_runs` | puts the prompts together from `experiment/`, checks them and prints the counts. Calls no model | `python -m pipeline.build_runs` |
| 1 | `run_models` | sends the prompts of one batch to one model and stores the raw answers | `python -m pipeline.run_models --batch pilot1 --model qwen3-32b --block 1 --base-url http://localhost:8000/v1 --allow-real-calls` |
| 2 | `parse_answers` | reads the answers (score, reason; `reasoning` for the reasoning variant) into one table. A risk-scale answer is also written on the grant scale (`visa_score`) | `python -m pipeline.parse_answers --batch pilot1` |
| 3 | `judge_build` | hides every nationality word in the reasons and prepares what the judge sees | `python -m pipeline.judge_build --batch pilot1` |
| 4 | `run_judge` | sends the judge inputs to the judge model and stores the raw answers | `python -m pipeline.run_judge --batch pilot1 --judge olmo-3.1-32b-instruct --base-url http://localhost:8000/v1 --allow-real-calls` |
| 5 | `judge_parse` | reads the judge's codes and puts them on every answer | `python -m pipeline.judge_parse --batch pilot1 --judge olmo-3.1-32b-instruct` |
| 6a | `judge_validate sample` | draws the items that the team codes by hand | `python -m pipeline.judge_validate sample --batch pilot1` |
| 6b | `judge_validate agreement` | measures how well two sets of codes agree | `python -m pipeline.judge_validate agreement --batch pilot1 --human coded.csv --judge olmo-3.1-32b-instruct` |

The commands of stages 1 and 4 are real calls. They are shown as they are used on the
cluster, where `cluster/run_vllm.sbatch` starts the server and passes `--allow-real-calls`
(`cluster/README.md`). On a PC, add `--mock` and give a batch name that starts with `mock`
instead of `--base-url` and `--allow-real-calls`.

Other flags: `--variant NAME` (repeatable; default `base`; the names are in `experiment/prompts/variants.csv`) and `--block N` (repeatable) and `--limit N` on `run_models`, `--limit N` on
`run_judge`, `--workers N` on both, `--n N`, `--seed N` and `--force` on
`judge_validate sample`, `--other-human FILE` in place of `--judge` on `judge_validate
agreement`, and `--data-root DIR` on every stage that reads or writes data.
`python -m pipeline.<stage> --help` lists them.

A stage that sends calls can be started again with the same command: it skips what is
already done and continues.

## Mock walk-through

This runs every stage on 50 mock answers and takes a few seconds. The batch is called
`mock_demo`. Run it from the repo root, from a clean `data/`. A mock batch name must start
with `mock`.

```
python -m pipeline.run_models --batch mock_demo --model qwen3-32b --mock --limit 50
python -m pipeline.parse_answers --batch mock_demo
python -m pipeline.judge_build --batch mock_demo
python -m pipeline.run_judge --batch mock_demo --judge olmo-3.1-32b-instruct --mock
python -m pipeline.judge_parse --batch mock_demo --judge olmo-3.1-32b-instruct
python -m pipeline.judge_validate sample --batch mock_demo --n 20
python -m pipeline.run_judge --batch mock_demo --judge gpt-oss-120b --mock
python -m pipeline.judge_parse --batch mock_demo --judge gpt-oss-120b
python -m pipeline.judge_validate agreement --batch mock_demo --human data/processed/mock_demo/judge_codes_gpt-oss-120b.csv --judge olmo-3.1-32b-instruct
```

Every command exits with 0. The last two judge commands and the `agreement` command use the
second judge model as a stand-in for the hand-coder, because nobody has coded the sample.
In real use `--human` is the team's coded copy of `validation_sample.csv`. A mock run has
only a handful of different reasons, so the sample is tiny and most agreement figures are
`n/a`.

The files go to `data/raw/mock_demo/` and `data/processed/mock_demo/`. Git ignores them.
To run the walk-through again, delete both folders first: `judge_validate sample` will not
overwrite an existing sample.

## What each stage reads and writes

`<batch>` is the batch name, `<alias>` the alias of a judge model.

| stage | reads | writes |
|---|---|---|
| `build_runs` | `experiment/` (policy, applicants, countries, prompts) | nothing, or with `--write FILE` all prompts as JSON lines |
| `run_models` | `build_runs`, `experiment/models.csv`, `experiment/run_settings.csv` | `data/raw/<batch>/answers.jsonl` (appended), `data/raw/<batch>/manifest.json` |
| `parse_answers` | `data/raw/<batch>/answers.jsonl` | `data/processed/<batch>/answers.csv` |
| `judge_build` | `data/processed/<batch>/answers.csv`, `experiment/judge/` (prompt files, `mask_terms.csv`), `experiment/countries/` | `data/processed/<batch>/judge_items.jsonl`, `judge_links.csv` |
| `run_judge` | `data/processed/<batch>/judge_items.jsonl`, `experiment/judge/judge_models.csv`, `experiment/run_settings.csv` | `data/raw/<batch>/judge_<alias>.jsonl` (appended), `judge_<alias>_manifest.json` |
| `judge_parse` | `data/raw/<batch>/judge_<alias>.jsonl`, `data/processed/<batch>/answers.csv`, `judge_items.jsonl`, `judge_links.csv` | `data/processed/<batch>/judge_codes_<alias>.csv`, `answers_judged_<alias>.csv` |
| `judge_validate sample` | `data/processed/<batch>/judge_items.jsonl` | `data/processed/<batch>/validation_sample.csv` |
| `judge_validate agreement` | the coded file, and `judge_codes_<alias>.csv` or a second coded file | `data/processed/<batch>/validation_agreement_<name>.csv`, and a table on the screen |

`parse_answers`, `judge_build`, `judge_parse` and `judge_validate agreement` write their
tables again on every run. `judge_validate sample` does so only with `--force`. The raw
files are never rewritten. `data/README.md` describes the folders, `experiment/judge/README.md` the judge.

## When a run is refused

A real run (without `--mock`) is refused unless all of this holds. The first condition that
fails is named in the message, which starts with `refusing:`, and the exit code is 2. The
conditions are checked in this order:

1. `--allow-real-calls` is given. Without it the run stays a mock run. It is given only
   with the team's explicit approval.
2. The batch name does not start with `mock`.
3. The `revision` of the model in its table (`experiment/models.csv`, or
   `experiment/judge/judge_models.csv` for the judge) is a 40-character commit hash (40
   lowercase hexadecimal characters). An empty cell, a branch name such as `main` or a short
   hash is refused. All revisions are empty today, so every real run is refused until they
   are pinned.
4. `git status --porcelain -- experiment pipeline` is empty. A run is tied to a commit.
5. The server lists the model's `model_id` at `GET /models`.

Also: a real run needs `--base-url`; a mock run needs a batch name that starts with `mock`;
a batch belongs to one audited model (several judges can code the same batch), and a second
audited model under the same batch name is refused; the stages refuse a real client that did
not come from `make_client`, which is where the five conditions are checked; `build_runs`
must report no problem.

A real session also records `MODEL_PATH`, `VLLM_ARGS` (both from the environment, empty when
unset) and the address of the server in its manifest. A mock session records empty values.

If a job is killed while it writes, the last line of a raw file may be cut off. The next run
skips such a line (it prints `skipped N unreadable line(s)`) and calls that key again.

Mock output is labelled. Every mock record has `"mock": true`, and every mock answer starts
with `MOCK ANSWER, NOT A RESULT.`

Raw files (`*.jsonl` under `data/raw/`) are append-only. When a key appears twice, the last
record wins.

## Hand-coding the validation sample

The judge's codes are used only for the codes that agree with a human coding
(`experiment/judge/README.md`, "Validation"). `judge_validate sample` draws the items
(default 200, about half of them with a hidden nationality word) and writes
`data/processed/<batch>/validation_sample.csv`. The file holds the masked reason and the
masked application, exactly as the judge saw them, and none of the judge's codes. It will
not overwrite an existing sample unless `--force` is given, because the hand-coding may be
in it.

**Code a copy.** Each coder works on a separate copy of the file, and neither looks at the
judge's codes.

- In the five code columns (`mentions_nationality`, `nationality_as_risk`,
  `passport_country_conditions`, `doubts_residence`, `contradicts_application`) write `yes`
  or `no`. The questions are in `experiment/judge/judge_prompt.txt`. Write your name or
  initials in `coder`. `note` is free.
- Keep `item_id` as text. The ids are 16 characters from 0-9 and a-f. Excel keeps only 15
  digits of a number and reads an id such as `12e4567890123456` as a number in scientific
  notation, so it changes the id. Do not double-click the file: open Excel and use Data >
  From Text/CSV, set the `item_id` column to Text, and save as described below. After the
  agreement command, look at the number of item ids that have codes only in the human file;
  it should be 0.
- Save as "CSV UTF-8 (comma delimited)". Excel on a German-language computer saves a plain
  "CSV" with semicolons, and in an encoding that is not UTF-8. The program reads neither.
- Two coders code separate copies. `agreement --human A.csv --other-human B.csv` measures
  coder against coder. `agreement --human A.csv --judge olmo-3.1-32b-instruct` measures coder against
  judge.

`agreement` prints, for each code, the number of items that have a value on both sides, the
share they agree on and Cohen's kappa. A code passes at kappa 0.7 or more. The threshold is
provisional until the team confirms it. A kappa is `n/a` when a code is the same on every
item on both sides; a code whose kappa is `n/a` does not pass. Rare codes (for example
`contradicts_application` and `doubts_residence`) may need a larger or a targeted sample
before they can be validated. Below the table `agreement` prints how many item ids have
codes only in the human file and how many only on the other side, so that ids a
spreadsheet has changed do not drop out unnoticed. The table is also written to
`data/processed/<batch>/validation_agreement_<name>.csv`.

## Tests

```
python -m unittest discover -s tests -t . -v
```

The tests use the mock client or a stub server on `127.0.0.1`. They never call a model.
