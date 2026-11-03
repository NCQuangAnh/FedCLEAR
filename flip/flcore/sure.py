"""Surprise-based noisy-client recognition and repair (`--sure true`, gate D stage 2).

Every round each client, before training, scores its own data (its given labels, every image)
against P, the average of the global prompt's prediction and frozen zero-shot CLIP's:

  score  = mean over images of the excess surprise of the label, with the label merged with its
           nearest class in CLIP's text space (flcore/diag.py, `xs_m`). It sits near 0 for a
           client whose labels are right, however hard or rare its classes, and rises with the
           share of wrong labels, so one fixed threshold works on every dataset.
  flag   = score > --sure_tau. The client reports the score and the flag (two numbers).

A flagged client repairs itself: an image whose label gets P(label) < --sure_img_thr is a
suspect; it is relabelled to P's top class when P is at least --sure_relabel_conf sure, and
left out of this round's training otherwise. An unflagged client trains on its data untouched.
Rescored every round from the original data, so a wrong call is undone the next round.

Settings were fixed on Pets in stage 1 (results/side-research/gate_D/D1_results.md): tau = the
95th percentile of honest clients' scores in the all-clean federation; image threshold and
relabel confidence from the per-image logs of the careless clients.

--sure_budget excess (gate D stage 3) caps a flagged client's suspects at the number it has
beyond what P expects for correct labels (see sure_round). --sure_unsure keep leaves a suspect
that cannot be relabelled confidently in the training set instead of dropping it.

Ablations: --sure_dist g (no zero-shot mix), --sure_score dis / xs (old disagreement, or no
look-alike merge), --sure_scope all (repair every client, no client-level decision).

--sure_audit true (CLEAR-FPL v2, results/side-research/clear2/clear2_plan.md) replaces the score,
tau, the image threshold and the cap. The client estimates its own noise rate from zero-shot
CLIP alone (report/clear2_theory.md): with p = zero-shot probabilities and m_i the probability of
image i's given label (merged with its nearest class under --sure_audit_merge true),

  rho = sum_i (S_i - m_i) / sum_i (S_i - c_i),  S_i = E_{k~p_i}[m_ik],  c_i = (M_i - S_i) / (K - 1),

the method-of-moments estimate under symmetric noise, unbiased when zero-shot CLIP is calibrated.
The client is flagged when rho / se > z_(1 - alpha) (one-sided test, --sure_audit_alpha), and then
repairs its round(rho * n) least zero-shot-plausible images: relabelled to P's top class when P is
--sure_relabel_conf sure, left out of the round otherwise. Zero-shot CLIP and the data never
change, so the estimate, the flag and the chosen images are computed once.

--sure_cal noise (results/side-research/calrepair/calrepair_plan.md) calibrates P once per round
before any client repairs. Each client's labels are modelled as (1 - eps) Cat(P^(1/T)) +
eps Uniform(K); for every T on CAL_T_GRID the client takes its own best eps and sends that profile
log-likelihood (cal_profile, 25 numbers). The server adds the clients' profiles and broadcasts the
best T (cal_pick). A wrong label is absorbed by eps rather than by softening P, so noisy clients do
not drag T, and a federation where every client is noisy still gets one. With P_T = P^(1/T):
  - a client is also flagged when xs_m on P_T exceeds --sure_cal_tau (its Pets-clean p95); every
    client the uncalibrated score flags stays flagged;
  - a flagged client's suspects are the images whose label lies outside P_T's (1 - alpha)
    prediction set, sum_k P_T,k [P_T,k <= P_T,label] < --sure_cal_alpha. This replaces
    --sure_img_thr and --sure_max_frac;
  - relabelling is unchanged and uses the uncalibrated P (top class, --sure_relabel_conf).
--sure_cal_flag false drops the extra flag on the calibrated score.

--sure_gate g (results/side-research/calrepair/gate_confirm_plan.md) makes the switch to --sure_cal
conditional on the referee's strength. The run is plain CLEAR-FPL for rounds 0..R
(--sure_gate_rounds). After round R the server adds the suspects and relabelled counts the clients
reported in rounds 1..R. Relabelled / suspects is the share of suspects where P names another class
at least --sure_relabel_conf sure; it is high where CLIP is a strong referee and near 0 where it is
weak (EuroSAT). If its one-sided 95% Wilson lower bound (gate_bound) is at least g, every later
round uses --sure_cal's repair; otherwise the run stays CLEAR-FPL. The decision is made once.

--sure_cal_tmax 1 (results/side-research/calrepair/gatec_plan.md) caps the broadcast temperature:
T = min(fitted T, 1). In the gated Pets N pair75 runs the fit went to the grid ceiling (T = 2) when
the global prompt had absorbed the wrong labels: the uniform-noise model explains such labels by
softening P rather than by eps, the prediction sets widen, fewer wrong labels are suspected, and the
prompt absorbs more of them on the next round. P is already softened by the zero-shot mix, so the
cap never lets the calibration soften it further. The fitted value is still logged (T_fit).

--sure_cal_floor true (results/side-research/calrepair/gatef_plan.md) gives a flagged client a
minimum number of suspects: round(eps0 * n), with eps0 its own noise estimate (the best eps above)
frozen at its first calibrated round. Where CLIP is a weak referee (DTD) the prediction sets are wide
and a client suspects far fewer images than it estimates are wrong; it then adds the images whose
labels are least plausible under P_T (smallest p-value, then smallest P_T(label)) up to that number.
eps0 is frozen because eps drifts down once the prompt has absorbed wrong labels.
"""
import math
import torch

from .diag import _nearest, _pristine_view, _probs, _rng_restore, _rng_state, _scores

CAL_T_GRID = [round(math.exp(math.log(0.1) + i * (math.log(2.0) - math.log(0.1)) / 24), 3)
              for i in range(25)]
CAL_EPS = torch.linspace(0, 0.95, 96, dtype=torch.float64)


def _zero_shot(client, view):
    """Zero-shot CLIP never changes and the scoring transform is deterministic: compute once."""
    cache = getattr(client, '_sure_pz', None)
    if cache is None or cache.shape[0] != len(view.samples):
        _, pz = _probs(client, view, with_zs=True)
        client._sure_pz = pz
    return client._sure_pz


def _audit(pz, y, nn, merge):
    """Noise-rate estimate, its standard error and each image's plausibility under zero-shot CLIP."""
    n, K = pz.shape
    idx = torch.arange(n)
    if merge and nn is not None:
        nn_all = torch.tensor([nn[k] for k in range(K)])
        other = (nn_all != torch.arange(K)).float()
        mk = pz + pz[:, nn_all] * other                 # P(k or its nearest class), per class k
    else:
        mk = pz
    m = mk[idx, y]                                      # observed: the given label
    S = (pz * mk).sum(dim=1)                            # expected for a label drawn from p
    c = (mk.sum(dim=1) - S) / (K - 1)                   # expected for a uniformly wrong label
    D = float((S - c).mean())
    t = (S - m) / D
    rho = float(t.mean())
    se = float(t.std(unbiased=False)) / math.sqrt(n)
    return rho, se, m


def _audit_plan(client, pz, y, args):
    """Flag and chosen images, computed once per client (zero-shot CLIP and the data are fixed)."""
    cache = getattr(client, '_audit_plan', None)
    if cache is not None and cache['n'] == len(y):
        return cache
    rho, se, m = _audit(pz, y, _nearest(client), getattr(args, 'sure_audit_merge', 'false') == 'true')
    alpha = float(getattr(args, 'sure_audit_alpha', 0.05))
    zcrit = float(torch.distributions.Normal(0., 1.).icdf(torch.tensor(1. - alpha)))
    flag = se > 0 and rho / se > zcrit
    budget = int(round(min(max(rho, 0.), 1.) * len(y))) if flag else 0
    chosen = sorted(range(len(y)), key=lambda i: float(m[i]))[:budget]
    client._audit_plan = {'n': len(y), 'rho': rho, 'se': se, 'flag': bool(flag), 'chosen': chosen}
    return client._audit_plan


def _referee(client, view):
    """CLEAR-FPL's P on the client's pristine data: the global prompt mixed with zero-shot CLIP."""
    pg, _ = _probs(client, view, with_zs=False)
    pz = None
    if getattr(client.args, 'sure_dist', 'e') == 'e' or getattr(client.args, 'sure_audit', 'false') == 'true':
        pz = _zero_shot(client, view)
    if getattr(client.args, 'sure_dist', 'e') == 'e':
        return 0.5 * (pg + pz) if pz is not None else pg
    return pg


def _temper(P, T):
    """log of P^(1/T), renormalised, in float64."""
    z = P.double().clamp_min(1e-30).log() / T
    return z - torch.logsumexp(z, dim=1, keepdim=True)


def _cal_ll(P, y, T):
    """Log-likelihood of the labels under (1 - eps) P^(1/T) + eps / K for every eps on CAL_EPS."""
    K = P.shape[1]
    py = _temper(P, T)[torch.arange(len(y)), y].exp()
    return torch.log((1 - CAL_EPS)[None] * py[:, None] + CAL_EPS[None] / K).sum(dim=0)


def cal_profile(client):
    """The client's profile log-likelihood on CAL_T_GRID (its best eps at each T), from the same P
    sure_round will use; every RNG is restored, so training is not affected."""
    st = _rng_state()
    try:
        view = _pristine_view(client)
        if len(view.samples) == 0:
            return None
        P = _referee(client, view)
        y = torch.tensor(view.targets)
        return [float(_cal_ll(P, y, T).max()) for T in CAL_T_GRID]
    finally:
        _rng_restore(st)


def cal_pick(profiles):
    """The server's temperature: the best T for the summed profiles (1.0 when there are none)."""
    profiles = [p for p in profiles if p is not None]
    if not profiles:
        return 1.0
    tot = [sum(p[i] for p in profiles) for i in range(len(CAL_T_GRID))]
    return CAL_T_GRID[max(range(len(tot)), key=tot.__getitem__)]


def gate_bound(relabeled, suspects, z=1.645):
    """One-sided 95% Wilson lower bound of relabeled / suspects (None without suspects)."""
    if not suspects:
        return None
    p, n = relabeled / suspects, suspects
    centre = p + z * z / (2 * n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (centre - half) / (1 + z * z / n)


def sure_round(client):
    """Score, flag and (if flagged) repair this client's training set for the coming round."""
    args = client.args
    ds = client.trainloader.dataset
    if not hasattr(ds, 'all_samples'):
        ds.all_samples = list(ds.samples)
        ds.all_clean = list(getattr(ds, 'clean_targets', [t for _, t in ds.samples]))
    st = _rng_state()
    try:
        view = _pristine_view(client)
        n = len(view.samples)
        if n == 0:
            return None
        pg, _ = _probs(client, view, with_zs=False)
        pz = None
        if getattr(args, 'sure_dist', 'e') == 'e' or getattr(args, 'sure_audit', 'false') == 'true':
            pz = _zero_shot(client, view)
        if getattr(args, 'sure_dist', 'e') == 'e':
            P = 0.5 * (pg + pz) if pz is not None else pg
        else:
            P = pg
        y = torch.tensor(view.targets)
        clean = [int(t) for t in view.clean_targets]
        score = _scores(P, y, _nearest(client)).get(getattr(args, 'sure_score', 'xs_m'))
    finally:
        _rng_restore(st)

    audit = getattr(args, 'sure_audit', 'false') == 'true'
    # --sure_gate: the server switches --sure_cal on or off per round (sure_cal_on, server_fedavg.py)
    cal = getattr(args, 'sure_cal', 'none') == 'noise' and getattr(client, 'sure_cal_on', True)
    if audit:
        if pz is None:
            raise RuntimeError('--sure_audit needs zero-shot CLIP text features')
        plan = _audit_plan(client, pz, y, args)
        score, flagged = plan['rho'], plan['flag']
    else:
        tau = float(getattr(args, 'sure_tau', 0.05))
        flagged = getattr(args, 'sure_scope', 'flagged') == 'all' or (score is not None and score > tau)
    if cal:
        # calibrated referee with the temperature the server broadcast this round (cal_pick)
        T = float(getattr(client, 'sure_T', 1.0))
        PT = _temper(P, T).exp()
        score_cal = _scores(PT.float(), y, _nearest(client)).get('xs_m')
        flag_clear = bool(flagged)
        flag_cal = (getattr(args, 'sure_cal_flag', 'true') == 'true' and score_cal is not None
                    and score_cal > float(getattr(args, 'sure_cal_tau', 0.384)))
        flagged = flag_clear or flag_cal

    ds.samples = list(ds.all_samples)
    ds.clean_targets = list(ds.all_clean)
    ds.sample_weights = None
    rep = {'score': None if score is None else round(float(score), 5), 'flag': bool(flagged), 'n': n,
           'noise': round(sum(int(t) != c for (_, t), c in zip(ds.all_samples, clean)) / n, 4),
           'suspects': 0, 'relabeled': 0, 'dropped': 0, 'fixed': 0, 'broken': 0,
           'dropped_noisy': 0, 'suspects_noisy': 0}
    if audit:
        rep.update({'se': round(plan['se'], 5), 'budget': len(plan['chosen'])})
    if cal:
        ll = _cal_ll(P, y, T)
        eps = float(CAL_EPS[int(ll.argmax())])
        if getattr(client, 'sure_eps0', None) is None:
            client.sure_eps0 = eps                      # --sure_cal_floor: frozen at the first calibrated round
        rep.update({'T': T, 'T_fit': float(getattr(client, 'sure_T_fit', T)),
                    'score_cal': None if score_cal is None else round(float(score_cal), 5),
                    'flag_clear': flag_clear, 'flag_cal': bool(flag_cal),
                    'eps': round(eps, 3), 'eps0': round(client.sure_eps0, 3)})
    if flagged:
        py = P[torch.arange(n), y]
        conf, top = P.max(dim=1)
        img_thr = float(getattr(args, 'sure_img_thr', 0.1))
        rconf = float(getattr(args, 'sure_relabel_conf', 0.5))
        sus = sorted((i for i in range(n) if float(py[i]) < img_thr), key=lambda i: float(py[i]))
        if audit:
            sus = list(plan['chosen'])                  # no threshold, no cap: the estimated count
        elif cal:
            # outside the calibrated (1 - alpha) prediction set: the classes P_T rates at most as
            # high as the label carry less than alpha of its mass. No threshold, no cap.
            pyT = PT[torch.arange(n), y]
            pval = (PT * (PT <= pyT[:, None] + 1e-12)).sum(dim=1)
            alpha = float(getattr(args, 'sure_cal_alpha', 0.05))
            sus = sorted((i for i in range(n) if float(pval[i]) < alpha), key=lambda i: float(pyT[i]))
            if getattr(args, 'sure_cal_floor', 'false') == 'true':
                # never fewer suspects than the client's own frozen noise estimate says it has
                floor = min(n, int(round(client.sure_eps0 * n)))
                rep['floor'] = floor
                if len(sus) < floor:
                    inside = set(sus)
                    rest = sorted((i for i in range(n) if i not in inside),
                                  key=lambda i: (float(pval[i]), float(pyT[i])))
                    sus = sus + rest[:floor - len(sus)]
        elif getattr(args, 'sure_budget', 'none') == 'excess':
            # Touch only as many images as the client has BEYOND what P itself expects. A label
            # drawn from P would fall below img_thr with probability sum_k P_k [P_k < img_thr];
            # summed over the images that is how many suspects a client with correct labels
            # should have. On a hard dataset that number is large, and a falsely flagged honest
            # client then gets a budget near 0 instead of losing every low-confidence image.
            expected = float((P * (P < img_thr)).sum())
            budget = max(0, int(round(len(sus) - expected)))
            rep['expected'] = round(expected, 2)
            sus = sus[:budget]
        if not audit and not cal:
            sus = sus[:int(float(getattr(args, 'sure_max_frac', 0.6)) * n)]
        new_label, drop = {}, set()
        for i in sus:
            if int(top[i]) != int(y[i]) and float(conf[i]) >= rconf:
                new_label[i] = int(top[i])
            elif getattr(args, 'sure_unsure', 'drop') == 'drop':
                drop.add(i)       # --sure_unsure keep: a suspect P is not sure about stays as it is
        rows = []
        for i, (path, lab) in enumerate(ds.all_samples):
            if i in drop:
                continue
            rows.append((i, (path, type(lab)(new_label[i])) if i in new_label else (path, lab)))
        ds.samples = [r for _, r in rows]
        ds.clean_targets = [ds.all_clean[i] for i, _ in rows]
        # ground-truth audit, logged only
        rep.update({'suspects': len(sus), 'relabeled': len(new_label), 'dropped': len(drop),
                    'suspects_noisy': sum(int(y[i]) != clean[i] for i in sus),
                    'dropped_noisy': sum(int(y[i]) != clean[i] for i in drop),
                    'fixed': sum(int(y[i]) != clean[i] and p == clean[i] for i, p in new_label.items()),
                    'broken': sum(int(y[i]) == clean[i] and p != clean[i] for i, p in new_label.items())})
    ds.targets = [t for _, t in ds.samples]
    return rep
