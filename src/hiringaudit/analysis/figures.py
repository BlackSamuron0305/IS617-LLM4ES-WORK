"""Matplotlib figures (PDF + PNG). Mock data get a visible watermark and title."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402

from .schema import ARAB_LABEL, MOCK_BANNER, REFERENCE  # noqa: E402

# Validated reference palette (categorical slots 1-3 pass all-pairs CVD checks).
INK = "#0b0b0b"
INK2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"
SURFACE = "#fcfcfb"
GROUP_COLORS = {"arab": "#2a78d6", "benchmark": "#eb6834", "control": "#1baf7a"}
GROUP_LABELS = {"arab": ARAB_LABEL, "benchmark": "benchmark nationalities", "control": "nationality not stated"}
COND_COLORS = {"baseline": "#2a78d6", "neutrality": "#eb6834",
               "forced_choice": "#2a78d6", "forced_choice_neutrality": "#eb6834"}
CRITICAL = "#d03b3b"
DIVERGING = LinearSegmentedColormap.from_list("red_gray_blue", ["#e34948", "#f0efec", "#2a78d6"])
SEQUENTIAL = LinearSegmentedColormap.from_list("blue_seq", ["#cde2fb", "#3987e5", "#0d366b"])

RC = {"font.family": "sans-serif", "font.size": 8, "axes.edgecolor": AXIS, "axes.labelcolor": INK2,
      "xtick.color": INK2, "ytick.color": INK2, "axes.grid": True, "grid.color": GRID,
      "grid.linewidth": 0.6, "axes.spines.top": False, "axes.spines.right": False,
      "figure.facecolor": "white", "axes.facecolor": "white", "legend.frameon": False}

OUTCOME_LABEL = {"overall_fit": "job-fit score (points, 0-100)",
                 "interview": "interview recommendation (percentage points)"}


# stem -> all figure-level text strings of each saved figure (used by tests to
# verify that mock figures carry the banner).
FIGURE_TEXT_REGISTRY: dict[str, list[str]] = {}


def banners_of(mock) -> list[str]:
    """``mock`` may be a bool (mock banner or none) or a list of banner strings."""
    if isinstance(mock, (list, tuple)):
        return list(mock)
    return [MOCK_BANNER] if mock else []


def finalize(fig, stem: Path, mock, title: str | None = None) -> list[Path]:
    """Add title (+ banners as title lines and diagonal watermark) and save PDF and PNG.

    ``mock``: bool or list of banners (e.g. the mock banner and "EXPLORATORY OVERRIDE").
    """
    stem.parent.mkdir(parents=True, exist_ok=True)
    banners = banners_of(mock)
    if banners:
        w_in, h_in = fig.get_size_inches()
        size = float(np.clip(min(w_in, 1.8 * h_in) * 3.2 / max(1, len(banners)) ** 0.5, 9, 30))
        wm = fig.text(0.5, 0.5, "\n".join(banners), rotation=np.degrees(np.arctan2(h_in, w_in)) * 0.8,
                      fontsize=size, color=CRITICAL, alpha=0.22, ha="center", va="center",
                      fontweight="bold", zorder=1000, transform=fig.transFigure)
        wm.set_in_layout(False)
        fig.suptitle("\n".join(banners) + ("\n" + title if title else ""), color=CRITICAL, fontsize=9,
                     fontweight="bold")
    elif title:
        fig.suptitle(title, fontsize=9, color=INK)
    texts = [t.get_text() for t in fig.texts]
    if fig._suptitle is not None:
        texts.append(fig._suptitle.get_text())
    FIGURE_TEXT_REGISTRY[str(stem)] = texts
    paths = [stem.with_suffix(".pdf"), stem.with_suffix(".png")]
    fig.savefig(paths[0], bbox_inches="tight")
    fig.savefig(paths[1], dpi=200, bbox_inches="tight")
    plt.close(fig)
    return paths


def _panel_grid(n: int, ncols_max: int = 3, w: float = 2.6, h: float = 4.6):
    ncols = min(n, ncols_max)
    nrows = int(np.ceil(n / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(w * ncols + 0.8, h * nrows), squeeze=False,
                             sharey=True)
    for ax in axes.ravel()[n:]:
        ax.set_visible(False)
    return fig, axes.ravel()


def coefficient_plot(coef: pd.DataFrame, outcome: str, condition: str, order: list[str],
                     stem: Path, mock: bool, pc: pd.DataFrame | None = None) -> list[Path]:
    """Per-origin difference to DEU with 95% CIs (thin) and simultaneous bands (light).

    The positive-control effect (yardstick, A7) is printed in each panel title.
    """
    d = coef[(coef["outcome"] == outcome) & (coef["condition"] == condition)]
    models = sorted(d["model"].unique())
    with plt.rc_context(RC):
        fig, axes = _panel_grid(len(models))
        codes = [c for c in order if c != REFERENCE and c in set(d["nationality"])]
        ypos = {c: k for k, c in enumerate(codes[::-1])}
        for ax, m in zip(axes, models):
            dm = d[d["model"] == m].set_index("nationality").reindex(codes)
            y = np.array([ypos[c] for c in codes])
            cols = [GROUP_COLORS.get(g, MUTED) for g in dm["group"]]
            ax.axvline(0, color=AXIS, lw=1)
            ax.hlines(y, dm["sim_ci_low"], dm["sim_ci_high"], color=GRID, lw=4, zorder=1)
            ax.hlines(y, dm["ci_low"], dm["ci_high"], color=cols, lw=1.2, zorder=2)
            ax.scatter(dm["estimate"], y, s=18, c=cols, zorder=3, edgecolor="white", linewidth=0.6)
            title = m
            if pc is not None and not pc.empty and condition == "baseline":
                r = pc[(pc["model"] == m) & (pc["outcome"] == outcome)]
                if len(r):
                    title += ("\npositive control: " f"{r['pc_effect'].iloc[0]:.1f} "
                              f"[{r['ci_low'].iloc[0]:.1f}, {r['ci_high'].iloc[0]:.1f}]")
            ax.set_title(title, fontsize=7.5, color=INK)
            ax.set_yticks(list(ypos.values()), list(ypos.keys()))
            ax.set_xlabel(f"difference vs {REFERENCE}")
            ax.grid(axis="y", visible=False)
        handles = [plt.Line2D([], [], marker="o", ls="", color=c, label=GROUP_LABELS[g]) for g, c in GROUP_COLORS.items()]
        handles.append(plt.Line2D([], [], color=GRID, lw=4, label="simultaneous 95% band"))
        fig.legend(handles=handles, loc="lower center", ncol=2, bbox_to_anchor=(0.5, -0.04))
        fig.tight_layout(rect=(0, 0.04, 1, 0.94))
        return finalize(fig, stem, mock, f"{OUTCOME_LABEL.get(outcome, outcome)} - {condition}")


def heterogeneity_plot(het: pd.DataFrame, outcome: str, stem: Path, mock: bool) -> list[Path]:
    """Debiased sigma_A (noncentral-F 95% CI) with the raw plug-in SD, its 95% null quantile and the SESOI."""
    d = het[het["outcome"] == outcome]
    models = sorted(d["model"].unique())
    conds = sorted(d["condition"].unique())
    with plt.rc_context(RC):
        fig, ax = plt.subplots(figsize=(max(4.8, 1.2 * len(models) + 2.0), 3.6))
        width = 0.7 / max(len(conds), 1)
        for k, c in enumerate(conds):
            dc = d[d["condition"] == c].set_index("model").reindex(models)
            x = np.arange(len(models)) - 0.35 + width * (k + 0.5)
            col = COND_COLORS.get(c, MUTED)
            ax.vlines(x, dc["ci_low"], dc["ci_high"], color=col, lw=1.4)
            ax.scatter(x, dc["sigma_A"], color=col, s=24, zorder=3, label=f"{c}: debiased sigma_A (95% CI)")
            ax.scatter(x, dc["sd_plugin"], facecolor="white", edgecolor=col, s=22, zorder=3, marker="D",
                       label=f"{c}: raw plug-in SD")
            ax.hlines(dc["sd_null_q95"], x - width / 2.5, x + width / 2.5, color=MUTED, lw=1.5,
                      label="raw SD: 95% quantile under no effect" if k == 0 else None)
            if "sigma_placebo" in dc and dc["sigma_placebo"].notna().any():
                ax.scatter(x, dc["sigma_placebo"], marker="x", color=INK2, s=26, zorder=4,
                           label="placebo nationalities: debiased SD" if k == 0 else None)
        if "sesoi" in d and d["sesoi"].notna().any():
            ax.axhline(float(d["sesoi"].iloc[0]), color=INK2, lw=0.8, ls="--", label="SESOI")
        ax.set_xticks(np.arange(len(models)), models, rotation=20, ha="right")
        ax.set_ylabel(f"SD across the 22 {ARAB_LABEL}\n({OUTCOME_LABEL.get(outcome, outcome)})", fontsize=7)
        ax.set_ylim(bottom=0)
        ax.legend(fontsize=6.5, loc="upper center", bbox_to_anchor=(0.5, -0.22), ncol=2)
        fig.tight_layout(rect=(0, 0, 1, 0.9))
        return finalize(fig, stem, mock, "Within-Arab heterogeneity (RQ1)")


def heatmap(coef: pd.DataFrame, outcome: str, condition: str, order: list[str], stem: Path,
            mock: bool) -> list[Path]:
    d = coef[(coef["outcome"] == outcome) & (coef["condition"] == condition)]
    M = d.pivot(index="nationality", columns="model", values="estimate")
    codes = [c for c in order if c in M.index]
    M = M.reindex(codes)
    lim = float(np.nanmax(np.abs(M.to_numpy()))) if M.size else 1.0
    lim = lim if lim > 0 else 1.0
    with plt.rc_context(RC | {"axes.grid": False}):
        fig, ax = plt.subplots(figsize=(1.0 * M.shape[1] + 2.2, 0.2 * M.shape[0] + 1.4))
        im = ax.imshow(M.to_numpy(), cmap=DIVERGING, vmin=-lim, vmax=lim, aspect="auto")
        ax.set_yticks(range(len(codes)), codes)
        ax.set_xticks(range(M.shape[1]), M.columns, rotation=20, ha="right")
        if M.shape[1] <= 8:
            for i in range(M.shape[0]):
                for j in range(M.shape[1]):
                    v = M.iat[i, j]
                    if np.isfinite(v):
                        ax.text(j, i, f"{v:.1f}", ha="center", va="center", fontsize=5.5, color=INK)
        cb = fig.colorbar(im, ax=ax, shrink=0.6)
        cb.set_label(f"difference vs {REFERENCE}")
        fig.tight_layout(rect=(0, 0, 1, 0.92))
        return finalize(fig, stem, mock, f"Nationality x model: {OUTCOME_LABEL.get(outcome, outcome)}, {condition}")


def prompt_comparison(coef: pd.DataFrame, outcome: str, order: list[str], stem: Path,
                      mock: bool, conditions=("baseline", "neutrality")) -> list[Path]:
    d = coef[(coef["outcome"] == outcome) & (coef["condition"].isin(conditions))]
    models = sorted(d["model"].unique())
    with plt.rc_context(RC):
        fig, axes = _panel_grid(len(models))
        codes = [c for c in order if c != REFERENCE and c in set(d["nationality"])]
        ypos = {c: k for k, c in enumerate(codes[::-1])}
        for ax, m in zip(axes, models):
            y = np.array([ypos[c] for c in codes])
            est = {c: d[(d["model"] == m) & (d["condition"] == c)].set_index("nationality")
                   .reindex(codes)["estimate"].to_numpy() for c in conditions}
            ax.axvline(0, color=AXIS, lw=1)
            if all(c in est for c in conditions):
                ax.hlines(y, np.fmin(*est.values()), np.fmax(*est.values()), color=GRID, lw=1.5)
            for c in conditions:
                ax.scatter(est[c], y, s=16, color=COND_COLORS.get(c, MUTED), zorder=3, label=c)
            ax.set_title(m, fontsize=8, color=INK)
            ax.set_yticks(list(ypos.values()), list(ypos.keys()))
            ax.set_xlabel(f"difference vs {REFERENCE}")
            ax.grid(axis="y", visible=False)
        h, lab = axes[0].get_legend_handles_labels()
        fig.legend(h, lab, loc="lower center", ncol=len(conditions), bbox_to_anchor=(0.5, -0.02))
        fig.tight_layout(rect=(0, 0.04, 1, 0.94))
        return finalize(fig, stem, mock, f"Baseline vs neutrality prompt: {OUTCOME_LABEL.get(outcome, outcome)}")


def bt_plot(bt: pd.DataFrame, order: list[str], stem: Path, mock: bool) -> list[Path]:
    """Bradley-Terry worth (log-odds vs DEU) with CV-bootstrap 95% CIs."""
    panels = bt[["model", "condition"]].drop_duplicates().sort_values(["model", "condition"])
    with plt.rc_context(RC):
        fig, axes = _panel_grid(len(panels))
        codes = [c for c in order if c in set(bt["nationality"])]
        ypos = {c: k for k, c in enumerate(codes[::-1])}
        for ax, (_, pnl) in zip(axes, panels.iterrows()):
            dm = bt[(bt["model"] == pnl["model"]) & (bt["condition"] == pnl["condition"])]
            dm = dm.set_index("nationality").reindex(codes)
            y = np.array([ypos[c] for c in codes])
            cols = [GROUP_COLORS.get(g, MUTED) for g in dm["group"]]
            ax.axvline(0, color=AXIS, lw=1)
            ax.hlines(y, dm["ci_low"], dm["ci_high"], color=cols, lw=1.2)
            ax.scatter(dm["beta"], y, s=18, c=cols, zorder=3, edgecolor="white", linewidth=0.6,
                       label="forced choice")
            if "beta_ie_implied" in dm and dm["beta_ie_implied"].notna().any():
                ax.scatter(dm["beta_ie_implied"], y, s=16, facecolor="white", edgecolor=INK2, zorder=3,
                           label="implied by independent scores")
            ax.set_title(f"{pnl['model']} | {pnl['condition']}", fontsize=7.5, color=INK)
            ax.set_yticks(list(ypos.values()), list(ypos.keys()))
            ax.set_xlabel("worth (log-odds), centred on the Arab mean")
            ax.grid(axis="y", visible=False)
        handles = [plt.Line2D([], [], marker="o", ls="", color=c, label=GROUP_LABELS[g])
                   for g, c in GROUP_COLORS.items() if g != "control"]
        handles.append(plt.Line2D([], [], marker="o", ls="", markerfacecolor="white", color=INK2,
                                  label="implied by independent scores"))
        fig.legend(handles=handles, loc="lower center", ncol=3, bbox_to_anchor=(0.5, -0.02))
        fig.tight_layout(rect=(0, 0.04, 1, 0.94))
        return finalize(fig, stem, mock, "Bradley-Terry nationality worth (forced choice)")


def status_table_figure(status: pd.DataFrame, stem: Path, mock: bool) -> list[Path]:
    """Share of calls per response status, by task x model x condition."""
    share_cols = [c for c in status.columns if c.startswith("share_")]
    labels = (status["task"] + " | " + status["model_alias"].astype(str) + " | "
              + status["prompt_condition"].astype(str)).tolist()
    M = status[share_cols].to_numpy(float) * 100
    with plt.rc_context(RC | {"axes.grid": False}):
        fig, ax = plt.subplots(figsize=(1.0 * len(share_cols) + 3.0, 0.3 * len(labels) + 1.3))
        ax.imshow(M, cmap=SEQUENTIAL, vmin=0, vmax=max(100.0, float(np.nanmax(M))), aspect="auto")
        ax.set_xticks(range(len(share_cols)), [c.replace("share_", "") for c in share_cols],
                      rotation=20, ha="right")
        ax.set_yticks(range(len(labels)), labels)
        for i in range(M.shape[0]):
            for j in range(M.shape[1]):
                v = M[i, j]
                ax.text(j, i, f"{v:.1f}%", ha="center", va="center", fontsize=6,
                        color="white" if v > 60 else INK)
        fig.tight_layout(rect=(0, 0, 1, 0.9))
        return finalize(fig, stem, mock, "Response status (share of calls)")
