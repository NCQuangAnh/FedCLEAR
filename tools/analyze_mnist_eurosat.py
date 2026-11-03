"""MNIST + EuroSAT study: rules R1-R4 of results/side-research/mnist_eurosat/plan.md, the reported
side numbers, and Step 1 of the CLIP-dependence diagnosis (where CLEAR's referee goes wrong).

Accuracy: last10, 5 seeds, paired over seeds (same reader as analyze_baselines.py). Pets / DTD /
Caltech101 come from the earlier 10-client runs under results/side-research, for comparison.
Zero-shot CLIP except MNIST comes from earlier single runs (see OLD_ZS).

Diagnosis, from the `sure` records of the CLEAR runs (rounds 1-50, every client every round):
- false flags: share of (honest client, round) pairs that CLEAR flags
- hits: share of (noisy client, round) pairs that CLEAR flags
- suspect precision: suspects whose label really is wrong / suspects
- clean images touched: suspects whose label is right / right-labelled images of flagged clients
- relabel precision: relabels that restore the true label / relabels; broken: right label made wrong

Usage: python tools/analyze_mnist_eurosat.py  (writes results/side-research/mnist_eurosat/results.md)
"""
import json
import os
import statistics as st

from analyze_baselines import SR, last10, paired
from analyze_client_estimates import auroc, files

OUT = os.path.join(SR, "mnist_eurosat", "results.md")
NEW = [("mnist", "MNIST"), ("eurosat", "EuroSAT")]
OLD = [("oxford_pets", "Pets"), ("dtd", "DTD"), ("caltech101", "Caltech101")]
MIXED = ["sym", "pair", "inst", "het"]
NOISY = [("S", s) for s in MIXED] + [("N", f"{n}{r}") for n in ("sym", "pair") for r in ("25", "50", "75")]
ALL = NOISY[:4] + [("S", "clean")] + NOISY[4:]
# zero-shot CLIP RN50 from earlier single runs (no training, so the seed does not matter):
# results/Phase1/3datasets/extracted/logs/<ds>_ZSCLIP.txt and results/Phase4/food101-eurosat
OLD_ZS = {"oxford_pets": 85.69, "dtd": 41.78, "caltech101": 85.76, "eurosat": 26.11}


def tags(ds, kind, sc):
    if kind == "S":
        return f"{ds}_S_{sc}_full", f"{ds}_D_{sc}_none"
    return f"{ds}_N_{sc}_clear", f"{ds}_N_{sc}_none"


def zero_shot(ds):
    if ds in OLD_ZS:
        return OLD_ZS[ds]
    v = last10(f"{ds}_S_clean_zs")
    return st.fmean(v) if v else None


def m(v):
    return st.fmean(v) if v else None


def f2(x, sign=False):
    return "—" if x is None else (f"{x:+.2f}" if sign else f"{x:.2f}")


def accuracy(ds):
    rows = {}
    for kind, sc in ALL:
        c, p = (last10(t) for t in tags(ds, kind, sc))
        rows[(kind, sc)] = (c, p, paired(c, p))
    return rows


def sure_records(tag):
    out = []
    for f in files(tag):
        rec = json.load(open(f, encoding="utf-8"))
        if rec.get("sure"):
            out.append(rec)
    return out


def diagnose(ds, group, arm="full"):
    """Pooled CLEAR referee counts over the settings of a group and all seeds. arm: the S_ method
    tag (full, or a diagnostic switch: noclip / nomerge); N_ settings always read the CLEAR runs."""
    c = dict.fromkeys(["hon", "hon_flag", "noi", "noi_flag", "sus", "sus_noisy", "clean_flagged",
                       "relab", "fixed", "broken", "drop", "drop_noisy"], 0)
    au_first, au_last = [], []
    for kind, sc in group:
        tag = f"{ds}_S_{sc}_{arm}" if kind == "S" else tags(ds, kind, sc)[0]
        for rec in sure_records(tag):
            rs = rec["sure"]
            for r in rs[1:]:
                for v in r["clients"].values():
                    n = v.get("n") or 0
                    if not n:
                        continue
                    honest = v["noise"] == 0
                    c["hon" if honest else "noi"] += 1
                    if v["flag"]:
                        c["hon_flag" if honest else "noi_flag"] += 1
                        c["clean_flagged"] += n - round(v["noise"] * n)
                    c["sus"] += v["suspects"]
                    c["sus_noisy"] += v["suspects_noisy"]
                    c["relab"] += v["relabeled"]
                    c["fixed"] += v["fixed"]
                    c["broken"] += v["broken"]
                    c["drop"] += v["dropped"]
                    c["drop_noisy"] += v["dropped_noisy"]
            if kind == "S" and sc in MIXED:
                true0 = {str(x["id"]): x["realized_rate"] for x in rec["noise"]["clients"]}
                for r, acc in ((rs[0], au_first), (rs[-1], au_last)):
                    d = {k: (v["score"], true0[k]) for k, v in r["clients"].items()
                         if v.get("n") and v["score"] is not None}
                    a = auroc([s for s, t in d.values() if t > 0], [s for s, t in d.values() if t == 0])
                    if a is not None:
                        acc.append(a)
    return c, m(au_first), m(au_last)


def pct(a, b):
    return "—" if not b else f"{100 * a / b:.0f}%"


SWITCHES = ["noclip", "nomerge"]


def switches():
    """Diagnostic follow-up of plan.md: which CLIP use shrinks the client score (rules C1, C2).
    Pets / DTD / Caltech101 noclip are the gate D2 runs, shown as the natural-image reference."""
    mixed = [("S", s) for s in MIXED]
    md = ["## Diagnostic follow-up: switch off one CLIP use (4 mixed settings)", "",
          "`noclip`: referee without zero-shot CLIP. `nomerge`: score without the look-alike merge. "
          "Both tau 0.072. Flag rates and precision pooled over rounds 1-50 and 5 seeds; accuracy is "
          "the mean of the 4 settings, differences are the mean of the 4 paired differences.", "",
          "| dataset | variant | acc | − full | − PromptFL | honest flagged | noisy flagged | "
          "relabel precision | relabels breaking | AUROC first / last | noisy score r50 |",
          "|---|---|---|---|---|---|---|---|---|---|---|"]
    verdict = {}
    for ds, name in NEW + OLD:
        base = None
        for arm in ["full"] + SWITCHES:
            acc_arm = {sc: last10(f"{ds}_S_{sc}_{arm}") for sc in MIXED}
            if not all(acc_arm.values()):
                continue
            full = {sc: last10(f"{ds}_S_{sc}_full") for sc in MIXED}
            pfl = {sc: last10(f"{ds}_D_{sc}_none") for sc in MIXED}
            d_full = [paired(acc_arm[sc], full[sc]) for sc in MIXED]
            d_pfl = [paired(acc_arm[sc], pfl[sc]) for sc in MIXED]
            c, a1, a2 = diagnose(ds, mixed, arm)
            noisy_r50 = [v["score"] for sc in MIXED for rec in sure_records(f"{ds}_S_{sc}_{arm}")
                         for v in rec["sure"][50]["clients"].values()
                         if v.get("n") and v["score"] is not None and v["noise"] > 0]
            hon = 100 * c["hon_flag"] / c["hon"] if c["hon"] else None
            noi = 100 * c["noi_flag"] / c["noi"] if c["noi"] else None
            gain = m([d[0] for d in d_full if d]) if arm != "full" else None
            if arm == "full":
                base = noi
            elif ds in dict(NEW):
                verdict[(name, arm)] = (noi, base, hon, gain, d_full)
            md.append(
                f"| {name} | {arm} | {f2(m([m(v) for v in acc_arm.values()]))} | "
                f"{'—' if arm == 'full' else f2(gain, True)} | {f2(m([d[0] for d in d_pfl if d]), True)} | "
                f"{pct(c['hon_flag'], c['hon'])} | {pct(c['noi_flag'], c['noi'])} | "
                f"{pct(c['fixed'], c['relab'])} | {pct(c['broken'], c['relab'])} | {f2(a1)} / {f2(a2)} | "
                f"{f'{st.median(noisy_r50):+.2f}' if noisy_r50 else '—'} |")
    md += ["", "### Rules C1 / C2 (plan.md, Diagnostic follow-up)", ""]
    for (name, arm), (noi, base, hon, gain, d_full) in verdict.items():
        c1 = noi is not None and base is not None and noi - base >= 20 and hon is not None and hon <= 10
        c2 = gain is not None and gain > 0
        per = ", ".join(f"{sc} {d[0]:+.2f} (p={d[1]:.3f})" for sc, d in zip(MIXED, d_full) if d)
        md += [f"- {name} {arm}: noisy flagged {f2(base)}% -> {f2(noi)}% ({f2(None if noi is None or base is None else noi - base, True)} points), "
               f"honest flagged {f2(hon)}% -> C1 **{'PASS' if c1 else 'FAIL'}**; "
               f"switch − full {f2(gain, True)} [{per}] -> C2 **{'PASS' if c2 else 'FAIL'}**"]
    md.append("")
    return md


def main():
    md = ["# MNIST + EuroSAT: results", "",
          "Generated by `tools/analyze_mnist_eurosat.py`. Rules are in `plan.md` (fixed before the runs). "
          "last10, mean over 5 seeds; differences paired over seeds: mean (p, seeds won / 5).", ""]
    acc = {ds: accuracy(ds) for ds, _ in NEW + OLD}

    # accuracy tables for the two new datasets
    for ds, name in NEW:
        zs = zero_shot(ds)
        md += [f"## {name} (zero-shot CLIP {f2(zs)})", "",
               "| setting | PromptFL | CLEAR-FPL | CLEAR − PromptFL |", "|---|---|---|---|"]
        for kind, sc in ALL:
            c, p, d = acc[ds][(kind, sc)]
            dd = "—" if d is None else f"{d[0]:+.2f} (p={d[1]:.3f}, {d[2]}/{d[3]})"
            md.append(f"| {kind} {sc} | {f2(m(p))} | {f2(m(c))} | {dd} |")
        md.append("")

    # rules
    md += ["## Rules (plan.md)", ""]
    for ds, name in NEW:
        rows = acc[ds]
        diffs = [rows[s][2] for s in NOISY if rows[s][2]]
        mean_gain = m([d[0] for d in diffs])
        wins = sum(d[0] > 0 and d[1] < 0.05 for d in diffs)
        losses = sum(d[0] < 0 and d[1] < 0.05 for d in diffs)
        r1 = mean_gain is not None and mean_gain > 0 and wins >= 5
        cl = rows[("S", "clean")][2]
        r2 = cl is not None and cl[0] >= -1
        _, au_first, au_last = diagnose(ds, [("S", s) for s in MIXED])
        r3 = au_first is not None and au_first >= 0.90
        zs, pc = zero_shot(ds), m(rows[("S", "clean")][1])
        r4 = zs is not None and pc is not None and pc - zs >= 10
        md += [f"### {name}",
               f"- R1 gain kept: mean gain over 10 noisy settings {f2(mean_gain, True)}, significant wins "
               f"{wins}/10 (significant losses {losses}/10) -> **{'PASS' if r1 else 'FAIL'}**",
               f"- R2 clean not hurt: CLEAR − PromptFL on S clean {f2(cl and cl[0], True)} -> "
               f"**{'PASS' if r2 else 'FAIL'}**",
               f"- R3 client detection: AUROC first round {f2(au_first)} (last round {f2(au_last)}) -> "
               f"**{'PASS' if r3 else 'FAIL'}**",
               f"- R4 training needed: PromptFL clean {f2(pc)} − zero-shot {f2(zs)} = "
               f"{f2(None if pc is None or zs is None else pc - zs, True)} -> **{'PASS' if r4 else 'FAIL'}**",
               ""]

    # reported numbers next to the old datasets
    md += ["## Reported next to Pets / DTD / Caltech101", "",
           "| dataset | zero-shot | PromptFL clean | PromptFL drop, mean of 10 noisy | CLEAR gain, mean of 10 noisy | "
           "CLEAR − PromptFL on clean |", "|---|---|---|---|---|---|"]
    for ds, name in NEW + OLD:
        rows = acc[ds]
        pc = m(rows[("S", "clean")][1])
        drops = [pc - m(rows[s][1]) for s in NOISY if rows[s][1]] if pc is not None else []
        gains = [rows[s][2][0] for s in NOISY if rows[s][2]]
        cl = rows[("S", "clean")][2]
        md.append(f"| {name} | {f2(zero_shot(ds))} | {f2(pc)} | {f2(m(drops))} ({len(drops)}) | "
                  f"{f2(m(gains), True)} ({len(gains)}) | {f2(cl and cl[0], True)} |")
    md += ["", "Per setting, PromptFL drop from its clean accuracy:", "",
           "| setting | " + " | ".join(n for _, n in NEW + OLD) + " |", "|---|" + "---|" * 5]
    for s in NOISY:
        cells = []
        for ds, _ in NEW + OLD:
            pc, pn = m(acc[ds][("S", "clean")][1]), m(acc[ds][s][1])
            cells.append(f2(None if pc is None or pn is None else pc - pn))
        md.append(f"| {s[0]} {s[1]} | " + " | ".join(cells) + " |")
    md.append("")

    # diagnosis
    groups = [("mixed (S sym/pair/inst/het)", [("S", s) for s in MIXED]),
              ("clean (S clean)", [("S", "clean")]),
              ("all noisy (N, 6 settings)", NOISY[4:])]
    md += ["## Step 1: where does CLEAR's referee go wrong?", "",
           "Pooled over settings, seeds and rounds 1-50. See the docstring for each count.", ""]
    for gname, group in groups:
        md += [f"### {gname}", "", "| | " + " | ".join(n for _, n in NEW + OLD) + " |",
               "|---|" + "---|" * 5]
        cs = [diagnose(ds, group)[0] for ds, _ in NEW + OLD]
        lines = [
            ("honest clients flagged", lambda c: pct(c["hon_flag"], c["hon"])),
            ("noisy clients flagged", lambda c: pct(c["noi_flag"], c["noi"])),
            ("suspect precision", lambda c: pct(c["sus_noisy"], c["sus"])),
            ("clean images touched in flagged clients",
             lambda c: pct(c["sus"] - c["sus_noisy"], c["clean_flagged"])),
            ("relabel precision", lambda c: pct(c["fixed"], c["relab"])),
            ("relabels that break a right label", lambda c: pct(c["broken"], c["relab"])),
            ("suspects relabelled (rest dropped)", lambda c: pct(c["relab"], c["sus"])),
            ("dropped images really wrong", lambda c: pct(c["drop_noisy"], c["drop"])),
        ]
        for lab, fn in lines:
            md.append(f"| {lab} | " + " | ".join(fn(c) for c in cs) + " |")
        md.append("")

    # the client score against the fixed flag threshold tau = 0.05
    md += ["### Client score, median (mixed settings, 5 seeds); CLEAR flags a client when score > 0.05", "",
           "| round, clients | " + " | ".join(n for _, n in NEW + OLD) + " |", "|---|" + "---|" * 5]
    med = {}
    for ds, _ in NEW + OLD:
        for sc in MIXED:
            for rec in sure_records(f"{ds}_S_{sc}_full"):
                for rnd in (1, 25, 50):
                    for v in rec["sure"][rnd]["clients"].values():
                        if v.get("n") and v["score"] is not None:
                            key = (ds, rnd, "noisy" if v["noise"] > 0 else "honest")
                            med.setdefault(key, []).append(v["score"])
    for rnd in (1, 25, 50):
        for who in ("honest", "noisy"):
            md.append(f"| {rnd}, {who} | " + " | ".join(
                f"{st.median(med[(ds, rnd, who)]):+.2f}" if med.get((ds, rnd, who)) else "—"
                for ds, _ in NEW + OLD) + " |")
    md.append("")
    md += switches()
    text = "\n".join(md) + "\n"
    open(OUT, "w", encoding="utf-8").write(text)
    print(text)


if __name__ == "__main__":
    main()
