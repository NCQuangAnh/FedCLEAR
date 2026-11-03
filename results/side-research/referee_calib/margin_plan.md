# A second, scale-free flag for CLEAR-FPL: plan (written 2026-10-29, before any run)

This plan replaces `calib_plan.md`. That plan was never run, and it had a flaw: it kept tau =
0.05, but calibrating the referee moves honest clients' score from about −0.47 toward 0, so honest
false flags would jump. Its temperature idea remains here as one candidate (`cal`), now with a
re-derived threshold.

## What we know (offline, 2026-10-29)

- On MNIST and EuroSAT, CLEAR-FPL flags only 37% / 44% of noisy client-rounds, against about
  100% on Pets / DTD / Caltech. Its gain over PromptFL is then about +2 points
  (`../mnist_eurosat/results.md`).
- It is not CLIP's fault. Taking zero-shot CLIP out makes things worse, and removing the
  look-alike merge changes nothing (diagnostic follow-up in `../mnist_eurosat/plan.md`).
- It is not the small clients' fault. MNIST / EuroSAT clients hold about 8 images, against 30 to
  82 elsewhere. But cutting Pets / DTD / Caltech clients down to 8 images still flags 86 / 72 / 91%
  of noisy client-rounds.
- Honest clients score the same on every dataset: median about −0.47 (DTD −0.70). What shrinks is
  the noisy side. Noisy minus honest is +1.95 on Pets, +1.3 on DTD, +2.6 on Caltech, but only +0.41
  on MNIST and +0.35 on EuroSAT. The referee is underconfident there (about 70% right, 36% sure),
  so a wrong label costs little surprise.
- Inside flagged noisy clients, the image-level repair still finds 77% of the wrong labels on
  MNIST. More client flags should therefore pay off on MNIST.

## Idea

Keep CLEAR-FPL exactly as it is, and add a second trigger: `flag = CLEAR's flag OR trigger 2`.
- A client CLEAR flags today stays flagged, so on Pets / DTD / Caltech results can only change
  through extra flags. Those are measured before any real run.
- Repair is unchanged.
- Trigger 2 must not depend on how confident the referee is. Candidates:
  - **margin**, the normalised margin per client:
    R = Σ_i (max_k log P_ik − log P_iy) / Σ_i (max_k log P_ik − mean_k log P_ik).
    - R is 0 when every label is the referee's top choice and about 1 for random labels.
    - Tempering the referee (P^(1/T)) multiplies both sums by 1/T, so R is exactly invariant to
      under- or over-confidence.
    - It uses only the client's own data and no other client, so it cannot collapse when every
      client is noisy, as a federation median does (the DBR-FPL failure).
  - **margin_m**: the same on CLEAR's look-alike-merged distribution P_k + P_nn(k).
  - **cal**: CLEAR's score on a tempered referee. T is the largest value in {1.00, ..., 0.10}
    whose mean confidence reaches the pooled share of images whose top class equals the given
    label. It only sharpens, and noisy labels lower its target.
- Every threshold is the 95th percentile of honest client-rounds in Pets clean, the same rule as
  every earlier tau.

## Stage 0: logged-only runs, then an offline screen

The current logs lack the full probability vector, so none of the candidates can be computed yet.
- Code: `--diag_full_probs true` (`flip/flcore/diag.py`) adds every class's log-probability under the
  global prompt and under zero-shot CLIP to each per-image row, every 5 rounds, plus the look-alike
  map. It is logging only; training is unchanged (RNG restored, as for every diag).
- Local smoke on toy MNIST: rc 0. Recomputing CLEAR's score from the new columns matches the
  logged score to 1e-4 (`python tools/screen_stage0.py --check <file>`).
- Runs: PromptFL with the gate D flags (`D_<sc>_fp`) and the gate N flags (`N_<x>_fp`), seeds 0-2.
  These are the same seeds as the earlier runs. 24 runs, 5 notebooks:

| notebook | runs | about |
|---|---|---|
| `stage0_mnist_eurosat` | MNIST and EuroSAT: sym, pair, het, clean, N sym50, N pair50 | 5.5 h |
| `stage0_pets` | Pets: sym, pair, het, clean | 4.5 h |
| `stage0_dtd` | DTD: sym, pair, het, clean | 6 h |
| `stage0_caltech_a` / `_b` | Caltech101: sym, pair / het, clean | 6 h each |

`inst` is left out to save time; it behaved like `sym` in every earlier screen.

Screen: `tools/screen_stage0.py`, written before the data. Rounds 10-50. It uses the same
client-rounds for every rule. Honest = no wrong label; noisy = at least one.

### Selection rule (fixed now)

- **E1, old datasets stable.** On each of Pets, DTD and Caltech, `CLEAR OR candidate` flags honest
  client-rounds (mixed + clean) at most 7 points more than CLEAR alone.
  - The candidate alone flags 5% of Pets clean by construction; the 2 extra points are margin.
- **E2.** On MNIST, `CLEAR OR candidate` flags at most 10% of honest client-rounds.
- **Winner.** Among the candidates passing E1 and E2: the highest noisy flag rate on MNIST mixed
  settings. Within 2 points, prefer margin, then margin_m, then cal (fewest moving parts first).
- **Go.** The winner raises MNIST's noisy flag rate by at least 20 points over CLEAR alone.
  Otherwise stop, and report a negative result.
- **EuroSAT is the confirmation.** It is "confirmed" if noisy flags rise by at least 20 points with
  at most 10% honest flags. Otherwise EuroSAT is a stated limitation, and stage A still runs it.
- **Reported:** all-noisy settings on MNIST / EuroSAT (N sym50, N pair50); the median pooled T
  of `cal`.

## Stage A, only after "Go": real runs on MNIST and EuroSAT

- Arm `<trigger>`: CLEAR-FPL plus the winner as a second trigger, with its threshold from the screen.
- 11 settings × 2 datasets = 22 runs, 5 seeds.
- Compared with the existing CLEAR-FPL and PromptFL runs (same seeds). Local smoke first.

Rules, per dataset:
- **A1.** On the mixed settings, rounds 1-50, noisy flags are at least CLEAR + 20 points, and honest
  flags are at most 10%.
- **A2.** The mean over the 10 noisy settings of new − CLEAR is at least +1 point, and no setting is
  significantly worse (paired t-test, p < 0.05).
- **A3.** On S clean, new − PromptFL is at least −1 point.
- **A4.** On the mixed settings, the share of relabels that break a right label is at most CLEAR's
  + 5 points.

Stage B runs if MNIST passes A1-A4. If only MNIST passes, EuroSAT is reported as a limitation.
If MNIST fails, stop.

## Stage B: no-collapse check on Pets, DTD and Caltech101

- 33 runs (11 settings each).
- **B1, per dataset.** The mean over the 11 settings of new − CLEAR is at least −0.3, and no setting
  is significantly worse by more than 1 point.

## Known weak spots, stated before the runs

- R ignores how confident the referee is, but not how accurate it is. EuroSAT (69% right) may draw
  more honest flags.
- EuroSAT repairs poorly: only 7% of the wrong labels in flagged clients are fixed by relabelling.
  More flags may help it little.
- High pair noise (N pair50 / 75) stays hard.
- Overlap to check before writing up: AUM (Pleiss et al. 2020, margin-based mislabel detection)
  and Confident Learning (Northcutt et al. 2021, per-class self-confidence thresholds).
  - Claimed as new: the diagnosis that underconfidence, not CLIP's errors, breaks a CLIP-based
    noisy-client detector on far domains;
  - Claimed as new: a confidence-invariant, per-client trigger that fixes it without a federation
    reference.

## Outcome of stage 0 (2026-10-29): NO GO, negative result

All 24 runs finished (rc 0, 3 seeds each). They are in `stage0_*/`, and the zips are deleted.
`--check` on Pets D sym seed 0 recomputes the logged xs_m to 9e-5. Full table: `stage0_screen.md`.

| rule | MNIST honest / noisy | EuroSAT | Pets | DTD | Caltech101 |
|---|---|---|---|---|---|
| clear | 0 / 44% | 3 / 52% | 1 / 92% | 0 / 85% | 0 / 96% |
| clear OR cal | 14 / 66% | 12 / 59% | 2 / 92% | 2 / 89% | 0 / 96% |
| clear OR margin | 75 / 99% | 87 / 100% | 17 / 100% | 98 / 100% | 5 / 100% |
| clear OR margin_m | 76 / 95% | 82 / 99% | 15 / 100% | 99 / 100% | 5 / 100% |

Pre-registered reading:
- `margin` and `margin_m` fail both E1 and E2.
- `cal` passes E1 but fails E2: 13.7% honest flags on MNIST, above the 10% limit. Its MNIST gain
  was +21.6 points.
- No candidate is eligible, so stage A and stage B are not run.

Exploratory follow-up (written after the data; it does not change the verdict):
- **Why margin fails.** R ignores the referee's confidence but not its accuracy. Its honest
  median is 0.012 to 0.014 on Pets and Caltech, but 0.08 on MNIST, 0.10 on DTD and 0.14 on
  EuroSAT. A threshold taken from Pets therefore flags most honest clients wherever the referee
  is less accurate. DTD shows this too, although CLEAR handles DTD well. This is the weak spot
  stated above, and it turned out larger than expected.
- **The signal itself is weaker on MNIST and EuroSAT, not only the threshold.** AUROC between
  noisy and honest client-rounds (rounds 10 to 50):

  | score | MNIST | EuroSAT | Pets / DTD / Caltech |
  |---|---|---|---|
  | clear | 0.84 | 0.86 | 0.99 to 1.00 |
  | margin | 0.88 | 0.88 | 1.00 |

  Even with a threshold fitted on each dataset's own honest clients (an oracle, which no client
  could compute in practice), at 5% honest flags the share of noisy client-rounds flagged is:

  | score | MNIST | EuroSAT |
  |---|---|---|
  | clear | 56% | 54% |
  | margin | 68% | 53% |

  So any rule that does not use the dataset's own labels could gain at most about +12 to +24
  points on MNIST and about +2 on EuroSAT at that false-flag level.
- **Conclusion for the thesis.** On far domains, CLEAR-FPL's client score still ranks clients
  (AUROC about 0.85), but noisy and honest clients overlap more. A fixed threshold that carries
  across datasets then misses about half of the noisy client-rounds. Neither a confidence-free
  score nor a pooled temperature fixes this without false flags. This is a stated limitation,
  with the underconfidence diagnosis as the finding.
