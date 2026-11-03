# FedRG (CVPR 2026), CLIP-adapted: run plan, fixed 2026-10-31 before any real run

FedRG (Wen et al., "FedRG: Unleashing the Representation Geometry for Federated Learning with Noisy Clients", CVPR 2026) is added as a comparator. The user asked for it, and it is the most recent federated noisy-label method.

- Code: `flip/flcore/fedrg.py`, flag `--fedrg true`, arms `S_<sc>_rg` and `N_<x>_rg`.
- What is kept, what is adapted and why: `fedrg_adaptation_notes.md`. The module docstring repeats it.

## Method as run

**Stage II of the official code, unchanged.** Per batch:
1. CLIP features of a weak and a strong view.
2. A vMF mixture on the sphere, with L clusters plus a background component.
3. A per-image concentration taken from the two views.
4. `P_clean`: how much of an image's cluster mass maps to its given label.
5. A 2-component GMM on `1 − P_clean` of the batch, threshold 0.5.
6. Loss = 0.4 · SCE over the batch + 1.0 · NLL through the client's noise matrix T over the noisy part.

T and the mixture state stay on the client and are never aggregated. Every constant is the official one.

**Adapted, because the official form cannot run with 8 shots per class:**
- CLIP RN50 is frozen; only the prompt is learned, as in every baseline.
- Stage I (SimCLR from scratch) is replaced by CLIP's image features.
- The strong view is the official RandAugment(3, 5) put in front of this repository's train transform.
- SCE gets the real number of classes. The official call hardcodes 10.

**Fixed here, because the paper gives no value for these datasets.**

| Number of clusters L | Value | Source |
|---|---|---|
| MNIST, EuroSAT (10 classes) | 10 | as CIFAR-10 / SVHN |
| Caltech101 (100 classes) | 50 | as CIFAR-100 |
| Pets (37) | 37 | number of classes |
| DTD (47) | 47 | number of classes |

**The shared setting of every baseline:**
- 50 rounds, batch size 16, all 10 clients every round;
- the prompt trained with SGD, lr 0.002, cosine;
- T trained with its own SGD (lr 0.01, momentum 0.9), as in the official stage II.

None of this is changed after a run has been seen.

## Runs

- Datasets: Pets, DTD and Caltech101. MNIST and EuroSAT are added later if wanted.
- Settings: the 11 settings of every baseline, 5 seeds, the same seeds as PromptFL, FedProx, FedCorr, NLPrompt and CLEAR-FPL.
- Total: 33 runs on Kaggle. The notebooks are listed below once they are built.

## What is reported

The results are reported, not judged, like every baseline:
- last10, paired with PromptFL and CLEAR-FPL over the 5 seeds;
- `python tools/analyze_baselines.py` adds the FedRG column.

Logged per client and round (noise json key `fedrg`), for the analysis only:
- the AUROC of `1 − P_clean` against the true noisy labels;
- the size of the noisy split and how much of it is truly noisy;
- the mean diagonal of T and the background weight.

## Predictions, written before the runs

1. **Close to PromptFL in the S settings and on clean data, within about 1 point.** SCE on clean labels behaves like CE, and T starts at the identity.
2. **Above PromptFL at 50-75% noise, where SCE's robust term matters,** but below CLEAR-FPL in most noisy settings. FedRG's detector has to estimate dozens of clusters from 10-40 images per client, and each client keeps its own clusters.
3. **Detector AUROC well below what the paper reports on CIFAR.** It should be lowest on Pets and DTD, where L is close to the number of images a client holds.

If prediction 3 fails, i.e. the detector works well, that is reported as it stands.

## Notebooks (built 2026-10-31, code zip of 2026-10-31)

| notebook | runs | estimate |
|---|---|---|
| `kaggle/rg_pets_1` | S sym, pair, inst, het, clean, N sym25 | about 7 h |
| `kaggle/rg_pets_2` | N sym50, sym75, pair25, pair50, pair75 | about 6 h |
| `kaggle/rg_dtd_1` | S sym, pair, inst, het, clean, N sym25 | about 7 h |
| `kaggle/rg_dtd_2` | N sym50, sym75, pair25, pair50, pair75 | about 6 h |
| `kaggle/rg_caltech_1` | S sym, pair, inst | about 9 h |
| `kaggle/rg_caltech_2` | S het, clean, N sym25 | about 9 h |
| `kaggle/rg_caltech_3` | N sym50, sym75, pair25 | about 9 h |
| `kaggle/rg_caltech_4` | N pair50, pair75 | about 6 h |

How the estimates were made: PromptFL's Kaggle time per run is about 0.75 h on Pets and 0.7 h on DTD. CLEAR-FPL's is 2.7 h on Caltech101. FedRG adds one CLIP image pass (the strong view) and a small GMM per batch, so these estimates assume about 1.5× PromptFL. A notebook skips any run that would end past 11.5 h, and the skipped runs go into a later notebook.

**Local smoke (2026-10-31).** Both runs used the 30-class toy set, 2 rounds, rc 0:
- `S_het_rg` in fp32;
- `N_pair75_rg` with `--precision amp` on CPU, where the scaler is disabled, so this checks the code path only.

What the smoke showed:
- the `fedrg` records are written;
- T moves away from the identity (mean diagonal 0.92-0.99);
- a 1-image last batch is skipped, as in the official code;
- the per-batch GMM sometimes puts a whole small batch on one side, as expected with M starting uniform.

**Results:** extract them to `results/side-research/fedrg/<notebook>/`, then run `python tools/analyze_baselines.py`.

## Pets results (rg_pets_1/2, 2026-10-31)

All 11 runs finished with rc 0 and 5 seeds. Kaggle time was 0.92-0.98 h per run, below the estimate of 1.1 h.

**Accuracy** (last10, paired over seeds). FedRG − PromptFL / FedRG − CLEAR-FPL:

| setting | FedRG | − PromptFL | − CLEAR-FPL |
|---|---|---|---|
| S sym | 87.25 | +6.79 (5/5) | −0.79 (p=0.099) |
| S pair | 87.04 | +7.97 (5/5) | −1.05 (p=0.054) |
| S inst | 87.18 | +4.94 (5/5) | −0.50 |
| S het | 86.93 | +10.62 (5/5) | −0.03 |
| S clean | 87.78 | +0.13 | −0.15 |
| N sym25 | 87.40 | +10.46 (5/5) | +0.37 (p=0.036, 5/5) |
| N sym50 | 86.01 | +22.74 (5/5) | −1.16 |
| N sym75 | 77.10 | +37.48 (5/5) | −1.33 |
| N pair25 | 87.07 | +12.98 (5/5) | +0.06 |
| N pair50 | 83.15 | +29.72 (5/5) | −3.74 (p=0.018, 0/5) |
| N pair75 | 75.37 | +46.59 (5/5) | +1.90 (p=0.278) |
| mean of 11 | 84.75 | | CLEAR-FPL 85.34 |

**Detector audit** (rounds 41-50, per client):

| setting | AUROC | share of the noisy split truly noisy | share of truly noisy caught |
|---|---|---|---|
| S sym | 0.63 | 0.12 | 0.93 |
| S het | 0.60 | 0.25 | 0.93 |
| N sym25 | 0.60 | 0.27 | 0.95 |
| N sym50 | 0.57 | 0.51 | 0.92 |
| N sym75 | 0.52 | 0.75 | 0.93 |
| N pair25 | 0.57 | 0.26 | 0.93 |
| N pair50 | 0.50 | 0.50 | 0.89 |
| N pair75 | 0.45 | 0.74 | 0.90 |

- The detector is close to chance. The noisy split's purity equals the true noise rate, so it puts about 90% of all images in the noisy split.
- FedRG's gain over PromptFL therefore comes from training almost every image through SCE plus the noise matrix T. T's mean diagonal is 0.2-0.7 under noise, and 0.92 on clean data. The gain does not come from finding the wrong labels.

**Against the predictions:**
1. Fails in part. On S clean FedRG is within 1 point of PromptFL (+0.13), but in the noisy S settings it is 5-11 points above.
2. Partly holds. It is far above PromptFL at 50-75%. Against CLEAR-FPL it is lower in 3 of 6 N settings, and significantly lower only in pair50 (−3.74). It is level or higher in sym25, pair25 and pair75.
3. Holds. AUROC is 0.45-0.63, against the paper's high values on CIFAR.

## DTD predictions, written 2026-10-31 after Pets and before any DTD FedRG run

Zero-shot CLIP is 41.78 on DTD (85.69 on Pets), so the anchor that keeps T and the prompt from absorbing wrong labels is weak. CLEAR-FPL's DTD means: 48.46 over 11 settings. It is below PromptFL at N sym25 (46.49 vs 47.54) and below NLPrompt (hist) at both 25% settings.
1. FedRG's mean over the 11 DTD settings is below CLEAR-FPL's.
2. At N sym75 and N pair75, FedRG is below CLEAR-FPL by more than on Pets (Pets: −1.33 and +1.90).
3. At N sym25 and N pair25, FedRG is level with CLEAR-FPL or above it, because CLEAR-FPL is weak there.
4. Detector AUROC stays near chance (≤ 0.65), as on Pets.

These are reported as they come out, like the Pets ones.

## Caltech101 on the server (added 2026-11-02)

The runs of `kaggle/rg_caltech_1` and `rg_caltech_2` (S sym, pair, inst, het, clean, N sym25) moved to the
Linux server as `server/queue_rg_caltech.txt`, one run at a time. Results go to
`results/server/queue_rg_caltech/`. `rg_caltech_3` and `rg_caltech_4` (N sym50, sym75, pair25, pair50, pair75)
and `rg_dtd_1/2` are still not started.
