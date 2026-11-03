# Gate R2 plan: fewer prototype sends (written 2026-10-01, before any run)

## Why

`R_prec` passes gate R, but every client sends its prototypes (about 20 on Pets and 53 on Caltech,
each a 1,024-number CLIP feature centroid) in **every** round: 51 sends per client per run. Each
send leaks something about the client's images. The image features never change (CLIP is frozen).
Only the labels and weights change, when the client re-runs its filter every 5 rounds. So most
sends repeat what the server already has.

## Method (`--proto_every`, `ServerBase.proto_verify`)

The server keeps the last prototypes each client sent. The check, the flag and the rebuild still
run every round, against the current global prompt, using those stored prototypes.

| Arm | Sends | Flags on top of `R_prec` |
|---|---|---|
| `R_prec` (reference) | every round, 51 per run | `--proto_every round` (default) |
| `R_prec_refresh` | only when the client re-runs its filter (rounds 0, 5, …, 50): 11 per run | `--proto_every refresh` |
| `R_prec_once` | only in round 0: 1 per run | `--proto_every once` |

Setting: gate R (8 honest + 2 device attackers), same seeds 0-4, Pets and Caltech. `R_none`,
`R_clip`, `R_prec` and `R_oracle60` are stored references and are not rerun.

## Criteria, fixed now

For each of `R_prec_once` and `R_prec_refresh`, on Pets and on Caltech:

1. **Main.** It keeps at least 80% salvage of the gap `R_none` → `R_oracle60` (the gate R criterion).
2. **Not worse than every-round.** Its mean is at most 0.5 below `R_prec` (paired, 5 seeds).
3. **Safety.** Honest clients are flagged or replaced in ≤ 10% of rounds, and its last-10 ASR is not
   above `R_clip`'s.
4. **Reported, not judged:** the sends per client per run (logged `fresh` field; expected 1 / 11),
   and the paired differences `once − refresh` and each arm − `R_prec`.

Reading: if `once` passes, one send per run is enough and the privacy cost drops 51x. If only
`refresh` passes, prototypes must follow the filter's relabels. If neither passes, every-round
sending is needed, and the thesis must say so.

Expected risk for `once`, written before the run: in round 0 no client has filtered yet and the
global prompt is random. The check then leans on CLIP's zero-shot reader alone. That was enough to
catch the attackers in gate P, so `once` is expected to pass on attacker detection. It may lose on
honest clients whose stored prototypes no longer match what they train on after filtering.
