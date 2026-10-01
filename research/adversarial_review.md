# Adversarial review (pre-pilot)

Date: 2026-09-30. Reviewer stance: an independent area-chair-level FAccT / ACL reviewer
who is looking for reasons to reject. I did not build any of this. No model or API
was called. The only file I changed in the repository is this one. All tampering ran
on copies in a temporary directory.

Every finding carries a status. **Verified** means I reproduced it, ran it, or read the
exact code path. **Suspicion** means it is a reasoned risk that I could not test
without real model output.

> **History note (added 2026-10-01 by integration methodology; the review text is
> unchanged).** This review, including round 2, describes the repository before
> 2026-10-01. The YAML files, `prompts/*.txt` templates, `stimuli/base_cvs/`,
> `generate-stimuli`, `stimulus_set_id` and `--config config/<x>.yaml` commands it quotes
> no longer exist; current equivalents: `research/design_contract.md` §000 (G1) and
> §00000 (U1, mapping table). Current status of every finding:
> `research/review_response.md`.

---

## 1. Verdict

**Major revision. Reject in the current state, but the design can be rescued before the pilot.**

The engineering is unusually careful:
- a byte-exact clone validator;
- seeded, nationality-free randomisation;
- base CVs as the independent unit;
- a debiased heterogeneity estimator with a permutation null;
- Holm-based families;
- mock data watermarked everywhere.

The citations hold up: 29 of 29 high-relevance entries were checked against their sources, with no fabrications.

The paper would still be rejected on five grounds. Each one is fixable before the pilot.

1. **The pilot's blinding and the confirmatory settings are enforced only by convention.** The documented `analyze` command produces fully unblinded per-origin results. SESOIs and the primary outcome can be overridden at analysis time.
2. **The qualification tiers are not what the paper says they are.** "Borderline" CVs have more total, and arguably more relevant, experience than "adequate" ones. At least 4 of the 12 borderline CVs have job titles that contradict their bullets.
3. **A single run can silently mix model revisions and job-ad versions.** I reproduced this. The model revisions are also still `null`, and nothing refuses a real run in that state.
4. **The default SESOI is larger than the best published estimate of the very effect being studied.** Lippens 2024 reports −1.41 points on a 1–100 scale. Under a 2-point SESOI, that known gap would be labelled "trivial" or "null".
5. **The headline estimand has no placebo or lexical floor.** The team's own novelty assessment names this as the strongest threat and prescribes the fix, but the design does not implement it. Three of the 22 origins are also Horn-of-Africa states, so "within-Arab heterogeneity" can be driven by associations with Black African origin rather than by differences among Arab nationalities.

**Novelty.** The contribution is real but narrow. It is the first disaggregation of a known pooled effect (Lippens 2024) into 22 national signals, in an LLM hiring decision, which MENAValues does for values rather than decisions. It is defensible only as absence of evidence. My independent prior-art search found no pre-emption (Section 6). The paper will survive the "predictable combination plus noise" critique only if H5 is fixed.

---

## 2. What I ran and observed

| command | result |
|---|---|
| `PYTHONPATH=src python -m hiringaudit validate-stimuli` | `[v1] OK: 1296 clones of 48 base CVs`, `[v1_native_german] OK: 1296 clones`, `VALIDATION PASSED`, exit 0 |
| `PYTHONPATH=src python -m pytest -q` | **132 passed** in 51.6 s |
| `... plan --config config/pilot.yaml` | 9,511 calls per model (4,212 + 162 + 4,212 + 400 + 525), 28,533 in total; FC: 100 quads, each level in 8, connected. Matches prereg §3.5. |
| `... plan --config config/main_experiment.yaml` | 24,333 calls per model (31,821 for qwen3-8b), 104,820 in total. Matches prereg §3.5. |
| Mock end to end in a temporary root: `run` → `parse` → `analyze` | 2,762 records. The analysis **runs** and writes 60+ tables. This contradicts README.md:195–197 (L1). |
| 24 validator tamper cases in a temporary root | Summary in the table below; details in H2, M5 and M6. |
| Resume after editing `jobs.yaml` and `models.yaml` | Mixed silently (H3). |
| `analysis/power_analysis.py --engine fast --n-sims 1000` (placeholder values and a pessimistic set) | See M14. |
| Regeneration of the base CVs from the seed (`generate-stimuli --regenerate-base-cvs --force` in a temporary root) | Byte-identical to the committed stimuli. |

### Validator tamper results

"Regen" means I edited the base YAML and re-rendered the clones consistently, so hashes and diffs match. That is how a careless teammate would introduce the change.

| # | tamper | caught? |
|---|---|---|
| T1–T3 | manifest `tier`, `pilot` or `occupation` changed for one base CV | **no** |
| T4 | employer city "Mainz" → "Beirut" (regen) | **no** |
| T9 | employer city → "Dubai" / "Istanbul" (regen) | **no** |
| T6 | bullet containing "halal" and "Ramadan" (regen) | **no** |
| T8 | skill "French" (regen) | **no** |
| T19 | profile "EU citizen." (regen) | **no** |
| T22 | positive-control line re-pointed to the Abitur line (regen) | **no** |
| T12 | job ad: "EU citizenship required" | **no** (job ads are never scanned) |
| T13 | "cultural fit with our German team" added to baseline_k1 and neutrality_k1 | **no** |
| T14 | system prompt: "Candidates from countries with weaker education systems need extra scrutiny" | **no** |
| T5, T20 | skill "Arabic" / "Mother tongue Arabic" | yes |
| T10 | zero-width space in the Nationality line, hash updated | yes |
| T11 | DEU clone edited, hash updated | yes |
| T15 | SYR/IRQ manifest paths swapped | yes |
| T16 | positive-control entry deleted | yes |
| T18 | CRLF line endings, hash updated | yes |
| T21 | unknown nationality code in the manifest | yes, but with a Python traceback (L2) |

---

## 3. HIGH — would sink the paper or corrupt data; fix before the pilot

### H1. Blinding and confirmatory settings are not enforced in code (Verified)

**Evidence**
- `src/hiringaudit/analysis/pipeline.py:98`: `"blind": False` is the default.
- The main CLI `analyze` has no `--blind` flag (`src/hiringaudit/cli.py:114–130, 204–208`). Only the sub-CLI `python -m hiringaudit.analysis --blind` has one.
- README.md:187–199 tells users to reproduce figures with `python -m hiringaudit analyze --run-id …`, and says only that "the pilot analysis runs blind".
- On the mock run, that command wrote `origin_deviations.csv`, `heterogeneity.csv`, `coefficients.csv` and a country heatmap. That is exactly what prereg §3.4 (preregistration.md:244–249) forbids until Stage B.
- The confirmatory settings (SESOI, `alpha`, `primary_outcome`, `confirmatory_condition`, `covariates_path`, `r4_processed_dir`) live in `pipeline.py:81–113`. They can be overridden by any YAML passed through `analyze --config` (cli.py:122–128 → `_merge`). Nothing ties an analysis to a frozen preregistration.
- `sesoi_is_final: False` is only a printed note (pipeline.py:97, 168).

**Why it matters.** Section 0 of the preregistration rests on a blind pilot and on SESOIs fixed before any outcome is seen. One run of the documented command by any teammate breaks both, and nothing in the outputs would show it happened. A reviewer who asks "how do we know the pilot was blind?" gets no verifiable answer.

**Fix**
- Make blind mode the default for every run whose id does not match a frozen main-study id.
- Add `--unblind`, which requires `preregistration.md` to be frozen: its SHA-256 written to a file such as `config/prereg_freeze.json`, checked at run time and printed in `summary.md`.
- Move the SESOIs and confirmatory settings into a frozen `config/analysis_confirmatory.yaml` whose hash is recorded.
- When `--config` overrides any confirmatory key, stamp every output with "EXPLORATORY OVERRIDE".
- Log every unblinded invocation (user, time, hash) to an append-only file in `results/`.

### H2. The tier manipulation is weak and partly inverted, and borderline CVs are incoherent (Verified)

**Evidence**

*Rubric.* `config/cv_pools.yaml:13–17` makes borderline "relevant experience 3–9 months below the minimum", plus an earlier "adjacent" job of 12–30 months (`src/hiringaudit/stimuli/generate.py:108–111`).

*Total experience.* Taken from the `tier_evidence` blocks of the base CVs:

| occupation | borderline total months | adequate total months |
|---|---|---|
| retail | 36, 30 | 13, 28, 25, 32 |
| warehouse | 31, 25 | 13, 16, 15, 13 |
| software developer | 42, **61** | 39, 44, 44, 53 |
| accountant | **61**, 44 | 55, 50, 51, 38 |

In the pilot subset, **every** retail and warehouse borderline CV has more total experience than **every** adequate CV.

*The "adjacent" work is often relevant.* The retail ad's must-haves include "Experience with cash register systems" (`config/jobs.yaml:77`). The "adjacent" job in `retail_03` is 27 months of "Operated the cash register and served customers at a supermarket checkout". The adequate `retail_02` has 13 months of retail in total.

*Title and bullets are drawn independently* (`generate.py:134` titles, `:145–148` bullets). This produces incoherent CVs:
- `retail_03`: "Call Centre Agent | Marktfeld Supermärkte GmbH" with checkout and stockroom bullets (`stimuli/base_cvs/retail_sales_associate/retail_03.yaml:22`; rendered at `…/retail_03__NONE.txt:19`).
- `retail_06`: "Cashier | Lichtblick Telekommunikation GmbH" with "Welcomed guests and handled check-in at the front desk".
- `swdev_03`: "IT Systems Administrator" with software-tester bullets.
- `swdev_06`: "Software Test Engineer" with IT-support and sysadmin bullets.
- `whse_06`: the profile says "earlier work in retail stockrooms", the title says "Delivery Driver".

That is at least 4 of the 12 borderline CVs.

*"Borderline" is barely borderline.* All must-haves are met except 3–9 months of experience, with all required skills and a relevant degree. LLM screeners will almost certainly invite such applicants, which predicts an interview ceiling. This is a suspicion until the pilot, but the rubric makes it likely.

**Why it matters**
- P4 (strong > adequate > borderline for every model) is at real risk of failing, and P3 (interview rate 10–90 %) is likely to fail. Either forces stimulus re-authoring after the pilot, which is a forking path.
- Forced-choice same-tier pairs are not matched on quality.
- R7 ("ambiguity theory") becomes uninterpretable.
- Incoherent CVs are easy for a reviewer to spot in the appendix. They add noise and may cue "synthetic test" (evaluation awareness).

The primary within-CV estimand stays unbiased. This finding threatens the tier-based parts of the design, the interview outcome and the credibility of the paper, not the clone logic.

**Fix, before the pilot**
- Draw adjacent bullets conditional on the adjacent title, for example a pool keyed by title.
- Make the adjacent job genuinely non-relevant, or cap total experience for borderline below the adequate minimum.
- Make borderline miss one must-have more clearly: 12–18 months short, or one required skill at basic level, as the design text itself suggests (`experimental_design.md` §2.3).
- Run the blind two-coder tier check (prereg checklist item 10) now, on the regenerated CVs.

### H3. Resume silently mixes model revisions, job ads and principle items, and real runs are allowed unpinned and uncommitted (Verified)

**Evidence**
- `_identity` (`src/hiringaudit/runner.py:513–515`) checks only `config_hash`, the stimulus manifests and the prompt templates.
- `config_hash` (`src/hiringaudit/config.py:389–400`) hashes the ExperimentConfig, which holds model *aliases* only. The model spec in `models.yaml` (revision, model_id), `jobs.yaml`, `principle_items.yaml`, `nationalities.yaml`, the CV template and the parser version are all excluded.
- `jobs_sha256` is recorded once at creation (runner.py:541) and never re-checked.

*Reproduction* (temporary root):
1. `run --config config/mock.yaml --limit 200`.
2. Edit `jobs.yaml` ("3 years" → "5 years" for software developer) and the mock `revision`.
3. Run again.

Result: `completed; 200 records written, 200 already present`. One run now holds **2 model revisions (200/200) and 2 job-ad versions** (101/110 prompts), with no warning.

*Further gaps*
- All four vLLM models have `revision: null` (`config/models.yaml:51, 72, 88, 108`). The real-call guard (runner.py:558) does not check it.
- `environment()` records the git state (`src/hiringaudit/manifest.py:36–39`), but a dirty or uncommitted tree is not refused. The whole hiring audit is currently **untracked**: `git status` shows `??` for `src/hiringaudit/`, `config/`, `prompts/` and `stimuli/`, and the only commit is the old outcome-bias scaffold 6ed2adb. A pilot run today would record that commit as its provenance.
- The analysis checks one `model_id` per alias (`src/hiringaudit/analysis/schema.py:254–256`) but not one `model_revision`. The processed tables carry no `prompt_sha256` (`src/hiringaudit/schemas.py:70–87`), so a mixed run is invisible downstream.

**Why it matters.** The workflow explicitly expects revisions to be pinned "before a real run". A pilot session started before pinning and resumed after it produces a run that looks homogeneous and is not. That is silent data corruption at the level of the unit of analysis, the model.

**Fix**
- Add these to `_identity`: the full ModelSpec of every selected model; SHA-256 of `jobs.yaml`, `principle_items.yaml`, `nationalities.yaml` and `cv_template_v1.txt`; `PARSER_VERSION`.
- Refuse `--allow-real-calls` when `revision` is null, when `status` is `unverified`, or when `git status --porcelain` lists changes under `src/`, `config/`, `prompts/` or `stimuli/`.
- Compare the server's `/v1/models` answer with `model_id` per session, and refuse on a mismatch.
- Carry `prompt_sha256`, `user_prompt_version` and `model_revision` into the processed tables. Make `load_processed` fail when an alias has more than one revision or prompt version.
- Commit and tag the code before the pilot.

### H4. The default SESOI would label the literature's known effect "trivial" (Verified against the source)

**Evidence**
- SESOI = 2 points for every `overall_fit` contrast and for σ_A: `research/hypotheses.md:33–34`, `preregistration.md:349–357`, `pipeline.py:96`.
- The only LLM CV audit with an Arab group, Lippens 2024, reports an Arab penalty of **−1.41 points** (SE 0.21) on a 1–100 scale. The minority-group range is −0.96 to −2.42, and Turkish is −1.75. I confirmed these numbers against the arXiv v3 full text.
- Lippens's own translation to callbacks is a **discrimination ratio of 0.85 at a cutoff of 75**. That is a large selection-rate gap produced by a mean shift of about 1.4 points.
- `design_decisions.md:584–595` (D24) cites this evidence and then sets it aside ("set by practical meaning, not by prior effect estimates").
- The SESOI rationale ("below the resolution at which a single score would plausibly change a decision") ignores how cutoffs amplify small mean shifts. The same row also appeals to "shortlists by rank among similarly qualified applicants", which is exactly where a 1.4-point shift decides outcomes.

**Why it matters**
- Under this SESOI, a Lippens-sized Arab-vs-German gap would at best be labelled "trivial effect". If the CI is tight, it becomes "null (equivalence)" and the paper would report "no meaningful bias".
- "Meaningful within-Arab heterogeneity" would require the typical origin to deviate from the Arab mean by more than the whole documented Arab-vs-majority gap.
- Reviewers will say the design defines away the effect it studies. The SESOI must be fixed at Stage A (A2), so it has to be resolved now.

**Fix**
- Anchor the SESOI to a decision-relevant quantity fixed before the data:
  - either the fit-score shift that changes interview rates by the interview SESOI, using the fit-to-interview link the pipeline already estimates (`_fit_interview_link`), computed on NONE clones in the blind pilot;
  - or 1 point, with the four-fifths heuristic for interview.
- State the trade-off honestly. With a smaller SESOI, RQ2 equivalence becomes unreachable (M14) and those contrasts will mostly be "inconclusive". That is acceptable. Claiming nulls against a lenient SESOI is not.

### H5. There is no placebo or lexical floor for σ_A, and the Arab League set mixes in race (Verified gap; the interpretation is a design judgement)

**Evidence**

*The team's own assessment names the threat.* `research/novelty_assessment.md:113–121` names the "predictable combination plus noise" critique as the strongest threat. Its prescribed fix (row 1 of §7, `:132`, and check 4 of §9, `:164`) is a comparison against "the dispersion across replicate reference clones or placebo one-line changes". Placebo clones are still parked (`experimental_design.md:701`).

*The only floor tests the wrong null.* The within-CV label permutation (`src/hiringaudit/analysis/core.py`, `heterogeneity`) tests exchangeability of the 22 labels. That rules out *random* decoder noise. It does not rule out *systematic* idiosyncratic responses to any demonym string: token rarity, multi-token words, and unusual forms such as "Comorian", "Djiboutian" and "Mauritanian".

*The set includes non-Arab-majority members.* SOM, DJI and COM (`config/nationalities.yaml:20–21, 34`), plus SDN and MRT, are states whose salient association for a model may be sub-Saharan or Black African. The seven lowest-income origins in `config/country_covariates.csv` are SOM, SDN, COM, SYR, PSE, MRT and DJI. So a large σ_A, and a positive H1d slope, may be driven by anti-Black or conflict associations rather than by differentiation among Arab nationalities.

R1 (excluding SOM, DJI and COM) is only a robustness check.

**Why it matters.** A reviewer's first question will be: "Is 22-way spread among Arab labels larger than 22-way spread among *any* labels, and is it driven by the Horn of Africa?" As designed, the paper cannot answer either question. The headline contribution then collapses into "LLMs react to demonyms", which is already known (Venkit 2023, Salinas 2023).

**Fix.** This is the smallest change that answers the question, and the one the novelty assessment already recommends.
- Add 6–10 **placebo nationality signals**: non-Arab, non-benchmark, spread in word frequency, including some rare demonyms. Evaluate them in baseline IE only. At pilot scale that is about 1.9k extra calls per model per 10 levels.
- Pre-register a comparison of σ_A against σ_placebo, both debiased, with a CV bootstrap.
- Either make the 19-origin σ_A co-primary, or pre-register that the headline claim requires both the 22- and the 19-origin versions.
- Report σ_A net of the sub-region means as a secondary quantity.

---

## 4. MEDIUM — a reviewer would demand these

**M1. The positive-control gate is vacuous (Verified).**
- *Evidence.* `detected` is two-sided (`src/hiringaudit/analysis/descriptives.py:182`: `ci_high < 0 or ci_low > 0`), so a wrong-signed PC counts as detected and licenses "null: a single Arab category is adequate" (`src/hiringaudit/analysis/hypotheses.py:38–52`). The PC also removes the *only* qualification line, which will be detected trivially and says nothing about sensitivity at SESOI scale.
- *Fix.* Detect one-sided (PC < 0 and CI below 0). Call the PC a manipulation check, not evidence of sensitivity, since sensitivity is what H1b and TOST already establish. Optionally add a mild PC, such as removing one required skill.

**M2. The "R5 bounds" are not bounds (Verified).**
- *Evidence.* `src/hiringaudit/analysis/robustness.py:138–155` imputes *every* non-ok call as the same lowest or highest value. For Δ(a, b), a worst-case bound needs a's non-ok at the lowest value and b's at the highest, and the reverse. For σ_A, uniform imputation bounds nothing.
- *Why it matters.* R5 feeds the "robust" label, and it becomes co-primary if differential missingness rejects (SAP §9).
- *Fix.* Implement Manski-style bounds per contrast. For σ_A, either use nationality-specific extreme assignments (for example, maximise and minimise dispersion by a greedy assignment) or rename R5 "single-value imputation sensitivity" everywhere.

**M3. The H1b equivalence test and the σ_A CI assume sphericity (Suspicion).**
- *Evidence.* The noncentral-F inversion (`core.py`, `ncf_sigma_limits`, `p_equivalence_sigma`) assumes equal residual variance across the 22 columns. LLM score distributions are often heteroscedastic by label: hedging, refusals near the boundary, bimodality. The SAP simulations (§5.4) use a homoscedastic generator.
- *Why it matters.* "A single Arab category is adequate" rests entirely on this test.
- *Fix.* Report the residual variances per column and a Greenhouse–Geisser ε. Add a sphericity-free cross-check, such as a CV-bootstrap upper bound calibrated by simulation, and require both for an equivalence claim.

**M4. "Meaningful heterogeneity" is awarded below the SESOI, and H1a is nearly certain to reject (Verified by simulation).**
- *Evidence.* `research/hypotheses.md:112` and `preregistration.md:95` label "H1a rejects, H1b does not" as support for meaningful heterogeneity. That includes σ̂_A = 1.5 with an upper limit of 2.4.
- The fast power engine gives H1a power 1.00 at α/3 even at the pilot size (18 CVs) under the placeholder variances, and 0.81 under pessimistic ones (M14). The omnibus test is close to a formality.
- *Fix.* Label that case "heterogeneity present; size relative to the SESOI undetermined". Reserve "meaningful" for a 95 % lower bound above the SESOI (a minimum-effect test).

**M5. Manifest metadata is trusted but never validated (Verified: T1–T3).**
- *Evidence.* The runner builds trials from the manifest's `tier`, `pilot` and `occupation` (`src/hiringaudit/runner.py:136–139`; `src/hiringaudit/randomization.py:281–299`). These drive forced-choice same-tier pairing, the pilot subset and `qualification_tier` in the processed data. `validate_stimulus_set` never compares them with the base YAML. They are consistent today (I checked 0 mismatches in both sets), but a manifest edit would pass validation.
- *Fix.* Validate `tier == qualification_tier`, `occupation` and `pilot` against the YAML, plus `applicant_reference` and `base_cv_hash`.

**M6. The leak check is narrow, and README / prereg overclaim it (Verified: T4, T6, T8, T9, T12–T14, T19).**
- *Evidence.* `src/hiringaudit/validation.py:47–48` forbids only demonyms, country names and 13 cue words. Cities, religious or cultural terms, languages other than German, and citizenship vocabulary all pass. Job ads and the system and task prompts are never scanned. Compare README.md:113 and preregistration.md:271: "no demonym or other origin cue elsewhere".
- *Fix*
  - Whitelist German cities: every `city` must come from an allowed list.
  - Forbid the capital and major cities of all 26 countries; "citizen", "citizenship", "passport", "residence permit", "naturalis", "refugee"; religious calendar and food terms; and non-German language names.
  - Run `find_leaks` over the job ads, the system prompt and every task template.

**M7. Transport failures become permanent missing cells (Verified by reading the code).**
- *Evidence.* `existing_record_ids` (`runner.py:335–345`) counts `api_error` records as done (`runner.py:575–581`). A vLLM restart writes at least 25 permanent `api_error` cells per session (`max_consecutive_api_errors`), and more with 8 workers. These cells break forced-choice quads and inflate the missingness outcome (Discrepancy 16).
- *Fix.* On resume, redo record_ids whose only records are `api_error`. Let the parser keep the last non-`api_error` record per record_id, counting attempts across sessions.

**M8. The technical stop rule is not implemented (Verified).**
- *Evidence.* Prereg §7 (preregistration.md:336–338) and ED §7 stop a model at more than 10 % non-ok in its first 5 % of calls. The runner only aborts on 25 *consecutive* `api_error` records.
- *Fix.* Implement the rule as a nationality-blind monitor in `run_experiment`, or change the documents.

**M9. Within-Arab confounds are not constant across the 22 origins (Suspicion, with design evidence).**
- *Evidence*
  - The missing native-language line is congruent for Somali-, French- and Comorian-speaking origins (SOM, DJI, COM, part of MRT) and incongruent for Arabic-speaking ones.
  - GCC nationals in warehouse and retail jobs are implausible (threat C6).
  - Income is collinear with race (Horn of Africa) and with conflict: SYR, PSE, SDN, SOM.
  - H1d is motivated by the Stereotype Content Model (`research/hypotheses.md:128–171`), but a positive slope would be equally predicted by anti-Black or anti-refugee associations.
- *Fix.* Pre-register H1d as ecological and descriptive of structure, not as a test of status → competence. Add pre-registered sensitivity slopes with sub-Saharan and fragile-and-conflict-state (FCS) indicators. Report the occupation-specific slopes that the team already plans.

**M10. "POL is the cleanest comparator" contradicts the design (Verified).**
- *Evidence.* The claim appears at preregistration.md:138–141, `research/hypotheses.md:206` and `research/experimental_design.md:159`. Poland is EU (free-movement right to work), Christian-majority and European. The same paragraph says TUR "matches the Arab set on non-EU citizenship".
- *Fix.* Drop "cleanest". Describe Ā–TUR as the closest match on non-EU legal status, and Ā–POL as foreign but EU.

**M11. Remaining researcher degrees of freedom after seeing data (Verified).**
- The H1d estimator is still open: REML vs design-based, which the SAP's own simulation shows can give p < .001 vs p = .08 (preregistration.md:518–526).
- The processed tables are **re-parsed from raw with the current parser** on every `parse` (`src/hiringaudit/parse_outputs.py:93–96`). A parser tweak after unblinding silently changes the analysed sample. `PARSER_VERSION` is logged but not frozen.
- `r4_processed_dir` lets any greedy run be attached after the fact.
- The Mistral model sits in the main config unpiloted (Discrepancy 10).
- The near-duplicate threshold is "[TO SET]".
- *Fix.* Freeze all of these at Stage A or B in the preregistration, including a parser code hash. Make `parse` refuse a `PARSER_VERSION` different from the one recorded in the run manifest unless it is flagged as exploratory.

**M12. The evaluation-awareness and culture-fit flags collide with CV vocabulary (Verified).**
- *Evidence*
  - `mentions_testing` matches bare "test", "tested", "testing" and "fair" (`config/text_coding.yaml:95–106`).
  - `mentions_culture_fit` matches "integrate", "integration" and "background" (`:74–76`).
  - 8 of 48 CVs contain "test" ("unit and integration tests", "Software Test Engineer", "ISTQB Certified Tester"). Four contain "integrat"; one contains "background in IT support".
  - P11's decision rule ("if high, reconsider framing") will fire on software-developer reasons, and software developer is one of the three pilot occupations.
- *Fix.* Use phrase patterns instead ("this is a test", "being evaluated", "bias test", "fairness (test|evaluation)", "cultural fit") and validate them on the hand-coded sample.

**M13. Forced-choice wording variants are confounded with nationality (Verified).**
- *Evidence.* Per nationality, the variant counts are **1–8** in the pilot and **12–19 of 48** in the main study. This contradicts `experimental_design.md:491` ("balanced over nationality pairs"). The Bradley–Terry model has no variant × nationality term.
- *Fix.* Rotate variants within each Hamiltonian cycle with a Latin scheme so that each level gets 1/3 of its quads per variant.

**M14. Power and sizing (Verified by running the script).**
- *Placeholder values*: H1a and H1b power are 1.00 from 6 CVs per occupation × 3 occupations. The sizing will be driven entirely by the per-origin SE target and TOST, and the documents should say so.
- *Pessimistic values* (σ_ατ = 6, σ_ατκ = 3, σ_ε = 10) at the main size (8 CVs per occupation × 6, r = 2): H1a and H1b power 1.00, but **TOST power for Δ(Ā, DEU) is 0.12**, and the mean SE(δ̂) is **1.05**, which misses the ≤ 0.8 target. The authoring ceiling of 16 per occupation may therefore bind.
- The script defaults to `--n-sims 40`, a Monte Carlo SE up to 0.08, for a ≥ 0.80 decision (`analysis/power_analysis.py:223`).
- `upper` is the maximum of the point estimates (`pipeline.py:834–838`), and ρ_ε comes from the pooled mean (Discrepancy 14, confirmed).
- *Fix*
  - Use n_sims ≥ 2,000 with the fast engine for the Stage B decision.
  - Compute real 80 % upper limits, for example with a CV bootstrap of each component.
  - Plan with ρ_ε = 0.
  - Pre-state what happens if the TOST target is unreachable at the ceiling: report the MDE, and do not change the SESOI.

**M15. A missing wording shifts the per-CV mean (Verified by reading the code).**
- *Evidence.* `Cell.Y = _nanmean(Yk, -1)` (`src/hiringaudit/analysis/core.py:95`). If one wording loses all its replicates for a (CV, nationality) cell, that cell's mean uses only two wordings. Wording main effects then leak into δ(n) exactly when non-ok is nationality-dependent.
- *Fix.* Impute additively per CV × wording before averaging, as `_impute_additive` already does for the variance components, or fit wording fixed effects.

**M16. The preregistration has no timestamp (Verified).**
- *Evidence.* The venue is "OPEN: internal file only, OSF, or AsPredicted" (preregistration.md:10).
- *Why it matters.* An untimestamped Stage A carries no evidential weight with reviewers.
- *Fix.* Register Stage A on OSF or AsPredicted before the pilot.

**M17. The scope of the models limits FAccT relevance (Suspicion).**
- *Evidence.* The models are 8–12B open-weight models, plus an unpiloted 24B model. No deployed recruiting-grade model is included.
- *Fix.* Pilot and include one pinned API model if the budget allows. Otherwise scope every claim to "open-weight 8–24B models under this template".

---

## 5. LOW — polish

- **L1.** README.md:195–197 says the analysis loader rejects the mock tables because of the `arm` key. It does not: the analysis runs end to end (Verified). The README test command (line 204) also omits the analysis tests; plain `pytest -q` runs all 132.
- **L2.** An unknown nationality code in the manifest crashes the validator with a `KeyError` traceback (`src/hiringaudit/validation.py:286`) instead of a clean error. It is reported at line 216 but then used unguarded.
- **L3.** Nothing checks that `positive_control_line` is the line carrying the requirement; T22 passed. Add `positive_control_line == education_line(education[0])`.
- **L4.** Parser behaviour (Verified with probes):
  - The first-JSON-object rule keeps a draft over a later correction.
  - The refusal regex misses "I refuse", "I'm not comfortable" and "As a language model"; these become `malformed_json`.
  - "Yes", "80", 80.5 and extra keys are schema violations. Expect model-specific spikes in non-ok at P1.
  - Consider a logged, non-coercing "near-miss" category for diagnostics only.
- **L5.** Mock and real runs are separated only by the run-id convention (`.gitignore`, README.md:177). Enforce in code that mock runs must use a `mock` prefix and real runs must not; a real run with that prefix would be git-ignored and its evidence lost.
- **L6.** P3 in `scale_use` pools the adequate and borderline tiers, which hides a ceiling within one tier. Report P3 per tier.
- **L7.** CV dates run to 09/2026, and certificates are dated 2026. That is after every piloted model's training cutoff, and "future" dates may read as synthetic. The dates are constant across clones. Consider a `reference_date` of 2024 or earlier.
- **L8.** `ETHICS.md:46–49`: AGG §1 does not list nationality, and Race Equality Directive 2000/43/EC Art. 3(2) excludes differences of treatment based on nationality. As written, the sentence is probably wrong, not merely unverified.
- **L9.** The three wordings share the same output block, job ad and CV template. "Robust across wordings" (R3) is therefore weak evidence of robustness to prompts (compare Sclar et al. 2024). Scope the claims to this template.
- **L10.** When `RunAborted` fires inside `handle`, the other completed futures in the same `finished` batch are dropped (runner.py, the ThreadPool loop). They are redone on resume, so this costs compute but does not corrupt data.
- **L11.** The reverse-keyed principle items are blatantly discriminatory, so E_m ≈ 1 is almost certain and the "gap" label in SQ1 is nearly automatic. This is fine as a descriptive result, but say so.
- **L12.** `summary.md` records package versions but no git commit or code hash for the analysis code.
- **L13.** The literature matrix has small nuances (from the citation check):
  - `kamruzzaman2024subtler` understates that the nationality effect is null for 2 of 4 models in one direction.
  - `lippens2024computer`'s "smaller than human benchmarks" does not hold for Turks against the Belgian benchmark (0.86 vs 0.85).
  - `chen2026beyond`'s "Australia" is inferred, not stated.
  - `koopmans2019taste`'s "about 100 applications per small group" is unverified.
- **L14.** Possible near-miss prior work to add: Hoffmann et al. 2026 (arXiv:2601.11379; freelance platform, Arabic-sounding names as one group) and Nakano et al. 2024 (arXiv:2409.12544; location strings swapped in GitHub profiles). The full text of Bilon 2025 is still unresolved.
- **L15.** Minor inconsistencies between documents:
  - The README says every request sends T = 0.7; the greedy arm sends 0.
  - The `vllm serve` flags differ between `models.yaml` and the README (`--seed 0`).
  - `power_analysis.py` defaults to `--n-models 5`, while the configs list 3–4 models.
  - The prereg states H1a's null as a weak null; the test is exact only for the sharp null (`hypotheses.md` says this correctly).

---

## 6. Discrepancy audit and novelty check

### The preregistration's 20 listed discrepancies

I checked 1, 2, 9, 10, 11, 12, 13, 14, 18 and 19 against the source files. All ten are accurately described:
- 9: ED §6 "all 300 pairs × 1 quad" vs 100 pairs in the config.
- 12: 13 vs 15 principle items.
- 13: `expected_answer` is present in `schemas.py:94`.
- 14: `upper` is the maximum of point estimates.

The others are plausible and I found no contradiction.

### New discrepancies found in this review

- README analysis status (L1).
- Validator claims vs behaviour (M6).
- Technical stop rule not implemented (M8).
- Variant balance claim (M13).
- "POL cleanest" vs "TUR matches on non-EU citizenship" (M10).
- Blind-by-default claimed vs `blind: False` (H1).
- D24 reasoning vs the SESOI rationale in `hypotheses.md` (H4).
- ETHICS legal framing (L8).
- The small items in L15.

### Novelty (Task B of the citation check)

The search covered the arXiv API, OpenAlex, the web, and Semantic Scholar, which was mostly rate-limited. **No study found varies more than one individual Arab country in an LLM hiring or screening decision.** The closest are:
- Lippens 2024: a pooled Arab name group;
- Mao & Zhao 2025: Sudan, Somalia and Iraq, in immigration decisions rather than hiring;
- MENAValues: 14 Arab states, on values rather than decisions;
- Salinas 2023: Jordan only;
- Huijzer & Chen 2025: Moroccan only.

C3 in `novelty_assessment.md` stands as absence of evidence. The claim is honest as written. Its defensibility against the "Lippens plus MENAValues plus noise" objection depends on H5.

---

## 7. Checked and found sound

- **Clone integrity.** Byte-exact line comparison against the DEU clone; NONE drops only the Nationality line; positive control = NONE minus the designated line; hashes and diffs regenerated and checked. The validator catches whitespace, zero-width characters, CRLF, path swaps, DEU edits and missing clones. All 2 × 1,296 clones pass.
- **Reproducibility of stimuli.** Base CVs and clone sets regenerate byte-identically from seed 20260929. `.gitattributes` pins LF line endings for the hashed trees.
- **No origin cues in the current materials.** Job ads, CV pools, prompts and applicant references contain no nationality cue (checked by grep for cities, religious, citizenship and language terms). Applicant references are random per (occupation, position). No hidden field (tier, `tier_evidence`, moderator codes) is rendered into a prompt. I inspected a full rendered forced-choice prompt and CVs from all three pilot occupations and all tiers.
- **Prompt interventions.** `neutrality_k` = `baseline_k` + the exact paragraph immediately before the output block, for each k, for both the IE and FC templates; one shared output block across the wording variants.
- **Randomisation.** Seeds are nationality-free (common random numbers across clones). Execution order is a seeded shuffle within each model. Trial and record ids are deterministic, with a uniqueness check. The FC quad balances CV slot and position by construction. The main FC design has each level in 48 quads, 8 per occupation and 16 per tier, and is connected.
- **Raw data handling.** Append-only JSONL. Corrupt trailing lines are reported, not dropped. The parser rejects duplicate record_ids. Retries cover transport errors only, and malformed or refused outputs are never re-sampled.
- **No pseudo-replication.** The base CV is the unit. Replicates are averaged within stimulus, then over wordings. The analysis applies the `clone_type == counterfactual` and `arm == primary` filters, so positive-control rows never enter the NONE cell.
- **Statistics**
  - Occupation-stratified t with Welch–Satterthwaite df; the TOST formula is correct.
  - The debiased σ̂²_A in code equals ((J−1)/J)(MS_nat − MS_res)/I, as in SAP §5.2.
  - The within-CV permutation recomputes the full statistic on every permutation. It is valid under the sharp null, and the common-random-number structure is symmetric across labels, so exchangeability holds.
  - The noncentral-F inversion is correct under its model (but see M3).
  - Holm adjustment is applied within the declared families.
- **Blind mode, when invoked.** `python -m hiringaudit.analysis --blind` writes only design, status, positive-control, tier, scale-use, FC-position, principle-probe and variance-component tables, with no per-origin output (checked on the mock).
- **Mock labelling.** Mock runs carry `is_mock` on every record, "SYNTHETIC MOCK DATA - NOT RESULTS" in the parse summary, `summary.md` and every table, and the analysis labels any input with a mock row as mock.
- **Citations.** 29 high-relevance entries were verified against arXiv, Crossref and full texts. All exist, the metadata matches, and the main results are fairly described (nuances in L13). Citation keys are consistent across all documents, `references.bib` and `literature_matrix.csv`: 123 keys, no orphans.

---

## Appendix: reproduction recipes

### Validator tamper

```bash
T=$(mktemp -d); cp -r config prompts stimuli pyproject.toml "$T"/
# e.g. T4: replace "city: Mainz" with "city: Beirut" in "$T"/stimuli/base_cvs/software_developer/swdev_01.yaml
PYTHONPATH=src python -m hiringaudit --root "$T" generate-stimuli --stimulus-set v1 --force
PYTHONPATH=src python -m hiringaudit --root "$T" validate-stimuli --stimulus-set v1   # -> VALIDATION PASSED
```

### Silent mixing on resume (H3)

```bash
PYTHONPATH=src python -m hiringaudit --root "$T" run --config config/mock.yaml --quiet --limit 200
# edit "$T"/config/jobs.yaml (the software developer "At least 3 years" line) and the mock `revision` in "$T"/config/models.yaml
PYTHONPATH=src python -m hiringaudit --root "$T" run --config config/mock.yaml --quiet --limit 200   # no refusal
# responses.jsonl: two model_revision values; prompts.jsonl: two job-ad versions
```

### Unblinded pilot output (H1)

```bash
PYTHONPATH=src python -m hiringaudit --root "$T" parse --run-id mock_pipeline_test
PYTHONPATH=src python -m hiringaudit --root "$T" analyze --run-id mock_pipeline_test
# summary.md: "blind mode: False"; tables/origin_deviations.csv written
```

### Tier evidence (H2)

Read `tier_evidence.total_experience_months` in `stimuli/base_cvs/*/*.yaml`, and the adjacent jobs in `retail_03`, `retail_06`, `swdev_03`, `swdev_06` and `whse_06`.

---

## Re-verification (round 2)

Date: 2026-09-30. I re-checked the code fixes adversarially. As instructed, the research documents were not re-checked. Everything ran in temporary copies (`--root <tmp>`, run ids starting with `mock`). No model was called. No committed file was touched; only this section was appended to this file.

### Regression checks

| check | result |
|---|---|
| `PYTHONPATH=src python -m pytest -q` | **222 passed** (88 s) |
| `validate-stimuli` | `[v1] OK: 1680 clones`, `[v1_native_german] OK: 1680 clones` (48 × (26 + 8 placebo + PC)), PASSED |
| `plan` pilot | 10,807 calls per model (baseline 4,212 + placebo 1,296 + PC 162 + neutrality 4,212 + FC 400 + principle 525); 32,421 in total |
| `plan` main | 26,637 calls per model (34,125 for qwen3-8b); 114,036 in total |
| Clean mock end to end (fresh temp root) | `run` (3,050 records) → `parse` → `analyze` (blind, into `results/<run>/blind`) → `analyze --unblind` (mock; log redirected to temp; 48 tables into `results/<run>/unblinded`). All labelled "SYNTHETIC MOCK DATA". |
| Validator tamper battery (original 24 cases plus 9 new) | **31 of 33 caught.** Not caught: T23 (applicant reference APP-0966; trivial) and new T26 (an unrelated job retitled "Senior Sales Associate" while keeping its kitchen bullets; title–bullet coherence is guaranteed by the generator but not validated). My first T30 did not apply (the text spans YAML lines); redone with a matching edit, "Istanbul" and "Casablanca" in a job ad are caught. |

### HIGH items

**H1 — PARTLY FIXED.**

What now works:
- `analyze` is blind by default and writes to `results/<run>/blind`.
- Unblinding real-labelled data is refused. I used the mock tables with `is_mock` set to False; the refusal cites a missing `config/prereg_freeze.json`.
- A direct `sesoi` override is stamped "EXPLORATORY OVERRIDE" in `summary.md` and in every table.
- Writing blind output into an unblinded directory is refused.

What still does not work (all verified):
- **(a) Two lines of `--config` bypass the gate.** The operational keys `repo_root: <tmp dir with a fake preregistration.md + matching prereg_freeze.json>` and `unblinding_log: <tmp file>` unblinded the real-labelled data. The run wrote `origin_deviations.csv`, `heterogeneity.csv` and `contrasts.csv`, reported "freeze valid: True", and logged outside the repository. Only the prereg SHA in `summary.md` betrays it.
- **(b) An alternative confirmatory file is not flagged.** `confirmatory_config: <copy with sesoi.overall_fit 3.0>` produces "Overridden confirmatory keys: none" and no banner. Only the path and SHA-256 differ.
- **(c) Anyone can freeze a draft.** A freeze only has to match the current hash of `preregistration.md`, and the freeze file does not have to be committed.
- **(d) `--root` is not passed through.** The main CLI does not pass `--root` to `repo_root`, so the gate and the log refer to the package repository, not the data root.
- **(e) Stale tables survive.** If `summary.md` is missing, for example after a crashed unblinded run, a blind run into the same directory proceeds and leaves 5 per-origin tables behind (LOW).
- **(f) Raw traceback.** In the main CLI an `UnblindingError` surfaces as a Python traceback (LOW).

*Fix.*
- Remove `repo_root`, `unblinding_log` and `confirmatory_config` from the keys users can set in a run config. Alternatively, when any of them is used, force an EXPLORATORY/TEST banner and refuse to unblind non-mock data.
- Treat a confirmatory-file hash that differs from the repository file as an override.
- Require `prereg_freeze.json` and `preregistration.md` to be committed at HEAD with the stated hash.
- Pass `paths.root` as `repo_root`.

**H2 — VERIFIED FIXED** (with one suspicion).

In all six occupations:
- strong CVs have ≥ req + 36 relevant months (76–109);
- adequate CVs have req + 1 to 20 months and no unrelated job;
- borderline CVs are 12–18 months short, with total experience below the minimum adequate total (for example retail: borderline 7/11 relevant and 17/19 total, against adequate totals of 25–32).

The unrelated roles are now coherent (kitchen assistant, delivery driver, restaurant server, and so on), and profiles match titles. The validator recomputes months from the dates and enforces the ordering: T17, T24, T25 and T25b are caught. The reference date is 2024-06, and T27 (a date after it) is caught.

*Suspicion.* In the 24-month jobs (retail, warehouse, administration), borderline CVs have only 7–11 relevant months, 29–46 % of the requirement. That may land at an interview floor rather than on the borderline. P3 and P4 in the pilot must show it. The job ads also changed (retail and warehouse now require 2 years).

**H3 — VERIFIED FIXED, with one residual.**

Verified:
- On resume, the run is refused after editing `jobs.yaml` ("input_files (jobs.yaml)"), `principle_items.yaml`, or a model revision ("models (mock)").
- The default run id changes with its inputs (`__f7654e4c` → `__f4c23a9f`).
- `--allow-real-calls` is refused while the revision is null and git state cannot be verified. No call is made.
- Processed tables carry `model_revision`, `prompt_sha256` and `user_prompt_version`. The analysis refuses a mixed revision ("model_alias with more than one model_revision") and mixed prompt versions.

*Residual (MEDIUM-LOW).* The dirty-tree guard checks git status of the **data root**, not of the code that runs. A clean git copy of config/prompts/stimuli, with a pinned revision, passed `preflight_real_calls` while `src/hiringaudit/` in the repository is untracked. *Fix:* also check the package's own directory and record a code hash.

Note that the whole project is still untracked in git, so a real run is correctly refused today. Commit it before the pilot.

**H4 — VERIFIED FIXED (code and config).** `config/analysis_confirmatory.yaml` sets SESOI to 1.0 fit point, h1d to 1.0, interview to 5 pp and FC to ±0.2007. `power_analysis.py` reads it. `sesoi_is_final: false` is still an Stage A team decision, and the documents are pending.

**H5 — VERIFIED FIXED, with a framing note.**

Verified:
- There are 8 placebo nationalities (URY, BOL, SYC, MWI, MDV, NPL, MYS, KHM), validated like other clones (T28, T29 and T31 caught).
- They appear only in baseline, primary arm, counterfactual IE: 1,296 / 2,304 / 288 calls per model in pilot / main / mock, and no FC, neutrality, robustness arm or positive control.
- In the unblinded output they appear **only** in `placebo.csv`, never in origin, contrast, BT or coefficient tables.
- H1e (σ_A vs σ_placebo, shared CV bootstrap) is computed.
- The headline RQ1 label requires the 22- and 19-origin labels to agree (`rq1_headline`).

*Note.* The headline label does not depend on H1e, and H1e is two-sided with only 8 placebo levels. Any claim that the spread is Arab-specific should require H1e to reject with σ_A > σ_placebo. That can be settled in the documents.

### MEDIUM items

| item | status | evidence |
|---|---|---|
| M1 | VERIFIED FIXED | one-sided `manipulation_check_passed` (effect < 0 and one-sided upper limit < 0), `descriptives.py:185–193` |
| M2 | VERIFIED FIXED, **new issue** | Manski bounds for Δ; σ_A check renamed SVI. With `manski_support: logical` (0/100), mock data with 3–4 % non-ok give Δ(Ā,DEU) = 2.74 [2.61, 2.87] in the main analysis, but Manski scenarios of −2.9 [−7.4, 1.6] and 6.9 [2.8, 11.1]. Every Δ is then "not robust", while σ_A faces only SVI (see N3). |
| M3 | VERIFIED FIXED | `sf_upper95`, `gg_epsilon`, residual variance range; equivalence requires noncentral-F **and** the calibrated residual-bootstrap test. The bound is computed for baseline only and uses complete-case rows. |
| M4 | VERIFIED FIXED | "meaningful" requires the minimum-effect test (lower bound above the SESOI); otherwise "heterogeneity present; size … undetermined" (seen in the mock output) |
| M5 | VERIFIED FIXED | T1–T3 and T31 caught |
| M6 | VERIFIED FIXED | whitelist of cities; forbidden cities, religious, citizenship and language terms; job ads and prompts scanned (T4, T6–T9b, T12–T14, T19, T30 caught) |
| M7 | VERIFIED FIXED | resume re-attempted 8 `api_error`-only calls (attempts 1 → 2); parse de-duplicates 3,058 raw records to 3,050. Deterministic errors are re-attempted in every session with no cap (LOW). |
| M8 | VERIFIED FIXED, new issue | at a 30 % malformed rate: "TECHNICAL STOP … 32.0 % non-ok in its first 153 calls", which persists on resume. `api_error` counts as non-ok, so a transient outage can permanently stop a model whose calls would otherwise be retried (N6). |
| M9 | PARTLY FIXED | sub-Saharan sensitivity slopes (`wb_sub_saharan` in the covariates); FCS is not used (not available from the API); framing is in the pending docs |
| M10 | NOT RE-CHECKED | documentation |
| M11 | PARTLY FIXED | the parser fingerprint is frozen (`parse` REFUSED after editing `text_coding.yaml`; `--exploratory` writes `<run>__exploratory`); the H1d estimator is fixed in the confirmatory config; `r4_processed_dir` is removed. **But** `run_analysis` ignores `parse_mode: exploratory` / "EXPLORATORY PARSE" in `parse_summary.json`: the outputs carry no stamp. Mistral is still in the main config and unpiloted. |
| M12 | PARTLY FIXED | the CVs' own text triggers no flag (0 hits over 48 NONE clones). But recall collapsed: "This looks like a test of whether I am biased by nationality", "I suspect this is an evaluation of bias", "good team fit" and "integrate well into the team culture" are **all unflagged** (N4). |
| M13 | VERIFIED FIXED | variants per nationality: main exactly 16/16/16 of 48; pilot 2–3 of 8 |
| M14 | VERIFIED FIXED (code) | `--n-sims` default 2000, ρ_ε planned at 0, `variance_components_upper80.csv` written; I did not re-run the power grid |
| M15 | VERIFIED FIXED | additive imputation within CV before averaging over wordings (`core.py` `Cell.Y`); note "160 … cells imputed" in the mock output |
| M16 | NOT VERIFIABLE | process (registry timestamp) |
| M17 | NOT RE-CHECKED | scope / documentation |

### New issues

- **N1 (MEDIUM).** The H1 bypass through the operational config keys: (a), (b), (c) and (d) above.
- **N2 (MEDIUM-LOW).** The dirty-tree preflight checks the data root, not the code location (H3 residual).
- **N3 (MEDIUM-LOW).** Manski bounds with logical support are about 10 points wide at realistic non-ok rates (2–5 %), against a 1-point SESOI. "Robust" becomes unreachable for Δ, so the label carries no information. *Fix:* pre-register observed support, report the bound width, or use Manski only when the differential-missingness test rejects, as originally planned.
- **N4 (LOW-MEDIUM).** The recall of `mentions_testing` and `mentions_culture_fit` now fails obvious phrasings, and P11 depends on it. *Fix:* use broader patterns that do not collide with CV vocabulary (for example `test\w* (of|for|whether).{0,40}(bias|nationalit)`, `evaluat\w+ (of|for) (bias|fairness)`, `team fit`, `integrat\w+ (well )?into`), and validate them on the hand-coded sample.
- **N5 (LOW-MEDIUM).** The analysis does not stamp outputs built from an exploratory re-parse.
- **N6 (LOW).** The technical stop rule counts transport errors.
- **N7 (LOW).**
  - T26: title–bullet coherence is not validated.
  - `--root` is not propagated to the analysis; the default unblinding log goes to the package repository (`results/unblinding_log.jsonl` there already holds entries from temp-root runs).
  - The main CLI shows a traceback on `UnblindingError`.
  - Stale per-origin tables survive when `summary.md` is missing.
  - `api_error` re-attempts are uncapped.

### Updated verdict

**Minor revision. The design is fit for the pilot once N1 and N2 are closed and the code is committed and tagged.**

- All five HIGH findings are fixed in code except H1. H1 works on every default path but can still be bypassed deliberately and silently through three configuration keys.
- Of the MEDIUM findings: 11 are verified fixed (M1–M8, M13–M15), including M2 and M8, which each introduced a new issue. Three are partly fixed (M9, M11, M12), and three were not re-checkable (M10, M16, M17).
- None of the new issues corrupts data. N1 and N2 undermine the provenance and blinding guarantees the paper will rely on. N3 and N4 make two reported quantities uninformative.
- The SESOI remains an open team decision at Stage A.
