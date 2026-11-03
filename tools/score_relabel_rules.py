"""Score alternative relabel rules offline, on the suspects one real run actually produced.

Reads the noise_seed_*.json files of a run made with --filter_relabel_log true. Every filter
refresh logged, per sample: its label, its true label, whether the filter picked it as a suspect,
whether the round was hard, and the global model's top-3 classes with probabilities. Each rule
below decides, for the suspects of hard rounds, "relabel to class k" or "delete", and is scored
against the truth. Nothing here runs a model; the true label is used only for scoring.

Value of a decision, relative to deleting the suspect (the K_base behaviour), with the exchange
rate fitted on DTD (dirty removed +0.326, clean removed -0.437 per 1000):
    relabel to the true class              +0.437   (a dirty image becomes a clean one)
    relabel to a wrong class               -0.326   (a dirty image stays dirty, or a clean
                                                     one becomes dirty, instead of going)
So relabelling pays whenever it is right more than 42.7% of the time. The rate is borrowed
from another dataset, so read the column as a ranking of the rules, not as points.

    python tools/score_relabel_rules.py <run dir> [<run dir> ...]
"""
import glob
import json
import os
import statistics
import sys
from collections import Counter, defaultdict

GAIN, LOSS = 0.437, 0.326


def load(paths):
    """rows[(seed, client)] = list of refreshes in round order; each is (round, role, samples)."""
    rows = defaultdict(list)
    for path in paths:
        for f in sorted(glob.glob(os.path.join(path, '**', 'noise_seed_*.json'), recursive=True)):
            seed = f"{path}:{os.path.basename(f)}"
            for rec in json.load(open(f, encoding='utf-8')).get('filter', []):
                for c, v in rec['clients'].items():
                    if 'samples' in v:
                        rows[(seed, c)].append((rec['round'], v['role'], v['samples']))
    for k in rows:
        rows[k].sort(key=lambda r: r[0])
    return rows


# ------------------------------------------------------------------ rules
# Each rule sees one suspect and its client context and returns a class, or None to delete.
# ctx: counts = Counter of the client's labels this refresh, prev = top-3 of the same sample at
# the previous refresh (None if there is none).

def r_top1(s, ctx):
    """K_fix: the global model's first choice, whenever it differs from the label."""
    k = s['top'][0][0]
    return k if k != s['y'] else None


def capped_prior(counts):
    # The client's own label histogram says which classes it really holds (Dirichlet 0.1: a
    # few). Capped at the median non-zero count, so a class blown up by an attacker -- its
    # target holds 40% of its labels -- gets no more pull than an ordinary big class.
    nz = sorted(v for v in counts.values() if v > 0)
    cap = nz[len(nz) // 2] if nz else 1
    return lambda k: (min(counts.get(k, 0), cap) + 1) / (cap + 1)


def r_prior(s, ctx):
    """A: re-rank the top-3 by probability x capped client prior."""
    pri = capped_prior(ctx['counts'])
    k = max(s['top'], key=lambda kp: kp[1] * pri(kp[0]))[0]
    return k if k != s['y'] else None


def overfull(counts):
    # a class holding more than twice the median non-zero count: what an attacker's target
    # looks like from inside the client's own label list
    nz = sorted(v for v in counts.values() if v > 0)
    med = nz[len(nz) // 2] if nz else 0
    return {k for k, v in counts.items() if v > 2 * med}


def r_no_overfull(s, ctx):
    """D: K_fix, but never relabel INTO an over-full class."""
    k = r_top1(s, ctx)
    return None if k is None or k in overfull(ctx['counts']) else k


def r_stable(s, ctx):
    """B: K_fix, but only if the first choice is the same as at the previous refresh."""
    k = r_top1(s, ctx)
    if k is None or ctx['prev'] is None or ctx['prev'][0][0] != k:
        return None
    return k


def r_margin(s, ctx):
    """First choice clearly ahead of the second (margin 0.2); for comparison with K_fixconf."""
    k = r_top1(s, ctx)
    if k is None or len(s['top']) < 2 or s['top'][0][1] - s['top'][1][1] < 0.2:
        return None
    return k


def r_prior_no_overfull(s, ctx):
    """A + D."""
    k = r_prior(s, ctx)
    return None if k is None or k in overfull(ctx['counts']) else k


def r_prior_stable(s, ctx):
    """A + B: prior-ranked choice, and the plain first choice was the same last refresh."""
    k = r_prior(s, ctx)
    if k is None or ctx['prev'] is None or ctx['prev'][0][0] != k:
        return None
    return k


RULES = [("K_fix (top-1)", r_top1), ("A client prior", r_prior),
         ("B stable over 2 refreshes", r_stable), ("D never into over-full class", r_no_overfull),
         ("A + D", r_prior_no_overfull), ("A + B", r_prior_stable), ("margin 0.2", r_margin)]


def score(rows):
    out = {name: defaultdict(Counter) for name, _ in RULES}
    for (seed, c), refreshes in rows.items():
        prev_top = {}
        for rnd, role, samples in refreshes:
            counts = Counter(r[0] for r in samples)
            for i, (y, clean, sus, hard, top) in enumerate(samples):
                s = {'y': y, 'top': top}
                ctx = {'counts': counts, 'prev': prev_top.get(i)}
                if sus and hard:
                    for name, rule in RULES:
                        k = rule(s, ctx)
                        o = out[name][role]
                        if k is None:
                            o['deleted'] += 1
                        else:
                            o['relabelled'] += 1
                            o['right' if k == clean else 'wrong'] += 1
                            if y == clean:
                                o['broke'] += 1
                prev_top[i] = top
    return out


def main():
    rows = load(sys.argv[1:])
    if not rows:
        sys.exit("no samples logged: run with --filter_relabel_log true")
    out = score(rows)
    roles = sorted({r for o in out.values() for r in o})
    print("Suspects of hard rounds only. value = relabel decisions priced against deleting:")
    print(f"  right x +{GAIN}, wrong x -{LOSS}, per 1000 label-rounds (a ranking, not points)\n")
    for name, _ in RULES:
        print(name)
        tot = 0.0
        for role in roles:
            o = out[name][role]
            n = o['relabelled']
            v = (GAIN * o['right'] - LOSS * o['wrong']) / 1000
            tot += v
            print(f"  {role:10s} relabelled {n:6d}  right {o['right']:6d} "
                  f"({100 * o['right'] / max(n, 1):5.1f}%)  wrong {o['wrong']:6d} "
                  f"(of which broke a clean label {o['broke']:5d})  deleted {o['deleted']:6d}"
                  f"  value {v:+.3f}")
        print(f"  {'total':10s} value {tot:+.3f}\n")


if __name__ == "__main__":
    main()
