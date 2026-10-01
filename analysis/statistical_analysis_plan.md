# Statistical analysis plan (SAP)

Version 0.5, 2026-10-01. Status: proposal, written before any real data exist.
v0.5 pre-specifies the handling of host-national status (§4a) after the CVs were set in the Arab world
(setting 2026-10-01; lead decision: keep all clones and adjust).
v0.3 implemented the analysis items of `research/adversarial_review.md` (§3–§5); v0.4 implements the
round-2 re-verification items N1, N3, N5 and the lead's additions (H1e label rule, api_error in the
missingness outcome, model cross-checks renamed MS1–MS3 to avoid a clash with threat ids).
It builds on `research/design_contract.md` (v0.2 core plus amendments v0.3–v0.5), `research/experimental_design.md`,
`research/hypotheses.md` and `preregistration.md`, which define estimands and hypotheses; this
document fixes how they are estimated and tested. Code: `src/hiringaudit/analysis/`
(entry point `run_analysis`); confirmatory settings: `config/analysis_settings.csv`;
companions `analysis/model_specifications.md`, `analysis/multiple_testing_plan.md`,
`analysis/power_analysis.py`.

Nothing computed from simulated or mock data is a finding. Every output produced from rows with
`is_mock == True` is labelled "SYNTHETIC MOCK DATA — NOT RESULTS".

---

## 0. Blinding, frozen settings and provenance (review H1, L12)

* **Blind by default.** `run_analysis` runs in blind mode unless `config["unblind"] is True`
  (`python -m hiringaudit analyze … --unblind`; `python -m hiringaudit.analysis … --unblind`).
  Blind mode outputs only the items in §16.
* **Project root.** `run_analysis(processed_dir, out_dir, config=None, *, root=None)`; the main CLI
  passes its `--root`; `root=None` means the repository that contains the package. The run config can
  NOT set the root, the confirmatory-config path or the log path (such keys are rejected with an
  error): the confirmatory config is always `<root>/config/analysis_settings.csv` and the log
  `<root>/results/unblinding_log.jsonl` (review round 2, N1a/b/d).
* **Unblinding gate (N1c).** For data that are not entirely mock, a freeze is valid only if
  (i) `preregistration.md` and `config/prereg_freeze.json` are both committed at HEAD and identical
  to the working-tree files; (ii) the freeze's `preregistration_sha256` equals the SHA-256 of
  `preregistration.md` (CRLF normalised to LF); (iii) `preregistration.md` contains no unresolved
  "[TEAM DECISION REQUIRED" or "TO PIN BEFORE FREEZE" markers; (iv) `config/analysis_settings.csv`
  is committed at HEAD and unchanged. Otherwise the run stops with `UnblindingError` and nothing is
  logged. If every input row is mock, unblinding is allowed without a freeze and all outputs keep the
  mock banner.
* **Unblinding log.** Every unblinded run appends one JSON line to `<root>/results/unblinding_log.jsonl`:
  UTC time, user, preregistration hash and freeze status, confirmatory-config hash, overridden keys,
  input and output directories, whether all rows were mock, git commit, analysis-code hash.
* **Frozen confirmatory settings.** α, FDR level, primary outcome, confirmatory / neutrality / FC
  conditions, primary arm, SESOIs, contested codes, positive-control direction, Manski support,
  endorsement and control-item thresholds, covariate file, host-national handling (§4a), seed and all
  resampling counts live in
  `config/analysis_settings.csv`. Its hash is recorded in `summary.md`. A run config that changes
  any of these keys (including resampling counts, e.g. `--quick`), or a confirmatory file that is not
  committed at HEAD or differs from the committed version, stamps every table, figure and report
  "EXPLORATORY OVERRIDE — confirmatory settings changed" and lists the reasons. Unknown config keys are
  rejected.
* **Exploratory parse (N5).** If `parse_summary.json` in the processed directory says
  `parse_mode: exploratory`, or the directory name ends with `__exploratory`, every output is stamped
  "EXPLORATORY PARSE — tables re-parsed with a non-frozen parser".
* **Output directories (N1e).** Blind and unblinded outputs never share a directory; a blind run also
  refuses a non-empty output directory without `summary.md` (possible stale per-origin tables). The former external `r4_processed_dir` option is removed: the greedy arm arrives in the
  same run via `arm == "greedy"`.
* **Provenance** in `summary.md`: project-root git commit and whether config / preregistration have
  uncommitted changes; the analysis-code repository commit and whether the analysis code has
  uncommitted changes; SHA-256 of the analysis code; confirmatory-config hash and commit status;
  preregistration hash and freeze status.

## 1. Data, units and arms

| level | definition | role |
|---|---|---|
| call | one (model m, condition p, wording k, base CV i, nationality n, replicate r) | measurement |
| stimulus | one rendered CV (i, n) under (m, p, k) | treatment cell |
| base CV | i across all its clones | **independent unit** (cluster) |

The loader fails loudly on contract violations and on mixed runs (review H3): one `model_revision`
per model alias (within and across tables), one `user_prompt_version` per (alias, condition, wording),
and one `prompt_sha256` per stimulus cell (replicates of a stimulus must have been rendered from the
same prompt). Placebo nationalities may only appear as counterfactual clones under baseline in the
primary arm and never in forced choice.

* **Arms.** Confirmatory analyses use `arm == "primary"`. Robustness arms (`greedy` → R4,
  others by name) are analysed separately. (The native-German arm, formerly R12, was
  removed on 2026-09-30 when jobs and CVs became English-only.)
* **Clone types.** Nationality analyses use `clone_type == "counterfactual"`; the
  `positive_control` clone is the manipulation check (§9).
* **Base country and host nationals (setting 2026-10-01).** Every base CV is set in one Arab League
  base country (`base_country` ∈ ARE, SAU, QAT, KWT, OMN, BHR, JOR, EGY; assigned per same-tier CV
  pair, 3 pairs = 6 CVs per country in the main set, spread over occupations and tiers); its
  employers, school and the advertised job are in that country. The clone whose nationality equals
  the base country is a **host national** (`host_national`): exactly 1 of the 22 Arab clones of a CV;
  benchmarks, placebos and NONE never are. Each of the 8 base-country nationalities is a host national
  in its own 6 CVs and a non-host in the other 42. Forced-choice pairs share a base country. The
  loader checks `host_national == (nationality == base_country)` in both tables, one base country per
  CV and per quad, base countries that are Arab League codes, and that forced-choice base countries
  agree with the evaluations table.
* **Placebo nationalities** (`nationality_group == "placebo"`, 8 levels) enter only the placebo
  comparison H1e (§5.8). They never enter Arab/benchmark contrasts, per-origin tables, BT, RQ2–RQ4,
  variance components or missingness tests.
* **Outcomes (A1).** `overall_fit` (0–100) is primary; `interview` (percentage points) is the key
  secondary outcome (R2); `confidence` is exploratory. The fit score is never a "hiring probability".
* **Models** are never pooled for confirmatory purposes.

## 2. Estimands (per model; baseline and `overall_fit` unless stated)

| symbol | definition | question |
|---|---|---|
| τ(n) | mean over CVs of μ̄(i, n) (replicates, then wordings averaged) | level for origin n |
| δ(n) | τ(n) − τ̄_A, n ∈ A (22 Arab League member states), net of the common host-national effect η (§4a) | deviation from the Arab mean |
| η | host-national clone minus the same origin's non-host clone, common across origins (§4a) | secondary, descriptive |
| **σ_A** | sqrt((1/22) Σ_A δ(n)²), finite-population SD | RQ1 |
| σ_A(19) | the same over the 19 origins without SOM, DJI, COM | RQ1 headline requires both |
| σ_A,net | σ_A net of the six sub-region means | secondary structure |
| σ_placebo | the same estimator over the 8 placebo nationalities | H1e floor |
| Δ(Ā, b) | τ̄_A − τ(b), b ∈ {DEU, POL, TUR, NONE} | RQ2 |
| ΔD_σ, ΔD_DEU | changes between neutrality and baseline | RQ3 |
| λ | τ_neu(NONE) − τ_base(NONE) | descriptive |
| PC | τ(positive control) − τ(NONE) | manipulation check |
| β_n, σ_A^FC/σ_A^IE, corr(β^FC, β^IE) | forced-choice worth, dispersion ratio, concordance | RQ4 |
| E_m | keyed endorsement of neutrality | SQ1 |

## 3. Replicates and wordings

Replicates are averaged within stimulus; stimulus means are averaged over the K wordings. A wording
without any valid replicate for a (CV, nationality) cell is **imputed additively within the CV**
(nationality + wording effects of that CV, Yates-type iteration) before averaging, so wording main
effects cannot leak into nationality contrasts when non-ok responses depend on nationality
(review M15; verified by simulation in the tests: with wording effects of −8/0/+8 points and one wording
missing for one origin, the unimputed contrast was shifted by more than 3 points, the imputed one by
less than 0.6). Cells with no valid wording at all stay missing. The number of
imputed cells is reported. Reasons for averaging rather than treating replicates as candidates:
the estimand is defined on μ̄; the stimulus-mean analysis has the correct error term
(CV × nationality interaction plus decoder noise / (K·r)); pseudo-replication is avoided; exact
permutation and cluster bootstrap become fast. The nested structure is still used for the variance
decomposition (§17).

## 4. Contrasts, equivalence and decision labels

Every linear estimand is the mean over base CVs of a per-CV contrast value (the unit-level causal
contrast). Point estimate = equal-weight mean of occupation means; SE occupation-stratified with
Welch–Satterthwaite df; 95 % CI and two-sided test from t(df); TOST at ±SESOI (90 % CI). This is the
closed form of the CV-fixed-effects model on stimulus means (cross-check MS1). Four-way labels
(hypotheses.md §0) use the Holm-adjusted test and the Holm-adjusted TOST of the family.

## 4a. Host-national status (lead decision 2026-10-01)

**Why it matters.** In a CV set in, say, Egypt, the Egyptian clone is a local applicant; every other
clone is a foreigner. If models favour locals, the 8 base-country nationalities collect a bonus in
their own CVs only. Without adjustment that bonus is attributed to the nationality: δ̂(n) is shifted
by η·(p_n − 1/22) (p_n = share of CVs set in country n, 6/48 for base countries, 0 otherwise), i.e.
+0.08·η for the 8 base-country nationalities and −0.045·η for the other 14, σ_A gains a spurious
component of about 0.06·η, and Δ(Ā, b) is shifted by η/22. (Verified in `tests/test_analysis_host.py`:
with η = 8 points and 48 CVs the unadjusted δ̂ of base-country nationalities was off by +0.65 points on
average over 4 simulated data sets (predicted +0.64), the adjusted by +0.01; with 18 CVs and no Arab
nationality effects the unadjusted omnibus test rejected in 17 % of 150 null data sets, the adjusted
test in 4 %.)

**Primary analysis: keep all clones and adjust.** The clone-level model on the stimulus means is

    ybar_in = alpha_i + tau_n + eta * H_in + e_in,        H_in = 1[n == base_country(i)]

The CV effects α_i absorb the base country (and everything else about the CV), so the only new
parameter is a common host-national effect η. δ(n), σ_A (22 and 19 origins), σ_A,net, the
Arab-vs-benchmark contrasts Δ(Ā, b) and their R1 versions, the per-origin Δ(n, DEU) / Δ(n, POL), H1c,
H1e and H3a/H3b are all computed **net of η**. η is identified because each base-country nationality
also appears as a non-host in the CVs of the other seven countries.

* **Estimator.** η̂ is the least-squares coefficient with both fixed effects (Frisch–Waugh: H
  residualised on the CV and nationality effects over the observed cells, alternating projections
  under missing cells; equal to the dummy-variable OLS coefficient). With complete data η̂ is the
  same for any column set that contains the 8 base countries (the 22 Arab, the 19 uncontested, or
  all 26 clones), because never-host columns get zero weight.
* **Contrasts (§4).** Every linear estimand becomes M[d_i(Y)] − η̂·M[d_i(H)], with M the
  occupation-stratified mean and d_i the per-CV contrast. Inference stays design-based: the per-CV
  values ψ_i = d_i(Y) − η̂·d_i(H) − M[d_i(H)]·u_i/w_i (u_i = CV i's influence on η̂, w_i its weight in M)
  have stratified mean equal to the adjusted estimate and a stratified-t variance that includes η̂'s
  estimation error and its covariance with the contrast. At the design's allocation this adds less
  than 1 % to the variance of δ̂(n); because the per-CV values no longer carry the host bonus, the
  SEs of the base-country δ̂(n) are in fact smaller than without adjustment.
* **σ_A and its tests (§5).** σ̂²_A is computed on Y − η̂H with one residual df fewer; the noise term
  adds η̂'s variance: σ̂²_A = (1/J) Σ δ̂(n)² − MS_res·[mean(1/I_n)(J−1)/J + mean_n c_n²/ΣX²], c_n = centred
  column mean of the row-centred H, X = residualised H (exact under iid errors for any missingness
  pattern, since X is orthogonal to the column means). The noncentral-F quantities use the matching
  effective I. η is **re-estimated in every bootstrap, permutation and calibration replicate.**
* **Permutation tests.** H1a, σ_A,net and the robustness-check permutations keep each CV's host
  cell fixed and shuffle only its other cells (placebo columns have no host cells). This test is exact for the sharp null that the
  non-host labels do not change any CV's output distribution while allowing an arbitrary host bonus
  (simulation: 4.0 % rejections at α = .05 in 150 null data sets with η = 8 points, 18 CVs).
* **Reported host effect (secondary, descriptive).** `host_effect.csv`: η̂ per model × condition ×
  outcome with a CV-clustered (occupation-stratified) 95 % CI, n of host cells. It is not part of any
  confirmatory or secondary family, carries no decision label and no multiplicity adjustment, and is
  an outcome estimate, so blind mode never computes it (§16). It is the effect of the CV's country
  matching the stated nationality, which bundles "local applicant" with "nationality matches every
  employer and school"; it is not interpreted as a pure citizenship effect.
* **Plug-in uses.** Cross-checks and descriptive structure (Hotelling T², H1d meta-regression,
  profile concordance, interaction profile tests) use Y − η̂H with η̂ treated as fixed.

**Sensitivity HX: exclude host-national clones.** All host-national cells are set to missing (no
adjustment) and σ_A (22 and 19 origins), δ(n) (`host_sensitivity_deltas.csv`, side by side with the
adjusted δ(n)) and Δ(Ā, b) are recomputed; the permutation test keeps the removed cells in place.
**HX is a required check of the "robust" label (§15), like R1:** both the 22- and the 19-origin HX
analyses must keep the sign and exclude 0. Under HX the 8 base-country δ(n) rest on 42 instead of 48
CVs.

**Forced choice.** The Bradley–Terry model adds host_A − host_B (unpenalised; reported as η_FC on the
log-odds scale with a CV-bootstrap CI, secondary). The within-Arab swap randomisation test never swaps
quads that contain a host national. Sensitivity: all quads with a host national dropped, BT refitted
without the host term (`bt_host_excluded.csv`, σ_A^FC in `bt_summary.csv`). The IE-implied
comparisons for RQ4 use the same host term.

## 5. RQ1 — within-Arab heterogeneity

### 5.1 Raw H and R are descriptive only
The plug-in SD and the range of estimated means are biased upward by estimation noise
(E[H²] ≈ σ²_A + mean SE²; the range grows with noise and the number of origins). They are shown
only next to their null reference distributions (random relabelling within CV: mean, 95 % quantile,
excess range).

### 5.2 Debiased σ_A
σ̂²_A = (1/22) Σ δ̂(n)² − mean SE² = ((J−1)/J)(MS_nat − MS_res)/I, truncated at 0 for σ̂_A; the REML
estimate for balanced data when positive. Interval by noncentral-F inversion (coverage holds near 0);
bootstrap percentile interval reported as a cross-check.

### 5.3 H1a — omnibus test (F1)
Within-CV permutation of the 22 Arab labels (≥ 10,000 permutations), statistic σ̂²_A. The test is
**exact for the sharp null** that the 22 labels do not change the output distribution of any CV; for
the weaker null of equal mean effects it is approximately valid, not exact (review L15). Cross-checks:
randomised-block F test and CV-clustered Hotelling T² (not computable when I − #occupations < 21).
Simulation: false-positive rates within binomial limits of 5 %.

### 5.4 H1b — equivalence (F1-eq), two tests required
1. Noncentral-F test: p = P(F′ ≤ F_obs; λ_S), λ_S = I·J·SESOI²/MS_res; equivalently the one-sided
   95 % upper limit < SESOI.
2. **Sphericity-free calibrated bootstrap test** (review M3): T = (σ̂²_A − SESOI²)/se, se from a
   stratified CV bootstrap (variance inflated by n_j/(n_j − 1)); critical value calibrated by
   simulation — residual rows of the additive fit (which keep each nationality's own residual variance
   and the correlation between nationalities) are resampled within occupation, a pattern with
   σ_A = SESOI is added, and T is recomputed with the same bootstrap (n_cal = 500 × 100 bootstrap).
   Upper bound U = sqrt(σ̂²_A − q̂·se). In simulations with residual SDs varying six-fold across
   nationalities, both tests kept the false-equivalence rate at or below 5 % at σ_A = SESOI
   (18 CVs: noncentral F 2.7 %, bootstrap 2.7 %; 48 CVs: 3.3 %, 3.3 %; homoscedastic 18 CVs:
   5.3 %, 6.0 %, within binomial error).
The per-nationality residual variances and a Greenhouse–Geisser ε are reported (ε is biased with
fewer CVs than nationalities; descriptive). Equivalence ("trivial" / "a single category is adequate")
requires both tests, each Holm-adjusted across models.

### 5.5 Minimum-effect test and labels (review M4)
H0: σ_A ≤ SESOI vs H1: σ_A > SESOI, p = P(F′ ≥ F_obs; λ_S) (Holm across models); rejection ⇔ one-sided
95 % lower limit of σ_A > SESOI. Labels per origin set:

| H1a (Holm) | minimum-effect (Holm) | equivalence (both tests, Holm) | label |
|---|---|---|---|
| rejects | rejects | – | **meaningful heterogeneity** (lower bound exceeds SESOI) |
| rejects | not | established | trivial heterogeneity |
| rejects | not | not | **heterogeneity present; size relative to SESOI undetermined** |
| not | – | established | null: a single category is adequate (only if the manipulation check passed) |
| not | – | not | inconclusive |

**Headline RQ1 label** (review H5): the strongest claim supported by *both* the 22-origin and the
19-origin analyses (identical labels → that label; both "effect" labels but different → "heterogeneity
present; size undetermined"; otherwise "inconclusive: 22- and 19-origin analyses disagree").

### 5.6 Exploratory structure
Per-origin δ(n) with stratified-t CIs, simultaneous max-|t| bootstrap bands, BH q-values (q = .05) and
bootstrap rank intervals; no origin called most/least favoured unless its simultaneous band excludes
the Arab mean. Empirical-Bayes shrunken δ(n) (R13).

### 5.7 σ_A net of sub-region means (secondary, review H5)
σ̂²_net = (1/J) Σ (δ̂(n) − mean of its sub-region)² − ((J − G)/J)·MS_res·mean(1/I_n), G = 6
sub-regions (Yemen is a singleton and contributes nothing). Permutation p-value with labels permuted
within sub-region within CV; debiased between-sub-region share 1 − σ̂²_net/σ̂²_A. Descriptive of
structure.

### 5.8 H1e — placebo floor (F2, review H5)

**Label rule (lead decision 2026-09-30):** "Arab spread exceeds placebo spread" iff the 95 % CV-bootstrap
CI of σ_A − σ_placebo lies above 0; "Arab spread below placebo spread" iff it lies below 0; otherwise
"not distinguishable from placebo spread". H1e is a secondary family with Holm across models; a
directional label additionally requires the Holm-adjusted p < α (otherwise "not distinguishable").
Any claim that the within-Arab spread is Arab-specific requires "exceeds".

σ_placebo is the same debiased estimator over the 8 placebo nationalities (baseline, primary arm;
noncentral-F CI and permutation p). Comparison σ_A − σ_placebo on the same CVs: test on the variance
scale (σ̂²_A − σ̂²_placebo, shared stratified CV bootstrap, inflated variance, t(I − #occupations));
effect size and 95 % CI on the SD scale by bootstrap percentiles. Simulation with equal true spreads:
false-positive rate 3.3 % (18 and 48 CVs); CI coverage 91 % (18 CVs) and 94 % (48 CVs). The comparison
asks whether within-Arab spread exceeds generic label spread; it cannot say why.

### 5.9 H1c — do models differ (F2)
Wald test of equal σ̂²_A across models, covariance from a CV bootstrap with the same resamples for every
model (inflated by n_j/(n_j − 1)), reference F(M − 1, I − #occupations) (simulated false-positive rate
5 % at pilot size, 3.5 % at main size). Reported with reliability-corrected profile concordance.

### 5.10 H1d — status gradient (F2; ecological, descriptive of structure; review M9, M11)
**Primary estimator (lead decision): REML random-effects meta-regression with Knapp–Hartung**,
δ̂(n) on centred log GDP per capita PPP (WDI `NY.GDP.PCAP.PP.KD`, 2022, `config/country_covariates.csv`;
origins without a value excluded and listed, currently Yemen), fitted in the 21-dimensional contrast
space with the CV-level sampling covariance plus a residual between-origin variance, t(k − 1 − p).
The design-based finite-population slope is reported as a sensitivity analysis only (it ignores the
between-origin residual variance and is anti-conservative for a claim about a gradient). Decision
quantity: predicted difference across the covariate's interdecile range, null if its 90 % CI lies within
±SESOI (1 point). Pre-registered sensitivity slopes: log GDP adjusted for the World Bank sub-Saharan
indicator (`wb_sub_saharan`), the sub-Saharan indicator alone, income group (ordinal), excluding
fallback-year origins. Fragile-and-conflict-state (FCS) status is not available from the World Bank API
and is not used. Occupation-specific slopes are exploratory. H1d is an ecological association across
origins: income is collinear with race (Horn of Africa) and conflict, so a slope is descriptive of
structure, not a test of status → competence.

## 6. RQ2 — Arab-origin signals vs benchmarks (F2)
Δ(Ā, b) via §4 (host-adjusted, §4a) with TOST and labels; Δ(DEU, NONE) descriptive; R1 versions on 19 origins; per-origin
Δ(n, DEU) and Δ(n, POL) exploratory with the positive-control yardstick. Ā–TUR is the closest match on
non-EU legal status; Ā–POL compares with a foreign EU national (review M10).

## 7. RQ3 — neutrality instruction (F2)
H3b: per-CV difference-in-differences of the host-adjusted [Ā − DEU] values (each condition with its own η̂),
stratified t, TOST. H3a: variance-scale test of
Δσ̂² with a paired CV bootstrap (inflated, t(I − #occupations)); SD-scale effect with 95 %/90 % bootstrap
intervals; equivalence if the 90 % interval lies within ±SESOI. Readings: attenuation / amplification /
overcorrection / no change / inconclusive; baseline-null prefix per hypotheses.md.

## 8. Interaction (profile) tests — exploratory
Nationality × model, × condition, × wording (R3): within-CV permutation of level labels jointly over
nationalities.

## 9. Manipulation check (review M1)
PC = positive-control clone minus NONE clone (baseline). **One-sided:** passed iff PC < 0 and the
one-sided 95 % upper limit is below 0; a wrong-signed effect fails. It shows that the model reads the
CV, not that the design is sensitive at SESOI scale (sensitivity is what H1b and TOST establish).
"Null" RQ1 labels require a passed manipulation check.

## 10. Missing data and bounds (review M2)
* Only `ok` rows carry outcomes; all statuses are counted per task × model × condition × arm; parser
  diagnostics (`n_json_objects`, `near_miss`) are carried but never used to coerce outcomes.
* **Non-ok includes terminal `api_error`.** Transport errors are retried by the runner; an `api_error`
  record that remains terminal is a missing cell like any other non-ok response. It counts as non-ok in
  the differential-missingness outcome and is treated like other non-ok cells in the single-value
  imputation sensitivity and the Manski bounds.
* Differential missingness is an outcome (P2): within-CV permutation test of the total non-ok share
  across nationalities, reported with the shares split by type (api_error, refusal, malformed_json,
  schema_violation, empty); if it rejects, R5 becomes a co-primary sensitivity analysis and the
  logical-support bounds become decision-relevant (below).
* **R5 — worst-case (Manski) bounds for Δ contrasts** (review M2; round 2, N3): lower bound = non-ok
  calls of the 22 Arab origins at the lower support limit and of the benchmark at the upper limit; upper
  bound = the reverse. **Pre-registered for the robust label: observed support**, i.e. the CV-specific
  range (minimum / maximum of the valid responses of the same base CV across its clones, wordings and
  replicates in that model × condition). **Logical support** (scale limits 0/100) is reported with the
  width of the identified interval (`manski_bounds.csv`) and is descriptive; it becomes decision-relevant
  (must also pass for "robust") only if the differential-missingness test rejects for that model ×
  condition. With 0–100 support the bounds are about 10 points wide at 2–5 % non-ok against a 1-point
  SESOI, so a label based on them alone would carry no information. Robust for R5 = both scenario CIs
  exclude 0 with the main sign.
* **SVI — single-value imputation sensitivity** (formerly mislabelled "R5 bounds"): every non-ok call
  imputed as the lowest / highest observed value (interview no/yes). Not a bound; used for σ_A, for
  which no simple worst-case bound exists, and labelled as such in the robustness table.

## 11. Smallest effect sizes of interest (OPEN DECISION; review H4)

| quantity | default (config) | alternatives | reasoning |
|---|---|---|---|
| `overall_fit` contrasts and σ_A | **1.0 point** | anchor to the fit shift that moves the interview rate by the interview SESOI (pilot fit→interview link, NONE clones, blind) | the adversarial review reports an LLM CV-audit Arab penalty of −1.41 points (1–100 scale; Lippens 2024, checked by the reviewer against the full text) that translates into a large selection-rate gap at a cutoff; a 2-point SESOI would have labelled that effect trivial |
| `interview` contrasts | **5 pp** | 2 pp; four-fifths heuristic (10 pp at a 50 % base rate) | "out of 100 identical applicants, fewer than 5 more/fewer invited" |
| forced choice | 0.45–0.55 (±0.20 logit) | 0.40–0.60 | as for interview |
| H1d | 1.0 point across the covariate IDR | follows the fit SESOI | translates the fit SESOI to a slope |

Trade-off stated in advance: with 1 point, equivalence for Δ contrasts is likely unreachable
(most will be "inconclusive"); the power script reports the minimum detectable effects instead. The
SESOI is never changed to fit the budget.

## 12. Forced choice — Bradley–Terry (exploratory, RQ4)
logit P(A) = γ_k + (β_{n_A} + θ_{i_A}) − (β_{n_B} + θ_{i_B}) + η_FC·(host_A − host_B); Σ_A β = 0; position
bias per wording; CV nuisance terms; weak ridge; product-weight CV bootstrap; debiased σ_A^FC; swap
randomisation test (quads with a host national are not swapped); host-free sensitivity (§4a).
NONE and placebo nationalities never appear.

## 13. RQ4 — response format (exploratory)
IE-implied comparisons for the same prompts (all IE draws), same BT model without position term;
debiased dispersion ratio, plug-in ratio with CI, concordance with CI, tie-free sensitivity. Caveats:
no ties in FC; concordance uninterpretable when σ_A ≈ 0.

## 14. SQ1 — principle vs behaviour (descriptive)
E_m from keyed target items (item-balanced, bootstrap over items); control items scored against
`expected_answer`; classification gap / substantive gap / consistent / unclassifiable using the headline
RQ1 label and the H2 labels. No combined index. Because reverse-keyed items are blatant, E_m ≈ 1 and the
"gap" label may be nearly automatic (review L11); this is reported as such.

## 15. Robustness (experimental_design.md §8)
R1 (19 origins), R2 (interview families), R3 (per wording + profile test + profile correlation), R4
(greedy arm), R5 (Manski bounds for Δ; SVI for σ_A), R6 (leave-one-occupation-out), R7 (tier),
R8 (within-CV ranks), R9 (= H2b, H2d), R11 (inside H1d), R12 (withdrawn 2026-09-30: native-German arm removed), R13 (shrinkage),
HX (host-national clones excluded, 22 and 19 origins; §4a). All checks except HX use the host-adjusted
estimators.
"Robust" = sign holds and CI excludes 0 under R1, R3 (≥ 2 of 3 wordings), R4, R5 (observed-support
Manski bounds; plus logical-support bounds if differential missingness rejected; SVI for σ_A) and HX
(both the 22- and the 19-origin version; `host_exclusion_required_for_robust: true`).

## 16. Blind mode (A15)
Outputs: design and balance checks; parse/refusal diagnostics (differential missingness as one omnibus
p-value); manipulation checks (positive control, tiers); scale use per tier (P3; review L6);
forced-choice position diagnostics (P7); principle-probe summaries (P8); text-flag and pronoun base rates
without nationality breakdown (P9, P11); variance components with 80 % upper limits (P6). No per-origin
means, contrasts, rankings, σ_A, placebo comparison, nationality tests, host-national effect (η, η_FC) or
host-exclusion results. (The variance components are not host-adjusted; a host bonus enlarges σ_ατ
slightly, which is conservative for planning.)

## 17. Variance components and power (review M14)
Moment estimates of the §1.6 components per model × condition × outcome; **80 % upper limits** from a
stratified CV bootstrap (90th percentile, n_boot_vc = 200); `variance_components.json` carries the
"upper" block (largest upper limit over models × conditions) with ρ_ε = 0 for planning.
`analysis/power_analysis.py` (fast engine, ≥ 2,000 simulations per cell for the Stage B decision,
M = 3 models by default) reports H1a power and size, H1b power, minimum-effect power at 2 × SESOI, TOST
power, SE of δ̂(n) against SESOI/2.5, and the minimum detectable effects when a target is unreachable at
the authoring ceiling. Mock-provider output must not be used for sizing.

## 18. Confirmatory vs exploratory

| status | analyses |
|---|---|
| **Confirmatory (F1)** | H1a, H1b (noncentral F and sphericity-free), minimum-effect test; 22 and 19 origins; per model; `overall_fit`, baseline |
| **Secondary confirmatory (F2)** | H1c; H1d (primary covariate); H1e; H2a–d; H3a–b |
| Robustness | R1–R13, HX (host exclusion), R2 = interview versions of all families; H1d sensitivity slopes; host-free BT |
| Descriptive | PC, λ, Δ(DEU, NONE), σ_A,net, E_m, SQ1 classification, variance components; **host-national effect η and η_FC** (secondary, never confirmatory) |
| **Exploratory** | per-origin δ(n), Δ(n, DEU), Δ(n, POL); profile tests; BT and RQ4; text flags; pronouns; confidence; occupation-specific H1d slopes; MS1–MS3 |

## 19. Reproducibility
Seed and all settings from the confirmatory config; its hash, git commit and analysis-code hash in
`summary.md`; every deviation recorded in `research/design_decisions.md`.

## 20. Open points for the lead
1. SESOI values remain an OPEN team decision (new defaults 1.0 / 5 pp / 0.45–0.55 / 1.0).
2. The freeze file is written and committed by the team when Stage A is frozen; the analysis only
   checks it. Until the project is committed, every run is stamped EXPLORATORY OVERRIDE because the
   confirmatory config is not committed at HEAD.
3. Host-national status (§4a) is pre-specified as a single common η. A host bonus that differs by
   origin (e.g. larger for Gulf nationals) is not separable from τ_n with 8 base countries × 6 CVs
   beyond what HX shows; heterogeneity of the host effect is not modelled and would be a deviation.
   `preregistration.md` and `research/hypotheses.md` should mention §4a and HX before the freeze
   (the statistician does not edit them).
