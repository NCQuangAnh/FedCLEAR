# Gate P plan: recover the device attacker's clean 60% with prototype verification (written 2026-09-27, before any run)

## Why

Gate N showed that every down-weighting rule is capped at `N_excl` (the attacker left out). That cap
sits 3.4 (Pets) and 1.5 (DTD) points under `L_oracle60`, and the gap is the attacker's clean 60%.
The user's target: for the device attacker, the oracle is `L_oracle60`, and the method should reclaim
part of that gap. A server-side rule cannot separate clean from poison inside one prompt update, so
gate P changes the protocol.

## Method (`flip/flcore/proto.py`, `ServerBase.proto_verify`)

1. **Send.** Every client also sends, for each label it holds, up to 3 k-means centroids of its CLIP
   image features (computed from its current training set, after its own filter), with each
   cluster's mass. Genuine images of a label and images relabelled into it fall into different
   clusters.
2. **Check.** A centroid passes if the round's global model OR CLIP's zero-shot template reads it
   as its own label (top-1). The zero-shot reader was added after the CPU smoke and before any GPU
   run: CoOp starts from a random context, so the global prompt alone would fail honest clients
   wholesale in the first rounds. The check is per (label, cluster), so 1, 2 or 3 target classes
   and random flips are judged alike.
3. **Rebuild.** From the passing centroids, the server computes the update the client should have
   sent: one gradient step of the mass-weighted cross-entropy at the global prompt, scaled to the
   round's median update norm.
4. **Replace.** A client is flagged if its verified mass share is < 0.8, or if the cosine between its
   sent and rebuilt update is more than 2 robust sds below the round's median. A flagged client's
   update is replaced by its rebuilt one. That is not a punishment: the rebuilt update is its own
   verified data.

The 2x-median norm clip (`L_clip`) stays on in every arm. The thresholds (0.8, 2 sd, K = 3, one step)
are fixed here and not tuned.

Device attacker variants: `none` sends honest prototypes of the data it trains on. `hide` sends
prototypes of its clean images only while still sending the poisoned update, so only the
sent-vs-rebuilt mismatch can catch it.

## Arms (`MODE = "gate_l_device"`, 5 seeds, Pets and Caltech first; DTD optional)

| Arm | Flags on top of the gate L base |
|---|---|
| `P_log` | `--norm_clip 2.0 --proto log` (records only; must equal `L_clip`) |
| `P_rec` | `--norm_clip 2.0 --proto replace` |
| `P_rec_hide` | `--norm_clip 2.0 --proto replace --proto_lie hide` |

## Criteria, fixed now

**Check quality (from `P_log`, per centroid, ground truth = purity):**
- C1: centroids of attackers that are mostly relabelled images (purity < 0.5) fail the check in
  ≥ 80% of cases, on Pets and on Caltech.
- C2: clean centroids (purity ≥ 0.9) of any role pass in ≥ 90% of cases.
- C3: honest clients are flagged in ≤ 10% of rounds, and attackers in ≥ 60% of rounds after round 10.

**Outcome (`P_rec`), with `L_oracle60` as the ceiling, as the user asked:**
- **Main.** `P_rec − N_excl` ≥ +1.0 on at least one of Pets and Caltech. Only then has any of the
  clean 60% been reclaimed; `N_excl` is already matched by `L_clip_down`.
- **Beats the current best.** `P_rec > L_clip_down` with p < 0.05 on at least one of the two, and
  not more than 0.3 worse on the other.
- **Safety.** ASR not above `L_clip`'s, and target-class accuracy not down by more than 2.
- Salvage reported as (arm − `L_base`) / (`L_oracle60` − `L_base`).

**`P_rec_hide`.** It passes if it keeps ≥ 70% of `P_rec`'s gain over `L_clip`. If it keeps less, the
mismatch check is too weak against an attacker that hides its flipped images, and the thesis must
say so.

`P_log` must equal `L_clip` seed by seed (difference < 0.05), otherwise the logging changed the run.

## Amendment before any GPU run (2026-09-27)

`P_rec` logs the same per-centroid check as `P_log`, so C1-C3 are scored on `P_rec`'s logs, and `P_log`
is dropped to save GPU. Gate N already showed that a logging-only arm reproduces `L_clip` exactly.
The check itself does not depend on the replacement, only on the global model it reads with.

Sessions: Pets `[P_rec, P_rec_hide]` (~3 h), Caltech `[P_rec, P_rec_hide]` (~7.5 h), DTD optional.
Both CPU smokes ran end to end: `replace` with `hide`, and `replace` with the zero-shot reader.
