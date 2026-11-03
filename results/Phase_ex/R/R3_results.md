# Gate R3 results: attackers aimed at the single prototype send (2026-10-02)

Plan: `gate_r3_plan.md`, written before the runs. Setting: gate R (8 honest + 2 device attackers),
`--proto_every once`, seeds 0-4. Zips: `_zips/*-R3-hide-turncoat.zip`.

| Last10 | `R_clip` | `R_prec_once` (naive attacker) | `_hide` | `_turncoat` | `R_oracle60` |
|---|---|---|---|---|---|
| Pets | 85.45 | 87.14 | 87.25 | 87.51 | 87.65 |
| Caltech | 87.68 | 89.70 | 89.41 | 89.60 | 89.56 |

| Paired (n = 5) | Pets | Caltech |
|---|---|---|
| `hide − R_prec_once` | +0.11 (p 0.82) | −0.28 (p 0.20) |
| `turncoat − R_prec_once` | +0.38 (p 0.20) | −0.09 (p 0.68) |
| `hide − R_clip` | +1.80 (p 0.024, 5/5) | +1.74 (p 0.002, 5/5) |
| `turncoat − R_clip` | +2.06 (p 0.050, 4/5) | +1.92 (p 0.004, 5/5) |
| `turncoat − hide` | +0.27 (p 0.54) | +0.19 (p 0.21) |

## Criteria

| Criterion | `hide` Pets | `hide` Caltech | `turncoat` Pets | `turncoat` Caltech |
|---|---|---|---|---|
| 1. keeps ≥ 70% of `R_prec_once`'s gain over `R_clip` | 107% pass | 86% pass | 122% pass | 95% pass |
| 2a. honest flagged ≤ 10% of rounds | 7.6% pass | 4.4% pass | 5.5% pass | 3.4% pass |
| 2b. ASR ≤ `R_clip` | 0.30% vs 0.73% pass | 0.10% vs 1.04% pass | 0.24% vs 0.73% pass | 0.13% vs 1.04% pass |

**Both attackers pass every criterion on both datasets.** Sending prototypes once holds up
against an attacker that knows the protocol and makes its one send look clean.

## How they are caught (reported, not judged)

| Attackers flagged (% of rounds) | round 0 | rounds 1-50 |
|---|---|---|
| `R_prec_once`, Pets / Caltech | 100 / 100 | 100 / 95 |
| `hide`, Pets / Caltech | 10 / 40 | 64 / 71 |
| `turncoat`, Pets / Caltech | 10 / 50 | 68 / 65 |

- With clean prototypes stored, the verified share of the attackers rises from 0.54 to about 0.90,
  above the 0.8 bar, so that test no longer fires. Every catch comes from the mismatch test (the
  attackers' mean z after round 0 is −2.9 to −3.3, against the −2 bar).
- The attackers are caught less often (64-71% of rounds instead of 95-100%), but accuracy does not
  fall. When an attacker is flagged, its update is rebuilt from the stored prototypes, and those
  are exactly its clean images, so the rebuild is the 60%-clean oracle's update. In the rounds it is
  not flagged, its update is still capped by the norm clip.
- `turncoat` is not worse than `hide`: behaving honestly in round 0 removes the round-0 damage and
  gains nothing later.

## Limits (not tested)

- An attacker that also shapes its update to stay above the z bar (weaker poisoning), or that
  fabricates prototypes the global model reads as the label while carrying the poisoned direction.
- No careless clients in this gate; `once` with noise is still untested.
