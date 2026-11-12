"""Stage 1 of results/side-research/merge_ablation/plan.md: arm gatefz (tau = 0, no look-alike merge)
against the paper's FedCLEAR on seeds 0-4, with the comparator rule of make_paper_tables.py (arm gatef,
basic-repair run where gatef is missing). Prints per-setting paired differences and the Z1-Z3 checks.

Usage: python tools/analyze_merge_ablation.py
"""
import os
import statistics as st
import sys

sys.path.insert(0, os.path.dirname(__file__))
import analyze_baselines as ab
from make_paper_tables import DS, S1, S2, seeds

z1, z2, z3 = [], [], []
for name in DS:
    for sc, rows in ((1, S1), (2, S2)):
        per_seed = []
        print(f"\n{name} scenario {sc}")
        for kind, s in rows:
            a = ab.last10(f"{DS[name]}_{kind}_{s}_gatefz")
            b = seeds(name, "CLEAR", kind, s, "gatef")
            if not a or len(a) != 5:
                print(f"  {kind} {s}: gatefz missing ({a})")
                continue
            r = ab.paired(a, b)
            d = [x - y for x, y in zip(a, b)]
            per_seed.append(d)
            print(f"  {kind} {s:7s} gatefz {st.fmean(a):6.2f}  FedCLEAR {st.fmean(b):6.2f}  diff {r[0]:+.2f}"
                  f"  p {r[1]:.3f}  worst seed {min(d):+.2f}")
            if r[0] < -1.0 and r[1] < 0.05:
                z2.append((name, kind, s, r[0], r[1]))
            z3 += [(name, kind, s, x) for x in d if x <= -5]
        if per_seed:
            m = st.fmean(x for d in per_seed for x in d)
            z1.append((name, sc, m, len(per_seed)))
            print(f"  mean {m:+.2f} over {len(per_seed)} settings")

print("\nZ1 (each mean >= -0.5):", "PASS" if all(m >= -0.5 for *_, m, _ in z1) and len(z1) == 10 else "FAIL",
      [(n, s, round(m, 2)) for n, s, m, _ in z1 if m < -0.5])
print("Z2 (no setting < -1 with p < 0.05):", "PASS" if not z2 else "FAIL", z2)
print("Z3 (no seed pair <= -5):", "PASS" if not z3 else "FAIL", z3)
