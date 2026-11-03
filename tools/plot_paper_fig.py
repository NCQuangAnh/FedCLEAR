"""Paper figures: accuracy of the five trained methods per setting, mean and spread over 5 seeds.

One panel per dataset (one row of the figure each). x = setting, y = last-10-round accuracy.
Each method is a marker at its mean with a +-1 sd bar (the spread shown in the tables); the five
seeds are drawn as small faint dots. ZS-CLIP is a dashed reference line (no training, no spread).
Markers are not joined: the settings are categories, not a continuous axis.

Usage: python tools/plot_paper_fig.py <scenario 1|2> <dataset> [<dataset> ...]
  e.g. python tools/plot_paper_fig.py 1 MNIST     -> paper/figs/s1_MNIST.pdf and .png
"""
import os
import statistics as st
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import analyze_baselines as ab

OUT = os.path.join(os.path.dirname(__file__), "..", "paper", "figs")
DS = {"Pets": "oxford_pets", "Caltech101": "caltech101", "MNIST": "mnist", "DTD": "dtd", "EuroSAT": "eurosat"}
# 2026-11-03, the user chose the original NLPrompt (uniform class prior) on every dataset;
# the client-histogram variant ("NLPrompt (hist)") is no longer in the paper
NLP = {n: "NLPrompt" for n in ("Pets", "Caltech101", "DTD", "MNIST", "EuroSAT")}
ZS = {"Pets": 85.69, "Caltech101": 85.76, "MNIST": 57.72, "DTD": 41.78, "EuroSAT": 26.11}
S1 = [("Sym.", ("S", "sym")), ("Pair.", ("S", "pair")), ("Inst.", ("S", "inst")),
      ("Varying", ("S", "het")), ("Clean", ("S", "clean"))]
S2 = [(f"{t}\n{r}%", ("N", f"{k}{r}")) for t, k in (("Sym.", "sym"), ("Pair.", "pair")) for r in (25, 50, 75)]
# name in the paper, key in analyze_baselines, colour (Okabe-Ito, colour-blind safe), marker
METHODS = [("FedProx", "FedProx", "#0072B2", "o"), ("FedCorr", "FedCorr", "#E69F00", "s"),
           ("PromptFL", "PromptFL", "#009E73", "^"), ("NLPrompt", None, "#CC79A7", "D"),
           ("FedRG", "FedRG", "#56B4E9", "v"),           # added 2026-11-03 (CVPR 2026 baseline)
           ("FedCLEAR (ours)", "CLEAR-FPL", "#D55E00", "*")]

plt.rcParams.update({
    "font.family": "serif", "font.serif": ["Times New Roman", "STIXGeneral"], "mathtext.fontset": "stix",
    "font.size": 8, "axes.labelsize": 8, "xtick.labelsize": 7.5, "ytick.labelsize": 7.5,
    "legend.fontsize": 7.5, "axes.linewidth": 0.6, "xtick.major.width": 0.6, "ytick.major.width": 0.6,
    "pdf.fonttype": 42, "ps.fonttype": 42, "savefig.dpi": 300,
})


def seeds(name, key, kind, setting):
    v = ab.last10(ab.tag(DS[name], key or NLP[name], kind, setting))
    assert v and len(v) == 5, (name, key, setting, v)
    return np.array(v)


def panel(ax, name, scenario, show_xlabels=True):
    rows = S1 if scenario == 1 else S2
    vals = [[seeds(name, key, *k) for _, key, _, _ in METHODS] for _, k in rows]
    # Avg.: per seed the mean over the settings, as in the tables
    vals.append([np.mean([vals[i][j] for i in range(len(rows))], axis=0) for j in range(len(METHODS))])
    labels = [lab for lab, _ in rows] + ["Avg."]
    n = len(METHODS)
    width = 0.78
    offs = (np.arange(n) - (n - 1) / 2) * width / n
    for i in range(len(labels)):
        if i % 2 == 1:
            ax.axvspan(i - 0.5, i + 0.5, color="#f2f2f2", zorder=0, lw=0)
    ax.axvline(len(rows) - 0.5, color="0.55", lw=0.6, zorder=1)          # separates Avg.
    ax.axhline(ZS[name], color="0.35", ls=(0, (4, 2)), lw=0.9, zorder=1)
    rng = np.random.default_rng(0)
    for i, group in enumerate(vals):
        for j, (lab, _, col, mk) in enumerate(METHODS):
            v = group[j]
            x = i + offs[j]
            ax.scatter(x + rng.uniform(-0.018, 0.018, len(v)), v, s=4, color=col, alpha=0.35, lw=0, zorder=2)
            ours = j == n - 1
            ax.errorbar(x, v.mean(), yerr=v.std(ddof=1), fmt=mk, color=col, ms=6.5 if ours else 3.8,
                        mec="black" if ours else col, mew=0.4 if ours else 0, elinewidth=1.0,
                        capsize=0, zorder=4 if ours else 3)
    ax.set_xlim(-0.5, len(labels) - 0.5)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels if show_xlabels else [])
    ax.tick_params(axis="x", length=0)
    ax.set_ylabel("Accuracy (%)")
    ax.grid(axis="y", color="0.85", lw=0.5, zorder=0)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.set_title(name, loc="left", fontsize=8.5, fontweight="bold", pad=3)
    return ax


def main():
    scenario, names = int(sys.argv[1]), sys.argv[2:]
    fig, axes = plt.subplots(len(names), 1, figsize=(4.8, 1.75 * len(names) + 0.45), squeeze=False)
    for k, name in enumerate(names):
        panel(axes[k][0], name, scenario, show_xlabels=k == len(names) - 1)
    handles = [plt.Line2D([], [], marker=mk, color=col, ls="", ms=6.5 if lab.startswith("FedCLEAR") else 4,
                          mec="black" if lab.startswith("FedCLEAR") else col,
                          mew=0.4 if lab.startswith("FedCLEAR") else 0, label=lab)
               for lab, _, col, mk in METHODS]
    handles.append(plt.Line2D([], [], color="0.35", ls=(0, (4, 2)), lw=0.9, label="ZS-CLIP"))
    fig.legend(handles=handles, loc="upper center", ncol=6, frameon=False, handletextpad=0.3,
               columnspacing=0.9, bbox_to_anchor=(0.5, 1.0))
    fig.tight_layout(rect=(0, 0, 1, 1 - 0.2 / fig.get_figheight()), h_pad=0.4)
    os.makedirs(OUT, exist_ok=True)
    base = os.path.join(OUT, f"s{scenario}_{'_'.join(names)}")
    fig.savefig(base + ".pdf", bbox_inches="tight", pad_inches=0.02)
    fig.savefig(base + ".png", bbox_inches="tight", pad_inches=0.02)
    print(os.path.abspath(base) + ".pdf / .png")


if __name__ == "__main__":
    main()
