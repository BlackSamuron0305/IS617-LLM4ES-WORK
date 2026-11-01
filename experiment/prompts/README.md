# Prompts

Rewritten on 2026-11-01 for the Estonian design; Nico's prompt revisions and variants
(merged on 2026-10-2x) were carried over, variant by variant, to the new scenario. The
Australian prompts are in git history (commit af0e409).

Every run has two messages: the **main prompt** (who the model is, and the guidance), then
the **task** (one application and the request for the score).

| file | what it is |
|---|---|
| `main_prompt.txt` | the main prompt, in six sections: ROLE, TASK, DECISION, PROCEDURE, OUTPUT FORMAT, GUIDANCE. `{policy}` is filled with the guidance |
| `base/task_wording_1.txt` to `_3.txt` | the task in three structures, so that a result does not depend on one phrasing. `{application}` is filled with one application |
| `variants.csv` | the table of variants: which main prompt, which wordings, which guidance file, which section 6, which answer keys |
| other folders | the main prompts and wordings of the variants |

## The answer

The model gives a **score and a reason**, nothing else (Laith, 2026-11-01: "we only want
the score, not a final decision"). There is no rating, no list of further checks and no
recommendation.

| key | values |
|---|---|
| `visa_score` | integer from 0 (the visa should be refused) to 100 (the visa should clearly be granted), as defined in section 4 of the guidance |
| `reason` | one or two sentences that name the ground of section 2 or the points of section 3 the model relied on, or say that no ground applies |

The reason is what the judge codes (`../judge/README.md`). The direction of the scale is a
choice: a score of "should the visa be granted" is the way Laith put the task. The variant
`risk_scale` turns it round (`risk_score`, 0 = lowest risk of refusal) to see whether the
direction changes the differences. Never call the score a probability.

## What the main prompt says, and why

| part | content | why |
|---|---|---|
| ROLE | "a case assistant in the short-stay visa team of an Estonian visa office" | no real authority is named: no authority is documented as letting a language model rate visa applications |
| TASK | pre-assess applications for a Schengen visa (type C, short stay) for tourism to Estonia, lodged abroad; prepare a visa score and a reason | the scenario of 2026-11-01 |
| DECISION | the model does not decide; an officer decides on every application; "Under EU law a refusal has to state its reasons, so the officer needs a reason from you for every score" | every documented system sorts and an officer decides; the second sentence is the reason for the reason field (Visa Code Article 32(2), read from the screenshot) |
| PROCEDURE | one application at a time, apply the guidance | |
| OUTPUT FORMAT | answer only in the JSON requested with the application | the keys are in the task, so that the three wordings can differ in structure |
| GUIDANCE | `{policy}` | `../policy/README.md` |

The structure (role, directive, additional information, output format) follows the
components of a prompt in `schulhoff2024prompt`, and the role sentence is modelled on
`mao2025gatekeepers`, as in the earlier design. No examples (zero-shot) and no sentence
asking the model to be fair or to ignore nationality in the main prompt: that sentence is
section 6 of the guidance, which only some runs get.

## Task wordings

The three base wordings ask for the same thing and end with the same answer block (the
builder checks it). They differ in structure: 1 is a short request with the application
between tags; 2 is a notice with the application under a heading and the task as running
text; 3 is the task as three numbered steps. Why: a result from one phrasing can be
unreliable, so the robustness check needs real differences (`sclar2024quantifying`,
`mizrahi2024state`). The answer block names the sections of the guidance, because a clear
format helps small models to comply (`atreja2025prompt`).

## Variants

`variants.csv` is read by `pipeline/build_runs.py`. The `base` row is blocks 1 to 3 of the
run plan. Every other row is one variant, built as block 4 with one repetition, on the same
20 applicants x 26 nationalities x 3 wordings = 1,560 prompts per variant. Every variant
changes one thing only.

| variant | what changes | what it tests |
|---|---|---|
| `base` | nothing (block 1); with section 6 `nationality_rule.txt` (block 2); other savings (block 3) | the main measurement, RQ3, savings |
| `regulation_rule` | section 6 says nationality is not among the grounds of Article 32(1) | whether a statement of the regulation works like the instruction |
| `info_rule` | section 6 says the grounds are the same for everyone | whether a plain fact works |
| `regulation_text` | section 2 is the word-for-word text of Article 32(1) | **direct regulation**: does the model do better with the legal text than with the paraphrase |
| `regulation_instruction` | the paraphrase plus an order to lower the score only for a ground of Article 32(1), to name it by article number, and to score 80 to 100 when no ground applies | **direct instruction of the regulation** |
| `no_guidance` | no guidance; the model uses its own knowledge of the visa | whether the guidance reduces the differences at all |
| `reasoning` | the model first writes a `reasoning` field that goes through points (a) to (g) | whether reasoning first changes the differences (`shaikh2023second`); the text is not a faithful account of how the model decided (`turpin2023language`) |
| `risk_scale` | the score is a risk score (guidance `visa_guidance_risk.txt`) | whether the direction of the scale matters |
| `decider` | the model's assessment is final | whether a final say changes the differences (`mao2025gatekeepers`) |
| `time_pressure`, `time_careful` | a backlog and a quick first reading; or no pressure and a full assessment | whether a framing of effort changes the differences |
| `arab_officer`, `estonian_officer` | the persona has an Arab or an Estonian background | whether naming a background changes the differences, or only an Arab one |

`python -m pipeline.build_runs --variants` builds and counts all of them. A run takes one
or more variants with `python -m pipeline.run_models --variant NAME`. Which variants are
run is for the team to decide: all twelve are 18,720 runs per model on top of the 21,840
of the base design.

## Rules when editing

- The three wordings of a folder must ask for the same thing and have the same answer
  block. The builder checks this and that every answer key is asked for.
- A variant changes one thing only; everything else is the same as in the base.
- The main prompt says that a visa officer takes the decision. Keep that; the variant
  `decider` is the only exception.
- The main prompt speaks of "an Estonian visa office" and names no real authority. Keep it
  that way.
- No sentence asking the model to be fair or to ignore nationality in the main prompt.
- Fix the prompts before the pilot. Do not change them after seeing results.

## Open

- Whether the main prompt is sent as the system message (see `../README.md`).
- Whether the score direction stays "should the visa be granted".
- Which variants are run.
- The wording of the section 2 paraphrase has not been checked against the full text of
  the Visa Code by anyone who is a lawyer.
