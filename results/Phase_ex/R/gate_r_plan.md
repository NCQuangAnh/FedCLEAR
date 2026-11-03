# Gate R plan: the device attacker alone (written 2026-09-29, before any run)

## Why

Gate L and gate P always mixed the device attacker with 3 careless clients, so part of what the
server defences won or lost may come from the noise, not from the attacker. Gate R takes the noise
out: 10 clients, **8 honest + 2 device attackers** (the attacker owns its machine: refuses the probe,
never filters, lies about its numbers, flips 40% of its labels to its own target class). No careless
client (`--noisy_client_frac 0`). Malicious clients are drawn before careless ones
(`flcore/attack.py:assign_roles`), so each seed has the same two attackers as in gate L, and runs
pair seed by seed with gate L.

## Arms (`MODE = "gate_r_device"`, 5 seeds, Pets and Caltech)

| Arm | What |
|---|---|
| `R_none` | no defence: what the two attackers alone cost |
| `R_clip` | client filter + 2x-median norm clip (the `L_clip` method) |
| `R_prec` | + prototype check and rebuild (the `P_rec` method, current best) |
| `R_oracle60` | ceiling: the attackers train on their clean 60% only (as `L_oracle60`) |
| `R_base` | optional: client filter only, no server defence |

## Criteria, fixed now

1. **Main.** `R_prec` closes at least 80% of the gap from `R_none` to `R_oracle60`
   (salvage = (`R_prec` − `R_none`) / (`R_oracle60` − `R_none`)), on both Pets and Caltech.
2. **The clip still helps without noise.** `R_clip > R_none` on both datasets (mean over 5 seeds).
3. **Safety.**
   - Honest clients are flagged or replaced by the prototype check in ≤ 10% of rounds.
   - Last-10 ASR of `R_prec` is not above `R_clip`'s.
4. **Reported, not judged:**
   - What the attackers alone cost: `R_oracle60 − R_none`, next to the gate L cost with noise
     (`L_oracle60 − L_base`).
   - `R_prec − P_rec` and `R_clip − L_clip`: how much the 3 careless clients took from each method.
   - `K_restore − R_oracle60` (10 fully clean clients vs the 60%-clean ceiling): what the
     attackers' 40% of lost data is worth.
   - The prototype pass rates by role and cluster purity.

If criterion 1 fails, the thesis must state that `P_rec` reaches the oracle only when noise is
present, and the logs must show why (rebuilds of honest clients, or attackers not caught).
