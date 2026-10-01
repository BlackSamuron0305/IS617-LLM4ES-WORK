# Response to the adversarial review

Version 0.3.1, 2026-10-01. Internal research document (integration methodology). Maps
every finding of `research/adversarial_review.md` — round 1 (H1–H5, M1–M17, L1–L15) and
the round-2 re-verification (N1–N7) — to its status in the implemented state. Statuses
were checked against the code, configs and fresh `validate-stimuli` / `plan` runs on
2026-09-30 and again after the setting change on 2026-10-01, not taken from summaries.

**Setting change after the review (2026-10-01, user request; contract V1–V10; design
decisions D44–D47).** The review was written for the German setting. Since 2026-10-01:
(1) every CV is set in one of eight Arab League base countries (ARE, SAU, QAT, KWT, OMN,
BHR, JOR, EGY; 3 same-tier CV pairs each), with employers, real local institutions and
the job ad in that country; nothing German remains (the Rhine-Neckar same-region rule is
superseded); (2) the clone whose nationality equals the base country is a host national;
primary estimates adjust for one common host effect, which is reported descriptively,
and the sensitivity check HX (host clones excluded) is required for the "robust" label
(SAP v0.5 §4a); forced-choice pairs share a base country and Bradley–Terry has a host
term; (3) CVs are longer, master's CVs list the bachelor's, and the positive control
removes every qualifying line; (4) DEU is now a Western-European-expatriate benchmark and
the German-setting benchmark rationale (review M10's framing) no longer applies; the
language threat C13 is superseded by C16 (inferred Arabic). No finding is reopened by the
change; the rows affected are M6, M9, M10, L3 and L13, updated below. New threats
(C14–C18, S12, E9, E10) are not review findings and are tracked in
`threats_to_validity.md` v0.4.

**Restructuring after the setting change (2026-10-01, engineering; contract U1–U5,
design decision D48).** Every input is now a CSV table (`config/runs.csv` replaces the
run YAML files, `config/analysis_settings.csv` the confirmatory YAML, `config/models.csv`,
`config/leak_terms.csv`, `config/text_flags.csv`, `stimuli/jobs.csv`,
`prompts/principle_items.csv`, `stimuli/base_countries.csv` and
`stimuli/building_blocks/` the other YAML files) and prompts are assembled from
`prompts/prompt_parts.csv` and `prompts/prompt_recipes.csv`; the CLI takes `--run
<mock|pilot|main>` instead of `--config config/<x>.yaml`. Purely structural: every
rendered prompt, job ad and CV clone is byte-identical (`tests/test_prompt_snapshot.py`).
No finding changes status; the "where fixed" column below uses the new paths. Re-checked
2026-10-01: `validate-stimuli` → `VALIDATION PASSED` (1,680 clones); `plan --run pilot` →
43,228 calls; `plan --run main` → 106,548 calls (FC 600 quads, each level in 48,
per-level variant spread 0). The two verification runs below are history and quote the
CLI of their date (`--config config/<x>.yaml`).

**Verification run (2026-10-01, after the setting change).** `validate-stimuli` → `OK: 48
CV rows x every nationality row (+ positive control) = 1680 clones rendered and checked,
0 error(s)`, `VALIDATION PASSED`. `plan --config config/main_experiment.yaml` → 26,637
calls per model, 106,548 in total (FC 600 quads per condition, each level in 48,
per-level variant spread 0); pilot unchanged at 43,228. `python -m pytest -q -p
no:hypothesispytest` → 294 passed.

**Status key.** `fixed` = implemented and verified in code/config/docs. `partly fixed`
= the main risk is addressed, a named part remains. `open decision` = the team must
decide. `won't fix` = deliberately not changed, with the reason. `superseded` = the
finding no longer applies because the design changed.

**Structural change after the review (2026-09-30, user request; contract G1–G3).**
(1) Stimuli are two tables, `stimuli/cvs.csv` and `stimuli/nationalities.csv`, plus
`stimuli/cv_template.txt`, rendered at call time; pre-rendered clones, manifests, diffs,
`stimuli/base_cvs/`, `config/stimulus_sets.yaml`, `generate-stimuli` and
`stimulus_set_id` are gone. (2) English is the only language: every ad requires only
"Fluent English (C1 or higher)" and every CV lists only English (C1). **The native-German
robustness arm (A13 / CR-13, R12) is removed**, and the open decision "native German as
the primary language line" no longer exists; the C4 language incongruity is resolved and
replaced by threat C13 (inferred-language channel in Arab-vs-DEU contrasts). (3) All CV
employers and institutions are in the Rhine-Neckar region; the accountant ad says "HGB
accounting standards". The pilot now uses all 4 main-study models. (Points (3) and C13
are superseded by the setting change of 2026-10-01, above.)

**Verification run (2026-09-30, after the structural change).**
`PYTHONPATH=src python -m hiringaudit validate-stimuli` → `OK: 48 CV rows x every
nationality row (+ positive control) = 1680 clones rendered and checked, 0 error(s)`,
`VALIDATION PASSED`. `plan --config config/pilot.yaml` → 10,807 calls per model, 43,228
for 4 models. `plan --config config/main_experiment.yaml` → 26,637 per model, 106,548 in
total; FC 600 quads, each level in 48, per-level variant spread 0.

## HIGH

| id | finding | status | where fixed | residual risk |
|---|---|---|---|---|
| H1 | Blinding and confirmatory settings enforced only by convention | **fixed** (round 2: N1 closed) | `analysis/settings.py` (unblinding gate, log, provenance); `pipeline.py` (blind default, separate output dirs, override and exploratory-parse stamps, stale-table refusal); `cli.py` (`analyze --unblind`, passes `--root`, one-line refusal); `config/analysis_settings.csv`; SAP v0.4 §0, §16; prereg §3.4, §14.2 | The gate now also requires the preregistration and freeze file committed at HEAD, no unresolved markers, and the confirmatory config committed and unchanged; the analysis config (`analyze --config <file.json>`) cannot redirect root, confirmatory file or log. Remaining by design: all-mock data may be unblinded without a freeze. Until the project is committed, every run is stamped EXPLORATORY OVERRIDE. `config/prereg_freeze.json` does not exist yet. |
| H2 | Tier manipulation weak and partly inverted; incoherent borderline CVs | **fixed** | tier rubric (documented in `stimuli/README.md`, building blocks in `stimuli/building_blocks/`; the CV table `stimuli/cvs.csv` is now the source of truth); validator: tier ordering, experience months vs job dates, title–bullet coherence against the pools (N7) | The blind two-coder tier check has not been run. An interview ceiling is still possible until P3 (per tier). |
| H3 | Resume silently mixes revisions and inputs; real runs allowed unpinned and uncommitted | **fixed** (round 2: N2 closed) | `runner.py`: run identity incl. full model specs, SHA-256 of `stimuli/cvs.csv`, `stimuli/nationalities.csv`, `stimuli/cv_template.txt`, `stimuli/jobs.csv`, `prompts/principle_items.csv`, `prompts/prompt_parts.csv`, `prompts/prompt_recipes.csv`, parser version; real-call guard (empty `revision`, `unverified`, dirty/untracked tree in the data root **and** the code repository, `/v1/models` mismatch); processed `prompt_sha256`, `user_prompt_version`; loader refuses mixed revisions/prompt versions | The code is still uncommitted, so the guard refuses every real run until it is committed and tagged; all four revisions in `config/models.csv` are still empty. |
| H4 | Default SESOI (2 points) larger than the known effect (Lippens −1.41) | **partly fixed / open decision** | defaults 1.0 fit point (contrasts, σ_A, H1d), 5 pp interview, FC unchanged (`config/analysis_settings.csv`; SAP §11; hypotheses §0; D24; prereg §8) | Values remain an OPEN team decision, due before the pilot (A2). RQ2/RQ3 equivalence often unreachable ("inconclusive"); MDEs reported; SESOI not changed after the pilot. |
| H5 | No placebo or lexical floor for σ_A; Horn-of-Africa origins can drive heterogeneity | **fixed** | 8 placebo rows in `stimuli/nationalities.csv` (rule in `stimuli/README.md`); H1e with label rule (SAP §5.8; `analysis/hypotheses.py`); 19-origin co-requirement (SAP §5.5); σ_A,net (SAP §5.7) | σ_placebo rests on 8 labels; H1e shows whether, not why; SD-scale CI coverage 91 % at 18 CVs, 94 % at 48. The race confound is bounded, not removed (MRT, SDN stay in the 19-origin set). |

## MEDIUM

| id | finding | status | where fixed | residual risk |
|---|---|---|---|---|
| M1 | Positive-control gate two-sided and trivially passed | **fixed** (mild PC: won't fix) | one-sided check (`positive_control_direction: negative`; SAP §9); called a manipulation check | No "mild" positive control (a new stimulus factor after the design freeze). |
| M2 | "R5 bounds" are not bounds | **fixed** (round 2: N3 closed) | Manski bounds per Δ contrast; robust label on **observed, CV-specific support**; logical 0/100 support reported with bound width, decision-relevant only if differential missingness rejects; uniform imputation renamed SVI (SAP v0.4 §10; `manski_support_robust: observed`) | No worst-case bound exists for σ_A (SVI only, labelled as such). |
| M3 | H1b and σ_A CI assume sphericity | **fixed** | sphericity-free calibrated bootstrap; equivalence requires both tests; residual variances and GG ε (SAP §5.4) | ε biased with fewer CVs than nationalities (descriptive). |
| M4 | "Meaningful heterogeneity" below the SESOI | **fixed** | minimum-effect test (F1-min); new labels (SAP §5.5) | — |
| M5 | Manifest metadata trusted but not validated | **superseded / fixed** | no manifest exists any more (G1): tier, occupation, pilot flag and applicant reference are columns of `stimuli/cvs.csv`, validated directly (unique ids and references, known occupations and tiers, experience months vs dates) | — |
| M6 | Leak check narrow; README/prereg overclaim | **fixed** | `config/leak_terms.csv` (cities, citizenship, religious and non-English language terms, German terms); base-country whitelists for employer cities and institutions (V1, 2026-10-01; formerly Rhine-Neckar, G3), only the CV's own base country exempt; English-only check (G2); job ads localised to every base country, system prompt, prompt parts and assembled templates scanned; the term `native speakers?` fires since 2026-10-01 (regex; it was matched literally before and never fired); documents say "listed cues only" | Still list-based; cannot judge whether a real local institution carries an origin association. |
| M7 | Transport failures become permanent missing cells | **fixed** | api_error-only calls re-attempted on resume, in at most 3 sessions (N7), attempts counted across sessions | Terminal api_error cells count as non-ok in the missingness outcome (SAP v0.4 §10). |
| M8 | Technical stop rule not implemented | **fixed** (round 2: N6 closed) | `runner.evaluate_stop`; `stop_rule_*` columns of `config/runs.csv`; `api_error` excluded from numerator and denominator | — |
| M9 | Within-Arab confounds not constant | **partly fixed** | H1d ecological; sensitivity slopes with `wb_sub_saharan` and income group; occupation slopes exploratory (SAP §5.10); host status, the new within-Arab confound of the Arab-world setting, adjusted with a common host effect and checked by HX (SAP v0.5 §4a) | FCS sensitivity impossible (not in the World Bank API). No CV lists any native language (G2), which a model may find more natural for Somali-, French- or Comorian-speaking origins than for Arabic-speaking ones, and in an Arab labour market may lead it to doubt their Arabic (C16); addressed only through the 19-origin co-requirement. New since 2026-10-01: GCC-partner status (C15) is not adjusted and is collinear with the high-income end of H1d (OPEN). |
| M10 | "POL is the cleanest comparator" | **fixed** (phrase dropped) / **superseded** in part | SAP §6; hypotheses RQ2; design §1.4 B; prereg H2 | The replacement framing ("Ā–TUR closest on non-EU legal status; Ā–POL = EU free movement") was German-specific and is withdrawn with the Arab-world setting; benchmark roles are an OPEN DECISION (design_decisions D19). Ā–DEU now carries a possible Western-expat premium (C17) and an inferred-Arabic advantage of the Arab set (C16; C13 superseded). |
| M11 | Researcher degrees of freedom after seeing data | **partly fixed** | H1d estimator fixed; parser freeze with exploratory-parse stamp (N5); `r4_processed_dir` removed; **Mistral now piloted (G4)** | Near-duplicate threshold still TO SET and no check exists in code. |
| M12 | Text flags collide with CV vocabulary | **fixed** (round 2: N4 closed) | phrase patterns plus broader non-colliding phrasings for `mentions_testing` and `mentions_culture_fit` (`config/text_flags.csv`) | Not yet validated against the hand-coded sample. |
| M13 | FC wording variants confounded with nationality | **fixed** | `randomization.balance_variants`; main per-level spread 0, pilot ≤ 1 | — |
| M14 | Power and sizing | **fixed** | power defaults (fast, 2,000 sims, ρ_ε = 0, MDE); 80 % upper limits from a CV bootstrap (SAP §17) | TOST and SE targets likely unreachable at the authoring ceiling with SESOI 1.0. |
| M15 | Missing wording shifts the per-CV mean | **fixed** | additive imputation within CV (SAP §3) | — |
| M16 | Preregistration has no timestamp | **open decision** | prereg §14.2 (freeze procedure incl. timestamped registration) | Git tags and the freeze hash are internal only. |
| M17 | Model scope (8–24B open-weight only) | **open decision** | claims scoped to the tested open-weight models under this template (hypotheses §0, prereg §1, §13) | Whether one pinned API model is piloted and included depends on budget. |

## LOW

| id | finding | status | where fixed | residual risk |
|---|---|---|---|---|
| L1 | README analysis status and test command | **fixed** | README | — |
| L2 | Unknown nationality code crashes the validator | **fixed / superseded** | table validation gives clean errors | — |
| L3 | Positive-control line not checked | **fixed** | validator: the removed lines must be exactly the CV's qualification lines (`positive_control_education` in `stimuli/cvs.csv`; since 2026-10-01 every qualifying line, e.g. master's and bachelor's) and no qualification cue may survive in the positive control | — |
| L4 | Parser edge cases | **fixed** | extended refusal patterns; first-object rule documented; `n_json_objects`, `near_miss` | A later correction in the same output is ignored (inspectable). |
| L5 | Mock and real runs separated only by convention | **fixed** | `RunIdPolicyError` | — |
| L6 | P3 pools two tiers | **fixed** | SAP §16 | — |
| L7 | CV dates after model cut-offs | **fixed** | `reference_date` 2024-06 in the table; validator date check | — |
| L8 | ETHICS legal framing | **fixed** | `ETHICS.md` §4 | [VERIFY] against legal texts before use. |
| L9 | Weak prompt-robustness evidence | **fixed** (documents) | scope statements (hypotheses §0, prereg §1, §13) | Three wordings share one template and output block. |
| L10 | Completed futures dropped on abort | **fixed** | `runner.handle_batch` | — |
| L11 | E_m ≈ 1 near-certain | **fixed** (documents) | hypotheses SQ1; SAP §14; prereg §2.4 | — |
| L12 | `summary.md` lacks git commit / code hash | **fixed** | `settings.provenance` | — |
| L13 | Literature-matrix nuances | **partly fixed** | three rows updated | `koopmans2019taste` per-group n still to confirm against the full text (less central since the setting is no longer German). The Arab-world setting rests on claims with no matrix source (nationalisation policies, GCC labour mobility, Gulf CV conventions), marked [VERIFY] in the documents. |
| L14 | Possible near-miss prior work | **fixed** | `hoffmann2026evaluating`, `nakano2024nigerian` added; verdict unchanged | Bilon 2025 full text unresolved. |
| L15 | Minor inconsistencies | **fixed** | README; power default `--n-models 3`; sharp-null wording | — |

## Round 2 (re-verification)

| id | finding | status | where fixed | residual risk |
|---|---|---|---|---|
| N1 | H1 bypass through operational config keys (root, confirmatory path, log path); freeze file need not be committed; `--root` not passed; stale tables; traceback | **fixed** | SAP v0.4 §0; `analysis/settings.py`; `cli.py` passes `--root`; gate requires committed files, hash match, no unresolved markers, committed confirmatory config; stale-table refusal; one-line error | — |
| N2 | Dirty-tree preflight checks the data root, not the code location | **fixed** | `runner.py` checks both the data root and the repository holding the running code | — |
| N3 | Manski bounds with logical support uninformative against a 1-point SESOI | **fixed** | observed support for the robust label; logical support descriptive unless missingness rejects (SAP v0.4 §10) | — |
| N4 | `mentions_testing` / `mentions_culture_fit` recall too low | **fixed** | broader patterns in `config/text_flags.csv` | Validation on the hand-coded sample pending. |
| N5 | Outputs from an exploratory re-parse not stamped | **fixed** | "EXPLORATORY PARSE" stamp (SAP v0.4 §0) | — |
| N6 | Stop rule counts transport errors | **fixed** | `api_error` excluded from the stop rule | — |
| N7 | Title–bullet coherence not validated; api_error re-attempts uncapped; other small items | **fixed** | coherence check against the builder pools; re-attempts capped at 3 sessions (`retry_max_api_error_sessions` in `config/runs.csv`) | — |

## Still open (team)

1. SESOI values (H4) — before the pilot.
2. Timestamped registration of Stage A (M16).
3. API model or open-weight-only scope (M17).
4. Near-duplicate threshold and check (M11) — engineering.
5. Commit and tag the code; pin revisions (H3) — before any real run.
6. Blind two-coder tier check (H2) — before the pilot, on the CV table rebuilt on
   2026-10-01.

New with the setting change (not review findings; `design_decisions.md` §2 items 10–14):
benchmark roles in the Arab-world setting; GCC-partner sensitivity; GCC-adjusted H1d
slope; Gulf-heavy base-country mix and English-only retail/warehouse ads in Cairo and
Amman; placebo labels with Gulf-specific associations.

No longer open: Mistral piloted or dropped (piloted, G4); Manski support (observed, N3);
native German as primary (withdrawn with the arm, G2).
