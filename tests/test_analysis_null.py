"""(b) Null calibration of the global test and (d) the debiased heterogeneity estimator under the null.

Set HIRINGAUDIT_SLOW_TESTS=1 for more replications (tighter checks).
"""

from __future__ import annotations

import os

import numpy as np
import pytest
from scipy import stats

from hiringaudit.analysis.core import (
    aggregate_stimulus,
    build_cell,
    global_test_F,
    global_test_perm,
    heterogeneity,
    nationality_order,
    twoway_stats,
)
from hiringaudit.analysis.simulate import SimDesign, SimParams, make_nationality_effects, simulate_evaluations

SLOW = os.environ.get("HIRINGAUDIT_SLOW_TESTS") == "1"
N_SIM = 400 if SLOW else 150
DESIGN = SimDesign(eval_conditions=("baseline",), repetitions=2, positive_control=False)


def _arab_matrix(seed, params):
    ev = simulate_evaluations(DESIGN, params, seed=seed)
    cell = build_cell(aggregate_stimulus(ev, "overall_fit"), "sim-model-a", "baseline", "overall_fit",
                      nationality_order(ev))
    return cell.Y[:, cell.cols(cell.arab_codes)], cell.occupations


def _binom_ok(k, n, p=0.05, level=0.999):
    lo, hi = stats.binom.ppf([(1 - level) / 2, (1 + level) / 2], n, p)
    return lo <= k <= hi


@pytest.fixture(scope="module")
def null_runs():
    """Arab effects all zero; benchmarks non-zero (must not matter for the within-Arab test)."""
    params = SimParams(nationality_effects=make_nationality_effects(arab_mean=-3, arab_sd=0,
                                                                    benchmarks={"TUR": -4, "POL": 2}),
                       rho_eps=0.3)
    rng = np.random.default_rng(2024)
    out = []
    for s in range(N_SIM):
        Y, occ = _arab_matrix(s, params)
        _, p_perm = global_test_perm(Y, 199, rng)
        _, p_F = global_test_F(Y)
        tw = twoway_stats(Y)
        out.append((p_perm, p_F, float(tw["sigma2_deb"]), float(tw["sd_plugin"]), float(tw["sigma_A"])))
    return np.array(out)


def test_global_permutation_test_false_positive_rate(null_runs):
    k = int(np.sum(null_runs[:, 0] < 0.05))
    assert _binom_ok(k, len(null_runs)), f"permutation FPR {k}/{len(null_runs)}"


def test_parametric_F_false_positive_rate(null_runs):
    k = int(np.sum(null_runs[:, 1] < 0.05))
    assert _binom_ok(k, len(null_runs)), f"F-test FPR {k}/{len(null_runs)}"


def test_permutation_pvalues_roughly_uniform(null_runs):
    assert stats.kstest(null_runs[:, 0], "uniform").pvalue > 0.001


def test_debiased_heterogeneity_is_zero_under_null(null_runs):
    s2 = null_runs[:, 2]
    se = s2.std(ddof=1) / np.sqrt(s2.size)
    assert abs(s2.mean()) < 3.5 * se                     # untruncated debiased variance: mean ~ 0
    assert null_runs[:, 3].mean() > 0.5                   # raw plug-in SD is clearly > 0 (noise floor)
    assert np.median(null_runs[:, 4]) < 0.25 * null_runs[:, 3].mean()   # truncated estimator mostly ~0


def test_equivalence_test_calibrated_at_sesoi():
    """H1b (noncentral F): when sigma_A equals the SESOI, 'equivalence' is claimed <= ~5% of the time."""
    sesoi = 1.0
    params = SimParams(nationality_effects=make_nationality_effects(arab_sd=sesoi, seed=5), rho_eps=0.0)
    rng = np.random.default_rng(3)
    n = 120 if not SLOW else 300
    hits = 0
    for s in range(n):
        Y, occ = _arab_matrix(5000 + s, params)
        h = heterogeneity(Y, [f"c{j}" for j in range(Y.shape[1])], occ, 19, 1, rng, sesoi=sesoi,
                          boot_idx=np.zeros((1, Y.shape[0]), int))
        hits += h.p_equivalence < 0.05
    assert hits <= stats.binom.ppf(0.999, n, 0.05), f"false equivalence {hits}/{n}"
