# Experiment

What is in this folder and how the experiment is run. Rewritten on 2026-11-01, when the
project moved from the Australian visitor visa to a Schengen visa for tourism to Estonia.
The Australian design of 2026-10-10 is in git history (commit af0e409); the bank design
of 2026-10-08 is in `research/old_design/bank_2026-10-08/`.

**Status.** Drafted by Claude Code with Laith on 2026-11-01. The other team members have
not confirmed it. Nothing has been run with a real model.

## The two questions

LLM bias among the Arab countries.

1. **Is there a bias?** Two people hand in the same application for a Schengen visa to
   Estonia. One holds a Syrian passport, the other a Jordanian one. The grounds for
   refusal in the Visa Code are the same for both. Does a model score them differently?
2. **Can the countries be grouped into rich, normal and poor?** If the models do treat the
   countries differently, do they sort them along these three groups?

## The idea

The motivation is Islamophobia. A visa form does not ask for a religion, it asks for a
passport, so the experiment looks at the passports of the 22 members of the Arab League.
The model is a case assistant that pre-assesses applications for a Schengen visa to Estonia
for an officer who decides. It returns **a score from 0 to 100** for how strongly the
application supports granting the visa, and **a reason**. It does not return a decision.

The setting rests on Article 32 of the Visa Code: a visa is refused only on the listed
grounds, and a refusal has to state its reasons. So a model's reason can be held against a
written list: does the reason rest on a ground of Article 32(1), or on the passport?
Laith reports that Estonia is adding AI to public services, including visa decision
support; **that was not confirmed** (`countries/README.md`).

## The yardstick: Article 32 of the Visa Code

The list of grounds does not contain nationality and is the same for every applicant
(`countries/official_rules.csv`, `policy/README.md`). By this yardstick the expected
result is no difference among the nationalities that need the visa. A systematic
difference is what the project calls bias.

**Not flat for two nationalities.** Emirati citizens (and Uruguayans, a placebo) need no
Schengen visa. They stay in the data, report apart, and the main comparison among Arab
nationalities is among **21** (`countries/README.md`). This is the price of Estonia against
Australia.

## Folders

| folder | content |
|---|---|
| `policy/` | the guidance the model is given, the three versions of section 6 on nationality, and the regulation-based variants |
| `applicants/` | 20 simulated applicants: the full record, the filter that removes name, age, sex and more, and what the model sees |
| `countries/` | the 26 nationalities an applicant can have, and the official rules for each |
| `prompts/` | the main prompt, three wordings of the task, and `variants.csv` with the twelve variants |
| `costs/` | how a difference in the scores is turned into money |
| `models.csv` | the four planned models |
| `judge/` | the judge that codes the free-text reason of each answer |
| `run_settings.csv` | the sampling settings for the audited models and the judge; each marked provisional or open |

The code is in `pipeline/` (`pipeline/README.md`). `pipeline/build_runs.py` puts the
prompts together and checks them; it never calls a model.

**Table conventions.** Tables are UTF-8 CSV files with one thing per row. An empty cell
means not applicable. Text that is filled in from a table is written `{{NAME}}`; text
that is filled in for each run is written `{name}`.

## What one run is

One call to one model with two messages: the **main prompt** (the role and the guidance),
and the **task** (one application and the request for the score). The answer is one JSON
object: `visa_score` (0 = refuse, 100 = clearly grant) and `reason`.

The application has the five items of the Estonian checklist: purpose of the journey,
travel medical insurance, round-trip flight, accommodation, means of subsistence
(`applicants/README.md`).

### The filter: what the model does not see

The 20 applicants were simulated as complete records, with name, sex, date of birth,
address, phone, e-mail and passport number. A documented filter (`applicants/field_filter.csv`)
removes all of these before a prompt is built, so that the passport is the only thing
that differs between runs, and `build_runs` checks that no removed value reaches a prompt.
The report has to describe this. Residual signals (family line, employment length, travel
history) remain and are stated in `applicants/README.md`.

## What varies

| | values | number |
|---|---|---|
| applicant | 20 applicants with different jobs, incomes and savings; 10 plain and 10 with one mild point (`applicants/`) | 20 |
| nationality | the 22 Arab League nationalities, and 4 unrelated ones as a noise check (`countries/`); 2 of the 26 need no visa | 26 |
| guidance version (blocks 1, 2) | without and with the paragraph that says nationality is not a ground for a lower score | 2 |
| wording of the task | three structures of the same request | 3 |
| savings (block 3) | the same application with each of five amounts | 5 |
| variant (block 4) | twelve changes of one thing each, among them the Article 32 text itself and an instruction to cite it | 12 |

## Run plan

`python -m pipeline.build_runs --variants` prints these counts from the files.

| block | what | prompts | repetitions | runs per model |
|---|---|---|---|---|
| 1 | guidance without the paragraph on nationality | 20 x 26 x 3 = 1,560 | 5 | 7,800 |
| 2 | guidance with the paragraph on nationality | 1,560 | 5 | 7,800 |
| 3 | block 1 again with the four other savings amounts | 6,240 | 1 | 6,240 |
| 4 | twelve variants, one repetition each | 12 x 1,560 = 18,720 | 1 | 18,720 |
| | **base design (blocks 1 to 3)** | **9,360** | | **21,840** |
| | **with all variants** | **28,080** | | **40,560** |

With four models: 87,360 runs for the base design and 162,240 with all variants. A prompt
has 550 to 1,400 words. Block 1 on all models is enough for the midterm; block 3 and the
variants are the first things to cut if time is short. Run in small batches (one model and
one block or variant at a time).

## What will be compared (draft, not an analysis plan)

- **Is there a bias among the 21?** Every one of the 21 Arab League nationalities that need
  the visa gets its own average score, and the 21 are put in order and compared with
  one another (Laith, 2026-10-12: the single countries, not groups). The rules say the
  spread should be zero. The Emirati row is read apart.
- **Rich, normal, poor?** A separate question: do the three groups differ, and is the
  order rich, normal, poor? Also the other way round: if the countries are sorted by the
  models' scores alone, do the groups match the three wealth groups?
- **Is it more than noise?** The placebo nationalities show how much any label moves the
  scores.
- **Does telling the model help?** Block 2, and the variants `regulation_rule` and
  `info_rule`. **Does the regulation itself help?** The variants `regulation_text`
  and `regulation_instruction`, against the paraphrase.
- **Does the model react to a real ground?** The lowest savings level is below the
  EUR 70 per day the rules ask for. A model that does not lower the score there does not
  use the rules. This is the check that the instrument works.
- **What do the reasons say?** The judge codes each reason: does it bring up the passport
  or the passport country, doubt the right to stay in the Emirates, contradict the
  application, and does it name a ground of Article 32? Exploratory, and only for codes
  that agree with the team's own coding of a sample (`judge/README.md`).
- **What does it cost?** `costs/README.md`.
- Plain applications against applications with one indicator; the four models against each
  other; the three wordings against each other; how often an answer cannot be read.

The score is a number given by a model. It is not a probability of anything.

## What a difference means, and what to say with it

- **It is a bias by the yardstick of the rules.** Same application, same list of grounds,
  different score. It is described as the weight the model gives the passport, not as
  proven prejudice: a model may know more about a passport than the application says.
- **It may have a source in the real world, and that does not justify it.** Real consulates
  refuse nationalities at different rates. A model that carries them over to identical
  applications is doing exactly what the experiment is looking for.
- **The Emirati row is a simplification.** An Emirati would be a citizen and needs no
  visa. The application treats the Emirati like everybody else, as for every nationality.
- **The rich group is exactly the six Gulf states**, which the application treats like
  everyone. A better score for the rich group may come from wealth or from what a model
  knows about Gulf citizens; the design cannot tell them apart.
- **The groups are small and uneven**: 6, 12 and 4 countries; the four poor countries
  are all at war or just out of one.
- **The rules were read in part.** Articles 14, 15 and 21 of the Visa Code were not read
  in full text, and the checklists of the Estonian mission could not be downloaded.
  Nobody on the team is a lawyer.
- **A passport is not a religion.** The applications state no religion. The experiment
  shows how a model treats Arab League passports. It cannot show that a model reacts to
  Islam as such.

## Open

- **The other team members have not agreed to this design.** The topic has now changed
  five times; the midterm on 11-12.11 needs first results.
- **Hypotheses and an analysis plan** have to be written before the first real run. The
  cost measures belong in the plan too.
- **A pilot** that shows whether the scores vary at all, react to savings and to the
  indicators. A pilot is a real model call and needs the team's explicit approval.
- **Whether the score direction stays "should the visa be granted"**, and whether a
  refusal line (below 20) and a doubt line (below 50) are the right cut-offs for the costs.
- **Whether the Emirati and Uruguayan rows stay**, given that they need no visa.
- **Whether "normal" is the right middle group** (12 countries).
- **Check before the runs:** Articles 22 and 25a (prior consultation, visa measures) for
  the 21 nationalities, the Estonian amount of means per day (EUR 70 per the ministry),
  the exchange rate of AED 4.2 per euro, and the checklist of the Estonian mission in the
  United Arab Emirates.
- **Whether Estonia is using AI in visa decisions**: the claim needs a source before it
  is in any text.
- **Decoding settings and repetitions**; how the answer format is enforced; whether the
  main prompt is the system message; the pinned versions of the models.
- **The judge.** The team has to confirm the agreement threshold (Cohen's kappa of 0.7 is
  provisional), the size of the validation sample, and the judge model
  (`judge/judge_models.csv` lists two). The sample has to be coded by hand first.
- No real model calls without the team's explicit approval. The runner refuses them until
  the model revisions are pinned (`pipeline/README.md`).
