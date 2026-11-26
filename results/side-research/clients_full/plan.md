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

## Extension 2026-11-26: all of Scenario 2 at 50 clients (user request)

Arms `gatefc50a/b` and `pflc50` now exist for N sym25 / sym50 / sym75 / pair25 / pair50 / pair75 (Pets, DTD).
Full Scenario 2 at 50 clients needs 18 more runs: PromptFL N pair50 x2 (skipped for time) plus the 4 new
settings x 2 methods x 2 datasets; about 110 Kaggle hours (FedCLEAR ~9.7 h per 5-seed run, PromptFL ~3.6 h).
First notebook: c50_pfl_9 (PromptFL DTD N pair50, Pets N pair50, Pets N pair75; ~10.6 h). Same reading rule.
Then c50_10 (FedCLEAR Pets N pair75 seeds 0-2 + PromptFL DTD N pair75; ~9.4 h, --hours=10.5).
Then c50_11 (FedCLEAR DTD N pair75 seeds 0-2 + PromptFL Pets N sym25; ~9.5 h, --hours=10.5).
Then c50_12 (FedCLEAR Pets N sym25 seeds 0-2 + PromptFL DTD N sym25; ~9.4 h, --hours=10.5).
Then c50_13 (FedCLEAR DTD N sym25 seeds 0-4; ~9.9 h).
Then c50_14 (FedCLEAR Pets N pair75 seeds 3-4 + PromptFL Pets N sym75; ~7.4 h) and c50_15 (FedCLEAR DTD N pair75 seeds 3-4 + PromptFL Pets N pair25; ~7.5 h), both --hours=8.
Then c50_pfl_16 (PromptFL DTD N sym75, N pair25; ~7.2 h) and c50_17 (FedCLEAR Pets N sym25 + N sym75 seeds 3-4; ~7.8 h, --hours=8.5).
Then c50_18 (FedCLEAR DTD N sym75 seeds 0-4; ~9.9 h).
