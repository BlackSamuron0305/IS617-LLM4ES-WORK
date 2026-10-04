# Beyond "Arab" as a Single Category (working title)

A counterfactual audit of national-origin bias in LLM hiring. Team project for IS 617
(LLM4ESS), University of Mannheim, HWS26. Course repository:
<https://github.com/dess-mannheim/LLM4ESS>.

## Research question

When LLMs act as simulated recruiters for jobs in the Arab world (each CV and
its job ad are set in one of eight Arab League countries), do they evaluate
otherwise identical synthetic CVs differently when only the stated nationality
changes, and is there heterogeneity among individual Arab League member-state
nationalities that a single "Arab" or "MENA" category would hide? This is an
**audit of model behaviour**, not a hiring tool. Every applicant, CV and employer
is synthetic.

## Status (2026-10-04)

Planning stage. No real model has been called and there are no results.

The repository was cleaned up on 2026-10-04. The pipeline code (`src/`), its tests,
`scripts/`, the analysis plans (`analysis/`), `results/` and all mock output were
removed and will be added back when the experiment is run. Everything removed is in
git history at commit `670f827`.

`research/`, `preregistration.md` and the READMEs under `experiment/` and `config/` still
name the removed code, its commands and old paths (`stimuli/cvs.csv`,
`stimuli/nationalities.csv`, `prompts/`). Read those as history until the documents are
revised.

## Repository layout

| path | contents |
|---|---|
| `research/` | literature review, novelty assessment, design documents, status report |
| `preregistration.md` | draft preregistration (not frozen) |
| `experiment/prompts/` | the prompt text: `prompt_parts.csv` (the text pieces) and `prompt_recipes.csv` (the order they are assembled in) |
| `experiment/stimuli/` | `applicant_cvs.csv` (48 synthetic CVs, no nationality), `applicant_nationalities.csv` (34 nationality conditions), `jobs.csv`, `base_countries.csv`, `cv_template.txt`, and `building_blocks/` (what the CVs were composed from) |
| `config/` | settings tables written for the removed code: runs, models, analysis settings, leak terms, text flags, country covariates |
| `data/raw/`, `data/processed/` | output of model runs; empty until the first real run |
| `paper/` | `proposal/`, `first_presentation/` (pitch), `second_presentation/` (midterm), `final_presentation/`, `final_paper/`; each has a README with the course criteria |
| `DATA_FORMAT.md` | conventions shared by every CSV table |
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
