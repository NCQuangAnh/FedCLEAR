"""Robust aggregation rules, and a record of which clients each rule keeps.

These are the defenses a reviewer will ask about, and they are also the measurement
instrument for the thesis question: a rule like Krum names the clients it trusts, so we can
count how often it throws out an honest-but-noisy client instead of a malicious one.

Every rule takes the same shape as FedAvg's: a dict of client id -> prompt state, and a dict
of client id -> weight. `selected` in the returned record is the set of clients that actually
influenced the result (all of them for mean-like rules).
"""

import torch

RULES = ('fedavg', 'median', 'trimmed_mean', 'krum', 'multikrum')


def _flatten(state, keys):
    return torch.cat([state[k].reshape(-1).float() for k in keys])


def _pairwise_sq_dists(flat):
    ids = list(flat)
    n = len(ids)
    d = torch.zeros(n, n)
    for i in range(n):
        for j in range(i + 1, n):
            v = torch.sum((flat[ids[i]] - flat[ids[j]]) ** 2)
            d[i, j] = d[j, i] = v
    return ids, d


def aggregate(states, weights, rule='fedavg', trim=0.1, num_malicious=None):
    """Aggregate client states. Returns (avg_state, record)."""
    assert states, 'no client states to aggregate'
    keys = list(states[list(states)[0]])
    ids = list(states)
    # client ids arrive as numpy integers from the server's selection draw; the record is
    # written to JSON, so it keeps plain ints
    record = {'rule': rule, 'selected': [int(c) for c in ids], 'excluded': []}

    if rule == 'fedavg':
        avg = {k: sum(s[k].float() * weights[c] for c, s in states.items()) for k in keys}
        return avg, record

    if rule == 'median':
        # coordinate-wise median, the standard Byzantine-robust baseline
        avg = {}
        for k in keys:
            stack = torch.stack([states[c][k].float() for c in ids])
            avg[k] = stack.median(dim=0).values
        return avg, record

    if rule == 'trimmed_mean':
        # drop the `trim` fraction at each end of every coordinate, then average the rest
        cut = max(1, int(round(trim * len(ids)))) if len(ids) > 2 else 0
        avg = {}
        for k in keys:
            stack = torch.stack([states[c][k].float() for c in ids])
            sorted_stack, _ = stack.sort(dim=0)
            kept = sorted_stack[cut:len(ids) - cut] if cut and len(ids) - 2 * cut > 0 else sorted_stack
            avg[k] = kept.mean(dim=0)
        record['trim_per_side'] = cut
        return avg, record

    if rule in ('krum', 'multikrum'):
        flat = {c: _flatten(states[c], keys) for c in ids}
        order, d = _pairwise_sq_dists(flat)
        n = len(order)
        f = num_malicious if num_malicious is not None else max(1, n // 5)
        # each client's score: sum of squared distances to its n-f-2 closest neighbours
        keep = max(1, n - f - 2)
        scores = []
        for i in range(n):
            row = torch.cat([d[i, :i], d[i, i + 1:]])
            scores.append(float(row.sort().values[:keep].sum()))
        ranked = [order[i] for i in sorted(range(n), key=lambda i: scores[i])]
        m = 1 if rule == 'krum' else max(1, n - f)
        chosen = ranked[:m]
        total = sum(weights[c] for c in chosen) or 1.0
        avg = {k: sum(states[c][k].float() * (weights[c] / total) for c in chosen) for k in keys}
        record.update({'selected': sorted(int(c) for c in chosen),
                       'excluded': sorted(int(c) for c in ids if c not in chosen),
                       'scores': {int(c): round(s, 4) for c, s in zip(order, scores)}})
        return avg, record

    raise ValueError(f'unknown aggregation rule: {rule}')
