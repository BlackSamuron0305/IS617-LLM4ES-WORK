"""End-to-end analysis: ``run_analysis(processed_dir, out_dir, config=None)``.

Implements analysis/statistical_analysis_plan.md (hypotheses per research/hypotheses.md and
preregistration.md). Produces CSV + LaTeX tables, PDF + PNG figures,
``variance_components.json`` (input for the power analysis) and ``summary.md`` listing every
output together with the provenance of the run. Contains no interpretation.

BLIND BY DEFAULT (A15, review H1). Unless ``config["unblind"] is True`` the run outputs only
design checks, parse / refusal diagnostics, manipulation checks (positive control, tiers), scale
use, forced-choice position diagnostics, principle-probe summaries, text-flag base rates and
variance components: no per-origin means, contrasts, rankings, sigma_A or nationality tests.
Unblinding real data requires a frozen preregistration (see ``settings.py``); every unblinded run
is logged. Confirmatory settings come from ``config/analysis_settings.csv``; overriding any
of them stamps every output "EXPLORATORY OVERRIDE".

HOST-NATIONAL STATUS (setting 2026-10-01). Every CV is set in one Arab League base country and one
Arab clone per CV is a host national. The primary within-Arab and Arab-vs-benchmark estimators
include a common host-national fixed effect (``core.host_fit``; delta(n), sigma_A and the contrasts
are net of it); the estimated host effect is a secondary, descriptive output (``host_effect.csv``,
unblinded only); the host-exclusion sensitivity (HX) is a required check of the 'robust' label;
forced choice adds host_A - host_B to the Bradley-Terry model and reports a host-free sensitivity.
"""

from __future__ import annotations

import dataclasses
import json
import platform
import warnings
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

from . import figures as figs
from .bradley_terry import arab_centred, bt_analysis, cv_multiplicities, fit_bt, implied_from_fc, prepare_fc
from .core import (
    aggregate_stimulus,
    build_cell,
    compare_sigma,
    contrast_values,
    heterogeneity,
    host_adjust,
    host_fit,
    hotelling_test,
    nationality_order,
    origin_deviations,
    profile_interaction_test,
    replicate_array,
    sigma_within_groups,
    stratified_bootstrap_indices,
    t_summary,
    tost,
    twoway_stats,
    variance_components,
)
from .descriptives import (
    balance_checks,
    design_table,
    differential_missingness,
    fc_diagnostics,
    missingness_by_nationality,
    positive_control,
    scale_use,
    status_rates,
    text_flag_rates,
    tier_check,
)
from .hypotheses import (
    INCOME_ORDER,
    boot_inflation,
    decision_label,
    h1c_equality,
    h1d_gradient,
    load_covariates,
    profile_concordance,
    h1e_label,
    rq1_headline,
    rq1_label,
    rq3_label,
)
from .multiplicity import adjust_within, bh
from .principle import classify, endorsement
from .robustness import manski_table, robust_labels, run_robustness
from .schema import ARAB_LABEL, MOCK_BANNER, PLACEBO, any_mock, load_processed, mixed_mock
from .schema import all_mock as _all_mock
from .sensitivity import cv_fe_ols, gee_interview, mixedlm_rep
from .settings import (
    OVERRIDE_BANNER,
    PARSE_BANNER,
    UNBLIND_LOG,
    append_unblinding_log,
    blind_requested,
    check_unblinding,
    provenance,
    resolve_config,
    unblinding_entry,
)
from .tables import write_csv, write_latex

OUTCOMES = ("overall_fit", "interview")
BENCHMARKS = ("DEU", "POL", "TUR", "NONE")
REFERENCE = "DEU"
BLIND_BANNER = "BLIND MODE (A15): no per-origin means, contrasts, rankings or nationality tests"


def _default_config() -> dict:
    """Operational defaults merged with config/analysis_settings.csv (for inspection)."""
    return resolve_config(None)[0]


class _Outputs:
    def __init__(self, out: Path, banners: list[str]):
        self.out, self.banners = out, banners
        self.items: list[tuple[str, str]] = []

    @property
    def mock(self):             # figures accept a list of banners
        return self.banners

    def csv(self, df: pd.DataFrame, name: str, desc: str) -> None:
        p = write_csv(df, self.out / "tables" / f"{name}.csv", self.banners)
        self.items.append((p.relative_to(self.out).as_posix(), desc))

    def tex(self, df: pd.DataFrame, name: str, desc: str, caption: str, digits: int = 2) -> None:
        p = write_latex(df, self.out / "tables" / f"{name}.tex", self.banners, caption, label=f"tab:{name}",
                        digits=digits)
        self.items.append((p.relative_to(self.out).as_posix(), desc))

    def fig(self, paths: list[Path], desc: str) -> None:
        for p in paths:
            self.items.append((p.relative_to(self.out).as_posix(), desc))


# =========================================================================== #
def _refuse_mode_mixing(out: Path, blind: bool) -> None:
    """Refuse to write blind output over unblinded output (or vice versa) in one directory.

    A blind run also refuses a non-empty output directory without summary.md: it may hold stale
    per-origin tables from a crashed unblinded run (review round 2, N1e).
    """
    summary = out / "summary.md"
    if not summary.exists():
        if blind and out.exists() and any(p.is_file() for p in out.rglob("*")):
            raise RuntimeError(
                f"{out} is not empty but has no summary.md (possibly stale unblinded output from an interrupted "
                "run); refusing to write blind output into it. Use an empty --out-dir or remove the directory.")
        return
    text = summary.read_text(encoding="utf-8")
    previous_blind = "blind mode: True" in text
    if ("blind mode: " in text) and previous_blind != blind:
        raise RuntimeError(
            f"{out} already holds {'blind' if previous_blind else 'UNBLINDED'} output; refusing to write "
            f"{'blind' if blind else 'unblinded'} output into the same directory. Use a different --out-dir."
        )


def _exploratory_parse(processed_dir) -> str | None:
    """Reason string if the processed tables come from an exploratory re-parse (review round 2, N5)."""
    d = Path(processed_dir)
    if d.name.endswith("__exploratory"):
        return f"processed directory name ends with '__exploratory' ({d.name})"
    ps = d / "parse_summary.json"
    if ps.exists():
        try:
            mode = json.loads(ps.read_text(encoding="utf-8")).get("parse_mode")
        except (json.JSONDecodeError, OSError):
            mode = None
        if str(mode).lower() == "exploratory":
            return "parse_summary.json: parse_mode = exploratory"
    return None


def run_analysis(processed_dir, out_dir, config: dict | None = None, *, root=None) -> dict:
    """Run the pre-registered analysis (blind subset unless ``config["unblind"] is True``).

    ``root`` is the project root (CLI ``--root``); default: the repository that contains this package.
    The confirmatory config and the unblinding log are always taken from / written to that root.
    Returns a dict with ``mock``, ``blind``, ``outputs`` (relative paths), ``notes``,
    ``results`` (DataFrames), ``provenance`` and the merged ``config``.
    """
    cfg, info = resolve_config(config, root)
    root = info["root"]
    out = Path(out_dir)
    tables = load_processed(processed_dir)
    mock, allmock = any_mock(tables), _all_mock(tables)
    blind = blind_requested(cfg)
    gate = {"prereg_sha256": None, "freeze_ok": None, "reason": "blind run: no unblinding requested"}
    if not blind:
        gate = check_unblinding(root, allmock)          # raises UnblindingError for real data without freeze
    _refuse_mode_mixing(out, blind)
    (out / "tables").mkdir(parents=True, exist_ok=True)
    (out / "figures").mkdir(parents=True, exist_ok=True)
    xparse = _exploratory_parse(processed_dir)
    banners = (([MOCK_BANNER] if mock else []) + ([OVERRIDE_BANNER] if info["overrides"] else [])
               + ([PARSE_BANNER] if xparse else []))
    O = _Outputs(out, banners)
    prov = provenance(root)
    log_path = root / UNBLIND_LOG
    notes: list[str] = []
    if xparse:
        notes.append(f"EXPLORATORY PARSE: {xparse}. Every output is exploratory.")
    if info["overrides"]:
        notes.append(f"EXPLORATORY OVERRIDE: confirmatory setting(s) changed or confirmatory file not committed: "
                     f"{info['overrides']}")
    if mixed_mock(tables):
        notes.append("WARNING: mock and non-mock rows are mixed in the input; everything is labelled as mock "
                     "and unblinding requires a frozen preregistration. Real and mock data must never be pooled.")
    if not cfg.get("sesoi_is_final", False):
        notes.append(f"SESOI values {cfg['sesoi']} are DEFAULTS (OPEN DECISION, A2), not final.")
    if not blind:
        entry = unblinding_entry(info, gate, processed_dir, out, allmock, prov)
        append_unblinding_log(log_path, entry)
        notes.append(f"Unblinded run logged to {log_path} ({gate['reason']}).")

    primary_arm = cfg["primary_arm"]
    ev_all, fc, pr = tables["evaluations"], tables["forced_choice"], tables["principle"]
    ev_prim = ev_all[ev_all["arm"] == primary_arm].copy()
    ev_plc = ev_prim[ev_prim["nationality_group"] == PLACEBO].copy()
    ev = ev_prim[ev_prim["nationality_group"] != PLACEBO].copy()     # placebo never enters main analyses
    arm_evs = {str(a): g[g["nationality_group"] != PLACEBO].copy()
               for a, g in ev_all[ev_all["arm"] != primary_arm].groupby("arm", observed=True)}
    if arm_evs:
        notes.append(f"Confirmatory analyses use arm == '{primary_arm}' only; robustness arms analysed separately: "
                     + ", ".join(f"{a} (n={len(g)})" for a, g in arm_evs.items()))
    if len(ev_plc):
        notes.append(f"{ev_plc['nationality'].nunique()} placebo nationalities ({len(ev_plc)} calls) are used only "
                     "for the placebo comparison (H1e), never in Arab/benchmark contrasts, BT or RQ2-RQ4.")
    rng = np.random.default_rng(cfg["seed"])
    alpha = cfg["alpha"]
    codes = nationality_order(ev)
    models = sorted(ev["model_alias"].astype(str).unique())
    conditions = [c for c in ("baseline", "neutrality") if c in set(ev["prompt_condition"].astype(str))]
    R: dict[str, pd.DataFrame] = {}

    # ------------------------------------------------------------ BLIND-SAFE part
    R["design"] = design_table(ev_all, fc, pr)
    R["balance"] = balance_checks(ev_all, fc)
    st = [status_rates(ev_all, "independent", by=("model_alias", "prompt_condition", "arm"))]
    if fc is not None:
        st.append(status_rates(fc, "forced_choice"))
    if pr is not None:
        st.append(status_rates(pr, "principle_probe", by=("model_alias",)))
    R["status"] = pd.concat(st, ignore_index=True)
    R["diff_missing"] = differential_missingness(ev, codes, cfg["n_perm_secondary"], rng, blind=blind)
    if R["diff_missing"]["flag"].any():
        notes.append("Non-ok share differs across nationalities (p < .05) for: "
                     + ", ".join((R["diff_missing"].loc[R["diff_missing"]["flag"], "model"] + "/"
                                  + R["diff_missing"].loc[R["diff_missing"]["flag"], "condition"]).tolist())
                     + ". P2 rule: the R5 worst-case bounds become a co-primary sensitivity analysis.")
    R["positive_control"] = positive_control(ev, alpha)
    R["tier_check"] = tier_check(ev)
    R["scale_use"] = scale_use(ev)
    if fc is not None:
        R["fc_diagnostics"] = fc_diagnostics(fc)
    if pr is not None:
        R["principle_endorsement"], R["principle_control_items"] = endorsement(
            pr, cfg["n_boot"], rng, alpha, cfg["control_accuracy_threshold"])
        if "expected_answer" not in pr.columns:
            notes.append("principle.csv has no 'expected_answer' column: control-item discrimination "
                         "cannot be scored (SQ1 classification then 'unclassifiable').")
    R["text_flag_rates"], R["text_flag_tests"], R["pronoun_gender"] = text_flag_rates(ev, codes, blind=blind)

    evs = ev.copy()
    evs["interview"] = evs["interview"] * 100.0                   # percentage points
    stims = {k: aggregate_stimulus(evs, k) for k in OUTCOMES}
    cells = {}
    for k in OUTCOMES:
        for m in models:
            for p in conditions:
                try:
                    cells[(m, p, k)] = build_cell(stims[k], m, p, k, codes)
                except ValueError:
                    continue
    small = sorted({c.n_cv for c in cells.values() if c.n_cv < cfg["min_cv_warning"]})
    if small:
        notes.append(f"Only {small} base CVs in some cells: CV-clustered inference is fragile with so few "
                     "independent units (pilot scale).")
    n_imp = sum(c.n_wording_imputed for c in cells.values() if c.Y is not None)
    if n_imp:
        notes.append(f"{n_imp} (CV, nationality, wording) stimulus cells had no valid replicate and were imputed "
                     "additively within CV before averaging over wordings (review M15).")
    vc_rows, vc_up = [], []
    for (m, p, k), cell in cells.items():
        rep = replicate_array(evs, m, p, k, cell.cvs, cell.codes, flatten_variants=False)
        vc_rows.append(dict(model=m, condition=p, outcome=k, **variance_components(cell, rep)))
        vc_up.append(dict(model=m, condition=p, outcome=k, **_vc_upper(cell, rep, cfg["n_boot_vc"], rng)))
    R["variance_components"] = pd.DataFrame(vc_rows)
    R["variance_components_upper80"] = pd.DataFrame(vc_up)
    _write_vc_json(out, O, R["variance_components"], R["variance_components_upper80"], ev, cfg, mock, blind,
                   processed_dir)

    if blind:
        _write_tables(O, R, blind=True)
        if cfg["make_figures"]:
            O.fig(figs.status_table_figure(R["status"], out / "figures" / "response_status", O.mock),
                  "Refusal / error / parse-failure table figure")
        _write_summary(out, O, cfg, info, gate, prov, notes, mock, blind, processed_dir, tables, log_path)
        return {"mock": mock, "blind": True, "outputs": [p for p, _ in O.items], "notes": notes, "results": R,
                "config": cfg, "provenance": prov}

    # ------------------------------------------------------------ UNBLINDED
    conf_c, neu_c = cfg["confirmatory_condition"], cfg["neutrality_condition"]
    if conf_c not in conditions:
        notes.append(f"Confirmatory condition '{conf_c}' absent: confirmatory families are empty.")
    pc = R["positive_control"]
    pc_fit = pc[pc["outcome"] == "overall_fit"].set_index("model") if not pc.empty else pd.DataFrame()
    sesoi = cfg["sesoi"]
    contested = set(cfg.get("contested_codes", []))
    if cfg.get("host_adjustment", "fixed_effect") != "fixed_effect":
        raise ValueError(f"host_adjustment must be 'fixed_effect' (pre-specified), got {cfg.get('host_adjustment')!r}")
    hosts = {key: host_fit(c.Y, c.host(), c.occupations, alpha) for key, c in cells.items()}
    no_host = sorted({f"{m}/{p}" for (m, p, k), h in hosts.items() if not h.identified})
    if no_host:
        notes.append("Host-national effect not identified (no base_country / no host clone) for: "
                     + ", ".join(no_host) + ". These cells are analysed without host adjustment.")
    R["host_effect"] = pd.DataFrame([dict(
        model=m, condition=p, outcome=k, estimand="eta: host-national clone minus same-origin non-host clone "
        "(common across origins; CV and nationality fixed effects)", estimate=h.eta, se=h.se, df=h.df,
        ci_low=h.ci_low, ci_high=h.ci_high, p=h.p, n_cv=h.n_cv, n_host_cells=h.n_host_cells,
        identified=h.identified, status="secondary / descriptive (not confirmatory)")
        for (m, p, k), h in hosts.items()])

    boot_idx = {}
    for k in OUTCOMES:
        cl = [c for (m, p, kk), c in cells.items() if kk == k]
        if cl and all(c.cvs == cl[0].cvs for c in cl):
            boot_idx[k] = stratified_bootstrap_indices(cl[0].occupations, cfg["n_boot"], rng)
        elif cl:
            notes.append(f"{k}: base-CV sets differ across cells; H1c and H3a (shared bootstrap) skipped.")

    # ---------------- RQ1 heterogeneity (22 and 19 origins), per-origin deviations, RQ2 contrasts
    het_rows, dev_rows, con_rows, hot_rows, eff_rows, sub_rows, hx_rows = [], [], [], [], [], [], []
    het_obj = {}
    for (m, p, k), cell in cells.items():
        Y, strata = cell.Y, cell.occupations
        a = cell.cols(cell.arab_codes)
        if a.size < 3:
            continue
        hf, Hc = hosts[(m, p, k)], cell.host()
        Hu = Hc if hf.identified else None
        cal = dict(n_cal=cfg["n_cal"], n_boot_cal=cfg["n_boot_cal"]) if p == conf_c else {}
        sets = {"22": cell.arab_codes, "19": [c for c in cell.arab_codes if c not in contested]}
        for sname, sc in sets.items():
            sci = cell.cols(sc)
            h = heterogeneity(Y[:, sci], sc, strata, cfg["n_perm"], cfg["n_boot"], rng, alpha, sesoi[k],
                              boot_idx=boot_idx.get(k), H=None if Hu is None else Hu[:, sci], **cal)
            het_obj[(m, p, k, sname)] = h
            het_rows.append(dict(
                model=m, condition=p, outcome=k, origins=sname, n_cv=h.n_cv, n_origins=h.n_nat,
                sigma_A=h.sigma_A, sigma2_debiased=h.sigma2_deb, ci_low=h.ncf_ci_low, ci_high=h.ncf_ci_high,
                lower95_one_sided=h.lower95_one_sided, upper95_one_sided=h.upper95_one_sided, sesoi=h.sesoi,
                p_h1a_perm=h.p_perm, p_h1b_equivalence=h.p_equivalence, p_min_effect=h.p_min_effect,
                sf_upper95=h.sf_upper95, sf_crit=h.sf_crit, sf_p=h.sf_p, sf_equivalent=h.sf_equivalent,
                gg_epsilon=h.gg_epsilon, resid_var_min=h.resid_var_min, resid_var_max=h.resid_var_max,
                p_F=h.p_F, sd_plugin=h.sd_plugin, sd_null_mean=h.sd_null_mean, sd_null_q95=h.sd_null_q95,
                range_raw=h.R_raw, range_null_q95=h.R_null_q95, excess_range=h.excess_range,
                boot_ci_low=h.boot_ci_low, boot_ci_high=h.boot_ci_high, ms_res=h.ms_res,
                host_adjusted=h.host_adjusted))
            if sname == "22":
                eff_rows.append(h.effects.assign(model=m, condition=p, outcome=k))
        hot_rows.append(dict(model=m, condition=p, outcome=k, **hotelling_test(host_adjust(Y, Hu, hf)[:, a], strata)))
        od = origin_deviations(Y[:, a], cell.arab_codes, strata, cfg["n_boot"], rng, alpha,
                               H=None if Hu is None else Hu[:, a], host=hf)
        od["q_bh"] = bh(od["p"].to_numpy())
        od["subregion"] = od["nationality"].map(cell.subregions)
        dev_rows.append(od.assign(model=m, condition=p, outcome=k))
        if Hu is not None:
            # HX sensitivity for delta(n): host-national clones removed, no adjustment
            ox = origin_deviations(np.where(Hu > 0, np.nan, Y)[:, a], cell.arab_codes, strata, cfg["n_boot"], rng,
                                   alpha)
            base_c = set(np.asarray(cell.base_countries, dtype=object))
            hx_rows.append(pd.DataFrame({
                "model": m, "condition": p, "outcome": k, "nationality": od["nationality"],
                "is_base_country": od["nationality"].isin(base_c), "delta_adjusted": od["delta"],
                "ci_low_adjusted": od["ci_low"], "ci_high_adjusted": od["ci_high"],
                "delta_host_excluded": ox["delta"], "ci_low_host_excluded": ox["ci_low"],
                "ci_high_host_excluded": ox["ci_high"], "n_cv_host_excluded": ox["n_cv"],
                "difference": ox["delta"] - od["delta"]}))
        sw = sigma_within_groups(Y[:, a], [cell.subregions[c] for c in cell.arab_codes], cfg["n_perm_secondary"],
                                 rng, H=None if Hu is None else Hu[:, a])
        sub_rows.append(dict(model=m, condition=p, outcome=k, sigma_A=het_obj[(m, p, k, "22")].sigma_A, **sw,
                             note="secondary: sigma_A net of the six pre-registered sub-region means"))
        for b in BENCHMARKS:
            if b not in cell.codes:
                continue
            d = contrast_values(Y, a, cell.cols([b]), Hu, hf, strata)
            t = t_summary(d, alpha, strata)
            e = tost(d, sesoi[k], alpha, strata)
            con_rows.append(dict(model=m, condition=p, outcome=k, contrast=f"ARAB_vs_{b}", estimand=f"Delta(A,{b})",
                                 estimate=t.estimate, se=t.se, df=t.df, ci_low=t.ci_low, ci_high=t.ci_high, p=t.p,
                                 ci90_low=e.ci90_low, ci90_high=e.ci90_high, p_tost=e.p_tost,
                                 equivalent=e.equivalent, sesoi=sesoi[k], n_cv=t.n_cv,
                                 label=decision_label(t.ci_low, t.ci_high, e.equivalent, sesoi[k])))
        if "NONE" in cell.codes and REFERENCE in cell.codes:
            t = t_summary(contrast_values(Y, cell.cols([REFERENCE]), cell.cols(["NONE"]), Hu, hf, strata), alpha,
                          strata)
            con_rows.append(dict(model=m, condition=p, outcome=k, contrast="DEU_vs_NONE", estimand="Delta(DEU,NONE)",
                                 estimate=t.estimate, se=t.se, df=t.df, ci_low=t.ci_low, ci_high=t.ci_high,
                                 p=t.p, n_cv=t.n_cv, label="descriptive"))
        unc = [c for c in cell.arab_codes if c not in contested]
        for b in BENCHMARKS:
            if b in cell.codes:
                t = t_summary(contrast_values(Y, cell.cols(unc), cell.cols([b]), Hu, hf, strata), alpha, strata)
                con_rows.append(dict(model=m, condition=p, outcome=k, contrast=f"ARAB19_vs_{b}",
                                     estimand=f"Delta(A19,{b}) [R1]", estimate=t.estimate, se=t.se, df=t.df,
                                     ci_low=t.ci_low, ci_high=t.ci_high, p=t.p, n_cv=t.n_cv, label="sensitivity R1"))
    R["heterogeneity"] = pd.DataFrame(het_rows)
    R["origin_deviations"] = pd.concat(dev_rows, ignore_index=True) if dev_rows else pd.DataFrame()
    R["heterogeneity_effects"] = pd.concat(eff_rows, ignore_index=True) if eff_rows else pd.DataFrame()
    R["h1a_wald_crosscheck"] = pd.DataFrame(hot_rows)
    R["subregion_net"] = pd.DataFrame(sub_rows)
    R["contrasts"] = pd.DataFrame(con_rows)
    R["host_sensitivity_deltas"] = pd.concat(hx_rows, ignore_index=True) if hx_rows else pd.DataFrame()
    R["coefficients"] = _per_origin_vs_benchmarks(cells, cfg, rng, alpha, pc, hosts)

    # ---------------- H1e: placebo floor (baseline, primary arm)
    R["placebo"] = _placebo_comparison(ev_prim, cells, codes, conf_c, cfg, rng, alpha, notes, hosts)

    # ---------------- H1c (models differ) + concordance
    h1c_rows, conc = [], []
    for k in OUTCOMES:
        for p in conditions:
            ks = [(m, p, k) for m in models if (m, p, k, "22") in het_obj]
            if len(ks) >= 2 and k in boot_idx:
                res = h1c_equality({mk[0]: het_obj[mk + ("22",)].sigma2_deb for mk in ks},
                                   {mk[0]: het_obj[mk + ("22",)].boot_sigma2 for mk in ks},
                                   inflate=boot_inflation(cells[ks[0]].occupations),
                                   df2=cells[ks[0]].n_cv - len(set(cells[ks[0]].occupations)))
                h1c_rows.append(dict(condition=p, outcome=k, **res))
                c0 = cells[ks[0]]
                Ys = {mk[0]: host_adjust(cells[mk].Y, cells[mk].host(), hosts[mk])[:, cells[mk].cols(c0.arab_codes)]
                      for mk in ks}
                conc.append(profile_concordance(Ys, c0.occupations, c0.tiers, cfg["concordance_splits"], rng)
                            .assign(condition=p, outcome=k))
    R["h1c"] = pd.DataFrame(h1c_rows)
    R["concordance"] = pd.concat(conc, ignore_index=True) if conc else pd.DataFrame()

    # ---------------- H1d status gradient (ecological, descriptive of structure)
    R["h1d"] = _h1d(cells, conf_c, cfg, notes, alpha, hosts)

    # ---------------- RQ3: neutrality instruction
    rq3_rows, lam_rows = [], []
    if conf_c in conditions and neu_c in conditions:
        for k in OUTCOMES:
            for m in models:
                if (m, conf_c, k) not in cells or (m, neu_c, k) not in cells:
                    continue
                cb, cn = cells[(m, conf_c, k)], cells[(m, neu_c, k)]
                common = [c for c in cb.cvs if c in set(cn.cvs)]
                Yb, Yn = cb.Y[cb.rows(common)], cn.Y[cn.rows(common)]
                strata = cb.occupations[cb.rows(common)]
                a = cb.cols(cb.arab_codes)
                rb, rn = cb.rows(common), cn.rows(common)
                d_b = contrast_values(Yb, a, cb.cols([REFERENCE]), cb.host()[rb], hosts[(m, conf_c, k)], strata, rb)
                d_n = contrast_values(Yn, a, cb.cols([REFERENCE]), cn.host()[rn], hosts[(m, neu_c, k)], strata, rn)
                t = t_summary(d_n - d_b, alpha, strata)
                e = tost(d_n - d_b, sesoi[k], alpha, strata)
                tb_, tn_ = t_summary(d_b, alpha, strata), t_summary(d_n, alpha, strata)
                lab = decision_label(t.ci_low, t.ci_high, e.equivalent, sesoi[k])
                rq3_rows.append(dict(model=m, outcome=k, hypothesis="H3b",
                                     estimand="Delta_neu(A,DEU) - Delta_base(A,DEU)",
                                     estimate=t.estimate, ci_low=t.ci_low, ci_high=t.ci_high, p=t.p,
                                     ci90_low=e.ci90_low, ci90_high=e.ci90_high, equivalent=e.equivalent,
                                     p_tost=e.p_tost, sesoi=sesoi[k], label_unadjusted=lab,
                                     base_estimate=tb_.estimate, base_ci_low=tb_.ci_low, base_ci_high=tb_.ci_high,
                                     neu_ci_low=tn_.ci_low, neu_ci_high=tn_.ci_high,
                                     base_label=_label_of(R["contrasts"], m, conf_c, k, "ARAB_vs_DEU")))
                hb_, hn_ = het_obj.get((m, conf_c, k, "22")), het_obj.get((m, neu_c, k, "22"))
                if hb_ is not None and hn_ is not None and k in boot_idx:
                    dv = hn_.sigma2_deb - hb_.sigma2_deb
                    bdv = hn_.boot_sigma2 - hb_.boot_sigma2
                    se_dv = float(np.nanstd(bdv, ddof=1)) * np.sqrt(boot_inflation(strata))
                    df3 = len(common) - len(set(strata))
                    p3a = float(2 * stats.t.sf(abs(dv / se_dv), max(df3, 1))) if se_dv > 0 else np.nan
                    dsd = hn_.sigma_A - hb_.sigma_A
                    bsd = np.sqrt(np.clip(hn_.boot_sigma2, 0, None)) - np.sqrt(np.clip(hb_.boot_sigma2, 0, None))
                    lo95, hi95 = np.nanpercentile(bsd, [100 * alpha / 2, 100 * (1 - alpha / 2)])
                    lo90, hi90 = np.nanpercentile(bsd, [100 * alpha, 100 * (1 - alpha)])
                    eq = bool(lo90 > -sesoi[k] and hi90 < sesoi[k])
                    lab = decision_label(lo95, hi95, eq, sesoi[k], rejects=bool(p3a < alpha))
                    base_rq1 = "null" if hb_.p_equivalence < alpha and hb_.p_perm >= alpha else None
                    rq3_rows.append(dict(model=m, outcome=k, hypothesis="H3a", estimand="sigma_A(neu) - sigma_A(base)",
                                         estimate=dsd, ci_low=lo95, ci_high=hi95, p=p3a, ci90_low=lo90,
                                         ci90_high=hi90, equivalent=eq, p_tost=np.nan, sesoi=sesoi[k],
                                         label_unadjusted=lab, base_estimate=1.0, base_ci_low=hb_.ncf_ci_low,
                                         base_ci_high=hb_.ncf_ci_high, neu_ci_low=hn_.ncf_ci_low,
                                         neu_ci_high=hn_.ncf_ci_high, base_label=base_rq1,
                                         variance_scale_change=dv, variance_scale_se=se_dv))
                if "NONE" in cb.codes:
                    j = cb.cols(["NONE"])[0]
                    t = t_summary(Yn[:, j] - Yb[:, j], alpha, strata)
                    lam_rows.append(dict(model=m, outcome=k, estimand="lambda = tau_neu(NONE) - tau_base(NONE)",
                                         estimate=t.estimate, ci_low=t.ci_low, ci_high=t.ci_high, p=t.p,
                                         n_cv=t.n_cv))
    R["rq3"] = pd.DataFrame(rq3_rows)
    R["rq3_lambda"] = pd.DataFrame(lam_rows)

    R["interactions"] = _interactions(cells, models, conditions, conf_c, neu_c, cfg, rng, hosts)

    # ---------------- families (Holm) and RQ1 decision
    R["confirmatory"] = _families(R, conf_c, alpha, cfg)
    R["rq1_decision"] = _rq1_decisions(R, pc_fit, alpha)

    # ---------------- robustness (arms from the same run; no external directories)
    if cfg["run_robustness"]:
        rob, prof = [], []
        for (m, p, k), cell in cells.items():
            if p != conf_c:
                continue
            r1, r2 = run_robustness(cell, ev, 100.0, cfg["n_perm_secondary"], rng, alpha, sesoi[k], arm_evs,
                                    support=cfg["manski_support_robust"],
                                    support_descriptive=cfg["manski_support_descriptive"])
            rob.append(r1)
            prof.append(r2)
        R["robustness"] = pd.concat(rob, ignore_index=True) if rob else pd.DataFrame()
        R["robustness_wording"] = pd.concat(prof, ignore_index=True) if prof else pd.DataFrame()
        dmf = {(r["model"], r["condition"]): bool(r["flag"]) for _, r in R["diff_missing"].iterrows()}
        R["robust_labels"] = (robust_labels(R["robustness"], alpha, dmf, cfg["manski_logical_if_differential_missing"],
                                            require_host_exclusion=cfg.get("host_exclusion_required_for_robust", True))
                              if not R["robustness"].empty else pd.DataFrame())
        R["manski_bounds"] = manski_table(R["robustness"]) if not R["robustness"].empty else pd.DataFrame()
        if "greedy" not in arm_evs:
            notes.append("R4 (greedy decoding) not assessed: no rows with arm == 'greedy'. "
                         "'Robust' labels are therefore provisional.")

    R["sensitivity_models"], R["sensitivity_status"] = _sensitivity(ev, stims, cells, models, conf_c, cfg, alpha)

    if fc is not None:
        R["bt"], R["bt_summary"], R["rq4"], R["bt_host_excluded"] = _forced_choice(fc, ev, cells, codes, conf_c, cfg,
                                                                                  rng, alpha, notes)
    else:
        notes.append("forced_choice.csv absent or empty: Bradley-Terry and RQ4 skipped.")

    if pr is not None:
        R["principle"] = _sq1(R, models, cfg)
    else:
        notes.append("principle.csv absent or empty: SQ1 skipped.")
    R["missing_by_nat"] = missingness_by_nationality(ev)

    _write_tables(O, R, blind=False)
    if cfg["make_figures"]:
        _write_figures(O, R, codes, conditions, conf_c, neu_c)
    _write_summary(out, O, cfg, info, gate, prov, notes, mock, blind, processed_dir, tables, log_path)
    return {"mock": mock, "blind": False, "outputs": [p for p, _ in O.items], "notes": notes, "results": R,
            "config": cfg, "provenance": prov}


# =========================================================================== #
# helpers
# =========================================================================== #
def _label_of(C: pd.DataFrame, m, p, k, contrast):
    if C.empty:
        return None
    r = C[(C["model"] == m) & (C["condition"] == p) & (C["outcome"] == k) & (C["contrast"] == contrast)]
    return r["label"].iloc[0] if len(r) else None


def _vc_upper(cell, rep: np.ndarray, B: int, rng: np.random.Generator) -> dict:
    """80% upper limits (90th percentile of a CV bootstrap) of each SD component (review M14)."""
    keys = ("sd_cv", "sd_at", "sd_atk", "sd_ak", "sd_tk", "sd_eps", "rho_eps")
    if B < 2 or cell.n_cv < 3:
        return {f"{k}_upper80": np.nan for k in keys} | {"n_boot_vc": 0}
    idx = stratified_bootstrap_indices(cell.occupations, B, rng)
    draws = {k: [] for k in keys}
    for b in range(B):
        ii = idx[b]
        c = dataclasses.replace(cell, Yk=cell.Yk[ii], n_valid=cell.n_valid[ii], occupations=cell.occupations[ii],
                                tiers=cell.tiers[ii], cvs=[f"{cell.cvs[i]}#{j}" for j, i in enumerate(ii)], _Y=None,
                                base_countries=None if cell.base_countries is None else cell.base_countries[ii])
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            v = variance_components(c, rep[ii])
        for k in keys:
            draws[k].append(v.get(k, np.nan))
    out = {}
    for k in keys:
        a = np.array(draws[k], float)
        out[f"{k}_upper80"] = float(np.nanpercentile(a, 90)) if np.isfinite(a).any() else np.nan
    out["n_boot_vc"] = B
    return out


def _per_origin_vs_benchmarks(cells, cfg, rng, alpha, pc, hosts) -> pd.DataFrame:
    """EXPLORATORY per-origin Delta(n, DEU) and Delta(n, POL) (host-adjusted), simultaneous bands, BH,
    PC yardstick."""
    rows = []
    for (m, p, k), cell in cells.items():
        Y, strata = cell.Y, cell.occupations
        hf = hosts[(m, p, k)]
        Hu = cell.host() if hf.identified else None
        pce = np.nan
        if not pc.empty and p == "baseline":
            r = pc[(pc["model"] == m) & (pc["outcome"] == k)]
            pce = float(r["pc_effect"].iloc[0]) if len(r) else np.nan
        for ref in ("DEU", "POL"):
            if ref not in cell.codes:
                continue
            others = [c for c in cell.codes if c != ref]
            D = np.column_stack([contrast_values(Y, cell.cols([c]), cell.cols([ref]), Hu, hf, strata) for c in others])
            ts = [t_summary(D[:, j], alpha, strata) for j in range(len(others))]
            est = np.array([t.estimate for t in ts])
            se = np.array([t.se for t in ts])
            bidx = stratified_bootstrap_indices(strata, cfg["n_boot"], rng)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", RuntimeWarning)
                Eb = np.nanmean(D[bidx], axis=1)
                maxt = np.nanmax(np.abs(Eb - est) / np.where(se > 0, se, np.nan), axis=1)
            c = float(np.nanpercentile(maxt, 100 * (1 - alpha))) if np.isfinite(maxt).any() else np.nan
            q = bh(np.array([t.p for t in ts]))
            for j, code in enumerate(others):
                rows.append(dict(model=m, condition=p, outcome=k, reference=ref, nationality=code,
                                 group=cell.groups[code], subregion=cell.subregions.get(code), estimate=est[j],
                                 se=se[j], ci_low=ts[j].ci_low, ci_high=ts[j].ci_high,
                                 sim_ci_low=est[j] - c * se[j], sim_ci_high=est[j] + c * se[j], p=ts[j].p,
                                 q_bh=q[j], n_cv=ts[j].n_cv,
                                 pct_of_positive_control=100 * est[j] / abs(pce) if np.isfinite(pce) and pce else np.nan))
    return pd.DataFrame(rows)


def _placebo_comparison(ev_prim, cells, codes, conf_c, cfg, rng, alpha, notes, hosts=None) -> pd.DataFrame:
    """H1e (review H5): sigma_placebo (same debiased estimator over the placebo nationalities) and the
    comparison sigma_A - sigma_placebo with a CV-cluster bootstrap (same resamples for both sets).

    Test on the variance scale (sigma2_A - sigma2_placebo; bootstrap SE inflated by n_j/(n_j-1),
    t(I - #occupations)); effect size and 95% CI on the SD scale (bootstrap percentiles).
    Baseline, primary arm; placebo rows never enter any other analysis. sigma_A is host-adjusted
    (placebo nationalities are never host nationals).
    """
    plc_all = ev_prim[(ev_prim["nationality_group"] == PLACEBO) & (ev_prim["prompt_condition"] == conf_c)]
    if plc_all.empty:
        notes.append("No placebo nationalities in the data: H1e (sigma_A vs sigma_placebo) skipped.")
        return pd.DataFrame()
    base = ev_prim[(ev_prim["prompt_condition"] == conf_c)
                   & ev_prim["nationality_group"].isin(["arab", PLACEBO])].copy()
    plc_codes = sorted(plc_all["nationality"].astype(str).unique())
    rows = []
    for k in OUTCOMES:
        b = base.assign(interview=base["interview"] * 100.0) if k == "interview" else base
        stim = aggregate_stimulus(b, k)
        for m in sorted(b["model_alias"].astype(str).unique()):
            try:
                cell = build_cell(stim, m, conf_c, k, list(codes) + plc_codes)
            except ValueError:
                continue
            a, q = cell.cols(cell.arab_codes), cell.cols(plc_codes)
            if a.size < 3 or q.size < 3:
                continue
            Y, strata = cell.Y, cell.occupations
            keep = ~(np.isnan(Y[:, a]).all(1) | np.isnan(Y[:, q]).all(1))
            hp = heterogeneity(Y[keep][:, q], [cell.codes[i] for i in q], strata[keep], cfg["n_perm_secondary"], 0,
                               rng, alpha, cfg["sesoi"][k], boot_idx=np.zeros((1, int(keep.sum())), int))
            Ha = cell.host(a)
            cmp_ = compare_sigma(Y[:, a], Y[:, q], strata, cfg["n_boot"], rng, alpha,
                                 Ha=Ha if Ha.any() else None)
            rows.append(dict(model=m, condition=conf_c, outcome=k, n_cv=cmp_["n_cv"], n_arab=int(a.size),
                             n_placebo=int(q.size), placebo_codes="|".join(cell.codes[i] for i in q),
                             sigma_A=cmp_["sigma_a"], sigma_placebo=cmp_["sigma_b"],
                             sigma_placebo_ci_low=hp.ncf_ci_low, sigma_placebo_ci_high=hp.ncf_ci_high,
                             p_placebo_perm=hp.p_perm, difference=cmp_["difference"],
                             diff_ci_low=cmp_["diff_ci_low"], diff_ci_high=cmp_["diff_ci_high"],
                             p_difference=cmp_["p_difference"],
                             variance_scale_difference=cmp_["variance_scale_difference"],
                             variance_scale_se=cmp_["variance_scale_se"], df=cmp_["df"]))
    return pd.DataFrame(rows)


def _h1d(cells, conf_c, cfg, notes, alpha, hosts=None) -> pd.DataFrame:
    path = cfg.get("covariates_path")
    cov, msg = load_covariates(path)
    if cov is None:
        notes.append(msg)
        return pd.DataFrame()
    cov = cov.set_index("code")
    gdp = pd.to_numeric(cov["gdp_pc_ppp_const"], errors="coerce").to_dict()
    flag = cov["gdp_flag"].to_dict() if "gdp_flag" in cov else {}
    inc = cov["income_group"].map(INCOME_ORDER).to_dict() if "income_group" in cov else {}
    ssa = pd.to_numeric(cov["wb_sub_saharan"], errors="coerce").to_dict() if "wb_sub_saharan" in cov else None
    if ssa is None:
        notes.append("country_covariates.csv has no wb_sub_saharan column: the sub-Saharan H1d sensitivity slopes "
                     "are skipped.")
    rows = []
    for (m, p, k), cell in cells.items():
        if p != conf_c:
            continue
        a = cell.cols(cell.arab_codes)
        Yh = host_adjust(cell.Y, cell.host(), (hosts or {}).get((m, p, k)))     # plug-in host adjustment
        sesoi_h = cfg["sesoi"]["h1d_points"] * (1 if k == "overall_fit"
                                                 else cfg["sesoi"]["interview"] / cfg["sesoi"]["overall_fit"])
        variants = [("H1d log GDP pc PPP", {"gdp": gdp}, {"gdp": "log"}, "primary")]
        fb = {c: v for c, v in gdp.items() if str(flag.get(c, "reference_year")) == "reference_year"}
        if len(fb) < len(gdp):
            variants.append(("R11 excluding fallback/excluded origins", {"gdp": fb}, {"gdp": "log"}, "sensitivity"))
        if inc:
            variants.append(("R11 income group (ordinal 0-3)", {"income_group": inc}, {}, "sensitivity"))
        if ssa is not None:
            variants.append(("M9 log GDP pc adjusted for sub-Saharan (wb_sub_saharan)",
                             {"gdp": gdp, "wb_sub_saharan": ssa}, {"gdp": "log"}, "sensitivity"))
            variants.append(("M9 sub-Saharan indicator alone (wb_sub_saharan)", {"wb_sub_saharan": ssa}, {},
                             "sensitivity"))
        for lab, covs, tr, role in variants:
            r = h1d_gradient(Yh[:, a], cell.arab_codes, cell.occupations, covs, sesoi_h, alpha, tr)
            rows.append(dict(model=m, condition=p, outcome=k, analysis=lab, role=role, **r))
        if k == "overall_fit":
            for occ in np.unique(cell.occupations):
                rr = np.flatnonzero(cell.occupations == occ)
                if rr.size < 4:
                    continue
                r = h1d_gradient(Yh[rr][:, a], cell.arab_codes, cell.occupations[rr], {"gdp": gdp}, sesoi_h,
                                 alpha, {"gdp": "log"})
                rows.append(dict(model=m, condition=p, outcome=k, analysis=f"occupation {occ} (exploratory)",
                                 role="exploratory", **r))
    excl = sorted({x for r in rows if r["role"] == "primary" for x in str(r.get("excluded", "")).split("|") if x})
    if excl:
        notes.append("H1d: origins without a covariate value were excluded: " + ", ".join(excl))
    return pd.DataFrame(rows)


def _interactions(cells, models, conditions, conf_c, neu_c, cfg, rng, hosts=None) -> pd.DataFrame:
    """Profile tests on plug-in host-adjusted matrices (each cell's own eta_hat removed)."""
    hosts = hosts or {}

    def Ya(c):
        return host_adjust(c.Y, c.host(), hosts.get((c.model, c.condition, c.outcome)))

    rows = []
    for k in OUTCOMES:
        for p in conditions:
            cs = [cells[(m, p, k)] for m in models if (m, p, k) in cells]
            if len(cs) >= 2:
                common = [c for c in cs[0].cvs if all(c in set(x.cvs) for x in cs)]
                ar = cs[0].arab_codes
                it = profile_interaction_test([Ya(c)[c.rows(common)][:, c.cols(ar)] for c in cs],
                                              [c.model for c in cs], ar, cfg["n_perm_secondary"], rng)
                rows.append(dict(factor="nationality x model", condition=p, outcome=k, model="all",
                                 n_cv=it.n_cv, T=it.T, p_perm=it.p_perm, status="exploratory"))
        if conf_c in conditions and neu_c in conditions:
            for m in models:
                if (m, conf_c, k) in cells and (m, neu_c, k) in cells:
                    cb, cn = cells[(m, conf_c, k)], cells[(m, neu_c, k)]
                    common = [c for c in cb.cvs if c in set(cn.cvs)]
                    a = cb.cols(cb.arab_codes)
                    it = profile_interaction_test([Ya(cb)[cb.rows(common)][:, a], Ya(cn)[cn.rows(common)][:, a]],
                                                  [conf_c, neu_c], cb.arab_codes, cfg["n_perm_secondary"], rng)
                    rows.append(dict(factor="nationality x condition", condition=f"{conf_c}|{neu_c}", outcome=k,
                                     model=m, n_cv=it.n_cv, T=it.T, p_perm=it.p_perm, status="exploratory"))
    return pd.DataFrame(rows)


def _families(R, conf_c, alpha, cfg) -> pd.DataFrame:
    """Families of hypotheses.md 0 / preregistration; R2 (interview) repeats the structure ("R2: ")."""
    rows = []
    H, C, Q, P = R["heterogeneity"], R["contrasts"], R["rq3"], R.get("placebo", pd.DataFrame())
    for k in OUTCOMES:
        tag = "" if k == cfg["primary_outcome"] else "R2: "
        if not H.empty:
            for _, r in H[(H["condition"] == conf_c) & (H["outcome"] == k)].iterrows():
                o = r["origins"]
                sfx = "" if o == "22" else ", 19 origins"
                rows.append(dict(family=f"{tag}F1 primary (H1a{sfx})", hypothesis="H1a", origins=o, model=r["model"],
                                 outcome=k, estimand="sigma_A", estimate=r["sigma_A"], ci_low=r["ci_low"],
                                 ci_high=r["ci_high"], p=r["p_h1a_perm"],
                                 test="within-CV permutation (debiased sigma_A^2)"))
                rows.append(dict(family=f"{tag}F1-eq primary (H1b{sfx})", hypothesis="H1b", origins=o,
                                 model=r["model"], outcome=k, estimand="sigma_A < SESOI",
                                 estimate=r["upper95_one_sided"], ci_low=np.nan, ci_high=r["upper95_one_sided"],
                                 p=r["p_h1b_equivalence"], test="noncentral-F equivalence (one-sided 95% upper limit)"))
                rows.append(dict(family=f"{tag}F1-eq sphericity-free (H1b-sf{sfx})", hypothesis="H1b-sf", origins=o,
                                 model=r["model"], outcome=k, estimand="sigma_A < SESOI",
                                 estimate=r["sf_upper95"], ci_low=np.nan, ci_high=r["sf_upper95"], p=r["sf_p"],
                                 test="CV-bootstrap t, critical value calibrated by residual-resampling simulation"))
                rows.append(dict(family=f"{tag}F1-min (minimum effect{sfx})", hypothesis="H1a-min", origins=o,
                                 model=r["model"], outcome=k, estimand="sigma_A > SESOI",
                                 estimate=r["lower95_one_sided"], ci_low=r["lower95_one_sided"], ci_high=np.nan,
                                 p=r["p_min_effect"], test="noncentral-F minimum-effect test (one-sided 95% lower limit)"))
        h1c = R.get("h1c", pd.DataFrame())
        if not h1c.empty:
            for _, r in h1c[(h1c["condition"] == conf_c) & (h1c["outcome"] == k)].iterrows():
                rows.append(dict(family=f"{tag}F2 H1c", hypothesis="H1c", model=r["models"], outcome=k,
                                 estimand="equal sigma_A across models", estimate=r["W"], ci_low=np.nan,
                                 ci_high=np.nan, p=r["p"], test=f"Wald F({r['df']}, {r['df2']}), shared CV bootstrap"))
        h1d = R.get("h1d", pd.DataFrame())
        if not h1d.empty and "status" in h1d:
            for _, r in h1d[(h1d["outcome"] == k) & (h1d["role"] == "primary") & (h1d["status"] == "ok")].iterrows():
                rows.append(dict(family=f"{tag}F2 H1d", hypothesis="H1d", model=r["model"], outcome=k,
                                 estimand="beta_W (per unit log GDP pc; ecological)", estimate=r["beta_W"],
                                 ci_low=r["ci_low"], ci_high=r["ci_high"], p=r["p"],
                                 test="REML meta-regression, Knapp-Hartung", label=r["label"]))
        if not P.empty:
            for _, r in P[P["outcome"] == k].iterrows():
                rows.append(dict(family=f"{tag}F2 H1e", hypothesis="H1e", model=r["model"], outcome=k,
                                 estimand="sigma_A - sigma_placebo", estimate=r["difference"], ci_low=r["diff_ci_low"],
                                 ci_high=r["diff_ci_high"], p=r["p_difference"],
                                 test="shared CV bootstrap t (variance scale); percentile CI (SD scale)"))
        if not C.empty:
            for i, b in enumerate(BENCHMARKS):
                for _, r in C[(C["condition"] == conf_c) & (C["outcome"] == k)
                              & (C["contrast"] == f"ARAB_vs_{b}")].iterrows():
                    rows.append(dict(family=f"{tag}F2 H2", hypothesis=f"H2{'abcd'[i]}", model=r["model"], outcome=k,
                                     estimand=r["estimand"], estimate=r["estimate"], ci_low=r["ci_low"],
                                     ci_high=r["ci_high"], p=r["p"], test="stratified paired t",
                                     p_tost=r["p_tost"], equivalent=r["equivalent"], sesoi=r["sesoi"]))
        if not Q.empty:
            for _, r in Q[Q["outcome"] == k].iterrows():
                rows.append(dict(family=f"{tag}F2 H3", hypothesis=r["hypothesis"], model=r["model"], outcome=k,
                                 estimand=r["estimand"], estimate=r["estimate"], ci_low=r["ci_low"],
                                 ci_high=r["ci_high"], p=r["p"],
                                 test="bootstrap t (variance scale)" if r["hypothesis"] == "H3a"
                                 else "stratified paired t (DiD)", p_tost=r["p_tost"], equivalent=r["equivalent"],
                                 sesoi=r["sesoi"], base_estimate=r["base_estimate"], base_ci_low=r["base_ci_low"],
                                 base_ci_high=r["base_ci_high"], neu_ci_low=r["neu_ci_low"],
                                 neu_ci_high=r["neu_ci_high"], base_label=r["base_label"]))
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df = adjust_within(df, "p", ["family"], "holm", "p_holm")
    df["reject_at_alpha"] = df["p_holm"] < alpha
    return _adjusted_labels(df, alpha)


def _adjusted_labels(df: pd.DataFrame, alpha: float) -> pd.DataFrame:
    """Decision labels from Holm-adjusted tests (and Holm-adjusted TOST where a TOST p exists)."""
    if "p_tost" in df:
        df = adjust_within(df, "p_tost", ["family"], "holm", "p_tost_holm")
    labels, readings = [], []
    for _, r in df.iterrows():
        h = r["hypothesis"]
        if h == "H1e":
            labels.append(h1e_label(r["ci_low"], r["ci_high"], r["p_holm"], alpha))
            readings.append("compares within-Arab spread with generic nationality-label spread; says nothing "
                            "about why")
            continue
        if h in ("H1a", "H1b", "H1b-sf", "H1a-min", "H1c"):
            labels.append(None)
            readings.append(None)
            continue
        if h == "H1d":
            eq = str(r.get("label", "")).startswith(("null", "trivial"))
            labels.append(decision_label(r["ci_low"], r["ci_high"], eq, np.inf, rejects=bool(r["p_holm"] < alpha)))
            readings.append("ecological association; descriptive of structure, not a test of status -> competence")
            continue
        pt = r.get("p_tost_holm", np.nan)
        eq = bool(pt < alpha) if np.isfinite(pt) else bool(r.get("equivalent", False))
        lab = decision_label(r["ci_low"], r["ci_high"], eq, r["sesoi"], rejects=bool(r["p_holm"] < alpha))
        labels.append(lab)
        if h in ("H3a", "H3b"):
            readings.append(rq3_label(lab, r["estimate"], r["base_estimate"], (r["base_ci_low"], r["base_ci_high"]),
                                      (r["neu_ci_low"], r["neu_ci_high"]),
                                      r["base_label"] if isinstance(r["base_label"], str) else None))
        else:
            readings.append(None)
    df["label"] = labels
    df["reading"] = readings
    return df.drop(columns=[c for c in ("base_estimate", "base_ci_low", "base_ci_high", "neu_ci_low",
                                        "neu_ci_high", "base_label") if c in df.columns])


def _rq1_decisions(R, pc_fit, alpha) -> pd.DataFrame:
    """RQ1 labels per origin set (22, 19) and the headline label requiring both (review H5, M3, M4)."""
    F = R["confirmatory"]
    if F.empty:
        return pd.DataFrame()
    rows = []

    def get(h, m, k, o, col="p_holm"):
        r = F[(F["hypothesis"] == h) & (F["model"] == m) & (F["outcome"] == k) & (F["origins"] == o)]
        return r[col].iloc[0] if len(r) else np.nan

    for k in OUTCOMES:
        for m in sorted(F.loc[F["hypothesis"] == "H1a", "model"].unique()):
            det = bool(pc_fit.loc[m, "manipulation_check_passed"]) if (not pc_fit.empty and m in pc_fit.index) else False
            labs = {}
            row = dict(model=m, outcome=k, manipulation_check_passed=det)
            for o in ("22", "19"):
                pa, pb, pm, psf = (get("H1a", m, k, o), get("H1b", m, k, o), get("H1a-min", m, k, o),
                                   get("H1b-sf", m, k, o))
                if not np.isfinite(pa):
                    continue
                labs[o] = rq1_label(pa, pb, pm, bool(np.isfinite(psf) and psf < alpha), det, alpha)
                row.update({f"sigma_A_{o}": get("H1a", m, k, o, "estimate"), f"ci_low_{o}": get("H1a", m, k, o, "ci_low"),
                            f"ci_high_{o}": get("H1a", m, k, o, "ci_high"), f"p_h1a_holm_{o}": pa,
                            f"p_h1b_holm_{o}": pb, f"p_h1b_sf_holm_{o}": psf, f"p_min_effect_holm_{o}": pm,
                            f"label_{o}": labs[o]})
            if "22" not in labs:
                continue
            row["headline_label"] = rq1_headline(labs["22"], labs.get("19", labs["22"]))
            rows.append(row)
    return pd.DataFrame(rows)


def _sensitivity(ev, stims, cells, models, conf_c, cfg, alpha):
    rows, status = [], []
    for m in models:
        if (m, conf_c, "overall_fit") not in cells:
            continue
        ev_c = ev[(ev["model_alias"] == m) & (ev["prompt_condition"] == conf_c)]
        for k in OUTCOMES:
            s = stims[k]
            s_c = s[(s["model_alias"] == m) & (s["prompt_condition"] == conf_c)]
            try:
                tab, stt = cv_fe_ols(s_c, alpha)
                rows.append(tab.assign(model=m, outcome=k, spec="MS1 CV-FE OLS + variant FE, CR1"))
                status.append(dict(model=m, outcome=k, spec="MS1", status=stt))
            except Exception as e:  # noqa: BLE001
                status.append(dict(model=m, outcome=k, spec="MS1", status=f"failed: {e}"))
        if cfg["run_mixedlm"]:
            tab, stt = mixedlm_rep(ev_c, "overall_fit", alpha)
            if not tab.empty:
                rows.append(tab.assign(model=m, outcome="overall_fit", spec="MS2 LMM"))
            status.append(dict(model=m, outcome="overall_fit", spec="MS2", status=json.dumps(stt, default=str)))
        if cfg["run_gee"]:
            tab, stt = gee_interview(ev_c, alpha)
            if not tab.empty:
                rows.append(tab.assign(model=m, outcome="interview", spec="MS3 GEE logit (log-odds)"))
            status.append(dict(model=m, outcome="interview", spec="MS3", status=json.dumps(stt, default=str)))
    return (pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()), pd.DataFrame(status)


def _forced_choice(fc, ev, cells, codes, conf_c, cfg, rng, alpha, notes):
    bt_rows, bt_sum, rq4, hx_rows = [], [], [], []
    arab_all = set(ev.loc[ev["nationality_group"] == "arab", "nationality"])
    grp = ev.drop_duplicates("nationality").set_index("nationality")["nationality_group"]
    for (m, p), g in fc.groupby(["model_alias", "prompt_condition"], observed=True):
        m, p = str(m), str(p)
        try:
            data = prepare_fc(g, codes=[c for c in codes if c != "NONE"])
        except ValueError as e:
            notes.append(f"BT {m}/{p}: {e}")
            continue
        arab = [c for c in data.codes if c in arab_all]
        if len(data.cvs) < cfg["min_cv_warning"]:
            notes.append(f"BT {m}/{p}: only {len(data.cvs)} base CVs enter the forced-choice data; "
                         "CV-bootstrap CIs are unreliable at this scale.")
        mult = cv_multiplicities(data.cvs, data.cv_strata, cfg["n_boot_bt"], rng)
        res = bt_analysis(data, arab, cfg["n_boot_bt"], cfg["n_perm_bt"], rng, REFERENCE, alpha, mult=mult)
        tab = res.table.assign(model=m, condition=p)
        tab["group"] = tab["nationality"].map(grp)
        row = dict(model=m, condition=p, gamma_position=res.gamma, gamma_ci_low=res.gamma_ci[0],
                   gamma_ci_high=res.gamma_ci[1], gamma_by_variant=json.dumps(res.gamma_k),
                   sd_beta_arab_plugin=res.sd_beta_arab, sigma_A_fc_debiased=res.sigma_A_fc,
                   p_swap_within_arab=res.p_perm_within_arab, n_comparisons=res.fit.n_comparisons,
                   converged=res.fit.converged, n_boot_failed=res.n_boot_failed, sesoi_logit=cfg["sesoi"]["fc_logit"],
                   host_effect_logit=res.host_effect, host_effect_ci_low=res.host_ci[0],
                   host_effect_ci_high=res.host_ci[1],
                   n_host_prompts=int(np.sum(data.hd != 0)) if data.hd is not None else 0)
        # sensitivity: drop every quad that contains a host national (no host term needed)
        if {"host_national_a", "host_national_b"} <= set(g.columns):
            hq = g.loc[g["host_national_a"].astype(bool) | g["host_national_b"].astype(bool), "quad_id"].unique()
            gx = g[~g["quad_id"].isin(hq)]
            try:
                dx = prepare_fc(gx, codes=[c for c in codes if c != "NONE"]) if len(gx) else None
            except ValueError:
                dx = None
            if dx is not None:
                ax = [c for c in dx.codes if c in arab_all]
                mx = cv_multiplicities(dx.cvs, dx.cv_strata, cfg["n_boot_bt"], rng)
                rx = bt_analysis(dx, ax, cfg["n_boot_bt"], 0, rng, REFERENCE, alpha, mult=mx, host=False)
                hx_rows.append(rx.table.assign(model=m, condition=p, n_quads_dropped=len(hq),
                                               sigma_A_fc_debiased=rx.sigma_A_fc))
                row.update(sigma_A_fc_host_excluded=rx.sigma_A_fc, n_host_quads_dropped=int(len(hq)))
        if (m, conf_c, "overall_fit") in cells:
            cell = cells[(m, conf_c, "overall_fit")]
            S = replicate_array(ev, m, conf_c, "overall_fit", cell.cvs, cell.codes, flatten_variants=True)
            imp = {}
            for tf in (False, True):
                idata = implied_from_fc(data, S, cell.cvs, cell.codes, tie_free=tf)
                if idata.ia.size:
                    imp[tf] = (idata, fit_bt(idata, REFERENCE, position=False))
            a_idx = np.array([data.codes.index(c) for c in arab])
            if False in imp:
                tab["beta_ie_implied"] = arab_centred(imp[False][1].theta_ref, a_idx)
            if True in imp:
                tab["beta_ie_implied_tiefree"] = arab_centred(imp[True][1].theta_ref, a_idx)
            if p == cfg["fc_condition"] and imp:
                rq4.append(_rq4(m, data, imp, res, arab, alpha, mult))
        bt_rows.append(tab)
        bt_sum.append(row)
    return (pd.concat(bt_rows, ignore_index=True) if bt_rows else pd.DataFrame(), pd.DataFrame(bt_sum),
            pd.DataFrame(rq4), pd.concat(hx_rows, ignore_index=True) if hx_rows else pd.DataFrame())


def _rq4(m, data, imp, res, arab, alpha, mult) -> dict:
    """RQ4 (exploratory): dispersion ratio and concordance on the common BT logit scale."""
    a_idx = np.array([data.codes.index(c) for c in arab])
    out = dict(model=m, n_origins=int(a_idx.size))
    fc_beta = res.table["beta"].to_numpy()
    for tf, (idata, ifit) in imp.items():
        tag = "_tiefree" if tf else ""
        ie_beta = arab_centred(ifit.theta_ref, a_idx)
        W_ie = mult[:, idata.ca] * mult[:, idata.cb]
        dr_fc, dr_ie, cors = [], [], []
        for b in range(mult.shape[0]):
            if not (W_ie[b] > 0).any() or not np.isfinite(res.boot_beta[b][a_idx]).all():
                continue
            f2 = fit_bt(idata, REFERENCE, False, weights=W_ie[b])
            if not f2.converged or f2.separation_suspected:
                continue
            x, y = res.boot_beta[b][a_idx], arab_centred(f2.theta_ref, a_idx)[a_idx]
            dr_fc.append(x)
            dr_ie.append(y)
            cors.append(np.corrcoef(x, y)[0, 1])
        dr_fc, dr_ie = np.array(dr_fc), np.array(dr_ie)
        sd_fc = float(np.sqrt(np.mean(fc_beta[a_idx] ** 2)))
        sd_ie = float(np.sqrt(np.mean(ie_beta[a_idx] ** 2)))
        if len(dr_ie) > 10:
            s_fc = float(np.sqrt(max(sd_fc ** 2 - np.mean(np.var(dr_fc, 0, ddof=1)), 0)))
            s_ie = float(np.sqrt(max(sd_ie ** 2 - np.mean(np.var(dr_ie, 0, ddof=1)), 0)))
            ratios = np.sqrt(np.mean(dr_fc ** 2, 1)) / np.sqrt(np.mean(dr_ie ** 2, 1))
            rlo, rhi = np.nanpercentile(ratios, [100 * alpha / 2, 100 * (1 - alpha / 2)])
            clo, chi = np.nanpercentile(cors, [100 * alpha / 2, 100 * (1 - alpha / 2)])
        else:
            s_fc = s_ie = rlo = rhi = clo = chi = np.nan
        out.update({f"sd_fc_plugin{tag}": sd_fc, f"sd_ie_plugin{tag}": sd_ie,
                    f"sigma_fc_debiased{tag}": s_fc, f"sigma_ie_debiased{tag}": s_ie,
                    f"dispersion_ratio_debiased{tag}": s_fc / s_ie if s_ie and s_ie > 0 else np.nan,
                    f"dispersion_ratio_plugin{tag}": sd_fc / sd_ie if sd_ie > 0 else np.nan,
                    f"ratio_plugin_ci_low{tag}": rlo, f"ratio_plugin_ci_high{tag}": rhi,
                    f"concordance{tag}": float(np.corrcoef(fc_beta[a_idx], ie_beta[a_idx])[0, 1]),
                    f"concordance_ci_low{tag}": clo, f"concordance_ci_high{tag}": chi,
                    f"n_boot_ok{tag}": int(len(dr_ie))})
    out["gamma_position"] = res.gamma
    out["caveat"] = ("forced choice forbids ties, which inflates FC dispersion when latent preferences are small; "
                     "concordance is uninterpretable when sigma_A is ~0 in either format")
    return out


def _sq1(R, models, cfg) -> pd.DataFrame:
    E = R["principle_endorsement"]
    F = R["confirmatory"]
    dec = R["rq1_decision"]
    beh = []
    for m in models:
        labels, effs = [], []
        d = dec[(dec["model"] == m) & (dec["outcome"] == "overall_fit")] if not dec.empty else pd.DataFrame()
        if len(d):
            lab = d["headline_label"].iloc[0]
            labels.append("effect" if lab.startswith(("meaningful", "heterogeneity present")) else
                          "null (equivalence)" if lab.startswith("null:") else
                          "trivial effect" if lab.startswith("trivial") else "inconclusive")
            if lab.startswith("meaningful"):
                effs.append(d["sigma_A_22"].iloc[0])
        if not F.empty:
            h2 = F[(F["model"] == m) & (F["hypothesis"].isin(["H2a", "H2b", "H2c", "H2d"]))
                   & (F["outcome"] == "overall_fit")]
            for _, r in h2.iterrows():
                labels.append(r["label"])
                if str(r["label"]).startswith("effect"):
                    effs.append(abs(r["estimate"]))
        beh.append(dict(model=m, labels=labels, max_abs_effect_at_label=max(effs) if effs else np.nan,
                        sesoi=cfg["sesoi"]["overall_fit"]))
    return classify(E, pd.DataFrame(beh), cfg["endorsement_threshold"])


def _nan_to_none(obj):
    if isinstance(obj, dict):
        return {k: _nan_to_none(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_nan_to_none(v) for v in obj]
    if isinstance(obj, float) and not np.isfinite(obj):
        return None
    return obj


def _write_vc_json(out, O, V, U, ev, cfg, mock, blind, processed_dir):
    link = _fit_interview_link(ev, cfg["confirmatory_condition"])
    js = {"is_mock": mock, "banners": O.banners, "blind": blind,
          "source": str(processed_dir), "created_utc": datetime.now(timezone.utc).isoformat(),
          "units": {"overall_fit": "points", "interview": "percentage points"},
          "model": "Y_inkr = mu + a_i + t_n + (at)_in + k_k + (tk)_nk + (ak)_ik + (atk)_ink + e_inkr "
                   "(experimental_design.md 1.6); rho_eps = cross-clone decoder-noise correlation",
          "cells": _nan_to_none(V.to_dict(orient="records")),
          "cells_upper80": _nan_to_none(U.to_dict(orient="records")),
          "pooled": {}, "upper": {}, "fit_to_interview_link": link,
          "planning_note": "Plan with rho_eps = 0 (review M14) and with the 'upper' block: per component the "
                           "largest 80% upper limit (90th percentile of a CV bootstrap) over models x conditions.",
          "caution": "Mock-provider data share decoder seeds across clones (common random numbers) and have "
                     "less clone-to-clone noise than real models: never size the study from mock output."}
    if not V.empty:
        for k in OUTCOMES:
            v, u = V[V["outcome"] == k], U[U["outcome"] == k]
            if v.empty:
                continue
            pooled = {}
            for s in ("sd_cv", "sd_at", "sd_atk", "sd_ak", "sd_eps"):
                pooled[s] = float(np.sqrt(np.nanmean(v[s] ** 2))) if v[s].notna().any() else None
            pooled["rho_eps"] = float(np.nanmean(v["rho_eps"])) if v["rho_eps"].notna().any() else None
            pooled["grand_mean"] = float(np.nanmean(v["grand_mean"]))
            js["pooled"][k] = pooled
            up = {}
            for s in ("sd_cv", "sd_at", "sd_atk", "sd_ak", "sd_eps"):
                col = f"{s}_upper80"
                up[s] = float(np.nanmax(u[col])) if col in u and u[col].notna().any() else pooled.get(s)
            up["rho_eps"] = 0.0
            up["grand_mean"] = pooled["grand_mean"]
            js["upper"][k] = up
    (out / "variance_components.json").write_text(json.dumps(_nan_to_none(js), indent=2, default=float),
                                                  encoding="utf-8")
    O.items.append(("variance_components.json", "Variance components per model x condition x outcome, pooled and "
                    "80% upper limits; input for analysis/power_analysis.py"))


def _fit_interview_link(ev: pd.DataFrame, cond: str) -> dict:
    """Call-level logistic link interview ~ fit (parameterises the power simulator)."""
    v = ev[(ev["parse_status"] == "ok") & (ev["prompt_condition"] == cond) & ev["overall_fit"].notna()
           & ev["interview"].notna()]
    if len(v) < 20 or v["interview"].nunique() < 2:
        return {"status": "not estimable"}
    from statsmodels.discrete.discrete_model import Logit
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            x = v["overall_fit"].astype(float).to_numpy()
            res = Logit(v["interview"].astype(float).to_numpy(), np.column_stack([np.ones_like(x), x])).fit(disp=0)
        a, b = map(float, res.params)
        return {"status": "ok", "intercept": a, "slope": b, "threshold": -a / b if b != 0 else None,
                "n": int(len(v))}
    except Exception as e:  # noqa: BLE001
        return {"status": f"failed: {e}"}


# =========================================================================== #
# writers
# =========================================================================== #
CSV_SPECS = {
    "design": "Design cells: calls, variants, positive-control calls, valid share (incl. placebo rows)",
    "balance": "Design checks: grid completeness, FC balance and connectivity",
    "status": "Response status counts and shares (P1 target: >= 95% ok)",
    "diff_missing": "Non-ok share across nationalities as its own outcome (P2); all non-ok incl. terminal "
                    "api_error, split by type",
    "positive_control": "Manipulation check (A7, review M1): positive_control minus NONE clone, one-sided",
    "tier_check": "Tier manipulation check on NONE clones (P4)",
    "scale_use": "Scale use per tier (P3; review L6)",
    "fc_diagnostics": "Forced-choice position share and CV/position-determined quads (P7)",
    "principle_endorsement": "Principle probe: keyed endorsement E_m and control-item discrimination (P8)",
    "principle_control_items": "Principle probe: control items per model",
    "text_flag_rates": "EXPLORATORY text-flag rates (incl. mentions_testing, P11)",
    "text_flag_tests": "EXPLORATORY text-flag Arab-vs-DEU contrasts with BH q-values",
    "pronoun_gender": "EXPLORATORY inferred pronoun distribution",
    "variance_components": "Variance components (1.6) per model x condition x outcome (P6)",
    "variance_components_upper80": "80% upper limits (CV bootstrap) of the variance components (review M14)",
    "heterogeneity": f"RQ1: sigma_A across the {ARAB_LABEL} (22 and 19 origins): debiased, noncentral-F CI, "
                     "H1a / H1b / minimum-effect p-values, sphericity-free bound, GG epsilon, raw SD and range "
                     "with permutation null references",
    "h1a_wald_crosscheck": "H1a cross-check: CV-clustered Hotelling T^2 Wald test",
    "heterogeneity_effects": "delta_hat per origin with empirical-Bayes shrinkage (R13) and residual variance",
    "origin_deviations": "EXPLORATORY per-origin delta(n) with simultaneous CIs, BH q-values, rank intervals",
    "subregion_net": "Secondary: sigma_A net of sub-region means (debiased) and between-sub-region share",
    "placebo": "H1e: sigma_placebo and sigma_A - sigma_placebo (baseline, primary arm; review H5)",
    "h1c": "H1c: Wald test of equal sigma_A across models (shared CV bootstrap)",
    "concordance": "Reliability-corrected profile concordance between models",
    "h1d": "H1d status gradient (ecological): REML meta-regression (Knapp-Hartung), design-based slope, "
           "R11 and sub-Saharan sensitivity slopes, occupation-specific slopes (exploratory)",
    "contrasts": "RQ2: Delta(A_bar, b) for b in DEU/POL/TUR/NONE (host-adjusted) with TOST and four-way labels; "
                 "R1 versions",
    "host_effect": "SECONDARY / descriptive: common host-national effect eta (host clone vs same-origin non-host "
                   "clone; CV and nationality fixed effects) per model x condition x outcome, CV-clustered CI",
    "host_sensitivity_deltas": "HX sensitivity: per-origin delta(n), host-adjusted (primary) vs host-national clones "
                               "excluded",
    "coefficients": "EXPLORATORY per-origin Delta(n, DEU) and Delta(n, POL): simultaneous CIs, BH, % of positive control",
    "rq3": "RQ3: H3a (change in sigma_A) and H3b (change in Delta(A,DEU)), unadjusted labels",
    "rq3_lambda": "RQ3: level effect of the neutrality paragraph on NONE clones (descriptive)",
    "interactions": "EXPLORATORY nationality x model and nationality x condition profile tests",
    "confirmatory": "Confirmatory and secondary families with Holm-adjusted p-values and adjusted labels",
    "rq1_decision": "RQ1 labels for 22 and 19 origins and the headline label requiring both",
    "robustness": "Robustness checks R1, R3, R4, R5 (Manski bounds), SVI, R6-R8, HX (host-national clones "
                  "excluded)",
    "robustness_wording": "R3: nationality x wording test and profile correlation across wordings",
    "robust_labels": "'Robust' labels (R1, R3 >= 2/3, R4, R5, HX; SVI replaces R5 for sigma_A)",
    "sensitivity_models": "Model-based cross-checks (MS1 CV-FE OLS, MS2 LMM, MS3 GEE)",
    "sensitivity_status": "Convergence / fallback status of MS1-MS3",
    "manski_bounds": "Manski worst-case bounds for Delta(A,b): observed support (robust label) and logical "
                     "0-100 support (descriptive; decision-relevant only if differential missingness rejects), "
                     "with bound widths",
    "bt": "Bradley-Terry worth (Arab-centred and vs DEU), CV-bootstrap CIs, IE-implied worth",
    "bt_summary": "Bradley-Terry position bias per variant, debiased sigma_A^FC, swap test, host covariate "
                  "(secondary) and host-excluded sigma_A^FC",
    "bt_host_excluded": "Bradley-Terry sensitivity: quads containing a host national dropped, no host term",
    "rq4": "RQ4 (exploratory): dispersion ratio and concordance, incl. tie-free sensitivity",
    "principle": "SQ1: E_m and classification (gap / substantive gap / consistent / unclassifiable)",
    "missing_by_nat": "Non-ok and refusal shares per nationality (unblinded)",
}


def _write_tables(O: _Outputs, R: dict[str, pd.DataFrame], blind: bool) -> None:
    for name, desc in CSV_SPECS.items():
        df = R.get(name)
        if df is not None and not df.empty:
            O.csv(df, name, desc + (" [blind mode]" if blind else ""))
    tex = {
        "design": (["task", "model", "condition", "arm", "base_cvs", "nationalities", "variants", "repetitions",
                    "calls", "valid_share"], "Design and data volume per task, model and condition."),
        "status": (["task", "model_alias", "prompt_condition", "arm", "calls", "share_ok", "share_refusal",
                    "share_malformed_json", "share_schema_violation", "share_empty", "share_api_error"],
                   "Response status shares by task, model and condition."),
        "coefficients": (["model", "condition", "outcome", "reference", "nationality", "estimate", "ci_low",
                          "ci_high", "sim_ci_low", "sim_ci_high"],
                         "Per-origin differences to the reference (paired over base CVs; 95\\% CI and "
                         "simultaneous band)."),
        "heterogeneity": (["model", "condition", "outcome", "origins", "n_cv", "sigma_A", "ci_low", "ci_high",
                           "upper95_one_sided", "sf_upper95", "p_h1a_perm", "p_h1b_equivalence", "p_min_effect"],
                          f"Heterogeneity across the {ARAB_LABEL}: debiased sigma_A with noncentral-F 95\\% CI."),
        "confirmatory": (["family", "hypothesis", "model", "outcome", "estimate", "ci_low", "ci_high", "p", "p_holm"],
                         "Confirmatory and secondary tests with Holm-adjusted p-values."),
        "placebo": (["model", "outcome", "sigma_A", "sigma_placebo", "difference", "diff_ci_low", "diff_ci_high",
                     "p_difference"], "Within-Arab spread compared with placebo nationality spread (baseline)."),
        "bt": (["model", "condition", "nationality", "beta", "ci_low", "ci_high", "beta_vs_ref"],
               "Bradley--Terry worth (log-odds; Arab-centred) with CV-bootstrap 95\\% CIs."),
        "variance_components": (["model", "condition", "outcome", "sd_at", "sd_atk", "sd_ak", "sd_eps", "rho_eps",
                                 "sd_cv"], "Variance components (SDs) of the planning model."),
        "positive_control": (["model", "outcome", "pc_effect", "ci_low", "ci_high", "upper_one_sided", "n_cv",
                              "manipulation_check_passed"],
                             "Manipulation check: effect of removing one must-have line (baseline)."),
    }
    for name, (cols, cap) in tex.items():
        df = R.get(name)
        if df is not None and not df.empty:
            O.tex(df[[c for c in cols if c in df.columns]], name, f"LaTeX (booktabs) version of {name}", cap)


def _write_figures(O: _Outputs, R, codes, conditions, conf_c, neu_c) -> None:
    fd = O.out / "figures"
    coef = R["coefficients"]
    if not coef.empty:
        cd = coef[coef["reference"] == REFERENCE]
        for k in OUTCOMES:
            for p in conditions:
                if ((cd["outcome"] == k) & (cd["condition"] == p)).any():
                    O.fig(figs.coefficient_plot(cd, k, p, codes, fd / f"coef_{k}_{p}", O.mock,
                                                R.get("positive_control")),
                          f"Per-origin difference to DEU with CIs, {k}, {p}")
                    O.fig(figs.heatmap(cd, k, p, codes, fd / f"heatmap_{k}_{p}", O.mock),
                          f"Nationality x model heatmap, {k}, {p}")
            if conf_c in conditions and neu_c in conditions:
                O.fig(figs.prompt_comparison(cd, k, codes, fd / f"prompt_comparison_{k}", O.mock, (conf_c, neu_c)),
                      f"Nationality x prompt condition, {k}")
    H = R["heterogeneity"]
    if not H.empty:
        H22 = H[H["origins"] == "22"].copy()
        P = R.get("placebo", pd.DataFrame())
        if not P.empty:
            H22 = H22.merge(P[["model", "condition", "outcome", "sigma_placebo"]],
                            on=["model", "condition", "outcome"], how="left")
        for k in OUTCOMES:
            if (H22["outcome"] == k).any():
                O.fig(figs.heterogeneity_plot(H22, k, fd / f"heterogeneity_{k}", O.mock),
                      f"sigma_A per model x condition (with placebo reference where available), {k}")
    if not R.get("bt", pd.DataFrame()).empty:
        O.fig(figs.bt_plot(R["bt"], codes, fd / "bradley_terry", O.mock), "Bradley-Terry estimates")
    O.fig(figs.status_table_figure(R["status"], fd / "response_status", O.mock),
          "Refusal / error / parse-failure table figure")


def _write_summary(out: Path, O: _Outputs, cfg, info, gate, prov, notes, mock, blind, processed_dir, tables,
                   log_path) -> None:
    import matplotlib
    import scipy
    import statsmodels

    lines = []
    for b in O.banners:
        lines += [f"# {b}", ""]
    if mock:
        lines += [f"**{MOCK_BANNER}** — every number in this directory comes from synthetic mock data and must "
                  "not be reported as a result.", ""]
    if info["overrides"]:
        lines += [f"**{OVERRIDE_BANNER}**: {', '.join(info['overrides'])}. Results are exploratory.", ""]
    if PARSE_BANNER in O.banners:
        lines += [f"**{PARSE_BANNER}**. Results are exploratory.", ""]
    if blind:
        lines += [f"**{BLIND_BANNER}**", ""]
    lines += ["# Analysis output summary", "",
              f"- Input: `{processed_dir}`",
              f"- Created (UTC): {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
              "- Rows: " + ", ".join(f"{k}={0 if v is None else len(v)}" for k, v in tables.items()),
              f"- is_mock rows present: {mock}; blind mode: {blind}",
              f"- Confirmatory config: `{info['confirmatory_path']}` (SHA-256 {info['confirmatory_sha256']})",
              f"- Overridden confirmatory keys: {info['overrides'] or 'none'}",
              f"- Preregistration SHA-256 at run time: {gate.get('prereg_sha256')}; freeze valid: {gate.get('freeze_ok')}"
              f" ({gate.get('reason')})",
              f"- Unblinding log: `{log_path}`" + ("" if not blind else " (not written: blind run)"),
              f"- Confirmatory config committed at HEAD and unchanged: {info.get('confirmatory_committed')} "
              f"({info.get('confirmatory_status')})",
              f"- Project root: `{info['root']}`; git commit: {prov.get('git_commit')}; config / preregistration "
              f"uncommitted changes: {prov.get('git_dirty')}",
              f"- Analysis code repository commit: {prov.get('code_git_commit')}; analysis code uncommitted changes: "
              f"{prov.get('code_git_dirty')}",
              f"- Analysis code SHA-256: {prov.get('analysis_code_sha256')}",
              f"- Seed: {cfg['seed']}; bootstrap B={cfg['n_boot']}; H1a permutations={cfg['n_perm']}; "
              f"secondary permutations={cfg['n_perm_secondary']}; BT bootstrap={cfg['n_boot_bt']}; "
              f"calibration sims={cfg['n_cal']}",
              f"- SESOI: {cfg['sesoi']} (final: {cfg['sesoi_is_final']})",
              f"- Versions: python {platform.python_version()}, numpy {np.__version__}, pandas {pd.__version__}, "
              f"scipy {scipy.__version__}, statsmodels {statsmodels.__version__}, matplotlib {matplotlib.__version__}",
              "", "This file lists outputs only. It contains no interpretation. Plan: "
              "`analysis/statistical_analysis_plan.md`.", "", "## Notes", ""]
    lines += [f"- {n}" for n in notes] or ["- none"]
    lines += ["", "## Outputs", ""]
    lines += [f"- `{p}` — {d}" for p, d in O.items]
    lines.append("- `summary.md` — this file")
    (out / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
