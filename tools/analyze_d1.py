"""Gate D stage 1: which client-level score names the careless clients best?

Reads the D_<scenario>_<arm> runs (diagnostic scores logged every round, flcore/diag.py) and
applies the selection rule fixed in results/side-research/gate_D/gate_d1_plan.md:

  - per round (10-49) and seed, AUROC of each candidate score at separating the clients whose
    labels are damaged from the rest, in the `none` arm of the four noisy scenarios;
  - an absolute threshold per score, set at the 95th percentile of the honest client-rounds of
    the all-clean federation (D_clean_none), and the recall / false-flag rate it gives in the
    noisy scenarios;
  - on `het`, the Spearman correlation between the score and each client's true noise rate;
  - the winner is the primary candidate with the highest mean AUROC over the four noisy
    scenarios; ties within 0.01 go to the lower false-flag rate.

Exploratory (not part of the rule): the same for every logged score, the `dbr` and `mae` arms,
and per-image AUROC of the sample-level rankings from diag_samples_seed_*.json.

Usage: python tools/analyze_d1.py <results root> [--dataset oxford_pets] [--out <dir>]
"""
import argparse
import glob
import json
import os
import re
import statistics as st

SCEN_NOISY = ["sym", "pair", "inst", "het"]
ARMS = ["none", "dbr", "mae"]
ROUNDS = range(10, 50)
# primary candidates, fixed before the run: (name, getter)
PRIMARY = [
    ("d (old, global)", ("g", "dis")),
    ("d_far (gate V)", ("g", "dis_far")),
    ("loss, global", ("g", "nll")),
    ("loss, local", ("l", "nll")),
    ("LID, local (FedCorr)", ("lid_l", None)),
    ("surprise, global", ("g", "xs")),
    ("surprise, global+CLIP", ("e", "xs")),
    ("surprise, global+CLIP, merged", ("e", "xs_m")),
    ("excess prob, global+CLIP", ("e", "xp")),
    ("share xp>0.5, global+CLIP", ("e", "f50")),
]
ROUND_RE = re.compile(r"round (\d+), train loss: .*?top1: ([\d.]+)%")


def all_getters(rec):
    out = []
    for p in ("g", "z", "e", "l"):
        for m in sorted(rec.get(p, {}) or {}):
            out.append((f"{p}.{m}", (p, m)))
    for k in ("lid_g", "lid_l"):
        if k in rec:
            out.append((k, (k, None)))
    return out


def get(rec, g):
    p, m = g
    v = rec.get(p)
    if m is None:
        return v
    return None if v is None else v.get(m)


def auroc(pos, neg):
    if not pos or not neg:
        return None
    tot = 0.0
    for a in pos:
        for b in neg:
            tot += 1.0 if a > b else 0.5 if a == b else 0.0
    return tot / (len(pos) * len(neg))


def spearman(x, y):
    def rank(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
                j += 1
            for k in range(i, j + 1):
                r[order[k]] = (i + j) / 2.0
            i = j + 1
        return r
    rx, ry = rank(x), rank(y)
    mx, my = st.fmean(rx), st.fmean(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = (sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry)) ** 0.5
    return num / den if den else None


def load(root, ds, scen, arm):
    """[(seed, diag records)] for one run."""
    out = []
    pat = os.path.join(root, "**", "runs", f"{ds}_D_{scen}_{arm}", "**", "noise_seed_*.json")
    for p in sorted(glob.glob(pat, recursive=True)):
        s = int(re.search(r"noise_seed_(\d+)", p).group(1))
        out.append((s, json.load(open(p))["diag"]))
    return out


def last10(root, ds, scen, arm):
    logs = glob.glob(os.path.join(root, "**", "logs", f"{ds}_D_{scen}_{arm}.txt"), recursive=True)
    if not logs:
        return None
    seeds, cur = [], None
    for line in open(logs[0], encoding="utf-8", errors="replace"):
        m = ROUND_RE.search(line)
        if m:
            if int(m.group(1)) == 0:
                cur = []
                seeds.append(cur)
            cur.append(float(m.group(2)))
    vals = [st.fmean(s[-10:]) for s in seeds if len(s) >= 10]
    return (st.fmean(vals), st.stdev(vals) if len(vals) > 1 else 0.0, len(vals)) if vals else None


def client_rounds(runs, getter):
    """[(seed, round, [(score, noise rate)])] over rounds 10-49."""
    rows = []
    for s, recs in runs:
        for r in recs:
            if r["round"] not in ROUNDS:
                continue
            pts = [(get(v, getter), v["noise"]) for v in r["clients"].values()]
            pts = [(a, b) for a, b in pts if a is not None]
            rows.append((s, r["round"], pts))
    return rows


def evaluate(root, ds, arm, getters):
    clean = load(root, ds, "clean", arm if arm != "mae" else "none")
    res = {}
    for name, g in getters:
        hon = [a for _, _, pts in client_rounds(clean, g) for a, _ in pts]
        thr = sorted(hon)[int(0.95 * (len(hon) - 1))] if hon else None
        row = {"thr": thr}
        aucs = []
        for sc in SCEN_NOISY:
            runs = load(root, ds, sc, arm)
            cr = client_rounds(runs, g)
            per = [auroc([a for a, n in pts if n > 0], [a for a, n in pts if n == 0]) for _, _, pts in cr]
            per = [x for x in per if x is not None]
            auc = st.fmean(per) if per else None
            row[sc] = {"auc": auc}
            if auc is not None:
                aucs.append(auc)
            if thr is not None and cr:
                pos = [a for _, _, pts in cr for a, n in pts if n > 0]
                neg = [a for _, _, pts in cr for a, n in pts if n == 0]
                row[sc]["recall"] = sum(a > thr for a in pos) / max(len(pos), 1)
                row[sc]["false"] = sum(a > thr for a in neg) / max(len(neg), 1)
            if sc == "het":
                rho = [spearman([a for a, _ in pts], [n for _, n in pts]) for _, _, pts in cr]
                rho = [x for x in rho if x is not None]
                row[sc]["spearman"] = st.fmean(rho) if rho else None
        row["mean_auc"] = st.fmean(aucs) if len(aucs) == len(SCEN_NOISY) else None
        row["mean_false"] = (st.fmean(row[sc]["false"] for sc in SCEN_NOISY if "false" in row[sc])
                             if all("false" in row[sc] for sc in SCEN_NOISY) else None)
        res[name] = row
    return res


def sample_level(root, ds, arm):
    """Per-image AUROC inside the careless clients, rounds 10-45 (exploratory, for H5)."""
    cols = ["label", "true"] + [f"{d}_{c}" for d in ("g", "z", "e")
                                for c in ("py", "pred", "pmax", "H", "sumsq", "pnn")]
    ix = {c: i for i, c in enumerate(cols)}
    rankers = {
        "1 - P_global(label)": lambda r: 1 - r[ix["g_py"]],
        "excess prob, global": lambda r: r[ix["g_sumsq"]] - r[ix["g_py"]],
        "1 - P_mix(label)": lambda r: 1 - r[ix["e_py"]],
        "excess prob, global+CLIP": lambda r: r[ix["e_sumsq"]] - r[ix["e_py"]],
        "excess prob, global+CLIP, merged": lambda r: r[ix["e_sumsq"]] - r[ix["e_py"]] - r[ix["e_pnn"]],
    }
    out = {}
    for sc in SCEN_NOISY:
        files = glob.glob(os.path.join(root, "**", "runs", f"{ds}_D_{sc}_{arm}", "**",
                                       "diag_samples_seed_*.json"), recursive=True)
        recs = [x for f in files for x in json.load(open(f)) if x["round"] in ROUNDS]
        out[sc] = {}
        for name, fn in rankers.items():
            aucs = []
            for x in recs:
                rows = [r for r in x["rows"] if None not in (r[ix["e_py"]], r[ix["e_pnn"]])]
                pos = [fn(r) for r in rows if r[0] != r[1]]
                neg = [fn(r) for r in rows if r[0] == r[1]]
                a = auroc(pos, neg)
                if a is not None:
                    aucs.append(a)
            out[sc][name] = st.fmean(aucs) if aucs else None
    return out


def fmt(v, p=3):
    return "—" if v is None else f"{v:.{p}f}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("--dataset", default="oxford_pets")
    ap.add_argument("--out", default=None)
    ap.add_argument("--rounds", nargs=2, type=int, default=None,
                    help="override the 10-49 window (CPU smoke runs only)")
    a = ap.parse_args()
    global ROUNDS
    if a.rounds:
        ROUNDS = range(a.rounds[0], a.rounds[1] + 1)
    ds = a.dataset
    md = [f"# Gate D stage 1 analysis: {ds}", "",
          "Generated by `tools/analyze_d1.py`. Rounds 10-49, 5 seeds. AUROC: careless vs other "
          "clients, per round, averaged. Threshold: 95th percentile of honest client-rounds in "
          "`D_clean_none`; recall / false = share of careless / honest client-rounds above it.", ""]

    md += ["## Accuracy (last10)", "", "| scenario | none | mae | dbr |", "|---|---|---|---|"]
    for sc in SCEN_NOISY + ["clean"]:
        cells = []
        for arm in ("none", "mae", "dbr"):
            v = last10(a.root, ds, sc, arm)
            cells.append("—" if v is None else f"{v[0]:.2f} ± {v[1]:.2f} (n={v[2]})")
        md.append(f"| {sc} | " + " | ".join(cells) + " |")
    md.append("")

    winner = None
    for arm in ARMS:
        if not any(load(a.root, ds, sc, arm) for sc in SCEN_NOISY):
            continue
        sample_rec = next((recs[0]["clients"] for sc in SCEN_NOISY
                           for _, recs in load(a.root, ds, sc, arm) if recs), None)
        getters = PRIMARY + ([g for g in all_getters(next(iter(sample_rec.values())))
                              if g[1] not in [p[1] for p in PRIMARY]] if sample_rec else [])
        res = evaluate(a.root, ds, arm, getters)
        title = "primary rule" if arm == "none" else "exploratory"
        md += [f"## Client-level scores, `{arm}` arm ({title})", "",
               "| score | sym AUC | pair AUC | inst AUC | het AUC | mean AUC | het Spearman | "
               "recall sym/pair/inst/het | false sym/pair/inst/het |",
               "|---|---|---|---|---|---|---|---|---|"]
        for i, (name, _) in enumerate(getters):
            r = res[name]
            rec = "/".join(fmt(r[sc].get("recall"), 2) for sc in SCEN_NOISY)
            fal = "/".join(fmt(r[sc].get("false"), 2) for sc in SCEN_NOISY)
            tag = "" if i < len(PRIMARY) else " *(expl.)*"
            md.append(f"| {name}{tag} | " + " | ".join(fmt(r[sc]["auc"]) for sc in SCEN_NOISY)
                      + f" | **{fmt(r['mean_auc'])}** | {fmt(r['het'].get('spearman'))} | {rec} | {fal} |")
        md.append("")
        if arm == "none":
            cand = [(n, res[n]) for n, _ in PRIMARY if res[n]["mean_auc"] is not None]
            if cand:
                best = max(c[1]["mean_auc"] for c in cand)
                tied = [c for c in cand if c[1]["mean_auc"] >= best - 0.01]
                winner = min(tied, key=lambda c: (c[1]["mean_false"] if c[1]["mean_false"] is not None
                                                  else 1.0, -c[1]["mean_auc"]))[0]
        sl = sample_level(a.root, ds, arm)
        md += [f"### Image-level rankings inside careless clients, `{arm}` (exploratory)", "",
               "| ranking | " + " | ".join(SCEN_NOISY) + " |", "|---|" + "---|" * len(SCEN_NOISY)]
        for name in next(iter(sl.values())):
            md.append(f"| {name} | " + " | ".join(fmt(sl[sc][name]) for sc in SCEN_NOISY) + " |")
        md.append("")
    md += ["## Selection rule", "", f"Winner (primary candidates, `none` arm): **{winner}**", ""]
    text = "\n".join(md) + "\n"
    if a.out:
        os.makedirs(a.out, exist_ok=True)
        open(os.path.join(a.out, f"d1_{ds}.md"), "w", encoding="utf-8").write(text)
    print(text)


if __name__ == "__main__":
    main()
