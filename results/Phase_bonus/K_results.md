# Gate K results: relabel instead of delete (OxfordPets, 2026-09-25)

Plan and criteria: `gate_k_plan.md` (written before running). Data-only attacker, 5 seeds (0-4),
last10 on the test set. Raw files: `K_/pets/phase6_results.zip`. Caltech101 (5b) still pending.

## Accuracy (last10)

| Arm | seed 0 | 1 | 2 | 3 | 4 | mean |
|---|---|---|---|---|---|---|
| `K_base` | 86.75 | 87.24 | 84.94 | 84.43 | 83.87 | **85.45** |
| `K_fix` | 87.49 | 86.86 | 84.08 | 85.95 | 85.25 | **85.93** |
| `K_fixconf` | 87.70 | 86.75 | 83.62 | 85.94 | 83.66 | **85.54** |

| Paired (n = 5) | mean | sd | t | per seed |
|---|---|---|---|---|
| `K_fix − K_base` | **+0.48** | 1.06 | +1.01 | +0.74, −0.39, −0.86, +1.52, +1.38 |
| `K_fixconf − K_base` | +0.09 | 1.14 | +0.17 | |
| `K_fixconf − K_fix` | −0.39 | 0.71 | −1.23 | |
| `K_base − H_auto (gate J)` | +0.30 | 1.30 | +0.51 | |

The server chose hard mode on 169 of 250 probe rounds (68%), soft mode on 81. Relabelling only
happens in hard rounds.

## Relabel audit (label-rounds summed over 5 seeds; one image is counted once per refresh)

| `K_fix` | relabelled | restored to true label | clean label broken | changed but still wrong |
|---|---|---|---|---|
| noisy | 4,806 | 3,535 (74%) | 158 (3%) | 1,113 |
| malicious | 3,677 | 2,413 (66%) | 438 (12%) | 826 |
| honest | 607 | 0 | 607 (100%) | 0 |

`K_fixconf` relabels about 20% fewer labels with a similar hit rate, and it deletes the rest. It
comes out lower than `K_fix`, so the confidence gate does not pay for itself here.

## Reading against the pre-registered criteria

- `K_fix` beats `K_base` by +0.48, but p is about 0.37 (t = 1.01, 4 degrees of freedom), and 2 of 5
  seeds go the wrong way. That is the row **"better but not p < 0.05"**: the direction is right and
  the evidence is not enough. The prediction was +0.5 to +1.5; the result sits at the lower edge.
- Caltech101 decides whether a K arm reaches p < 0.05 on at least one dataset.
- `K_base` is +0.30 from the old `H_auto` (< 0.5), as predicted: changing the attacker to data-only
  barely moves the current method on Pets.
- The known risk shows up in the audit: on malicious clients 12% of the relabels overwrite a clean
  label (438), against 3% on noisy clients. On honest clients every relabel is a break. For comparison,
  `K_base` deletes 1,038 honest label-rounds. The log does not say whether these are the same
  images, so this is only a comparison of counts.

## Where `K_fix` gains and loses, by client type (estimate)

This cannot be measured directly: the runs give one global accuracy, not one per client. The
estimate prices each change against `K_base` with the exchange rate fitted on DTD (dirty removed
+0.326, clean removed −0.437 per 1000). A clean label broken is priced as a clean one removed plus a
dirty one added. A dirty label moved to a different wrong class is priced as a dirty one kept. The
model predicts +1.54 in total where +0.48 was measured, so every term is scaled by 0.31 to match.
Only the shares carry information.

| Type | fewer clean deleted | clean labels broken | dirty labels restored | dirty relabelled to another wrong class | net |
|---|---|---|---|---|---|
| honest | +0.08 | **−0.14** (607) | — | — | **−0.06** |
| noisy | +0.03 | −0.04 (158) | +0.48 (3,535) | **−0.11** (1,113) | **+0.35** |
| malicious | +0.06 | **−0.10** (438) | +0.33 (2,413) | **−0.08** (826) | **+0.19** |

Losses total about −0.47 and gains about +0.95. Two mechanisms cause the losses, in similar amounts:
- The global model is wrong on a suspect that was actually clean, and the relabel breaks it. This
  hits honest clients most (every relabel there is a break) and malicious clients next (12%).
- A dirty image is relabelled to a class that is still wrong. It stays in training as a dirty image,
  where `K_base` would have deleted it. The log does not record which class these went to, so it
  cannot say whether the malicious ones moved towards the attacker's target.

# Caltech101 (5b, 2026-09-25)

Raw files: `K_/caltech/phase6_results.zip`. All three arms finished (rc 0, about 2.7-2.95 h each).
The server chose hard mode on 211 of 250 probe rounds (84%), against 68% on Pets.

| Arm | seed 0 | 1 | 2 | 3 | 4 | mean |
|---|---|---|---|---|---|---|
| `K_base` | 87.49 | 90.28 | 88.62 | 88.85 | 88.86 | **88.82** |
| `K_fix` | 89.21 | 91.14 | 89.62 | 88.19 | 89.20 | **89.47** |
| `K_fixconf` | 88.96 | 90.84 | 89.35 | 88.91 | 89.29 | **89.47** |

| Paired (n = 5) | mean | sd | t | p (two-sided) | per seed |
|---|---|---|---|---|---|
| `K_fix − K_base` | +0.65 | 0.88 | +1.65 | 0.17 | +1.72, +0.86, +1.00, −0.66, +0.34 |
| `K_fixconf − K_base` | **+0.65** | 0.52 | **+2.79** | **0.049** | +1.47, +0.55, +0.73, +0.06, +0.43 |
| `K_fixconf − K_fix` | −0.00 | 0.43 | −0.01 | 0.99 | |
| `K_base − H_auto (gate J)` | +0.10 | 0.70 | +0.31 | | |

## Relabel audit (label-rounds, 5 seeds)

| | relabelled | restored | broke a clean label | still wrong |
|---|---|---|---|---|
| `K_fix` noisy | 18,799 | 77% | 7% | 16% |
| `K_fix` malicious | 12,241 | 79% | 6% | 15% |
| `K_fixconf` noisy | 16,530 | 85% | 4% | 11% |
| `K_fixconf` malicious | 10,966 | 86% | 4% | 10% |
| honest | 229 (`K_fix`) / 205 (`K_fixconf`) | 0 | all | 0 |

On Caltech the confidence gate does what it was meant to do: it removes about half of the bad
relabels and loses almost none of the good ones. On Pets it did not. The explanation first offered here
(the teacher is unsure even when right, so the gate deleted good fixes) was checked on the
`gate_k_diag` log and is **wrong**. On Pets the 0.5 gate blocks 443 right relabels and 801 wrong
ones, a net gain offline. The −0.39 of `K_fixconf` against `K_fix` on Pets (p ~ 0.29) is most likely
seed noise.

## Verdict against the pre-registered criteria (both datasets now in)

The criterion reads: *a K arm beats `K_base` with p < 0.05 on at least one dataset, and is not more
than 0.3 worse on the other*.

- **`K_fixconf` meets it:** Caltech +0.65 (p = 0.049), Pets +0.09 (not worse). Reading as written:
  **relabelling wins and becomes the third mode of the rule.**
- `K_fix` does not meet it: +0.65 (p = 0.17) on Caltech and +0.48 (p = 0.37) on Pets. It is
  positive on both datasets, though.

Honest caveats, all of which go into the thesis next to the verdict:
1. p = 0.049 sits right on the line. Four tests were run (2 arms x 2 datasets). Any correction for
   that (Bonferroni: 0.0125) would not pass, and the criterion did not ask for one.
2. Pooled over both datasets (10 pairs, a descriptive check that was not pre-registered):
   `K_fix` +0.56 (t = 1.93, p ~ 0.09), `K_fixconf` +0.37 (t = 1.32, p ~ 0.22). The arm that passes
   on its own is not the one that looks best pooled.
3. The choice between the two arms is not settled. They tie on Caltech (−0.00), and `K_fix` leads
   on Pets (+0.39, p ~ 0.29).
4. The size is modest, +0.4 to +0.7 points. The prediction was +0.5 to +1.5, and both datasets sit
   at the low end of it.

Decision: adopt `K_fixconf` as the relabel mode, as the criterion says, and describe it as "a small,
consistent gain, significant on one dataset at the 0.05 edge". The `gate_k_diag` offline rules (A/B/D)
are still worth running: the losses they target are 21-23% of relabels on `K_fix` and 14% on
`K_fixconf`.

# gate_k_diag: other relabel rules scored offline (OxfordPets, 2026-09-25)

`K_fix_log` reproduces `K_fix` to the digit on all 5 seeds (difference 0.00), so the logging
changed nothing. The scorer's `K_fix` counts match the run's own audit exactly (607 / 3,677 /
4,806 relabelled; 2,413 / 3,535 right). Each rule was scored on the same hard-round suspects,
valued against deleting: right +0.437, wrong −0.326 per 1000.

| Rule | right on malicious | right on noisy | honest broken | total value | vs K_fix |
|---|---|---|---|---|---|
| K_fix (top-1) | 65.6% | 73.6% | 607 | +1.575 | — |
| **A client prior** | **74.3%** | **78.0%** | 459 | **+1.985** | **+26%** |
| B stable over 2 refreshes | 66.4% | 74.2% | 564 | +1.598 | +1% |
| D never into over-full class | 62.7% | 66.5% | 602 | +0.935 | −41% |
| A + D | 71.9% | 72.8% | 444 | +1.326 | −16% |
| A + B | 75.0% | 78.6% | 385 | +1.865 | +18% |
| margin 0.2 | 71.9% | 78.4% | 377 | +1.707 | +8% |

Against the rule fixed before the data (≥ 20% over K_fix, and malicious right-rate not lower):
**only A passes** (+26%, 74.3% ≥ 65.6%). A + B misses at +18%.

D fails badly. On noisy clients the over-full classes are simply the big true classes, so D blocks
good relabels (1,398 extra deletions). Caveat: every rule is scored one step on the trajectory
`K_fix` produced; the teacher it would itself train is not simulated. Hence the GPU arm.

## Addendum 2 to the plan (written before `K_prior` runs)

`--filter_relabel prior` implements A exactly as scored. `MODE = "gate_k_prior"` runs `K_prior` on
OxfordPets and Caltech101, same seeds, paired against the stored `K_base`, `K_fix` and `K_fixconf`.
- `K_prior` replaces `K_fixconf` as the relabel mode if its mean is higher than `K_fixconf` on
  both datasets and higher by at least 0.3 pooled over the 10 pairs.
- Otherwise `K_fixconf` stays, and A is reported as an offline-only improvement in label quality.

# gate_k_prior results (2026-09-25)

| | Pets | Caltech101 |
|---|---|---|
| `K_prior` mean | 85.53 | 89.39 |
| vs `K_base` | +0.08 (p 0.92) | +0.57 (p 0.081) |
| vs `K_fix` | −0.40 (p 0.39) | −0.09 (p 0.69) |
| vs `K_fixconf` | −0.01 (p 0.99) | −0.08 (p 0.033, every seed slightly lower) |

Pooled over 10 pairs, against `K_fixconf`: −0.05 (p 0.86).

Criterion (higher than `K_fixconf` on both datasets and +0.3 pooled): **fails. `K_fixconf` stays the
relabel mode.** The +26% offline gain in label quality did not reach accuracy. Its absolute size is
small: about +0.4 value units per 1000 label-rounds, which is well under seed noise. It was also
measured against `K_fix`, not `K_fixconf`, and one step along `K_fix`'s own trajectory. Lesson: an
offline label-quality gain needs to be several times larger than the accuracy noise before it earns
GPU time.

# gate_k_proto results (2026-09-28)

Plan: `gate_k_proto_plan.md`, written before the runs. Raw files are in `K_/proto/{pets,caltech}`.
`K_restore` is the all-clean oracle (every damaged label restored), 5 seeds, in this exact
configuration.

| | no defence (`A0_refuse`) | `K_base` | `K_fixconf` | **`K_proto`** | `K_restore` (oracle) |
|---|---|---|---|---|---|
| Pets | 75.88 | 85.45 | 85.53 | **87.24** | 87.88 |
| Caltech | 84.52 | 88.82 | **89.47** | 88.43 | 90.21 |
| share of the gap to the oracle closed (Pets / Caltech) | | 80% / 76% | 80% / 87% | **95%** / 69% | 100% |

| Paired (n = 5) | Pets | Caltech |
|---|---|---|
| `K_proto − K_fixconf` | **+1.71 (p 0.037)** | **−1.04 (p 0.049)** |
| `K_restore − K_fixconf` | +2.35 (p 0.030) | +0.74 (p 0.038) |
| `K_restore − K_proto` | +0.64 (p 0.10) | +1.78 (p 0.010) |

## Verdict against the pre-registered criterion

*Beats `K_fixconf` with p < 0.05 on at least one dataset and is not more than 0.3 worse on the other*:
Pets yes, but Caltech is **1.04 worse** (p 0.049). **`K_proto` fails as written, and `K_fixconf` stays the
relabel mode.** The result is split: a large, significant win on Pets (95% of the gap to the
all-clean oracle) and a significant loss on Caltech.

## Why: the audit (label-rounds, 5 seeds)

| | suspects: really damaged | damage caught | relabel: fixed / broke | honest clean labels harmed |
|---|---|---|---|---|
| Pets noisy / malicious | 85% / 81% | 96% / 100% | 76% / 10% · 66% / 16% | 2,547 broken + 1,099 deleted |
| Caltech noisy / malicious | 85% / 86% | 98% / 89% | 81% / 10% · 80% / 10% | **4,158 broken + 3,011 deleted** |
| `K_fixconf`, Caltech (for comparison) | | | 85% / 4% · 86% / 4% | 205 broken + 175 deleted |

1. **The cluster check finds almost all the damage**: 89-100% recall, against the loss filter's
   budget-limited selection.
2. **But `K_proto` has no clean band.** `K_fixconf` leaves alone every client whose disagreement sits
   near the clean baseline, so honest clients are barely touched. `K_proto` checks every client, and
   about 6% of an honest client's clusters fail the check (the pass rate for clean clusters was
   92-94% in gate P). Every such image is then relabelled or deleted. On Caltech that is about 7,200
   harmed honest label-rounds, 20 times `K_fixconf`'s.
3. **Relabel accuracy is lower on Caltech** (10% broken against 4%). `K_fixconf` relabels only in hard
   rounds, when the global model is good. `K_proto` relabels from round 0 with the global+zero-shot
   average.
4. On Caltech `K_fixconf` already closes 87% of the gap, so there is little to win and these side
   effects dominate. On Pets the room was larger (80% closed) and the extra recall pays.
5. The user's point is confirmed. The attackers' failing clusters mix many source classes: up to
   9 on Pets and up to 23 on Caltech. Relabelling a cluster as a whole would have been wrong.
   Relabelling image by image was necessary.

## Next (to be pre-registered before running)

`K_proto_band`: the same cluster check, but inside the existing clean band. A client whose
disagreement is within 0.10 of the baseline is not touched, exactly as in `K_fixconf`. That targets
reason 2 directly. Reason 3 suggests relabelling only in hard rounds, like `K_fixconf`. Both stay
cheap, since the method runs on the client.

# K_proto_band results (2026-09-28)

Plan: `gate_k_proto_band_plan.md`, written before the runs. Raw files are in `K_/proto_band/{pets,caltech}`.

| | no defence | `K_base` | `K_fixconf` | `K_proto` | **`K_proto_band`** | `K_restore` (oracle) |
|---|---|---|---|---|---|---|
| Pets | 75.88 | 85.45 | 85.53 | 87.24 | **87.46** | 87.88 |
| Caltech | 84.52 | 88.82 | **89.47** | 88.43 | 88.23 | 90.21 |
| gap to the oracle closed (Pets / Caltech) | | 80% / 76% | 80% / 87% | 95% / 69% | **97%** / 65% | 100% |

| Paired (n = 5) | Pets | Caltech |
|---|---|---|
| `K_proto_band − K_fixconf` | +1.93 (p 0.12; seeds −0.42, +1.02, +4.64, +0.54, +3.86) | −1.24 (p 0.16; seeds −2.99, +0.13, −2.98, −0.06, −0.34) |
| `K_proto_band − K_base` | +2.02 (p 0.038) | −0.59 (p 0.34) |
| `K_proto_band − K_proto` | +0.22 (p 0.73) | −0.20 (p 0.83) |

## Criteria (fixed before the runs)

| Criterion | Result | |
|---|---|---|
| Main: beats `K_fixconf` with p < 0.05 on ≥ 1 dataset, not more than 0.3 worse on the other | Pets +1.93 but p 0.12; Caltech −1.24 | **fail** |
| Caltech repair: honest harmed label-rounds ≤ 2x `K_fixconf` | 247 broken + 86 deleted = 333, against 380 for `K_fixconf` (it was 7,169 for `K_proto`) | pass |
| Pets gain survived: recall ≥ 85% and ≥ +1.0 over `K_fixconf` | recall noisy 85% / malicious 88%; +1.93 | pass |

**Verdict: `K_fixconf` stays the relabel mode.** The clean band worked exactly as intended: honest
clients are left alone again (1,234 of 1,275 honest records exempt on Caltech). But Caltech still
loses, so honest-client harm was not the whole story.

## Why Caltech still loses

The relabel accuracy on the suspects the clusters pick is worse than on the suspects the loss
filter picks:

| Caltech | relabelled | restored | broke a clean label |
|---|---|---|---|
| `K_fixconf` noisy / malicious | 16,530 / 10,966 | 85% / 86% | 4% / 4% |
| `K_proto_band` noisy / malicious | 17,899 / 8,876 | 81% / 74% | 9% / 13% |

A failing cluster also contains clean images: about 13-16% of its suspects are clean. On those, the
global model is sometimes confidently wrong (≥ 50%), so clean labels get broken. The loss filter's
suspects are the images the client itself cannot fit, where the teacher is more often right. On
Caltech `K_fixconf` already closes 87% of the gap, so those extra breaks outweigh the extra recall.
Two seeds (0 and 2) account for most of the loss.

## What goes into the thesis

The cluster check is a **dataset-dependent option**. Where the per-image filter leaves room (Pets:
80% → 97% of the gap to the all-clean oracle), it helps a lot. Where the filter is already strong
(Caltech: 87%), it costs about 1 point. The line stops here, as pre-registered: no more K variants,
and `K_fixconf` goes into gate M.

# Gate Q results: noise only, 7 honest + 3 careless, no attacker (2026-09-29)

Plan: `gate_q_plan.md`. Raw files are in `Q_/{pets,caltech}`. The ceiling is `K_restore` (10 clean clients, same seeds).

| | `Q_none` | `Q_filter` | `Q_fixconf` | ceiling |
|---|---|---|---|---|
| Pets | 80.47 | **86.97** · 88% | 86.87 · 86% | 87.88 |
| Caltech | 87.79 | 89.61 · 75% | **89.77** · 82% | 90.21 |

Paired: `Q_fixconf − Q_none` is +6.40 (p 0.001) on Pets and +1.99 (p 0.001) on Caltech.
`Q_fixconf − Q_filter` is −0.10 (p 0.87) on Pets and +0.16 (p 0.21) on Caltech, so the relabel adds
about 0 on noise alone. The distance to the ceiling is 1.01 (p 0.21) on Pets and 0.44 (p 0.017) on Caltech.

## Criteria

| Criterion | Pets | Caltech | |
|---|---|---|---|
| 1. `Q_fixconf` closes ≥ 80% of the gap | 86% | 82% | **pass** |
| 2. Honest clients' harmed label-rounds < 1% | **3.23%** (797 deleted + 844 relabelled wrongly, of 50,847) | 0.30% | **fail on Pets** |

- Against careless clients the method works: 82-86% of the damage is recovered, and on Pets it
  nearly reaches 10 clean clients.
- On Pets it also touches honest clients at 3.2%. Some honest clients sit outside the clean band.
  On Pets the gap between "clean" and "careless" disagreement is narrow: the breeds look alike,
  so an honest client also disagrees with the global model fairly often. Caltech keeps honest
  clients almost untouched (0.3%).
- The relabel adds nothing measurable on noise alone. Its value in gate K (Caltech +0.65) comes
  mostly from the attackers' images.
- What the two data-only attackers cost once the method runs (`Q_fixconf − K_fixconf`): +1.34 on Pets
  (p 0.051) and +0.30 on Caltech (p 0.087).
