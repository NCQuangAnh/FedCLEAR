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

## Extension 2026-11-25: DTD and MNIST (user decision after the Pets / EuroSAT result)

Same arms, settings, seeds and hyperparameters; FedRG still left out. CoOp class names change nothing
on DTD or MNIST (empty rename table), so the RN50 comparators are the paper's 8-shot runs.
Kaggle: `vit_dtd_3` (DTD FedCLEAR S sym, S pair, N sym50, N pair50 + PromptFL N sym50, ~9.6 h),
`vit_dtd_mnist_4` (DTD FedCLEAR N pair75 + PromptFL N pair50, N pair75, S sym, S pair; MNIST FedCLEAR
S sym, S pair, ~8.9 h), `vit_mnist_5` (MNIST FedCLEAR N x3 + PromptFL all 5, ~6.6 h).
Fixed before the runs: report every setting; read each dataset as above (mean difference, wins out
of 5, gate opens vs RN50). The Pets / EuroSAT verdict stands on its own; DTD and MNIST are reported
per dataset, and a negative mean on either is stated as such.

## Extension 2026-11-25: Caltech101 on the server (user request)

Same 10 arms, server queue `queue_vit_caltech` (run alone on the GPU). Caltech folder names are already
the CoOp names, so the RN50 comparators are the paper's 8-shot runs. Same reading rule as above.
