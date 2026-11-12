# Simpler client flag: tau = 0, no look-alike merge. Pre-registered plan

Written 2026-11-04, before any run of this arm. Replaces the first version of this plan (arm `gatefnm`,
no merge with tau = 0.072), which was never run; the user chose this design the same day.

## Question

Can FedCLEAR (arm `gatef`) drop two hand-set items, tau = 0.05 and the look-alike merge, without losing
accuracy? If the labels follow P, the expected excess loss s_i is exactly 0, so tau = 0 needs no tuning.

## How the idea was found

An exploratory replay on logged PromptFL runs (scenario 1, 3 seeds, no training) showed flags nearly
unchanged:

| clean / noisy clients flagged | now (merge, tau 0.05) | no merge, tau 0 |
|---|---|---|
| Pets | 1.8% / 92.8% | 2.4% / 93.9% |
| Caltech101 | 0% / 96.7% | 0% / 96.7% |
| DTD | 2.4% / 86.2% | 3.1% / 86.8% |
| MNIST | 0% / 41.3% | 0.5% / 48.5% |
| EuroSAT | 6.3% / 55.1% | 9.3% / 54.8% |

The value 0 comes from the expectation, not from a search, but the idea came after seeing this data, and
seeds 0-4 were used to develop the method. Stage 2 therefore uses fresh seeds.

## Stage 1: seeds 0-4

Arm `gatefz` = `gatef` + `--sure_score xs --sure_tau 0`. Nothing else changes (delta, gamma, kappa, alpha,
g, R_g, clipping). All 11 settings on all 5 datasets, 55 runs:

| Queue | Datasets | Runs | Estimated time |
|---|---|---|---|
| `queue_z_pets_dtd` | Pets, DTD | 22 | about 15 h, two at a time |
| `queue_z_caltech` | Caltech101 | 11 | about 25 h, alone |
| `queue_z_mnist_eurosat` | MNIST, EuroSAT | 22 | about 6.5 h, two at a time |

Comparator: the paper's FedCLEAR numbers on the same seeds, by the rule of `tools/make_paper_tables.py`
(arm `gatef`; settings without that arm use the basic-repair run). Measure: last-10 accuracy, difference
= `gatefz` - comparator, paired over seeds. Also reported: macro-F1 where both have it, flag rates on clean
and noisy client-rounds, gate decisions.

Stage 1 passes only if all three hold:

- **Z1, no loss on average:** each of the 10 averages (5 datasets x 2 scenarios) is at least -0.5.
- **Z2, no setting clearly worse:** no setting is lower by more than 1 point with p < 0.05.
- **Z3, no collapse:** no seed pair at -5 or worse, on any dataset.

## Stage 2: fresh seeds 8-10, only if stage 1 passes

`gatefz` against the existing `gatef` runs (`N_<x>_gatefc`) on their 12 settings: Pets, DTD and Caltech101 at
N sym75 and N pair75, DTD at N sym25 and N pair25, MNIST and EuroSAT at N sym75 and N pair75. 36 seed pairs.

- **H1:** no seed pair at -5 or worse.
- **H2:** the mean over the 36 seed pairs is at least -0.5.

The arm and its queue are added only when stage 1 passes.

## Outcome

- **Both stages pass:** recommend `gatefz` as FedCLEAR. All FedCLEAR numbers, tau and the merge text of the
  paper change. The user decides.
- **Otherwise:** FedCLEAR stays `gatef`, and no variant is tried on these seeds. The table is reported as
  it is. It measures tau and the merge together, so a loss cannot be assigned to one of them; arm `gatefnm`
  (no merge, tau = 0.072) stays available to separate them.

## 2026-11-05: stage 1, Pets and DTD in (queue_z_pets_dtd)

Extracted to `merge_ablation/queue_z_pets_dtd/`, 22 runs, rc 0, 5 seeds. Mean difference gatefz - gatef:
Pets S1 +0.06, S2 -0.16; DTD S1 +0.36, S2 +0.45. Z1 holds for these 4 of 10 averages. Z2: no setting lower by
more than 1 point with p < 0.05 (largest drop Pets N pair75 -0.90, p 0.26). Z3: worst seed pair -2.57 (Pets N
pair75). DTD N pair25 is higher, +1.51, p 0.009. Caltech, MNIST and EuroSAT queues still to come.

## 2026-11-07: stage 1 complete, FAIL

Caltech101 and MNIST/EuroSAT queues extracted to `merge_ablation/queue_z_caltech/` and
`merge_ablation/queue_z_mnist_eurosat/`, 33 runs, rc 0, 5 seeds, args checked (`--sure_score xs --sure_tau 0`).
Analysis: `python tools/analyze_merge_ablation.py`.

| Mean gatefz - FedCLEAR | Scenario 1 | Scenario 2 |
|---|---|---|
| Pets | +0.06 | -0.16 |
| Caltech101 | +0.04 | +0.00 |
| MNIST | +0.84 | -0.28 |
| DTD | +0.36 | +0.45 |
| EuroSAT | -1.14 | -0.55 |

- **Z1 fails:** EuroSAT S1 -1.14, S2 -0.55.
- **Z2 fails:** MNIST N pair50 -2.72 (p 0.002), N pair75 -1.84 (p 0.039).
- **Z3 fails:** 16 seed pairs at -5 or worse, all on MNIST (N sym50 -10.25, N sym75 -8.31) and EuroSAT (down to -10.83).
- Caltech101 scenario 2 is identical to FedCLEAR seed by seed (same round accuracies): with every client noisy
  the flags do not change.

Outcome by the pre-registered rule: stage 2 is not run, FedCLEAR stays `gatef` (tau = 0.05 with the merge), and
no other variant is tried on these seeds. The table is reported as it is; it measures tau and the merge
together. On Pets, Caltech101 and DTD the simpler flag is within ±1 everywhere (DTD N pair25 +1.51, p 0.009),
so the hand-set items matter on the weak-CLIP datasets (MNIST, EuroSAT).

## 2026-11-13: look-alike merge alone (arm `gatefnm`), written before any run of this arm

Why: the supervisor asked for an ablation of the look-alike merge alone. `gatefz` changed two things at
once (no merge and tau = 0), so it cannot isolate the merge.

Arm `gatefnm` = `gatef` + `--sure_score xs --sure_tau 0.072`. Only the merge is removed. tau is reset by
the same rule that gave tau = 0.05 with the merge: the 95th percentile of client scores in the noise-free
Pets federation, which is 0.0725 for the score without the merge (gate D stage 1 logs). The 8-shot
paper setting is unchanged: seeds 0-4, EuroSAT with the folder class names (the paper's comparator).
Comparator: the paper's FedCLEAR (`gatef`), by the rule of `tools/make_paper_tables.py`.

Kaggle batch 1 (2 notebooks of 11 h): all 11 MNIST settings, all 11 EuroSAT settings, and Pets S sym,
S pair and S clean. The rest (8 Pets, 11 DTD and 11 Caltech101 settings) comes later.

Reported for each run: last-10 accuracy paired with gatef over the 5 seeds; the share of clean and noisy
client-rounds that are flagged.

Reading, fixed now:
- **No benefit from the merge:** every dataset-scenario average of `gatefnm` - `gatef` is at least -0.5,
  no setting is lower by more than 1 point with p < 0.05, and no seed pair is at -5 or worse. Then the
  merge can be dropped from FedCLEAR. The user and the supervisor decide.
- **Otherwise:** the merge stays and the table is reported as the ablation, with the datasets where it
  helps.
