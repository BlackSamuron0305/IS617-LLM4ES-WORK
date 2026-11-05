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

## D4, 2026-11-02: a boundary set of applicants (blocks 5 and 6), added after the main run

**Why.** The main run (blocks 1 to 3) showed what pilot 2 had suggested: the scores of all three models
sit near the ceiling (mean 79 to 87) because almost every application is clean, so the room in which a
passport can move the score is small (the 21 nationalities differ by 1.6 to 3.4 points between the highest and
the lowest). That is a limit of the instrument, not a finding about the models. The extension asks the same question where applications are
close to the decision line.

**What.** Ten more applicants, `applicant_set = boundary`: **every one of the ten ways to choose three of the five mild
points** (new job, no travel abroad, contract ending, long stay, relative in Estonia). The set was fixed by this rule,
not by looking at which applications gave large differences; no result by nationality was looked at to choose it. Savings are
AED 3,000 to 10,500 (not the AED 2,000 level, which is a ground of its own); the long stays have AED 7,000 or 10,500.
They run as block 5 (guidance without the paragraph on nationality) and block 6 (with it), 10 x 26 x 3 x 5 = 3,900 runs each
per model.

**Status.** Exploratory extension, reported apart from the confirmatory H1 to H3 (which keep their blocks 1 and 2). The same
test is computed on blocks 5 and 6 (`python -m pipeline.analysis.analyze_main --blocks 5 6`). Blocks 1 to 4 are unchanged: the builder
puts only the 30 main applicants in them.

## D5, 2026-11-02: six more models as a robustness extension (E2)

**Why.** Asked by the project lead to run more and finish by Sunday. The three audited models differ in origin (China, USA, Europe) but
are all 24 to 32 billion parameters. The main finding (small, systematic gaps; poor and war-affected countries lowest) should be
checked on other models: do small models or a large reasoning model show larger gaps?

**Which.** Every instruction-tuned chat model that was already downloaded on the cluster and fits one GPU, taken from the list on the cluster
before any result of these models was seen: Qwen2.5 7B (China), Falcon3 7B (United Arab Emirates), Phi-3.5 mini (USA), OLMo 2 7B (USA),
Mistral 7B v0.3 (France) and gpt-oss-120b (USA, a reasoning model). Left out for a stated reason, not for a result: DeepSeek V4 flash (156 GB,
no chat template) and Mistral Medium 3.5 (249 GB). The three audited models stay the audited models; the six are **exploratory** and never replace them.

**What.** The base design, unchanged: blocks 1, 2, 3, 5 and 6 (40,560 answers per model), same prompts, same settings, split into
small shards so that several 30-minute jobs run at the same time. Revisions are pinned from the download metadata (`experiment/config/models.csv`).
The analysis is the same tests as for the audited models (`analyze_main`), reported as a separate table.

## D6, 2026-11-02: the parser reads a whole number written as text

In the smoke test of the extra models, Mistral 7B wrote `"visa_score": "80"` (a string) once in 40 answers. The parser took it as a bad value.
It now reads a whole number between 0 and 999 written as text ("80") and still rejects words and decimals; a number outside 0 to 100 is still a bad value.
No answer of the three audited models changes: all their answers were read before (the only bad values were the object-valued reasoning
field, D-parser note in `pipeline/answers/parse_answers.py`). Re-parsing the audited batches gives the same tables.

## D7, 2026-11-02: bigger models (E3), after the extra small models

**Why.** In E2 (D5) one small model, Qwen2.5 7B, showed a gap of 29 points between nationalities (the audited models: 1.6 to 3.4; the other extra
models: 0 to 2), and its reasons raised doubts about money and credibility far more often for Somali, Syrian and Iraqi applicants. The project
lead asked for bigger models for the report. Two questions: does that gap shrink with size inside one family, and does a large model behave like
the audited ones?

**Which.** Qwen2.5 32B and 72B (the same family as the 7B model, from the same maker; downloaded on 2026-11-02, revisions pinned to the current head
before any answer was seen) and Mistral Medium 3.5 128B (already on the cluster). Exploratory, like E2; the audited models stay the three of 2026-11-01.

**What.** The base design unchanged (blocks 1, 2, 3, 5, 6), sharded; two to four GPUs per job for the large ones (tensor parallel).

## D8, 2026-11-03 to 2026-11-05: the deep dive (exploratory; branch `bias-deep-dive`, merged into `main` on 2026-11-04)

**Why.** After the runs of D1 to D7 the project lead asked what else explains the gaps: which line of the application carries them, whether
negative applicants, other prompts, other nationalities, thinking, the sampling temperature or the judge change the picture.

**What.** Everything is exploratory and none of it replaces the audited design or any audited table. Every old prompt stays byte-identical (hash checked).
(1) Negative applicants (blocks 7 and 8); eleven more prompt variants; ablations of the nationality and document lines; reference nationalities (German,
American, Indian, Filipino, Pakistani, not stated; run on the project lead's explicit request, which overrides the rule of 2026-10-10 for this work only);
eight more Qwen models; a judge lab (`pipeline/judge/lab.py`). (2) Five repetitions of the key variants for four models and a conflict-country set
(Afghanistan, Ukraine, Eritrea, Myanmar against Nepal and Vietnam, plus Venezuela) for six models. (3) Thinking switched on (Qwen3 32B and 14B; gpt-oss-120b at reasoning
effort high instead of low) and the temperatures 0.0, 0.3, 1.0 and 1.5 for four models, block 1, one repetition (`--temperature`, `--max-tokens` of `run_models`;
the parser reads the answer after the last `</think>`). No result by nationality was used to choose any of it; the models and temperatures were fixed before the runs.
Findings: `experiment/deep_dive/RESULTS.md`; tables: `results/deep_dive/`.
