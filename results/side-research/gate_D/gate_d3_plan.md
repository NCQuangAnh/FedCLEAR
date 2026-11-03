# Gate D stage 3 plan: stop repairing correct labels on hard datasets (written 2026-10-18, before any run)

## Problem (from stage 2)

On clean DTD the method costs 0.87 (p = 0.048). Cause, read from the `sure` records: 5-10% of
honest client-rounds are flagged, and a flagged client treats every image with P(label) < 0.1 as
a suspect. On DTD the model is weak, so many correctly labelled images sit below 0.1: across
5 seeds, honest clients lost 906 correct images in rounds 0-9 alone, plus 130 wrong relabels.
On Pets the same false flags touch few images (P(label) is rarely that low for a correct label),
and on Caltech nobody honest is flagged.

## Two candidate fixes, chosen on Pets, then confirmed on DTD and Caltech

| arm | change to the stage 2 method |
|---|---|
| `S_<sc>_budget` | a flagged client repairs at most (its suspects − the suspects P expects for correct labels), expected = sum over images and classes of P_k [P_k < 0.1]. Self-referenced, no new parameter |
| `S_<sc>_keep` | a suspect P cannot relabel with >= 0.5 confidence is kept, not dropped |

Pets, 5 scenarios each, 5 seeds (kaggle/gate_d3_pets_budget.ipynb, gate_d3_pets_keep.ipynb).
Reference: `S_<sc>_full` (stage 2, same seeds).

## Selection rule on Pets, fixed now

A candidate qualifies if, against `S_full` on Pets:
- mean accuracy over the 4 noisy scenarios is at least `S_full` − 0.3, and
- clean accuracy is at least `S_full` − 0.3.

Among qualifying candidates, the one that touches fewer correct images of honest clients (dropped
plus wrongly relabelled, rounds 0-49, all scenarios) wins. If neither qualifies, `S_full` stays
and the DTD clean cost is reported as a limitation.

## Confirmation (after the choice): the winner on DTD and Caltech, all 5 scenarios

The winner replaces `S_full` in the stage 2 criteria. It must:
- cost no more than 0.3 on clean DTD;
- keep `new − MAE` > 0 (p < 0.05) on every DTD combo;
- not fall below `S_full` by more than 0.3 on average over the noisy combos of each dataset.
