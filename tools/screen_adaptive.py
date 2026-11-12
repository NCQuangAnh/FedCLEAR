"""Offline screen 2 of the adaptive-threshold study (results/side-research/adaptive_thr/screen2_plan.md).

Reads the stage 0 PromptFL logs with full per-image log-probabilities (D_<sc>_fp, N_<x>_fp) and checks:
  S1  a per-client predictive-skill score Delta_c (zero-shot CLIP vs the client's label frequencies):
      when Delta_c > 0, is the client's calibrated noise estimate eps_c trustworthy?
  S2  relabel rules on suspects: K (P_top >= 0.5, current), KT (same on P_T), AG (g and z agree)
  S3  a BIC-selected 1-vs-2 Gaussian mixture on class-normalised surprise, against CLEAR's current rule
The oracle labels are used only to score. Rounds 10-50, seeds 0-2.

Usage: python tools/screen_adaptive.py   (writes results/side-research/adaptive_thr/screen2.md)
"""
import glob
import json
import math
import os
import warnings
from collections import defaultdict

import numpy as np
from sklearn.mixture import GaussianMixture

from analyze_baselines import SR

OUT = os.path.join(SR, "adaptive_thr", "screen2.md")
DATASETS = [("mnist", "MNIST"), ("eurosat", "EuroSAT"), ("oxford_pets", "Pets"), ("dtd", "DTD"),
            ("caltech101", "Caltech101")]
OLD = ["oxford_pets", "dtd", "caltech101"]
TAGS = ["D_sym_fp", "D_pair_fp", "D_het_fp", "D_clean_fp"]
NTAGS = ["N_sym50_fp", "N_pair50_fp"]
CAL_T = [round(math.exp(math.log(0.1) + i * (math.log(2.0) - math.log(0.1)) / 24), 3) for i in range(25)]
CAL_EPS = np.linspace(0, 0.95, 96)
NLL_CLIP = 10.0


def temper(logp, T):
    z = logp / T
    return z - np.logaddexp.reduce(z, axis=1, keepdims=True)


def cal_ll(logp, y, T):
    """log-likelihood of the labels under (1 - eps) P^(1/T) + eps / K, for every eps on CAL_EPS"""
    K = logp.shape[1]
    py = np.exp(temper(logp, T)[np.arange(len(y)), y])
    return np.log((1 - CAL_EPS)[None] * py[:, None] + CAL_EPS[None] / K).sum(axis=0)


def fit_T_eps(clients):
    """pooled T (capped at 1, as gatef) and each client's best eps at that T"""
    tot = np.zeros(len(CAL_T))
    for lp, y in clients:
        tot += np.array([cal_ll(lp, y, T).max() for T in CAL_T])
    T = min(CAL_T[int(tot.argmax())], 1.0)
    return T, [float(CAL_EPS[int(cal_ll(lp, y, T).argmax())]) for lp, y in clients]


def xs_m(logp, y, nn):
    P = np.exp(logp)
    nl = np.minimum(-np.log(np.maximum(P + P[:, nn], 1e-12)), NLL_CLIP)
    return float((nl[np.arange(len(y)), y] - (P * nl).sum(axis=1)).mean())


def load(ds, tag):
    """{(seed, round): [(lg, lz, y, t)]} and the look-alike map"""
    out, nn = defaultdict(list), None
    files = sorted(glob.glob(os.path.join(SR, "**", "runs", f"{ds}_{tag}", "**", "diag_samples_seed_*.json"),
                             recursive=True))
    for f in files:
        seed = int(f.rsplit("_", 1)[1].split(".")[0])
        if nn is None:
            noise = json.load(open(f.replace("diag_samples_seed", "noise_seed"), encoding="utf-8"))
            nn = np.array(next(v["nn"] for r in noise["diag"] for v in r["clients"].values() if v.get("nn")))
        for rec in json.load(open(f, encoding="utf-8")):
            if rec["round"] < 10 or not rec["rows"]:
                continue
            rows = rec["rows"]
            out[(seed, rec["round"])].append((np.array([r[20] for r in rows], dtype=np.float64),
                                              np.array([r[21] for r in rows], dtype=np.float64),
                                              np.array([r[0] for r in rows]), np.array([r[1] for r in rows])))
    return out, nn, len(files)


def gmm_suspects(s, y):
    """S3: class-normalised surprise, 1 vs 2 Gaussian components by BIC; returns (two_chosen, mask)"""
    n = len(s)
    z = np.full(n, np.nan)
    med, mad = np.median(s), np.median(np.abs(s - np.median(s)))
    scale = 1.4826 * mad if mad > 0 else s.std()
    for k in np.unique(y):
        m = y == k
        if m.sum() >= 5:
            mk = np.median(s[m])
            madk = np.median(np.abs(s[m] - mk))
            sk = 1.4826 * madk if madk > 0 else s[m].std()
            if sk > 0:
                z[m] = (s[m] - mk) / sk
                continue
        if scale > 0:
            z[m] = (s[m] - med) / scale
    if n < 2 or np.isnan(z).any() or np.ptp(z) == 0:
        return False, np.zeros(n, dtype=bool)
    X = z.reshape(-1, 1)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        g1 = GaussianMixture(1, n_init=5, random_state=0).fit(X)
        g2 = GaussianMixture(2, n_init=5, random_state=0).fit(X)
    if g2.bic(X) >= g1.bic(X):
        return False, np.zeros(n, dtype=bool)
    hi = int(np.argmax(g2.means_.ravel()))
    return True, g2.predict_proba(X)[:, hi] > 0.5


def main():
    S1 = defaultdict(lambda: defaultdict(list))
    S2 = defaultdict(lambda: np.zeros(3))     # (ds, set, rule) -> relabels, correct, suspects
    S3 = defaultdict(lambda: defaultdict(float))
    found = {}
    for ds, _ in DATASETS:
        for tag in TAGS + (NTAGS if ds in ("mnist", "eurosat") else []):
            data, nn, nf = load(ds, tag)
            found[(ds, tag)] = nf
            for _, clients in sorted(data.items()):
                lps = [np.logaddexp(lg, lz) - math.log(2.0) for lg, lz, _, _ in clients]
                ys = [y for _, _, y, _ in clients]
                T, eps = fit_T_eps(list(zip(lps, ys)))
                Tz, epsz = fit_T_eps([(lz, y) for (_, lz, y, _) in clients])
                for (lg, lz, y, t), lp, e, ez in zip(clients, lps, eps, epsz):
                    n, K = len(y), lp.shape[1]
                    idx = np.arange(n)
                    true = float((y != t).mean())
                    honest = true == 0
                    pi = (np.bincount(y, minlength=K) + 0.5) / (n + K / 2)
                    Qz = (1 - ez) * np.exp(temper(lz, Tz))[idx, y] + ez / K
                    dz = float(np.log(Qz / pi[y]).sum())
                    QP = (1 - e) * np.exp(temper(lp, T))[idx, y] + e / K
                    dP = float(np.log(QP / pi[y]).sum())
                    r = S1[ds]
                    r["dz_pos"].append(dz > 0)
                    r["dP_pos"].append(dP > 0)
                    r["err_pos" if dz > 0 else "err_neg"].append(abs(e - true))
                    if honest:
                        r["heps_pos" if dz > 0 else "heps_neg"].append(e)
                    r["err_all"].append(abs(e - true))

                    # S2
                    P = np.exp(lp)
                    PT = np.exp(temper(lp, T))
                    py = P[idx, y]
                    top, conf, confT = P.argmax(1), P.max(1), PT.max(1)
                    ag = (lg.argmax(1) == lz.argmax(1))
                    sus_i = sorted((i for i in range(n) if py[i] < 0.1), key=lambda i: py[i])[:int(0.6 * n)]
                    sus_ii = list(np.argsort(PT[idx, y], kind="stable")[:int(round(e * n))])
                    for sname, sus in (("i", sus_i), ("ii", sus_ii)):
                        for rule in ("K", "KT", "AG"):
                            acc = S2[(ds, sname, rule)]
                            for i in sus:
                                if top[i] == y[i]:
                                    continue
                                ok = {"K": conf[i] >= 0.5, "KT": confT[i] >= 0.5, "AG": ag[i]}[rule]
                                if ok:
                                    acc[0] += 1
                                    acc[1] += top[i] == t[i]
                            acc[2] += len(sus)

                    # S3
                    s = -np.log(np.maximum(py, 1e-12))
                    two, mask = gmm_suspects(s, y)
                    flag = xs_m(lp, y, nn) > 0.05
                    cl = np.zeros(n, dtype=bool)
                    if flag:
                        cl[sus_i] = True
                    wrong = y != t
                    q = S3[ds]
                    grp = "honest" if honest else "noisy"
                    q[f"cr_{grp}"] += 1
                    q[f"two_{grp}"] += two
                    q["wrong"] += wrong.sum()
                    for name, m in (("gmm", mask), ("clear", cl)):
                        q[f"{name}_marked"] += m.sum()
                        q[f"{name}_hit"] += (m & wrong).sum()
                        if honest:
                            q[f"{name}_honest_marked"] += m.sum()
                    if honest:
                        q["honest_labels"] += n

    L = ["# Offline screen 2: results (2026-11-05)", "",
         "Plan and pass rules: `screen2_plan.md` (written before these numbers). Script: "
         "`tools/screen_adaptive.py`. Stage 0 PromptFL logs, seeds 0-2, rounds 10-50.", ""]
    L += ["Files read per run: " + ", ".join(f"{ds} {tag.replace('_fp', '')} {nf}"
                                           for (ds, tag), nf in found.items()), ""]
    m = lambda v: float(np.mean(v)) if len(v) else float("nan")

    L += ["## S1: per-client predictive skill (Delta_c on zero-shot CLIP)", "",
          "| Dataset | Delta_z > 0 | Delta_P > 0 | |eps - true|, Delta_z > 0 | |eps - true|, Delta_z <= 0 | "
          "honest eps, Delta_z > 0 | honest eps, Delta_z <= 0 |", "|---|---|---|---|---|---|---|"]
    pos_err, pos_heps = [], []
    for ds, name in DATASETS:
        r = S1[ds]
        pos_err += r["err_pos"]
        pos_heps += r["heps_pos"]
        L.append(f"| {name} | {100 * m(r['dz_pos']):.0f}% | {100 * m(r['dP_pos']):.0f}% | "
                 f"{m(r['err_pos']):.3f} | {m(r['err_neg']):.3f} | {m(r['heps_pos']):.3f} | {m(r['heps_neg']):.3f} |")
    s1a = m(pos_err) <= 0.08 and m(pos_heps) <= 0.05
    cover = {ds: 100 * m(S1[ds]["dz_pos"]) for ds in OLD}
    s1b = all(v >= 90 for v in cover.values())
    s1c = all(m(S1[ds]["err_neg"]) > m(S1[ds]["err_pos"]) for ds in ("mnist", "eurosat"))
    L += ["", f"- S1-A (trust): pooled |eps - true| with Delta_z > 0 = {m(pos_err):.3f} (<= 0.08), honest eps = "
          f"{m(pos_heps):.3f} (<= 0.05): **{'PASS' if s1a else 'FAIL'}**",
          f"- S1-B (coverage on Pets / DTD / Caltech, >= 90%): "
          + ", ".join(f"{dict(DATASETS)[d]} {v:.0f}%" for d, v in cover.items())
          + f": **{'PASS' if s1b else 'FAIL'}**",
          f"- S1-C (informative on MNIST / EuroSAT, reported): {'yes' if s1c else 'no'}",
          f"- **S1: {'GO' if s1a and s1b else 'NO GO'}**", ""]

    L += ["## S2: relabel rules on suspects (per 100 suspects)", ""]
    s2 = True
    for sname, title in (("i", "suspect set (i): P(y) < 0.1, 60% cap"),
                         ("ii", "suspect set (ii): round(eps * n) lowest P_T(y)")):
        L += [f"### {title}", "", "| Dataset | rule | relabels | correct | precision | net (correct - wrong) |",
              "|---|---|---|---|---|---|"]
        for ds, name in DATASETS:
            nets = {}
            for rule in ("K", "KT", "AG"):
                rel, cor, sus = S2[(ds, sname, rule)]
                f = 100 / sus if sus else float("nan")
                nets[rule] = (2 * cor - rel) * f
                L.append(f"| {name} | {rule} | {rel * f:.1f} | {cor * f:.1f} | "
                         f"{100 * cor / rel if rel else float('nan'):.0f}% | {nets[rule]:+.1f} |")
            if sname == "i" and not nets["AG"] >= nets["K"] - 2:
                s2 = False
        L.append("")
    L += [f"- **S2 (AG net >= K net - 2 on every dataset, set (i)): {'GO' if s2 else 'NO GO'}**", ""]

    L += ["## S3: BIC mixture vs CLEAR's current rule", "",
          "| Dataset | 2 comps, noisy clients | 2 comps, honest clients | mixture precision | mixture recall | "
          "mixture honest marked | CLEAR precision | CLEAR recall | CLEAR honest marked |",
          "|---|---|---|---|---|---|---|---|---|"]
    claim, wrong_claim = True, True
    for ds, name in DATASETS:
        q = S3[ds]
        pc = lambda a, b: 100 * a / b if b else float("nan")
        two_n, two_h = pc(q["two_noisy"], q["cr_noisy"]), pc(q["two_honest"], q["cr_honest"])
        gp, gr = pc(q["gmm_hit"], q["gmm_marked"]), pc(q["gmm_hit"], q["wrong"])
        gh = pc(q["gmm_honest_marked"], q["honest_labels"])
        cp, cr = pc(q["clear_hit"], q["clear_marked"]), pc(q["clear_hit"], q["wrong"])
        ch = pc(q["clear_honest_marked"], q["honest_labels"])
        L.append(f"| {name} | {two_n:.0f}% | {two_h:.0f}% | {gp:.0f}% | {gr:.0f}% | {gh:.1f}% | "
                 f"{cp:.0f}% | {cr:.0f}% | {ch:.1f}% |")
        if ds in ("mnist", "eurosat"):
            claim &= two_n < 20 and gr < 30
            wrong_claim &= gr > cr and gp >= 70 and gh <= 5
    L += ["", f"- Prediction (2 comps in < 20% of noisy client-rounds and recall < 30% on MNIST and EuroSAT): "
          f"**{'held' if claim else 'did not hold'}**",
          f"- Mixture worth its own plan (recall above CLEAR, precision >= 70%, honest marked <= 5% on both): "
          f"**{'yes' if wrong_claim else 'no'}**", ""]
    open(OUT, "w", encoding="utf-8").write("\n".join(L))
    print("\n".join(L))


if __name__ == "__main__":
    main()
