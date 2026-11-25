# Client-count study on full data (reviewer point "ten clients")

Written 2026-11-25, before any 50- or 100-client result was seen.

## Setup

- Full data (`--num_shot 0`), Dirichlet 0.1, every client takes part each round, RN50, paper hyperparameters
  (g = 0.12 unchanged).
- Datasets Pets and DTD. Settings S sym, N sym50, N pair50. Seeds 0-4.
- 10 clients: existing runs in results/full.
- 50 clients: arms `gatefc50a/b` (FedCLEAR, seeds 0-2 / 3-4) and `pflc50` (PromptFL). Kaggle c50_pets_1-3,
  c50_dtd_4-6, c50_pfl_pets_7, c50_pfl_dtd_8.
- 100 clients: arms `gatefc100a/b` and `pflc100`. Kaggle c100_pets_1 ... c100_pfl_13.
  The simulated split has 5-11 images in the smallest client and a median of 29.
- The a and b halves merge into one 5-seed FedCLEAR run.
- Accuracy is the mean of the last 10 rounds, averaged over 5 seeds.

## Reading rule

Per dataset and client count, Δ = FedCLEAR - PromptFL, averaged over the 3 settings.

- If Δ > 0 on both datasets at 50 and at 100 clients, the paper may say that the advantage holds with
  50 and 100 clients.
- If Δ ≤ 0 anywhere, report that cell as a limitation, with the number.
- A single-setting gap smaller than 2 seed std is not called a win or a loss.
- Also report how FedCLEAR accuracy changes from 10 to 50 to 100 clients. This is descriptive only, with no
  claim attached.
