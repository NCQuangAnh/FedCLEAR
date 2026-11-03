"""Offline checks for the reviewer-facing additions of the paper (2026-11-03). No training run.

Every number is replayed from logs that already exist:
  v1 records    the per-round client records of the basic-repair runs (CLEAR-FPL v1, tags S_<sc>_full
                and N_<x>_clear, 5 seeds): client score, flag, suspects, relabelled, true noise
  gatef records the same for the full method (eps, eps0, T)
  stage 0 logs  logged-only PromptFL runs with the full per-image probabilities (3 seeds), on which
                the basic repair can be replayed with other constants
  metrics       metrics_seed_<s>.json of the runs made with --log_metrics

Sections:
  tau     client flags of clean / noisy client-rounds for tau in a range (v1 records, scenario 1)
  gate    gate decisions for R_g in {3, 5, 10} and g in {0.06 ... 0.18} (v1 records, all settings)
  gamma   how often the 60% cap is reached on a flagged client (v1 records)
  delta   the basic suspect rule for delta in {0.05, 0.1, 0.2, 0.3} (stage 0 replay)
  clip    client flags with the -log clipped at 5 / 10 / 20 / not at all (stage 0 replay)
  merge   client flags with and without the look-alike merge (stage 0 replay)
  eps     the frozen noise estimate eps0 vs the round-50 estimate vs the true rate (gatef records)
  stats   per dataset and scenario: mean +- sd over seeds of the per-seed average, paired t-tests
  cost    wall time per round and peak GPU memory, FedCLEAR vs FedRG on the same notebooks

Usage: python tools/paper_sensitivity.py   (writes results/side-research/paper_sensitivity.md)
"""
import math
import os
import statistics as st
import sys

import numpy as np
from scipy import stats as sps

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "flip"))
import make_paper_tables as mpt
from analyze_baselines import SR
from analyze_gatec import records
from analyze_rg_metrics import metric_runs
from flcore.sure import gate_bound
from screen_stage0 import load_run

OUT = os.path.join(SR, "paper_sensitivity.md")
DS = [("oxford_pets", "Pets"), ("caltech101", "Caltech101"), ("dtd", "DTD"), ("mnist", "MNIST"),
      ("eurosat", "EuroSAT")]
S1 = ["sym", "pair", "inst", "het", "clean"]
S2 = [f"{t}{r}" for t in ("sym", "pair") for r in (25, 50, 75)]
TAU = 0.05
md = []


def v1(ds, kind, x):
    return records(f"{ds}_S_{x}_full" if kind == "S" else f"{ds}_N_{x}_clear")


def out(line=""):
    md.append(line)
    print(line)


def tau_section():
    taus = [0.0, 0.025, 0.05, 0.1, 0.2, 0.5]
    out("## tau: share of client-rounds flagged (scenario 1, basic repair, rounds 10-50)")
    out("")
    out("| dataset | clients | " + " | ".join(f"tau={t}" for t in taus) + " |")
    out("|---|---|" + "---|" * len(taus))
    for ds, name in DS:
        c, n = [], []
        for sc in S1:
            for rec in v1(ds, "S", sc):
                for r in rec:
                    if r.get("round", 0) < 10:
                        continue
                    for x in r["clients"].values():
                        if x.get("score") is not None:
                            (n if x["noise"] > 0 else c).append(x["score"])
        c, n = np.array(c), np.array(n)
        out(f"| {name} | clean | " + " | ".join(f"{np.mean(c > t):.1%}" for t in taus) + " |")
        out(f"| {name} | noisy | " + " | ".join(f"{np.mean(n > t):.1%}" for t in taus) + " |")
    out("")


def gate_counts(rec, R):
    rel = sus = 0
    for r in rec:
        if 1 <= r["round"] <= R:
            for x in r["clients"].values():
                rel += x.get("relabeled") or 0
                sus += x.get("suspects") or 0
    return gate_bound(rel, sus)


def gate_section():
    Rs, gs = [3, 5, 10], [0.06, 0.09, 0.12, 0.15, 0.18]
    out("## gate: decisions replayed on the basic-repair runs (11 settings x 5 seeds per dataset)")
    out("")
    out("| dataset | open, R_g=5, g=0.12 | open R_g=3 | open R_g=10 | same decision as R_g=5 (R_g=3 / 10) | "
        + " | ".join(f"open g={g}" for g in gs) + " |")
    out("|---|---|---|---|---|" + "---|" * len(gs))
    tot = {"same3": 0, "same10": 0, "n": 0}
    for ds, name in DS:
        b = {R: [] for R in Rs}
        for kind, xs in (("S", S1), ("N", S2)):
            for x in xs:
                for rec in v1(ds, kind, x):
                    for R in Rs:
                        b[R].append(gate_counts(rec, R))
        dec = {R: [v is not None and v >= 0.12 for v in b[R]] for R in Rs}
        same3 = sum(a == c for a, c in zip(dec[3], dec[5]))
        same10 = sum(a == c for a, c in zip(dec[10], dec[5]))
        n = len(dec[5])
        tot["same3"] += same3
        tot["same10"] += same10
        tot["n"] += n
        gcount = [sum(v is not None and v >= g for v in b[5]) for g in gs]
        out(f"| {name} | {sum(dec[5])}/{n} | {sum(dec[3])}/{n} | {sum(dec[10])}/{n} | {same3}/{n} / {same10}/{n} | "
            + " | ".join(f"{k}/{n}" for k in gcount) + " |")
    out(f"\nAll datasets: same decision with R_g=3 in {tot['same3']}/{tot['n']} runs, with R_g=10 in "
        f"{tot['same10']}/{tot['n']}.\n")


def gamma_section():
    out("## gamma: flagged client-rounds whose suspects reached the 60% cap (basic repair, rounds 1-50)")
    out("")
    out("| dataset | scenario 1 | scenario 2 |")
    out("|---|---|---|")
    for ds, name in DS:
        cells = []
        for kind, xs in (("S", S1), ("N", S2)):
            hit = flagged = 0
            for x in xs:
                for rec in v1(ds, kind, x):
                    for r in rec:
                        if r.get("round", 0) < 1:
                            continue
                        for c in r["clients"].values():
                            if not c.get("flag"):
                                continue
                            flagged += 1
                            cap = int(0.6 * c["n"])
                            hit += cap > 0 and c.get("suspects", 0) >= cap
            cells.append(f"{hit / flagged:.1%} of {flagged}" if flagged else "—")
        out(f"| {name} | {cells[0]} | {cells[1]} |")
    out("")


def xs_score(lp, y, nn, clip=10.0, merge=True):
    P = np.exp(lp)
    M = P + P[:, nn] if merge else P
    nl = -np.log(np.maximum(M, 1e-300))
    if clip is not None:
        nl = np.minimum(nl, clip)
    return float((nl[np.arange(len(y)), y] - (P * nl).sum(axis=1)).mean())


def stage0_sets(ds):
    tags = [f"D_{sc}_fp" for sc in ("sym", "pair", "het", "clean")]
    if ds in ("mnist", "eurosat"):
        tags += ["N_sym50_fp", "N_pair50_fp"]
    return tags


def auroc(pos, neg):
    if not pos or not neg:
        return float("nan")
    a = np.array(pos)[:, None]
    b = np.array(neg)[None, :]
    return float(((a > b).sum() + 0.5 * (a == b).sum()) / (a.size * b.size))


def stage0_sections():
    deltas = [0.05, 0.1, 0.2, 0.3]
    rows_d, rows_c, rows_m = [], [], []
    for ds, name in DS:
        acc = {d: np.zeros(6) for d in deltas}   # wrong caught, wrong, sus, sus wrong, relab, relab right
        correct_marked = {d: [0, 0] for d in deltas}
        flags = {k: [] for k in ("c10", "c5", "c20", "cinf", "nomerge")}
        noisy_c = []
        sc_m, sc_nm = {"clean": [], "noisy": []}, {"clean": [], "noisy": []}
        for tag in stage0_sets(ds):
            data, nn = load_run(ds, tag)
            for _, clients in data.items():
                for _, lp, y, t in clients:
                    wrong = y != t
                    s10 = xs_score(lp, y, nn)
                    flags["c10"].append(s10 > TAU)
                    flags["c5"].append(xs_score(lp, y, nn, clip=5.0) > TAU)
                    flags["c20"].append(xs_score(lp, y, nn, clip=20.0) > TAU)
                    flags["cinf"].append(xs_score(lp, y, nn, clip=None) > TAU)
                    snm = xs_score(lp, y, nn, merge=False)
                    flags["nomerge"].append(snm > TAU)
                    noisy_c.append(bool(wrong.any()))
                    (sc_m["noisy"] if wrong.any() else sc_m["clean"]).append(s10)
                    (sc_nm["noisy"] if wrong.any() else sc_nm["clean"]).append(snm)
                    P = np.exp(lp)
                    py = P[np.arange(len(y)), y]
                    top, conf = P.argmax(axis=1), P.max(axis=1)
                    for d in deltas:
                        acc[d][1] += wrong.sum()
                        correct_marked[d][1] += (~wrong).sum()
                        if s10 <= TAU:
                            continue
                        idx = sorted(np.where(py < d)[0].tolist(), key=lambda i: py[i])[:int(0.6 * len(y))]
                        for i in idx:
                            acc[d][2] += 1
                            acc[d][3] += wrong[i]
                            acc[d][0] += wrong[i]
                            correct_marked[d][0] += not wrong[i]
                            if top[i] != y[i] and conf[i] >= 0.5:
                                acc[d][4] += 1
                                acc[d][5] += top[i] == t[i]
        rows_d.append((name, {d: (acc[d][0] / acc[d][1], acc[d][3] / max(acc[d][2], 1),
                                  correct_marked[d][0] / correct_marked[d][1], acc[d][5] / max(acc[d][4], 1))
                              for d in deltas}))
        f10 = np.array(flags["c10"])
        nc = np.array(noisy_c)
        rows_c.append((name, {k: float(np.mean(np.array(flags[k]) == f10)) for k in ("c5", "c20", "cinf")}))
        fn = np.array(flags["nomerge"])
        rows_m.append((name, (np.mean(f10[~nc]), np.mean(f10[nc]), auroc(sc_m["noisy"], sc_m["clean"]),
                              np.mean(fn[~nc]), np.mean(fn[nc]), auroc(sc_nm["noisy"], sc_nm["clean"]))))
    out("## delta: basic suspect rule replayed on stage 0 (PromptFL reference, rounds 10-50, 3 seeds)")
    out("")
    out("| dataset | " + " | ".join(f"delta={d}: recall / suspect precision / correct marked / relabel precision"
                                    for d in deltas) + " |")
    out("|---|" + "---|" * len(deltas))
    for name, r in rows_d:
        out(f"| {name} | " + " | ".join(f"{a:.0%} / {b:.0%} / {c:.1%} / {e:.0%}" for a, b, c, e in
                                        (r[d] for d in deltas)) + " |")
    out("")
    out("## clip: client flags identical to clip=10 (stage 0)")
    out("")
    out("| dataset | clip 5 | clip 20 | no clip |")
    out("|---|---|---|---|")
    for name, r in rows_c:
        out(f"| {name} | {r['c5']:.1%} | {r['c20']:.1%} | {r['cinf']:.1%} |")
    out("")
    out("## merge: client flags at tau=0.05 and AUROC, with and without the look-alike merge (stage 0)")
    out("")
    out("| dataset | merge: clean flagged / noisy flagged / AUROC | no merge: clean flagged / noisy flagged / AUROC |")
    out("|---|---|---|")
    for name, (a, b, c, d, e, f) in rows_m:
        out(f"| {name} | {a:.1%} / {b:.1%} / {c:.3f} | {d:.1%} / {e:.1%} / {f:.3f} |")
    out("")


def eps_section():
    out("## eps: the frozen estimate eps0 vs the estimate at round 50 vs the true rate (gatef, scenario 2, gate open)")
    out("")
    out("| dataset | setting | true noise | eps0 (first calibrated round) | eps at round 50 |")
    out("|---|---|---|---|---|")
    for ds, name in DS[:3]:
        for x in S2:
            tru, e0, e50 = [], [], []
            for rec in records(f"{ds}_N_{x}_gatef"):
                last = [r for r in rec if r.get("round") == 50]
                if not last:
                    continue
                for c in last[0]["clients"].values():
                    if c.get("eps0") is None:
                        continue
                    tru.append(c["noise"])
                    e0.append(c["eps0"])
                    e50.append(c["eps"])
            if tru:
                out(f"| {name} | N {x} | {st.fmean(tru):.2f} | {st.fmean(e0):.2f} | {st.fmean(e50):.2f} |")
    out("")


def stats_section():
    names = [m[0] for m in mpt.METHODS]
    out("## stats: per-seed average over the settings, mean +- sd over 5 seeds; FedCLEAR vs each baseline,"
        " paired t-test over seeds (difference, p, seeds won)")
    out("")
    out("| dataset | scenario | " + " | ".join(names) + " |")
    out("|---|---|" + "---|" * len(names))
    for sc in (1, 2):
        rows = mpt.S1 if sc == 1 else mpt.S2
        for name in ["Pets", "Caltech101", "MNIST", "DTD", "EuroSAT"]:
            per = {}
            for lab, key, _ in mpt.METHODS:
                v = [mpt.seeds(name, key, k, s, "gatef") for k, s in rows]
                per[lab] = [st.fmean(x[i] for x in v) for i in range(5)]
            ours = per["FedCLEAR"]
            cells = []
            for lab in names:
                a = per[lab]
                cell = f"{st.fmean(a):.1f}$\\pm${st.stdev(a):.1f}"
                if lab != "FedCLEAR":
                    d = [o - b for o, b in zip(ours, a)]
                    p = sps.ttest_rel(ours, a).pvalue
                    cell += f" ({st.fmean(d):+.1f}, p={p:.3f}, {sum(x > 0 for x in d)}/5)"
                cells.append(cell)
            out(f"| {name} | {sc} | " + " | ".join(cells) + " |")
    out("")


def cost_section():
    out("## cost: per run, FedCLEAR (gatef) vs FedRG on the same Kaggle notebooks (MNIST, EuroSAT)")
    out("")
    out("| dataset | method | runs | wall s / round | slowest client s / round | peak GPU MB |")
    out("|---|---|---|---|---|---|")
    for ds, name in (("mnist", "MNIST"), ("eurosat", "EuroSAT")):
        for arm, lab in (("rg", "FedRG"), ("gatef", "FedCLEAR")):
            w, cm, mem, n = [], [], [], 0
            for kind, xs in (("S", S1), ("N", S2)):
                for x in xs:
                    runs = metric_runs(f"{ds}_{kind}_{x}_{arm}")
                    for r in runs or []:
                        n += 1
                        w.append(st.fmean(q["wall_s"] for q in r))
                        cm.append(st.fmean(q["client_s_max"] for q in r))
                        mem.append(max(q["peak_mem_mb"] for q in r))
            if n:
                out(f"| {name} | {lab} | {n} | {st.fmean(w):.2f} | {st.fmean(cm):.2f} | {max(mem):.0f} |")
    out("")


def main():
    out("# Offline checks for the paper (tools/paper_sensitivity.py)")
    out("")
    tau_section()
    gate_section()
    gamma_section()
    eps_section()
    stats_section()
    cost_section()
    stage0_sections()
    open(OUT, "w", encoding="utf-8").write("\n".join(md))


if __name__ == "__main__":
    main()
