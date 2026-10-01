"""Host-national status (setting 2026-10-01): every CV is set in one Arab League base country and the
clone whose nationality equals it is a host national.

Checks: the simulator allocates base countries like the real design; the host fixed effect equals the
least-squares coefficient; delta(n), sigma_A and Delta(A_bar, DEU) are unbiased after adjustment and
biased without it; the adjusted omnibus test stays calibrated under a host effect while the unadjusted
one does not; the host-effect CI covers; forced choice recovers the host covariate; the host-exclusion
check enters the 'robust' label; schema validation of host status.

Set HIRINGAUDIT_SLOW_TESTS=1 for more replications.
"""

from __future__ import annotations

import os

import numpy as np
import pandas as pd
import pytest
from scipy import stats

from hiringaudit.analysis.bradley_terry import arab_centred, bt_analysis, fit_bt, prepare_fc
from hiringaudit.analysis.core import (
    aggregate_stimulus,
    build_cell,
    contrast_values,
    global_test_F,
    global_test_perm,
    heterogeneity,
    host_fit,
    nationality_order,
    origin_deviations,
    permute_within_rows,
    t_summary,
    twoway_stats,
)
from hiringaudit.analysis.robustness import robust_labels, run_robustness
from hiringaudit.analysis.schema import SchemaError, validate_evaluations, validate_forced_choice
from hiringaudit.analysis.simulate import (
    ARAB_CODES,
    BASE_COUNTRIES,
    FC_CODES,
    MAIN_OCCUPATIONS,
    MAIN_TIERS,
    SimDesign,
    SimParams,
    make_nationality_effects,
    simulate_all,
    simulate_evaluations,
    simulate_forced_choice,
)

SLOW = os.environ.get("HIRINGAUDIT_SLOW_TESTS") == "1"
ETA = 8.0
MAIN = SimDesign(eval_conditions=("baseline",), occupations=MAIN_OCCUPATIONS, cvs_per_occupation=8,
                 tier_pattern=MAIN_TIERS, repetitions=1, positive_control=False)
PILOT = SimDesign(eval_conditions=("baseline",), repetitions=2, positive_control=False)


def _cell(ev, outcome="overall_fit"):
    return build_cell(aggregate_stimulus(ev, outcome), "sim-model-a", "baseline", outcome, nationality_order(ev))


# ------------------------------------------------------------------ design
def test_simulator_allocates_base_countries_like_the_real_design():
    ev = simulate_evaluations(MAIN, SimParams(), seed=1)
    cv = ev.drop_duplicates("base_cv_id")
    counts = cv["base_country"].value_counts()
    assert set(counts.index) == set(BASE_COUNTRIES) and (counts == 6).all()       # 3 pairs per country
    assert (cv.groupby("base_country")["occupation"].nunique() == 3).all()          # in different occupations
    assert (cv.groupby(["occupation", "qualification_tier", "base_country"]).size() % 2 == 0).all()   # pairs
    cf = ev[ev["clone_type"] == "counterfactual"]
    per_cv = cf[cf["prompt_variant"] == "k1"].groupby("base_cv_id")["host_national"].sum()
    assert (per_cv == 1).all()                                                      # 1 host clone per CV
    assert not cf.loc[cf["nationality_group"] != "arab", "host_national"].any()      # never a benchmark / NONE
    fc = simulate_all(SimDesign(cvs_per_occupation=6), SimParams(), seed=2, principle=False)["forced_choice"]
    assert (fc.groupby("quad_id")["base_country"].nunique() == 1).all()             # FC pairs share a country
    assert (fc["host_national_a"] == (fc["nationality_a"] == fc["base_country"])).all()


# ------------------------------------------------------------------ estimator
def _design_matrix(I=48, J=22, seed=0):
    rng = np.random.default_rng(seed)
    bc = np.repeat(np.arange(8), I // 8)
    rng.shuffle(bc)
    H = np.zeros((I, J))
    H[np.arange(I), bc] = 1.0
    return H, rng


def test_host_fit_equals_least_squares_with_missing_cells():
    H, rng = _design_matrix()
    I, J = H.shape
    Y = 60 + rng.normal(0, 5, (I, 1)) + rng.normal(0, 1.5, J)[None] + 4.0 * H + rng.normal(0, 2, (I, J))
    Y[3, 5] = Y[7, np.flatnonzero(H[7])[0]] = np.nan
    Y[10, :5] = np.nan
    r, c = np.meshgrid(np.arange(I), np.arange(J), indexing="ij")
    X = np.column_stack([np.eye(I)[r.ravel()], np.eye(J)[c.ravel()][:, 1:], H.ravel()])
    ok = ~np.isnan(Y.ravel())
    b = np.linalg.lstsq(X[ok], Y.ravel()[ok], rcond=None)[0]
    hf = host_fit(Y, H, np.repeat(np.arange(6), 8))
    assert hf.identified and abs(hf.eta - b[-1]) < 1e-8
    assert abs(float(twoway_stats(Y, H)["eta"]) - b[-1]) < 1e-8
    assert hf.ci_low < hf.eta < hf.ci_high and 0.1 < hf.se < 1.0
    assert not host_fit(Y, np.zeros_like(H)).identified                          # no host cells: not identified


def test_adjustment_is_exact_without_noise_and_unadjusted_bias_is_eta_times_imbalance():
    """Noise-free additive data: the adjusted delta(n) and Delta(A, b) are exact; the unadjusted ones are off by
    eta * (p_n - 1/J) and eta / J (p_n = share of CVs whose base country is n)."""
    H, rng = _design_matrix()
    I, J = H.shape
    tau = rng.normal(0, 2, J)
    Hfull = np.column_stack([H, np.zeros((I, 1))])                              # + one benchmark column (never host)
    tau_b = -1.0
    Y = 60 + rng.normal(0, 5, (I, 1)) + np.append(tau, tau_b)[None] + ETA * Hfull
    occ = np.repeat(np.arange(6), 8)
    a, b = np.arange(J), np.array([J])
    od = origin_deviations(Y[:, a], [str(j) for j in a], occ, 19, rng, H=H)
    od0 = origin_deviations(Y[:, a], [str(j) for j in a], occ, 19, rng)
    true = tau - tau.mean()
    p = H.mean(0)
    assert np.allclose(od["delta"], true, atol=1e-8)
    assert np.allclose(od0["delta"], true + ETA * (p - 1 / J), atol=1e-8)
    d_adj = t_summary(contrast_values(Y, a, b, Hfull, host_fit(Y, Hfull, occ), occ), strata=occ).estimate
    d_raw = t_summary(contrast_values(Y, a, b), strata=occ).estimate
    assert abs(d_adj - (tau.mean() - tau_b)) < 1e-8 and abs(d_raw - (tau.mean() - tau_b) - ETA / J) < 1e-8
    s_adj, s_raw = twoway_stats(Y[:, a], H), twoway_stats(Y[:, a])
    assert abs(float(s_adj["sd_plugin"]) - np.sqrt(np.mean(true ** 2))) < 1e-8
    assert float(s_raw["sd_plugin"]) > float(s_adj["sd_plugin"])


@pytest.fixture(scope="module")
def host_runs():
    """Main-size design, sigma_A = 2, host effect ETA: adjusted vs unadjusted estimates over replications."""
    eff = make_nationality_effects(arab_mean=-1.0, arab_sd=2.0, seed=3)
    params = SimParams(nationality_effects=eff, host_national_effect=ETA, sd_stim=1.5, sd_rep=3.0)
    out = []
    for s in range(4 if not SLOW else 12):
        cell = _cell(simulate_evaluations(MAIN, params, seed=300 + s))
        a = cell.cols(cell.arab_codes)
        Ha, Hc = cell.host(a), cell.host()
        rng = np.random.default_rng(s)
        od = origin_deviations(cell.Y[:, a], cell.arab_codes, cell.occupations, 9, rng, H=Ha)
        od0 = origin_deviations(cell.Y[:, a], cell.arab_codes, cell.occupations, 9, rng)
        hf = host_fit(cell.Y, Hc, cell.occupations)
        deu = cell.cols(["DEU"])
        d = t_summary(contrast_values(cell.Y, a, deu, Hc, hf, cell.occupations), strata=cell.occupations)
        d0 = t_summary(contrast_values(cell.Y, a, deu), strata=cell.occupations)
        out.append(dict(codes=cell.arab_codes, base=set(cell.base_countries), delta=od["delta"].to_numpy(),
                        delta0=od0["delta"].to_numpy(), eta=hf.eta, eta_lo=hf.ci_low, eta_hi=hf.ci_high,
                        d=d.estimate, d0=d0.estimate,
                        s_adj=float(twoway_stats(cell.Y[:, a], Ha)["sigma_A"]),
                        s_raw=float(twoway_stats(cell.Y[:, a])["sigma_A"])))
    return eff, out


def test_delta_unbiased_after_adjustment_and_biased_without(host_runs):
    eff, runs = host_runs
    codes = runs[0]["codes"]
    true = np.array([eff[c] for c in codes])
    true -= true.mean()
    is_host = np.array([c in runs[0]["base"] for c in codes])
    err = np.array([r["delta"] - true for r in runs])
    err0 = np.array([r["delta0"] - true for r in runs])
    # expected bias without adjustment: +eta * (6/48 - 1/22) for the 8 base countries, -eta/22 for the others
    b_host, b_other = ETA * (6 / 48 - 1 / 22), -ETA / 22
    assert abs(err[:, is_host].mean()) < 0.25 and abs(err[:, ~is_host].mean()) < 0.15
    assert abs(err0[:, is_host].mean() - b_host) < 0.25 and abs(err0[:, ~is_host].mean() - b_other) < 0.15
    assert err0[:, is_host].mean() - err[:, is_host].mean() > 0.4                # the difference adjustment makes
    eta_hat = np.array([r["eta"] for r in runs])
    assert abs(eta_hat.mean() - ETA) < 0.4
    true_d = np.mean([eff[c] for c in ARAB_CODES]) - eff["DEU"]
    d = np.array([r["d"] for r in runs])
    d0 = np.array([r["d0"] for r in runs])
    assert abs(d.mean() - true_d) < 0.3 and abs((d0 - d).mean() - ETA / 22) < 0.05
    assert np.mean([r["s_raw"] > r["s_adj"] for r in runs]) >= 0.75               # host effect inflates sigma_A


def test_host_effect_ci_coverage():
    params = SimParams(host_national_effect=3.0, nationality_effects=make_nationality_effects(arab_sd=1.5, seed=1))
    n = 40 if not SLOW else 120
    cover = []
    for s in range(n):
        cell = _cell(simulate_evaluations(PILOT, params, seed=700 + s))
        hf = host_fit(cell.Y, cell.host(), cell.occupations)
        cover.append(hf.ci_low <= 3.0 <= hf.ci_high)
    assert np.mean(cover) >= 0.85


def test_restricted_permutation_keeps_host_cells():
    rng = np.random.default_rng(0)
    H = np.zeros((12, 6))
    H[np.arange(12), np.arange(12) % 4] = 1.0
    Y = rng.normal(size=H.shape)
    P = permute_within_rows(Y, 50, rng, H > 0)
    assert np.allclose(P[:, H > 0], Y[H > 0])
    assert np.allclose(np.sort(P, -1), np.sort(Y, -1)[None])
    free = ~(H > 0)
    assert not np.allclose(P[:, free], Y[free][None])                           # the other cells do move


# ------------------------------------------------------------------ null calibration under a host effect
@pytest.fixture(scope="module")
def null_host_runs():
    """No Arab nationality effects, host effect ETA: H1a with and without host adjustment."""
    params = SimParams(nationality_effects=make_nationality_effects(arab_mean=-2, arab_sd=0), rho_eps=0.3,
                       host_national_effect=ETA)
    rng = np.random.default_rng(99)
    out = []
    for s in range(150 if not SLOW else 400):
        cell = _cell(simulate_evaluations(PILOT, params, seed=s))
        a = cell.cols(cell.arab_codes)
        Y, H = cell.Y[:, a], cell.host(a)
        _, p_adj = global_test_perm(Y, 199, rng, H=H)
        _, p_raw = global_test_perm(Y, 199, rng)
        out.append((p_adj, p_raw, float(twoway_stats(Y, H)["sigma2_deb"]), global_test_F(Y, H)[1]))
    return np.array(out)


def test_adjusted_global_test_calibrated_under_host_effect(null_host_runs):
    n = len(null_host_runs)
    k = int(np.sum(null_host_runs[:, 0] < 0.05))
    lo, hi = stats.binom.ppf([0.0005, 0.9995], n, 0.05)
    assert lo <= k <= hi, f"adjusted FPR {k}/{n}"
    assert stats.kstest(null_host_runs[:, 0], "uniform").pvalue > 0.001
    s2 = null_host_runs[:, 2]
    assert abs(s2.mean()) < 3.5 * s2.std(ddof=1) / np.sqrt(n)                     # debiased sigma^2 ~ 0
    kf = int(np.sum(null_host_runs[:, 3] < 0.05))
    assert lo <= kf <= hi, f"adjusted parametric F FPR {kf}/{n}"


def test_equivalence_test_calibrated_at_sesoi_under_host_effect():
    """H1b (noncentral F, host-adjusted): sigma_A = SESOI and a large host effect -> 'equivalence' <= ~5%."""
    params = SimParams(nationality_effects=make_nationality_effects(arab_sd=1.0, seed=5), host_national_effect=ETA)
    rng = np.random.default_rng(3)
    n = 120 if not SLOW else 300
    hits = cover = 0
    for s in range(n):
        cell = _cell(simulate_evaluations(PILOT, params, seed=5000 + s))
        a = cell.cols(cell.arab_codes)
        h = heterogeneity(cell.Y[:, a], cell.arab_codes, cell.occupations, 19, 1, rng, sesoi=1.0,
                          boot_idx=np.zeros((1, cell.n_cv), int), H=cell.host(a))
        hits += h.p_equivalence < 0.05
        cover += h.ncf_ci_low <= 1.0 <= h.ncf_ci_high
    assert hits <= stats.binom.ppf(0.999, n, 0.05), f"false equivalence {hits}/{n}"
    assert cover / n >= 0.88


def test_unadjusted_global_test_is_not_calibrated_under_host_effect(null_host_runs):
    n = len(null_host_runs)
    k = int(np.sum(null_host_runs[:, 1] < 0.05))
    assert k > stats.binom.ppf(0.999, n, 0.05), f"unadjusted FPR only {k}/{n}"     # observed about 17%


# ------------------------------------------------------------------ heterogeneity object and HX robustness
def test_heterogeneity_reports_host_adjustment_and_hx_rows():
    params = SimParams(nationality_effects=make_nationality_effects(arab_sd=2.0, seed=4), host_national_effect=5.0)
    ev = simulate_evaluations(SimDesign(eval_conditions=("baseline",), repetitions=1, variants=("k1", "k2")),
                              params, seed=5)
    cell = _cell(ev)
    a = cell.cols(cell.arab_codes)
    h = heterogeneity(cell.Y[:, a], cell.arab_codes, cell.occupations, 99, 49, np.random.default_rng(0), sesoi=1.0,
                      H=cell.host(a))
    assert h.host_adjusted and abs(h.host_effect - 5.0) < 2.0
    rob, _ = run_robustness(cell, ev, 100.0, 49, np.random.default_rng(1), 0.05, 1.0)
    hx = rob[rob["check"] == "HX"]
    assert len(hx) == 2 and set(hx["host_handling"]) == {"excluded"}
    assert set(rob.loc[rob["check"] == "main", "host_handling"]) == {"adjusted"}
    lab = robust_labels(rob, 0.05)
    assert "HX" in lab.columns and "HX_detail" in lab.columns


def test_robust_label_requires_host_exclusion():
    base = dict(model="m", condition="baseline", outcome="overall_fit")
    ok = dict(sigma_A=2.0, p_perm=0.001, d_DEU=-2.0, d_DEU_lo=-3.0, d_DEU_hi=-1.0)
    rows = [dict(base, check="main", subset="all", **ok), dict(base, check="R1", subset="19", **ok),
            dict(base, check="R4", subset="greedy", **ok), dict(base, check="SVI", subset="lo", **ok),
            dict(base, check="R5", subset="lower", d_DEU=-2.0, d_DEU_lo=-3.0, d_DEU_hi=-1.0),
            dict(base, check="R5", subset="upper", d_DEU=-1.5, d_DEU_lo=-2.5, d_DEU_hi=-0.5)]
    rows += [dict(base, check="R3", subset=f"wording k{j}", **ok) for j in (1, 2, 3)]
    hx_pass = [dict(base, check="HX", subset="22", **ok), dict(base, check="HX", subset="19", **ok)]
    hx_fail = [dict(base, check="HX", subset="22", **ok),
               dict(base, check="HX", subset="19", sigma_A=0.5, p_perm=0.4, d_DEU=-0.5, d_DEU_lo=-1.5, d_DEU_hi=0.5)]
    lab_ok = robust_labels(pd.DataFrame(rows + hx_pass)).set_index("estimand")
    lab_bad = robust_labels(pd.DataFrame(rows + hx_fail)).set_index("estimand")
    lab_none = robust_labels(pd.DataFrame(rows)).set_index("estimand")
    assert lab_ok.loc["sigma_A", "robust"] == "robust" and lab_ok.loc["d_DEU", "robust"] == "robust"
    assert lab_bad.loc["sigma_A", "robust"] == "not robust" and lab_bad.loc["d_DEU", "robust"] == "not robust"
    assert "missing HX" in lab_none.loc["sigma_A", "robust"]
    assert robust_labels(pd.DataFrame(rows), require_host_exclusion=False).set_index("estimand").loc[
        "sigma_A", "robust"] == "robust"


# ------------------------------------------------------------------ forced choice
def test_bradley_terry_host_covariate():
    rng0 = np.random.default_rng(5)
    theta = {c: float(rng0.normal(0, 0.5)) for c in FC_CODES}
    theta["DEU"] = 0.0
    design = SimDesign(occupations=MAIN_OCCUPATIONS, cvs_per_occupation=8, tier_pattern=MAIN_TIERS,
                       fc_pair_offsets=(1, 2, 3, 4, 5, 6), fc_cv_pairs_per_nat_pair=3, fc_repetitions=2)
    fc = simulate_forced_choice(design, SimParams(fc_theta=theta, fc_host_effect=1.0, fc_position_bias=0.3), seed=6)
    data = prepare_fc(fc, codes=list(FC_CODES))
    assert data.hd is not None and np.any(data.hd != 0)
    f = fit_bt(data)
    f0 = fit_bt(data, host=False)
    assert f.converged and abs(f.host_effect - 1.0) < 0.35 and np.isnan(f0.host_effect)
    a = np.array([data.codes.index(c) for c in ARAB_CODES])
    true = arab_centred(np.array([theta[c] for c in data.codes]), a)
    hosts = np.array([c in BASE_COUNTRIES for c in data.codes])
    err = arab_centred(f.theta_ref, a) - true
    err0 = arab_centred(f0.theta_ref, a) - true
    assert err0[hosts].mean() > err[hosts].mean() + 0.03             # without the host term base countries gain
    res = bt_analysis(data, list(ARAB_CODES), n_boot=20, n_perm=0, rng=np.random.default_rng(0))
    assert res.host_ci[0] <= res.host_effect <= res.host_ci[1]


# ------------------------------------------------------------------ schema
@pytest.fixture(scope="module")
def tables():
    d = SimDesign(cvs_per_occupation=2, tier_pattern=("adequate",), repetitions=1, variants=("k1",),
                  fc_pair_offsets=(1,), principle_repetitions=1)
    return simulate_all(d, SimParams(), seed=3, principle=False)


def _problems(fn, df):
    with pytest.raises(SchemaError) as ei:
        fn(df)
    return " | ".join(ei.value.problems)


def test_schema_host_status_must_match_base_country(tables):
    ev = tables["evaluations"].copy()
    i = ev.index[ev["host_national"]][0]
    ev.loc[i, "host_national"] = False
    assert "'host_national' != (nationality == base_country)" in _problems(validate_evaluations, ev)
    ev = tables["evaluations"].copy()
    ev.loc[ev.index[0], "base_country"] = "XXX"
    assert "inconsistent 'base_country'" in _problems(validate_evaluations, ev)
    ev = tables["evaluations"].copy()
    ev["base_country"] = "DEU"
    ev["host_national"] = ev["nationality"] == "DEU"
    assert "not Arab League" in _problems(validate_evaluations, ev)
    assert "missing required column" in _problems(validate_evaluations, tables["evaluations"].drop(
        columns=["host_national"]))


def test_schema_forced_choice_host_status(tables):
    fc = tables["forced_choice"].copy()
    fc["host_national_a"] = ~fc["host_national_a"]
    assert "'host_national_a' != (nationality_a == base_country)" in _problems(validate_forced_choice, fc)
    fc = tables["forced_choice"].copy()
    q = fc["quad_id"].iloc[0]
    j = fc.index[fc["quad_id"] == q][0]
    fc.loc[j, "base_country"] = "ZZZ" if fc.loc[j, "base_country"] != "ZZZ" else "YYY"
    fc.loc[j, ["host_national_a", "host_national_b"]] = False
    assert "more than one base_country" in _problems(validate_forced_choice, fc)


def test_load_processed_cross_checks_fc_base_country(tables, tmp_path):
    from hiringaudit.analysis.schema import load_processed
    from hiringaudit.analysis.simulate import write_processed
    t = dict(tables)
    fc = t["forced_choice"].copy()
    fc["base_country"] = "EGY" if (fc["base_country"] != "EGY").all() else "JOR"
    fc["host_national_a"] = fc["nationality_a"] == fc["base_country"]
    fc["host_national_b"] = fc["nationality_b"] == fc["base_country"]
    t["forced_choice"] = fc
    write_processed(t, tmp_path)
    with pytest.raises(SchemaError, match="base_country differs"):
        load_processed(tmp_path)
