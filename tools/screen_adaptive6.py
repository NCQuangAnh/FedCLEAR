"""Offline screen 6 (results/side-research/adaptive_thr/screen6_plan.md): goodness of fit of the noise model."""
import math, os
from collections import defaultdict
import numpy as np
from scipy import stats
from analyze_baselines import SR
from screen_adaptive import DATASETS, NTAGS, OLD, TAGS, fit_T_eps, temper
from screen_adaptive3 import load_all

OUT = os.path.join(SR, "adaptive_thr", "screen6.md")


def main():
    rng = np.random.default_rng(0)
    S = defaultdict(lambda: defaultdict(list))
    for ds, _ in DATASETS:
        for tag in TAGS + (NTAGS if ds in ("mnist", "eurosat") else []):
            for (seed, rd), clients in sorted(load_all(ds, tag).items()):
                if rd < 10:
                    continue
                lps = [np.logaddexp(lg, lz) - math.log(2.0) for _, lg, lz, _, _ in clients]
                T, eps = fit_T_eps([(lp, c[3]) for lp, c in zip(lps, clients)])
                _, epsz = fit_T_eps([(c[2], c[3]) for c in clients])
                A = E = V = 0.0
                Qs, Ps, ys = [], [], []
                errs, heps = [], []
                for (c, lg, lz, y, t), lp, e in zip(clients, lps, eps):
                    n, K = lp.shape
                    P = np.exp(lp)
                    Q = (1 - e) * np.exp(temper(lp, T)) + e / K
                    top = P.argmax(1)
                    q = Q[np.arange(n), top]
                    A += (y == top).sum(); E += q.sum(); V += (q * (1 - q)).sum()
                    Qs.append(Q); Ps.append(P); ys.append(y)
                    true = float((y != t).mean())
                    errs.append(abs(e - true))
                    if true == 0:
                        heps.append(e)
                g1 = V > 0 and 2 * stats.norm.sf(abs(A - E) / math.sqrt(V)) > 0.05
                d = np.array(epsz) - np.array(eps)
                g2 = True if np.allclose(d, d[0]) else stats.ttest_1samp(d, 0).pvalue > 0.05

                def rho(lab):
                    s = a = 0
                    for P, y in zip(Ps, lab):
                        idx = np.arange(len(y))
                        Si = P[idx, y] < 0.1
                        Pm = P.copy(); Pm[idx, y] = -1
                        Ai = Pm.max(1) >= 0.5
                        s += Si.sum(); a += (Si & Ai).sum()
                    return a / s if s else None
                obs = rho(ys)
                if obs is None:
                    g3 = False
                else:
                    # vectorised: per image, S and S&A depend only on the sampled class k
                    s_tot = np.zeros(500); a_tot = np.zeros(500)
                    for P, Q in zip(Ps, Qs):
                        n, K = P.shape
                        Sk = P < 0.1
                        srt = np.sort(P, axis=1)
                        am = P.argmax(1)
                        alt = np.where(np.arange(K)[None] == am[:, None], srt[:, -2:-1], srt[:, -1:]) >= 0.5
                        cum = np.cumsum(Q / Q.sum(1, keepdims=True), axis=1)
                        u = rng.random((500, n, 1))
                        k = np.minimum((u > cum[None]).sum(2), K - 1)
                        idx = np.arange(n)[None]
                        si = Sk[idx, k]
                        s_tot += si.sum(1); a_tot += (si & alt[idx, k]).sum(1)
                    sims = [a / s for a, s in zip(a_tot, s_tot) if s > 0]
                    g3 = (1 + sum(r <= obs for r in sims)) / (len(sims) + 1) > 0.05
                for name, ok in (("G1", g1), ("G2", g2), ("G3", g3)):
                    s = S[(ds, name)]
                    s["open"].append(ok)
                    if ok:
                        s["err"] += errs; s["heps"] += heps
    m = lambda v: float(np.mean(v)) if len(v) else float("nan")
    L = ["# Offline screen 6: results (2026-11-05)", "", "Plan: `screen6_plan.md`. Script: `tools/screen_adaptive6.py`.", ""]
    for name in ("G1", "G2", "G3"):
        L += [f"## {name}", "", "| Dataset | opens | eps error when open | honest eps when open | pass |", "|---|---|---|---|---|"]
        allok = True
        for ds, dn in DATASETS:
            s = S[(ds, name)]
            op = 100 * m(s["open"])
            ok = op >= 90 if ds in OLD else (op <= 10 or (m(s["err"]) <= 0.08 and (not s["heps"] or m(s["heps"]) <= 0.05)))
            allok &= ok
            L.append(f"| {dn} | {op:.0f}% | {m(s['err']):.3f} | {m(s['heps']):.3f} | {'yes' if ok else 'no'} |")
        L += ["", f"- **{name}: {'GO' if allok else 'NO GO'}**", ""]
    open(OUT, "w", encoding="utf-8").write("\n".join(L))
    print("\n".join(L))


if __name__ == "__main__":
    main()
