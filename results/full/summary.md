# Full-data results, 10 clients (arms gatefcnfull / pflcnfull, `--num_shot 0`)

All training images, split over 10 clients as in the paper setup; seeds 0-4. Accuracy = mean of the last
10 rounds, averaged over 5 seeds (`analyze_s16.last10`). Runs sit in `<Dataset>/<FedCLEAR|PromptFL>/`.
Scope (user decision 2026-11-16): Pets and DTD only, Scenario 2 (N settings). The two S sym FedCLEAR runs
are kept as extras. "± std" = std over 5 seeds of FedCLEAR full. 32-shot columns for comparison.
Hours = Kaggle wall time per run (5 seeds).

## Pets

| Setting | PromptFL full | FedCLEAR full | ± std | Δ full | PromptFL 32 | FedCLEAR 32 | Δ 32 | h FedCLEAR | h PromptFL |
|---|---|---|---|---|---|---|---|---|---|
| S sym | — | 88.00 | 0.32 | — | 84.53 | 88.54 | +4.01 | 7.88 | — |
| N sym25 | 80.06 | 88.42 | 0.29 | +8.37 | 81.90 | 88.68 | +6.78 | 7.51 | 1.95 |
| N sym50 | 73.66 | 87.18 | 0.90 | +13.52 | 71.19 | 87.50 | +16.31 | 7.90 | 1.97 |
| N sym75 | 48.98 | 84.40 | 1.02 | +35.42 | 46.81 | 85.05 | +38.24 | 7.66 | 1.95 |
| N pair25 | 67.38 | 88.23 | 0.54 | +20.85 | 71.56 | 88.45 | +16.89 | 7.83 | 1.95 |
| N pair50 | 40.75 | 86.72 | 0.76 | +45.97 | 44.93 | 86.45 | +41.52 | 7.94 | 2.00 |
| N pair75 | 14.69 | 80.26 | 2.28 | +65.57 | 14.79 | 80.04 | +65.26 | 8.51 | 2.10 |

## DTD

| Setting | PromptFL full | FedCLEAR full | ± std | Δ full | PromptFL 32 | FedCLEAR 32 | Δ 32 | h FedCLEAR | h PromptFL |
|---|---|---|---|---|---|---|---|---|---|
| S sym | — | 61.50 | 0.82 | — | 58.54 | 59.94 | +1.40 | 8.65 | — |
| N sym25 | 57.11 | 61.61 | 0.99 | +4.50 | 54.99 | 58.94 | +3.95 | 7.76 | 1.94 |
| N sym50 | 52.74 | 57.30 | 0.46 | +4.56 | 47.99 | 54.78 | +6.79 | 8.43 | 1.93 |
| N sym75 | 37.73 | 50.23 | 1.08 | +12.50 | 35.26 | 47.64 | +12.38 | 7.78 | 2.02 |
| N pair25 | 50.63 | 61.22 | 0.83 | +10.59 | 49.35 | 59.08 | +9.73 | 8.18 | 1.96 |
| N pair50 | 31.88 | 54.93 | 0.77 | +23.04 | 31.09 | 53.39 | +22.29 | 7.78 | 2.09 |
| N pair75 | 10.27 | 45.64 | 0.46 | +35.37 | 9.77 | 44.86 | +35.08 | 7.94 | 1.97 |

FedCLEAR > PromptFL on full data: 12/12 (grid complete)

Merged: full_pets_1, full_dtd_3 (2026-11-16); full_pfl_7, full_pets_8, full_dtd_9, full_pets_10, full_dtd_11,
full_pets_12, full_dtd_13, full_pets_14, full_dtd_15, full_pets_16, full_pets_18, full_dtd_19 (2026-11-17).
All rc 0, 5 seeds each. The DTD PromptFL bonus runs (pair50, pair75, sym75) all finished.
full_dtd_20 (DTD N pair25 FedCLEAR, 2026-11-18) completes the grid. full_pets_8 also carried the 32-shot Pets S inst PromptFL seed 4
rerun, merged into results/32-shot.
