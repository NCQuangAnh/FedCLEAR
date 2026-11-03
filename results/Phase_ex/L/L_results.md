# Gate L results: the device-level attacker (2026-09-25)

Plan and criteria: `results/Phase_bonus/gate_l_plan.md` (written before running). Five seeds (0-4),
last10 on the test set. The folders are split by dataset (`dtd/`, `oxford_pets/`, `caltech101/`),
and each `run_index.json` records which Kaggle session a run came from. The original zips are in
`_zips/`.

**Caltech101 `L_tdr` and `L_tdr_early` crashed** at the first round (CUDA OOM). The batched
gradient for 100 classes asked for 5.9 GB. The fallback loop then hit "backward through the graph a
second time", because the failed call had already freed the graph. Fixed in `tdr_directions`: the
gradient is now computed in chunks of 16 classes and keeps the graph between chunks. On a toy case
the result matches the per-class loop to 1e-9. Caltech needs a rerun of those two arms.

## Accuracy

| | `L_base` | `L_down` | `L_tdr` | `L_tdr_early` | `L_oracle60` (ceiling) |
|---|---|---|---|---|---|
| DTD | 49.26 | 49.61 | 50.16 | 49.79 | 52.18 |
| OxfordPets | 80.06 | 81.50 | 82.25 | 82.61 | 86.70 |
| Caltech101 | 84.41 | 85.62 | crashed | crashed | 88.84 |

### What the device attacker costs the current method (`L_base` − old `H_auto`, same seeds)

| DTD | OxfordPets | Caltech101 |
|---|---|---|
| −1.51 (p 0.046) | **−5.09** (p 0.012) | **−4.31** (p 0.002) |

Predicted: −1 to −2, −2 to −4, −1 to −2.5. DTD matched. Pets and Caltech lost more than predicted.
An attacker that owns its machine is a real limit of the client-side method.

### Paired against `L_base`

| | DTD | OxfordPets | Caltech101 |
|---|---|---|---|
| `L_down` | +0.36 (p 0.26) | +1.44 (p 0.051) | +1.21 (p 0.31) |
| `L_tdr` | +0.90 (p 0.071) | **+2.19 (p 0.030)** | — |
| `L_tdr_early` | **+0.53 (p 0.037)** | **+2.55 (p 0.006)** | — |
| `L_oracle60` | +2.92 (p 0.08) | +6.64 (p 0.004) | +4.43 (p 0.004) |
| salvage `L_down` / `L_tdr` / `L_tdr_early` | 12% / 31% / 18% | 22% / 33% / 38% | 27% / — / — |

`L_down − L_tdr`: −0.55 on DTD and −0.75 on Pets, neither significant.

### ASR (last 10 rounds) and accuracy on the real target class

| | DTD ASR | Pets ASR | Caltech ASR | target-class accuracy |
|---|---|---|---|---|
| `L_base` | 4.48% | 2.93% | 2.90% | 38.6 / 74.1 / 83.3 |
| `L_down` | 4.03% | 2.20% | 2.17% | 38.4 / 78.6 / 83.0 |
| `L_tdr` | 4.41% | 1.92% | — | 38.6 / 78.9 / — |
| `L_tdr_early` | 4.64% | 1.64% | — | 40.2 / 77.9 / — |
| `L_oracle60` | 1.20% | 0.25% | 0.07% | 40.7 / 90.5 / 90.0 |

ASR falls on Pets and Caltech. On DTD it barely moves, and for `L_tdr_early` it rises slightly.
Target-class accuracy never drops by more than 2 points.

## The refusal detector

Flag decisions, summed over seeds: DTD 41-49, all malicious. Pets 38-47 malicious plus 1-4 noisy.
Caltech 34 malicious plus 3 noisy. The first flag came at round 10-40, and in one seed per dataset
the detector never fired.

## The finding that changes how TDR is described

TDR guesses the attacker's target class **almost never correctly**:

| | cuts on malicious | target guessed right | chance level |
|---|---|---|---|
| DTD `L_tdr` / `L_tdr_early` | 112 / 332 | **0 / 0** | 2.1% |
| Pets `L_tdr` / `L_tdr_early` | 189 / 453 | 17 (9%) / 35 (8%) | 2.7% |

The guess also changes from round to round for the same attacker. So the gain of `L_tdr` does
**not** come from removing the attacker's pull towards its target. It comes from removing *some*
above-median component of a flagged client's update, plus the norm clip: in practice a targeted
damping of the flagged client. The thesis must describe it that way. The label "target-direction
residualisation" is not supported by the data.

False cuts on non-malicious clients: Pets 5 of 194 (2.6%) and 16 of 469 (3.4%), all on noisy
clients through a false refusal flag. DTD had 0. Both are far under the 20% disqualification line.

## Verdict against the pre-registered criteria

| Criterion | Status |
|---|---|
| An arm beats `L_base` with p < 0.05 on ≥ 2/3 datasets, ASR down, target accuracy not down > 2 | `L_tdr`: Pets yes, DTD p 0.071, Caltech pending. **Not decided until the Caltech rerun.** `L_down`: 0/3 at p < 0.05, so "right direction, not enough evidence" |
| TDR false cuts > 20% | no (≤ 3.4%) |
| Early rounds: `L_tdr_early − L_tdr` < 0.5 on all 3 datasets means accept contamination, no rollback | DTD −0.37, Pets +0.36. Caltech pending. So far: **accept, no rollback mechanism** |

Honest reading: the server can take back a fifth to a third of what the device attacker costs. The
ceiling (oracle60) shows much more is there. The mechanism that works is damping the flagged
client, not finding its target.

## Next

1. Rerun Caltech `L_tdr` and `L_tdr_early` with the fix (`MODE = "gate_l_device"`,
   `DATASETS = ["caltech101"]`, `L_ARMS = ["L_tdr", "L_tdr_early"]`, `BUDGET_HOURS = 10`, about 8.5 h).
   The references for `L_base`, `L_down` and `L_oracle60` are stored in the notebook, so it pairs
   against them.
2. An honest control for the damping reading: `L_tdr` with a random direction instead of d_target.
   If it scores the same, the damping reading is confirmed. Not run yet.

# Why the target guess fails, and the follow-up (written before the follow-up runs)

## Diagnosis from the logs already on disk

- The per-round signal `conc_class` finds the target far better than TDR does. It is the class that
  gets the most zero-shot probe mass under the client's own prompt, and it is logged in every run.
  In `L_base` it names the true target in 40% of rounds on DTD (TDR: 0%) and 20% on Pets (TDR:
  8%). A vote over the run gets 7/10, 3/10 and 6/10 attackers right on DTD, Pets and Caltech
  (mass-weighted vote: 6, 5, 8 of 10). By round 10 the vote is only 3, 0 and 3 of 10.
- The likely reasons TDR's projection fails:
  (1) It reads the update through a first-order projection, but the update is several local steps.
  (2) It divides by |d_c|^2, so classes with small directions get inflated scores. The logged guesses
      pile up on a few classes that are the same for every client.
  (3) Under Dirichlet 0.1 every client pushes its own few classes up, which looks like "stealing"
      too.
  (1)-(3) are not separated by these runs.
- `L_tdr` also clips every client's update to 2x the median norm, flagged or not. That clip may be
  doing part of the work credited to the cut. It was not logged; `clip_scale` is logged from now on.

## Why `L_tdr_early` is not above `L_tdr`

The gap is −0.37 on DTD (p 0.30, seeds split 2 up / 3 down) and +0.36 on Pets. That is noise around
zero, not a real reversal. "Clean from round 0" never happened: the cut hits the wrong class almost
every time, so cutting earlier removes more of the attacker's clean 60% learning, not its poison.

## Follow-up arms (`MODE = "gate_l_device"`), each differing from `L_tdr` in one thing

| Arm | Change |
|---|---|
| `L_tdr_conc` | target from the client's excess probe mass (client minus global), averaged over rounds |
| `L_tdr_true` | ORACLE: the attacker's real target |
| `L_tdr_rand` | CONTROL: a fixed random class per client |
| `L_clip` | CONTROL: never cut; only the norm clip |

## Decisions, fixed now

1. If `L_tdr_true − L_tdr` < 0.5 on both DTD and Pets, perfect targeting is worth little. Drop the
   targeting, and describe the method as damping.
2. If `L_clip` is within 0.5 of `L_tdr` on both datasets, the clip does the work. The method becomes
   the clip plus the detector, which is simpler to state.
3. `L_tdr_conc` replaces `proj` only if it names the right target on at least 30% of its malicious
   cuts and its mean is at least `L_tdr`'s on both datasets.
4. If `L_tdr_rand` is within 0.5 of `L_tdr`, that confirms the damping reading, whatever 1-3 say.

# Follow-up results (sessions 7a DTD, 7b Pets, 2026-09-25)

The runs are merged into `dtd/` and `oxford_pets/`; the zips are in `_zips/L-conc`, `_zips/L-tdrconc-pets`.

| | DTD mean | vs `L_tdr` | vs `L_base` | Pets mean | vs `L_tdr` | vs `L_base` |
|---|---|---|---|---|---|---|
| `L_tdr` (proj) | 50.16 | — | +0.90 (p 0.071) | 82.25 | — | +2.19 (p 0.030) |
| `L_tdr_conc` | 49.56 | −0.60 | +0.30 (p 0.16) | 82.19 | −0.06 | +2.13 (p 0.035) |
| `L_tdr_true` (oracle) | 49.63 | −0.53 | +0.37 (p 0.14) | 82.28 | +0.03 | +2.22 (p 0.013) |
| `L_tdr_rand` | 49.65 | −0.51 | +0.40 (p 0.08) | 81.90 | −0.35 | +1.84 (p 0.020) |
| **`L_clip`** | 49.78 | −0.38 | **+0.52 (p 0.006)** | 82.05 | −0.20 | **+1.99 (p 0.033)** |

**The norm clip is the mechanism.** On Pets the 2x-median clip hits the attackers in 387 of about 500
attacker-rounds and scales their updates to 0.70 on average. Honest clients stay at 0.99 and noisy
ones at 0.98. The attacker's update is bigger because it trains on every poisoned label and never
filters. On the seeds where the refusal detector never fired (DTD seed 3, Pets seed 1), every TDR arm
equals `L_clip` to the digit. On Pets seed 1, `L_tdr` still beat `L_base` by +3.07 without a single
cut, so the clip did all of it.

On DTD the clip rarely acts (attacker mean 0.997), and every arm lands at +0.3 to +0.5 over
`L_base`. The +0.90 of the original `L_tdr` rests on one seed (seed 0: +2.13). `L_clip` is the most
consistent: every seed is positive, sd 0.22.

**Targeting.** `conc` names the right target on DTD: 216 of 410 guesses after round 10 (53%), and 77
of 182 cuts (42%). On Pets it gets 10 of 410 (2.4%), because Pets' look-alike classes share probe
mass. Even perfect targeting (`L_tdr_true`) adds nothing: −0.53 on DTD and +0.03 on Pets.

ASR / target-class accuracy: `L_clip` DTD 4.44% / 38.2% (base 4.48 / 38.6), Pets 2.03% / 79.2% (base
2.93 / 74.1).

## Decisions (as fixed before the runs)

1. `L_tdr_true − L_tdr` < 0.5 on both: **drop the targeting.**
2. `L_clip` within 0.5 of `L_tdr` on both: **the clip does the work.** The server-side defence against
   the device attacker is the 2x-median norm clip.
3. `L_tdr_conc`: 42% of cuts right on DTD but 6% on Pets, and below `L_tdr` on DTD. **Not adopted.**
4. `L_tdr_rand` within 0.5 of `L_tdr`: **damping reading confirmed.**

Main gate L criterion (p < 0.05 on ≥ 2/3 datasets, ASR down, target accuracy not down > 2): `L_clip`
has DTD p 0.006 and Pets p 0.033, so it is **met on 2/3**. ASR drops on Pets and is flat on DTD.
Caltech is still to run.

Honesty for the thesis: norm clipping/bounding is a known defence (Sun et al. 2019, "Can You Really
Backdoor Federated Learning?"), so it is not a contribution. What is ours is the measurement:
(a) against an attacker that never cleans its data, the clip removes a fifth to a third of the
damage; (b) the refusal detector plus targeted cutting adds nothing measurable on top; (c) the 2x
median bound is harmless to honest and noisy clients (0.98-0.99). Also note: `L_clip` never uses the
detector's flags, so the defence needs no detection at all.

Next: Caltech `L_clip` (about 3.1 h) to complete the criterion. Optionally `L_clip + L_down` (the clip
plus proportional down-weighting of flagged clients), to see whether the two add up.

# Caltech101 rerun of `L_tdr` / `L_tdr_early` after the OOM fix (2026-09-25)

The crashed logs are kept as `*.crashed_oom.txt`. This session ran code from before `clip_scale`
logging existed, so the clip's effect is not visible in these logs.

| | mean | vs `L_base` | salvage |
|---|---|---|---|
| `L_tdr` | 87.07 | **+2.66 (p 0.020)** | 60% |
| `L_tdr_early` | 86.98 | +2.57 (p 0.022) | 58% |
| `L_down` | 85.62 | +1.21 (p 0.31) | 27% |

- `L_tdr_early − L_tdr` = −0.09 (p 0.84). Early rounds, all three datasets: −0.37 / +0.36 / −0.09,
  all under 0.5. **Decision final: no rollback mechanism.**
- ASR fell from 2.90% to 1.02%, and target-class accuracy rose from 83.3 to 87.3.
- Target guessed right on 0 of 103 malicious cuts, again. This is consistent with damping from the
  clip.
- **False cuts: 34 of 137 cuts (24.8%) hit honest clients**, through false refusal flags (for
  example seed 0, round 30: an honest client flagged). That is over the 20% disqualification line,
  so **TDR is disqualified**, independently of the finding that the clip does the work.
  `L_tdr_early`: 15 of 457 (3.3%).

Consequence: the gate L candidate is `L_clip`, which never uses flags and so cannot hit anyone
through a false flag. It has passed on DTD and Pets; Caltech `L_clip` is the missing cell. The same
false flags are a risk for `L_clip_down`, which down-weights flagged clients, so its value has to
be measured, not assumed.

# Sessions 8a / 8b: `L_clip` on Caltech, `L_clip_down` everywhere (2026-09-26)

| | `L_base` | `L_down` | `L_clip` | `L_clip_down` | `L_oracle60` |
|---|---|---|---|---|---|
| DTD | 49.26 | 49.61 | 49.78 | **50.28** | 52.18 |
| OxfordPets | 80.06 | 81.50 | 82.05 | **83.50** | 86.70 |
| Caltech101 | 84.41 | 85.62 | **87.16** | 86.89 | 88.84 |

| vs `L_base` (paired, n = 5) | DTD | Pets | Caltech | salvage (DTD / Pets / Caltech) |
|---|---|---|---|---|
| `L_clip` | +0.53 (p 0.006) | +1.99 (p 0.033) | +2.75 (p 0.014) | 18% / 30% / 62% |
| `L_clip_down` | +1.02 (p 0.030) | +3.44 (p 0.004) | +2.48 (p 0.019) | 35% / 52% / 56% |

`L_clip_down − L_clip`: DTD +0.49 (p 0.20), Pets +1.45 (p 0.072), Caltech −0.27 (p 0.18). Pooled
over 15 pairs: +0.56 (t = 1.96, p ~ 0.07). This pooled test is descriptive, not pre-registered.

| ASR / target-class accuracy | DTD | Pets | Caltech |
|---|---|---|---|
| `L_base` | 4.48% / 38.6 | 2.93% / 74.1 | 2.90% / 83.3 |
| `L_clip` | 4.44% / 38.2 | 2.03% / 79.2 | 0.97% / 85.0 |
| `L_clip_down` | 3.68% / **35.7** | 1.04% / 83.2 | 1.00% / 88.2 |

Mechanism, from `clip_scale`: the clip shrinks the attackers to 0.70 (Pets) and 0.56 (Caltech) on
average, in 383-436 of about 500 attacker-rounds. Honest and noisy clients stay at 0.98-0.998. On
DTD it barely acts (0.998 for everyone): the attacker's update is not larger there. That is why
DTD's salvage is lowest.

Where the down-weighting helps and where it hurts:
- On seeds where the detector never fires (DTD s3, Pets s1, Caltech s3), `L_clip_down = L_clip`
  exactly.
- Pets: the detector flags only attackers (43 malicious, 2 noisy), and the combination adds +1.45.
- Caltech: the detector flags honest clients too (5 of 23 flag decisions). Down-weighting them
  costs −0.27, and the clip had already done most of the work (62% salvage).

## Verdict against the gate L criterion

*An arm beats `L_base` with p < 0.05 on ≥ 2/3 datasets, ASR down, target-class accuracy not down
by more than 2.*

- **`L_clip`: passes on 3/3.** p < 0.05 everywhere. ASR is down on Pets and Caltech and flat on DTD.
  Target-class accuracy is within −0.4 on DTD and up elsewhere.
- **`L_clip_down`: passes on 2/3** (Pets, Caltech). On DTD, p 0.030 and ASR is down, but
  target-class accuracy falls 2.9 points (38.6 → 35.7), past the 2-point line. That number rests on
  few test images (one target class per attacker), so it is noisy, but the rule is the rule.

Decision: **`L_clip` is the server-side defence**. It is simplest, needs no detector, cannot punish a
falsely flagged client, and passes on every dataset. `L_clip_down` is reported as a variant that
adds +0.5 to +1.5 where the detector is clean (DTD, Pets) and loses a little where it is not
(Caltech). That is a trade-off tied to detector precision, not a free gain.

Reminder for the thesis: norm clipping is prior work (Sun et al. 2019). The contribution is the
measurement: against an attacker that never cleans its data, the clip recovers 18-62% of the
damage, costs honest and noisy clients nothing measurable, and the target-direction cut on top
adds nothing.

# Toward improving gate L: offline analysis of server-side signals (2026-09-26)

Data: the `L_base` logs (5 seeds per dataset). The question: which label-free server signals single
out the device attacker from honest and noisy clients (noisy clients filter on their own machine)?

Per-round AUC, attacker vs everyone else:

| Signal | DTD | Pets | Caltech |
|---|---|---|---|
| `s_upd` (update norm / median) | 0.67 | 0.90 | 0.96 |
| `s_conc_kl` (probe-mass concentration) | 0.63 | 0.81 | 0.75 |
| `r_align` (refusal, every 5 rounds) | 0.74 | 0.78 | 0.78 |

Averaging a signal per client over rounds so far, the attackers rank in the top 2 of 10 by round
10-20 on Caltech (AUC 0.94-1.00) and on Pets (AUC 0.82-0.93). On DTD the AUC stays at 0.45-0.71.

A simulated trust weight (EMA 0.8 of robust z-scores; weight 2/z above z = 2; parameters taken from
the existing detectors, not tuned) gives the mean weights below:

| Signals | DTD mal / honest / noisy | Pets | Caltech |
|---|---|---|---|
| `s_upd` | 0.97 / 1.00 / 1.00 | 0.71 / 0.96 / 0.98 | 0.50 / 1.00 / 1.00 |
| `s_upd + s_conc_kl` | 0.96 / 0.96 / 1.00 | 0.53 / 0.90 / **0.76** | 0.34 / 0.97 / 0.98 |

Reading:
1. `s_upd` is the signal the clip already uses. A trust weight built on it mostly repeats the clip,
   only with memory. It acts from round 2-6 on Caltech, against round 10-25 for the refusal
   detector.
2. The concentration signal adds attacker suppression on Pets, but it also down-weights noisy
   clients (weight 0.76), which is exactly what the project must not do.
3. On DTD no label-free server signal separates the attacker: its update is neither larger nor
   more concentrated. The server-only information has been used up there. Any real improvement
   on DTD needs information from real images.

# Gate N step 1 results: Pets and DTD (session N2, 2026-09-27; Caltech N1 pending)

The analysis cell crashed on a `cut_norm` KeyError after all 4 runs had finished (fixed; the runs
are now also zipped before any analysis). The runs were recovered from the Output download.
They are merged into `oxford_pets/` and `dtd/`, with a slim zip in `_zips/N2-pets-dtd/`.

| | `L_base` | `L_clip` | `L_clip_down` | `N_log` | **`N_excl`** (oracle: attackers out) | `L_oracle60` |
|---|---|---|---|---|---|---|
| Pets | 80.06 | 82.05 | 83.50 | 82.05 | **83.28** | 86.70 |
| DTD | 49.26 | 49.78 | 50.28 | 49.78 | **50.66** | 52.18 |

- **D3 passes.** `N_log` equals `L_clip` to the digit on every seed, on both datasets. Logging changes
  nothing, and the standalone clip reproduces the old one.
- **D2.** `N_excl − L_clip`: Pets +1.23 (p 0.23), DTD +0.87 (p 0.45). Pets meets the ≥ 1.0 bar;
  Caltech is pending.
- **D1 fails on Pets.** Cumulative AUC at round 10 is 0.78 for `self` and 0.70 for `loo`, against a bar of
  0.90. `self` reaches 0.90 only by round 20. `loo` also down-weights honest and noisy clients (simulated
  weights 0.92 / 0.87), which breaks the second half of D1. `self` is clean (1.00 / 0.97; attackers
  0.61). On DTD the signal is weak, as expected (AUC 0.50-0.60 at round 10). D1 needs both Caltech
  and Pets, so **step 2 (`N_xval`) does not run, whatever Caltech shows.**

## The finding that matters more: the realistic ceiling

`N_excl` (the attackers left out from round 0, a perfect detector) is the ceiling of **every**
down-weighting rule. It sits far below `L_oracle60`: Pets −3.42 (p 0.036), DTD −1.52. The gap is
the attackers' clean 60%. A device attacker never trains on its clean part alone, and no server-side
rule can make it, so `L_oracle60` is not reachable without the attacker's cooperation. The honest
yardstick for a server-side defence against this attacker is `N_excl`.

| Salvage against `N_excl` (reachable ceiling) | Pets | DTD |
|---|---|---|
| `L_clip` | 62% | 37% |
| `L_clip_down` | **107%** (−0.22 vs `N_excl`, p 0.84) | **73%** |

`L_clip_down` already matches a perfect detector on Pets and reaches about three quarters of it on
DTD. Better detection, cross-client validation included, has at most +1.2 (Pets) / +0.9 (DTD) left
over `L_clip`, and about 0 / +0.4 over `L_clip_down`. That is why gate N's weighting line stops
here. It is not a failure to find a better detector: there is almost nothing left for any detector
to win.

To report in the thesis:
1. Against an attacker that controls its machine, the achievable ceiling is excluding it. Its clean
   data cannot be reclaimed.
2. The clip alone reaches 37-62% of that ceiling with no detector. The clip plus proportional
   down-weighting reaches 73-107%.
3. `L_oracle60` stays in the tables as the "if the attacker cooperated" bound, clearly labelled.

# Gate N step 1: Caltech (session N1, 2026-09-27)

| | `L_base` | `L_clip` | `L_clip_down` | `N_log` | `N_excl` | `L_oracle60` |
|---|---|---|---|---|---|---|
| Caltech | 84.41 | 87.16 | 86.89 | 87.16 | **87.91** | 88.84 |

- D3: `N_log = L_clip` to the digit on every seed. **Passes on all three datasets.**
- D2: `N_excl − L_clip` = +0.75 (p 0.17), under the 1.0 bar. Pets (+1.23) met it, so D2 passes on one dataset.
- D1: cumulative AUC at round 10 is 0.75 (`self`) and 0.40 (`loo`). **Fails on Caltech too.** `self`
  reaches 1.00 only by round 20. Honest and noisy simulated weights stay at ≥ 0.98 with `self`.
- **Gate N final: the weighting line stops.** D1 fails on both priority datasets.

Reachable ceiling (`N_excl`) against the full one (`L_oracle60`) on Caltech: −0.93 (p 0.19), the smallest
of the three datasets. `L_clip` already gets 78% of `N_excl`'s gain.

| Gap `L_oracle60 − N_excl` (the attacker's clean 60%) | DTD | Pets | Caltech |
|---|---|---|---|
| points | 1.52 | **3.42** | 0.93 |

This is the size of the prize gate P is after. It is largest on Pets.

# Gate P results: prototype verification (sessions P1 Pets, P2 Caltech; 2026-09-28)

Plan: `gate_p_plan.md`, written before the runs. The Pets `N_excl` and `L_oracle60` reruns (with
per-class logging) reproduce the old runs to the digit; the old ones are kept in `oxford_pets/_superseded/`.

| | `L_base` | `L_clip` | `L_clip_down` | `N_excl` | **`P_rec`** | `P_rec_hide` | `L_oracle60` |
|---|---|---|---|---|---|---|---|
| Pets | 80.06 | 82.05 | 83.50 | 83.28 | **87.41** | 86.47 | 86.70 |
| Caltech | 84.41 | 87.16 | 86.89 | 87.91 | **89.07** | 88.96 | 88.84 |
| salvage (Pets / Caltech) | | 30% / 62% | 52% / 56% | 48% / 79% | **111% / 105%** | 97% / 103% | 100% |

| Paired (n = 5) | Pets | Caltech |
|---|---|---|
| `P_rec − L_clip` | +5.36 (p 0.023) | +1.91 (p 0.007) |
| `P_rec − L_clip_down` | **+3.91 (p 0.022)** | **+2.18 (p 0.014)** |
| `P_rec − N_excl` | **+4.13 (p 0.035)** | +1.16 (p 0.13) |
| `P_rec − L_oracle60` | +0.71 (p 0.23) | +0.23 (p 0.68) |
| `P_rec_hide − P_rec` | −0.94 (p 0.13) | −0.12 (p 0.62) |

## Criteria (all fixed before the runs)

| Criterion | Pets | Caltech | Verdict |
|---|---|---|---|
| C1: attackers' relabelled centroids (purity < 0.5) fail ≥ 80% | 100% fail | 90% fail | pass |
| C2: clean centroids (purity ≥ 0.9) pass ≥ 90% | honest 92 / malicious 90 / noisy 92 | 94 / 90 / 93 | pass (malicious at the edge) |
| C3: honest flagged ≤ 10%; attackers ≥ 60% after round 10 | 0% / 100% | 2% / 99% | pass |
| Main: `P_rec − N_excl` ≥ +1.0 on ≥ 1 dataset | +4.13 | +1.16 | **pass** |
| Beats `L_clip_down` with p < 0.05 on ≥ 1, not > 0.3 worse on the other | p 0.022 | p 0.014 | **pass (both)** |
| Safety: ASR ≤ `L_clip`, target-class accuracy not down > 2 | 0.19% vs 2.03%, 90.4 | 0.13% vs 0.97%, 87.6 | pass |
| `P_rec_hide` keeps ≥ 70% of `P_rec`'s gain over `L_clip` | 82% | 94% | pass |

**Gate P passes every criterion.** Against the device attacker, the server now reaches the oracle
that assumes the attacker cooperates (`L_oracle60`), on both priority datasets.

## Why it works, from the logs

- The check separates the data exactly as designed. The attackers' relabelled clusters pass 0%
  (Pets) and 10% (Caltech) of the time, while their clean clusters pass 90%. So the attackers' clean
  60% is kept and the poison is dropped.
- The per-class analysis (`tools/class_gap.py`) answers the earlier question. On Pets, 2-4 of the
  37 classes are held ≥ 80% by the attackers. Leaving the attackers out drops those classes from 88%
  to 60% accuracy, which is 2.5 of the 3.4 points between `N_excl` and `L_oracle60`. `P_rec` brings
  them back (89%).
- `P_rec` slightly exceeds `L_oracle60`. The likely reason, not proven: it also cleans the noisy
  clients. Their residual flipped clusters fail the check (97-99%), and noisy clients are replaced
  in 23% (Pets) / 2% (Caltech) of rounds after round 10, while `L_oracle60` keeps their residual
  noise. The gain sits in the classes shared between attackers and others (+1.05 points on Pets).
- The `hide` attacker sends only clean prototypes, so it is caught only by the sent-vs-rebuilt
  cosine: 49% of rounds on Pets, 66% on Caltech. It still loses most of its effect (ASR 0.60% on Pets).

## Costs and limits to state in the thesis

- **Protocol change.** Clients send k-means centroids of their image features per label, which
  leaks more than a prompt does. Prototype sharing is established (FedProto, FedPCL), but its
  privacy cost must be discussed. DP noise on the centroids is the standard mitigation, untested
  here.
- **The check relies on CLIP zero-shot or the global model reading the images correctly.** That
  holds on Pets and Caltech; DTD has not been run and is expected to be weaker.
- **Noisy clients get replaced often on Pets** (37% of all rounds). By design that is not a
  penalty, since the rebuilt update is their own verified data, but it deserves a sentence.
- **An adaptive attacker was tested only as `hide`.** One that crafts centroids that look like the
  label while pulling towards the target was not tested.

## Next

- DTD (optional): `P_rec`, to show where the method stops working.
- Gate K setting (data-only attacker + noisy): `P_rec` may also beat `K_fixconf`. On Pets it scores
  87.41 against a device attacker, while our method scores 85.54 against the weaker data-only
  attacker. Worth one run.
- Gate M: one data-only and one device attacker, with the final method.
