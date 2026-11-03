"""Gate with a capped temperature (arm `gatec`): rules of results/side-research/calrepair/gatec_plan.md.

Written with the plan, before any gatec run. Differences are gatec - CLEAR-FPL, last10, paired by seed.
Stage 1 (seeds 0-4) applies the gate plan's C1-C3. A setting whose gate run never broadcast T > 1 is
the gate run itself (gatec would take the same decision every round); a setting the gate plan does
not run is CLEAR-FPL by construction (difference 0). Stage 2 (held-out seeds 5-7, arms gatech / clearh):
  H1  Pets / DTD / Caltech101 W settings: no seed pair at -5 or worse
  H2  same 24 seed pairs: mean >= +1.0
  H3  MNIST / EuroSAT N sym75 and N pair75: mean over the 12 seed pairs >= -1.0
Adopt if C1-C3 and H1-H3.

Usage: python tools/analyze_gatec.py   (writes results/side-research/calrepair/gatec_results.md)
"""
import json
import os
import re
import statistics as st

from analyze_baselines import SR, last10, paired
from analyze_calrepair import DATASETS, SETTINGS, fd, tag
from analyze_client_estimates import files
from analyze_gate import NOT_RUN, W, sig_better, sig_worse, yes

OUT = os.path.join(SR, "calrepair", "gatec_results.md")
NAME = dict(DATASETS)
HELD = [(d, ("N", x)) for d, _ in DATASETS for x in ("sym75", "pair75")] + \
       [("dtd", ("N", "sym25")), ("dtd", ("N", "pair25"))]
HELD_W = [x for x in HELD if x in W]
HELD_ME = [x for x in HELD if x[0] in ("mnist", "eurosat")]


def records(t):
    """The `sure` records of a run, ordered by seed."""
    fs = sorted(files(t), key=lambda f: int(re.search(r"noise_seed_(\d+)", f).group(1)))
    return [json.load(open(f, encoding="utf-8")).get("sure") or [] for f in fs]


def softened(ds, k):
    """True if some seed of the gate run broadcast T > 1; None if the gate run is missing."""
    recs = records(tag(ds, *k, "gate"))
    if not recs:
        return None
    return any(c.get("T") is not None and c["T"] > 1 + 1e-9
               for rec in recs for r in rec for c in r["clients"].values())


def source(ds, k):
    """Which run stands for gatec in stage 1: 'clear', 'gate', 'gatec' or None (missing)."""
    if (ds, k) in NOT_RUN:
        return "clear"
    s = softened(ds, k)
    if s is False and last10(tag(ds, *k, "gate")):
        return "gate"
    return "gatec" if last10(tag(ds, *k, "gatec")) else None


def result(ds, k):
    src = source(ds, k)
    if src == "clear":
        return (0.0, None, 0, 5)
    return None if src is None else paired(last10(tag(ds, *k, src)), last10(tag(ds, *k, "clear")))


def switch_T(t):
    """Per seed: (broadcast T, fitted T) at the first calibrated round, or None (gate off)."""
    out = []
    for rec in records(t):
        r = next((r for r in rec if any("T" in c for c in r["clients"].values())), None)
        c = None if r is None else next(c for c in r["clients"].values() if "T" in c)
        out.append(None if c is None else (c["T"], c.get("T_fit", c["T"])))
    return out


def kept(rec, start=6):
    """Mean share of wrong labels left in training (rounds >= start), from the ground-truth audit."""
    vals = []
    for r in rec:
        if r["round"] < start:
            continue
        n = drp = wrong = drpn = fix = brk = 0
        for c in r["clients"].values():
            n += c["n"]; drp += c["dropped"]; wrong += round(c["n"] * c["noise"])
            drpn += c["dropped_noisy"]; fix += c["fixed"]; brk += c["broken"]
        vals.append((wrong - drpn - fix + brk) / max(1, n - drp))
    return None if not vals else st.fmean(vals)


def seed_line(t_arm, t_clear):
    a, c = records(t_arm), records(t_clear)
    ts = switch_T(t_arm)
    parts = []
    for i, rec in enumerate(a):
        x = ts[i] if i < len(ts) else None
        ka, kc = kept(rec), (kept(c[i]) if i < len(c) else None)
        parts.append(("off" if x is None else f"T {x[0]:.2f}/{x[1]:.2f}") +
                     ("" if ka is None or kc is None else f", kept {ka:.2f} vs {kc:.2f}"))
    return "; ".join(parts) or "—"


def stage1(md):
    res = {(ds, k): result(ds, k) for ds, _ in DATASETS for k in SETTINGS}
    md += ["## Stage 1: seeds 0-4 (development; rules C1-C3 of gate_confirm_plan.md)", ""]
    for ds, dn in DATASETS:
        md += [f"### {dn}", "", "| setting | run used | CLEAR-FPL | gatec | gatec − CLEAR | per seed: T broadcast/fitted at switch, wrong labels kept vs CLEAR |",
               "|---|---|---|---|---|---|"]
        for k in SETTINGS:
            src = source(ds, k)
            c = last10(tag(ds, *k, "clear"))
            g = None if src in (None, "clear") else last10(tag(ds, *k, src))
            r = res[(ds, k)]
            md.append(f"| {' '.join(k)}{' (W)' if (ds, k) in W else ''} | {src or 'MISSING'} | "
                      f"{'—' if not c else f'{st.fmean(c):.2f}'} | {'—' if not g else f'{st.fmean(g):.2f}'} | "
                      f"{'= CLEAR' if src == 'clear' else fd(r)} | "
                      f"{'—' if src in (None, 'clear') else seed_line(tag(ds, *k, src), tag(ds, *k, 'clear'))} |")
        md.append("")
    missing = [x for x, r in res.items() if r is None]
    w = [res[x] for x in W]
    c1 = None if any(r is None for r in w) else (
        st.fmean(r[0] for r in w) >= 2.0 and sum(sig_better(r) for r in w) >= 4)
    means, c2 = {}, None if missing else True
    for ds, dn in DATASETS:
        rs = [res[(ds, k)] for k in SETTINGS if (ds, k) not in W]
        means[dn] = None if any(r is None for r in rs) else st.fmean(r[0] for r in rs)
        if means[dn] is not None and means[dn] < -0.3:
            c2 = False
    bad = [x for x, r in res.items() if sig_worse(r)]
    if bad and c2 is not None:
        c2 = False
    c3, clean = True, {}
    for ds, dn in DATASETS:
        src = source(ds, ("S", "clean"))
        arm = "clear" if src == "clear" else src
        r = None if arm is None else paired(last10(tag(ds, "S", "clean", arm)), last10(f"{ds}_D_clean_none"))
        clean[dn] = r
        if r is None:
            c3 = None if c3 is not False else c3
        elif r[0] < -1.0:
            c3 = False
    md += ["### Stage 1 rules", "",
           f"- C1: over W mean {'—' if any(r is None for r in w) else f'{st.fmean(r[0] for r in w):+.2f}'} "
           f"(>= +2.0), significantly better {sum(sig_better(r) for r in w if r)}/8 (>= 4) -> {yes(c1)}",
           "- C2: means outside W " + ", ".join(f"{d} {'—' if m is None else f'{m:+.2f}'}" for d, m in means.items())
           + " (>= −0.3); significantly worse by > 1: "
           + (", ".join(f"{NAME[d]} {' '.join(k)} {res[(d, k)][0]:+.2f}" for d, k in bad) or "none") + f" -> {yes(c2)}",
           "- C3: S clean − PromptFL " + ", ".join(f"{d} {fd(r)}" for d, r in clean.items()) + f" (>= −1) -> {yes(c3)}",
           f"- missing: {len(missing)}" + ("" if not missing else " (" + ", ".join(
               f"{NAME[d]} {' '.join(k)}" for d, k in missing) + ")"), ""]
    return None if None in (c1, c2, c3) else (c1 and c2 and c3)


def pairs(ds, k):
    a, b = last10(tag(ds, *k, "gatech")), last10(tag(ds, *k, "clearh"))
    return None if not a or not b or len(a) != len(b) else [x - y for x, y in zip(a, b)]


def stage2(md):
    md += ["## Stage 2: held-out seeds 5-7", "",
           "| dataset | setting | CLEAR-FPL | gatec | per seed gatec − CLEAR | per seed: T at switch, kept vs CLEAR |",
           "|---|---|---|---|---|---|"]
    d = {}
    for ds, k in HELD:
        d[(ds, k)] = pairs(ds, k)
        a, b = last10(tag(ds, *k, "gatech")), last10(tag(ds, *k, "clearh"))
        md.append(f"| {NAME[ds]} | {' '.join(k)}{' (W)' if (ds, k) in W else ''} | "
                  f"{'—' if not b else f'{st.fmean(b):.2f}'} | {'—' if not a else f'{st.fmean(a):.2f}'} | "
                  f"{'—' if d[(ds, k)] is None else ' '.join(f'{x:+.1f}' for x in d[(ds, k)])} | "
                  f"{'—' if not a else seed_line(tag(ds, *k, 'gatech'), tag(ds, *k, 'clearh'))} |")
    w = None if any(d[x] is None for x in HELD_W) else [v for x in HELD_W for v in d[x]]
    me = None if any(d[x] is None for x in HELD_ME) else [v for x in HELD_ME for v in d[x]]
    h1 = None if w is None else min(w) > -5.0
    h2 = None if w is None else st.fmean(w) >= 1.0
    h3 = None if me is None else st.fmean(me) >= -1.0
    md += ["", "### Stage 2 rules", "",
           f"- H1: worst seed pair on Pets/DTD/Caltech101 W {'—' if w is None else f'{min(w):+.2f}'} (> −5) -> {yes(h1)}",
           f"- H2: mean over those {0 if w is None else len(w)} seed pairs {'—' if w is None else f'{st.fmean(w):+.2f}'} (>= +1.0) -> {yes(h2)}",
           f"- H3: MNIST/EuroSAT 75% mean {'—' if me is None else f'{st.fmean(me):+.2f}'} (>= −1.0) -> {yes(h3)}", ""]
    return None if None in (h1, h2, h3) else (h1 and h2 and h3)


def main():
    md = ["# Gate with a capped temperature (gatec): results", "",
          "Generated by `tools/analyze_gatec.py`; rules fixed in `gatec_plan.md` before the runs. "
          "last10, paired by seed: mean (p, seeds won / seeds).", ""]
    s1 = stage1(md)
    s2 = stage2(md)
    md += [f"**Stage 1: {yes(s1)} | Stage 2: {yes(s2)} | Adopt gatec: "
           f"{yes(None if None in (s1, s2) else (s1 and s2))}**", ""]
    text = "\n".join(md)
    open(OUT, "w", encoding="utf-8").write(text)
    print(text)


if __name__ == "__main__":
    main()
