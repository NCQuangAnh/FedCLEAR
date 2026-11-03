"""Offline check: does averaging CLEAR's client score over rounds (a 'middle stage' that pools
evidence) separate noisy from honest clients better than the per-round flag?

Data: stage 0 logged-only PromptFL runs (3 seeds, diag every 5 rounds), referee e = CLEAR's P.
Per (setting, seed, client): s_R = xs_m at round R; m_R = mean of s over rounds 5..R.
Threshold for m_R: 95th percentile of honest clients on Pets (transferred, never tuned on MNIST).
"""
import glob
import json
import os
import sys

import numpy as np

sys.path.insert(0, 'tools')
from analyze_baselines import SR
from screen_stage0 import log_e, xs_m

DATASETS = [("mnist", "MNIST"), ("eurosat", "EuroSAT"), ("oxford_pets", "Pets"), ("dtd", "DTD"),
            ("caltech101", "Caltech101")]
MIXED = ["sym", "pair", "het"]
NSET = ["sym50", "pair50"]
CHECK = [10, 20, 30, 50]


def load(ds, tag):
    """{(seed, client): ({round: xs_m}, noisy)}"""
    out = {}
    for f in sorted(glob.glob(os.path.join(SR, "**", "runs", f"{ds}_{tag}", "**",
                                           "diag_samples_seed_*.json"), recursive=True)):
        seed = int(f.rsplit("_", 1)[1].split(".")[0])
        noise = json.load(open(f.replace("diag_samples_seed", "noise_seed"), encoding="utf-8"))
        nn = np.array(next(v["nn"] for r in noise["diag"] for v in r["clients"].values() if v.get("nn")))
        for rec in json.load(open(f, encoding="utf-8")):
            rows = rec["rows"]
            if not rows:
                continue
            lp = log_e(np.array([r[20] for r in rows], float), np.array([r[21] for r in rows], float))
            y = np.array([r[0] for r in rows])
            t = np.array([r[1] for r in rows])
            d, _ = out.setdefault((seed, rec["client"]), ({}, bool((y != t).any())))
            d[rec["round"]] = xs_m(lp, y, nn)
    return out


def auroc(h, n):
    h, n = np.asarray(h), np.asarray(n)
    if not len(h) or not len(n):
        return float("nan")
    return float(((n[:, None] > h[None, :]).mean() + 0.5 * (n[:, None] == h[None, :]).mean()))


def feats(runs, R):
    """per client: (s_R, m_R, noisy)"""
    res = []
    for d, noisy in runs.values():
        rs = sorted(r for r in d if 5 <= r <= R)
        if R in d and rs:
            res.append((d[R], float(np.mean([d[r] for r in rs])), noisy))
    return res


data = {}
for ds, _ in DATASETS:
    for sc in MIXED + ["clean"]:
        data[(ds, sc)] = load(ds, f"D_{sc}_fp")
    if ds in ("mnist", "eurosat"):
        for x in NSET:
            data[(ds, "N" + x)] = load(ds, f"N_{x}_fp")

for R in CHECK:
    F = {k: feats(v, R) for k, v in data.items()}
    pets_h = [f for sc in MIXED + ["clean"] for f in F[("oxford_pets", sc)] if not f[2]]
    thr_m = float(np.quantile([f[1] for f in pets_h], 0.95))
    thr_s = float(np.quantile([f[0] for f in pets_h], 0.95))
    print(f"\n=== round {R}: Pets-honest p95 threshold  per-round s {thr_s:+.3f} | running mean m {thr_m:+.3f}")
    print(f"{'dataset':10s} | AUROC s / m | CLEAR tau .05: hon / noisy / allN | s>p95: hon / noisy / allN"
          f" | m>p95: hon / noisy / allN | oracle m @5% hon: noisy")
    for ds, name in DATASETS:
        hon = [f for sc in MIXED + ["clean"] for f in F[(ds, sc)] if not f[2]]
        noi = [f for sc in MIXED for f in F[(ds, sc)] if f[2]]
        alln = [f for x in NSET for f in F.get((ds, "N" + x), []) if f[2]]

        def r(fs, i, thr):
            return "  —" if not fs else f"{100 * np.mean([f[i] > thr for f in fs]):3.0f}"
        a_s = auroc([f[0] for f in hon], [f[0] for f in noi])
        a_m = auroc([f[1] for f in hon], [f[1] for f in noi])
        orc = float(np.quantile([f[1] for f in hon], 0.95))
        print(f"{name:10s} | {a_s:.2f} / {a_m:.2f} | {r(hon,0,.05)} / {r(noi,0,.05)} / {r(alln,0,.05)}"
              f" | {r(hon,0,thr_s)} / {r(noi,0,thr_s)} / {r(alln,0,thr_s)}"
              f" | {r(hon,1,thr_m)} / {r(noi,1,thr_m)} / {r(alln,1,thr_m)} | {r(noi,1,orc)}"
              f"   (n hon {len(hon)}, noisy {len(noi)}, allN {len(alln)}; median m hon {np.median([f[1] for f in hon]):+.2f}"
              f" noisy {np.median([f[1] for f in noi]):+.2f})")
