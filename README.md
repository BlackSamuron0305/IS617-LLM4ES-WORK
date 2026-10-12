# Which Arab? (working title)

How LLMs rate visa applicants from the 22 Arab League countries. An audit of model
behaviour with identical synthetic visa applications. Team project for IS 617 (LLM4ESS),
University of Mannheim, HWS26. Course repository:
<https://github.com/dess-mannheim/LLM4ESS>.

## Research question

LLM bias among the Arab countries. The motivation is Islamophobia; a visa form asks for
no religion, it asks for a passport. Two questions:

1. **Is there a bias?** When an LLM is given the guidance of a visa office and an
   application for a visitor visa, does its risk rating differ among the 22 Arab League
   nationalities although the application is identical and the official rules are the
   same for all of them? Why should a Syrian applicant be rated worse than an Emirati
   one with the same application?
2. **Can the countries be grouped into rich, normal and poor?** Do the models sort the
   22 along these three groups (World Bank income classes: 6, 12 and 4 countries)?

Also: does telling the model help, and what would the difference cost an applicant? All applicants were born in the
United Arab Emirates and live and work there; the visa is an Australian visitor visa.
This is an **audit of model behaviour**, not a tool for assessing applicants. Every
applicant and every employer is synthetic.

## Status (2026-10-10)

Planning stage. No real model has been called and there are no results.

The project moved from bank customer checks to visitor visa applications on 2026-10-10.
The experiment is described in `experiment/README.md`; the team has not confirmed it
yet. The bank design of 2026-10-08 is in `research/old_design/bank_2026-10-08/`, the
hiring design of 2026-10-04 in `research/old_design/hiring_2026-10-04/`. The code that
sends the runs and reads the answers does not exist yet; `scripts/build_runs.py` builds
and checks the prompts only.

## Repository layout

| path | contents |
|---|---|
| `experiment/README.md` | overview of the experiment and the run plan. Start here |
| `experiment/policy/` | the guidance the model is given (a paraphrase of the public rules for the Australian visitor visa) and the paragraph on nationality added in the second version |
| `experiment/applicants/` | `applicants.csv` (20 synthetic applicants) and `application_template.txt` (the layout of an application) |
| `experiment/countries/` | `applicant_nationalities.csv` (26 rows: the 22 Arab League nationalities and 4 placebo nationalities), `official_rules.csv` (what the official Australian rules say about each: the same for all) |
| `experiment/prompts/` | the main prompt and three wordings of the task |
| `experiment/costs/` | how a difference is turned into money, with prices and sources |
| `experiment/models.csv` | the four planned models |
| `scripts/build_runs.py` | puts the prompts together, checks them and prints the counts; calls no model |
| `data/raw/`, `data/processed/` | output of model runs; empty until the first real run |
| `research/` | literature review, literature matrix, references, novelty assessment, literature notes, framing outline. Most of it was written for the hiring design |
| `research/visa_scenario/` | the research notes of 2026-10-10 behind the visa design |
| `research/scenario_reviews/` | the review notes that led from hiring to the bank scenario |
| `research/old_design/` | documents and materials of the three earlier designs; background and sources only |
| `paper/` | `proposal/`, `first_presentation/` (pitch, with slides), `second_presentation/` (midterm), `final_presentation/`, `final_paper/`; each has a README with the course criteria |
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
