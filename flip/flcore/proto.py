"""Prototype verification: recover the clean part of a device attacker's data (gate P).

A device attacker owns its machine, so its prompt update mixes what it learned from its clean 60%
with what it learned from its 40% poisoned labels, and no server-side rule can separate the two
(results/Phase_ex/L/L_results.md). Gate P changes the protocol instead. Every client also sends,
for each label it holds, up to K centroids of its CLIP image features. They are k-means clusters,
so the genuine images of a class and the images an attacker relabelled into it fall into
different clusters. It also sends each cluster's mass. Prototype sharing itself is established
(FedProto, FedPCL NeurIPS 2022). Here the server uses the prototypes to check labels:

  check    a centroid passes if the global model reads it as the label it carries (and, with
           --proto_conf, is at least that sure). The check is per (label, cluster), so it does
           not assume one target class: 1, 2 or 3 targets, or random flips, are judged alike.
  rebuild  from the centroids that pass, the server computes the update the client SHOULD have
           sent: one gradient step of the count-weighted cross-entropy at the round's global
           prompt, scaled to the round's median update norm.
  replace  a client whose verified share is low, or whose sent update points away from its
           rebuilt one, has its update replaced by the rebuilt one. That is not a punishment: the
           rebuilt update is the client's own verified data. A false positive only loses what
           centroids cannot carry (augmentations, the spread inside a class).

The frozen image encoder is what makes this cheap: features are computed once per image.

--proto_lie hide: the attacker knows which labels it flipped, so it can send prototypes of its
clean images only, while still sending its poisoned update. Then the prototypes all pass, and the
only thing that can catch it is the mismatch between what it sent and what its prototypes imply.
"""
import torch


def kmeans(x, k, iters=10, seed=0):
    """Cosine k-means on L2-normalised rows, k-means++ init, deterministic. Returns (C, assign)."""
    n = x.shape[0]
    k = max(1, min(k, n))
    g = torch.Generator().manual_seed(seed)
    idx = [int(torch.randint(n, (1,), generator=g))]
    for _ in range(1, k):
        d = (1.0 - x @ x[idx].t()).min(dim=1).values.clamp_min(0)
        if float(d.sum()) <= 1e-9:
            break
        idx.append(int(torch.multinomial(d / d.sum(), 1, generator=g)))
    C = x[idx].clone()
    for _ in range(iters):
        a = (x @ C.t()).argmax(1)
        for j in range(C.shape[0]):
            m = a == j
            if m.any():
                C[j] = x[m].mean(0)
        C = C / C.norm(dim=1, keepdim=True).clamp_min(1e-12)
    return C, (x @ C.t()).argmax(1)


def client_prototypes(client, cache, K=3, lie='none'):
    """[(label, centroid, mass, purity)] for one client's CURRENT training set.

    mass is the summed sample weight, so a softly down-weighted image counts less. purity is
    ground truth, the share of the cluster's mass whose true label is the label: it is logged for
    scoring only and feeds no decision.
    """
    ds = client.trainloader.dataset
    samples = list(ds.samples)
    clean = getattr(ds, 'clean_targets', None)
    clean = list(clean) if clean is not None else None
    sw = getattr(ds, 'sample_weights', None)
    w = [float(x) for x in sw] if sw is not None else [1.0] * len(samples)
    rows = list(range(len(samples)))
    if lie in ('hide', 'turncoat') and getattr(client, 'device_attacker', False) and clean is not None:
        rows = [i for i in rows if int(samples[i][1]) == int(clean[i])]
    by_label = {}
    for i in rows:
        if w[i] > 0:
            by_label.setdefault(int(samples[i][1]), []).append(i)
    out = []
    for lab, idx in sorted(by_label.items()):
        x = torch.stack([cache[samples[i][0]] for i in idx]).float()
        C, a = kmeans(x, K, seed=lab)
        for j in range(C.shape[0]):
            mem = [idx[t] for t in range(len(idx)) if int(a[t]) == j]
            if not mem:
                continue
            m = torch.tensor([w[i] for i in mem])
            f = torch.stack([cache[samples[i][0]] for i in mem]).float()
            cen = (f * m.unsqueeze(1)).sum(0)
            cen = cen / cen.norm().clamp_min(1e-12)
            mass = float(m.sum())
            pur = (sum(w[i] for i in mem if int(clean[i]) == lab) / mass) if clean else -1.0
            out.append((lab, cen, mass, pur))
    return out
