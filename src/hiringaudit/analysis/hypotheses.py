"""Confirmatory and secondary hypothesis machinery (research/hypotheses.md).

Decision labels follow the four-way rule of Lakens, Scheel & Isager (2018) as
fixed in hypotheses.md §0. Nothing here interprets results; it only applies
pre-registered rules to numbers.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import optimize, stats

from .core import _nanmean, t_summary

# --------------------------------------------------------------------------- #
# Decision rules
# --------------------------------------------------------------------------- #


def decision_label(ci_low: float, ci_high: float, equivalent: bool, sesoi: float,
                   rejects: bool | None = None) -> str:
    """Four-way rule: effect / effect exceeds SESOI / trivial effect / null (equivalence) / inconclusive."""
    if not (np.isfinite(ci_low) and np.isfinite(ci_high)) and rejects is None:
        return "not estimable"
    excl = bool(rejects) if rejects is not None else bool(ci_low > 0 or ci_high < 0)
    if excl and not equivalent:
        if np.isfinite(ci_low) and np.isfinite(ci_high) and (ci_low > sesoi or ci_high < -sesoi):
            return "effect exceeds SESOI"
        return "effect"
    if excl and equivalent:
        return "trivial effect"
    if equivalent:
        return "null (equivalence)"
    return "inconclusive"


RQ1_MEANINGFUL = "meaningful heterogeneity (95% lower bound of sigma_A exceeds SESOI)"
RQ1_PRESENT = "heterogeneity present; size relative to SESOI undetermined"
RQ1_TRIVIAL = "trivial heterogeneity (present but below SESOI)"
RQ1_NULL = "null: a single category is adequate for this model"
RQ1_NULL_NO_PC = "null not claimed: manipulation check (positive control) not passed"


def rq1_label(p_h1a: float, p_h1b: float, p_min: float, sf_equivalent: bool, pc_detected: bool,
              alpha: float = 0.05) -> str:
    """Joint reading of H1a (omnibus), H1b (equivalence) and the minimum-effect test (review M4).

    * "meaningful" requires the minimum-effect test (H0: sigma_A <= SESOI) to reject, i.e. the
      one-sided 95% lower bound of sigma_A exceeds the SESOI.
    * equivalence ("trivial" / "null") requires BOTH the noncentral-F H1b test and the
      sphericity-free calibrated bootstrap test (review M3).
    * "null" additionally requires a passed manipulation check (positive control).
    All p-values passed in should already be Holm-adjusted within their families.
    """
    if not (np.isfinite(p_h1a) and np.isfinite(p_h1b)):
        return "not estimable"
    equiv = bool(p_h1b < alpha and sf_equivalent)
    if p_h1a < alpha:
        if np.isfinite(p_min) and p_min < alpha:
            return RQ1_MEANINGFUL
        if equiv:
            return RQ1_TRIVIAL
        return RQ1_PRESENT
    if equiv:
        return RQ1_NULL if pc_detected else RQ1_NULL_NO_PC
    return "inconclusive"


def rq1_headline(label22: str, label19: str) -> str:
    """Headline RQ1 label: the strongest claim supported by BOTH the 22- and the 19-origin analyses
    (review H5)."""
    if label22 == label19:
        return label22
    effect = {RQ1_MEANINGFUL, RQ1_TRIVIAL, RQ1_PRESENT}
    if label22 in effect and label19 in effect:
        return RQ1_PRESENT
    return f"inconclusive: 22-origin ('{label22}') and 19-origin ('{label19}') analyses disagree"


H1E_ABOVE = "Arab spread exceeds placebo spread"
H1E_BELOW = "Arab spread below placebo spread"
H1E_NONE = "not distinguishable from placebo spread"


def h1e_label(ci_low: float, ci_high: float, p_holm: float, alpha: float = 0.05) -> str:
    """H1e decision rule (preregistration; lead decision 2026-09-30).

    "exceeds" iff the 95% CV-bootstrap CI of sigma_A - sigma_placebo lies above 0, "below" iff it lies
    below 0, otherwise "not distinguishable". H1e is a secondary family with Holm across models: a
    directional label also requires the Holm-adjusted p < alpha (otherwise it is downgraded to
    "not distinguishable"), so the label never claims more than the family-wise test supports.
    """
    if not (np.isfinite(ci_low) and np.isfinite(ci_high)):
        return "not estimable"
    holm_ok = bool(np.isfinite(p_holm) and p_holm < alpha)
    if ci_low > 0 and holm_ok:
        return H1E_ABOVE
    if ci_high < 0 and holm_ok:
        return H1E_BELOW
    return H1E_NONE


def rq3_label(label: str, change: float, base_est: float, base_ci: tuple[float, float],
              neu_ci: tuple[float, float], base_label: str | None = None) -> str:
    """Attenuation / amplification / overcorrection / no change (hypotheses.md RQ3).

    For a signed disparity (Delta): attenuation = change towards zero from the
    baseline sign. For sigma_A differences pass base_est = +1 (disparity is
    non-negative), so a negative change is attenuation.
    """
    prefix = ""
    if base_label is not None and base_label.startswith("null"):
        prefix = "baseline null -> read as 'does the instruction create disparities': "
    if label == "null (equivalence)":
        return prefix + "no change (within SESOI)"
    if label == "trivial effect":
        towards_zero = np.sign(change) == -np.sign(base_est) if base_est != 0 else False
        return prefix + f"no change within SESOI (trivial {'attenuation' if towards_zero else 'amplification'})"
    if label.startswith("effect"):
        if (base_ci[0] > 0 and neu_ci[1] < 0) or (base_ci[1] < 0 and neu_ci[0] > 0):
            return prefix + "overcorrection (sign reversal, both CIs exclude 0)"
        towards_zero = np.sign(change) == -np.sign(base_est) if base_est != 0 else False
        return prefix + ("attenuation" if towards_zero else "amplification")
    return prefix + label


# --------------------------------------------------------------------------- #
# H1c: equality of sigma_A across models; profile concordance
# --------------------------------------------------------------------------- #
def boot_inflation(strata: np.ndarray) -> float:
    """Factor correcting the downward bias of a stratified bootstrap variance (n_j / (n_j - 1))."""
    _, nj = np.unique(np.asarray(strata), return_counts=True)
    nj = nj[nj > 1]
    return float(np.mean(nj / (nj - 1))) if nj.size else 1.0


def h1c_equality(sigma2_obs: dict[str, float], boot: dict[str, np.ndarray], inflate: float = 1.0,
                 df2: float | None = None) -> dict:
    """Wald test of equal debiased sigma_A^2 across models (shared CV bootstrap).

    Tested on the variance scale (smooth, untruncated debiased estimator);
    equality of variances is equality of SDs. Covariance from bootstrap draws
    computed on the same base-CV resamples for every model, inflated by
    n_j/(n_j-1) (stratified-bootstrap bias). Reference distribution
    F(M-1, df2) with df2 = #CVs - #occupations (small-cluster correction; a
    chi2 reference was anti-conservative at pilot size in simulation).
    """
    models = list(sigma2_obs)
    M = len(models)
    if M < 2:
        return dict(W=np.nan, df=0, p=np.nan, models="|".join(models))
    s = np.array([sigma2_obs[m] for m in models])
    Bm = np.column_stack([boot[m] for m in models])
    Bm = Bm[np.isfinite(Bm).all(1)]
    V = np.cov(Bm, rowvar=False) * inflate
    C = np.hstack([np.ones((M - 1, 1)), -np.eye(M - 1)])
    d = C @ s
    try:
        W = float(d @ np.linalg.solve(C @ V @ C.T, d))
    except np.linalg.LinAlgError:
        W = np.nan
    if not np.isfinite(W):
        p = np.nan
    elif df2 is not None and df2 > 0:
        p = float(stats.f.sf(W / (M - 1), M - 1, df2))
    else:
        p = float(stats.chi2.sf(W, M - 1))
    return dict(W=W, df=M - 1, df2=df2, p=p, models="|".join(models), n_boot=int(Bm.shape[0]))


def profile_concordance(Ys: dict[str, np.ndarray], occupations: np.ndarray, tiers: np.ndarray,
                        n_splits: int, rng: np.random.Generator) -> pd.DataFrame:
    """Reliability-corrected correlation of delta profiles between models (§1.4 C).

    Split-half reliability per model: base CVs split in halves within
    occupation x tier, Pearson r between half profiles, Spearman-Brown
    corrected, averaged over ``n_splits`` random splits.
    rho_corrected = r(full profiles) / sqrt(rel_m * rel_m'); values > 1 are
    reported uncapped (they signal noisy reliabilities).
    """
    def prof(Y):
        Z = Y - _nanmean(Y, -1)[:, None]
        p = _nanmean(Z, 0)
        return p - np.nanmean(p)

    strata = pd.Series(list(zip(occupations, tiers))).astype(str).to_numpy()
    rel = {m: [] for m in Ys}
    for _ in range(n_splits):
        h = np.zeros(len(strata), bool)
        for s in np.unique(strata):
            idx = np.flatnonzero(strata == s)
            pick = rng.permutation(idx)[: idx.size // 2]
            h[pick] = True
        if h.sum() < 2 or (~h).sum() < 2:
            continue
        for m, Y in Ys.items():
            a, b = prof(Y[h]), prof(Y[~h])
            ok = np.isfinite(a) & np.isfinite(b)
            r = np.corrcoef(a[ok], b[ok])[0, 1] if ok.sum() > 2 else np.nan
            rel[m].append(2 * r / (1 + r) if np.isfinite(r) and r > -1 else np.nan)
    relm = {m: float(np.nanmean(v)) if v else np.nan for m, v in rel.items()}
    rows = []
    ms = list(Ys)
    for i in range(len(ms)):
        for j in range(i + 1, len(ms)):
            a, b = prof(Ys[ms[i]]), prof(Ys[ms[j]])
            ok = np.isfinite(a) & np.isfinite(b)
            r = float(np.corrcoef(a[ok], b[ok])[0, 1]) if ok.sum() > 2 else np.nan
            den = np.sqrt(relm[ms[i]] * relm[ms[j]]) if relm[ms[i]] > 0 and relm[ms[j]] > 0 else np.nan
            rows.append(dict(model_a=ms[i], model_b=ms[j], rho_raw=r, reliability_a=relm[ms[i]],
                             reliability_b=relm[ms[j]], rho_corrected=r / den if np.isfinite(den) else np.nan))
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- #
# H1d: status gradient (meta-regression of delta(n) on centred log income)
# --------------------------------------------------------------------------- #
INCOME_ORDER = {"Low income": 0, "Lower middle income": 1, "Upper middle income": 2, "High income": 3}


def _orth_contrast(k: int) -> np.ndarray:
    """(k-1, k) orthonormal rows orthogonal to the ones vector (Helmert)."""
    Q = np.zeros((k - 1, k))
    for r in range(1, k):
        Q[r - 1, :r] = 1.0
        Q[r - 1, r] = -r
        Q[r - 1] /= np.linalg.norm(Q[r - 1])
    return Q


def h1d_gradient(Y: np.ndarray, codes: list[str], strata: np.ndarray, covariates: dict[str, dict],
                 sesoi: float, alpha: float = 0.05, transforms: dict[str, str] | None = None) -> dict:
    """Meta-regression of delta(n) on centred origin covariates (H1d; ecological, descriptive).

    ``covariates`` maps a name to {code: value}; the FIRST covariate is the focal one (its
    coefficient beta_W is reported and its interdecile range defines the decision quantity);
    the others are adjusted for. ``transforms`` maps names to "log" (natural log) or "raw".

    (1) Primary: REML random-effects meta-regression with Knapp-Hartung t(k-1-p) inference:
        delta_hat carries the CV-level sampling covariance S (occupation-stratified) plus a
        residual between-origin variance tau2_res; fitted in the (k-1)-dim contrast space
        (Helmert basis) because delta_hat sums to zero.
    (2) Sensitivity: design-based finite-population slope (mean over CVs of each CV's OLS
        coefficient, stratified t), which ignores between-origin residual variance.
    Decision quantity: predicted difference across the focal covariate's interdecile range (IDR)
    among included origins; null if its 90% CI lies within +-SESOI.
    """
    transforms = transforms or {}
    names = list(covariates)
    inc = [c for c in codes if all(np.isfinite(covariates[nm].get(c, np.nan)) for nm in names)]
    excluded = [c for c in codes if c not in inc]
    k, p = len(inc), len(names)
    if k < p + 4:
        return dict(status=f"skipped: only {k} origins with all covariates", excluded="|".join(excluded))
    cols = np.array([codes.index(c) for c in inc])
    X = np.column_stack([np.array([covariates[nm][c] for c in inc], float) for nm in names])
    for j, nm in enumerate(names):
        if transforms.get(nm, "raw") == "log":
            X[:, j] = np.log(X[:, j])
    if np.any(np.std(X, 0) == 0):
        return dict(status="skipped: a covariate is constant among included origins", excluded="|".join(excluded))
    Xc = X - X.mean(0)
    idr = float(np.percentile(X[:, 0], 90) - np.percentile(X[:, 0], 10))
    Yi = Y[:, cols]
    ok = ~np.isnan(Yi).any(1)
    Yi, st = Yi[ok], np.asarray(strata)[ok]
    Z = Yi - Yi.mean(1, keepdims=True)
    # (2) design-based
    b_i = Z @ Xc @ np.linalg.inv(Xc.T @ Xc)
    td = t_summary(b_i[:, 0], alpha, st)
    # (1) REML in contrast space
    labs = np.unique(st)
    nj = np.array([np.sum(st == s) for s in labs])
    dbar = np.mean([Z[st == s].mean(0) for s in labs], axis=0)
    Zc = np.vstack([Z[st == s] - Z[st == s].mean(0) for s in labs])
    nu = max(Z.shape[0] - labs.size, 1)
    S = (Zc.T @ Zc / nu) * np.sum(1.0 / (labs.size ** 2 * nj))
    Q = _orth_contrast(k)
    z, Sz, Xz = Q @ dbar, Q @ S @ Q.T, Q @ Xc

    def neg_reml(t2):
        V = Sz + t2 * np.eye(k - 1)
        try:
            L = np.linalg.cholesky(V)
        except np.linalg.LinAlgError:
            return 1e12
        Vi = np.linalg.inv(V)
        XtViX = Xz.T @ Vi @ Xz
        b = np.linalg.solve(XtViX, Xz.T @ Vi @ z)
        r = z - Xz @ b
        sign, logdet = np.linalg.slogdet(XtViX)
        return float(0.5 * (2 * np.sum(np.log(np.diag(L))) + logdet + r @ Vi @ r))

    hi = max(float(np.var(z)) * 10, 1e-6)
    opt = optimize.minimize_scalar(neg_reml, bounds=(0.0, hi), method="bounded")
    t2 = float(opt.x) if neg_reml(opt.x) < neg_reml(0.0) else 0.0
    Vi = np.linalg.inv(Sz + t2 * np.eye(k - 1))
    A = np.linalg.inv(Xz.T @ Vi @ Xz)
    beta = A @ Xz.T @ Vi @ z
    r = z - Xz @ beta
    df = k - 1 - p
    q_kh = float(r @ Vi @ r) / df
    se_all = np.sqrt(np.diag(A) * max(q_kh, 1.0))          # truncated KH (never below model SE)
    b, se = float(beta[0]), float(se_all[0])
    tq, tq90 = stats.t.ppf(1 - alpha / 2, df), stats.t.ppf(1 - alpha, df)
    pval = float(2 * stats.t.sf(abs(b / se), df))
    pred, pred_se = b * idr, se * idr
    eq = bool(pred - tq90 * pred_se > -sesoi and pred + tq90 * pred_se < sesoi)
    lab = decision_label(b - tq * se, b + tq * se, eq, np.inf)
    return dict(status="ok", k=k, excluded="|".join(excluded), covariates="+".join(
                    f"{transforms.get(nm, 'raw')}({nm})" for nm in names),
                idr=idr, beta_W=b, se=se, df=df, ci_low=b - tq * se, ci_high=b + tq * se, p=pval,
                tau2_residual=t2, pred_diff_idr=pred, pred_ci90_low=pred - tq90 * pred_se,
                pred_ci90_high=pred + tq90 * pred_se, equivalent=eq, label=lab,
                beta_design=td.estimate, se_design=td.se, ci_low_design=td.ci_low,
                ci_high_design=td.ci_high, p_design=td.p, n_cv=td.n_cv,
                reading="ecological association across origins; not the causal effect of national income")


def load_covariates(path) -> tuple[pd.DataFrame | None, str]:
    """Read config/country_covariates.csv; returns (df, message)."""
    from pathlib import Path
    p = Path(path) if path else None
    if p is None or not p.exists():
        return None, f"country covariate file not found ({path}); H1d skipped"
    df = pd.read_csv(p)
    need = {"code", "gdp_pc_ppp_const"}
    if not need.issubset(df.columns):
        return None, f"country covariate file lacks columns {sorted(need - set(df.columns))}; H1d skipped"
    return df, f"covariates read from {p}"
