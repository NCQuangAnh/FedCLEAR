# Gate R2 results: fewer prototype sends (2026-10-01)

Plan: `gate_r2_plan.md`, written before the runs. Setting: gate R (8 honest + 2 device attackers),
seeds 0-4. Sessions R4 Pets and R5 Caltech, `[R_prec_once, R_prec_refresh]`. Zips are in
`_zips/*-R2-once-refresh.zip`.

| Last10 | `R_none` | `R_prec` (51 sends) | `R_prec_refresh` (11 sends) | `R_prec_once` (1 send) | `R_oracle60` |
|---|---|---|---|---|---|
| Pets | 83.38 | 87.20 | 87.20 | 87.14 | 87.65 |
| Caltech | 85.43 | 89.69 | 89.69 | 89.70 | 89.56 |

The logged `fresh` field confirms the sends: 51.0 / 11.0 / 1.0 per client per run.

## Criteria

| Criterion | `once` Pets | `once` Caltech | `refresh` Pets | `refresh` Caltech |
|---|---|---|---|---|
| 1. salvage ≥ 80% | 88% pass | 103% pass | 90% pass | 103% pass |
| 2. at most 0.5 below `R_prec` | −0.06 (p 0.61) pass | +0.01 (p 0.91) pass | 0.00 pass | 0.00 pass |
| 3a. honest flagged ≤ 10% of rounds | 6.9% pass | 4.3% pass | 6.2% pass | 2.6% pass |
| 3b. ASR ≤ `R_clip` | 0.17% vs 0.73% pass | 0.10% vs 1.04% pass | 0.18% pass | 0.10% pass |

**Both arms pass every criterion on both datasets.** Attackers are flagged in 100% (Pets) and
95.5% (`once`, Caltech) of rounds.

## Reading

- **`refresh` equals `R_prec` seed by seed, to the digit.** That follows from the design, and it
  also checks the code. A client's prototypes depend only on its image features (fixed, because
  CLIP is frozen) and on its labels and weights, and those change only when it re-runs its filter.
  Between refreshes the stored prototypes are identical to fresh ones. So the every-round protocol
  was sending the same prototypes 5 times out of 6. Sending only at refresh costs nothing.
- **`once` (one send per run) loses nothing measurable**: −0.06 on Pets and +0.01 on Caltech.
  Honest clients are flagged slightly more often (Pets 6.2% → 6.9%, Caltech 2.6% → 4.3%), because
  their stored prototypes no longer follow their own filtering. That is still within the 10% limit.
- The privacy exposure drops 51× with `once` and 4.6× with `refresh`, at no cost here.

## Limits (not tested by this gate)

- No careless clients here. With careless clients, honest filtering changes a client's data more,
  and `once` may lose more than here. Gate L/P (with noise) has not been run with `once`.
- An attacker that knows the server keeps its round-0 prototypes could behave honestly at round 0
  and attack later. The sent-vs-rebuilt mismatch check still runs every round, which is what
  caught the `hide` attacker in gate P, but this adaptive attacker has not been run.
