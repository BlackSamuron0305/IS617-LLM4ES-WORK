"""Figures from the summary tables in results/<name>/ (written by pipeline.summarize).

Needs matplotlib. Writes PNG files to the folder given by --out. A figure whose table is missing is
skipped. Standard colours: rich = blue, normal = grey, poor = orange, placebo = hollow.

Usage:
    python -m pipeline.make_figures --name main --out paper/second_presentation/figures
"""

import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path

from pipeline.common import ROOT

COLORS = {"rich": "#1f6fb2", "normal": "#8a8a8a", "poor": "#e07b00"}
MODELS = ["qwen3-32b", "mistral-small-3.2-24b-instruct", "gemma-4-31b-it"]
LABEL = {"qwen3-32b": "Qwen3 32B", "mistral-small-3.2-24b-instruct": "Mistral Small 3.2 24B", "gemma-4-31b-it": "Gemma 4 31B",
         "qwen2.5-7b-instruct": "Qwen2.5 7B", "falcon3-7b-instruct": "Falcon3 7B", "phi-3.5-mini-instruct": "Phi-3.5 mini 3.8B",
         "olmo-2-7b-instruct": "OLMo 2 7B", "mistral-7b-instruct-v0.3": "Mistral 7B", "gpt-oss-120b": "gpt-oss-120b"}
EXTRA_MODELS = ["qwen2.5-7b-instruct", "falcon3-7b-instruct", "phi-3.5-mini-instruct", "olmo-2-7b-instruct", "mistral-7b-instruct-v0.3", "gpt-oss-120b"]


def table(results, name):
    path = Path(results) / f"{name}.csv"
    if not path.exists():
        return None
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def fig_nationalities(plt, rows, out, models=None, fname="nationalities.png"):
    models = models or MODELS
    # One dot per nationality and model: mean score after removing the cell mean (block 1, base, no rule).
    rows = [r for r in rows if r["block"] == "1" and r["variant"] == "base" and r["visa_required"] == "yes"]
    avg = defaultdict(list)
    for r in rows:
        avg[r["country"]].append(float(r["centred_mean"]))
    order = sorted(avg, key=lambda c: sum(avg[c]) / len(avg[c]))
    fig, axes = plt.subplots(1, len(models), figsize=(4.3 * len(models), 7.2), sharey=True)
    for ax, model in zip(axes, models):
        data = {r["country"]: r for r in rows if r["model"] == model}
        for i, c in enumerate(order):
            if c not in data:
                continue
            r = data[c]
            placebo = r["group"] == "placebo"
            ax.scatter(float(r["centred_mean"]), i, s=70, facecolors="none" if placebo else COLORS[r["wealth_group"]],
                       edgecolors=COLORS[r["wealth_group"]], linewidths=1.8, zorder=3)
        ax.axvline(0, color="#444", lw=0.8)
        ax.set_title(LABEL[model], fontsize=13)
        ax.set_xlabel("score points above / below the average\nof the same application")
        ax.grid(axis="x", alpha=0.25)
    axes[0].set_yticks(range(len(order)))
    axes[0].set_yticklabels(order, fontsize=10)
    for k, g in enumerate(("rich", "normal", "poor")):
        axes[-1].scatter([], [], color=COLORS[g], label=g, s=60)
    axes[-1].scatter([], [], facecolors="none", edgecolors="#333", label="placebo (not Arab League)", s=60)
    axes[-1].legend(loc="lower right", frameon=False)
    fig.suptitle("Same application, different passport: how far each nationality moves the score", fontsize=14)
    fig.tight_layout()
    fig.savefig(out / fname, dpi=170)
    plt.close(fig)


def fig_wealth(plt, rows, out):
    rows = [r for r in rows if r["block"] == "1" and r["variant"] == "base" and r["group"] == "arab" and r["visa_required"] == "yes"]
    fig, axes = plt.subplots(1, 3, figsize=(11, 4.2), sharey=True)
    for ax, model in zip(axes, MODELS):
        for x, g in enumerate(("rich", "normal", "poor")):
            vals = [float(r["centred_mean"]) for r in rows if r["model"] == model and r["wealth_group"] == g]
            ax.scatter([x + (i - len(vals) / 2) * 0.03 for i in range(len(vals))], vals, color=COLORS[g], s=40, alpha=0.8)
            if vals:
                m = sum(vals) / len(vals)
                ax.hlines(m, x - 0.25, x + 0.25, color=COLORS[g], lw=3)
        ax.set_xticks(range(3))
        ax.set_xticklabels(["rich\n(5)", "normal\n(12)", "poor\n(4)"])
        ax.axhline(0, color="#444", lw=0.8)
        ax.set_title(LABEL[model])
        ax.grid(axis="y", alpha=0.25)
    axes[0].set_ylabel("score points relative to the same application")
    fig.suptitle("Do the models sort the Arab League countries by wealth?", fontsize=13)
    fig.tight_layout()
    fig.savefig(out / "wealth_groups.png", dpi=170)
    plt.close(fig)


def matplotlib_null():
    from matplotlib.ticker import NullLocator
    return NullLocator()


def fig_money(plt, rows, out):
    fig, ax = plt.subplots(figsize=(6.5, 4.4))
    for model, color in zip(MODELS, ("#c0392b", "#7f8c8d", "#1f6fb2")):
        pts = sorted((int(r["savings_aed"]), float(r["centred_mean"])) for r in rows if r["model"] == model)
        ax.plot([p[0] for p in pts], [p[1] for p in pts], marker="o", color=color, label=LABEL[model], lw=2)
    ax.axvline(2352, color="#444", ls="--", lw=1)
    ax.text(2420, ax.get_ylim()[0] + 1, "EUR 560 needed\nfor 8 days", fontsize=9, va="bottom")
    ax.set_xscale("log")
    ax.xaxis.set_minor_locator(matplotlib_null())
    ax.set_xticks([2000, 3000, 4500, 7000, 10500])
    ax.set_xticklabels(["2,000", "3,000", "4,500", "7,000", "10,500"])
    ax.set_xlabel("funds available for the trip (AED)")
    ax.set_ylabel("score points relative to the same application")
    ax.set_title("Does the score react to a real ground?")
    ax.legend(frameon=False)
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(out / "money.png", dpi=170)
    plt.close(fig)


def fig_variants(plt, rows, out):
    base = {(r["model"], r["block"]): r for r in rows if r["variant"] == "base"}
    variants = [v for v in dict.fromkeys(r["variant"] for r in rows if r["block"] == "4")]
    names = ["base (block 1)", "with the rule (block 2)"] + variants + ["boundary (block 5)", "boundary with rule (block 6)"]
    fig, ax = plt.subplots(figsize=(10, 5.2))
    width = 0.27
    for k, model in enumerate(MODELS):
        vals = []
        for n in names:
            if n == "base (block 1)":
                r = base.get((model, "1"))
            elif n == "with the rule (block 2)":
                r = base.get((model, "2"))
            elif n == "boundary (block 5)":
                r = base.get((model, "5"))
            elif n == "boundary with rule (block 6)":
                r = base.get((model, "6"))
            else:
                r = next((x for x in rows if x["model"] == model and x["variant"] == n), None)
            vals.append(float(r["range_rep1"]) if r and r.get("range_rep1", "") != "" else 0.0)
        ax.bar([i + (k - 1) * width for i in range(len(names))], vals, width, label=LABEL[model])
        nulls = []
        for n in names:
            key = {"base (block 1)": "1", "with the rule (block 2)": "2", "boundary (block 5)": "5", "boundary with rule (block 6)": "6"}.get(n)
            r_ = base.get((model, key)) if key else next((x for x in rows if x["model"] == model and x["variant"] == n), None)
            nulls.append(float(r_["null_range_rep1"]) if r_ and r_.get("null_range_rep1", "") != "" else None)
        for i, v in enumerate(nulls):
            if v is not None:
                ax.hlines(v, i + (k - 1) * width - width / 2, i + (k - 1) * width + width / 2, color="black", lw=2)
    ax.set_xticks(range(len(names)))
    ax.set_xticklabels(names, rotation=40, ha="right")
    ax.set_ylabel("gap highest to lowest of the 21 nationalities,\none repetition (points)")
    ax.set_title("What shrinks or grows the gap?  (black tick: the gap chance alone gives)")
    ax.legend(frameon=False)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(out / "variants.png", dpi=170)
    plt.close(fig)


def fig_models(plt, audited, extra, out):
    # One bar per model: the gap between the highest and the lowest of the 21 nationalities (block 1, all repetitions).
    rows = []
    for table_rows, tag in ((audited, "audited"), (extra, "extra")):
        for r_ in table_rows:
            if r_["block"] == "1" and r_["variant"] == "base":
                rows.append((float(r_["range"]), r_["model"], tag, float(r_["null_range_rep1"]) if r_.get("null_range_rep1") else None))
    rows.sort()
    fig, ax = plt.subplots(figsize=(9, 4.8))
    for i, (v, m, tag, _) in enumerate(rows):
        ax.barh(i, v, color="#1f6fb2" if tag == "audited" else "#8a8a8a")
        ax.text(v + 0.3, i, f"{v:.1f}", va="center", fontsize=10)
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([LABEL.get(m, m) for _, m, _, _ in rows])
    ax.set_xlabel("gap between the highest and the lowest of the 21 nationalities (score points)")
    ax.set_title("How big is the passport gap, model by model?")
    ax.barh([], [], color="#1f6fb2", label="audited models")
    ax.barh([], [], color="#8a8a8a", label="extra models (exploratory)")
    ax.legend(frameon=False, loc="lower right")
    ax.grid(axis="x", alpha=0.25)
    fig.tight_layout()
    fig.savefig(out / "models.png", dpi=170)
    plt.close(fig)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--name", default="main")
    parser.add_argument("--out", required=True)
    parser.add_argument("--extra", help="name of a second results folder with the extra models (results/<name>)")
    args = parser.parse_args(argv)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.family": "DejaVu Sans", "axes.spines.top": False, "axes.spines.right": False})
    results = ROOT / "results" / args.name
    out = ROOT / args.out
    out.mkdir(parents=True, exist_ok=True)
    made = []
    for name, function, key in (("nationalities", fig_nationalities, "by_country"), ("wealth", fig_wealth, "by_country"),
                                ("money", fig_money, "by_savings"), ("variants", fig_variants, "by_variant")):
        rows = table(results, key)
        if rows:
            function(plt, rows, out)
            made.append(name)
    if args.extra:
        extra_dir = ROOT / "results" / args.extra
        ex_country, ex_variant = table(extra_dir, "by_country"), table(extra_dir, "by_variant")
        if ex_country:
            fig_nationalities(plt, ex_country, out, EXTRA_MODELS[:3], "nationalities_extra_a.png")
            fig_nationalities(plt, ex_country, out, EXTRA_MODELS[3:], "nationalities_extra_b.png")
            made += ["nationalities_extra"]
        if ex_variant and table(results, "by_variant"):
            fig_models(plt, table(results, "by_variant"), ex_variant, out)
            made += ["models"]
    print("figures:", ", ".join(made), "->", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
