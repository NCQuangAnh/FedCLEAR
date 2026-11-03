# Gated repair with a capped temperature (arm `gatec`): plan, fixed 2026-10-30 before any gatec run

## Why

This is the user's decision, taken after the gate confirmation (`gate_confirm_plan.md`) had partly come in: "tôi vẫn muốn sửa để cải tiến FedCLEAR ... nếu kết quả pass trên các seed hiện tại thì ta bốc thêm 3 seed khác để kiểm tra xem có bị sập ko" ("I still want to fix it to improve FedCLEAR ... if the result passes on the current seeds, we draw 3 more seeds to check whether it collapses"). The gate confirmation keeps its own pre-registered verdict, which is reported as planned.

**The failure being fixed.** In the gated Pets N pair75 run, seeds 2 and 3 collapsed: 53.7 and 36.9 against CLEAR-FPL's 69.9 and 75.4. The `sure` records show the mechanism.
- At the switch (round 6), the pooled temperature T went to the grid ceiling, 2.0.
- A high T softens P. The 95% prediction sets widen, and the suspects drop from about 174 to 115-121. The share of wrong labels kept in training rises from 0.25 to 0.40-0.43.
- The global prompt then absorbs more wrong labels, and fewer still are suspected. In seed 3 the suspects fall to 15, eps falls to 0.06 against a true noise of 0.75, and the noise kept reaches 0.70.
- Seeds whose T stayed at 1.2-1.4 kept the same or less noise than CLEAR-FPL.

The same sign appears elsewhere. Every run-seed with T = 2.0 is a loss (6/6): Pets pair75 under stage-A `cal` (−21.3), EuroSAT sym75 seeds 3 and 4 (−13.9, −9.3), MNIST sym75 seed 2 (−5.3), and the two seeds above.

**The fix, fixed on principle and not tuned.** T = min(fitted T, 1).
- P is the average of the global prompt and zero-shot CLIP, so it is already softened by that mix.
- A fit above 1 arises when the uniform-noise model has to explain wrong labels that the global prompt has partly learned. It does that by softening P instead of raising eps.
- With the cap, the calibration may sharpen P but never soften it.
- The value 1 is "no softening", not a tuned number. No other cap value is tried.

The other candidate was rejected before any run. Falling back to CLEAR-FPL's suspects whenever `cal` has fewer would cancel the DTD 25% gains, which come exactly from `cal` suspecting fewer images.

**Honesty.** The fix was designed after seeing the failure on seeds 0-4, so stage 1 on those seeds is a development check only. Stage 2 runs on held-out seeds 5-7, which no earlier run used and no decision has looked at. It is the real test.

## Method (arm `gatec`)

The gate arm, unchanged, plus `--sure_cal_tmax 1`:

`--sure true --sure_cal noise --sure_cal_flag false --sure_gate 0.12 --sure_cal_tmax 1`

The fitted T is still logged as `T_fit`, next to the broadcast `T`.

## Stage 1: seeds 0-4 (development)

**Runs.** A setting needs a `gatec` run only if, in its gate run, some seed had a broadcast T above 1 in some round. Otherwise `gatec` takes the same decision as `gate` in every round, and the gate run is reused as it is. Settings the gate plan does not run (13) are CLEAR-FPL by construction, as before.
- **Known on 2026-10-30:**
  - Pets N pair75 (T up to 2.0), N sym75 (1.214) and N pair50 (1.071);
  - Caltech101 N sym75 (seed 0, 1.071).
- **The rest:** decided by the same rule as each gate result arrives (DTD, MNIST, EuroSAT and the remaining Caltech101). The list is appended here before those runs start.

**Rules.** C1, C2 and C3 exactly as in `gate_confirm_plan.md`, with the same comparators: CLEAR-FPL `S_<sc>_full` / `N_<x>_clear` on the same seeds, last10, paired over the 5 seeds.
- C1: over W, the mean is at least +2.0, and at least 4 of the 8 are significantly better.
- C2: on each dataset, the mean outside W is at least −0.3, and no setting is significantly worse by more than 1 point.
- C3: S clean is at least PromptFL − 1 on every dataset.

**Pass:** go to stage 2. **Fail:** stop, and FedCLEAR stays as it is. No further variant is tried.

## Stage 2: held-out seeds 5, 6, 7 (confirmation)

**Runs.** Run on seeds 5, 6 and 7 (`--seed 5 --times 3`): arm `gatech` (`gatec`) and arm `clearh` (CLEAR-FPL as comparator). These cover 12 settings:
- N sym75 and N pair75 on all five datasets;
- DTD N sym25 and N pair25.

That is 24 runs of 3 seeds each.

**Rules.** Differences are gatec − CLEAR-FPL, last10, paired by seed.
- **H1, no collapse:** on Pets, DTD and Caltech101 (the 8 W settings, 24 seed pairs), no seed pair has a difference of −5 points or worse.
- **H2, the gain holds:** the mean difference over the same 24 seed pairs is at least +1.0.
- **H3, no harm on MNIST and EuroSAT:** the mean difference over their 4 settings (12 seed pairs) is at least −1.0.

H1 is limited to Pets, DTD and Caltech101 because single-seed MNIST and EuroSAT differences swing by ±10 points even at 25% noise (stage A). MNIST and EuroSAT are covered by the mean in H3.

**Adopt** `gatec` as the improved FedCLEAR only if stage 1 (C1-C3) and stage 2 (H1-H3) both pass. The paper tables then use the seed 0-4 runs, and the held-out check is reported in the text. Otherwise FedCLEAR stays, final. The collapse mechanism is reported as the reason FedCLEAR uses a fixed threshold and cap.

**Reported, not decided:**
- per seed: the broadcast T and the fitted T at the switch;
- the share of wrong labels kept in training against CLEAR-FPL;
- every gate decision.

Analysis: `tools/analyze_gatec.py`, written with this plan; output `calrepair/gatec_results.md`.

## Stage 1 list, appended 2026-10-31 before these runs start

The gate zips for DTD (`gate_dtd`, server `queue_gate`) and the rest of Caltech101 (`queue_gate`) are in. By the rule above, a gatec run is needed wherever some seed of the gate run broadcast T > 1. That gives 6 more runs. The largest broadcast T per seed, seeds 0-4:

| setting | max broadcast T per seed |
|---|---|
| DTD N sym50 | 0.835, 0.946, 0.946, **1.071**, 0.835 |
| DTD N sym75 (W) | 0.946, **1.214**, 0.650, 0.737, 0.835 |
| DTD N pair25 (W) | 0.946, 0.946, 0.946, **1.071**, 0.835 |
| DTD N pair75 (W) | **1.071**, 0.946, 0.835, 0.737, 0.835 |
| Caltech101 N pair50 | **1.071**, 0.835, 0.835, 0.835, 0.946 |
| Caltech101 N pair75 (W) | **1.214**, **1.214**, **1.071**, **1.214**, **1.071** |

- Every other DTD and Caltech101 gate run stayed at T ≤ 1, so it is reused as it is.
- Where they run: the server, one at a time (`server/queue_gatec.txt`, W settings first), about 8 h in total.
- MNIST and EuroSAT are decided by the same rule when the `gate_mnist_eurosat` zip arrives, and appended here before their runs.
