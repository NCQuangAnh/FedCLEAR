# 20-client study: plan (written 2026-10-27, before any run)

Question: does CLEAR-FPL keep its gain over PromptFL when the federation has 20 clients instead of 10?

## Setup
Everything as in the 10-client runs (FLIP, CLIP RN50, CoOp, Dirichlet 0.1, 8 shots, 50 rounds,
5 seeds, last10), except `--num_clients 20`. The noisy fractions are unchanged, so:

| setting | noisy clients | noise per noisy client |
|---|---|---|
| S_sym / S_pair / S_inst | 6 of 20 | 40% |
| S_het | 10 of 20 | 8, 16, 24, 32, 40, 48, 56, 64, 72, 80% |
| S_clean | 0 | 0 |
| N_sym25 ... N_pair75 | 20 of 20 | 25 / 50 / 75% |

Arms: `c20` (CLEAR-FPL, `--sure true`, cap 60%, threshold 0.1) and `c20p` (PromptFL). Queues:
`server/queue_c20.txt` and `server/queue_c20_promptfl.txt`, 33 runs each.
Each client holds about half the images it had with 10 clients. A simulation of the split
(seeds 0-4) gives the smallest client 5-8 images on Pets, 6-13 on DTD, 14-30 on Caltech.

## Decision rules (fixed now)
- R1, gain kept: on every dataset, CLEAR-FPL-20 minus PromptFL-20, averaged over the 10 noisy
  settings, is above 0, and CLEAR wins with paired t-test p < 0.05 over 5 seeds in at least 5 of
  the 10 noisy settings.
- R2, clean not hurt: on S_clean, CLEAR-20 is not below PromptFL-20 by more than 1 point.
- R3, client detection: the client-level AUROC at the first check, over the 4 mixed settings
  (S_sym / pair / inst / het), is at least 0.90 on every dataset (10 clients: 1.00 / 0.99 / 1.00).
- Reported, not decided: the gain at 20 clients next to the gain at 10 clients, per dataset.

If R1-R3 pass: write "the gain holds at 20 clients". If any fails: report which one and where,
as a limitation (the likely cause to check first is the very small clients on Pets).
