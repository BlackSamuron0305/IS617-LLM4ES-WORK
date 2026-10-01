"""(c) Bradley-Terry: recovers known worth ordering and the position (slot-A) parameter."""

from __future__ import annotations

import numpy as np
import pytest

from hiringaudit.analysis.bradley_terry import (
    arab_centred,
    bt_analysis,
    fit_bt,
    implied_from_fc,
    prepare_fc,
)
from hiringaudit.analysis.simulate import ARAB_CODES, FC_CODES, SimDesign, SimParams, simulate_forced_choice

rng0 = np.random.default_rng(42)
THETA = {c: float(rng0.normal(0, 0.6)) for c in FC_CODES}
THETA["DEU"] = 0.0
DESIGN = SimDesign(cvs_per_occupation=6, tier_pattern=("adequate", "adequate", "adequate", "strong", "strong",
                                                         "strong"),
                   fc_pair_offsets=(1, 2, 3, 4, 5, 6), fc_cv_pairs_per_nat_pair=3, fc_repetitions=2)


@pytest.fixture(scope="module")
def data():
    fc = simulate_forced_choice(DESIGN, SimParams(fc_theta=THETA, fc_position_bias=0.7, fc_kappa=0.2), seed=1)
    return prepare_fc(fc, codes=list(FC_CODES))


def test_worth_and_position_recovered(data):
    f = fit_bt(data)
    assert f.converged
    true = np.array([THETA[c] for c in data.codes])
    assert np.corrcoef(true, f.theta_ref)[0, 1] > 0.95
    assert np.max(np.abs(true - f.theta_ref)) < 0.35
    assert abs(f.gamma - 0.7) < 0.12
    from scipy.stats import spearmanr
    assert spearmanr(true, f.theta_ref)[0] > 0.9


def test_omitting_position_keeps_order_but_attenuates_scale(data):
    """Balanced quads protect the ordering, but an omitted logit term shrinks all worths
    (non-collapsibility), which is why the position parameter is part of the model."""
    f1, f0 = fit_bt(data), fit_bt(data, position=False)
    from scipy.stats import spearmanr
    assert spearmanr(f1.theta_ref, f0.theta_ref)[0] > 0.99
    slope = np.polyfit(f1.theta_ref, f0.theta_ref, 1)[0]
    assert 0.8 < slope < 1.0


def test_identification_arab_centred(data):
    f = fit_bt(data)
    a = np.array([data.codes.index(c) for c in ARAB_CODES])
    b = arab_centred(f.theta_ref, a)
    assert abs(np.mean(b[a])) < 1e-10
    assert np.allclose(np.diff(b), np.diff(f.theta_ref))         # only the constant changes


def test_bootstrap_cis_cover_truth(data):
    rng = np.random.default_rng(0)
    res = bt_analysis(data, list(ARAB_CODES), n_boot=60, n_perm=0, rng=rng)
    true = np.array([THETA[c] for c in data.codes])
    a = np.array([data.codes.index(c) for c in ARAB_CODES])
    tb = arab_centred(true, a)
    tab = res.table
    cover = np.mean((tab["ci_low"] <= tb) & (tb <= tab["ci_high"]))
    assert cover >= 0.8
    assert res.gamma_ci[0] <= 0.7 <= res.gamma_ci[1] + 0.05
    assert res.sigma_A_fc > 0.2


def test_null_worths_give_no_spurious_heterogeneity():
    fc = simulate_forced_choice(DESIGN, SimParams(fc_theta={c: 0.0 for c in FC_CODES}, fc_position_bias=0.4), seed=9)
    d = prepare_fc(fc, codes=list(FC_CODES))
    res = bt_analysis(d, list(ARAB_CODES), n_boot=60, n_perm=19, rng=np.random.default_rng(1))
    assert res.sigma_A_fc < res.sd_beta_arab                     # debiasing removes noise
    assert res.p_perm_within_arab > 0.01


def test_implied_comparisons_are_probabilities(data):
    S = np.random.default_rng(0).normal(60, 5, (len(data.cvs), len(data.codes), 6)).round()
    idata = implied_from_fc(data, S, data.cvs, data.codes)
    y = idata.k / idata.n
    assert np.all((y >= 0) & (y <= 1)) and idata.ia.size == data.ia.size
    tf = implied_from_fc(data, S, data.cvs, data.codes, tie_free=True)
    assert tf.ia.size <= data.ia.size
