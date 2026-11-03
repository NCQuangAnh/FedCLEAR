"""Score every candidate sample-level detection signal against the ground truth.

Reads the samples_seed_*.json files a --sample_diag run leaves behind and reports, for each
signal, the AUC of separating damaged samples from clean ones. Nothing here runs on a GPU and
nothing here is part of any rule: the `d` field is ground truth the server never sees.

    python tools/score_sample_signals.py <dir with samples_seed_*.json>
"""
import glob
import json
import os
import statistics
import sys
from collections import defaultdict


def auc(pos, neg):
    if not pos or not neg:
        return float('nan')
    # rank-based Mann-Whitney, ties counted as half
    order = sorted([(v, 1) for v in pos] + [(v, 0) for v in neg])
    ranks, i = {}, 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and order[j + 1][0] == order[i][0]:
            j += 1
        r = (i + j) / 2 + 1
        for k in range(i, j + 1):
            ranks[k] = r
        i = j + 1
    rsum = sum(ranks[k] for k in range(len(order)) if order[k][1] == 1)
    n1, n0 = len(pos), len(neg)
    return (rsum - n1 * (n1 + 1) / 2) / (n1 * n0)


def load(path):
    recs = []
    for f in sorted(glob.glob(os.path.join(path, '**', 'samples_seed_*.json'), recursive=True)):
        seed = os.path.basename(f).split('_')[-1].split('.')[0]
        for blob in json.load(open(f, encoding='utf-8')):
            for r in blob['rows']:
                recs.append({**r, 'seed': seed, 'round': blob['round'],
                             'client': blob['client'], 'role': blob['role']})
    return recs


def derived(recs):
    """Signals that only exist once the per-round rows are grouped."""
    # temporal: how often the global model disagreed with this label across probe rounds
    hist = defaultdict(list)
    for r in recs:
        hist[(r['seed'], r['client'], r['i'])].append(r)
    for key, rows in hist.items():
        dis = 1 - statistics.fmean(x['gok'] for x in rows)
        mloss = statistics.fmean(x['loss'] for x in rows)
        for x in rows:
            x['t_disagree'] = dis          # 0..1, high = teacher never agreed
            x['mean_loss'] = mloss         # loss averaged over probe rounds
    # per-class disagreement inside one client: a poisoned class sits near zero agreement
    per = defaultdict(list)
    for r in recs:
        per[(r['seed'], r['client'], r['y'])].append(r['gok'])
    rate = {k: statistics.fmean(v) for k, v in per.items()}
    for r in recs:
        r['cls_disagree'] = 1 - rate[(r['seed'], r['client'], r['y'])]
    return recs


SIGNALS = [
    ('loss (single round)', lambda r: r['loss']),
    ('loss (mean over rounds)', lambda r: r['mean_loss']),
    ('teacher disagrees', lambda r: 1 - r['gok']),
    ('teacher disagrees x conf', lambda r: (1 - r['gok']) * r['gconf']),
    ('teacher disagrees (mean)', lambda r: r['t_disagree']),
    ('own model disagrees', lambda r: 1 - r['sok']),
    ('class disagreement rate', lambda r: r['cls_disagree']),
    ('class rate x loss', lambda r: r['cls_disagree'] * r['mean_loss']),
]


def report(recs, title):
    pos = [r for r in recs if r['d'] == 1]
    neg = [r for r in recs if r['d'] == 0]
    if not pos or not neg:
        return
    print(f"\n--- {title}   damaged {len(pos)}, clean {len(neg)}")
    print(f"{'signal':28s} {'AUC':>7s}")
    for name, fn in SIGNALS:
        print(f"{name:28s} {auc([fn(r) for r in pos], [fn(r) for r in neg]):7.3f}")


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else '.'
    recs = derived(load(path))
    if not recs:
        print(f'no samples_seed_*.json under {path}')
        return
    print(f"{len(recs)} sample-rounds from {len({(r['seed'], r['client']) for r in recs})} "
          f"client-seeds")
    report(recs, 'ALL clients')
    for role in ('noisy', 'malicious'):
        report([r for r in recs if r['role'] == role], f'{role} clients only')
    late = [r for r in recs if r['round'] >= 25]
    report(late, 'ALL clients, rounds 25+ (teacher is stronger)')


if __name__ == '__main__':
    main()
