# Referee-strength gate: confirmation (plan, fixed 2026-10-30 before any gated run)

The user's last attempt to improve FedCLEAR (CLEAR-FPL). The background is in `gate_screen_plan.md`:
- the offline check was NO GO under its own pre-registered rule;
- a threshold chosen post hoc looked promising.

This plan tests that idea on new runs, with the rules fixed here. Whatever the outcome, it is final: no further variant of `cal` is tried.

## Method (arm `gate`)

1. **Rounds 0-5: plain CLEAR-FPL.**
2. **Decision, after round 5.** The server adds up the suspects and relabelled counts that the clients reported in rounds 1-5. It turns the gate on if the one-sided 95% Wilson lower bound of relabelled / suspects is at least **0.12**. With no suspects at all, the gate stays off. The decision is made once.
3. **Rounds 6-50, gate on:** `cal`'s repair, which is:
   - the noise-aware pooled temperature;
   - suspects = labels outside the calibrated 95% prediction set, with no 0.1 threshold and no cap.

   The calibrated extra flag is **dropped** (`--sure_cal_flag false`): only CLEAR-FPL's own flag decides who repairs.
4. **Rounds 6-50, gate off:** CLEAR-FPL unchanged.

Flags: `--sure true --sure_cal noise --sure_cal_flag false --sure_gate 0.12` (`--sure_gate_rounds 5` is the default).

**Why the decision is per run, with a lower bound.** The share was examined pooled over 5 seeds (`gate_screen.md`). A single run sometimes has very few suspects; for example MNIST N sym25 seed 1 has 5/5. The lower bound keeps a handful of suspects from switching the method. This guard was added before any gated run. It was chosen after looking at the per-seed counts of the existing CLEAR-FPL runs, which are label-free; no outcome was known.

## Runs (42; 5 seeds each, same COMMON settings as every other run)

For planning, the gate decision of each existing CLEAR-FPL seed is predicted from its logged counts. Every setting where any seed's lower bound is at least 0.08 (the threshold minus a safety margin) is run:

| dataset | settings run | count |
|---|---|---|
| MNIST | S het, N sym25, N sym50, N sym75, N pair25, N pair50, N pair75 | 7 |
| EuroSAT | S sym, S het, N pair75 | 3 |
| Pets | all 11 | 11 |
| DTD | all 11 | 11 |
| Caltech101 | all except S clean | 10 |

**Not run: 13 settings**, where every seed's bound is at most 0.07 or undefined:
- MNIST S sym / pair / inst / clean;
- EuroSAT S pair / inst / clean and N sym25 / sym50 / sym75 / pair25 / pair50;
- Caltech S clean.

There the gated method is plain CLEAR-FPL by construction. The analysis uses CLEAR-FPL's numbers with a difference of 0.

The 8 stage-A settings that `cal` helped are re-run, because the gated method is not `cal`: it has 5 CLEAR rounds first and no extra flag.

## Rules (comparators: existing CLEAR-FPL runs `S_<sc>_full` / `N_<x>_clear`, same seeds; last10; paired over the 5 seeds)

Weak spots W are the 8 settings: Pets, DTD and Caltech101 at N sym75 and N pair75, plus DTD N sym25 and N pair25.

- **C1 (gain where CLEAR-FPL is weak).** Over W:
  - the mean gated − CLEAR is at least **+2.0**;
  - at least **4 of the 8** are significantly better (p < 0.05).
- **C2 (no harm elsewhere).**
  - On each of the 5 datasets, the mean gated − CLEAR over its settings outside W is at least **−0.3**.
  - No setting among all 55 is significantly worse than CLEAR-FPL (p < 0.05) by more than 1 point.
- **C3 (clean federation).** On every dataset, gated S clean is at least PromptFL − 1.

**Adopt** the gated method, so that it replaces FedCLEAR in the paper, only if C1, C2 and C3 all pass. Otherwise FedCLEAR stays, final.

The C1 bar was set after stage A. Stage A's `cal` gave +2.91 over W, with 5 of 8 significant. The old A1 bar (+3.0 over the six 75% runs) cannot be reached by any gating of `cal` (`gate_screen_plan.md`), so C1 replaces it with the user's goal: "raise accuracy where CLEAR is weak, and do not collapse elsewhere".

**Reported, not decided:**
- every run's actual gate decision, compared with the prediction;
- for gated-off seeds, how close the result is to CLEAR-FPL (GPU runs are not bit-identical).

Analysis: `tools/analyze_gate.py` (written with this plan), output `calrepair/gate_results.md`.
