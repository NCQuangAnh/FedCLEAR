"""Offline screen behind results/side-research/calrepair/calrepair_plan.md (exploratory, 2026-10-29).

Replays CLEAR-FPL's repair and three alternatives on the stage-0 logs (PromptFL runs with every
class's log-probability per image, `D_<sc>_fp` / `N_<x>_fp`, seeds 0-2, rounds 10-50), and on
synthetic all-noisy labels: the labels of the clean runs flipped offline (sym / pair, 25 / 50 / 75%)
while the referee stays the clean-trained one. This is the development data of the plan; the
real-run rules in the plan are fixed after it and before any real run.

Referee P = 0.5 (global prompt + zero-shot CLIP), as in CLEAR-FPL.

Noise-aware temperature (one per seed and round, pooled over the clients):
  each client c has labels y ~ (1 - eps_c) Cat(P^(1/T)) + eps_c Uniform(K). For each T on a grid it
  takes its own best eps_c (profile likelihood); the server sums the clients' profile
  log-likelihoods and keeps the best T. A wrong label is explained by eps_c, not by softening P, so
  noisy clients do not pull T, and a federation where every client is noisy still has a T.

Designs (all relabel exactly as CLEAR-FPL: to raw P's top class when raw P is >= 0.5 sure, else drop):
  CLEAR  flag = xs_m(P) > 0.05; suspects P(label) < 0.1, at most 60% of the client
  nc05   CLEAR's flag; suspects P(label) < 0.05, no cap (cap study, exploratory there)
  A      CLEAR's flag; suspects = labels outside the calibrated referee's 95% prediction set,
         i.e. sum_k P_T,k [P_T,k <= P_T,label] < 0.05; no threshold, no cap
  B      A, but a client is also flagged when xs_m(P_T) > its Pets-clean 95th percentile

Per design: share of wrong labels caught, share of correct labels touched (dropped or relabelled),
noise left in the training set (wrong labels kept or relabelled to another wrong class, over the
images kept), and the share of honest client-rounds that lose at least one image.

Usage: python tools/screen_calrepair.py   (writes results/side-research/calrepair/offline_screen.md)
"""
import glob
import json
import os

import numpy as np

from analyze_baselines import SR
from screen_stage0 import xs_m

OUT = os.path.join(SR, "calrepair", "offline_screen.md")
K = {"mnist": 10, "eurosat": 10, "oxford_pets": 37, "dtd": 47, "caltech101": 100}
NAMES = {"mnist": "MNIST", "eurosat": "EuroSAT", "oxford_pets": "Pets", "dtd": "DTD", "caltech101": "Caltech101"}
T_GRID = np.round(np.exp(np.linspace(np.log(0.1), np.log(2.0), 25)), 3)
E_GRID = np.linspace(0, 0.95, 96)
ALPHA = 0.05
DESIGNS = ["CLEAR", "nc05", "A", "B"]


def load(ds, tag):
    """{(seed, round): [client dicts: lp (log P), y given, t true]}"""
    out = {}
    for f in sorted(glob.glob(os.path.join(SR, "**", "runs", f"{ds}_{tag}", "**", "diag_samples_seed_*.json"),
                              recursive=True)):
        seed = f.rsplit("_", 1)[1]
        for rec in json.load(open(f, encoding="utf-8")):
            if rec["round"] < 10 or not rec["rows"]:
                continue
            R = rec["rows"]
            lp = np.logaddexp(np.array([r[20] for r in R], float), np.array([r[21] for r in R], float)) - np.log(2)
            out.setdefault((seed, rec["round"]), []).append(
                {"lp": lp, "y": np.array([r[0] for r in R]), "t": np.array([r[1] for r in R])})
    return out


def look_alike(ds):
    f = glob.glob(os.path.join(SR, "**", "runs", f"{ds}_D_clean_fp", "**", "noise_seed_0.json"), recursive=True)[0]
    noise = json.load(open(f, encoding="utf-8"))
    return np.array(next(v["nn"] for r in noise["diag"] for v in r["clients"].values() if v.get("nn")))


def temper(lp, T):
    z = lp / T
    return z - np.logaddexp.reduce(z, axis=1, keepdims=True)


def profile(lpT, y, k):
    py = np.exp(lpT[np.arange(len(y)), y])
    return np.log((1 - E_GRID)[None] * py[:, None] + E_GRID[None] / k).sum(0).max()


def fit_T(clients, k):
    tot = [sum(profile(temper(c["lp"], T), c["y"], k) for c in clients) for T in T_GRID]
    return float(T_GRID[int(np.argmax(tot))])


def synth(clients, k, kind, rate, rng):
    out = []
    for c in clients:
        t = c["t"]
        flip = rng.random(len(t)) < rate
        y = np.where(flip, (t + rng.integers(1, k, len(t))) % k, t) if kind == "sym" else np.where(flip, (t + 1) % k, t)
        out.append({"lp": c["lp"], "y": y, "t": t})
    return out


def client_values(clients, k, nn):
    T = fit_T(clients, k)
    vals = []
    for c in clients:
        lpT = temper(c["lp"], T)
        vals.append({"c": c, "T": T, "lpT": lpT, "xs1": xs_m(c["lp"], c["y"], nn), "xsT": xs_m(lpT, c["y"], nn),
                     "noisy": bool((c["y"] != c["t"]).any())})
    return vals


def suspects(v, design, thr_b, all_flagged):
    c = v["c"]
    n = len(c["y"])
    idx = np.arange(n)
    py = np.exp(c["lp"][idx, c["y"]])
    flag = all_flagged or v["xs1"] > 0.05
    if design in ("CLEAR", "nc05"):
        thr, cap = (0.1, 0.6) if design == "CLEAR" else (0.05, 1.0)
        s = np.zeros(n, bool)
        if flag:
            s[[i for i in np.argsort(py) if py[i] < thr][:int(cap * n)]] = True
        return s
    PT = np.exp(v["lpT"])
    pyT = PT[idx, c["y"]]
    pval = (PT * (PT <= pyT[:, None] + 1e-12)).sum(1)
    if design == "B":
        flag = flag or v["xsT"] > thr_b
    return (pval < ALPHA) & flag


def outcome(v, sus):
    c = v["c"]
    P = np.exp(c["lp"])
    pred, conf = P.argmax(1), P.max(1)
    wrong = c["y"] != c["t"]
    rel = sus & (pred != c["y"]) & (conf >= 0.5)
    drop = sus & ~rel
    honest = not wrong.any()
    return {"W": wrong.sum(), "C": (~wrong).sum(), "caught": (sus & wrong).sum(), "touched": (sus & ~wrong).sum(),
            "res": (wrong & ~sus).sum() + (rel & (pred != c["t"])).sum(), "size": len(c["y"]) - drop.sum(),
            "hon": int(honest), "hon_touch": int(honest and sus.any())}


def summarise(vals, thr_b, all_flagged=False):
    res = {}
    for d in DESIGNS:
        tot = {}
        for v in vals:
            for a, b in outcome(v, suspects(v, d, thr_b, all_flagged)).items():
                tot[a] = tot.get(a, 0) + b
        res[d] = tot
    return res


def cell(s, show_h):
    txt = f"{100 * s['caught'] / max(1, s['W']):.0f} / {100 * s['touched'] / max(1, s['C']):.1f} / {100 * s['res'] / max(1, s['size']):.1f}"
    if show_h and s["hon"]:
        txt += f" / {100 * s['hon_touch'] / s['hon']:.0f}"
    return txt


def main():
    real, syn, Ts = {}, {}, {}
    for ds, k in K.items():
        nn = look_alike(ds)
        for sc in ["sym", "pair", "het", "clean"] + (["Nsym50", "Npair50"] if ds in ("mnist", "eurosat") else []):
            tag = f"N_{sc[1:]}_fp" if sc.startswith("N") else f"D_{sc}_fp"
            real[(ds, sc)] = [v for cl in load(ds, tag).values() for v in client_values(cl, k, nn)]
        clean = load(ds, "D_clean_fp")
        rng = np.random.default_rng(0)
        for kind in ("sym", "pair"):
            for rate in (25, 50, 75):
                syn[(ds, f"{kind}{rate}")] = [v for cl in clean.values()
                                              for v in client_values(synth(cl, k, kind, rate / 100, rng), k, nn)]
    pets = sorted(v["xsT"] for v in real[("oxford_pets", "clean")] if not v["noisy"])
    thr_b = pets[int(0.95 * (len(pets) - 1))]

    md = ["# Calibrated repair: offline screen (exploratory)", "",
          "Generated by `tools/screen_calrepair.py` (definitions in its docstring). Development data for "
          "`calrepair_plan.md`; nothing here is a real-run result.", "",
          f"Design B's extra flag threshold (calibrated client score, Pets clean p95): {thr_b:.3f}.", "",
          "## The calibrated referee", "",
          "| dataset | median temperature | honest score, raw / calibrated | noisy score, raw / calibrated | "
          "flags honest / noisy: CLEAR | B |", "|---|---|---|---|---|---|"]
    for ds in K:
        hon = [v for sc in ("sym", "pair", "het", "clean") for v in real[(ds, sc)] if not v["noisy"]]
        noi = [v for sc in ("sym", "pair", "het") for v in real[(ds, sc)] if v["noisy"]]
        T = np.median([v["T"] for sc in ("sym", "pair", "het", "clean") for v in real[(ds, sc)]])

        def r(vs, f):
            return 100 * np.mean([f(v) for v in vs])
        md.append(f"| {NAMES[ds]} | {T:.2f} | {np.median([v['xs1'] for v in hon]):+.2f} / {np.median([v['xsT'] for v in hon]):+.2f} | "
                  f"{np.median([v['xs1'] for v in noi]):+.2f} / {np.median([v['xsT'] for v in noi]):+.2f} | "
                  f"{r(hon, lambda v: v['xs1'] > 0.05):.0f}% / {r(noi, lambda v: v['xs1'] > 0.05):.0f}% | "
                  f"{r(hon, lambda v: v['xs1'] > 0.05 or v['xsT'] > thr_b):.0f}% / {r(noi, lambda v: v['xs1'] > 0.05 or v['xsT'] > thr_b):.0f}% |")
    head = "| dataset | setting | " + " | ".join(DESIGNS) + " |"
    md += ["", "## Real labels (stage-0 runs, PromptFL referee)", "",
           "Each cell: wrong labels caught % / correct labels touched % / noise left % / honest client-rounds "
           "touched %.", "", head, "|---|---|" + "---|" * len(DESIGNS)]
    for (ds, sc), vals in real.items():
        s = summarise(vals, thr_b)
        md.append(f"| {NAMES[ds]} | {sc} | " + " | ".join(cell(s[d], True) for d in DESIGNS) + " |")
    md += ["", "## Synthetic all-noisy labels (clean-trained referee, every client flagged as in CLEAR's gate N runs)", "",
           "Each cell: wrong labels caught % / correct labels touched % / noise left %.", "", head,
           "|---|---|" + "---|" * len(DESIGNS)]
    for (ds, sc), vals in syn.items():
        s = summarise(vals, thr_b, all_flagged=True)
        md.append(f"| {NAMES[ds]} | {sc} | " + " | ".join(cell(s[d], False) for d in DESIGNS) + " |")
    text = "\n".join(md) + "\n"
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, "w", encoding="utf-8").write(text)
    print(text)


if __name__ == "__main__":
    main()
