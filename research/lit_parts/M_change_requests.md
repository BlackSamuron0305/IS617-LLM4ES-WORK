# Methodology change requests (v0.1, 2026-09-30)

For the lead to reconcile against `research/design_contract.md`,
`config/nationalities.yaml` and the occupation list. Nothing below has been
edited in the contract, configs or code. Details: `research/experimental_design.md`
(design §), `research/hypotheses.md`, `research/threats_to_validity.md` (threat id).
**OPEN DECISION** = the team's call; methodology cannot settle it.

## High

1. **CR-1 — Name the primary outcome.** `overall_fit` (baseline) is primary, `interview` the key secondary, `confidence` exploratory (contract §5). *Reason:* confirmatory tests and the preregistration need one primary outcome. **High.**
2. **CR-2 — Fix SESOIs before the pilot.** Proposed: 2 points on `overall_fit` (contrasts and σ_A), 5 pp on `interview`, 0.55/0.45 in forced choice. *Reason:* equivalence tests, and so every null claim, need bounds set in advance. **High; the values are an OPEN DECISION.**
3. **CR-3 — Add K = 3 wording variants per task prompt,** crossed with nationality within base CV for IE (replacing pure R = 5 repeats with K × r; pilot r = 3), balanced across quads for FC; log `prompt_variant`; `neutrality_k` = `baseline_k` + the same paragraph. *Reason:* with one wording every result depends on it and prompt-specific effects cannot be detected (I5). **High.**
4. **CR-4 — Retry only transport/API errors.** Malformed, empty or refused outputs are terminal outcomes and are never re-sampled; `attempts` counts transport retries only. *Reason:* re-sampling selects on the outcome, possibly differently by nationality (I8). **High.**
5. **CR-5 — Randomise execution order** over all cells within a model (seeded shuffle), run each model's conditions in one contiguous window, and log `execution_index`. *Reason:* otherwise drift, batching and cache effects can line up with nationality (I2). **High.**
6. **CR-6 — Pin model provenance:** HF commit SHA, tokenizer/chat-template hash, vLLM version, dtype, quantisation, GPU type (and dated snapshots for any API model) in manifest and raw record (`model_revision`). *Reason:* `model_id` alone does not identify weights; needed for reproducibility and drift control (I3). **High.**

## Medium

7. **CR-7 — Add a positive-control clone per base CV:** the `NONE` clone with the line carrying one designated must-have removed; extend the validator. *Reason:* shows the design detects a one-line job-relevant change, so nulls can be defended and effects given a yardstick. **Medium.**
8. **CR-8 — Add constant personal-details fields** (driving licence; availability / notice period) around the nationality line. *Reason:* a lone `Nationality:` field is a test cue (C5). **Medium.**
9. **CR-9 — Exclude `NONE` from forced choice** (25 levels, 300 pairs); each nationality pair assigned to c ≥ 2 CV pairs, balanced over occupation, tier, CV slot and position. *Reason:* one-sided line presence makes nationality the most salient difference; c ≥ 2 avoids tying a pair to one CV pair. **Medium.**
10. **CR-10 — Uniform sampling settings:** T = 0.7, top_p = 1.0, top_k off for every model; add a greedy (T = 0) robustness run for baseline. *Reason:* the contract logs top_p but does not fix it; model-specific defaults would confound family with decoding (S4). **Medium.**
11. **CR-11 — Redesign the principle probe:** ≥ 10 statement items (half reverse-keyed) plus 2–3 control items, 7 contexts, r = 5, fresh context, same system prompt; schema `{"answer": yes|no, "agreement", "reason"}` replacing `endorses_neutrality`; `principle.csv` gains `item_id`, `keying`, `item_type`. *Reason:* acquiescence and blanket "no" answers otherwise pass for endorsement (C8). **Medium.**
12. **CR-12 — Swap `sales_representative` for a low-skill, high-contact role** (e.g. retail sales associate) and code skill / contact / trust / fit in `config/jobs.yaml`. *Reason:* covers all four skill × contact corners; the current set cannot separate them (E3). **Medium; OPEN DECISION; must be settled before pilot stimuli are authored.**
13. **CR-13 — Add a language-line robustness arm:** "German: native speaker" in every clone, baseline, 1–2 models. *Reason:* "C2" for a German national makes the reference clone incongruent and biases all Δ(·, DEU) (C4). **Medium; whether to make it the primary is an OPEN DECISION.**
14. **CR-14 — Add `config/country_covariates.csv`:** WDI `NY.GDP.PCAP.PP.KD` (2022, with the fallback rule), World Bank income group, plus exploratory FCS status and Destatis resident counts; source, edition and retrieval date recorded; frozen before main data; no values from memory. *Reason:* needed for the pre-registered status-gradient hypothesis H1d. **Medium.**
15. **CR-15 — Blind the pilot:** the pilot analysis outputs variance components, manipulation checks and diagnostics only, and no per-origin means until the preregistration is frozen. *Reason:* keeps the pilot from shaping hypotheses or contrasts. **Medium.**

## Low

16. **CR-16 — CV allocation:** pilot 6 per occupation (2/2/2) instead of 4 (1/2/1); main default 8 as 2/4/2. *Reason:* with 1/2/1 only the adequate tier has a same-tier FC pair, and the tier check rests on one CV per tier. **Low.**
17. **CR-17 — Derive seeds from (model, condition, base CV, variant, repetition), not from nationality.** *Reason:* clones then share random streams (common random numbers), which makes contrasts more precise without bias. **Low.**
18. **CR-18 — Processed-table fields:** add `prompt_variant`, `execution_index`, `seed`, `model_revision`, `clone_type`, `mentions_testing` and an inferred-gender pronoun flag. *Reason:* needed for R3, drift checks, the positive control and the evaluation-awareness probe. **Low.**
19. **CR-19 — Labelling:** outputs and figures say "Arab League member-state nationalities", not "Arab applicants". *Reason:* the criterion is political-institutional and the signal is nationality, not ethnicity (C1, E1). **Low.**
20. **CR-20 — Notes in `nationalities.yaml`** for Palestine (recognition and administrative recording in Germany [VERIFY]), Syria (December 2024 change of government; training vintage) and Sudan (war since 2023). Interpretation notes only, no design change. *Reason:* these signals carry distinctive, time-varying associations (C9). **Low.**
21. **CR-21 — Name the run-config files** (e.g. `config/experiment.yaml`, `config/models.yaml`) in the contract. *Reason:* `variables.md` needs a single place of definition for models, decoding and repetitions. **Low.**
22. **CR-22 — Optionally add one non-EU, non-MENA benchmark** (recommended: Ukrainian). *Reason:* it separates "non-EU / refugee-associated" from "Arab / MENA", which the current three benchmarks cannot (E2). **Low; OPEN DECISION.**
23. **CR-23 — Optional system-prompt sentence** saying that names and contact details are replaced by an applicant reference; test it in the pilot (P11). *Reason:* explains the missing name without cueing a bias test (C3, C5). **Low.**
24. **CR-24 — Job ads state that English-language applications are accepted.** *Reason:* makes English CVs plausible for every occupation (E4). **Low.**

## Other OPEN DECISIONS (not contract changes)

- Model set: at least 3 families at roughly matched size, pinned revisions; whether budget allows one proprietary API model.
- Authoring ceiling for base CVs per occupation (proposed 16), which caps the main-study N.
- Whether a model with persistently > 10 % unparseable output stays in the main set.
- Preregistration venue (internal file only, or OSF / AsPredicted timestamp).
- Timeline: pilot by about 20.10, preregistration about 27.10, main collection before the 11–12.11 midterm.
