"""Offline screen 5 (results/side-research/adaptive_thr/screen5_plan.md): permutation p-value gate."""
import math, os
from collections import defaultdict
import numpy as np
from analyze_baselines import SR
from screen_adaptive import DATASETS, NTAGS, OLD, TAGS, fit_T_eps
from screen_adaptive3 import load_all

OUT = os.path.join(SR, "adaptive_thr", "screen5.md")
B = 2000


def perm_p(lz, y, rng):
    n, K = lz.shape
    if n < 2:
        return None
    cnt = np.bincount(y, minlength=K)
    lpi = np.log((cnt[y] - 1 + 0.5) / (n - 1 + K / 2))
    obs = (lz[np.arange(n), y] - lpi).mean()
    A = lz[:, y]                                  # A[j, i] = log z_j(y_i)
    ge = 0
    for _ in range(B):
        perm = rng.permutation(n)
        ge += (A[perm, np.arange(n)] - lpi).mean() >= obs - 1e-12
    return (1 + ge) / (B + 1)


def main():
    rng = np.random.default_rng(0)
    S = defaultdict(lambda: defaultdict(list))
    for ds, _ in DATASETS:
        for tag in TAGS + (NTAGS if ds in ("mnist", "eurosat") else []):
            pcache = {}
            for (seed, rd), clients in sorted(load_all(ds, tag).items()):
                if rd < 10:
                    continue
                lps = [np.logaddexp(lg, lz) - math.log(2.0) for _, lg, lz, _, _ in clients]
                _, eps = fit_T_eps([(lp, c[3]) for lp, c in zip(lps, clients)])
                for (c, lg, lz, y, t), e in zip(clients, eps):
                    if (seed, c) not in pcache:
                        pcache[(seed, c)] = perm_p(lz, y, rng)
                    p = pcache[(seed, c)]
                    ok = p is not None and p <= 0.05
                    true = float((y != t).mean())
                    s = S[ds]
                    s["open"].append(ok)
                    s["n"].append(len(y))
                    if ok:
                        s["err"].append(abs(e - true))
                        if true == 0:
                            s["heps"].append(e)
    m = lambda v: float(np.mean(v)) if len(v) else float("nan")
    L = ["# Offline screen 5: results (2026-11-05)", "", "Plan: `screen5_plan.md`. Script: `tools/screen_adaptive5.py`.", "",
         "| Dataset | median images | opens | |eps - true| when open | honest eps when open | pass |", "|---|---|---|---|---|---|"]
    allok = True
    for ds, dn in DATASETS:
        s = S[ds]
        op = 100 * m(s["open"])
        ok = op >= 90 if ds in OLD else (op <= 10 or (m(s["err"]) <= 0.08 and (not s["heps"] or m(s["heps"]) <= 0.05)))
        allok &= ok
        L.append(f"| {dn} | {np.median(s['n']):.0f} | {op:.0f}% | {m(s['err']):.3f} | {m(s['heps']):.3f} | {'yes' if ok else 'no'} |")
    L += ["", f"- **Permutation gate: {'GO' if allok else 'NO GO'}**", ""]
    open(OUT, "w", encoding="utf-8").write("\n".join(L))
    print("\n".join(L))


if __name__ == "__main__":
    main()
