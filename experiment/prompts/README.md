# Prompts

Written on 2026-10-10. Each file is a message with placeholders. The prompts of the bank
design are in `research/old_design/bank_2026-10-08/prompts/`.

Every run has two messages: the **main prompt** (who the model is, and the guidance),
then the **task** (one application and the request for the rating).

| file | what it is |
|---|---|
| `main_prompt.txt` | the main prompt, in six sections: ROLE, TASK, DECISION, PROCEDURE, OUTPUT FORMAT, GUIDANCE. `{policy}` is filled with the guidance, without section 7 or with one version of it (see "Variants") |
| `base/task_wording_1.txt`, `base/task_wording_2.txt`, `base/task_wording_3.txt` | the task in three phrasings, so that a result does not depend on one phrasing. `{application}` is filled with one application |
| other folders | variants of the main prompt or of the task wordings (see "Variants") |

## Placeholders

| placeholder | filled with | comes from |
|---|---|---|
| `{policy}` | the guidance, without section 7 or with one version of it | `experiment/policy/` |
| `{application}` | one applicant with one nationality | `experiment/applicants/`, `experiment/countries/applicant_nationalities.csv` |

The nationality enters only through the application: the lines `Nationality:` and
`Travel document:`.

## The answer

The three base wordings (`base/`) ask for the same JSON object. The variants `reasoning`, `trust` and `no_policy` change it (see "Variants"):

| key | values |
|---|---|
| `risk_score` | integer from 0 (lowest risk) to 100 (highest risk) |
| `risk_rating` | `low`, `medium` or `high`, as defined in section 4 of the guidance |
| `further_checks` | a JSON list of capital letters `A` to `F` from section 5 of the guidance, or an empty list |
| `recommendation` | `grant`, `refer` or `refuse`, as defined in section 6 of the guidance |
| `reason` | one or two sentences that name the points from section 3 of the guidance the model relied on |

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

## Main prompt: structure and sources

| section | prompt component | source | why |
|---|---|---|---|
| all sections | structure | `schulhoff2024prompt`, section 1.2.1, pp. 5-6 | the prompt uses the standard components of a prompt: role, directive, additional information, output formatting |
| ROLE | role | `schulhoff2024prompt`; `mao2025gatekeepers`, p. 3 | role is a standard component; Mao and Zhao give the model the role of an immigration officer as well |
| TASK | directive | `schulhoff2024prompt`; `tamkin2023evaluating`, pp. 2-3 | the directive is "the core intent of the prompt"; Tamkin et al. let the model decide about one described person, including "issuing a tourist visa" |
| DECISION | additional information | the table above; `mao2025gatekeepers` | documented systems sort applications and an officer decides; in Mao and Zhao the model decides itself, here it only supports the officer |
| PROCEDURE | directive | `schulhoff2024prompt`; `tamkin2023evaluating` | one application per request, as one person per prompt in Tamkin et al. |
| OUTPUT FORMAT | output formatting | `schulhoff2024prompt` | the format is a component of its own; the exact format is given in the task |
| GUIDANCE | additional information | `schulhoff2024prompt`; `tamkin2023evaluating`, p. 8 | the guidance is context; its section 7 is an intervention like "Ignore demographics" in Tamkin et al., which reduced discrimination strongly (RQ3) |

Left out on purpose:
- **No examples (zero-shot).** Examples would anchor the scores and would need a nationality themselves. `mao2025gatekeepers` and `tamkin2023evaluating` are zero-shot as well.
- **No sentence asking the model to be fair.** Such statements reduce discrimination strongly (`tamkin2023evaluating`, p. 8). Here that sentence is section 7 of the guidance, which only some runs get; in the main prompt it would remove the contrast that RQ3 tests.

## Task wordings: structure and sources

The three base wordings ask for the same thing and end with the same answer block. They differ in structure, not only in a few words:

| wording | structure |
|---|---|
| 1 | a short request, then the application between `<application>` tags, then the task in one sentence |
| 2 | a one-line notice, then the application under the heading APPLICATION, then the task as running text |
| 3 | the task as three numbered steps, then the application under the heading APPLICATION |

| change | why | source |
|---|---|---|
| three different structures instead of three near-identical phrasings | a result from one phrasing can be unreliable; small changes of format and wording change results strongly, so the robustness check needs real differences | `sclar2024quantifying`; `mizrahi2024state` |
| "one or more of the criteria in section 2" instead of "does not meet the criteria" | names the criteria the risk refers to and is easier to read for small models; the same in all three wordings | `atreja2025prompt` |
| answer block linked to the guidance ("as defined in section 4 / 6", "a JSON list of the capital letters") | the model should use the definitions of the guidance, and a clear format helps small models to comply | `atreja2025prompt` |
| the reason field is kept and names the points from section 3 | asking for an explanation improves compliance with the instructions; naming the points lets the reasons be coded later | `atreja2025prompt`, p. 7 |
| answer block identical in all three wordings | the answers must be comparable; `scripts/build_runs.py` checks this | — |

## Variants

Every variant uses the same applications and changes one thing only. Not yet used by `scripts/build_runs.py`; which variants are run is to be decided by the team.

| variant | main prompt | task wordings | guidance | what it tests |
|---|---|---|---|---|
| base | `main_prompt.txt` | `base/` | without section 7 | the main measurement |
| nationality rule | `main_prompt.txt` | `base/` | with `../policy/nationality_rule.txt` | whether "nationality is not a ground" reduces the differences (RQ3) |
| illegal rule | `main_prompt.txt` | `base/` | with `../policy/illegal_rule.txt` | whether a prohibition works better than the instruction (`tamkin2023evaluating`) |
| info rule | `main_prompt.txt` | `base/` | with `../policy/info_rule.txt` | whether a plain fact works like the instruction or the prohibition |
| no guidance | `no_policy/main_prompt.txt` | `no_policy/` | none | whether the guidance reduces the differences at all; only score, rating and recommendation are comparable |
| reasoning | `main_prompt.txt` | `reasoning/` | without section 7 | whether reasoning first changes the differences (`shaikh2023second`); the reasoning text is not a faithful account of how the model decided (`turpin2023language`) |
| trust | `main_prompt.txt` | `trust/` | without section 7 | whether a positive scale gives the same differences as the risk scale |
| decider | `decider/main_prompt.txt` | `base/` | without section 7 | whether a final say changes the differences (`mao2025gatekeepers`) |
| time pressure | `time_pressure/main_prompt.txt` | `base/` | without section 7 | whether a backlog framing changes the differences |
| time careful | `time_careful/main_prompt.txt` | `base/` | without section 7 | counterpart to time pressure: a framing of no pressure and full assessment |
| Arab officer | `arab_officer/main_prompt.txt` | `base/` | without section 7 | whether a persona of Arab background changes the differences (persona prompting) |
| Australian officer | `australian_officer/main_prompt.txt` | `base/` | without section 7 | counterpart to the Arab officer: does naming any background change the differences, or only an Arab one |

## Rules when editing

- The three wordings of a folder must ask for the same thing and must have the same answer format.
  `scripts/build_runs.py` checks the format.
- A variant changes one thing only; everything else is the same as in the base.
- The main prompt says that a visa officer takes the decision. Keep that: it is how
  every documented system works. The variant `decider` is the only exception.
- The main prompt speaks of "an Australian visa office" and names no real authority.
  Keep it that way: no authority runs this system.
- The main prompt has no examples and no sentence asking the model to be fair or to
  ignore nationality. Keep it that way: see "Main prompt: structure and sources".
- Fix the prompts before the pilot. Do not change them after seeing results.

## Open

- Whether the main prompt is sent as the system message (see `experiment/README.md`).
- Whether `refuse` stays among the recommendations.
- Which variants are run.