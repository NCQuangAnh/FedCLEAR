# EuroSAT 8-shot rerun with CoOp class names (arms gatefcn8 / pflcn8 / zscn, `--coop_classnames true`)

Notebook eurosat8_23 (Kaggle, merged 2026-11-18). All runs rc 0, seeds 0-4. Accuracy = mean of the last
10 rounds, averaged over 5 seeds (`analyze_s16.last10`); "±" = std over seeds. The old 8-shot EuroSAT runs
used folder names as class names (see the EuroSAT class-name bug); they are shown for comparison only.
Zero-shot CLIP with CoOp names: 36.67% (old folder names: 26.11%).

| Setting | PromptFL | FedCLEAR | Δ | old 8-shot PromptFL | old 8-shot FedCLEAR | 16-shot-cn PromptFL | 16-shot-cn FedCLEAR |
|---|---|---|---|---|---|---|---|
| S sym | 60.20 ± 3.42 | 59.16 ± 3.53 | -1.04 | 60.59 | 60.68 | 64.20 | 64.80 |
| S pair | 59.02 ± 3.03 | 57.02 ± 3.83 | -2.01 | 58.22 | 58.89 | 64.25 | 63.19 |
| S inst | 60.85 ± 3.59 | 59.94 ± 3.78 | -0.91 | 59.78 | 60.00 | 62.83 | 62.87 |
| S het | 55.21 ± 4.37 | 56.51 ± 4.64 | +1.30 | 53.93 | 56.70 | 59.63 | 60.43 |
| S clean | 65.26 ± 2.54 | 62.39 ± 3.04 | -2.87 | 65.03 | 64.25 | 72.62 | 71.16 |
| N sym25 | 52.04 ± 4.65 | 53.07 ± 1.52 | +1.03 | 53.55 | 54.05 | 59.10 | 54.27 |
| N sym50 | 37.97 ± 4.44 | 42.92 ± 5.00 | +4.95 | 40.36 | 41.41 | 46.92 | 46.63 |
| N sym75 | 21.31 ± 1.24 | 31.99 ± 5.12 | +10.68 | 23.71 | 25.59 | 26.51 | 35.10 |
| N pair25 | 56.33 ± 2.79 | 53.31 ± 3.09 | -3.02 | 52.74 | 55.20 | 56.92 | 50.01 |
| N pair50 | 33.15 ± 2.35 | 38.57 ± 4.38 | +5.42 | 33.99 | 40.57 | 41.31 | 38.35 |
| N pair75 | 19.45 ± 3.01 | 26.00 ± 2.81 | +6.55 | 15.37 | 25.77 | 18.33 | 22.58 |

FedCLEAR > PromptFL: 6/11 (all four S losses and N pair25 lose by 0.9-3.0 points; seed std is 2.5-5).
Kaggle wall time per run: FedCLEAR 0.41-0.48 h, PromptFL N 0.38-0.39 h, PromptFL S 0.49-0.53 h.
