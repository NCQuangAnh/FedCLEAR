"""Numbers and figures added to the paper for the supervisor's comments (2026-11-03).

  scores   Fig. score: distribution of the client score S_k for clean and noisy clients, per
           dataset, scenario 1 (CLEAR-FPL v1 runs, rounds 10-50, 5 seeds), with tau = 0.05
  early    share of correct labels that the repair changes (relabelled to a wrong class or set
           aside) on flagged clients, rounds 1-5 vs 41-50: decisions are revised as the prompt
           improves
  mix      the reference with and without zero-shot CLIP (global prompt only, arm noclip), scenario 1
  noise    Fig. 1: PromptFL (no noise handling) against the noise-handling methods (NLPrompt,
           FedCorr, FedRG) on Pets / Caltech101 under growing noise

Usage: python tools/paper_extras.py <out_dir>
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
from analyze_gatec import records

DS = [("oxford_pets", "Pets"), ("caltech101", "Caltech101"), ("dtd", "DTD"), ("mnist", "MNIST"),
      ("eurosat", "EuroSAT")]
S1 = ["sym", "pair", "inst", "het", "clean"]
TAU = 0.05
plt.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman", "STIXGeneral"],
                     "mathtext.fontset": "stix", "font.size": 8, "pdf.fonttype": 42})


def scores(out):
    clean, noisy = {}, {}
    for ds, name in DS:
        c, n = [], []
        for sc in S1:
            for rec in records(f"{ds}_S_{sc}_full"):
                for r in rec:
                    if r.get("round", 0) < 10:
                        continue
                    for x in r["clients"].values():
                        if x.get("score") is None:
                            continue
                        (n if x["noise"] > 0 else c).append(x["score"])
        clean[name], noisy[name] = np.array(c), np.array(n)
    fig, ax = plt.subplots(figsize=(4.8, 2.3))
    pos = np.arange(len(DS))
    for k, (data, col, off, lab) in enumerate([(clean, "#0072B2", -0.18, "clean clients"),
                                                (noisy, "#D55E00", 0.18, "noisy clients")]):
        vals = [np.clip(data[n], -1.5, 6) for _, n in DS]
        vp = ax.violinplot(vals, positions=pos + off, widths=0.32, showextrema=False)
        for b in vp["bodies"]:
            b.set_facecolor(col)
            b.set_alpha(0.55)
            b.set_edgecolor("none")
        ax.scatter(pos + off, [np.median(v) for v in vals], color=col, s=10, zorder=3,
                   edgecolor="black", linewidth=0.3)
        ax.plot([], [], color=col, lw=6, alpha=0.55, label=lab)
    ax.axhline(TAU, color="0.2", ls=(0, (4, 2)), lw=0.8, label=r"$\tau = 0.05$")
    ax.set_xticks(pos)
    ax.set_xticklabels([n for _, n in DS])
    ax.set_ylabel(r"client score $S_k$")
    ax.set_ylim(-1.5, 6)
    ax.grid(axis="y", color="0.9", lw=0.5)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.legend(frameon=False, fontsize=7, ncol=3, loc="upper right")
    fig.tight_layout()
    fig.savefig(os.path.join(out, "ScoreDistribution.pdf"), bbox_inches="tight", pad_inches=0.02)
    for _, n in DS:
        c, z = clean[n], noisy[n]
        print(f"score {n}: clean median {np.median(c):.2f} p95 {np.percentile(c, 95):.2f} flagged "
              f"{np.mean(c > TAU):.1%} | noisy median {np.median(z):.2f} flagged {np.mean(z > TAU):.1%}")


def early():
    for ds, name in DS[:3]:
        win = {"1-5": [0, 0], "41-50": [0, 0]}
        for sc in S1[:4]:
            for rec in records(f"{ds}_S_{sc}_full"):
                for r in rec:
                    rd = r.get("round", 0)
                    key = "1-5" if 1 <= rd <= 5 else "41-50" if rd >= 41 else None
                    if key is None:
                        continue
                    for x in r["clients"].values():
                        correct = x["n"] - round(x["noise"] * x["n"])
                        harmed = x.get("broken", 0) + (x.get("dropped", 0) - x.get("dropped_noisy", 0))
                        win[key][0] += harmed
                        win[key][1] += correct
        print(f"early {name}: correct labels changed, rounds 1-5 {win['1-5'][0] / win['1-5'][1]:.2%}, "
              f"rounds 41-50 {win['41-50'][0] / win['41-50'][1]:.2%}")


def mix():
    for ds, name in DS:
        row = []
        for sc in S1:
            a, b = ab.last10(f"{ds}_S_{sc}_noclip"), ab.last10(f"{ds}_S_{sc}_full")
            row.append("—" if not a else f"{st.fmean(a):.1f} / {st.fmean(b):.1f}")
        print(f"mix {name}: " + " | ".join(row))


def noise_fig(out):
    # Two groups (supervisor, 2026-11-16 regrouping): PromptFL, which has no noise handling, and the
    # three methods designed for noisy labels. A small gap separates the groups inside each setting.
    groups = [("No noise handling", [("PromptFL", "PromptFL", "#2F5D8A")]),
              ("Noise handling", [("NLPrompt", "NLPrompt", "#F6C99A"), ("FedCorr", "FedCorr", "#E08A4A"),
                                  ("FedRG", "FedRG", "#A8431A")])]
    settings = [("clean", ("S", "clean")), ("3 of 10 noisy\n(40% sym.)", ("S", "sym")),
                ("all noisy\n(50% sym.)", ("N", "sym50")), ("all noisy\n(75% sym.)", ("N", "sym75"))]
    zs = {"Pets": 85.69, "Caltech101": 85.76}
    w, gap = 0.18, 0.05
    offs = [-1.5 * w - gap * 3 / 4, -0.5 * w + gap / 4, 0.5 * w + gap / 4, 1.5 * w + gap / 4]
    fig, axes = plt.subplots(1, 2, figsize=(4.9, 1.8), sharey=True)
    handles = {}
    for ax, (ds, name) in zip(axes, [("oxford_pets", "Pets"), ("caltech101", "Caltech101")]):
        j = 0
        for g, members in groups:
            for lab, key, col in members:
                vals = [st.fmean(ab.last10(ab.tag(ds, key, k, s))) for _, (k, s) in settings]
                x = np.arange(len(settings)) + offs[j]
                handles[lab] = ax.bar(x, vals, w, color=col, zorder=2)
                print(f"fig1 {name} {lab}: " + " ".join(f"{v:.1f}" for v in vals))
                j += 1
        handles["Zero-shot CLIP"] = ax.axhline(zs[name], color="0.25", ls=(0, (4, 2)), lw=0.9, zorder=3)
        ax.set_xticks(range(len(settings)))
        ax.set_xticklabels([s for s, _ in settings], fontsize=6.3)
        ax.set_title(name, fontsize=8, pad=2)
        ax.set_ylim(30, 92)
        ax.grid(axis="y", color="0.9", lw=0.5, zorder=0)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
    axes[0].set_ylabel("Accuracy (%)")
    # one legend box per group, then zero-shot CLIP, side by side above the panels
    boxes = [(g, [m[0] for m in members]) for g, members in groups] + [("Reference", ["Zero-shot CLIP"])]
    for (title, labs), x0 in zip(boxes, (0.17, 0.53, 0.88)):
        leg = fig.legend([handles[l] for l in labs], labs, title=title, frameon=False, fontsize=6.8,
                         title_fontsize=6.8, ncol=len(labs), loc="lower center", bbox_to_anchor=(x0, 0.97),
                         handlelength=1.2, columnspacing=0.8)
        leg.get_title().set_fontweight("bold")
    fig.tight_layout()
    fig.savefig(os.path.join(out, "NoiseImpact.pdf"), bbox_inches="tight", pad_inches=0.02)
    fig.savefig(os.path.join(out, "NoiseImpact.png"), dpi=300, bbox_inches="tight", pad_inches=0.02)


if __name__ == "__main__":
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    scores(out)
    early()
    mix()
    noise_fig(out)
