import torch
import torch.nn as nn
import os
import numpy as np
import h5py
import copy
import time
import random
import datetime
import json
from torch.cuda.amp import GradScaler, autocast

from ..models.utils import load_pretrained_weights
from ..models.clip import clip_maps
from ..models.clip.clip import load_clip_to_cpu
from ..datasets import datasets_map
from ..datasets.info import INFO
from ..utils import (unit, AccuracyCounter, eval_global, eval_base_novel, get_device,
                     seed_everything, TestFeatureCache, collect_state)
from ..attack import attack_update, UPDATE_ATTACKS
from ..robust_agg import aggregate as robust_aggregate
from ..signals import client_signals, log_signals, zero_shot_text_features
from ..correction import run_correction_probe, probe_signals, log_probe
from ..pretty.history import History
from ..pretty.logger import log

class ServerBase(object):
    def __init__(self, args, times):
        # Set up the main attributes
        self.task = args.task
        self.args = args
        self.bench = args.benchmark
        self.fed_algo = args.fed_algo
        self.prompt_algo = args.prompt_algo
        self.central = args.central == 'true'
        self.device = get_device(args.device_id)
        self.state_device = torch.device('cpu')
        self.dataset = args.dataset
        self.target_dataset = args.target_dataset
        self.img_folder = INFO[args.dataset]['img_folder']
        self.image_size = INFO[args.dataset]['shape'][-1]
        self.global_rounds = args.global_rounds
        self.local_epochs = args.local_epochs
        self.batch_size = args.batch_size
        self.learning_rate = args.local_learning_rate
        self.num_clients = 1 if self.central else args.num_clients
        self.num_shards = args.num_shards
        self.split_mode = args.split_mode
        self.data_root = args.data_root
        self.data_transform = args.data_transform
        self.drop_last = args.drop_last == 'true'
        self.split_alpha = args.split_alpha
        self.split_beta = args.split_beta
        self.train_fraction = args.train_fraction
        self.num_join_clients = int(self.num_clients * self.train_fraction)
        self.current_num_join_clients = self.num_join_clients
        self.grad_clipping_norm = args.grad_clipping_norm
        # explicit seed per run: run r of `--times` uses args.seed + r for few-shot sampling,
        # client split, client selection and prompt init, so runs can be paired across configs
        self.seed = args.seed + times
        self.cache_test_feats = getattr(args, 'cache_test_feats', 'false') == 'true'
        self.test_cache = None
        self.attack_cfg = {'type': getattr(args, 'attack_type', 'none'),
                           'rate': getattr(args, 'attack_rate', 0.4),
                           'frac': getattr(args, 'malicious_client_frac', 0.0),
                           'scale': getattr(args, 'attack_scale', 5.0),
                           'sample_oracle': getattr(args, 'sample_oracle', 'none')}
        self.noise_cfg = {'type': getattr(args, 'noise_type', 'none'),
                          'rate': getattr(args, 'noise_rate', 0.0),
                          'mode': getattr(args, 'noise_mode', 'uniform'),
                          'frac': getattr(args, 'noisy_client_frac', 0.5),
                          'oracle': getattr(args, 'noise_oracle', 'none'),
                          'attack': self.attack_cfg}
        self.agg_rule = getattr(args, 'agg_rule', 'fedavg')
        self.agg_trim = getattr(args, 'agg_trim', 0.1)
        self.noise_report = None
        self.attack_report = None
        self.client_roles = None
        self.agg_records = []
        self.excluded_client_ids = []
        self.log_signals = getattr(args, 'log_signals', 'false') == 'true'
        self.correction_every = getattr(args, 'correction_every', 0)
        # The audit is what turns the probe from an observation into a mechanism. When the
        # server aggregates the PROBE prompt instead of the round's own update, refusing stops
        # being free: a forged "I complied" prompt is then the contribution that counts, so
        # forging costs the attacker exactly what complying would have cost.
        self.probe_audit_prob = getattr(args, 'probe_audit_prob', 0.0)
        # Gate E measured that refusing the correction is visible at AUC 0.91-0.99, including
        # against merely noisy clients, but nothing was ever done with that label. This is the
        # missing half of the protocol: flag refusers online, from r_align alone, and stop
        # aggregating them. No roles, no oracle, no assumed attacker count for the 'mad' rule.
        self.warmup_rounds = getattr(args, 'warmup_rounds', 0)
        self.refusal_rule = getattr(args, 'refusal_rule', 'none')
        self.refusal_k = getattr(args, 'refusal_k', 2.0)
        self.refusal_patience = getattr(args, 'refusal_patience', 3)
        self.refusal_floor = getattr(args, 'refusal_floor', 0.12)
        self.refusal_history = {}
        self.refusal_probe_rounds = 0
        self.refusal_banned = set()
        # --refusal_action downweight: the clients flagged at the LAST decision, re-decided every
        # probe round (a set of current flags, not a growing list of convictions)
        self.refusal_flagged = set()
        self.refusal_wts = {}
        self.asr_records = []
        self.tdr_records = []
        self.tdr_evidence = {}
        self.tdr_rounds = 0
        self.tdr_random_class = {}
        # cross-client validation (flcore/xval.py): per-client feature caches, per-client trust
        # evidence, the weights it currently implies, and what it logged
        self.xval_cache = {}
        self.xval_evidence = {}
        self.xval_wts = {}
        self.xval_records = []
        # gate P (flcore/proto.py): what the prototype check did, per round
        self.proto_records = []
        self.proto_store = {}      # last prototypes each client sent (--proto_every)
        # per-class test accuracy over the last-10 window, so a loss can be traced to the classes
        # it comes from (e.g. classes that only the attackers hold)
        self.class_acc_records = []
        # --log_metrics: per eval round, macro P / R / F1 on the test set and the round's cost
        self.metric_records = []
        if (self.refusal_rule != 'none'
                and getattr(args, 'probe_fork', 'chain') == 'fork'):
            # Measured on CPU: under fork a refuser reruns its own labels from the same start,
            # so its corrected branch is a near-replica of its update and r_align goes to +0.93
            # while honest clients fall to -0.26. The ban rule cuts the BOTTOM of that ranking,
            # so it would ban the honest clients and never the refuser.
            log.warn('--refusal_rule with --probe_fork fork bans the wrong clients; '
                     'use r_norm or keep --probe_fork chain')
        if self.refusal_rule != 'none' and not self.log_signals:
            # the ban is fed by the probe scores, which are only computed when the zero-shot
            # reference exists; failing silently here would look like "the rule does nothing"
            log.warn('--refusal_rule needs --log_signals true; turning it on')
            self.log_signals = True
        self.refusal_records = []
        self.sample_records = []
        self.filter_records = []
        # --diag_scores: per round, every client's candidate noise scores (logged only)
        self.diag_records = []
        self.diag_sample_records = []
        # --sure: per round, every client's score, flag and repair counts
        self.sure_records = []
        self.nlp_records = []      # --nlprompt: per round, every client's OT split audit
        self.fedrg_records = []    # --fedrg: per round, every client's clean/noisy split audit
        self.dis_baseline = None
        # --filter_soft auto: running mean of the baseline, and the mode it currently implies.
        # Soft is the starting mode because it is the safe one -- the hard filter is what
        # collapsed the F_both run, and it collapses precisely when the teacher is weak, which
        # is exactly what the first rounds look like before the baseline has settled.
        self.dis_baseline_run = None
        # --filter_dis far: the same low quantile, taken over the look-alike-excluded score
        self.far_baseline = None
        self.filter_hard = False
        self.audit_records = []
        self.signal_records = []
        self.probe_records = []
        self.zs_text_feats = None
        self.clients = []
        self.num_shot = args.num_shot
        self.num_workers = args.num_workers
        self.client_drop_rate = args.client_drop_rate
        self.exp_name = os.path.join(
            self.dataset, args.image_backbone, self.fed_algo, self.prompt_algo)
        dtime = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
        self.tbname = os.path.join(self.exp_name, dtime)
        self.tb = History(self.tbname)
        self.client_eval = args.client_eval == 'true'
        self.precision = args.precision
        self.eval_scaler = args.eval_scaler
        self.eval_rounds = args.eval_rounds
        self.optim_name = args.optim_name
        self.momentum = args.optim_momentum
        self.weight_decay = args.optim_weight_decay
        self.learning_rate_scheduler = args.lr_scheduler
        self.loss_type = self.args.loss_type

    def init_clients(self, clientObj):
        seed_everything(self.seed)
        self.init_dataset()
        seed_everything(self.seed)      # prompt init must not depend on data-loading RNG draws
        self.init_model()
        self.build_test_cache()
        for i in range(self.num_clients):
            client = clientObj(self.args,
                            id=i,
                            trainloader=self.trainloaders[i],
                            testloader=self.testloader)
            self.set_client_attr(client)
            self.clients.append(client)

    def set_client_attr(self, client):
        # Refusing the correction is something an ATTACKER does, so a malicious-role client in
        # a run with no attack configured must still comply. The first Gate D run got this
        # wrong: its "control" still contained refusers, so it could not separate detecting
        # refusal from detecting poisoned data.
        attacking = self.attack_cfg.get('type', 'none') != 'none'
        # --attack_probe_comply makes the attacker take the other horn of the dilemma: it obeys
        # the correction, which keeps it invisible but lets the server's own labels overwrite
        # its poison. Measuring what that costs it is what makes the dilemma real rather than
        # asserted.
        forced = getattr(self.args, 'attack_probe_comply', 'false') == 'true'
        # --attacker_model data (the default from gate K on): the attacker poisons its DATA and
        # nothing else. Its device runs the stock client, so it does every step the protocol
        # asks -- trains, filters, relabels, and answers the probe honestly. That is what the
        # sample-level results always assumed; the earlier attacker also refused the probe,
        # which only a device the attacker controls could do, so one simulated client mixed two
        # threat models. 'legacy' keeps that behaviour so gates E-J can be reproduced exactly.
        model = getattr(self.args, 'attacker_model', 'data')
        mal = self.is_malicious(client.client_id) and attacking
        if model == 'data':
            client.probe_comply = True
        elif model == 'device':
            # owns its machine: refuses the probe, and skips the client-side filter entirely
            client.probe_comply = not mal
        else:
            client.probe_comply = forced or not mal
        client.device_attacker = model == 'device' and mal
        client.train_classnames = self.train_classnames
        client.test_classnames = self.test_classnames
        if self.bench == 'base2novel':
            client.testloader_base = self.testloader_base
            client.testloader_novel = self.testloader_novel
            client.test_classnames_base = self.test_classnames_base
            client.test_classnames_novel = self.test_classnames_novel


    def init_model(self,):
        log.debug(f"Loading CLIP (backbone: {self.args.image_backbone})")
        clip_model = load_clip_to_cpu(self.args.image_backbone,
                                      design_details=self.gen_design_details())

        if self.args.precision == "fp32" or self.args.precision == "amp":
            # CLIP's default precision is fp16
            clip_model.float()

        print("Turning off gradients in both the image and the text encoder")
        for name, param in clip_model.named_parameters():
            param.requires_grad_(False)

        log.debug("Building custom CLIP")

        self.model = clip_maps[self.prompt_algo](self.args, self.train_classnames,
                                                 clip_model)
        if (self.log_signals or getattr(self.args, 'sample_filter', 'none') != 'none'
                or getattr(self.args, 'diag_scores', 'false') == 'true'
                or getattr(self.args, 'sure', 'false') == 'true'):
            # CLIP's own class embeddings, the only clean reference this setting allows. The
            # sample filter needs them too, for the look-alike classes of --filter_dis far
            self.zs_text_feats = zero_shot_text_features(
                clip_model.to(self.device), self.train_classnames, self.dataset, self.device)

        print("Turning off gradients in both the image and the text encoder")
        def requires_grad_filter(name):
            requires_list = ['prompt_learner', 'decoder',]
            excludes_list = ['embedding_func',
                            'ZS_image_encoder']
            for k in requires_list:
                if k in name:
                    for e in excludes_list:
                        if e in name:
                            return False
                    return True
            return False
        for name, param in self.model.named_parameters():
            param.requires_grad_(requires_grad_filter(name))
            print(name, param.requires_grad)

        if self.args.init_weights:
            load_pretrained_weights(self.model.prompt_learner, self.args.init_weights)

        if self.args.dataset == "ImageNet":
            cuda_device = torch.device("cuda")
            self.model.to(self.device)
            self.model.text_encoder.to(cuda_device)
            self.model.text_encoder=nn.DataParallel(self.model.text_encoder)
        else:
            self.model.to(self.device)

        self.scaler = GradScaler() if self.args.precision == "amp" else None

    def init_dataset(self,):
        self.dataset_params = { 'bench': self.bench,
            'name': self.dataset, 'split': 'train', 'batch_size': self.batch_size,
            'num_clients': self.num_clients, 'num_shards': self.num_shards,
            'split_mode': self.split_mode, 'alpha': self.split_alpha,
            'beta': self.split_beta, 'parallel': True, 'data_dir': self.data_root,
            'num_shot': self.num_shot, 'data_transform': self.data_transform,
            'img_folder': self.img_folder, 'drop_last': self.drop_last,
            'seed': self.seed, 'num_workers': self.num_workers, 'subsample': 'base',
            'noise': self.noise_cfg,
        }
        Dataset = datasets_map[self.dataset]
        self.trainloaders = Dataset(**self.dataset_params)
        self.noise_report = getattr(self.trainloaders[0], 'noise_report', None)
        self.attack_report = getattr(self.trainloaders[0], 'attack_report', None)
        self.client_roles = getattr(self.trainloaders[0], 'roles', None)
        if self.noise_report is not None:
            self.excluded_client_ids = list(self.noise_report.get('excluded', []))
        if getattr(self.args, 'attack_oracle', 'none') == 'drop_malicious' and self.client_roles:
            # the ceiling for removal: perfect knowledge, acted on from round 0. Gate F measured
            # that a detector which is right but late buys +0.65; this says how much a detector
            # that is right AND instant could ever buy, which is the honest upper bound for any
            # method whose only lever is throwing clients away
            mal = [c for c, r in enumerate(self.client_roles) if r == 'malicious']
            self.excluded_client_ids = sorted(set(self.excluded_client_ids) | set(mal))
            log.info(f'- ORACLE drop_malicious: excluding clients {mal} from training')
        self.test_params = copy.deepcopy(self.dataset_params)
        self.val_params = copy.deepcopy(self.dataset_params)
        self.test_params['split'] = 'test'
        self.test_params['drop_last'] = False
        self.test_params['subsample'] = None
        self.test_params['batch_size'] = self.batch_size * self.eval_scaler
        # if self.bench == 'xdomain':
        #     self.test_params['name'] = self.target_dataset
        #     self.val_params['name'] = self.target_dataset
        self.testloader = Dataset(**self.test_params) # test all classes for eval_global
        self.val_params['split'] = 'val'
        self.val_params['drop_last'] = False
        self.val_params['batch_size'] = self.batch_size * self.eval_scaler
        self.valloader = Dataset(**self.val_params)
        if self.bench == 'dual' or self.bench == 'personal':
            self.test_params_per = copy.deepcopy(self.dataset_params)
            self.test_params_per['split'] = 'personal'
            self.test_params_per['drop_last'] = False
            self.test_params_per['subsample'] = None
            self.test_params_per['batch_size'] = self.batch_size * self.eval_scaler
            self.testloaders_per = Dataset(**self.test_params_per)
        if self.bench == 'multidomain':
            self.testloaders_mdomain = self.testloader
            self.testloader = self.testloader['real']

        self.train_classnames = list(self.trainloaders[0].dataset.dataset.classes)
        self.test_classnames = list(self.testloader.dataset.dataset.classes)
        if getattr(self.args, 'coop_classnames', 'false') == 'true':
            # update_class_names only renames class_to_idx, so the prompts kept the folder names
            from ..datasets.imageloader import replace_dicts
            rename = replace_dicts.get(self.dataset) or {}
            self.train_classnames = [rename.get(c, c) for c in self.train_classnames]
            self.test_classnames = [rename.get(c, c) for c in self.test_classnames]
            print(f"- class names given to CLIP: {self.train_classnames}")

        if self.bench == 'base2novel':
            self.test_params['subsample'] = 'base'
            self.testloader_base = Dataset(**self.test_params)
            self.test_params['subsample'] = 'new'
            self.testloader_novel = Dataset(**self.test_params)
            self.test_classnames_base = list(self.testloader_base.dataset.dataset.classes)
            self.test_classnames_novel = list(self.testloader_novel.dataset.dataset.classes)


    def build_test_cache(self):
        """ Precompute frozen image-encoder features for the shared test set (exact, cheaper). """
        if not self.cache_test_feats or self.task != 'class' or self.test_cache is not None:
            return
        if self.bench not in ('global', 'xdomain', 'dual', 'personal'):
            log.info(f'test feature cache disabled for benchmark {self.bench}')
            return
        start = time.time()
        self.test_cache = TestFeatureCache(self.model, self.testloader, self.device, self.precision)
        log.info(f'cached test features: {len(self.test_cache)} batches, '
                 f'{self.test_cache.nbytes / 1e6:.0f} MB, in {time.time() - start:.0f}s')

    def select_clients(self):
        self.cur_join_clients = self.num_join_clients
        selected_client_ids = list(np.random.choice(list(range(self.num_clients)),
                                                self.cur_join_clients, replace=False))
        if self.warmup_rounds and self.rounds < self.warmup_rounds and self.client_roles:
            # Staged participation. For the first W rounds only the clients the server already
            # trusts take part, so the global model -- which is what every correction is judged
            # against -- is built from clean labels before the noisy ones arrive.
            #
            # This assumes a trusted subset, which is NOT free: it is the same assumption
            # FLTrust makes with its clean root dataset, and it has to be declared and compared
            # against, not slipped in. It is also a real bet against data scarcity: gate A
            # measured that on DTD, losing five clients costs 7.11 points while their noise
            # only costs 6.82, so training on a fraction of the clients can easily lose more
            # than the noise it avoids. That is exactly what this experiment measures.
            trusted = [c for c in selected_client_ids if self.client_roles[c] == 'honest']
            if trusted:
                selected_client_ids = trusted
        if self.excluded_client_ids:
            # ORACLE drop_noisy: the draw itself is left untouched so the RNG stream, and
            # therefore every other run paired with this one, stays identical
            selected_client_ids = [c for c in selected_client_ids
                                   if c not in self.excluded_client_ids]
        self.cur_join_clients = len(selected_client_ids)
        return selected_client_ids

    def eval_personal(self,):
        pass

    def eval_multiple(self, *args, **kwargs):
        pass

    def receive_results(self, results):
        assert (len(self.selected_client_ids) > 0)

        active_client_ids = random.sample(self.selected_client_ids,
                        int((1-self.client_drop_rate) * self.cur_join_clients))
        states, weights, losses, accs = {}, {}, [], []
        tot_samples = 0
        attack_kind = self.attack_cfg.get('type', 'none')
        global_state = (collect_state(self.model, self.task, self.prompt_algo)
                        if attack_kind in UPDATE_ATTACKS else None)
        for c in active_client_ids:
            if results[c]['status'] != 'error':
                if results[c]['num_train_samples'] > 0:     # a client left with no image did not train
                    losses.append(results[c]['loss'])
                    accs.append(results[c]['accuracy'])
                tot_samples += results[c]['num_train_samples']
                weights[c] = results[c]['num_train_samples']
                states[c] = {
                    k: v.to(self.state_device) for k, v in results[c]['state'].items()}
                if global_state is not None and self.is_malicious(c):
                    # the update leaves the client already poisoned; simulating it here keeps
                    # the client code identical for honest and malicious participants
                    states[c] = attack_update(states[c], global_state, attack_kind,
                                              self.attack_cfg.get('scale', 5.0))
        for i, w in weights.items():
            weights[i] = w / tot_samples if tot_samples > 0 else 1.0 / len(weights)
        # the only thing the filter needs from outside the client: the federation's median
        # disagreement, one scalar per client per probe round
        reports = [(c, results[c].get('filter')) for c in states
                   if isinstance(results.get(c), dict) and results[c].get('filter')]
        if reports:
            # A LOW quantile, not the median. Half the clients are damaged in this setting,
            # so the median sits among them and every estimate comes out too small: the
            # attacker at 0.704 disagreement scored rho 0.24 against a true contamination of
            # 0.40. The baseline is supposed to describe a clean client, and with up to half
            # the federation damaged only a low quantile still does.
            vals = sorted(r['mean_dis'] for _, r in reports)
            q = float(getattr(self.args, 'filter_baseline_q', 0.25))
            self.dis_baseline = vals[min(len(vals) - 1, int(q * len(vals)))]
            far = sorted(r['dis_far'] for _, r in reports if r.get('dis_far') is not None)
            if far:
                self.far_baseline = far[min(len(far) - 1, int(q * len(far)))]
            self.choose_filter_mode()
            roles = self.client_roles
            self.filter_records.append(
                {'round': self.rounds, 'baseline': round(self.dis_baseline, 5),
                 'far_baseline': None if self.far_baseline is None else round(self.far_baseline, 5),
                 'baseline_run': round(self.dis_baseline_run, 5),
                 'hard': self.filter_hard,
                 'clients': {str(int(c)): {**r, 'role': roles[c] if roles else 'unknown'}
                             for c, r in reports}})
        diag = {str(int(c)): {**results[c]['diag'],
                               'role': self.client_roles[c] if self.client_roles else 'unknown'}
                for c in active_client_ids
                if isinstance(results.get(c), dict) and results[c].get('diag')}
        sure = {str(int(c)): {**results[c]['sure'],
                               'role': self.client_roles[c] if self.client_roles else 'unknown'}
                for c in active_client_ids
                if isinstance(results.get(c), dict) and results[c].get('sure')}
        if sure:
            self.sure_records.append({'round': self.rounds, 'clients': sure})
        nlp = {str(int(c)): {**results[c]['nlp'],
                              'role': self.client_roles[c] if self.client_roles else 'unknown'}
               for c in active_client_ids
               if isinstance(results.get(c), dict) and results[c].get('nlp')}
        if nlp:
            self.nlp_records.append({'round': self.rounds, 'clients': nlp})
        fedrg = {str(int(c)): {**results[c]['fedrg'],
                                'role': self.client_roles[c] if self.client_roles else 'unknown'}
                 for c in active_client_ids
                 if isinstance(results.get(c), dict) and results[c].get('fedrg')}
        if fedrg:
            self.fedrg_records.append({'round': self.rounds, 'clients': fedrg})
        if diag:
            self.diag_records.append({'round': self.rounds, 'clients': diag})
            for c in active_client_ids:
                rows = results[c].get('diag_rows') if isinstance(results.get(c), dict) else None
                if rows:
                    self.diag_sample_records.append({'round': self.rounds, 'client': int(c),
                                                     'rows': rows})
        self.record_signals(states, results)
        if getattr(self.args, 'tdr', 'false') == 'true':
            # global_state above only exists for update attacks; TDR needs the round's global
            # prompt whatever the attack, and self.model still holds it (aggregation is later)
            self.tdr_residualize(states, global_state if global_state is not None else
                                 collect_state(self.model, self.task, self.prompt_algo))
        if (float(getattr(self.args, 'norm_clip', 0.0)) > 0
                and getattr(self.args, 'tdr', 'false') != 'true'):
            self.clip_norms(states, collect_state(self.model, self.task, self.prompt_algo))
        if getattr(self.args, 'xval', 'none') != 'none':
            self.cross_validate(states, weights)
        if getattr(self.args, 'proto', 'none') != 'none':
            self.proto_verify(states)
        # the ban is applied after scoring and after the audit, so the records describe what the
        # clients sent and the aggregation describes what the server decided to use
        self.drop_banned(states, weights)
        avg_loss, avg_acc = np.mean(losses), np.mean(accs)
        self.tb.add_scalar('train/client/avg_loss', avg_loss, self.rounds)
        self.tb.add_scalar('train/client/avg_acc', avg_acc, self.rounds)
        if self.client_eval:
            self.tb_client_accs(results, self.rounds)
        info = (
            f'round {self.rounds}, train loss: '
            f'{avg_loss:.3f}±{np.std(losses) / avg_loss:.1%}'
            )
        return states, weights, info

    def is_malicious(self, client_id):
        return bool(self.client_roles) and self.client_roles[client_id] == 'malicious'

    def apply_probe_audit(self, results, states):
        """With probability p, a client's contribution for this round becomes its probe prompt."""
        if not self.probe_audit_prob or not self.correction_every:
            return
        audited = []
        for cid in list(states):
            probe = results[cid].get('probe') if isinstance(results.get(cid), dict) else None
            if probe is None or np.random.rand() >= self.probe_audit_prob:
                continue
            states[cid] = {k: v.to(self.state_device) for k, v in probe['state'].items()}
            audited.append(int(cid))
        if audited:
            roles = self.client_roles
            self.audit_records.append(
                {'round': self.rounds, 'audited': audited,
                 'roles': [roles[c] for c in audited] if roles else None})
            log.debug(f'- probe audit: round {self.rounds}, contributions replaced for {audited}')

    def update_refusal_flags(self, scores):
        """Ban clients whose corrected pass does not line up with the round's aggregate.

        Three things make this work where the obvious version does not, all three measured
        offline on the Gate E probe records before any of it was run on a GPU:

        * the decision uses each client's RUNNING MEAN of r_align, not the round's value. A
          single probe round is far too noisy: per-round thresholding banned 12 of 40 innocent
          clients on OxfordPets with no attacker present.
        * the threshold is median - k * spread, where spread is the MAD but never smaller than
          `refusal_floor` times the median. Without that floor a federation where everyone
          complied has near-zero MAD, so the rule always finds someone at the bottom of a tight
          cluster and accuses them.
        * nothing here looks at roles, at an assumed attacker count, or at any held-out data.
        """
        if self.refusal_rule == 'none' or len(scores) < 3:
            return
        for c, v in scores.items():
            self.refusal_history.setdefault(int(c), []).append(v['r_align'])
        self.refusal_probe_rounds += 1
        if self.refusal_probe_rounds < self.refusal_patience:
            return
        mean = {c: float(np.mean(v)) for c, v in self.refusal_history.items()}
        if self.refusal_rule == 'mad':
            vals = list(mean.values())
            med = float(np.median(vals))
            mad = float(np.median([abs(v - med) for v in vals])) * 1.4826
            cutoff = med - self.refusal_k * max(mad, self.refusal_floor * abs(med))
            flagged = [c for c, v in mean.items() if v < cutoff]
        elif self.refusal_rule == 'bottom_k':
            flagged = [c for c, _ in sorted(mean.items(), key=lambda kv: kv[1])[:int(self.refusal_k)]]
        else:
            raise ValueError(f'unknown --refusal_rule {self.refusal_rule}')
        roles = self.client_roles
        if getattr(self.args, 'refusal_action', 'ban') in ('downweight', 'flag'):
            # Re-decided from scratch each time: a client flagged by mistake (an honest one whose
            # running mean dipped) gets its weight back as soon as the mean recovers. Same cap as
            # the ban -- never more than half the federation -- ranked by how far below the cutoff.
            flagged = sorted(flagged, key=lambda c: mean[c])[:len(mean) // 2]
            self.refusal_flagged = set(flagged)
            med_all = float(np.median(list(mean.values())))
            if getattr(self.args, 'refusal_action', 'ban') == 'flag':
                self.refusal_wts = {c: 1.0 for c in flagged}      # detect only, weight untouched
            elif getattr(self.args, 'refusal_weight_mode', 'proportional') == 'proportional' \
                    and med_all > 0:
                # the detector's own evidence sets the weight: a client aligned half as well as
                # the typical client keeps half its weight. No hand-picked constant.
                self.refusal_wts = {c: float(min(1.0, max(0.0, mean[c] / med_all)))
                                    for c in flagged}
            else:
                self.refusal_wts = {c: float(getattr(self.args, 'refusal_weight', 0.25))
                                    for c in flagged}
            self.refusal_records.append(
                {'round': self.rounds, 'action': getattr(self.args, 'refusal_action', 'ban'),
                 'mean_align': {str(c): round(v, 5) for c, v in sorted(mean.items())},
                 'flagged': sorted(int(c) for c in self.refusal_flagged),
                 'weights': {str(int(c)): round(w, 4) for c, w in self.refusal_wts.items()},
                 'roles_flagged': [roles[c] for c in sorted(self.refusal_flagged)] if roles else None})
            return
        newly = sorted(c for c in flagged if c not in self.refusal_banned)
        # a rule that can accuse someone every round would eventually empty the federation;
        # never let the bans reach half the clients, whatever the rule says
        room = max(0, len(mean) // 2 - len(self.refusal_banned))
        newly = newly[:room]
        self.refusal_banned.update(newly)
        self.refusal_records.append(
            {'round': self.rounds,
             'mean_align': {str(c): round(v, 5) for c, v in sorted(mean.items())},
             'banned_now': [int(c) for c in newly],
             'banned_total': sorted(int(c) for c in self.refusal_banned),
             'roles_banned': [roles[c] for c in sorted(self.refusal_banned)] if roles else None})
        if newly:
            log.debug(f'- refusal: round {self.rounds}, banned {newly} '
                      f'({[roles[c] for c in newly] if roles else "roles unknown"})')

    def choose_filter_mode(self):
        """Pick deletion or down-weighting from the one number the server already has.

        Neither setting wins everywhere. Measured head to head on five paired seeds:

            DTD    soft +3.19, hard +2.29   soft ahead by 0.86 +- 2.07 (p = 0.40)
            Pets   soft +5.29, hard +9.62   hard ahead by 4.33 +- 1.79 (p = 0.0057)

        The mechanism is the exchange rate. Down-weighting halves both sides of the trade: a
        mistake costs a fraction of a deletion, but a correct call also earns a fraction. Where
        the filter is imprecise the first term dominates and soft wins; where it is precise
        there is almost nothing to insure against and soft only keeps half the poison it
        correctly identified. So the right mode is a function of the filter's PRECISION -- and
        precision needs the ground truth, which the server never has.

        What it does have is `dis_baseline`: the low quantile of the clients' disagreement with
        the global model, i.e. the teacher's own error rate on the cleanest clients it can see.
        That is the quantity precision ultimately rests on, and over the 460 probe rounds of the
        H_ and I_ runs it tracks realised precision at r = -0.53 (fit: precision ~ 0.868 - 0.470
        * baseline). The two datasets sit far apart on it -- DTD 0.344, Pets 0.135 -- and a
        threshold of 0.22 falls in empty space between them.

        Decided on a running mean rather than the current round, for the same reason the refusal
        rule is: a single probe round is noisy enough to flip the mode on its own. The weight
        was picked by replaying all four smoothing factors over the same records: 0.5 and 0.3
        both pick the winning mode on both datasets (DTD 17.0% / 11.3% hard, Pets 82.6% /
        79.1%) at about one flip per run, but fed a baseline oscillating between 0.10 and 0.40
        the 0.5 mean flips 29 times and the 0.3 mean once. Same answer where it is measured,
        steadier where it is not.
        """
        b = self.dis_baseline
        if b is None:
            return
        prev = self.dis_baseline_run
        a = float(getattr(self.args, 'filter_mode_alpha', 0.3))
        self.dis_baseline_run = b if prev is None else (1 - a) * prev + a * b
        if getattr(self.args, 'filter_soft', 'false') != 'auto':
            return
        thr = float(getattr(self.args, 'filter_mode_thr', 0.22))
        band = float(getattr(self.args, 'filter_mode_band', 0.02))
        run = self.dis_baseline_run
        if run < thr - band:
            self.filter_hard = True
        elif run > thr + band:
            self.filter_hard = False
        # inside the dead band the previous decision stands

    def far_neighbours(self):
        """Per class, the --filter_far_k classes nearest to it in CLIP's zero-shot text space.

        Computed once from the class names alone, so it costs no data and nothing goes on the
        wire that a client could not compute itself. Always available, so the look-alike-excluded
        disagreement is logged in every filtered run even when the budget does not use it.
        """
        if getattr(self, '_far_nb', None) is None:
            if self.zs_text_feats is None:
                return None
            t = self.zs_text_feats.float()
            t = t / t.norm(dim=-1, keepdim=True)
            sim = t @ t.T
            sim.fill_diagonal_(-2.0)
            k = max(0, int(getattr(self.args, 'filter_far_k', 1)))
            self._far_nb = [set(row.topk(k).indices.tolist()) if k else set() for row in sim]
        return self._far_nb

    def record_asr(self, collect):
        """Per attacker, on the test set: ASR towards its own target, and accuracy on the target.
        Also, over the last-10 window, the accuracy of every class (logging only)."""
        if self.rounds >= self.global_rounds - 9:
            p_all = torch.cat([p for p, _ in collect])
            y_all = torch.cat([y for _, y in collect])
            C = int(y_all.max()) + 1
            n = torch.bincount(y_all, minlength=C)
            hit = torch.bincount(y_all[p_all == y_all], minlength=C)
            self.class_acc_records.append(
                {'round': self.rounds, 'n': n.tolist(),
                 'acc': [round(float(h) / float(k), 4) if k else None
                         for h, k in zip(hit.tolist(), n.tolist())]})
        rep = self.attack_report or {}
        targets = {int(c['id']): int(c['target']) for c in rep.get('clients', [])
                   if 'id' in c and 'target' in c}
        if not targets:
            return
        pred = torch.cat([p for p, _ in collect])
        lab = torch.cat([y for _, y in collect])
        out = {}
        for cid, t in targets.items():
            other = lab != t
            own = lab == t
            out[str(cid)] = {
                'target': t,
                'asr': round(float((pred[other] == t).float().mean()), 5) if other.any() else None,
                'target_acc': round(float((pred[own] == t).float().mean()), 5) if own.any() else None}
        self.asr_records.append({'round': self.rounds, 'clients': out})

    def tdr_directions(self):
        """d_c = grad of phi_c at the current global prompt, one row per class, no images.

        phi_c(P) = mean over the zero-shot embeddings of the OTHER classes of the probability
        they give class c under prompt P -- "how much class c steals other classes". A label-flip
        attacker pushes exactly that; a client learning c from real images of c does not, which
        is why the diagonal is excluded.
        """
        learner = self.model.prompt_learner
        zs = self.zs_text_feats.to(self.device).float()
        ctx = learner.ctx
        was = ctx.requires_grad
        ctx.requires_grad_(True)
        with torch.enable_grad():
            prompts = learner()
            t = self.model.text_encoder(prompts, learner.tokenized_prompts).float()
            t = t / t.norm(dim=-1, keepdim=True)
            C = zs.shape[0]
            t = t[:C]
            p = (100.0 * zs @ t.t()).softmax(dim=-1)
            off = 1.0 - torch.eye(C, device=p.device)
            phi = (p * off).sum(0) / (C - 1)
            # Batched in chunks, keeping the graph between them. The first version asked for all
            # C rows in one batched call and fell back to a loop on failure; on Caltech101 (100
            # classes) the batched call failed after it had already freed the graph, so the
            # fallback crashed with "backward through the graph a second time".
            eye = torch.eye(C, device=p.device)
            rows = []
            for s in range(0, C, 16):
                g, = torch.autograd.grad(phi, ctx, grad_outputs=eye[s:s + 16],
                                         is_grads_batched=True, retain_graph=True)
                rows.append(g.reshape(g.shape[0], -1))
            D = torch.cat(rows)
        ctx.requires_grad_(was)
        D = D.detach().float()
        if getattr(self.args, 'tdr_center', 'false') == 'true':
            D = D - D.mean(0, keepdim=True)
        return D

    def tdr_residualize(self, states, global_state):
        """Target-direction residualisation. Per client, per round:

        a[k, c] = projection of the client's update on d_c; excess = a - median over clients;
        evidence[k] = rho * evidence[k] + (1 - rho) * excess[k] (clients never change roles and
        always take part, so a real target keeps pointing the same way while noise does not);
        target = argmax evidence; act only when that class stands out of the client's own class
        distribution by --tdr_z robust sds, after --tdr_patience rounds. Then remove only this
        round's EXCESS along the target: update -= max(0, excess) * d_target. The part of the
        update that is not an abnormal pull towards one class is kept, whoever sent it.
        """
        if self.zs_text_feats is None:
            return
        key = next((k for k in global_state if 'ctx' in k), None)
        if key is None:
            return
        D = self.tdr_directions()                                      # (C, P) on device
        norms2 = (D * D).sum(1).clamp_min(1e-12)
        g = global_state[key].reshape(-1).float().to(self.device)
        cids = [c for c in states if key in states[c]]
        if len(cids) < 3:
            return
        deltas = torch.stack([states[c][key].reshape(-1).float().to(self.device) - g for c in cids])
        if deltas.shape[1] != D.shape[1]:
            return
        A = deltas @ D.t() / norms2                                     # (K, C)
        excess = A - A.median(dim=0).values
        mode = getattr(self.args, 'tdr_target', 'proj')
        if mode == 'conc':
            # Evidence from what the client's prompt DOES, not from a linear proxy of it: the
            # zero-shot probe mass each class attracts under the client's prompt, minus what it
            # attracts under the global prompt. The projection evidence failed in gate L (right
            # 0/444 on DTD): a multi-step update is not its first-order projection, and dividing
            # by |d_c|^2 lets classes with tiny directions dominate the argmax.
            from ..signals import prompt_text_features
            zs = self.zs_text_feats.to(self.device).float()

            def mass(state):
                f = prompt_text_features(self.model, state, self.device).float()[:zs.shape[0]]
                return (100.0 * zs @ f.t()).softmax(dim=-1).mean(0)
            g_mass = mass(global_state)
            ev_in = torch.stack([mass(states[c]) - g_mass for c in cids])
        else:
            ev_in = excess
        rho = float(getattr(self.args, 'tdr_rho', 0.8))
        zthr = float(getattr(self.args, 'tdr_z', 3.0))
        self.tdr_rounds += 1
        patient = self.tdr_rounds >= int(getattr(self.args, 'tdr_patience', 3))
        rep = self.attack_report or {}
        true_t = {int(c['id']): int(c['target']) for c in rep.get('clients', [])
                  if 'id' in c and 'target' in c}
        roles = self.client_roles
        rec = {}
        new_norms = {}
        for i, c in enumerate(cids):
            ci = int(c)
            ev = self.tdr_evidence.get(ci)
            ev = ev_in[i].clone() if ev is None else rho * ev + (1 - rho) * ev_in[i]
            self.tdr_evidence[ci] = ev
            top = int(ev.argmax())
            med = ev.median()
            mad = (ev - med).abs().median() * 1.4826
            z = float((ev[top] - med) / mad.clamp_min(1e-12))
            if mode == 'true' and ci in true_t:
                top = true_t[ci]
            elif mode == 'random':
                top = self.tdr_random_class.setdefault(
                    ci, int(torch.randint(D.shape[0], (1,),
                                          generator=torch.Generator().manual_seed(1000 + ci))))
            cut = 0.0
            # evidence is kept for everyone, so it is ready the moment a client is flagged; the
            # cut itself is only for clients the refusal detector flags (--tdr_scope flagged)
            allowed = (getattr(self.args, 'tdr_scope', 'flagged') == 'all'
                       or ci in self.refusal_flagged
                       or (getattr(self.args, 'tdr_oracle_who', 'false') == 'true'
                           and self.is_malicious(ci)))
            if patient and allowed and z >= zthr:
                e = float(excess[i, top].clamp_min(0))
                if e > 0:
                    new = deltas[i] - e * D[top]
                    cut = e * float(D[top].norm())
                    deltas[i] = new
            rec[str(ci)] = {'target_hat': top, 'z': round(z, 3), 'cut_norm': round(cut, 6),
                            'flagged': bool(ci in self.refusal_flagged),
                            'role': roles[ci] if roles else None,
                            'true_target': true_t.get(ci)}
        clip = float(getattr(self.args, 'tdr_clip', 2.0))
        if clip > 0:
            nrm = deltas.norm(dim=1)
            cap = clip * nrm.median()
            scale = torch.clamp(cap / nrm.clamp_min(1e-12), max=1.0)
            # a round where nearly every update is zero (the last step of the cosine schedule)
            # has a zero median: nothing to clip, and scale 0 would only mislead the log
            scale = torch.where(nrm > 1e-12, scale, torch.ones_like(scale))
            deltas = deltas * scale.unsqueeze(1)
            # the clip applies to EVERY client, flagged or not, so it may be doing part of the
            # work credited to the cut -- log it
            for i, c in enumerate(cids):
                rec[str(int(c))]['clip_scale'] = round(float(scale[i]), 4)
        for i, c in enumerate(cids):
            src = states[c][key]
            states[c][key] = (g + deltas[i]).reshape(src.shape).to(src.dtype).to(src.device)
        self.tdr_records.append({'round': self.rounds, 'clients': rec})

    def clip_norms(self, states, global_state):
        """The gate L defence on its own: clip every client's update to --norm_clip times the
        median update norm. The same arithmetic as the clip inside tdr_residualize (which L_clip
        ran through --tdr true --tdr_z 1e9), without computing C gradient directions per round."""
        key = next((k for k in global_state if 'ctx' in k), None)
        cids = [c for c in states if key is not None and key in states[c]]
        if len(cids) < 3:
            return
        g = global_state[key].reshape(-1).float().to(self.device)
        deltas = torch.stack([states[c][key].reshape(-1).float().to(self.device) - g
                              for c in cids])
        nrm = deltas.norm(dim=1)
        cap = float(self.args.norm_clip) * nrm.median()
        scale = torch.clamp(cap / nrm.clamp_min(1e-12), max=1.0)
        scale = torch.where(nrm > 1e-12, scale, torch.ones_like(scale))
        deltas = deltas * scale.unsqueeze(1)
        rec = {}
        for i, c in enumerate(cids):
            src = states[c][key]
            states[c][key] = (g + deltas[i]).reshape(src.shape).to(src.dtype).to(src.device)
            rec[str(int(c))] = {'clip_scale': round(float(scale[i]), 4),
                                'role': self.client_roles[c] if self.client_roles else None}
        self.tdr_records.append({'round': self.rounds, 'clients': rec})

    def cross_validate(self, states, weights):
        """Score every update on the other clients' images; see flcore/xval.py.

        --xval log: record the scores only. --xval weight: turn them into aggregation weights,
        re-decided every round, so a client whose score recovers gets its weight back:
        evidence = EMA (--xval_rho) of this round's robust z-score across candidates; weight 1 up
        to --xval_z, then --xval_z / evidence.
        """
        from ..xval import feature_cache, validator_view, text_feats, weighted_ce
        cids = list(states)
        if len(cids) < 3:
            return
        for c in cids:
            if c not in self.xval_cache:
                self.xval_cache[c] = feature_cache(self, self.clients[c])
        glob = collect_state(self.model, self.task, self.prompt_algo)
        scale = float(self.model.logit_scale.exp())
        tot = sum(weights[c] for c in cids) or 1.0
        w = {c: weights[c] / tot for c in cids}
        keys = list(states[cids[0]])

        def mix(skip=None):
            ws = {c: w[c] for c in cids if c != skip}
            z = sum(ws.values()) or 1.0
            return {k: sum(states[c][k].float() * (ws[c] / z) for c in ws) for k in keys}
        T = {'global': text_feats(self, glob), 'agg': text_feats(self, mix())}
        for c in cids:
            T[('self', c)] = text_feats(self, states[c])
            T[('loo', c)] = text_feats(self, mix(skip=c))
        lie = getattr(self.args, 'xval_lie', 'smear')
        scores = {c: {'self': [], 'loo': []} for c in cids}
        for v in cids:
            feats, labels, sw = validator_view(self.clients[v], self.xval_cache[v])
            if feats is None or len(labels) == 0:
                continue
            liar = bool(getattr(self.clients[v], 'device_attacker', False)) and lie != 'none'
            base_g = weighted_ce(feats, labels, sw, T['global'], scale)
            base_a = weighted_ce(feats, labels, sw, T['agg'], scale)
            for c in cids:
                if c == v:
                    continue
                if liar:
                    # it owns its machine, so it can report anything: that everyone else hurts it
                    scores[c]['self'].append(1.0)
                    scores[c]['loo'].append(1.0)
                    continue
                scores[c]['self'].append(
                    weighted_ce(feats, labels, sw, T[('self', c)], scale) - base_g)
                scores[c]['loo'].append(
                    base_a - weighted_ce(feats, labels, sw, T[('loo', c)], scale))
        med = {c: {m: (float(torch.tensor(s).median()) if s else 0.0) for m, s in d.items()}
               for c, d in scores.items()}
        which = getattr(self.args, 'xval_score', 'loo')
        vals = torch.tensor([med[c][which] for c in cids])
        mid = vals.median()
        mad = (vals - mid).abs().median() * 1.4826
        z = (vals - mid) / mad.clamp_min(1e-12)
        rho = float(getattr(self.args, 'xval_rho', 0.8))
        z0 = float(getattr(self.args, 'xval_z', 2.0))
        act = getattr(self.args, 'xval', 'none') == 'weight'
        roles = self.client_roles
        rec = {}
        for i, c in enumerate(cids):
            ci = int(c)
            e = self.xval_evidence.get(ci)
            e = float(z[i]) if e is None else rho * e + (1 - rho) * float(z[i])
            self.xval_evidence[ci] = e
            wt = 1.0 if e <= z0 else z0 / e
            self.xval_wts[ci] = wt
            rec[str(ci)] = {'self': round(med[c]['self'], 6), 'loo': round(med[c]['loo'], 6),
                            'z': round(float(z[i]), 4), 'evidence': round(e, 4),
                            'weight': round(wt, 4), 'n_val': len(scores[c][which]),
                            'role': roles[c] if roles else None}
        self.xval_records.append({'round': self.rounds, 'score': which, 'acting': act,
                                  'clients': rec})

    def proto_verify(self, states):
        """Gate P: check every client's class prototypes against the global model, rebuild the
        update its verified prototypes imply, and (--proto replace) swap it in where the client's
        own update does not match. See flcore/proto.py.

        Replace rule, fixed before any run: verified share < --proto_share, or the cosine between
        the sent and the rebuilt update more than --proto_z robust sds below the round's median.
        """
        from ..proto import client_prototypes
        from ..xval import feature_cache, text_feats
        glob = collect_state(self.model, self.task, self.prompt_algo)
        key = next((k for k in glob if 'ctx' in k), None)
        cids = [c for c in states if key is not None and key in states[c]]
        if len(cids) < 3:
            return
        for c in cids:
            if c not in self.xval_cache:
                self.xval_cache[c] = feature_cache(self, self.clients[c])
        learner = self.model.prompt_learner
        scale_t = self.model.logit_scale.exp().float()
        T = text_feats(self, glob)
        g = glob[key].reshape(-1).float().to(self.device)
        K = int(getattr(self.args, 'proto_k', 3))
        lie = getattr(self.args, 'proto_lie', 'none')
        conf_thr = float(getattr(self.args, 'proto_conf', 0.0))
        info, rebuilt = {}, {}
        every = getattr(self.args, 'proto_every', 'round')
        period = int(getattr(self.args, 'correction_every', 0) or 1)
        fresh, forge_rep = {}, {}
        for c in cids:
            # a fresh send, or the prototypes the client sent last time. The check and the
            # rebuild still run every round, against the current global prompt
            fresh[c] = (every == 'round' or c not in self.proto_store
                        or (every == 'refresh' and self.rounds % period == 0))
            if fresh[c]:
                self.proto_store[c] = client_prototypes(self.clients[c], self.xval_cache[c], K, lie)
                if lie == 'forge' and getattr(self.clients[c], 'device_attacker', False):
                    # the attacker fabricates what it sends; it knows its own update and the
                    # global prompt it was sent, nothing about other clients
                    from ..forge import forge_prototypes
                    # target: the update it submits this round. With 'once' its single send must
                    # cover all its later updates, so it forges against the direction its
                    # poisoned data pulls in (d_c None -> computed inside forge_prototypes from
                    # its real centroids). The same fallback covers a round where its submitted
                    # update is zero (e.g. AMP skipping the first steps of a small client)
                    sub = states[c][key].reshape(-1).float().to(self.device) - g
                    d_c = None if (every == 'once' or float(sub.norm()) == 0) else sub
                    zsf = (self.zs_text_feats.to(self.device).float()
                           if self.zs_text_feats is not None else T)
                    self.proto_store[c], forge_rep[c] = forge_prototypes(
                        self, self.proto_store[c], d_c, T, zsf, scale_t)
            protos = self.proto_store[c]
            delta = states[c][key].reshape(-1).float().to(self.device) - g
            if not protos:
                info[c] = {'share': 0.0, 'cos': 0.0, 'cents': []}
                rebuilt[c] = torch.zeros_like(delta)
                continue
            P = torch.stack([p[1] for p in protos]).to(self.device)
            lab = torch.tensor([p[0] for p in protos], device=self.device)
            mass = torch.tensor([p[2] for p in protos], device=self.device)
            with torch.no_grad():
                pr = (scale_t * P @ T.t()).softmax(dim=-1)
                # CoOp starts from a random context, so for the first rounds the global prompt
                # reads images badly and would fail honest clients wholesale. CLIP's own zero-shot
                # template ("a photo of a <class>") is right on ~86% of Pets / Caltech images from
                # round 0. A centroid passes if EITHER reads it as its label; a relabelled cluster
                # (Beagles labelled "pug") is read as a beagle by both.
                zs = self.zs_text_feats
                pz = ((scale_t * P @ zs.to(self.device).float().t()).softmax(dim=-1)
                      if zs is not None else pr)
            pred = pr.argmax(dim=-1)
            conf = pr[torch.arange(len(lab)), lab]
            pred_z = pz.argmax(dim=-1)
            conf_z = pz[torch.arange(len(lab)), lab]
            ok = (((pred == lab) & (conf >= conf_thr))
                  | ((pred_z == lab) & (conf_z >= conf_thr)))
            share = float(mass[ok].sum() / mass.sum().clamp_min(1e-12))
            dhat = torch.zeros_like(delta)
            if ok.any():
                ctx = learner.ctx
                was = ctx.requires_grad
                ctx.requires_grad_(True)
                with torch.enable_grad():
                    t = self.model.text_encoder(learner(), learner.tokenized_prompts).float()
                    t = t / t.norm(dim=-1, keepdim=True)
                    logits = scale_t * P[ok] @ t[:T.shape[0]].t()
                    ce = torch.nn.functional.cross_entropy(logits, lab[ok], reduction='none')
                    loss = (ce * mass[ok]).sum() / mass[ok].sum()
                    gr, = torch.autograd.grad(loss, ctx)
                ctx.requires_grad_(was)
                dhat = -gr.reshape(-1).float().to(self.device)
            rebuilt[c] = dhat
            cos = float(torch.nn.functional.cosine_similarity(delta, dhat, dim=0)) \
                if float(dhat.norm()) > 0 and float(delta.norm()) > 0 else 0.0
            info[c] = {'share': share, 'cos': cos,
                       'cents': [[int(p[0]), round(p[2], 2), round(p[3], 3), int(pred[i]),
                                  round(float(conf[i]), 3), int(ok[i]), int(pred_z[i])]
                                 for i, p in enumerate(protos)]}
        cosv = torch.tensor([info[c]['cos'] for c in cids])
        mid = cosv.median()
        mad = (cosv - mid).abs().median() * 1.4826
        z = (cosv - mid) / mad.clamp_min(1e-6)
        norms = torch.stack([(states[c][key].reshape(-1).float().to(self.device) - g).norm()
                             for c in cids])
        med_norm = float(norms.median())
        act = getattr(self.args, 'proto', 'none') == 'replace'
        share_thr = float(getattr(self.args, 'proto_share', 0.8))
        zthr = float(getattr(self.args, 'proto_z', 2.0))
        roles = self.client_roles
        rec = {}
        for i, c in enumerate(cids):
            flag = info[c]['share'] < share_thr or float(z[i]) < -zthr
            done = False
            if act and flag:
                d = rebuilt[c]
                d = d / d.norm().clamp_min(1e-12) * med_norm if float(d.norm()) > 0 else d
                src = states[c][key]
                states[c][key] = (g + d).reshape(src.shape).to(src.dtype).to(src.device)
                done = True
            rec[str(int(c))] = {'share': round(info[c]['share'], 4), 'cos': round(info[c]['cos'], 4),
                                'z': round(float(z[i]), 3), 'flag': bool(flag), 'replaced': done,
                                'fresh': bool(fresh[c]), 'forge': forge_rep.get(c),
                                'role': roles[c] if roles else None, 'cents': info[c]['cents']}
        self.proto_records.append({'round': self.rounds, 'acting': act, 'clients': rec})

    def client_class_counts(self):
        """{client: {'true': {class: n}, 'given': {class: n}}} over each client's ORIGINAL
        training set (before any filter): which classes a client really holds, and which labels
        it trains on. Ground truth, for analysis only."""
        out = {}
        for c, cl in enumerate(self.clients):
            ds = cl.trainloader.dataset
            samples = getattr(ds, 'all_samples', None) or ds.samples
            clean = getattr(ds, 'all_clean', None) or getattr(ds, 'clean_targets', None)
            given, true = {}, {}
            for i, (_, y) in enumerate(samples):
                given[int(y)] = given.get(int(y), 0) + 1
                t = int(clean[i]) if clean is not None else int(y)
                true[t] = true.get(t, 0) + 1
            out[str(c)] = {'true': {str(k): v for k, v in sorted(true.items())},
                           'given': {str(k): v for k, v in sorted(given.items())}}
        return out

    def drop_banned(self, states, weights):
        """Remove banned clients from this round's aggregation and renormalise the weights."""
        changed = False
        if getattr(self.args, 'xval', 'none') == 'weight' and self.xval_wts:
            for c in weights:
                weights[c] *= self.xval_wts.get(int(c), 1.0)
            changed = True
        ow = float(getattr(self.args, 'oracle_mal_weight', -1.0))
        if ow >= 0:
            # ORACLE, not a method: the true attackers' weight from round 0, the ceiling of every
            # rule that works by down-weighting (0 = the attackers are simply left out)
            for c in weights:
                if self.is_malicious(c):
                    weights[c] *= ow
            changed = True
        if changed:
            total = sum(weights.values())
            if total > 0:
                for c in weights:
                    weights[c] /= total
        if self.refusal_flagged:
            # down-weight, not remove: the flagged client's prompt still counts, at a fraction
            for c in weights:
                if c in self.refusal_flagged:
                    weights[c] *= self.refusal_wts.get(int(c), 0.25)
            total = sum(weights.values())
            if total > 0:
                for c in weights:
                    weights[c] /= total
        if not self.refusal_banned:
            return
        kept = [c for c in states if c not in self.refusal_banned]
        if not kept:            # never let the ban empty the round
            return
        for c in list(states):
            if c not in kept:
                states.pop(c), weights.pop(c)
        total = sum(weights.values())
        if total > 0:
            for c in weights:
                weights[c] /= total

    def run_probes(self, results, states, global_state):
        """Score the correction probes the clients returned. Off unless --correction_every."""
        if not self.correction_every or self.zs_text_feats is None:
            return
        out = {}
        for cid in states:
            probe = results[cid].get('probe') if isinstance(results.get(cid), dict) else None
            if probe is None:
                continue
            out[int(cid)] = probe_signals(probe, states[cid], global_state, self.model,
                                          self.zs_text_feats, self.device)
        if not out:
            return
        log_probe(self.rounds, out, self.client_roles)
        self.update_refusal_flags(out)
        for cid in states:
            probe = results[cid].get('probe') if isinstance(results.get(cid), dict) else None
            rows = probe.get('samples') if probe else None
            if rows:
                role = self.client_roles[cid] if self.client_roles else 'unknown'
                self.sample_records.append(
                    {'round': self.rounds, 'client': int(cid), 'role': role, 'rows': rows})
        # the true role goes into the stored record too, not just the log line: these files are
        # what the detection study is redone from later, and a score without its label is dead
        roles = self.client_roles
        self.probe_records.append(
            {'round': self.rounds,
             'clients': {str(c): {**v, 'role': roles[c] if roles else 'unknown'}
                         for c, v in sorted(out.items())}})

    def record_signals(self, states, results=None):
        """Phase 4: score every client from its prompt alone, before aggregating."""
        if not self.log_signals or self.zs_text_feats is None or not states:
            return
        global_state = collect_state(self.model, self.task, self.prompt_algo)
        sig = client_signals(self.model, states, global_state, self.zs_text_feats, self.device)
        self.signal_records.append(log_signals(self.rounds, sig, self.client_roles))
        if results is not None:
            self.run_probes(results, states, global_state)
            # scoring first, then the audit: the signals must describe what the client sent,
            # not what the server decided to do about it
            self.apply_probe_audit(results, states)

    def aggregate(self, states, weights):
        assert (len(states) > 0)
        if self.agg_rule == 'fedavg':
            avg_state = {}
            keys = list(states[list(states)[0]])
            for k in keys:
                s = [s[k].to(self.state_device) * weights[c] for c, s in states.items()]
                avg_state[k] = sum(s).to(self.state_device)
            return avg_state
        # robust rules: they also tell us which clients they trusted, which is the
        # measurement the noisy-versus-malicious question needs
        n_mal = sum(1 for c in states if self.is_malicious(c)) or None
        avg_state, record = robust_aggregate(states, weights, self.agg_rule,
                                             self.agg_trim, n_mal)
        record['round'] = self.rounds
        if self.client_roles:
            record['excluded_roles'] = [self.client_roles[c] for c in record['excluded']]
            record['selected_roles'] = [self.client_roles[c] for c in record['selected']]
        self.agg_records.append(record)
        return {k: v.to(self.state_device) for k, v in avg_state.items()}

    def save_checkpoint(self, info, name):
        torch.save(info, name)

    def grad_func(self,):
        pass

    def run(self,):
        raise NotImplementedError

    def tb_client_accs(self, results, rounds):
        for c, rv in results.items():
            self.tb.add_scalar(f'eval/client_{c}_acc', rv['eval_acc'], rounds)

    def gen_design_details(self,):
        return None

    def save_run_info(self, results_dir):
        """--log_metrics: what is needed to trace a run: machine, code version, flags, and the
        final-round confusion matrix."""
        import socket
        version = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'CODE_VERSION.txt')
        info = {'host': socket.gethostname(),
                'gpu': torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
                'torch': torch.__version__, 'cuda': torch.version.cuda,
                'code_version': open(version).read().strip() if os.path.exists(version) else None,
                'args': vars(self.args),
                'confusion': getattr(self, 'final_confusion', None)}
        with open(os.path.join(results_dir, f'runinfo_seed_{self.seed}.json'), 'w+', encoding='utf-8') as f:
            json.dump(info, f, ensure_ascii=False, default=str)

    def summarize(self,):
        if self.bench == 'base2novel':
            exp_results = {'base': self.best_acc,
                           'novel':self.best_acc_novel,
                           'hm':self.best_acc_hm}
        elif self.bench == 'dual':
            exp_results = {'global': self.best_acc,
                           'personal': self.best_acc_per,
                           'hm': self.best_acc_hm}
        elif self.bench == 'xdomain' or self.bench == 'global':
            exp_results = {'global': self.best_acc}
        elif self.bench == 'personal':
            exp_results = {'personal': float(self.best_acc_per)}
        elif self.bench == 'multidomain':
            exp_results = {'multidomain': float(self.best_acc),
                           **self.best_acc_mds}
        else:
            raise  NotImplementedError

        print(exp_results)
        results_dir = os.path.join('results', self.exp_name, f'shot_{self.num_shot}')
        os.makedirs(results_dir, exist_ok=True)
        results_path = os.path.join(results_dir, f'exps_seed_{self.seed}.json')
        with open(results_path, 'w+', encoding='utf-8') as f:
            json.dump(exp_results, f, ensure_ascii=False, indent=4)
        f.close()
        if self.metric_records:
            # --log_metrics; its own file, so parse_results never averages it with the scores
            with open(os.path.join(results_dir, f'metrics_seed_{self.seed}.json'), 'w+',
                      encoding='utf-8') as f:
                json.dump(self.metric_records, f, ensure_ascii=False)
            self.save_run_info(results_dir)
        fedcorr = getattr(self, 'fedcorr_records', [])      # --fedcorr (server_fedcorr.py)
        if (self.noise_report is not None or self.diag_records or self.sure_records
                or self.nlp_records or fedcorr or self.fedrg_records):
            # separate file: parse_results averages every key of every 'exps*' file, so the
            # noise ground truth must not live inside the score file
            noise_path = os.path.join(results_dir, f'noise_seed_{self.seed}.json')
            with open(noise_path, 'w+', encoding='utf-8') as f:
                json.dump({'noise': self.noise_report, 'attack': self.attack_report,
                           'roles': self.client_roles, 'agg_rule': self.agg_rule,
                           'agg_records': self.agg_records,
                           'signals': self.signal_records,
                           'probes': self.probe_records,
                           'refusal': self.refusal_records,
                           'audits': self.audit_records,
                           'filter': self.filter_records,
                           'diag': self.diag_records,
                           'sure': self.sure_records,
                           'nlp': self.nlp_records,
                           'fedrg': self.fedrg_records,
                           'fedcorr': fedcorr,
                           'asr': self.asr_records,
                           'tdr': self.tdr_records,
                           'xval': self.xval_records,
                           'proto': self.proto_records,
                           'class_acc': self.class_acc_records,
                           'client_classes': self.client_class_counts()}, f, ensure_ascii=False)
            if self.diag_sample_records:
                # one row per image every --diag_samples_every rounds, for the offline design
                # of the sample-level rule; columns are listed in flcore/diag.py
                with open(os.path.join(results_dir, f'diag_samples_seed_{self.seed}.json'), 'w+',
                          encoding='utf-8') as f:
                    json.dump(self.diag_sample_records, f, ensure_ascii=False)
            if self.sample_records:
                # its own file: one row per sample per probe round is far too much to leave in
                # the file people open by hand, and it is read by a script anyway
                samp_path = os.path.join(results_dir, f'samples_seed_{self.seed}.json')
                with open(samp_path, 'w+', encoding='utf-8') as f:
                    json.dump(self.sample_records, f, ensure_ascii=False)
