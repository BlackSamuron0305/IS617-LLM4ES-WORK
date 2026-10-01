"""(a) Parameter recovery: known nationality effects, sigma_A, variance components, positive control."""

from __future__ import annotations

import numpy as np
import pytest

from hiringaudit.analysis.core import (
    aggregate_stimulus,
    build_cell,
    cv_contrast,
    heterogeneity,
    nationality_order,
    origin_deviations,
    replicate_array,
    t_summary,
    variance_components,
)
from hiringaudit.analysis.descriptives import positive_control
from hiringaudit.analysis.simulate import (
    ARAB_CODES,
    MAIN_OCCUPATIONS,
    MAIN_TIERS,
    SimDesign,
    SimParams,
    make_nationality_effects,
    simulate_evaluations,
)

EFF = make_nationality_effects(arab_mean=-1.5, arab_sd=2.5, benchmarks={"POL": -1.0, "TUR": -3.0},
                               control=0.5, seed=7)
DESIGN = SimDesign(eval_conditions=("baseline",), occupations=MAIN_OCCUPATIONS, cvs_per_occupation=8,
                   tier_pattern=MAIN_TIERS, repetitions=2)
PARAMS = SimParams(nationality_effects=EFF, sd_stim=2.0, sd_stim_variant=1.0, sd_rep=5.0, rho_eps=0.3,
                   sd_cv_variant=1.0, positive_control_effect=-10.0)


def _cell(ev, outcome="overall_fit"):
    stim = aggregate_stimulus(ev, outcome)
    return build_cell(stim, "sim-model-a", "baseline", outcome, nationality_order(ev))


@pytest.fixture(scope="module")
def one_run():
    ev = simulate_evaluations(DESIGN, PARAMS, seed=11)
    return ev, _cell(ev)


def test_delta_vs_reference_recovered(one_run):
    _, cell = one_run
    ref = cell.cols(["DEU"])
    est, lo, hi = [], [], []
    for c in cell.codes:
        if c == "DEU":
            continue
        t = t_summary(cv_contrast(cell.Y, cell.cols([c]), ref), strata=cell.occupations)
        est.append(t.estimate); lo.append(t.ci_low); hi.append(t.ci_high)
    true = np.array([EFF[c] for c in cell.codes if c != "DEU"])
    est = np.array(est)
    assert np.corrcoef(true, est)[0, 1] > 0.9
    assert np.max(np.abs(est - true)) < 2.0
    assert np.mean((np.array(lo) <= true) & (true <= np.array(hi))) >= 0.8


def test_sigma_A_and_origin_deviations_recovered(one_run):
    _, cell = one_run
    a = cell.cols(cell.arab_codes)
    rng = np.random.default_rng(0)
    h = heterogeneity(cell.Y[:, a], cell.arab_codes, cell.occupations, 999, 199, rng, sesoi=2.0)
    assert h.p_perm < 0.01
    assert h.ncf_ci_low <= 2.5 <= h.ncf_ci_high or abs(h.sigma_A - 2.5) < 0.4
    assert h.sd_plugin > h.sigma_A                         # plug-in is biased upward
    od = origin_deviations(cell.Y[:, a], cell.arab_codes, cell.occupations, 199, rng)
    true = np.array([EFF[c] for c in cell.arab_codes])
    true -= true.mean()
    assert np.corrcoef(true, od["delta"])[0, 1] > 0.9
    assert np.all((od["sim_ci_low"] <= od["ci_low"]) & (od["sim_ci_high"] >= od["ci_high"]))


def test_ci_coverage_over_replications():
    """Coverage of the 95% CI for Delta(A_bar, DEU) and sigma_A (noncentral F) over replications."""
    design = SimDesign(eval_conditions=("baseline",), cvs_per_occupation=6, repetitions=2, positive_control=False)
    true_d = np.mean([EFF[c] for c in ARAB_CODES])
    cov_d, cov_s = [], []
    rng = np.random.default_rng(1)
    for s in range(40):
        ev = simulate_evaluations(design, PARAMS, seed=100 + s)
        cell = _cell(ev)
        a = cell.cols(cell.arab_codes)
        t = t_summary(cv_contrast(cell.Y, a, cell.cols(["DEU"])), strata=cell.occupations)
        cov_d.append(t.ci_low <= true_d <= t.ci_high)
        h = heterogeneity(cell.Y[:, a], cell.arab_codes, cell.occupations, 99, 1, rng, sesoi=2.0)
        cov_s.append(h.ncf_ci_low <= 2.5 <= h.ncf_ci_high)
    assert 0.8 <= np.mean(cov_d) <= 1.0
    assert 0.8 <= np.mean(cov_s) <= 1.0


def test_variance_components_recovered(one_run):
    ev, cell = one_run
    rep = replicate_array(ev, "sim-model-a", "baseline", "overall_fit", cell.cvs, cell.codes, flatten_variants=False)
    vc = variance_components(cell, rep)
    assert abs(vc["sd_eps"] - 5.0) < 0.3
    assert abs(vc["rho_eps"] - 0.3) < 0.08
    assert abs(vc["sd_at"] - 2.0) < 0.5
    assert abs(vc["sd_atk"] - 1.0) < 0.5
    assert vc["sd_tk"] < 0.6                                # no nationality x wording effect simulated


def test_positive_control_recovered(one_run):
    ev, _ = one_run
    pc = positive_control(ev)
    r = pc[pc["outcome"] == "overall_fit"].iloc[0]
    assert r["detected"] and r["ci_low"] <= -10.0 <= r["ci_high"] + 1.0
