"""Cross-client validation: other clients score each update on their own images.

The server has no images, so for the device attacker -- which never filters, refuses the probe and
lies about its numbers -- every signal the server can compute on its own ran out on DTD, and is
only partly informative on Pets (results/Phase_ex/L/L_results.md). BaFFLe (ICDCS 2021) and
FLShield (IEEE S&P 2024) validate updates on other participants' data and REJECT the ones that
fail. Here nothing is rejected: the score only sets an aggregation weight, which recovers as soon
as the score does.

Prompt learning makes this nearly free. CLIP's image encoder is frozen, so each client computes
its images' features once, and scoring any prompt afterwards costs one text-encoder pass over the
class names plus a matrix product. In a real deployment the server sends each candidate prompt
(2,048 numbers for CoOp) to the validators, and each one returns a single number per candidate.

Two scores per candidate k, each the median over validators v != k:
  self   L_v(prompt_k) - L_v(global prompt of this round):  does k alone make v's images worse?
  loo    L_v(aggregate) - L_v(aggregate without k):          does including k make it worse?
Positive means harmful. `loo` asks the question aggregation actually faces. Under Dirichlet 0.1,
`self` also charges an honest client for forgetting classes it does not hold.

A device attacker asked to validate lies (--xval_lie smear): it reports that every candidate
hurts it. The median over validators is what that lie has to move.
"""
import torch
from torch.utils.data import DataLoader

from .signals import prompt_text_features


class _Paths(torch.utils.data.Dataset):
    def __init__(self, paths, loader, transform):
        self.paths, self.loader, self.transform = paths, loader, transform

    def __len__(self):
        return len(self.paths)

    def __getitem__(self, i):
        return self.transform(self.loader(self.paths[i]))


@torch.no_grad()
def feature_cache(server, client):
    """{image path: L2-normalised CLIP image feature}, from the deterministic test transform.

    Computed once per client per run: the encoder is frozen and the transform is fixed, so the
    features never change. Keyed by path because the filter rewrites the list of samples every
    refresh (drops, relabels), while the images themselves stay the same.
    """
    from .datasets.imageloader import augment
    ds = client.trainloader.dataset
    samples = getattr(ds, 'all_samples', None) or ds.samples
    paths = [p for p, _ in samples]
    tf = augment(server.dataset, False, server.data_transform)
    # its own generator: creating a DataLoader iterator otherwise draws from the global RNG even
    # with shuffle=False (found in phase 1), which would shift every later random draw and make
    # a logging-only run differ from the same run without logging
    dl = DataLoader(_Paths(paths, ds.loader, tf), batch_size=64, shuffle=False, num_workers=0,
                    generator=torch.Generator().manual_seed(0))
    model = server.model
    out = []
    for x in dl:
        f = model.image_encoder(x.to(server.device).type(model.dtype))
        f = f[0]    # the pooled token, exactly as CoOpCLIP.forward takes it
        out.append((f / f.norm(dim=-1, keepdim=True)).float().cpu())
    feats = torch.cat(out) if out else torch.zeros(0)
    return {p: feats[i] for i, p in enumerate(paths)}


def validator_view(client, cache):
    """The validator's CURRENT training set: after its own filter, with any relabels and soft
    weights. A validator scores on the labels it trains on, nothing more."""
    ds = client.trainloader.dataset
    feats = torch.stack([cache[p] for p, _ in ds.samples]) if ds.samples else None
    labels = torch.tensor([int(y) for _, y in ds.samples])
    w = getattr(ds, 'sample_weights', None)
    w = torch.tensor([float(x) for x in w]) if w is not None else torch.ones(len(labels))
    return feats, labels, w


@torch.no_grad()
def text_feats(server, state):
    return prompt_text_features(server.model, state, server.device).float()


@torch.no_grad()
def weighted_ce(feats, labels, w, tfeats, scale):
    logits = scale * feats.to(tfeats.device) @ tfeats.t()
    ce = torch.nn.functional.cross_entropy(logits, labels.to(tfeats.device), reduction='none')
    w = w.to(ce.device)
    return float((ce * w).sum() / w.sum().clamp_min(1e-12))
