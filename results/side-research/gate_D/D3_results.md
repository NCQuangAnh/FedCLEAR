# Gate D stage 3 results: both fixes fail on Pets (2026-10-18)

Plan: `gate_d3_plan.md`. Runs: d3/gate_d3_pets_{budget,keep}, 5 scenarios x 5 seeds each.
Reference `S_full` = stage 2, same seeds.

| Pets last10 | sym | pair | inst | het | clean | noisy mean |
|---|---|---|---|---|---|---|
| S_full (stage 2) | 88.04 | 88.09 | 87.68 | 86.96 | 87.93 | 87.69 |
| budget | 86.75 | 85.48 | 86.58 | 85.81 | 87.83 | 86.15 (−1.54) |
| keep | 87.27 | 87.02 | 87.05 | 85.57 | 87.93 | 86.73 (−0.96) |

Correct images of honest clients touched, all scenarios, rounds 0-49:
- S_full: 1208 (346 dropped, 862 wrongly relabelled);
- budget: 174;
- keep: 683.

Noisy images caught in careless clients:
- S_full: 44245 of 47787 image-rounds;
- budget: 35549;
- keep: 43953.

**Rule outcome: neither candidate qualifies** (both lose more than 0.3 on the noisy mean). As
written in the plan, `S_full` stays and the clean-DTD cost (−0.87) is reported as a limitation.
- budget does protect honest clients (7x fewer correct images touched), but it also leaves a
  quarter of the real noise in the careless clients.
- keep loses the drops of unsure noisy images, which matter on Pets.

Extra check on the stage 2 records (offline, not part of the rule): would requiring the flag in k
consecutive rounds help? No. The false flags are persistent (the same honest clients sit above
the threshold round after round): on DTD clean the honest flag rate goes 6.2% -> 5.1% at k = 3,
while careless clients lose 4% of their flags. The false flags come from particular honest clients
whose score stays above 0.05 on DTD, not from noise in the score.
