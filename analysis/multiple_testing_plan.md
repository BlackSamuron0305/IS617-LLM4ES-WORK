# Multiple-testing plan

Version 0.4, 2026-10-01 (host-national status, SAP §4a). Implements the multiplicity table of
`research/hypotheses.md` §0 / `preregistration.md`; code: `pipeline._families`, `multiplicity.py`.

## 1. Hierarchy

| tier | what | error control | output |
|---|---|---|---|
| 1 | **Global test** per model: H1a (22 Arab origins equal), and separately for the 19 uncontested origins | FWER, Holm across models, one family per origin set (F1, F1 19 origins) | `confirmatory.csv` |
| 1b | **Equivalence** per model: H1b (σ_A < SESOI) by the noncentral-F test and by the sphericity-free calibrated bootstrap test; 22 and 19 origins | FWER, Holm across models within each of the four families (equivalence requires both tests) | `confirmatory.csv` |
| 1c | **Minimum-effect test** per model: σ_A > SESOI (needed for "meaningful heterogeneity"); 22 and 19 origins | FWER, Holm across models (F1-min, F1-min 19 origins) | `confirmatory.csv` |
| 2 | **Model-based estimates with CIs**: σ_A (noncentral-F CI), Δ(Ā, b), per-origin δ(n) and Δ(n, DEU) with marginal 95 % CIs **and simultaneous 95 % bands** (max-|t| bootstrap); all host-adjusted (SAP §4a) | estimation, no significance claims | `heterogeneity.csv`, `contrasts.csv`, `coefficients.csv`, `origin_deviations.csv` |
| 2b | **Host-national effect** η per model × condition × outcome (and η_FC in forced choice): secondary, descriptive, 95 % CI only | none: no family, no Holm, no decision label; never confirmatory; not reported in blind mode | `host_effect.csv`, `bt_summary.csv` |
| 3 | **Small set of pre-registered secondary tests** (F2) | FWER, Holm **within** each sub-family | `confirmatory.csv` |
| 4 | **Exploratory pairwise / per-origin** comparisons | FDR, Benjamini–Hochberg q = .05, labelled exploratory | `origin_deviations.csv`, `coefficients.csv`, `text_flag_tests.csv` |

F2 sub-families (each Holm-adjusted across all its tests; sub-families answer
distinct questions and are not adjusted against each other):

| sub-family | members | size with M models |
|---|---|---|
| H1c | equal σ_A across models (one Wald test per condition) | 1 |
| H1d | status gradient (primary covariate), one per model | M |
| H1e | σ_A − σ_placebo, one per model; label "exceeds / below / not distinguishable from placebo spread" from the 95 % bootstrap CI, directional only if the Holm-adjusted p < α | M |
| H2 | Δ(Ā, DEU), Δ(Ā, POL), Δ(Ā, TUR), Δ(Ā, NONE) per model | 4M |
| H3 | ΔD_σ (H3a) and ΔD_DEU (H3b) per model | 2M |

Why no 231 pairwise significance claims: the 22 origins give 231 pairwise
differences per model × condition × outcome. Testing them one by one at α = .05
would produce about 11 false "differences" per cell even if all origins were
treated identically. The omnibus test (tier 1) answers whether any difference exists;
σ_A (tier 2) says how large the spread is; individual origins are shown with
simultaneous bands (which hold for all 22 at once) and BH q-values, and no origin is
called "most" or "least" favoured unless its simultaneous band excludes the Arab mean.

## 2. The two primary-candidate outcomes

A1 makes `overall_fit` the single primary outcome, so no α is split between outcomes.
`interview` (percentage points) is the key secondary outcome: every family is
repeated on it with the **same structure and its own Holm adjustment**, labelled
"R2:" (robustness), and it can support but never replace a primary conclusion.
Rationale: the fit score is continuous and more informative per call; the interview
decision is closer to the callback construct and practically more meaningful, which
is why it is always reported alongside, but promoting it to co-primary would halve
α for the primary question.

The RQ1 headline label requires both the 22- and the 19-origin analyses (intersection–union logic:
claiming a result for both sets needs no further adjustment).

## 3. Decision labels respect the multiplicity adjustment

The four-way labels (effect / effect exceeds SESOI / trivial / null (equivalence) /
inconclusive) for confirmatory estimands use

* "CI excludes 0" := Holm-adjusted p < α within the family, and
* "equivalence established" := Holm-adjusted TOST p < α within the same family
  (H2, H3b); for H3a (bootstrap interval) the equivalence decision comes from its own interval;
  for σ_A it requires the Holm-adjusted noncentral-F test AND the Holm-adjusted sphericity-free test;
* "meaningful heterogeneity" := Holm-adjusted minimum-effect test p < α (the 95 % lower bound of σ_A
  exceeds the SESOI). H1a rejecting alone gives "heterogeneity present; size relative to SESOI
  undetermined".

So a label never claims an effect or an equivalence that the family-wise procedure
does not support. Unadjusted labels are kept in `contrasts.csv` / `rq3.csv` for
transparency. The joint RQ1 reading (`rq1_decision.csv`) uses the Holm-adjusted H1a
and H1b p-values; "null" additionally requires a detected positive control.

## 4. What is not adjusted

* Robustness checks (R1–R13, HX) are not additional hypotheses; they qualify a
  confirmatory result as "robust" (sign and CI under R1, R3 ≥ 2/3, R4, R5 and HX, the host-national
  exclusion in its 22- and 19-origin versions).
* The host-national effect η (and η_FC) is a nuisance parameter of the primary model reported for
  transparency. Its p-value is unadjusted and must not be read as a test of a hypothesis; a claim
  about local-applicant preference would be a new, exploratory question.
* Descriptive quantities (PC, λ, E_m, variance components) carry CIs only.
* Exploratory analyses outside tier 4 (forced choice / RQ4, interaction profile
  tests, sub-regional share, text flags other than the Arab–DEU tests, MS1–MS3) are
  reported with unadjusted CIs / p-values and labelled exploratory.

## 5. Family-wise error rate is per family

FWER is controlled within each family, not across the whole study. This follows the
convention that distinct research questions are separate families (hypotheses.md).
A stricter alternative (Holm across F1 and all F2 sub-families) is available by
concatenating the p-values in `confirmatory.csv`; switching would be a documented
deviation.
