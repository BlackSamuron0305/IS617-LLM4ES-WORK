# Prompts

Written on 2026-10-10. Each file is a message with placeholders. The prompts of the bank
design are in `research/old_design/bank_2026-10-08/prompts/`.

Every run has two messages: the **main prompt** (who the model is, and the guidance),
then the **task** (one application and the request for the rating).

| file | what it is |
|---|---|
| `main_prompt.txt` | the main prompt. `{policy}` is filled with one of the two versions of the guidance |
| `task_wording_1.txt`, `task_wording_2.txt`, `task_wording_3.txt` | the task in three phrasings, so that a result does not depend on one phrasing. `{application}` is filled with one application |

## Placeholders

| placeholder | filled with | comes from |
|---|---|---|
| `{policy}` | the guidance without or with the paragraph on nationality | `experiment/policy/` |
| `{application}` | one applicant with one nationality | `experiment/applicants/`, `experiment/countries/applicant_nationalities.csv` |

The nationality enters only through the application: the lines `Nationality:` and
`Travel document:`.

## The answer

All three wordings ask for the same JSON object:

| key | values |
|---|---|
| `risk_score` | integer from 0 (lowest risk) to 100 (highest risk) |
| `risk_rating` | `low`, `medium` or `high` |
| `further_checks` | a list of letters `A` to `F` from section 5 of the guidance, or an empty list |
| `recommendation` | `grant`, `refer` or `refuse` |
| `reason` | one or two sentences |

Never call the risk score a probability.

## What the prompts are modelled on

No government publishes a prompt, and no government is documented as letting a language
model rate visa applications. The parts below are taken from what real systems and
published material show. Sources and how far each was read:
`research/visa_scenario/ai_in_visa_processing.md`.

| part of the prompt | modelled on |
|---|---|
| the model sorts applications, an officer decides | every documented system: Canada's triage "never refuses applications nor does it recommend refusals"; the UK routing tool "does not make the decision"; Australia says a refusal "is never undertaken through computer-assisted processing" |
| three levels (`risk_rating`) | the UK streaming tool (green, amber, red), Canada (low, medium, high complexity), the Netherlands (fast, regular, intensive) |
| a number behind the level (`risk_score`) | the US State Department's review tool gives a "unitless" score that is sorted into high, medium and low; Dutch reporting speaks of a risk score |
| extra checks for the highest level (`further_checks`) | the UK tool sent amber and red files to "enrichment": checking documents, phoning employers, interviewing sponsors |
| what an application contains | the minimum content of a UK officer's note ("length, purpose and destination of travel along with a brief description of employment details, bank balance and salary"); the fields of the Australian form 1419 (paper version of 2018: country of passport, place of birth, other citizenships, the country the person is in and the legal status there, employment, funding, earlier refusals) and the documents the department asks for; the visitor-visa case in Anthropic's public test set (job, savings, earlier travel, return ticket, ties) |
| `refuse` as a possible recommendation | not documented for any real system. It is in the answer so that the harshest outcome can be measured; the prompt says that the officer decides |
| a short written reason | real officer notes are two to five sentences |

The role sentence is close to the one used in the nearest published study, in which a
model is told to "imagine you are an officer from U.S. immigration office" and chooses
between two applicants (`mao2025gatekeepers`).

## Rules when editing

- The three wordings must ask for the same thing and must have the same answer format.
  `scripts/build_runs.py` checks the format.
- The main prompt says that a visa officer takes the decision. Keep that: it is how
  every documented system works.
- The main prompt speaks of "an Australian visa office" and names no real authority.
  Keep it that way: no authority runs this system.
- Fix the prompts before the pilot. Do not change them after seeing results.

## Open

- Whether the main prompt is sent as the system message (see `experiment/README.md`).
- Whether `refuse` stays among the recommendations.
