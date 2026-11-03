"""FedRG next to CLEAR-FPL (v1) and the improved FedCLEAR (gatef), on accuracy and on the metrics
logged with --log_metrics (macro precision / recall / F1, time, GPU memory, bytes).

Accuracy: last10, 5 seeds, paired over seeds, every dataset. gatef equals CLEAR-FPL where the gate
stays off, so a setting without a gatef run takes the CLEAR-FPL value (marked *).
Metrics: only runs made with --log_metrics carry metrics_seed_<s>.json, i.e. the FedRG runs of DTD,
Caltech101 (notebooks 3-4), MNIST and EuroSAT, and the gatef runs of the rg_me notebooks. Precision,
recall and F1 are the mean of the last 10 rounds, like last10 accuracy.

Usage: python tools/analyze_rg_metrics.py   (writes results/side-research/fedrg/rg_metrics_results.md)
"""
import glob
import json
import os
import statistics as st

from analyze_baselines import DATASETS, SETTINGS, SR, find_log, last10, paired

OUT = os.path.join(SR, "fedrg", "rg_metrics_results.md")
NAME = dict(DATASETS)


def tags(ds, kind, x):
    clear = f"{ds}_{'S_' + x + '_full' if kind == 'S' else 'N_' + x + '_clear'}"
    return {"rg": f"{ds}_{kind}_{x}_rg", "clear": clear, "gatef": f"{ds}_{kind}_{x}_gatef"}


_METRICS = None


def metric_runs(tag):
    """Every metrics_seed_<s>.json of a tag, in seed order. The same tag can sit in several
    notebooks (gatef in calrepair and fedrg), so the index keeps the folder that has metrics."""
    global _METRICS
    if _METRICS is None:
        _METRICS = {}
        for d in glob.glob(os.path.join(SR, "**", "runs", "*"), recursive=True):
            fs = glob.glob(os.path.join(d, "results", "*", "*", "*", "*", "*", "metrics_seed_*.json"))
            if fs:
                _METRICS.setdefault(os.path.basename(d), sorted(fs, key=lambda f: int(f.rsplit("_", 1)[1][:-5])))
    fs = _METRICS.get(tag)
    return [json.load(open(f, encoding="utf-8")) for f in fs] if fs else None


def summarize(recs):
    """Per seed: last-10-round mean of precision / recall / F1 / acc (in %), and the run's cost."""
    rows = []
    for r in recs:
        last = r[-10:]
        rows.append({
            "acc": 100 * st.fmean(x["acc"] for x in last),
            "precision": 100 * st.fmean(x["precision"] for x in last),
            "recall": 100 * st.fmean(x["recall"] for x in last),
            "f1": 100 * st.fmean(x["f1"] for x in last),
            "wall_min": sum(x["wall_s"] for x in r) / 60,
            "client_s": st.fmean(x["client_s_sum"] for x in r),
            "client_max": st.fmean(x["client_s_max"] for x in r),
            "mem": max(x["peak_mem_mb"] for x in r),
            "kb_round": st.fmean((x["up_bytes"] + x["down_bytes"]) for x in r) / 1024,
        })
    return rows


def ms(v, d=2):
    return "—" if not v else f"{st.fmean(v):.{d}f} ± {st.stdev(v):.{d}f}" if len(v) > 1 else f"{v[0]:.{d}f}"


def dcell(a, b):
    p = paired(a, b)
    return "—" if p is None else f"{p[0]:+.2f} (p={p[1]:.3f}, {p[2]}/{p[3]})"


def acc_section(md):
    md += ["## 1. Accuracy (last10)", "",
           "CLEAR-v2 = gatef; * = gate off in this setting, value is CLEAR-FPL. "
           "Differences: mean (paired t-test p, seeds won / 5).", ""]
    means = {}
    for ds, nm in DATASETS:
        md += [f"### {nm}", "",
               "| setting | FedRG | CLEAR-FPL | CLEAR-v2 | CLEAR-FPL − FedRG | CLEAR-v2 − FedRG |",
               "|---|---|---|---|---|---|"]
        cols = {"rg": [], "clear": [], "gatef": []}
        for kind, x in SETTINGS:
            t = tags(ds, kind, x)
            rg, cl, gf = last10(t["rg"]), last10(t["clear"]), last10(t["gatef"])
            star = "" if gf else "*"
            gf = gf or cl
            for k, v in (("rg", rg), ("clear", cl), ("gatef", gf)):
                if v:
                    cols[k].append(st.fmean(v))
            md.append(f"| {kind} {x} | {ms(rg)} | {ms(cl)} | {ms(gf)}{star} | {dcell(cl, rg)} | {dcell(gf, rg)} |")
        m = {k: (st.fmean(v) if len(v) == len(SETTINGS) else None) for k, v in cols.items()}
        means[nm] = m
        f = lambda v: "—" if v is None else f"{v:.2f}"
        g = lambda k: "—" if None in (m["rg"], m[k]) else f"{m[k] - m['rg']:+.2f}"
        md += [f"| mean of 11 | {f(m['rg'])} | {f(m['clear'])} | {f(m['gatef'])} | {g('clear')} | {g('gatef')} |", ""]
    md += ["### Mean of 11 settings", "", "| dataset | FedRG | CLEAR-FPL | CLEAR-v2 |", "|---|---|---|---|"]
    for nm, m in means.items():
        md.append(f"| {nm} | " + " | ".join("—" if m[k] is None else f"{m[k]:.2f}" for k in ("rg", "clear", "gatef")) + " |")
    md.append("")


def metric_section(md):
    md += ["## 2. Macro precision / recall / F1 (last 10 rounds, %)", "",
           "Only where both sides were logged with --log_metrics. Macro = averaged over the classes of "
           "the test set; a class the model never predicts counts precision 0. acc − F1 large means the "
           "model leans on a few classes.", ""]
    pooled = {}
    for ds, nm in DATASETS:
        rows = []
        for kind, x in SETTINGS:
            t = tags(ds, kind, x)
            a, b = metric_runs(t["rg"]), metric_runs(t["gatef"])
            if not a:
                continue
            sa = summarize(a)
            sb = summarize(b) if b and len(b) == len(a) else None
            line = f"| {kind} {x} |"
            for k in ("acc", "precision", "recall", "f1"):
                va = [r[k] for r in sa]
                vb = None if sb is None else [r[k] for r in sb]
                line += f" {ms(va, 1)} | {'—' if vb is None else ms(vb, 1)} |"
                if vb:
                    pooled.setdefault((nm, k), ([], []))
                    pooled[(nm, k)][0].extend(va)
                    pooled[(nm, k)][1].extend(vb)
            line += f" {'—' if sb is None else dcell([r['f1'] for r in sb], [r['f1'] for r in sa])} |"
            rows.append(line)
        if not rows:
            continue
        md += [f"### {nm}", "",
               "| setting | acc RG | acc v2 | prec RG | prec v2 | rec RG | rec v2 | F1 RG | F1 v2 | F1 v2 − RG |",
               "|---|---|---|---|---|---|---|---|---|---|"] + rows + [""]
    if pooled:
        md += ["### Pooled over the settings with both sides (seed pairs)", "",
               "| dataset | metric | FedRG | CLEAR-v2 | v2 − RG |", "|---|---|---|---|---|"]
        for (nm, k), (va, vb) in pooled.items():
            md.append(f"| {nm} | {k} | {st.fmean(va):.2f} | {st.fmean(vb):.2f} | {dcell(vb, va)} |")
        md.append("")


def cost_section(md):
    md += ["## 3. Cost per run (50 rounds + round 0)", "",
           "wall = server time of all rounds (train + aggregate + eval); client = summed local training "
           "time of the selected clients per round; peak GPU memory of the run; bytes sent + received per "
           "round. Same Kaggle GPU type is not guaranteed between notebooks, so time compares best "
           "inside one notebook.", "",
           "| dataset | method | runs | wall min/run | client s/round | slowest client s/round | peak GPU MB | KB/round |",
           "|---|---|---|---|---|---|---|---|"]
    for ds, nm in DATASETS:
        for arm, label in (("rg", "FedRG"), ("gatef", "CLEAR-v2")):
            allr = []
            for kind, x in SETTINGS:
                r = metric_runs(tags(ds, kind, x)[arm])
                if r:
                    allr += summarize(r)
            if not allr:
                continue
            f = lambda k, d=1: f"{st.fmean(r[k] for r in allr):.{d}f}"
            md.append(f"| {nm} | {label} | {len(allr)} | {f('wall_min')} | {f('client_s', 2)} | "
                      f"{f('client_max', 2)} | {max(r['mem'] for r in allr):.0f} | {f('kb_round', 0)} |")
    md.append("")


def main():
    md = ["# FedRG vs CLEAR-FPL / CLEAR-v2: accuracy, macro metrics, cost", "",
          "Generated by `tools/analyze_rg_metrics.py`.", ""]
    acc_section(md)
    metric_section(md)
    cost_section(md)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(md))
    print(OUT)


if __name__ == "__main__":
    main()
