import time
import torch
import numpy as np
import torch.nn as nn
from statistics import harmonic_mean as hmean
from matplotlib import pyplot as plt

from ..clients.client_fedavg import ClientFedAvg
from ..servers.server_base import ServerBase
from ..utils import ( DivergeError, eval_global, eval_base_novel,
                     eval_personal, svd, eval_domains, collect_state,
                     load_state_dict)
from ..pretty.logger import log
# from scipy.spatial.distance import cosine as CosineSimilarity
from sklearn.metrics.pairwise import cosine_similarity as CosineSimilarity

def macro_prf(collect):
    """Macro precision, recall and F1 on the test set from (prediction, label) batches.
    Averaged over the classes that occur in the test labels; a class never predicted has
    precision 0 (as sklearn with zero_division=0)."""
    pred = torch.cat([p for p, _ in collect]).long()
    y = torch.cat([t for _, t in collect]).long()
    C = int(max(pred.max(), y.max())) + 1
    tp = torch.bincount(y[pred == y], minlength=C).double()
    n_pred = torch.bincount(pred, minlength=C).double()
    n_true = torch.bincount(y, minlength=C).double()
    keep = n_true > 0
    prec = torch.where(n_pred > 0, tp / n_pred.clamp_min(1), torch.zeros_like(tp))[keep]
    rec = (tp / n_true.clamp_min(1))[keep]
    f1 = torch.where(prec + rec > 0, 2 * prec * rec / (prec + rec).clamp_min(1e-12), torch.zeros_like(prec))
    return {'precision': round(float(prec.mean()), 5), 'recall': round(float(rec.mean()), 5),
            'f1': round(float(f1.mean()), 5)}


def confusion_matrix(collect):
    """Test-set confusion counts from (prediction, label) batches; rows are the true classes."""
    pred = torch.cat([p for p, _ in collect]).long()
    y = torch.cat([t for _, t in collect]).long()
    C = int(max(pred.max(), y.max())) + 1
    return torch.bincount(C * y + pred, minlength=C * C).reshape(C, C).tolist()


class FedAvg(ServerBase):
    def __init__(self, args, times):
        super().__init__(args, times)
        self.init_clients(ClientFedAvg)
        print(f"\nTrain fraction: {self.train_fraction}, total clients: {self.num_clients}")
        print("Finished creating server and clients.")

        self.Budget = []
        self.best_acc = 0.
        self.best_acc_novel = 0.
        self.best_acc_hm = 0.
        self.best_acc_per = 0.
        self.best_acc_mds = {}
        self.id_text_feats = {}
        self.ood_text_feats = {}

    def run(self):
        if self.prompt_algo == 'CLIP':
            if self.bench == 'multidomain':
                top1, md_accs = eval_domains(self.model, self.testloaders_mdomain,
                                   self.device, precision=self.precision)
                if top1 > self.best_acc:
                    self.best_acc = top1
                    self.best_acc_mds = md_accs
            else:
                top1, _ = eval_global(self.model, self.testloader, self.device,
                                      self.precision, self.task, cache=self.test_cache)
                self.best_acc = top1
                self.best_acc_per = top1
                self.best_acc_hm = top1
            log.info(f'CLIP acc: {top1:.2%}')
        else:
            log.info('Starting Local Training...')
            metrics = getattr(self.args, 'log_metrics', 'false') == 'true'
            for i in range(self.global_rounds+1):
                self.rounds = i
                start_time = time.time()
                if metrics and torch.cuda.is_available():
                    torch.cuda.reset_peak_memory_stats()
                self.round_metrics = {'round': i} if metrics else None
                self.selected_client_ids = self.select_clients()
                info, top1 = self.comm_round()
                log.info(f'{info}, top1: {top1:.2%}, '
                         f'elapsed: {time.time() - start_time:.1f}s, '
                         f'best_acc: {self.best_acc:.2%}.')
                if metrics:
                    rec = self.round_metrics
                    rec['acc'] = round(float(top1), 5)
                    rec['wall_s'] = round(time.time() - start_time, 2)
                    rec['peak_mem_mb'] = (round(torch.cuda.max_memory_allocated() / 2 ** 20, 1)
                                          if torch.cuda.is_available() else None)
                    self.metric_records.append(rec)
                    if 'f1' in rec:
                        log.info(f'metrics round {i}: precision {rec["precision"]:.2%}, '
                                 f'recall {rec["recall"]:.2%}, f1 {rec["f1"]:.2%}')

        self.summarize()


    def comm_round(self, ):
        results = {}
        top1 = 0.

        cal = getattr(self.args, 'sure', 'false') == 'true' and getattr(self.args, 'sure_cal', 'none') == 'noise'
        gate = float(getattr(self.args, 'sure_gate', 0.0) or 0.0)
        if cal and gate > 0:
            # --sure_gate: CLEAR-FPL until the decision after round R, then --sure_cal only if on
            cal = getattr(self, 'sure_gate_on', False)
            for c in self.selected_client_ids:
                self.clients[c].sure_cal_on = cal
        if cal:
            # --sure_cal noise: before anyone repairs, each client sends its profile log-likelihood
            # on the temperature grid (25 numbers) and the server broadcasts the best temperature
            from ..sure import cal_pick, cal_profile
            profiles = []
            for c in self.selected_client_ids:
                self.clients[c].zs_text_feats = self.zs_text_feats
                self.clients[c].init(self.model, self.rounds)
                profiles.append(cal_profile(self.clients[c]))
                # free this client's model copy now: the training loop below makes a fresh one, and
                # keeping all copies alive at once runs a 16 GB GPU out of memory with 50 clients
                for attr in ('model', 'optimizer', 'lr_scheduler'):
                    if hasattr(self.clients[c], attr):
                        delattr(self.clients[c], attr)
            T_fit = cal_pick(profiles)
            tmax = float(getattr(self.args, 'sure_cal_tmax', 0.0) or 0.0)
            # --sure_cal_tmax: P is already softened by the zero-shot mix; a fitted T above the cap
            # comes from labels the global prompt has absorbed, not from an overconfident P
            T = min(T_fit, tmax) if tmax > 0 else T_fit
            for c in self.selected_client_ids:
                self.clients[c].sure_T = T
                self.clients[c].sure_T_fit = T_fit

        for c in self.selected_client_ids:
            self.clients[c].dis_baseline = self.dis_baseline
            self.clients[c].far_baseline = self.far_baseline
            self.clients[c].far_neighbours = self.far_neighbours()
            self.clients[c].filter_hard = self.filter_hard
            # CLIP's zero-shot class embeddings: every client can compute them itself; handing
            # them over only saves recomputing (used by --sample_filter proto)
            self.clients[c].zs_text_feats = self.zs_text_feats
            self.clients[c].init(self.model, self.rounds)
            t0 = time.time()
            results[c] = self.clients[c].local_train()
            if getattr(self, 'round_metrics', None) is not None:
                # clients run one after another here; on real devices they would run in parallel,
                # so both the sum and the slowest client are kept
                dt = time.time() - t0
                rm = self.round_metrics
                rm['client_s_sum'] = round(rm.get('client_s_sum', 0.0) + dt, 2)
                rm['client_s_max'] = round(max(rm.get('client_s_max', 0.0), dt), 2)
            # self.check_clip(c)

        if not results:
            raise DivergeError('All clients trained to divergence.')

        states, weights, info = self.receive_results(results)
        if getattr(self, 'round_metrics', None) is not None:
            # what goes on the wire: each client's uploaded state, and the global state it received
            size = [sum(v.numel() * v.element_size() for v in s.values()) for s in states.values()]
            self.round_metrics['up_bytes'] = int(sum(size))
            self.round_metrics['down_bytes'] = int(max(size, default=0) * len(self.selected_client_ids))
            self.round_metrics['clients'] = len(self.selected_client_ids)
        if (gate > 0 and getattr(self.args, 'sure_cal', 'none') == 'noise'
                and self.rounds == int(getattr(self.args, 'sure_gate_rounds', 5)) and self.sure_records):
            self.decide_gate(gate)
        avg_state = self.aggregate(states, weights)
        self.model = load_state_dict(self.model, avg_state, self.task)
        self.model.custom_avg(self.rounds)
        avg_state = collect_state(self.model, self.task, self.prompt_algo)
        if self.eval_rounds > 1 and (self.rounds % self.eval_rounds != 0):
            return info, top1

        if self.bench == 'base2novel':
            top1, _ = eval_base_novel(self.model, self.testloader_base, self.device,
                                 self.train_classnames, self.test_classnames_base, self.precision)
            top1_novel, _ = eval_base_novel(self.model, self.testloader_novel, self.device,
                                 self.train_classnames, self.test_classnames_novel, self.precision)
            top1_hm = hmean([top1, top1_novel])
            if top1_hm > self.best_acc_hm:
                self.best_acc = top1
                self.best_acc_novel = top1_novel
                self.best_acc_hm = top1_hm
            info += f', eval_novel: {top1_novel:.2%}'
            info += f', best_hm: {self.best_acc_hm:.2%}'
            self.tb.add_scalar('eval/top1_base', top1, self.rounds)
            self.tb.add_scalar('eval/best_base', self.best_acc, self.rounds)
            self.tb.add_scalar('eval/top1_novel', top1_novel, self.rounds)
            self.tb.add_scalar('eval/best_novel', self.best_acc_novel, self.rounds)
            self.tb.add_scalar('eval/top1_hmean', top1_hm, self.rounds)
            self.tb.add_scalar('eval/best_hmean', self.best_acc_hm, self.rounds)
            self.eval_multiple()
        elif self.bench == 'dual':
            top1, _ = eval_global(self.model, self.testloader, self.device,
                                  self.precision, self.task, cache=self.test_cache)
            top1_per, _ = eval_personal(self.model, states, weights,
                                        self.testloaders_per, self.device, self.precision)
            self.model.prompt_learner.load_state_dict(avg_state, strict=False) # reload avg_state
            top1_hm = hmean([top1, top1_per])
            if top1_hm > self.best_acc_hm:
                self.best_acc = top1
                self.best_acc_per = top1_per
                self.best_acc_hm = top1_hm
            info += f', eval_per: {top1_per:.2%}'
            info += f', best_hm: {self.best_acc_hm:.2%}'
            self.tb.add_scalar('eval/top1_global', top1, self.rounds)
            self.tb.add_scalar('eval/best_global', self.best_acc, self.rounds)
            self.tb.add_scalar('eval/top1_personal', top1_per, self.rounds)
            self.tb.add_scalar('eval/best_personal', self.best_acc_per, self.rounds)
            self.tb.add_scalar('eval/top1_hmean', top1_hm, self.rounds)
            self.tb.add_scalar('eval/best_hmean', self.best_acc_hm, self.rounds)
        elif self.bench == 'personal':
            top1, _ = eval_personal(self.model, states, weights, self.testloaders_per,
                                        self.device, self.precision)
            self.model.prompt_learner.load_state_dict(avg_state, strict=False) # reload avg_state
            self.best_acc = top1 if top1 > self.best_acc else self.best_acc
            self.best_acc_per = top1 if top1 > self.best_acc_per else self.best_acc_per
            self.tb.add_scalar('eval/top1_personal', top1, self.rounds)
            self.tb.add_scalar('eval/best_personal', self.best_acc, self.rounds)
        elif self.bench == 'multidomain':
            top1, md_accs = eval_domains(self.model, self.testloaders_mdomain,
                                   self.device, precision=self.precision)
            if top1 > self.best_acc:
                self.best_acc = top1
                self.best_acc_mds = md_accs
            self.tb.add_scalar('eval/top1_domain_weighted', top1, self.rounds)
            self.tb.add_scalar('eval/best_domain_weighted', self.best_acc, self.rounds)
            self.tb.add_multiple_scalars('eval/multidomain', self.best_acc_mds, self.rounds)
        else:
            # global, xdomain
            want = getattr(self, 'round_metrics', None) is not None
            collect = [] if getattr(self.args, 'log_asr', 'false') == 'true' or want else None
            top1, _ = eval_global(self.model, self.testloader, self.device,
                                  self.precision, self.task, cache=self.test_cache,
                                  collect=collect)
            if collect and getattr(self.args, 'log_asr', 'false') == 'true':
                self.record_asr(collect)
            if collect and want:
                self.round_metrics.update(macro_prf(collect))
                if self.rounds == self.global_rounds:
                    self.final_confusion = confusion_matrix(collect)
            self.best_acc = top1 if top1 > self.best_acc else self.best_acc
            self.tb.add_scalar('eval/top1', top1, self.rounds)
            self.tb.add_scalar('eval/best', self.best_acc, self.rounds)
        return info, top1

    def decide_gate(self, gate):
        """--sure_gate: from the suspects / relabelled counts the clients reported in rounds 1..R,
        switch to --sure_cal's repair for the rest of the run when the referee is strong."""
        from ..sure import gate_bound
        R = int(getattr(self.args, 'sure_gate_rounds', 5))
        rel = sus = 0
        for rec in self.sure_records:
            if 1 <= rec['round'] <= R:
                for c in rec['clients'].values():
                    rel += c.get('relabeled') or 0
                    sus += c.get('suspects') or 0
        lo = gate_bound(rel, sus)
        self.sure_gate_on = lo is not None and lo >= gate
        self.sure_records[-1]['gate'] = {'relabeled': rel, 'suspects': sus,
                                         'bound': None if lo is None else round(lo, 4),
                                         'threshold': gate, 'on': self.sure_gate_on}
        log.info(f'referee gate: {rel}/{sus} relabelled, lower bound '
                 f'{"—" if lo is None else f"{lo:.3f}"} vs {gate}: '
                 f'{"switch to calibrated repair" if self.sure_gate_on else "stay CLEAR-FPL"}')

    def check_clip(self, c):
        for (n1, p1) in self.model.named_parameters():
            print(f'layer name: {n1}')
        for (n1, p1), (n2, p2) in zip(self.model.named_parameters(),
                                      self.clients[c].model.named_parameters()):
            print(f'layer name: {n1}')
            delta = 1e-8 * torch.ones_like(p1).to(self.device)
            diff = torch.any(torch.gt((p1 - p2), delta))
            if diff:
                print('weight difference!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
