# Gate Q plan: the client-side method on noise alone (written 2026-09-28, before any run)

## Why

Every gate so far has mixed careless clients with attackers, so it has never been measured cleanly
how well the filter and the relabel repair careless clients on their own. Gate Q takes the attacker
out: 10 clients, **7 honest + 3 careless** (40% random flips), no malicious client. Seeds are the same
as every earlier gate, so runs pair with the stored references.

## Arms (`MODE = "gate_q_noise"`, 5 seeds, Pets and Caltech; DTD optional)

| Arm | What |
|---|---|
| `Q_none` | no defence: what the noise alone costs |
| `Q_filter` | the filter only (delete / down-weight, server-chosen), the `K_base` method |
| `Q_fixconf` | filter + relabel, the `K_fixconf` method (the current method) |
| ceiling | `K_restore`: every label correct, 10 clean clients (stored reference, same seeds). An optional arm `Q_clean` (noise off) gives the same ceiling run in exactly this configuration |

## Criteria, fixed now

1. **The method does its job on noise.** `Q_fixconf` closes at least 80% of the gap from `Q_none` to
   the all-clean ceiling, on both Pets and Caltech.
2. **Honest clients are left alone.** The 7 honest clients' harmed label-rounds (deleted, or
   relabelled to a wrong class) stay below 1% of their label-rounds.
3. **Reported, not judged:**
   - the share of damaged labels caught, relabels fixed and broken;
   - `Q_fixconf − Q_filter` (what the relabel adds on noise alone);
   - the K gate (with attackers) against Q (without), which gives what the two data-only
     attackers cost on top of the noise once the method runs.

If criterion 1 fails, the thesis must state that the client-side method leaves a real share of the
noise damage in place even without attackers, and the audit says where: missed suspects,
wrong relabels, or deleted clean images.
