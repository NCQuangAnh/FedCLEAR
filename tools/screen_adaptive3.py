"""Offline screen 3 of the adaptive-threshold study (results/side-research/adaptive_thr/screen3_plan.md).

T1 leave-one-out predictive skill (zero-shot), T2 label-permutation skill (raw zero-shot), T3 relabel by
the posterior under the uniform noise model, T4 soft targets on suspects (reported), T5 late memorisation
of wrong labels. Stage 0 PromptFL logs, seeds 0-2. The oracle labels are used only to score.

Usage: python tools/screen_adaptive3.py   (writes results/side-research/adaptive_thr/screen3.md)
"""
import math
import os
from collections import defaultdict

import numpy as np
from sklearn.metrics import roc_auc_score

from analyze_baselines import SR
from screen_adaptive import CAL_EPS, CAL_T, DATASETS, NTAGS, OLD, TAGS, cal_ll, fit_T_eps, temper
import glob
import json

OUT = os.path.join(SR, "adaptive_thr", "screen3.md")
EARLY, MID, LATE = (5, 10, 15), (20, 25, 30), (40, 45, 50)


def load_all(ds, tag):
    """{(seed, round): [(client, lg, lz, y, t)]}, every logged round"""
    out = defaultdict(list)
    for f in sorted(glob.glob(os.path.join(SR, "**", "runs", f"{ds}_{tag}", "**", "diag_samples_seed_*.json"),
                              recursive=True)):
        seed = int(f.rsplit("_", 1)[1].split(".")[0])
        for rec in json.load(open(f, encoding="utf-8")):
            rows = rec["rows"]
            if not rows:
                continue
            out[(seed, rec["round"])].append((rec["client"], np.array([r[20] for r in rows], dtype=np.float64),
                                              np.array([r[21] for r in rows], dtype=np.float64),
                                              np.array([r[0] for r in rows]), np.array([r[1] for r in rows])))
    return out


def profile(lp, y):
    return np.array([cal_ll(lp, y, T).max() for T in CAL_T])


def delta_loo(lz, y, T):
    n, K = lz.shape
    zy = np.exp(temper(lz, T))[np.arange(n), y]
    L = np.log((1 - CAL_EPS)[None] * zy[:, None] + CAL_EPS[None] / K)          # n x E
    lw = L.sum(axis=0)[None] - L
    w = np.exp(lw - lw.max(axis=1, keepdims=True))
    eb = (w * CAL_EPS[None]).sum(axis=1) / w.sum(axis=1)
    Q = (1 - eb) * zy + eb / K
    cnt = np.bincount(y, minlength=K)
    pi = (cnt[y] - 1 + 0.5) / (n - 1 + K / 2)
    return float(np.log(Q / pi).sum())


def perm_z(lz, y):
    n = len(y)
    if n < 2:
        return None
    A = lz[:, y]                                         # a(i, j) = log z_i(y_j)
    d = A - A.mean(axis=1, keepdims=True) - A.mean(axis=0, keepdims=True) + A.mean()
    var = (d ** 2).sum() / (n - 1)
    if var <= 1e-12:
        return None
    return float((np.trace(A) - A.sum() / n) / math.sqrt(var))


def posterior_relabel(PT_i, y, e, kind):
    K = len(PT_i)
    if kind == "uniform":
        tr = np.full(K, e / K)
        tr[y] = 1 - e + e / K
    elif kind == "sym":
        tr = np.full(K, e / (K - 1))
        tr[y] = 1 - e
    else:                                                # pair: y came from y - 1 with prob e
        tr = np.zeros(K)
        tr[y] = 1 - e
        tr[(y - 1) % K] += e
    r = PT_i * tr
    s = r.sum()
    if s <= 0:
        return None, 0.0
    r = r / s
    k = int(r.argmax())
    return (k, float(r[k])) if (k != y and r[k] > 0.5) else (None, float(r[k]))


def auroc(labels, scores):
    labels = np.asarray(labels)
    return float(roc_auc_score(labels, scores)) if 0 < labels.sum() < len(labels) else float("nan")


def main():
    S = defaultdict(lambda: defaultdict(list))
    R = defaultdict(lambda: np.zeros(4))      # (ds, set, rule) -> relabels, correct, suspects, sum r of relabels
    W = defaultdict(lambda: defaultdict(list))
    D = defaultdict(lambda: defaultdict(list))
    skipped = 0
    for ds, _ in DATASETS:
        for tag in TAGS + (NTAGS if ds in ("mnist", "eurosat") else []):
            kind = "pair" if "pair" in tag else "sym"
            data = load_all(ds, tag)
            traj = defaultdict(dict)
            for (seed, rd), clients in sorted(data.items()):
                for c, lg, lz, y, t in clients:
                    traj[(seed, c)][rd] = (lg, lz, y, t)
                if rd < 10:
                    continue
                lps = [np.logaddexp(lg, lz) - math.log(2.0) for _, lg, lz, _, _ in clients]
                ys = [y for _, _, _, y, _ in clients]
                T, eps = fit_T_eps(list(zip(lps, ys)))
                profs = [profile(lz, y) for _, _, lz, y, _ in clients]
                tot = np.sum(profs, axis=0)
                for ci, ((c, lg, lz, y, t), lp, e) in enumerate(zip(clients, lps, eps)):
                    n, K = lp.shape
                    idx = np.arange(n)
                    true = float((y != t).mean())
                    honest = true == 0
                    Tz = min(CAL_T[int((tot - profs[ci]).argmax())], 1.0) if len(clients) > 1 else 1.0
                    dl = delta_loo(lz, y, Tz)
                    z = perm_z(lz, y)
                    s = S[ds]
                    for name, ok in (("t1", dl > 0), ("t2", z is not None and z > 0)):
                        s[f"{name}_pos"].append(ok)
                        s[f"{name}_err_{'pos' if ok else 'neg'}"].append(abs(e - true))
                        if honest:
                            s[f"{name}_heps_{'pos' if ok else 'neg'}"].append(e)
                        if not honest:
                            s[f"{name}_noisy_pos"].append(ok)

                    P = np.exp(lp)
                    PT = np.exp(temper(lp, T))
                    py = P[idx, y]
                    top, conf = P.argmax(1), P.max(1)
                    ag = lg.argmax(1) == lz.argmax(1)
                    U = 1 - (-(P * lp).sum(1)) / math.log(K)
                    w = np.where(ag, 1.0, 0.5) * U
                    sus_i = sorted((i for i in range(n) if py[i] < 0.1), key=lambda i: py[i])[:int(0.6 * n)]
                    sus_ii = list(np.argsort(PT[idx, y], kind="stable")[:int(round(e * n))])
                    for sname, sus in (("i", sus_i), ("ii", sus_ii)):
                        for i in sus:
                            # K: current rule
                            acc = R[(ds, sname, "K")]
                            if top[i] != y[i] and conf[i] >= 0.5:
                                acc[0] += 1
                                acc[1] += top[i] == t[i]
                            for rule, kd in (("T3", "uniform"), ("oracle", kind)):
                                k, rk = posterior_relabel(PT[i], int(y[i]), e, kd)
                                acc = R[(ds, sname, rule)]
                                if k is not None:
                                    acc[0] += 1
                                    acc[1] += k == t[i]
                                    acc[3] += rk
                            ww = W[(ds, sname)]
                            ww["mass_true"].append(P[i, t[i]])
                            ww["mass_given"].append(P[i, y[i]])
                            ww["w"].append(w[i])
                            ww["top_true"].append(top[i] == t[i])
                        for rule in ("K", "T3", "oracle"):
                            R[(ds, sname, rule)][2] += len(sus)

            # T5: per-image trajectories
            for (seed, c), byr in traj.items():
                need = set(EARLY + MID + LATE)
                if not need <= set(byr):
                    skipped += 1
                    continue
                y0, t0 = byr[EARLY[0]][2], byr[EARLY[0]][3]
                if any(not (np.array_equal(byr[r][2], y0) and np.array_equal(byr[r][3], t0)) for r in need):
                    skipped += 1
                    continue
                idx = np.arange(len(y0))
                Lg = {r: -byr[r][0][idx, y0] for r in need}
                early = np.mean([Lg[r] for r in EARLY], axis=0)
                mid = np.mean([Lg[r] for r in MID], axis=0)
                late = np.mean([Lg[r] for r in LATE], axis=0)
                sP = lambda r: -(np.logaddexp(byr[r][0], byr[r][1]) - math.log(2.0))[idx, y0]
                d = D[ds]
                d["wrong"] += list(y0 != t0)
                d["M"] += list(early - late)
                d["M_early"] += list(early - mid)
                d["s10"] += list(sP(10))
                d["s50"] += list(sP(50))

    m = lambda v: float(np.mean(v)) if len(v) else float("nan")
    L = ["# Offline screen 3: results (2026-11-05)", "",
         "Plan and pass rules: `screen3_plan.md` (written before these numbers). Script: "
         "`tools/screen_adaptive3.py`. Stage 0 PromptFL logs, seeds 0-2.", ""]

    verdict = {}
    for name, title in (("t1", "T1: leave-one-out predictive skill (zero-shot)"),
                        ("t2", "T2: label-permutation skill (raw zero-shot)")):
        L += [f"## {title}", "",
              "| Dataset | trusted | noisy clients trusted | |eps - true|, trusted | |eps - true|, not trusted | "
              "honest eps, trusted | honest eps, not trusted |", "|---|---|---|---|---|---|---|"]
        pe, ph = [], []
        for ds, dn in DATASETS:
            s = S[ds]
            pe += s[f"{name}_err_pos"]
            ph += s[f"{name}_heps_pos"]
            L.append(f"| {dn} | {100 * m(s[f'{name}_pos']):.0f}% | {100 * m(s[f'{name}_noisy_pos']):.0f}% | "
                     f"{m(s[f'{name}_err_pos']):.3f} | {m(s[f'{name}_err_neg']):.3f} | "
                     f"{m(s[f'{name}_heps_pos']):.3f} | {m(s[f'{name}_heps_neg']):.3f} |")
        a = m(pe) <= 0.08 and m(ph) <= 0.05
        cov = {ds: 100 * m(S[ds][f"{name}_pos"]) for ds in OLD}
        b = all(v >= 90 for v in cov.values())
        verdict[name] = a and b
        L += ["", f"- A (trust): pooled error {m(pe):.3f} (<= 0.08), honest eps {m(ph):.3f} (<= 0.05): "
              f"**{'PASS' if a else 'FAIL'}**",
              "- B (coverage >= 90%): " + ", ".join(f"{dict(DATASETS)[d]} {v:.0f}%" for d, v in cov.items())
              + f": **{'PASS' if b else 'FAIL'}**", f"- **{name.upper()}: {'GO' if a and b else 'NO GO'}**", ""]

    L += ["## T3: relabel by the posterior under the uniform noise model (per 100 suspects)", ""]
    t3 = True
    for sname, title in (("i", "suspect set (i): P(y) < 0.1, 60% cap"),
                         ("ii", "suspect set (ii): round(eps * n) lowest P_T(y)")):
        L += [f"### {title}", "",
              "| Dataset | rule | relabels | precision | mean r of relabels | net (correct - wrong) |",
              "|---|---|---|---|---|---|"]
        for ds, dn in DATASETS:
            nets = {}
            for rule in ("K", "T3", "oracle"):
                rel, cor, sus, sr = R[(ds, sname, rule)]
                f = 100 / sus if sus else float("nan")
                nets[rule] = (2 * cor - rel) * f
                mr = f"{sr / rel:.2f}" if rule != "K" and rel else "—"
                L.append(f"| {dn} | {rule} | {rel * f:.1f} | {100 * cor / rel if rel else float('nan'):.0f}% | "
                         f"{mr} | {nets[rule]:+.1f} |")
            if not nets["T3"] >= nets["K"] - 2:
                t3 = False
        L.append("")
    verdict["t3"] = t3
    L += ["`oracle` uses the run's true noise mechanism and is reported only.", "",
          f"- **T3 (net >= K - 2 on both sets and every dataset): {'GO' if t3 else 'NO GO'}**", ""]

    L += ["## T4: soft targets on suspects (reported only)", "",
          "| Dataset | set | P on true class | P on given label | K relabels correctly | AUROC of w for top = true |",
          "|---|---|---|---|---|---|"]
    for ds, dn in DATASETS:
        for sname in ("i", "ii"):
            ww = W[(ds, sname)]
            rel, cor, sus, _ = R[(ds, sname, "K")]
            L.append(f"| {dn} | {sname} | {m(ww['mass_true']):.3f} | {m(ww['mass_given']):.3f} | "
                     f"{100 * cor / sus if sus else float('nan'):.0f}% | {auroc(ww['top_true'], ww['w']):.2f} |")
    L.append("")

    L += ["## T5: late memorisation of wrong labels (AUROC for wrong labels)", "",
          "| Dataset | images | wrong | M (5-15 minus 40-50) | M early (5-15 minus 20-30) | s_10 | s_50 |",
          "|---|---|---|---|---|---|---|"]
    t5 = True
    for ds, dn in DATASETS:
        d = D[ds]
        aM, aE, a10, a50 = (auroc(d["wrong"], d[k]) for k in ("M", "M_early", "s10", "s50"))
        L.append(f"| {dn} | {len(d['wrong'])} | {sum(d['wrong'])} | {aM:.3f} | {aE:.3f} | {a10:.3f} | {a50:.3f} |")
        if ds in ("mnist", "eurosat"):
            t5 &= aM >= max(a10, a50) + 0.05
    verdict["t5"] = t5
    L += ["", f"Trajectories skipped (missing rounds or labels changing order): {skipped}", "",
          f"- **T5 (AUROC(M) >= best one-round + 0.05 on MNIST and EuroSAT): {'GO' if t5 else 'NO GO'}**", ""]
    open(OUT, "w", encoding="utf-8").write("\n".join(L))
    print("\n".join(L))


if __name__ == "__main__":
    main()
