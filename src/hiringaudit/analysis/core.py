"""Core estimators for the independent-evaluation outcomes.

Levels (experimental_design.md §1.5): call -> stimulus -> base CV. Replicates
are averaged within stimulus (model x condition x wording variant x base CV x
nationality); stimulus means are then averaged over the K wording variants,
giving mu_bar(i, n) per model x condition x outcome. For one such cell the
data are a matrix ``Y[i, n]`` (base CV x nationality), NaN where no valid
response exists. Only ``clone_type == 'counterfactual'`` rows enter (A7).

Base CVs are the independent units:
* contrasts are averages of per-CV contrast values with occupation-stratified
  t inference (occupations are fixed strata, weighted equally),
* the bootstrap resamples base CVs within occupation,
* permutation tests shuffle nationality labels *within* a base CV.

Host-national status (setting 2026-10-01). Every base CV is set in one Arab League base country;
the clone whose nationality equals the base country is a host national (one Arab clone per CV;
benchmarks, placebos and NONE never are). The primary estimators adjust for a common host-national
fixed effect eta in the clone-level model

    ybar_in = alpha_i + tau_n + eta * H_in + e_in,      H_in = 1[n == base_country(i)],

so delta(n), sigma_A and the contrasts are nationality effects net of a common host bonus (the CV
effects alpha_i already absorb the base country). ``host_fit`` estimates eta by least squares
(Frisch-Waugh: H and Y residualised on the CV + nationality fixed effects over the observed cells)
and returns per-CV influence values, so the stratified-t machinery carries eta's estimation error
(``host_adjusted_values``). ``twoway_stats(Y, H)`` re-estimates eta inside every bootstrap and
permutation replicate; permutation tests then keep host cells fixed and shuffle only the non-host
cells of a CV (exact under the sharp null that non-host labels do not matter).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from scipy import optimize, stats

from .schema import REFERENCE

STIM_KEYS = ["model_alias", "prompt_condition", "prompt_variant", "base_cv_id", "nationality"]


# --------------------------------------------------------------------------- #
# Aggregation
# --------------------------------------------------------------------------- #
def counterfactual(ev: pd.DataFrame) -> pd.DataFrame:
    return ev[(ev["clone_type"] == "counterfactual").fillna(False)]


def nationality_order(ev: pd.DataFrame) -> list[str]:
    """Canonical display order: Arab by subregion then code, benchmarks, control."""
    meta = counterfactual(ev).drop_duplicates("nationality").set_index("nationality")
    grp_rank = {"arab": 0, "benchmark": 1, "control": 2}
    bench_rank = {REFERENCE: 0, "POL": 1, "TUR": 2}

    def key(c):
        g = meta.at[c, "nationality_group"]
        return (grp_rank.get(g, 3), str(meta.at[c, "subregion"]) if g == "arab" else "",
                bench_rank.get(c, 9), c)

    return sorted(meta.index.astype(str).tolist(), key=key)


def aggregate_stimulus(ev: pd.DataFrame, outcome: str) -> pd.DataFrame:
    """Average valid replicates within stimulus (counterfactual clones only).

    One row per (model, condition, variant, base CV, nationality) present in
    ``ev`` (stimuli with zero valid calls get ``y = NaN``), with ``y, n_valid,
    n_total, var_within`` and CV / nationality metadata.
    """
    ev = counterfactual(ev)
    valid = ev[(ev["parse_status"] == "ok").fillna(False) & ev[outcome].notna()]
    agg = (valid.groupby(STIM_KEYS, observed=True)[outcome]
           .agg(y="mean", n_valid="count", var_within="var").reset_index())
    tot = ev.groupby(STIM_KEYS, observed=True).size().rename("n_total").reset_index()
    stim = tot.merge(agg, on=STIM_KEYS, how="left")
    stim["n_valid"] = stim["n_valid"].fillna(0).astype(int)
    cv_cols = ["base_cv_id", "occupation", "qualification_tier"] + (["base_country"] if "base_country" in ev else [])
    cv_meta = ev.drop_duplicates("base_cv_id")[cv_cols]
    nat_meta = ev.drop_duplicates("nationality")[["nationality", "nationality_group", "subregion",
                                                  "arab_identity_contested"]]
    stim = stim.merge(cv_meta, on="base_cv_id", how="left").merge(nat_meta, on="nationality", how="left")
    for c in STIM_KEYS + ["occupation", "qualification_tier", "nationality_group", "subregion"]:
        stim[c] = stim[c].astype(str)
    if "base_country" in stim:
        stim["base_country"] = stim["base_country"].fillna("").astype(str)
        stim["host_national"] = (stim["nationality"] == stim["base_country"]).astype(float)
    stim["y"] = stim["y"].astype(float)
    return stim


@dataclass
class Cell:
    """Stimulus means for one model x condition x outcome."""
    model: str
    condition: str
    outcome: str
    Yk: np.ndarray                # (I, N, K) stimulus means per wording variant
    n_valid: np.ndarray           # (I, N, K) valid replicates per stimulus
    cvs: list[str]
    occupations: np.ndarray       # (I,)
    tiers: np.ndarray             # (I,)
    codes: list[str]              # nationality column order
    variants: list[str]
    groups: dict[str, str]
    subregions: dict[str, str] = field(default_factory=dict)
    contested: dict[str, bool] = field(default_factory=dict)
    _Y: np.ndarray | None = field(default=None, repr=False)
    n_wording_imputed: int = 0
    base_countries: np.ndarray | None = None     # (I,) base country per CV ("" if unknown)

    @property
    def Y(self) -> np.ndarray:
        """(I, N) wording-averaged stimulus means mu_bar(i, n).

        A wording missing for a (CV, nationality) cell is imputed additively within
        the CV (nationality + wording effects of that CV) before averaging, so wording
        main effects cannot leak into nationality contrasts (review M15). Cells with no
        valid wording at all stay missing.
        """
        if self._Y is None:
            filled, n = impute_wordings(self.Yk)
            self._Y = _nanmean(filled, -1)
            self.n_wording_imputed = n
        return self._Y

    def cols(self, codes) -> np.ndarray:
        idx = {c: k for k, c in enumerate(self.codes)}
        return np.array([idx[c] for c in codes if c in idx], dtype=int)

    @property
    def arab_codes(self) -> list[str]:
        return [c for c in self.codes if self.groups.get(c) == "arab"]

    @property
    def n_cv(self) -> int:
        return len(self.cvs)

    def rows(self, cvs: list[str]) -> np.ndarray:
        pos = {c: k for k, c in enumerate(self.cvs)}
        return np.array([pos[c] for c in cvs], dtype=int)

    def host(self, cols: np.ndarray | None = None) -> np.ndarray:
        """(I, len(cols)) host-national indicator H_in = 1[code n == base country of CV i] (0 if unknown)."""
        cols = np.arange(len(self.codes)) if cols is None else np.asarray(cols, int)
        if self.base_countries is None:
            return np.zeros((self.n_cv, cols.size))
        codes = np.asarray(self.codes, dtype=object)[cols]
        return (codes[None, :] == np.asarray(self.base_countries, dtype=object)[:, None]).astype(float)

    @property
    def has_host(self) -> bool:
        return bool(self.host().any())


def build_cell(stim: pd.DataFrame, model: str, condition: str, outcome: str,
               codes: list[str]) -> Cell:
    s = stim[(stim["model_alias"] == model) & (stim["prompt_condition"] == condition)]
    if s.empty:
        raise ValueError(f"no stimuli for model={model!r}, condition={condition!r}")
    cvs = sorted(s["base_cv_id"].unique())
    present = [c for c in codes if c in set(s["nationality"])]
    variants = sorted(s["prompt_variant"].unique())
    ci = {c: k for k, c in enumerate(cvs)}
    ni = {c: k for k, c in enumerate(present)}
    vi = {c: k for k, c in enumerate(variants)}
    s = s[s["nationality"].isin(present)]
    Yk = np.full((len(cvs), len(present), len(variants)), np.nan)
    Nk = np.zeros_like(Yk)
    idx = (s["base_cv_id"].map(ci).to_numpy(int), s["nationality"].map(ni).to_numpy(int),
           s["prompt_variant"].map(vi).to_numpy(int))
    Yk[idx] = s["y"].to_numpy(float)
    Nk[idx] = s["n_valid"].to_numpy(float)
    cvm = s.drop_duplicates("base_cv_id").set_index("base_cv_id").reindex(cvs)
    nm = s.drop_duplicates("nationality").set_index("nationality")
    bcs = (cvm["base_country"].fillna("").astype(str).to_numpy() if "base_country" in cvm else None)
    return Cell(model=model, condition=condition, outcome=outcome, Yk=Yk, n_valid=Nk, cvs=cvs,
                occupations=cvm["occupation"].astype(str).to_numpy(),
                tiers=cvm["qualification_tier"].astype(str).to_numpy(), codes=present,
                variants=variants, groups={c: str(nm.at[c, "nationality_group"]) for c in present},
                subregions={c: str(nm.at[c, "subregion"]) for c in present},
                contested={c: bool(nm.at[c, "arab_identity_contested"]) for c in present},
                base_countries=bcs)


def impute_wordings(Yk: np.ndarray, n_iter: int = 100, tol: float = 1e-9) -> tuple[np.ndarray, int]:
    """Fill missing (CV, nationality, wording) stimulus means from the within-CV additive model
    nationality + wording (Yates-type iteration). Rows (CV, nationality) without any observed
    wording and CVs without any observation stay NaN. Returns (filled, number of cells imputed)."""
    Y = np.array(Yk, float)
    miss = np.isnan(Y)
    row_any = (~miss).any(-1)                                       # (I, N)
    fillable = miss & row_any[..., None] & (~miss).any(1)[:, None, :]
    n = int(fillable.sum())
    if n == 0 or Y.shape[-1] == 1:
        return Y, 0
    rm = _nanmean(Y, -1)
    Y[fillable] = np.broadcast_to(rm[..., None], Y.shape)[fillable]
    Yw = np.where(row_any[..., None], Y, np.nan)
    for _ in range(n_iter):
        r = _nanmean(Yw, -1)[..., None]                               # (I, N, 1)
        c = _nanmean(Yw, 1)[:, None, :]                               # (I, 1, K)
        g = _nanmean(_nanmean(Yw, -1), -1)[:, None, None]
        fit = r + c - g
        d = np.nanmax(np.abs(Yw[fillable] - fit[fillable])) if n else 0.0
        Yw[fillable] = fit[fillable]
        if d < tol:
            break
    return Yw, n


def replicate_array(ev: pd.DataFrame, model: str, condition: str, outcome: str,
                    cvs: list[str], codes: list[str], flatten_variants: bool = True) -> np.ndarray:
    """Replicate-level valid outcome values, NaN padded.

    Returns (I, N, K, R), or (I, N, K*R) with ``flatten_variants``.
    """
    v = counterfactual(ev)
    v = v[(v["model_alias"] == model) & (v["prompt_condition"] == condition)
          & (v["parse_status"] == "ok").fillna(False) & v[outcome].notna()]
    variants = sorted(counterfactual(ev)["prompt_variant"].astype(str).unique())
    R = int(v["repetition"].max()) + 1 if len(v) else 1
    out = np.full((len(cvs), len(codes), len(variants), R), np.nan)
    ci = {c: k for k, c in enumerate(cvs)}
    ni = {c: k for k, c in enumerate(codes)}
    vi = {c: k for k, c in enumerate(variants)}
    i = v["base_cv_id"].astype(str).map(ci)
    n = v["nationality"].astype(str).map(ni)
    keep = (i.notna() & n.notna()).to_numpy()
    out[i[keep].astype(int).to_numpy(), n[keep].astype(int).to_numpy(),
        v.loc[keep, "prompt_variant"].astype(str).map(vi).astype(int).to_numpy(),
        v.loc[keep, "repetition"].astype(int).to_numpy()] = v.loc[keep, outcome].astype(float).to_numpy()
    return out.reshape(len(cvs), len(codes), -1) if flatten_variants else out


# --------------------------------------------------------------------------- #
# Contrasts: per-CV contrast values, stratified t inference, TOST
# --------------------------------------------------------------------------- #
def _nanmean(a, axis):
    a = np.asarray(a, float)
    with np.errstate(invalid="ignore", divide="ignore"):
        cnt = np.sum(~np.isnan(a), axis=axis)
        s = np.nansum(a, axis=axis)
        return np.where(cnt > 0, s / np.maximum(cnt, 1), np.nan)


def cv_contrast(Y: np.ndarray, target: np.ndarray, comparison: np.ndarray) -> np.ndarray:
    """Per-CV contrast: mean of available target cells minus mean of comparison cells."""
    return _nanmean(Y[..., target], -1) - _nanmean(Y[..., comparison], -1)


@dataclass
class TResult:
    estimate: float
    se: float
    df: float
    ci_low: float
    ci_high: float
    p: float
    n_cv: int
    stratified: bool = False


def _moments(d: np.ndarray, strata: np.ndarray | None):
    """Estimate, SE, df: equal-weight stratified mean with Welch-Satterthwaite df."""
    n = d.size
    if strata is not None:
        labs = np.unique(strata)
        nj = np.array([np.sum(strata == s) for s in labs])
        if labs.size >= 2 and np.all(nj >= 2):
            J = labs.size
            mj = np.array([d[strata == s].mean() for s in labs])
            vj = np.array([d[strata == s].var(ddof=1) for s in labs])
            a = 1.0 / (J * J * nj)
            var = float(np.sum(a * vj))
            den = np.sum((a * vj) ** 2 / (nj - 1))
            df = float(var ** 2 / den) if den > 0 else float(n - J)
            return float(mj.mean()), float(np.sqrt(var)), df, True
    return float(d.mean()), float(d.std(ddof=1) / np.sqrt(n)), float(n - 1), False


def t_summary(d: np.ndarray, alpha: float = 0.05, strata: np.ndarray | None = None) -> TResult:
    """t inference on per-CV contrast values (NaN dropped), occupation-stratified if given."""
    d = np.asarray(d, float)
    ok = ~np.isnan(d)
    st = None if strata is None else np.asarray(strata)[ok]
    d = d[ok]
    n = d.size
    if n < 2:
        return TResult(float(d.mean()) if n else np.nan, np.nan, max(n - 1, 0), np.nan, np.nan, np.nan, n)
    est, se, df, strat = _moments(d, st)
    q = stats.t.ppf(1 - alpha / 2, df)
    if se == 0:
        p = 1.0 if est == 0 else 0.0
    else:
        p = float(2 * stats.t.sf(abs(est / se), df))
    return TResult(est, se, df, est - q * se, est + q * se, p, n, strat)


@dataclass
class TOSTResult:
    estimate: float
    se: float
    df: float
    sesoi: float
    ci90_low: float
    ci90_high: float
    p_lower: float
    p_upper: float
    p_tost: float
    equivalent: bool


def tost(d: np.ndarray, sesoi: float, alpha: float = 0.05, strata: np.ndarray | None = None) -> TOSTResult:
    """Two one-sided tests of |mean| < sesoi on per-CV contrast values."""
    t = t_summary(d, strata=strata)
    if not np.isfinite(t.se) or t.se == 0:
        eq = bool(np.isfinite(t.estimate) and abs(t.estimate) < sesoi and t.se == 0)
        return TOSTResult(t.estimate, t.se, t.df, sesoi, np.nan, np.nan, np.nan, np.nan,
                          0.0 if eq else 1.0, eq)
    p_lo = float(stats.t.sf((t.estimate + sesoi) / t.se, t.df))
    p_hi = float(stats.t.cdf((t.estimate - sesoi) / t.se, t.df))
    q = stats.t.ppf(1 - alpha, t.df)
    p = max(p_lo, p_hi)
    return TOSTResult(t.estimate, t.se, t.df, sesoi, t.estimate - q * t.se, t.estimate + q * t.se,
                      p_lo, p_hi, p, bool(p < alpha))


def tost_from_ci(est: float, lo90: float, hi90: float, sesoi: float) -> bool:
    return bool(np.isfinite(lo90) and np.isfinite(hi90) and lo90 > -sesoi and hi90 < sesoi)


# --------------------------------------------------------------------------- #
# Host-national fixed effect (setting 2026-10-01)
# --------------------------------------------------------------------------- #
def _fe_residual(A: np.ndarray, n_iter: int = 1000, tol: float = 1e-11) -> np.ndarray:
    """Residual of ``A`` (..., I, J) after least-squares projection on row (CV) and column
    (nationality) fixed effects over its non-NaN cells. Alternating projections; one sweep is exact
    for complete data. NaN cells stay NaN."""
    X = np.array(A, float)
    obs = ~np.isnan(X)
    if not obs.any():
        return X
    scale = 1.0 + float(np.nanmax(np.abs(X)))
    for _ in range(n_iter):
        X = X - np.nan_to_num(_nanmean(X, -1))[..., None]
        X = np.where(obs, X - np.nan_to_num(_nanmean(X, -2))[..., None, :], np.nan)
        if np.nanmax(np.abs(np.nan_to_num(_nanmean(X, -1)))) < tol * scale:
            break
    return X


def _strat_weights(valid: np.ndarray, strata: np.ndarray | None) -> np.ndarray:
    """Weights w_i of the (stratified) mean that ``t_summary`` applies to the valid entries."""
    valid = np.asarray(valid, bool)
    w = np.zeros(valid.size)
    n = int(valid.sum())
    if n == 0:
        return w
    if strata is not None:
        st = np.asarray(strata)
        labs = np.unique(st[valid])
        nj = np.array([np.sum(valid & (st == x)) for x in labs])
        if labs.size >= 2 and np.all(nj >= 2):
            for x, k in zip(labs, nj):
                w[valid & (st == x)] = 1.0 / (labs.size * k)
            return w
    w[valid] = 1.0 / n
    return w


@dataclass
class HostFit:
    """Common host-national effect eta (points) in ybar_in = alpha_i + tau_n + eta * H_in + e_in."""
    eta: float
    se: float
    df: float
    ci_low: float
    ci_high: float
    p: float
    n_cv: int
    n_host_cells: int
    identified: bool
    u: np.ndarray = field(repr=False, default=None)   # (I,) per-CV influence: eta_hat - eta = sum_i u_i


def host_fit(Y: np.ndarray, H: np.ndarray | None, strata: np.ndarray | None = None,
             alpha: float = 0.05) -> HostFit:
    """Least-squares host-national effect with CV and nationality fixed effects (Frisch-Waugh).

    X = H residualised on the two-way fixed effects over the observed cells of Y;
    eta = sum(X * Y) / sum(X^2). Per-CV influence u_i = sum_n X_in r_in / sum(X^2) (r: residuals
    of the full model), so eta - eta_true = sum_i u_i up to O(1/I); the SE is the CV-clustered
    (occupation-stratified) sandwich obtained by feeding eta + u_i / w_i to ``t_summary``.
    Not identified (eta = NaN) if no observed host cell exists or H is collinear with the FE.
    """
    Y = np.asarray(Y, float)
    I = Y.shape[0]
    none = HostFit(np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, I, 0, False, np.zeros(I))
    if H is None:
        return none
    H = np.broadcast_to(np.asarray(H, float), Y.shape)
    obs = ~np.isnan(Y)
    n_host = int(np.sum(obs & (H > 0)))
    if n_host == 0:
        return none
    X = _fe_residual(np.where(obs, H, np.nan))
    sxx = float(np.nansum(X ** 2))
    if not sxx > 1e-8 * n_host:
        none.n_host_cells = n_host
        return none
    Yt = _fe_residual(Y)
    eta = float(np.nansum(X * Yt) / sxx)
    u = np.nansum(X * (Yt - eta * X), axis=1) / sxx
    valid = obs.any(1)
    w = _strat_weights(valid, strata)
    psi = np.full(I, np.nan)
    psi[valid] = eta + u[valid] / w[valid]
    t = t_summary(psi, alpha, None if strata is None else np.asarray(strata))
    return HostFit(eta=eta, se=t.se, df=t.df, ci_low=t.ci_low, ci_high=t.ci_high, p=t.p, n_cv=int(valid.sum()),
                   n_host_cells=n_host, identified=True, u=u)


def host_adjusted_values(d_y: np.ndarray, d_h: np.ndarray, host: HostFit | None, strata: np.ndarray | None = None,
                         rows: np.ndarray | None = None) -> np.ndarray:
    """Per-CV values psi_i with stratified mean M[psi] = M[d_y] - eta * M[d_h] (the host-adjusted
    contrast) whose stratified-t variance includes eta's estimation error (influence of eta added).

    ``d_y`` / ``d_h``: per-CV contrast of Y and of H (H restricted to the observed cells of Y, same
    contrast operator). ``rows``: rows of ``host``'s matrix that ``d_y`` refers to (default all).
    Without an identified host fit ``d_y`` is returned unchanged.
    """
    d_y = np.asarray(d_y, float)
    if host is None or not host.identified:
        return d_y
    ok = ~np.isnan(d_y)
    if not ok.any():
        return d_y
    u_all = host.u
    u = u_all if rows is None else u_all[np.asarray(rows, int)]
    w = _strat_weights(ok, strata)
    dh = np.where(ok, np.nan_to_num(np.asarray(d_h, float)), 0.0)
    m_dh = float(np.sum(w * dh))
    left = float(np.sum(u_all) - np.sum(u[ok]))        # influence of CVs without a contrast value
    out = np.full_like(d_y, np.nan)
    out[ok] = d_y[ok] - host.eta * dh[ok] - m_dh * (u[ok] / w[ok] + left)
    return out


def contrast_values(Y: np.ndarray, target: np.ndarray, comparison: np.ndarray, H: np.ndarray | None = None,
                    host: HostFit | None = None, strata: np.ndarray | None = None,
                    rows: np.ndarray | None = None) -> np.ndarray:
    """Per-CV contrast values, host-adjusted when ``H`` (aligned with ``Y``) and an identified ``host`` fit are
    given (``rows``: rows of the host fit that ``Y`` holds)."""
    d = cv_contrast(Y, target, comparison)
    if H is None or host is None or not host.identified:
        return d
    Hm = np.where(np.isnan(Y), np.nan, H)
    return host_adjusted_values(d, cv_contrast(Hm, target, comparison), host, strata, rows)


def host_adjust(Y: np.ndarray, H: np.ndarray | None, host: HostFit | None) -> np.ndarray:
    """Plug-in host-adjusted matrix Y - eta_hat * H (for cross-checks and descriptive structure)."""
    if H is None or host is None or not host.identified:
        return Y
    return Y - host.eta * H


# --------------------------------------------------------------------------- #
# Bootstrap (base CVs resampled within occupation)
# --------------------------------------------------------------------------- #
def stratified_bootstrap_indices(strata: np.ndarray, B: int, rng: np.random.Generator) -> np.ndarray:
    """(B, I) row indices; each stratum resampled with replacement to its own size."""
    strata = np.asarray(strata)
    out = np.empty((B, strata.size), dtype=int)
    for s in np.unique(strata):
        idx = np.flatnonzero(strata == s)
        out[:, idx] = idx[rng.integers(0, idx.size, size=(B, idx.size))]
    return out


def percentile_ci(draws: np.ndarray, alpha: float = 0.05, axis: int = 0):
    with np.errstate(invalid="ignore"):
        lo = np.nanpercentile(draws, 100 * alpha / 2, axis=axis)
        hi = np.nanpercentile(draws, 100 * (1 - alpha / 2), axis=axis)
    return lo, hi


# --------------------------------------------------------------------------- #
# Two-way (CV x nationality) decomposition and sigma_A
# --------------------------------------------------------------------------- #
def twoway_stats(Y: np.ndarray, H: np.ndarray | None = None) -> dict[str, np.ndarray]:
    """NaN-aware additive CV x nationality decomposition on (..., I, J) arrays.

    Returns: ``cm`` (CV-adjusted nationality deviations delta_hat, centred),
    ``F`` (randomised-block F), ``ms_res``, ``df_res``, ``sd_plugin`` (plug-in
    SD of delta_hat, divisor J), ``R`` (range), ``sigma2_deb`` (debiased
    finite-population variance sigma_A^2 = mean(delta_hat^2) - mean SE^2,
    untruncated), ``sigma_A`` (sqrt of the truncated value), ``n_j``.
    For complete data: sigma2_deb = ((J-1)/J) * (MS_nat - MS_res) / I.

    With ``H`` (host-national indicator, broadcastable to ``Y``) the common host effect eta is
    estimated per leading index (``eta``; least squares with both fixed effects) and removed first:
    everything is computed on Y - eta * H, the residual df drop by one, and the variance of eta_hat
    enters the noise term: mean SE^2 = MS_res * [inv_n (J-1)/J + mean_n c_n^2 / sum(X^2)], where c_n
    is the centred column mean of the row-centred H and X the FE-residualised H (``inv_n`` is
    returned in this effective form, so I_eff = 1 / inv_n and F = MS_nat / MS_res * inv_n_raw / inv_n).
    """
    eta = n_par = extra_n = None
    if H is not None:
        H = np.broadcast_to(np.asarray(H, float), Y.shape)
        obs0 = ~np.isnan(Y)
        if np.any(obs0 & (H > 0)):
            Hm = np.where(obs0, H, np.nan)
            X = _fe_residual(Hm)
            sxx = np.nansum(X ** 2, axis=(-2, -1))
            ident = sxx > 1e-8
            Yt = Y - _nanmean(Y, -1)[..., None]           # X has zero row and column sums: FE drop out
            eta = np.where(ident, np.nansum(X * Yt, axis=(-2, -1)) / np.where(ident, sxx, 1.0), 0.0)
            Y = Y - np.asarray(eta)[..., None, None] * H
            Zh = Hm - _nanmean(Hm, -1)[..., None]
            cmh = _nanmean(Zh, -2)
            cmh = cmh - _nanmean(cmh, -1)[..., None]
            extra_n = np.where(np.asarray(ident)[..., None], np.nan_to_num(cmh) ** 2
                               / np.where(ident, sxx, 1.0)[..., None], 0.0)
            n_par = np.asarray(ident, float)
            eta = np.where(ident, eta, np.nan)
    obs = ~np.isnan(Y)
    Z = Y - _nanmean(Y, -1)[..., None]
    n_j = obs.sum(-2)
    cm = _nanmean(Z, -2)
    J = Y.shape[-1]
    wbar = np.nansum(cm * n_j, -1) / np.maximum(n_j.sum(-1), 1)
    ss_nat = np.nansum(n_j * (cm - wbar[..., None]) ** 2, -1)
    resid = Z - cm[..., None, :]
    ss_res = np.nansum(np.where(obs, resid ** 2, 0.0), -1).sum(-1)
    n_obs = obs.sum((-2, -1))
    n_rows = (obs.sum(-1) > 0).sum(-1)
    df_res = n_obs - n_rows - J + 1 - (0 if n_par is None else n_par)
    with np.errstate(invalid="ignore", divide="ignore"):
        ms_res = ss_res / np.where(df_res > 0, df_res, np.nan)
        F = (ss_nat / (J - 1)) / ms_res
        cmc = cm - _nanmean(cm, -1)[..., None]
        sd_plugin = np.sqrt(np.nansum(cmc ** 2, -1) / J)
        R = np.nanmax(cm, -1) - np.nanmin(cm, -1)
        inv_n = _nanmean(np.where(n_j > 0, 1.0 / np.maximum(n_j, 1), np.nan), -1)
        if extra_n is not None:
            inv_raw = inv_n
            inv_n = inv_n + np.mean(extra_n, -1) * J / (J - 1)
            F = F * inv_raw / inv_n
        sigma2_deb = sd_plugin ** 2 - ms_res * inv_n * (J - 1) / J
    return dict(cm=cm, F=F, ms_res=ms_res, df_res=df_res, sd_plugin=sd_plugin, R=R,
                sigma2_deb=sigma2_deb, sigma_A=np.sqrt(np.clip(sigma2_deb, 0, None)), n_j=n_j,
                inv_n=inv_n, eta=eta, extra_n=extra_n, Y_adj=Y if H is not None else None)


def permute_within_rows(Y: np.ndarray, B: int, rng: np.random.Generator,
                        fixed: np.ndarray | None = None) -> np.ndarray:
    """(B, I, J) copies of Y with each row's entries independently shuffled.

    ``fixed`` (I, J) marks cells that stay in place (host-national cells): only the other cells of a
    row are shuffled among themselves."""
    keys = rng.random((B,) + Y.shape)
    if fixed is None or not np.any(fixed):
        order = np.argsort(keys, axis=-1)
        return np.take_along_axis(np.broadcast_to(Y, (B,) + Y.shape), order, axis=-1)
    J = Y.shape[-1]
    fx = np.broadcast_to(np.asarray(fixed, bool), Y.shape)
    pos = np.arange(J) / J
    order = np.argsort(np.where(fx, 2.0 + pos, keys), axis=-1)            # free cells shuffled, fixed last
    target = np.broadcast_to(np.argsort(np.where(fx, 1.0 + pos, pos), axis=-1), (B,) + Y.shape)
    vals = np.take_along_axis(np.broadcast_to(Y, (B,) + Y.shape), order, axis=-1)
    out = np.empty((B,) + Y.shape)
    np.put_along_axis(out, target, vals, axis=-1)
    return out


def permutation_null(Y: np.ndarray, n_perm: int, rng: np.random.Generator,
                     chunk: int = 1000, H: np.ndarray | None = None,
                     fixed: np.ndarray | None = None) -> dict[str, np.ndarray]:
    """Null distributions (within-CV label permutation) of sigma2_deb, F, sd_plugin, R.

    With ``H`` the statistic is the host-adjusted one (eta re-estimated per permutation) and host
    cells stay fixed (``fixed`` defaults to H > 0)."""
    keys = ("sigma2_deb", "F", "sd_plugin", "R", "sigma_A")
    out = {k: [] for k in keys}
    if fixed is None and H is not None:
        fixed = np.asarray(H) > 0
    done = 0
    while done < n_perm:
        b = min(chunk, n_perm - done)
        s = twoway_stats(permute_within_rows(Y, b, rng, fixed), H)
        for k in keys:
            out[k].append(np.atleast_1d(s[k]))
        done += b
    return {k: np.concatenate(v) for k, v in out.items()}


def ncf_sigma_limits(F: float, df1: float, df2: float, I_eff: float, J: int, ms_res: float,
                     alpha: float = 0.05) -> dict[str, float]:
    """Noncentral-F inversion for sigma_A (coverage holds near zero).

    Under the normal randomised-block model F ~ F'(J-1, df_res, lambda) with
    lambda = I * J * sigma_A^2 / sigma^2. Limits for lambda are found by test
    inversion (bounded below by 0) and converted with sigma^2 = MS_res.
    Returns two-sided (1-alpha) limits and the one-sided (1-alpha) upper limit.
    """
    if not (np.isfinite(F) and df2 > 0 and ms_res > 0):
        return dict(lower=np.nan, upper=np.nan, upper_one_sided=np.nan, lower_one_sided=np.nan)

    def lam_for(p):
        # lambda with P(F' <= F_obs; lambda) = p ; cdf decreases in lambda
        if stats.f.cdf(F, df1, df2) <= p:
            return 0.0
        hi = max(10.0, F * df1 * 2)
        while stats.ncf.cdf(F, df1, df2, hi) > p:
            hi *= 2
            if hi > 1e8:
                return np.inf
        return optimize.brentq(lambda lam: stats.ncf.cdf(F, df1, df2, lam) - p, 0.0, hi, xtol=1e-8)

    conv = ms_res / (I_eff * J)
    return dict(lower=float(np.sqrt(lam_for(1 - alpha / 2) * conv)),
                upper=float(np.sqrt(lam_for(alpha / 2) * conv)),
                upper_one_sided=float(np.sqrt(lam_for(alpha) * conv)),
                lower_one_sided=float(np.sqrt(lam_for(1 - alpha) * conv)))


def p_minimum_effect_sigma(F: float, df1: float, df2: float, I_eff: float, J: int, ms_res: float,
                           sesoi: float) -> float:
    """Minimum-effect test of H0: sigma_A <= SESOI (review M4): P(F' >= F_obs) at sigma_A = SESOI."""
    if not (np.isfinite(F) and df2 > 0 and ms_res > 0):
        return np.nan
    lam = I_eff * J * sesoi ** 2 / ms_res
    return float(stats.ncf.sf(F, df1, df2, lam))


def column_residual_variances(Y: np.ndarray) -> np.ndarray:
    """Residual variance per nationality column of the additive CV x nationality fit (review M3).
    Scaled so that the average equals MS_res under complete data."""
    keep = np.sum(~np.isnan(Y), axis=1) >= 2
    Y = Y[keep]
    Z = Y - _nanmean(Y, -1)[:, None]
    e = Z - _nanmean(Z, 0)[None, :]
    I, J = Y.shape
    n = np.sum(~np.isnan(e), 0)
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.nansum(e ** 2, 0) / np.maximum(n - 1, 1) * J / max(J - 1, 1)


def greenhouse_geisser(Y: np.ndarray) -> float:
    """Greenhouse-Geisser epsilon of the CV x nationality matrix (1 = sphericity; lower bound 1/(J-1)).
    Uses complete rows. With fewer CVs than nationalities the covariance is rank-deficient and
    epsilon is biased; report it as a descriptive check."""
    Yc = Y[~np.isnan(Y).any(1)]
    I, J = Yc.shape
    if I < 3:
        return np.nan
    S = np.cov(Yc, rowvar=False)
    C = np.eye(J) - 1.0 / J
    D = C @ S @ C
    tr, tr2 = np.trace(D), np.trace(D @ D)
    return float(tr ** 2 / ((J - 1) * tr2)) if tr2 > 0 else np.nan


def _boot_inflate(strata: np.ndarray) -> float:
    _, nj = np.unique(np.asarray(strata), return_counts=True)
    nj = nj[nj > 1]
    return float(np.mean(nj / (nj - 1))) if nj.size else 1.0


def sphericity_free_equivalence(Y: np.ndarray, strata: np.ndarray, sesoi: float, n_boot: int, n_cal: int,
                                n_boot_cal: int, rng: np.random.Generator, alpha: float = 0.05,
                                chunk: int = 20, H: np.ndarray | None = None) -> dict:
    """Sphericity-free equivalence test for sigma_A < SESOI (review M3).

    Statistic: T = (sigma2_deb - SESOI^2) / se, se from a stratified CV bootstrap (variance
    inflated by n_j/(n_j-1)). Critical value calibrated by simulation: residual rows of the
    additive fit (which keep each column's own variance and the correlations between columns)
    are resampled within occupation, a nationality pattern with sigma_A = SESOI (the observed
    pattern rescaled) is added, and T is recomputed with the same bootstrap. Equivalence iff
    T_obs < alpha-quantile of the calibration distribution; upper bound
    U = sqrt(max(sigma2_deb - q * se, 0)).
    With ``H`` every statistic is host-adjusted (eta re-estimated in each bootstrap and calibration
    replicate); residuals are taken after removing the host effect.
    """
    out = dict(sf_upper95=np.nan, sf_crit=np.nan, sf_p=np.nan, sf_equivalent=False, sf_se=np.nan)
    if not (np.isfinite(sesoi) and n_boot > 1 and n_cal > 1 and n_boot_cal > 1):
        return out
    keep = ~np.isnan(Y).any(1)
    Y, strata = Y[keep], np.asarray(strata)[keep]
    if H is not None:
        H = np.asarray(H, float)[keep]
    I, J = Y.shape
    if I < 4:
        return out
    infl = _boot_inflate(strata)
    tw = twoway_stats(Y, H)
    s2 = float(tw["sigma2_deb"])
    bidx = stratified_bootstrap_indices(strata, n_boot, rng)
    se = float(np.sqrt(np.nanvar(twoway_stats(Y[bidx], None if H is None else H[bidx])["sigma2_deb"], ddof=1)
                       * infl))
    if not se > 0:
        return out
    t_obs = (s2 - sesoi ** 2) / se
    cm = tw["cm"] - np.mean(tw["cm"])
    sd = np.sqrt(np.mean(cm ** 2))
    if sd > 0:
        pattern = cm / sd * sesoi
    else:
        z = stats.norm.ppf((np.arange(1, J + 1) - 0.5) / J)
        pattern = (z - z.mean()) / z.std() * sesoi
    Ya = tw["Y_adj"] if tw.get("Y_adj") is not None else Y
    E = Ya - Ya.mean(1, keepdims=True) - Ya.mean(0, keepdims=True) + Ya.mean()
    E *= np.sqrt(I / (I - 1) * J / (J - 1))
    labs = np.unique(strata)
    groups = [np.flatnonzero(strata == s) for s in labs]
    T = []
    done = 0
    while done < n_cal:
        c = min(chunk, n_cal - done)
        rows = np.empty((c, I), int)
        for g in groups:
            rows[:, g] = g[rng.integers(0, g.size, (c, g.size))]
        Ys = E[rows] + pattern[None, None, :]                          # (c, I, J)
        Hs = None if H is None else H[rows]
        s2s = twoway_stats(Ys, Hs)["sigma2_deb"]                        # (c,)
        bi = np.empty((c, n_boot_cal, I), int)
        for g in groups:
            bi[:, :, g] = g[rng.integers(0, g.size, (c, n_boot_cal, g.size))]
        Yb = np.take_along_axis(Ys[:, None, :, :], bi[..., None], axis=2)  # (c, B, I, J)
        Hb = None if Hs is None else np.take_along_axis(Hs[:, None, :, :], bi[..., None], axis=2)
        seb = np.sqrt(np.nanvar(twoway_stats(Yb, Hb)["sigma2_deb"], axis=1, ddof=1) * infl)
        T.append((s2s - sesoi ** 2) / seb)
        done += c
    T = np.concatenate(T)
    q = float(np.nanquantile(T, alpha))
    return dict(sf_upper95=float(np.sqrt(max(s2 - q * se, 0.0))), sf_crit=q,
                sf_p=float((1 + np.sum(T <= t_obs)) / (1 + T.size)), sf_equivalent=bool(t_obs < q), sf_se=se)


def compare_sigma(Ya: np.ndarray, Yb: np.ndarray, strata: np.ndarray, n_boot: int, rng: np.random.Generator,
                  alpha: float = 0.05, Ha: np.ndarray | None = None, Hb: np.ndarray | None = None) -> dict:
    """Compare debiased spreads of two column sets measured on the SAME base CVs (H1e: sigma_A vs
    sigma_placebo; review H5).

    Test on the variance scale: d = sigma2_a - sigma2_b, SE from a shared stratified CV bootstrap
    (inflated by n_j/(n_j-1)), t(I - #strata). Effect size on the SD scale (difference of truncated
    debiased SDs) with a bootstrap percentile interval. ``Ha`` / ``Hb``: host indicators (host-adjusted spreads).
    """
    keep = ~(np.isnan(Ya).all(1) | np.isnan(Yb).all(1))
    Ya, Yb, strata = Ya[keep], Yb[keep], np.asarray(strata)[keep]
    Ha = None if Ha is None else np.asarray(Ha, float)[keep]
    Hb = None if Hb is None else np.asarray(Hb, float)[keep]
    sa, sb = twoway_stats(Ya, Ha), twoway_stats(Yb, Hb)
    bidx = stratified_bootstrap_indices(strata, n_boot, rng)
    ba = twoway_stats(Ya[bidx], None if Ha is None else Ha[bidx])
    bb = twoway_stats(Yb[bidx], None if Hb is None else Hb[bidx])
    dv = float(sa["sigma2_deb"]) - float(sb["sigma2_deb"])
    se = float(np.nanstd(ba["sigma2_deb"] - bb["sigma2_deb"], ddof=1)) * np.sqrt(_boot_inflate(strata))
    df = len(strata) - len(set(strata))
    p = float(2 * stats.t.sf(abs(dv / se), max(df, 1))) if se > 0 else np.nan
    bsd = ba["sigma_A"] - bb["sigma_A"]
    lo, hi = np.nanpercentile(bsd, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return dict(n_cv=int(len(strata)), sigma_a=float(sa["sigma_A"]), sigma_b=float(sb["sigma_A"]),
                difference=float(sa["sigma_A"]) - float(sb["sigma_A"]), diff_ci_low=float(lo), diff_ci_high=float(hi),
                p_difference=p, variance_scale_difference=dv, variance_scale_se=se, df=df)


def sigma_within_groups(Y: np.ndarray, groups: list[str], n_perm: int, rng: np.random.Generator,
                        H: np.ndarray | None = None) -> dict:
    """sigma_A net of group (sub-region) means (review H5): debiased within-group spread.

    sigma2_net = (1/J) sum_n (delta_n - mean_{g(n)} delta)^2 - ((J - G)/J) * MS_res * mean(1/n_j),
    G = number of groups. p-value: nationality labels permuted within group within CV.
    With ``H`` the host effect is removed (re-estimated per permutation) and host cells stay fixed.
    """
    keep = np.sum(~np.isnan(Y), axis=1) >= 2
    Y = Y[keep]
    H = None if H is None else np.asarray(H, float)[keep]
    fixed = None if H is None else H > 0
    g = np.asarray(groups)
    labs = [np.flatnonzero(g == s) for s in np.unique(g)]
    J, G = Y.shape[1], len(labs)

    def stat(Yx):
        tw = twoway_stats(Yx, H)
        cm = tw["cm"]
        dev = cm.copy()
        for ix in labs:
            dev[..., ix] = cm[..., ix] - _nanmean(cm[..., ix], -1)[..., None]
        plug = np.nansum(dev ** 2, -1) / J
        return plug - (J - G) / J * tw["ms_res"] * tw["inv_n"], tw["sigma2_deb"]

    s_net, s_all = stat(Y)
    s_net, s_all = float(s_net), float(s_all)
    p = np.nan
    if n_perm > 0 and any(ix.size > 1 for ix in labs):
        Yp = np.broadcast_to(Y, (n_perm,) + Y.shape).copy()
        for ix in labs:
            if ix.size > 1:
                Yp[..., ix] = permute_within_rows(Y[:, ix], n_perm, rng, None if fixed is None else fixed[:, ix])
        sp, _ = stat(Yp)
        p = float((1 + np.sum(sp >= s_net - 1e-12)) / (1 + n_perm))
    share = 1 - max(s_net, 0) / s_all if s_all > 0 else np.nan
    return dict(sigma_net=float(np.sqrt(max(s_net, 0))), sigma2_net=s_net, p_perm_within=p,
                between_group_share=float(share) if np.isfinite(share) else np.nan, n_groups=G)


def p_equivalence_sigma(F: float, df1: float, df2: float, I_eff: float, J: int, ms_res: float,
                        sesoi: float) -> float:
    """H1b p-value: P(F' <= F_obs) at sigma_A = SESOI (small -> sigma_A < SESOI)."""
    if not (np.isfinite(F) and df2 > 0 and ms_res > 0):
        return np.nan
    lam = I_eff * J * sesoi ** 2 / ms_res
    return float(stats.ncf.cdf(F, df1, df2, lam))


@dataclass
class HeterogeneityResult:
    n_cv: int
    n_nat: int
    sigma_A: float               # debiased (truncated at 0), finite-population SD, divisor J
    sigma2_deb: float            # untruncated debiased variance
    sd_plugin: float             # raw plug-in SD of delta_hat (biased upward)
    R_raw: float                 # raw range (biased upward)
    F: float
    df_res: float
    ms_res: float
    p_perm: float                # H1a: within-CV permutation, statistic = sigma2_deb
    p_F: float                   # parametric randomised-block F (cross-check)
    ncf_ci_low: float            # 95% CI for sigma_A by noncentral-F inversion
    ncf_ci_high: float
    upper95_one_sided: float     # H1b decision quantity
    p_equivalence: float         # H1b p-value at SESOI
    sesoi: float
    boot_ci_low: float           # bootstrap percentile CI (cross-check; poor near 0)
    boot_ci_high: float
    sd_null_mean: float
    sd_null_q95: float
    R_null_mean: float
    R_null_q95: float
    excess_range: float
    sigma_null_mean: float
    lower95_one_sided: float = np.nan   # minimum-effect decision quantity (review M4)
    p_min_effect: float = np.nan        # H0: sigma_A <= SESOI
    gg_epsilon: float = np.nan          # Greenhouse-Geisser epsilon (review M3)
    resid_var_min: float = np.nan
    resid_var_max: float = np.nan
    sf_upper95: float = np.nan          # sphericity-free calibrated bootstrap upper bound
    sf_crit: float = np.nan
    sf_p: float = np.nan
    sf_equivalent: bool = False
    host_effect: float = np.nan         # eta re-estimated on this column set (NaN: no host adjustment)
    host_adjusted: bool = False
    boot_sigma2: np.ndarray = field(repr=False, default=None)
    effects: pd.DataFrame = field(repr=False, default=None)


def heterogeneity(Y: np.ndarray, codes: list[str], strata: np.ndarray, n_perm: int, n_boot: int,
                  rng: np.random.Generator, alpha: float = 0.05, sesoi: float = np.nan,
                  boot_idx: np.ndarray | None = None, n_cal: int = 0,
                  n_boot_cal: int = 0, H: np.ndarray | None = None,
                  fixed: np.ndarray | None = None) -> HeterogeneityResult:
    """RQ1 quantities for the columns of ``Y`` (e.g. the 22 Arab origins).

    ``boot_idx`` (B, I) may be supplied so several models / conditions share
    the same bootstrap resamples (needed for H1c and H3a).
    ``H`` (host-national indicator aligned with ``Y``): every quantity is adjusted for a common host
    effect (re-estimated in each bootstrap / permutation replicate; host cells fixed in permutations).
    ``fixed``: cells kept in place by the permutation test (default H > 0; the host-exclusion
    sensitivity passes its NaN host cells here).
    """
    keep = np.sum(~np.isnan(Y), axis=1) >= 2
    Y = Y[keep]
    strata = np.asarray(strata)[keep]
    if H is not None:
        H = np.asarray(H, float)[keep]
        if not np.any(H > 0):
            H = None
    if fixed is None and H is not None:
        fixed = H > 0
    elif fixed is not None:
        fixed = np.asarray(fixed, bool)[keep]
    I, J = Y.shape
    obs = twoway_stats(Y, H)
    null = permutation_null(Y, n_perm, rng, H=H, fixed=fixed)
    s_obs = float(obs["sigma2_deb"])
    p_perm = float((1 + np.sum(null["sigma2_deb"] >= s_obs - 1e-12)) / (1 + n_perm))
    df1, df2 = J - 1, float(obs["df_res"])
    F_obs = float(obs["F"])
    p_F = float(stats.f.sf(F_obs, df1, df2)) if df2 > 0 and np.isfinite(F_obs) else np.nan
    I_eff = 1.0 / float(obs["inv_n"]) if np.isfinite(obs["inv_n"]) else I
    lim = ncf_sigma_limits(F_obs, df1, df2, I_eff, J, float(obs["ms_res"]), alpha)
    p_eq = p_equivalence_sigma(F_obs, df1, df2, I_eff, J, float(obs["ms_res"]), sesoi) \
        if np.isfinite(sesoi) else np.nan
    if boot_idx is None:
        boot_idx = stratified_bootstrap_indices(strata, n_boot, rng)
    else:
        boot_idx = _remap_boot(boot_idx, keep)
    boot = twoway_stats(Y[boot_idx], None if H is None else H[boot_idx])
    b_lo, b_hi = percentile_ci(boot["sigma_A"], alpha)
    p_min = p_minimum_effect_sigma(F_obs, df1, df2, I_eff, J, float(obs["ms_res"]), sesoi) \
        if np.isfinite(sesoi) else np.nan
    Yadj = obs["Y_adj"] if obs.get("Y_adj") is not None else Y
    rv = column_residual_variances(Yadj)
    sf = sphericity_free_equivalence(Y, strata, sesoi, max(n_boot, 2), n_cal, n_boot_cal, rng, alpha, H=H) \
        if n_cal > 0 else {}
    cm = obs["cm"]
    s2 = max(s_obs, 0.0)
    noise = float(obs["ms_res"]) / np.maximum(obs["n_j"], 1) * (J - 1) / J
    if obs.get("extra_n") is not None:
        noise = noise + float(obs["ms_res"]) * np.asarray(obs["extra_n"])
    shrink = s2 / (s2 + noise) if s2 > 0 else np.zeros_like(noise)
    delta = cm - np.nanmean(cm)
    eff = pd.DataFrame({"nationality": codes, "delta_hat": delta, "delta_shrunk": shrink * delta,
                        "shrinkage_weight": shrink, "n_cv": obs["n_j"], "residual_variance": rv})
    return HeterogeneityResult(
        n_cv=I, n_nat=J, sigma_A=float(obs["sigma_A"]), sigma2_deb=s_obs,
        sd_plugin=float(obs["sd_plugin"]), R_raw=float(obs["R"]), F=F_obs, df_res=df2,
        ms_res=float(obs["ms_res"]), p_perm=p_perm, p_F=p_F, ncf_ci_low=lim["lower"],
        ncf_ci_high=lim["upper"], upper95_one_sided=lim["upper_one_sided"], p_equivalence=p_eq,
        sesoi=sesoi, boot_ci_low=float(b_lo), boot_ci_high=float(b_hi),
        sd_null_mean=float(np.nanmean(null["sd_plugin"])),
        sd_null_q95=float(np.nanpercentile(null["sd_plugin"], 95)),
        R_null_mean=float(np.nanmean(null["R"])), R_null_q95=float(np.nanpercentile(null["R"], 95)),
        excess_range=float(obs["R"]) - float(np.nanmedian(null["R"])),
        sigma_null_mean=float(np.nanmean(null["sigma_A"])),
        lower95_one_sided=lim["lower_one_sided"], p_min_effect=p_min, gg_epsilon=greenhouse_geisser(Yadj),
        resid_var_min=float(np.nanmin(rv)), resid_var_max=float(np.nanmax(rv)),
        sf_upper95=sf.get("sf_upper95", np.nan), sf_crit=sf.get("sf_crit", np.nan), sf_p=sf.get("sf_p", np.nan),
        sf_equivalent=bool(sf.get("sf_equivalent", False)),
        host_effect=float(obs["eta"]) if obs.get("eta") is not None else np.nan, host_adjusted=H is not None,
        boot_sigma2=np.asarray(boot["sigma2_deb"]), effects=eff)


def _remap_boot(boot_idx: np.ndarray, keep: np.ndarray) -> np.ndarray:
    """Map shared bootstrap row indices onto the rows kept for this cell."""
    if keep.all():
        return boot_idx
    new_pos = np.cumsum(keep) - 1
    # dropped rows are replaced by a kept row of the same draw (rare: only all-missing CVs)
    fallback = int(np.flatnonzero(keep)[0])
    b = np.where(keep[boot_idx], boot_idx, fallback)
    return new_pos[b]


def global_test_F(Y: np.ndarray, H: np.ndarray | None = None) -> tuple[float, float]:
    """Parametric randomised-block F test (fast; used by the power analysis); host-adjusted with ``H``."""
    keep = np.sum(~np.isnan(Y), axis=1) >= 2
    s = twoway_stats(Y[keep], None if H is None else np.asarray(H, float)[keep])
    J = Y.shape[1]
    df2, F = float(s["df_res"]), float(s["F"])
    if not (df2 > 0 and np.isfinite(F)):
        return F, np.nan
    return F, float(stats.f.sf(F, J - 1, df2))


def global_test_perm(Y: np.ndarray, n_perm: int, rng: np.random.Generator,
                     H: np.ndarray | None = None) -> tuple[float, float]:
    """Within-CV permutation test, statistic = debiased sigma_A^2 (host-adjusted with ``H``; host cells fixed)."""
    keep = np.sum(~np.isnan(Y), axis=1) >= 2
    Y = Y[keep]
    H = None if H is None else np.asarray(H, float)[keep]
    s = float(twoway_stats(Y, H)["sigma2_deb"])
    null = permutation_null(Y, n_perm, rng, H=H)["sigma2_deb"]
    return s, float((1 + np.sum(null >= s - 1e-12)) / (1 + n_perm))


# --------------------------------------------------------------------------- #
# Per-origin deviations (exploratory): simultaneous CIs, BH, rank intervals
# --------------------------------------------------------------------------- #
def origin_deviations(Y: np.ndarray, codes: list[str], strata: np.ndarray, n_boot: int,
                      rng: np.random.Generator, alpha: float = 0.05, H: np.ndarray | None = None,
                      host: HostFit | None = None) -> pd.DataFrame:
    """delta(n) = tau(n) - mean Arab tau, per origin, from per-CV values.

    Marginal stratified-t CIs, simultaneous max-|t| bootstrap band, bootstrap
    rank intervals (rank 1 = highest delta). With ``H`` (aligned with ``Y``) delta(n) is net of the
    common host effect (``host``: fit to use, default fitted on ``Y``); the per-CV values carry the
    influence of eta_hat.
    """
    D = Y - _nanmean(Y, -1)[:, None]
    if H is not None and np.any(np.asarray(H) > 0):
        host = host if host is not None else host_fit(Y, H, strata, alpha)
        Hm = np.where(np.isnan(Y), np.nan, np.asarray(H, float))
        DH = Hm - _nanmean(Hm, -1)[:, None]
        D = np.column_stack([host_adjusted_values(D[:, j], DH[:, j], host, strata) for j in range(D.shape[1])])
    ts = [t_summary(D[:, j], alpha, strata) for j in range(len(codes))]
    est = np.array([t.estimate for t in ts])
    se = np.array([t.se for t in ts])
    bidx = stratified_bootstrap_indices(strata, n_boot, rng)
    with np.errstate(invalid="ignore", divide="ignore"):
        Eb = _nanmean(D[bidx], 1)                                      # (B, J)
        maxt = np.nanmax(np.abs(Eb - est) / np.where(se > 0, se, np.nan), axis=1)
    c = float(np.nanpercentile(maxt, 100 * (1 - alpha))) if np.isfinite(maxt).any() else np.nan
    ranks = (-Eb).argsort(1).argsort(1) + 1
    r_lo, r_hi = np.percentile(ranks, [100 * alpha / 2, 100 * (1 - alpha / 2)], axis=0)
    return pd.DataFrame({"nationality": codes, "delta": est, "se": se,
                         "ci_low": [t.ci_low for t in ts], "ci_high": [t.ci_high for t in ts],
                         "sim_ci_low": est - c * se, "sim_ci_high": est + c * se,
                         "p": [t.p for t in ts], "n_cv": [t.n_cv for t in ts],
                         "rank": (-est).argsort().argsort() + 1, "rank_ci_low": r_lo, "rank_ci_high": r_hi})


def hotelling_test(Y: np.ndarray, strata: np.ndarray) -> dict[str, float]:
    """CV-clustered Wald cross-check for H1a: Hotelling T^2 on per-CV deviation vectors.

    Uses J-1 of the J per-CV deviations (they sum to zero), within-occupation
    pooled covariance, F reference with nu = I - #occupations. Needs nu >= J-1.
    """
    D = Y - _nanmean(Y, -1)[:, None]
    D = D[:, :-1]
    ok = ~np.isnan(D).any(1)
    D, st = D[ok], np.asarray(strata)[ok]
    labs = np.unique(st)
    p = D.shape[1]
    I = D.shape[0]
    nu = I - labs.size
    if nu < p:
        return dict(T2=np.nan, F=np.nan, df1=p, df2=np.nan, p=np.nan,
                    note=f"not computable: {I} CVs, {labs.size} strata, {p} restrictions")
    Dc = np.vstack([D[st == s] - D[st == s].mean(0) for s in labs])
    S = Dc.T @ Dc / nu
    nj = np.array([np.sum(st == s) for s in labs])
    dbar = np.mean([D[st == s].mean(0) for s in labs], axis=0)
    c = np.sum(1.0 / (labs.size ** 2 * nj))
    T2 = float(dbar @ np.linalg.solve(c * S, dbar))
    F = (nu - p + 1) / (p * nu) * T2
    df2 = nu - p + 1
    return dict(T2=T2, F=float(F), df1=p, df2=df2, p=float(stats.f.sf(F, p, df2)), note="")


# --------------------------------------------------------------------------- #
# Profile-interaction test (nationality x model / condition / wording)
# --------------------------------------------------------------------------- #
@dataclass
class InteractionResult:
    levels: list[str]
    n_cv: int
    n_nat: int
    T: float
    p_perm: float
    profiles: pd.DataFrame


def profile_interaction_test(Ys: list[np.ndarray], levels: list[str], codes: list[str],
                             n_perm: int, rng: np.random.Generator) -> InteractionResult:
    """Does the nationality profile differ across levels (models, conditions, wordings)?

    ``Ys`` are (I, J) matrices over the SAME base CVs and nationalities. Rows
    are centred within level; profile = column means; T = sum of squared
    deviations of level profiles from their average. Null: within each base CV
    the level labels are permuted jointly across nationalities.
    """
    Z = np.stack([Y - _nanmean(Y, -1)[:, None] for Y in Ys])
    L, I, J = Z.shape

    def stat(Zb):
        P = _nanmean(Zb, -2)
        return np.nansum((P - _nanmean(P, -2)[..., None, :]) ** 2, axis=(-2, -1)), P

    T, P = stat(Z)
    Zt = np.transpose(Z, (1, 0, 2))
    count = 0
    done = 0
    while done < n_perm:
        b = min(1000, n_perm - done)
        order = np.argsort(rng.random((b, I, L)), axis=-1)
        Zp = Zt[np.arange(I)[None, :, None], order]
        Tp, _ = stat(np.transpose(Zp, (0, 2, 1, 3)))
        count += int(np.sum(Tp >= T - 1e-12))
        done += b
    return InteractionResult(levels=list(levels), n_cv=I, n_nat=J, T=float(T),
                             p_perm=float((1 + count) / (1 + n_perm)),
                             profiles=pd.DataFrame(P.T, index=codes, columns=levels))


# --------------------------------------------------------------------------- #
# Variance components (planning inputs, experimental_design.md §1.6)
# --------------------------------------------------------------------------- #
def _impute_additive(Y: np.ndarray, n_iter: int = 50) -> tuple[np.ndarray, int]:
    """Fill missing stimulus cells of an (I, N, K) array with the fit of the model containing all
    main effects and two-way interactions (Yates-type iterative imputation). Returns (filled, n_missing).
    Residual degrees of freedom are reduced by n_missing by the caller."""
    Y = np.array(Y, float)
    miss = np.isnan(Y)
    n = int(miss.sum())
    if n == 0:
        return Y, 0
    if Y.shape[2] == 1:
        fill = _nanmean(Y, 0)[None] + _nanmean(Y, 1)[:, None] - np.nanmean(Y)
    else:
        fill = np.broadcast_to(np.nanmean(Y), Y.shape)
    Y[miss] = np.broadcast_to(fill, Y.shape)[miss]
    for _ in range(n_iter):
        g = Y.mean()
        mi, mn, mk = Y.mean((1, 2)), Y.mean((0, 2)), Y.mean((0, 1))
        fit = (Y.mean(2)[:, :, None] + Y.mean(1)[:, None, :] + Y.mean(0)[None, :, :]
               - mi[:, None, None] - mn[None, :, None] - mk[None, None, :] + g)
        if Y.shape[2] == 1:
            fit = mi[:, None, None] + mn[None, :, None] - g + 0 * Y
        delta = np.max(np.abs(Y[miss] - fit[miss]))
        Y[miss] = fit[miss]
        if delta < 1e-8:
            break
    return Y, n


def variance_components(cell: Cell, rep: np.ndarray) -> dict[str, float]:
    """Moment estimates of the §1.6 components for one model x condition x outcome.

    ``rep`` is the (I, N, K, R) replicate array aligned with ``cell``.
    sigma2_eps: pooled within-stimulus variance; rho_eps: cross-clone correlation
    of decoder noise at the same (CV, variant, replicate); the rest from the
    three-way CV x nationality x variant ANOVA on stimulus means (CVs with all
    cells observed): E[MS_ink] = s2_atk + (1-rho) s2_eps / r,
    E[MS_in] = K s2_at + E[MS_ink], E[MS_nk] = I s2_tk + E[MS_ink],
    E[MS_ik] = N s2_ak + E[MS_ink] + N rho s2_eps / r.
    """
    x = rep
    with np.errstate(invalid="ignore", divide="ignore"):
        cnt = np.sum(~np.isnan(x), -1)
        m = _nanmean(x, -1)
        dev = x - m[..., None]
        ss = np.nansum(dev ** 2, -1)
        s2_eps = float(np.nansum(ss) / np.sum(np.clip(cnt - 1, 0, None))) if np.sum(cnt > 1) else np.nan
        # rho: centred residuals, cross-nationality products at same (i, k, r)
        e = np.transpose(dev, (0, 2, 3, 1))                              # (I, K, R, N)
        valid = ~np.isnan(e)
        S1 = np.nansum(e, -1)
        S2 = np.nansum(e ** 2, -1)
        mm = valid.sum(-1)
        cross = np.sum(S1 ** 2 - S2)
        pairs = np.sum(mm * (mm - 1))
        rho = float((cross / pairs) / (np.sum(S2) / np.sum(mm))) if pairs > 0 and np.sum(S2) > 0 else np.nan
    r_bar = float(np.nanmean(np.where(cell.n_valid > 0, cell.n_valid, np.nan)))
    rho_c = float(np.clip(rho, 0, 1)) if np.isfinite(rho) else 0.0
    eps_term = (1 - rho_c) * s2_eps / r_bar if np.isfinite(s2_eps) else 0.0
    Yk = cell.Yk
    keep = np.sum(~np.isnan(Yk).reshape(Yk.shape[0], -1), 1) > 0
    Yc, n_miss = _impute_additive(Yk[keep])
    comp = keep
    I, N, K = Yc.shape
    out = dict(n_cv=int(Yk.shape[0]), n_cells_imputed=int(n_miss), n_nat=int(N), K=int(K), r_bar=r_bar,
               sigma2_eps=s2_eps, rho_eps=rho, grand_mean=float(np.nanmean(Yk)))
    if I < 2:
        out.update(sigma2_at=np.nan, sigma2_atk=np.nan, sigma2_ak=np.nan, sigma2_tk=np.nan, sigma2_cv=np.nan,
                   df_cv=0)
        for k in ("sigma2_eps", "sigma2_at", "sigma2_atk", "sigma2_ak", "sigma2_tk", "sigma2_cv"):
            v = out.get(k)
            out[k.replace("sigma2", "sd")] = float(np.sqrt(v)) if v is not None and np.isfinite(v) else np.nan
        return out
    g = Yc.mean()
    mi, mn, mk = Yc.mean((1, 2)), Yc.mean((0, 2)), Yc.mean((0, 1))
    min_, mik, mnk = Yc.mean(2), Yc.mean(1), Yc.mean(0)
    ss_in = K * np.sum((min_ - mi[:, None] - mn[None, :] + g) ** 2)
    ss_ik = N * np.sum((mik - mi[:, None] - mk[None, :] + g) ** 2)
    ss_nk = I * np.sum((mnk - mn[:, None] - mk[None, :] + g) ** 2)
    res = (Yc - min_[:, :, None] - mik[:, None, :] - mnk[None, :, :]
           + mi[:, None, None] + mn[None, :, None] + mk[None, None, :] - g)
    if K > 1:
        df_ink = max((I - 1) * (N - 1) * (K - 1) - n_miss, 1)
        ms_ink = np.sum(res ** 2) / df_ink
        ms_in = ss_in / ((I - 1) * (N - 1))
        ms_ik = ss_ik / ((I - 1) * (K - 1))
        ms_nk = ss_nk / ((N - 1) * (K - 1))
        s2_atk = max(ms_ink - eps_term, 0.0)
        s2_at = max((ms_in - ms_ink) / K, 0.0)
        s2_ak = max((ms_ik - ms_ink - N * rho_c * s2_eps / r_bar) / N, 0.0) if np.isfinite(s2_eps) else np.nan
        s2_tk = max((ms_nk - ms_ink) / I, 0.0)
    else:
        ms_in = ss_in / max((I - 1) * (N - 1) - n_miss, 1)
        s2_at = max(ms_in - eps_term, 0.0)
        s2_atk = s2_ak = s2_tk = np.nan
    # between-CV variance net of occupation x tier
    rm = Yc.mean((1, 2))
    grp = pd.Series(rm).groupby([cell.occupations[comp], cell.tiers[comp]])
    dev_cv = rm - grp.transform("mean").to_numpy()
    df_cv = I - grp.ngroups
    if df_cv > 0:
        s2 = float(np.sum(dev_cv ** 2) / df_cv)
        corr = (s2_at / N + (0 if np.isnan(s2_ak) else s2_ak / K)
                + (0 if np.isnan(s2_atk) else s2_atk / (N * K))
                + (s2_eps * (rho_c / K + (1 - rho_c) / (N * K)) / r_bar if np.isfinite(s2_eps) else 0))
        s2_cv = max(s2 - corr, 0.0)
    else:
        s2_cv = np.nan
    out.update(sigma2_at=float(s2_at), sigma2_atk=float(s2_atk), sigma2_ak=float(s2_ak),
               sigma2_tk=float(s2_tk), sigma2_cv=float(s2_cv), df_cv=int(df_cv))
    for k in ("sigma2_eps", "sigma2_at", "sigma2_atk", "sigma2_ak", "sigma2_tk", "sigma2_cv"):
        v = out.get(k)
        out[k.replace("sigma2", "sd")] = float(np.sqrt(v)) if v is not None and np.isfinite(v) else np.nan
    return out
