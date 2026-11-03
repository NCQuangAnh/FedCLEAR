"""FedCorr (Xu et al., CVPR 2022) helpers for the prompt setting (`--fedcorr true`).

The stages live in flcore/servers/server_fedcorr.py; this module holds the pieces that touch a
client's data. Each one follows the official code (github.com/Xu-Jingyi/FedCorr, main.py and
util/util.py), with the differences listed in results/side-research/fedcorr/fedcorr_plan.md.
"""
import copy

import numpy as np
import torch
from sklearn.mixture import GaussianMixture

from .diag import _lid, _pristine_view, _probs, _rng_restore, _rng_state


def _labels(client):
    return [int(t) for _, t in client.trainloader.dataset.samples]


def _predict(client):
    """Softmax of client.model on the client's images (test transform, every RNG restored)."""
    st = _rng_state()
    try:
        view = _pristine_view(client)
        if len(view.samples) == 0:
            return None, view
        p, _ = _probs(client, view, with_zs=False)
        return p, view
    finally:
        _rng_restore(st)


def local_report(client):
    """What a client reports after its pre-processing training, from its own trained prompt:
    the LID of its predictions on its images (k = 20) and every image's loss.

    The loss is the official one: cross-entropy applied to the softmax output (get_output in
    util/util.py), not to the logits. For K classes it is almost exactly a constant minus the
    probability of the label, which is what the loss GMM then splits."""
    p, view = _predict(client)
    if p is None:
        return {'lid': None, 'loss': []}
    y = torch.tensor(view.targets)
    loss = torch.nn.functional.cross_entropy(p, y, reduction='none')
    return {'lid': _lid(p), 'loss': [float(v) for v in loss]}


def global_probs(model, client):
    """The global prompt's softmax on a client's images, computed on the client."""
    client.model = copy.deepcopy(model)
    try:
        p, _ = _predict(client)
    finally:
        del client.model
    return p


def gmm_high(x, seed):
    """Official split: a 2-component GMM on x; True where x falls in the higher-mean component."""
    x = np.asarray(x, dtype=float).reshape(-1, 1)
    if len(x) < 2 or np.ptp(x) == 0:
        return np.zeros(len(x), dtype=bool)
    g = GaussianMixture(n_components=2, random_state=seed).fit(x)
    low = int(np.argsort(g.means_[:, 0])[0])
    return g.predict(x) != low


def relabel(client, idx, new):
    """Set image idx[j]'s label to new[j] for good, and count, against the true labels, how many
    wrong labels this fixed and how many right ones it broke (logged only)."""
    ds = client.trainloader.dataset
    clean = [int(t) for t in ds.clean_targets]
    rep = {'relabeled': 0, 'fixed': 0, 'broken': 0}
    for i, k in zip(idx, new):
        path, lab = ds.samples[i]
        if int(lab) == int(k):
            continue
        rep['relabeled'] += 1
        rep['fixed'] += int(int(lab) != clean[i] and int(k) == clean[i])
        rep['broken'] += int(int(lab) == clean[i] and int(k) != clean[i])
        ds.samples[i] = (path, type(lab)(int(k)))
    ds.targets = [t for _, t in ds.samples]
    return rep


def noise_level(client):
    """Share of the client's current labels that are wrong (ground truth, logged only)."""
    ds = client.trainloader.dataset
    n = len(ds.samples)
    if n == 0:
        return 0.0
    return round(sum(int(t) != int(c) for (_, t), c in zip(ds.samples, ds.clean_targets)) / n, 4)
