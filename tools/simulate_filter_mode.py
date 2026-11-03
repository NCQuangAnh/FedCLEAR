"""Replay --filter_soft auto over the filter records already in hand.

Same trick as the refusal-rule calibration: the decision only reads `baseline`, which every
past run logged, so the rule can be checked on five seeds of two datasets before spending a
single GPU minute.
"""
import json, glob, statistics as st

THR, BAND, ALPHA = 0.22, 0.02, 0.3   # must match flip/main.py defaults

def replay(root, tag):
    per_seed = []
    for f in sorted(glob.glob(f"{root}/**/*{tag}*/**/noise_seed_*.json", recursive=True)):
        d = json.load(open(f, encoding='utf-8'))
        run, hard, picks = None, False, []
        for rec in d['filter']:
            b = rec['baseline']
            run = b if run is None else (1 - ALPHA) * run + ALPHA * b
            if run < THR - BAND:
                hard = True
            elif run > THR + BAND:
                hard = False
            dr = sum(c['dropped'] for c in rec['clients'].values())
            if rec['round'] > 0 and dr > 0:
                dd = sum(c['dropped_damaged'] for c in rec['clients'].values())
                picks.append((hard, dd / dr, run))
        per_seed.append(picks)
    return per_seed

for name, root, tag in [("DTD ", "results/Phase_bonus/H_", "dtd_H_band"),
                        ("Pets", "results/Phase_bonus/I_/pets", "oxford_pets_H_band")]:
    seeds = replay(root, tag)
    flat = [p for s in seeds for p in s]
    hard_frac = sum(1 for h, _, _ in flat if h) / len(flat)
    flips = [sum(1 for a, b in zip(s, s[1:]) if a[0] != b[0]) for s in seeds]
    prec_h = [p for h, p, _ in flat if h]
    prec_s = [p for h, p, _ in flat if not h]
    print(f"{name}: {len(seeds)} seeds, {len(flat)} active rounds")
    print(f"      picks HARD on {hard_frac:5.1%} of rounds, {st.fmean(flips):.1f} mode flips per run")
    if prec_h: print(f"      precision when it picked hard: {st.fmean(prec_h):.3f}  (n={len(prec_h)})")
    if prec_s: print(f"      precision when it picked soft: {st.fmean(prec_s):.3f}  (n={len(prec_s)})")
    print(f"      per-seed hard share: {[f'{sum(1 for h,_,_ in s if h)/len(s):.0%}' for s in seeds]}")
