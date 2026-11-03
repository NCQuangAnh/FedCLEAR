# Image-side referee and confident learning: offline screens (pre-registered)

Written 2026-11-03, before any number of these screens was computed. Motivation: on MNIST / EuroSAT
CLEAR's client flag catches about half of the noisy clients (`clip-dependence` study, stage 0 NO GO).
Literature check (2026-11-03): CLIP RN50's image features are strong where its class-name side is
weak (linear probe MNIST 98.3 / EuroSAT 95.2 against our zero-shot 57.7 / 26.1; Pets 88.2 / ~86).
CLEAR's referee P = 1/2 (global prompt + zero-shot) only uses the class-name side. Two old ideas
are screened offline, no training run.

## Screen 1: confident learning (Northcutt et al., JAIR 2021) on the stage 0 logs

Data: `referee_calib/stage0_*` (PromptFL, logged only, full per-image log-probabilities, 3 seeds,
rounds 10-50); settings D sym / pair / het / clean on all five datasets, N sym50 / pair50 on MNIST
and EuroSAT. Referee e = CLEAR's P.

Rule (no constant of ours): per (seed, round) the server gets, per class j, the sum of e_j over
the images labelled j and their count from every client (2K numbers per client), and sets
t_j = mean e_j over the images labelled j (CL's per-class threshold, the average self-confidence).
An image with label y is marked when some class k != y has e_k >= t_k and, among the classes that
pass their threshold, the largest e_k is not y (CL's off-diagonal of the confident joint). There
is no client flag: every client's images are judged.

Compared with CLEAR-FPL on the same client-rounds: an image is marked by CLEAR when its client's
xs_m > 0.05 and e_y < 0.1 (v1 suspect rule).

Measures, pooled over settings, seeds and rounds 10-50:
- recall = share of wrong labels marked;
- false marks = share of correct labels marked.

Pass rules:
- G1 MNIST: CL recall >= CLEAR recall + 20 points (mixed D settings and N settings pooled).
- G2 MNIST: CL false marks <= 10%.
- G3 Pets, DTD, Caltech101, each: CL false marks <= CLEAR false marks + 5 points, and CL recall
  >= CLEAR recall - 5 points.
- EuroSAT: the same numbers are reported as the confirmation, not required.
GO for a real arm if G1, G2 and G3 pass.

## Screen 2: image-side referee from class prototypes (MNIST / EuroSAT, local proof of principle)

Only the MNIST and EuroSAT images are on this machine (`.smoke/data_{mnist,eurosat}`: 60 train and
30 test images per class, real images). The old datasets need a feature dump on Kaggle, which is a
later step and only if this screen passes.

Simulation per seed (20 seeds), mirroring the repository: 8 images per class drawn from the local
train pool; each class's images spread over 10 clients with Dirichlet(0.1) proportions; noise as
`flcore/datasets/noise.py` with the arms' flags (S sym / pair: rate 0.4 on 3 of 10 clients;
S het: sym, hetero, rate 0.8 on 5 clients; S clean; N sym50 / pair50: every client). Image features
and zero-shot text features from CLIP RN50 with the repository's templates and class names.

Referees (probability of each class for every training image):
- z: zero-shot CLIP;
- proto_fed: cosine to the federated class prototypes (normalised mean feature of the images
  labelled k over all clients; what clients would send: per-class feature sums and counts);
- proto_local: the same with each client's own images only (closer to FedRG, which keeps its
  clusters on the client);
- mix: 1/2 (z + proto_fed).

Main measure: image-level AUROC of the given label's probability, wrong vs correct labels (scale
free, so no threshold or temperature is chosen). Reference: the same AUROC for CLEAR's e on the
stage 0 runs of the same dataset and settings (different images, same setup; the global prompt in
e has trained for 10-50 rounds, which the simulation cannot reproduce).

Pass rules:
- P1 MNIST: AUROC(proto_fed) >= AUROC(CLEAR e, stage 0) + 0.05 and >= AUROC(z) + 0.05.
- P2 EuroSAT: the same, as the confirmation.
- Sanity check before reading P1 / P2: zero-shot test accuracy on the local test images within 10
  points of the logged value (MNIST 57.7, EuroSAT 26.1); otherwise the local pool is not
  representative and the screen is void.
Exploratory, no rule: proto_local vs proto_fed (why FedRG's per-client geometry fails here),
CL marks on proto_fed, N pair settings where prototypes follow the majority (wrong) label.

If P1 passes: ask the user before the Kaggle feature dump of all five datasets and before any arm.

## Outcome (2026-11-03, after both screens)

Both screens are NO GO by the rules above. Tables: `screen_cl.md`, `screen_proto.md`.

- Screen 1, confident learning: MNIST recall 24.9% -> 75.2% (G1 pass), but false marks 16.8%
  (G2 fail, limit 10%). On the old datasets the recall drops (Pets 89 -> 77, Caltech 96 -> 78) and
  the false marks rise (DTD 4 -> 30%) (G3 fail). A per-class threshold only moves along the same
  ranking; it cannot add information.
- Screen 2, prototypes: pooled AUROC proto_fed 0.788 (MNIST) / 0.811 (EuroSAT) vs CLEAR e 0.852 /
  0.816 and z 0.864 / 0.840 (P1, P2 fail). Sanity ok (local zero-shot 57.7 / 33.3%).
- Exploratory reading:
  - Image prototypes beat the text side only where most labels are right (D settings, EuroSAT
    0.90-0.94 vs CLEAR e 0.78-0.88). They are built from the noisy labels, so they collapse when
    every client is noisy (N sym50 0.80-0.82) and invert under pair noise (N pair50 ~0.5,
    N pair75 0.15-0.18). Zero-shot CLIP never reads a label and stays at 0.82-0.90 whatever the
    noise: the reason CLEAR anchors on it.
  - Per-client prototypes (FedRG-like geometry on the client's own ~8 images) are near chance,
    0.47-0.69: a likely reason FedRG falls below PromptFL on MNIST / EuroSAT.
  - mix = 1/2 (z + proto_fed) is the best pooled referee (0.871 / 0.856), +0.02 / +0.04 over CLEAR e,
    below the +0.05 bar; it inherits the prototype collapse in N pair settings.
- Thesis use: limitation section. The image-level ranking ceiling (AUROC ~0.85) is shared by every
  label-free reference tried; label-built references (prototypes, CL, GMM on loss) trade it for
  dependence on the noise level.
