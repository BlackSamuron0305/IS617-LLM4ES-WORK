"""Figures of the deep-dive from results/deep_dive/ablations_reference_family (written by pipeline.deep_dive.report): family, ablation, reference, negative.

    python -m pipeline.deep_dive.figures --name deep_dive/ablations_reference_family --out experiment/deep_dive/figures
"""

import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path

from pipeline.core.common import ROOT

ORDER = ["qwen2.5-0.5b-instruct", "qwen2.5-1.5b-instruct", "qwen2.5-3b-instruct", "qwen2.5-7b-instruct", "qwen2.5-14b-instruct",
         "qwen2.5-32b-instruct", "qwen2.5-72b-instruct", "qwen2-7b-instruct", "qwen3-4b", "qwen3-8b", "qwen3-14b", "qwen3-32b"]
NAME = {m: m.replace("-instruct", "").replace("qwen", "Qwen") for m in ORDER}
FOUR = ["qwen2.5-7b-instruct", "qwen3-32b", "gemma-4-31b-it", "mistral-small-3.2-24b-instruct"]
FOURN = {"qwen2.5-7b-instruct": "Qwen2.5 7B", "qwen3-32b": "Qwen3 32B", "gemma-4-31b-it": "Gemma 4 31B", "mistral-small-3.2-24b-instruct": "Mistral Small 24B"}
COL = ["#c0392b", "#1f6fb2", "#27ae60", "#e07b00"]


def table(folder, name):
    path = Path(folder) / f"{name}.csv"
    return list(csv.DictReader(open(path, encoding="utf-8", newline=""))) if path.exists() else []


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--name", default="deep_dive/ablations_reference_family")
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.family": "DejaVu Sans", "axes.spines.top": False, "axes.spines.right": False})
    res, out = ROOT / "results" / args.name, ROOT / args.out
    out.mkdir(parents=True, exist_ok=True)
    made = []

    fam = {r["model"]: r for r in table(res, "family")}
    if fam:
        names = [m for m in ORDER if m in fam]
        fig, ax = plt.subplots(figsize=(9, 4.6))
        vals = [float(fam[m]["gap_21"]) for m in names]
        ax.bar(range(len(names)), vals, color=["#c0392b" if v > 10 else "#8a8a8a" for v in vals])
        for i, v in enumerate(vals):
            ax.text(i, v + 0.5, f"{v:.1f}", ha="center", fontsize=9)
        ax.set_xticks(range(len(names)))
        ax.set_xticklabels([NAME[m] for m in names], rotation=45, ha="right")
        ax.set_ylabel("gap between the highest and lowest of the 21 nationalities (points)")
        ax.set_title("Qwen family: the large gap is one checkpoint, not size")
        fig.tight_layout()
        fig.savefig(out / "family.png", dpi=170)
        plt.close(fig)
        made.append("family")

    ab = {(r["model"], r["variant"]): r for r in table(res, "ablation")}
    variants = ["base", "no_nationality_line", "no_document_line", "home_country_line", "strict_officer", "lenient_officer", "fairness_first", "fairness_last", "reason_first"]
    if ab:
        fig, ax = plt.subplots(figsize=(10, 4.8))
        w = 0.2
        for k, m in enumerate(FOUR):
            ax.bar([i + (k - 1.5) * w for i in range(len(variants))], [float(ab[(m, v)]["range"]) if (m, v) in ab else 0 for v in variants], w, color=COL[k], label=FOURN[m])
        ax.set_xticks(range(len(variants)))
        ax.set_xticklabels(variants, rotation=35, ha="right")
        ax.set_ylabel("gap highest to lowest of the 21 (points, one repetition)")
        ax.set_title("Which line and which wording carries the passport effect?")
        ax.legend(frameon=False)
        ax.grid(axis="y", alpha=0.25)
        fig.tight_layout()
        fig.savefig(out / "ablation.png", dpi=170)
        plt.close(fig)
        made.append("ablation")

    ref = defaultdict(dict)
    for r in table(res, "reference"):
        ref[r["country"]][r["model"]] = float(r["mean"])
    if ref:
        order = ["Not stated", "Germany", "United States", "India", "Philippines", "Pakistan", "Qatar", "Jordan", "Syria", "Somalia"]
        fig, axes = plt.subplots(1, len(FOUR), figsize=(13, 4.6), sharey=True)
        for ax, m in zip(axes, FOUR):
            vals = [ref[c].get(m) for c in order]
            ax.barh(range(len(order)), [v if v is not None else 0 for v in vals], color=["#555" if c == "Not stated" else "#1f6fb2" if c in ("Germany", "United States") else "#e07b00" if c in ("Syria", "Somalia") else "#8a8a8a" for c in order])
            base = ref["Not stated"].get(m)
            if base:
                ax.axvline(base, color="black", lw=1, ls="--")
            lo = min(v for v in vals if v) - 3
            ax.set_xlim(lo, max(v for v in vals if v) + 2)
            ax.set_title(FOURN[m], fontsize=11)
            ax.invert_yaxis()
        axes[0].set_yticks(range(len(order)))
        axes[0].set_yticklabels(order)
        fig.suptitle("A baseline outside the 22: mean score by passport (dashed: no nationality stated)", fontsize=12)
        fig.tight_layout()
        fig.savefig(out / "reference.png", dpi=170)
        plt.close(fig)
        made.append("reference")

    eff = defaultdict(dict)
    for r in table(res, "negative_effect"):
        eff[r["model"]][r["group"]] = r
    if eff:
        names = [m for m in ORDER + ["gemma-4-31b-it", "mistral-small-3.2-24b-instruct", "gpt-oss-120b", "mistral-medium-3.5", "mistral-7b-instruct-v0.3", "falcon3-7b-instruct", "phi-3.5-mini-instruct", "olmo-2-7b-instruct"] if m in eff]
        names = sorted(set(names), key=lambda m: float(eff[m]["Syria"]["effect_main_block1"]))
        fig, ax = plt.subplots(figsize=(8, 6.5))
        for i, m in enumerate(names):
            main_, neg_ = float(eff[m]["Syria"]["effect_main_block1"]), float(eff[m]["Syria"]["effect_negative_block7"])
            ax.plot([main_, neg_], [i, i], color="#bbb", lw=1.5, zorder=1)
            ax.scatter(main_, i, color="#1f6fb2", s=45, zorder=2, label="normal applications" if i == 0 else None)
            ax.scatter(neg_, i, color="#c0392b", s=45, zorder=2, label="applications with a clear ground for refusal" if i == 0 else None)
        ax.axvline(0, color="#444", lw=0.8)
        ax.set_yticks(range(len(names)))
        ax.set_yticklabels([NAME.get(m, m) for m in names], fontsize=9)
        ax.set_xlabel("score of Syrian applications minus the average of the same application (points)")
        ax.set_title("Is a Syrian application with a real problem rated worse?")
        ax.legend(frameon=False, loc="lower right")
        fig.tight_layout()
        fig.savefig(out / "negative.png", dpi=170)
        plt.close(fig)
        made.append("negative")
    print("figures:", ", ".join(made), "->", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
