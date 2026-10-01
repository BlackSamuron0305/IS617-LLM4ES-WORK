"""Deterministic trial construction, forced-choice design, seeds and execution order.

Terminology
-----------
trial     one prompt cell: (model, arm, condition, wording variant, stimuli,
          order, item/context). ``trial_id`` hashes exactly those fields, so it is
          stable across runs and independent of seeds and execution order.
call      one repetition of a trial. ``record_id = hash(run_id, trial_id,
          repetition)`` identifies the raw record; resuming skips record_ids that
          already have a record.
quad      forced choice: two different same-occupation, same-tier CVs with the
          same base country (CV1 < CV2; the job ad is located in that country)
          and two nationalities a != b give four prompts, {CV1:a, CV2:b} and
          {CV1:b, CV2:a}, each shown in both orders, all with ONE wording variant.
          ``fc_order = "AB"`` means CV1 is candidate A; "BA" means CV2 is.

Seeds (A17) derive from (model, arm, condition, base CV or CV pair, variant,
repetition, FC order, item, context) and never from nationality or clone type,
so the clones of a base CV share random streams (common random numbers).

Execution order (A5): a seeded shuffle of all calls within each model; models run
one after another, each in one contiguous window. ``execution_index`` is the
position in that planned order.

Forced-choice nationality pairs (A9)
------------------------------------
NONE is excluded (25 levels, 300 pairs). The levels, in a seeded order, are
decomposed into Hamiltonian cycles (Walecki's construction; for an odd number of
levels the cycles partition all pairs). Every cycle contains every level in
exactly two pairs and is connected, so any union of cycles is balanced and
connected. ``n_cycles`` cycles are used, each ``copies`` (c) times, and each
copy goes to a different (occupation, tier) cell, hence to a different CV pair.
When there are at least as many cycle copies as cells, whole cycles are dealt
to cells in rounds that visit every occupation once with rotating tiers, so each
level appears equally often per occupation and per tier whenever the counts
divide evenly (main study: 12 cycles x c=2 over 6 x 3 cells). Otherwise the
pairs are dealt one by one over the cells (pilot). Within a cell, pairs are
spread over its CV pairs. Wording variants are then assigned so that every
nationality gets about 1/K of its quads per variant (``balance_variants``).
Placebo nationalities never enter forced choice.
"""

from __future__ import annotations

import itertools
import random
from collections import Counter, defaultdict, deque
from dataclasses import dataclass, field

from .config import FC_CONDITIONS, INDEPENDENT_CONDITIONS, ExperimentConfig, PrincipleSpec
from .utils import derive_int, sha256_text, stable_hash

PRIMARY_ARM = "primary"


# --------------------------------------------------------------------------- #
# IDs and seeds
# --------------------------------------------------------------------------- #
def make_trial_id(**fields) -> str:
    return "t_" + stable_hash(fields, 16)


def make_record_id(run_id: str, trial_id: str, repetition: int) -> str:
    return "r_" + sha256_text(f"{run_id}|{trial_id}|{repetition}")[:20]


def make_quad_id(**fields) -> str:
    return "q_" + stable_hash(fields, 16)


# --------------------------------------------------------------------------- #
# Data classes
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Trial:
    trial_id: str
    task_type: str                 # independent | forced_choice | principle_probe
    prompt_condition: str          # baseline | neutrality | forced_choice | forced_choice_neutrality | principle_probe
    template_id: str
    model_alias: str
    repetitions: int
    occupation: str | None = None
    prompt_variant: str | None = None
    arm: str = PRIMARY_ARM
    temperature: float | None = None   # None = primary sampling temperature
    stimulus_ids: tuple[str, ...] = ()
    base_cv_ids: tuple[str, ...] = ()
    nationalities: tuple[str, ...] = ()
    clone_type: str | None = None
    qualification_tier: str | None = None
    fc_order: str | None = None
    quad_id: str | None = None
    item_id: str | None = None
    context: str | None = None
    base_country: str | None = None    # base country of the CV(s); not part of trial_id (implied by the CVs)

    def seed_key(self) -> tuple:
        """Everything that defines the random stream EXCEPT nationality / clone type (A17)."""
        cvs = tuple(sorted(self.base_cv_ids))
        return (self.model_alias, self.arm, self.prompt_condition, cvs, self.prompt_variant, self.fc_order,
                self.item_id, self.context)


@dataclass(frozen=True)
class Call:
    trial: Trial
    repetition: int                # 1..R
    record_id: str
    seed: int
    execution_index: int = -1


@dataclass(frozen=True)
class StimulusRef:
    """One (CV row, nationality row, clone type) combination; rendered on demand."""

    stimulus_id: str
    cv_id: str
    occupation: str
    tier: str
    clone_type: str
    nationality_code: str
    pilot: bool = False
    base_country: str = ""         # the CV's base country (ISO3); host_national = nationality_code == base_country


@dataclass(frozen=True)
class Quad:
    occupation: str
    tier: str
    cv1: str
    cv2: str
    nat_a: str
    nat_b: str
    variant: str
    copy: int
    base_country: str = ""         # shared by cv1 and cv2


@dataclass
class TrialPlan:
    trials: list[Trial]
    fc_design: list[Quad] = field(default_factory=list)
    fc_cells: dict[tuple[str, str], list[tuple[str, str]]] = field(default_factory=dict)


def call_seed(master_seed: int, trial: Trial, repetition: int) -> int:
    return derive_int(master_seed, "call", *trial.seed_key(), repetition)


# --------------------------------------------------------------------------- #
# Nationality pair designs
# --------------------------------------------------------------------------- #
def walecki_cycles(labels: list[str]) -> list[list[tuple[str, str]]]:
    """Hamiltonian decomposition of the complete graph on ``labels``.

    Odd n: (n-1)/2 edge-disjoint Hamiltonian cycles covering every pair once.
    Even n: a dummy vertex is added and its edges dropped, giving n/2 paths in
    which every label still appears in exactly n-1 pairs overall.
    """
    labels = list(labels)
    if len(labels) < 3:
        raise ValueError("need at least three nationality levels for a cycle design")
    dummy = None
    if len(labels) % 2 == 0:
        dummy = "__dummy__"
        labels = labels + [dummy]
    inf, ring = labels[0], labels[1:]
    two_m = len(ring)
    m = two_m // 2
    cycles = []
    for i in range(m):
        path = []
        for t in range(two_m):
            off = (t + 1) // 2 if t % 2 == 1 else -(t // 2)
            path.append(ring[(i + off) % two_m])
        verts = [inf, *path, inf]
        edges = [tuple(sorted((verts[j], verts[j + 1]))) for j in range(len(verts) - 1)]
        cycles.append([e for e in edges if dummy not in e])
    return cycles


def pair_degrees(pairs) -> Counter:
    c: Counter = Counter()
    for a, b in pairs:
        c[a] += 1
        c[b] += 1
    return c


def is_connected(codes: list[str], pairs) -> bool:
    if not codes:
        return True
    adj = defaultdict(set)
    for a, b in pairs:
        adj[a].add(b)
        adj[b].add(a)
    seen = {codes[0]}
    q = deque([codes[0]])
    while q:
        for nb in adj[q.popleft()]:
            if nb not in seen:
                seen.add(nb)
                q.append(nb)
    return seen == set(codes)


def _cell_rounds(occupations: list[str], tiers: list[str], cells: set[tuple[str, str]]):
    """Infinite cell sequence: each round visits every occupation once, tiers rotate."""
    r = 0
    while True:
        for o_idx, occ in enumerate(occupations):
            for shift in range(len(tiers)):
                t = tiers[(o_idx + r + shift) % len(tiers)]
                if (occ, t) in cells:
                    yield (occ, t)
                    break
        r += 1


def fc_design(codes: list[str], cells: dict[tuple[str, str], list[tuple[str, str]]], occupations: list[str],
              tiers: list[str], n_cycles, copies: int, variants: list[str], seed: int) -> list[Quad]:
    """Assign nationality pairs to CV pairs and wording variants (see module docstring)."""
    if not cells:
        return []
    labels = sorted(codes)
    random.Random(derive_int(seed, "fc_labels")).shuffle(labels)
    cycles = walecki_cycles(labels)
    n_sel = len(cycles) if n_cycles == "all" else int(n_cycles)
    if not 1 <= n_sel <= len(cycles):
        raise ValueError(f"n_cycles must be between 1 and {len(cycles)} for {len(codes)} levels")
    cycles = cycles[:n_sel]
    cell_set = set(cells)
    n_cells = len(cell_set)
    units = [(ci, j) for j in range(copies) for ci in range(n_sel)]
    gen = _cell_rounds(occupations, tiers, cell_set)

    assigned: list[tuple[tuple[str, str], tuple[str, str], int]] = []  # (cell, pair, copy)
    if len(units) >= n_cells:  # whole cycles per cell
        seq = [next(gen) for _ in units]
        for u, (ci, j) in enumerate(units):
            for pair in cycles[ci]:
                assigned.append((seq[u], pair, j))
    else:  # deal pairs one by one over the cells
        order = [next(gen) for _ in range(n_cells)]
        k = 0
        for ci, j in units:
            for pair in cycles[ci]:
                assigned.append((order[k % n_cells], pair, j))
                k += 1
    # every copy of a pair must sit in a different cell (hence a different CV pair)
    order_all = sorted(cell_set)
    used: dict[tuple[str, str], set] = defaultdict(set)
    fixed = []
    for cell, pair, j in assigned:
        if cell in used[pair]:
            free = [c for c in order_all if c not in used[pair]]
            if not free:
                raise ValueError("copies exceed the number of cells; lower forced_choice copies")
            cell = free[0]
        used[pair].add(cell)
        fixed.append((cell, pair, j))

    quads: list[Quad] = []
    per_cell: dict[tuple[str, str], list] = defaultdict(list)
    for cell, pair, j in fixed:
        per_cell[cell].append((pair, j))
    for cell in sorted(per_cell):
        occ, tier = cell
        pairs_cv = cells[cell]
        cv_off = random.Random(derive_int(seed, "fc_cell", occ, tier)).randrange(len(pairs_cv))
        for idx, ((a, b), j) in enumerate(per_cell[cell]):
            cv1, cv2 = pairs_cv[(idx + cv_off) % len(pairs_cv)]
            quads.append(Quad(occ, tier, cv1, cv2, a, b, variants[0], j))
    return balance_variants(quads, variants, seed)


def balance_variants(quads: list[Quad], variants: list[str], seed: int) -> list[Quad]:
    """Assign wording variants so that every nationality gets ~1/K of its quads per
    variant, and variants are balanced overall (review M13).

    Start from a Latin rotation (variant = position mod K along the cycle order) and
    improve by deterministic local search on
        sum_levels sum_variants (count - share)^2  +  sum_variants (total - N/K)^2.
    All four prompts of a quad share its variant.
    """
    k = len(variants)
    if k == 1 or not quads:
        return [Quad(**{**q.__dict__, "variant": variants[0]}) for q in quads]
    off = random.Random(derive_int(seed, "fc_variants")).randrange(k)
    assign = [(i + off) % k for i in range(len(quads))]
    deg = Counter()
    for q in quads:
        deg[q.nat_a] += 1
        deg[q.nat_b] += 1
    cnt: dict[str, list[int]] = {n: [0] * k for n in deg}
    tot = [0] * k
    for q, v in zip(quads, assign):
        cnt[q.nat_a][v] += 1
        cnt[q.nat_b][v] += 1
        tot[v] += 1
    target_tot = len(quads) / k

    def cost_delta(i: int, new: int) -> float:
        q, old = quads[i], assign[i]
        d = 0.0
        for n in (q.nat_a, q.nat_b):
            t = deg[n] / k
            d += (cnt[n][new] + 1 - t) ** 2 - (cnt[n][new] - t) ** 2
            d += (cnt[n][old] - 1 - t) ** 2 - (cnt[n][old] - t) ** 2
        d += (tot[new] + 1 - target_tot) ** 2 - (tot[new] - target_tot) ** 2
        d += (tot[old] - 1 - target_tot) ** 2 - (tot[old] - target_tot) ** 2
        return d

    improved = True
    while improved:
        improved = False
        for i in range(len(quads)):
            best, best_d = assign[i], -1e-9
            for v in range(k):
                if v != assign[i]:
                    d = cost_delta(i, v)
                    if d < best_d:
                        best, best_d = v, d
            if best != assign[i]:
                q, old = quads[i], assign[i]
                for n in (q.nat_a, q.nat_b):
                    cnt[n][old] -= 1
                    cnt[n][best] += 1
                tot[old] -= 1
                tot[best] += 1
                assign[i] = best
                improved = True
    # Phase 2: swap the variants of two quads (keeps the overall totals) when that
    # lowers the per-level cost; only quads touching an unbalanced level are tried.
    def level_cost(nodes) -> float:
        return sum((cnt[n][v] - deg[n] / k) ** 2 for n in set(nodes) for v in range(k))

    def apply(i: int, new: int) -> None:
        q, old = quads[i], assign[i]
        for n in (q.nat_a, q.nat_b):
            cnt[n][old] -= 1
            cnt[n][new] += 1
        assign[i] = new

    changed = True
    while changed:
        changed = False
        unbalanced = sorted(n for n in deg if max(cnt[n]) - min(cnt[n]) > 1)
        for n in unbalanced:
            if max(cnt[n]) - min(cnt[n]) <= 1:
                continue
            hi, lo = cnt[n].index(max(cnt[n])), cnt[n].index(min(cnt[n]))
            done = False
            for i in [i for i, q in enumerate(quads) if n in (q.nat_a, q.nat_b) and assign[i] == hi]:
                for j in [j for j in range(len(quads)) if assign[j] == lo and n not in (quads[j].nat_a, quads[j].nat_b)]:
                    nodes = [quads[i].nat_a, quads[i].nat_b, quads[j].nat_a, quads[j].nat_b]
                    before = level_cost(nodes)
                    apply(i, lo)
                    apply(j, hi)
                    if level_cost(nodes) < before - 1e-9:
                        done = changed = True
                        break
                    apply(j, lo)
                    apply(i, hi)
                if done:
                    break
    return [Quad(**{**q.__dict__, "variant": variants[v]}) for q, v in zip(quads, assign)]


# --------------------------------------------------------------------------- #
# Trial construction
# --------------------------------------------------------------------------- #
def select_cvs(cfg: ExperimentConfig, stimuli: list[StimulusRef], occupations: list[str]) -> dict[str, list[tuple[str, str]]]:
    """{occupation: [(cv_id, tier), ...]} for the configured base CVs."""
    info = {s.cv_id: (s.occupation, s.tier, s.pilot) for s in stimuli}
    out = {}
    for occ in occupations:
        avail = sorted(cv for cv, (o, _, _) in info.items() if o == occ)
        if cfg.base_cvs == "all":
            chosen = avail
        elif cfg.base_cvs == "pilot":
            chosen = [cv for cv in avail if info[cv][2]]
        else:
            chosen = list(cfg.base_cvs.get(occ, []))
            missing = set(chosen) - set(avail)
            if missing:
                raise KeyError(f"base CVs not in stimuli/cvs.csv: {sorted(missing)}")
        if not chosen:
            raise ValueError(f"no base CVs selected for occupation {occ}")
        out[occ] = [(cv, info[cv][1]) for cv in chosen]
    return out


def _ie_trial(model, cond, variant, occ, s: StimulusRef, tier, reps, arm=PRIMARY_ARM, temperature=None) -> Trial:
    fields = dict(model_alias=model, arm=arm, prompt_condition=cond, prompt_variant=variant,
                  task_type="independent", stimulus_ids=[s.stimulus_id])
    return Trial(trial_id=make_trial_id(**fields), task_type="independent", prompt_condition=cond,
                 template_id=f"{cond}_{variant}", model_alias=model, repetitions=reps, occupation=occ,
                 prompt_variant=variant, arm=arm, temperature=temperature, stimulus_ids=(s.stimulus_id,),
                 base_cv_ids=(s.cv_id,), nationalities=(s.nationality_code,), clone_type=s.clone_type,
                 qualification_tier=tier, base_country=s.base_country or None)


def build_trials(cfg: ExperimentConfig, stimuli: list[StimulusRef], occupations: list[str],
                 nationality_codes: list[str], principle: PrincipleSpec | None = None,
                 all_occupations: list[str] | None = None, placebo_codes: set[str] | None = None) -> TrialPlan:
    """Build every trial. Placebo nationalities (H5) are used ONLY in baseline
    independent evaluation of the primary arm; never in neutrality, forced choice,
    the positive control or a robustness arm."""
    placebo_codes = set(placebo_codes or ())
    core_codes = [c for c in nationality_codes if c not in placebo_codes]
    baseline_codes = core_codes + ([c for c in nationality_codes if c in placebo_codes]
                                   if cfg.include_placebo else [])
    index = {(s.cv_id, s.nationality_code, s.clone_type): s for s in stimuli}
    cvs_by_occ = select_cvs(cfg, stimuli, occupations)
    for occ, cvs in cvs_by_occ.items():
        for cv, _ in cvs:
            for code in baseline_codes:
                if (cv, code, "counterfactual") not in index:
                    raise KeyError(f"no stimulus for CV {cv} x nationality {code}")

    enabled = cfg.enabled_conditions()
    variants = list(cfg.prompt_variants)
    trials: list[Trial] = []

    # ---- forced-choice design (model independent) ----
    fc_conds = [c for c in FC_CONDITIONS if c in enabled]
    quads: list[Quad] = []
    cells: dict[tuple[str, str], list[tuple[str, str]]] = {}
    if fc_conds:
        fc_codes = [c for c in core_codes if c not in cfg.forced_choice_design.exclude_nationalities]
        tiers = list(cfg.forced_choice_design.tiers)
        base_of = {s.cv_id: s.base_country for s in stimuli}
        for occ in occupations:
            for tier in tiers:
                tier_cvs = sorted(cv for cv, t in cvs_by_occ[occ] if t == tier)
                # a forced-choice pair shares occupation, tier AND base country (the ad is located there)
                pairs = [(a, b) for a, b in itertools.combinations(tier_cvs, 2) if base_of[a] == base_of[b]]
                if pairs:
                    cells[(occ, tier)] = pairs
        pd = cfg.forced_choice_design.nationality_pairs
        quads = fc_design(fc_codes, cells, occupations, tiers, pd.n_cycles, pd.copies, variants, cfg.seed)
        quads = [Quad(**{**q.__dict__, "base_country": base_of[q.cv1]}) for q in quads]

    for model in cfg.models:
        # ---- independent evaluation, primary arm ----
        for cond in INDEPENDENT_CONDITIONS:
            if cond not in enabled:
                continue
            reps = cfg.repetitions(cond)
            for occ in occupations:
                for cv, tier in cvs_by_occ[occ]:
                    for variant in variants:
                        for code in (baseline_codes if cond == "baseline" else core_codes):
                            s = index[(cv, code, "counterfactual")]
                            trials.append(_ie_trial(model, cond, variant, occ, s, tier, reps))
                        if cond == "baseline" and cfg.positive_control:
                            s = index[(cv, "NONE", "positive_control")]
                            trials.append(_ie_trial(model, cond, variant, occ, s, tier, reps))
        # ---- robustness arms (counterfactual clones only) ----
        for arm in cfg.robustness_arms:
            if arm.models != "all" and model not in arm.models:
                continue
            arm_variants = variants if arm.prompt_variants == "all" else list(arm.prompt_variants)
            for cond in arm.conditions:
                for occ in occupations:
                    for cv, tier in cvs_by_occ[occ]:
                        for variant in arm_variants:
                            for code in core_codes:
                                s = index[(cv, code, "counterfactual")]
                                trials.append(_ie_trial(model, cond, variant, occ, s, tier, arm.repetitions,
                                                        arm=arm.arm_id, temperature=arm.temperature))
        # ---- forced-choice quads ----
        for cond in fc_conds:
            for q in quads:
                trials.extend(_quad_trials(model, cond, q, index, cfg.repetitions(cond)))
        # ---- principle probe ----
        if "principle_probe" in enabled:
            if principle is None:
                raise ValueError("principle_probe enabled but no principle items loaded")
            pcfg = cfg.conditions.principle_probe
            contexts = (["generic", *(all_occupations or occupations)] if pcfg.contexts == "all"
                        else list(pcfg.contexts))
            items = principle.items if pcfg.items == "all" else [principle.by_id()[i] for i in pcfg.items]
            for ctx in contexts:
                for item in items:
                    fields = dict(model_alias=model, prompt_condition="principle_probe", task_type="principle_probe",
                                  item_id=item.item_id, context=ctx)
                    trials.append(Trial(
                        trial_id=make_trial_id(**fields), task_type="principle_probe",
                        prompt_condition="principle_probe", template_id="principle_probe", model_alias=model,
                        repetitions=pcfg.repetitions, occupation=None if ctx == "generic" else ctx,
                        item_id=item.item_id, context=ctx))

    ids = [t.trial_id for t in trials]
    if len(ids) != len(set(ids)):
        raise RuntimeError("duplicate trial ids generated (design error)")
    return TrialPlan(trials=trials, fc_design=quads, fc_cells=cells)


def _quad_trials(model, cond, q: Quad, index, reps) -> list[Trial]:
    quad_id = make_quad_id(model_alias=model, prompt_condition=cond, occupation=q.occupation,
                           cvs=[q.cv1, q.cv2], nationalities=sorted([q.nat_a, q.nat_b]), variant=q.variant)
    out = []
    for n1, n2 in ((q.nat_a, q.nat_b), (q.nat_b, q.nat_a)):  # nationality swap
        s1 = index[(q.cv1, n1, "counterfactual")]
        s2 = index[(q.cv2, n2, "counterfactual")]
        if s1.base_country != s2.base_country:
            raise ValueError(f"forced-choice pair {q.cv1}/{q.cv2} has two base countries")
        for order in ("AB", "BA"):  # position swap
            sa, sb = (s1, s2) if order == "AB" else (s2, s1)
            fields = dict(model_alias=model, prompt_condition=cond, prompt_variant=q.variant,
                          task_type="forced_choice",
                          stimulus_ids=[sa.stimulus_id, sb.stimulus_id], fc_order=order)
            out.append(Trial(
                trial_id=make_trial_id(**fields), task_type="forced_choice", prompt_condition=cond,
                template_id=f"{cond}_{q.variant}", model_alias=model, repetitions=reps, occupation=q.occupation,
                prompt_variant=q.variant, stimulus_ids=(sa.stimulus_id, sb.stimulus_id),
                base_cv_ids=(sa.cv_id, sb.cv_id), nationalities=(sa.nationality_code, sb.nationality_code),
                clone_type="counterfactual", qualification_tier=q.tier, fc_order=order, quad_id=quad_id,
                base_country=s1.base_country or None))
    return out


# --------------------------------------------------------------------------- #
# Calls and execution order (A5)
# --------------------------------------------------------------------------- #
def expand_calls(trials: list[Trial], run_id: str, master_seed: int, model_order: list[str]) -> list[Call]:
    by_model: dict[str, list[Call]] = defaultdict(list)
    for t in trials:
        for r in range(1, t.repetitions + 1):
            by_model[t.model_alias].append(Call(t, r, make_record_id(run_id, t.trial_id, r),
                                                call_seed(master_seed, t, r)))
    ordered: list[Call] = []
    for m in [*model_order, *sorted(set(by_model) - set(model_order))]:
        group = by_model.get(m, [])
        random.Random(derive_int(master_seed, "execution_order", m)).shuffle(group)
        ordered.extend(group)
    return [Call(c.trial, c.repetition, c.record_id, c.seed, i) for i, c in enumerate(ordered)]


def fc_design_summary(quads: list[Quad]) -> dict:
    pairs = [(q.nat_a, q.nat_b) for q in quads]
    codes = sorted({c for p in pairs for c in p})
    deg = pair_degrees(pairs)
    per_level: dict[str, Counter] = defaultdict(Counter)
    variants = sorted({q.variant for q in quads})
    for q in quads:
        per_level[q.nat_a][q.variant] += 1
        per_level[q.nat_b][q.variant] += 1
    spread = [max(c.values()) - min(c.get(v, 0) for v in variants) for c in per_level.values()] or [0]
    return {
        "variant_spread_per_level": max(spread),
        "n_quads": len(quads),
        "n_distinct_pairs": len(set(pairs)),
        "levels": codes,
        "appearances_per_level": sorted(set(deg.values())),
        "connected": is_connected(codes, pairs),
        "quads_per_variant": dict(Counter(q.variant for q in quads)),
        "quads_per_cell": {f"{o}/{t}": n for (o, t), n in sorted(Counter((q.occupation, q.tier) for q in quads).items())},
        "quads_per_base_country": dict(sorted(Counter(q.base_country for q in quads).items())),
    }


def all_stimuli(cvs: list[dict], nationality_codes: list[str], positive_control: bool = True) -> list[StimulusRef]:
    """Every CV row x nationality row combination (+ one positive control per CV)."""
    from .stimuli.render import COUNTERFACTUAL, POSITIVE_CONTROL, stimulus_id

    out = []
    for cv in cvs:
        pilot = bool(cv.get("pilot"))
        base = cv.get("base_country") or ""
        for code in nationality_codes:
            out.append(StimulusRef(stimulus_id(cv["cv_id"], code), cv["cv_id"], cv["occupation"],
                                   cv["qualification_tier"], COUNTERFACTUAL, code, pilot, base))
        if positive_control:
            out.append(StimulusRef(stimulus_id(cv["cv_id"], "NONE", POSITIVE_CONTROL), cv["cv_id"],
                                   cv["occupation"], cv["qualification_tier"], POSITIVE_CONTROL, "NONE", pilot,
                                   base))
    return out
