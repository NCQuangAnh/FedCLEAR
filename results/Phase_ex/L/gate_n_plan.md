# Gate N plan: cross-client validation against the device attacker (written 2026-09-26, before any run)

## Why

`L_clip` recovers 18% / 30% / 62% of the device attacker's damage (DTD / Pets / Caltech). The offline
analysis in `L_results.md` shows that the label-free server signals are close to used up. So the
missing information is how an update behaves on real images, and only the clients have images.

Priority, agreed with the user: **Caltech101 and OxfordPets**, where the global model is good enough
for validation to be meaningful. DTD is optional.

## Method (`flip/flcore/xval.py`, `ServerBase.cross_validate`)

Every round, after the 2x-median norm clip, each client scores every other client's update on its
own current training set (after its own filter, with its relabels and soft weights). Two scores
per candidate, each the median over validators:
- `loo` = loss(aggregate) − loss(aggregate without the candidate)
- `self` = loss(candidate's prompt) − loss(round's global prompt)

Positive means the update hurts the validators. A device attacker asked to validate lies: it
reports that every update hurts it ("smear").

In `--xval weight` mode:
- evidence = EMA 0.8 of the round's robust z-score (median/MAD across candidates);
- weight = 1 up to z = 2, then 2 / evidence;
- re-decided every round, and nobody is removed.

The EMA 0.8 and z 2 values are the ones the refusal detector and TDR already used. They are not
tuned.

## Step 1: measure only (this plan)

| Arm | Flags on top of the gate L base | What it answers |
|---|---|---|
| `N_log` | `--norm_clip 2.0 --xval log` | Does the validation score single out the attacker? Must reproduce `L_clip` |
| `N_excl` | `--norm_clip 2.0 --oracle_mal_weight 0` | ORACLE: attackers left out from round 0. The ceiling of any down-weighting rule |

Sessions (5 seeds): Caltech `[N_log, N_excl]` ~7 h; Pets `[N_log, N_excl]` ~3 h; DTD optional ~3 h.

## Criteria, fixed now

- **D1, the signal.** For `loo` or `self`: evidence AUC (attackers vs the other 8 clients) ≥ 0.90 by
  round 10 on both Caltech and Pets. Also, the simulated weights must stay at ≥ 0.95 on average for
  honest clients and for noisy clients separately.
- **D2, the headroom.** `N_excl − L_clip` ≥ 1.0 point on at least one of Caltech and Pets. Below
  that on both, down-weighting cannot buy enough, and this line stops whatever D1 says.
- **D3, the sanity check.** `N_log` equals `L_clip` seed by seed (difference < 0.05). If not, the
  logging changed the run and D1 is not trusted.
- **Score choice for step 2.** Whichever of `loo` / `self` passes D1 with the higher round-10 AUC
  averaged over the two datasets. On a tie, `loo`.

## Step 2 (only if D1, D2 and D3 all pass)

Arm `N_xval`: `--norm_clip 2.0 --xval weight --xval_score <chosen>`, 5 seeds, Caltech and Pets.

Success: `N_xval` beats `L_clip` with p < 0.05 on at least one of the two datasets and is not
more than 0.3 worse on the other. Honest and noisy mean weights must stay ≥ 0.95. Report salvage
against `L_oracle60` and against `N_excl`.

## CPU checks before the GPU runs (2026-09-26)

- `--norm_clip 2.0` alone reproduces `L_clip` (`--tdr true --tdr_z 1e9`) exactly over 4 rounds on the
  synthetic set: the same train loss and the same per-client clip scale every round.
- `N_excl` (oracle weight 0) runs to the end.
- `--xval weight` runs to the end. In round 0 the attacker has the highest `loo` score (+0.030,
  weight 0.03).
- Known risk, to be checked on the real logs under D1: with 4 clients the MAD is tiny, and a noisy
  client got z 8.3 (weight 0.24) in round 0. With 10 clients the MAD should be steadier. If the step-1
  logs show honest or noisy weights below 0.95, the weight rule must be revised and pre-registered
  again before step 2.
