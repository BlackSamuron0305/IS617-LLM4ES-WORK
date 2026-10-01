# hiringaudit: a counterfactual audit of LLM CV screening (DRAFT)

IS 617 (LLM4ESS), University of Mannheim, HWS26. Draft engineering README; the
research documents in `research/` are authoritative for the design.

## Research question

When LLMs act as simulated recruiters for jobs in the Arab world (each CV and
its job ad are set in one of eight Arab League countries), do they evaluate
otherwise identical synthetic CVs differently when only the stated nationality
changes, and is there heterogeneity among individual Arab League member-state
nationalities that a single "Arab" or "MENA" category would hide? This is an
**audit of model behaviour**, not a hiring tool. Every applicant, CV and employer
is synthetic.

## Design at a glance

- **Stimuli:** two tables. `stimuli/cvs.csv` holds 6 occupations x 8 base CVs
  (tiers 2 strong / 4 adequate / 2 borderline, defined relative to the job ad's
  experience minimum; borderline CVs are 12-18 months short of it).
  `stimuli/nationalities.csv` holds 34 nationality conditions (22 Arab League
  states; German reference, Polish, Turkish; 8 placebo nationalities; and `NONE` =
  line omitted). Every prompt combines one CV row with one nationality row, so the
  clones of a CV differ only in the `Nationality:` line by construction; each CV
  also has one positive-control clone (the `NONE` clone minus all its
  qualification lines, e.g. a master's and the preceding bachelor's). **Setting:** every CV is set entirely in one of eight Arab League base
  countries (ARE, SAU, QAT, KWT, OMN, BHR, JOR, EGY; 6 CVs each): its location,
  every employer city and its institution are there, and the job ad it is shown
  with is located in its base city. Nothing in a CV, job ad or prompt is German.
  The two CVs of a forced-choice pair share their base country. `host_national`
  (nationality code = base country) is carried into the raw records and the
  processed tables. Jobs require English only; every CV lists English (C1) only.
  CVs have a profile, key achievements, 2-4 roles, education, 8-12 skills and up
  to 3 certificates; all CV dates end in mid-2024.
- **Tasks:** independent evaluation under `baseline` and `neutrality` (one inserted
  paragraph), each in K = 3 wording variants; forced choice between two same-tier
  CVs with the same base country in quads (nationality swap x position swap; `NONE` and placebo levels
  excluded; wording variants balanced per nationality); a principle probe
  (15 statements, half reverse-keyed, 3 controls, 7 contexts). Placebo
  nationalities appear only in baseline independent evaluation.
- **Models:** open-weight models served by vLLM on bwUniCluster (OpenAI-compatible
  endpoint); a deterministic mock provider for everything that does not need a model.
- **Runs** are the rows of `config/runs.csv` (every setting a column). **Pilot**
  (`--run pilot`): 3 occupations x 6 CVs, r = 3, all 4 main-study models, 10,807
  calls per model (43,228 in total). **Main** (`--run main`, 106,548 calls): sizes
  are PROVISIONAL until the pilot power analysis.
- **Inputs are tables.** Every input is a CSV table with the same conventions
  (`DATA_FORMAT.md`); prompts are assembled from structured parts and recipes
  (`prompts/README.md`); configuration is documented in `config/README.md`.

## Research documents

Authority order for the design: `preregistration.md` (once frozen) →
`research/experimental_design.md` → `research/design_decisions.md` →
`research/design_contract.md` (the interface spec the code was built against; §00000
v0.6, §0000 v0.5, §000 v0.4, §00 v0.3 and §0 v0.2 amendments).

| document | contents |
|---|---|
| `preregistration.md` | draft preregistration (not frozen): hypotheses and decision rules, design, exclusions, SESOIs, sample-size and stopping rule, freeze checklist and freeze procedure (§14), open discrepancies (§16) |
| `research/design_contract.md` | shared interface spec; §00000 = v0.6 amendments (CSV tables and prompt parts instead of YAML and text templates; structural only), §0000 = v0.5 (Arab-world setting, base-country allocation, host nationals and HX, extended CVs), §000 = v0.4 (table-based stimuli, English only; its same-region rule is superseded), §00 = v0.3 (review fixes), §0 = v0.2 |
| `research/experimental_design.md` | causal framework, estimands, stimuli, forced-choice and principle-probe design, pilot, sample-size rule, robustness checks R1–R13 and HX |
| `research/hypotheses.md` | research questions, hypotheses (incl. H1e placebo floor), SESOIs, decision rules, multiplicity families |
| `research/design_decisions.md` | literature-to-design traceability (D01–D48), status of every decision, consolidated open decisions, deviations from the contract |
| `research/variables.md` | every variable and the single place it is set |
| `research/threats_to_validity.md` | threats (ids I/C/S/E) with mitigations and probes |
| `research/adversarial_review.md`, `research/review_response.md` | independent pre-pilot review and the status of every finding |
| `research/literature_review.md`, `research/novelty_assessment.md` | literature synthesis and novelty verdict |
| `research/literature_matrix.csv`, `research/references.bib` | one row / entry per source with verification level; all documents cite these keys |
| `analysis/statistical_analysis_plan.md` | estimators, tests, missing data, blinding and freeze gate (SAP) |
| `analysis/model_specifications.md`, `analysis/multiple_testing_plan.md` | exact model formulas; testing hierarchy and Holm / BH families |
| `analysis/power_analysis.py` | simulation-based sample-size planning (placeholder variance components until the pilot) |
| `config/analysis_settings.csv` | frozen confirmatory analysis settings (SESOIs, α, outcome, resampling counts) |
| `ETHICS.md` | ethics statement and handling rules |

`scripts/fetch_country_covariates.py` downloads the World Bank covariates for
hypothesis H1d (GDP per capita PPP, income group, region and the sub-Saharan
indicator) into `config/country_covariates.csv`, with the retrieval date on every row.
The values are fetched, never typed by hand, and the file is frozen before main-study
data collection.

## Repository layout

| path | contents | owner |
|---|---|---|
| `research/` | research documents (see "Research documents" above) | methodology / lead |
| `analysis/` | analysis plans and `power_analysis.py` | statistician |
| `DATA_FORMAT.md` | the CSV conventions shared by every input table, and where each table lives | engineering |
| `scripts/` | `fetch_country_covariates.py` (World Bank covariates for H1d, lead); `build_cv_table.py` (how `stimuli/cvs.csv` was built) | lead / engineering |
| `stimuli/` | **the two stimulus tables** `cvs.csv` and `nationalities.csv`, the CV template `cv_template.txt`, the job ads `jobs.csv`, the base countries `base_countries.csv`, the CV `building_blocks/` (builder input), and `README.md` (column reference, notes on the nationality set) | engineering (nationality notes: lead) |
| `config/` | `runs.csv` (mock / pilot / main), `models.csv`, `leak_terms.csv`, `text_flags.csv`, `analysis_settings.csv` (statistician), `country_covariates.csv` (lead), `README.md` (column reference) | engineering |
| `prompts/` | `prompt_parts.csv` (fixed text), `prompt_recipes.csv` (how each condition x variant is assembled), `principle_items.csv`, `README.md` (worked example) | engineering |
| `src/hiringaudit/` | package: stimuli, validation, randomisation, providers, runner, parser, CLI | engineering |
| `src/hiringaudit/analysis/` | statistical analysis (`run_analysis`) | statistician |
| `data/raw/<run_id>/` | append-only model responses + run manifest | produced by `run` |
| `data/processed/<run_id>/` | analysis tables (regenerable) | produced by `parse` |
| `results/<run_id>/{blind,unblinded}/` | figures and tables | produced by `analyze`; the two modes never share a directory |
| `paper/` | the report | team |

## Setup

Python 3.11+ (developed on 3.14). Runtime dependencies: numpy, pandas, scipy,
statsmodels, matplotlib, pydantic, jsonschema, pyarrow, tqdm. Provider SDKs
are optional extras (`openai`, `anthropic`, `google`, `local`); the vLLM path needs
none of them.

With the packages already installed system-wide, no install is needed; point
Python at `src/` (Git Bash shown; in PowerShell use `$env:PYTHONPATH = "src"`):

```bash
export PYTHONPATH=src
python -m hiringaudit --help
```

A pinned environment is in `uv.lock` (created with `uv lock`).

## Stimuli: the two tables

The stimuli are two UTF-8 CSV tables you can open and edit in Excel or an IDE
(column reference and editing notes: `stimuli/README.md`):

- `stimuli/cvs.csv`: one row per base CV (48 rows) with every CV field in wide,
  readable columns (profile, `achievement1` ... key achievements, `exp1_*` ...
  jobs, `edu1_*` ... education, skills, `cert1_*` ... certificates) plus metadata
  (tier, pilot flag, `base_country`, `base_city`, applicant reference, experience
  months, the positive-control education entries). No nationality column.
- `stimuli/nationalities.csv`: one row per nationality condition (code, country,
  demonym, group, subregion, Arab League accession year, contested flag, note).

Nothing is pre-rendered. When a prompt is built, the runner renders the CV row with
the nationality row through the one template `stimuli/cv_template.txt`: the
`Nationality:` line is the only substituted line (omitted for `NONE`; the positive
control also drops every qualification line that satisfies the ad's designated
must-have). The job ad of the CV's occupation (`stimuli/jobs.csv`) is localized to
the CV's base city (`{city}, {country}`), and both are inserted into the prompt
recipe of the trial's condition and wording variant (`prompts/README.md` has a
fully worked example). Every rendered prompt is stored once in
`data/raw/<run_id>/prompts.jsonl`.

```bash
python -m hiringaudit validate-stimuli     # exit code 1 on any violation
```

After editing either table, validate. The validator fails if:

- a table is malformed: duplicate CV ids or applicant references, unknown
  occupation or tier, missing DEU or NONE, a duplicate or multi-line demonym, or a
  design constant (availability, languages) that differs between rows;
- a CV lists any language other than English;
- a CV's base country is not one of the base countries in `stimuli/base_countries.csv`
  (Arab League rows of `nationalities.csv`), its base city is not that country's,
  or its Location, work-authorization or driving-licence line is not the one
  derived from the base country;
- an employer city or an educational institution is outside the CV's
  base-country whitelist (`stimuli/base_countries.csv`, `stimuli/building_blocks/institutions.csv`);
- a CV does not have exactly one same-occupation, same-tier partner with the same
  base country (its forced-choice pair) with the same pilot status;
- an applicant reference encodes a nationality;
- a listed origin cue appears in a rendered CV outside its `Nationality:` line.
  The lists are in `config/leak_terms.csv`: demonyms and country names, capitals
  and major cities of every listed country, region names, citizenship and
  residence vocabulary, religious terms, languages other than English, and German
  terms (cities, institutions, credentials, legal forms, HGB, euro, umlauts). Only
  the CV's own base country and its cities are exempt. The job ads (localized to
  every base country), the system prompt, every prompt part, the assembled prompt templates and the
  principle-probe contexts are scanned too. This is a list-based check: it catches
  the listed cues, not every conceivable one;
- anything is dated after the reference date (06/2024), or the stated experience
  months do not match the job dates;
- the tiers are not ordered by relevant experience within an occupation, or a
  borderline CV has as much total experience as an adequate one;
- a job's bullets or employer do not belong to its title, or a key achievement
  does not belong to the CV's tier (checked against `stimuli/building_blocks/`);
- the lines of the positive-control entries (`positive_control_education`) are not exactly the CV's qualification lines, or a
  qualification cue (degree line, diploma / degree / university / "qualified"
  wording) survives in the positive control;
- any rendered CV x nationality combination differs from the DEU clone other than
  in the `Nationality:` line (every combination is rendered in memory);
- the prompt tables are malformed (see `prompts/README.md`, "Checks"), in
  particular when a `neutrality` recipe is not its `baseline` recipe plus exactly
  one added part, the neutrality paragraph, before the output instructions (same
  for forced choice).

`cvs.csv` was built by `python scripts/build_cv_table.py --force` (2026-10-01,
Arab-world setting) from `stimuli/building_blocks/`, `stimuli/jobs.csv` and
`stimuli/base_countries.csv` (fixed seed); the table is the source of truth
afterwards and the runtime never reads the building blocks. The builder refuses to overwrite the table
without `--force`.

## Models and credentials

Models are defined in `config/models.csv` (one row per alias: provider, exact model id,
capabilities, provenance fields such as `revision`). Keys and endpoints come from
environment variables only; copy `.env.example` to `.env` (git-ignored) or export
them:

- vLLM on bwUniCluster: `VLLM_BASE_URL` (e.g. `http://<node>:8000/v1`, via an SSH
  tunnel) and `VLLM_API_KEY` (if the server uses one).
- Optional API models: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`. Their
  model ids are `status: unverified` and must be pinned before any run.

Serve one model per vLLM instance with a pinned revision and without the model's
own generation defaults (the same command is in `config/README.md`), then record
the revision in the `revision` column of `config/models.csv`:

```bash
vllm serve <model_id> --revision <sha> --generation-config vllm --seed 0 --port 8000 --api-key "$VLLM_API_KEY"
```

Qwen3 thinking is disabled through `chat_template_kwargs` (logged per record).
Primary-arm requests use temperature 0.7, top_p 1.0 and `top_k = -1` for every
model (A10); the greedy robustness arm uses temperature 0.

## Running

```bash
python -m hiringaudit plan --run mock             # call counts + rough token estimate
python -m hiringaudit run  --run mock --quiet     # mock end to end, seconds, no network
python -m hiringaudit plan --run pilot            # 43,228 calls
python -m hiringaudit plan --run main             # 106,548 calls (PROVISIONAL sizes)
```

`--run` names a row of `config/runs.csv`; the former `--config config/<x>.yaml`
is refused with a pointer to `--run`.

Real providers are refused (exit code 2) unless all of these hold:
`--allow-real-calls` is given; every selected model has a pinned `revision` and is
not `status: unverified`; `git status` shows no modified or untracked files under
`src/`, `config/`, `prompts/` or `stimuli/`, both in the data root and in the
repository that holds the running code (commit first); and the vLLM server serves
exactly the configured `model_id`.

```bash
python -m hiringaudit run --run pilot                       # refused: no --allow-real-calls
python -m hiringaudit run --run pilot --allow-real-calls    # refused while revisions are unpinned
```

The real pilot, once those conditions hold, on the cluster with `VLLM_BASE_URL`
set (not run here), one model per session:

```bash
python -m hiringaudit run --run pilot --allow-real-calls --models qwen3-8b
```

Behaviour of `run`:

- Runs are resumable. Re-running skips every call with a final record; calls whose
  only records are API errors are tried again, in at most 3 sessions (then the API
  error is final and listed in the manifest). `--limit N` makes at most N calls.
- Only transport/API errors are retried within a call; malformed, empty or refused
  outputs are final.
- Calls run in a seeded random order within each model.
- A run can only be resumed with identical inputs (its row of `runs.csv`, full
  model specs, the assembled prompt templates, both stimulus tables, the CV
  template, `jobs.csv`, `principle_items.csv`, `prompt_parts.csv`,
  `prompt_recipes.csv`, parser version). The SHA-256 of each is in the run manifest. The default run id contains a hash of these, so changing any of
  them starts a new run.
- Mock run ids must start with `mock`, real ones must not.
- Technical stop rule: once a model has 5 % of its planned calls answered, it is
  stopped if more than 10 % of those answers are non-ok. Transport (API) errors
  count neither way. It uses parse-status counts only, never nationality, and is
  recorded in the run manifest.

## Outputs and the raw-vs-processed policy

- `data/raw/<run_id>/responses.jsonl`: one line per call attempt series,
  append-only, never rewritten; failures are records. `prompts.jsonl` stores each
  rendered prompt once. `run_manifest.json` has the config snapshot, the run
  identity and hashes, model provenance, parser version and fingerprint, seeds,
  stop-rule decisions, git commit, package versions and one entry per session.
  `fc_design.json` stores the forced-choice design.
- `data/processed/<run_id>/`: `evaluations.csv`, `forced_choice.csv`,
  `principle.csv`, `parse_summary.json`. Evaluations carry `base_country` and
  `host_national`; forced choice carries `base_country`, `host_national_a` and
  `host_national_b`. `parse` refuses when the parser differs
  from the one recorded for the run; `parse --exploratory` then writes clearly
  marked tables to `data/processed/<run_id>__exploratory/`.
- **Git policy.** Real-run raw outputs are the primary evidence and are committed
  (they are deliberately not git-ignored); processed tables are small and committed
  too. Mock runs are synthetic, carry `is_mock = true`, have run ids starting with
  `mock`, and are git-ignored (`data/raw/mock*/`, `data/processed/mock*/`,
  `results/mock*/`). Everything from the mock is labelled
  "SYNTHETIC MOCK DATA - NOT RESULTS".

```bash
python -m hiringaudit parse --run-id mock_pipeline_test
python -m hiringaudit manifest --run-id mock_pipeline_test --run mock   # provenance + coverage
```

## Analysis, figures and tables

```bash
python -m hiringaudit analyze --run-id mock_pipeline_test             # blind (default) -> results/mock_pipeline_test/blind/
python -m hiringaudit analyze --run-id mock_pipeline_test --unblind   # unblinded -> results/mock_pipeline_test/unblinded/
```

`analyze` hands `data/processed/<run_id>/` to
`hiringaudit.analysis.run_analysis` (maintained separately in
`src/hiringaudit/analysis/`). It is blind by default: no per-origin means or
nationality contrasts. `--unblind` asks for full output; for data that are not
entirely mock, `run_analysis` refuses unless `preregistration.md` and
`config/prereg_freeze.json` are committed at HEAD and unchanged, the freeze file holds
the SHA-256 of `preregistration.md`, the preregistration has no unresolved decision or
pin markers, and `config/analysis_settings.csv` is committed and unchanged
(procedure: `preregistration.md` §14.2; SAP §0). This is checked relative to `--root`;
a refusal is a one-line error with exit code 2.
Every unblinded run is appended to `results/unblinding_log.jsonl`. Confirmatory
settings come from `config/analysis_settings.csv`; an analysis config (`analyze --config <file.json>`) that changes any
of them stamps every output "EXPLORATORY OVERRIDE". To reproduce figures and tables
for a run: `parse`, then `analyze`.

## Tests

```bash
python -m pytest -q
```

This runs every test, including the analysis tests. The engineering tests alone:

```bash
python -m pytest tests/test_tables.py tests/test_validation.py tests/test_prompts.py tests/test_randomization.py tests/test_parsing.py tests/test_runner.py tests/test_mock_provider.py tests/test_text_flags.py tests/test_prompt_snapshot.py -q
```

The tests never call a real provider. They cover the two tables and the builder,
rendering every CV x nationality combination, validator failures on tampered table
rows, the leak, base-country, German-term and tier checks, forced-choice pairs
sharing a base country, `host_national`, prompt
interventions, randomisation and forced-choice balance, output parsing,
deterministic ids, resume and retry behaviour, the real-call guards, the stop rule
and the text flags. `tests/test_prompt_snapshot.py` proves that the move from YAML
and text files to CSV tables (2026-10-01) changed no behaviour: every rendered
prompt of the mock, pilot and main runs, every job ad and CV clone, every trial
id, record id, seed and call count equals a snapshot taken before the move
(`tests/fixtures/`).
