# Gate D stage 2 plan: the frozen method (written 2026-10-17, before any run)

## Method (`--sure true`, flip/flcore/sure.py), every setting fixed from Pets in stage 1

Each round, before training, a client scores its own data against P = average of the global
prompt's and frozen zero-shot CLIP's predictions:

1. **Client score** = merged excess surprise of its labels (stage 1 winner, `e.xs_m`).
2. **Flag** if score > 0.05 (= 95th percentile of honest clients in Pets clean). Fixed for every
   dataset: the score is self-referenced, honest clients sit near 0 everywhere.
3. **Repair, flagged clients only**: an image with P(label) < 0.1 is a suspect; relabelled to P's
   top class if P(top) >= 0.5, otherwise left out of the round; at most 60% of a client touched.
   (Pets careless clients, stage 1 logs: suspects 94-97% truly noisy, catching 81-97% of the
   noise; relabels right 85-88%.)
4. Unflagged clients train untouched. Sent up per round: the prompt, the score, the flag.

## Arms (5 seeds, 50 rounds, FLIP protocol, CLIP RN50, 8 shots; Pets, DTD, Caltech101)

Scenarios as stage 1: sym, pair, inst (3 careless at 40%), het (5 careless at 16-80%), clean.

| arm | what |
|---|---|
| `S_<sc>_full` | the method |
| `S_<sc>_all` | repair every client (no client-level decision) |
| `S_<sc>_noclip` | global prompt only, no zero-shot mix (tau = its own Pets clean p95, 0.072) |
| `S_<sc>_d` | the old disagreement as client score (tau = Pets clean p95, 0.304), global only |
| comparators | stage 1 runs, same seeds: `D_<sc>_none`, `D_<sc>_mae`, `D_<sc>_dbr` |

## Criteria, fixed now (last10, paired over seeds; 12 noisy combos = 4 scenarios x 3 datasets)

1. **Works:** `full − none` > 0 with p < 0.05 in at least 10 of the 12 noisy combos.
2. **Not worse than MAE anywhere, better where MAE breaks:** `full − mae` ≥ −0.5 in all 12, and
   `full − mae` > 0 with p < 0.05 in every DTD combo.
3. **Better than the old DBR-FPL:** mean of `full − dbr` over the 12 combos > 0.
4. **Harmless when nobody is careless:** in `clean`, `full − none` ≥ −0.5 on each dataset, and at
   most 5% of honest client-rounds flagged (rounds 10-49) in every scenario and dataset.
5. **Names the careless clients:** at least 90% of careless client-rounds flagged (rounds 10-49)
   in sym, pair and inst on each dataset; het reported (the 16% client is expected to be missed).

Reported, not judged: each ablation's cost (`full − all`, `full − noclip`, `full − d`), repair
precision / relabel accuracy, flags per round, time per round.
