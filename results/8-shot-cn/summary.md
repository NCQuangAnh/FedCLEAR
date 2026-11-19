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

## All methods (notebooks eurosat8_23/24/25, merged 2026-11-19)

FedRG and FedCorr from eurosat8_24, NLPrompt and FedProx from eurosat8_25; all 44 runs rc 0, seeds 0-4,
same Kaggle Tesla T4 type, CoOp class names. Accuracy = last-10 mean (rounds 41-50), mean ± population std
over 5 seeds. Bold = best in the row.

| Setting | PromptFL | FedProx | FedCorr | NLPrompt | FedRG | FedCLEAR |
|---|---|---|---|---|---|---|
| S sym | **60.20** ± 3.42 | 60.14 ± 3.17 | 48.79 ± 9.88 | 48.53 ± 8.01 | 58.42 ± 2.17 | 59.16 ± 3.53 |
| S pair | 59.02 ± 3.03 | **59.43** ± 2.60 | 51.46 ± 5.13 | 49.51 ± 4.97 | 55.03 ± 4.52 | 57.02 ± 3.83 |
| S inst | **60.85** ± 3.59 | 60.80 ± 3.31 | 50.11 ± 9.87 | 52.54 ± 3.77 | 58.75 ± 3.40 | 59.94 ± 3.78 |
| S het | 55.21 ± 4.37 | 55.83 ± 5.54 | 48.45 ± 5.05 | 46.33 ± 6.34 | 56.31 ± 4.11 | **56.51** ± 4.64 |
| S clean | 65.26 ± 2.54 | **65.37** ± 2.29 | 55.65 ± 4.80 | 52.41 ± 5.92 | 63.94 ± 4.44 | 62.39 ± 3.04 |
| N sym25 | 52.04 ± 4.65 | 52.04 ± 4.65 | 45.41 ± 6.26 | 46.00 ± 1.90 | 49.59 ± 6.97 | **53.07** ± 1.52 |
| N sym50 | 37.97 ± 4.44 | 37.97 ± 4.44 | 37.07 ± 2.64 | 34.78 ± 5.83 | **45.30** ± 5.54 | 42.92 ± 5.00 |
| N sym75 | 21.31 ± 1.24 | 21.31 ± 1.24 | 22.94 ± 2.08 | 28.89 ± 3.04 | 25.52 ± 2.73 | **31.99** ± 5.12 |
| N pair25 | **56.33** ± 2.79 | **56.33** ± 2.79 | 48.06 ± 2.84 | 44.10 ± 3.01 | 50.90 ± 4.31 | 53.31 ± 3.09 |
| N pair50 | 33.15 ± 2.35 | 33.15 ± 2.35 | 30.16 ± 5.10 | 36.69 ± 1.57 | 37.94 ± 3.15 | **38.57** ± 4.38 |
| N pair75 | 19.45 ± 3.01 | 19.45 ± 3.01 | 18.43 ± 3.61 | 24.62 ± 3.13 | 25.35 ± 3.51 | **26.00** ± 2.81 |
| Mean | 47.35 | 47.44 | 41.50 | 42.22 | 47.91 | **49.17** |

Best in row: FedCLEAR 5, PromptFL 3, FedProx 3 (ties), FedRG 1, FedCorr 0, NLPrompt 0.
FedCLEAR beats PromptFL 6/11, FedProx 6/11, FedRG 9/11, FedCorr 11/11, NLPrompt 11/11.
FedProx equals PromptFL in Scenario 2 (one local step per round on EuroSAT 8-shot, see next-runs notes).

### Cost (same runs, Kaggle Tesla T4)

Wall time per round and slowest client per round from the round log ("elapsed", client "time:"), rounds 1-50,
55 runs x 50 rounds per method (equal to metrics_seed_*.json wall_s where that file exists; FedCorr's
server does not write metrics files). Peak GPU memory = per-run max of torch max_memory_allocated.

| Method | Wall s/round | Slowest client s/round | Peak GPU MB (median / max) | Upload + download per run |
|---|---|---|---|---|
| PromptFL | 5.99 | 0.46 | 1248 / 1346 | 7.97 MiB |
| FedProx | 5.70 | 0.42 | 1246 / 1248 | 7.97 MiB |
| FedCorr | 5.50 | 0.46 | not logged | 6.87 MiB (mean, fewer clients in fine-tuning) |
| NLPrompt | 6.45 | 0.55 | 1243 / 1244 | 7.97 MiB |
| FedRG | 7.43 | 0.61 | 1256 / 1260 | 7.97 MiB |
| FedCLEAR | 6.14 | 0.47 | 1247 / 4793 | 7.97 MiB + gate/profile scalars |

FedCLEAR peak memory: 1.25 GB in the 36 runs where the gate stays closed; about 4.8 GB from round 6 on in
exactly the 19 runs where the gate opens (calibrated repair). Time differences between methods are within
about 25% and include Kaggle machine noise (PromptFL S runs: 6.15 min per seed vs 4.64 for N).
