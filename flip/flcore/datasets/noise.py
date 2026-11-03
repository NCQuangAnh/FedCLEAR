"""Client-side label noise injection.

Noise is applied after the Dirichlet split, on each client's own subset, so the split
itself stays identical to a clean run with the same seed. That is what makes noisy and
clean runs comparable run by run.

Three noise models:

  sym       flip to any other class, uniformly (symmetric flip)
  pair      flip to the next class index, i.e. a fixed similar-class pairing (pair flip)
  instance  instance-dependent noise following Xia et al. 2020: a per-sample flip rate and
            a flip distribution that depends on the image itself

The instance-dependent features are downscaled raw pixels, never CLIP features. The
detection signals we study are CLIP-based, so generating the noise with CLIP would leak
the answer into the data.
"""

import numpy as np
from PIL import Image

from ..pretty.logger import log

NOISE_TYPES = ('none', 'sym', 'pair', 'instance')
NOISE_MODES = ('uniform', 'hetero')
ORACLES = ('none', 'clean', 'drop_noisy')

# side length the images are downscaled to for instance-dependent noise
IDN_SIZE = 16
# spread of the per-sample flip rate around the client's target rate (Xia et al. 2020)
IDN_RATE_STD = 0.1


def _samples_as_tuples(subset):
    """Normalize `samples` to a list of (path, int) tuples.

    After the few-shot split, `samples` is a numpy array of strings (np.delete coerces the
    list of tuples), so labels come back as np.str_. Writing plain tuples back keeps
    `__getitem__`, `get_stats` and our own bookkeeping on integers.
    """
    return [(str(p), int(t)) for p, t in subset.samples]


def assign_client_rates(num_clients, rate, mode, frac, rng):
    """Pick which clients are noisy and at what rate.

    uniform: every noisy client gets exactly `rate`.
    hetero:  noisy clients get rates spread evenly over (0, rate], so with rate=0.5 and
             all ten clients noisy the rates are 0.05, 0.10, ..., 0.50. This is the
             heterogeneous-noise setting used by FedCorr and later noisy-FL work.
    """
    num_noisy = int(round(frac * num_clients))
    num_noisy = max(0, min(num_clients, num_noisy))
    noisy_ids = sorted(rng.permutation(num_clients)[:num_noisy].tolist())
    rates = [0.0] * num_clients
    for k, cid in enumerate(noisy_ids):
        if mode == 'hetero':
            rates[cid] = rate * (k + 1) / num_noisy
        else:
            rates[cid] = rate
    return rates


def _flip_sym(targets, num_classes, flip_idx, rng):
    new = list(targets)
    for i in flip_idx:
        choices = [c for c in range(num_classes) if c != targets[i]]
        new[i] = int(rng.choice(choices))
    return new


def _flip_pair(targets, num_classes, flip_idx, rng):
    new = list(targets)
    for i in flip_idx:
        new[i] = int((targets[i] + 1) % num_classes)
    return new


def _pixel_features(paths):
    """Downscaled grayscale pixels, flattened and standardized. No trained model involved."""
    feats = []
    for p in paths:
        with Image.open(p) as im:
            im = im.convert('L').resize((IDN_SIZE, IDN_SIZE), Image.BILINEAR)
            feats.append(np.asarray(im, dtype=np.float32).reshape(-1) / 255.0)
    x = np.stack(feats)
    x = x - x.mean(axis=0, keepdims=True)
    norm = np.linalg.norm(x, axis=1, keepdims=True)
    return x / np.maximum(norm, 1e-8)


def _flip_instance(targets, num_classes, paths, rate, rng):
    """Instance-dependent noise (Xia et al. 2020, 'Part-dependent label noise').

    Each sample gets its own flip rate q ~ N(rate, 0.1) clipped to [0, 1], and the mass q is
    spread over the wrong classes by softmax(x @ W[y]). The number of flips is therefore
    only approximately `rate * n`, which is the point: real mislabelling concentrates on
    ambiguous images instead of hitting a fixed quota.
    """
    n = len(targets)
    x = _pixel_features(paths)
    dim = x.shape[1]
    W = rng.normal(size=(num_classes, dim, num_classes)).astype(np.float32)
    q = np.clip(rng.normal(rate, IDN_RATE_STD, size=n), 0.0, 1.0)
    new = list(targets)
    flipped = []
    for i in range(n):
        y = int(targets[i])
        p = x[i] @ W[y]
        p[y] = -np.inf
        p = np.exp(p - p.max())
        p = p / p.sum() * q[i]
        p[y] = 1.0 - q[i]
        drawn = int(rng.choice(num_classes, p=p / p.sum()))
        if drawn != y:
            new[i] = drawn
            flipped.append(i)
    return new, flipped


def inject_client_label_noise(splits, num_classes, cfg, seed, roles=None):
    """Corrupt the labels of `splits` in place and return a report.

    `cfg` keys: type, rate, mode, frac, oracle. Every client keeps `clean_targets`, so an
    oracle run or an analysis of which samples were flipped needs no second pass.

    `roles` (phase 3) marks which clients are malicious; those are left untouched here, since
    their labels are the attacker's business and are set in flcore/attack.py.
    """
    ntype = cfg.get('type', 'none')
    oracle = cfg.get('oracle', 'none')
    report = {'type': ntype, 'rate': cfg.get('rate', 0.0), 'mode': cfg.get('mode', 'uniform'),
              'frac': cfg.get('frac', 1.0), 'oracle': oracle, 'seed': int(seed), 'clients': []}
    if ntype == 'none' or cfg.get('rate', 0.0) <= 0:
        for cid, subset in enumerate(splits):
            subset.samples = _samples_as_tuples(subset)
            subset.targets = [t for _, t in subset.samples]
            subset.clean_targets = list(subset.targets)
            report['clients'].append({'id': cid, 'role': 'honest', 'target_rate': 0.0,
                                      'realized_rate': 0.0, 'n': len(subset.targets),
                                      'flipped': 0})
        report['num_flipped'] = 0
        report['num_samples'] = sum(c['n'] for c in report['clients'])
        report['excluded'] = []
        return report

    # one RNG for the role assignment, one per client for the flips: adding a client or
    # changing its size must not shift another client's noise
    rates = assign_client_rates(len(splits), cfg['rate'], cfg.get('mode', 'uniform'),
                                cfg.get('frac', 1.0), np.random.default_rng(seed * 7919 + 1))
    if roles is not None:
        # roles were decided up front (malicious first), so honour them instead of the draw
        noisy_ids = [c for c, r in enumerate(roles) if r == 'noisy']
        chosen = [r for r in rates if r > 0] or [cfg['rate']]
        rates = [0.0] * len(splits)
        for k, cid in enumerate(noisy_ids):
            rates[cid] = chosen[k % len(chosen)] if cfg.get('mode') == 'hetero' else cfg['rate']
    excluded = []
    for cid, subset in enumerate(splits):
        subset.samples = _samples_as_tuples(subset)
        clean = [t for _, t in subset.samples]
        subset.clean_targets = list(clean)
        rate = rates[cid]
        rng = np.random.default_rng(seed * 7919 + 13 + cid)
        n = len(clean)
        flip_idx = []
        if rate > 0 and n > 0:
            if ntype == 'instance':
                paths = [p for p, _ in subset.samples]
                new, flip_idx = _flip_instance(clean, num_classes, paths, rate, rng)
            else:
                # a fixed quota of round(rate * n) samples, chosen without replacement
                k = int(round(rate * n))
                flip_idx = sorted(rng.permutation(n)[:k].tolist())
                flip = _flip_sym if ntype == 'sym' else _flip_pair
                new = flip(clean, num_classes, flip_idx, rng)
            if oracle != 'clean':
                subset.samples = [(p, int(t)) for (p, _), t in zip(subset.samples, new)]
        subset.targets = [t for _, t in subset.samples]
        realized = sum(1 for a, b in zip(subset.targets, clean) if a != b)
        role = 'noisy' if rate > 0 else 'honest'
        if role == 'noisy' and oracle == 'drop_noisy':
            excluded.append(cid)
        report['clients'].append({'id': cid, 'role': role, 'target_rate': round(rate, 4),
                                  'realized_rate': round(realized / n, 4) if n else 0.0,
                                  'n': n, 'flipped': realized})
    report['num_flipped'] = sum(c['flipped'] for c in report['clients'])
    report['num_samples'] = sum(c['n'] for c in report['clients'])
    report['excluded'] = excluded
    return report


def log_noise_report(report):
    import json
    noisy = [c for c in report['clients'] if c['role'] == 'noisy']
    log.info(f"- label noise: type={report['type']} rate={report['rate']} "
             f"mode={report['mode']} oracle={report['oracle']}, "
             f"{len(noisy)}/{len(report['clients'])} noisy clients, "
             f"{report['num_flipped']}/{report['num_samples']} labels flipped "
             f"({report['num_flipped'] / max(report['num_samples'], 1):.1%})")
    for c in report['clients']:
        log.debug(f"  client {c['id']}: role={c['role']} target={c['target_rate']} "
                  f"realized={c['realized_rate']} n={c['n']} flipped={c['flipped']}")
    if report['excluded']:
        log.info(f"- ORACLE drop_noisy: excluding clients {report['excluded']} from training")
    # one machine-readable line, so tools/parse_flip_log.py can recover the ground truth
    log.info('NOISE_REPORT ' + json.dumps(report, sort_keys=True))
