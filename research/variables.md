# Variables

Version 0.4 (methodology), 2026-10-01. Companion to
`research/experimental_design.md`. Paths follow `research/design_contract.md`
(amendments A1–A24, B1–B21, G1–G7, V1–V10, U1–U5); since U1 (2026-10-01) every input is
a CSV table and prompts are assembled from parts (`prompts/prompt_parts.csv`,
`prompts/prompt_recipes.csv`), so the YAML and `.txt` paths of earlier versions are
replaced below. v0.4 reflects the Arab-world setting (V1:
`base_country`, `base_city`, per-country personal-details lines, localised job ads),
the base-country allocation (V2), `host_national` and the host-adjusted estimands (V3–V6),
and the extended CVs with the positive-control column (V7; now `positive_control_education`); the Rhine-Neckar same-region
rule (G3) is superseded. v0.3 reflected the table-based stimuli rendered at call time
(G1) and the English-only language requirement (G2); the native-German arm and
`stimulus_set_id` no longer exist.

Column key. **Type**: nominal, ordinal, binary, integer, continuous, text.
**Set in**: the single place where the value is defined; code modules only
read it from there.

---

## 1. Manipulated variables (the treatments)

| variable | type | levels / range | source / rationale | set in |
|---|---|---|---|---|
| `nationality` (N) | nominal | 34: 22 Arab League member states; DEU (reference), POL, TUR; 8 placebo signals (URY, BOL, SYC, MWI, MDV, NPL, MYS, KHM); NONE (line omitted) | inclusion rule and placebo selection rule in `stimuli/README.md` | `stimuli/nationalities.csv` (`code`, `demonym`, `group`); rendered at call time with `stimuli/cv_template.txt`; checked by `validate-stimuli` |
| `nationality_group` | nominal | arab, benchmark, placebo, control | placebo rows enter only H1e | `stimuli/nationalities.csv` (`group`) |
| `clone_type` | nominal | `counterfactual`, `positive_control` | positive control = `NONE` clone minus every qualification line that satisfies the must-have (A7 as amended by V7; master's and bachelor's for master's CVs) | designated requirement: `stimuli/jobs.csv` (`positive_control_requirement`); removed entries: `positive_control_education` column of `stimuli/cvs.csv` (education entries such as `edu1 \| edu2`; validator checks that their lines are exactly the CV's qualification lines and that no qualification cue survives) |
| `host_national` | binary | 1 if `nationality` == the CV's `base_country`, else 0 | derived, not manipulated separately: exactly one Arab clone per CV; never 1 for benchmarks, placebos or NONE (V3) | derived when records are written and parsed (`src/hiringaudit/stimuli/setting.py`, `parse_outputs.py`); `host_national` (evaluations), `host_national_a`, `host_national_b` (forced choice) |
| `prompt_condition` (P) | nominal | baseline, neutrality, forced_choice, forced_choice_neutrality, principle_probe | contract §4 | recipes in `prompts/prompt_recipes.csv` (parts in `prompts/prompt_parts.csv`); which conditions run: `<condition>_enabled` columns of `config/runs.csv` |
| `prompt_variant` (K) | nominal | k1, k2, k3 per task | wording robustness (A3) | `variant` of the recipe rows in `prompts/prompt_recipes.csv` (variant-specific parts `*_intro_k*`, `*_task_k*`); which variants run: `prompt_variants` in `config/runs.csv`; logged as `prompt_variant` and `user_prompt_version` |
| `fc_order` | binary | AB, BA | quad counterbalancing | FC design (`src/hiringaudit/randomization.py`; stored per run in `fc_design.json`) |
| FC arrangement | binary | {i1:a, i2:b} or {i1:b, i2:a} | quad counterbalancing | same FC design; appears as `cv_a`, `cv_b`, `nationality_a`, `nationality_b` |
| `arm` | nominal | primary; greedy (T = 0, R4) | robustness arm (A10); the native-German arm is withdrawn (G2) | `greedy_arm` and `greedy_*` columns of `config/runs.csv` (row `main`) |
| principle item | nominal | 12 target items (6 pro, 6 reverse) + 3 control items | A11 | `prompts/principle_items.csv`; recipe `principle_probe` in `prompts/prompt_recipes.csv`; which items run: `principle_probe_items` in `config/runs.csv` |
| principle item keying | nominal | pro, reverse, control | acquiescence control | `prompts/principle_items.csv` (`keying`) |
| principle item type | binary | principle, control (+ `expected_answer` for control items) | specificity check | `prompts/principle_items.csv` (`item_type`, `expected_answer`) |
| principle context | nominal | generic + 6 occupations | 7 contexts | parts `probe_context_generic`, `probe_context_occupation` (`{title}` from `stimuli/jobs.csv`) in `prompts/prompt_parts.csv`; which contexts run: `principle_probe_contexts` in `config/runs.csv`; `principle.csv` `context` |

## 2. Blocking and stratification variables

| variable | type | levels / range | role | set in |
|---|---|---|---|---|
| `occupation` (J) | nominal | 6 main; 3 pilot | stratum; weighted equally | `stimuli/jobs.csv`; per CV in `stimuli/cvs.csv`; which run: `occupations` in `config/runs.csv` |
| occupation attributes | ordinal | `skill_level`, `customer_contact`, `trust_role`, `fit_emphasis` | descriptive moderators only | `stimuli/jobs.csv` |
| `required_years` | integer | 3 (software, accountant, consultant), 2 (retail, warehouse, admin) | anchor of the tier rubric | `stimuli/jobs.csv` |
| `base_cv_id` (i) | nominal | main 8 per occupation (2/4/2); pilot 6 (2/2/2) | independent unit; cluster for inference | `stimuli/cvs.csv` (`cv_id`, `pilot`); which run: `base_cvs` in `config/runs.csv` |
| `base_country`, `base_city` | nominal | ARE Dubai, SAU Riyadh, QAT Doha, KWT Kuwait City, OMN Muscat, BHR Manama, JOR Amman, EGY Cairo; 6 CVs per country (main), assigned per same-tier CV pair | CV attribute (absorbed by the CV effects); defines `host_national`; forced-choice pairs share it; job ad location | `stimuli/cvs.csv`; allocation `fc_pair`, `base_country` in `stimuli/building_blocks/cv_slots.csv`; whitelists `stimuli/base_countries.csv`, `stimuli/building_blocks/institutions.csv`; carried in raw records and processed tables |
| `qualification_tier` | ordinal | strong, adequate, borderline | stratum; FC pairs within tier; ambiguity moderator | `stimuli/cvs.csv`; rubric documented in `stimuli/README.md` (building blocks in `stimuli/building_blocks/`); ordering enforced by the validator |
| `relevant_experience_months`, `total_experience_months` | integer | months | tier check (not rendered) | `stimuli/cvs.csv`; must equal what the job dates imply (validated) |
| `model_alias` / `model_id` (m) | nominal | see `config/models.csv` | fixed level; never pooled for confirmatory tests | `config/models.csv`; each run lists aliases in the `models` column of `config/runs.csv` |
| `model_revision` | text | HF commit SHA or dated API snapshot | provenance; the loader refuses more than one per alias | `config/models.csv` (`revision`; empty = not pinned); copied into every record |
| `repetition` (r) | integer | 1 … r (pilot 3; main PROVISIONAL, default 2) | replicate index; not a unit | `<condition>_repetitions` columns of `config/runs.csv` |
| `seed` | integer | derived per call from (model, arm, condition, base CV or CV pair, variant, repetition, FC order, item, context) — never from nationality or clone type | common random numbers (A17) | `src/hiringaudit/randomization.py`; master seed: `seed` column of `config/runs.csv` |
| `execution_index` | integer | 0 … N−1 | randomised order across cells (A5) | `src/hiringaudit/randomization.py` |
| `quad_id`, CV pair | nominal | per FC design | FC cluster; wording variants Latin-rotated per nationality | FC design |
| `subregion` | nominal | gcc, mashriq, nile_valley, maghreb, peninsula_non_gcc, horn_indian_ocean; western_europe (DEU; formerly host_country), eu_foreign, non_arab_mena; latin_america, sub_saharan_africa, south_asia, east_asia_pacific (placebo); not_stated | hierarchical structure; σ_A,net | `stimuli/nationalities.csv` |
| `arab_identity_contested` | binary | true for SOM, DJI, COM | 19-origin analyses (headline co-requirement; R1) | `stimuli/nationalities.csv`; also `contested_codes` in `config/analysis_settings.csv` |

## 3. Held-constant variables

Constant **within a base CV across its clones** (by construction: one CV row is
rendered with each nationality row). "Design constant" = also identical in every row of
`stimuli/cvs.csv` (validated); "per base country" = constant within a CV, varying across
CVs with the CV's base country (V1; absorbed by the CV effects).

| variable | value | why held constant | set in | checked by |
|---|---|---|---|---|
| applicant reference | `APP-dddd`, unique per CV row, never encodes nationality | replaces name (threat C3) | `stimuli/cvs.csv` | validator |
| location (per base country) | `<base city>, <country>`, e.g. "Dubai, United Arab Emirates" | residence channel | `stimuli/cvs.csv`; derived in `src/hiringaudit/stimuli/setting.py` | validator (must equal the derived line) |
| work authorisation (per base country) | `Work authorization: Authorized to work in <the country>; no visa sponsorship required` | legal-status channel (C2, C15) | `stimuli/cvs.csv`; `setting.py` | validator |
| driving licence (per base country) | `Valid driving licence issued in <the country>` | conventional personal-details block (C5; A8) | `stimuli/cvs.csv`; `setting.py` | validator |
| availability (design constant) | `One month's notice` | conventional personal-details block (C5; A8) | `stimuli/cvs.csv` | validator |
| languages (design constant) | `English (C1)` only; no German, Arabic or any other language anywhere (G2) | language channel (C2, C16) | `stimuli/cvs.csv` | validator + leak list |
| education (per base country) | qualification (master's CVs: master's and preceding bachelor's; otherwise a degree or diploma) from a real institution of the base country, then "Secondary school certificate" (V1, V7) | foreign-credential channel; local credentials for every clone | `stimuli/cvs.csv`; whitelist `stimuli/building_blocks/institutions.csv` | validator |
| employers (per base country) | invented, country-neutral English names in cities of the base country; most recent job in the base city (V1) | foreign-experience channel | `stimuli/cvs.csv`; city whitelist in `stimuli/base_countries.csv` | validator |
| dates | nothing after the reference date 06/2024 | "future" dates could read as synthetic | `stimuli/cvs.csv` (`reference_date`) | validator |
| profile, key achievements, experience bullets, skills, certifications | per CV row: 2–3-sentence profile; achievements strong 3 / adequate 2 / borderline 2; 3–5 bullets per relevant job; skills 12 / 10 / 8; up to 3 certificates; each job's bullets and employer from the pool for its title, achievements from the tier's pool (V7) | coherence (review H2, N7); realism (C5, E5) | `stimuli/cvs.csv` (built by `scripts/build_cv_table.py` from `stimuli/building_blocks/*.csv`; rebuilt 2026-10-01, seed 20261001) | validator (title–bullet and achievement–tier coherence against the pools) |
| template, section order, formatting | one template | clone rule | `stimuli/cv_template.txt` | validator renders every CV × nationality combination (1,680) |
| absent fields | no name, photo, date of birth, gender, pronouns, religion, marital status, birthplace | removes other group signals | template | validator (leak list: listed terms only) |
| job ad | one per occupation, localised to the CV's base city (`location: "{city}, {country}"`), otherwise identical; invented country-neutral employer; only language requirement "Fluent English (C1 or higher)"; accountant: IFRS (no "Applications in English are welcome" sentence; deviation from A24) | constant task within a CV and within a forced-choice pair | `stimuli/jobs.csv` | leak scan of the ads rendered for every base country |
| system prompt | one shared text incl. the constant pseudonymisation sentence (A23) | role identical across tasks | part `system` in `prompts/prompt_parts.csv` (step 1 of every recipe) | `system_prompt_version` logged; leak scan; validator: the same system part in every recipe |
| neutrality paragraph | fixed text immediately before the output block | RQ3 treatment | part `neutrality_paragraph` (`part_type` intervention) in `prompts/prompt_parts.csv`, added by the `neutrality` and `forced_choice_neutrality` recipes | validator: each neutrality recipe = its baseline recipe + exactly this one step, immediately before the output instructions |
| output schema and field order | score → interview → confidence → reason | reason is post-hoc | output parts (`*_output`) in `prompts/prompt_parts.csv`; `src/hiringaudit/schemas.py` | parser tests; validator: one output part per task, the last step |
| decoding parameters | T 0.7 (greedy arm 0), top_p 1.0, top_k −1, min_p 0, repetition penalty 1.0, max_tokens 400, thinking off | comparability across models (A10) | `config/runs.csv` (`temperature`, `top_p`, `max_tokens`, `json_mode`, `openai_compatible_extra`; greedy arm `greedy_temperature`); thinking off via `extra_body` in `config/models.csv` | logged per call |
| serving stack | vLLM version, dtype, quantisation, GPU type, chat-template hash | drift, nondeterminism (A6) | `config/models.csv` + server introspection | manifest; real-call guard checks `/v1/models` |

## 4. Measured variables (per call)

| variable | type | range | task | stored |
|---|---|---|---|---|
| `overall_fit` | integer | 0–100 | independent evaluation | `evaluations.csv` — **primary outcome** |
| `interview` | binary | yes/no → 1/0/NA | independent evaluation | `evaluations.csv` — key secondary (analysed in pp) |
| `confidence` | integer | 0–100 | IE, FC | exploratory; never treated as calibrated |
| `reason` | text | free | all | source for text flags |
| `choice` | nominal | A, B, NA | forced choice | `forced_choice.csv` |
| `answer` | binary | yes/no | principle probe | `principle.csv` |
| `agreement` | integer | 0–100 | principle probe | `principle.csv` |
| `parse_status` | nominal | ok, malformed_json, schema_violation, refusal, empty, api_error | all | all processed tables; **an outcome, not a filter**; terminal `api_error` counts as non-ok |
| `refusal`, `api_error`, `finish_reason` | binary / text | — | all | raw + processed |
| `n_json_objects`, `near_miss` | integer / binary | — | all | parser diagnostics; never used to coerce an outcome |
| `usage`, `latency_ms`, `attempts` | integer | — | all | raw (`attempts` counts transport retries across sessions; api_error-only calls re-attempted in at most 3 sessions) |
| `logprobs` | list | optional | where the provider offers them | raw only; R10 is not implemented in the processed schema |
| `raw_output` | text | — | all | raw JSONL, never rewritten |

## 5. Derived variables

Computed in `src/hiringaudit/analysis` from processed tables.

| variable | definition | level |
|---|---|---|
| stimulus mean μ̂(i,n,m,p,k) | mean over replicates of one exact prompt | stimulus × wording |
| μ̄̂(i,n,m,p) | mean over the K wordings; a wording with no valid replicate is imputed additively within the CV first | stimulus |
| CV-level contrast d_i(a,b) | μ̄̂(i,a) − μ̄̂(i,b) | base CV |
| τ̂(n), Δ̂(a,b) | occupation-balanced means / contrasts (design §1.3) | model × condition |
| τ̄̂_A, δ̂(n), σ̂_A (debiased), σ̂_A(19), σ̂_A,net | within-Arab estimands (A), net of the common host effect η (SAP §4a) | model × condition |
| η̂ | common host-national effect: host clone minus the same origin's non-host clone, CV and nationality fixed effects (secondary, descriptive; `host_effect.csv`; not in blind mode) | model × condition × outcome |
| HX estimates | σ̂_A (22, 19), δ̂(n) and Δ̂(Ā, b) with host cells removed and no host term (`host_sensitivity_deltas.csv`); required for "robust" | model × condition |
| σ̂_placebo, σ̂_A − σ̂_placebo | placebo floor (H1e) | model (baseline) |
| lower / upper one-sided 95 % limits of σ_A; sphericity-free upper bound; Greenhouse–Geisser ε | minimum-effect and equivalence tests (SAP §5.4–5.5) | model × origin set |
| β̂_W | slope of δ(n) on centred log income (H1d); sensitivity slopes with `wb_sub_saharan`, income group | model |
| ΔD_σ, ΔD_DEU, λ̂ | prompt-condition estimands (D) | model |
| ρ̂(m, m′), split-half reliability | profile concordance (C) | model pair |
| PC_m | positive control: τ(positive_control) − τ(NONE); passed iff < 0 with one-sided upper limit < 0 | model |
| `chosen_nationality`, `chosen_cv` | from `choice` and the FC design | FC call |
| π̂_q | share of the 4 quad calls choosing the candidate with nationality a | quad |
| β̂_n, θ̂_i, γ̂, η̂_FC | Bradley–Terry nationality worths, CV worths, position bias (E), host term (secondary); host-free sensitivity (`bt_host_excluded.csv`) | model × condition |
| π^IE_q, β^IE | IE-implied pairwise preferences and worths | model |
| σ_A^FC / σ_A^IE, corr(β^FC, β^IE) | format comparison (RQ4) | model |
| non-ok indicator | 1[parse_status ≠ ok] (incl. terminal api_error) | call |
| Manski bounds; SVI | worst-case bounds for Δ (robust label: observed CV-specific support; logical 0/100 descriptive); single-value imputation sensitivity for σ_A (R5) | model × contrast |
| `mentions_*` flags | phrase-pattern dictionaries on `reason` (`config/text_flags.csv`); `mentions_language` also measures unsupported language concerns (C16, e.g. about Arabic); `mentions_visa` unsupported visa or sponsorship concerns (C2); `pronoun_gender` | call |
| concern / mention / disclaimer code | hand-coded on a stratified sample (proposed 200), two coders, agreement reported | call (sample) |
| endorsement | answer × keying (1 = endorses neutrality) | principle call |
| E_m | mean endorsement over target items × contexts × replicates (item-balanced) | model |
| D_m, G_m | behavioural disparity (RQ1 headline + H2 labels) and principle–behaviour classification (hypotheses SQ1) | model |
| variance components + 80 % upper limits | moments; CV-bootstrap 90th percentile | model × condition × outcome |

## 6. Country-level covariates

Downloaded by `scripts/fetch_country_covariates.py` from the World Bank API for every
code in `stimuli/nationalities.csv`, with the retrieval date per row; never entered from
memory. Stored in `config/country_covariates.csv` (retrieved 2026-09-30), frozen before
main-study data collection.

| variable | source | reference period | use |
|---|---|---|---|
| `gdp_pc_ppp_const` (log taken in analysis) | WDI `NY.GDP.PCAP.PP.KD` | 2022; if missing, most recent 2015–2021, flagged; if none, excluded (Yemen) | H1d primary covariate |
| `income_group` | World Bank country API; edition at download | recorded | H1d sensitivity (ordinal) |
| `wb_region`, `wb_sub_saharan` | World Bank country API | at download | H1d sensitivity slopes; sub-Saharan among the Arab set: COM, MRT, SOM, SDN |
| fragile / conflict status | not available from the World Bank API | — | not used |
| ~~nationals resident in Germany~~ | Destatis (not fetched) | — | withdrawn 2026-10-01 (German setting); no replacement planned |

## 7. Provenance variables (per call; contract §6, A6, B12, G1)

`record_id`, `trial_id`, `run_id`, `experiment_id`, `config_hash`,
`timestamp_utc`, `provider`, `model_id`, `model_alias`, `model_revision`,
`temperature`, `top_p`, `max_tokens`, `seed`, `system_prompt_version`,
`user_prompt_version` (`<condition>_<variant>@sha256:<hash of the assembled template>`
since 2026-10-01), `prompt_variant`, `prompt_sha256`, `stimulus_ids`
(`<cv_id>__<code>`; positive control `<cv_id>__NONE__pc`), `base_cv_ids`,
`execution_index`, `arm`, `is_mock`; since 2026-10-01 also `base_country` and
`host_national` (aligned with `nationalities`). Every rendered prompt is stored once per SHA-256 in
`data/raw/<run_id>/prompts.jsonl`. Processed tables carry `prompt_sha256`,
`user_prompt_version` and `model_revision`; the analysis loader refuses mixed revisions
or prompt versions. The run manifest records the run identity (config hash of the run's row of
`config/runs.csv`, full model specs, the assembled prompt templates, SHA-256 of
`stimuli/cvs.csv`, `stimuli/nationalities.csv`, `stimuli/cv_template.txt`,
`stimuli/jobs.csv`, `prompts/principle_items.csv`, `prompts/prompt_parts.csv`,
`prompts/prompt_recipes.csv`, parser version and fingerprint), git commits, package versions and stop-rule decisions.
Everything from the mock provider carries `is_mock = true` and is labelled "SYNTHETIC
MOCK DATA — NOT RESULTS"; mock run ids must start with `mock`, real ones must not.

## 8. Unit summary

| quantity | pilot (per model) | main default (per model) |
|---|---|---|
| base CVs | 18 (6 × 3) | 48 (8 × 6); final I from the pilot |
| base countries | 8 (9 CV pairs: each country once, ARE twice) | 8 (24 CV pairs, 3 per country) |
| host cells per host-eligible nationality | ARE 4, the other seven 2 (of 18 CVs) | 6 (of 48 CVs) |
| renderings per base CV | 35 (26 counterfactual + 8 placebo + 1 positive control) | 35 |
| IE calls per rendering and condition | K × r = 3 × 3 = 9 (placebo and PC: baseline only) | 3 × r (default r = 2) |
| calls in total (`hiringaudit plan`) | 10,807 (43,228 for 4 models) | 26,637 (106,548 for 4 models); PROVISIONAL |
| independent units for inference | base CVs | base CVs |
