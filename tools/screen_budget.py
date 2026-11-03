"""Noise-budget repair, offline check: rules of results/side-research/calrepair/budget_screen_plan.md.

Design E: a client flagged by CLEAR-FPL's own score repairs its round(eps * n) least plausible
images, eps = its best-fit noise share under the noise-aware model at the pooled temperature (the
eps `cal` logs), plausibility = calibrated P_T(label). Relabelling as CLEAR-FPL.
  R  real cal runs: |eps - true noise| per flagged client-round                       -> check 1
  F  stage-0 D_*_fp logs (real S noise, full probabilities): honest clients touched     -> check 2
  Y  synthetic all-noisy DTD 25% from the clean-trained referee: E vs design A          -> check 3
  D  N_*_diag logs (referee trained on the noisy labels, T = 1): E vs CLEAR-FPL's rule  -> check 4

Usage: python tools/screen_budget.py   (writes results/side-research/calrepair/budget_screen.md)
"""
import glob
import json
import os

import numpy as np

from analyze_baselines import SR
from analyze_calrepair import tag
from analyze_client_estimates import files
from screen_calrepair import E_GRID, K, client_values, load, look_alike, suspects, synth

OUT = os.path.join(SR, "calrepair", "budget_screen.md")
NAMES = {"mnist": "MNIST", "eurosat": "EuroSAT", "oxford_pets": "Pets", "dtd": "DTD", "caltech101": "Caltech101"}


def eps_of(py, k):
    ll = np.log((1 - E_GRID)[None] * py[:, None] + E_GRID[None] / k).sum(0)
    return float(E_GRID[int(np.argmax(ll))])


def lowest(py, m):
    s = np.zeros(len(py), bool)
    s[np.argsort(py, kind="stable")[:m]] = True
    return s


def tally(y, t, pred, conf, sus, tot):
    wrong = y != t
    rel = sus & (pred != y) & (conf >= 0.5)
    drop = sus & ~rel
    for a, b in {"W": wrong.sum(), "C": (~wrong).sum(), "caught": (sus & wrong).sum(),
                 "touched": (sus & ~wrong).sum(),
                 "res": (wrong & ~sus).sum() + (rel & (pred != t)).sum(),
                 "size": len(y) - drop.sum()}.items():
        tot[a] = tot.get(a, 0) + int(b)


def pct(s):
    return (100 * s["caught"] / max(1, s["W"]), 100 * s["touched"] / max(1, s["C"]),
            100 * s["res"] / max(1, s["size"]))


def cell(s):
    a, b, c = pct(s)
    return f"{a:.0f} / {b:.1f} / {c:.1f}"


# --- check 1: real cal runs ----------------------------------------------------------------------
R_SET = [(d, ("N", x)) for d in ("oxford_pets", "dtd", "caltech101") for x in ("sym75", "pair75")] + \
        [("dtd", ("N", "sym25")), ("dtd", ("N", "pair25"))]


def check1():
    per = {}
    for ds, k in R_SET:
        err = []
        for f in files(tag(ds, *k, "cal")):
            for r in json.load(open(f, encoding="utf-8")).get("sure") or []:
                if 1 <= r["round"] <= 50:
                    err += [c["eps"] - c["noise"] for c in r["clients"].values()
                            if c.get("flag") and c.get("eps") is not None]
        per[(ds, k)] = err
    return per


# --- checks 2 and 3: full-probability logs -------------------------------------------------------
def budget_sus(v, all_flagged):
    c = v["c"]
    if not (all_flagged or v["xs1"] > 0.05):
        return np.zeros(len(c["y"]), bool)
    k = c["lp"].shape[1]
    pyT = np.exp(v["lpT"][np.arange(len(c["y"])), c["y"]])
    return lowest(pyT, int(round(eps_of(pyT, k) * len(c["y"]))))


def run_full(vals, designs, all_flagged, honest_only=False):
    res = {}
    for d in designs:
        tot = {}
        for v in vals:
            if honest_only and v["noisy"]:
                continue
            c = v["c"]
            P = np.exp(c["lp"])
            sus = budget_sus(v, all_flagged) if d == "E" else suspects(v, d, 0.0, all_flagged)
            tally(c["y"], c["t"], P.argmax(1), P.max(1), sus, tot)
        res[d] = tot
    return res


# --- check 4: logs of a referee trained on the noisy labels (no full probabilities) --------------
def load_diag(ds, sc):
    out = []
    for f in glob.glob(os.path.join(SR, "**", "runs", f"{ds}_N_{sc}_diag", "**", "diag_samples_seed_*.json"),
                       recursive=True):
        for rec in json.load(open(f, encoding="utf-8")):
            if rec["round"] < 10 or not rec["rows"]:
                continue
            R = rec["rows"]
            out.append({"y": np.array([r[0] for r in R]), "t": np.array([r[1] for r in R]),
                        "py": np.array([r[14] for r in R], float), "pred": np.array([r[15] for r in R]),
                        "conf": np.array([r[16] for r in R], float)})
    return out


def run_diag(clients, k):
    res = {d: {} for d in ("CLEAR", "E", "oracle")}
    for c in clients:
        n = len(c["y"])
        s_clear = np.zeros(n, bool)
        s_clear[[i for i in np.argsort(c["py"], kind="stable") if c["py"][i] < 0.1][:int(0.6 * n)]] = True
        s_e = lowest(c["py"], int(round(eps_of(c["py"], k) * n)))
        s_o = lowest(c["py"], int(round((c["y"] != c["t"]).mean() * n)))
        for d, s in (("CLEAR", s_clear), ("E", s_e), ("oracle", s_o)):
            tally(c["y"], c["t"], c["pred"], c["conf"], s, res[d])
    return res, len(clients)


def main():
    md = ["# Noise-budget repair: offline check", "",
          "Generated by `tools/screen_budget.py`; rules in `budget_screen_plan.md` (fixed before computing). "
          "Cells: wrong labels caught % / correct labels touched % / noise left %.", ""]
    verdict = {}

    per = check1()
    md += ["## Check 1: eps against the true noise share (real `cal` runs, flagged client-rounds)", "",
           "| dataset | setting | client-rounds | mean abs error | mean bias (eps − true) |", "|---|---|---|---|---|"]
    by_ds = {}
    for (ds, k), e in per.items():
        by_ds.setdefault(ds, []).extend(e)
        md.append(f"| {NAMES[ds]} | {' '.join(k)} | {len(e)} | {np.mean(np.abs(e)):.3f} | {np.mean(e):+.3f} |")
    ok1 = all(np.mean(np.abs(e)) <= 0.10 for e in by_ds.values())
    md += ["", "Per dataset: " + ", ".join(f"{NAMES[d]} {np.mean(np.abs(e)):.3f}" for d, e in by_ds.items())
           + f" (<= 0.10) -> **{'pass' if ok1 else 'FAIL'}**", ""]
    verdict["1"] = ok1

    md += ["## Check 2: honest clients (stage-0 real S noise, honest client-rounds only)", "",
           "| dataset | CLEAR-FPL | E | correct touched: E <= CLEAR |", "|---|---|---|---|"]
    ok2 = True
    full = {}
    for ds in ("oxford_pets", "dtd", "caltech101"):
        k, nn = K[ds], look_alike(ds)
        vals = [v for sc in ("sym", "pair", "het", "clean") for cl in load(ds, f"D_{sc}_fp").values()
                for v in client_values(cl, k, nn)]
        r = run_full(vals, ["CLEAR", "E"], all_flagged=False, honest_only=True)
        good = pct(r["E"])[1] <= pct(r["CLEAR"])[1] + 1e-9
        ok2 &= good
        md.append(f"| {NAMES[ds]} | {cell(r['CLEAR'])} | {cell(r['E'])} | {'pass' if good else 'FAIL'} |")
        # report only: all clients of the real S settings
        full[ds] = {sc: run_full([v for cl in load(ds, f"D_{sc}_fp").values() for v in client_values(cl, k, nn)],
                                 ["CLEAR", "A", "E"], all_flagged=False) for sc in ("sym", "pair", "het")}
    md += ["", f"-> **{'pass' if ok2 else 'FAIL'}**", ""]
    verdict["2"] = ok2

    md += ["## Check 3: DTD 25%, synthetic all-noisy (clean-trained referee, every client flagged)", "",
           "| setting | CLEAR-FPL | A (prediction set) | E | E touched <= A + 1, E noise <= A |", "|---|---|---|---|---|"]
    ok3 = True
    k, nn = K["dtd"], look_alike("dtd")
    clean = load("dtd", "D_clean_fp")
    rng = np.random.default_rng(0)
    syn = {}
    for kind in ("sym", "pair"):
        for rate in (25, 50, 75):
            syn[f"{kind}{rate}"] = [v for cl in clean.values()
                                    for v in client_values(synth(cl, k, kind, rate / 100, rng), k, nn)]
    for sc in ("sym25", "pair25"):
        r = run_full(syn[sc], ["CLEAR", "A", "E"], all_flagged=True)
        a, e = pct(r["A"]), pct(r["E"])
        good = e[1] <= a[1] + 1 and e[2] <= a[2] + 1e-9
        ok3 &= good
        md.append(f"| {sc} | {cell(r['CLEAR'])} | {cell(r['A'])} | {cell(r['E'])} | {'pass' if good else 'FAIL'} |")
    verdict["3"] = ok3
    md += ["", f"-> **{'pass' if ok3 else 'FAIL'}**", "", "Report only, the other synthetic DTD rates:", "",
           "| setting | CLEAR-FPL | A | E |", "|---|---|---|---|"]
    for sc in ("sym50", "pair50", "sym75", "pair75"):
        r = run_full(syn[sc], ["CLEAR", "A", "E"], all_flagged=True)
        md.append(f"| {sc} | {cell(r['CLEAR'])} | {cell(r['A'])} | {cell(r['E'])} |")
    md.append("")

    md += ["## Check 4: high noise, referee trained on the noisy labels (PromptFL N_*_diag, T = 1, every client flagged)", "",
           "| dataset | setting | client-rounds | CLEAR-FPL | E | oracle budget (report) | E noise <= CLEAR + 1, touched <= CLEAR + 5 |",
           "|---|---|---|---|---|---|---|"]
    ok4 = True
    for ds, sc, decides in (("dtd", "sym75", True), ("dtd", "pair75", True), ("oxford_pets", "sym75", True),
                            ("oxford_pets", "pair75", True), ("dtd", "pair50", False), ("oxford_pets", "pair50", False)):
        cl = load_diag(ds, sc)
        if not cl:
            md.append(f"| {NAMES[ds]} | N {sc} | 0 | — | — | — | missing |")
            ok4 = ok4 and not decides
            continue
        r, m = run_diag(cl, K[ds])
        c, e = pct(r["CLEAR"]), pct(r["E"])
        good = e[2] <= c[2] + 1 and e[1] <= c[1] + 5
        if decides:
            ok4 &= good
        md.append(f"| {NAMES[ds]} | N {sc} | {m} | {cell(r['CLEAR'])} | {cell(r['E'])} | {cell(r['oracle'])} | "
                  f"{('pass' if good else 'FAIL') if decides else 'report'} |")
    md += ["", f"-> **{'pass' if ok4 else 'FAIL'}**", ""]
    verdict["4"] = ok4

    md += ["## Report only: real S-setting noise (stage-0, all clients, CLEAR flag decides)", "",
           "| dataset | setting | CLEAR-FPL | A | E |", "|---|---|---|---|---|"]
    for ds, rs in full.items():
        for sc, r in rs.items():
            md.append(f"| {NAMES[ds]} | {sc} | {cell(r['CLEAR'])} | {cell(r['A'])} | {cell(r['E'])} |")
    go = all(verdict.values())
    md += ["", "## Verdict", "", " | ".join(f"check {a}: {'pass' if b else 'FAIL'}" for a, b in verdict.items()), "",
           f"**Budget repair: {'GO' if go else 'NO GO'}**", ""]
    text = "\n".join(md)
    open(OUT, "w", encoding="utf-8").write(text)
    print(text)


if __name__ == "__main__":
    main()
