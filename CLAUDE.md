# CLAUDE.md

Project context for IS 617 (LLM4ESS) team project. Read this before doing anything in this repo.

## The project

IS 617 — Large Language Models for the Economic and Social Sciences, University of Mannheim, HWS26.
Course repo: https://github.com/dess-mannheim/LLM4ESS
Team of 3. Deliverable: 4–5 page short paper, ACL template, plus three presentations.

**Pivot (2026-09-29).** The team replaced the earlier outcome-bias / trading-records
study with the hiring audit below. The old project's files were deleted on
2026-10-01; they survive only in git history (commit 6ed2adb).

**Cleanup (2026-10-04).** The team removed the pipeline code (`src/hiringaudit/`), its
tests, `scripts/`, the analysis plans and power script (`analysis/`), `results/` and all
mock output. They will be added back when the experiment is run and are in git history
at commit 670f827. `prompts/` and `stimuli/` moved into `experiment/`, and the two
stimulus tables were renamed (`cvs.csv` → `applicant_cvs.csv`, `nationalities.csv` →
`applicant_nationalities.csv`). `research/`, `preregistration.md` and the READMEs under
`experiment/` and `config/` still name the removed code, commands and old paths; read
those as history until the documents are revised.

## Repository layout

- `research/`: literature, design and status documents.
- `experiment/prompts/`: prompt parts and recipes (see its README).
- `experiment/stimuli/`: CVs, nationalities, job ads, base countries, CV template and
  the building blocks the CVs were made from.
- `config/`: run, model and analysis settings tables for the removed code.
- `data/raw/`, `data/processed/`: empty until the first real run.
- `paper/`: `proposal/`, `first_presentation/` (pitch), `second_presentation/`
  (midterm), `final_presentation/`, `final_paper/`. Each has a README with the course
  criteria. The two paper folders use the ACL template.

## The research question

Working title: *Beyond "Arab" as a Single Category: A Counterfactual Audit of
National-Origin Bias in LLM Hiring.*

> Do LLMs used as simulated recruiters evaluate otherwise-identical synthetic
> applicants differently when only the applicant's stated national origin changes
> — and does a single "Arab"/"MENA" category hide systematic differences among
> individual Arab national origins?

The main contribution under test is **within-Arab heterogeneity**. "Arab vs
European" is a secondary benchmark only. This is an **audit** of model behaviour,
never a hiring tool. All applicants and employers are synthetic.

The novelty claim is tentative until `research/novelty_assessment.md` is final.
Do not state it as fact anywhere.

## Design at a glance

Authoritative sources, in order: `preregistration.md` (once frozen) →
`research/experimental_design.md` → `research/design_decisions.md` →
`research/design_contract.md` (the interface spec the code was built against).

- Stimuli are two tables: `experiment/stimuli/applicant_cvs.csv` (one row per base CV,
  no nationality) and `experiment/stimuli/applicant_nationalities.csv` (22 Arab League
  origins + German, Polish, Turkish benchmarks + 8 placebo nationalities + a not-stated
  control). Each prompt renders job ad + one CV row + one nationality row at call time,
  so clones are identical by construction.
- Setting: the Arab world. Each CV has one base country (UAE, Saudi Arabia, Qatar,
  Kuwait, Oman, Bahrain, Jordan, Egypt; mixed across CVs). Its employers, schools and
  the advertised job are all in that country. Nothing in the stimuli is German.
  `host_national` marks clones whose nationality equals the base country.
- Manipulation: a single `Nationality:` line in the CV. No names in the primary
  design. Jobs require English only; every CV lists English (C1) only.
- Base CVs: several per occupation, spread across qualification tiers. They are the
  independent units. Repetitions are replicates, not new candidates.
- Everything is a table (conventions in `DATA_FORMAT.md`; no YAML): run settings in
  `config/runs.csv` (one row per run: mock, pilot, main), models in
  `config/models.csv`, confirmatory analysis settings in `config/analysis_settings.csv`.
  Prompts are assembled from `experiment/prompts/prompt_parts.csv` in the order given
  by `experiment/prompts/prompt_recipes.csv`.
- Prompts (restructured 2026-10-04; the research documents still describe the earlier
  set): an initial prompt (plain, or with a neutrality instruction), then a follow-up
  message that either rates one applicant or chooses between two (nationality-swap ×
  order-swap quads). Choosing has two versions: A or B, and A, B or lottery. The
  principle probe was dropped.
- Outcomes: interview yes/no and a 0–100 job-fit score. Never call the score a
  hiring probability.

## Compute and models

Open-weight models served with vLLM on bwUniCluster (KIT) through the
OpenAI-compatible provider. There is no API budget. **Never launch real or paid model
calls without explicit approval.** The removed runner refused them unless
`--allow-real-calls` was passed; any new runner must keep that guard.

## Deadlines

| Date | Milestone |
|---|---|
| 13.10.2026 | Pitch — 5 min + 5 min Q&A |
| 11–12.11.2026 | Midterm — requires preliminary results |
| 09–10.12.2026 | Final — 12 min + 15 min Q&A (15 of 25 points are Q&A) |
| 08.01.2027 | Report due |

## Working rules

**AI usage policy.** The chair has had cases that nearly failed students over
LLM-written text, and the report requires a per-task declaration of AI use. Claude
does design, code, analysis and internal research documents. Claude does **not**
write report or presentation prose. Never paste generated text into `paper/`.

**No fabricated results or citations.** Mock-provider output is labelled
`is_mock` and watermarked. Every citation carries a verification level in
`research/literature_matrix.csv`. Verify against the full text before anything goes
in the paper.

**Pre-registration discipline.** Do not choose countries, occupations, prompts or
models after seeing which ones produce the largest disparity. Confirmatory and
exploratory analyses stay separate.

**Novelty and scope discipline.** Do not add experimental factors to chase novelty.
New ideas go to the parked list. The rubric rewards a finished, defensible
experiment: Data [10] + Methods [10] + Results [10] = 30 of 50 report points, and
15 of 25 final-presentation points are Q&A.

## Parked — publication extension, not the course project

- Name-based robustness experiment (beyond a small secondary check)
- German-language prompts
- Arabic-centric models (e.g. ALLaM, Jais) as an extra model family
- LLM-judge coding of free-text reasons
- Foreign-degree / credential-recognition channel

## Open decisions

See the "Unresolved decisions" section of `research/status_report.md`.
