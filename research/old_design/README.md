# Old designs

Nothing in this folder describes the current experiment; that is in
`experiment/README.md`. The folder holds two earlier designs, both about hiring. They
are kept for the reasoning and the sources behind choices that still hold, for example
why the files carry no names (`design_decisions.md`, D03) and why there are placebo
nationalities.

## The first hiring design (replaced on 2026-10-04)

The files directly in this folder. 6 jobs with 48 CVs, 8 fixed countries, cities, school
and company names, 11 comparison nationalities, a principle probe. The code, settings and
analysis plans these documents refer to were removed (git history, commit 670f827).

| file | what it was |
|---|---|
| `preregistration.md` | draft preregistration, never frozen |
| `experimental_design.md` | the full design |
| `design_decisions.md` | each design decision with its sources |
| `hypotheses.md` | research questions and hypotheses |
| `variables.md` | every variable |
| `threats_to_validity.md` | what could go wrong, and the answers |
| `design_contract.md` | the specification the removed code was built against |
| `status_report.md` | status as of 2026-10-01 |

## The second hiring design (replaced on 2026-10-08)

In `hiring_2026-10-04/`. 20 jobs with one CV each, every job in all 22 Arab League
countries, a `Nationality:` line with 29 conditions, a main prompt plus a follow-up
message, a lottery option, a promotion scenario. It was never run. It was replaced by
the bank customer check because a nationality line on a CV can be removed before a model
sees it (`research/scenario_reviews/`).

| path | what it was |
|---|---|
| `hiring_2026-10-04/experiment_README.md` | overview and run plan (128,480 runs per model) |
| `hiring_2026-10-04/prompts/` | main prompts and follow-up messages, hiring and promotion, with and without the ignore-nationality paragraph |
| `hiring_2026-10-04/jobs/` | 20 job ads and the template |
| `hiring_2026-10-04/cvs/` | 20 CVs and the template |
| `hiring_2026-10-04/countries/` | the 22 countries a job was set in, and the nationality table with a not-stated row |
| `hiring_2026-10-04/proposal/` | the proposal of 2026-10-04, source and PDF |
| `hiring_2026-10-04/first_presentation/` | the pitch slides and Q&A notes made for this design |

The 20 occupations of the jobs live on as the occupations of the 20 customers in
`experiment/customers/customers.csv`. The paths inside these files (for example
`experiment/prompts/`) are the paths of that time.
