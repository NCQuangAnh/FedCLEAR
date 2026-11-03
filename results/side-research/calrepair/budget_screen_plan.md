# Noise-budget repair: offline check (plan, fixed 2026-10-30 before anything was computed)

## Question

In the stage-A runs, `cal`'s suspect rule (labels outside the calibrated 95% prediction set) gives opposite results on DTD:
- **Under-repairs at 75% noise.** It catches 53% of the wrong labels vs CLEAR-FPL's 68%, leaving 50% noise vs 39%.
- **Gains at 25% noise** because it touches far fewer correct labels: 7% vs 36%.

The idea: each flagged client repairs as many images as its own noise estimate says it has. The rule is fixed by a principle, with no new threshold:

- **Design E (budget).** Only clients flagged by CLEAR-FPL's own flag repair; there is no extra flag.
  - The client's noise estimate eps_c is the eps of its best fit under the noise-aware model at the pooled temperature T. This is the same eps that `cal` already logs.
  - Suspects are the round(eps_c · n) images with the lowest calibrated P_T(label). Under that fitted model these are the images most likely to be wrong.
  - Relabelling is unchanged: P's top class when P is at least 0.5 sure, dropped otherwise.

**Lessons from DBR-FPL that this check must clear.** DBR-FPL estimated a client's contamination against a federation median, which assumes mostly clean clients. Its estimate was 23-33 points off, it collapsed when every client was noisy (CLEAR-FPL beat it by 8-41 points), and it cut every client, honest ones included.

## Data (all already on disk; no new runs)

- **R:** real `cal` runs, `sure` records: eps against the true noise share per client-round. The available settings are Pets / DTD / Caltech N sym75 and N pair75, and DTD N sym25 and N pair25.
- **F:** stage-0 `D_*_fp` logs. These have real S-setting noise, a PromptFL referee and full probabilities, so T and eps are fitted exactly as in `cal`.
- **Y:** synthetic all-noisy labels flipped from the clean `D_clean_fp` logs, with a clean-trained referee, as in `offline_screen.md`. Every client is flagged.
- **D:** `N_*_diag` logs, PromptFL trained on the noisy labels (DTD and Pets N sym75 / pair75 / pair50). The referee here is corrupted as it is in a real 75% run, which Y missed. There are no full probabilities, so E uses T = 1 there: eps is fitted on P(label), and images are ranked by P(label). Every client is flagged.
- Also reported, without a verdict: an oracle budget that uses the true noise share, to separate the ranking quality from the accuracy of eps.

## Checks (all must pass, otherwise NO GO and nothing is tuned)

1. **Estimate does not collapse when every client is noisy.** On R, mean |eps − true noise| over flagged client-rounds (rounds 1-50) is at most 0.10 on each of Pets, DTD and Caltech101.
2. **Honest clients are not cut.** On F, the correct labels E touches on honest client-rounds are no more than CLEAR-FPL's, on each of Pets, DTD and Caltech101.
3. **No over-repair at 25% (DTD).** On Y, for DTD sym25 and pair25, E touches no more correct labels than design A (`cal`'s prediction set without the extra flag) plus 1 point, and leaves no more noise than A.
4. **No under-repair at 75%.** On D, for DTD N sym75 and N pair75 and for Pets N pair75 and N sym75, compared with CLEAR-FPL's rule replayed on the same logs:
   - E leaves no more noise than CLEAR + 1 point;
   - E touches no more correct labels than CLEAR + 5 points.

**GO:** E replaces `cal`'s prediction-set suspects inside the gated method (the gate is unchanged) before the 42 confirmation runs start. `gate_confirm_plan.md` is re-fixed with this change, before any run.

**NO GO:** the confirmation runs go ahead exactly as planned.

Script: `tools/screen_budget.py`, which writes `calrepair/budget_screen.md`.

## Outcome (2026-10-30; details in `budget_screen.md`)

**NO GO.** Checks 1-3 pass; check 4 fails on all four deciding settings.

1. **eps does not collapse** when every client is noisy. Per-dataset error: Pets 0.087, DTD 0.083, Caltech 0.031, so DBR-FPL's failure is avoided. At 75% noise eps underestimates: Pets pair75 −0.13, DTD sym75 −0.08.
2. **Honest clients are untouched:** 0.0% of their correct labels.
3. **DTD 25% is slightly better than A:** noise left 5.8 / 5.6 vs 6.4 / 6.5, correct labels touched 5.2 / 5.4 vs 4.6 / 4.8.
4. **With a referee trained on 75%-noisy labels, E catches far fewer wrong labels than CLEAR-FPL's rule.**
   - DTD sym75: 48% vs 75% caught, 58% vs 42% noise left.
   - Pets pair75: 21% vs 65% caught.
   - Even the oracle budget (the true noise count) touches 28-43% of the correct labels on DTD 75%, against CLEAR-FPL's 12-25%.

**Caveat.** E ran at T = 1 there, because those logs have no full probabilities. That makes its eps lower than in a real `cal` run.

**Reading.** At 75% noise the referee itself is corrupted, so cutting more wrong labels necessarily cuts correct ones too. DTD 75% is a limit of the referee, not of how many images a client cuts.

As planned, the gate confirmation runs go ahead unchanged.
