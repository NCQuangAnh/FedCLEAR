# Gate R3 plan: attackers aimed at the single prototype send (written 2026-10-02, before any run)

## Why

`R_prec_once` (gate R2) sends prototypes once, in round 0, and the server keeps them for the
whole run. In R2 the device attacker sent honest prototypes of what it trains on, including its
40% relabelled images, so the round-0 check caught it. A smarter attacker knows the server only
looks once. It can make that one send look clean and attack afterwards.

## Attackers (`--proto_lie`, device attacker, 8 honest + 2 attackers, seeds 0-4)

| Arm | What the attacker does |
|---|---|
| `R_prec_once` (stored reference) | sends prototypes of everything it trains on, relabelled images included |
| `R_prec_once_hide` | sends prototypes of its clean images only; trains on everything from round 0 |
| `R_prec_once_turncoat` | sends prototypes of its clean images only, **and** trains only on its clean images in round 0, so its round-0 update also looks honest. From round 1 on it trains on everything (`--turncoat_rounds 1`) |

With `once`, the stored prototypes of both new attackers are clean, so the verified-share test
never fires. The only thing left that can catch them is the mismatch test: the cosine between
the update a client sends and the update its stored prototypes imply, every round.

## Criteria, fixed now

For each of `hide` and `turncoat`, on Pets and on Caltech:

1. **Main.** It keeps at least 70% of `R_prec_once`'s gain over `R_clip` (the same bar gate P set
   for `P_rec_hide`).
2. **Safety.** Honest clients are flagged in ≤ 10% of rounds, and its last-10 ASR is not above
   `R_clip`'s.
3. **Reported, not judged:** how often the attackers are flagged per round (round 0 and rounds
   1-49 separately), and `turncoat − hide`.

If criterion 1 fails, sending prototypes once is not safe against an attacker who knows the
protocol, and the thesis must recommend sending at every filter refresh instead (R2 showed that
costs nothing in accuracy) and say why.
