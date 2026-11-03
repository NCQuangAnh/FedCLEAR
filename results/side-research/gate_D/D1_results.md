# Gate D stage 1 results (2026-10-16)

Plan: `gate_d1_plan.md` (+ addendum). Full tables: `analysis/d1_<dataset>.md` (tools/analyze_d1.py).
Runs: Pets 15/15 (pets/), DTD 12/15 and Caltech 13/15 (raw/). Missing, skipped by the time
budget, rerun in kaggle/gate_d1_fill_dtd.ipynb (inst_none, sym_mae, het_dbr) and
kaggle/gate_d1_fill_caltech.ipynb (pair_none, het_none).

## Selection (Pets, pre-registered rule): winner = "surprise, global+CLIP, merged"

`none` arm, rounds 10-49, 5 seeds. Threshold = 95th percentile of honest client-rounds in clean.

| score | mean AUROC | recall sym/pair/inst/het | false flags sym/pair/inst/het |
|---|---|---|---|
| d (old DBR-FPL) | 0.965 | 1.00/0.94/0.99/0.87 | 0.10/0.09/0.08/0.17 |
| loss, global | 0.997 | 1.00/0.99/1.00/1.00 | 0.34/0.25/0.29/0.74 |
| loss, local | 1.000 | 1.00/0.98/1.00/1.00 | 0.04/0.03/0.04/0.03 |
| LID, local (FedCorr) | 0.377 | 0/0/0/0 | 0.04/0.05/0.04/0.04 |
| **surprise, global+CLIP, merged** | **1.000** | 1.00/0.99/1.00/0.88 | **0.00/0.00/0.00/0.00** |

Several candidates tie at AUROC 1.000; the tie-break (false flags) picks the merged surprise
score, the only one with zero false flags in all four scenarios. The pre-registered sink test
(a surprise variant must beat d by >= 0.02) passes (+0.035). Unlike AUROC, the false-flag rate
separates surprise from plain loss: loss-local accuses 3-4% of honest client-rounds, loss-global
25-74%, surprise none.

## Confirmation on DTD and Caltech (partial, no re-selection)

| dataset | score | AUROC sym/pair/het | false flags sym/pair/het |
|---|---|---|---|
| DTD | d (old) | 0.972/0.950/0.975 | 0.10/0.13/0.08 |
| DTD | loss, local | 0.990/0.968/0.984 | 0.07/0.06/0.08 |
| DTD | **surprise merged** | **1.000/0.989/0.999** | 0.05/0.05/0.01 |
| Caltech | d (old) | 1.000/—/— (sym, inst) | 0.10/0.10 |
| Caltech | loss, local | 1.000 | 0.09/0.04 |
| Caltech | **surprise merged** | **1.000** | **0.00/0.00** |

The Pets winner is the best primary candidate on DTD and tied best on Caltech, and beats d on
both: confirmation passes on the runs in hand (DTD inst and Caltech pair/het pending).

Self-referenced scale (why one threshold can travel): honest clients' surprise in the clean
federation sits at or below 0 on every dataset (95th percentile Pets 0.05, DTD -0.17, Caltech
-0.08), while the old d's clean level moves with the dataset (0.30 / 0.55 / 0.18).

FedCorr's LID: AUROC 0.38 (Pets), ~0.76 (DTD), ~0.92 (Caltech): weak with 20-80 images per client.

## Accuracy (last10)

| | Pets none / MAE / DBR | DTD none / MAE / DBR | Caltech none / MAE / DBR |
|---|---|---|---|
| sym | 80.47 / 88.12 / 86.87 | 51.91 / — / 53.30 | 87.79 / 89.78 / 89.77 |
| pair | 79.07 / 87.53 / 86.11 | 51.08 / 47.69 / 52.27 | — / 89.79 / 89.80 |
| inst | 82.24 / 87.50 / 87.08 | — / 47.48 / 52.85 | 86.91 / 89.83 / 89.76 |
| het | 76.31 / 87.46 / 85.29 | 46.68 / 45.88 / — | — / 89.42 / 87.86 |
| clean | 87.65 / 87.68 / 87.95 | 56.14 / 49.27 / 55.44 | 89.95 / 90.04 / 89.85 |

MAE collapses on DTD: it loses 6.9 points even with clean labels and falls below no defence in
every noisy scenario, while DBR-FPL beats no defence there. On Pets MAE is best; on Caltech MAE
and DBR-FPL tie except het (MAE +1.6).
