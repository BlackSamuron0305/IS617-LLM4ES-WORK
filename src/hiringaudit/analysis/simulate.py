"""Synthetic data in the processed-table schema (design contract v0.2).

Used by the analysis tests, by ``analysis/power_analysis.py`` and (optionally)
by the engineer's pipeline tests. Everything produced here is synthetic and is
marked ``is_mock = True`` by default. Numbers produced by this module are
never findings.

Generative model for independent evaluations (experimental_design.md §1.6):

    q[m,p,i,n,k] = mu + occ[j(i)] + off[m] + tier[i] + kappa[k] + alpha[i] + (ak)[i,k]
                   + s_m[m] * s_p[p] * (tau[n] + (tk)[n,k]) + (at)[i,n] + (atk)[i,n,k]
    y*[r]        = q + sqrt(rho) * s[i,k,r] + sqrt(1 - rho) * u[i,n,k,r]      (decoder noise, sd_rep)
    fit[r]       = clip(round(y*[r]), 0, 100)
    interview[r] ~ Bernoulli(logistic(slope * (y*[r] - threshold)))

s[i,k,r] is shared by all clones of a base CV with the same variant and
replicate (common random numbers from nationality-free seeds, A17), so rho is
the cross-clone correlation of decoder noise. The positive-control clone is
the NONE clone with ``positive_control_effect`` added (A7, baseline only).

Setting (2026-10-01): every base CV is set in one Arab League base country (``base_country``),
allocated per same-occupation, same-tier CV pair as in the real design (``SimDesign.base_countries``;
3 pairs per country in the main design, spread over occupations and tiers). The clone whose
nationality equals the base country is a host national; ``host_national_effect`` (fit points,
scaled like the nationality effects by s_m * s_p) is added to it:

    q[m,p,i,n,k] += s_m[m] * s_p[p] * eta_host * 1[n == base_country(i)]

Forced choice: P(choose slot A) = logistic(delta + kappa_fc * (q_A - q_B)),
or, if ``fc_theta`` is given, logistic(delta + theta_a - theta_b + kappa_fc * (cv_A - cv_B)
+ fc_host_effect * (host_A - host_B)). Both CVs of a forced-choice pair share one base country.
"""

from __future__ import annotations

import zlib
from dataclasses import dataclass, field, replace
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd

from .schema import EVALUATION_COLUMNS, FORCED_CHOICE_COLUMNS, PRINCIPLE_COLUMNS, TEXT_FLAGS

# Mirror of stimuli/nationalities.csv (authoritative). Kept in code so that the
# simulation does not depend on the stimulus files; a test checks the two agree.
NATIONALITIES: tuple[dict, ...] = tuple(
    dict(code=c, group=g, subregion=s, contested=k)
    for c, g, s, k in [
        ("DZA", "arab", "maghreb", False), ("BHR", "arab", "gcc", False),
        ("COM", "arab", "horn_indian_ocean", True), ("DJI", "arab", "horn_indian_ocean", True),
        ("EGY", "arab", "nile_valley", False), ("IRQ", "arab", "mashriq", False),
        ("JOR", "arab", "mashriq", False), ("KWT", "arab", "gcc", False),
        ("LBN", "arab", "mashriq", False), ("LBY", "arab", "maghreb", False),
        ("MRT", "arab", "maghreb", False), ("MAR", "arab", "maghreb", False),
        ("OMN", "arab", "gcc", False), ("PSE", "arab", "mashriq", False),
        ("QAT", "arab", "gcc", False), ("SAU", "arab", "gcc", False),
        ("SOM", "arab", "horn_indian_ocean", True), ("SDN", "arab", "nile_valley", False),
        ("SYR", "arab", "mashriq", False), ("TUN", "arab", "maghreb", False),
        ("ARE", "arab", "gcc", False), ("YEM", "arab", "peninsula_non_gcc", False),
        ("DEU", "benchmark", "western_europe", False), ("POL", "benchmark", "eu_foreign", False),
        ("TUR", "benchmark", "non_arab_mena", False),
        ("URY", "placebo", "latin_america", False), ("BOL", "placebo", "latin_america", False),
        ("SYC", "placebo", "sub_saharan_africa", False), ("MWI", "placebo", "sub_saharan_africa", False),
        ("MDV", "placebo", "south_asia", False), ("NPL", "placebo", "south_asia", False),
        ("MYS", "placebo", "east_asia_pacific", False), ("KHM", "placebo", "east_asia_pacific", False),
        ("NONE", "control", "not_stated", False),
    ]
)
NAT_META = {d["code"]: d for d in NATIONALITIES}
ARAB_CODES = tuple(d["code"] for d in NATIONALITIES if d["group"] == "arab")
PLACEBO_CODES = tuple(d["code"] for d in NATIONALITIES if d["group"] == "placebo")
ALL_CODES = tuple(d["code"] for d in NATIONALITIES if d["group"] != "placebo")   # the 26 contract levels
FC_CODES = tuple(c for c in ALL_CODES if c != "NONE")          # A9

# Base countries of the CVs (stimuli/README.md, setting 2026-10-01); all are Arab League members.
BASE_COUNTRIES = ("ARE", "SAU", "QAT", "KWT", "OMN", "BHR", "JOR", "EGY")

PILOT_OCCUPATIONS = ("software_developer", "retail_sales_associate", "warehouse_associate")  # A12
MAIN_OCCUPATIONS = PILOT_OCCUPATIONS + (
    "financial_accountant", "management_consultant", "administrative_assistant")
PILOT_TIERS = ("strong", "strong", "adequate", "adequate", "borderline", "borderline")      # A16
MAIN_TIERS = ("strong", "strong", "adequate", "adequate", "adequate", "adequate",
              "borderline", "borderline")

PRINCIPLE_ITEMS = (
    [dict(item_id=f"P{k:02d}", keying="pro", item_type="principle", expected_answer=None) for k in range(1, 6)]
    + [dict(item_id=f"R{k:02d}", keying="reverse", item_type="principle", expected_answer=None)
       for k in range(1, 6)]
    + [dict(item_id="C01", keying="control", item_type="control", expected_answer="yes"),   # should matter
       dict(item_id="C02", keying="control", item_type="control", expected_answer="no")]    # irrelevant
)


@dataclass(frozen=True)
class SimDesign:
    models: tuple[str, ...] = ("sim-model-a",)
    eval_conditions: tuple[str, ...] = ("baseline", "neutrality")
    fc_conditions: tuple[str, ...] = ("forced_choice",)
    occupations: tuple[str, ...] = PILOT_OCCUPATIONS
    cvs_per_occupation: int = 6
    tier_pattern: tuple[str, ...] = PILOT_TIERS
    nationalities: tuple[str, ...] = ALL_CODES
    variants: tuple[str, ...] = ("k1", "k2", "k3")
    repetitions: int = 3
    positive_control: bool = True
    placebo: tuple[str, ...] = ()          # placebo nationalities, baseline IE primary arm only (review H5)
    # forced choice: nationality pairs from a cyclic design with these offsets
    # (each nationality then appears in 2*len(offsets) pairs); None = all pairs
    fc_pair_offsets: tuple[int, ...] | None = (1, 2, 3, 4)
    fc_cv_pairs_per_nat_pair: int = 1                      # c in experimental_design.md §4
    fc_repetitions: int = 1
    principle_contexts: tuple[str, ...] | None = None      # default: generic + occupations
    principle_repetitions: int = 5
    # robustness arms written as extra evaluation rows (baseline, first variant, one replicate):
    # "greedy" (temperature 0), as in the engineer's output
    robustness_arms: tuple[str, ...] = ()
    # base countries allocated per same-occupation, same-tier CV pair (empty tuple: no base country)
    base_countries: tuple[str, ...] = BASE_COUNTRIES
    run_id: str = "sim-run"


@dataclass(frozen=True)
class SimParams:
    fit_intercept: float = 62.0
    occupation_effects: dict = field(default_factory=dict)
    tier_effects: dict = field(default_factory=lambda: {"strong": 14.0, "adequate": 0.0,
                                                        "borderline": -14.0})
    model_offsets: dict = field(default_factory=dict)
    variant_effects: dict = field(default_factory=dict)          # kappa_k
    sd_cv: float = 6.0                                           # alpha_i
    sd_cv_variant: float = 1.0                                   # (alpha kappa)_ik
    sd_stim: float = 2.0                                         # (alpha tau)_in
    sd_stim_variant: float = 1.0                                 # (alpha tau kappa)_ink
    sd_rep: float = 5.0                                          # decoder noise
    rho_eps: float = 0.0                                         # cross-clone noise correlation
    nationality_effects: dict = field(default_factory=dict)      # tau_n, fit points vs DEU
    host_national_effect: float = 0.0                            # eta: bonus of the host-national clone
    fc_host_effect: float = 0.0                                  # logit host term (fc_theta branch only)
    nat_variant_effects: dict = field(default_factory=dict)      # {(code, variant): value}
    model_effect_scale: dict = field(default_factory=dict)
    condition_effect_scale: dict = field(default_factory=dict)   # e.g. {"neutrality": .5}
    positive_control_effect: float = -12.0
    interview_threshold: float = 60.0
    interview_slope: float = 0.25
    fc_position_bias: float = 0.3
    fc_kappa: float = 0.25
    fc_theta: dict | None = None
    p_api_error: float = 0.0
    p_refusal: float = 0.0
    p_malformed: float = 0.0
    refusal_by_nationality: dict = field(default_factory=dict)
    stim_sd_scale: dict = field(default_factory=dict)            # per-nationality multiplier of sd_stim(_variant)
    flag_base_rate: float = 0.05
    flag_rate_by_group: dict = field(default_factory=dict)
    pronoun_probs: tuple[float, float, float, float] = (0.7, 0.2, 0.05, 0.05)  # none, they, he, she
    principle_endorse_prob: dict = field(default_factory=dict)   # per model, default .95
    principle_control_accuracy: dict = field(default_factory=dict)  # per model, default .95


def make_nationality_effects(arab_mean: float = 0.0, arab_sd: float = 0.0,
                             benchmarks: dict | None = None, control: float = 0.0,
                             codes: tuple[str, ...] = ARAB_CODES, seed: int = 0,
                             ddof: int = 0) -> dict:
    """Nationality effects (vs DEU) with an exact within-Arab SD.

    Within-Arab deviations are evenly spaced normal quantiles rescaled to have
    SD exactly ``arab_sd`` (divisor ``len(codes) - ddof``; ddof=0 matches the
    finite-population sigma_A of experimental_design.md §1.4), assigned to codes
    in a seeded random order. Used only to specify simulation scenarios.
    """
    from scipy.stats import norm

    k = len(codes)
    eff = {c: 0.0 for c in ALL_CODES}
    if arab_sd > 0:
        z = norm.ppf((np.arange(1, k + 1) - 0.5) / k)
        z = (z - z.mean()) / z.std(ddof=ddof) * arab_sd
        order = np.random.default_rng(seed).permutation(k)
        for c, val in zip(codes, z[order]):
            eff[c] = float(val)
    for c in codes:
        eff[c] += arab_mean
    eff["NONE"] = float(control)
    for c, v in (benchmarks or {}).items():
        eff[c] = float(v)
    eff["DEU"] = 0.0
    return eff


def _seed(*parts) -> int:
    """Deterministic nationality-free seed (A17)."""
    return zlib.crc32("|".join(map(str, parts)).encode()) & 0x7FFFFFFF


def allocate_base_countries(cvs: pd.DataFrame, countries: tuple[str, ...]) -> pd.Series:
    """Base country per CV, assigned per same-occupation, same-tier CV pair (like stimuli/building_blocks/cv_slots.csv).

    Within each occupation the CVs of one tier are paired in order (a leftover CV forms a unit of its
    own); unit u (in order of first appearance) of occupation o gets country (u * n_occ + o) mod n,
    so each country receives units from different occupations and positions. With the main design
    (6 occupations x 4 pairs) every country gets 3 pairs (6 CVs); with the pilot design (3 x 3 pairs)
    one country gets two pairs, as in the real pilot.
    """
    if not countries:
        return pd.Series("", index=cvs.index, dtype=object)
    occs = list(dict.fromkeys(cvs["occupation"]))
    out = pd.Series("", index=cvs.index, dtype=object)
    for o, occ in enumerate(occs):
        g = cvs[cvs["occupation"] == occ]
        units, open_unit = [], {}
        for idx, tier in zip(g.index, g["qualification_tier"]):
            if tier in open_unit:
                units[open_unit.pop(tier)].append(idx)
            else:
                open_unit[tier] = len(units)
                units.append([idx])
        for u, members in enumerate(units):
            out.loc[members] = countries[(u * len(occs) + o) % len(countries)]
    return out


def _cv_table(design: SimDesign, params: SimParams, rng: np.random.Generator) -> pd.DataFrame:
    rows = []
    for occ in design.occupations:
        for k in range(design.cvs_per_occupation):
            tier = design.tier_pattern[k % len(design.tier_pattern)]
            rows.append(dict(base_cv_id=f"{occ}__cv{k + 1:02d}", occupation=occ, qualification_tier=tier))
    cvs = pd.DataFrame(rows)
    cvs["base_country"] = allocate_base_countries(cvs, tuple(design.base_countries))
    cvs["u"] = rng.normal(0.0, params.sd_cv, len(cvs))
    cvs["fixed"] = (params.fit_intercept
                    + cvs["occupation"].map(lambda o: params.occupation_effects.get(o, 0.0))
                    + cvs["qualification_tier"].map(lambda t: params.tier_effects.get(t, 0.0)))
    return cvs


def _logistic(x):
    return 1.0 / (1.0 + np.exp(-x))


def simulate_evaluations(design: SimDesign, params: SimParams, seed: int = 0,
                         is_mock: bool = True, cvs: pd.DataFrame | None = None,
                         rng: np.random.Generator | None = None) -> pd.DataFrame:
    """Simulate ``evaluations.csv`` rows (one per call) under the model above."""
    rng = rng if rng is not None else np.random.default_rng(seed)
    if cvs is None:
        cvs = _cv_table(design, params, rng)
    models, conds = np.array(design.models), np.array(design.eval_conditions)
    variants = np.array(design.variants)
    I, K, R = len(cvs), len(variants), design.repetitions
    # clone list: counterfactual nationalities (+ positive control, baseline only)
    clones = [(c, "counterfactual") for c in design.nationalities]
    n_cf = len(clones)
    clones += [(c, "counterfactual") for c in design.placebo if c not in design.nationalities]
    is_placebo = np.arange(len(clones)) >= n_cf
    if design.positive_control:
        clones.append(("NONE", "positive_control"))
    C = len(clones)
    clone_nat = np.array([c for c, _ in clones])
    clone_type = np.array([t for _, t in clones])
    tau = np.array([params.nationality_effects.get(c, 0.0) if t == "counterfactual" else
                    params.nationality_effects.get("NONE", 0.0) for c, t in clones])
    pc_add = np.where(clone_type == "positive_control", params.positive_control_effect, 0.0)
    bc = cvs["base_country"].astype(str).to_numpy() if "base_country" in cvs else np.full(I, "", object)
    host = (clone_nat[None, :] == bc[:, None]) & (clone_type == "counterfactual")[None, :]   # (I, C)
    kap = np.array([params.variant_effects.get(k, 0.0) for k in variants])
    tk = np.array([[params.nat_variant_effects.get((c, k), 0.0) for k in variants] for c in clone_nat])

    frames = []
    for mi, m in enumerate(models):
        s_m = params.model_effect_scale.get(m, 1.0)
        off = params.model_offsets.get(m, 0.0)
        for p in conds:
            s_p = params.condition_effect_scale.get(p, 1.0)
            is_plc = np.concatenate([is_placebo, np.zeros(C - is_placebo.size, bool)])
            keep_clone = np.ones(C, bool) if p == "baseline" else ((clone_type == "counterfactual") & ~is_plc)
            ak = rng.normal(0, params.sd_cv_variant, (I, K))
            sc = np.array([params.stim_sd_scale.get(c, 1.0) for c in clone_nat])
            at = rng.normal(0, params.sd_stim, (I, C)) * sc[None, :]
            atk = rng.normal(0, params.sd_stim_variant, (I, C, K)) * sc[None, :, None]
            shared = rng.normal(0, 1, (I, K, R))
            q = (cvs["fixed"].to_numpy()[:, None, None] + cvs["u"].to_numpy()[:, None, None] + off
                 + kap[None, None, :] + ak[:, None, :]
                 + s_m * s_p * (tau[None, :, None] + tk[None, :, :]) + at[:, :, None] + atk
                 + s_m * s_p * params.host_national_effect * host[:, :, None]
                 + pc_add[None, :, None])                                      # (I, C, K)
            u = rng.normal(0, 1, (I, C, K, R))
            noise = params.sd_rep * (np.sqrt(params.rho_eps) * shared[:, None, :, :]
                                     + np.sqrt(1 - params.rho_eps) * u)
            ystar = q[..., None] + noise                                        # (I, C, K, R)
            ii, cc, kk, rr = np.meshgrid(np.arange(I), np.arange(C), np.arange(K), np.arange(R),
                                         indexing="ij")
            sel = keep_clone[cc]
            ii, cc, kk, rr, ys = ii[sel], cc[sel], kk[sel], rr[sel], ystar[sel]
            n = ys.size
            fit = np.clip(np.round(ys), 0, 100)
            interview = (rng.random(n) < _logistic(params.interview_slope
                                                   * (ys - params.interview_threshold))).astype(float)
            nat_rows = clone_nat[cc]
            p_ref = params.p_refusal + np.array([params.refusal_by_nationality.get(c, 0.0) for c in nat_rows])
            uu = rng.random(n)
            status = np.full(n, "ok", dtype=object)
            status[uu < params.p_api_error] = "api_error"
            status[(uu >= params.p_api_error) & (uu < params.p_api_error + p_ref)] = "refusal"
            lo = params.p_api_error + p_ref
            status[(uu >= lo) & (uu < lo + params.p_malformed)] = "malformed_json"
            bad = status != "ok"
            conf = np.clip(np.round(rng.normal(75, 10, n)), 0, 100)
            fit[bad], interview[bad], conf[bad] = np.nan, np.nan, np.nan
            cv_ids = cvs["base_cv_id"].to_numpy()[ii]
            groups = np.array([NAT_META[c]["group"] for c in nat_rows])
            ctype = clone_type[cc]
            stim = np.where(ctype == "positive_control", np.char.add(cv_ids.astype(str), "__NONE__pc"),
                            np.char.add(np.char.add(cv_ids.astype(str), "__"), nat_rows.astype(str)))
            f = pd.DataFrame({
                "model_alias": m, "prompt_condition": p, "prompt_variant": variants[kk],
                "clone_type": ctype, "occupation": cvs["occupation"].to_numpy()[ii],
                "base_cv_id": cv_ids, "qualification_tier": cvs["qualification_tier"].to_numpy()[ii],
                "nationality": nat_rows, "nationality_group": groups,
                "subregion": [NAT_META[c]["subregion"] for c in nat_rows],
                "arab_identity_contested": [NAT_META[c]["contested"] for c in nat_rows],
                "repetition": rr + 1, "overall_fit": fit, "interview": interview, "confidence": conf,
                "parse_status": status, "stim": stim, "arm": "primary",
                "temperature": 0.7, "base_country": bc[ii], "host_national": host[ii, cc],
            })
            sg = np.array([[[_seed(m, p, cv, k, r) for r in range(R)] for k in variants]
                           for cv in cvs["base_cv_id"]])
            f["seed"] = sg[ii, kk, rr]
            frames.append(f)
            if p == "baseline":
                for arm in design.robustness_arms:
                    a = f[(f["prompt_variant"] == variants[0]) & (f["repetition"] == 1)
                          & (f["clone_type"] == "counterfactual") & (f["nationality_group"] != "placebo")].copy()
                    a["arm"] = arm
                    if arm == "greedy":
                        a["temperature"] = 0.0
                    frames.append(a)
    df = pd.concat(frames, ignore_index=True)
    n = len(df)
    run = design.run_id
    df["trial_id"] = (df["arm"] + "|" + df["model_alias"] + "|" + df["prompt_condition"] + "|"
                      + df["prompt_variant"] + "|" + df["stim"])
    df["run_id"] = run
    df["record_id"] = [f"{run}-ev-{k:08d}" for k in range(n)]
    df["is_mock"] = is_mock
    df["provider"] = "simulator"
    df["model_id"] = "sim/" + df["model_alias"]
    df["model_revision"] = "sim-rev-0001"
    df["execution_index"] = -1
    for m in design.models:
        idx = np.flatnonzero(df["model_alias"].to_numpy() == m)
        df.loc[idx, "execution_index"] = rng.permutation(idx.size)
    df["reason"] = "simulated"
    bad = df["parse_status"] != "ok"
    df["refusal"] = df["parse_status"] == "refusal"
    df["api_error"] = df["parse_status"] == "api_error"
    flag_p = params.flag_base_rate + df["nationality_group"].map(
        lambda g: params.flag_rate_by_group.get(g, 0.0)).to_numpy()
    for f in TEXT_FLAGS:
        vals = (rng.random(n) < flag_p).astype(object)
        vals[bad.to_numpy()] = None
        df[f] = vals
    pr = rng.choice(np.array(["none", "they", "he", "she"]), size=n, p=np.array(params.pronoun_probs))
    df["pronoun_gender"] = np.where(bad, None, pr)
    df["user_prompt_version"] = df["prompt_condition"] + "_" + df["prompt_variant"] + "@sim-v1"
    df["prompt_sha256"] = [f"{zlib.crc32(f'{s}|{c}|{v}'.encode()):08x}" for s, c, v in
                           zip(df["stim"], df["prompt_condition"], df["prompt_variant"])]
    _parser_diagnostics(df)
    return df[list(EVALUATION_COLUMNS) + ["arm", "temperature", "user_prompt_version",
                                          "prompt_sha256", "n_json_objects", "near_miss"]]


def _parser_diagnostics(df: pd.DataFrame) -> None:
    """Engineer parser diagnostics (review L4): JSON objects found and near-miss flag (never coerced)."""
    st = df["parse_status"].to_numpy()
    df["n_json_objects"] = np.where(np.isin(st, ["ok", "schema_violation"]), 1, 0)
    df["near_miss"] = False


def _fc_nat_pairs(codes: tuple[str, ...], offsets) -> list[tuple[str, str]]:
    if offsets is None:
        return list(combinations(codes, 2))
    n = len(codes)
    pairs = set()
    for d in offsets:
        for i in range(n):
            a, b = codes[i], codes[(i + d) % n]
            if a != b:
                pairs.add(tuple(sorted((a, b))))
    return sorted(pairs)


def simulate_forced_choice(design: SimDesign, params: SimParams, seed: int = 0,
                           is_mock: bool = True, cvs: pd.DataFrame | None = None,
                           rng: np.random.Generator | None = None) -> pd.DataFrame:
    """Simulate ``forced_choice.csv`` with the quad design (contract §4, A3, A9).

    ``cv_a``/``nationality_a`` denote the candidate shown in slot A.
    ``fc_order`` is "AB" when the quad's first CV is in slot A, else "BA".
    Each nationality pair is assigned to ``fc_cv_pairs_per_nat_pair`` same-tier
    CV pairs (round-robin over a seeded shuffle); all 4 prompts of a quad share
    one wording variant (round-robin).
    """
    rng = rng if rng is not None else np.random.default_rng(seed)
    if cvs is None:
        cvs = _cv_table(design, params, rng)
    codes = tuple(c for c in design.nationalities if c != "NONE")
    nat_pairs = _fc_nat_pairs(codes, design.fc_pair_offsets)
    if "base_country" not in cvs:
        cvs = cvs.assign(base_country="")
    cvq = cvs.set_index("base_cv_id")
    cv_pairs = []
    for _, g in cvs.groupby(["occupation", "qualification_tier", "base_country"], sort=True):
        cv_pairs += list(combinations(sorted(g["base_cv_id"]), 2))     # an FC pair shares its base country
    if not cv_pairs:
        raise ValueError("no same-occupation, same-tier CV pairs available for forced choice")
    order = rng.permutation(len(cv_pairs))
    assign = []
    pos = 0
    for a, b in nat_pairs:
        for _ in range(design.fc_cv_pairs_per_nat_pair):
            assign.append((cv_pairs[order[pos % len(cv_pairs)]], (a, b), design.variants[pos % len(design.variants)]))
            pos += 1
    rows = []
    for m in design.models:
        s_m = params.model_effect_scale.get(m, 1.0)
        for cond in design.fc_conditions:
            s_p = params.condition_effect_scale.get(cond, 1.0)
            stim_noise: dict = {}

            def latent(cv, nat):
                key = (cv, nat)
                if key not in stim_noise:
                    stim_noise[key] = rng.normal(0.0, params.sd_stim)
                base = cvq.at[cv, "fixed"] + cvq.at[cv, "u"]
                hb = params.host_national_effect if nat == cvq.at[cv, "base_country"] else 0.0
                return base + s_m * s_p * (params.nationality_effects.get(nat, 0.0) + hb) + stim_noise[key]

            for (c1, c2), (a, b), var in assign:
                quad = f"{m}|{cond}|{c1}+{c2}|{a}+{b}"
                for (cvA, natA, cvB, natB, fo) in ((c1, a, c2, b, "AB"), (c2, b, c1, a, "BA"),
                                                   (c1, b, c2, a, "AB"), (c2, a, c1, b, "BA")):
                    if params.fc_theta is not None:
                        cvd = ((cvq.at[cvA, "fixed"] + cvq.at[cvA, "u"]) - (cvq.at[cvB, "fixed"] + cvq.at[cvB, "u"]))
                        hd = (float(natA == cvq.at[cvA, "base_country"])
                              - float(natB == cvq.at[cvB, "base_country"]))
                        eta = (params.fc_position_bias + params.fc_theta.get(natA, 0.0)
                               - params.fc_theta.get(natB, 0.0) + params.fc_kappa * cvd
                               + params.fc_host_effect * hd)
                    else:
                        eta = params.fc_position_bias + params.fc_kappa * (latent(cvA, natA) - latent(cvB, natB))
                    trial = f"{quad}|{cvA}:{natA}>{cvB}:{natB}"
                    for r in range(design.fc_repetitions):
                        rows.append((m, cond, var, cvq.at[c1, "occupation"], cvq.at[c1, "qualification_tier"],
                                     quad, trial, cvA, cvB, natA, natB, fo, r + 1, eta,
                                     cvq.at[c1, "base_country"]))
    df = pd.DataFrame(rows, columns=["model_alias", "prompt_condition", "prompt_variant", "occupation",
                                     "qualification_tier", "quad_id", "trial_id", "cv_a", "cv_b",
                                     "nationality_a", "nationality_b", "fc_order", "repetition", "eta",
                                     "base_country"])
    df["host_national_a"] = df["nationality_a"] == df["base_country"]
    df["host_national_b"] = df["nationality_b"] == df["base_country"]
    n = len(df)
    pick_a = rng.random(n) < _logistic(df["eta"].to_numpy())
    u = rng.random(n)
    status = np.full(n, "ok", dtype=object)
    status[u < params.p_api_error] = "api_error"
    status[(u >= params.p_api_error) & (u < params.p_api_error + params.p_refusal)] = "refusal"
    ok = status == "ok"
    choice = np.where(pick_a, "A", "B").astype(object)
    choice[~ok] = None
    df["choice"] = choice
    df["chosen_nationality"] = np.where(ok, np.where(pick_a, df["nationality_a"], df["nationality_b"]), None)
    df["chosen_cv"] = np.where(ok, np.where(pick_a, df["cv_a"], df["cv_b"]), None)
    df["run_id"] = design.run_id
    df["record_id"] = [f"{design.run_id}-fc-{k:08d}" for k in range(n)]
    df["is_mock"] = is_mock
    df["provider"] = "simulator"
    df["model_id"] = "sim/" + df["model_alias"]
    conf = np.clip(np.round(rng.normal(70, 10, n)), 0, 100)
    conf[~ok] = np.nan
    df["confidence"] = conf
    df["reason"] = "simulated"
    df["parse_status"] = status
    df["refusal"] = status == "refusal"
    df["api_error"] = status == "api_error"
    df["execution_index"] = rng.permutation(n)
    df["seed"] = [_seed(t, r) for t, r in zip(df["quad_id"], df["repetition"])]
    df["model_revision"] = "sim-rev-0001"
    df["user_prompt_version"] = df["prompt_condition"] + "_" + df["prompt_variant"] + "@sim-v1"
    df["prompt_sha256"] = [f"{zlib.crc32(t.encode()):08x}" for t in df["trial_id"]]
    _parser_diagnostics(df)
    return df[list(FORCED_CHOICE_COLUMNS) + ["execution_index", "seed", "model_revision", "repetition",
                                             "prompt_sha256", "user_prompt_version", "n_json_objects", "near_miss"]]


def simulate_principle(design: SimDesign, params: SimParams, seed: int = 0,
                       is_mock: bool = True, rng: np.random.Generator | None = None) -> pd.DataFrame:
    """Simulate ``principle.csv`` (A11): keyed target items + control items x contexts x replicates."""
    rng = rng if rng is not None else np.random.default_rng(seed)
    contexts = design.principle_contexts or (("generic",) + tuple(design.occupations))
    rows = []
    for m in design.models:
        p_end = params.principle_endorse_prob.get(m, 0.95)
        p_ctl = params.principle_control_accuracy.get(m, 0.95)
        for it in PRINCIPLE_ITEMS:
            for ctx in contexts:
                for r in range(design.principle_repetitions):
                    if it["item_type"] == "control":
                        correct = rng.random() < p_ctl
                        ans = it["expected_answer"] if correct else ("no" if it["expected_answer"] == "yes" else "yes")
                        endorse = None
                    else:
                        endorse = "yes" if rng.random() < p_end else "no"
                        ans = endorse if it["keying"] == "pro" else ("no" if endorse == "yes" else "yes")
                    agree = float(np.clip(round(rng.normal(85 if ans == "yes" else 20, 10)), 0, 100))
                    rows.append((m, it["item_id"], it["keying"], it["item_type"], ctx, r + 1, ans, endorse,
                                 agree, it["expected_answer"]))
    df = pd.DataFrame(rows, columns=["model_alias", "item_id", "keying", "item_type", "context",
                                     "repetition", "answer", "endorses_neutrality", "agreement",
                                     "expected_answer"])
    n = len(df)
    df["run_id"] = design.run_id
    df["record_id"] = [f"{design.run_id}-pr-{k:08d}" for k in range(n)]
    df["is_mock"] = is_mock
    df["provider"] = "simulator"
    df["model_id"] = "sim/" + df["model_alias"]
    df["reason"] = "simulated"
    df["parse_status"] = "ok"
    df["refusal"] = False
    df["api_error"] = False
    df["probe_id"] = df["item_id"]
    df["occupation"] = df["context"].where(df["context"] != "generic", None)
    df["prompt_variant"] = None
    df["execution_index"] = rng.permutation(n)
    df["model_revision"] = "sim-rev-0001"
    df["seed"] = [_seed(m, i, c, r) for m, i, c, r in zip(df["model_alias"], df["item_id"], df["context"],
                                                           df["repetition"])]
    df["user_prompt_version"] = "principle_probe@sim-v1"
    df["prompt_sha256"] = [f"{zlib.crc32(f'{i}|{c}'.encode()):08x}" for i, c in zip(df["item_id"], df["context"])]
    _parser_diagnostics(df)
    return df[list(PRINCIPLE_COLUMNS) + ["seed", "user_prompt_version", "prompt_sha256", "n_json_objects",
                                         "near_miss", "expected_answer", "probe_id", "occupation", "prompt_variant",
                                         "execution_index", "model_revision"]]


def simulate_all(design: SimDesign, params: SimParams, seed: int = 0, is_mock: bool = True,
                 forced_choice: bool = True, principle: bool = True) -> dict[str, pd.DataFrame | None]:
    """Simulate all three processed tables with shared base-CV effects."""
    rng = np.random.default_rng(seed)
    cvs = _cv_table(design, params, rng)
    out: dict[str, pd.DataFrame | None] = {
        "evaluations": simulate_evaluations(design, params, is_mock=is_mock, cvs=cvs, rng=rng),
        "forced_choice": None, "principle": None,
    }
    if forced_choice and design.fc_conditions:
        out["forced_choice"] = simulate_forced_choice(design, params, is_mock=is_mock, cvs=cvs, rng=rng)
    if principle:
        out["principle"] = simulate_principle(design, params, is_mock=is_mock, rng=rng)
    return out


def write_processed(tables: dict[str, pd.DataFrame | None], out_dir: str | Path) -> Path:
    """Write simulated tables as ``evaluations.csv`` etc. into ``out_dir``."""
    d = Path(out_dir)
    d.mkdir(parents=True, exist_ok=True)
    for name, df in tables.items():
        if df is not None:
            df.to_csv(d / f"{name}.csv", index=False)
    return d


__all__ = [
    "NATIONALITIES", "NAT_META", "ARAB_CODES", "ALL_CODES", "FC_CODES", "BASE_COUNTRIES",
    "allocate_base_countries", "PILOT_OCCUPATIONS",
    "MAIN_OCCUPATIONS", "PILOT_TIERS", "MAIN_TIERS", "PRINCIPLE_ITEMS", "SimDesign", "SimParams",
    "make_nationality_effects", "simulate_evaluations", "simulate_forced_choice",
    "simulate_principle", "simulate_all", "write_processed", "replace",
]
