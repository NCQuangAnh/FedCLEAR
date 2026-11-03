"""Paper figures: test accuracy per round, same layout as tools/plot_paper_curves.py but easier to read.

Changes asked by the supervisor ("too many rounds, the margin of FedCLEAR is not visible"):
  - one point every 5 rounds, each the mean of the 5 rounds it closes (and of the 5 seeds);
  - no +-1 sd bands; the baselines thin and light, FedCLEAR thick on top;
  - at the right end of each panel, FedCLEAR's margin over the best trained baseline on the
    last-10-round accuracy of the tables (red when ahead, grey when behind).
The shaded window marks rounds 41-50, the last 10 rounds whose mean the tables report.

Both scenarios are now zoomed (2026-11-02, the user asked): rounds 41-50 only (the last-10 window of the tables), every round, with the
+-1 sd bands of the first version, and the y-axis fitted to the mean curves.

FedCLEAR's arm (2026-11-03): --arm=gatef plots CLEAR-v2 (gatef); a setting without a gatef run falls
back to CLEAR-FPL v1, which gatef equals when its gate stays off (as make_paper_tables.py does). The
legend says "FedCLEAR" (no "(ours)").

Usage: python tools/plot_paper_curves2.py <scenario 1|2> <dataset> [<dataset> ...] [--arm=gatef]
  -> results/side-research/figures/curves/curves_s<scenario>_<datasets>.pdf (PDF only, for Overleaf)
"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import analyze_baselines as ab
from analyze_calrepair import tag as arm_tag
from plot_paper_curves import DS, PANEL_H, PANEL_W, S1, curves
from plot_paper_fig import METHODS, ZS

METHODS = [(("FedCLEAR" if lab.startswith("FedCLEAR") else lab), key, col, mk) for lab, key, col, mk in METHODS]
ARM = "clear"       # set from --arm=


def ours_curves(name, kind, setting):
    """seeds x 51 for FedCLEAR: the chosen arm, else CLEAR-FPL v1"""
    if ARM != "clear" and ab.find_log(arm_tag(DS[name], kind, setting, ARM)):
        path = ab.find_log(arm_tag(DS[name], kind, setting, ARM))
        seeds, cur = [], None
        for line in open(path, encoding="utf-8", errors="replace"):
            m = ab.ROUND_RE.search(line)
            if m:
                if int(m.group(1)) == 0:
                    cur = []
                    seeds.append(cur)
                if cur is not None:
                    cur.append(float(m.group(2)))
        seeds = [x for x in seeds if len(x) == 51]
        assert len(seeds) == 5, (name, setting, len(seeds))
        return np.array(seeds)
    return curves(name, "CLEAR-FPL", kind, setting)

OUT = os.path.join(os.path.dirname(__file__), "..", "results", "side-research", "figures", "curves")
STEP = 5
START = 41          # scenario 1: the last 10 rounds only, the window the tables average
OURS = "#C0392B"


def coarse(a):
    """seeds x 51 -> mean over seeds at rounds 0, 5, ..., 50; round r averages rounds r-4..r"""
    m = a.mean(axis=0)
    return np.array([m[0]] + [m[r - STEP + 1:r + 1].mean() for r in range(STEP, 51, STEP)])


def panel(ax, name, label, kind, setting, first_col, last_row, zoom=False):
    """zoom (scenario 1): rounds 41-50 only, every round, +-1 sd bands, y-axis fitted to the means."""
    if not zoom:
        ax.axvspan(40.5, 51, color="#ededed", lw=0, zorder=0)
    ax.axhline(ZS[name], color="0.35", ls=(0, (4, 2)), lw=0.8, zorder=1)
    x = np.arange(START, 51) if zoom else np.arange(0, 51, STEP)
    last, means = [], []
    for j, (lab, key, col, mk) in enumerate(METHODS):
        ours = j == len(METHODS) - 1
        a = ours_curves(name, kind, setting) if ours else curves(name, key, kind, setting)
        last.append(a[:, 41:].mean())
        if zoom:
            m, sd = a.mean(axis=0)[START:], a.std(axis=0, ddof=1)[START:]
            ax.fill_between(x, m - sd, m + sd, color=OURS if ours else col, alpha=0.18 if ours else 0.10,
                            lw=0, zorder=2)
            every = 3                   # markers at the x ticks only: 41, 44, 47, 50
        else:
            m, every = coarse(a), None
        means.append(m)
        if ours:
            ax.plot(x, m, color=OURS, lw=2.0, marker="*", ms=6.5, mec="black", mew=0.35, markevery=every, zorder=5)
        else:
            ax.plot(x, m, color=col, lw=0.8, marker=mk, ms=2.6, alpha=0.75, markevery=every, zorder=3)
    gap = last[-1] - max(last[:-1])
    ax.annotate(f"{gap:+.1f}", (50, means[-1][-1]), xytext=(5, 0), textcoords="offset points", va="center",
                ha="left", fontsize=7, fontweight="bold", color=OURS if gap >= 0 else "0.45",
                annotation_clip=False)
    if zoom:
        lo, hi = min(v.min() for v in means), max(v.max() for v in means)
        pad = max(0.4, 0.15 * (hi - lo))
        ax.set_ylim(lo - pad, hi + pad)
        ax.yaxis.set_major_locator(MaxNLocator(nbins=5, steps=[1, 2, 2.5, 5]))
        ax.set_xlim(START - 0.3, 50.3)
        ax.set_xticks(range(START, 51, 3))
    else:
        ax.set_xlim(0, 51)
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
    global ARM
    args = [a for a in sys.argv[1:] if not a.startswith("--arm=")]
    ARM = next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--arm=")), "clear")
    scenario, names = int(args[0]), args[1:]
    plt.rcParams.update({"xtick.labelsize": 6.5, "ytick.labelsize": 6.5, "axes.labelsize": 7.5,
                         "legend.fontsize": 7})
    if scenario == 1:
        grid = [[(name,) + (lab,) + k for name in names] for lab, k in S1]
    else:
        grid = [[(name, f"{t} {r}%", "N", f"{k}{r}") for r in (25, 50, 75)]
                for name in names for t, k in (("Sym.", "sym"), ("Pair.", "pair"))]
    rows, cols = len(grid), len(grid[0])
    fig, axes = plt.subplots(rows, cols, squeeze=False,
                             figsize=(max(PANEL_W * cols, 2.4) + 0.25 * cols, PANEL_H * rows + 0.5))
    for r in range(rows):
        for c in range(cols):
            panel(axes[r][c], *grid[r][c], c == 0, r == rows - 1, zoom=True)
    handles = [plt.Line2D([], [], color=OURS, marker="*", lw=2.0, ms=6.5, mec="black", mew=0.35, label=lab)
               if lab.startswith("FedCLEAR") else
               plt.Line2D([], [], color=col, marker=mk, lw=0.8, ms=2.6, alpha=0.7, label=lab)
               for lab, _, col, mk in METHODS]
    handles.append(plt.Line2D([], [], color="0.35", ls=(0, (4, 2)), lw=0.8, label="ZS-CLIP"))
    ncol = 7 if cols >= 3 else 4
    fig.legend(handles=handles, loc="upper center", ncol=ncol, frameon=False, handletextpad=0.3,
               columnspacing=0.8, handlelength=1.6, bbox_to_anchor=(0.5, 1.0))
    top = (0.22 if ncol == 7 else 0.36) / fig.get_figheight()
    fig.tight_layout(rect=(0, 0, 1, 1 - top), h_pad=0.5, w_pad=1.2)
    os.makedirs(OUT, exist_ok=True)
    base = os.path.join(OUT, f"curves_s{scenario}_{'_'.join(names)}")
    fig.savefig(base + ".pdf", bbox_inches="tight", pad_inches=0.02)
    if os.environ.get("PREVIEW"):            # PNG for checking only, outside the figure folder
        fig.savefig(os.path.join(os.environ["PREVIEW"], os.path.basename(base) + ".png"),
                    bbox_inches="tight", pad_inches=0.02, dpi=200)
    print(os.path.abspath(base) + ".pdf")


if __name__ == "__main__":
    main()
