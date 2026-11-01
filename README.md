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

## Status (2026-10-24)

Planning stage. No real model has been called and there are no results.

The project moved from bank customer checks to visitor visa applications on 2026-10-10.
The experiment is described in `experiment/README.md`; the team has not confirmed it
yet. The bank design of 2026-10-08 is in `research/old_design/bank_2026-10-08/`, the
hiring design of 2026-10-04 in `research/old_design/hiring_2026-10-04/`.

On 2026-10-24 the code was added (`pipeline/`): it builds the prompts, sends them to a
model, reads the answers and runs a judge model on the free-text reason of each answer.
It has been tried only with a mock model. The judge is exploratory, and it is not
confirmed by the team. `cluster/run_vllm.sbatch` is the script for the cluster; it has
never been run there.

## Repository layout

| path | contents |
|---|---|
| `experiment/README.md` | overview of the experiment and the run plan. Start here |
| `experiment/policy/` | the guidance the model is given (a paraphrase of the public rules for the Australian visitor visa) and the paragraph on nationality added in the second version |
| `experiment/applicants/` | `applicants.csv` (20 synthetic applicants) and `application_template.txt` (the layout of an application) |
| `experiment/countries/` | `applicant_nationalities.csv` (26 rows: the 22 Arab League nationalities and 4 placebo nationalities), `official_rules.csv` (what the official Australian rules say about each: the same for all) |
| `experiment/prompts/` | the main prompt and three wordings of the task |
| `experiment/costs/` | how a difference is turned into money, with prices and sources |
| `experiment/models.csv` | the three planned models |
| `experiment/judge/` | the judge that codes the free-text reason of each answer: prompt files, the terms that are hidden from it, the two judge models, `README.md` |
| `experiment/run_settings.csv` | the sampling settings for the audited models and for the judge |
| `pipeline/` | the code, one module per stage: `build_runs`, `run_models`, `parse_answers`, `judge_build`, `run_judge`, `judge_parse`, `judge_validate`. Calls no model unless a run is approved. `pipeline/README.md` has the commands |
| `cluster/` | `run_vllm.sbatch`, the Slurm script that starts vLLM and runs one stage on bwUniCluster (untested), and `README.md` |
| `tests/` | the unit tests; they use a mock model or a local stub server only |
| `data/raw/`, `data/processed/` | output of model runs, by batch; empty until the first real run. `data/README.md` has the layout |
| `docs/superpowers/plans/` | the implementation plan of the pipeline and the judge |
| `research/` | literature review, literature matrix, references, novelty assessment, literature notes, framing outline. Most of it was written for the hiring design |
| `research/visa_scenario/` | the research notes of 2026-10-10 behind the visa design |
| `research/scenario_reviews/` | the review notes that led from hiring to the bank scenario |
| `research/old_design/` | documents and materials of the three earlier designs; background and sources only |
| `paper/` | `proposal/`, `first_presentation/` (pitch, with slides), `second_presentation/` (midterm), `final_presentation/`, `final_paper/`; each has a README with the course criteria |
| `ETHICS.md` | ethics statement and handling rules |
| `CLAUDE.md` | project context and working rules for AI assistants |

Check the experiment files: `python -m pipeline.build_runs --example`

Run the tests: `python -m unittest discover -s tests -t . -v`

Try the whole pipeline with a mock model (no server, no real call): the walk-through in
`pipeline/README.md`. A real run needs the team's approval (`cluster/README.md`).

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
