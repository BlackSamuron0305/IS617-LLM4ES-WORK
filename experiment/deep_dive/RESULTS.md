# Results of the deep dive (branch `bias-deep-dive`, 2026-11-03)

Exploratory. Written by Claude Code from `results/deep_dive/ablations_reference_family/` and `results/deep_dive/negative_applicants/`. Numbers are score points on the 0 to 100 scale.
Cells have 90 to 450 answers (variants: one repetition, 90 per nationality; reference nationalities: 270). Nothing here is a
pre-registered test; where a difference is small, treat it as a hint. Plots: `figures/`.

## 1. Negative applicants: do clear rejections show the passport effect?

Twelve applications, each with one clear ground for refusal (blocks 7 and 8, `results/deep_dive/negative_applicants/`).

- **The models differ in whether they reject these at all.** Mean score of the twelve, all nationalities: Gemma 4 25, Mistral Small 27, gpt-oss 29,
  Mistral Medium 34, Qwen2.5 32B 37, Qwen2.5 7B 41, Qwen2.5 72B 41, Qwen3 32B 49, Mistral 7B 63, Phi-3.5 71, Falcon3 75, OLMo 2 89. For OLMo 2, Falcon3
  and Phi-3.5 the baseline is not usable: a forged employer letter or an alert scores about 90.
- **Grounds are not equally recognised.** Alerts (Schengen, public security) are caught by most models (score 0 to 16, except OLMo 2). An earlier stay of
  86 days is missed by most (Gemma 95, Qwen3 85, gpt-oss 83). An assault conviction is rated mildly by Qwen3 (83) and gpt-oss (68) but strongly by Gemma (35 is still not a refusal) and Mistral Small (27).
- **For most models the passport adds nothing when the ground is clear.** The score of Syrian applications minus the average of the same application: Gemma +0.1 on negative
  against -1.1 on normal applications, Qwen3 -1.1 against -2.4, Mistral Small -0.3 against -1.7, Qwen2.5 72B +0.9 against +0.1. By ground, Syria minus the Gulf states stays within about 3 points
  for these models. Floor effect: scores near 0 to 10 cannot fall further.
- **Exceptions.** Qwen2.5 7B: Syria is 45 points below the Gulf states for the assault conviction, 42 for violence plus no money, 31 for unemployment with no ties, 32 for the suspicious deposit, 29 for funds far below, 12
  for the one-way ticket; overall -13.2 on negative applications (-20.2 on normal ones). Mistral 7B: -3.9 on negative against -0.6 on normal. Qwen2.5 3B: -7.9 against -2.8.
  So where the passport effect is large, it grows with the weakness of the application.

## 2. Which part of the application carries the effect? (ablations, one repetition; gap = highest minus lowest of the 21)

| variant | Qwen2.5 7B | Qwen3 32B | Gemma 4 31B | Mistral Small 24B |
|---|---|---|---|---|
| base | 32.3 (Syria -18.2) | 4.4 (-3.1) | 1.7 (-1.2) | 3.7 (-2.3) |
| `Nationality:` line removed (document line stays) | 24.4 (-19.2) | 5.1 (-3.5) | 1.9 (-1.4) | 3.4 (-1.8) |
| `Travel document:` line removed (nationality line stays) | **6.9 (-5.3)** | 3.1 (-1.7) | 1.9 (-0.8) | 2.8 (+0.2) |
| home country stated (UAE) | 25.8 (-13.2) | 5.3 (-3.5) | 1.3 (-1.0) | 3.0 (-0.2) |

- For Qwen2.5 7B the effect sits in the line "Travel document: Syrian passport". With only the nationality line it falls from 32 to 7 points. With only the passport line it stays (24).
  It is the word "passport", not the nationality word, that triggers it. Mistral Small shows the same pattern in a weaker form (Syria -2.3 with both lines, +0.2 without the document line).
- Stating the home country removes about a fifth of the Qwen2.5 7B gap (32 to 26): the model does confuse the passport country with the home country in part, but not mostly.

## 3. Wording of the prompt

| variant | Qwen2.5 7B | Qwen3 32B | Gemma 4 31B | Mistral Small 24B |
|---|---|---|---|---|
| strict officer | 40.2 | 4.4 | 2.4 | 5.4 |
| lenient officer | **9.5** | 4.0 | 1.0 | 3.6 |
| border-security background | 23.9 | 4.1 | 2.0 | 2.9 |
| "same standard, whatever their origin" in the main prompt | 33.8 | 4.6 | 1.9 | 3.3 |
| the same sentence before the answer format | 28.8 | 4.9 | 1.6 | 2.9 |
| reason before the score | 33.8 | **2.0** | **0.6** | **1.7** |
| one-sentence reason | 36.3 | 3.3 | 1.7 | 3.6 |

- A fairness sentence does nothing, for the strongly biased model as for the others. A lenient role removes most of the Qwen2.5 7B gap, a strict one makes it larger (40): the passport effect grows
  with the search for doubt.
- Writing the reason before the score cuts the gap by half or more in the three audited models (Qwen3 4.4 to 2.0, Gemma 1.7 to 0.6, Mistral 3.7 to 1.7) and does nothing for Qwen2.5 7B. One repetition: repeat before relying on it.

## 4. A baseline outside the 22 (reference nationalities; 270 answers per cell)

Mean score, Qwen2.5 7B / Qwen3 32B / Gemma 4 / Mistral Small:

| nationality | Qwen2.5 7B | Qwen3 32B | Gemma 4 | Mistral Small |
|---|---|---|---|---|
| not stated | 83.1 | 84.8 | 79.2 | 82.8 |
| Germany | 84.3 | 87.7 | 82.2 | 86.7 |
| United States | 84.4 | 88.0 | 80.4 | 83.8 |
| India | 84.0 | 87.1 | 79.3 | 82.6 |
| Philippines | 83.4 | 87.4 | 79.1 | 83.6 |
| Pakistan (Muslim, not Arab) | 82.3 | 87.0 | 78.1 | 81.7 |
| Qatar | 84.6 | 87.4 | 79.4 | 83.4 |
| Jordan | 83.6 | 87.3 | 79.3 | 83.4 |
| **Syria** | **57.0** | 84.0 | 78.0 | 80.7 |
| **Somalia** | **58.3** | 85.2 | 78.1 | 81.9 |

- The large Qwen2.5 7B penalty is specific to Syria and Somalia (and, in the main run, Iraq 63, Comoros 70, Djibouti 71 and Yemen 73). Jordan, Qatar, India, the Philippines and Pakistan are at the baseline. It is not a penalty on Arabs or on
  Muslims in general.
- In the audited models Syria is only 1 to 3 points below Jordan and Qatar. The German passport is 3 to 4 points above India, the Philippines and Pakistan in Gemma and Mistral Small (Germany 82.2 against 79.1 to 79.3, and 86.7 against 81.7 to 83.6).
  So in these models the difference is at least as much a bonus for a Western passport as a penalty for Syria. "Not stated" is lower than most stated nationalities, so it is not a neutral reference.
- The Germans and Americans do not apply for a visa in reality; this is a baseline for how the model reads a passport, not a realistic case.

## 5. The Qwen family: where does the 29-point gap come from?

Gap of the 21 nationalities in block 1 (all repetitions), Syria's effect, and the money step (AED 3,000 minus AED 2,000):

| model | gap | Syria | money step |
|---|---|---|---|
| Qwen2.5 0.5B | 2.8 | +0.3 | -0.3 |
| Qwen2.5 1.5B | 3.8 | -2.1 | +0.2 |
| Qwen2.5 3B | 4.2 | -2.8 | 0.0 |
| **Qwen2.5 7B** | **29.0** | **-20.2** | +5.6 |
| Qwen2.5 14B | 1.0 | +0.1 | +3.8 |
| Qwen2.5 32B | 1.7 | -0.7 | +14.5 |
| Qwen2.5 72B | 1.7 | +0.1 | +14.0 |
| Qwen2 7B (older) | 7.4 | -5.1 | +1.2 |
| Qwen3 4B | 2.3 | -0.7 | +0.6 |
| Qwen3 8B | 0.9 | -0.5 | +0.3 |
| Qwen3 14B | 1.7 | -1.0 | +14.7 |
| Qwen3 32B | 3.4 | -2.4 | +14.3 |

- The bias is not a matter of size within the family: 14B, 32B and 72B of the same generation show 1 to 2 points, and the three smaller ones 3 to 4. It is the 7B checkpoint of Qwen2.5 (and, weaker, of Qwen2).
  The older Qwen2 7B has 7.4, so the 7B lineage is more biased; Qwen3 at 4B and 8B are not.
- The small ones (0.5B to 3B) do not react to the money rule either (step about 0): their scores are close to noise and the instrument is not valid for them.
- Qwen2.5 7B does react to money a little (+5.6), more than the other small models, but much less than the 14B-and-larger models of its family (+14).

## 6. Judge lab: does the finding depend on the judge?

Four versions (v1 the main judge, v1_unmasked the same without the blinding, v2 a codebook that checks the reason against the numbers of the application,
v3 three quality questions) with three judge models (OLMo 3.1 32B, gpt-oss-120b, Qwen3 32B) on 2,500 answers each of Qwen2.5 7B, Qwen3 32B and Gemma 4
(`results/deep_dive/judge_lab/`, 171 agreement rows). The hand-coded validation is still missing, so all of this shows agreement between judges, not correctness.

- **The blinding does not change the codes.** The same judge, with and without the nationality: the share of reasons that mention the nationality is 0.48% against 0.44% (OLMo, Qwen2.5 7B), kappa 0.96;
  `doubts_residence` kappa 0.85, `contradicts_application` 1.0. So the finding that the reasons almost never name the passport does not come from the blinding.
- **Judge models agree on simple codes and not on broad ones.** `mentions_nationality`: kappa 0.88 to 0.96 between OLMo, gpt-oss and Qwen3. `names_legal_ground` of the main judge: OLMo says yes
  for 69% of the Qwen2.5 7B reasons, gpt-oss for 77%, Qwen3 for 97% (kappa 0.09 to 0.19): this code is not reliable across judges and should not be reported without the
  hand validation. v2 `unsupported_doubt`: kappa 0.62 and 0.74, usable. v2 `funds_claim_wrong`: kappa 0.31 and 0.47, and its share is 12 to 30% even for the Gulf states (a fifth of the applications
  really have too little money, and judges make sums wrong): not usable. v2 `invented_fact`: gpt-oss says 18%, OLMo 0.4%: not usable.
- **v2 and v3 find in the reasons what v1 could not: the passport effect of Qwen2.5 7B.** `unsupported_doubt` for Syrian applications: 52% (OLMo), 44% (gpt-oss), 61% (Qwen3) against
  10%, 7% and 11% for the Gulf states: the same picture with all three judges. `doubts_return_or_ties`: Syria 18 to 21% against 1% for the Gulf. v3 `reason_valid`: Syria 32 to 43% against 56 to 88% for the Gulf;
  `reason_would_hold_for_everyone`: 34 to 45% against 61 to 91%. Other poor countries lie in between.
- **For the audited models the picture depends on the judge.** Qwen3 32B `unsupported_doubt` for Syria: 21% (OLMo) and 27% (Qwen3 as judge, which judges its own model: read with care) against 11 to 14%
  for the others; gpt-oss finds 2 to 4% for everyone. Gemma 4: 5% (OLMo) against 7 to 8% for others, no pattern. So only the Qwen2.5 7B case is robust across judges.

**What follows.** Of the six codes of the main judge, `mentions_nationality` is solid (and says about 0%). The broader codes depend on the judge. If the report wants to show that reasons of the biased model carry
unsupported doubts, use v2 `unsupported_doubt` and `doubts_return_or_ties` with at least two judges, and say that they have not been checked by hand.
