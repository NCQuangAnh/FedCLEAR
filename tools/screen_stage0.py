"""Stage 0 screen of the referee study (results/side-research/referee_calib/margin_plan.md).

Reads the logged-only PromptFL runs with full per-image log-probabilities (`D_<sc>_fp`, `N_<x>_fp`,
--diag_full_probs true) and replays CLEAR-FPL's client flag plus three candidate second triggers on
the same client-rounds. Nothing here was tuned on these data: every threshold is the 95th
percentile of honest client-rounds in Pets clean, as for every earlier tau.

Referee e = 0.5 (global prompt + zero-shot CLIP), CLEAR's P. Per client, over its images:
  clear      CLEAR-FPL's score xs_m (flcore/diag.py _scores), flag above tau = 0.05
  cal        xs_m under e tempered to T, T per (seed, round) pooled over all clients: the largest
             T in {1.00, 0.95, ..., 0.10} whose mean max-probability reaches the share of images
             whose argmax equals the given label (sharpen only; noisy labels lower the target)
  margin     R = sum (max_k log e_k - log e_y) / sum (max_k log e_k - mean_k log e_k).
             Both sums scale by 1/T when the referee is tempered, so R does not depend on how
             confident the referee is; it needs no other client
  margin_m   the same on the look-alike-merged distribution e_k + e_nn(k) (CLEAR's merge)
A candidate is used as  flag = clear OR candidate  (every client CLEAR flags stays flagged).

Rates: rounds 10-50, all seeds. Honest = client-rounds with no wrong label (mixed + clean
settings); noisy = client-rounds with at least one wrong label (mixed settings, or N settings).

Usage: python tools/screen_stage0.py [--check FILE]
  writes results/side-research/referee_calib/stage0_screen.md
  --check: recompute xs_m from one diag_samples file and compare with the logged value
"""
import argparse
import glob
import json
import os
import statistics as st

import numpy as np

from analyze_baselines import SR

OUT = os.path.join(SR, "referee_calib", "stage0_screen.md")
DATASETS = [("mnist", "MNIST"), ("eurosat", "EuroSAT"), ("oxford_pets", "Pets"), ("dtd", "DTD"),
            ("caltech101", "Caltech101")]
OLD = ["oxford_pets", "dtd", "caltech101"]
MIXED = ["sym", "pair", "het"]
NSET = ["sym50", "pair50"]
TAU = 0.05
NLL_CLIP = 10.0
T_GRID = [round(1.0 - 0.05 * i, 2) for i in range(19)]       # 1.00 ... 0.10
CANDIDATES = ["cal", "margin", "margin_m"]
PREFER = ["margin", "margin_m", "cal"]                         # tie-break order, simplest first


def log_e(lg, lz):
    return np.logaddexp(lg, lz) - np.log(2.0)


def xs_m(logp, y, nn):
    """CLEAR's merged excess surprise, as flcore/diag.py _scores computes it."""
    P = np.exp(logp)
    merged = P + P[:, nn]
    nl = np.minimum(-np.log(np.maximum(merged, 1e-12)), NLL_CLIP)
    obs = nl[np.arange(len(y)), y]
    exp_ = (P * nl).sum(axis=1)
    return float((obs - exp_).mean())


def temper(logp, T):
    z = logp / T
    return z - np.logaddexp.reduce(z, axis=1, keepdims=True)


def margin(logp, y):
    top = logp.max(axis=1)
    a = top - logp[np.arange(len(y)), y]
    b = top - logp.mean(axis=1)
    return float(a.sum() / b.sum()) if b.sum() > 0 else 0.0


def margin_m(logp, y, nn):
    P = np.exp(logp)
    lm = np.log(np.maximum(P + P[:, nn], 1e-300))
    return margin(lm, y)


def load_run(ds, tag):
    """{(seed, round): [(client, logp e, given, true)]} and the look-alike map."""
    out, nn = {}, None
    for f in sorted(glob.glob(os.path.join(SR, "**", "runs", f"{ds}_{tag}", "**",
                                           "diag_samples_seed_*.json"), recursive=True)):
        seed = int(f.rsplit("_", 1)[1].split(".")[0])
        if nn is None:
            noise = json.load(open(f.replace("diag_samples_seed", "noise_seed"), encoding="utf-8"))
            nn = next(v["nn"] for r in noise["diag"] for v in r["clients"].values() if v.get("nn"))
        for rec in json.load(open(f, encoding="utf-8")):
            if rec["round"] < 10 or not rec["rows"]:
                continue
            rows = rec["rows"]
            lg = np.array([r[20] for r in rows], dtype=np.float64)
            lz = np.array([r[21] for r in rows], dtype=np.float64)
            y = np.array([r[0] for r in rows])
            t = np.array([r[1] for r in rows])
            out.setdefault((seed, rec["round"]), []).append((rec["client"], log_e(lg, lz), y, t))
    return out, (np.array(nn) if nn is not None else None)


def client_rounds(ds, tag):
    """[(values, noisy)] with every candidate's value for each client-round of a run."""
    data, nn = load_run(ds, tag)
    res = []
    for _, clients in data.items():
        # the pooled temperature of this (seed, round): target = share of argmax == given label
        agree = np.mean(np.concatenate([lp.argmax(1) == y for _, lp, y, _ in clients]))
        allp = np.concatenate([lp for _, lp, _, _ in clients])
        T = T_GRID[-1]
        for g in T_GRID:
            if np.exp(temper(allp, g)).max(axis=1).mean() >= agree:
                T = g
                break
        for _, lp, y, t in clients:
            v = {"clear": xs_m(lp, y, nn), "cal": xs_m(temper(lp, T), y, nn),
                 "margin": margin(lp, y), "margin_m": margin_m(lp, y, nn), "T": T}
            res.append((v, bool((y != t).any())))
    return res


def rate(vals, flag):
    return 100.0 * sum(flag(v) for v in vals) / len(vals) if vals else None


def fmt(x):
    return "—" if x is None else f"{x:.0f}%"


def main():
    runs = {}
    for ds, _ in DATASETS:
        for sc in MIXED + ["clean"]:
            runs[(ds, sc)] = client_rounds(ds, f"D_{sc}_fp")
        if ds in ("mnist", "eurosat"):
            for x in NSET:
                runs[(ds, "N" + x)] = client_rounds(ds, f"N_{x}_fp")
    pets_clean = [v for v, n in runs[("oxford_pets", "clean")] if not n]
    thr = {c: sorted(v[c] for v in pets_clean)[int(0.95 * (len(pets_clean) - 1))] for c in CANDIDATES}

    def flag_or(c):
        return lambda v: v["clear"] > TAU or v[c] > thr[c]

    rules = {"clear": lambda v: v["clear"] > TAU, **{f"clear OR {c}": flag_or(c) for c in CANDIDATES}}
    stats = {}
    for ds, _ in DATASETS:
        hon = [v for sc in MIXED + ["clean"] for v, n in runs[(ds, sc)] if not n]
        noi = [v for sc in MIXED for v, n in runs[(ds, sc)] if n]
        nall = [v for x in NSET for v, n in runs.get((ds, "N" + x), []) if n]
        for r, fn in rules.items():
            stats[(ds, r)] = (rate(hon, fn), rate(noi, fn), rate(nall, fn))
        stats[(ds, "T")] = st.median([v["T"] for sc in MIXED + ["clean"] for v, _ in runs[(ds, sc)]]
                                      or [float("nan")])
    md = ["# Stage 0 screen", "",
          "Generated by `tools/screen_stage0.py` (rules in its docstring and in `margin_plan.md`). "
          "Thresholds (Pets clean p95): " + ", ".join(f"{c} {thr[c]:.3f}" for c in CANDIDATES) +
          f"; clear tau {TAU}.", "",
          "| rule | " + " | ".join(f"{n} honest / noisy" for _, n in DATASETS) + " | MNIST / EuroSAT all-noisy |",
          "|---|" + "---|" * (len(DATASETS) + 1)]
    for r in rules:
        md.append(f"| {r} | " + " | ".join(f"{fmt(stats[(ds, r)][0])} / {fmt(stats[(ds, r)][1])}"
                                          for ds, _ in DATASETS) +
                  f" | {fmt(stats[('mnist', r)][2])} / {fmt(stats[('eurosat', r)][2])} |")
    md += ["", "Median pooled temperature of `cal`: " +
           ", ".join(f"{n} {stats[(ds, 'T')]:.2f}" for ds, n in DATASETS), ""]

    # pre-registered selection
    md += ["## Selection (margin_plan.md, fixed before the data)", ""]
    base_m = stats[("mnist", "clear")][1]
    eligible = []
    for c in CANDIDATES:
        r = f"clear OR {c}"
        e1 = all(stats[(ds, r)][0] <= stats[(ds, "clear")][0] + 7 for ds in OLD)
        e2 = stats[("mnist", r)][0] <= 10
        old = ", ".join(f"{stats[(ds, r)][0]:.1f} vs {stats[(ds, 'clear')][0]:.1f}" for ds in OLD)
        md.append(f"- {c}: E1 old datasets honest flags within +7 points of CLEAR ({old}) "
                  f"-> {'yes' if e1 else 'NO'}; E2 MNIST honest {stats[('mnist', r)][0]:.1f}% <= 10 -> "
                  f"{'yes' if e2 else 'NO'}; MNIST noisy flagged {stats[('mnist', r)][1]:.1f}% (CLEAR {base_m:.1f}%)")
        if e1 and e2:
            eligible.append(c)
    if eligible:
        best = max(stats[("mnist", f"clear OR {c}")][1] for c in eligible)
        tied = [c for c in eligible if stats[("mnist", f"clear OR {c}")][1] >= best - 2]
        win = min(tied, key=PREFER.index)
        gain = stats[("mnist", f"clear OR {win}")][1] - base_m
        go = gain >= 20
        eh, en = stats[("eurosat", f"clear OR {win}")][:2]
        conf = en - stats[("eurosat", "clear")][1] >= 20 and eh <= 10
        md += ["", f"Winner: **{win}** (threshold {thr[win]:.3f}). MNIST noisy flagged +{gain:.1f} points "
                   f"-> {'GO to stage A' if go else 'NO GO (below +20): stop, negative result'}.",
               f"EuroSAT confirmation: noisy +{en - stats[('eurosat', 'clear')][1]:.1f} points, honest {eh:.1f}% "
               f"-> {'confirmed' if conf else 'not confirmed (EuroSAT is a stated limitation in stage A)'}."]
    else:
        md += ["", "No eligible candidate: stop, negative result."]
    text = "\n".join(md) + "\n"
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, "w", encoding="utf-8").write(text)
    print(text)


def check(path):
    """xs_m recomputed from the logged log-probabilities against the value the run logged."""
    noise = json.load(open(path.replace("diag_samples_seed", "noise_seed"), encoding="utf-8"))
    logged = {(r["round"], int(c)): v for r in noise["diag"] for c, v in r["clients"].items()}
    worst = 0.0
    for rec in json.load(open(path, encoding="utf-8")):
        rows = rec["rows"]
        v = logged[(rec["round"], rec["client"])]
        lp = log_e(np.array([r[20] for r in rows], float), np.array([r[21] for r in rows], float))
        mine = xs_m(lp, np.array([r[0] for r in rows]), np.array(v["nn"]))
        worst = max(worst, abs(mine - v["e"]["xs_m"]))
        print(f"round {rec['round']} client {rec['client']}: logged {v['e']['xs_m']:+.5f} "
              f"recomputed {mine:+.5f}  margin {margin(lp, np.array([r[0] for r in rows])):.3f}")
    print("largest difference", worst)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--check")
    a = ap.parse_args()
    check(a.check) if a.check else main()
