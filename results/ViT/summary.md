# CLIP ViT-B/16 backbone check (plan: results/side-research/vit_backbone/plan.md)

8 shots, 10 clients, seeds 0-4, every hyperparameter as in the paper (g = 0.12 unchanged).
Accuracy = mean of the last 10 rounds, averaged over 5 seeds (`analyze_s16.last10`); ± = std over seeds.
RN50 columns = paper Tables res1 / res3 (8 shots, CoOp class names).
Runs sit in `<Dataset>/<FedCLEAR|PromptFL>/`.

Status 2026-11-25: Kaggle vit_pets_1 and vit_pets_2 merged (7 runs, all rc 0). Still on the server
(`queue_vit`): EuroSAT all 10 runs, Pets PromptFL N sym50 / N pair50 / N pair75.

## Pets

| Setting | PromptFL ViT | FedCLEAR ViT | ± | Δ ViT | gate opens ViT | PromptFL RN50 | FedCLEAR RN50 | Δ RN50 |
|---|---|---|---|---|---|---|---|---|
| S sym | 86.38 | 92.18 | 0.68 | +5.80 | 5/5 | 80.5 | 88.0 | +7.5 |
| S pair | 85.48 | 92.08 | 0.71 | +6.60 | 5/5 | 79.1 | 88.2 | +9.1 |
| N sym50 | (server) | 90.03 | 1.17 | | 5/5 | 63.3 | 86.8 | +23.5 |
| N pair50 | (server) | 89.92 | 1.64 | | 5/5 | 53.4 | 86.9 | +33.5 |
| N pair75 | (server) | 85.13 | 1.30 | | 5/5 | 28.8 | 84.7 | +55.9 |

Kaggle hours per run (5 seeds): FedCLEAR 1.72-1.83, PromptFL 1.16-1.18.

## EuroSAT

All 10 runs on the server (`queue_vit`), not in yet.
