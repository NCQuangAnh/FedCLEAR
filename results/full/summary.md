# Full-data results, 10 clients (arms gatefcnfull / pflcnfull, `--num_shot 0`)

All training images, split over 10 clients as in the paper setup; seeds 0-4. Accuracy = mean of the last
10 rounds, averaged over 5 seeds (`analyze_s16.last10`). Runs sit in `<Dataset>/<FedCLEAR|PromptFL>/`.

| Dataset | Setting | PromptFL full | FedCLEAR full | ± std | FedCLEAR 64 | FedCLEAR 32 | Notebook | Kaggle time |
|---|---|---|---|---|---|---|---|---|
| Pets | S sym | — | 88.00 | 0.32 | 88.54 | 88.54 | full_pets_1 | 7.88 h |
| DTD | S sym | — | 61.50 | 0.82 | (= full) | 59.94 | full_dtd_3 | 8.65 h |

Merged 2026-11-16, rc 0. Still out: full_pets_2, full_dtd_4 (FedCLEAR N sym50), full_pfl_pets_5,
full_pfl_dtd_6 (PromptFL S sym, N sym50, N pair50).
