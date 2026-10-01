"""Adversarial-review fixes: M1 (one-sided manipulation check), M2 (Manski bounds), M3 (sphericity-free
equivalence), M4 (RQ1 labels), M15 (wording imputation), H1d multi-covariate, H5 (placebo comparison), L6."""

from __future__ import annotations

import os

import numpy as np
import pytest
from scipy import stats

from hiringaudit.analysis.core import (
    aggregate_stimulus,
    build_cell,
    compare_sigma,
    cv_contrast,
    impute_wordings,
    nationality_order,
    sigma_within_groups,
    sphericity_free_equivalence,
    t_summary,
)
from hiringaudit.analysis.descriptives import positive_control, scale_use
from hiringaudit.analysis.hypotheses import (H1E_ABOVE, H1E_BELOW, H1E_NONE, RQ1_MEANINGFUL, RQ1_NULL,
                                             RQ1_NULL_NO_PC, RQ1_PRESENT, RQ1_TRIVIAL, h1d_gradient, h1e_label,
                                             rq1_headline, rq1_label)
from hiringaudit.analysis.robustness import _manski_matrices, _svi_matrices, manski_table, robust_labels, run_robustness
from hiringaudit.analysis.simulate import (ARAB_CODES, SimDesign, SimParams, make_nationality_effects,
                                           simulate_evaluations)

SLOW = os.environ.get("HIRINGAUDIT_SLOW_TESTS") == "1"
SMALL = SimDesign(eval_conditions=("baseline",), cvs_per_occupation=6, repetitions=2, variants=("k1", "k2"))


def _cell(ev, outcome="overall_fit"):
    e = ev.assign(interview=ev["interview"] * 100.0) if outcome == "interview" else ev
    return build_cell(aggregate_stimulus(e, outcome), "sim-model-a", "baseline", outcome, nationality_order(ev))


# ---------------------------------------------------------------- M1
def test_manipulation_check_is_one_sided():
    ok = positive_control(simulate_evaluations(SMALL, SimParams(positive_control_effect=-10), seed=1))
    bad = positive_control(simulate_evaluations(SMALL, SimParams(positive_control_effect=+10), seed=1))
    assert ok.set_index("outcome").loc["overall_fit", "manipulation_check_passed"]
    assert not bad.set_index("outcome").loc["overall_fit", "manipulation_check_passed"]   # wrong sign fails


# ---------------------------------------------------------------- M2
def test_manski_bounds_bracket_estimate_and_are_wider_than_svi():
    eff = make_nationality_effects(arab_mean=-2, seed=1)
    ev = simulate_evaluations(SMALL, SimParams(nationality_effects=eff, p_refusal=0.08), seed=2)
    cell = _cell(ev)
    a, ref = cell.cols(cell.arab_codes), cell.cols(["DEU"])
    est = t_summary(cv_contrast(cell.Y, a, ref), strata=cell.occupations).estimate
    mk = _manski_matrices(cell, ev, 100.0, "DEU", "logical")
    lo = t_summary(cv_contrast(mk["lower bound"], a, ref), strata=cell.occupations).estimate
    hi = t_summary(cv_contrast(mk["upper bound"], a, ref), strata=cell.occupations).estimate
    assert lo < est < hi
    sv = [t_summary(cv_contrast(Y, a, ref), strata=cell.occupations).estimate
          for Y in _svi_matrices(cell, ev, 100.0).values()]
    assert lo <= min(sv) and max(sv) <= hi
    obs = _manski_matrices(cell, ev, 100.0, "DEU", "observed")
    lo_o = t_summary(cv_contrast(obs["lower bound"], a, ref), strata=cell.occupations).estimate
    assert lo <= lo_o <= est


# ---------------------------------------------------------------- M3
def _matrix(I, sigma, sds, rng):
    J = len(sds)
    z = stats.norm.ppf((np.arange(1, J + 1) - 0.5) / J)
    pat = (z - z.mean()) / z.std() * sigma
    return 60 + rng.normal(0, 5, (I, 1)) + pat[None, rng.permutation(J)] + rng.normal(0, 1, (I, J)) * sds[None, :]


def test_sphericity_free_equivalence_calibrated_under_heteroscedasticity():
    rng = np.random.default_rng(11)
    sds = np.linspace(1, 6, 22)
    sds = sds / np.sqrt(np.mean(sds ** 2)) * 2.0
    occ = np.repeat(["a", "b", "c"], 6)
    n = 150 if SLOW else 50
    hits = sum(sphericity_free_equivalence(_matrix(18, 1.0, sds, rng), occ, 1.0, 99, 99, 49, rng)["sf_equivalent"]
               for _ in range(n))
    assert hits <= stats.binom.ppf(0.999, n, 0.05), f"false equivalence {hits}/{n}"


def test_sphericity_free_equivalence_has_power_when_sigma_zero():
    rng = np.random.default_rng(12)
    occ = np.repeat(["a", "b", "c", "d", "e", "f"], 8)
    hits = [sphericity_free_equivalence(_matrix(48, 0.0, np.full(22, 1.0), rng), occ, 1.0, 99, 99, 49, rng)
            for _ in range(15)]
    assert np.mean([h["sf_equivalent"] for h in hits]) >= 0.8
    assert all(h["sf_upper95"] < 1.0 for h in hits if h["sf_equivalent"])


# ---------------------------------------------------------------- M4
def test_rq1_labels():
    a = 0.05
    assert rq1_label(0.001, 0.9, 0.01, False, True, a) == RQ1_MEANINGFUL
    assert rq1_label(0.001, 0.9, 0.40, False, True, a) == RQ1_PRESENT      # H1a rejects, H1b not: undetermined
    assert rq1_label(0.001, 0.01, 0.99, True, True, a) == RQ1_TRIVIAL
    assert rq1_label(0.001, 0.01, 0.99, False, True, a) == RQ1_PRESENT     # equivalence needs both tests
    assert rq1_label(0.40, 0.01, 0.99, True, True, a) == RQ1_NULL
    assert rq1_label(0.40, 0.01, 0.99, True, False, a) == RQ1_NULL_NO_PC
    assert rq1_label(0.40, 0.30, 0.99, True, True, a) == "inconclusive"
    assert rq1_headline(RQ1_MEANINGFUL, RQ1_MEANINGFUL) == RQ1_MEANINGFUL
    assert rq1_headline(RQ1_MEANINGFUL, RQ1_PRESENT) == RQ1_PRESENT
    assert rq1_headline(RQ1_MEANINGFUL, "inconclusive").startswith("inconclusive")
    assert rq1_headline(RQ1_NULL, "inconclusive").startswith("inconclusive")


# ---------------------------------------------------------------- M15
def test_impute_wordings_additive():
    rng = np.random.default_rng(0)
    Yk = (50 + rng.normal(0, 5, (10, 1, 1)) + np.arange(5)[None, :, None] + np.array([-6.0, 0.0, 6.0])[None, None, :])
    Ym = Yk.copy()
    Ym[0, 2, 2] = np.nan
    Ym[4, 1, 0] = np.nan
    Ym[6, 3, :] = np.nan
    f, n = impute_wordings(Ym)
    assert n == 2 and np.nanmax(np.abs(f - Yk)) < 1e-6 and np.isnan(f[6, 3]).all()


def test_missing_wording_does_not_leak_into_contrasts():
    design = SimDesign(eval_conditions=("baseline",), cvs_per_occupation=6, repetitions=1, positive_control=False)
    ev = simulate_evaluations(design, SimParams(variant_effects={"k1": -8, "k2": 0, "k3": 8}, sd_rep=0.5,
                                                sd_stim=0.2, sd_stim_variant=0.2), seed=3)
    drop = (ev["nationality"] == "SYR") & (ev["prompt_variant"] == "k3")
    ev.loc[drop, "parse_status"] = "refusal"
    ev.loc[drop, ["overall_fit", "interview"]] = np.nan
    cell = _cell(ev)
    d = t_summary(cv_contrast(cell.Y, cell.cols(["SYR"]), cell.cols(["DEU"])), strata=cell.occupations)
    naive = np.nanmean(np.nanmean(cell.Yk[:, cell.cols(["SYR"])[0]], -1) - cell.Y[:, cell.cols(["DEU"])[0]])
    assert abs(d.estimate) < 0.6 and naive < -3        # without imputation the wording effect leaks (about -4)


# ---------------------------------------------------------------- H1d
def test_h1d_recovers_planted_gradient_and_adjusts():
    import pandas as pd
    cov = pd.read_csv("config/country_covariates.csv").set_index("code")
    gdp = cov["gdp_pc_ppp_const"].to_dict()
    ssa = cov["wb_sub_saharan"].to_dict()
    eff = {c: 0.0 for c in ARAB_CODES}
    for c in ARAB_CODES:
        if np.isfinite(gdp.get(c, np.nan)):
            eff[c] = 1.5 * (np.log(gdp[c]) - 9.5)
    design = SimDesign(eval_conditions=("baseline",), cvs_per_occupation=8, repetitions=1, positive_control=False)
    ev = simulate_evaluations(design, SimParams(nationality_effects=eff, sd_stim=1.0), seed=4)
    cell = _cell(ev)
    a = cell.cols(cell.arab_codes)
    r = h1d_gradient(cell.Y[:, a], cell.arab_codes, cell.occupations, {"gdp": gdp}, 1.0, 0.05, {"gdp": "log"})
    assert r["status"] == "ok" and r["k"] == 21 and r["ci_low"] <= 1.5 <= r["ci_high"] and r["p"] < 0.01
    r2 = h1d_gradient(cell.Y[:, a], cell.arab_codes, cell.occupations, {"gdp": gdp, "ssa": ssa}, 1.0, 0.05,
                      {"gdp": "log"})
    assert r2["status"] == "ok" and r2["df"] == 21 - 1 - 2 and r2["beta_W"] > 0


# ---------------------------------------------------------------- H5
def test_compare_sigma_calibrated_when_spreads_equal():
    rng = np.random.default_rng(21)
    occ = np.repeat(["a", "b", "c"], 6)
    n = 200 if SLOW else 80
    rej = 0
    for _ in range(n):
        Ya = _matrix(18, 1.0, np.full(22, 2.5), rng)
        Yb = _matrix(18, 1.0, np.full(8, 2.5), rng)
        rej += compare_sigma(Ya, Yb, occ, 199, rng)["p_difference"] < 0.05
    assert rej <= stats.binom.ppf(0.999, n, 0.05)


def test_compare_sigma_detects_larger_arab_spread():
    rng = np.random.default_rng(22)
    occ = np.repeat(["a", "b", "c", "d", "e", "f"], 8)
    r = compare_sigma(_matrix(48, 2.0, np.full(22, 2.0), rng), _matrix(48, 0.0, np.full(8, 2.0), rng), occ, 299, rng)
    assert r["p_difference"] < 0.01 and r["diff_ci_low"] > 0


def test_sigma_net_of_groups():
    rng = np.random.default_rng(23)
    groups = ["g1"] * 11 + ["g2"] * 11
    shift = np.array([2.0] * 11 + [-2.0] * 11)
    Y = 60 + rng.normal(0, 5, (30, 1)) + shift[None, :] + rng.normal(0, 1.0, (30, 22))
    r = sigma_within_groups(Y, groups, 199, rng)
    assert r["sigma_net"] < 0.4 and r["between_group_share"] > 0.9 and r["p_perm_within"] > 0.01


# ---------------------------------------------------------------- L6
def test_scale_use_is_per_tier():
    su = scale_use(simulate_evaluations(SMALL, SimParams(), seed=5))
    assert {"strong", "adequate", "borderline"} == set(su["tier"])
    assert su.loc[su["tier"] == "strong", "p3_applies"].eq(False).all()


# ---------------------------------------------------------------- round 2: N3 and H1e
def test_robust_label_uses_observed_support_and_logical_only_under_differential_missingness():
    eff = make_nationality_effects(arab_mean=-4, seed=1)
    ev = simulate_evaluations(SMALL, SimParams(nationality_effects=eff, p_refusal=0.04, sd_rep=2.0), seed=7)
    cell = _cell(ev)
    rob, _ = run_robustness(cell, ev, 100.0, 49, np.random.default_rng(0), 0.05, 1.0, None,
                            support="observed", support_descriptive="logical")
    mt = manski_table(rob)
    deu = mt[mt["contrast"] == "Delta(A,DEU)"].set_index("support")
    assert deu.loc["logical", "width"] > deu.loc["observed", "width"] > 0
    lab = robust_labels(rob, 0.05, {("sim-model-a", "baseline"): False}).set_index("estimand")
    lab_dm = robust_labels(rob, 0.05, {("sim-model-a", "baseline"): True}).set_index("estimand")
    assert "observed support" in lab.loc["d_DEU", "r5_basis"] and "R5-logical" not in lab.loc["d_DEU", "R5_detail"]
    assert "R5-logical" in lab_dm.loc["d_DEU", "R5_detail"]
    assert bool(lab.loc["d_DEU", "R5"])              # CV-specific observed support: informative
    assert not bool(lab_dm.loc["d_DEU", "R5"])       # 0-100 bounds (decision-relevant only under differential missingness)


def test_h1e_label_rule():
    assert h1e_label(0.2, 1.0, 0.01) == H1E_ABOVE
    assert h1e_label(-1.0, -0.2, 0.01) == H1E_BELOW
    assert h1e_label(-0.2, 1.0, 0.30) == H1E_NONE
    assert h1e_label(0.2, 1.0, 0.20) == H1E_NONE          # Holm-adjusted test does not reject: no directional label
