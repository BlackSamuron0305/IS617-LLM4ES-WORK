# Model specifications

Version 0.4, 2026-10-01 (host-national fixed effect, SAP §4a). Companion to `statistical_analysis_plan.md`.
Confirmatory settings (SESOIs, alpha, resampling counts) come from `config/analysis_settings.csv`. Formulas use
statsmodels formula syntax. In code the models are built from the statsmodels
submodules (`statsmodels.regression.linear_model.OLS.from_formula`,
`MixedLM.from_formula`, `GEE.from_formula`) because `statsmodels.api` /
`statsmodels.formula.api` import a compiled extension that an application-control
policy blocks on one team machine; the formulas are identical to the `smf.*` spellings.

## 0. Conventions

| item | choice |
|---|---|
| rows entering nationality models | `arm == "primary"`, `clone_type == "counterfactual"`, `parse_status == "ok"`, `nationality_group != "placebo"` (placebo only in H1e) |
| outcome scales | `overall_fit` in points (0–100); `interview` × 100 = percentage points |
| unit of analysis (primary) | stimulus mean over replicates, then over the K wording variants: μ̄(i, n); a missing wording is imputed additively within the CV (nationality + wording) before averaging |
| reference level (nationality) | `DEU` (treatment coding): `C(nationality, Treatment(reference="DEU"))` |
| within-Arab parametrisation | deviation (sum-to-zero over the 22 Arab codes): δ(n) = τ(n) − τ̄_A |
| other factors | treatment coding, reference = first level alphabetically (`prompt_variant` k1, `qualification_tier` adequate, `occupation` first) — nuisance only |
| clusters | base CV (`base_cv_id`); strata = occupation |
| host-national indicator | `host_national` = 1[nationality == base_country of the CV] (0/1 covariate; 1 Arab clone per CV) |
| α | .05 two-sided; TOST at 90 % CI |

## 1. Primary estimator (closed form of the CV fixed-effects model)

Model on the (CV × nationality) matrix of μ̄ for one model × condition × outcome:

    ybar_in = alpha_i + tau_n + eta * H_in + e_in      (i: base CV, n: nationality)
    H_in    = 1[n == base_country(i)]                  (host national)

* alpha_i — base-CV fixed effect (absorbs occupation, tier, base country and everything else about the CV).
* tau_n — nationality effect; with the CV fixed effects, tau_n − tau_DEU is identified.
* eta — common host-national effect (points): a clone whose nationality matches the CV's country vs the
  same origin's clone in a CV set elsewhere. Secondary, descriptive (`host_effect.csv`).
* e_in — CV × nationality interaction plus averaged decoder noise.

Host effect (code: `core.host_fit`): X = H residualised on both fixed effects over the observed cells
(alternating projections), eta_hat = Σ X·Y / Σ X², identical to the dummy-variable OLS coefficient;
per-CV influence u_i = Σ_n X_in r_in / Σ X² (r = full-model residuals), CV-clustered SE from
t_summary(eta_hat + u_i / w_i).

Closed form used in code: for any contrast (target set T vs comparison set C),
d_i = mean_{n∈T} ybar_in − mean_{n∈C} ybar_in, estimate = equal-weight mean of occupation means
M[d_i] − eta_hat · M[d_i(H)] (host-adjusted), computed as the stratified mean of
psi_i = d_i(Y) − eta_hat d_i(H) − M[d_i(H)] u_i / w_i (w_i = weight of CV i in M), SE from
within-occupation variances of psi, Welch–Satterthwaite df (code: `core.contrast_values`). Sensitivity
HX: host cells set to missing, no eta.

| contrast | T | C | meaning in plain words |
|---|---|---|---|
| Δ(n, DEU) | {n} | {DEU} | points by which origin n's clone scores above (+) or below (−) the German clone of the same CV, on average over CVs |
| Δ(Ā, b) | 22 Arab codes | {b} | same for the average Arab-origin clone vs benchmark b |
| δ(n) | {n} | 22 Arab codes | how far origin n sits from the Arab average |
| ΔD_DEU | DiD of Δ(Ā, DEU) between neutrality and baseline (per CV) | | change of the Arab–German gap caused by the instruction |
| PC | positive-control clone | NONE clone | effect of removing one must-have line |

## 2. σ_A (randomised-block ANOVA on the 22 Arab columns)

All quantities below are computed on ybar − eta_hat·H (eta re-estimated on the analysed columns, and in
every bootstrap / permutation / calibration replicate); df_res loses one; with c_n the centred column
mean of the row-centred H, the noise term gains mean_n c_n² / Σ X² (equivalently 1/I is replaced by
I_eff^-1 = mean(1/I_n) + (J/(J−1)) mean_n c_n²/ΣX², and F is scaled by mean(1/I_n)·I_eff). Permutations keep
host cells fixed. Without host cells the formulas reduce to the unadjusted ones:

    MS_nat = I * sum_n (delta_hat_n)^2 / (J - 1)
    MS_res = sum_{i,n} (ybar_in - rowmean_i - colmean_n + grand)^2 / ((I - 1)(J - 1))
    sigma2_A_hat = ((J - 1) / J) * (MS_nat - MS_res) / I          (J = 22)
    F = MS_nat / MS_res  ~  noncentral F(J - 1, (I - 1)(J - 1), lambda = I J sigma2_A / sigma2)

Missing cells: row-centring and column means use available cells; 1/I is replaced by
the mean of 1/I_n over columns; df_res = #observed − #rows − J + 1.

Tests and bounds built on this decomposition (λ_S = I J SESOI² / MS_res):

    H1b (equivalence):     p = ncf.cdf(F_obs; J-1, df_res, lambda_S)       reject => sigma_A < SESOI
    minimum-effect test:   p = ncf.sf(F_obs;  J-1, df_res, lambda_S)       reject => sigma_A > SESOI
    one-sided 95% limits:  noncentral-F inversion (upper for H1b, lower for "meaningful")

Sphericity-free equivalence (review M3): T = (sigma2_hat - SESOI^2) / se_boot, se_boot from a
stratified CV bootstrap × sqrt(n_j/(n_j-1)); critical value q = 5% quantile of T over n_cal
simulations that resample residual rows e_i = y_i - rowmean_i - colmean + grand (scaled by
sqrt(IJ/((I-1)(J-1)))) within occupation and add a pattern with sigma_A = SESOI; equivalence iff
T_obs < q; bound U = sqrt(sigma2_hat - q se_boot). Also reported: residual variance per column and the
Greenhouse–Geisser epsilon of the CV × nationality covariance.

sigma_A net of sub-regions (G groups): sigma2_net = (1/J) Σ (delta_n − mean_g(n) delta)² − ((J−G)/J)·MS_res·mean(1/I_n).

Placebo comparison (H1e): d = sigma2_A − sigma2_placebo on the same CVs; se from a shared stratified CV
bootstrap (inflated); t(I − #occupations); SD-scale percentile CI for sigma_A − sigma_placebo.

## 3. Cross-check MS1 — CV fixed effects OLS (statsmodels)

    y ~ C(nationality, Treatment(reference="DEU")) + host_national + C(prompt_variant) + C(base_cv_id)

Data: stimulus (variant-level) means, one model, baseline. The `host_national` coefficient (row
`term == "host_national"`) is the model-based counterpart of eta. Fit:
`.fit(cov_type="cluster", cov_kwds={"groups": cv_codes, "use_correction": True})`,
t(G − 1) reference. Coefficient `C(nationality...)[T.n]` = Δ(n, DEU) in points (or
pp). `C(prompt_variant)[T.k]` = level shift of wording k vs k1 (nuisance). Under a
balanced design the nationality coefficients equal the closed-form estimates.
Fallback: none needed (OLS always fits); if the CR1 matrix is singular only the
point estimates are used.

## 4. Cross-check MS2 — replicate-level linear mixed model (overall_fit)

    overall_fit ~ C(nationality, Treatment(reference="DEU")) + host_national + C(prompt_variant)
                  + C(qualification_tier) + C(occupation)
    groups = base_cv_id, re_formula = "1", vc_formula = {"stimulus": "0 + C(nationality)"}

* Random intercept per base CV = σ²_α; variance component "stimulus" = CV ×
  nationality deviation σ²_ατ (+ σ²_ατκ/K absorbed); residual = σ²_ε (+ variant
  interactions).
* Nationality coefficients = Δ(n, DEU) conditional on CV (identical meaning to MS1
  because the model is linear).
* REML. Fallback chain: `method="lbfgs"` → `method="powell"` → random-intercept LMM
  on stimulus means (`groups = base_cv_id`) → report failure and rely on MS1 / the
  primary estimator. Convergence status and warnings are written to
  `sensitivity_status.csv`.

## 5. Cross-check MS3 — GEE logit for interview

    interview ~ C(nationality, Treatment(reference="DEU")) + host_national + C(prompt_variant)
                + C(qualification_tier) + C(occupation)
    groups = base_cv_id, family = Binomial(logit), cov_struct = Exchangeable()

(`host_national` is dropped from MS1–MS3 only if it does not vary, e.g. data without base countries.)

Coefficients = population-averaged log-odds ratios of an interview recommendation
vs the German clone; `odds_ratio = exp(coef)` with robust (sandwich) CIs. Odds ratios
are non-collapsible and depend on the baseline rate, so the confirmatory interview
estimands stay on the percentage-point scale; MS3 checks direction and existence only.
Fallback: `Independence()` working correlation; separation (a nationality at 0 % or
100 %) is flagged when a robust SE exceeds 10.

## 6. Variance components (planning model, experimental_design.md §1.6)

    Y_inkr = mu + a_i + t_n + (at)_in + k_k + (tk)_nk + (ak)_ik + (atk)_ink + e_inkr

Estimated by moments per model × condition × outcome:

| component | estimator |
|---|---|
| σ²_ε | pooled within-stimulus variance of replicates |
| ρ_ε | pooled cross-nationality covariance of within-stimulus-centred residuals at the same (CV, variant, replicate) ÷ pooled variance |
| σ²_ατκ | MS_ink − (1 − ρ_ε) σ²_ε / r̄ |
| σ²_ατ | (MS_in − MS_ink) / K |
| σ²_ακ | (MS_ik − MS_ink − N ρ_ε σ²_ε / r̄) / N |
| σ²_τκ | (MS_nk − MS_ink) / I (nationality × wording, fixed; size only) |
| σ²_α | variance of CV means within occupation × tier minus the implied noise share |

Negative moment estimates are truncated at 0. Missing stimulus cells are filled by
Yates-type iterative imputation from the model with all two-way terms, and the
residual df is reduced by the number of filled cells. With one replicate σ²_ε and
ρ_ε are not estimable (reported as missing) and σ²_ατκ then includes decoder noise.

## 7. H1d meta-regression (primary estimator by lead decision; ecological)

    delta_hat = X beta + u + e,   u ~ N(0, tau2_res I),   e ~ N(0, S)
    X = centred covariates (first = focal: log GDP per capita PPP), S = CV-level sampling covariance

Variants: log GDP (primary); log GDP + wb_sub_saharan; wb_sub_saharan alone; income group (0–3);
excluding fallback-year origins; per occupation (exploratory). Knapp–Hartung df = k − 1 − p.
The design-based slope (mean over CVs of each CV's OLS coefficient) is a sensitivity analysis.

Fitted in the (k−1)-dim contrast space z = Q delta_hat (Q: Helmert rows orthogonal to 1),
so V = tau2_res I + Q S Q', intercept eliminated. REML for tau2_res (bounded 1-D
optimisation), GLS for beta, Knapp–Hartung SE (truncated at the model SE), t(k − 1 − p).
β_W = change in δ (points) per unit of log income (≈ per 2.7-fold income ratio).

## 8. Bradley–Terry

    logit P(A chosen) = gamma[k] + beta[n_A] - beta[n_B] + theta[i_A] - theta[i_B]
                        + eta_FC * (host_A - host_B)

Penalised Newton–Raphson on the prompt-level aggregated binomial likelihood
(sparse design). Constraints: β_DEU = 0 during fitting, then re-expressed with
Σ_A β = 0; θ with ridge 1e-4 (identifiability); β with ridge 0.01 (separation).
β_n = log-odds that origin n's candidate is chosen over an otherwise equivalent
candidate at the Arab-average worth; γ_k = log-odds of choosing slot A under
wording k when the two candidates are equivalent. η_FC (unpenalised) = log-odds bonus of a
host-national candidate (both CVs of a pair share the base country); reported with a CV-bootstrap
percentile CI (secondary). Sensitivity: quads with a host national dropped, no host term. The
within-Arab swap test swaps only quads without a host national. Fallback: a bootstrap replicate
that does not converge or shows |β| > 15 is discarded and counted (`n_boot_failed`).

## 9. Interaction (profile) tests

For levels ℓ (models, conditions or wordings) on the same CVs:
Z_ℓ = Y_ℓ − rowmean(Y_ℓ); P_ℓ = colmeans(Z_ℓ); T = Σ_ℓ Σ_n (P_ℓn − mean_ℓ P_ℓn)².
Null by permuting ℓ within each CV (jointly over nationalities). Parametric
alternative (not used for inference because the cluster-robust covariance of
21 × (L − 1) interaction terms is singular with ≤ 48 clusters):

    y ~ C(nationality) * C(model) + C(base_cv_id):C(model)
