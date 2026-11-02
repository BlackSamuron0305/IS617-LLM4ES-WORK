# AGENTS.md

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
`research/scenario_reviews/`. The hiring material of 2026-10-04 (prompts, jobs, CVs, country tables, proposal, pitch
slides, Q&A notes) was moved to `research/old_design/hiring_2026-10-04/`; the state
before the move is commit 272792d.

**Move from bank customer checks to visitor visa applications (2026-10-10).** At Laith's
request the bank scenario was replaced with the pre-assessment of applications for a
visitor visa. Whether Aleksander and Nico have agreed is not recorded here. Reason given
by Laith: the motivation is Islamophobia, and the project should look at Arab countries
in visa applications, in a country that asks all of them for a visa, and put a cost on
the bias. The research behind the design is in `research/visa_scenario/`. The bank
material of 2026-10-08 (policy, customers, country tables, prompts, build script,
proposal, Q&A notes) was moved to `research/old_design/bank_2026-10-08/`; the state
before the move is commit 39d32f2.

**Single branch (2026-10-23).** At Laith's request the branch `Arabs-in-Visa` was merged
into `main` and every other branch was deleted, locally and on GitHub
(`switching-hr-to-banking`, `research-realistic-hr-process`). Nothing was lost: all
their commits were already in `Arabs-in-Visa`. Work happens on `main`.

**What the project is about (Laith, 2026-10-10, said twice in one session).** Bias among
Arabs: do models treat the 22 Arab League nationalities differently from one another
when the application is identical? The yardstick is the **official rules** of the
destination for these countries, which are the same for all 22 under the Australian design and for the 21 that need a visa under the Estonian one. It is **not** passport
strength, and the project is **not** a comparison of Arab with non-Arab countries.
Codex's first draft of that day had added both (22 comparison passports matched on the
Henley Passport Index, five non-Arab Muslim-majority passports, a research question on
passport strength); Laith removed them. They are parked in
`research/visa_scenario/parked_comparison_set/`. Do not bring passport strength or
non-Arab comparison groups back into the design, the proposal or the slides unless
asked.

**Applicants moved from Germany to the United Arab Emirates (2026-10-10, later the same
day).** Codex's first draft set all applicants in Germany with a permanent right to
stay. Laith decided that they are born, raised and working in the United Arab Emirates:
the most realistic place to grow up with one of these passports without becoming a
citizen. Laith also decided that every application states the same legal status ("lawful
long-term resident with the full right to live and work there") and that there is no
special case for the Gulf nationalities, although an Emirati is in reality a citizen and
Gulf citizens need no visa there. Do not move the setting back and do not reintroduce a
separate status for some nationalities without being asked. What the documents keep
saying, and what must not be dropped: a model may know more about a passport than the
application states, so a difference is described as the weight the model gives the
passport, not as proven prejudice.

**Move from the Australian visitor visa to a Schengen visa for Estonia (2026-11-01).** At
Laith's request. Reason given by Laith: EU law demands a valid reason for a visa refusal
(Article 32 of the Visa Code, supplied as a screenshot), and Estonia is said to be adding AI
to public services including visa decision support (**not confirmed**: a search on
2026-11-01 found nothing about visas; see `research/visa_scenario/estonia_scenario.md`; do not
state it as fact). Changes decided that day: the model gives **only a score from 0 to 100
(0 = refuse, 100 = clearly grant) and a reason**, no rating, no further checks and no
recommendation; the reason is coded by the judge; the application has five items (purpose,
travel medical insurance, return flight, accommodation, means of subsistence); a realistic
full record (name, sex, age, address ...) is simulated and then removed by a documented
filter before any model sees it; and some prompts carry the regulation directly (the text of
Article 32(1), and an instruction to cite its grounds). Whether Aleksander and Nico have
agreed is not recorded here. Consequence that Claude flagged: Emirati citizens (and the
placebo Uruguayans) need no Schengen visa, so the rules are flat for 21 of the 22 Arab
League nationalities, not for all; the two rows stay in the data and are reported apart.
The Australian design is in git history (commit af0e409, with its real grant and refusal
rates by nationality). Nico's prompt revisions and variants (merged on 2026-10-2x) were
carried over to the new scenario as `experiment/prompts/variants.csv`.

**Runs on bwUniCluster (2026-11-02, at Laith's instruction to run to completion).** Pilots 1 and 2
(Qwen3 32B), then the main run: Qwen3 32B, Gemma 4 31B and Mistral Small 3.2 24B, blocks 1 to 3 (32,760 answers each),
twelve prompt variants (28,080 each), a boundary set of ten more applicants (blocks 5 and 6, 7,800 each; deviation D4) and
the judge OLMo 3.1 32B on block 1, three variants and block 5. Everything is in `experiment/deviations.md` (D1 to D4:
required-funds line and ten two-point applicants after pilot 1; go-ahead after pilot 2 missed two checks narrowly; clearer
judge code; boundary set), the tables in `results/main/`, the figures and the midterm deck in `paper/second_presentation/`.
Findings (confirmatory tests of `experiment/analysis_plan.md`): the 21 Arab nationalities that need a visa differ by 1.6 to 3.4
score points between highest and lowest (permutation p = 0.0002 in all three models, far below the 5 points the plan calls
worth noting); Syria, Yemen, Sudan, Iraq, Libya and Somalia are lowest in all models; the order rich > normal > poor holds
(Spearman -0.72, -0.52, -0.76); the paragraph "nationality is not a ground" does not shrink the gaps; no prompt variant
removes them for Qwen and Gemma; the reasons name the passport in about 0% of cases (the judge is not validated yet). The
instrument is limited: scores sit near the ceiling, and Mistral ignores the money rule. The slides' wording was drafted by Claude
at Laith's explicit request (declare AI use); the final report was prepared only as visible `\teamnote` blocks in
`paper/final_paper/paper.tex` (results, limits, AI declaration). Also done: the check without the Gulf states (spread unchanged; wealth order holds for Gemma and Qwen, weaker for Mistral), the cost measures
(`pipeline/costs.py`: a Syrian passport weighs about AED 290 of savings for Gemma, undefined for the other two; fees lost about nothing), and a
validation sample of 200 reasons for the team to code by hand (`experiment/judge/validation/`). Not done: that hand coding, the pre-run checks of
Articles 21, 22 and 25a. Raw answers are backed up on this PC in `data/raw/` (305 MB, not committed).

## Repository layout

- `experiment/README.md`: overview of the experiment and the run plan. Start here.
- `experiment/policy/`: the guidance the model is given (`visa_guidance.txt`, a paraphrase
  of Article 32(1) of the Visa Code and of the Estonian ministry's page on the Schengen
  visa), its variants (`visa_guidance_risk.txt`, `regulation_text.txt`,
  `regulation_instruction.txt`) and three versions of section 6 on nationality
  (`nationality_rule.txt`, `regulation_rule.txt`, `info_rule.txt`).
- `experiment/applicants/`: `applicants_full.csv` (20 complete simulated records),
  `field_filter.csv` (which fields the model never sees, and why), `applicants.csv` (the
  filtered result, written by `python -m pipeline.filter_applicants`) and the layout of an
  application.
- `experiment/countries/`: `applicant_nationalities.csv` (26 nationality rows: the 22 Arab
  League nationalities and 4 placebo nationalities; column `visa_required`) and
  `official_rules.csv` (what the rules for a Schengen visa to Estonia say about each). The
  README explains the yardstick.
- `experiment/prompts/`: the main prompt, three wordings of the task, and `variants.csv`
  with twelve variants (folders per variant).
- `experiment/costs/`: the cost measures and `cost_assumptions.csv` (prices and rates with
  sources).
- `experiment/models.csv`: the three planned models (qwen3-32b, gemma-4-31b-it, mistral-small-3.2-24b-instruct).
- `experiment/analysis_plan.md` (hypotheses, tests, pilot go / no-go), `experiment/design_review.md` (the referee's view) and `cluster/PILOT.md` (how to run the pilot).
- `experiment/judge/`: the judge that codes the free-text reason of each answer (prompt
  files, `mask_terms.csv`, `judge_models.csv`). Its README is authoritative.
- `experiment/run_settings.csv`: the sampling settings; all provisional or open.
- `pipeline/`: the code, one module per stage: `filter_applicants`, `build_runs` (builds and checks the
  prompts, never calls a model), `run_models`, `parse_answers`, `judge_build`,
  `run_judge`, `judge_parse`, `judge_validate`. `pipeline/README.md` has the commands, a
  mock walk-through and the refusal rules.
- `cluster/`: `run_vllm.sbatch`, the Slurm script that starts vLLM on bwUniCluster and
  runs one stage (untested), and its README.
- `tests/`: the unit tests (`python -m unittest discover -s tests -t . -v`). They use a
  mock model or a local stub server and never call a real one.
- `docs/superpowers/plans/`: the implementation plan of the pipeline and the judge.
- `data/raw/`, `data/processed/`: empty until the first real run; one folder per batch
  (`data/README.md`).
- `research/`: literature review, literature matrix, references, novelty assessment,
  literature notes (`lit_parts/`), framing outline. Most of it was written for the
  hiring design; the 13 sources added on 2026-10-08 are the strands `banking_aml` and
  `llm_lending`, the 87 added on 2026-10-10 are the strands `islamophobia_context`,
  `visa_evidence`, `cost_method`, `visa_ai_systems` and `visa_rules_data`.
- `research/visa_scenario/`: the three research notes of 2026-10-10 behind the visa
  design.
- `research/scenario_reviews/`: the four review notes of 2026-10-08 that led to the
  bank scenario.
- `research/old_design/`: documents of the first hiring design, in
  `hiring_2026-10-04/` everything of the second hiring design, and in
  `bank_2026-10-08/` everything of the bank design. Background and sources only; they do
  not describe the current experiment.
- `paper/`: `proposal/`, `first_presentation/` (pitch, with `pitch.pptx`),
  `second_presentation/` (midterm), `final_presentation/`, `final_paper/`. Each has a
  README with the course criteria. The two paper folders use the ACL template.
- `ETHICS.md`: ethics statement and handling rules.

## The research question

Working title (proposed by Codex on 2026-10-10 at Laith's request; **the team has not
confirmed it**): *Which Arab? How LLMs Rate Visa Applicants from the 22 Arab League
Countries.* Earlier titles: *... Rate Bank Customers ... in Money-Laundering Checks*
(2026-10-08), *... Treat Candidates ... in Hiring and Promotion* (2026-10-04) and
*Beyond "Arab" as a Single Category*.

> When an LLM pre-assesses otherwise identical synthetic applications for a visitor
> visa, does its visa score (since 2026-11-01 a score from 0 to 100 and a reason) change when only the stated nationality changes, does a
> single "Arab" category hide systematic differences among the 22 Arab League
> nationalities, and what would the difference cost an applicant?

**The motivation is Islamophobia** (Laith, 2026-10-10: keep it as the main motivation).
The line of argument: a visa form asks for no religion, it asks for a passport; all
Muslim-majority countries together are too mixed a group; the 22 Arab League countries
are a subset with less noise (one language, one label) that still differ widely. Arab is
not Muslim and a passport is not a religion: the experiment measures how passports are
treated and must not be described as measuring bias against Islam.

The two questions (Laith, 2026-10-10): **(1) is there an LLM bias among the Arab
countries, and (2) can the countries be grouped into rich, normal and poor?** Laith on
2026-10-12: question 1 compares the single countries, each of the 22 with the others;
the three groups are a different research question and not the way the countries are
compared. Slides and documents must not present the project as a comparison of groups. In the
proposal (`paper/proposal/proposal.tex`): RQ1, do ratings and recommendations (now: scores) differ
across the 22 Arab League nationalities when the application is identical and the
official rules are the same for all of them; RQ2, do the models sort the 22 along three
groups, rich, normal and poor. Two further questions: RQ3, do the differences remain
when the guidance says that nationality is not a ground for a higher rating; RQ4, what
do the differences cost an applicant. Every question is answered for three models.

The three groups are fixed before any run from the World Bank income classification
(retrieved 10 October 2026): rich = high income (Bahrain, Kuwait, Oman, Qatar, Saudi
Arabia, United Arab Emirates); normal = upper and lower middle income (Algeria, Comoros,
Djibouti, Egypt, Iraq, Jordan, Lebanon, Libya, Mauritania, Morocco, Palestine, Tunisia);
poor = low income (Somalia, Sudan, Syria, Yemen). Column `wealth_group` in
`experiment/countries/applicant_nationalities.csv`. Do not move a country to another
group after seeing results. Known limits to state: the rich group is exactly the six
Gulf states, and the four poor countries are all at war or just out of one.

The main contribution under test is **within-Arab heterogeneity**. This is an **audit**
of model behaviour, never a tool for assessing applicants. All applicants and employers
are synthetic.

No novelty claim exists for this design. `research/novelty_assessment.md` was written
for hiring. For visa applications only limited searches were done on 2026-10-10
(`research/visa_scenario/`). Do not state novelty as fact anywhere.

## Design at a glance

The current design is described in `experiment/README.md` and the READMEs of its
folders. Those are authoritative. `research/old_design/` and the Australian files in git
history (commit af0e409) are not. The design was drafted by Claude on 2026-11-01 and has
not been confirmed by the team.

- Setting: the model is a case assistant that pre-assesses applications for a Schengen
  visa (type C, short stay, tourism) to Estonia; a visa officer decides. Real systems of
  this kind sort applications by fixed rules or machine learning, not with language
  models; no authority is documented as letting a language model rate visa applications
  (`research/visa_scenario/ai_in_visa_processing.md`). Do not say "Estonia uses AI for
  visa decisions" until a source is found.
- Yardstick: Article 32(1) of the Visa Code. Its list of grounds for refusal names no
  nationality and is the same for every applicant. Expected result by the rules: no
  difference among nationalities that need the visa. A systematic difference is what the
  project calls bias. Not checked: Article 22 (prior consultation) and Article 25a (visa
  measures) for the 21 nationalities.
- Emirati (and Uruguayan, a placebo) citizens need no visa (Annex II of Regulation
  2018/1806, not read again). They stay in the data and are reported apart; the main
  comparison among the Arab nationalities is among **21**.
- Applicants: 30 synthetic applications. Everyone was born in the United Arab Emirates,
  has lived there since birth, is employed there, applies there, and has a clean record.
  10 applications are plain, 10 carry one mild point, 10 carry two (added on 2026-11-02, see `../deviations.md`). Savings are on five levels (AED
  2,000 to 10,500): the lowest is below the EUR 70 per day that Estonia counts, so a
  model has one level where a lower score follows from the rules.
- The application has five items: purpose of the journey, travel medical insurance,
  return flight, accommodation, means of subsistence.
- **The filter.** The simulated records contain name, sex, date of birth, place of birth,
  address, phone, e-mail and passport number. `experiment/applicants/field_filter.csv`
  removes them before any prompt is built; `pipeline/build_runs.py` checks that no removed
  value reaches a prompt. The paper must document this filter (Laith, 2026-11-01).
  Residual age and sex signals are listed in `experiment/applicants/README.md`.
- Manipulation: the `Nationality:` line and the `Travel document:` line. The 22 Arab League
  nationalities and 4 placebo nationalities (Uruguayan, Malawian, Maldivian, Cambodian).
  No not-stated row.
- Legal status: every application states the same line, "lawful long-term resident with
  the full right to live and work there". All applications differ in two lines only; the
  builder checks it.
- Prompts: a main prompt with the guidance, then a message with one application, in three
  wordings. Block 2 adds the instruction that nationality is not a ground. Twelve
  variants (`experiment/prompts/variants.csv`) change one thing each, among them
  `regulation_text` (the word-for-word Article 32(1) as the guidance), `regulation_instruction`
  (an order to cite the ground), `no_guidance`, `reasoning`, `risk_scale`, `decider`,
  the two time framings and the two personas.
- Outcome: `visa_score` 0-100 (0 = the visa should be refused, 100 = clearly granted) and
  a `reason` naming the ground. Never call the score a probability. The direction of the
  scale is an open decision (variant `risk_scale` turns it round).
- Cost: three measures (`experiment/costs/README.md`): the savings an applicant would need
  to make up for a passport (main); fees lost per 1,000 identical applications (EUR 90 per
  refusal, a refusal line below 20 and a doubt line below 50); the share of scores that
  send an application to a closer look (20 to 49). All are illustrations of model
  behaviour, never forecasts.
- Run plan: three models; blocks 5 and 6 (boundary applicants) add 7,800 runs per model; blocks 1 to 3 are 32,760 runs per model (block 3 repeats block 1
  with the other savings levels); block 4 is 28,080 runs per model for the twelve
  variants.
- Judge (drafted by Claude on 2026-10-24, extended on 2026-11-01 with the code
  `names_legal_ground`, **not confirmed by the team**): a second model codes the free-text
  `reason` of each answer, and only that field, with six yes/no codes (mentions
  nationality, treats it as a risk, refers to conditions in the passport country, doubts
  the right to stay in the Emirates, contradicts the application, names a ground of Article
  32 or one of the five items). It is blinded: it sees the reason and the application with
  the nationality words and lines hidden, never the score. The codes describe how a model
  justifies its score, not why it gave it; they are exploratory, and a code is used only
  if it agrees with the team's own coding of a sample by hand. `experiment/judge/README.md`
  is authoritative.

## Compute and models

Open-weight models (`experiment/models.csv`) served with vLLM on bwUniCluster (KIT).
There is no API budget. **Never launch real or paid model calls without explicit
approval.** The runner in `pipeline/` refuses real calls unless `--allow-real-calls` is
given and the other conditions hold (a batch name that does not start with `mock`, a
pinned model revision, no uncommitted change in `experiment/` or `pipeline/`, and the
model listed by the server); any other runner must do the same. The revisions in
`experiment/models.csv` and `experiment/judge/judge_models.csv` are empty, so every real
call is refused until they are pinned. `cluster/run_vllm.sbatch` is the only place that
passes `--allow-real-calls`, and only with `ALLOW_REAL_CALLS=yes`; it has not been run on
the cluster.

## Deadlines

| Date | Milestone |
|---|---|
| 13.10.2026 | Pitch — 5 min + 5 min Q&A |
| 11–12.11.2026 | Midterm — requires preliminary results |
| 09–10.12.2026 | Final — 12 min + 15 min Q&A (15 of 25 points are Q&A) |
| 08.01.2027 | Report due |

## Working rules

**AI usage policy.** The chair has had cases that nearly failed students over
LLM-written text, and the report requires a per-task declaration of AI use. Codex
does design, code, analysis and internal research documents. Codex does **not**
write report or presentation prose. Never paste generated text into `paper/`.
One exception, since 2026-10-04: when asked to put something into the paper, add it as
a visible `\teamnote{...}{...}` in `paper/final_paper/paper.tex` (blue bullet notes with
the facts, marked "not report text"), so the change shows in the PDF. The team rewrites
each note in its own words; notes are hidden with `\shownotesfalse` and must be gone
before submission. Comment-only edits are not enough: the user cannot see them.
`paper/proposal/proposal.tex` (a plan sent to the professor for feedback, not a graded
deliverable) was drafted by Codex at Laith's explicit request, on 2026-10-04 for the
hiring design, on 2026-10-08 for the bank design and on 2026-10-10 for the visa design;
all three drafts have to be listed when AI use is declared, and so do the two paragraphs
on software that sorts or rates visa applicants, which Codex extended on 2026-10-12.
The working titles were also
proposed by Codex. The pitch slides (`paper/first_presentation/pitch.pptx`, and the
short versions `pitch_v2.pptx` to `pitch_v8.pptx` of 2026-10-12; v5, reordered by the
team by hand, is the one to present, v6 is v5 with Google's post on slide 2, v7 is v6
with the titles of twelve published studies on slide 3 in place of the three figures, and
v8 is v7 with four new slides: one big group against the others, why Arabs, which
scenario, experimental setup)
were built
by Codex at Laith's explicit request, including their wording: the team rewrites the
wording or declares it. The judge prompt, the codebook and `mask_terms.csv` in
`experiment/judge/` were drafted by Codex on 2026-10-24 at Laith's request and have to
be listed when AI use is declared.

**No fabricated results or citations.** Output of mock or test runs is labelled as
such and is never reported as a result. Every citation carries a verification level in
`research/literature_matrix.csv`. Verify against the full text before anything goes
in the paper. Legal texts and guidelines were read in single sections only; the matrix
says which. Company websites and press reports are marked as such. For the sources added
on 2026-10-10, `abstract` in the matrix also covers pages read only through a
summarising fetch tool; the notes in `research/visa_scenario/` say which. Numbers marked
"own calculation" there are not published figures.

**Pre-registration discipline.** Do not choose countries, applications, prompts,
guidance text, cost measures or models after seeing which ones produce the largest
disparity.
Confirmatory and exploratory analyses stay separate.

**Novelty and scope discipline.** Do not add experimental factors to chase novelty.
New ideas go to the parked list. The rubric rewards a finished, defensible
experiment: Data [10] + Methods [10] + Results [10] = 30 of 50 report points, and
15 of 25 final-presentation points are Q&A. The scenario has now changed five times;
further changes cost time the midterm needs.

## Parked — publication extension, not the course project

- A condition that states a religion (the motivation is Islamophobia; the design varies
  a passport)
- A version of the guidance with the sentence from real practice that officers may use
  statistics about other nationals of the applicant's country to look closer
- Arab League passports against non-Arab passports (matched on passport strength, or
  every nationality that needs the Schengen visa); material in
  `research/visa_scenario/parked_comparison_set/`
- Comparing the model's order of the 22 with real grant and refusal rates
- The same applications set in a country with a permanent right to stay (the German
  first draft), as a check of how much the setting matters
- A second destination, a work or student visa, an applicant who lives in the country of
  the passport
- Condition 8503 ("no further stay") as a further outcome
- German-language applications and prompts
- Arabic-centric models (e.g. ALLaM, Jais) as an extra model family
- The bank design of 2026-10-08 with its own parked ideas (name screening, payments to
  the home country, other lists), the hiring and promotion design of 2026-10-04, and the
  loan scenario compared in `research/scenario_reviews/`

## Open decisions

See "Open" in `experiment/README.md`. The largest ones: the team has not confirmed the
Estonia design; the design has no written hypotheses or analysis plan; and no pilot has
shown that the answers vary at all or react to savings. Hypotheses, analysis plan and
cost measures come before the first real run; the pilot needs explicit approval. Before
the pitch on 13.10. the team has to go through `paper/first_presentation/pitch.pptx`
and check its numbers (`paper/first_presentation/README.md`). Before any run, check Articles 22 and 25a of the Visa Code for the 21 nationalities, the Estonian
amount for means (EUR 70 per day), and the checklist of the Estonian mission in the United Arab Emirates
(`experiment/countries/README.md`). For the judge: the team has to confirm the agreement
threshold (Cohen's kappa of 0.7 is provisional) and the size of the validation sample,
and decide whether the optional second judge stays (`experiment/judge/judge_models.csv`; the main judge is OLMo 3.1 32B). The
validation sample has to be coded by hand before any judge code is used.
