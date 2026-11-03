# CLEAR-FPL with a calibrated referee: plan (written 2026-10-29, before any real run)

This plan follows the negative stage 0 screen of `../referee_calib/margin_plan.md`. It was written
after re-reading every CLEAR-FPL run we have (5 datasets × 11 settings), the cap study, the gate D2
ablations and the stage-0 logs. The design was chosen on those logs (development data,
`offline_screen.md`, `tools/screen_calrepair.py`). The real-run rules below are fixed now, before
any real run.

## 1. What the runs show

Noise in the training set before → after CLEAR-FPL's repair, and the share of correct labels it
touches. CLEAR runs, 5 seeds, rounds 2-50.

| | Pets | Caltech101 | DTD | MNIST | EuroSAT |
|---|---|---|---|---|---|
| some clients noisy (S sym) | 13→2%, touches 1% | 12→2%, 1% | 12→3%, 7% | 12→8%, 1% | 12→10%, 6% |
| every client 25% (N sym25) | 25→6%, 3% | 25→5%, 5% | 25→17%, **36%** | 25→23%, 4% | 25→23%, 10% |
| every client 50% (N sym50) | 50→8%, 4% | 50→6%, 5% | 50→20%, 25% | 50→43%, 5% | 50→41%, 13% |
| every client 75% (N sym75) | 75→**24%**, 0% | 75→**21%**, 0% | 75→**39%**, 10% | 75→62%, 10% | 75→65%, 20% |

CLEAR-FPL is near the ceiling wherever its referee is good. It has three weak spots, and all three
come from probability thresholds fixed on Pets (flag tau 0.05, image threshold P(label) < 0.1,
60% cap):

1. **75% noise everywhere: the cap.** It stops repair at 60% of a client's images.
   - Results: Caltech N pair75 is 9.7 points behind MAE, N sym75 is 4.0 behind; Pets is 1.7-1.9
     behind.
   - The cap study already showed it: removing the cap gives Pets +6.9 / +11.3.
2. **DTD, every client 25% noisy: over-repair.** P(label) < 0.1 also hits correct images of hard
   texture classes. CLEAR touches 34-36% of the correct labels to remove 8 points of noise.
   - Results: −3.5 / −2.5 against NLPrompt-hist; −1.05 against PromptFL at sym25.
   - In the cap study, a lower threshold (0.05, exploratory) gave +3.2 / +2.4 there.
3. **MNIST and EuroSAT: almost no repair.** Only 33-44% of noisy client-rounds are flagged, and the
   noise barely drops (50→43%).
   - Cause (stage 0): the referee is right about 60% of the time but underconfident, so its scores
     are compressed.
   - The same stage-0 logs set a limit. At low noise, no rule we screened leaves less noise than
     CLEAR's, because the referee is wrong on about 40% of correct labels. A more aggressive rule
     breaks about as many labels as it fixes.
   - So on these two datasets, gains are only possible where the noise is high.

## 2. Idea: calibrate the referee once per round, then test each label against it

**Finding behind it.** On every dataset, honest clients score −0.3 to −0.5 instead of 0. Noisy
clients score just above that on MNIST and EuroSAT, but far above it on Pets. Both are miscalibration
of the referee P, not CLIP's errors. After the calibration below, the honest median is +0.01 (MNIST),
+0.11 (EuroSAT), −0.06 (Pets), 0.00 (DTD) and −0.02 (Caltech).

**Method: CLEAR-FPL + calibrated repair** (arm `cal`). Everything not listed here is CLEAR-FPL
unchanged: the referee P = ½ (global prompt + zero-shot CLIP), the score xs_m, flag tau 0.05, the
relabel rule, rescoring every round, FedAvg, and no client is ever expelled.

1. **Noise-aware temperature, one per round, pooled.**
   - Model: each client's labels follow (1 − ε_c) Cat(P^(1/T)) + ε_c Uniform(K).
   - Each client computes, for 25 temperatures (0.1 to 2.0, log-spaced), its log-likelihood under
     its own best ε_c, and sends these 25 numbers.
   - The server adds them up and broadcasts the best T.
   - A wrong label is absorbed by ε_c instead of softening P. Noisy clients therefore do not drag
     T, and a federation where every client is noisy still gets a sensible T.
   - This is the difference from a federation median, which collapses in that case (DBR-FPL).
2. **Second entry to the flag.** A client is also flagged when xs_m on the calibrated referee P_T
   exceeds 0.384. That threshold is its Pets-clean 95th percentile, the same rule as tau.
   - Every client CLEAR flags today stays flagged.
3. **Suspects.** In a flagged client, an image is a suspect when its label lies outside the
   calibrated referee's 95% prediction set: Σ_k P_T,k [P_T,k ≤ P_T,label] < 0.05.
   - This replaces the image threshold 0.1 and the 60% cap.
   - A wrong label is rejected only when the calibrated referee can reject it at the 5% level. The
     test, not a cap, limits how many correct labels are lost.
4. **Repair unchanged.** A suspect is relabelled to raw P's top class when raw P is at least 0.5
   sure, and dropped otherwise.
   - Relabelling stays on the raw P on purpose: on EuroSAT, relabelling with the sharper P_T
     broke more correct labels offline.

Cost: one extra message per round (25 numbers up, 1 down). No other client information is shared.

## 3. Offline evidence (development data, not results)

Full tables: `offline_screen.md`.

| | CLEAR | cal (design B) |
|---|---|---|
| Synthetic 75% noise, wrong labels caught (Pets / Caltech / DTD) | 77-78 / 79 / 77-78% | 86-98 / 94-99 / 84-86% |
| Synthetic DTD 25%, correct labels touched | 19% | 5% |
| MNIST real noise, noise left (sym / pair / het / N sym50 / N pair50) | 8.1 / 8.9 / 14.3 / 43.5 / 45.8% | 6.0 / 6.8 / 11.2 / 36.5 / 39.8% |
| DTD real mixed noise, noise left (sym / pair / het) | 2.5 / 3.4 / 7.8% | 4.1 / 4.8 / 10.9% (touches 1% vs 5% of correct labels) |
| Pets pair, wrong labels caught | 77% | 68% |
| MNIST / EuroSAT clean, correct labels touched | 0 / 1% | 6 / 5% |
| EuroSAT N sym50, noise left | 43.0% | 46.7% |

The offline proxy (labels caught, labels touched, noise left) was checked against the cap study,
whose real accuracies we know. It got the direction right in 6 of the 8 settings where the
exploratory threshold 0.05 changed accuracy by more than 1 point. It missed Pets N pair50 (−1.21)
and DTD N pair50 (−1.34). It is a guide, not a forecast.

## 4. Runs

Local smoke first (toy MNIST). Check that `--sure_cal none` reproduces CLEAR-FPL exactly. Then:

- **Stage A, where gains are expected: 30 runs, 5 seeds.**
  - MNIST and EuroSAT: all 11 settings each (22 runs).
  - Pets, DTD and Caltech101: N sym75 and N pair75 (6 runs).
  - DTD: N sym25 and N pair25 (2 runs).
- **Stage B, no-collapse check: 25 runs.** The other settings of Pets (9), DTD (7) and
  Caltech101 (9).

Comparators are the existing runs with the same seeds: CLEAR-FPL (`S_<sc>_full`, `N_<x>_clear`) and
PromptFL for S clean.

## 5. Rules (fixed before the runs)

Differences are new − CLEAR-FPL, last10, paired over 5 seeds.

Stage A:
- **A1, natural-image weak spots.**
  - The mean over the six 75% runs (Pets, DTD, Caltech × N sym75, N pair75) is at least +3.0.
  - The mean over DTD N sym25 and N pair25 is at least +1.0.
- **A2, far domains.**
  - The mean over the 10 noisy settings is at least +1.0 on MNIST.
  - It is at least −0.3 on EuroSAT.
- **A3, no collapse.**
  - No stage-A run is significantly worse than CLEAR (p < 0.05) by more than 1 point.
  - S clean on MNIST and EuroSAT is at least PromptFL − 1.
- **Go to stage B** if A3 holds and at least one of A1 and A2 holds. Otherwise stop: CLEAR-FPL
  stays, and the calibration finding is reported on its own.

Stage B, per dataset (Pets, DTD, Caltech101):
- **B1.** The mean over the 9 settings below 75% is at least −0.3.
- **B2.** No setting is significantly worse than CLEAR by more than 1 point.
- **B3.** S clean is at least PromptFL − 1.

**Adopt** `cal` as the thesis method if A3 and B1-B3 hold, together with A1 or A2. If only A1 or
only A2 passes, the part that failed is reported as a limitation.

Reported regardless:
- the temperature per dataset over rounds;
- honest and noisy calibrated scores;
- flags by entry (CLEAR's own flag or the calibrated one);
- repair counts;
- each client's ε_c against its true noise share.

## 6. Expected outcome and weak spots, stated before the runs

- **Likely gains:**
  - the 75% settings on Pets and Caltech (offline, about as large as removing the cap, +5 to +10);
  - DTD at 25% and 75%.
- **Possible small gain:** MNIST (+0.5 to +2).
- **Uncertain:** EuroSAT. Offline, its all-noisy settings were not better.
- **Risks:**
  - DTD mixed settings and Pets pair. The test catches fewer wrong labels there (DTD 60-72% vs
    75-88%; Pets pair 68% vs 77%), so these may lose up to about 1 point.
  - MNIST / EuroSAT clean. The extra flag hits 17-34% of honest client-rounds there. In the clean
    setting it touches about 6% (MNIST) and 5% (EuroSAT) of all correct images.
  - Pair noise at 75%. The uniform noise model does not fit it, so T softens (1.21 on Pets
    synthetic pair75) and only 86% of wrong labels are caught, against 98% for sym75.
- **Not a promise of "better everywhere".** The far-domain ceiling (section 1, point 3) applies
  to any referee-based repair.

## 7. Overlap to check before writing up

- **Tools that are known:**
  - temperature scaling (Guo et al. 2017);
  - prediction sets and conformal-style label tests (Romano et al. 2020, APS);
  - Confident Learning (Northcutt et al. 2021, per-class self-confidence thresholds);
  - noisy-label calibration;
  - federated calibration.
- **Claimed as new:**
  - the diagnosis that miscalibration, not CLIP's errors, explains why one fixed threshold breaks
    across datasets (far domains, hard classes, extreme noise);
  - a noise-aware federated temperature that profiles out each client's noise share, so it needs
    no clean reference and no federation median;
  - replacing CLEAR's fixed image threshold and cap by a calibrated prediction-set test.

## 8. Implementation (2026-10-29, after the user's OK, before any real run)

**Code.**
- `flip/flcore/sure.py` adds `cal_profile`, `cal_pick` and the `--sure_cal noise` branch of
  `sure_round`.
- `flip/flcore/servers/server_fedavg.py` adds the pre-pass that collects the profiles and
  broadcasts T each round.
- `flip/main.py` adds the flags `--sure_cal`, `--sure_cal_tau 0.384` and `--sure_cal_alpha 0.05`.
- Each client-round's record also logs T, the calibrated score, which entry flagged it, and eps.

**Local smoke** on toy MNIST, 2 rounds, CPU:
- `S_sym_cal` and `N_sym75_cal` both finish with rc 0.
- CLEAR-FPL (`S_het_full`) gives the same loss and accuracy at every round as its log from before
  the change, so `--sure_cal none` leaves CLEAR-FPL untouched.
- In the N sym75 smoke the calibrated entry flagged 4 clients that CLEAR's score missed (71-78%
  noise). Their suspects were almost all wrong labels.
- T sat at the grid's lower end (0.10-0.11) in rounds 0-2. The grid stays as planned: the offline
  screen used the same grid, and from round 10 on MNIST it gave a median of 0.17.
- On CPU a round takes about 1.5× as long, because of the extra forward pass in the pre-pass.

**Notebooks and analysis.**
- Arm `cal` in `tools/make_notebook.py` (`S_<sc>_cal`, `N_<x>_cal`).
- Stage A notebooks:
  - `kaggle/calA_mnist_1` (6 runs);
  - `kaggle/calA_mnist_2` (5);
  - `kaggle/calA_eurosat` (11);
  - `kaggle/calA_pets` (2);
  - `kaggle/calA_dtd` (4);
  - `kaggle/calA_caltech_1` and `kaggle/calA_caltech_2` (1 each).
  - EuroSAT, DTD and Caltech101 stage-A runs (17) go to the server via `server/queue_calA.txt`; MNIST and Pets stay on Kaggle.
- Analysis, written now: `tools/analyze_calrepair.py`. It writes `results.md`, and every
  CLEAR-FPL and PromptFL comparator run is present with 5 seeds.
