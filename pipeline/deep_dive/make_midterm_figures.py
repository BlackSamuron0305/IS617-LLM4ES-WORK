"""Figures of the redesigned midterm deck (2026-11-08): the base values and the deep-dive results in plain pictures. Exploratory.

  base_scores.png     how often each score is given (block 1 of the audited runs): the scores sit near the top
  profile_scores.png  mean score of plain applications and of applications with one or two weak points
  negative_scores.png mean score on normal applications and on applications with one clear ground for refusal
  ablation.png        gap among the 21 nationalities when a line or a sentence of the prompt is changed

Data: data/processed (audited main run) and results/deep_dive/ablations_reference_family/.

    python -m pipeline.deep_dive.make_midterm_figures --style deck --out paper/second_presentation/figures
"""

import argparse
import csv
import statistics
import sys
from collections import defaultdict

from pipeline.analysis.make_figures import LABEL, STYLES
from pipeline.core.common import ROOT, batch_dir, DATA
from pathlib import Path

AUDITED = ["qwen3-32b", "mistral-small-3.2-24b-instruct", "gemma-4-31b-it"]
LABEL = {**LABEL, "qwen2.5-72b-instruct": "Qwen2.5 72B", "qwen2.5-7b-instruct": "Qwen2.5 7B"}
DD = ROOT / "results" / "deep_dive" / "ablations_reference_family"


def table(path):
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def block1(model):
    path = batch_dir(Path(DATA), "processed", f"main_{model}") / "answers.csv"
    return [r for r in table(path) if r["block"] == "1" and r["variant"] == "base" and r["parse_status"] == "ok"]


def fig_base_scores(plt, S, out):
    fig, axes = plt.subplots(1, 3, figsize=(11.5, 3.9), sharey=True)
    for ax, m, colour in zip(axes, AUDITED, S["bars"]):
        scores = [float(r["visa_score"]) for r in block1(m)]
        ax.hist(scores, bins=range(0, 105, 5), color=colour, edgecolor="white", weights=[100 / len(scores)] * len(scores))
        share = sum(s >= 80 for s in scores) / len(scores) * 100
        ax.axvspan(80, 100, color=S["chance"], alpha=0.07, lw=0)
        ax.set_title(f"{LABEL[m]}\n{share:.0f}% of the scores are 80 or more", fontsize=12)
        ax.set_xlabel("visa score (0 = refuse, 100 = grant)")
        ax.set_xlim(0, 100)
    axes[0].set_ylabel("share of answers (%)")
    fig.tight_layout()
    fig.savefig(out / "base_scores.png", dpi=170)
    plt.close(fig)


def fig_profile_scores(plt, S, out):
    names = [("plain", "plain application"), ("one_indicator", "one weak point"), ("two_indicators", "two weak points")]
    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    width = 0.26
    for j, (m, colour) in enumerate(zip(AUDITED, S["bars"])):
        rows = block1(m)
        for i, (key, _label) in enumerate(names):
            vals = [float(r["visa_score"]) for r in rows if r["file_profile"] == key]
            v = statistics.fmean(vals)
            x = i + (j - 1) * width
            ax.bar(x, v, width * 0.92, color=colour, label=LABEL[m] if i == 0 else None)
            ax.text(x, v + 0.8, f"{v:.0f}", ha="center", fontsize=10)
    ax.set_xticks(range(3), [n[1] for n in names])
    ax.set_ylim(50, 100)
    ax.set_ylabel("mean score")
    ax.legend(frameon=False, fontsize=10, loc="lower left")
    fig.tight_layout()
    fig.savefig(out / "profile_scores.png", dpi=170)
    plt.close(fig)


def fig_negative(plt, S, out):
    neg = table(DD / "negative.csv")
    base = {r["model"]: float(r["mean_score"]) for r in table(DD / "ablation.csv") if r["variant"] == "base"}
    models = ["gemma-4-31b-it", "mistral-small-3.2-24b-instruct", "gpt-oss-120b", "qwen2.5-72b-instruct", "qwen2.5-7b-instruct", "qwen3-32b"]
    means = {}
    for m in models:
        rows = [r for r in neg if r["model"] == m]
        means[m] = sum(float(r["mean"]) * int(r["n"]) for r in rows) / sum(int(r["n"]) for r in rows)
    models.sort(key=lambda m: means[m])
    fig, ax = plt.subplots(figsize=(7.4, 4.4))
    for i, m in enumerate(models):
        ax.plot([means[m], base[m]], [i, i], color=S["extra"], lw=4, solid_capstyle="round", zorder=1)
        ax.scatter([base[m]], [i], s=110, color=S["bars"][0], zorder=2, label="normal applications" if i == 0 else None)
        ax.scatter([means[m]], [i], s=110, color=S["chance"], zorder=2, label="one clear ground for refusal" if i == 0 else None)
        ax.text(means[m] - 2, i, f"{means[m]:.0f}", ha="right", va="center", fontsize=10)
    ax.set_yticks(range(len(models)), [LABEL[m] for m in models])
    ax.set_xlim(0, 100)
    ax.set_xlabel("mean score")
    ax.legend(frameon=False, fontsize=10, loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=2)
    fig.tight_layout()
    fig.savefig(out / "negative_scores.png", dpi=170)
    plt.close(fig)


def fig_ablation(plt, S, out):
    rows = table(DD / "ablation.csv")
    models = ["qwen3-32b", "gemma-4-31b-it", "mistral-small-3.2-24b-instruct", "qwen2.5-7b-instruct"]
    variants = [("base", "as run"), ("no_nationality_line", "no nationality line"), ("no_document_line", "no passport line"),
                ("home_country_line", "home country stated"), ("fairness_first", "fairness sentence"), ("reason_first", "reason first"),
                ("lenient_officer", "lenient role"), ("strict_officer", "strict role")]
    fig, axes = plt.subplots(1, 4, figsize=(12.4, 4.6))
    for ax, m in zip(axes, models):
        vals = []
        for key, _l in variants:
            r = next(r for r in rows if r["model"] == m and r["variant"] == key)
            vals.append(float(r["range"]))
        colours = [S["bars"][0] if k == "base" else (S["bars"][2] if k in ("no_document_line", "reason_first") else S["bars"][1]) for k, _l in variants]
        ax.barh(range(len(vals)), vals, color=colours)
        for i, v in enumerate(vals):
            ax.text(v + max(vals) * 0.02, i, f"{v:.1f}", va="center", fontsize=9)
        ax.set_yticks(range(len(vals)), [l for _k, l in variants] if m == models[0] else [""] * len(vals))
        ax.invert_yaxis()
        ax.set_xlim(0, max(vals) * 1.18)
        ax.set_title(LABEL[m], fontsize=12)
        ax.set_xlabel("gap (points)")
    fig.tight_layout()
    fig.savefig(out / "ablation.png", dpi=170)
    plt.close(fig)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--out", required=True)
    parser.add_argument("--style", choices=sorted(STYLES), default="paper")
    args = parser.parse_args(argv)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    S = STYLES[args.style]
    plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False, **S["rc"]})
    out = ROOT / args.out
    out.mkdir(parents=True, exist_ok=True)
    for f in (fig_base_scores, fig_profile_scores, fig_negative, fig_ablation):
        f(plt, S, out)
    print("figures ->", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
