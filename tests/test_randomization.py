"""Trial construction, forced-choice design, seeds and execution order."""

from __future__ import annotations

import itertools
from collections import Counter, defaultdict

import pytest
from eng_helpers import REPO, make_paths, stim_paths, tiny_config  # noqa: F401  (fixture)

from hiringaudit.config import load_experiment_config
from hiringaudit.randomization import (expand_calls, fc_design, is_connected, make_record_id, pair_degrees,
                                       walecki_cycles)
from hiringaudit.runner import load_experiment

CODES_25 = [f"N{i:02d}" for i in range(25)]


def test_walecki_partitions_all_pairs_odd():
    cycles = walecki_cycles(CODES_25)
    assert len(cycles) == 12
    edges = [e for c in cycles for e in c]
    assert len(edges) == 300 and len(set(edges)) == 300
    assert set(edges) == set(itertools.combinations(sorted(CODES_25), 2))
    for c in cycles:
        assert set(pair_degrees(c).values()) == {2} and is_connected(CODES_25, c)


def test_walecki_even_is_balanced():
    codes = CODES_25 + ["N25"]
    edges = [e for c in walecki_cycles(codes) for e in c]
    assert len(set(edges)) == 26 * 25 // 2
    assert set(pair_degrees(edges).values()) == {25}


def _cells(occs, tiers, pairs_per_cell):
    return {(o, t): [(f"{o}_{t}_{i}a", f"{o}_{t}_{i}b") for i in range(pairs_per_cell[t])] for o in occs for t in tiers}


def test_main_like_design_is_exactly_balanced():
    occs = [f"occ{i}" for i in range(6)]
    tiers = ["strong", "adequate", "borderline"]
    cells = _cells(occs, tiers, {"strong": 1, "adequate": 6, "borderline": 1})
    quads = fc_design(CODES_25, cells, occs, tiers, "all", 2, ["k1", "k2", "k3"], seed=7)
    assert len(quads) == 600
    pairs = Counter((q.nat_a, q.nat_b) for q in quads)
    assert len(pairs) == 300 and set(pairs.values()) == {2}
    # c = 2 distinct CV pairs per nationality pair
    cvp = defaultdict(set)
    for q in quads:
        cvp[(q.nat_a, q.nat_b)].add((q.cv1, q.cv2))
    assert all(len(v) == 2 for v in cvp.values())
    # each level equally often per occupation and per tier
    for key in ("occupation", "tier"):
        per = defaultdict(Counter)
        for q in quads:
            per[getattr(q, key)][q.nat_a] += 1
            per[getattr(q, key)][q.nat_b] += 1
        for counts in per.values():
            assert len(set(counts.values())) == 1 and len(counts) == 25
    assert set(Counter(q.variant for q in quads).values()) == {200}
    # M13: every nationality gets exactly 1/3 of its 48 quads per variant
    per_level = defaultdict(Counter)
    for q in quads:
        per_level[q.nat_a][q.variant] += 1
        per_level[q.nat_b][q.variant] += 1
    assert all(set(c.values()) == {16} for c in per_level.values())


def test_pilot_like_design_balanced_connected():
    occs = ["a", "b", "c"]
    tiers = ["strong", "adequate", "borderline"]
    cells = _cells(occs, tiers, {"strong": 1, "adequate": 1, "borderline": 1})
    quads = fc_design(CODES_25, cells, occs, tiers, 4, 1, ["k1", "k2", "k3"], seed=1)
    pairs = [(q.nat_a, q.nat_b) for q in quads]
    assert len(pairs) == len(set(pairs)) == 100
    assert set(pair_degrees(pairs).values()) == {8}
    assert is_connected(CODES_25, pairs)
    assert {(q.occupation, q.tier) for q in quads} == set(cells)  # every cell used
    per_level = defaultdict(Counter)  # M13: 8 quads per level -> 3/3/2 across variants
    for q in quads:
        per_level[q.nat_a][q.variant] += 1
        per_level[q.nat_b][q.variant] += 1
    assert all(sorted(c.values()) == [2, 3, 3] for c in per_level.values())


@pytest.fixture(scope="module")
def exp(tmp_path_factory):
    return load_experiment(tiny_config(), make_paths(tmp_path_factory.mktemp("rand")))


def test_ie_crossing_variants_and_positive_control(exp):
    ie = [t for t in exp.plan.trials if t.task_type == "independent"]
    cvs = ["swdev_01", "swdev_02", "swdev_04", "swdev_05"]
    codes = ["DEU", "EGY", "SYR", "POL", "TUR", "NONE"]
    placebo = ["URY", "MWI"]
    for cond, expected in (("baseline", codes + placebo), ("neutrality", codes)):
        cells = Counter((t.base_cv_ids[0], t.nationalities[0], t.prompt_variant)
                        for t in ie if t.prompt_condition == cond and t.clone_type == "counterfactual")
        assert set(cells) == set(itertools.product(cvs, expected, ["k1", "k2"])) and set(cells.values()) == {1}
    pc = [t for t in ie if t.clone_type == "positive_control"]
    assert {t.prompt_condition for t in pc} == {"baseline"}
    assert Counter(t.base_cv_ids[0] for t in pc) == {cv: 2 for cv in cvs}
    assert all(t.stimulus_ids[0].endswith("__NONE__pc") for t in pc)
    assert {t.repetitions for t in ie if t.prompt_condition == "baseline"} == {2}


def test_forced_choice_quads(exp):
    fc = [t for t in exp.plan.trials if t.task_type == "forced_choice"]
    assert fc and all(not {"NONE", "URY", "MWI"} & set(t.nationalities) for t in fc)
    by_quad = defaultdict(list)
    for t in fc:
        by_quad[t.quad_id].append(t)
    for trials in by_quad.values():
        assert len(trials) == 4
        assert len({t.prompt_variant for t in trials}) == 1
        assert len({t.prompt_condition for t in trials}) == 1
        cv1, cv2 = sorted(set(trials[0].base_cv_ids))
        assert cv1 != cv2 and len({t.qualification_tier for t in trials}) == 1
        assert Counter(t.fc_order for t in trials) == {"AB": 2, "BA": 2}
        # every CV carries both nationalities; every nationality in both positions
        carried = {(cv, n) for t in trials for cv, n in zip(t.base_cv_ids, t.nationalities)}
        nats = set(trials[0].nationalities)
        assert carried == {(cv, n) for cv in (cv1, cv2) for n in nats}
        assert Counter(t.nationalities[0] for t in trials) == {n: 2 for n in nats}
        assert Counter(t.base_cv_ids[0] for t in trials) == {cv1: 2, cv2: 2}
    # A/B reversal balance over the whole design
    slot_a = Counter(t.nationalities[0] for t in fc)
    slot_b = Counter(t.nationalities[1] for t in fc)
    assert slot_a == slot_b


def test_determinism_and_seed_independence_of_ids(stim_paths):  # noqa: F811
    e1 = load_experiment(tiny_config(), stim_paths)
    e2 = load_experiment(tiny_config(), stim_paths)
    c1 = expand_calls(e1.plan.trials, "run", e1.cfg.seed, e1.cfg.models)
    c2 = expand_calls(e2.plan.trials, "run", e2.cfg.seed, e2.cfg.models)
    assert [(c.record_id, c.seed, c.execution_index) for c in c1] == [(c.record_id, c.seed, c.execution_index) for c in c2]
    # A different master seed changes seeds, execution order and the (seeded) FC
    # design, but not the ids of the fully crossed IE and principle cells.
    e3 = load_experiment(tiny_config(seed=99), stim_paths)
    crossed = lambda e: {t.trial_id for t in e.plan.trials if t.task_type != "forced_choice"}  # noqa: E731
    assert crossed(e3) == crossed(e1)
    c3 = [c for c in expand_calls(e3.plan.trials, "run", e3.cfg.seed, e3.cfg.models) if c.trial.task_type != "forced_choice"]
    c1x = [c for c in c1 if c.trial.task_type != "forced_choice"]
    assert [c.record_id for c in c3] != [c.record_id for c in c1x]  # different order
    assert {c.record_id for c in c3} == {c.record_id for c in c1x}  # same set
    assert {c.seed for c in c3} != {c.seed for c in c1x}
    assert make_record_id("run", "t_x", 1) == make_record_id("run", "t_x", 1) != make_record_id("run2", "t_x", 1)


def test_seeds_never_depend_on_nationality(exp):
    calls = expand_calls(exp.plan.trials, "run", exp.cfg.seed, exp.cfg.models)
    groups = defaultdict(set)
    for c in calls:
        t = c.trial
        if t.task_type == "independent":
            groups[("ie", t.prompt_condition, t.base_cv_ids, t.prompt_variant, c.repetition)].add(c.seed)
        elif t.task_type == "forced_choice":
            groups[("fc", t.quad_id, t.fc_order, c.repetition)].add(c.seed)
    assert groups and all(len(s) == 1 for s in groups.values())
    # but seeds do differ between repetitions and variants
    assert len({c.seed for c in calls}) > len(calls) // 20


def test_execution_order_contiguous_per_model(stim_paths):  # noqa: F811
    cfg = load_experiment_config(tiny_config())
    exp2 = load_experiment(tiny_config(), stim_paths)
    trials = exp2.plan.trials
    fake = [t.__class__(**{**t.__dict__, "model_alias": "other"}) for t in trials]
    calls = expand_calls(trials + fake, "run", cfg.seed, ["mock", "other"])
    models = [c.trial.model_alias for c in calls]
    first_other = models.index("other")
    assert set(models[:first_other]) == {"mock"} and set(models[first_other:]) == {"other"}
    assert [c.execution_index for c in calls] == list(range(len(calls)))
    conds = [c.trial.prompt_condition for c in calls[:first_other]]
    assert conds[:50] != sorted(conds[:50])  # shuffled, not grouped by condition


def test_placebo_only_in_baseline_primary(stim_paths):  # noqa: F811
    cfg = tiny_config(robustness_arms=[{"arm_id": "greedy", "conditions": ["baseline"], "temperature": 0.0,
                                        "prompt_variants": ["k1"]}])
    e = load_experiment(cfg, stim_paths)
    placebo = {"URY", "MWI"}
    uses = {(t.task_type, t.prompt_condition, t.arm, t.clone_type) for t in e.plan.trials
            if placebo & set(t.nationalities)}
    assert uses == {("independent", "baseline", "primary", "counterfactual")}
    assert e.placebo_codes == placebo
    off = load_experiment(tiny_config(include_placebo=False), stim_paths)
    assert not any(placebo & set(t.nationalities) for t in off.plan.trials)


def test_forced_choice_pairs_share_base_country_and_job_ad_location(stim_paths):  # noqa: F811
    """User request 2026-10-01: an FC pair = same occupation, same tier, same base
    country, and the job ad is located in that base city."""
    from hiringaudit.runner import PromptBuilder

    cfg = tiny_config(occupations="all", base_cvs="all",
                      nationalities=["DEU", "EGY", "SYR", "POL", "TUR", "ARE", "SAU", "NONE"],
                      conditions={"baseline": {"enabled": True, "repetitions": 1},
                                  "neutrality": {"enabled": False}, "forced_choice": {"enabled": True},
                                  "forced_choice_neutrality": {"enabled": False},
                                  "principle_probe": {"enabled": False}},
                      prompt_variants=["k1"],
                      forced_choice_design={"tiers": ["strong", "adequate", "borderline"],
                                            "nationality_pairs": {"n_cycles": "all", "copies": 1}})
    e = load_experiment(cfg, stim_paths)
    base = {cv_id: (cv["base_country"], cv["base_city"]) for cv_id, cv in e.cvs.items()}
    # every cell holds only same-base-country CV pairs; adequate cells hold 2 (of 6 possible) pairs
    for (occ, tier), pairs in e.plan.fc_cells.items():
        assert pairs and all(base[a] == base[b] for a, b in pairs)
        assert len(pairs) == (2 if tier == "adequate" else 1)
    assert all(base[q.cv1][0] == base[q.cv2][0] == q.base_country for q in e.plan.fc_design)
    builder = PromptBuilder(e)
    fc = [t for t in e.plan.trials if t.task_type == "forced_choice"]
    ie = [t for t in e.plan.trials if t.task_type == "independent"]
    assert fc and ie
    for t in fc[:40] + ie[::97]:
        codes = {base[c][0] for c in t.base_cv_ids}
        assert codes == {t.base_country}
        city = base[t.base_cv_ids[0]][1]
        country = e.all_nationalities.by_code(t.base_country).country
        assert f"Location: {city}, {country}" in builder.user_text(t)
