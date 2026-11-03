# Gate R4 results: the attacker that fabricates its prototypes (2026-10-03)

Plan: `gate_r4_plan.md` (copied here from `Phase_ex/R/`), written before the runs. Setting: gate R
(8 honest + 2 device attackers), seeds 0-4. The first `R_prec_once_forge` run was invalid (deleted 2026-10-03 to save space); the rerun (R4b) is
below. References (`R_none`, `R_clip`, `R_prec`,
`R_prec_once`, `R_oracle60`) are the stored gate R / R2 runs in `Phase_ex/R/`. The run zips were
deleted after extraction, as the user asked.

## `R_prec_forge`: forging every round (valid)

| Last10 | `R_clip` | `R_prec` | `R_prec_forge` |
|---|---|---|---|
| Pets | 85.45 | 87.20 | **85.45** |
| Caltech | 87.68 | 89.69 | **88.39** |

| Criterion | Pets | Caltech |
|---|---|---|
| 1. keeps ≥ 70% of `R_prec`'s gain over `R_clip` | **0%, fail** | **36%, fail** |
| 2a. honest flagged ≤ 10% | **15.0%, fail** | 6.5% pass |
| 2b. ASR ≤ `R_clip` | **0.85% vs 0.73%, fail** | 0.69% vs 1.04% pass |

- `R_prec_forge − R_prec`: −1.75 (p 0.18) on Pets, −1.30 (p 0.005, 0/5 seeds) on Caltech.
  `R_prec_forge − R_clip`: +0.01 on Pets, +0.71 (p 0.08) on Caltech.
- Forging works as designed: 100% of forged centroids pass the label check, and the cosine
  between the server's rebuild and the attacker's update rises from 0.75 to 0.87 (Pets) and from
  0.60 to 0.86 (Caltech), above most honest clients. After round 0 the attackers are flagged in
  only 1.6% (Pets) and 1.2% (Caltech) of rounds, against about 100% for the naive attacker.
- **Reading:** an attacker that knows the protocol and fabricates its prototypes every round
  defeats the prototype check. What is left is the norm clip, and accuracy falls back to the
  `R_clip` level (the floor written in the plan holds). On Pets the honest-flag rate also rises to
  15%: the forged attackers sit at the top of the cosine distribution and push honest clients
  down in the robust z-score.

## `R_prec_once_forge`: forging the single send (rerun R4b, 2026-10-03)

The first run was invalid. It forged against the attacker's round-0 update, and on Pets every
client's round-0 update is exactly zero: the mixed-precision (AMP) gradient scaler skips the first
optimiser steps while it calibrates, and a Pets client has about 2 steps per round. That run was
deleted to save space. The rerun forges against the direction the attacker's poisoned
data pulls in (minus the gradient of its real centroids, relabelled ones included, at the round-0
prompt). All 10 round-0 attacker sends per dataset were forged against that target.

| Last10 | `R_clip` | `R_prec_once` (naive) | **`R_prec_once_forge`** | `R_prec_forge` (every round) |
|---|---|---|---|---|
| Pets | 85.45 | 87.14 | **87.33** | 85.45 |
| Caltech | 87.68 | 89.70 | **88.95** | 88.39 |

| Criterion | Pets | Caltech |
|---|---|---|
| 1. keeps ≥ 70% of `R_prec_once`'s gain over `R_clip` | **111% pass** | **63% fail** |
| 2a. honest flagged ≤ 10% | 6.8% pass | 4.9% pass |
| 2b. ASR ≤ `R_clip` | 0.31% vs 0.73% pass | 0.07% vs 1.04% pass |

- `once_forge − R_prec_once`: +0.19 (p 0.54) on Pets, −0.74 (p 0.18, 1/5 seeds) on Caltech.
  `once_forge − R_clip`: +1.88 (p 0.046) on Pets, +1.27 (p 0.074) on Caltech.
- **Sending once is clearly more robust than sending every round** against this attacker: +1.87
  over `R_prec_forge` on Pets (p 0.09) and +0.56 on Caltech (p 0.41).
- How it holds. At round 0 the attacker could not make all its centroids pass while keeping the
  poisoned direction. 84% (Pets) and 93% (Caltech) of the forged centroids pass, but by mass only
  0.64 / 0.62 of its data does, under the 0.8 bar. The large relabelled clusters are the hard ones.
  Because the server keeps those centroids, the attacker is flagged in about 91-93% of all rounds,
  and its update is replaced by the rebuild from them. The forged centroids still carry part of
  the poison, which is what costs Caltech 0.74.
- **Caveat.** This attacker uses a fixed budget: 20 Adam steps from its real centroids, margin
  0.02. A stronger optimiser at round 0 (more steps, or starting from centroids of the target
  class) might pass the share test too. An attacker that does gets the every-round outcome only
  if its stored centroids also keep matching its later updates. Not tested.

## Overall reading

| Attacker vs method | `R_prec` (every round) | `R_prec_once` |
|---|---|---|
| naive / hide / turncoat | pass | pass |
| forge | fail on both (back to the `R_clip` floor) | pass on Pets, fail on Caltech (63%) |

The prototype check is not robust to a white-box attacker that fabricates prototypes every round.
Committing to the prototypes once, at round 0, makes that attack much weaker but does not fully
stop it on Caltech. In every case the norm clip keeps accuracy at or above the `R_clip` level.
