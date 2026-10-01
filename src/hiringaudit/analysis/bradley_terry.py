"""Bradley-Terry model for the forced-choice task (experimental_design.md §1.4 E).

    logit P(slot A chosen) = gamma[k] + (beta[nat_A] + theta[cv_A]) - (beta[nat_B] + theta[cv_B])
                             + eta_FC * (host_A - host_B)

* ``beta`` — nationality worth on the log-odds scale. Reported two ways:
  ``beta`` identified by sum over the 22 Arab origins = 0 (comparable to
  delta(n); primary for RQ4) and ``beta_vs_ref`` = beta - beta[DEU] (display).
  exp(beta_a - beta_b) is the odds that a is preferred to b, other things equal.
* ``gamma[k]`` — position (slot-A) bias per wording variant k (variant is a
  blocking factor, A3); ``gamma`` (mean over variants) is reported.
* ``theta`` — base-CV quality nuisance terms, identified only within sets of
  CVs compared with each other; a tiny ridge picks the minimum-norm solution
  without affecting beta or gamma beyond O(ridge).
* ``eta_FC`` — host-national covariate (setting 2026-10-01): host_X = 1 if the candidate's
  nationality equals the pair's base country (both CVs of a pair share it). beta is then net of a
  common host bonus; eta_FC is reported as a secondary quantity (log-odds).

Inference: base CVs are the independent units. Each trial involves two CVs, so
the bootstrap draws CV multiplicities within occupation and weights each
prompt by the product of its two CVs' multiplicities.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import sparse
from scipy.special import expit

from .core import stratified_bootstrap_indices


@dataclass
class BTData:
    """Prompt-level aggregated comparisons (replicates collapsed)."""
    ia: np.ndarray        # nationality index in slot A
    ib: np.ndarray
    ca: np.ndarray        # CV index in slot A
    cb: np.ndarray
    k: np.ndarray         # number of A choices (fractional for implied data)
    n: np.ndarray         # number of valid responses (weights)
    group: np.ndarray     # swap-group id (quad x CV in slot A) for the randomisation test
    pos_group: np.ndarray  # wording-variant index (position-bias block)
    codes: list[str]
    cvs: list[str]
    cv_strata: np.ndarray  # occupation per CV
    variants: list[str]
    hd: np.ndarray | None = None   # host_national_a - host_national_b per prompt (None: no host information)


@dataclass
class BTFit:
    codes: list[str]
    theta_ref: np.ndarray        # worth relative to the pinned reference (NaN if absent)
    gamma_k: np.ndarray          # position bias per variant (empty if position=False)
    se_model: np.ndarray         # model-based SEs of theta_ref (ignore clustering)
    converged: bool
    n_iter: int
    loglik: float
    separation_suspected: bool
    n_comparisons: float
    host_effect: float = np.nan          # eta_FC (log-odds); NaN if the host covariate is not in the model
    host_se: float = np.nan

    @property
    def gamma(self) -> float:
        return float(np.nanmean(self.gamma_k)) if self.gamma_k.size else np.nan


def prepare_fc(fc: pd.DataFrame, codes: list[str] | None = None) -> BTData:
    """Aggregate valid forced-choice rows of ONE model x condition to prompt level."""
    v = fc[(fc["parse_status"] == "ok").fillna(False) & fc["choice"].isin(["A", "B"]).fillna(False)].copy()
    if v.empty:
        raise ValueError("no valid forced-choice responses")
    v["is_a"] = (v["choice"] == "A").astype(float)
    keys = ["quad_id", "prompt_variant", "cv_a", "cv_b", "nationality_a", "nationality_b"]
    has_host = {"host_national_a", "host_national_b"} <= set(v.columns)
    if has_host:
        v["hd"] = v["host_national_a"].astype(float) - v["host_national_b"].astype(float)
        g = v.groupby(keys, observed=True).agg(k=("is_a", "sum"), n=("is_a", "count"), hd=("hd", "first")).reset_index()
    else:
        g = v.groupby(keys, observed=True)["is_a"].agg(k="sum", n="count").reset_index()
    for c in keys:
        g[c] = g[c].astype(str)
    present = set(g["nationality_a"]) | set(g["nationality_b"])
    codes = [c for c in codes if c in present] if codes is not None else sorted(present)
    cvs = sorted(set(g["cv_a"]) | set(g["cv_b"]))
    variants = sorted(g["prompt_variant"].unique())
    ni = {c: k for k, c in enumerate(codes)}
    ci = {c: k for k, c in enumerate(cvs)}
    vi = {c: k for k, c in enumerate(variants)}
    occ = (pd.concat([fc[["cv_a", "occupation"]].rename(columns={"cv_a": "cv"}),
                      fc[["cv_b", "occupation"]].rename(columns={"cv_b": "cv"})])
           .astype(str).drop_duplicates("cv").set_index("cv")["occupation"])
    grp = pd.factorize(g["quad_id"] + "||" + g["cv_a"])[0]
    return BTData(ia=g["nationality_a"].map(ni).to_numpy(int), ib=g["nationality_b"].map(ni).to_numpy(int),
                  ca=g["cv_a"].map(ci).to_numpy(int), cb=g["cv_b"].map(ci).to_numpy(int),
                  k=g["k"].to_numpy(float), n=g["n"].to_numpy(float), group=grp,
                  pos_group=g["prompt_variant"].map(vi).to_numpy(int), codes=list(codes), cvs=cvs,
                  cv_strata=occ.reindex(cvs).to_numpy(), variants=variants,
                  hd=g["hd"].to_numpy(float) if has_host else None)


def fit_bt(data: BTData, reference: str = "DEU", position: bool = True,
           weights: np.ndarray | None = None, ia: np.ndarray | None = None,
           ib: np.ndarray | None = None, ridge_theta: float = 0.01,
           ridge_cv: float = 1e-4, max_iter: int = 100, tol: float = 1e-9, host: bool = True) -> BTFit:
    """Penalised-Newton ML fit with CV nuisance terms, per-variant position bias and (``host`` and
    host information present) the host-national covariate host_A - host_B (unpenalised).

    ``ridge_theta`` = 0.01 is a weak penalty (a N(0, 10^2) prior on each
    log-odds worth): negligible for |beta| < 3, but it keeps estimates finite
    under (quasi-)separation, common in bootstrap resamples and implied data at
    pilot scale. Set 0 for pure ML.
    """
    ia = data.ia if ia is None else ia
    ib = data.ib if ib is None else ib
    N, C = len(data.codes), len(data.cvs)
    G = int(data.pos_group.max()) + 1 if position else 0
    ref = data.codes.index(reference) if reference in data.codes else 0
    n = data.n * (1.0 if weights is None else weights)
    use = n > 0
    ia, ib, ca, cb, pg, n = ia[use], ib[use], data.ca[use], data.cb[use], data.pos_group[use], n[use]
    y = np.clip(data.k[use] / data.n[use], 0, 1)
    hd = data.hd[use] if (host and data.hd is not None) else None
    use_host = hd is not None and bool(np.any(hd != 0))
    off_t, off_g = G, G + N
    P = off_g + C + (1 if use_host else 0)
    rows = np.arange(ia.size)
    rr, cols, vals = [], [], []
    if position:
        rr.append(rows); cols.append(pg); vals.append(np.ones(rows.size))
    rr += [rows, rows, rows, rows]
    cols += [off_t + ia, off_t + ib, off_g + ca, off_g + cb]
    vals += [np.ones(rows.size), -np.ones(rows.size), np.ones(rows.size), -np.ones(rows.size)]
    if use_host:
        rr.append(rows); cols.append(np.full(rows.size, P - 1)); vals.append(hd.astype(float))
    X = sparse.csr_matrix((np.concatenate(vals), (np.concatenate(rr), np.concatenate(cols))),
                          shape=(rows.size, P))
    present = np.zeros(N, bool)
    present[np.unique(np.concatenate([ia, ib]))] = True
    pen = np.zeros(P)
    pen[off_t:off_g] = ridge_theta
    pen[off_t + ref] = 1e8
    pen[off_t:off_g][~present] = 1e8
    pen[off_g:off_g + C] = ridge_cv
    beta = np.zeros(P)

    def objective(b):
        eta = X @ b
        return float(np.sum(n * (y * eta - np.logaddexp(0, eta))) - 0.5 * np.sum(pen * b * b))

    ll = objective(beta)
    converged = False
    it = 0
    for it in range(1, max_iter + 1):
        p = expit(X @ beta)
        grad = X.T @ (n * (y - p)) - pen * beta
        H = (X.T @ X.multiply((n * p * (1 - p))[:, None])).toarray() + np.diag(pen)
        try:
            step = np.linalg.solve(H, grad)
        except np.linalg.LinAlgError:
            step = np.linalg.lstsq(H, grad, rcond=None)[0]
        t = 1.0
        for _ in range(30):
            cand = beta + t * step
            ll_c = objective(cand)
            if ll_c >= ll - 1e-10:
                break
            t /= 2
        beta, ll = cand, ll_c
        if np.max(np.abs(t * step)) < tol * (1 + np.max(np.abs(beta))):
            converged = True
            break
    p = expit(X @ beta)
    H = (X.T @ X.multiply((n * p * (1 - p))[:, None])).toarray() + np.diag(pen)
    try:
        dinv = np.diag(np.linalg.inv(H))
        se = np.sqrt(np.clip(dinv[off_t:off_g], 0, None))
        host_se = float(np.sqrt(max(dinv[P - 1], 0))) if use_host else np.nan
    except np.linalg.LinAlgError:
        se = np.full(N, np.nan)
        host_se = np.nan
    th = beta[off_t:off_g].copy()
    th[~present] = np.nan
    se[~present] = np.nan
    se[ref] = 0.0
    sep = bool(np.nanmax(np.abs(th)) > 15) if present.any() else False
    return BTFit(codes=list(data.codes), theta_ref=th, gamma_k=beta[:G].copy() if position else np.array([]),
                 se_model=se, converged=converged, n_iter=it, loglik=ll, separation_suspected=sep,
                 n_comparisons=float(n.sum()), host_effect=float(beta[P - 1]) if use_host else np.nan,
                 host_se=host_se)


def arab_centred(theta: np.ndarray, a_idx: np.ndarray) -> np.ndarray:
    """beta identified by sum over Arab origins = 0."""
    return theta - np.nanmean(theta[..., a_idx], axis=-1, keepdims=theta.ndim > 1)


def cv_multiplicities(cvs: list[str], strata: np.ndarray, B: int, rng: np.random.Generator) -> np.ndarray:
    idx = stratified_bootstrap_indices(strata, B, rng)
    return np.stack([np.bincount(r, minlength=len(cvs)) for r in idx]).astype(float)


@dataclass
class BTResult:
    table: pd.DataFrame
    gamma: float
    gamma_ci: tuple[float, float]
    gamma_k: dict
    fit: BTFit
    boot_beta: np.ndarray        # (B, N) Arab-centred
    n_boot_failed: int
    p_perm_within_arab: float
    sd_beta_arab: float          # plug-in SD (divisor J) of Arab-centred beta
    sigma_A_fc: float            # debiased: plug-in variance minus mean bootstrap variance
    host_effect: float = np.nan  # eta_FC (log-odds), secondary
    host_ci: tuple[float, float] = (np.nan, np.nan)


def bt_analysis(data: BTData, arab_codes: list[str], n_boot: int, n_perm: int,
                rng: np.random.Generator, reference: str = "DEU", alpha: float = 0.05,
                position: bool = True, mult: np.ndarray | None = None, host: bool = True) -> BTResult:
    """Point fit, CV-cluster bootstrap CIs, within-Arab swap randomisation test.
    ``host``: include the host-national covariate when the data carry host information."""
    fit = fit_bt(data, reference=reference, position=position, host=host)
    a_idx = np.array([data.codes.index(c) for c in arab_codes if c in data.codes], int)
    if mult is None:
        mult = cv_multiplicities(data.cvs, data.cv_strata, n_boot, rng)
    W = mult[:, data.ca] * mult[:, data.cb]
    draws = np.full((W.shape[0], len(data.codes)), np.nan)
    draws_ref = np.full_like(draws, np.nan)
    gammas = np.full(W.shape[0], np.nan)
    hosts = np.full(W.shape[0], np.nan)
    failed = 0
    for b in range(W.shape[0]):
        if not np.any(W[b] > 0):
            failed += 1
            continue
        fb = fit_bt(data, reference=reference, position=position, weights=W[b], host=host)
        if not fb.converged or fb.separation_suspected:
            failed += 1
            continue
        draws_ref[b] = fb.theta_ref
        draws[b] = arab_centred(fb.theta_ref, a_idx) if a_idx.size else fb.theta_ref
        gammas[b] = fb.gamma
        hosts[b] = fb.host_effect
    beta = arab_centred(fit.theta_ref, a_idx) if a_idx.size else fit.theta_ref
    n_ok = W.shape[0] - failed
    ok_b = n_ok > 0
    nanv = np.full(len(data.codes), np.nan)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)          # codes absent from every resample
        lo, hi = (np.nanpercentile(draws, [100 * alpha / 2, 100 * (1 - alpha / 2)], axis=0) if ok_b
                  else (nanv, nanv))
        rlo, rhi = (np.nanpercentile(draws_ref, [100 * alpha / 2, 100 * (1 - alpha / 2)], axis=0) if ok_b
                    else (nanv, nanv))
    J = a_idx.size
    sd_a = float(np.sqrt(np.nanmean(beta[a_idx] ** 2))) if J > 1 else np.nan
    if J > 1 and n_ok >= 2:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            noise = float(np.nanmean(np.nanvar(draws[:, a_idx], axis=0, ddof=1)))
        sig = float(np.sqrt(max(sd_a ** 2 - noise, 0.0)))
    else:
        sig = np.nan
    p_perm = bt_within_arab_swap_test(data, a_idx, n_perm, rng, reference, position, host=host) \
        if (n_perm > 0 and J > 2) else np.nan
    tab = pd.DataFrame({"nationality": data.codes, "beta": beta, "ci_low": lo, "ci_high": hi,
                        "beta_vs_ref": fit.theta_ref, "ci_low_vs_ref": rlo, "ci_high_vs_ref": rhi,
                        "se_model_vs_ref": fit.se_model,
                        "p_preferred_over_ref": expit(fit.theta_ref)})
    gci = ((float(np.nanpercentile(gammas, 100 * alpha / 2)), float(np.nanpercentile(gammas, 100 * (1 - alpha / 2))))
           if position and ok_b else (np.nan, np.nan))
    hci = ((float(np.nanpercentile(hosts, 100 * alpha / 2)), float(np.nanpercentile(hosts, 100 * (1 - alpha / 2))))
           if np.isfinite(fit.host_effect) and np.isfinite(hosts).any() else (np.nan, np.nan))
    return BTResult(table=tab, gamma=fit.gamma, gamma_ci=gci,
                    gamma_k=dict(zip(data.variants, fit.gamma_k.tolist())) if position else {},
                    fit=fit, boot_beta=draws, n_boot_failed=failed, p_perm_within_arab=p_perm,
                    sd_beta_arab=sd_a, sigma_A_fc=sig, host_effect=fit.host_effect, host_ci=hci)


def bt_within_arab_swap_test(data: BTData, a_idx: np.ndarray, n_perm: int, rng: np.random.Generator,
                             reference: str = "DEU", position: bool = True, host: bool = True) -> float:
    """Randomisation test of H0: all Arab origins have equal worth (exploratory).

    Two prompts of a quad that share the CV in slot A differ only by swapping
    the nationalities; for Arab-Arab quads they are exchangeable under the sharp
    null, so their labels are swapped jointly with probability 1/2 per group.
    Quads with a host national are never swapped (the host term makes their prompts non-exchangeable).
    Statistic: SD of Arab-centred worths.
    """
    is_arab = np.zeros(len(data.codes), bool)
    is_arab[a_idx] = True
    both = is_arab[data.ia] & is_arab[data.ib]
    if data.hd is not None:
        both = both & (data.hd == 0)
    if not both.any():
        return np.nan

    def stat(ia, ib):
        f = fit_bt(data, reference=reference, position=position, ia=ia, ib=ib, host=host)
        return float(np.nanstd(arab_centred(f.theta_ref, a_idx)[a_idx]))

    t_obs = stat(data.ia, data.ib)
    n_groups = data.group.max() + 1
    count = 0
    for _ in range(n_perm):
        flip = (rng.random(n_groups) < 0.5)[data.group] & both
        count += stat(np.where(flip, data.ib, data.ia), np.where(flip, data.ia, data.ib)) >= t_obs - 1e-12
    return float((1 + count) / (1 + n_perm))


def implied_from_fc(data: BTData, S: np.ndarray, ie_cvs: list[str], ie_codes: list[str],
                    tie_free: bool = False) -> BTData:
    """IE-implied comparisons for the SAME forced-choice prompts (RQ4 common scale).

    ``S`` is (I, N, D): replicate-level independent-evaluation scores (all
    wording variants x replicates pooled as draws) per base CV x nationality.
    For prompt (cv_A: a) vs (cv_B: b) the outcome is
    pi = P(Y(cv_A, a) > Y(cv_B, b)) + 1/2 P(tie) over all pairs of draws
    (experimental_design.md §1.4 E); with ``tie_free`` ties are dropped:
    pi = P(>) / (P(>) + P(<)), and the prompt is dropped if every pair ties.
    No position term applies (fit with ``position=False``).
    """
    ci = {c: k for k, c in enumerate(ie_cvs)}
    ni = {c: k for k, c in enumerate(ie_codes)}
    pi, w = np.zeros(data.ia.size), np.zeros(data.ia.size)
    for r in range(data.ia.size):
        cva, cvb = data.cvs[data.ca[r]], data.cvs[data.cb[r]]
        na, nb = data.codes[data.ia[r]], data.codes[data.ib[r]]
        if cva not in ci or cvb not in ci or na not in ni or nb not in ni:
            continue
        xa, xb = S[ci[cva], ni[na]], S[ci[cvb], ni[nb]]
        xa, xb = xa[~np.isnan(xa)][:, None], xb[~np.isnan(xb)][None, :]
        if xa.size == 0 or xb.size == 0:
            continue
        gt, lt = float(np.mean(xa > xb)), float(np.mean(xa < xb))
        if tie_free:
            if gt + lt > 0:
                pi[r], w[r] = gt / (gt + lt), 1.0
        else:
            pi[r], w[r] = gt + 0.5 * (1 - gt - lt), 1.0
    keep = w > 0
    return BTData(ia=data.ia[keep], ib=data.ib[keep], ca=data.ca[keep], cb=data.cb[keep],
                  k=pi[keep], n=np.ones(keep.sum()), group=data.group[keep],
                  pos_group=np.zeros(keep.sum(), int), codes=list(data.codes), cvs=list(data.cvs),
                  cv_strata=data.cv_strata.copy(), variants=["all"],
                  hd=None if data.hd is None else data.hd[keep])
