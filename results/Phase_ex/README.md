# Phase_ex — extended experiments

## Layout

```
Phase_ex/
  README.md                this file
  L/                       gate L: the device-level attacker
    L_results.md           all results, the pre-registered decisions, and the verdicts
    dtd/                   one folder per dataset:
    oxford_pets/             logs/<dataset>_<arm>.txt, runs/<dataset>_<arm>/, run_index.json
    caltech101/              (run_index.json records which Kaggle session each run came from)
      _failed/             the first L_tdr / L_tdr_early attempts that crashed (CUDA OOM)
    _zips/<session>/       the original Kaggle zips, kept for reproducibility
```

Plan and criteria: `results/Phase_bonus/gate_l_plan.md`. Results and verdicts: `L/L_results.md`.

## Arms (every run: 5 seeds 0-4, last10 on the test set)

| Arm | What the server does against the device attacker |
|---|---|
| `L_base` | nothing beyond the client-side method |
| `L_down` | down-weights clients the refusal detector flags, in proportion to the evidence |
| `L_tdr` | cuts the "target direction" of flagged clients + 2x-median norm clip for everyone |
| `L_tdr_early` | `L_tdr`, but the server knows the attackers from round 0 (oracle on who) |
| `L_tdr_conc` / `_true` / `_rand` | `L_tdr` with the target from probe mass / the true target (oracle) / a random class (control) |
| `L_clip` | only the 2x-median norm clip for everyone; no cut, and flags have no effect |
| `L_clip_down` | `L_clip` + `L_down` |
| `L_oracle60` | ceiling: the attackers train on their clean 60% only |

## Sessions

| Session | Runs | Zip |
|---|---|---|
| 6c / 6x / 6y | first gate L sessions: `L_base`, `L_down`, `L_tdr`, `L_tdr_early`, `L_oracle60` | not kept |
| 7a / 7b | TDR diagnosis on DTD / Pets | `_zips/7a-…`, `_zips/7b-…` |
| 7c | Caltech `L_tdr`, `L_tdr_early` rerun after the OOM fix | `_zips/7c-…` |
| 8a / 8b | Caltech `L_clip`, `L_clip_down`; DTD and Pets `L_clip_down` | `_zips/8a-…`, `_zips/8b-…` |
