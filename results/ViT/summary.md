# CLIP ViT-B/16 backbone check (plan: results/side-research/vit_backbone/plan.md)

8 shots, 10 clients, seeds 0-4, every hyperparameter as in the paper (g = 0.12 unchanged).
Accuracy = mean of the last 10 rounds, averaged over 5 seeds (`analyze_s16.last10`); ± = std over seeds.
RN50 columns = paper Tables res1-res4 (8 shots, CoOp class names); RN50 gate counts from the logs of
those runs (Pets: side-research/calrepair/gatef0_pets_*, EuroSAT: 8-shot-cn).
Runs sit in `<Dataset>/<FedCLEAR|PromptFL>/`. Complete 2026-11-25: 20/20 runs, all rc 0
(Kaggle vit_pets_1, vit_pets_2; server queue_vit, index in server_index/).

## Verdict against the pre-registered rule

FedCLEAR - PromptFL, mean over the 5 settings: Pets +25.14 (5/5 wins), EuroSAT +5.47 (5/5 wins).
Positive on both datasets, so the rule allows "the result carries over to ViT-B/16".
With RN50 the same 5 settings give Pets +25.90 (5/5) and EuroSAT +2.78 (3/5).

## Pets

| Setting | PromptFL ViT | FedCLEAR ViT | ± | Δ ViT | gate ViT | PromptFL RN50 | FedCLEAR RN50 | Δ RN50 | gate RN50 |
|---|---|---|---|---|---|---|---|---|---|
| S sym | 86.38 | 92.18 | 0.68 | +5.80 | 5/5 | 80.5 | 88.0 | +7.5 | 5/5 |
| S pair | 85.48 | 92.08 | 0.71 | +6.60 | 5/5 | 79.1 | 88.2 | +9.1 | 5/5 |
| N sym50 | 68.45 | 90.03 | 1.17 | +21.58 | 5/5 | 63.3 | 86.8 | +23.5 | 5/5 |
| N pair50 | 58.36 | 89.92 | 1.64 | +31.56 | 5/5 | 53.4 | 86.9 | +33.5 | 5/5 |
| N pair75 | 24.96 | 85.13 | 1.30 | +60.17 | 5/5 | 28.8 | 84.7 | +55.9 | 5/5 |
| Mean | | | | +25.14 | 25/25 | | | +25.90 | 25/25 |

## EuroSAT

| Setting | PromptFL ViT | FedCLEAR ViT | ± | Δ ViT | gate ViT | PromptFL RN50 | FedCLEAR RN50 | Δ RN50 | gate RN50 |
|---|---|---|---|---|---|---|---|---|---|
| S sym | 64.21 | 65.76 | 2.30 | +1.55 | 3/5 | 60.2 | 59.2 | -1.0 | 0/5 |
| S pair | 63.79 | 64.13 | 1.86 | +0.34 | 2/5 | 59.0 | 57.0 | -2.0 | 2/5 |
| N sym50 | 48.24 | 52.42 | 5.09 | +4.18 | 4/5 | 38.0 | 42.9 | +4.9 | 2/5 |
| N pair50 | 40.27 | 47.12 | 5.46 | +6.85 | 5/5 | 33.1 | 38.6 | +5.5 | 2/5 |
| N pair75 | 21.60 | 36.02 | 4.56 | +14.42 | 5/5 | 19.4 | 26.0 | +6.6 | 2/5 |
| Mean | | | | +5.47 | 19/25 | | | +2.78 | 8/25 |

Notes:
- On EuroSAT the gate opens more often with ViT (19/25 vs 8/25), and FedCLEAR's margin over PromptFL
  grows (+5.47 vs +2.78); the two Scenario 1 settings where RN50 FedCLEAR was behind are now ahead,
  but only by 1.55 and 0.34, inside one seed std.
- EuroSAT seed std is large (1.9-5.5), so single-setting gaps below about 3 points are not reliable.
- Hours per run (5 seeds): Pets Kaggle FedCLEAR 1.72-1.83, PromptFL 1.16-1.18; server Pets PromptFL
  0.47; server EuroSAT 0.19-0.30.
