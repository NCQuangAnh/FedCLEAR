# Gate V plan: other noise types, and naming the noisy clients (written 2026-10-14, before any run)

## Why

Gate Q-MAE failed its criterion: under symmetric 40% noise, PromptFL + MAE (a one-line loss
change) matched or beat DBR-FPL. DBR-FPL can only keep a claim on what MAE does not give:
(a) robustness across noise types, and (b) saying WHICH clients are noisy. On (b) DBR-FPL has a
known weakness: on Pets an honest client holding look-alike classes (american bulldog, pit bull)
reaches the same disagreement as a careless one (0.43 vs 0.43-0.47, seed 0, round 50), gets a
budget and has correct labels relabelled (honest harm 3.23% on Pets).

## The fix tested (`--filter_dis far`)

`d_far` = the share of a client's images where the global model's prediction differs from the
label AND is not the label's nearest class in CLIP's zero-shot text space (k = 1 neighbour,
computed from the class names only, no data, nothing extra on the wire). The budget uses
`d_far` and its own 25% low-quantile baseline; the soft/hard mode choice still uses `d`, so only
the budget changes. Both `d` and `d_far` are logged in every filtered run.

Known blind spot, stated now: noise that flips a label to its own look-alike is invisible to
`d_far`. Under pair noise (label -> next class index) this happens only where the next index
happens to be the nearest class; the share will be reported.

## Setting

7 honest + 3 careless clients, 40% flip rate, FLIP protocol, CLIP RN50, 8 shots, 50 rounds,
seeds 0-4 (same splits and roles as gate Q, so `K_restore` is the shared all-clean ceiling).

- `pair`: flip to the next class index (Han et al. 2018).
- `inst`: instance-dependent (Xia et al. 2020), on raw pixels, per-image flip rate ~ N(0.4, 0.1).
- `sym`: stored gate Q runs, plus the new `V_sym_far`.

Arms per noise type: `V_<n>_none` (CE), `V_<n>_mae` (PromptFL + MAE), `V_<n>_dbr` (DBR-FPL as
before), `V_<n>_far` (DBR-FPL with `d_far`).

Sessions: Pets (9 jobs incl. `V_sym_far`), Caltech pair (+ `V_sym_far`), Caltech inst.

## Criteria, fixed now

Accuracy = last10, paired over seeds.

1. **Handles other noise types:** `V_far − V_none` > 0 with p < 0.05 on all four of
   {pair, inst} x {Pets, Caltech}.
2. **Not worse than the robust loss:** `V_far − V_mae` ≥ −0.5 on all four. (Reported in
   addition: where it is > 0 and significant.)
3. **Names the noisy clients better:** a client-round is flagged when its budget ρ > 0, rounds
   10-49, pooled over seeds.
   - 3a. On Pets sym (where the problem was seen) the honest false-flag rate of `V_sym_far` is at
     most half that of `Q_fixconf`.
   - 3b. In every combo where `V_dbr` flags ≥ 90% of the careless client-rounds, `V_far` also
     flags ≥ 90%.
   - Reported, not judged: per-round AUROC of `d_far`, `d`, and of the client training loss in
     the `none` and `mae` runs (the loss-based detector a robust-loss method would have).
4. **The fix costs no accuracy:** mean of `V_far − V_dbr` over the six combos
   ({sym, pair, inst} x {Pets, Caltech}) ≥ −0.3.

## What each outcome means

- 1 + 2 + 3 pass: DBR-FPL's claim becomes "matches a robust loss on accuracy across three
  noise types, and additionally names the noisy clients with few false accusations".
- 2 fails: MAE stays the better accuracy method; DBR-FPL is reported as a detector only.
- 3 fails: the look-alike explanation of the honest false flags is wrong (or incomplete); the
  next candidate is the leave-one-out per-class baseline (needs secure aggregation of per-class
  counts).
