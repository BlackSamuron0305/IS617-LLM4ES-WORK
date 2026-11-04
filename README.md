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

## Status (2026-11-04)

The experiment ran in full on bwUniCluster (2026-11-01 to 2026-11-03): three audited models, twelve prompt variants, a boundary
set, nine extra models and a judge. The tables are in `results/`, the midterm deck in `paper/second_presentation/`, and the
final report exists only as visible notes in `paper/final_paper/paper.tex`. The branch `bias-deep-dive` adds exploratory
work (negative applicants, more variants, the Qwen family, reference and conflict nationalities, a judge lab). The setting is a
Schengen visa to Estonia (since 2026-11-01); the team has not confirmed the design. `CLAUDE.md` has the history and the
findings.

## Repository layout

`docs/REPO_MAP.md` has the full annotated tree. In short:

| path | contents |
|---|---|
| `experiment/` | everything that defines the experiment. `README.md` first |
| `experiment/inputs/` | `policy/` (the guidance), `applicants/`, `countries/`, `costs/` |
| `experiment/prompts/` | `main_prompts/`, `task_wordings/`, `variants.csv` |
| `experiment/config/` | `models.csv`, `run_settings.csv` |
| `experiment/planning/` | `analysis_plan.md`, `design_review.md`, `deviations.md` |
| `experiment/judge/` | the judge: prompts, codebook, `lab/` (other versions), `validation/` (hand coding) |
| `experiment/deep_dive/` | the exploratory work of the branch `bias-deep-dive` |
| `pipeline/` | the code, in packages: `core/`, `design/`, `answers/`, `judge/`, `analysis/`, `deep_dive/`. `pipeline/README.md` has the commands |
| `tests/` | the unit tests, one folder per package; they use a mock model or a local stub server only |
| `cluster/` | the Slurm scripts for bwUniCluster and `README.md` |
| `data/raw/` | the model answers, grouped by run, then model, then batch (`data/README.md`) |
| `data/processed/` | the same folders as tables; rebuilt with the pipeline, not committed |
| `results/` | summary tables by run (`audited_models/`, `extra_models/`, `deep_dive/`); `results/README.md` |
| `paper/` | `proposal/`, `first_presentation/`, `second_presentation/`, `final_presentation/`, `final_paper/` |
| `research/` | `literature/` (review, matrix, references), `visa_scenario/`, `scenario_reviews/`, `old_design/` |
| `docs/` | `REPO_MAP.md` and the implementation plans |
| `ETHICS.md`, `CLAUDE.md`, `AGENTS.md` | ethics statement; project context and working rules for AI assistants |

Check the experiment files: `python -m pipeline.design.build_runs --example`

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
  `research/literature/literature_matrix.csv`.
- **No real or paid model calls without the team's explicit approval.**
