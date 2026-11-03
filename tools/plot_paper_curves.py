"""Paper figures: test accuracy per round, mean over 5 seeds, shaded band = +-1 sd.

Scenario 1: one row per setting (experiment), one column per dataset.
Scenario 2: per dataset two rows, symmetric noise on top and pairwise below, 25/50/75% across.
The lightly shaded window marks rounds 41-50, the last 10 rounds whose mean the tables report.
ZS-CLIP is a dashed reference line.
Colours and markers match tools/plot_paper_fig.py (Okabe-Ito, colour-blind safe; a marker every
10 rounds so the curves stay apart in black and white).

Usage: python tools/plot_paper_curves.py <scenario 1|2> <dataset> [<dataset> ...]
  e.g. python tools/plot_paper_curves.py 1 MNIST   -> paper/figs/curves_s1_MNIST.pdf and .png
"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import analyze_baselines as ab
from plot_paper_fig import DS, METHODS, NLP, OUT, ZS

S1 = [("Sym.", ("S", "sym")), ("Pair.", ("S", "pair")), ("Inst.", ("S", "inst")),
      ("Varying", ("S", "het")), ("Clean", ("S", "clean"))]
S2 = [(f"{t} {r}%", ("N", f"{k}{r}")) for t, k in (("Sym.", "sym"), ("Pair.", "pair")) for r in (25, 50, 75)]
PANEL_W, PANEL_H = 1.6, 1.15        # inches; three columns fill the LNCS text width (12.2 cm)


def curves(name, key, kind, setting):
    """seeds x 51 rounds of test accuracy"""
    path = ab.find_log(ab.tag(DS[name], key or NLP[name], kind, setting))
    assert path, (name, key, setting)
    seeds, cur = [], None
    for line in open(path, encoding="utf-8", errors="replace"):
        m = ab.ROUND_RE.search(line)
        if m:
            if int(m.group(1)) == 0:
                cur = []
                seeds.append(cur)
            if cur is not None:
                cur.append(float(m.group(2)))
    seeds = [s for s in seeds if len(s) == 51]
    assert len(seeds) == 5, (name, key, setting, len(seeds))
    return np.array(seeds)


def panel(ax, name, label, kind, setting, first_col, last_row):
    ax.axvspan(40.5, 50.5, color="#ededed", lw=0, zorder=0)
    ax.axhline(ZS[name], color="0.35", ls=(0, (4, 2)), lw=0.8, zorder=1)
    x = np.arange(51)
    for j, (lab, key, col, mk) in enumerate(METHODS):
        a = curves(name, key, kind, setting)
        m, sd = a.mean(axis=0), a.std(axis=0, ddof=1)
        ours = j == len(METHODS) - 1
        ax.fill_between(x, m - sd, m + sd, color=col, alpha=0.18 if ours else 0.12, lw=0, zorder=2)
        ax.plot(x, m, color=col, lw=1.3 if ours else 0.8, marker=mk, markevery=(0, 10),
                ms=4.5 if ours else 2.6, mec="black" if ours else col, mew=0.3 if ours else 0,
                zorder=5 if ours else 3)
    ax.set_xlim(0, 50.5)
    ax.set_xticks(range(0, 51, 10))
    if not last_row:
        ax.set_xticklabels([])
    else:
        ax.set_xlabel("Round")
    if first_col:
        ax.set_ylabel("Accuracy (%)")
    ax.set_title(f"{name} · {label}", loc="left", fontsize=7.5, pad=2)
    ax.grid(axis="y", color="0.88", lw=0.4, zorder=0)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


def main():
    scenario, names = int(sys.argv[1]), sys.argv[2:]
    plt.rcParams.update({"xtick.labelsize": 6.5, "ytick.labelsize": 6.5, "axes.labelsize": 7.5,
                         "legend.fontsize": 7})
    if scenario == 1:            # grid[r][c] = (dataset, label, kind, setting)
        grid = [[(name,) + (lab,) + k for name in names] for lab, k in S1]
    else:
        grid = [[(name, f"{t} {r}%", "N", f"{k}{r}") for r in (25, 50, 75)]
                for name in names for t, k in (("Sym.", "sym"), ("Pair.", "pair"))]
    rows, cols = len(grid), len(grid[0])
    fig, axes = plt.subplots(rows, cols, squeeze=False,
                             figsize=(max(PANEL_W * cols, 2.4), PANEL_H * rows + 0.5))
    for r in range(rows):
        for c in range(cols):
            panel(axes[r][c], *grid[r][c], c == 0, r == rows - 1)
    handles = [plt.Line2D([], [], color=col, marker=mk, lw=1.3 if lab.startswith("FedCLEAR") else 0.8,
                          ms=4.5 if lab.startswith("FedCLEAR") else 2.6,
                          mec="black" if lab.startswith("FedCLEAR") else col,
                          mew=0.3 if lab.startswith("FedCLEAR") else 0, label=lab)
               for lab, _, col, mk in METHODS]
    handles.append(plt.Line2D([], [], color="0.35", ls=(0, (4, 2)), lw=0.8, label="ZS-CLIP"))
    ncol = 6 if cols >= 3 else 3
    fig.legend(handles=handles, loc="upper center", ncol=ncol, frameon=False, handletextpad=0.3,
               columnspacing=0.8, handlelength=1.6, bbox_to_anchor=(0.5, 1.0))
    top = (0.22 if ncol == 6 else 0.36) / fig.get_figheight()
    fig.tight_layout(rect=(0, 0, 1, 1 - top), h_pad=0.5, w_pad=0.6)
    os.makedirs(OUT, exist_ok=True)
    base = os.path.join(OUT, f"curves_s{scenario}_{'_'.join(names)}")
    fig.savefig(base + ".pdf", bbox_inches="tight", pad_inches=0.02)
    fig.savefig(base + ".png", bbox_inches="tight", pad_inches=0.02)
    print(os.path.abspath(base) + ".pdf / .png")


if __name__ == "__main__":
    main()
