"""Fig. 1 of the paper (motivation): PromptFL with 10 clean clients vs 3 of 10 clients with 40%
symmetric noise, and zero-shot CLIP, on Pets and Caltech101.

Replaces Figs/NoiseImpact.png, whose clean bars were 87.88 (FedProx's clean Pets value) and 90.21
(FedCLEAR's clean Caltech101 value) instead of PromptFL's own 87.65 and 89.95. All values are read
from the logs (last10, mean of 5 seeds) like the tables.

Usage: python tools/plot_noise_impact.py <out.pdf>
"""
import os
import statistics as st
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(__file__))
import analyze_baselines as ab

DATA = [("Pets", "oxford_pets", 85.69), ("Caltech101", "caltech101", 85.76)]


def mean(ds, sc):
    return st.fmean(ab.last10(ab.tag(ds, "PromptFL", "S", sc)))


def main():
    plt.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman", "STIXGeneral"],
                         "mathtext.fontset": "stix", "font.size": 8, "pdf.fonttype": 42})
    fig, ax = plt.subplots(figsize=(4.8, 2.4))
    w = 0.26
    cols = ["#0072B2", "#D55E00", "0.55"]
    labels = ["PromptFL, all clients clean", "PromptFL, 3 of 10 clients noisy",
              "Zero-shot CLIP"]
    for i, (name, ds, zs) in enumerate(DATA):
        vals = [mean(ds, "clean"), mean(ds, "sym"), zs]
        for j, v in enumerate(vals):
            x = i + (j - 1) * w
            ax.bar(x, v, w, color=cols[j], label=labels[j] if i == 0 else None, zorder=2)
            ax.text(x, v + 0.25, f"{v:.2f}", ha="center", va="bottom", fontsize=7)
        drop = vals[1] - vals[0]
        ax.text(i, vals[1] - 0.6, f"{drop:+.2f}", ha="center", va="top", fontsize=7.5,
                fontweight="bold", color="white")
    ax.set_xticks(range(len(DATA)))
    ax.set_xticklabels([d[0] for d in DATA])
    ax.set_ylim(70, 92)
    ax.set_ylabel("Accuracy (%)")
    ax.grid(axis="y", color="0.9", lw=0.5, zorder=0)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.legend(frameon=False, fontsize=6.8, loc="lower center", ncol=3, bbox_to_anchor=(0.5, 1.0),
              handlelength=1.2, columnspacing=0.9)
    fig.tight_layout()
    fig.savefig(sys.argv[1], bbox_inches="tight", pad_inches=0.02)
    print(sys.argv[1])


if __name__ == "__main__":
    main()
