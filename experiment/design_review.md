# Design review, as a professor and a referee would read it

Written on 2026-11-01 by Claude Code at Laith's request, after the move to Estonia. Internal
document, not report text. Its job is to say what is weak before someone else does.

## Verdict

It makes sense as an **audit with a stated yardstick**: identical applications, one thing
changes, the rules say the answer should not change, and the model has to give a reason that
can be held against a written list (Article 32(1)). That is a clean and defensible design for a
short paper. What it can show is "this model gives the passport this much weight". It cannot
show prejudice, cannot show anything about real offices, and cannot show anything about Islam.
The paper must say so in those words. The strongest part is the within-Arab comparison with a
legal yardstick and a reason-level analysis; the weakest is the small and clean applicant set.

## What a professor would ask, and the answer now

| # | objection | status |
|---|---|---|
| 1 | **The money check was invalid.** The application gave both savings and a monthly income, and the income alone covers 8 days at EUR 70. A model that ignored the AED 2,000 level would be right to. | **Fixed.** The application now states "funds available for the trip" (the bank balance) and the guidance says to compare that with the amount, with income as evidence of how the funds were built up. |
| 2 | No hypotheses, no analysis plan, no stopping rules; "bias" undefined. | **Fixed.** `analysis_plan.md`: four confirmatory questions, a permutation test with the labels shuffled inside each applicant cell, Holm correction over models, a 5-point smallest effect of interest, exploratory work kept apart, exclusions fixed. `pipeline/analyze_main.py` runs it; a planted effect is found and a null is not. |
| 3 | No evidence the instrument can move at all (a ceiling at 90 for everybody). | **Pilot with go / no-go rules fixed in advance** (`cluster/PILOT.md`, `pipeline/pilot_report.py`): readable share, ceiling share, spread, and the reaction to a real ground. |
| 4 | "Nationality is not a ground" is too strong as a legal claim. The Visa Code asks officers to assess the risk of illegal immigration (Article 21, not read in full text), and EU systems have risk indicators. A model that weights nationality is not obviously wrong about the law. | **Handled in wording.** Article 32(1) lists no nationality, and the prompts say only that. The report must call a difference "the weight given to the passport", not unlawful. Read Article 21 before the report. |
| 5 | The noise reference is weak: one of four placebo nationalities (Uruguay) needs no visa. | **Handled.** Noise comes from the permutation of labels inside cells, with the three placebo nationalities that need a visa as a second reference. Uruguay and the United Arab Emirates are read apart. |
| 6 | Multiple comparisons: 21 nationalities, 210 pairs, three models, twelve variants. | **Handled.** One omnibus statistic per question, Holm over models, pairs and variants labelled exploratory. |
| 7 | Pseudo-replication: 20 applicants only, so the nationality effect could be one applicant. | **Handled.** Cells are applicants; the permutation respects them; the pilot report and the final tables show the effect by indicator; the report says 20 applicants is a limit. Adding applicants stays on the parked list (scope). |
| 8 | Prompt sensitivity. | Three wordings of different structure, twelve variants, five repetitions at temperature 0.7. |
| 9 | The judge is another model, and its blinding leaks. | Blinded, only the reason, six codes, a code is used only with kappa of 0.7 against the team's coding. Leaks are listed in `judge/README.md` and not measured yet. |
| 10 | Stale numbers: "four models". | **Fixed.** Three audited models (`models.csv`); documents corrected. |
| 11 | `max_tokens` 400 truncates the `reasoning` variant. | **Fixed.** 800. |
| 12 | The rich group is exactly the Gulf states; the poor group is four countries at war. | Stated. Cannot be fixed within the design; said as a limitation. |
| 13 | External validity: synthetic applicants, residents of one country, open models of 24 to 32 billion parameters, a task no authority is documented as giving to a model. | Stated. The claim is about model behaviour on this task, not about practice. |

## Open, and the team has to decide

- **Score direction** (grant scale or risk scale) and the **cut-offs** for the cost measures (below
  20, below 50). Fix before the pilot.
- Whether the **Emirati and Uruguayan rows** stay. They cost 2 of 26 nationalities and answer a
  different question (what a model does with a visa application nobody from that country files).
- **Articles 14, 15, 21, 22 and 25a** and the visa exemption of the Emirates and Uruguay: read the
  text. The EUR-Lex fetch failed and the checklist of the Estonian mission could not be
  downloaded.
- The **claim that Estonia uses AI** in visa decision support: no source found.
- **How many variants** to run. Twelve is 18,720 runs per model on top of 21,840. A defensible
  short list is base, `regulation_text`, `regulation_instruction`, `no_guidance`.
- **Format enforcement** (JSON schema) after the pilot. **Pinned revisions** of the three models and
  the judge models.
- **Agreement of Aleksander and Nico**, in writing, before the pilot: the scenario has changed
  five times, and the midterm on 11 and 12 November needs first results.

## What would make the paper stronger without adding factors

- Report the effect in points and in the cost measures, next to the noise, for every model.
- Show five or six reasons verbatim, chosen by a rule fixed beforehand (for example the lowest
  score of each nationality group), not by taste.
- Say what the filter removed and what it could not remove (`applicants/README.md`).
- Keep the claims small: "differences that the rules do not explain", not "discrimination".
