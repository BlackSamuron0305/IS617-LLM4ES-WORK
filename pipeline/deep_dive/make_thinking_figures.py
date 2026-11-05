"""Two figures of the deep dive for the midterm slides and the report notes (2026-11-04). Exploratory.

  thinking_temperature.png  left: gap of the 21 nationalities with thinking off and on; right: gap against temperature
  conflict_countries.png    differences between nationalities (conflict against peaceful countries and others), with
                            95% intervals, per model

Data: results/deep_dive/thinking_and_temperature/ and results/deep_dive/significance_tests/.

    python -m pipeline.deep_dive.make_thinking_figures --style deck --out paper/second_presentation/figures
"""

import argparse
import csv
import sys
from pathlib import Path

from pipeline.analysis.make_figures import LABEL, STYLES
from pipeline.core.common import ROOT

LABEL = {**LABEL, "qwen3-14b": "Qwen3 14B", "qwen2-7b-instruct": "Qwen2 7B", "qwen2.5-14b-instruct": "Qwen2.5 14B"}


def table(path):
    with open(ROOT / path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def fig_thinking_temperature(plt, S, out):
    thinking = table("results/deep_dive/thinking_and_temperature/thinking.csv")
    temperature = table("results/deep_dive/thinking_and_temperature/temperature.csv")
    fig, (left, right) = plt.subplots(1, 2, figsize=(11.5, 4.6), gridspec_kw={"width_ratios": [1, 1.25]})
    off, on = S["bars"][0], S["bars"][2]
    families = ["qwen3-32b", "qwen3-14b", "gpt-oss-120b"]
    names = {"qwen3-32b": "Qwen3 32B", "qwen3-14b": "Qwen3 14B", "gpt-oss-120b": "gpt-oss-120b"}
    width = 0.36
    for i, fam in enumerate(families):
        rows = [r for r in thinking if r["model"] == fam]
        for j, (r, colour) in enumerate(zip(rows, (off, on))):
            x = i + (j - 0.5) * width
            left.bar(x, float(r["gap_21"]), width * 0.92, color=colour,
                     label=("thinking off (gpt-oss: effort low)" if j == 0 else "thinking on (gpt-oss: effort high)") if i == 0 else None)
            left.plot([x - width * 0.46, x + width * 0.46], [float(r["gap_chance_p95"])] * 2, color=S["chance"], lw=3,
                      label="gap that chance alone gives" if (i == 0 and j == 0) else None)
    left.set_xticks(range(len(families)), [names[f] for f in families])
    left.set_ylabel("gap, highest to lowest of the 21 (points)")
    left.legend(frameon=False, fontsize=9, loc="upper left")
    left.set_ylim(0, 8)
    left.set_title("Thinking on" if S["titles"] else "")
    models = ["qwen3-32b", "gemma-4-31b-it", "mistral-small-3.2-24b-instruct"]
    colours = dict(zip(models, S["bars"]))
    for m in models:
        rows = sorted((r for r in temperature if r["model"] == m), key=lambda r: float(r["temperature"]))
        xs = [float(r["temperature"]) for r in rows]
        ys = [float(r["gap_21"]) for r in rows]
        right.plot(xs, ys, "-o", color=colours[m], lw=2.2, ms=6, label=LABEL[m])
        right.plot(xs, [float(r["gap_chance_p95"]) for r in rows], ls="none", marker="_", ms=14, mew=2.5, color=S["chance"],
                   label="gap that chance alone gives" if m == models[0] else None)
        bad = [r for r in rows if float(r["share_unreadable"]) > 0.5]
        for r in bad:
            right.plot([float(r["temperature"])], [float(r["gap_21"])], "o", mfc="white", mec=colours[m], ms=8, mew=2)
            right.annotate("85% unreadable", (float(r["temperature"]), float(r["gap_21"])), xytext=(-70, 12), textcoords="offset points",
                           fontsize=9, color=S["line"])
    right.set_xlabel("temperature (audited runs: 0.7)")
    right.set_ylabel("gap (points)")
    right.set_xticks([0, 0.3, 0.7, 1.0, 1.5])
    right.set_ylim(0, 7)
    right.legend(frameon=False, fontsize=9, loc="upper left")
    right.text(1.5, 0.35, "Qwen2.5 7B: 30 to 33 at every temperature (not shown)", ha="right", fontsize=9, color=S["line"])
    right.set_title("Temperature" if S["titles"] else "")
    fig.tight_layout()
    fig.savefig(out / "thinking_temperature.png", dpi=170)
    plt.close(fig)


def fig_conflict(plt, S, out):
    pairs = [r for r in table("results/deep_dive/significance_tests/pairs.csv") if r["variant"] == "conflict_nationalities"]
    comps = [("Afghanistan - Nepal", "Afghanistan\nagainst Nepal"), ("Ukraine - Vietnam", "Ukraine\nagainst Vietnam"),
             ("Syria - conflict (4)", "Syria against the four\nconflict countries"), ("Syria - Jordan", "Syria\nagainst Jordan")]
    models = ["qwen3-32b", "gemma-4-31b-it", "mistral-small-3.2-24b-instruct", "qwen2-7b-instruct", "qwen2.5-14b-instruct"]
    colours = [S["bars"][0], S["bars"][2], S["bars"][1], S["line"], S["extra"]]
    fig, ax = plt.subplots(figsize=(8.6, 4.6))
    step = 0.15
    for k, (comp, label) in enumerate(comps):
        for j, m in enumerate(models):
            r = next((r for r in pairs if r["model"] == m and r["comparison"] == comp), None)
            if not r:
                continue
            y = k + (j - (len(models) - 1) / 2) * step
            d, lo, hi = float(r["diff"]), float(r["ci_lo"]), float(r["ci_hi"])
            ax.plot([lo, hi], [y, y], color=colours[j], lw=2.2, solid_capstyle="round")
            ax.plot([d], [y], "o", color=colours[j], ms=7, label=LABEL[m] if k == 0 else None)
    ax.axvline(0, color=S["line"], lw=1)
    ax.set_yticks(range(len(comps)), [c[1] for c in comps])
    ax.invert_yaxis()
    ax.set_xlabel("mean score difference in points (95% interval); negative = the first country scores lower\n"
                  "Qwen2.5 7B is off the scale: -25.5, -4.1, -8.8 and -26.5 points")
    ax.set_xlim(-9, 3)
    ax.legend(frameon=False, fontsize=9, loc="upper center", bbox_to_anchor=(0.45, -0.2), ncol=3)
    fig.tight_layout()
    fig.savefig(out / "conflict_countries.png", dpi=170)
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
    fig_thinking_temperature(plt, S, out)
    fig_conflict(plt, S, out)
    print("figures ->", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
