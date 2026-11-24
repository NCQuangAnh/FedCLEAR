# CLIP ViT-B/16 backbone check (2026-11-24)

Why: a mock review of the PAKDD draft says the paper uses one backbone (CLIP with a ResNet-50 image
encoder). This check reruns FedCLEAR and PromptFL with the ViT-B/16 image encoder.

Setup: the paper's 8-shot arms unchanged (gatefcn8 = FedCLEAR, pflcn8 = PromptFL, CoOp class names),
plus `--image_backbone ViT-B/16`. Every hyperparameter is kept as in the paper (tau 0.05, delta 0.1,
kappa 0.5, alpha 0.05, gamma 0.6, g 0.12, R_g 5); nothing is tuned for ViT. Seeds 0-4.
Arms: `*_gatefv16`, `*_pflv16`.

Settings (2 datasets x 5): Pets and EuroSAT; S sym, S pair, N sym50, N pair50, N pair75.

Where: Kaggle `vit_pets_1` (Pets FedCLEAR S sym, S pair, N sym50), `vit_pets_2` (Pets FedCLEAR N pair50,
N pair75 + Pets PromptFL S sym, S pair); server `queue_vit` (EuroSAT all 10, Pets PromptFL N x3).
FedRG is left for later.

Fixed before the runs:
- Report every setting, whatever the result.
- Main question: with g = 0.12 unchanged, does FedCLEAR still beat PromptFL? Read per dataset:
  mean last-10 accuracy difference FedCLEAR - PromptFL over the 5 settings, wins out of 5, and the
  number of runs in which the gate opens (compare with RN50).
- Claim "the result carries over to ViT-B/16" only if FedCLEAR's mean difference is positive on both
  datasets; otherwise state where it fails.
