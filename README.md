# Which Arab? (working title)

How LLMs rate bank customers from the 22 Arab League countries in money-laundering
checks. An audit of model behaviour with identical synthetic customer files. Team project
for IS 617 (LLM4ESS), University of Mannheim, HWS26. Course repository:
<https://github.com/dess-mannheim/LLM4ESS>.

## Research question

A bank has to check every new customer for money-laundering risk and has to record the
customer's nationality. When an LLM is given the bank's policy and a customer file, does
its risk rating change when only the stated nationality changes, and is there
heterogeneity among the 22 Arab League nationalities that a single "Arab" category would
hide? This is an **audit of model behaviour**, not a tool for checking customers. Every
customer, the bank and every employer is synthetic.

## Status (2026-10-08)

Planning stage. No real model has been called and there are no results.

The project moved from hiring to bank customer checks on 2026-10-08. The experiment is
described in `experiment/README.md`. The hiring design of 2026-10-04 is in
`research/old_design/hiring_2026-10-04/`. The code that sends the runs and reads the
answers does not exist yet; `scripts/build_runs.py` builds and checks the prompts only.

## Repository layout

| path | contents |
|---|---|
| `experiment/README.md` | overview of the experiment and the run plan. Start here |
| `experiment/policy/` | the invented bank's policy and the paragraph on nationality added in the second version |
| `experiment/customers/` | `customers.csv` (20 synthetic customer files) and `customer_file_template.txt` (the file layout) |
| `experiment/countries/` | `customer_nationalities.csv` (28 rows: 22 Arab League, 2 benchmark, 4 placebo; with the EU high-risk list status), `country_covariates.csv` (World Bank income and region data) |
| `experiment/prompts/` | the main prompt and three wordings of the task |
| `experiment/models.csv` | the four planned models |
| `scripts/build_runs.py` | puts the prompts together, checks them and prints the counts; calls no model |
| `data/raw/`, `data/processed/` | output of model runs; empty until the first real run |
| `research/` | literature review, literature matrix, references, novelty assessment, literature notes, framing outline |
| `research/scenario_reviews/` | the review notes that led from hiring to the bank scenario |
| `research/old_design/` | documents and materials of the two earlier hiring designs; background and sources only |
| `paper/` | `proposal/`, `first_presentation/` (pitch), `second_presentation/` (midterm), `final_presentation/`, `final_paper/`; each has a README with the course criteria |
| `ETHICS.md` | ethics statement and handling rules |
| `CLAUDE.md` | project context and working rules for AI assistants |

Check the experiment files: `python scripts/build_runs.py --example`

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
