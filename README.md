# Which Arab? (working title)

How LLMs treat candidates from the 22 Arab League countries in hiring and promotion.
An audit of model behaviour with identical synthetic CVs. Team project for IS 617
(LLM4ESS), University of Mannheim, HWS26. Course repository:
<https://github.com/dess-mannheim/LLM4ESS>.

## Research question

When LLMs act as simulated recruiters for jobs in the Arab world (every job is set once
in each of the 22 Arab League countries), do they evaluate otherwise identical synthetic
CVs differently when only the stated nationality changes, and is there heterogeneity
among individual Arab League member-state nationalities that a single "Arab" or "MENA"
category would hide? This is an **audit of model behaviour**, not a hiring tool. Every
applicant, CV and employer is synthetic.

## Status (2026-10-04)

Planning stage. No real model has been called and there are no results.

The experiment was simplified on 2026-10-04 and is described in `experiment/README.md`.
The code, tests, settings and analysis plans built for the earlier design were removed
and are in git history at commit `670f827`. The code that builds and sends the runs has
to be rewritten for the current design.

## Repository layout

| path | contents |
|---|---|
| `experiment/README.md` | overview of the experiment and the run plan. Start here |
| `experiment/prompts/` | the prompts as plain text, in two folders (`without_ignore_prompt/`, `with_ignore_prompt/`), each split into `hiring/` and `promotion/` with a main prompt and one subfolder per experiment and version |
| `experiment/jobs/` | `jobs.csv` (20 jobs, one per row) and `job_ad_template.txt` (the job ad layout) |
| `experiment/cvs/` | `applicant_cvs.csv` (20 synthetic CVs, one per job, no nationality and no country) and `cv_template.txt` (the CV layout) |
| `experiment/countries/` | `base_countries.csv` (the 22 Arab countries; every job is run once in each), `applicant_nationalities.csv` (29 rows: 22 Arab, 2 benchmark, 4 placebo, 1 not stated), `country_covariates.csv` (World Bank income and region data) |
| `experiment/models.csv` | the four planned models |
| `data/raw/`, `data/processed/` | output of model runs; empty until the first real run |
| `research/` | literature review, literature matrix, references, novelty assessment, literature notes, framing outline |
| `research/old_design/` | design documents and draft preregistration of the earlier design; background and sources only |
| `paper/` | `proposal/`, `first_presentation/` (pitch), `second_presentation/` (midterm), `final_presentation/`, `final_paper/`; each has a README with the course criteria |
| `ETHICS.md` | ethics statement and handling rules |
| `CLAUDE.md` | project context and working rules for AI assistants |

## Deadlines

| Date | Milestone |
|---|---|
| 13.10.2026 | Pitch: 5 min + 5 min Q&A |
| 11-12.11.2026 | Midterm: 10 min + 5 min Q&A, needs preliminary results |
| 09-10.12.2026 | Final: 12 min + 15 min Q&A |
| 08.01.2027 | Report due |

## Rules

- **AI use.** The report must declare which tasks were assisted by AI tools. Report and
  presentation text is written by the team, not generated.
- **No fabricated results or citations.** Every citation carries a verification level in
  `research/literature_matrix.csv`.
- **No real or paid model calls without the team's explicit approval.**
