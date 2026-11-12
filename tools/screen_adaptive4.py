"""Offline screen 4 (results/side-research/adaptive_thr/screen4_plan.md): per-client rules to replace g."""
import math, os
from collections import defaultdict
import numpy as np
from analyze_baselines import SR
from screen_adaptive import CAL_T, DATASETS, NTAGS, OLD, TAGS, fit_T_eps, temper
from screen_adaptive3 import delta_loo, load_all, profile

OUT = os.path.join(SR, "adaptive_thr", "screen4.md")


def gain(PT, y, e, sus):
    K = PT.shape[1]
    g = 0.0
    for i in sus:
        tr = np.full(K, e / K); tr[y[i]] = 1 - e + e / K
        r = PT[i] * tr; r = r / r.sum()
        k = int(r.argmax())
        rep = 2 * r[k] - 1 if (k != y[i] and r[k] > 0.5) else 0.0
        g += rep - (2 * r[y[i]] - 1)
    return g


def main():
    S = defaultdict(lambda: defaultdict(list))
    for ds, _ in DATASETS:
        for tag in TAGS + (NTAGS if ds in ("mnist", "eurosat") else []):
            for (seed, rd), clients in sorted(load_all(ds, tag).items()):
                if rd < 10:
                    continue
                lps = [np.logaddexp(lg, lz) - math.log(2.0) for _, lg, lz, _, _ in clients]
                T, eps = fit_T_eps([(lp, y) for lp, (_, _, _, y, _) in zip(lps, clients)])
                profs = [profile(lz, y) for _, _, lz, y, _ in clients]
                tot = np.sum(profs, axis=0)
                for ci, ((c, lg, lz, y, t), lp, e) in enumerate(zip(clients, lps, eps)):
                    n = len(y)
                    true = float((y != t).mean())
                    Tz = min(CAL_T[int((tot - profs[ci]).argmax())], 1.0)
                    PT = np.exp(temper(lp, T))
                    sus = list(np.argsort(PT[np.arange(n), y], kind="stable")[:int(round(e * n))])
                    c1 = delta_loo(lz, y, Tz) > 0
                    c2 = gain(PT, y, e, sus) > 0
                    for name, ok in (("C1", c1), ("C2", c2), ("C3", c1 and c2)):
                        s = S[(ds, name)]
                        s["open"].append(ok)
                        if ok:
                            s["err"].append(abs(e - true))
                            if true == 0:
                                s["heps"].append(e)
    m = lambda v: float(np.mean(v)) if len(v) else float("nan")
    L = ["# Offline screen 4: results (2026-11-05)", "", "Plan: `screen4_plan.md`. Script: `tools/screen_adaptive4.py`.", ""]
    for name in ("C1", "C2", "C3"):
        L += [f"## {name}", "", "| Dataset | opens | |eps - true| when open | honest eps when open | pass |", "|---|---|---|---|---|"]
        allok = True
        for ds, dn in DATASETS:
            s = S[(ds, name)]
            op = 100 * m(s["open"])
            if ds in OLD:
                ok = op >= 90
            else:
                ok = op <= 10 or (m(s["err"]) <= 0.08 and (not s["heps"] or m(s["heps"]) <= 0.05))
            allok &= ok
            L.append(f"| {dn} | {op:.0f}% | {m(s['err']):.3f} | {m(s['heps']):.3f} | {'yes' if ok else 'no'} |")
        L += ["", f"- **{name}: {'GO' if allok else 'NO GO'}**", ""]
    open(OUT, "w", encoding="utf-8").write("\n".join(L))
    print("\n".join(L))


if __name__ == "__main__":
    main()
