import copy
import torch
import argparse
import os
import time
import warnings
import numpy as np
import torchvision
import logging
import json
import random



from flcore.servers import get_server
from flcore.utils import seed_everything
from flcore.pretty.logger import log


def parse_results(args):
    exp_name = os.path.join(args.dataset, args.image_backbone, args.fed_algo, args.prompt_algo)
    results_dir = os.path.join('results', exp_name, f'shot_{args.num_shot}')
    json_files = [os.path.join(results_dir, file) for file in os.listdir(results_dir) if 'exps' in file]

    with open(json_files[0], 'r') as json_file:
            json_data = json.load(json_file)
            accs = {k: [] for k in json_data.keys()}

    results = copy.deepcopy(accs)
    for file in json_files:
        with open(file) as json_file:
            json_data = json.load(json_file)
            for k,v in json_data.items():
                accs[k].append(v)
    for k,v in accs.items():
        results[k].append(np.mean(v)) # mean
        results[k].append(np.std(v)) # var
    with open(os.path.join(results_dir, 'summary.json'), 'w+') as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
    f.close()



def special_args(args):
    if args.prompt_algo == 'CoCoOp':
        args.batch_size = 1
        args.eval_scaler = 1
    if args.prompt_algo == 'OTP':
        args.fed_algo = 'FedOTP'
        args.num_prompt = 2
    if args.prompt_algo == 'BPL':
        args.batch_size = 1
        args.eval_scaler = 1
    if args.prompt_algo == 'ProDA':
        args.prompt_batch_size = 1
    if args.prompt_algo == 'CLIP':
        args.ctx_init = 'a photo of a'
    if args.central == 'true':
        args.fed_algo = 'Central'
    if args.prompt_algo == 'MaPLe':
        args.fed_algo = 'MaPLe'
        assert 'ViT' in args.image_backbone, 'MaPLe requires Transformer vision encoder'
        assert args.num_prompt == 1, 'MaPLe requires num_prompt = 1'
    if args.prompt_algo == 'PGP':
        args.fed_algo = 'FedPGP'
    if args.prompt_algo == 'Folio':
        args.fed_algo = 'Folio'
    if args.prompt_algo == 'DPFPL':
        args.precision = 'fp32'
        args.fed_algo = 'FedDPFPL'
    return args

def main(args):
    if args.deterministic == 'true':
        torch.manual_seed(args.seed)
        random.seed(args.seed)
        np.random.seed(args.seed)
        torch.backends.cudnn.benchmark = False
        # torch.use_deterministic_algorithms(True)
    if args.verbose:
        log.level = 'verbose'
    elif args.verbose2:
        log.level = 'debug'
    for i in range(args.times):
        # run i is fully determined by args.seed + i (see ServerBase.__init__)
        seed_everything(args.seed + i)
        log.info(f'run {i}, seed {args.seed + i}')
        server = get_server(args, i)
        start = time.time()
        server.run()
        end = time.time()
        log.info(f'Experiment run: {i}, Total time ellapsed: {int(end-start)}s')
    parse_results(args)



if __name__ == "__main__":
    total_start = time.time()

    parser = argparse.ArgumentParser()
    # general
    parser.add_argument('-task', "--task", type=str, default='class',
                                        choices=['class', 'seg', ], )
    parser.add_argument('-bench', "--benchmark", type=str, default="global",
                        choices=['dual', 'global', 'personal',
                                 'base2novel', 'xdomain', 'multidomain', 'xdataset'])
    parser.add_argument('-falg', "--fed_algo", type=str, default='FedAvg',
                                        choices=['FedAvg', 'FedOTP', ], )
    parser.add_argument('-palg', "--prompt_algo", type=str, default="CoOp",
                                        choices=['CLIP', 'CoOp', 'CoCoOp', 'PLOT',
                                                 'ALIGN', 'ProDA', 'ProGrad', 'PromptSRC',
                                                 'KgCoOp','OTP', 'PGP',
                                                 'TPG', 'DPFPL', 'MaPLe', 'Folio',
                                                 'DenseCoOp'])
    parser.add_argument('-ctr', "--central", type=str, default='false')
    parser.add_argument('-did', "--device_id", type=int, default=0)
    parser.add_argument('-t', "--times", type=int, default=1)
    parser.add_argument('-sfn', "--save_folder_name", type=str, default='summary')
    parser.add_argument('-slurm', "--slurm", type=str, default='false', choices=['true', 'false'])
    parser.add_argument('-detm', "--deterministic", type=str, default='true', choices=['true', 'false'])
    parser.add_argument("--verbose", action='store_true')
    parser.add_argument("--verbose2", action='store_true')
    # model
    parser.add_argument('-ibb', "--image_backbone", type=str, default='RN50',
                                                    choices=['RN50', 'RN101', 'ViT-B/16'])
    parser.add_argument('-m', "--model", type=str, default="resnet50")
    # dataset
    parser.add_argument('-data', "--dataset", type=str, default="caltech101")
    parser.add_argument('-tdata', "--target_dataset", type=str, default="caltech101")
    parser.add_argument('-root', "--data_root", type=str, default="~/data/prompt")
    parser.add_argument('-dnt', "--num_shot", type=int, default=1)
    parser.add_argument('-dns', "--num_shards", type=int, default=10)
    parser.add_argument('-dsm', "--split_mode", type=str, default='dirichlet',
                        choices=['dirichlet', 'iid', 'task','predefined'])
    parser.add_argument('-dsa', "--split_alpha", type=float, default=1)
    parser.add_argument('-dsb', "--split_beta", type=float, default=1)
    parser.add_argument('-dtf', "--data_transform", type=str, default="default",
                        choices=['default', 'default_norm', 'paper', 'randaug'])
    parser.add_argument('-dlt', "--drop_last", type=str, default='false', choices=['true', 'false'])
    # client label noise (phase 2). Noise is injected after the Dirichlet split, so a noisy
    # run and a clean run with the same seed see exactly the same client partition.
    parser.add_argument('-nt', "--noise_type", type=str, default='none',
                        choices=['none', 'sym', 'pair', 'instance'],
                        help="sym: uniform flip; pair: flip to the next class; "
                             "instance: instance-dependent (Xia et al. 2020), on raw pixels")
    parser.add_argument('-nr', "--noise_rate", type=float, default=0.0,
                        help="flip rate of a noisy client")
    parser.add_argument('-nm', "--noise_mode", type=str, default='uniform',
                        choices=['uniform', 'hetero'],
                        help="uniform: every noisy client uses --noise_rate; "
                             "hetero: rates spread evenly over (0, --noise_rate]")
    parser.add_argument('-ncf', "--noisy_client_frac", type=float, default=0.5,
                        help="fraction of clients that are noisy")
    parser.add_argument('-nor', "--noise_oracle", type=str, default='none',
                        choices=['none', 'clean', 'drop_noisy'],
                        help="clean: inject then restore the labels (must match a 0%% run); "
                             "drop_noisy: exclude noisy clients, the ceiling for client-level triage")
    # malicious clients (phase 3). Roles are disjoint: honest, noisy, or malicious.
    parser.add_argument('-at', "--attack_type", type=str, default='none',
                        choices=['none', 'targeted_flip', 'noise_disguise', 'scale', 'signflip'],
                        help="targeted_flip/noise_disguise poison the labels; "
                             "scale/signflip poison the prompt update that is sent back")
    parser.add_argument('-ar', "--attack_rate", type=float, default=0.4,
                        help="flip rate for noise_disguise; matched to --noise_rate by default")
    parser.add_argument('-mcf', "--malicious_client_frac", type=float, default=0.0,
                        help="fraction of clients that are malicious (drawn before the noisy ones)")
    parser.add_argument('-asc', "--attack_scale", type=float, default=5.0,
                        help="multiplier for the scale attack")
    parser.add_argument('-agg', "--agg_rule", type=str, default='fedavg',
                        choices=['fedavg', 'median', 'trimmed_mean', 'krum', 'multikrum'],
                        help="server aggregation rule; the robust ones also log which clients "
                             "they kept, which is how we measure noisy-vs-malicious confusion")
    parser.add_argument('-agt', "--agg_trim", type=float, default=0.1,
                        help="fraction trimmed at each end for trimmed_mean")
    parser.add_argument('-alie', "--attack_lie", type=str, default='mimic', choices=['mimic', 'big'],
                        help="how a malicious client answers the correction probe. mimic: run the "
                             "correction privately, report the gain it would have earned, send back "
                             "the uncorrected prompt. big: invent a large drop. mimic is the harder "
                             "case and the default")
    parser.add_argument('-pap', "--probe_audit_prob", type=float, default=0.0,
                        help="probability that a probe round's contribution is taken from the "
                             "correction probe instead of the client's own update. This is what "
                             "makes refusing or forging cost the attacker its attack")
    parser.add_argument('-atm', "--attacker_model", type=str, default='data',
                        choices=['data', 'device', 'legacy'],
                        help="'data': the attacker only poisons its labels; its device runs the "
                             "stock client and follows every step (train, filter, relabel, answer "
                             "the probe honestly). 'device': the attacker owns its machine -- it "
                             "poisons its labels, refuses the probe, never filters or relabels, and "
                             "reports the broadcast baseline as its own disagreement so it looks "
                             "clean. 'legacy': the gates E-J attacker, which refused the probe but "
                             "still filtered -- kept only to reproduce those runs")
    parser.add_argument('-apc', "--attack_probe_comply", type=str, default='false',
                        choices=['true', 'false'],
                        help="make the malicious clients comply with the probe, to measure what "
                             "complying costs them")
    parser.add_argument('-ceq', "--correction_every", type=int, default=0,
                        help="phase 5: every N rounds, ask each client to redo one pass with the "
                             "global model's predictions as labels, and score the response. "
                             "0 disables the probe")
    parser.add_argument('-clb', "--correction_labels", type=str, default='corrected',
                        choices=['corrected', 'own'],
                        help="control: 'own' runs the probe exactly as usual but leaves the "
                             "labels alone. Same extra epoch, same returned prompt, same audit "
                             "-- only the relabelling is removed, so whatever gain survives is "
                             "not label repair")
    parser.add_argument('-pfk', "--probe_fork", type=str, default='chain',
                        choices=['chain', 'fork'],
                        help="where the corrected pass starts. 'chain' (current) appends it to "
                             "the prompt the client just trained, so an audited contribution "
                             "still carries that client's own epoch. 'fork' restarts from the "
                             "global prompt, giving a genuine alternative update -- but it "
                             "likely breaks the refusal detector, which is the point of the "
                             "comparison")
    parser.add_argument('-wup', "--warmup_rounds", type=int, default=0,
                        help="staged participation: for the first W rounds only clients the "
                             "server trusts (role 'honest') take part, so the global model is "
                             "built from clean labels before the noisy ones join. Assumes a "
                             "trusted subset, the same assumption FLTrust makes with a clean "
                             "root dataset; declare it and compare against it")
    parser.add_argument('-sfl', "--sample_filter", type=str, default='none',
                        choices=['none', 'rho', 'both', 'proto'],
                        help="stop training on a client's own suspect samples instead of "
                             "dropping the client. 'rho': drop the worst-loss fraction, where "
                             "the fraction is each client's own contamination estimate. "
                             "'both': that plus every sample in a class the global model "
                             "contradicts almost everywhere, which is what catches a targeted "
                             "attack that small-loss is blind to")
    parser.add_argument('-fcb', "--filter_clean_band", type=float, default=0.0,
                        help="amnesty: a client whose estimated contamination is at or below "
                             "this is left completely alone. Honest clients estimated 0.03-0.05 "
                             "and damaged ones 0.33-0.44, so a band around 0.10 costs nothing "
                             "and removes every false drop on a clean client")
    parser.add_argument('-fsf', "--filter_soft", type=str, default='false',
                        choices=['true', 'false', 'auto'],
                        help="weight suspect samples down instead of deleting them. Dropping a "
                             "clean sample was measured to cost 1.34x what dropping a damaged "
                             "one gains, which puts break-even precision at 57.3%; a weight "
                             "makes a mistake cost a fraction of that. 'auto' lets the server "
                             "choose per probe round from --filter_mode_thr: neither setting "
                             "wins everywhere -- on DTD soft is ahead by 0.86 (p=0.40) and on "
                             "OxfordPets hard is ahead by 4.33 (p=0.006)")
    parser.add_argument('-fmt', "--filter_mode_thr", type=float, default=0.22,
                        help="under --filter_soft auto: delete outright while the clean "
                             "baseline disagreement stays below this, weight down above it. "
                             "The baseline is what the server already computes, so this costs "
                             "no extra communication. Calibrated offline on the H_/I_ filter "
                             "records, where baseline predicts the filter's realised precision "
                             "at r = -0.53 over 460 probe rounds: DTD sits at 0.344 mean "
                             "baseline / 65.7% precision and Pets at 0.135 / 85.3%. At 0.22 the "
                             "rule picks soft on 82.6% of DTD rounds and hard on 93.5% of Pets "
                             "rounds, which is the setting that won on each")
    parser.add_argument('-fma', "--filter_mode_alpha", type=float, default=0.3,
                        help="weight of the newest probe round in the running mean of the "
                             "baseline that --filter_soft auto decides on. Lower is steadier")
    parser.add_argument('-frl', "--filter_relabel", type=str, default='none',
                        choices=['none', 'all', 'conf', 'prior'],
                        help="in the hard path, replace a suspect's label with the global "
                             "model's guess instead of deleting it, wherever the two disagree. "
                             "'conf' only where the global model is at least "
                             "--filter_relabel_conf sure; the rest are deleted as before. Under "
                             "--filter_soft auto this only ever runs once the server has judged "
                             "the global model good enough to delete on")
    parser.add_argument('-frlg', "--filter_relabel_log", type=str, default='false',
                        help="log, every filter refresh, each sample's label, true label and the "
                             "global model's top-3 classes with probabilities, so other relabel "
                             "rules can be scored offline on the same suspects. Diagnostic only")
    parser.add_argument('-frc', "--filter_relabel_conf", type=float, default=0.5,
                        help="softmax confidence the global model needs before its guess "
                             "replaces a suspect's label under --filter_relabel conf")
    parser.add_argument('-fmb', "--filter_mode_band", type=float, default=0.02,
                        help="dead band around --filter_mode_thr. The decision is taken on a "
                             "running mean of the baseline and must clear the threshold by this "
                             "margin to flip, so a dataset sitting near the boundary settles on "
                             "one mode instead of alternating every probe round")
    parser.add_argument('-fsm', "--filter_soft_mode", type=str, default='rank',
                        choices=['rank', 'score'],
                        help="how the soft weights are spaced. 'rank' walks the ranking in "
                             "equal steps; 'score' derives the weight from the suspicion score "
                             "itself and rescales so the total removed still matches the "
                             "budget, so equally suspect samples are weighted equally")
    parser.add_argument('-fsn', "--filter_score_norm", type=str, default='robust',
                        choices=['robust', 'minmax'],
                        help="how --filter_soft_mode score turns a suspicion score into a "
                             "weight. 'minmax' lets a single outlier set the scale and flattens "
                             "everything else; 'robust' centres on the median and scales by the "
                             "IQR, so the bulk keeps its spread and the tail is clipped")
    parser.add_argument('-fwm', "--filter_w_min", type=float, default=0.0,
                        help="weight given to the most suspect sample under --filter_soft")
    parser.add_argument('-fmc', "--filter_min_class", type=int, default=0,
                        help="a class with fewer samples than this is never flagged by the "
                             "class rule: with the global model wrong 45% of the time, three "
                             "samples reach full disagreement by luck alone")
    parser.add_argument('-fct', "--filter_cls_thr", type=float, default=0.9,
                        help="class-disagreement threshold for --sample_filter both")
    parser.add_argument('-fdis', "--filter_dis", type=str, default='all',
                        choices=['all', 'far'],
                        help="which disagreement sets the budget. 'all' counts every image the "
                             "global model labels differently. 'far' does not count an image "
                             "whose predicted class is one of the --filter_far_k classes nearest "
                             "to its label in CLIP's zero-shot text space: an honest client "
                             "holding look-alike classes (two bulldog breeds) is contradicted "
                             "there by the model's own confusion, not by wrong labels. The mode "
                             "choice (soft/hard) still uses 'all', so only the budget changes")
    parser.add_argument('-ffk', "--filter_far_k", type=int, default=1,
                        help="number of nearest classes excluded under --filter_dis far")
    parser.add_argument("--prox_mu", type=float, default=0.0,
                        help="FedProx proximal weight on the prompt (0 = plain FedAvg)")
    # FedCorr (CVPR 2022) + CoOp, a comparator (flcore/servers/server_fedcorr.py); defaults are the
    # official CIFAR-10 values (github.com/Xu-Jingyi/FedCorr, README)
    parser.add_argument("--fedcorr", type=str, default='false', choices=['true', 'false'],
                        help="FedCorr's three stages: pre-processing with LID client detection and "
                             "loss-GMM correction, fine-tuning on clean clients, usual training")
    parser.add_argument("--fedcorr_iters", type=int, default=5, help="pre-processing iterations (T1)")
    parser.add_argument("--fedcorr_ft_rounds", type=int, default=-1,
                        help="fine-tuning rounds (T2); -1 = half the rounds left after pre-processing")
    parser.add_argument("--fedcorr_beta", type=float, default=5.0,
                        help="weight of the adaptive proximal term in pre-processing")
    parser.add_argument("--fedcorr_relabel_ratio", type=float, default=0.5,
                        help="share of a noisy client's estimated noisy images considered for relabelling")
    parser.add_argument("--fedcorr_conf", type=float, default=0.5,
                        help="the global prompt must be more confident than this to relabel an image")
    parser.add_argument("--fedcorr_clean_thres", type=float, default=0.1,
                        help="clients with an estimated noise level at most this form the fine-tuning set")
    parser.add_argument("--fedcorr_mixup", type=float, default=1.0,
                        help="mixup alpha in FedCorr's local training (0 = off)")
    # NLPrompt (CVPR 2025) on every client (flcore/nlprompt.py), a comparator
    parser.add_argument("--nlprompt", type=str, default='none', choices=['none', 'uniform', 'hist'],
                        help="uniform: NLPrompt's OT split with a uniform class marginal; hist: the "
                             "client's label histogram as class marginal")
    parser.add_argument("--nlprompt_reg", type=float, default=0.01, help="Sinkhorn entropy (REG_E)")
    # FedRG (CVPR 2026) adapted to CLIP + prompt, a comparator (flcore/fedrg.py)
    parser.add_argument("--fedrg", type=str, default='false', choices=['true', 'false'],
                        help="FedRG stage II on every client: vMF geometry of CLIP features, a GMM "
                             "clean/noisy split per batch, SCE + a per-client noise matrix")
    parser.add_argument("--fedrg_clusters", type=int, default=0,
                        help="vMF clusters L; 0: number of classes, 50 for 100 classes (the paper's "
                             "CIFAR-10 / SVHN / CIFAR-100 choices)")
    # gate D stage 2: the surprise-based method (flcore/sure.py)
    parser.add_argument("--sure", type=str, default='false', choices=['true', 'false'],
                        help="score each client by the excess surprise of its labels, flag it "
                             "above --sure_tau, and repair a flagged client's suspect images")
    parser.add_argument("--sure_dist", type=str, default='e', choices=['e', 'g'],
                        help="e: global prompt averaged with zero-shot CLIP; g: global prompt only")
    parser.add_argument("--sure_score", type=str, default='xs_m', choices=['xs_m', 'xs', 'dis', 'xs_mb'],
                        help="client score: merged excess surprise, plain excess surprise, or the "
                             "old disagreement")
    parser.add_argument("--sure_tau", type=float, default=0.05,
                        help="flag threshold on the client score (Pets clean 95th percentile)")
    parser.add_argument("--sure_scope", type=str, default='flagged', choices=['flagged', 'all'],
                        help="repair flagged clients only, or every client (ablation)")
    parser.add_argument("--sure_img_thr", type=float, default=0.1,
                        help="an image is a suspect when P(label) is below this")
    parser.add_argument("--sure_relabel_conf", type=float, default=0.5,
                        help="a suspect is relabelled to P's top class when P is this sure, "
                             "otherwise left out of the round")
    parser.add_argument("--sure_budget", type=str, default='none', choices=['none', 'excess'],
                        help="excess: a flagged client repairs at most (suspects - suspects expected "
                             "under P for correct labels) images")
    parser.add_argument("--sure_unsure", type=str, default='drop', choices=['drop', 'keep'],
                        help="what happens to a suspect P cannot relabel confidently")
    parser.add_argument("--sure_max_frac", type=float, default=0.6,
                        help="at most this share of a client's images is ever touched")
    parser.add_argument("--sure_audit", type=str, default='false', choices=['true', 'false'],
                        help="CLEAR-FPL v2: estimate the client's noise rate from zero-shot CLIP, flag "
                             "it by a one-sided test, repair round(rate * n) least plausible images "
                             "(replaces --sure_tau, --sure_img_thr and --sure_max_frac)")
    parser.add_argument("--sure_audit_merge", type=str, default='false', choices=['true', 'false'],
                        help="merge each label with its nearest class in the noise-rate estimate")
    parser.add_argument("--sure_audit_alpha", type=float, default=0.05,
                        help="false-flag rate of the one-sided test on the noise-rate estimate")
    parser.add_argument("--sure_cal", type=str, default='none', choices=['none', 'noise'],
                        help="noise: calibrate P every round with one pooled, noise-aware temperature; "
                             "flag also on the calibrated score; suspects = labels outside the "
                             "calibrated prediction set (replaces --sure_img_thr and --sure_max_frac; "
                             "results/side-research/calrepair/calrepair_plan.md)")
    parser.add_argument("--sure_cal_tau", type=float, default=0.384,
                        help="flag threshold on the calibrated score (its Pets-clean 95th percentile)")
    parser.add_argument("--sure_cal_alpha", type=float, default=0.05,
                        help="a label outside the calibrated (1 - alpha) prediction set is a suspect")
    parser.add_argument("--sure_cal_flag", type=str, default='true', choices=['true', 'false'],
                        help="false: --sure_cal does not add its own flag on the calibrated score; "
                             "only CLEAR-FPL's flag decides who repairs")
    parser.add_argument("--sure_cal_tmax", type=float, default=0.0,
                        help="> 0: the broadcast temperature is min(fitted T, this); 1 never lets "
                             "the calibration soften P (results/side-research/calrepair/gatec_plan.md)")
    parser.add_argument("--sure_cal_floor", type=str, default='false', choices=['true', 'false'],
                        help="true: a flagged client suspects at least round(eps0 * n) images, eps0 its "
                             "own noise estimate frozen at its first calibrated round "
                             "(results/side-research/calrepair/gatef_plan.md)")
    # referee-strength gate (results/side-research/calrepair/gate_confirm_plan.md)
    parser.add_argument("--sure_gate", type=float, default=0.0,
                        help="> 0: run CLEAR-FPL for --sure_gate_rounds rounds, then switch to "
                             "--sure_cal's repair for the rest of the run only if the one-sided 95%% "
                             "lower bound of relabelled / suspects over rounds 1..R is at least this")
    parser.add_argument("--sure_gate_rounds", type=int, default=5,
                        help="rounds 1..R of CLEAR-FPL that the gate reads before deciding")
    parser.add_argument('-dgs', "--diag_scores", type=str, default='false',
                        choices=['true', 'false'],
                        help="gate D: every round, log each client's candidate noise scores "
                             "(disagreement, look-alike-excluded disagreement, excess surprise, "
                             "loss, LID) for the global prompt, zero-shot CLIP and their mix, "
                             "and for the trained local prompt. Logged only (flcore/diag.py)")
    parser.add_argument('-dge', "--diag_samples_every", type=int, default=0,
                        help="with --diag_scores, also write one row per image every this many "
                             "rounds to diag_samples_seed_*.json (0 = off)")
    parser.add_argument("--diag_full_probs", type=str, default='false', choices=['true', 'false'],
                        help="with --diag_samples_every, add every class's log-probability under "
                             "the global prompt and under zero-shot CLIP to each row (logged only)")
    parser.add_argument('-fbq', "--filter_baseline_q", type=float, default=0.25,
                        help="quantile of the clients' mean disagreement used as the clean "
                             "baseline. The median is wrong when up to half the federation is "
                             "damaged, because then the median is damaged too")
    parser.add_argument('-frf', "--filter_rho_floor", type=float, default=0.0,
                        help="minimum budget for a client the baseline already judged dirty, "
                             "as a fraction of its samples. 0 leaves the estimate alone")
    parser.add_argument('-fmf', "--filter_max_frac", type=float, default=0.6,
                        help="never let the filter drop more than this fraction of one "
                             "client's samples, whatever the rules say")
    parser.add_argument('-fst', "--filter_start", type=int, default=0,
                        help="first round the filter may act")
    parser.add_argument('-sdg', "--sample_diag", type=str, default='false',
                        choices=['true', 'false'],
                        help="diagnostic: log every candidate sample-level signal (training "
                             "loss, global-model confidence and agreement, the client's own "
                             "agreement, the label) next to the ground truth, so the detection "
                             "AUC of each can be scored offline. Never feeds any rule")
    parser.add_argument('-cau', "--correction_audit", type=str, default='false',
                        choices=['true', 'false'],
                        help="diagnostic: at each probe round, compare the global model's "
                             "proposed labels against the ground truth the noise injector kept, "
                             "and log how many labels the correction FIXES versus BREAKS. Never "
                             "feeds the algorithm; one forward pass, costs seconds")
    parser.add_argument('-ccf', "--correction_conf", type=float, default=0.0,
                        help="confidence gate on the correction: keep the client's own label "
                             "wherever the global model is not sure enough. 0 disables it, "
                             "which is the naive version gate E and gate F measured")
    parser.add_argument('-ccm', "--correction_conf_mode", type=str, default='quantile',
                        choices=['quantile', 'abs'],
                        help="how --correction_conf is read. 'quantile': the fraction of each "
                             "client's samples to LEAVE ALONE, so 0.5 relabels the surest half "
                             "and needs no per-dataset tuning. 'abs': a raw softmax threshold, "
                             "which does not transfer between datasets because CLIP's logit "
                             "scale makes the softmax very peaked")
    parser.add_argument('-sor', "--sample_oracle", type=str, default='none',
                        choices=['none', 'drop_dirty', 'restore_dirty', 'drop_dirty_mal'],
                        help="sample-level oracle, a ceiling and not a method. 'drop_dirty' "
                             "deletes exactly the samples whose label was changed; "
                             "'restore_dirty' puts the true label back. Applied after both the "
                             "noise and the attack, so it covers damage from either")
    parser.add_argument('-ato', "--attack_oracle", type=str, default='none',
                        choices=['none', 'drop_malicious'],
                        help="oracle control: remove the malicious clients from round 0. The "
                             "ceiling for any defence whose only action is exclusion")
    parser.add_argument('-rex', "--refusal_rule", type=str, default='none',
                        choices=['none', 'mad', 'bottom_k'],
                        help="phase 6: stop aggregating clients that refuse the correction. "
                             "'mad' flags r_align below median - k*MAD within the round, which "
                             "needs no assumed attacker count; 'bottom_k' flags the k lowest")
    parser.add_argument('-rac', "--refusal_action", type=str, default='ban',
                        choices=['ban', 'downweight', 'flag'],
                        help="what a refusal flag does. 'ban': removed from aggregation for good "
                             "(gates F-J). 'downweight': its aggregation weight is multiplied by "
                             "--refusal_weight, and the flag is re-decided every probe round, so a "
                             "client flagged by mistake recovers its weight. 'flag': decide and "
                             "record the flags, change no weight -- for --tdr_scope flagged")
    parser.add_argument('-rwt', "--refusal_weight", type=float, default=0.25,
                        help="aggregation weight multiplier for a flagged client under "
                             "--refusal_action downweight with --refusal_weight_mode fixed")
    parser.add_argument('-rwm', "--refusal_weight_mode", type=str, default='proportional',
                        choices=['proportional', 'fixed'],
                        help="'proportional': a flagged client keeps weight = its running "
                             "r_align / the federation's median, clipped to [0, 1] -- the "
                             "detector's own evidence sets the weight. 'fixed': --refusal_weight")
    parser.add_argument("--coop_classnames", type=str, default='false', choices=['true', 'false'],
                        help="feed CLIP the readable class names of CoOp (e.g. EuroSAT 'Annual Crop "
                             "Land' instead of the folder name 'AnnualCrop'). The renaming tables "
                             "existed but never reached the prompts; 'false' keeps the old runs "
                             "reproducible. Only EuroSAT changes among our datasets")
    parser.add_argument("--log_metrics", type=str, default='false', choices=['true', 'false'],
                        help="every eval round, macro precision / recall / F1 on the test set, and "
                             "the cost of the round: wall time, client training time, peak GPU "
                             "memory, bytes sent and received. Written to metrics_seed_<seed>.json")
    parser.add_argument('-asr', "--log_asr", type=str, default='false', choices=['true', 'false'],
                        help="diagnostic: every eval, for each attacker's target class t, log the "
                             "share of test images of other classes predicted as t (attack "
                             "success rate) and the accuracy on real images of t. Test set only")
    parser.add_argument('-tdr', "--tdr", type=str, default='false', choices=['true', 'false'],
                        help="target-direction residualisation: estimate, per client and over "
                             "rounds, the class its update pulls other classes towards (from the "
                             "CLIP text encoder alone, no images), and remove only the part of "
                             "that pull above the federation's median. Needs --log_signals true")
    parser.add_argument('-tdrs', "--tdr_scope", type=str, default='flagged',
                        choices=['flagged', 'all'],
                        help="whose update TDR may cut. 'flagged': only clients the refusal "
                             "detector currently flags. A careless client's noise is spread over "
                             "every class and is repaired on its own machine by the sample filter; "
                             "cutting its update would only remove clean learning. Only a client "
                             "that refuses to repair its data has to be repaired at the server")
    parser.add_argument('-tdro', "--tdr_oracle_who", type=str, default='false',
                        choices=['true', 'false'],
                        help="ORACLE, not a method: TDR may cut the true malicious clients from "
                             "round 0 instead of waiting for the refusal detector. The gap to the "
                             "same arm without it is the most that any fix for the early rounds -- "
                             "rollback included -- could buy")
    parser.add_argument('-ncl', "--norm_clip", type=float, default=0.0,
                        help="clip every client's prompt update to this many times the median "
                             "update norm (the gate L defence, without TDR's direction machinery). "
                             "0 = off. Ignored when --tdr true, which clips on its own")
    parser.add_argument('-xv', "--xval", type=str, default='none',
                        choices=['none', 'log', 'weight'],
                        help="cross-client validation (flcore/xval.py): the other clients score "
                             "each update on their own images. 'log' records only; 'weight' also "
                             "sets aggregation weights from it")
    parser.add_argument('-xvs', "--xval_score", type=str, default='loo', choices=['loo', 'self'],
                        help="'loo': loss of the aggregate minus the aggregate without the client; "
                             "'self': loss of the client's prompt minus the round's global prompt")
    parser.add_argument('-xvr', "--xval_rho", type=float, default=0.8,
                        help="memory of the per-client evidence (exponential average)")
    parser.add_argument('-xvz', "--xval_z", type=float, default=2.0,
                        help="weight 1 up to this evidence, then xval_z / evidence")
    parser.add_argument('-xvl', "--xval_lie", type=str, default='smear',
                        choices=['smear', 'none'],
                        help="what a device attacker reports as a validator. 'smear': that every "
                             "other update hurts it. 'none': the truth (a control)")
    parser.add_argument('-pro', "--proto", type=str, default='none',
                        choices=['none', 'log', 'replace'],
                        help="gate P (flcore/proto.py): clients also send k-means centroids of "
                             "their image features per label; the server checks each against the "
                             "global model and rebuilds the update the verified ones imply. 'log' "
                             "records only; 'replace' swaps the rebuilt update in for flagged "
                             "clients")
    parser.add_argument('-prk', "--proto_k", type=int, default=3,
                        help="centroids per label (k-means), so genuine and relabelled images of "
                             "one label land in different clusters")
    parser.add_argument('-prc', "--proto_conf", type=float, default=0.0,
                        help="a centroid passes only if the global model gives its label at least "
                             "this probability (0 = top-1 is enough)")
    parser.add_argument('-prs', "--proto_share", type=float, default=0.8,
                        help="flag a client whose verified prototype mass is below this share")
    parser.add_argument('-prz', "--proto_z", type=float, default=2.0,
                        help="flag a client whose sent-vs-rebuilt cosine is this many robust sds "
                             "below the round's median")
    parser.add_argument('-prl', "--proto_lie", type=str, default='none',
                        choices=['none', 'hide', 'turncoat', 'forge'],
                        help="device attacker's prototypes. 'none': honest prototypes of the data "
                             "it trains on. 'hide': prototypes of its clean images only, while it "
                             "still sends the poisoned update. 'turncoat': as 'hide', and it also "
                             "trains only on its clean images for its first --turncoat_rounds "
                             "rounds, so the prototypes the server stores early look honest. "
                             "'forge': moves its real centroids until both readers pass them and "
                             "their rebuild points along its poisoned update (flcore/forge.py)")
    parser.add_argument('-tcr', "--turncoat_rounds", type=int, default=1,
                        help="--proto_lie turncoat: how many opening rounds it behaves honestly")
    parser.add_argument('-pre', "--proto_every", type=str, default='round',
                        choices=['round', 'refresh', 'once'],
                        help="how often a client sends fresh prototypes. 'round': every round. "
                             "'refresh': only in rounds where the client re-runs its filter "
                             "(every --correction_every rounds). 'once': only in its first round. "
                             "Between sends the server checks and rebuilds from the last ones")
    parser.add_argument('-prb', "--proto_band", type=str, default='false',
                        choices=['true', 'false'],
                        help="--sample_filter proto with K_fixconf's two safeguards: clients "
                             "inside the clean band are left alone, and relabel/delete happen only "
                             "in hard rounds (soft rounds down-weight suspects instead)")
    parser.add_argument('-omw', "--oracle_mal_weight", type=float, default=-1.0,
                        help="ORACLE: multiply the true attackers' aggregation weight by this from "
                             "round 0 (0 = leave them out). Negative = off")
    parser.add_argument('-tdrt', "--tdr_target", type=str, default='proj',
                        choices=['proj', 'conc', 'true', 'random'],
                        help="how TDR picks the class to cut. 'proj': the class whose gradient "
                             "direction the update projects on most (gates L: right 0% on DTD, "
                             "~8% on Pets). 'conc': the class the client's own prompt gives more "
                             "zero-shot probe mass than the global prompt does, averaged over "
                             "rounds -- the signal that voted the right target 6-8 of 10 times "
                             "offline. 'true': ORACLE, the attacker's real target (non-attackers "
                             "keep 'proj'); measures what perfect targeting is worth. 'random': "
                             "CONTROL, a fixed random class per client; if it scores like the "
                             "others, the gain is damping, not targeting")
    parser.add_argument('-tdrr', "--tdr_rho", type=float, default=0.8,
                        help="memory of the per-client target evidence (exponential average)")
    parser.add_argument('-tdrz', "--tdr_z", type=float, default=3.0,
                        help="act only when the top class's evidence is this many robust "
                             "standard deviations above the client's median class")
    parser.add_argument('-tdrp', "--tdr_patience", type=int, default=3,
                        help="rounds of evidence before any cut")
    parser.add_argument('-tdrc', "--tdr_center", type=str, default='false', choices=['true', 'false'],
                        help="remove the direction every class shares before comparing classes. "
                             "Off by default: tools/check_target_directions.py measured that the "
                             "raw directions are already distinct at a realistic prompt (mean "
                             "pairwise cosine 0.22 DTD / 0.26 Pets, none above 0.9), while "
                             "centering makes them WORSE (0.69 / 0.77, some pairs at 1.0) -- the "
                             "classes whose raw direction is near zero all collapse onto minus "
                             "the mean")
    parser.add_argument('-tdrk', "--tdr_clip", type=float, default=2.0,
                        help="after the cut, clip any update to this many times the median norm; "
                             "0 disables")
    parser.add_argument('-rk', "--refusal_k", type=float, default=2.0,
                        help="threshold for --refusal_rule: MAD multiplier for 'mad', number of "
                             "clients for 'bottom_k'")
    parser.add_argument('-rpat', "--refusal_patience", type=int, default=3,
                        help="how many probe rounds must pass before any ban, so the running "
                             "mean of r_align is built from more than one noisy observation")
    parser.add_argument('-rfl', "--refusal_floor", type=float, default=0.12,
                        help="minimum spread for the 'mad' rule, as a fraction of the median. "
                             "Without it a federation where everyone complied has near-zero "
                             "MAD and the rule accuses whoever happens to sit lowest")
    parser.add_argument('-lsig', "--log_signals", type=str, default='false', choices=['true', 'false'],
                        help="phase 4: score every client from its prompt each round and log the "
                             "scores with its true role, for the detection study")
    parser.add_argument('-dpl', "--parallel", type=str, default='true', choices=['true', 'false'])
    parser.add_argument('-dnw', "--num_workers", type=int, default=8)
    # general federated learning settings
    parser.add_argument('-nc', "--num_clients", type=int, default=4)
    parser.add_argument('-cevl', "--client_eval", type=str, default='false', choices=['true', 'false'])
    parser.add_argument('-gr', "--global_rounds", type=int, default=100)
    parser.add_argument('-le', "--local_epochs", type=int, default=1,
                        help="Multiple update steps in one local epoch.")
    parser.add_argument('-tf', "--train_fraction", type=float, default=1.)
    parser.add_argument('-cdr', "--client_drop_rate", type=float, default=0)
    # optimization
    parser.add_argument('-opn', "--optim_name", type=str, default='sgd')
    parser.add_argument('-orho', "--optim_rho", type=float, default=0.01)
    parser.add_argument('-lrs', "--lr_scheduler", type=str, default='', choices=['', 'cos'])
    parser.add_argument('-lbs', "--batch_size", type=int, default=8)
    parser.add_argument('-lvbs', "--eval_scaler", type=int, default=1)
    parser.add_argument('-evrds', "--eval_rounds", type=int, default=1)
    parser.add_argument('-lr', "--local_learning_rate", type=float, default=0.005,
                        help="Local learning rate")
    parser.add_argument('-omt', "--optim_momentum", type=float, default=0.9,)
    parser.add_argument('-owd', "--optim_weight_decay", type=float, default=0.0001,)
    parser.add_argument('-lrd', "--learning_rate_decay", type=bool, default=False)
    parser.add_argument('-lrdg', "--learning_rate_decay_gamma", type=float, default=0.99)
    parser.add_argument('-prec', "--precision", type=str, default="fp32", choices=['fp32', 'fp16', 'amp'])
    parser.add_argument('-iws', "--init_weights", type=str, default=None,)
    parser.add_argument('-lst', "--loss_type", type=str, default='ce', choices=['ce', 'bce', 'mae'])
    parser.add_argument('-gcn', "--grad_clipping_norm", type=float, default=0.,)
    parser.add_argument('-seed', "--seed", type=int, default=0)
    parser.add_argument('-ctf', "--cache_test_feats", type=str, default='false',
                        choices=['true', 'false'],
                        help='precompute frozen image-encoder features for the test set')
    # prompt learning general settings
    parser.add_argument('-npt', "--num_prompt", type=int, default=1)
    parser.add_argument('-nptv', "--num_prompt_vision", type=int, default=1)
    parser.add_argument('-nctx', "--num_context", type=int, default=4)
    parser.add_argument('-ctp', "--class_token_position", type=str, default='end')
    parser.add_argument('-csc', "--class_specific_context", type=str, default='false', choices=['true', 'false'])
    parser.add_argument('-cti', "--ctx_init", type=str, default='')
    # prompt learning algorithms' settings
    parser.add_argument('-pbsz', "--prompt_batch_size", type=int, default=0) # ProDA
    parser.add_argument('-pgpbt', "--pgp_bottleneck", type=int, default=8) # PGP bottleneck
    parser.add_argument('-frac', "--folio_frac", type=float, default=0.2) # PromptFolio
    parser.add_argument('-dprank', "--dpfpl_rank", type=int, default=8) # DP-FPL
    parser.add_argument('-noise', "--noise", type=float, default=0.4) # DP-FPL
    parser.add_argument('-nthr', "--norm_thresh", type=float, default=10) # DP-FPL
    parser.add_argument('-fact', "--factorization", type=str, default='dpfpl') # DP-FPL
    parser.add_argument('-pdepth', "--prompt_depth", type=int, default=1) # MaPLe
    # segmentation task settings
    parser.add_argument('-stls', "--seg_text_loss_scale", type=float, default=1) #
    # FL algorithms' settings

    args = parser.parse_args()
    args.data_root = os.path.expanduser(args.data_root)
    if args.slurm == 'true':
        print(f'Job {args.prompt_algo} allocated GPU: {os.environ["CUDA_VISIBLE_DEVICES"]}')
        args.device_id = int(os.environ["CUDA_VISIBLE_DEVICES"])
    else:
        os.environ["CUDA_VISIBLE_DEVICES"] = str(args.device_id)

    args = special_args(args)
    main(args)