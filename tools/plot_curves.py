"""Training curves of CLEAR-FPL, DBR-FPL and NLPrompt (PromptFL as reference): test accuracy and
train loss per round, mean over 5 seeds, plus a convergence table.

Four settings per dataset: S_sym (3 clients at 40% symmetric), N_pair50, N_sym75 and N_pair75
(every client noisy).
The train loss is each method's loss on its own training data as it trains on it (CLEAR on repaired
labels, DBR without the dropped images, NLPrompt CE on its clean split + MAE on the rest), so its
level is not comparable across methods; only its shape is. Test loss is not logged.

Usage: python tools/plot_curves.py   (writes results/side-research/figures/)
"""
import os
import re
import statistics as st

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from analyze_baselines import SR, find_log

OUT = os.path.join(SR, "figures")
LINE = re.compile(r"round (\d+), (?:train loss: ([\d.]+)±[\d.]+%, )?.*?top1: ([\d.]+)%")
DATASETS = [("oxford_pets", "Pets"), ("dtd", "DTD"), ("caltech101", "Caltech101")]
SETTINGS = [("sym", "3 client nhiễu đều 40%"), ("pair50", "mọi client nhiễu cặp 50%"),
            ("sym75", "mọi client nhiễu đều 75%"), ("pair75", "mọi client nhiễu cặp 75%")]
# name -> (tag of the S_sym run, suffix of the N_<x> runs), colour, line style
METHODS = [
    ("CLEAR-FPL", ("S_sym_full", "clear"), "#2a78d6", "-"),
    ("DBR-FPL (cũ)", ("D_sym_dbr", "dbr"), "#eb6834", "-"),
    ("NLPrompt (gốc)", ("S_sym_nlp", "nlp"), "#1baf7a", "-"),
    ("NLPrompt (chỉnh)", ("S_sym_nlph", "nlph"), "#eda100", "-"),
    ("PromptFL", ("D_sym_none", "none"), "#8a8984", "--"),
]


def run_tag(ds, sc, tags):
    return f"{ds}_{tags[0]}" if sc == "sym" else f"{ds}_N_{sc}_{tags[1]}"


INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e6e5e0"


def curves(tag):
    """Per seed: arrays of test accuracy and train loss over rounds 0..50."""
    path = find_log(tag)
    if not path:
        return None
    seeds, cur = [], None
    for line in open(path, encoding="utf-8", errors="replace"):
        m = LINE.search(line)
        if not m:
            continue
        if int(m.group(1)) == 0:
            cur = {"acc": [], "loss": []}
            seeds.append(cur)
        if cur is not None:
            cur["acc"].append(float(m.group(3)))
            cur["loss"].append(float(m.group(2)) if m.group(2) else np.nan)
    seeds = [s for s in seeds if len(s["acc"]) == 51]
    if not seeds:
        return None
    return np.array([s["acc"] for s in seeds]), np.array([s["loss"] for s in seeds])


def converge_round(acc):
    """First round where the seed-mean accuracy reaches 95% of its last10 level."""
    mean = acc.mean(axis=0)
    target = 0.95 * mean[-10:].mean()
    hit = np.where(mean >= target)[0]
    return int(hit[0]) if len(hit) else None


def style(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(MUTED)
        ax.spines[s].set_linewidth(0.8)
    ax.tick_params(colors=MUTED, labelsize=8, length=3)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def figure(kind, data):
    fig, axes = plt.subplots(len(SETTINGS), 3, figsize=(12, 3.1 * len(SETTINGS) + 0.6), sharex=True)
    for j, (ds, dname) in enumerate(DATASETS):
        for i, (sc, sname) in enumerate(SETTINGS):
            ax = axes[i, j]
            style(ax)
            for name, tags, color, ls in METHODS:
                d = data.get((ds, sc, name))
                if d is None:
                    continue
                y = d[0] if kind == "acc" else d[1]
                mean, sd = np.nanmean(y, axis=0), np.nanstd(y, axis=0)
                x = np.arange(len(mean))
                ax.plot(x, mean, color=color, ls=ls, lw=2 if ls == "-" else 1.4, label=name)
                if ls == "-":
                    ax.fill_between(x, mean - sd, mean + sd, color=color, alpha=0.12, lw=0)
            ax.set_title(f"{dname} · {sname}", fontsize=9.5, color=INK, loc="left")
            if j == 0:
                ax.set_ylabel("độ chính xác test (%)" if kind == "acc" else "train loss", fontsize=9,
                              color=MUTED)
            if i == len(SETTINGS) - 1:
                ax.set_xlabel("vòng", fontsize=9, color=MUTED)
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=len(METHODS), frameon=False, fontsize=9.5,
               bbox_to_anchor=(0.5, 1.0))
    title = ("Độ chính xác test theo vòng" if kind == "acc" else
             "Train loss theo vòng (mức loss không so được giữa các phương pháp, chỉ xem hình dạng)")
    fig.suptitle(title + " — trung bình 5 seed, dải = ±1 độ lệch chuẩn", fontsize=10.5, color=INK,
                 y=0.965)
    fig.tight_layout(rect=(0, 0, 1, 0.955))
    out = os.path.join(OUT, f"curves_{kind}.png")
    fig.savefig(out, dpi=200, facecolor="white")
    plt.close(fig)
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    data = {}
    for ds, _ in DATASETS:
        for sc, _ in SETTINGS:
            for name, tags, _, _ in METHODS:
                c = curves(run_tag(ds, sc, tags))
                if c is not None:
                    data[(ds, sc, name)] = c
    print(figure("acc", data))
    print(figure("loss", data))
    md = ["# Tốc độ hội tụ", "",
          "Vòng đầu tiên mà độ chính xác trung bình 5 seed đạt 95% mức last10 của chính phương pháp đó; "
          "trong ngoặc là last10. Sinh bởi `tools/plot_curves.py`.", "",
          "| bộ dữ liệu | kịch bản | " + " | ".join(m[0] for m in METHODS) + " |",
          "|---|---|" + "---|" * len(METHODS)]
    for ds, dname in DATASETS:
        for sc, sname in SETTINGS:
            cells = []
            for name, *_ in METHODS:
                d = data.get((ds, sc, name))
                if d is None:
                    cells.append("—")
                    continue
                r = converge_round(d[0])
                cells.append(f"{r} ({d[0].mean(axis=0)[-10:].mean():.1f})")
            md.append(f"| {dname} | {sname} | " + " | ".join(cells) + " |")
    text = "\n".join(md) + "\n"
    open(os.path.join(OUT, "convergence.md"), "w", encoding="utf-8").write(text)
    print(text)


if __name__ == "__main__":
    main()
