# Client-count study on full data: results so far (2026-11-26)

Plan and reading rule: plan.md (written before any result). Runs: `results/clients50/<Dataset>/<Method>`,
`results/clients100/<Dataset>/<Method>`; 10 clients = `results/full`. Accuracy = mean of the last 10 rounds,
averaged over seeds (`analyze_s16.last10`); ± = std over seeds of FedCLEAR; (n) = seeds in. Gate = seeds in
which the referee gate opens. All runs rc 0.

## Pets

| Setting | 10: PromptFL | 10: FedCLEAR | Δ10 | 50: PromptFL | 50: FedCLEAR | Δ50 | 100: PromptFL | 100: FedCLEAR | Δ100 |
|---|---|---|---|---|---|---|---|---|---|
| S sym | — | 88.00 ±0.36 | — | 87.66 | 89.55 ±0.25 | +1.88 | — | 89.40 ±0.40 (5) | — |
| N sym50 | 73.66 | 87.18 ±1.00 | +13.52 | 81.22 | 88.74 ±0.27 | +7.52 | 79.24 | 87.99 ±0.92 (3) | +8.75 |
| N pair50 | 40.75 | 86.72 ±0.85 | +45.97 | — | 88.23 ±0.60 | — | — | 88.52 ±0.49 (3) | — |

## DTD

| Setting | 10: PromptFL | 10: FedCLEAR | Δ10 | 50: PromptFL | 50: FedCLEAR | Δ50 | 100: PromptFL | 100: FedCLEAR | Δ100 |
|---|---|---|---|---|---|---|---|---|---|
| S sym | — | 61.50 ±0.92 | — | 59.48 | 60.76 ±1.15 | +1.29 | — | 57.67 ±2.44 (3) | — |
| N sym50 | 52.74 | 57.30 ±0.52 | +4.56 | 50.93 | 54.17 ±1.26 | +3.23 | — | 51.39 ±1.26 (3) | — |
| N pair50 | 31.88 | 54.93 ±0.86 | +23.04 | — | 52.81 ±1.25 | — | — | 50.10 ±1.74 (3) | — |

Gate: open in every FedCLEAR run at 50 clients (30/30) and at 100 clients (17/17 so far).

## What is missing

- 50 clients: PromptFL N pair50 on Pets and DTD (skipped for time in c50_pfl_pets_7 / c50_pfl_dtd_8).
  10 clients has no PromptFL S sym full-data run.
- 100 clients: FedCLEAR seeds 3-4 for Pets N sym50 / N pair50 and all DTD settings; PromptFL for all but
  Pets N sym50. Notebooks still out: c100_pets_8, c100_dtd_9, c100_dtd_10, c100_b_11, c100_pfl_12, c100_pfl_13.

## Notes (descriptive, no claim yet)

- Every Δ measured so far is positive (5/5 cells at 50 clients plus Pets N sym50 at 100).
  The rule needs the 3-setting mean per dataset, so it cannot be applied until the missing PromptFL runs are in.
- Pets FedCLEAR barely moves with more clients (87-90 at 10, 50 and 100). DTD FedCLEAR drops as clients
  grow: S sym 61.50 / 60.76 / 57.67, N pair50 54.93 / 52.81 / 50.10 (100-client values are 3 seeds).
- PromptFL Pets N sym50 is higher with 50 clients (81.22) than with 10 (73.66), so Δ shrinks there
  (+13.52 to +7.52).
- Kaggle hours: 50 clients FedCLEAR 5.5-5.9 (3 seeds) and 3.7-3.9 (2 seeds), PromptFL S 5.7-5.8, N 3.5-3.6;
  100 clients FedCLEAR 6.7-7.3 (3 seeds), 4.8 (2 seeds), PromptFL N 5.1.
