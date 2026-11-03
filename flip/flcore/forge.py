"""Gate R4: a device attacker that fabricates its prototypes (--proto_lie forge).

The prototype check (ServerBase.proto_verify) has two tests. A centroid passes if the global
prompt or CLIP's zero-shot template reads it as its label, and a client is flagged if the update
it sent points away from the update its passing centroids imply (the rebuild). An attacker that
sends honest prototypes fails the first test; one that hides its relabelled images fails the
second (gate R3). This attacker tries to pass both: it moves its centroids, starting from its
real ones, until

  (a) every centroid is read as its label by at least one of the two readers, with a margin, and
  (b) the rebuild they imply points the same way as its poisoned update.

It uses only what such an attacker has: the global prompt it was sent, its own update, the public
CLIP model and the public rule the server follows. It never sees other clients.

The rebuild is d_hat = -J^T G / sum(m), where J is the Jacobian of the class text features t
(C x D) with respect to the prompt context, and G = sum_i m_i * s * (p_i - e_{y_i}) (x) P_i
(C x D) collects the centroids. G is cheap in P; J is fixed in a round. So the cosine with the
attacker's update delta is

    cos = -<G, J delta> / (||J^T G|| * ||delta||)

and its gradient in G needs only J delta and J w with w = J^T G / ||J^T G||. Both are directional
derivatives of t, taken by central finite differences (two forward passes each, float32), and
J^T G is one backward pass, the same one the server's rebuild does. No second-order graph.
"""
import torch


def _text(server, learner, C):
    t = server.model.text_encoder(learner(), learner.tokenized_prompts).float()
    return (t / t.norm(dim=-1, keepdim=True))[:C]


@torch.no_grad()
def _jvp(server, learner, c0, direction, C, eps):
    """J @ direction (direction in ctx space, any norm), by central differences."""
    n = float(direction.norm())
    if n == 0:
        return None
    d = (direction / n).reshape(c0.shape).to(c0.dtype)
    learner.ctx.copy_(c0 + eps * d)
    tp = _text(server, learner, C)
    learner.ctx.copy_(c0 - eps * d)
    tm = _text(server, learner, C)
    learner.ctx.copy_(c0)
    return (tp - tm) / (2 * eps) * n


def _vjp(server, learner, G, C):
    """J^T @ G (G is C x D), one backward pass at the current context."""
    ctx = learner.ctx
    was = ctx.requires_grad
    ctx.requires_grad_(True)
    with torch.enable_grad():
        t = _text(server, learner, C)
        g, = torch.autograd.grad(t, ctx, grad_outputs=G)
    ctx.requires_grad_(was)
    return g.reshape(-1).float()


def data_direction(server, P, lab, mass, C):
    """The update the attacker's own (poisoned) data asks for: minus the gradient of the
    mass-weighted cross-entropy of its real centroids at the current prompt."""
    learner = server.model.prompt_learner
    scale = server.model.logit_scale.exp().float()
    ctx = learner.ctx
    was = ctx.requires_grad
    ctx.requires_grad_(True)
    with torch.enable_grad():
        t = server.model.text_encoder(learner(), learner.tokenized_prompts).float()
        t = t / t.norm(dim=-1, keepdim=True)
        ce = torch.nn.functional.cross_entropy(scale * P @ t[:C].t(), lab, reduction='none')
        gr, = torch.autograd.grad((ce * mass).sum() / mass.sum(), ctx)
    ctx.requires_grad_(was)
    return -gr.reshape(-1).float()


def server_cos(server, P, lab, mass, delta, C):
    """The cosine exactly as ServerBase.proto_verify computes it (all centroids passing)."""
    learner = server.model.prompt_learner
    scale = server.model.logit_scale.exp().float()
    ctx = learner.ctx
    was = ctx.requires_grad
    ctx.requires_grad_(True)
    with torch.enable_grad():
        t = server.model.text_encoder(learner(), learner.tokenized_prompts).float()
        t = t / t.norm(dim=-1, keepdim=True)
        logits = scale * P @ t[:C].t()
        ce = torch.nn.functional.cross_entropy(logits, lab, reduction='none')
        loss = (ce * mass).sum() / mass.sum()
        gr, = torch.autograd.grad(loss, ctx)
    ctx.requires_grad_(was)
    d = -gr.reshape(-1).float()
    return float(torch.nn.functional.cosine_similarity(d, delta.float(), dim=0))


def forge_prototypes(server, protos, delta, T, Z, scale, steps=20, lr=0.003, kappa=0.02, lam=10.0, eps=3e-3):
    """protos: [(label, centroid, mass, purity)] of the attacker's real data.
    delta: its update (flattened ctx difference). T, Z: global / zero-shot class features (C x D).
    Returns the forged list, same labels, masses and logged purities, and a small report."""
    if not protos:
        return protos, {}
    dev = server.device
    learner = server.model.prompt_learner
    C = T.shape[0]
    c0 = learner.ctx.detach().clone()
    lab = torch.tensor([p[0] for p in protos], device=dev)
    mass = torch.tensor([p[2] for p in protos], device=dev, dtype=torch.float32)
    P0 = torch.stack([p[1] for p in protos]).to(dev).float()
    onehot = torch.nn.functional.one_hot(lab, C).float()
    target = 'update'
    if delta is None or float(delta.norm()) == 0:
        delta, target = data_direction(server, P0, lab, mass, C), 'data'
    u = _jvp(server, learner, c0, delta.to(dev), C, eps)          # J delta, fixed in the round
    if u is None:
        return protos, {}
    dn = delta.norm().to(dev)

    with torch.no_grad():
        Tt = _text(server, learner, C)     # the text features the rebuild itself uses

    def G_of(P):
        p = (scale * P @ Tt.t()).softmax(dim=-1)
        return scale * ((p - onehot) * mass[:, None]).t() @ P    # C x D

    def margins(P):
        out = []
        for R in (T, Z):
            lg = scale * P @ R.t()
            own = lg.gather(1, lab[:, None]).squeeze(1)
            other = lg.masked_fill(onehot.bool(), float('-inf')).max(dim=1).values
            out.append(own - other)
        # in cosine units (logits / scale), the better of the two readers
        return torch.stack(out).max(dim=0).values / scale

    W = P0.clone().requires_grad_(True)
    opt = torch.optim.Adam([W], lr=lr)
    cos_start, best = None, None
    dvec = delta.to(dev).reshape(-1).float()
    for _ in range(steps + 1):
        P = W / W.norm(dim=1, keepdim=True)
        with torch.no_grad():
            G = G_of(P)
            jt = _vjp(server, learner, G, C)                     # J^T G
            D = jt.norm().clamp_min(1e-12)
            N = (G * u).sum()
            Jw = _jvp(server, learner, c0, jt, C, eps)           # J (J^T G), already scaled
            # f = -N / D ; df/dG = -u / D + (N / D^3) * J J^T G
            dfdG = -u / D + (N / D ** 3) * Jw
            # the exact cosine the server will compute: <J^T G, delta> needs no finite difference
            f_exact = float(-(jt @ dvec) / (D * dn))
            mg = margins(P)
            key = (float((mg > 0).float().mean()), f_exact)
            if best is None or key > best[0]:
                best = (key, P.detach().clone())
            if cos_start is None:
                cos_start = f_exact
        surrogate = (G_of(P) * dfdG).sum()                       # same gradient in P as f
        penalty = lam * torch.relu(kappa - margins(P)).mean()
        loss = -surrogate + penalty
        opt.zero_grad()
        loss.backward()
        opt.step()
    learner.ctx.data.copy_(c0)
    # keep the best centroids by the EXACT objective: most centroids passing, then cosine.
    # The finite-difference gradient only proposes the steps
    P = best[1]
    m_end = margins(P)
    out = [(int(l), P[i].cpu(), float(mass[i]), protos[i][3]) for i, l in enumerate(lab.tolist())]
    with torch.no_grad():
        G = G_of(P)
        jt = _vjp(server, learner, G, C)
        cos_end = float(-(jt @ dvec) / (jt.norm() * dn).clamp_min(1e-12))
    cs0 = server_cos(server, P0, lab, mass, delta.to(dev), C)
    cs1 = server_cos(server, P, lab, mass, delta.to(dev), C)
    rep = {'cos_start': round(cos_start, 4), 'cos_end': round(cos_end, 4),
           'srv_start': round(cs0, 4), 'srv_end': round(cs1, 4),
           'pass_end': round(float((m_end > 0).float().mean()), 3), 'target': target,
           'moved': round(float((P - P0).norm(dim=1).mean()), 4)}
    return out, rep
