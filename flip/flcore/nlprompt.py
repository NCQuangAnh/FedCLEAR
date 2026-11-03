"""NLPrompt (Pan et al., CVPR 2025) run on every client of the federation (`--nlprompt uniform|hist`).

Follows the official code (github.com/qunovo/NLPrompt, trainers/nlprompt.py and utils.py), with
its default settings (train.py: USE_OT, CURRICLUM_EPOCH 0 so every sample is selected,
PMODE 'logP', REG_E 0.01). Before each local epoch, i.e. every round here:

  1. out = softmax(logit_scale * cos(image feature, text feature of the current prompt))
  2. P = log_softmax(out)                                   (PMODE 'logP', as in the code)
  3. coupling = Sinkhorn(a = uniform over samples, b = uniform over classes, cost = -P, reg 0.01)
  4. pseudo label = argmax of each sample's row of the coupling
  5. clean = pseudo label == given label -> cross-entropy; the rest -> GCE with q = 1, i.e.
     1 - p(label), the MAE loss of the paper (the code's `gce_loss = GeneralizedCrossEntropy(q=1.0)`)

Federated adaptation, stated so it can be judged:
- the OT runs on each client's own data with the global prompt it just received; nothing extra
  is sent;
- the official code trains a pass over the clean subset with CE, then a pass over the noisy subset
  with MAE; here one pass mixes them per sample (CE or MAE chosen by the split), as the client
  trains one epoch per round;
- `--nlprompt uniform` keeps NLPrompt's uniform class marginal b. Under Dirichlet 0.1 a client holds
  a few classes, so a uniform b pushes pseudo labels toward classes the client does not have.
  `--nlprompt hist` uses the client's own label histogram as b, the natural federated version,
  so NLPrompt is not judged only on an assumption the federated setting breaks.

The split rides on `sample_weights`: +1 = clean (CE), -1 = noisy (MAE); see ClientFedAvg._weighted.
"""
import math

import torch

from .diag import _pristine_view, _rng_restore, _rng_state
from torch.utils.data import DataLoader


def sinkhorn_log(M, a, b, reg, iters=1000, tol=1e-6):
    """Entropic OT coupling for cost M (n x C) and marginals a (n), b (C), in the log domain."""
    K = -M / reg
    log_a, log_b = a.log(), b.log()
    f = torch.zeros_like(a)
    g = torch.zeros_like(b)
    for _ in range(iters):
        f_prev = f
        f = log_a - torch.logsumexp(K + g[None, :], dim=1)
        g = log_b - torch.logsumexp(K + f[:, None], dim=0)
        if torch.max(torch.abs(f - f_prev)) < tol:
            break
    return torch.exp(K + f[:, None] + g[None, :])


@torch.no_grad()
def nlprompt_split(client):
    """Split this client's data into OT-clean (CE) and OT-noisy (MAE) for the coming round."""
    mode = getattr(client.args, 'nlprompt', 'none')
    ds = client.trainloader.dataset
    if not hasattr(ds, 'all_samples'):
        ds.all_samples = list(ds.samples)
        ds.all_clean = list(getattr(ds, 'clean_targets', [t for _, t in ds.samples]))
    ds.samples = list(ds.all_samples)
    ds.clean_targets = list(ds.all_clean)
    ds.targets = [t for _, t in ds.samples]
    ds.sample_weights = None
    st = _rng_state()
    try:
        view = _pristine_view(client)
        n = len(view.samples)
        if n == 0:
            return None
        loader = DataLoader(view, batch_size=client.trainloader.batch_size, shuffle=False,
                            num_workers=0, drop_last=False)
        out = torch.cat([client.model(b[0].to(client.device), None, test=True).float().softmax(-1).cpu()
                         for b in loader]).double()
    finally:
        _rng_restore(st)
    y = torch.tensor(view.targets)
    C = out.shape[1]
    P = torch.log_softmax(out, dim=1)
    a = torch.full((n,), 1.0 / n, dtype=torch.float64)
    if mode == 'hist':
        cnt = torch.bincount(y, minlength=C).double()
        b = (cnt + 1e-6) / (cnt + 1e-6).sum()
    else:
        b = torch.full((C,), 1.0 / C, dtype=torch.float64)
    Q = sinkhorn_log(-P, a, b, reg=float(getattr(client.args, 'nlprompt_reg', 0.01)))
    pseudo = Q.argmax(dim=1)
    clean_mask = pseudo == y
    ds.sample_weights = [1.0 if bool(c) else -1.0 for c in clean_mask]
    truth = torch.tensor([int(t) for t in view.clean_targets])
    noisy_true = y != truth
    return {'n': n, 'noise': round(float(noisy_true.float().mean()), 4),
            'clean_split': int(clean_mask.sum()),
            'clean_split_truly_clean': int((clean_mask & ~noisy_true).sum()),
            'noisy_split_truly_noisy': int((~clean_mask & noisy_true).sum()),
            'pseudo_right': int((pseudo == truth).sum())}
