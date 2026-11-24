"""Gate D stage 1: client-level noise scores, logged only (`--diag_scores true`).

Every round, before local training, each client scores its own pristine data (its given
labels, before any filtering) against three predictive distributions:

  g   the global prompt it just received
  z   frozen zero-shot CLIP (never trained on any label, so never on a noisy one)
  e   the average of the two

and after local training once more with its own trained prompt (`l`). Nothing here feeds a
decision: the scores are written to the noise json so the candidate detectors can be compared
offline on the same runs. The pass runs on the test transform and restores every RNG it could
touch, so a run with the scores on trains exactly like the same run with them off.

Per distribution P, averaged over the client's images (y = the given label, nn(y) = the class
nearest to y in CLIP's zero-shot text space):

  dis      argmax P != y                                       (the old disagreement d)
  dis_far  argmax P not in {y, nn(y)}                          (gate V's look-alike exclusion)
  nll      -log P_y, clipped at 10                             (the loss-based detector)
  xs       -log P_y - H(P): surprise beyond what P itself expects. An image the model is
           unsure about (look-alike classes, a hard or rare class) costs little; a label that
           contradicts a confident prediction costs a lot
  xs_m     the same with y merged with nn(y), on both sides
  xs_mb    xs_m with the merged P-bar (sum about 2) also weighting the expected term
  xp       sum_k P_k^2 - P_y: the bounded version of xs (expected minus observed probability
           of the label under P)
  f30/f50  share of images with xp > 0.3 / 0.5, a count version that estimates contamination

plus `lid`, the local intrinsic dimension of P over the client's images (the FedCorr score,
CVPR 2022), for g and for the trained local prompt.
"""
import copy
import math
import random

import numpy as np
import torch
from torch.utils.data import DataLoader

NLL_CLIP = 10.0
LID_K = 20
# columns of a diag_samples row: given label, true label, then for g, z and e in turn:
# P(label), argmax, max prob, entropy, sum of squared probs, P(nearest class of the label).
# With --diag_full_probs true, two more columns: the K log-probabilities under g and under z.
DIAG_ROW_COLUMNS = ['label', 'true'] + [f'{d}_{c}' for d in ('g', 'z', 'e')
                                        for c in ('py', 'pred', 'pmax', 'H', 'sumsq', 'pnn')]


def _rng_state():
    st = {'py': random.getstate(), 'np': np.random.get_state(), 'torch': torch.get_rng_state()}
    if torch.cuda.is_available():
        st['cuda'] = torch.cuda.get_rng_state_all()
    return st


def _rng_restore(st):
    random.setstate(st['py'])
    np.random.set_state(st['np'])
    torch.set_rng_state(st['torch'])
    if 'cuda' in st:
        torch.cuda.set_rng_state_all(st['cuda'])


def _pristine_view(client):
    """The client's own data as it arrived: every image, its given label, test transform."""
    ds = client.trainloader.dataset
    view = copy.copy(ds)
    view.samples = list(getattr(ds, 'all_samples', ds.samples))
    view.clean_targets = list(getattr(ds, 'all_clean', getattr(ds, 'clean_targets',
                                                               [t for _, t in view.samples])))
    view.targets = [int(t) for _, t in view.samples]
    view.sample_weights = None
    test_ds = getattr(getattr(client, 'testloader', None), 'dataset', None)
    tf = getattr(test_ds, 'transform', None)
    if tf is not None:
        view.transform = tf
    return view


@torch.no_grad()
def _probs(client, view, with_zs, with_log=False):
    """Probabilities of the global prompt and of zero-shot CLIP; with_log=True also returns
    their log-probabilities from log_softmax, exact where a probability underflows to 0."""
    loader = DataLoader(view, batch_size=client.trainloader.batch_size, shuffle=False,
                        num_workers=0, drop_last=False)
    model = client.model
    zs = getattr(client, 'zs_text_feats', None) if with_zs else None
    pg, pz, lg, lz = [], [], [], []
    for batch in loader:
        data = batch[0].to(client.device)
        logits = model(data, None, test=True).float()
        pg.append(logits.softmax(dim=-1).cpu())
        if with_log:
            lg.append(logits.log_softmax(dim=-1).cpu())
        if zs is not None:
            f = model.image_encoder(data.type(model.dtype))[0].float()
            f = f / f.norm(dim=-1, keepdim=True)
            t = zs.to(f.device).float()
            scale = float(model.logit_scale.exp()) if hasattr(model, 'logit_scale') else 100.0
            zl = scale * f @ t.T
            pz.append(zl.softmax(dim=-1).cpu())
            if with_log:
                lz.append(zl.log_softmax(dim=-1).cpu())
    out = (torch.cat(pg), (torch.cat(pz) if pz else None))
    if with_log:
        out += (torch.cat(lg), (torch.cat(lz) if lz else None))
    return out


def _lid(P):
    """MLE local intrinsic dimension of the rows of P, averaged (Ma et al. 2018, as in FedCorr)."""
    n = P.shape[0]
    k = min(LID_K, n - 1)
    if k < 2:
        return None
    d = torch.cdist(P.double(), P.double())
    d.fill_diagonal_(float('inf'))
    r, _ = d.topk(k, dim=1, largest=False)
    r = r.clamp_min(1e-12)
    v = torch.log(r / r[:, -1:]).mean(dim=1)
    v = v.clamp(max=-1e-12)
    return float((-1.0 / v).mean())


def _scores(P, y, nn):
    n = P.shape[0]
    idx = torch.arange(n)
    py = P[idx, y]
    pred = P.argmax(dim=1)
    eps = 1e-12
    logP = P.clamp_min(eps).log()
    H = -(P * logP).sum(dim=1)
    nll = (-py.clamp_min(eps).log()).clamp(max=NLL_CLIP)
    sumsq = (P * P).sum(dim=1)
    xp = sumsq - py
    nn_y = torch.tensor([nn[int(c)] for c in y.tolist()]) if nn is not None else None
    out = {
        'dis': float((pred != y).float().mean()),
        'nll': float(nll.mean()),
        'xs': float((nll - H).mean()),
        'xp': float(xp.mean()),
        'f30': float((xp > 0.3).float().mean()),
        'f50': float((xp > 0.5).float().mean()),
    }
    if nn_y is not None:
        out['dis_far'] = float(((pred != y) & (pred != nn_y)).float().mean())
        nn_all = torch.tensor([nn[k] for k in range(P.shape[1])])
        merged = P + P[:, nn_all]                       # P(k or nn(k)) for every class k
        obs = (-merged[idx, y].clamp_min(eps).log()).clamp(max=NLL_CLIP)
        exp_ = (P * (-merged.clamp_min(eps).log()).clamp(max=NLL_CLIP)).sum(dim=1)
        out['xs_m'] = float((obs - exp_).mean())
        # xs_mb: Eq. 4 with the merged P-bar also as the weights of the expected term (not normalised;
        # the weights sum to 1 + sum_k P_nn(k), about 2) - user's comparison run 2026-11-24
        exp_b = (merged * (-merged.clamp_min(eps).log()).clamp(max=NLL_CLIP)).sum(dim=1)
        out['xs_mb'] = float((obs - exp_b).mean())
    return out


def _nearest(client):
    nb = getattr(client, 'far_neighbours', None)
    if not nb:
        return None
    return [min(s) if s else k for k, s in enumerate(nb)]   # k = 1: one neighbour per class


def diag_before(client):
    """Scores of the received global prompt (g), zero-shot CLIP (z) and their mix (e)."""
    st = _rng_state()
    try:
        view = _pristine_view(client)
        if len(view.samples) == 0:
            return None
        every = int(getattr(client.args, 'diag_samples_every', 0))
        dump = bool(every) and client.rounds % every == 0
        full = dump and getattr(client.args, 'diag_full_probs', 'false') == 'true'
        if full:
            pg, pz, lg, lz = _probs(client, view, with_zs=True, with_log=True)
        else:
            pg, pz = _probs(client, view, with_zs=True)
        y = torch.tensor(view.targets)
        clean = torch.tensor([int(t) for t in view.clean_targets])
        nn = _nearest(client)
        rep = {'n': len(y), 'noise': round(float((y != clean).float().mean()), 4),
               'g': _scores(pg, y, nn), 'lid_g': _lid(pg)}
        if pz is not None:
            pe = 0.5 * (pg + pz)
            rep['z'] = _scores(pz, y, nn)
            rep['e'] = _scores(pe, y, nn)
        if dump:
            # one row per image, columns in DIAG_ROW_COLUMNS (z / e / nn columns are None when
            # zero-shot CLIP or the neighbour map is unavailable)
            def stats(P, i, yi):
                p = P[i]
                return [round(float(p[yi]), 4), int(p.argmax()), round(float(p.max()), 4),
                        round(float(-(p * p.clamp_min(1e-12).log()).sum()), 4),
                        round(float((p * p).sum()), 4),
                        round(float(p[nn[yi]]), 4) if nn is not None else None]
            pe_ = 0.5 * (pg + pz) if pz is not None else None
            rows = []
            for i in range(len(y)):
                yi = int(y[i])
                row = [yi, int(clean[i])] + stats(pg, i, yi)
                row += stats(pz, i, yi) if pz is not None else [None] * 6
                row += stats(pe_, i, yi) if pe_ is not None else [None] * 6
                if full:
                    # --diag_full_probs: every class's log-probability under g and under z, so
                    # rules that need the whole distribution (temperature, margins) can be
                    # screened offline (results/side-research/referee_calib/margin_plan.md)
                    row += [[round(float(v), 3) for v in lg[i]],
                            [round(float(v), 3) for v in lz[i]] if lz is not None else None]
                rows.append(row)
            client.diag_rows = rows
            if full:
                rep['nn'] = nn       # the look-alike map, for merged variants of the rules
        else:
            client.diag_rows = None
        return rep
    finally:
        _rng_restore(st)


def diag_after(client, rep):
    """Adds the trained local prompt's scores (l) and its LID, the quantity FedCorr uses."""
    if rep is None:
        return None
    st = _rng_state()
    try:
        view = _pristine_view(client)
        pl, _ = _probs(client, view, with_zs=False)
        y = torch.tensor(view.targets)
        rep['l'] = _scores(pl, y, _nearest(client))
        rep['lid_l'] = _lid(pl)
        for k in ('g', 'z', 'e', 'l'):
            if k in rep:
                rep[k] = {m: (round(v, 5) if isinstance(v, float) and math.isfinite(v) else v)
                          for m, v in rep[k].items()}
        for k in ('lid_g', 'lid_l'):
            if rep.get(k) is not None:
                rep[k] = round(rep[k], 4)
        return rep
    finally:
        _rng_restore(st)
