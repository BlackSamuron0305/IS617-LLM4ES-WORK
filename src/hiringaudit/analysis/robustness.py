"""Pre-specified robustness checks (experimental_design.md §8).

Implemented here:
  R1  exclude contested members (SOM, DJI, COM)
  R3  per wording; nationality x wording profile test; profile correlation across wordings
  R4  greedy decoding (rows with arm == "greedy" in the same run)
  R5  worst-case (Manski) bounds for Delta contrasts: non-ok calls (all types, incl. terminal
      api_error) of the target set at the lower support limit and of the comparison nationality at
      the upper limit, and the reverse. Pre-registered for the robust label: OBSERVED support
      (CV-specific: min / max of the valid responses of the same base CV). Logical support (scale limits 0 / 100) is reported descriptively with
      its width (check "R5-logical") and becomes decision-relevant only if the differential-
      missingness test rejects for that model x condition (review round 2, N3)
  SVI single-value imputation sensitivity (formerly called "R5 bounds"; review M2): every non-ok
      call imputed as the lowest / highest value. NOT a bound; used for sigma_A, for which no
      simple worst-case bound exists
  R6  leave one occupation out;  R7 tier-specific;  R8 within-CV rank outcome
  HX  host-national exclusion (setting 2026-10-01): every host-national clone (nationality == the
      CV's base country) is removed and sigma_A (22 and 19 origins) and Delta(A_bar, b) are recomputed
      WITHOUT the host adjustment; required for the 'robust' label like R1. All other checks use the
      primary, host-adjusted estimators.
  Robustness arms other than greedy decoding (R4) are reported by name (the R12 language-line arm
  was removed with the stimulus-table simplification of 2026-09-30)
R2 (interview) runs through the main pipeline; R9 (POL / NONE references) is H2b / H2d; R11 is
inside H1d; R13 is the shrinkage column of the heterogeneity effects table; R10 (logprobs) needs
inputs the processed schema does not carry.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from .core import (
    Cell,
    _nanmean,
    aggregate_stimulus,
    build_cell,
    contrast_values,
    counterfactual,
    heterogeneity,
    host_fit,
    profile_interaction_test,
    t_summary,
)
from .schema import REFERENCE

BENCH = ("DEU", "POL", "TUR", "NONE")


def summarise_matrix(Y: np.ndarray, codes: list[str], groups: dict[str, str], strata: np.ndarray,
                     n_perm: int, rng: np.random.Generator, alpha: float, sesoi: float,
                     arab: list[str] | None = None, bench: tuple[str, ...] = BENCH,
                     H: np.ndarray | None = None, exclude_host: bool = False) -> dict:
    """sigma_A (debiased, ncf CI, permutation p) + Delta(A_bar, b) for b in DEU/POL/TUR/NONE.

    ``H`` (host-national indicator aligned with ``Y``): the primary estimators adjust for the common
    host effect. ``exclude_host``: host-national cells are set to missing instead and nothing is
    adjusted (sensitivity HX; the permutation test keeps the removed cells in place).
    """
    idx = {c: k for k, c in enumerate(codes)}
    arab = arab if arab is not None else [c for c in codes if groups.get(c) == "arab"]
    a = np.array([idx[c] for c in arab if c in idx], dtype=int)
    has_host = H is not None and bool(np.any(np.asarray(H) > 0))
    fixed = None
    if exclude_host:
        if has_host:
            hm = np.asarray(H) > 0
            Y = np.where(hm, np.nan, Y)
            fixed = hm
        H, has_host = None, False
    Hc = np.asarray(H, float) if has_host else None
    out: dict = {"host_handling": "excluded" if exclude_host else ("adjusted" if has_host else "none")}
    if n_perm > 0 and a.size >= 3 and Y.shape[0] >= 2:
        h = heterogeneity(Y[:, a], [codes[i] for i in a], strata, n_perm, 0, rng, alpha, sesoi,
                          boot_idx=np.zeros((1, Y.shape[0]), int), H=None if Hc is None else Hc[:, a],
                          fixed=None if fixed is None else fixed[:, a])
        out.update(sigma_A=h.sigma_A, p_perm=h.p_perm, sigma_ci_low=h.ncf_ci_low, sigma_ci_high=h.ncf_ci_high,
                   upper95=h.upper95_one_sided, p_equivalence=h.p_equivalence, n_cv=h.n_cv)
    hf = host_fit(Y, Hc, strata, alpha) if Hc is not None else None
    if hf is not None and hf.identified:
        out["host_effect"] = hf.eta
    for b in bench:
        if b in idx and a.size:
            t = t_summary(contrast_values(Y, a, np.array([idx[b]]), Hc, hf, strata), alpha, strata)
            out[f"d_{b}"], out[f"d_{b}_lo"], out[f"d_{b}_hi"] = t.estimate, t.ci_low, t.ci_high
    return out


def _cell_summary(cell: Cell, Y: np.ndarray, rows: np.ndarray | None, n_perm, rng, alpha, sesoi, arab=None,
                  exclude_host: bool = False):
    rows = np.arange(Y.shape[0]) if rows is None else rows
    return summarise_matrix(Y[rows], cell.codes, cell.groups, cell.occupations[rows], n_perm, rng, alpha,
                            sesoi, arab, H=cell.host()[rows], exclude_host=exclude_host)


ARM_CHECK = {"greedy": ("R4", "greedy decoding (T=0) arm")}


def run_robustness(cell: Cell, ev: pd.DataFrame, outcome_scale: float, n_perm: int,
                   rng: np.random.Generator, alpha: float, sesoi: float,
                   arm_evs: dict[str, pd.DataFrame] | None = None,
                   support: str = "observed",
                   support_descriptive: str | None = "logical") -> tuple[pd.DataFrame, pd.DataFrame]:
    """All checks for one model x condition x outcome. Returns (summary rows, wording-profile rows).

    ``arm_evs`` maps robustness-arm names (evaluations rows with arm != 'primary', e.g. greedy)
    to their rows; each is summarised like the main analysis (baseline only).
    """
    rows = []

    def add(check, subset, res):
        rows.append(dict(model=cell.model, condition=cell.condition, outcome=cell.outcome, check=check,
                         subset=subset, **res))

    Y = cell.Y
    add("main", "all", _cell_summary(cell, Y, None, n_perm, rng, alpha, sesoi))
    # R1: exclude contested members
    unc = [c for c in cell.arab_codes if not cell.contested.get(c, False)]
    add("R1", "exclude contested (SOM, DJI, COM)", _cell_summary(cell, Y, None, n_perm, rng, alpha, sesoi, unc))
    # HX: exclude host-national clones (no host adjustment), 22 and 19 origins
    if cell.has_host:
        add("HX", "exclude host-national clones (22 origins)",
            _cell_summary(cell, Y, None, n_perm, rng, alpha, sesoi, exclude_host=True))
        add("HX", "exclude host-national clones (19 origins)",
            _cell_summary(cell, Y, None, n_perm, rng, alpha, sesoi, unc, exclude_host=True))
    # R3: per wording + nationality x wording test + profile correlations
    prof_rows = []
    if len(cell.variants) > 1:
        a = cell.cols(cell.arab_codes)
        for k, var in enumerate(cell.variants):
            add("R3", f"wording {var}", _cell_summary(cell, cell.Yk[:, :, k], None, n_perm, rng, alpha, sesoi))
        it = profile_interaction_test([cell.Yk[:, a, k] for k in range(len(cell.variants))], cell.variants,
                                      cell.arab_codes, n_perm, rng)
        P = it.profiles
        cors = []
        for i in range(len(cell.variants)):
            for j in range(i + 1, len(cell.variants)):
                cors.append(float(np.corrcoef(P.iloc[:, i], P.iloc[:, j])[0, 1]))
        prof_rows.append(dict(model=cell.model, condition=cell.condition, outcome=cell.outcome,
                              test="nationality x wording (22 Arab profile)", T=it.T, p_perm=it.p_perm,
                              mean_profile_correlation=float(np.mean(cors)) if cors else np.nan,
                              min_profile_correlation=float(np.min(cors)) if cors else np.nan))
    # SVI: single-value imputation sensitivity (not a bound)
    for lab, Yb in _svi_matrices(cell, ev, outcome_scale).items():
        add("SVI", f"single-value imputation sensitivity: {lab}",
            _cell_summary(cell, Yb, None, n_perm, rng, alpha, sesoi))
    # R5: worst-case (Manski) bounds for the Delta contrasts (robust-label support + descriptive support)
    supports = [("R5", support)]
    if support_descriptive and support_descriptive != support:
        supports.append(("R5-logical" if support_descriptive == "logical" else "R5-descriptive", support_descriptive))
    for chk, sup in supports:
        for b in BENCH:
            if b not in cell.codes:
                continue
            for lab, Yb in _manski_matrices(cell, ev, outcome_scale, b, sup).items():
                r = summarise_matrix(Yb, cell.codes, cell.groups, cell.occupations, 0, rng, alpha, np.nan,
                                     bench=(b,), H=cell.host())
                add(chk, f"Manski {lab} for Delta(A,{b}) (support: {sup})",
                    {k: v for k, v in r.items() if k.startswith(f"d_{b}")} | {"bench": b, "support": sup,
                                                                                "scenario": lab})
    # R6: leave one occupation out
    for occ in np.unique(cell.occupations):
        keep = np.flatnonzero(cell.occupations != occ)
        if keep.size >= 4:
            add("R6", f"without {occ}", _cell_summary(cell, Y, keep, n_perm, rng, alpha, sesoi))
    # R7: tier-specific
    for tier in np.unique(cell.tiers):
        keep = np.flatnonzero(cell.tiers == tier)
        if keep.size >= 3:
            add("R7", f"tier {tier}", _cell_summary(cell, Y, keep, n_perm, rng, alpha, sesoi))
    # R8: within-CV rank outcome (ranks across nationalities within CV x wording, averaged over wordings)
    Yr = np.full_like(cell.Yk, np.nan)
    for k in range(cell.Yk.shape[2]):
        Yr[:, :, k] = pd.DataFrame(cell.Yk[:, :, k]).rank(axis=1).to_numpy()
    add("R8", "within-CV ranks (rank units)", summarise_matrix(
        _nanmean(Yr, -1), cell.codes, cell.groups, cell.occupations, n_perm, rng, alpha, np.nan, H=cell.host()))
    # robustness arms (R4 greedy decoding, others by name)
    for arm, aev in (arm_evs or {}).items():
        if cell.condition != "baseline":
            continue
        g = aev[aev["model_alias"] == cell.model].copy()
        if g.empty:
            continue
        if cell.outcome == "interview":
            g["interview"] = g["interview"] * outcome_scale
        check, label = ARM_CHECK.get(arm, (f"arm:{arm}", f"robustness arm '{arm}'"))
        try:
            gc = build_cell(aggregate_stimulus(g, cell.outcome), cell.model, "baseline", cell.outcome, cell.codes)
        except ValueError:
            continue
        add(check, label, summarise_matrix(gc.Y, gc.codes, gc.groups, gc.occupations, n_perm, rng, alpha, sesoi,
                                           H=gc.host()))
    return pd.DataFrame(rows), pd.DataFrame(prof_rows)


def _cell_rows(cell: Cell, ev: pd.DataFrame, scale: float) -> tuple[pd.DataFrame, pd.Series, pd.Series]:
    g = counterfactual(ev)
    g = g[(g["model_alias"] == cell.model) & (g["prompt_condition"] == cell.condition)
          & g["nationality"].isin(cell.codes)].copy()
    y = g[cell.outcome].astype(float) * (scale if cell.outcome == "interview" else 1.0)
    ok = (g["parse_status"] == "ok") & y.notna()
    return g, y, ok


def _matrix_from(cell: Cell, g: pd.DataFrame, values: pd.Series, keep: pd.Series) -> np.ndarray:
    h = g[keep.to_numpy()].copy()
    h[cell.outcome] = values[keep].to_numpy()
    h["parse_status"] = "ok"
    c = build_cell(aggregate_stimulus(h, cell.outcome), cell.model, cell.condition, cell.outcome, cell.codes)
    if c.cvs == cell.cvs and c.codes == cell.codes:
        return c.Y
    Y = np.full((cell.n_cv, len(cell.codes)), np.nan)
    ri = {v: k for k, v in enumerate(cell.cvs)}
    ci = {v: k for k, v in enumerate(cell.codes)}
    Y[np.ix_([ri[v] for v in c.cvs], [ci[v] for v in c.codes])] = c.Y
    return Y


def _svi_matrices(cell: Cell, ev: pd.DataFrame, scale: float) -> dict[str, np.ndarray]:
    """Every non-ok call imputed as the lowest / highest observed value (interview: no / yes)."""
    g, y, ok = _cell_rows(cell, ev, scale)
    if ok.all() or not ok.any():
        return {}
    lo, hi = (0.0, 100.0) if cell.outcome == "interview" else (float(y[ok].min()), float(y[ok].max()))
    keep = pd.Series(True, index=g.index)
    return {lab: _matrix_from(cell, g, y.where(ok, val), keep)
            for lab, val in (("non-ok = lowest", lo), ("non-ok = highest", hi))}


def _manski_matrices(cell: Cell, ev: pd.DataFrame, scale: float, b: str, support: str) -> dict[str, np.ndarray]:
    """Worst-case bounds for Delta(A_bar, b) (review M2).

    lower: non-ok calls of the 22 Arab origins at the lower support limit L and of b at the
    upper limit U; upper: the reverse. Non-ok calls of other nationalities do not enter this
    contrast. support = "logical" (scale limits 0 / 100) or "observed" (CV-specific observed min / max:
    the range of valid responses of the same base CV across its clones, wordings and replicates).
    """
    g, y, ok = _cell_rows(cell, ev, scale)
    if ok.all() or not ok.any():
        return {}
    if support == "observed":
        # CV-specific observed support: min / max of the valid responses of the same base CV (all its clones,
        # wordings and replicates in this model x condition); CVs without any valid response use the cell range
        yv = y.where(ok)
        L = yv.groupby(g["base_cv_id"]).transform("min").fillna(float(y[ok].min()))
        U = yv.groupby(g["base_cv_id"]).transform("max").fillna(float(y[ok].max()))
    else:
        L = pd.Series(0.0, index=g.index)
        U = pd.Series(100.0, index=g.index)
    arab = g["nationality"].isin(cell.arab_codes)
    isb = g["nationality"] == b
    keep = ok | arab | isb
    out = {}
    for lab, (va, vb) in (("lower bound", (L, U)), ("upper bound", (U, L))):
        vals = y.copy()
        vals[~ok & arab] = va[~ok & arab]
        vals[~ok & isb] = vb[~ok & isb]
        out[lab] = _matrix_from(cell, g, vals, keep)
    return out


def manski_table(rob: pd.DataFrame) -> pd.DataFrame:
    """One row per model x condition x outcome x benchmark x support: bound estimates, outer CI limits,
    width of the identified interval (upper-scenario estimate minus lower-scenario estimate)."""
    m = rob[rob["check"].isin(["R5", "R5-logical", "R5-descriptive"])]
    rows = []
    if m.empty or "bench" not in m:
        return pd.DataFrame()
    for (mod, p, k, b, sup, chk), g in m.groupby(["model", "condition", "outcome", "bench", "support", "check"]):
        lo = g[g["scenario"] == "lower bound"]
        hi = g[g["scenario"] == "upper bound"]
        if lo.empty or hi.empty:
            continue
        e_lo, e_hi = float(lo[f"d_{b}"].iloc[0]), float(hi[f"d_{b}"].iloc[0])
        rows.append(dict(model=mod, condition=p, outcome=k, contrast=f"Delta(A,{b})", support=sup,
                         role="robust label" if chk == "R5" else "descriptive (decision-relevant only if "
                                                                  "differential missingness rejects)",
                         lower_bound_estimate=e_lo, upper_bound_estimate=e_hi, width=e_hi - e_lo,
                         outer_ci_low=float(lo[f"d_{b}_lo"].iloc[0]), outer_ci_high=float(hi[f"d_{b}_hi"].iloc[0])))
    return pd.DataFrame(rows)


def robust_labels(rob: pd.DataFrame, alpha: float = 0.05, diff_missing: dict | None = None,
                  logical_if_differential: bool = True, require_host_exclusion: bool = True) -> pd.DataFrame:
    """'Robust' per hypotheses.md §0: sign holds and CI excludes 0 under R1, R3 (>= 2 of 3
    wordings), R4, R5 and (setting 2026-10-01) HX, the host-national exclusion: both HX rows (22 and
    19 origins, host clones removed, no host adjustment) must pass, as R1 must for the 19 origins.
    For Delta contrasts R5 = both Manski worst-case scenarios with OBSERVED
    support (the lower scenario's CI and the upper scenario's CI both exclude 0 with the main sign);
    if the differential-missingness test rejected for that model x condition (``diff_missing``), the
    logical-support (0-100) bounds must pass as well. For sigma_A no worst-case bound exists; the
    single-value imputation sensitivity (SVI) is used in its place and labelled as such.
    sigma_A 'CI excludes 0' = permutation p < alpha."""
    out = []
    checks = ("R1", "R3", "R4", "R5") + (("HX",) if require_host_exclusion else ())
    diff_missing = diff_missing or {}
    for (m, p, k), g in rob.groupby(["model", "condition", "outcome"]):
        dm = bool(diff_missing.get((m, p), False)) and logical_if_differential
        main = g[g["check"] == "main"].iloc[0]
        for est in ["sigma_A"] + [f"d_{b}" for b in BENCH]:
            if est not in g or not np.isfinite(main.get(est, np.nan)):
                continue

            def passes(r):
                if est == "sigma_A":
                    return bool(r.get("p_perm", 1) < alpha)
                lo, hi = r.get(f"{est}_lo", np.nan), r.get(f"{est}_hi", np.nan)
                same = np.sign(r.get(est, np.nan)) == np.sign(main[est])
                return bool(same and (lo > 0 or hi < 0))

            res = {}
            for chk in checks:
                src = "SVI" if (chk == "R5" and est == "sigma_A") else chk
                srcs = [src] + (["R5-logical"] if (chk == "R5" and est != "sigma_A" and dm) else [])
                sub = g[g["check"].isin(srcs)]
                sub = sub[sub[est].notna()] if est in sub else sub.iloc[0:0]
                if sub.empty:
                    res[chk] = None
                    continue
                flags = [passes(r) for _, r in sub.iterrows()]
                res[chk] = (sum(flags) >= 2) if chk == "R3" else all(flags)
                res[chk + "_detail"] = f"{'+'.join(srcs)}: {sum(flags)}/{len(flags)}"
            main_ok = passes(main)
            missing = [c for c in checks if res.get(c) is None]
            if not main_ok:
                lab = "n/a (no effect in main analysis)"
            elif any(res.get(c) is False for c in checks):
                lab = "not robust"
            elif missing:
                lab = f"robust on available checks; missing {','.join(missing)}"
            else:
                lab = "robust"
            out.append(dict(model=m, condition=p, outcome=k, estimand=est, main_passes=main_ok,
                            **{c: res.get(c) for c in checks},
                            **{c + "_detail": res.get(c + "_detail") for c in checks},
                            r5_basis=("SVI (no worst-case bound exists for sigma_A)" if est == "sigma_A"
                                      else "Manski bounds, observed support"
                                      + (" + logical support (differential missingness rejected)" if dm else "")),
                            robust=lab))
    return pd.DataFrame(out)


__all__ = ["summarise_matrix", "run_robustness", "robust_labels", "manski_table", "stats"]
