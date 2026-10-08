# Scenario reviews

Four internal notes written by Claude Code on 2026-10-08 in one working session with
Laith. They record how the project got from hiring to bank customer checks. They are
research notes, not report text. Most of their sources were read through search
summaries; each note has a table that says how far every source was checked. Sources
that went into the proposal were read again directly and are in
`../literature_matrix.csv`.

Read them in this order:

| file | question | answer in one line |
|---|---|---|
| `prompt_realism_review.md` | How close were the hiring prompts to real AI hiring tools? | Close to direct use of a chat model, not to commercial systems, which check fixed criteria on extracted fields |
| `nationality_line_pipeline_review.md` | Would a `Nationality:` line on a CV reach the model in a real pipeline? | Depends on the pipeline. A standard redaction tool removed it in 96% of 12,320 CV versions, but never for "Djiboutian" |
| `scenario_alternatives_review.md` | Which other scenarios keep the nationality in the input? | Visa, asylum, loans and housing compared; includes a design sketch for mortgage files and for Germany |
| `bank_onboarding_scenario.md` | Where is the nationality needed for the task, with an AI pipeline in use? | The money-laundering check at bank onboarding. This became the project |

Things to know when reading them:

- They refer to the hiring files by the paths of that day (`experiment/prompts/`,
  `experiment/jobs/`, `experiment/cvs/`). Those files are now in
  `../old_design/hiring_2026-10-04/`.
- The first note was corrected by the second on one point (whether parsing drops the
  nationality). The correction is marked in the first note.
- `bank_onboarding_scenario.md` says the 2021 version of the EBA guidelines and annex 2
  of the German act had not been read. Both were read later the same day; the result is
  in `experiment/policy/README.md`.
- The redaction test was a test of a tool on the old CVs, not an experiment result. Its
  script was in a temporary folder and is not in the repository.
