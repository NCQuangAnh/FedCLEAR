# Gate N plan: NLPrompt-style noise, every client noisy (written 2026-10-19, before any run)

## Why

NLPrompt (CVPR 2025) corrupts the whole training set at one rate, symmetric (flip to any other
class) or asymmetric (flip to the next class), 12.5-75%. Our scenarios so far corrupt only some
clients. Here every client is noisy at the same rate, in the federated setting. It answers the
cô's question (how does NLPrompt simulate noise, and does our method hold under it), and it is
the case where the old DBR-FPL should break: its baseline is the 25% low quantile of the clients'
disagreement, which assumes some clients are clean.

## Arms (FLIP protocol, CLIP RN50, 8 shots, 10 clients, Dirichlet 0.1, 50 rounds, 5 seeds)

Noise: `sym` or `pair` (= NLPrompt's asym), rate 25 / 50 / 75%, on all 10 clients
(`--noisy_client_frac 1.0`). Datasets: Pets, DTD, Caltech101. Per noise setting:

| arm | what |
|---|---|
| `N_<noise><rate>_none` | PromptFL |
| `N_<noise><rate>_mae` | PromptFL + MAE |
| `N_<noise><rate>_dbr` | old DBR-FPL |
| `N_<noise><rate>_clear` | CLEAR-FPL (`--sure true`, frozen settings of stage 2) |

Ceiling: the clean runs of gate D (`S_clean_full` / `D_clean_none`), same seeds.
Note: pair at 75% makes most labels of each class point to the previous class, so it is beyond
what any label-noise method can identify; it is run for completeness, as NLPrompt does.

## Criteria, fixed now (last10, paired over seeds; 18 combos = 2 noise x 3 rates x 3 datasets)

1. CLEAR − none > 0 with p < 0.05 in at least 12 of the 12 combos at 25% and 50%.
2. CLEAR − MAE ≥ −0.5 in at least 10 of the 12 combos at 25% and 50%, and CLEAR > MAE on every
   DTD combo at 25% and 50%.
3. CLEAR − DBR-FPL > 0 on average over the 12 combos at 25% and 50%.
4. CLEAR flags at least 90% of client-rounds (rounds 10-49) at 25% and 50% on every dataset.

The 75% results are reported, not judged.
