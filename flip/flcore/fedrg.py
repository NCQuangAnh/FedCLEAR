"""FedRG (Wen et al., CVPR 2026) adapted to CLIP + CoOp, a comparator (`--fedrg true`).

Follows the official code, github.com/Tianjoker/FedRG: `FedRG/client.py`,
`finetune_train_VMF_ori` (stage II), `loss/SymCE_loss.py` (SCE), `model/SemiFed.py` (the noise
matrix T), `data_preprocessing/randaugment.py` and `personalized_dataset.py` (the strong view). Notes
and reasons: results/side-research/fedrg/fedrg_adaptation_notes.md; plan: fedrg_plan.md.

Kept as in the official stage II, per batch:
  1. z1, z2 = L2-normalised features of a weak and a strong view of each image
  2. vMF mixture on the sphere: L clusters (MU, KAPPA, BETA) plus a background weight PI0;
     responsibilities from softmax([log PI0, KAPPA * cos(z, MU) + log BETA] / 2)
  3. per-image concentration from the two views, kappa_i = Ainv(||(z1 + z2) / 2||), scaled by a
     running median and clipped to [0.2, 2]; it sharpens or flattens the image's responsibilities
  4. P_clean = mass of the clusters mapped to the given label (M[y]) over the total mass
  5. a 2-component GMM on 1 - P_clean of the batch; the component with the lower mean is clean,
     images with posterior >= 0.5 are clean, the rest noisy
  6. loss = 0.4 * SCE(logits, y) over the whole batch + 1.0 * NLL(log(softmax(logits) @ T), y) over
     the noisy images; SCE = 0.1 * CE + 1.0 * RCE
  7. T is renormalised to a row-stochastic matrix after each step; MU, KAPPA, BETA, PI0 and M
     follow their batch estimates with momentum 0.1, M from the clean images only
Every constant below is the official code's. T and the mixture state belong to the client and are
never aggregated (finetune_agg_include_keys = classifier_head, unsup_model); T starts at the
identity and is trained by its own SGD (lr 0.01, momentum 0.9, no weight decay), as in the code.
At test time the global prompt is used alone, without T, as the official test uses the head alone.

Adapted, because the official form cannot run in this setting (8 shots per class, CLIP):
  - the network: frozen CLIP RN50 + a learned prompt, as every other baseline here. The prompt
    plays the classifier head; the image encoder is not trained;
  - stage I (federated SimCLR from scratch) is dropped. Its job is features learned without the
    labels; CLIP's image features are that, and SimCLR cannot be learned from ~30 images a client;
  - the strong view: the official RandAugment(3, 5) put in front of this repository's train
    transform, as the official code puts it in front of its own;
  - SCELoss gets the real number of classes (the official call keeps its default of 10, which
    only runs on 10-class data);
  - rounds, batch size, client sampling, optimiser of the prompt and the data are the shared
    setting of every baseline (50 rounds, batch 16, all 10 clients, SGD 0.002 cos).
L, the number of clusters, is not given for these datasets. The paper uses 10 for CIFAR-10 and
SVHN (10 classes) and 50 for CIFAR-100 (100 classes); here L = number of classes, except 50 for
100 classes (Caltech101). --fedrg_clusters overrides it.
"""
import copy
import random

import numpy as np
import PIL
import PIL.ImageDraw
import PIL.ImageEnhance
import PIL.ImageOps
import torch
from torch.nn import functional as F
from torch.cuda.amp import autocast

# ---------------------------------------------------------------------------------------------
# the official constants (FedRG/client.py, finetune_train_VMF_ori; conf/algorithms/tcfnll.yaml)
KAPPA_INIT, KAPPA_MIN, KAPPA_MAX = 5.0, 0.5, 100.0
PI0_INIT, PI0_MIN, PI0_MAX = 0.05, 1e-3, 0.2
DP_ALPHA = 5.0               # getattr(args.algorithms, 'dp_alpha', 5.0)
DIRICHLET_SMOOTH = 0.5       # getattr(args.algorithms, 'dirichlet_smooth', 0.5)
PROTO_MOMENTUM = 0.1         # getattr(args.algorithms, 'proto_momentum', 0.1)
MIX_TEMPERATURE = 2.0        # softmax(logits_mix / 2.0)
R_CLIP = (0.2, 2.0)          # clamp of kappa_aug / median
MEDIAN_MOMENTUM = 0.9        # 0.9 * old + 0.1 * new median
GMM_THRESHOLD = 0.5          # gmm_thread
CLEAN_WEIGHT, NOISE_WEIGHT = 0.4, 1.0   # loss_weight.clean_loss / noise_loss
SCE_ALPHA, SCE_BETA = 0.1, 1.0          # SCELoss defaults
T_LR, T_MOMENTUM = 0.01, 0.9            # the stage II SGD, weight decay 0 for T
RANDAUG_N, RANDAUG_M = 3, 5             # RandAugment(3, 5, dataset)


# ---------------------------------------------------------------------------------------------
# RandAugment, verbatim from the official data_preprocessing/randaugment.py
def AutoContrast(img, _):
    return PIL.ImageOps.autocontrast(img)


def Brightness(img, v):
    assert v >= 0.0
    return PIL.ImageEnhance.Brightness(img).enhance(v)


def Color(img, v):
    assert v >= 0.0
    return PIL.ImageEnhance.Color(img).enhance(v)


def Contrast(img, v):
    assert v >= 0.0
    return PIL.ImageEnhance.Contrast(img).enhance(v)


def Equalize(img, _):
    return PIL.ImageOps.equalize(img)


def Identity(img, v):
    return img


def Posterize(img, v):  # [4, 8]
    v = int(v)
    v = max(1, v)
    return PIL.ImageOps.posterize(img, v)


def Rotate(img, v):  # [-30, 30]
    return img.rotate(v)


def Sharpness(img, v):  # [0.1,1.9]
    assert v >= 0.0
    return PIL.ImageEnhance.Sharpness(img).enhance(v)


_AFFINE = getattr(getattr(PIL.Image, 'Transform', PIL.Image), 'AFFINE', None) or PIL.Image.AFFINE


def ShearX(img, v):  # [-0.3, 0.3]
    return img.transform(img.size, _AFFINE, (1, v, 0, 0, 1, 0))


def ShearY(img, v):  # [-0.3, 0.3]
    return img.transform(img.size, _AFFINE, (1, 0, 0, v, 1, 0))


def TranslateX(img, v):  # [-150, 150] => percentage: [-0.45, 0.45]
    v = v * img.size[0]
    return img.transform(img.size, _AFFINE, (1, 0, v, 0, 1, 0))


def TranslateY(img, v):  # [-150, 150] => percentage: [-0.45, 0.45]
    v = v * img.size[1]
    return img.transform(img.size, _AFFINE, (1, 0, 0, 0, 1, v))


def Solarize(img, v):  # [0, 256]
    assert 0 <= v <= 256
    return PIL.ImageOps.solarize(img, v)


def Cutout(img, v):  # [0, 60] => percentage: [0, 0.2] => change to [0, 0.5]
    assert 0.0 <= v <= 0.5
    if v <= 0.:
        return img
    v = v * img.size[0]
    return CutoutAbs(img, v)


def CutoutAbs(img, v):  # [0, 60] => percentage: [0, 0.2]
    if v < 0:
        return img
    w, h = img.size
    x0 = np.random.uniform(w)
    y0 = np.random.uniform(h)
    x0 = int(max(0, x0 - v / 2.))
    y0 = int(max(0, y0 - v / 2.))
    x1 = min(w, x0 + v)
    y1 = min(h, y0 + v)
    xy = (x0, y0, x1, y1)
    color = (125, 123, 114)
    img = img.copy()
    PIL.ImageDraw.Draw(img).rectangle(xy, color)
    return img


def augment_list():
    return [
        (AutoContrast, 0, 1),
        (Brightness, 0.05, 0.95),
        (Color, 0.05, 0.95),
        (Contrast, 0.05, 0.95),
        (Equalize, 0, 1),
        (Identity, 0, 1),
        (Posterize, 4, 8),
        (Rotate, -30, 30),
        (Sharpness, 0.05, 0.95),
        (ShearX, -0.3, 0.3),
        (ShearY, -0.3, 0.3),
        (Solarize, 0, 256),
        (TranslateX, -0.3, 0.3),
        (TranslateY, -0.3, 0.3)
    ]


class RandAugment:
    """Official RandAugment(n, m, dataset); the cutout branch is the one every dataset but
    fmnist / SVHN takes, which is every dataset here."""
    def __init__(self, n, m):
        self.n = n
        self.m = m      # [0, 30] in fixmatch, deprecated.
        self.augment_list = augment_list()

    def __call__(self, img):
        ops = random.choices(self.augment_list, k=self.n)
        for op, min_val, max_val in ops:
            val = min_val + float(max_val - min_val) * random.random()
            img = op(img, val)
        cutout_val = random.random() * 0.5
        img = Cutout(img, cutout_val)  # for fixmatch
        return img


def strong_transform(weak):
    """The official strong view: RandAugment inserted in front of the weak (train) transform."""
    tf = copy.deepcopy(weak)
    tf.transforms.insert(0, RandAugment(RANDAUG_N, RANDAUG_M))
    return tf


# ---------------------------------------------------------------------------------------------
def l2n(x, dim=1, eps=1e-8):
    return x / (x.norm(p=2, dim=dim, keepdim=True) + eps)


def Ainv_from_R(R, d):
    R = torch.clamp(R, 1e-6, 1 - 1e-6)
    return R * (d - R ** 2) / (1 - R ** 2)


def vmf_logits(z, MU, KAPPA):
    cos = torch.matmul(z, MU.t())  # [B, G]
    return cos * KAPPA.unsqueeze(0)  # [B, G]


def sce_per_sample(logits, labels, num_classes):
    """Official SCELoss(alpha=0.1, beta=1) per sample, with the real number of classes."""
    ce = F.cross_entropy(logits, labels, reduction='none')
    p = torch.clamp(F.softmax(logits, dim=1), min=1e-7, max=1.0)
    one_hot = torch.clamp(F.one_hot(labels, num_classes).float(), min=1e-4, max=1.0)
    rce = -1 * torch.sum(p * torch.log(one_hot), dim=1)
    return SCE_ALPHA * ce + SCE_BETA * rce


def n_clusters(args, num_classes):
    L = int(getattr(args, 'fedrg_clusters', 0) or 0)
    if L > 0:
        return L
    return num_classes // 2 if num_classes >= 100 else num_classes


def _init_state(client, num_classes, d):
    """The client's mixture state and T, as the official code builds them on its first batch.
    MU is drawn from a generator of its own, so the run's other random streams do not move."""
    L = n_clusters(client.args, num_classes)
    g = torch.Generator().manual_seed(int(client.args.seed) * 1000003 + 7919 * int(client.client_id) + 1)
    MU = l2n(torch.randn(L, d, generator=g), dim=1)
    return {
        'MU': MU, 'KAPPA': torch.full((L,), KAPPA_INIT), 'BETA': torch.full((L,), 1.0 / L),
        'PI0': torch.tensor(PI0_INIT), 'M': torch.full((num_classes, L), 1.0 / num_classes),
        'kappa_median': None, 'T': torch.eye(num_classes), 'L': L, 'd': d,
    }


def _gmm_clean(w_np):
    """Official split: 2-component GMM (full covariance, reg 1e-6, 100 iterations, random_state 0)
    fitted on 1 - P_clean of the batch; returns the posterior of the lower-mean component."""
    from sklearn.mixture import GaussianMixture
    gmm = GaussianMixture(n_components=2, covariance_type="full", reg_covar=1e-6, max_iter=100,
                          random_state=0)
    gmm.fit(w_np)
    probs = gmm.predict_proba(w_np)
    clean_comp = int(np.argmin(gmm.means_.flatten()))
    return probs[:, clean_comp]


def fedrg_train(client, epochs, avg_losses, avg_add_losses, avg_accs):
    """One round of FedRG stage II local training on `client`; returns the round's audit."""
    import warnings
    from sklearn.exceptions import ConvergenceWarning
    from sklearn.metrics import roc_auc_score
    from .utils import DivergeError

    args, device, model = client.args, client.device, client.model
    ds = client.trainloader.dataset
    num_classes = model.prompt_learner.n_cls
    st = getattr(client, 'fedrg_state', None)
    T = None
    T_opt = None
    amp = args.precision == "amp"
    truth_all = list(getattr(ds, 'clean_targets', [t for _, t in ds.samples]))
    audit = {'w': [], 'noisy': [], 'split_noisy': [], 'n_batches_skipped': 0}

    ds.strong_transform = strong_transform(ds.transform)
    try:
        for e in range(epochs):
            for b, batch in enumerate(client.trainloader):
                x, y, xs, idx = batch
                bs = x.size(0)
                if bs == 1:          # official: `if bs == 1: continue`
                    audit['n_batches_skipped'] += 1
                    continue
                x, y, xs = x.to(device), y.to(device), xs.to(device)
                with torch.no_grad(), autocast(enabled=amp):
                    f1 = model.image_encoder(x.type(model.dtype))
                    f2 = model.image_encoder(xs.type(model.dtype))
                z1 = l2n(f1[0].float(), dim=1)
                z2 = l2n(f2[0].float(), dim=1)
                z = z1
                if st is None:
                    st = _init_state(client, num_classes, z.shape[1])
                if T is None:
                    T = torch.nn.Parameter(st['T'].to(device))
                    T_opt = torch.optim.SGD([T], lr=T_LR, momentum=T_MOMENTUM, weight_decay=0.0)
                MU, KAPPA, BETA = st['MU'].to(device), st['KAPPA'].to(device), st['BETA'].to(device)
                PI0, M_map = st['PI0'].to(device), st['M'].to(device)
                L, d = st['L'], st['d']

                client.optimizer.zero_grad()
                T_opt.zero_grad()
                with autocast(enabled=amp):
                    logits = model(x, y, test=False, image_features=f1)
                logits = logits.float()
                p = torch.softmax(logits, dim=1)

                with torch.no_grad():
                    logit_bg = torch.full((bs, 1), float(torch.log(PI0 + 1e-12)), device=device)
                    R = ((z1 + z2) / 2.0).norm(p=2, dim=1).clamp(1e-6, 1 - 1e-6)
                    kappa_aug = Ainv_from_R(R, d)
                    med = torch.median(kappa_aug).detach().cpu()
                    if st['kappa_median'] is None:
                        st['kappa_median'] = med
                    else:
                        st['kappa_median'] = MEDIAN_MOMENTUM * st['kappa_median'] + (1 - MEDIAN_MOMENTUM) * med
                    r_i = torch.clamp(kappa_aug / (st['kappa_median'].to(device) + 1e-8), *R_CLIP)
                    logit_g_tilde = (vmf_logits(z, MU, KAPPA) * r_i.unsqueeze(1)) + torch.log(BETA + 1e-12)
                    post_tilde = torch.softmax(torch.cat([logit_bg, logit_g_tilde], dim=1) / MIX_TEMPERATURE, dim=1)
                    gamma_bg_tilde = post_tilde[:, :1]
                    gamma_tilde = post_tilde[:, 1:]
                    M_y = M_map[y]
                    q_tilde_y = torch.sum(M_y * gamma_tilde, dim=1)
                    rest_sum = torch.sum((1.0 - M_y) * gamma_tilde, dim=1)
                    denom = q_tilde_y + rest_sum + gamma_bg_tilde.squeeze(1) + 1e-12
                    P_clean = q_tilde_y / denom
                    w_np = (1.0 - P_clean).detach().cpu().view(-1, 1).numpy()   # float32, as the official
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", ConvergenceWarning)
                    P_clean_gmm = torch.from_numpy(_gmm_clean(w_np)).to(device).float()
                clean_mask = P_clean_gmm >= GMM_THRESHOLD
                m_clean = clean_mask.float()
                m_noisy = (~clean_mask).float()

                loss_clean = sce_per_sample(logits, y, num_classes).mean()
                p_noisy = torch.matmul(p, T)
                loss_noisy_per = F.nll_loss(torch.log(p_noisy + 1e-12), y, reduction='none')
                loss_noisy = (loss_noisy_per * m_noisy).sum() / (m_noisy.sum() + 1e-8)
                loss = CLEAN_WEIGHT * loss_clean + NOISE_WEIGHT * loss_noisy
                if torch.isnan(loss).any():
                    raise DivergeError('Training loss diverged to NaN.')
                if amp:
                    client.scaler.scale(loss).backward()
                    client.scaler.step(client.optimizer)
                    client.scaler.step(T_opt)
                    client.scaler.update()
                else:
                    loss.backward()
                    client.optimizer.step()
                    T_opt.step()

                with torch.no_grad():
                    T.data = T.data.clamp_min(1e-6)
                    T.data /= T.data.sum(dim=1, keepdim=True)
                    # mixture update after every batch (mix_update_interval 1)
                    sum_vec = torch.matmul(gamma_tilde.t(), z)
                    count = torch.sum(gamma_tilde, dim=0)
                    bg_count = torch.sum(gamma_bg_tilde)
                    N_cg = torch.zeros_like(M_map)
                    if m_clean.sum() > 0:
                        N_cg.index_add_(0, y, gamma_tilde * m_clean.unsqueeze(1))
                    new_mu = l2n(sum_vec.clone(), dim=1)
                    MU = l2n(MU * (1 - PROTO_MOMENTUM) + PROTO_MOMENTUM * new_mu, dim=1)
                    R_g = (sum_vec.norm(p=2, dim=1) / (count + 1e-8)).clamp(1e-6, 1 - 1e-6)
                    new_kappa = Ainv_from_R(R_g, d).clamp(KAPPA_MIN, KAPPA_MAX)
                    KAPPA = KAPPA * (1 - PROTO_MOMENTUM) + PROTO_MOMENTUM * new_kappa
                    total = count.sum() + bg_count
                    prior = DP_ALPHA / L
                    new_beta = (count + prior) / (count.sum() + prior * L + 1e-12)
                    new_pi0 = (bg_count + (DP_ALPHA * 0.1)) / (total + DP_ALPHA * 0.1 + 1e-12)
                    BETA = BETA * (1 - PROTO_MOMENTUM) + PROTO_MOMENTUM * new_beta
                    PI0 = (PI0 * (1 - PROTO_MOMENTUM) + PROTO_MOMENTUM * new_pi0).clamp(PI0_MIN, PI0_MAX)
                    if N_cg.sum().item() > 0:
                        M_new = (N_cg + DIRICHLET_SMOOTH) / (torch.sum(N_cg + DIRICHLET_SMOOTH, dim=1, keepdim=True) + 1e-12)
                        M_map = M_map * (1 - PROTO_MOMENTUM) + PROTO_MOMENTUM * M_new
                        M_map = M_map / (M_map.sum(dim=1, keepdim=True) + 1e-12)
                    st.update({'MU': MU.cpu(), 'KAPPA': KAPPA.cpu(), 'BETA': BETA.cpu(),
                               'PI0': PI0.cpu(), 'M': M_map.cpu()})

                truth = torch.tensor([int(truth_all[int(i)]) for i in idx])
                audit['w'] += (1.0 - P_clean).cpu().tolist()
                audit['noisy'] += (y.cpu() != truth).tolist()
                audit['split_noisy'] += (~clean_mask).cpu().tolist()
                avg_losses.add(loss.detach())
                avg_add_losses.add(model.add_loss())
                avg_accs.add(client.metric(logits, y))
    finally:
        ds.strong_transform = None
    if st is not None and T is not None:
        T.data.clamp_(min=1e-6)
        T.data /= T.data.sum(dim=1, keepdim=True)
        st['T'] = T.detach().cpu()
    client.fedrg_state = st

    noisy = np.array(audit['noisy'], dtype=bool)
    split = np.array(audit['split_noisy'], dtype=bool)
    w = np.array(audit['w'], dtype=float)
    auroc = None
    if noisy.any() and (~noisy).any():
        auroc = round(float(roc_auc_score(noisy, w)), 4)
    report = {'n': int(len(noisy)), 'noise': round(float(noisy.mean()), 4) if len(noisy) else None,
              'split_noisy': int(split.sum()), 'split_noisy_truly_noisy': int((split & noisy).sum()),
              'truly_noisy': int(noisy.sum()), 'auroc': auroc,
              'skipped_batches': audit['n_batches_skipped']}
    if st is not None:
        report.update({'L': st['L'], 'T_diag': round(float(torch.diagonal(st['T']).mean()), 4),
                       'pi0': round(float(st['PI0']), 4)})
    return report
