# Gate R results: the device attacker alone (8 honest + 2 device attackers; 2026-09-30)

Plan: `gate_r_plan.md`, written before the runs. Sessions: R1 Pets (4 arms, done), R2 Caltech
`[R_none, R_clip]` (done), R3 Caltech `[R_prec, R_oracle60]` (done 2026-10-01, rerun). The first R3 attempt ran with
`MODE` left at its default `gate_k_relabel` and reran `K_base / K_fix / K_fixconf` on Caltech (5 honest +
3 careless + 2 data-only attackers). It reproduced the stored gate K numbers to the digit (88.82 / 89.47 /
89.47), so it adds nothing new. Its zip is kept as `_zips/caltech-WRONG-MODE-gate_k_relabel.zip`.

## Accuracy (last10, 5 seeds)

| | `R_none` | `R_clip` | `R_prec` | `R_oracle60` |
|---|---|---|---|---|
| Pets | 83.38 | 85.45 | **87.20** | 87.65 |
| Caltech | 85.43 | 87.68 | **89.69** | 89.56 |

| Paired (n = 5) | Pets | Caltech |
|---|---|---|
| `R_clip − R_none` | +2.07 (p 0.001, 5/5 seeds) | +2.24 (p 0.003, 5/5) |
| `R_prec − R_none` | +3.82 (p 0.014, 5/5) | +4.26 (p 0.002, 5/5) |
| `R_prec − R_clip` | +1.75 (p 0.081, 4/5) | +2.01 (p 0.002, 5/5) |
| `R_oracle60 − R_prec` | +0.45 (p 0.34) | −0.13 (p 0.62) |

## Criteria

| Criterion | Pets | Caltech |
|---|---|---|
| 1. `R_prec` salvage ≥ 80% of `R_none` → `R_oracle60` | **89%** pass | **103%** pass |
| 2. `R_clip > R_none` | +2.07 pass | +2.24 pass |
| 3a. honest clients flagged/replaced ≤ 10% of rounds | 6.3% pass (9.8% in rounds 0-9, 5.4% after) | 2.6% pass |
| 3b. ASR `R_prec` ≤ `R_clip` | 0.18% vs 0.73% pass | 0.10% vs 1.04% pass |

**Gate R passes every pre-registered criterion on both datasets.** Attackers are flagged by the prototype check in 100% (Pets) / 96.9% (Caltech) of rounds.

Last-10 ASR / accuracy on the attackers' target classes: Pets `R_none` 1.59% / 77.8%, `R_clip` 0.73% / 83.8%,
`R_prec` 0.18% / 89.0%, `R_oracle60` 0.19% / 88.4%. Caltech `R_none` 2.49% / 90.8%, `R_clip` 1.04% / 90.6%, `R_prec` 0.10% / 87.1%, `R_oracle60` 0.06% / 85.6%. On Caltech the target-class accuracy falls as the attack is removed, and the oracle falls furthest. The most likely reason, not tested: the flipped images added extra, partly correct, examples of the target class.

## Reported, not judged

- **What the two attackers alone cost** (`R_oracle60 − R_none`): Pets 4.27. With the noise (gate L,
  `L_oracle60 − L_base`): 6.64. Note that `R_none` has no client filter while `L_base` has one.
- **What the 3 careless clients take from each method:** `R_clip − L_clip` = +3.39 on Pets (p 0.013), +0.52
  on Caltech (p 0.30). `R_prec − P_rec` = −0.21 on Pets (p 0.73), +0.62 on Caltech (p 0.045): once the prototype check runs,
  the 3 careless clients cost nothing measurable on Pets and 0.6 on Caltech. That fits the gate P note that `P_rec`
  also cleans the careless clients.
- `K_restore − R_oracle60` (10 clean clients vs attackers on their clean 60%): Pets 87.88 − 87.65 = +0.23.
  Caltech 90.21 − 89.56 = +0.65. The attackers' lost 40% of data is worth little.

## Next

Gate R is complete.
