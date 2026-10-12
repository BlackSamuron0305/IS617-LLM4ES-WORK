# Experiment

What is in this folder and how the experiment is run. Written on 2026-10-10, when the
project moved from bank customer checks to visitor visa applications. The bank design of
2026-10-08 is in `research/old_design/bank_2026-10-08/`. The research behind this design
is in `research/visa_scenario/`.

**Status.** Drafted by Claude Code with Laith on 2026-10-10. The other team members have
not confirmed it. Nothing has been run.

## The two questions

LLM bias among the Arab countries.

1. **Is there a bias?** Two people hand in the same visa application. One holds a Syrian
   passport, the other an Emirati one. The official rules for the visa are the same for
   both. Does a model rate them differently?
2. **Can the countries be grouped into rich, normal and poor?** If the models do treat
   the 22 differently, do they sort them along these three groups?

## The idea in five sentences

The motivation is Islamophobia. A visa form does not ask for a religion, it asks for a
passport, so the experiment looks at the passports of one group of countries that are
commonly read as Muslim and Arab: the 22 members of the Arab League. The model is given
the guidance of a visa office and one application for an Australian visitor visa, and
returns a risk rating and a recommendation. The application is identical for every
applicant except for the nationality and the passport that goes with it. Australia's
official rules are the same for all 22 nationalities, so a model that rates identical
applications differently has no basis for it in the rules or in the application.

## The yardstick: the official rules

The experiment does not ask how strong a passport is or how a country is seen. It asks
what the official rules of the destination say about the 22 nationalities. For the
Australian visitor visa they say the same for all of them
(`countries/official_rules.csv`, sources in `countries/README.md` and
`policy/README.md`):

| | for each of the 22 |
|---|---|
| visa needed | Visitor visa (subclass 600); no electronic permit, no visa on arrival |
| form and fee | the same online form, AUD 250 |
| legal test | the same: a genuine intention to stay temporarily, enough money, health and character |
| list of risk nationalities | none in force (the last one was revoked in 2009) |
| entry ban or suspension | none, as of 10 October 2026 |

`scripts/build_runs.py` reads that table and stops with a problem if a rule differs
between two nationalities.

By this yardstick the expected result is no difference. A systematic difference among
the 22 is what the project calls bias.

## The three groups: rich, normal, poor

Laith's decision of 2026-10-10. The groups are fixed before any run, from an official
source and not from results: the World Bank's income classification (retrieved on
10 October 2026).

| group | World Bank class | countries |
|---|---|---|
| rich | high income | Bahrain, Kuwait, Oman, Qatar, Saudi Arabia, United Arab Emirates (6) |
| normal | middle income (upper and lower) | Algeria, Comoros, Djibouti, Egypt, Iraq, Jordan, Lebanon, Libya, Mauritania, Morocco, Palestine, Tunisia (12) |
| poor | low income | Somalia, Sudan, Syria, Yemen (4) |

The group of each country is in the column `wealth_group` of
`countries/applicant_nationalities.csv`. `countries/README.md` has the details.

## Why Australia as the destination

It is the only destination that was checked where the official rules are the same for
all 22. Elsewhere the rules themselves sort the nationalities: Emirati citizens need no
visa for the Schengen area, Gulf citizens travel to the United Kingdom, Canada and New
Zealand on an electronic permit, and the United States bars six of the 22 by
proclamation. A different answer for a Syrian and an Emirati applicant would then follow
from a rule and would not be a bias. `countries/README.md` has the check for each
destination.

## Why the United Arab Emirates as the place where the applicants live

Laith's decision: it is the most realistic place for people of all these nationalities
to be born and raised without becoming citizens. Every application states the same
legal status there. `applicants/README.md` has the sources.

## Folders

| folder | content |
|---|---|
| `policy/` | the guidance the model is given, and the paragraph on nationality that is added in the second version |
| `applicants/` | 20 applicants, one row each, and the layout of an application |
| `countries/` | the 26 nationalities an applicant can have, and the official rules for each |
| `prompts/` | the main prompt and the three wordings of the task |
| `costs/` | how a difference in the answers is turned into money, with the prices and their sources |
| `models.csv` | the four planned models: name, exact model id, version to pin, notes |

Each folder has its own README. `scripts/build_runs.py` puts the prompts together and
checks them; it never calls a model.

**Table conventions.** Tables are UTF-8 CSV files with one thing per row. An empty cell
means not applicable. Text that is filled in from a table is written `{{NAME}}`; text
that is filled in for each run is written `{name}`.

## What one run is

One run is one call to one model with two messages:

1. the **main prompt**: who the model is, and the guidance in one of two versions;
2. the **task**: one application and the request for the rating, in one of three
   wordings.

The model is a case assistant that sorts applications before an officer decides. This is
the role documented for real systems: they sort applications into three levels, and a
person decides (`research/visa_scenario/ai_in_visa_processing.md`).

The answer is one JSON object: `risk_score` (0 to 100), `risk_rating` (low, medium,
high), `further_checks` (a list of letters from a fixed menu of six checks, or empty),
`recommendation` (grant, refer, refuse) and a short `reason`.

## What varies

| | values | number |
|---|---|---|
| applicant | 20 applicants with different jobs, incomes and savings; 10 plain applications and 10 with one mild point the guidance names (`applicants/`) | 20 |
| nationality | the 22 Arab League nationalities, and 4 unrelated nationalities as a noise check (`countries/`) | 26 |
| guidance version | without and with a paragraph that says nationality is not a ground for a higher rating (`policy/`) | 2 |
| wording of the task | three phrasings of the same request (`prompts/`) | 3 |
| savings, in block 3 only | the same application with each of the five savings amounts (`applicants/`) | 5 |

Nothing else changes between runs. There is no version without a nationality: a visa
cannot be applied for without a passport.

## Run plan

`python scripts/build_runs.py` prints these counts from the files.

| block | what | prompts | repetitions | runs per model |
|---|---|---|---|---|
| 1 | guidance without the paragraph on nationality | 20 x 26 x 3 = 1,560 | 5 | 7,800 |
| 2 | guidance with the paragraph on nationality | 1,560 | 5 | 7,800 |
| 3 | block 1 again with the four other savings amounts | 20 x 4 x 26 x 3 = 6,240 | 1 | 6,240 |
| | **total** | **9,360** | | **21,840** |

With four models: 87,360 runs. A prompt has about 1,000 to 1,100 words. Block 1 on all
models is enough for the preliminary results of the midterm.

Block 3 is there for the cost figure and as a check of the instrument: it shows how much
the answers move when only the bank balance changes (`costs/README.md`). It is the first
thing to cut if time is short.

Five repetitions per prompt are a proposal. Whether repetitions make sense depends on the
decoding settings, which are not decided (see "Open").

Run in small batches (one model and one block at a time, or smaller), so that a failed
batch can be repeated on its own.

## What will be compared (draft, not an analysis plan)

- **Is there a bias among the 22?** The main question, and it is about the single
  countries (Laith, 2026-10-12): every one of the 22 Arab League nationalities gets its
  own average risk score, rating, number of further checks and recommendation; the 22
  are put in order and compared with one another, and the spread across them is
  reported. The rules say it should be zero.
- **Rich, normal, poor?** A separate question, not the way the countries are compared.
  Two checks. First: do the three groups differ, and is the
  order rich, normal, poor? Second, the other way round: if the 22 are sorted into three
  groups by the models' ratings alone, do these groups match the three wealth groups,
  and which countries land in the "wrong" one? Also whether this holds for each model,
  wording and applicant.
- **Is it more than noise?** Any set of labels moves a model's answers a little. The
  four unrelated nationalities show how much. They are a check, not a research
  question: the project is about the differences among the 22.
- **Does telling the model help?** The same with the paragraph on nationality.
- **What does it cost?** The differences expressed in money (`costs/README.md`).
- Plain applications against applications with one indicator.
- The four models against each other, and the three wordings against each other.
- How often an answer cannot be read or the model refuses, by nationality.

The risk score is a rating given by a model. It is not a probability of anything.

## What a difference means, and what to say with it

- **It is a bias by the yardstick of the rules.** Same application, same rules,
  different answer.
- **It may have a source in the real world, and that does not justify it.** Real offices
  grant and refuse these nationalities at very different rates (Australia granted 96.5%
  of Omani and 21.9% of Somali visitor visa applications in 2019-20). Those figures come
  from real applicants in very different circumstances. A model that carries them over
  to identical applications is doing exactly what the experiment is looking for.
- **One simplification to state.** Every application says the applicant is a lawful
  long-term resident of the Emirates with the full right to live and work there. In
  reality an Emirati is a citizen there and citizens of the other Gulf states need no
  visa. A model may know that. As a check, the comparisons can be repeated without the
  six Gulf nationalities.
- **The rich group is exactly the six Gulf states.** These are the six nationalities
  for which the status line simplifies most. A better rating for the rich group may
  come from wealth or from what a model knows about Gulf citizens in the Emirates; the
  design cannot tell the two apart. The comparison of normal and poor is free of this.
- **The groups are small and uneven**: 6, 12 and 4 countries. Four poor countries, all
  of them at war or just out of one, cannot separate "poor" from "at war".
- **The rules were read in part.** The Australian instruction for officers that was read
  is the version of 2016, and nobody on the team is a lawyer (`policy/README.md`).
- **A passport is not a religion.** The applications state no religion. The experiment
  shows how a model treats Arab League passports. It cannot show that a model reacts to
  Islam as such.

## Open

- **The other team members have not agreed to this design.** The topic has now changed
  four times; the midterm on 11-12.11 needs first results.
- **Hypotheses and an analysis plan.** They have to be written before the first real run,
  not after seeing results. Nothing above is a hypothesis. The cost measures belong in
  the plan too.
- **A pilot** that shows whether the answers vary at all, and whether they react to
  savings and to the indicators. All 20 applicants are ordinary visitors, so a model may
  answer "low" and "grant" for everybody. A pilot is a real model call and needs the
  team's explicit approval.
- **Whether "normal" is the right middle group.** It puts upper and lower middle income
  together (12 countries, from Libya to Mauritania). The alternative is four groups, as
  the World Bank has them. Fix this before the first run.
- **Whether the four unrelated nationalities stay.** They are the four of the earlier
  designs. Without them the experiment is the 22 only, and "more than noise" has to be
  shown from the repetitions alone.
- **Decoding settings and repetitions**: temperature, seeds, and how many repetitions.
- **How the answer format is enforced**: by the instruction only, or by a JSON schema at
  decoding time.
- **Whether the main prompt is sent as the system message.** Gemma has no separate
  system role (`models.csv`).
- **Check the Australian legislation register before the runs** for a new travel
  suspension by nationality (`countries/README.md`). One that names an Arab League
  nationality would be a rule, and the yardstick would no longer be flat.
- Pinning the model versions, and a timing test of a few hundred runs.
- The code that sends the runs and reads the answers does not exist. It must refuse real
  calls unless the team has approved them explicitly.
- No real model calls without the team's explicit approval.
