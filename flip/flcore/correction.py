"""The correction probe: judge a client by how it *responds*, not by how far it deviates.

Gate C showed the limit of reading a client's prompt geometry. A prompt says what a client
learned; it does not say whether the client meant it. Two clients can produce the same drift
for opposite reasons, and on datasets where the prompt barely moves there is almost nothing to
read at all.

This probe asks a question instead of taking a measurement.

Every `--correction_every` rounds the server asks each client to do one extra pass in which its
own labels are replaced by the global model's predictions, and to return both the resulting
prompt and the loss before and after. The point is not the loss number, which anyone can make
up, but the *prompt* that comes back with it:

  * an honest client with noisy labels genuinely benefits. Its wrong labels are replaced by
    something closer to the truth, so the extra pass pulls its prompt back towards the global
    one and whatever accidental structure its noise created gets weaker.
  * a malicious client cannot comply, because complying deletes the attack: the corrections
    come from the global model, which does not share the attacker's target. It must either
    refuse (and return a prompt that still leans on its target class) or claim a loss drop that
    its returned prompt does not support.

So the server checks the claim against the evidence, and neither side of that check needs the
client's data. Three signals come out:

  r_gain       the loss drop the client reports. On its own, unverifiable.
  r_align      how closely the corrected pass follows the direction of the update the client is
               having aggregated this round. The reference is the server's own copy of that
               update, not a second thing the client sent, so the client cannot choose both
               sides of the comparison.
  r_conc_drop  how much the concentration signal fell after correction. A difference between
               two states of the same client, so the 1/C floor that made s_conc incomparable
               across datasets largely cancels.

`r_gain` times `r_align` is the lie detector. An honest clean client has little to gain. An
honest noisy client gains a lot and visibly changes course. Only a client that claims the gain
while carrying on exactly as before scores high on both.
"""

import copy
import json

import torch

from .pretty.logger import log


@torch.no_grad()
def pseudo_labels(model, data, precision='amp'):
    """The global model's prediction for each sample, and how sure it is.

    The confidence is what the first version was missing. Overwriting EVERY label with the
    global model's guess means overwriting correct labels too, and on a dataset where the
    global model is only about as accurate as the noisy client it is correcting, that trade is
    roughly break-even: DTD's global model sits near 52% while a client at 40% symmetric noise
    still has 60% of its labels right. You cannot correct a student above the teacher, but you
    can at least stop the teacher from overwriting the answers the student already had right.
    """
    if precision == 'amp':
        with torch.cuda.amp.autocast():
            output = model(data, None, test=True)
    else:
        output = model(data, None, test=True)
    prob = output.float().softmax(dim=-1)
    conf, pred = prob.max(dim=-1)
    return pred.detach(), conf.detach()


def gate_corrections(proposals, conf_thr, mode):
    """Keep the client's own label wherever the global model is not sure enough.

    `mode='quantile'` is the default because it needs no per-dataset tuning: CLIP logits carry
    a learned scale near 100, so absolute softmax values are wildly different between datasets
    and an absolute threshold that works on Pets is meaningless on DTD. The quantile is taken
    over one client's whole training set, so each client calibrates against itself.

    Returns the number of labels actually replaced, for the log line.
    """
    if conf_thr <= 0:
        # off: every label is replaced, which is what gate E and gate F measured
        return sum(int((c != t).sum()) for _, t, c, _ in proposals)
    if mode == 'quantile':
        allc = torch.cat([conf.reshape(-1) for *_, conf in proposals])
        # conf_thr = fraction of samples to LEAVE ALONE, so 0.5 relabels the surest half
        cut = float(torch.quantile(allc.float(), min(max(conf_thr, 0.0), 1.0)))
    else:
        cut = conf_thr
    replaced = 0
    for i, (data, target, corrected, conf) in enumerate(proposals):
        keep = conf < cut
        used = torch.where(keep, target, corrected)
        replaced += int((used != target).sum())
        proposals[i] = (data, target, used, conf)
    return replaced


@torch.no_grad()
def audit_correction_quality(client, conf_thr, conf_mode):
    """Diagnostic only: is the correction actually better than the labels it overwrites?

    The whole repair idea rests on an assumption nobody has measured: that the global model's
    guess beats the client's label. On DTD the global model sits near 52% while a client at 40%
    symmetric noise still has 60% of its labels right, so the assumption may simply be false.

    Uses `clean_targets`, the ground truth the noise injector kept. That makes this an OFFLINE
    measurement, never available to the server, and it never feeds the algorithm.

    Walks the client's dataset in order with shuffling off so sample i lines up with
    clean_targets[i]. One forward pass, no backward, so the cost is seconds.
    """
    from torch.utils.data import DataLoader

    ds = client.trainloader.dataset
    clean = getattr(ds, 'clean_targets', None)
    if clean is None:
        return None
    loader = DataLoader(ds, batch_size=client.trainloader.batch_size,
                        shuffle=False, num_workers=0, drop_last=False)
    trained = copy.deepcopy(client.model.prompt_learner).state_dict()
    client.model.prompt_learner.load_state_dict(
        {k: v.to(client.device) for k, v in client.init_state.items()}, strict=False)
    preds, confs, given = [], [], []
    for batch in loader:
        data, target = batch[0], batch[1]
        p, c = pseudo_labels(client.model, data.to(client.device), client.precision)
        preds.append(p.cpu()), confs.append(c.cpu()), given.append(target.cpu())
    client.model.prompt_learner.load_state_dict(trained, strict=False)
    pred = torch.cat(preds); conf = torch.cat(confs); lab = torch.cat(given)
    true = torch.tensor([int(t) for t in clean[:len(lab)]])   # np.str_ when no noise was injected
    if conf_thr > 0:
        cut = (float(torch.quantile(conf.float(), min(max(conf_thr, 0.0), 1.0)))
               if conf_mode == 'quantile' else conf_thr)
        use = conf >= cut
    else:
        use = torch.ones_like(conf, dtype=torch.bool)
    dirty = lab != true                      # the samples noise or the attack actually damaged
    out = {
        'n': int(len(lab)),
        'coverage': round(float(use.float().mean()), 4),
        'conf_used': round(float(conf[use].mean()) if int(use.sum()) else 0.0, 4),
        'label_acc': round(float((lab == true).float().mean()), 4),
        'teacher_acc': round(float((pred == true).float().mean()), 4),
        'teacher_acc_used': round(float((pred[use] == true[use]).float().mean())
                                  if int(use.sum()) else 0.0, 4),
        # what the correction does where it is actually applied
        'fixed': int(((pred == true) & (lab != true) & use).sum()),      # was wrong, now right
        'broken': int(((pred != true) & (lab == true) & use).sum()),     # was right, now wrong
        'still_wrong': int(((pred != true) & (lab != true) & use).sum()),
        'kept_right': int(((pred == true) & (lab == true) & use).sum()),
        'n_dirty': int(dirty.sum()),
    }
    out['net'] = out['fixed'] - out['broken']
    return out


@torch.no_grad()
def sample_diagnostic(client):
    """Per-sample evidence for the question the oracle ladder left open.

    `L_drop` recovered 6.02 of the 8.39 available points by DELETING exactly the damaged
    samples. Deleting needs only a yes/no judgement per sample, which is a far easier problem
    than naming the right label out of 47 -- and it is the problem nobody here has measured.

    So log, for every sample, each candidate signal side by side with the ground truth:

      loss     the client's own training loss on its own label. A wrong label is one the model
               keeps failing to fit, which is the standard small-loss criterion and the one
               tool from the noisy-label literature this project has never tried.
      conf     how sure the GLOBAL model is, and whether it agrees with the client's label.
      self     whether the client's OWN trained model agrees with its own label. A client that
               cannot fit its own label after a full epoch is holding a suspect sample.
      cls      the label itself, so per-class disagreement inside one client can be computed
               offline -- a poisoned class sits near zero agreement while a normal one sits
               near the model's average.
      dirty    ground truth, from clean_targets. Offline only, never seen by any rule.

    Temporal consistency needs no extra field: the same sample is logged every probe round, so
    stability is recovered by grouping on (client, index) afterwards.
    """
    from torch.utils.data import DataLoader

    ds = client.trainloader.dataset
    clean = getattr(ds, 'clean_targets', None)
    if clean is None:
        return None
    loader = DataLoader(ds, batch_size=client.trainloader.batch_size,
                        shuffle=False, num_workers=0, drop_last=False)
    trained = copy.deepcopy(client.model.prompt_learner).state_dict()
    global_state = {k: v.to(client.device) for k, v in client.init_state.items()}
    rows, idx = [], 0

    def forward(data, state):
        client.model.prompt_learner.load_state_dict(state, strict=False)
        if client.precision == 'amp':
            with torch.cuda.amp.autocast():
                return client.model(data, None, test=True).float()
        return client.model(data, None, test=True).float()

    for batch in loader:
        data, target = batch[0], batch[1]
        data, target = data.to(client.device), target.to(client.device)
        gl = forward(data, global_state).softmax(dim=-1)
        gconf, gpred = gl.max(dim=-1)
        cl = forward(data, trained)
        closs = torch.nn.functional.cross_entropy(cl, target, reduction='none')
        cpred = cl.argmax(dim=-1)
        for j in range(len(target)):
            rows.append({'i': idx, 'y': int(target[j]), 'd': int(target[j] != clean[idx]),
                         'loss': round(float(closs[j]), 4),
                         'gconf': round(float(gconf[j]), 4),
                         'gok': int(gpred[j] == target[j]),
                         'sok': int(cpred[j] == target[j])})
            idx += 1
    client.model.prompt_learner.load_state_dict(trained, strict=False)
    return rows


@torch.no_grad()
def refresh_sample_filter(client, baseline):
    """Decide, on the client, which of its own samples to stop training on.

    The oracle ladder said deleting exactly the damaged samples is worth +6.02 of the 8.39
    points available, so the whole remaining problem is a yes/no call per sample. The offline
    scoring of the diagnostic run said which calls are possible:

      class disagreement   within one client, the fraction of a CLASS's samples the global
                           model contradicts. A poisoned class sits near 1.0 while an ordinary
                           class sits near the model's own error rate. Caught 100% of the
                           attack's samples and touched only 7.1% of an honest client's data.
      loss ranking         a wrong random label is one the model keeps failing to fit. AUC 0.92
                           on careless clients and 0.53 on malicious ones -- a targeted attack
                           is CONSISTENT, so it is easy to fit and small-loss is blind to it.
                           The two rules cover each other's blind spot.

    How much to cut is not fixed: each client estimates its own contamination from how far its
    disagreement sits above `baseline`, the median across clients that the server broadcasts.
    On the diagnostic run that estimate gave exactly 0.00 for all five honest clients and a
    positive value for all five damaged ones.

    Nothing here uses labels the client does not already have, and the only thing that crosses
    the wire is one scalar per client per probe round.
    """
    from torch.utils.data import DataLoader

    mode = getattr(client.args, 'sample_filter', 'none')
    ds = client.trainloader.dataset
    if not hasattr(ds, 'all_samples'):
        ds.all_samples = list(ds.samples)
        ds.all_clean = list(getattr(ds, 'clean_targets', [t for _, t in ds.samples]))
    # always score the pristine set, so a sample dropped once can come back
    ds.samples = list(ds.all_samples)
    ds.clean_targets = list(ds.all_clean)
    ds.targets = [t for _, t in ds.samples]
    ds.sample_weights = None
    if mode == 'none':
        return None

    loader = DataLoader(ds, batch_size=client.trainloader.batch_size,
                        shuffle=False, num_workers=0, drop_last=False)
    trained = copy.deepcopy(client.model.prompt_learner).state_dict()
    global_state = {k: v.to(client.device) for k, v in client.init_state.items()}
    loss_of, agree, labels, t_pred, t_conf, t_top = [], [], [], [], [], []
    # --sample_filter proto also needs each image's feature and the global model's full
    # probability vector; nothing else changes, so the other modes stay byte-identical
    want_proto = mode == 'proto'
    feats, g_prob = [], []
    for batch in loader:
        data, target = batch[0], batch[1]
        data, target = data.to(client.device), target.to(client.device)
        client.model.prompt_learner.load_state_dict(global_state, strict=False)
        g = client.model(data, None, test=True).float()
        client.model.prompt_learner.load_state_dict(trained, strict=False)
        c = client.model(data, None, test=True).float()
        loss_of += torch.nn.functional.cross_entropy(c, target, reduction='none').tolist()
        agree += (g.argmax(dim=-1) == target).int().tolist()
        labels += target.tolist()
        gp = g.softmax(dim=-1)
        t_conf += gp.max(dim=-1).values.tolist()
        t_pred += gp.argmax(dim=-1).tolist()
        tv, ti = gp.topk(min(3, gp.shape[-1]), dim=-1)
        t_top += [list(zip(a, b)) for a, b in zip(ti.tolist(), tv.tolist())]
        if want_proto:
            f = client.model.image_encoder(data.type(client.model.dtype))[0].float()
            feats.append((f / f.norm(dim=-1, keepdim=True)).cpu())
            g_prob.append(gp.cpu())
    client.model.prompt_learner.load_state_dict(trained, strict=False)

    n = len(labels)

    def with_samples(report, suspects):
        if dis_far is not None:
            report['dis_far'] = round(dis_far, 5)
        # --filter_relabel_log: one row per sample, [label, true label, suspect?, hard round?,
        # [[class, prob] x3]], so other relabel rules can be scored offline on the same
        # suspects. Ground truth is logged for that scoring only and feeds nothing
        if getattr(client.args, 'filter_relabel_log', 'false') == 'true':
            hard = int(not soft)
            report['samples'] = [[int(labels[i]), int(ds.all_clean[i]), int(i in suspects), hard,
                                  [[int(k), round(float(p), 4)] for k, p in t_top[i]]]
                                 for i in range(n)]
        return report

    mean_dis = 1.0 - (sum(agree) / n if n else 0.0)
    # --filter_dis far: the client-level score skips disagreements that land on a look-alike
    # class of the label (nearest in CLIP's zero-shot text space). Both scores are reported;
    # the server takes its mode baseline from mean_dis and the budget baseline from dis_far
    dis_far = None
    nb = getattr(client, 'far_neighbours', None)
    if nb is not None and n:
        dis_far = sum(1 for i in range(n) if t_pred[i] != labels[i]
                      and t_pred[i] not in nb[labels[i]]) / n
    if getattr(client.args, 'filter_dis', 'all') == 'far' and dis_far is not None:
        score = dis_far
        baseline = getattr(client, 'far_baseline', None)
    else:
        score = mean_dis
    if want_proto:
        return proto_select(client, ds, labels, torch.cat(feats), torch.cat(g_prob),
                            global_state, trained, mean_dis, baseline)
    by_class = {}
    for y, a in zip(labels, agree):
        by_class.setdefault(y, []).append(a)
    cls_dis = {y: 1.0 - sum(v) / len(v) for y, v in by_class.items()}
    # contamination estimate, clipped: 0 for a client no worse than the federation's median
    rho = 0.0
    if baseline is not None and baseline < 1.0:
        rho = max(0.0, min(0.6, (score - baseline) / (1.0 - baseline)))
    # Amnesty. A client whose disagreement sits within `clean_band` of the federation's clean
    # baseline is treated as clean and nothing is touched. Measured on the diagnostic run the
    # two groups are far apart -- honest clients estimated 0.03-0.05, damaged ones 0.33-0.44 --
    # so a band of 0.10 sits in empty space. It is expressed relative to the baseline rather
    # than as an absolute number so it travels to datasets with a different error floor.
    band = float(getattr(client.args, 'filter_clean_band', 0.0))
    if band > 0 and rho <= band:
        rho = 0.0
    rho_floor = float(getattr(client.args, 'filter_rho_floor', 0.0))
    if rho > 0:
        rho = max(rho, rho_floor)      # a client already judged dirty gets at least this much
    # rho is a BUDGET, not one rule among several. The first version let the class rule drop
    # as much as it liked and the run collapsed: it took 45.3% of the honest clients' samples,
    # none of them damaged, because an absolute class threshold fires everywhere once the
    # teacher weakens -- and the teacher weakens precisely because the filter is cutting. Cut
    # more, teach worse, cut more. Making rho the cap breaks that loop at the root: a client
    # the federation sees as no worse than clean has budget zero and is never touched, however
    # bad the teacher gets.
    budget = int(round(rho * n))
    min_cls = int(getattr(client.args, 'filter_min_class', 0))
    cls_n = {y: len(v) for y, v in by_class.items()}
    # FIX 3: a class too small to judge. The global model is wrong about 45% of the time, so a
    # class holding three samples reaches 100% disagreement by luck alone -- and under
    # Dirichlet 0.1 most classes a client holds are that small. Below the threshold the class
    # rule abstains and only loss speaks.
    flagged = {y for y, d in cls_dis.items()
               if d >= float(getattr(client.args, 'filter_cls_thr', 0.9)) and cls_n[y] >= min_cls}

    soft_flag = getattr(client.args, 'filter_soft', 'false')
    if soft_flag == 'auto':
        # the server decided from the baseline it broadcast with this call; before the first
        # probe round there is no baseline and no budget either, so the value is moot
        soft = not getattr(client, 'filter_hard', False)
    else:
        soft = soft_flag == 'true'
    # FIX 2: separate budgets. Ranking both rules in one queue let the class rule push aside
    # samples the loss rule was sure about, and precision fell from 71.1% to 64.4%. Now the
    # class rule may only spend inside classes it actually flagged, and the loss rule keeps
    # the rest, so the two add up instead of diluting each other.
    if mode == 'both' and flagged:
        cls_idx = [i for i, y in enumerate(labels) if y in flagged]
        share = min(len(cls_idx), int(round(budget * len(cls_idx) / max(n, 1) * 2)))
        cls_order = sorted(cls_idx, key=lambda i: (-cls_dis[labels[i]], -loss_of[i]))
        picked = set(cls_order[:share])
        rest = sorted((i for i in range(n) if i not in picked), key=lambda i: -loss_of[i])
        order = cls_order[:share] + rest
    else:
        order = sorted(range(n), key=lambda i: -loss_of[i])

    if soft and getattr(client.args, 'filter_soft_mode', 'rank') == 'score':
        # Weights from the SCORE, not the rank. The rank ramp spaces every neighbour equally,
        # so three samples the evidence rates identically come out 0.00 / 0.10 / 0.20 while a
        # far cleaner one only reaches 0.30 -- the ranking knows the order but throws away the
        # distances. Here the raw suspicion drives the weight, and the whole vector is then
        # rescaled so the total weight removed equals the budget: the honesty of the score with
        # the safety of the cap.
        #
        # The first version of that rescale only ever SHRANK (`if removed > budget`), and the
        # loss distribution is heavy-tailed enough that min-max normalising it puts almost every
        # sample near weight 1, so the raw vector lands well UNDER budget and nothing brought it
        # back up. Measured over five seeds on DTD: the rank ramp spends its budget exactly
        # (2695 units per run) while the score version spent 2128, i.e. 79% of the same budget,
        # and lost 1.14 points (p = 0.035). That is a comparison between a full dose and a
        # three-quarter dose, not between two ways of spacing the weights -- so it never tested
        # the idea it was written to test.
        w_min = float(getattr(client.args, 'filter_w_min', 0.0))
        key = (lambda i: (cls_dis[labels[i]], loss_of[i])) if (mode == 'both' and flagged)             else (lambda i: (loss_of[i],))
        raw = [key(i)[0] for i in range(n)]
        if getattr(client.args, 'filter_score_norm', 'robust') == 'minmax':
            lo, hi = min(raw), max(raw)
            span = (hi - lo) or 1.0
            frac = [(v - lo) / span for v in raw]
        else:
            # Min-max is the wrong scale for this. One sample far out in the tail sets `hi` on
            # its own, every other sample normalises to nearly the same number, and the rescale
            # cannot separate them again however hard it pushes: on a vector of 39 equal values
            # plus one outlier it can spend at most 1.0 of a budget of 12. Median and IQR are
            # set by the bulk, so the bulk keeps its spread and the tail is simply clipped.
            #
            # Note what the lower clip does, because it looks like a bug in the logs and is not:
            # everything at or below the median gets frac 0, weight exactly 1, and no amount of
            # rescaling can touch it. So this scale can never spend more than about half a
            # client's samples -- the CPU smoke run shows budget 12 met by 9 units removed.
            # That is the rule declining to spend budget on samples it believes are clean, and
            # the exchange rate says declining is right: on a simulated client (40 samples, 12
            # damaged) at budget 12 it puts 77.1% of its weight on damaged samples against
            # 60.8% for min-max, and a min..p90 scale that always spends the full budget scores
            # 59.8%. The budget is a CEILING, not a quota. The min-max under-spend that started
            # all this was a different thing: a scale artefact, not a refusal.
            srt = sorted(raw)
            med = srt[n // 2]
            q1, q3 = srt[max(0, n // 4)], srt[min(n - 1, (3 * n) // 4)]
            iqr = (q3 - q1) or (max(raw) - min(raw)) or 1.0
            frac = [min(1.0, max(0.0, (v - med) / (2.0 * iqr))) for v in raw]
        # 1 for the least suspect sample, w_min for the most
        base_w = [1.0 - (1.0 - w_min) * f for f in frac]
        budget_w = float(budget)

        def scaled(k):
            # every penalty multiplied by k, floored at w_min so a sample is never weighted
            # below what the hard cut would leave it
            return [max(w_min, 1.0 - (1.0 - w) * k) for w in base_w]

        def spent(ws):
            return sum(1.0 - w for w in ws)

        ceiling = n * (1.0 - w_min)               # everything at w_min: nothing can spend more
        if budget_w <= 0:
            weights = [1.0] * n
        elif budget_w >= ceiling:
            weights = [w_min] * n
        else:
            # spent(scaled(k)) rises monotonically with k and saturates, so bisection lands on
            # the k that spends exactly the budget whether the raw vector started over or under
            lo_k, hi_k = 0.0, 1.0
            while spent(scaled(hi_k)) < budget_w and hi_k < 1e6:
                hi_k *= 2.0
            for _ in range(60):
                mid = 0.5 * (lo_k + hi_k)
                if spent(scaled(mid)) < budget_w:
                    lo_k = mid
                else:
                    hi_k = mid
            weights = scaled(0.5 * (lo_k + hi_k))
        removed = spent(weights)
        ds.sample_weights = weights
        damaged_w = sum((1.0 - weights[i]) for i in range(n)
                        if ds.all_samples[i][1] != ds.all_clean[i])
        log.debug(f'  client {client.client_id}: score filter rho={rho:.2f} '
                  f'removed {removed:.1f}/{n} weight ({damaged_w:.1f} from damaged)')
        return with_samples({'mean_dis': round(mean_dis, 5), 'rho': round(rho, 4),
                             'dropped': int(round(removed)), 'n': n,
                             'dropped_damaged': int(round(damaged_w))}, set(order[:budget]))
    if soft:
        # FIX 1: no cut line. Every sample keeps a weight in [w_min, 1] that falls with its
        # rank, and the budget now controls how much total weight is removed rather than how
        # many samples are deleted. A sample the ranking got wrong still contributes.
        w_min = float(getattr(client.args, 'filter_w_min', 0.0))
        # A zero budget must mean zero interference. The first version floored the ramp at one
        # sample, so a client the estimator had cleared still had its single most suspect
        # sample zeroed -- caught on CPU, where an honest client logged "removed 1.0 weight"
        # while the hard filter correctly dropped nothing.
        span = int(round(2 * budget))
        weights = [1.0] * n
        for rank, i in enumerate(order[:span]):
            frac = rank / span                       # 0 at the top of the ranking, 1 at the end
            weights[i] = w_min + (1.0 - w_min) * frac
        ds.sample_weights = weights
        removed = sum(1.0 - w for w in weights)
        damaged_w = sum((1.0 - weights[i]) for i in range(n)
                        if ds.all_samples[i][1] != ds.all_clean[i])
        log.debug(f'  client {client.client_id}: soft filter rho={rho:.2f} '
                  f'removed {removed:.1f}/{n} weight ({damaged_w:.1f} from damaged)')
        return with_samples({'mean_dis': round(mean_dis, 5), 'rho': round(rho, 4),
                             'dropped': int(round(removed)), 'n': n,
                             'dropped_damaged': int(round(damaged_w))}, set(order[:budget]))
    ds.sample_weights = None
    drop = set(order[:budget])
    # Relabel instead of delete. Deleting throws the image away; relabelling turns it back into
    # good data, and the oracle ladder priced that difference at +2.37 on DTD (restore every
    # label 55.94 vs delete every damaged image 53.58). Gate G rejected relabelling, but it
    # relabelled EVERY image on DTD, where the global model (51%) is worse than the labels it
    # overwrites (61%). On OxfordPets and Caltech101 the same audit shows the opposite -- the
    # global model is right 81% / 86% on damaged clients against labels at ~75% -- so the idea
    # was never tested where it can win.
    #
    # It lives in the hard path on purpose: under --filter_soft auto the server only chooses
    # hard once the global model is good (baseline < 0.22), so relabelling is gated by the same
    # evidence that gates deletion, and a weak teacher never gets to overwrite anything.
    # Only suspects are touched, and only where the teacher disagrees with the label; a suspect
    # the teacher agrees with keeps its deletion.
    relabel = getattr(client.args, 'filter_relabel', 'none')
    suspects = set(drop)
    new_label = {}
    if relabel == 'prior':
        # Rule A of the gate_k_diag offline test: re-rank the global model's top 3 by the
        # client's own label histogram. Under Dirichlet 0.1 a client really holds a few classes,
        # so a guess outside them is usually wrong. The histogram is capped at the median class
        # size so an attacker's target (40% of its labels) pulls no harder than an ordinary big
        # class. Offline on Pets it scored +26% over plain top-1, with the right-rate on
        # malicious clients up from 65.6% to 74.3%. If the re-ranked choice is the label itself,
        # the suspect is deleted as before.
        from collections import Counter
        counts = Counter(labels)
        nz = sorted(v for v in counts.values() if v > 0)
        cap = nz[len(nz) // 2] if nz else 1
        for i in sorted(drop):
            k = max(t_top[i], key=lambda kp: kp[1] * (min(counts.get(kp[0], 0), cap) + 1))[0]
            if k != labels[i]:
                new_label[i] = int(k)
        drop -= set(new_label)
    elif relabel != 'none':
        thr = float(getattr(client.args, 'filter_relabel_conf', 0.5))
        for i in sorted(drop):
            if t_pred[i] == labels[i]:
                continue
            if relabel == 'all' or t_conf[i] >= thr:
                new_label[i] = t_pred[i]
        drop -= set(new_label)
    # Safety cap. Measured on CPU: where the global model is no better than chance, EVERY
    # class looks contradicted and the class rule fires on the whole client -- it dropped 8 of
    # 12 samples, none of them actually damaged. On a dataset the model can learn at all this
    # never triggers (an ordinary DTD class sits near 0.45 disagreement, far under the 0.9
    # threshold), but a rule that can empty a client when the teacher is bad must not be
    # allowed to do so silently.
    cap = int(getattr(client.args, 'filter_max_frac', 0.6) * n)
    if len(drop) > cap:
        ranked = sorted(drop, key=lambda i: (-cls_dis[labels[i]], -loss_of[i]))
        drop = set(ranked[:cap])
        log.debug(f'  client {client.client_id}: filter capped at {cap}/{n}')
    keep = [i for i in range(n) if i not in drop]

    def row(i):
        path, lab = ds.all_samples[i][0], ds.all_samples[i][1]
        if i not in new_label:
            return ds.all_samples[i]
        # same type as the stored label (the few-shot split stores them as numpy strings)
        return (path, type(lab)(int(new_label[i])))

    ds.samples = [row(i) for i in keep]
    ds.clean_targets = [ds.all_clean[i] for i in keep]
    ds.targets = [t for _, t in ds.samples]
    really = sum(1 for i in drop if ds.all_samples[i][1] != ds.all_clean[i])
    # ground-truth audit of the relabelling, logged only: nothing below feeds a decision
    fixed = broken = 0
    for i, p in new_label.items():
        orig, clean = int(ds.all_samples[i][1]), int(ds.all_clean[i])
        fixed += int(orig != clean and int(p) == clean)
        broken += int(orig == clean and int(p) != clean)
    log.debug(f'  client {client.client_id}: filter {mode} rho={rho:.2f} '
              f'dropped {len(drop)}/{n} ({really} actually damaged), '
              f'relabelled {len(new_label)} (fixed {fixed}, broke {broken})')
    report = {'mean_dis': round(mean_dis, 5), 'rho': round(rho, 4),
              'dropped': len(drop), 'n': n, 'dropped_damaged': really,
              'relabeled': len(new_label), 'relabel_fixed': fixed, 'relabel_broken': broken}
    return with_samples(report, suspects)


@torch.no_grad()
def proto_select(client, ds, labels, feats, g_prob, global_state, trained, mean_dis,
                 baseline=None):
    """--sample_filter proto (gate K_proto): find suspects by CLUSTER, relabel them one by one.

    Gate P showed that a label cluster's centroid is read far more reliably than a single image:
    relabelled clusters failed the check 90-100% of the time, clean ones passed 90-94%. The
    loss-ranked filter picks suspects image by image, and that selection is where it errs.

    Here, on the client's own machine (a client that runs our code needs to send nothing):
      1. per label, k-means (K = --proto_k) on its images' CLIP features;
      2. a cluster passes if the global prompt OR CLIP's zero-shot template reads its centroid as
         the label; every image of a failing cluster is a suspect;
      3. each suspect is judged ON ITS OWN, because one cluster can mix several source classes
         (an attacker relabels images of all its classes into one target): the ensemble of the
         global and the zero-shot reading predicts its class; if that is its label it is kept,
         if confident (>= --filter_relabel_conf) it is relabelled to it, otherwise deleted.
    """
    from .proto import kmeans
    n = len(labels)
    # --proto_band true (K_proto_band): the two safeguards K_fixconf has and K_proto lacked.
    #   (a) the clean band: a client whose disagreement sits within --filter_clean_band of the
    #       federation's clean baseline is left alone, exactly as the loss filter does. K_proto
    #       checked every client and harmed ~7,200 honest label-rounds on Caltech, 20x K_fixconf.
    #   (b) the server's hard/soft decision: relabel or delete only in HARD rounds (global model
    #       judged good), with the global model as the teacher, as K_fixconf does. In SOFT rounds
    #       a suspect is only down-weighted, to the support the global and zero-shot readers give
    #       its own label.
    band_mode = getattr(client.args, 'proto_band', 'false') == 'true'
    rho = 0.0
    if baseline is not None and baseline < 1.0:
        rho = max(0.0, min(0.6, (mean_dis - baseline) / (1.0 - baseline)))
    if band_mode:
        if rho <= float(getattr(client.args, 'filter_clean_band', 0.0)):
            # untouched: the pristine set, no weights (refresh_sample_filter already reset it)
            return {'mean_dis': round(mean_dis, 5), 'rho': 0.0, 'dropped': 0, 'n': n,
                    'dropped_damaged': 0, 'relabeled': 0, 'relabel_fixed': 0,
                    'relabel_broken': 0, 'suspects': 0, 'suspects_damaged': 0,
                    'damaged': sum(1 for i in range(n)
                                   if int(ds.all_samples[i][1]) != int(ds.all_clean[i])),
                    'clusters': 0, 'fail_sources': [], 'capped': False, 'exempt': True}
        soft_flag = getattr(client.args, 'filter_soft', 'false')
        soft = (not getattr(client, 'filter_hard', False)) if soft_flag == 'auto' \
            else soft_flag == 'true'
    else:
        soft = False
    zs = getattr(client, 'zs_text_feats', None)
    learner = client.model.prompt_learner
    learner.load_state_dict(global_state, strict=False)
    t = client.model.text_encoder(learner(), learner.tokenized_prompts).float()
    learner.load_state_dict(trained, strict=False)
    Tg = (t / t.norm(dim=-1, keepdim=True)).cpu()
    scale = float(client.model.logit_scale.exp())
    Tz = zs.float().cpu() if zs is not None else Tg
    z_prob = (scale * feats @ Tz.t()).softmax(dim=-1)
    ens = 0.5 * (g_prob + z_prob)
    K = int(getattr(client.args, 'proto_k', 3))
    thr = float(getattr(client.args, 'filter_relabel_conf', 0.5))
    clean = list(ds.all_clean)
    by_label = {}
    for i, y in enumerate(labels):
        by_label.setdefault(int(y), []).append(i)
    suspects, n_clusters, fail_sources = set(), 0, []
    for lab, idx in by_label.items():
        C, a = kmeans(feats[idx], K, seed=lab)
        for j in range(C.shape[0]):
            mem = [idx[q] for q in range(len(idx)) if int(a[q]) == j]
            if not mem:
                continue
            n_clusters += 1
            ok = (int((C[j] @ Tg.t()).argmax()) == lab) or (int((C[j] @ Tz.t()).argmax()) == lab)
            if not ok:
                suspects.update(mem)
                # ground truth, logged only: how many distinct source classes the damaged
                # members of this failing cluster come from
                src = {int(clean[i]) for i in mem if int(clean[i]) != lab}
                fail_sources.append(len(src))
    if band_mode and soft:
        # soft round: nothing is relabelled or deleted; each suspect trains at the weight its own
        # label earns from the two readers
        w = [1.0] * n
        for i in suspects:
            w[i] = float(ens[i, int(labels[i])])
        ds.sample_weights = w
        sus_dmg = sum(1 for i in suspects if int(ds.all_samples[i][1]) != int(clean[i]))
        dmg = sum(1 for i in range(n) if int(ds.all_samples[i][1]) != int(clean[i]))
        removed = sum(1.0 - x for x in w)
        removed_dmg = sum(1.0 - w[i] for i in range(n)
                          if int(ds.all_samples[i][1]) != int(clean[i]))
        return {'mean_dis': round(mean_dis, 5), 'rho': round(rho, 4),
                'dropped': int(round(removed)), 'n': n,
                'dropped_damaged': int(round(removed_dmg)), 'relabeled': 0,
                'relabel_fixed': 0, 'relabel_broken': 0, 'suspects': len(suspects),
                'suspects_damaged': sus_dmg, 'damaged': dmg, 'clusters': n_clusters,
                'fail_sources': fail_sources, 'capped': False, 'exempt': False, 'soft': True}
    # hard round: K_proto_band uses the global model alone as the teacher (like K_fixconf);
    # K_proto uses the global + zero-shot average
    teach = g_prob if band_mode else ens
    new_label, drop = {}, set()
    for i in suspects:
        p = int(teach[i].argmax())
        if p == int(labels[i]):
            continue
        if float(teach[i, p]) >= thr:
            new_label[i] = p
        else:
            drop.add(i)

    # the same safety cap as the loss filter: where both readers are no better than chance (the
    # CPU smoke run, or a hopeless dataset) every cluster fails and every suspect is deleted,
    # which empties the client. Never delete more than --filter_max_frac; the deletions kept are
    # the images whose own label the readers support least
    cap = int(float(getattr(client.args, 'filter_max_frac', 0.6)) * n)
    capped = len(drop) > cap
    if capped:
        drop = set(sorted(drop, key=lambda i: float(ens[i, int(labels[i])]))[:cap])

    def row(i):
        path, lab = ds.all_samples[i][0], ds.all_samples[i][1]
        return (path, type(lab)(int(new_label[i]))) if i in new_label else ds.all_samples[i]
    keep = [i for i in range(n) if i not in drop]
    ds.samples = [row(i) for i in keep]
    ds.clean_targets = [clean[i] for i in keep]
    ds.targets = [t for _, t in ds.samples]
    ds.sample_weights = None
    really = sum(1 for i in drop if int(ds.all_samples[i][1]) != int(clean[i]))
    fixed = sum(1 for i, p in new_label.items()
                if int(ds.all_samples[i][1]) != int(clean[i]) and p == int(clean[i]))
    broken = sum(1 for i, p in new_label.items()
                 if int(ds.all_samples[i][1]) == int(clean[i]) and p != int(clean[i]))
    sus_dmg = sum(1 for i in suspects if int(ds.all_samples[i][1]) != int(clean[i]))
    dmg = sum(1 for i in range(n) if int(ds.all_samples[i][1]) != int(clean[i]))
    return {'mean_dis': round(mean_dis, 5), 'rho': round(rho, 4), 'dropped': len(drop), 'n': n,
            'dropped_damaged': really, 'relabeled': len(new_label), 'relabel_fixed': fixed,
            'relabel_broken': broken, 'suspects': len(suspects), 'suspects_damaged': sus_dmg,
            'damaged': dmg, 'clusters': n_clusters, 'fail_sources': fail_sources,
            'capped': capped, 'exempt': False, 'soft': False}


def run_correction_probe(client, comply=True, lie='mimic'):
    """One extra local pass on corrected labels, run by the client at the end of its round.

    It has to live on the client: the server never sees the data, and in FLIP the client frees
    its model as soon as the round ends. What crosses the wire is only what a client would
    really send — a prompt and two numbers.

    `comply=False` is the malicious client. It keeps its own labels, because adopting the
    server's corrections would delete its attack, and it reports the loss drop an honest client
    would have reported. Catching that is the whole point, so it has to be implemented here
    rather than merely described.
    """
    from .utils import collect_state

    trained = copy.deepcopy(client.model.prompt_learner).state_dict()
    global_state = {k: v.to(client.device) for k, v in client.init_state.items()}

    # the corrections come from the GLOBAL model, which is what makes them unusable to an
    # attacker: the global model does not share the attacker's target class
    client.model.prompt_learner.load_state_dict(global_state, strict=False)
    proposals = []
    for batch in client.trainloader:
        data, target = batch[0], batch[1]
        data = data.to(client.device)
        pred, conf = pseudo_labels(client.model, data, client.precision)
        proposals.append((data, target.to(client.device), pred, conf))
    client.model.prompt_learner.load_state_dict(trained, strict=False)
    conf_thr = float(getattr(client.args, 'correction_conf', 0.0))
    conf_mode = getattr(client.args, 'correction_conf_mode', 'quantile')
    if getattr(client.args, 'correction_labels', 'corrected') == 'own':
        # The control for the whole idea. Everything stays identical -- the extra epoch, the
        # prompt that gets returned, the audit that aggregates it -- except that the labels are
        # NOT corrected. If the accuracy gain survives this, the gain never came from repairing
        # labels; it came from the extra pass and from what aggregation does with it.
        proposals = [(d, t, t.clone(), c) for d, t, _, c in proposals]
    n_total = sum(int(t.numel()) for _, t, _, _ in proposals)
    n_replaced = gate_corrections(proposals, conf_thr, conf_mode)
    log.debug(f'  client {client.client_id}: correction replaced {n_replaced}/{n_total} labels'
              f' (conf {conf_mode} {conf_thr})')
    samples = None
    if getattr(client.args, 'sample_diag', 'false') == 'true':
        samples = sample_diagnostic(client)
    audit = None
    if getattr(client.args, 'correction_audit', 'false') == 'true':
        audit = audit_correction_quality(client, conf_thr, conf_mode)
        if audit is not None:
            log.info('CORRECTION_AUDIT ' + json.dumps(
                {'round': client.rounds, 'client': int(client.client_id), **audit},
                sort_keys=True))

    # Two extra passes from the same starting point, differing only in the labels used. One
    # pass alone tells us little: any extra training carries the prompt further along the
    # direction it was already going. The comparison is what carries the information.
    opt_state = copy.deepcopy(client.optimizer.state_dict())
    # Where the corrected pass starts from. 'chain' appends the correction to the prompt the
    # client just trained, so whatever its own labels did is already baked in: auditing such a
    # prompt aggregates one poisoned epoch plus a correction, never a clean update. 'fork'
    # restarts from the round's global prompt, so the two passes are genuine alternatives that
    # differ only in the labels.
    #
    # Fork is NOT strictly better. It very likely breaks the refusal detector: a refuser reruns
    # the same labels from the same start, so its corrected branch is a near-replica of its own
    # update and r_align goes to 1, i.e. it hides among the clean clients instead of standing
    # out at 0.43. Both modes are kept so that can be measured rather than argued.
    fork = getattr(client.args, 'probe_fork', 'chain') == 'fork'
    start = global_state if fork else trained

    def one_pass(label_of):
        client.optimizer.load_state_dict(opt_state)
        client.model.prompt_learner.load_state_dict(start, strict=False)
        losses = []
        for data, target, corrected, _ in proposals:
            used = label_of(target, corrected)
            client.optimizer.zero_grad()
            if client.precision == 'amp':
                with torch.cuda.amp.autocast():
                    loss = client.loss_func(client.model(data, used, test=False), used)
                client.scaler.scale(loss).backward()
                client.scaler.step(client.optimizer)
                client.scaler.update()
            else:
                loss = client.loss_func(client.model(data, used, test=False), used)
                loss.backward()
                client.optimizer.step()
            with torch.no_grad():
                losses.append(float(client.loss_func(
                    client.model(data, corrected, test=False), corrected)))
        state = collect_state(client.model, client.task, client.prompt_algo)
        return {k: v.cpu() for k, v in state.items()}, sum(losses) / max(len(losses), 1)

    with torch.no_grad():
        loss_before = sum(float(client.loss_func(client.model(d, t, test=False), t))
                          for d, t, _, _ in proposals) / max(len(proposals), 1)

    corr_state, loss_after = one_pass(
        (lambda target, corrected: corrected) if comply else (lambda target, corrected: target))

    if not comply:
        # Two attackers, and the second is the one worth designing against.
        #   'big'   names a large drop out of thin air. Easy to catch on the number alone.
        #   'mimic' runs the honest correction privately, reports exactly the gain it WOULD
        #           have earned, and sends back the prompt trained on its own labels. Its
        #           report is then indistinguishable from an honest client's, so the number
        #           carries no information at all and only the returned prompt can give it away.
        if lie == 'big':
            loss_after = loss_before * 0.4
        else:
            # 'mimic' first runs the correction privately, keeps the gain it would have earned,
            # then retrains on its own labels so the prompt it sends still carries the attack
            honest_gain_state, honest_after = corr_state, loss_after
            corr_state, _ = one_pass(lambda target, corrected: target)
            loss_after = honest_after

    # the probe must not change the round's real update
    client.model.prompt_learner.load_state_dict(trained, strict=False)
    client.optimizer.load_state_dict(opt_state)
    return {'state': corr_state, 'lie': None if comply else lie, 'fork': fork,
            'loss_before': loss_before, 'loss_after': loss_after,
            'n_replaced': n_replaced, 'n_total': n_total, 'audit': audit,
            'samples': samples}


@torch.no_grad()
def probe_signals(probe, client_state, global_state, model, zs_feats, device):
    """Turn one client's probe into the three response signals."""
    from .signals import prompt_text_features, _concentration

    flat = lambda st: torch.cat([st[k].reshape(-1).float() for k in global_state])
    g, c = flat(global_state), flat(client_state)
    # The reference is the update the client is having AGGREGATED this round, which the server
    # already holds and the client cannot fabricate without giving up its attack. Comparing two
    # things the client sent would let the attacker choose both.
    u_main = c - g
    # under fork the corrected pass started from the global prompt, so the update it represents
    # is measured from there; under chain it started from what the client sent
    u_corr = flat(probe['state']) - (g if probe.get('fork') else c)
    denom = u_corr.norm() * u_main.norm()
    # high means the corrected pass simply carried on in the same direction as the round's own
    # training. True for an honest client whose labels already agree with the global model, and
    # for a client that quietly ignored the corrections.
    r_align = float((u_corr @ u_main) / denom) if float(denom) > 0 else 1.0

    zs = zs_feats.float()
    _, _, conc_before, kl_before = _concentration(prompt_text_features(model, client_state, device), zs)
    _, _, conc_after, kl_after = _concentration(prompt_text_features(model, probe['state'], device), zs)

    gain = probe['loss_before'] - probe['loss_after']
    return {
        'r_gain': round(gain, 5),
        'r_align': round(r_align, 5),
        'r_conc_drop': round(conc_before - conc_after, 5),
        'r_kl_drop': round(kl_before - kl_after, 5),
        # The lie detector, and the reason the probe exists. A client claiming a large gain
        # while the corrections changed nothing about its training is claiming credit for work
        # it did not do. An honest client is small on one factor or the other: a clean client
        # has little to gain, a noisy one genuinely changes course.
        'r_unearned': round(gain * max(r_align, 0.0), 5),
        # Magnitude, not direction. A client that really trained on the global model's own
        # predictions barely moves, because the global prompt already fits them; one that
        # quietly reran its own labels moves as far as it did the first time. Logged as a log
        # ratio so it does not inherit the per-client scale of the update itself, which varies
        # with sample count and class mix under a Dirichlet split.
        'r_norm': round(float(torch.log((u_corr.norm() + 1e-12) / (u_main.norm() + 1e-12))), 5),
        # how much the confidence gate actually let through, so a sweep over thresholds can be
        # read against what it did rather than against the number that was asked for
        'r_replaced': round(probe.get('n_replaced', 0) / max(probe.get('n_total', 1), 1), 4),
    }


def log_probe(round_idx, signals, roles):
    import json
    log.debug('PROBE ' + json.dumps(
        {'round': round_idx,
         'clients': {str(c): {**v, 'role': roles[c] if roles else 'unknown'}
                     for c, v in sorted(signals.items())}}, sort_keys=True))
