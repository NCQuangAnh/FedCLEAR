"""Shot study figure for the paper (supervisor's "Few-shot learning analysis", PAKDD_12pages.tex):
PromptFL and FedCLEAR average accuracy per scenario against the number of labelled images per class.

Accuracy = mean of the last 10 rounds per seed, mean over 5 seeds, then averaged over the settings of a
scenario (5 in Scenario 1, 6 in Scenario 2), as in the tables. A point is drawn only when every setting
of the scenario is available; a setting with fewer than 5 seeds is used and reported.

Sources: 8 shots = the paper runs (FedCLEAR arm gatef, PromptFL); 16/32/64 shots = results/<n>-shot/
(arms gatefcn<n> / pflcn<n>); full data = results/full/ (arms gatefcnfull / pflcnfull) when present.
EuroSAT starts at 16 shots: its 8-shot runs used the raw folder class names, the later ones the CoOp
names, so the 8-shot point is not comparable. DTD has 60 training images per class, so its 64-shot
point is its full data.

Usage: python tools/plot_shot_study.py <out_dir>     (writes ShotStudy.pdf and ShotStudy.png)
"""
import os
import statistics as st
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(__file__))
import analyze_s16 as a16
import make_paper_tables as mp

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAMES = ["Pets", "Caltech101", "DTD", "MNIST", "EuroSAT"]
SHOTS = [8, 16, 32, 64, "full"]
SCEN = {"Scenario 1": mp.S1, "Scenario 2": mp.S2}
ARM = {("FedCLEAR", 32): "gatefcn32", ("PromptFL", 32): "pflcn32", ("FedCLEAR", 64): "gatefcn64",
       ("PromptFL", 64): "pflcn64", ("FedCLEAR", "full"): "gatefcnfull", ("PromptFL", "full"): "pflcnfull"}


def seeds(name, method, kind, s, shot):
    if shot == 8:
        return None if name == "EuroSAT" else a16.s8(name, method, kind, s)
    if shot == 16:
        return a16.s16(name, method, kind, s)
    if name == "DTD" and shot == 64:
        return None
    d = "full" if shot == "full" else f"{shot}-shot"
    p = os.path.join(ROOT, "results", d, name, method, "logs", f"{mp.DS[name]}_{kind}_{s}_{ARM[method, shot]}.txt")
    return a16.last10(p) if os.path.exists(p) else None


def point(name, method, scen, shot):
    vals = []
    for kind, s in SCEN[scen]:
        v = seeds(name, method, kind, s, shot)
        if not v:
            return None
        if len(v) < 5:
            print(f"  note: {name} {method} {kind} {s} {shot}-shot has {len(v)} seeds")
        vals.append(st.fmean(v))
    return st.fmean(vals)


def main(out):
    plt.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman", "STIXGeneral"],
                         "mathtext.fontset": "stix", "font.size": 7, "pdf.fonttype": 42})
    data = {(n, m, sc): [point(n, m, sc, k) for k in SHOTS]
            for n in NAMES for m in ("PromptFL", "FedCLEAR") for sc in SCEN}
    shots = [k for k in SHOTS if any(v[SHOTS.index(k)] is not None for v in data.values())]
    xs = list(range(len(shots)))
    fig, axes = plt.subplots(1, len(NAMES), figsize=(7.0, 1.4))
    style = {"PromptFL": ("#2F5D8A", "o"), "FedCLEAR": ("#C0392B", "s")}
    for ax, n in zip(axes, NAMES):
        for m in ("PromptFL", "FedCLEAR"):
            col, mk = style[m]
            for sc, ls in (("Scenario 1", "-"), ("Scenario 2", (0, (3, 1.5)))):
                pts = [(x, data[n, m, sc][SHOTS.index(k)]) for x, k in zip(xs, shots)
                       if data[n, m, sc][SHOTS.index(k)] is not None]
                if pts:
                    ax.plot(*zip(*pts), color=col, ls=ls, marker=mk, ms=2.8, lw=1.0,
                            mfc=col if sc == "Scenario 1" else "white", mew=0.8)
                print(f"{n:10s} {m:8s} {sc}: " + "  ".join(
                    f"{k}:{'—' if v is None else f'{v:.1f}'}" for k, v in zip(SHOTS, data[n, m, sc])))
        ax.set_title(n, fontsize=7.5, pad=2)
        ax.set_xticks(xs)
        ax.set_xticklabels([str(k) for k in shots])
        ax.tick_params(labelsize=6.3, length=2, pad=1.5)
        ax.grid(color="0.9", lw=0.5)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
    axes[0].set_ylabel("Accuracy (%)", fontsize=7)
    fig.supxlabel("labelled images per class", fontsize=7, y=0.0)
    hs = [plt.Line2D([], [], color=style[m][0], marker=style[m][1], ms=3, lw=1.0, ls=ls,
                     mfc=style[m][0] if f == "S1" else "white")
          for m in ("PromptFL", "FedCLEAR") for f, ls in (("S1", "-"), ("S2", (0, (3, 1.5))))]
    labs = [f"{m}, {sc}" for m in ("PromptFL", "FedCLEAR") for sc in ("Scenario 1", "Scenario 2")]
    fig.legend(hs, labs, ncol=4, frameon=False, fontsize=6.5, loc="lower center",
               bbox_to_anchor=(0.5, 0.97), handlelength=2.2, columnspacing=1.2)
    fig.tight_layout(pad=0.3, w_pad=0.6)
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(out, f"ShotStudy.{ext}"), dpi=300, bbox_inches="tight", pad_inches=0.02)
    print("wrote", os.path.join(out, "ShotStudy.pdf"))


if __name__ == "__main__":
    os.makedirs(sys.argv[1], exist_ok=True)
    main(sys.argv[1])
