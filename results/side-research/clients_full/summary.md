# Client-count study on full data: results so far (2026-11-27)

Plan and reading rule: plan.md (written before any result). Runs: `results/clients50/<Dataset>/<Method>`,
`results/clients100/<Dataset>/<Method>`; 10 clients = `results/full`. Accuracy = mean of the last 10 rounds,
averaged over seeds (`analyze_s16.last10`); ± = std over seeds of FedCLEAR; (n) = seeds in. Gate = seeds in
which the referee gate opens. All runs rc 0.

## Pets

| Setting | 10: PromptFL | 10: FedCLEAR | Δ10 | 50: PromptFL | 50: FedCLEAR | Δ50 | 100: PromptFL | 100: FedCLEAR | Δ100 |
|---|---|---|---|---|---|---|---|---|---|
| S sym (extra) | — | 88.00 ±0.36 | — | 87.66 | 89.55 ±0.25 | +1.88 | — | 89.40 ±0.40 (5) | — |
| N sym25 | 80.06 | 88.42 ±0.32 | +8.37 | 85.82 | 89.56 ±0.42 | +3.74 | — | — | — |
| N sym50 | 73.66 | 87.18 ±1.00 | +13.52 | 81.22 | 88.74 ±0.27 | +7.52 | 79.24 | 87.99 ±0.92 (3) | +8.75 |
| N sym75 | 48.98 | 84.40 ±1.14 | +35.42 | 57.29 | — | — | — | — | — |
| N pair25 | 67.38 | 88.23 ±0.60 | +20.85 | 78.18 | — | — | — | — | — |
| N pair50 | 40.75 | 86.72 ±0.85 | +45.97 | 50.09 | 88.23 ±0.60 | +38.14 | — | 88.52 ±0.49 (3) | — |
| N pair75 | 14.69 | 80.26 ±2.55 | +65.57 | 18.78 | 84.52 ±1.46 | +65.74 | — | — | — |

## DTD

| Setting | 10: PromptFL | 10: FedCLEAR | Δ10 | 50: PromptFL | 50: FedCLEAR | Δ50 | 100: PromptFL | 100: FedCLEAR | Δ100 |
|---|---|---|---|---|---|---|---|---|---|
| S sym (extra) | — | 61.50 ±0.92 | — | 59.48 | 60.76 ±1.15 | +1.29 | — | 57.67 ±2.44 (3) | — |
| N sym25 | 57.11 | 61.61 ±1.11 | +4.50 | 57.09 | 58.18 ±1.07 | +1.08 | — | — | — |
| N sym50 | 52.74 | 57.30 ±0.52 | +4.56 | 50.93 | 54.17 ±1.26 | +3.23 | — | 51.39 ±1.26 (3) | — |
| N sym75 | 37.73 | 50.23 ±1.21 | +12.50 | 37.56 | 47.38 ±1.47 | +9.82 | — | — | — |
| N pair25 | 50.63 | 61.22 ±0.93 | +10.60 | 53.79 | — | — | — | — | — |
| N pair50 | 31.88 | 54.93 ±0.86 | +23.04 | 36.34 | 52.81 ±1.25 | +16.46 | — | 50.10 ±1.74 (3) | — |
| N pair75 | 10.27 | 45.64 ±0.52 | +35.37 | 12.53 | 44.12 ±0.58 | +31.59 | — | — | — |

Gate: open in every FedCLEAR run so far at 50 clients (63/63 seeds) and at 100 clients (17/17).

## What is missing

- 50 clients (Scenario 2): only FedCLEAR N pair25 (c50_19 DTD, c50_20 Pets) and Pets N sym75 (c50_21).
- 100 clients: kept notebooks c100_pets_8, c100_dtd_10, c100_b_11 (not run); the rest is built only when asked.

## Notes (descriptive, no claim yet)

- Every Δ measured so far at 50 clients is positive (9/9 Scenario 2 cells, plus S sym). Smallest: DTD N sym25
  +1.08, which is about 1 seed std of FedCLEAR (1.07), so it is not called a win under the plan's rule.
- Pets FedCLEAR barely moves with more clients (84-90 at 10, 50 and 100). DTD FedCLEAR drops a little at 50
  clients in every setting (N sym25 61.61 to 58.18, N sym75 50.23 to 47.38, N pair50 54.93 to 52.81).
- PromptFL gains more from 50 clients than FedCLEAR does at low noise (Pets N sym25 80.06 to 85.82, N pair25
  67.38 to 78.18), so Δ shrinks there; at 75% noise Δ stays about the same (Pets N pair75 +65.57 / +65.74).
- Kaggle hours at 50 clients: FedCLEAR 5.6-6.3 (3 seeds), 3.6-4.4 (2 seeds); PromptFL N 3.35-3.60.
