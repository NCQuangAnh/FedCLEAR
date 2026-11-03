"""Server-side signals for telling honest, noisy and malicious clients apart.

Everything here is computed from a client's prompt alone. The server never sees client data,
never needs a clean validation set, and never touches the test set. The only extra thing it
uses is CLIP itself, which every participant already has.

The idea comes straight out of the gate results:

  * Gate A: the data of a noisy client is worth about what it costs to throw away, so noisy
    clients must be corrected and kept; malicious clients must be removed. Two opposite
    treatments, so the two must be told apart.
  * Gate B: rules that decide who to trust by how far an update deviates (Krum and friends)
    flag the noisy clients instead of the attackers, because deviation is what label noise
    produces too. Magnitude alone cannot separate them.

So the signals split into "how far" and "in what shape":

  S_sem   how far the client's class embeddings drift away from CLIP's own zero-shot
          semantics. Label noise and attacks both raise it, honest clients do not.
  S_conc  how much of that drift piles onto a single class. Symmetric label noise scatters
          mass over many classes; a targeted or noise-disguised attack concentrates it on the
          class the attacker wants. This is the one that separates noisy from malicious.
  S_upd   plain update deviation, the Krum-style signal, kept as the baseline to beat.

The probe trick: CLIP's text and image embeddings share a space, so the zero-shot text
embedding of a class stands in for an image of that class. That gives the server a probe set
with no data at all.
"""

import json

import torch

from .models.clip import clip
from .models.clip.ZSCLIP import CUSTOM_TEMPLATES
from .pretty.logger import log


@torch.no_grad()
def zero_shot_text_features(clip_model, classnames, dataset, device):
    """CLIP's own class embeddings from the hand-written template: the clean reference."""
    template = CUSTOM_TEMPLATES.get(dataset, "a photo of a {}.")
    prompts = [template.format(c.replace("_", " ")) for c in classnames]
    tokens = torch.cat([clip.tokenize(p) for p in prompts]).to(device)
    feats = clip_model.encode_text(tokens)
    return feats / feats.norm(dim=-1, keepdim=True)


@torch.no_grad()
def prompt_text_features(model, state, device):
    """Class embeddings a client's prompt produces. Restores the model's own prompt after."""
    learner = model.prompt_learner
    backup = {k: v.detach().clone() for k, v in learner.state_dict().items()}
    learner.load_state_dict({k: v.to(device) for k, v in state.items()}, strict=False)
    try:
        prompts = learner()
        feats = model.text_encoder(prompts, learner.tokenized_prompts)
        feats = feats / feats.norm(dim=-1, keepdim=True)
    finally:
        learner.load_state_dict(backup, strict=False)
    return feats.float()


def _concentration(client_feats, probe_feats, scale=100.0):
    """How much probe mass a single class attracts under this client's prompt.

    Rows are probes (one per class), columns are the client's class embeddings. A prompt that
    keeps the semantics puts the mass on the diagonal, so every column receives about 1/C. A
    prompt trained on labels that were all flipped towards class t pulls every row towards
    column t, and that column's share goes up.

    Returns the raw maximum share, the class it falls on, and two scale-free versions. The raw
    share has a 1/C floor, so it is not comparable across datasets with different class counts
    -- which is exactly the suspicion the Caltech101 run raised. `mass x C` and the KL distance
    from uniform both remove that floor.
    """
    n_prm = client_feats.shape[0] // probe_feats.shape[0]
    if n_prm > 1:       # FedOTP-style multi-prompt: average the prompts of each class
        c = probe_feats.shape[0]
        client_feats = client_feats.reshape(n_prm, c, -1).mean(0)
        client_feats = client_feats / client_feats.norm(dim=-1, keepdim=True)
    logits = scale * probe_feats @ client_feats.t()
    p = logits.softmax(dim=-1)
    column_mass = p.mean(0)
    n_cls = column_mass.shape[0]
    uniform = 1.0 / n_cls
    kl = float((column_mass * (column_mass.clamp_min(1e-12) / uniform).log()).sum())
    return (float(column_mass.max()), int(column_mass.argmax()),
            float(column_mass.max()) * n_cls, kl)


@torch.no_grad()
def client_signals(model, states, global_state, zs_feats, device):
    """Per-client signals for one round. Returns {client id: {...}}."""
    global_feats = prompt_text_features(model, global_state, device)
    g_sem = float((global_feats * zs_feats.to(global_feats.dtype)).sum(-1).mean())
    g_conc, _, g_conc_n, g_kl = _concentration(global_feats, zs_feats.float())

    flat_global = torch.cat([v.reshape(-1).float() for v in global_state.values()])
    deviations = {}
    for cid, state in states.items():
        flat = torch.cat([state[k].reshape(-1).float() for k in global_state])
        deviations[int(cid)] = float(torch.norm(flat - flat_global))
    median_dev = float(torch.tensor(list(deviations.values())).median()) or 1.0

    out = {}
    for cid, state in states.items():
        feats = prompt_text_features(model, state, device)
        sem = float((feats * zs_feats.to(feats.dtype)).sum(-1).mean())
        conc, target, conc_n, kl = _concentration(feats, zs_feats.float())
        out[int(cid)] = {
            # scale-free variants of s_conc: the raw share has a 1/C floor, these do not
            's_conc_n': round(conc_n - g_conc_n, 5),
            's_conc_kl': round(kl - g_kl, 5),
            # positive = this client drifts further from CLIP's semantics than the global model
            's_sem': round(g_sem - sem, 5),
            # positive = this client concentrates more probe mass on one class than global
            's_conc': round(conc - g_conc, 5),
            'conc_class': target,
            # the Krum-style magnitude signal, scaled by the median so rounds are comparable
            's_upd': round(deviations[int(cid)] / median_dev, 5),
        }
    return out


def log_signals(round_idx, signals, roles):
    record = {'round': round_idx,
              'clients': {str(c): {**v, 'role': roles[c] if roles else 'unknown'}
                          for c, v in sorted(signals.items())}}
    log.debug('SIGNALS ' + json.dumps(record, sort_keys=True))
    return record
