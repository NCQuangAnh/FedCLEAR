"""Malicious clients: role assignment, data poisoning, update poisoning.

Phase 2 measured that excluding *noisy* clients buys almost nothing, because their data is
still worth roughly what it costs to lose it. Malicious clients are the opposite case: their
contribution has negative value, so exclusion is the only correct treatment. The thesis
question is therefore whether the two can be told apart — which first needs attacks that
deliberately look like noise.

Roles are disjoint: a client is honest, noisy, or malicious.

Data-side attacks (the labels a client trains on):

  targeted_flip   every sample of one class is relabelled as another, fixed class. Loud, and
                  what the poisoning literature usually studies.
  noise_disguise  the same *marginal* flip statistics as an honest noisy client (same rate,
                  same "looks random" first-order profile) but the targets are chosen
                  adversarially. Designed to be indistinguishable from label noise by any
                  detector that only looks at how *much* a client disagrees.

Update-side attacks (what the client sends back):

  scale           the prompt update is multiplied by a factor (classic scaling attack)
  signflip        the prompt update is negated, which drags the global prompt backwards
"""

import numpy as np

from .pretty.logger import log

ATTACKS = ('none', 'targeted_flip', 'noise_disguise', 'scale', 'signflip')
DATA_ATTACKS = ('targeted_flip', 'noise_disguise')
UPDATE_ATTACKS = ('scale', 'signflip')


def assign_roles(num_clients, noisy_frac, malicious_frac, seed):
    """Disjoint roles. Malicious are drawn first, then noisy from the rest.

    With malicious_frac = 0 this reproduces exactly the noisy set phase 2 used, so gate-A
    runs stay comparable.
    """
    roles = ['honest'] * num_clients
    n_mal = max(0, min(num_clients, int(round(malicious_frac * num_clients))))
    mal_rng = np.random.default_rng(seed * 104729 + 3)
    malicious = sorted(mal_rng.permutation(num_clients)[:n_mal].tolist()) if n_mal else []
    for c in malicious:
        roles[c] = 'malicious'
    n_noisy = max(0, min(num_clients - n_mal, int(round(noisy_frac * num_clients))))
    if n_noisy:
        # same stream as the phase-2 injector, minus anyone already malicious
        noise_rng = np.random.default_rng(seed * 7919 + 1)
        order = [c for c in noise_rng.permutation(num_clients).tolist() if c not in malicious]
        for c in sorted(order[:n_noisy]):
            roles[c] = 'noisy'
    return roles


def _class_pairs(num_classes, rng):
    """A fixed source -> target class map for targeted attacks (source != target)."""
    src = int(rng.integers(num_classes))
    dst = int((src + 1 + rng.integers(num_classes - 1)) % num_classes)
    return src, dst


def apply_data_attack(subset, kind, rate, num_classes, rng):
    """Corrupt one malicious client's labels in place; returns a per-client report."""
    clean = list(subset.clean_targets)
    n = len(clean)
    new = list(subset.targets)
    info = {'kind': kind, 'rate': rate}
    if kind == 'targeted_flip':
        src, dst = _class_pairs(num_classes, rng)
        idx = [i for i, t in enumerate(clean) if t == src]
        if not idx:
            # this client holds nothing of the source class; fall back to its largest class
            counts = np.bincount(clean, minlength=num_classes)
            src = int(counts.argmax())
            dst = int((src + 1) % num_classes)
            idx = [i for i, t in enumerate(clean) if t == src]
        for i in idx:
            new[i] = dst
        info.update({'source': src, 'target': dst, 'n_source': len(idx)})
    elif kind == 'noise_disguise':
        # Same flip rate as an honest noisy client, so any "how much does this client
        # disagree" statistic sees nothing unusual. The targets are what differ: instead of
        # a uniform draw, every flipped label is pushed to the class the attacker wants
        # over-represented, one target per client.
        k = int(round(rate * n))
        idx = sorted(rng.permutation(n)[:k].tolist())
        dst = int(rng.integers(num_classes))
        for i in idx:
            new[i] = dst if clean[i] != dst else int((dst + 1) % num_classes)
        info.update({'target': dst, 'n_flipped': len(idx)})
    else:
        raise ValueError(f'not a data attack: {kind}')
    subset.samples = [(p, int(t)) for (p, _), t in zip(subset.samples, new)]
    subset.targets = [t for _, t in subset.samples]
    info['realized_rate'] = round(sum(1 for a, b in zip(subset.targets, clean) if a != b) / max(n, 1), 4)
    return info


def apply_client_attacks(splits, num_classes, roles, cfg, seed):
    """Run the data-side attack on every malicious client. Returns a report."""
    kind = cfg.get('type', 'none')
    report = {'type': kind, 'rate': cfg.get('rate', 0.0), 'scale': cfg.get('scale', 1.0),
              'malicious': [c for c, r in enumerate(roles) if r == 'malicious'], 'clients': []}
    if kind in DATA_ATTACKS:
        for cid, subset in enumerate(splits):
            if roles[cid] != 'malicious':
                continue
            rng = np.random.default_rng(seed * 104729 + 17 + cid)
            info = apply_data_attack(subset, kind, cfg.get('rate', 0.0), num_classes, rng)
            info['id'] = cid
            report['clients'].append(info)
    return report


def apply_sample_oracle(splits, roles, mode):
    """Sample-level oracles. Not methods -- ceilings.

    Every previous defence in this project acts on whole clients, and gate F measured that even
    perfect, instant client removal buys about one point. These two say what the sample level
    could buy if it were solved perfectly, and they run after both the noise and the attack so
    they cover damage from either source.

      drop_dirty     delete exactly the samples whose label was changed. Ceiling of perfect
                     sample filtering: the poison is gone, and so is that data.
      restore_dirty  put the true label back. Ceiling of perfect label repair: the poison is
                     gone and the data stays.

    The gap between them is the price of throwing a sample away instead of fixing it. The gap
    between restore_dirty and the all-clean baseline is everything label contamination does NOT
    explain -- data scarcity, the Dirichlet split, prompt-learning instability.
    """
    report = {'mode': mode, 'clients': []}
    if mode == 'none':
        return report
    for cid, subset in enumerate(splits):
        clean = getattr(subset, 'clean_targets', None)
        if clean is None:
            continue
        dirty = [i for i, (t, c) in enumerate(zip(subset.targets, clean)) if t != c]
        if mode == 'drop_dirty_mal':
            # the 60% oracle for gate L: only the malicious clients lose their flipped samples,
            # so this is the ceiling of salvaging exactly their clean part
            if not roles or roles[cid] != 'malicious':
                continue
            mode_here = 'drop_dirty'
        else:
            mode_here = mode
        if mode_here == 'restore_dirty':
            subset.samples = [(p, int(c)) for (p, _), c in zip(subset.samples, clean)]
        elif mode_here == 'drop_dirty':
            keep = [i for i in range(len(subset.targets)) if i not in set(dirty)]
            subset.samples = [subset.samples[i] for i in keep]
            subset.clean_targets = [clean[i] for i in keep]
        else:
            raise ValueError(f'unknown sample oracle {mode}')
        subset.targets = [t for _, t in subset.samples]
        report['clients'].append({'id': cid, 'role': roles[cid] if roles else 'unknown',
                                  'dirty': len(dirty), 'n_after': len(subset.targets)})
    total = sum(c['dirty'] for c in report['clients'])
    log.info(f"- ORACLE {mode}: {total} damaged samples across "
             f"{sum(1 for c in report['clients'] if c['dirty'])} clients")
    return report


def attack_update(state, global_state, kind, scale):
    """Poison one client's returned prompt state, given the global state it started from."""
    if kind == 'scale':
        factor = scale
    elif kind == 'signflip':
        factor = -1.0
    else:
        raise ValueError(f'not an update attack: {kind}')
    out = {}
    for k, v in state.items():
        g = global_state[k].to(v.device).type(v.dtype)
        out[k] = g + (v - g) * factor
    return out


def log_attack_report(report, roles):
    import json
    counts = {r: roles.count(r) for r in ('honest', 'noisy', 'malicious')}
    log.info(f"- client roles: {counts}, attack={report['type']}")
    for c in report['clients']:
        log.debug(f"  malicious client {c['id']}: {c}")
    log.info('ATTACK_REPORT ' + json.dumps({'roles': roles, **report}, sort_keys=True))
