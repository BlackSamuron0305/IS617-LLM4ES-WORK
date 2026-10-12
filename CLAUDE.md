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

**Move from bank customer checks to visitor visa applications (2026-10-10).** At Laith's
request the bank scenario was replaced with the pre-assessment of applications for a
visitor visa. Whether Aleksander and Nico have agreed is not recorded here. Reason given
by Laith: the motivation is Islamophobia, and the project should look at Arab countries
in visa applications, in a country that asks all of them for a visa, and put a cost on
the bias. The research behind the design is in `research/visa_scenario/`. The work is on
the branch `Arabs-in-Visa`. The bank material of 2026-10-08 (policy, customers, country
tables, prompts, build script, proposal, Q&A notes) was moved to
`research/old_design/bank_2026-10-08/`; the state before the move is commit 39d32f2.

**What the project is about (Laith, 2026-10-10, said twice in one session).** Bias among
Arabs: do models treat the 22 Arab League nationalities differently from one another
when the application is identical? The yardstick is the **official rules** of the
destination for these countries, which are the same for all 22. It is **not** passport
strength, and the project is **not** a comparison of Arab with non-Arab countries.
Claude's first draft of that day had added both (22 comparison passports matched on the
Henley Passport Index, five non-Arab Muslim-majority passports, a research question on
passport strength); Laith removed them. They are parked in
`research/visa_scenario/parked_comparison_set/`. Do not bring passport strength or
non-Arab comparison groups back into the design, the proposal or the slides unless
asked.

**Applicants moved from Germany to the United Arab Emirates (2026-10-10, later the same
day).** Claude's first draft set all applicants in Germany with a permanent right to
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

## Repository layout

- `experiment/README.md`: overview of the experiment and the run plan. Start here.
- `experiment/policy/`: the guidance the model is given (`visa_guidance.txt`, a
  paraphrase of the public rules for the Australian visitor visa) and the paragraph on
  nationality that the second version adds (`nationality_rule.txt`). The README names
  the public rule behind each section.
- `experiment/applicants/`: `applicants.csv` (20 applicants) and the layout of an
  application.
- `experiment/countries/`: `applicant_nationalities.csv` (26 nationality rows: the 22
  Arab League nationalities and 4 placebo nationalities) and `official_rules.csv` (what
  the official Australian rules say about each of them, plus real grant and refusal
  rates for context). The README explains the yardstick.
- `experiment/prompts/`: the main prompt and three wordings of the task.
- `experiment/costs/`: the cost measures and `cost_assumptions.csv` (prices and rates
  with sources).
- `experiment/models.csv`: the four planned models.
- `scripts/build_runs.py`: builds and checks the prompts. It never calls a model.
- `data/raw/`, `data/processed/`: empty until the first real run.
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

Working title (proposed by Claude on 2026-10-10 at Laith's request; **the team has not
confirmed it**): *Which Arab? How LLMs Rate Visa Applicants from the 22 Arab League
Countries.* Earlier titles: *... Rate Bank Customers ... in Money-Laundering Checks*
(2026-10-08), *... Treat Candidates ... in Hiring and Promotion* (2026-10-04) and
*Beyond "Arab" as a Single Category*.

> When an LLM pre-assesses otherwise identical synthetic applications for a visitor
> visa, does its risk rating change when only the stated nationality changes, does a
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
proposal (`paper/proposal/proposal.tex`): RQ1, do ratings and recommendations differ
across the 22 Arab League nationalities when the application is identical and the
official rules are the same for all of them; RQ2, do the models sort the 22 along three
groups, rich, normal and poor. Two further questions: RQ3, do the differences remain
when the guidance says that nationality is not a ground for a higher rating; RQ4, what
do the differences cost an applicant. Every question is answered for four models.

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
folders. Those are authoritative. `research/old_design/` is not. The design was drafted
by Claude on 2026-10-10 and has not been confirmed by the team.

- Setting: the model is a case assistant that pre-assesses applications for an
  Australian Visitor visa (subclass 600, Tourist stream); a visa officer decides. Real
  systems of this kind sort or rate applicants by fixed rules (United Kingdom until
  2020, Netherlands) or with machine learning (Australia: to "predict risk in visa
  programs"; Canada calls its system "advanced analytics"), not with language models; no
  authority is documented as letting a language model rate visa applications. Checked on
  the original documents on 2026-10-12 (`research/visa_scenario/ai_in_visa_processing.md`,
  addendum). Do not say "Australia rates every applicant with AI": the document names no
  inputs and no rating per application.
- Yardstick: the official rules. For the Australian visitor visa they are the same for
  all 22 Arab League nationalities: same visa, same form, same fee, same legal test, no
  list of risk nationalities in force, no ban (`experiment/countries/official_rules.csv`;
  `scripts/build_runs.py` checks it). Expected result by the rules: no difference. A
  systematic difference among the 22 is what the project calls bias.
- Why Australia: the only destination checked where the rules are the same for all 22.
  The United States bars six of the 22 by proclamation, the Schengen area exempts
  Emirati citizens: there a different answer follows from a rule and is not a bias.
- Applicants: 20 synthetic applications. Everyone was born in the United Arab Emirates,
  has lived there since birth, is employed there and has a clean record. 10
  applications are plain, 10 carry one mild point the guidance names. Savings are on
  five levels (AED 16,000 to 81,000).
- Manipulation: the `Nationality:` line and the `Travel document:` line. No names, no
  gender. `applicant_nationalities.csv` has the 22 Arab League nationalities and 4
  placebo nationalities (Uruguayan, Malawian, Maldivian, Cambodian; the four of the
  earlier designs). The placebo rows are a noise check, not a research question. There
  is no not-stated row.
- Legal status: every application states the same line, "lawful long-term resident with
  the full right to live and work there". All applications differ in two lines only;
  `scripts/build_runs.py` checks it. The six Gulf nationalities are marked in the `note`
  column of the nationality table; a check without them is listed among the comparisons.
- Real grant and refusal rates (Australia 2019-20, United States 2025) are in
  `official_rules.csv` as context and for the slides: they show that the 22 fare very
  differently in practice although the rules are the same. They are not rules and not a
  yardstick, and they come from real applicants in different circumstances.
- The published Australian rules define the home country as the country of usual
  residence and count it in an applicant's favour to live in a low-risk country
  whatever the passport; Emirati citizens are a low-risk group in the Australian
  figures. For applicants born and living in the Emirates with the full right to stay,
  the rules point towards rating the passports alike. A model may still act on what it
  believes about a passport (for example that a foreigner's stay depends on the job).
  The instruction read is the version of 2016.
- Comoros, Djibouti and Somalia are flagged `arab_identity_contested`. The flag does
  not exclude them from any comparison; the paper should point them out.
- Prompts: a main prompt with the guidance, then a message with one application, in
  three wordings. Two versions of the guidance: without and with a paragraph saying that
  nationality is not a ground for a higher rating.
- Outcomes: a 0-100 risk score, a rating (low, medium, high), a list of further checks
  from a menu of six, and a recommendation (grant, refer, refuse). Never call the score
  a probability.
- Cost: three measures (`experiment/costs/README.md`). Main one: the savings an
  applicant would need to make up for a passport. Also fees lost per 1,000 identical
  applicants (AUD 250 per refusal) and the number of further checks. All are
  illustrations of model behaviour, never forecasts.
- Run plan: four models, three blocks, 21,840 runs per model. Block 3 repeats block 1
  with the other savings levels.

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
hiring design, on 2026-10-08 for the bank design and on 2026-10-10 for the visa design;
all three drafts have to be listed when AI use is declared, and so do the two paragraphs
on software that sorts or rates visa applicants, which Claude extended on 2026-10-12.
The working titles were also
proposed by Claude. The pitch slides (`paper/first_presentation/pitch.pptx`, and the
short versions `pitch_v2.pptx` to `pitch_v8.pptx` of 2026-10-12; v5, reordered by the
team by hand, is the one to present, v6 is v5 with Google's post on slide 2, v7 is v6
with the titles of twelve published studies on slide 3 in place of the three figures, and
v8 is v7 with four new slides: one big group against the others, why Arabs, which
scenario, experimental setup)
were built
by Claude at Laith's explicit request, including their wording: the team rewrites the
wording or declares it.

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
15 of 25 final-presentation points are Q&A. The scenario has now changed four times;
further changes cost time the midterm needs.

## Parked — publication extension, not the course project

- A condition that states a religion (the motivation is Islamophobia; the design varies
  a passport)
- A version of the guidance with the sentence from real practice that officers may use
  statistics about other nationals of the applicant's country to look closer
- Arab League passports against non-Arab passports (matched on passport strength, or
  every nationality that needs the Australian visa); material in
  `research/visa_scenario/parked_comparison_set/`
- Comparing the model's order of the 22 with real grant and refusal rates
- The same applications set in a country with a permanent right to stay (the German
  first draft), as a check of how much the setting matters
- A second destination, a work or student visa, an applicant who lives in the country of
  the passport
- Condition 8503 ("no further stay") as a further outcome
- German-language applications and prompts
- Arabic-centric models (e.g. ALLaM, Jais) as an extra model family
- LLM-judge coding of free-text reasons
- The bank design of 2026-10-08 with its own parked ideas (name screening, payments to
  the home country, other lists), the hiring and promotion design of 2026-10-04, and the
  loan scenario compared in `research/scenario_reviews/`

## Open decisions

See "Open" in `experiment/README.md`. The largest ones: the team has not confirmed the
visa design; the design has no written hypotheses or analysis plan; and no pilot has
shown that the answers vary at all or react to savings. Hypotheses, analysis plan and
cost measures come before the first real run; the pilot needs explicit approval. Before
the pitch on 13.10. the team has to go through `paper/first_presentation/pitch.pptx`
and check its numbers (`paper/first_presentation/README.md`). Before any run, check the
Australian legislation register for a travel suspension by nationality
(`experiment/countries/README.md`).
