# Data format

Every input of the experiment is a CSV table (plus two plain-text templates). The
same conventions hold in every table, so each one opens cleanly in Excel or an IDE.

## Conventions

| rule | meaning |
|---|---|
| encoding | UTF-8, comma-separated, LF line endings (a byte-order mark and CRLF from Excel are accepted when reading) |
| header | the first row names the columns; column order does not matter, names do |
| rows | one entity per row (one CV, one job, one model, one run, one prompt part, ...) |
| lists | several values in one cell are separated by `" \| "` (space, pipe, space), e.g. `k1 \| k2 \| k3` |
| booleans | `true` / `false` |
| missing | an empty cell means missing / not applicable |
| placeholders | text that is filled in later uses `{name}`, e.g. `{city}`, `{title}`, `{experience}` |
| JSON | the two cells that pass parameters to a model server hold one JSON object (`models.csv` `extra_body`, `runs.csv` `openai_compatible_extra`) |
| line breaks | allowed inside a quoted cell; used only for the multi-line output instructions in `experiment/prompts/prompt_parts.csv` |

Exceptions: `experiment/stimuli/applicant_cvs.csv` is one row per CV with numbered column groups
(`exp1_*`, `edu1_*`, `cert1_*`, ...) so that a whole CV reads left to right;
`config/country_covariates.csv` is fetched from the World Bank and keeps its
`wb_sub_saharan` indicator as 0/1 (a regressor).

After editing any table, run `python -m hiringaudit validate-stimuli`.

## Where everything is

| file | one row per | reference |
|---|---|---|
| `experiment/stimuli/applicant_cvs.csv` | base CV | `experiment/stimuli/README.md` |
| `experiment/stimuli/applicant_nationalities.csv` | nationality condition | `experiment/stimuli/README.md` |
| `experiment/stimuli/jobs.csv` | occupation (its job ad) | `experiment/stimuli/README.md` |
| `experiment/stimuli/base_countries.csv` | base country (setting of a CV and its job ad) | `experiment/stimuli/README.md` |
| `experiment/stimuli/building_blocks/*.csv` | CV building block (input of the CV builder only) | `experiment/stimuli/README.md` |
| `experiment/prompts/prompt_parts.csv` | piece of fixed prompt text | `experiment/prompts/README.md` |
| `experiment/prompts/prompt_recipes.csv` | step of a message (version x wording) | `experiment/prompts/README.md` |
| `config/runs.csv` | run (mock, pilot, main) with every setting | `config/README.md` |
| `config/models.csv` | model | `config/README.md` |
| `config/leak_terms.csv` | forbidden origin cue | `config/README.md` |
| `config/text_flags.csv` | pattern of an exploratory reason-text flag | `config/README.md` |
| `config/analysis_settings.csv` | confirmatory analysis setting | `config/README.md` |
| `config/country_covariates.csv` | country (H1d covariates) | `config/README.md` |

The two templates are `experiment/stimuli/cv_template.txt` (the CV layout) and the prompt
recipes above (the prompt layout).
