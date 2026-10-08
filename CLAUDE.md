# CLAUDE.md

Project context for IS 617 (LLM4ESS) team project. Read this before doing anything in this repo.

## The project

IS 617 — Large Language Models for the Economic and Social Sciences, University of Mannheim, HWS26.
Course repo: https://github.com/dess-mannheim/LLM4ESS
Team of 3 (Laith Sandouk, Aleksander Kasak, Nico Fedotov). Deliverable: 4–5 page short paper, ACL template, plus three presentations.

**Pivot (2026-09-29).** The team replaced the earlier outcome-bias / trading-records
study with a hiring audit. The old project's files were deleted on 2026-10-01; they
survive only in git history (commit 6ed2adb).

**Redesign and cleanup (2026-10-04).** The team simplified the hiring experiment and
removed everything built for the first hiring design: the pipeline code
(`src/hiringaudit/`), its tests, `scripts/`, the analysis plans (`analysis/`), `config/`,
`results/`, all mock output, `pyproject.toml` and `uv.lock`. All of it is in git history
at commit 670f827. Its documents are in `research/old_design/`.

**Move from hiring to bank customer checks (2026-10-08).** At Laith's request the
hiring and promotion scenario was replaced with the money-laundering check a bank runs
when it takes on a customer. Whether Aleksander and Nico have agreed is not recorded
here. Reason: in hiring a nationality line can be dropped before a model sees
it; in a bank's customer file the nationality is mandatory, AI systems are sold for the
task, and an official list ranks the countries. The reasoning and the sources are in
`research/scenario_reviews/`. The work is on the branch `switching-hr-to-banking`. The
hiring material of 2026-10-04 (prompts, jobs, CVs, country tables, proposal, pitch
slides, Q&A notes) was moved to `research/old_design/hiring_2026-10-04/`; the state
before the move is commit 272792d.

## Repository layout

- `experiment/README.md`: overview of the experiment and the run plan. Start here.
- `experiment/policy/`: the invented bank's risk-assessment policy (`bank_policy.txt`)
  and the paragraph on nationality that the second version adds
  (`nationality_rule.txt`). The README names the public rule behind each section.
- `experiment/customers/`: `customers.csv` (20 customer files) and the file layout.
- `experiment/countries/`: `customer_nationalities.csv` (28 nationality rows with the EU
  high-risk list status) and `country_covariates.csv` (World Bank income and region).
- `experiment/prompts/`: the main prompt and three wordings of the task.
- `experiment/models.csv`: the four planned models.
- `scripts/build_runs.py`: builds and checks the prompts. It never calls a model.
- `data/raw/`, `data/processed/`: empty until the first real run.
- `research/`: literature review, literature matrix, references, novelty assessment,
  literature notes (`lit_parts/`), framing outline. Most of it was written for the
  hiring design; the 13 sources added on 2026-10-08 are the strands `banking_aml` and
  `llm_lending` in the matrix.
- `research/scenario_reviews/`: the four review notes of 2026-10-08 that led to the
  bank scenario.
- `research/old_design/`: documents of the first hiring design, and in
  `hiring_2026-10-04/` everything of the second hiring design. Background and sources
  only; they do not describe the current experiment.
- `paper/`: `proposal/`, `first_presentation/` (pitch), `second_presentation/`
  (midterm), `final_presentation/`, `final_paper/`. Each has a README with the course
  criteria. The two paper folders use the ACL template.
- `ETHICS.md`: ethics statement and handling rules.

## The research question

Working title (proposed by Claude on 2026-10-08 at Laith's request; **the team has not
confirmed it**): *Which Arab? How LLMs Rate Bank Customers from the 22 Arab League
Countries in Money-Laundering Checks.* Earlier titles: *Which Arab? How LLMs Treat
Candidates from the 22 Arab League Countries in Hiring and Promotion* (2026-10-04) and
*Beyond "Arab" as a Single Category*.

> When an LLM rates the money-laundering risk of otherwise identical synthetic bank
> customers, does the rating change when only the stated nationality changes — and does
> a single "Arab" category hide systematic differences among the 22 Arab League
> nationalities?

The proposal of 2026-10-08 (`paper/proposal/proposal.tex`) splits this into five
research questions: (1) differences among the 22 nationalities, against placebo
nationalities; (2) whether they follow the EU list of high-risk countries, on which four
of the 22 appear, or a country's economic and political position; (3) Arab League
nationalities as a group against German, Turkish and placebo nationalities; (4) whether
the differences remain when the policy says that nationality is not a risk factor;
(5) across models.

The main contribution under test is **within-Arab heterogeneity**. "Arab vs others" is a
secondary benchmark only. This is an **audit** of model behaviour, never a tool for
checking customers. All customers, the bank and the employers are synthetic.

No novelty claim exists for this design. `research/novelty_assessment.md` was written
for hiring. For bank customer checks only a few web searches were done on 2026-10-08. Do
not state novelty as fact anywhere.

## Design at a glance

The current design is described in `experiment/README.md` and the READMEs of its
folders. Those are authoritative. `research/old_design/` is not.

- Setting: an invented retail bank in Germany opens a current account for a private
  customer. German law requires the bank to record the nationality and to rate the
  money-laundering risk.
- Customers: 20 synthetic files with different occupations and incomes. All live in
  Germany, are employed there, expect no payments abroad and have clean screening
  results. 10 files are plain, 10 carry one mild indicator the policy names.
- Manipulation: the `Nationality:` line and the matching passport line. No names, no
  place of birth. `customer_nationalities.csv` has 22 Arab League origins, German and
  Turkish benchmarks and 4 placebo nationalities. There is no not-stated row: the field
  is mandatory. Non-German customers hold an unlimited settlement permit; the German
  customer is a citizen, so that file differs in three lines.
- Yardstick: the European Commission's list of high-risk third countries (26 entries,
  as of 29 January 2026). Algeria, Lebanon, Syria and Yemen are on it. By the published
  rules the list is about where a customer lives and where payments go, not about the
  passport.
- Comoros, Djibouti and Somalia are flagged `arab_identity_contested`. The flag does
  not exclude them from any comparison; the paper should point them out.
- Prompts: a main prompt with the bank's policy, then a message with one customer file,
  in three wordings. Two policy versions: without and with a paragraph saying that
  nationality is not a risk factor.
- Outcomes: a 0–100 risk score, a rating (low, medium, high), enhanced checks yes/no and
  a recommendation (open, escalate, decline). Never call the score a probability.
- Run plan: four models, two blocks, 16,800 runs per model with five repetitions.

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
One exception, since 2026-10-04: when asked to put something into the paper, add it as
a visible `\teamnote{...}{...}` in `paper/final_paper/paper.tex` (blue bullet notes with
the facts, marked "not report text"), so the change shows in the PDF. The team rewrites
each note in its own words; notes are hidden with `\shownotesfalse` and must be gone
before submission. Comment-only edits are not enough: the user cannot see them.
`paper/proposal/proposal.tex` (a plan sent to the professor for feedback, not a graded
deliverable) was drafted by Claude at Laith's explicit request, on 2026-10-04 for the
hiring design and again on 2026-10-08 for the bank design; both drafts have to be listed
when AI use is declared. The working title of 2026-10-08 was also proposed by Claude.

**No fabricated results or citations.** Output of mock or test runs is labelled as
such and is never reported as a result. Every citation carries a verification level in
`research/literature_matrix.csv`. Verify against the full text before anything goes
in the paper. Legal texts and guidelines were read in single sections only; the matrix
says which. Company websites and press reports are marked as such.

**Pre-registration discipline.** Do not choose countries, customer files, prompts,
policy text or models after seeing which ones produce the largest disparity.
Confirmatory and exploratory analyses stay separate.

**Novelty and scope discipline.** Do not add experimental factors to chase novelty.
New ideas go to the parked list. The rubric rewards a finished, defensible
experiment: Data [10] + Methods [10] + Results [10] = 30 of 50 report points, and
15 of 25 final-presentation points are Q&A. The scenario has now changed three times;
further changes cost time the midterm needs.

## Parked — publication extension, not the course project

- German-language policy, files and prompts (a German bank's file is in German)
- A name-screening task: is this customer the person on a sanctions list?
- Payments to the home country as a second factor
- A version of the policy without the list of high-risk countries
- Other lists as yardsticks (FATF, Basel AML Index)
- Arabic-centric models (e.g. ALLaM, Jais) as an extra model family
- LLM-judge coding of free-text reasons
- The hiring and promotion design of 2026-10-04, and the loan and visa scenarios
  compared in `research/scenario_reviews/`

## Open decisions

See "Open" in `experiment/README.md`. The largest ones: the design has no written
hypotheses or analysis plan, and no pilot has shown that the answers vary at all. Both
come before the first real run; the pilot needs explicit approval. The pitch slides and
Q&A notes for 13.10. have to be rebuilt for the new topic
(`paper/first_presentation/README.md`).
