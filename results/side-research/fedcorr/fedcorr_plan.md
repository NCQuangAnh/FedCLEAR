# FedCorr + CoOp baseline (pre-registered 2026-10-26)

FedCorr: Xu, Chen, Quek, Chong, "FedCorr: Multi-Stage Federated Learning for Label Noise Correction", CVPR 2022. Official code: github.com/Xu-Jingyi/FedCorr. The code here follows its `main.py` stage by stage.

Where the code lives:
- `flip/flcore/servers/server_fedcorr.py`: the three stages;
- `flip/flcore/fedcorr.py`: LID, losses, the GMM split, relabelling;
- `flip/flcore/clients/client_fedavg.py`: `_prox` (the adaptive proximal term) and `_mixup`.

Flag: `--fedcorr true`; the arm is `corr`.

## Runs

There are 33 runs, `S_<sc>_corr` and `N_<x>_corr` on Pets, DTD and Caltech101. They use the same 11 settings, seeds, protocol and server as FedProx (`queue_baselines`), so every run pairs by seed with PromptFL, FedProx, NLPrompt and CLEAR-FPL.

The queue is `server/queue_fedcorr.txt`. Results go to `results/server/queue_fedcorr/`.

## What is kept from the official code

- **Pre-processing:** T1 = 5 iterations (the CIFAR-10 value). In each iteration:
  - every client trains once, one at a time in random order;
  - each client starts from the latest global model, and its trained model becomes the new global model (one client per step, as in every official setting).
- **Adaptive proximal term:** β·μ̂_k·‖w − w_global‖.
  - β = 5;
  - the norm itself, not squared;
  - applied from the second batch of an epoch on;
  - μ̂_k is the client's noise level estimated in the previous iteration, 0 in the first.
- **Client detection:**
  - LID (k = 20) of the client's trained-model softmax on its own images;
  - accumulated over the iterations;
  - a 2-component GMM; the high component is the noisy set.
- **Noise level of a noisy client:** a 2-component GMM on its per-image losses; μ̂_k is the share of images in the high-loss component. The loss is the official one, cross-entropy applied to the softmax output.
- **Correction after each iteration:** of the int(n·μ̂_k·0.5) highest-loss images, those the global model predicts with confidence > 0.5 take the predicted label.
- **Fine-tuning:** FedAvg over the clients with μ̂_k ≤ 0.1 only. Afterwards, every image of the noisy set predicted with confidence > 0.5 takes the predicted label.
- **Usual training:** FedAvg over all clients with the corrected labels. Corrected labels stay corrected.
- **Mixup** (α = 1) in local training in every stage.
- **No proximal term** after pre-processing.
- **Hyper-parameters:** relabel_ratio 0.5, confidence 0.5, clean threshold 0.1, β 5. These are the CIFAR-10/100 values. The Clothing1M values (0.8 / 0.9) were tuned for real noise; ours is synthetic, like CIFAR's.

## Adaptations (none of them tuned on our data)

| | official | here | why |
|---|---|---|---|
| model | ResNet trained end to end | CoOp prompt, CLIP RN50 frozen | the setting of the thesis |
| local training | lr 0.03, momentum 0.5, batch 10, 5 epochs | lr 0.002, momentum 0.9, batch 16, 1 epoch, cosine | same as every other arm, so only the method differs |
| rounds | T1 = 5, T2 = 500, T3 = 450 | T1 = 5, T2 = 23, T3 = 23 (51 logged rounds) | the 50-round budget of every arm. One iteration trains each client once, the same cost as one round. T2 : T3 ≈ 1 : 1 as in the official settings |
| clients per round in stages 2-3 | frac2 = 0.1 | all eligible clients | our protocol trains every client every round |
| LID and loss computed on | training images with the training transform | the same images, test transform | deterministic, and the same view every other score in this repo uses |
| LID with fewer than 21 images | k = 20 in the formula anyway | k = min(20, n − 1) | the official formula is wrong when n ≤ 20; the 30-80 images per client here make this common |
| empty fine-tuning set | crashes (division by zero) | the clients with the lowest μ̂ | needed when every client is noisy; logged as `fallback` |
| client with < 3 images | — | LID = median of the iteration | LID is undefined there |

## What is compared

Means over 5 seeds of last10, paired by seed, per setting and dataset, against:
- PromptFL (`none`);
- FedProx (`prox`);
- NLPrompt (`nlp`);
- CLEAR-FPL (`full` / `clear`).

Logged in `noise_seed_*.json` under `fedcorr`:
- per iteration: each client's LID, accumulated LID, the noisy set, μ̂, the relabel counts (fixed / broken against the true labels), and the noise left;
- the fine-tuning set and whether the fallback was used;
- the correction after fine-tuning.

## Predictions (reported whatever happens)

FedCorr is a comparator. No decision about CLEAR depends on it.

- **P1, client detection by LID:**
  - weak on Pets: AUROC of the accumulated LID, noisy versus honest, < 0.6 in S_sym, S_pair and S_inst;
  - good on Caltech: ≥ 0.8.
  - Basis: gate D measured LID AUROC 0.38 / 0.76 / 0.92 for Pets / DTD / Caltech. That was on PromptFL's local prompts, not on FedCorr's sequential training, so it is a prediction, not a certainty.
- **P2, the clean federation:** the GMM always splits clients into two groups. So in S_clean some honest clients are called noisy and lose correct labels: broken > 0 in at least 4 of 5 seeds on every dataset.
- **P3, every client noisy:** FedCorr fine-tunes on noisy clients in every N setting, because there is no clean client to find. Its gain over PromptFL, averaged over the 6 N settings, is smaller than CLEAR-FPL's on each dataset.
- **P4, estimate error:** mean |μ̂_k − true noise| over the clients in the noisy set is larger than CLEAR v2's audit error (≤ 0.10 predicted in `clear2_plan.md`) on Pets and DTD.

## Known risks

- **The proximal term has a fixed pull.** Its gradient has size β·μ̂_k whatever the distance, so in pre-processing a noisy client barely leaves the global prompt. This is what the official code does. It lasts 5 of the 51 rounds.
- **The global model swings in pre-processing.** One client per step on Dirichlet-0.1 data makes the global model follow the last client trained, so accuracy in rounds 0-4 means little. Those rounds are outside last10.
