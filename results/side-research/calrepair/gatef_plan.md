# gatef: the gate, capped temperature, and a suspect floor at the client's own noise estimate

Written 2026-11-01, before any gatef run. Analysis: `tools/analyze_gatef.py`.

**Deviation from gatec_plan.md.** That plan said: if gatec fails, FedCLEAR stays and no further variant is tried. gatec failed stage 2 on H1 only (DTD N pair75 seed 5, −5.14; H2 +4.08 and H3 +0.00 passed). On 2026-11-01 the user decided to try one more variant, designed from the seed 5-7 logs. Seeds 5-7 are therefore development seeds now, and the decision rests on fresh seeds 8, 9 and 10, which no run has used.

## The failure being fixed

From the `sure` records of the gatec held-out runs (`gatec_results.md`, stage 2):
- In calibrated mode a flagged client suspects only the images whose label lies outside P_T's 95% prediction set. Where CLIP is a weak referee (DTD, zero-shot 42%, 47 classes), the sets are wide, many wrong labels fall inside them, and the client suspects far fewer images than it has wrong labels.
- DTD N pair75 seed 5: at the switch (round 6) the suspects fall from CLEAR-FPL's 221 to 159, then 136 by round 10. The wrong labels kept in training rise from 86 (CLEAR-FPL) to 159, and accuracy falls from 38 to 33 while CLEAR-FPL climbs to 41.
- The client's own noise estimate eps (the best eps of the (1 − eps) Cat(P_T) + eps Uniform(K) model, already computed by `--sure_cal`) was right: about 0.72 against a true 0.75. Suspects per image were only 0.36-0.53 on DTD 75%, against eps 0.72-0.78. On Pets and Caltech101 at 75% the suspects per image were already close to eps (0.62-0.75), which is where gatec gains.
- eps drifts once the prompt absorbs wrong labels: DTD N pair75 seed 5 went from 0.72 at round 6 to 0.57 at round 20. At the switch round it is accurate on every dataset where the gate turns on (pooled error 0.00-0.03 on Pets, Caltech101 and DTD; per client mean error 0.00-0.07, worst 0.29 on DTD).

## Method (arm `gatef`)

gatec (`--sure_cal noise --sure_cal_flag false --sure_gate 0.12 --sure_cal_tmax 1`) plus `--sure_cal_floor true`:
- At its first calibrated round (the switch, round 6), each client freezes its noise estimate eps0. It is never recomputed.
- From then on, a flagged client suspects at least round(eps0 · n) images. If its prediction-set suspects are fewer, it adds the images whose labels are least plausible under P_T (smallest prediction-set p-value, then smallest P_T(label)) until it reaches that number.
- Nothing else changes: who is flagged is still decided every round, relabelling and dropping are unchanged, and a client that is not flagged trains on its data untouched. Before the switch, and wherever the gate stays off, gatef is exactly CLEAR-FPL.
- No new tuned number: eps is already estimated, and the floor uses it as it is.

Known risk: the per-client error of eps on DTD reaches 0.29. A flagged clean client with an overestimated eps loses some clean images. In DTD S het seed 4, a clean client had eps 0.16 and was flagged at round 6 only.

## Stage D: development, seeds 5-7

Arms `N_<x>_gatefh`, with `N_<x>_clearh` (already run) as the comparator, on the 8 W settings: Pets, DTD and Caltech101 at N sym75 and N pair75, plus DTD N sym25 and N pair25. On MNIST and EuroSAT the gate stayed off on every seed 5-7 run, so gatef equals CLEAR-FPL there by construction and is not run.
- **D1:** no seed pair at −5 or worse among the 24 (this includes DTD N pair75 seed 5).

## Stage H: confirmation, fresh seeds 8, 9, 10

Arms `N_<x>_gatefc` and `N_<x>_clearc` on the same 12 settings as gatec stage 2: the 8 W settings plus MNIST and EuroSAT at N sym75 and N pair75. Differences are gatef − CLEAR-FPL, last10, paired by seed.
- **H1, no collapse:** on the 8 W settings (24 seed pairs), no seed pair at −5 or worse.
- **H2, the gain holds:** the mean over the same 24 seed pairs is at least +1.0.
- **H3, no harm on MNIST and EuroSAT:** the mean over their 4 settings (12 seed pairs) is at least −1.0.

**Adopt** gatef as the improved FedCLEAR only if D1 and H1-H3 all pass. Then gatef is run on seeds 0-4 for every setting where the gate turned on in any gate run, the paper tables use those runs, and the seed 5-10 checks are reported in the text. Otherwise FedCLEAR (CLEAR-FPL v1) stays, final; gatec and gatef are reported as an analysis of why a fixed suspect cap is the safe choice. No further variant either way.

## Predictions (written before the runs)

- DTD N sym75 / N pair75, seeds 5-7: after the switch, suspects per image at least eps0 (about 0.72), and fewer wrong labels kept at round 10 than CLEAR-FPL. The mean difference over these 6 seed pairs is at least −1.
- Pets and Caltech101 at 75%, seeds 5-7: within ±1.5 of gatec's held-out gain per setting (the floor rarely binds there).
- DTD N sym25 / N pair25, seeds 5-7: a mean gain of at least +2 (gatec: +3.0 and +3.5).

## Reported, not decided

Per seed: eps0, suspects per image after the switch, the share of rounds where the floor binds, and the wrong labels kept against CLEAR-FPL.

## Seeds 0-4 (added 2026-11-01, before any gatef run; reported, not decided)

The notebooks have spare time, so each ends with one 5-seed gatef run on seeds 0-4: DTD N pair75 (`gatef_a`) and DTD N sym75 (`gatef_b`), against CLEAR-FPL `N_<x>_clear`. These are the settings where the floor should matter most (gatec on seeds 0-4: −0.08 and +0.16). Seeds 0-4 were seen during the design, so these runs decide nothing. They are reported, and if gatef is adopted they go into the paper tables.

## Runs

- Kaggle `gatef_a`: DTD gatefh × 4; DTD N sym75 and N pair75, gatefc and clearc; MNIST N sym75 and N pair75, gatefc and clearc. 12 runs, about 8.8 h, then DTD N pair75 gatef on seeds 0-4 (about 1.6 h).
- Kaggle `gatef_b`: DTD N sym25 and N pair25, gatefc and clearc; Pets gatefh × 2; Pets N sym75 and N pair75, gatefc and clearc; EuroSAT N sym75 and N pair75, gatefc and clearc. 14 runs, about 8.9 h, then DTD N sym75 gatef on seeds 0-4 (about 1.6 h).
- Server `queue_gatef_caltech`: Caltech101 gatefh × 2, then gatefc and clearc × 2. 6 runs, about 7.4 h, one at a time.

## Outcome and the seeds 0-4 runs (added 2026-11-02, after the verdict)

`tools/analyze_gatef.py` (`gatef_results.md`): D1 pass (worst seed pair −2.17, mean +5.51), H1 pass (worst −1.86, DTD N pair75 seed 9), H2 pass (+4.40), H3 pass (+0.00; the gate stayed off on every MNIST/EuroSAT seed 8-10). gatef is adopted as the improved FedCLEAR.

Predictions against the outcome:
- DTD N sym75 / N pair75, seeds 5-7: suspects per image matched eps0 (0.72-0.79), as predicted. Fewer wrong labels kept than CLEAR-FPL in 5 of 6 seed pairs (DTD N pair75 seed 7: 0.42 vs 0.40). Mean difference +0.78 (prediction: at least −1). Correct.
- Pets and Caltech101 at 75%, seeds 5-7, within ±1.5 of gatec: Pets sym75 +5.75 vs +6.1, Caltech sym75 +9.34 vs +9.1, Caltech pair75 +12.50 vs +11.2 hold; Pets pair75 +7.78 vs +2.7 does not (better). "The floor rarely binds there" was wrong: it bound in 62-100% of the calibrated rounds on Pets and Caltech101.
- DTD N sym25 / N pair25, seeds 5-7, mean gain at least +2: +3.72 and +3.44. Correct.

Per the rule above, gatef now runs on seeds 0-4 in every setting where the gate turned on in at least one seed of the gate runs (`gate_results.md`). Read off that table:
- MNIST (5): S het, N sym25, N sym50, N pair25, N pair50. N sym75 / N pair75 and the S settings not run there were off in every seed.
- EuroSAT (1): S sym.
- Pets (11): all settings.
- DTD (8): S sym, S pair, S inst, S het, N sym25, N sym50, N pair25, N pair50. N sym75 and N pair75 are already done (`gatef_a`, `gatef_b`); S clean was off in every seed.
- Caltech101 (10): every setting except S clean (not run in the gate study, predicted off).

That is 35 runs of 5 seeds. Every other setting keeps the CLEAR-FPL seeds 0-4 runs, which gatef equals by construction when the gate is off.

## Seeds 0-4 runs in (added 2026-11-02)

In: `gatef0_pets_1`, `gatef0_pets_2`, `gatef0_caltech_1`, `gatef0_caltech_2` (Kaggle) and `queue_gatef0_caltech` (server, 6 N runs). 23 runs, all rc 0, seeds 0-4. The server zip also held a partial Caltech101 S het run (stopped with Ctrl+C, a duplicate of the Kaggle run); it was deleted. Still out: `gatef0_dtd_1`, `gatef0_dtd_2` (DTD's 8 settings and MNIST N sym25/sym50/pair25/pair50).

Per setting in `gatef_results.md` (section "Seeds 0-4"). In short, gatef − CLEAR-FPL:
- 75%: Pets sym75 +5.43, pair75 +11.24; Caltech101 sym75 +4.80, pair75 +8.91; DTD sym75 +2.05, pair75 +1.33. Every seed pair positive except DTD pair75 seed 3 (−1.0).
- Scenario 1 and 25/50%: every setting mean within ±1.01. Largest drops Caltech101 N pair50 −0.76 (p 0.13) and N sym50 −0.57 (p 0.22), Pets N sym50 −0.35 (p 0.044, 5/5 seeds negative). Largest gains Caltech101 S het +1.01, Pets N sym25 +0.56, Pets S het +0.43.
- MNIST S het −0.48: the gate turned on in one seed only (seed 1, −2.39, the worst seed pair of the 125); the other four seeds equal CLEAR-FPL. EuroSAT S sym +0.02 (on in one seed).
- Against the other trained methods (NLPrompt as in the paper tables): gatef ranks first in 22 of the 23 settings, second in Caltech101 S inst (89.64 vs NLPrompt 89.79, as CLEAR-FPL did). It moves to first in Pets N sym25, Caltech101 S sym (89.88 vs 89.87) and Caltech101 S het.

No no-harm rule was fixed for these runs, so nothing here is a decision.

## Seeds 0-4 complete (added 2026-11-02, after gatef0_dtd_1/2)

All 37 seeds 0-4 gatef runs are in (rc 0, 5 seeds each); `gatef_results.md` regenerated.
- DTD scenario 1: S sym +0.74, S pair +0.37, S inst -0.02, S het +1.32 (no harm). DTD N: sym25 +4.42,
  pair25 +3.64, sym50 +0.67, pair50 -0.29, sym75 +2.05, pair75 +1.33. DTD mean +1.42 over 50 seed pairs.
- MNIST: the gate opened on seed 1 only, in every MNIST setting. N sym50 seed 1 is -10.61 (mean 50.10 ->
  47.97); S het seed 1 -2.39; N pair25 seed 1 +1.94. In N sym50 seed 1 the floor holds 36 of the 80 images as
  suspects from round 6 on; 27 are dropped and only about 14 of those are noisy, so about 13 clean images
  (16% of the data) leave training every round. With a weak referee (zero-shot CLIP 57.7% on MNIST) the
  floor pushes out clean images the prediction set alone would have kept.
- The pre-registered rules (D1, H1-H3) did not cover MNIST N sym50; this seed is reported, not used to decide.
