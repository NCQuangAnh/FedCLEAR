import copy
import torch
import numpy as np
import time
import collections
from torch.cuda.amp import GradScaler, autocast
from torch.nn import functional as F

from .client_base import Client
from ..utils import (MovingAverage, AccuracyCounter, DivergeError,
                          topk, IoU, unit, build_loss_fn, eval_global, eval_base_novel,
                          collect_state)
from ..pretty.logger import log

class ClientFedAvg(Client):
    len_history = 100
    def __init__(self, args, id, trainloader, testloader, **kwargs):
        super().__init__(args, id, trainloader, testloader, **kwargs)

    def _turncoat_view(self):
        """--proto_lie turncoat: for its first --turncoat_rounds rounds the device attacker trains
        on its clean images only, so its update and the prototypes the server keeps from those
        rounds look honest. Afterwards it trains on everything, poisoned labels included."""
        ds = self.trainloader.dataset
        if not hasattr(ds, 'all_samples'):
            ds.all_samples = list(ds.samples)
            ds.all_clean = list(getattr(ds, 'clean_targets', [t for _, t in ds.samples]))
        if self.rounds < int(getattr(self.args, 'turncoat_rounds', 1)):
            keep = [i for i, (_, y) in enumerate(ds.all_samples) if int(y) == int(ds.all_clean[i])]
        else:
            keep = list(range(len(ds.all_samples)))
        ds.samples = [ds.all_samples[i] for i in keep]
        ds.clean_targets = [ds.all_clean[i] for i in keep]
        ds.targets = [t for _, t in ds.samples]
        ds.sample_weights = None

    def local_train(self,):
        begin_time = time.time()
        msg = f'c: {self.client_id}'
        avg_accs = MovingAverage(self.len_history)
        avg_losses = MovingAverage(self.len_history)
        avg_add_losses = MovingAverage(self.len_history)
        self.optimizer.state = collections.defaultdict(dict)
        self.optimizer.zero_grad()
        if self.lr_scheduler:
            self.lr_scheduler.last_epoch = self.rounds - 1
            self.optimizer.zero_grad()
            if self.optim_name != 'sam':
                self.optimizer.step()  # disable warning on the next line...
            self.lr_scheduler.step()
        self.init_state = copy.deepcopy(self.model.prompt_learner).state_dict()
        diag = None
        if getattr(self.args, 'diag_scores', 'false') == 'true':
            # logged only, on the pristine data and with every RNG restored (flcore/diag.py)
            from ..diag import diag_before
            diag = diag_before(self)
        nlp = None
        if getattr(self.args, 'nlprompt', 'none') != 'none':
            from ..nlprompt import nlprompt_split
            nlp = nlprompt_split(self)
        sure = None
        if getattr(self.args, 'sure', 'false') == 'true':
            from ..sure import sure_round
            sure = sure_round(self)
        every = getattr(self.args, 'correction_every', 0)
        if (getattr(self.args, 'sample_filter', 'none') != 'none' and every
                and self.rounds % every == 0
                and self.rounds >= getattr(self.args, 'filter_start', 0)):
            # re-scored from the pristine set every time, so a sample the rule got wrong early
            # can come back once the global model knows more
            from ..correction import refresh_sample_filter
            if getattr(self, 'device_attacker', False):
                # It owns its machine, so the client-side filter never runs here: it trains on
                # every poisoned label it has. The one number it owes the server it fabricates --
                # the last broadcast baseline, i.e. exactly what the cleanest client looks like.
                # Before any baseline exists it has nothing to copy and reports its true value.
                ds = self.trainloader.dataset
                base = getattr(self, 'dis_baseline', None)
                true_dis = None
                if base is None:
                    report = refresh_sample_filter(self, None)   # baseline None -> filters nothing
                    true_dis = report['mean_dis'] if report else None
                self.filter_report = {
                    'mean_dis': round(float(base if base is not None else (true_dis or 0.0)), 5),
                    'rho': 0.0, 'dropped': 0, 'n': len(ds), 'dropped_damaged': 0, 'lied': True}
                far = getattr(self, 'far_baseline', None)
                if far is not None:
                    self.filter_report['dis_far'] = round(float(far), 5)   # same lie, other score
            else:
                self.filter_report = refresh_sample_filter(self, getattr(self, 'dis_baseline', None))
        if getattr(self, 'device_attacker', False) and getattr(self.args, 'proto_lie', 'none') == 'turncoat':
            self._turncoat_view()
        flops, steps = 0, 0
        result = {
            'flops.model': flops,
            'flops.total': flops * steps * self.batch_size,
        }
        init_state = {
            k: v.to(self.device, copy=True) for k, v in self.init_state.items()}
        if self.task == 'seg':
            self.model.decoder.train()
        self.model.update_global_text_feats()
        # a repair can leave no image it trusts (--sure_audit at a ~100% noise estimate): the client
        # then sends the received prompt back unchanged instead of training on nothing
        epochs = self.local_epochs if len(self.trainloader.dataset) > 0 else 0
        fedrg = None
        try:
            if getattr(self.args, 'fedrg', 'false') == 'true':
                # FedRG stage II replaces the plain batch loop (flcore/fedrg.py)
                from ..fedrg import fedrg_train
                fedrg = fedrg_train(self, epochs, avg_losses, avg_add_losses, avg_accs)
                epochs = 0
            for e in range(epochs):
                for b, batch in enumerate(self.trainloader):
                    self._batch_idx = b
                    data, target = batch[0], batch[1]
                    w = batch[2] if len(batch) > 2 else None
                    self._step(data, target, init_state, avg_losses, avg_add_losses,
                               avg_accs, self.rounds, w)
                if self.central:
                    self.round_eval(avg_losses, avg_add_losses, e)
        except DivergeError as e:
            log.verbose(f'{msg}, diverged to NaN.')
            return {'status': 'error', 'exception': e, **result}

        result.update({
            'status': 'normal',
            'state': collect_state(self.model, self.task, self.prompt_algo),
            'accuracy': float(avg_accs.mean()),
            'loss': float(avg_losses.mean()),
            'num_train_samples': len(self.trainloader.dataset.targets),
            'filter': getattr(self, 'filter_report', None)
        })
        if sure is not None:
            result['sure'] = sure
        if nlp is not None:
            result['nlp'] = nlp
        if fedrg is not None:
            result['fedrg'] = fedrg
        if getattr(self, 'fedcorr_collect', False):
            # FedCorr pre-processing: LID and per-image losses of the prompt just trained
            from ..fedcorr import local_report
            result['fedcorr'] = local_report(self)
        if diag is not None:
            from ..diag import diag_after
            result['diag'] = diag_after(self, diag)
            result['diag_rows'] = getattr(self, 'diag_rows', None)
        every = getattr(self.args, 'correction_every', 0)
        if every and self.rounds % every == 0:
            # the correction probe: one extra pass on the global model's proposed labels.
            # `probe_comply` is set by the server; a malicious client refuses and lies.
            from ..correction import run_correction_probe
            result['probe'] = run_correction_probe(
                self, comply=getattr(self, 'probe_comply', True),
                lie=getattr(self.args, 'attack_lie', 'mimic'))

        if self.client_eval:
            if self.bench == 'base2novel':
                top1_base, _ = eval_base_novel(self.model,  self.testloader_base, self.device,
                                  self.train_classnames, self.test_classnames_base, self.precision)
                result.update({'eval_acc':top1_base,})

                top1_novel, _ = eval_base_novel(self.model,  self.testloader_novel, self.device,
                                  self.train_classnames, self.test_classnames_novel, self.precision)
                msg += f', eval_novel: {top1_novel:.2%}'
                result.update({'eval_novel':top1_novel})
            else:
                top1, _ = eval_global(self.model,  self.testloader, self.device,
                                      self.precision, self.task)
                result.update({
                    'eval_acc':top1,
                })
                msg += f', eval: {top1:.2%}'
        end_time = time.time()
        log.info(
            f'{msg}, train: {float(avg_accs.mean()):.2%}, '
            f'ep: {self.local_epochs}, '
            f'lr: {self._get_lr():.4f}, flops: {unit(flops)}, '
            f'loss: {(avg_losses.mean()):.4f}, '
            f'add_loss: {(avg_add_losses.mean()):.6f}, '
            f'time:{end_time - begin_time:.2f}s.')

        self.round_epilog()
        return result

    def _weighted(self, output, target, weights):
        """Per-sample weighted loss; identical to the plain loss when weights are absent.

        A hard filter throws a sample away, so a sample the rule got wrong is lost entirely --
        and dropping one clean sample was measured to cost 1.34x what dropping one damaged one
        gains, which is where the 57.3% break-even precision comes from. A weight keeps the
        sample in the batch at reduced strength, so a mistake costs a fraction of that.
        """
        if weights is None:
            return self.loss_func(output, target)
        if getattr(self.args, 'nlprompt', 'none') != 'none':
            # NLPrompt split (flcore/nlprompt.py): +1 = OT-clean -> CE, -1 = OT-noisy -> 1 - p(label)
            ce = torch.nn.functional.cross_entropy(output.float(), target, reduction='none')
            p = torch.softmax(output.float(), dim=-1).gather(1, target.view(-1, 1)).squeeze(1)
            return torch.where(weights < 0, 1.0 - p, ce).mean()
        if getattr(self, 'loss_type', 'ce') == 'mae':
            from ..utils import mae_per_sample
            per = mae_per_sample(output, target)
        else:
            per = torch.nn.functional.cross_entropy(output, target, reduction='none')
        return (per * weights).sum() / weights.sum().clamp(min=1e-8)

    def _prox(self, init_state):
        """FedProx (Li et al., MLSys 2020): (mu / 2) * ||w - w_global||^2 over the prompt.

        In FedCorr's pre-processing stage the adaptive term of the official code instead:
        beta * mu_k * ||w - w_global||, the norm itself (not squared), from the second batch of an
        epoch on, mu_k being the client's estimated noise level (set by server_fedcorr.py)."""
        fc_mu = float(getattr(self, 'fedcorr_mu', 0.0))
        mu = float(getattr(self.args, 'prox_mu', 0.0))
        if fc_mu > 0:
            if getattr(self, '_batch_idx', 0) == 0:
                return 0.0
        elif mu <= 0:
            return 0.0
        reg = 0.0
        for name, p in self.model.prompt_learner.named_parameters():
            if p.requires_grad and name in init_state:
                reg = reg + ((p.float() - init_state[name].float()) ** 2).sum()
        if fc_mu > 0:
            return float(self.args.fedcorr_beta) * fc_mu * torch.sqrt(reg.clamp_min(1e-12))
        return 0.5 * mu * reg

    def _mixup(self, data, target):
        """FedCorr trains with mixup (official mixup_data, alpha = --fedcorr_mixup): returns the
        mixed images and a loss function of the output. Plain data and loss otherwise."""
        alpha = float(getattr(self.args, 'fedcorr_mixup', 0.0))
        if getattr(self.args, 'fedcorr', 'false') != 'true' or alpha <= 0:
            return data, None
        lam = float(np.random.beta(alpha, alpha))
        perm = torch.randperm(data.size(0), device=data.device)
        mixed = lam * data + (1 - lam) * data[perm]
        return mixed, lambda out: (lam * self.loss_func(out, target)
                                   + (1 - lam) * self.loss_func(out, target[perm]))

    def _step(self, data, target, init_state, avg_losses, avg_add_losses, avg_accs, rounds,
              weights=None):
        data, target = data.to(self.device), target.to(self.device)
        if weights is not None:
            weights = weights.to(self.device)
        self.optimizer.zero_grad()
        data, mix_loss = self._mixup(data, target)
        if self.args.precision == "amp":
            with autocast():
                output = self.model(data, target, test=False)
                loss = mix_loss(output) if mix_loss else self._weighted(output, target, weights)
                add_loss = self.model.add_loss()
                loss += add_loss
            loss = loss + self._prox(init_state)
            self.optimizer.zero_grad()
            self.scaler.scale(loss).backward()
            self.scaler.step(self.optimizer)
            self.scaler.update()
        else:
            if self.optim_name == 'sam':
                output = self.model(data, target, test=False)
                loss = self._weighted(output, target, weights)
                add_loss = self.model.add_loss()
                loss += add_loss
                self.optimizer.zero_grad()
                loss.backward()
                self.optimizer.first_step(zero_grad=True)

                output = self.model(data, target, test=False)
                loss = self._weighted(output, target, weights)
                loss.backward()
                self.optimizer.second_step(zero_grad=True)
            else:
                output = self.model(data, target, test=False)
                loss = mix_loss(output) if mix_loss else self._weighted(output, target, weights)
                add_loss = self.model.add_loss()
                loss += add_loss
                loss = loss + self._prox(init_state)

                if torch.isnan(loss).any():
                    raise DivergeError('Training loss diverged to NaN.')

                loss.backward()
                self.grad_func(init_state)
                if self.grad_clipping_norm > 0:
                    self.grad_clip()
                self.optimizer.step()
        train_acc = self.metric(output, target)
        avg_losses.add(loss)
        avg_add_losses.add(add_loss)
        avg_accs.add(train_acc)

    def round_epilog(self,):
        if not self.central:
            self.keep_states()
            del self.model
            del self.optimizer
            del self.lr_scheduler
            del self.init_state

    def round_eval(self, avg_losses, avg_add_losses, cur_epoch):
        top1, _ = eval_global(self.model,  self.testloader, self.device,
                              self.precision, self.task)
        msg = f'{self.prompt_algo}, c: {self.client_id}'
        log.verbose(
            f'{msg}, eval: {float(top1):.2%}, '
            f'total_epochs: {self.local_epochs}, '
            f'cur_epoch: {cur_epoch}, '
            f'lr: {self._get_lr():.4f}, '
            f'loss: {(avg_losses.mean()):.4f}, '
            f'add_loss: {(avg_add_losses.mean()):.4f}')
        if self.lr_scheduler:
            self.lr_scheduler.step()
