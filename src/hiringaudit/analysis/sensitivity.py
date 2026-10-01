"""Model-based cross-checks with statsmodels (see analysis/model_specifications.md).

These are secondary to the design-based estimators in ``core.py``:

* MS1  CV fixed-effects OLS on stimulus (variant-level) means with wording-
      variant fixed effects, CV-clustered (CR1) SEs, t(G-1) — reproduces the
      primary Delta(n, DEU) point estimates under a balanced design.
* MS2  Linear mixed model on replicate-level fit scores: nationality, variant,
      tier and occupation fixed effects; base-CV random intercept; stimulus
      (CV x nationality) variance component.
* MS3  GEE logistic model for replicate-level interview recommendations with
      the same fixed effects, clustered on base CV (population-averaged ORs).
Only counterfactual clones enter (A7). Every model includes the host-national indicator
``host_national`` (nationality == the CV's base country; setting 2026-10-01) as a fixed effect when it
varies, so the nationality coefficients are net of a common host bonus; its coefficient is reported
as a row with ``term == "host_national"``.

Each returns (table, status) where ``status`` records the fallback used.
"""

from __future__ import annotations

import re
import warnings

import numpy as np
import pandas as pd
from scipy import stats

# Import statsmodels submodules directly: ``statsmodels.api`` / ``formula.api``
# pull in compiled extensions (statsmodels.robust._qn) that are blocked by an
# application-control policy on at least one team machine. The formulas are
# identical to the ``smf.ols`` / ``smf.mixedlm`` / ``smf.gee`` spellings.
from statsmodels.genmod import cov_struct as sm_cov_struct
from statsmodels.genmod import families as sm_families
from statsmodels.genmod.generalized_estimating_equations import GEE
from statsmodels.regression.linear_model import OLS
from statsmodels.regression.mixed_linear_model import MixedLM

from .schema import REFERENCE

NAT_TERM = f'C(nationality, Treatment(reference="{REFERENCE}"))'
_CODE_RE = re.compile(r"\[T\.([^\]]+)\]")


def _host_term(d: pd.DataFrame) -> str:
    """' + host_national' if the host indicator exists and varies in ``d`` (else '')."""
    if "host_national" not in d.columns:
        return ""
    h = pd.to_numeric(d["host_national"].astype(float), errors="coerce")
    return " + host_national" if h.nunique(dropna=True) > 1 else ""


def _nat_rows(params: pd.Series, bse: pd.Series, df_t: float | None, alpha: float = 0.05,
              exp: bool = False) -> pd.DataFrame:
    rows = []
    for name in params.index:
        if name == "host_national":
            code, term = "host_national", "host_national"
        elif name.startswith("C(nationality"):
            code, term = _CODE_RE.search(name).group(1), "nationality"
        else:
            continue
        est, se = float(params[name]), float(bse[name])
        q = stats.t.ppf(1 - alpha / 2, df_t) if df_t else stats.norm.ppf(1 - alpha / 2)
        z = est / se if se > 0 else np.nan
        p = 2 * (stats.t.sf(abs(z), df_t) if df_t else stats.norm.sf(abs(z)))
        r = dict(term=term, nationality=code, estimate=est, se=se, ci_low=est - q * se, ci_high=est + q * se, p=p)
        if exp:
            r.update(odds_ratio=np.exp(est), or_ci_low=np.exp(est - q * se), or_ci_high=np.exp(est + q * se))
        rows.append(r)
    return pd.DataFrame(rows)


def cv_fe_ols(stim_cell: pd.DataFrame, alpha: float = 0.05) -> tuple[pd.DataFrame, str]:
    """MS1: y_bar ~ nationality + variant + base CV fixed effects, CR1 SEs clustered on base CV."""
    d = stim_cell.dropna(subset=["y"]).copy()
    groups = pd.factorize(d["base_cv_id"])[0]
    G = groups.max() + 1
    var = " + C(prompt_variant)" if d["prompt_variant"].nunique() > 1 else ""
    res = OLS.from_formula(f"y ~ {NAT_TERM}{_host_term(d)}{var} + C(base_cv_id)", data=d).fit(
        cov_type="cluster", cov_kwds={"groups": groups, "use_correction": True})
    return _nat_rows(res.params, res.bse, df_t=G - 1, alpha=alpha), f"ok (G={G} clusters, t(G-1))"


def mixedlm_rep(ev_cell: pd.DataFrame, outcome: str = "overall_fit",
                alpha: float = 0.05) -> tuple[pd.DataFrame, dict]:
    """MS2: replicate-level LMM with base-CV random intercept + stimulus variance component.

    Fallback chain: lbfgs -> powell -> random intercept on stimulus means.
    """
    d = ev_cell[(ev_cell["parse_status"] == "ok") & ev_cell[outcome].notna()
                & (ev_cell["clone_type"] == "counterfactual")].copy()
    d = d.rename(columns={outcome: "y"})
    for c in ("nationality", "base_cv_id", "qualification_tier", "occupation", "prompt_variant"):
        d[c] = d[c].astype(str)
    if "host_national" in d.columns:
        d["host_national"] = d["host_national"].astype(float)
    fixed = f"y ~ {NAT_TERM}{_host_term(d)} + C(prompt_variant) + C(qualification_tier) + C(occupation)"
    if d["prompt_variant"].nunique() < 2:
        fixed = fixed.replace(" + C(prompt_variant)", "")
    if d["occupation"].nunique() < 2:
        fixed = fixed.replace(" + C(occupation)", "")
    if d["qualification_tier"].nunique() < 2:
        fixed = fixed.replace(" + C(qualification_tier)", "")
    status: dict = {}
    for method in ("lbfgs", "powell"):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            try:
                md = MixedLM.from_formula(fixed, d, groups="base_cv_id", re_formula="1",
                                          vc_formula={"stimulus": "0 + C(nationality)"})
                res = md.fit(reml=True, method=method)
            except Exception as e:  # noqa: BLE001 - record and fall back
                status[method] = f"failed: {type(e).__name__}: {e}"
                continue
        conv = bool(getattr(res, "converged", False))
        warn_txt = "; ".join(sorted({str(x.message)[:80] for x in w}))
        status[method] = "converged" if conv else "not converged"
        if warn_txt:
            status[method + "_warnings"] = warn_txt
        if conv:
            vc = dict(var_cv=float(res.cov_re.iloc[0, 0]),
                      var_stimulus=float(res.vcomp[0]) if len(res.vcomp) else np.nan,
                      var_rep=float(res.scale))
            status.update(model="LMM rep-level: (1|cv) + vc(cv:nationality)", **vc)
            return _nat_rows(res.fe_params, res.bse_fe, df_t=None, alpha=alpha), status
    # fallback: random intercept on stimulus means
    gk = ["base_cv_id", "nationality", "prompt_variant", "qualification_tier", "occupation"]
    gk += ["host_national"] if "host_national" in d.columns else []
    sm_ = d.groupby(gk, observed=True)["y"].mean().reset_index()
    try:
        res = MixedLM.from_formula(fixed, sm_, groups="base_cv_id").fit(reml=True)
        status.update(model="FALLBACK LMM on stimulus means: (1|cv)",
                      converged=bool(res.converged))
        return _nat_rows(res.fe_params, res.bse_fe, df_t=None, alpha=alpha), status
    except Exception as e:  # noqa: BLE001
        status.update(model="all mixed models failed; rely on MS1/primary", error=str(e))
        return pd.DataFrame(), status


def gee_interview(ev_cell: pd.DataFrame, alpha: float = 0.05) -> tuple[pd.DataFrame, dict]:
    """MS3: GEE logit, exchangeable working correlation within base CV, robust SEs."""
    d = ev_cell[(ev_cell["parse_status"] == "ok") & ev_cell["interview"].notna()
                & (ev_cell["clone_type"] == "counterfactual")].copy()
    for c in ("nationality", "base_cv_id", "qualification_tier", "occupation", "prompt_variant"):
        d[c] = d[c].astype(str)
    d["interview"] = d["interview"].astype(float)
    if "host_national" in d.columns:
        d["host_national"] = d["host_national"].astype(float)
    fixed = f"interview ~ {NAT_TERM}{_host_term(d)} + C(prompt_variant) + C(qualification_tier) + C(occupation)"
    if d["prompt_variant"].nunique() < 2:
        fixed = fixed.replace(" + C(prompt_variant)", "")
    if d["occupation"].nunique() < 2:
        fixed = fixed.replace(" + C(occupation)", "")
    if d["qualification_tier"].nunique() < 2:
        fixed = fixed.replace(" + C(qualification_tier)", "")
    status: dict = {}
    G = d["base_cv_id"].nunique()
    for name, cs in (("exchangeable", sm_cov_struct.Exchangeable()),
                     ("independence", sm_cov_struct.Independence())):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            try:
                res = GEE.from_formula(fixed, "base_cv_id", d, family=sm_families.Binomial(),
                                       cov_struct=cs).fit()
            except Exception as e:  # noqa: BLE001
                status[name] = f"failed: {type(e).__name__}: {e}"
                continue
        warn_txt = "; ".join(sorted({str(x.message)[:80] for x in w}))
        status.update(model=f"GEE logit, {name} working correlation, robust SE, G={G}",
                      warnings=warn_txt)
        tab = _nat_rows(res.params, res.bse, df_t=None, alpha=alpha, exp=True)
        if (tab["se"] > 10).any():
            status["separation_suspected"] = tab.loc[tab["se"] > 10, "nationality"].tolist()
        return tab, status
    status["model"] = "GEE failed"
    return pd.DataFrame(), status
