# Referee-strength gate: offline check (plan, fixed 2026-10-30 before any signal was computed)

## Question

Stage A of `cal` failed (`results.md`). Its repair gains a lot where CLIP is a strong referee:
- Caltech 75%: +3.9 / +8.4;
- Pets sym75: +5.1;
- DTD N25: +5.4 / +4.5.

It loses where CLIP is weak: EuroSAT is lower in 10 of 11 settings.

Can the federation tell, **without clean labels**, when the referee is strong enough to switch from CLEAR-FPL's repair to `cal`'s repair?

The gated method is: use `cal` when the gate is on, CLEAR-FPL when it is off. Offline, the gated result in a setting is therefore `cal − CLEAR` when the gate is on, and 0 when it is off. This uses the 30 stage-A settings, for which both arms have 5 real seeds.

## Honesty note

The per-setting outcomes of stage A are already known. Only the signal values are not. So this check is exploratory: a GO here only earns a confirmatory run (stage B settings plus the gate), never adoption.

Known before computing anything: no gating of `cal` can pass the old A1 bar.
- The mean over the six 75% runs is +2.23 with every run on.
- With the three losing 75% runs gated off, it is 17.42 / 6 = +2.90, still below +3.0.

## Candidate signals (label-free: noisy labels and referee outputs only, never the true labels)

| id | signal | source |
|---|---|---|
| Z1 | median calibrated temperature T, client-rounds 1-5 | `cal` runs, `sure` records |
| Z2 | relabel share = Σ relabelled / Σ suspects over client-rounds 1-5 (the referee confidently names another class) | CLEAR-FPL runs (what the gate sees while running CLEAR) |
| Z3 | zero-shot confidence = mean over images of max-class zero-shot CLIP probability; one value per dataset, independent of noise | stage-0 `*_fp` logs, column z |

Secondary, report only: Z2 computed from the `cal` runs instead, and Z1/Z2 over rounds 1-50.

## Threshold

The threshold is chosen leave-one-dataset-out:
- For each held-out dataset, the threshold and its direction (on when above, or on when below) are picked on the other four datasets' stage-A settings, to maximise the total gated gain.
- Ties go to the midpoint between neighbouring signal values.
- The chosen threshold is then applied to the held-out dataset.
- Z3 is dataset-level, so its held-out dataset is decided by a threshold learned on the other four values.

## Pass criteria (per signal, on the leave-one-dataset-out gated results)

- **G1 (no harm).**
  - No setting is significantly worse than CLEAR-FPL (paired p < 0.05) by more than 1 point.
  - Every dataset's mean gated − CLEAR over its stage-A settings is at least −0.3.
- **G2 (gain kept).** The total gated gain over the 30 settings is at least 50% of the oracle gate's total gain. The oracle gate is on exactly where `cal − CLEAR > 0`.

**GO** if at least one signal passes G1 and G2. If several pass, take the one with the largest gain.

A GO leads to:
- a stage-B-style confirmation (Pets / DTD / Caltech, the 25 settings `cal` never ran, gate included);
- dropping the calibrated extra flag (lesson from stage A).

**NO GO** closes the referee-strength line: the limitation is reported as is.

## Outcome (2026-10-30; details in `gate_screen.md`)

**Amendment, made after the first run of the script.** The plan did not cover a setting where a signal has no value. That happens for Z2 on MNIST S clean: nothing is flagged in rounds 1-5, so there are no suspects. Such a setting keeps the gate off (CLEAR-FPL). It is the only case affected.

**Verdict: NO GO.** All three primary signals fail G1 and G2 under the leave-one-dataset-out threshold.

**Why.** EuroSAT is the only dataset where `cal` hurts. MNIST, with an equally weak referee, has a positive total (+6.95, noise-level). So when EuroSAT is held out, the best threshold on the other four datasets is "always on", and the gate turns `cal` on for EuroSAT.

**What the signals show (exploratory).** The relabel share Z2 is in effect a dataset-level referee-strength measure that does not move with the noise level, unlike the temperature T. Over all 55 settings of the CLEAR-FPL runs:

| dataset | relabel share Z2 |
|---|---|
| EuroSAT | 0.03-0.06 |
| MNIST | 0-0.15 |
| DTD | 0.13-0.29 |
| Pets | 0.55-0.82 |
| Caltech | 0.79-0.88 |

- A fixed threshold anywhere between about 0.06 and 0.18 passes G1 and G2 on the 30 stage-A settings, keeping 59-78% of the oracle gain. That threshold is chosen post hoc.
- Zero-shot confidence Z3 passes only between EuroSAT (0.318) and DTD (0.394).
- T passes only in a narrow band.

**Open risk.** A gate at about 0.12 would turn `cal` on in every DTD setting, including the mixed settings. There the offline screen expects `cal` to leave more noise (DTD sym 2.5% → 4.3%, het 7.8% → 12.0%).
