"""FedCorr + CoOp (Xu et al., CVPR 2022), a comparator (`--fedcorr true`).

Follows the official code (github.com/Xu-Jingyi/FedCorr, main.py) stage by stage. The plan and the
few adaptations to prompt learning are in results/side-research/fedcorr/fedcorr_plan.md.

Stage 1, pre-processing (T1 iterations). In an iteration every client trains once, one at a time in
random order, starting from the latest global prompt, which its trained prompt then replaces (one
client per step, as in every official setting). Local training adds the adaptive proximal term
beta * mu_k * ||w - w_global||, mu_k being the client's noise level estimated in the previous
iteration (0 in the first). Each client reports the LID of its trained prompt's predictions on its
images and every image's loss (flcore/fedcorr.py). After the iteration:
  - a 2-component GMM on the accumulated LID; the high component is the noisy set;
  - per noisy client, a 2-component GMM on its losses; the share in the high-loss component is
    its estimated noise level mu_k (0 for the other clients);
  - correction: of its int(n * mu_k * relabel_ratio) highest-loss images, those the global prompt
    predicts with confidence > conf take the predicted label.
Stage 2, fine-tuning (T2 rounds): FedAvg over the clients with mu_k <= clean_thres only. Then every
image of the noisy set that the fine-tuned global prompt predicts with confidence > conf takes
that label.
Stage 3, usual training (the remaining rounds): FedAvg over every client, corrected labels.
Mixup in local training throughout; no proximal term after stage 1. Labels, once corrected, stay
corrected.

One logged round per iteration or round, numbered 0..global_rounds like every other arm, so
last10 is read the same way: T1 + T2 + T3 = global_rounds + 1.
"""
import time

import numpy as np

from .server_fedavg import FedAvg
from ..fedcorr import gmm_high, global_probs, noise_level, relabel
from ..utils import eval_global, load_state_dict
from ..pretty.logger import log


class FedCorr(FedAvg):
    def __init__(self, args, times):
        super().__init__(args, times)
        assert self.bench == 'global' and self.task == 'class', 'FedCorr: global classification only'
        self.fedcorr_records = []

    def stage_lengths(self):
        total = self.global_rounds + 1
        t1 = min(int(self.args.fedcorr_iters), max(1, total // 3))
        ft = int(self.args.fedcorr_ft_rounds)
        # official T2:T3 is about 1:1 (500:450, 450:450, 50:50): half of what is left by default
        t2 = (total - t1) // 2 if ft < 0 else min(ft, total - t1 - 1)
        return t1, t2, total - t1 - t2

    def run(self):
        t1, t2, t3 = self.stage_lengths()
        log.info(f'FedCorr: pre-processing {t1} iterations, fine-tuning {t2} rounds, '
                 f'usual training {t3} rounds')
        n = self.num_clients
        lid_acc, mu, noisy = np.zeros(n), np.zeros(n), []
        self.fedcorr_records.append({'stage': 0, 'lengths': [t1, t2, t3],
                                     'true_noise': [noise_level(c) for c in self.clients]})
        for i in range(self.global_rounds + 1):
            self.rounds = i
            start_time = time.time()
            if i < t1:
                info, top1, noisy, mu = self.preprocess(lid_acc, mu)
            else:
                if i == t1:
                    self.clean_ids = self.choose_clean(mu)
                if i == t1 + t2:
                    self.correct_after_finetune(noisy)
                if i < t1 + t2:
                    m = min(max(int(self.train_fraction * n), 1), len(self.clean_ids))
                    self.selected_client_ids = list(np.random.choice(self.clean_ids, m, replace=False))
                    self.cur_join_clients = m
                else:
                    self.selected_client_ids = self.select_clients()
                info, top1 = self.comm_round()
            log.info(f'{info}, top1: {top1:.2%}, '
                     f'elapsed: {time.time() - start_time:.1f}s, '
                     f'best_acc: {self.best_acc:.2%}.')
        self.summarize()

    def preprocess(self, lid_acc, mu):
        """One pre-processing iteration: sequential local training, then detection and correction."""
        n = self.num_clients
        lid, losses = np.full(n, np.nan), {}
        for c in np.random.permutation(n):
            cl = self.clients[c]
            cl.fedcorr_mu, cl.fedcorr_collect = float(mu[c]), True
            cl.init(self.model, self.rounds)
            res = cl.local_train()
            cl.fedcorr_mu, cl.fedcorr_collect = 0.0, False
            if res['status'] == 'error':
                continue                                # diverged: the global prompt is kept
            state = {k: v.to(self.state_device) for k, v in res['state'].items()}
            self.model = load_state_dict(self.model, state, self.task)
            self.model.custom_avg(self.rounds)
            rep = res.get('fedcorr') or {}
            if rep.get('lid') is not None:
                lid[c] = rep['lid']
            losses[c] = np.asarray(rep.get('loss', []), dtype=float)
        # a client too small for a LID (fewer than 3 images) counts as the median client
        fill = float(np.nanmedian(lid)) if np.isfinite(lid).any() else 0.0
        lid_acc += np.where(np.isfinite(lid), lid, fill)

        high = gmm_high(lid_acc, self.seed)
        noisy = [int(c) for c in np.where(high)[0]]
        mu = np.zeros(n)
        for c in noisy:
            loss = losses.get(c, np.zeros(0))
            if len(loss) >= 2:
                mu[c] = float(gmm_high(loss, self.seed).mean())
        conf_thr = float(self.args.fedcorr_conf)
        fixes = {}
        for c in noisy:
            loss = losses.get(c, np.zeros(0))
            k = int(len(loss) * mu[c] * float(self.args.fedcorr_relabel_ratio))
            if k == 0:
                continue
            p = global_probs(self.model, self.clients[c])
            conf, pred = p.max(dim=1)
            idx = [int(i) for i in np.argsort(-loss)[:k] if float(conf[i]) > conf_thr]
            fixes[str(c)] = {'k': k, 'confident': len(idx),
                             **relabel(self.clients[c], idx, [int(pred[i]) for i in idx])}
        self.fedcorr_records.append({
            'stage': 1, 'round': self.rounds,
            'lid': [None if not np.isfinite(v) else round(float(v), 4) for v in lid],
            'lid_acc': [round(float(v), 4) for v in lid_acc], 'noisy_set': noisy,
            'mu': [round(float(v), 4) for v in mu], 'relabel': fixes,
            'noise_after': [noise_level(cl) for cl in self.clients]})
        top1 = self.evaluate()
        info = f'round {self.rounds}, FedCorr pre-processing, noisy set {noisy}'
        return info, top1, noisy, mu

    def choose_clean(self, mu):
        """The fine-tuning set: clients whose estimated noise level is at most clean_thres. The
        official code has no answer when that set is empty (it divides by zero); here the clients
        with the lowest estimate are used then, and the record says so."""
        thr = float(self.args.fedcorr_clean_thres)
        clean = [int(c) for c in np.where(mu <= thr)[0]]
        fallback = not clean
        if fallback:
            clean = [int(c) for c in np.where(mu == mu.min())[0]]
        self.fedcorr_records.append({'stage': 2, 'round': self.rounds, 'clean_set': clean,
                                     'fallback': fallback})
        return clean

    def correct_after_finetune(self, noisy):
        """Every image of the noisy set that the fine-tuned global prompt is confident about
        takes the predicted label."""
        conf_thr = float(self.args.fedcorr_conf)
        fixes = {}
        for c in noisy:
            p = global_probs(self.model, self.clients[c])
            if p is None:
                continue
            conf, pred = p.max(dim=1)
            idx = [i for i in range(len(pred)) if float(conf[i]) > conf_thr]
            fixes[str(c)] = {'confident': len(idx),
                             **relabel(self.clients[c], idx, [int(pred[i]) for i in idx])}
        self.fedcorr_records.append({'stage': 3, 'round': self.rounds, 'relabel': fixes,
                                     'noise_after': [noise_level(cl) for cl in self.clients]})

    def evaluate(self):
        top1, _ = eval_global(self.model, self.testloader, self.device,
                              self.precision, self.task, cache=self.test_cache)
        self.best_acc = max(self.best_acc, top1)
        self.tb.add_scalar('eval/top1', top1, self.rounds)
        self.tb.add_scalar('eval/best', self.best_acc, self.rounds)
        return top1
