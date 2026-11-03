# Gate R4 plan: an attacker that fabricates its prototypes (written 2026-10-02, before any run)

## Why

Gate R3 showed that hiding the relabelled clusters is not enough: the mismatch test (sent update
vs the rebuild its prototypes imply) still catches the attacker. The strongest attacker the
protocol allows fabricates prototypes that pass **both** tests. It owns its machine, so the
server can never check that a centroid comes from real images.

## Attacker (`--proto_lie forge`, `flcore/forge.py`)

Each time it sends prototypes, the attacker starts from its real centroids (relabelled clusters
included) and moves them by gradient steps (20 Adam steps) to:

- make every centroid read as its label by the global prompt or the zero-shot template, with a
  margin of 0.02 in cosine; and
- make the rebuild the server will compute from them point along its own poisoned update
  (maximise their cosine).

It uses only its own update, the global prompt it was sent, the public CLIP model and the public
server rule (white-box on the protocol, blind to other clients). Masses are its real ones.

| Arm | Sends | Reference |
|---|---|---|
| `R_prec_forge` | every round: forges against each round's update | `R_prec` |
| `R_prec_once_forge` | once, round 0: must commit before its later updates exist | `R_prec_once` |

Setting: gate R (8 honest + 2 device attackers), seeds 0-4, Pets and Caltech.

## Criteria, fixed now

For each arm, on Pets and on Caltech:

1. **Main.** It keeps at least 70% of its reference's gain over `R_clip`.
2. **Safety.** Honest clients flagged in ≤ 10% of rounds; last-10 ASR not above `R_clip`'s.
3. **Reported, not judged:** forged centroids that pass the check, cosine before and after forging,
   how often the attackers are flagged, and `R_prec_forge − R_clip`.

**Reading.** Even an attacker that evades both tests still has its update capped by the 2x-median
norm clip, so the floor is about `R_clip`. If criterion 1 fails for `R_prec_forge`, the thesis
must state that a white-box attacker who fabricates prototypes defeats the prototype check,
leaving the clip as the only defence against it. If `R_prec_once_forge` passes while
`R_prec_forge` fails, sending once has a security benefit: it forces the attacker to commit to its
prototypes before it knows its later updates.
