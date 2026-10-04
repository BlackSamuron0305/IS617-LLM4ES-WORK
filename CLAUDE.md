# CLAUDE.md

Project context for IS 617 (LLM4ESS) team project. Read this before doing anything in this repo.

## The project

IS 617 — Large Language Models for the Economic and Social Sciences, University of Mannheim, HWS26.
Course repo: https://github.com/dess-mannheim/LLM4ESS
Team of 3. Deliverable: 4–5 page short paper, ACL template, plus three presentations.

**Pivot (2026-09-29).** The team replaced the earlier outcome-bias / trading-records
study with the hiring audit below. The old project's files were deleted on
2026-10-01; they survive only in git history (commit 6ed2adb).

**Redesign and cleanup (2026-10-04).** The team simplified the experiment and removed
everything built for the earlier design: the pipeline code (`src/hiringaudit/`), its
tests, `scripts/`, the analysis plans (`analysis/`), `config/`, `results/`, all mock
output, `pyproject.toml` and `uv.lock`. All of it is in git history at commit 670f827.
The code has to be rewritten for the current design. The documents of the earlier design
are in `research/old_design/`.

## Repository layout

- `experiment/README.md`: overview of the experiment and the current run plan. Start
  here.
- `experiment/prompts/`: two folders, `without_ignore_prompt/` and
  `with_ignore_prompt/`. Each has `hiring/` and `promotion/`, and each of those holds
  its `main_prompt.txt` and one subfolder per experiment and version with the full
  message text.
- `experiment/jobs/`: `jobs.csv` (20 jobs) and the job ad template.
- `experiment/cvs/`: `applicant_cvs.csv` (20 CVs, one per job) and the CV template.
- `experiment/countries/`: `base_countries.csv` (the 22 countries a job is set in),
  `applicant_nationalities.csv` (the 29 nationality rows) and `country_covariates.csv`
  (World Bank income and region data).
- `experiment/models.csv`: the four planned models.
- `data/raw/`, `data/processed/`: empty until the first real run.
- `research/`: literature review, literature matrix, references, novelty assessment,
  literature notes (`lit_parts/`), framing outline.
- `research/old_design/`: design documents and draft preregistration of the earlier
  design. Background and sources only; they do not describe the current experiment.
- `paper/`: `proposal/`, `first_presentation/` (pitch), `second_presentation/`
  (midterm), `final_presentation/`, `final_paper/`. Each has a README with the course
  criteria. The two paper folders use the ACL template.
- `ETHICS.md`: ethics statement and handling rules.

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

The current design is described in `experiment/README.md` and the READMEs of its
folders. Those are authoritative. `research/old_design/` is not.

- Jobs and CVs: 20 jobs, one CV per job, all at a middle qualification level. The CVs
  are the independent units. Job ads and CVs name no city, school or company from any
  country. Jobs require English only; every CV lists English (C1) only.
- Setting: the Arab world. Every job is run once in each of the 22 Arab League
  countries in `base_countries.csv`: the job ad, the CV and the main prompt carry a
  `{country}` placeholder. `host_national` means the nationality equals that country.
- Manipulation: a single `Nationality:` line in the CV. No names.
  `applicant_nationalities.csv` has 22 Arab League origins, German and Turkish
  benchmarks, 4 placebo nationalities and a not-stated control.
- Comoros, Djibouti and Somalia are flagged `arab_identity_contested`. The flag does
  not exclude them from any comparison; the paper should point them out.
- Prompts: a main prompt, then a follow-up message; plain text files, one per message.
  Experiment 1 rates one person. Experiment 2 chooses between two people who have the
  same CV, in two versions: A, B or lottery, and A or B. Experiment 3 repeats both with
  a main prompt that adds an ignore-nationality paragraph. All of it exists for two
  scenarios, hiring and promotion (added by the team on 2026-10-04 although the scope
  rule below parks new factors).
- Outcomes: a 0–100 fit score and yes/no (interview, or promote), and the choice. Never
  call the score a hiring probability.
- Run plan: four models, four blocks, 128,480 runs per model.

## Compute and models

Open-weight models (`experiment/models.csv`) served with vLLM on bwUniCluster (KIT).
There is no API budget. **Never launch real or paid model calls without explicit
approval.** Any new runner must refuse real calls unless that approval is given
explicitly, as the removed one did.

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

**No fabricated results or citations.** Output of mock or test runs is labelled as
such and is never reported as a result. Every citation carries a verification level in
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

See "Open" in `experiment/README.md`. The largest one: the current design has no
written hypotheses or analysis plan. The draft preregistration in `research/old_design/`
belongs to the earlier design. Both have to be written before the first real run.
