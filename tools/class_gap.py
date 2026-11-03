"""Where does the gap between two arms come from, class by class?

Reads `class_acc` (per-class test accuracy over the last-10 window) and `client_classes` (which
classes each client really holds) from the noise_seed_*.json files, which runs have logged since
2026-09-27. Classes are grouped by how much of their training data sits with the attackers:

  attacker-only   the attackers hold >= 80% of the class's clean training images
  shared          20% .. 80%
  others          < 20%

For each group it prints the mean per-class accuracy of arm A, arm B, and the difference, paired
by seed. The question it answers: is `L_oracle60 - N_excl` (what the attackers' clean 60% is worth)
concentrated in the classes only the attackers hold?

    python tools/class_gap.py <dataset dir> <arm A> <arm B>
    e.g. python tools/class_gap.py results/Phase_ex/L/oxford_pets L_oracle60 N_excl
"""
import glob
import json
import os
import statistics
import sys


def load(ds_dir, arm):
    out = {}
    for f in glob.glob(os.path.join(ds_dir, 'runs', f'*_{arm}', '**', 'noise_seed_*.json'),
                       recursive=True):
        seed = int(os.path.basename(f).split('_')[-1].split('.')[0])
        J = json.load(open(f, encoding='utf-8'))
        if not J.get('class_acc'):
            continue
        C = len(J['class_acc'][0]['acc'])
        acc = [statistics.fmean(r['acc'][c] for r in J['class_acc'] if r['acc'][c] is not None)
               for c in range(C)]
        out[seed] = (acc, J['client_classes'], J['roles'])
    return out


def groups(client_classes, roles, C):
    tot, mal = [0] * C, [0] * C
    for cid, v in client_classes.items():
        for k, n in v['true'].items():
            tot[int(k)] += n
            if roles[int(cid)] == 'malicious':
                mal[int(k)] += n
    g = {}
    for c in range(C):
        share = mal[c] / tot[c] if tot[c] else 0.0
        g[c] = 'attacker-only' if share >= 0.8 else 'shared' if share >= 0.2 else 'others'
    return g


def main():
    ds_dir, a, b = sys.argv[1:4]
    A, B = load(ds_dir, a), load(ds_dir, b)
    seeds = sorted(set(A) & set(B))
    if not seeds:
        sys.exit(f"no seeds with class_acc for both {a} and {b}")
    rows = {}
    for s in seeds:
        accA, cc, roles = A[s]
        accB = B[s][0]
        g = groups(cc, roles, len(accA))
        for c, grp in g.items():
            rows.setdefault(grp, {}).setdefault(s, []).append((accA[c], accB[c]))
    print(f"{a} vs {b}, per-class test accuracy (last-10), {len(seeds)} seeds")
    for grp in ('attacker-only', 'shared', 'others'):
        if grp not in rows:
            continue
        per_seed = rows[grp]
        n_cls = statistics.fmean(len(v) for v in per_seed.values())
        ma = statistics.fmean(statistics.fmean(x for x, _ in v) for v in per_seed.values())
        mb = statistics.fmean(statistics.fmean(y for _, y in v) for v in per_seed.values())
        n_all = len(A[seeds[0]][0])
        # points of overall accuracy this group accounts for (classes are about equal-sized in test)
        print(f"  {grp:14s} ~{n_cls:5.1f} classes/seed   {a} {100 * ma:6.2f}   {b} {100 * mb:6.2f}"
              f"   diff {100 * (ma - mb):+6.2f}   -> {100 * (ma - mb) * n_cls / n_all:+5.2f} "
              f"points of the overall gap")


if __name__ == "__main__":
    main()
