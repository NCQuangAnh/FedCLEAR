# Client-count study on full data: results so far (2026-11-28)

Plan and reading rule: plan.md (written before any result). Runs: `results/clients50/<Dataset>/<Method>`,
`results/clients100/<Dataset>/<Method>`; 10 clients = `results/full`. Accuracy = mean of the last 10 rounds,
averaged over seeds (`analyze_s16.last10`); ± = std over seeds of FedCLEAR; (n) = seeds in. Gate = seeds in
which the referee gate opens. All runs rc 0.

## Pets

| Setting | 10: PromptFL | 10: FedCLEAR | Δ10 | 50: PromptFL | 50: FedCLEAR | Δ50 | 100: PromptFL | 100: FedCLEAR | Δ100 |
|---|---|---|---|---|---|---|---|---|---|
| S sym (extra) | — | 88.00 ±0.36 | — | 87.66 | 89.55 ±0.25 | +1.88 | — | 89.40 ±0.40 | — |
| N sym25 | 80.06 | 88.42 ±0.32 | +8.37 | 85.82 | 89.56 ±0.42 | +3.74 | 85.46 | 89.06 ±0.39 | +3.60 |
| N sym50 | 73.66 | 87.18 ±1.00 | +13.52 | 81.22 | 88.74 ±0.27 | +7.52 | 79.24 | 88.11 ±0.69 | +8.87 |
| N sym75 | 48.98 | 84.40 ±1.14 | +35.42 | 57.29 | 87.13 ±0.84 | +29.84 | 61.04 | 86.73 ±1.13 | +25.69 |
| N pair25 | 67.38 | 88.23 ±0.60 | +20.85 | 78.18 | 89.57 ±0.41 | +11.39 | 81.50 | 89.08 ±0.40 | +7.58 |
| N pair50 | 40.75 | 86.72 ±0.85 | +45.97 | 50.09 | 88.23 ±0.60 | +38.14 | 59.07 | 88.49 ±0.36 | +29.42 |
| N pair75 | 14.69 | 80.26 ±2.55 | +65.57 | 18.78 | 84.52 ±1.46 | +65.74 | 24.31 | 85.11 ±1.17 (2) | +60.80 |

## DTD

| Setting | 10: PromptFL | 10: FedCLEAR | Δ10 | 50: PromptFL | 50: FedCLEAR | Δ50 | 100: PromptFL | 100: FedCLEAR | Δ100 |
|---|---|---|---|---|---|---|---|---|---|
| S sym (extra) | — | 61.50 ±0.92 | — | 59.48 | 60.76 ±1.15 | +1.29 | — | 57.67 ±2.44 (3) | — |
| N sym25 | 57.11 | 61.61 ±1.11 | +4.50 | 57.09 | 58.18 ±1.07 | +1.08 | 54.24 | 55.02 ±2.14 (2) | +0.78 |
| N sym50 | 52.74 | 57.30 ±0.52 | +4.56 | 50.93 | 54.17 ±1.26 | +3.23 | 47.11 | 51.58 ±1.31 | +4.47 |
| N sym75 | 37.73 | 50.23 ±1.21 | +12.50 | 37.56 | 47.38 ±1.47 | +9.82 | 34.40 | 45.79 ±0.33 (2) | +11.39 |
| N pair25 | 50.63 | 61.22 ±0.93 | +10.60 | 53.79 | 58.30 ±1.31 | +4.51 | 54.00 | 54.83 ±3.41 (2) | +0.83 |
| N pair50 | 31.88 | 54.93 ±0.86 | +23.04 | 36.34 | 52.81 ±1.25 | +16.46 | 39.18 | 50.43 ±1.46 | +11.25 |
| N pair75 | 10.27 | 45.64 ±0.52 | +35.37 | 12.53 | 44.12 ±0.58 | +31.59 | 17.61 | 43.49 ±1.59 (2) | +25.88 |

Gate: open in every FedCLEAR run at 50 clients (70/70 seeds) and at 100 clients (53/53 seeds so far).

## What is missing

- 50 clients: complete (Scenario 2, both datasets, both methods, 5 seeds).
- 100 clients: FedCLEAR seeds 0-2 for Pets N pair75 and DTD N sym25 / sym75 / pair25 / pair75 (server queue
  `queue_c100_1`, running). Cells marked (2) have only seeds 3-4 so far.

## Notes (descriptive, no claim yet)

- FedCLEAR is ahead in every Scenario 2 cell at 50 clients (14/14) and in every cell so far at 100 clients (12/12).
- Small gaps: DTD N sym25 +1.08 at 50 clients (about 1 std); at 100 clients DTD N sym25 +0.78 and N pair25 +0.83,
  both inside FedCLEAR's std with only 2 seeds. These are not called wins under the plan's rule.
- Pets FedCLEAR barely moves with more clients (85-90 at 50 and 100). DTD FedCLEAR drops with more clients in
  every setting (N sym25 61.61 / 58.18 / 55.02; N pair25 61.22 / 58.30 / 54.83).
- PromptFL gains from more clients at pair noise (Pets N pair50 40.75 / 50.09 / 59.07), so Δ shrinks there, but
  at 75% noise Δ stays large (Pets N pair75 +60.80 at 100 clients).
- Kaggle hours: 50 clients FedCLEAR 5.3-6.3 (3 seeds), 3.5-4.4 (2 seeds); 100 clients FedCLEAR 6.8-6.9
  (3 seeds), 4.5-4.9 (2 seeds), PromptFL 4.8-5.3 (5 seeds), 3.9-4.1 (4 seeds), 0.95 (1 seed).
