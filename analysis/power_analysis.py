"""Simulation-based power analysis for the hiring-audit study (Stage B sizing).

Targets (research/experimental_design.md §7; preregistration.md):
  (1) H1a      power of the within-Arab omnibus test to detect sigma_A = SESOI, at alpha and at the
               Holm worst case alpha / M (M = number of models); size under sigma_A = 0 is reported.
  (2) H1b      power of the noncentral-F equivalence test to conclude sigma_A < SESOI when sigma_A = 0.
               (The pipeline also requires the sphericity-free calibrated bootstrap test; under the
               homoscedastic planning model both agree, so only the noncentral-F test is simulated.)
  (3) min-eff  power of the minimum-effect test (sigma_A > SESOI, needed for the label "meaningful")
               when sigma_A = --sigma-alt-mult x SESOI (default 2).
  (4) TOST     power to establish equivalence of Delta(Arab mean, DEU) within +-SESOI when it is 0
               (fit points; interview percentage points with the schema engine).
  (5) precision mean SE of the per-origin deviations delta_hat(n) vs the target SESOI / 2.5.
If the TOST target (power >= .80) is unreachable at the authoring ceiling (--ceiling CVs per
occupation), the script prints the minimum detectable effects at the ceiling. The SESOI is never
changed to fit the budget (experimental_design.md §7).

Grid: base CVs per occupation x replicates per stimulus (K wording variants fixed).

Engines:
  fast    (default; use for the Stage B decision, n_sims >= 2000) draws wording- and replicate-
          averaged stimulus means from the planning variance model
          Var = s2_at + s2_atk / K + (1 - rho) s2_eps / (K r)  (review M14: plan with rho = 0).
  schema  simulates the processed evaluations table with hiringaudit.analysis.simulate and runs the
          pipeline's own aggregation (slow; for validating the fast engine and for interview TOST).

EVERY DEFAULT VARIANCE COMPONENT BELOW IS A PLACEHOLDER. Replace them with pilot estimates:
pass --pilot-json <out_dir>/variance_components.json from a (blind) pilot run; by default the
"upper" block is used (per component the largest 80% upper limit over models x conditions, from a
CV bootstrap). Never size from mock-provider output (it shares decoder seeds across clones).

Usage:
  PYTHONPATH=src python analysis/power_analysis.py                                  # Stage B default
  PYTHONPATH=src python analysis/power_analysis.py --quick
  PYTHONPATH=src python analysis/power_analysis.py --pilot-json results/pilot/variance_components.json
  PYTHONPATH=src python analysis/power_analysis.py --engine schema --n-sims 40 --cvs 8 --reps 2
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import optimize, stats

ROOT = Path(__file__).resolve().parents[1]
try:
    from hiringaudit.analysis.core import (
        aggregate_stimulus, build_cell, cv_contrast, nationality_order, p_equivalence_sigma,
        p_minimum_effect_sigma, tost, twoway_stats)
    from hiringaudit.analysis.simulate import (
        ARAB_CODES, MAIN_OCCUPATIONS, SimDesign, SimParams, make_nationality_effects, simulate_evaluations)
except ImportError:  # allow running without PYTHONPATH=src
    sys.path.insert(0, str(ROOT / "src"))
    from hiringaudit.analysis.core import (  # noqa: E402
        aggregate_stimulus, build_cell, cv_contrast, nationality_order, p_equivalence_sigma,
        p_minimum_effect_sigma, tost, twoway_stats)
    from hiringaudit.analysis.simulate import (  # noqa: E402
        ARAB_CODES, MAIN_OCCUPATIONS, SimDesign, SimParams, make_nationality_effects, simulate_evaluations)

# --------------------------------------------------------------------------- #
# PLACEHOLDER planning values (points on the 0-100 fit scale). NOT estimates.
# --------------------------------------------------------------------------- #
PLACEHOLDER = {
    "sd_cv": 6.0,        # between base CVs (cancels in within-CV contrasts)
    "sd_ak": 1.0,        # CV x wording
    "sd_at": 2.0,        # CV x nationality  (the term replicates cannot reduce)
    "sd_atk": 1.0,       # CV x nationality x wording
    "sd_eps": 5.0,       # decoder noise between replicates
    "rho_eps": 0.0,      # cross-clone decoder-noise correlation: planned at 0 (review M14)
    "grand_mean": 62.0,
}
WARNING = ("WARNING: variance components are PLACEHOLDER values, not estimates. Replace them with pilot "
           "estimates (--pilot-json) before sizing the study. Simulated power is a planning input, never a finding.")
CODES = ARAB_CODES + ("DEU",)


def confirmatory_sesoi() -> dict:
    """SESOI defaults from config/analysis_settings.csv (fallback: 1.0 points, 5 pp)."""
    try:
        from hiringaudit.analysis.settings import load_confirmatory
        d = load_confirmatory(ROOT / "config" / "analysis_settings.csv")
        return {"overall_fit": float(d["sesoi"]["overall_fit"]), "interview": float(d["sesoi"]["interview"])}
    except Exception:  # noqa: BLE001
        return {"overall_fit": 1.0, "interview": 5.0}


def load_pilot(path: str, use: str) -> tuple[dict, bool]:
    js = json.loads(Path(path).read_text(encoding="utf-8"))
    block = (js.get(use) or {}).get("overall_fit") or js.get("pooled", {}).get("overall_fit")
    if not block:
        raise SystemExit(f"{path}: no '{use}' or 'pooled' block for overall_fit")
    vals = dict(PLACEHOLDER)
    pooled = js.get("pooled", {}).get("overall_fit", {})
    for k in vals:
        v = block.get(k, pooled.get(k))
        if v is not None and np.isfinite(v):
            vals[k] = float(v)
    return vals, bool(js.get("is_mock", False))


def _tier_pattern():
    return ("strong", "adequate", "adequate", "borderline")        # 1 : 2 : 1 (experimental_design.md §7)


def stimulus_var(vc: dict, K: int, r: int) -> float:
    return vc["sd_at"] ** 2 + vc["sd_atk"] ** 2 / K + (1 - vc["rho_eps"]) * vc["sd_eps"] ** 2 / (K * r)


def simulate_matrix_fast(ncv: int, n_occ: int, K: int, r: int, vc: dict, sigma_A: float,
                         rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray]:
    """(I, 23) wording/replicate-averaged stimulus means for 22 Arab origins + DEU."""
    I = ncv * n_occ
    eff = make_nationality_effects(arab_sd=sigma_A, seed=int(rng.integers(1 << 30)))
    tau = np.array([eff[c] for c in CODES])
    row = rng.normal(0, vc["sd_cv"], I)[:, None]
    Y = vc["grand_mean"] + row + tau[None, :] + rng.normal(0, np.sqrt(stimulus_var(vc, K, r)), (I, len(CODES)))
    occ = np.repeat(np.arange(n_occ), ncv).astype(str)
    return Y, occ


def simulate_matrix_schema(ncv: int, occupations, K: int, r: int, vc: dict, sigma_A: float,
                           seed: int) -> tuple[dict, np.ndarray]:
    """Simulate evaluations.csv rows and aggregate them with the pipeline's own functions."""
    design = SimDesign(eval_conditions=("baseline",), occupations=tuple(occupations), cvs_per_occupation=ncv,
                       tier_pattern=_tier_pattern(), nationalities=CODES, variants=tuple(f"k{j + 1}" for j in range(K)),
                       repetitions=r, positive_control=False)
    params = SimParams(fit_intercept=vc["grand_mean"], sd_cv=vc["sd_cv"], sd_cv_variant=vc["sd_ak"],
                       sd_stim=vc["sd_at"], sd_stim_variant=vc["sd_atk"], sd_rep=vc["sd_eps"],
                       rho_eps=vc["rho_eps"], nationality_effects=make_nationality_effects(arab_sd=sigma_A, seed=seed))
    ev = simulate_evaluations(design, params, seed=seed)
    out = {}
    for outcome, scale in (("overall_fit", 1.0), ("interview", 100.0)):
        e = ev.assign(interview=ev["interview"] * scale) if outcome == "interview" else ev
        cell = build_cell(aggregate_stimulus(e, outcome), "sim-model-a", "baseline", outcome, nationality_order(ev))
        out[outcome] = cell.Y[:, [cell.codes.index(c) for c in CODES]]
    return out, cell.occupations


def _stratified_se(D: np.ndarray, occ: np.ndarray) -> np.ndarray:
    """Vectorised occupation-stratified SE of column means of per-CV values D (I, n)."""
    labs = np.unique(occ)
    J = labs.size
    var = np.zeros(D.shape[1])
    for s in labs:
        x = D[occ == s]
        var += x.var(0, ddof=1) / (J * J * x.shape[0])
    return np.sqrt(var)


def evaluate(Y: np.ndarray, occ: np.ndarray, sesoi: float, alpha: float, M: int) -> dict:
    """Tests applied to one simulated data set (fit outcome)."""
    A = Y[:, :22]
    tw = twoway_stats(A)
    J = A.shape[1]
    F, df2, ms = float(tw["F"]), float(tw["df_res"]), float(tw["ms_res"])
    I_eff = 1.0 / float(tw["inv_n"])
    p_h1a = float(stats.f.sf(F, J - 1, df2))
    p_h1b = p_equivalence_sigma(F, J - 1, df2, I_eff, J, ms, sesoi)
    p_min = p_minimum_effect_sigma(F, J - 1, df2, I_eff, J, ms, sesoi)
    d = cv_contrast(Y, np.arange(22), np.array([22]))
    eq = tost(d, sesoi, alpha, occ)
    D = A - A.mean(1, keepdims=True)
    return dict(h1a=p_h1a < alpha, h1a_holm=p_h1a < alpha / M, h1b=p_h1b < alpha, h1b_holm=p_h1b < alpha / M,
                min_eff_holm=p_min < alpha / M, tost=eq.p_tost < alpha, se_contrast=eq.se,
                se_delta=float(np.mean(_stratified_se(D, occ))), sigma_hat=float(tw["sigma_A"]))


def mde_at(total_cvs: int, n_occ: int, K: int, r: int, vc: dict, se_contrast: float, alpha: float, M: int,
           power: float = 0.8) -> dict:
    """Minimum detectable effects for a design (normal / noncentral-F approximations)."""
    z = stats.norm.ppf
    out = dict(mde_tost_margin=(z(1 - alpha) + z(1 - (1 - power) / 2)) * se_contrast,
               mde_delta_two_sided=(z(1 - alpha / 2) + z(power)) * se_contrast)
    J, I = 22, total_cvs
    df1, df2 = J - 1, (I - 1) * (J - 1)
    s2 = stimulus_var(vc, K, r)

    def pw_h1b(S):              # P(reject H1b | sigma_A = 0) at alpha / M
        lam = I * J * S ** 2 / s2
        return stats.f.cdf(stats.ncf.ppf(alpha / M, df1, df2, lam), df1, df2) - power

    try:
        out["mde_sigma_equivalence"] = float(optimize.brentq(pw_h1b, 1e-6, 50.0))
    except ValueError:
        out["mde_sigma_equivalence"] = np.nan
    return out


def run_grid(cvs, reps, K, n_occ, vc, sesoi, sesoi_iv, alpha, M, n_sims, engine, seed, alt_mult) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    occs = MAIN_OCCUPATIONS[:n_occ] if n_occ <= len(MAIN_OCCUPATIONS) else tuple(f"occ{j}" for j in range(n_occ))
    rows = []
    for ncv in cvs:
        for r in reps:
            res = {"null": [], "sesoi": [], "alt": []}
            iv = []
            for scen, sig in (("null", 0.0), ("sesoi", sesoi), ("alt", alt_mult * sesoi)):
                for _ in range(n_sims):
                    if engine == "fast":
                        Y, occ = simulate_matrix_fast(ncv, n_occ, K, r, vc, sig, rng)
                    else:
                        Ys, occ = simulate_matrix_schema(ncv, occs, K, r, vc, sig, int(rng.integers(1 << 30)))
                        Y = Ys["overall_fit"]
                        if scen == "null":
                            d = cv_contrast(Ys["interview"], np.arange(22), np.array([22]))
                            iv.append(tost(d, sesoi_iv, alpha, occ).p_tost < alpha)
                    res[scen].append(evaluate(Y, occ, sesoi, alpha, M))
            n0, n1, n2 = (pd.DataFrame(res[k]) for k in ("null", "sesoi", "alt"))
            rows.append(dict(cvs_per_occupation=ncv, total_cvs=ncv * n_occ, replicates=r, K=K,
                             calls_per_model_condition=ncv * n_occ * 27 * K * r,
                             power_H1a=n1["h1a"].mean(), power_H1a_holm=n1["h1a_holm"].mean(),
                             size_H1a=n0["h1a"].mean(),
                             power_H1b=n0["h1b"].mean(), power_H1b_holm=n0["h1b_holm"].mean(),
                             power_min_effect_holm=n2["min_eff_holm"].mean(),
                             power_TOST_fit=n0["tost"].mean(),
                             power_TOST_interview=float(np.mean(iv)) if iv else np.nan,
                             mean_se_contrast=n0["se_contrast"].mean(), mean_se_delta=n0["se_delta"].mean(),
                             se_target_met=bool(n0["se_delta"].mean() <= sesoi / 2.5), n_sims=n_sims))
            print(f"  cvs/occ={ncv:>3} r={r}: H1a {rows[-1]['power_H1a_holm']:.2f}, H1b {rows[-1]['power_H1b_holm']:.2f}, "
                  f"min-effect {rows[-1]['power_min_effect_holm']:.2f} (alpha/M); TOST {rows[-1]['power_TOST_fit']:.2f}; "
                  f"SE(delta) {rows[-1]['mean_se_delta']:.2f}", flush=True)
    return pd.DataFrame(rows)


def main(argv=None) -> int:
    ses = confirmatory_sesoi()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pilot-json", help="variance_components.json from run_analysis (replaces PLACEHOLDERS)")
    ap.add_argument("--use", choices=["pooled", "upper"], default="upper",
                    help="pilot JSON block: upper = largest 80%% upper limit over models x conditions (default)")
    for k, v in PLACEHOLDER.items():
        ap.add_argument(f"--{k.replace('_', '-')}", type=float, default=None,
                        help=f"override {k} (PLACEHOLDER default {v})")
    ap.add_argument("--cvs", type=int, nargs="+", default=[8, 12, 16], help="base CVs per occupation")
    ap.add_argument("--reps", type=int, nargs="+", default=[1, 2, 3], help="replicates per stimulus")
    ap.add_argument("--K", type=int, default=3, help="wording variants (A3)")
    ap.add_argument("--occupations", type=int, default=6)
    ap.add_argument("--ceiling", type=int, default=16, help="authoring ceiling: base CVs per occupation (OPEN)")
    ap.add_argument("--sesoi", type=float, default=ses["overall_fit"],
                    help="SESOI (fit points) for sigma_A and Delta; default from config/analysis_settings.csv")
    ap.add_argument("--sesoi-interview", type=float, default=ses["interview"], help="SESOI interview (pp)")
    ap.add_argument("--sigma-alt-mult", type=float, default=2.0,
                    help="sigma_A = mult x SESOI for the minimum-effect ('meaningful') power")
    ap.add_argument("--alpha", type=float, default=0.05)
    ap.add_argument("--n-models", type=int, default=3, help="M for the Holm worst case alpha/M")
    ap.add_argument("--n-sims", type=int, default=2000, help="simulations per grid cell and scenario")
    ap.add_argument("--engine", choices=["fast", "schema"], default="fast")
    ap.add_argument("--seed", type=int, default=20261013)
    ap.add_argument("--quick", action="store_true", help="small grid and 200 simulations (smoke run)")
    ap.add_argument("--out", default="analysis/power_results.csv")
    a = ap.parse_args(argv)

    vc, placeholder, mock_src = dict(PLACEHOLDER), True, False
    if a.pilot_json:
        vc, mock_src = load_pilot(a.pilot_json, a.use)
        placeholder = False
    rho_given = a.rho_eps is not None
    for k in PLACEHOLDER:
        v = getattr(a, k)
        if v is not None:
            vc[k] = v
    if not rho_given and vc["rho_eps"] != 0.0:
        print(f"note: planning with rho_eps = 0 (pilot estimate {vc['rho_eps']:.3f} ignored; review M14). "
              "Pass --rho-eps to override.")
        vc["rho_eps"] = 0.0
    if a.quick:
        a.cvs, a.reps, a.n_sims = [8, 16], [1, 3], 200
    if a.engine == "schema" and a.n_sims > 200:
        print("note: the schema engine is slow; reduce --n-sims (e.g. 40) and use it only to validate the fast engine.")
    if placeholder:
        print(WARNING)
    if mock_src:
        print("WARNING: the pilot JSON is marked is_mock=true - these variance components are SYNTHETIC.")
    print(f"engine={a.engine}  K={a.K}  occupations={a.occupations}  SESOI={a.sesoi}  alpha={a.alpha}  "
          f"M={a.n_models}  n_sims={a.n_sims}  ceiling={a.ceiling}/occupation")
    print("variance components:", {k: round(v, 3) for k, v in vc.items()})
    t0 = time.time()
    df = run_grid(a.cvs, a.reps, a.K, a.occupations, vc, a.sesoi, a.sesoi_interview, a.alpha, a.n_models,
                  a.n_sims, a.engine, a.seed, a.sigma_alt_mult)
    mc = 0.5 / np.sqrt(a.n_sims)
    print(f"\nfinished in {time.time() - t0:.0f} s; Monte-Carlo SE of each power value <= {mc:.3f}")
    with pd.option_context("display.width", 220, "display.max_columns", 30):
        print(df.round(3).to_string(index=False))
    ceil = df[df["cvs_per_occupation"] == min(a.ceiling, df["cvs_per_occupation"].max())]
    mde_rows = []
    if (ceil["power_TOST_fit"] < 0.8).all() or (ceil["power_H1b_holm"] < 0.8).all():
        print(f"\nTARGET UNREACHABLE at the authoring ceiling ({int(ceil['cvs_per_occupation'].iloc[0])} CVs/occupation). "
              "Minimum detectable effects (80% power) at the ceiling - report these; do NOT change the SESOI:")
        for _, r in ceil.iterrows():
            md = mde_at(int(r["total_cvs"]), a.occupations, a.K, int(r["replicates"]), vc, r["mean_se_contrast"],
                        a.alpha, a.n_models)
            mde_rows.append(dict(replicates=int(r["replicates"]), **md))
            print(f"  r={int(r['replicates'])}: narrowest equivalence margin for Delta(A,DEU) = {md['mde_tost_margin']:.2f}; "
                  f"smallest detectable Delta = {md['mde_delta_two_sided']:.2f}; narrowest sigma_A equivalence bound "
                  f"(alpha/M) = {md['mde_sigma_equivalence']:.2f}  [SESOI = {a.sesoi}]")
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    header = [f"# {WARNING}"] if placeholder else []
    if mock_src:
        header.append("# SYNTHETIC MOCK DATA - NOT RESULTS (variance components from mock data)")
    with open(out, "w", encoding="utf-8", newline="") as fh:
        for h in header:
            fh.write(h + "\n")
        df.to_csv(fh, index=False)
    meta = dict(inputs=vc, placeholder=placeholder, pilot_json=a.pilot_json, use=a.use, engine=a.engine,
                K=a.K, occupations=a.occupations, ceiling=a.ceiling, sesoi=a.sesoi, sesoi_interview=a.sesoi_interview,
                sigma_alt_mult=a.sigma_alt_mult, alpha=a.alpha, n_models=a.n_models, n_sims=a.n_sims, seed=a.seed,
                mde_at_ceiling=mde_rows)
    out.with_suffix(".json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"wrote {out} and {out.with_suffix('.json')}")
    if placeholder:
        print(WARNING)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
