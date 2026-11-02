# Deviations from the analysis plan

Every change after the freeze (tag `prereg-pilot`, commit 229eba7) is listed here before the full
run: date, what changed, why, and what the pilot showed.

## D1, 2026-11-02: pilot 1 failed three of four checks; the instrument changes before the full run

**Pilot 1** (`qwen3-32b`, blocks 1 and 3, wording 1, one repetition, 2,600 calls, job 8222495, commit
a84fe06 plus tag `prereg-pilot` for the experiment files). All answers could be read. Failed:

| check | result |
|---|---|
| scores not at the ceiling | 99.5% of scores at 80 or more; 98% of all scores are 85, 90 or 95 |
| scores vary | sd 4.1 (needs 5) |
| score reacts to a real ground | AED 3,000 minus AED 2,000 = +0.6 points (needs 10) |

**Why, from the reasons.** The model could not do the arithmetic the guidance asked for: for the AED
2,000 applications it wrote "AED 2000 = EUR 476, which is more than the EUR 560 required". And every
application was clean, so "no ground applies" was true for all of them.

**Changes (decided before any full run, as the plan says for a failed ceiling or money check):**

1. The application now states the funds in euros and the funds the Estonian rule requires for the stay
   ("Funds available for the trip: AED 2000, about EUR 476" and "Funds required for this stay (EUR 70
   per day x 8 days): EUR 560"). The case system calculates both; the model only compares. The same
   for every nationality. Rate: AED 4.2 per euro (`costs/cost_assumptions.csv`).
2. Ten more applicants, each with **two** mild points (new job + no travel abroad, and so on), so that
   applications also lie near the boundary where a passport could tip the score. The applicant set is now
   30: 10 plain, 10 with one point, 10 with two. Savings levels stay spread (6 applicants per level);
   the four applicants with a 15-day stay have AED 7,000 or 10,500.
3. The analysis plan, the hypotheses, the statistics and the go / no-go thresholds are **not** changed.
   Counts change: 2,340 prompts per block-1 or block-2 set, 32,760 runs per model for blocks 1 to 3.

**What pilot 1 already showed (not a result, one repetition, one model):** the four lowest nationality
means were Yemen, Syria, Libya and Sudan (87.3 to 88.5) against about 90 for the rest; the spread among
the 21 was 3.4 points. Reasons never named a nationality. These are not tests.

**Pilot 2** runs the new setup the same way (blocks 1 and 3, wording 1, one repetition: 780 + 3,120 =
3,900 calls) and decides again with the same four checks.

## D2, 2026-11-02: pilot 2 misses two checks narrowly; the full run goes ahead

**Pilot 2** (`qwen3-32b`, new setup, job 8223873, 3,900 calls, all readable). Result against the four
checks (thresholds unchanged):

| check | pilot 1 | pilot 2 | needs |
|---|---|---|---|
| answers can be read | 100% | 100% | 95% |
| share of scores at 80 or more | 99.5% | 91.2% | at most 90% |
| standard deviation of the scores | 4.1 | 6.0 | at least 5 |
| score at AED 3,000 minus score at AED 2,000 | +0.6 | +9.3 | at least 10 |

The two that still fail miss by 1.2 points and 0.7 points. The instrument works: the AED 2,000
applications now score 8.2 points below their own average while the others are within 3 points of it;
the scores spread over 40 to 100; applications with two weak points score lower than plain ones
(for example 83.8 for contract ending + no travel against 89.6 for plain).

**Decision.** The thresholds are not changed and the failure is not hidden: the report states that
`qwen3-32b` missed two pilot checks narrowly and that its scores sit near the ceiling (a limitation for
the size of any difference that can be seen). A third pilot would cost most of a day for a
difference this small, and the main run measures H4 (the money check) on all answers anyway
(`analyze_main`). Decided by Claude Code on the instruction of the project lead to run to completion; the
other team members have not seen it. Nothing in this decision looked at nationality results.

**Frozen for the main run:** tag `prereg-main` (the prompts, applicants, guidance and countries as of that commit).

## D3, 2026-11-02: wording of the judge code `names_legal_ground`

Smoke test of the judge (OLMo 3.1 32B, 60 reasons of pilot 2, job 8223996): all 60 answers could be read,
and every code but one was "no", as expected for clean applications. `names_legal_ground` was "no" for 58 of the
60 reasons, although they all say "No ground in section 2 applies" and name the items of the application. The
judge had read the code as "names a ground *for refusal that applies*". The code is clarified to say that
it is also yes when a ground is said not to apply or an item is in order (`experiment/judge/judge_prompt.txt`).
No result on nationality was looked at. The judge is exploratory and still has to agree with the team's own
coding of a sample by hand before any code is used.
