# Referee calibration: plan (written 2026-10-29, before any run)

> **Superseded on 2026-10-29 by `margin_plan.md`; never run.** Flaw: it keeps tau = 0.05, but calibration moves honest clients' scores toward 0, so honest false flags would jump. The temperature idea is kept there as candidate `cal`, with a re-derived threshold.

## Why

The MNIST / EuroSAT study (`../mnist_eurosat/results.md`) and its diagnostic follow-up showed:
- CLEAR-FPL under-flags on MNIST and EuroSAT. Only 37% / 44% of noisy client-rounds are flagged,
  against about 100% on Pets / DTD / Caltech. Its gain over PromptFL drops to about +2 points.
- Neither CLIP use is the cause. Taking zero-shot CLIP out of the referee (`noclip`) makes things
  worse, and removing the look-alike merge (`nomerge`) changes nothing.

### Offline screen (2026-10-29, `screen.md`, `tools/screen_flag_rules.py`)

The screen used the PromptFL runs' per-image logs on all 5 datasets. Every self-calibrating test
"against labels drawn from P" fails on MNIST / EuroSAT:
- one-sided z-test of the mean surprise: 3% / 7% of noisy clients flagged;
- the noise share implied by P: 45% / 37%;
- that share as a z-test: 4% / 10%;
- surprise per unit of entropy: 23% / 23%.

The reason is measured directly (clean clients, rounds 40-50, referee e):

| | Pets | DTD | Caltech101 | MNIST | EuroSAT |
|---|---|---|---|---|---|
| accuracy of P on the client's images | 87.6 | 72.2 | 91.2 | 71.5 | 68.8 |
| mean confidence (max prob) | 77.9 | 48.2 | 83.1 | 35.8 | 36.5 |
| entropy / log K | 0.18 | 0.51 | 0.13 | 0.81 | 0.79 |

On MNIST and EuroSAT the referee is right about 70% of the time but only about 36% confident. Its
predictions are nearly flat. A wrong label then costs almost no extra surprise, and a right label
looks less surprising than P expects, so honest clients sit well below 0 (z about -5). Every rule
that measures surprise against P's own expectation inherits this bias.

The root cause is therefore the referee's **underconfidence**, not its errors and not CLIP. This
also explains two side effects:
- the 0.1 suspect threshold means little when every class has P ≈ 0.1;
- MNIST relabels only 25% of its suspects, because P rarely reaches the 0.5 relabel confidence.

## Method: calibrate the referee's temperature from the federation's labels (`--sure_calib median`)

- Each round, every client fits a temperature T_c on its own pristine data. T_c minimises the mean
  negative log-likelihood of its given labels under P^(1/T), renormalised, over the grid
  T ∈ {0.10, 0.15, ..., 1.00}.
- **Sharpen only:** T ≤ 1, so the referee is never made flatter than CLEAR-FPL's.
- The client reports T_c with its score, as one more number.
- The server takes the median over the round's clients. The next round's referee is P^(1/T),
  renormalised. Round 0 uses T = 1.
- Everything else is unchanged: score `xs_m`, tau 0.05, suspect threshold 0.1, relabel confidence
  0.5, cap 60%, the 50/50 zero-shot mix. All of them now read the calibrated P.

Expected behaviour:
- Pets and Caltech are mildly underconfident, so T should be slightly below 1 and change little.
- On MNIST / EuroSAT, T should be well below 1. Noisy clients' surprise should then rise above tau.

Robustness:
- The median ignores noisy clients while they are fewer than half (the mixed settings).
- When every client is noisy (N settings), noisy labels pull T toward 1. Sharpen-only then makes
  the worst case equal to today's CLEAR-FPL, not worse.
- The median is used only to set the referee's scale. No client's flag depends on other clients'
  scores, so this is not a relative threshold. That family failed earlier because it breaks when
  every client is noisy.

Logged: T_c per client per round and the T in use, in the `sure` record.

## Runs

Same setting as all 10-client runs: FLIP, CLIP RN50, CoOp, FedAvg, 10 clients, Dirichlet 0.1,
8 shots, 50 rounds, 5 seeds, last10. Arm `cal` = CLEAR-FPL + `--sure_calib median`.
- **Stage A, 22 runs:** MNIST and EuroSAT, all 11 settings (`S_<sc>_cal`, `N_<x>_cal`).
- **Stage B, 33 runs, only if stage A passes:** Pets, DTD and Caltech101, all 11 settings.
- Comparators: the existing `S_<sc>_full` / `N_<x>_clear` (CLEAR-FPL) and `D_<sc>_none` / `N_<x>_none`
  (PromptFL) runs, which use the same seeds.
- Before the notebooks: a local smoke on the toy MNIST set.

## Decision rules (fixed now)

Stage A, checked per dataset:
- **A1, flagging restored.** On the 4 mixed settings, rounds 1-50, at least 80% of noisy
  client-rounds are flagged and at most 10% of honest client-rounds.
- **A2, it pays.** Over the 10 noisy settings, the mean of cal − CLEAR-FPL is at least +1 point,
  and no setting is significantly worse than CLEAR-FPL (paired t-test, p < 0.05).
- **A3, clean not hurt.** On S clean, cal − PromptFL is at least −1 point.
- Stage A passes when A1-A3 hold on both datasets.
- If only MNIST passes, stage B still runs, and EuroSAT is reported as a limitation.
- If neither passes, stop; this is reported as a negative result.

Stage B, checked per dataset:
- **B1, no loss.** The mean over the 11 settings of cal − CLEAR-FPL is at least −0.3, and no
  setting is significantly worse by more than 1 point.

Reported, not decided:
- the fitted T per dataset and round, next to the confidence-gap table above;
- R1-R4 of `../mnist_eurosat/plan.md` with `cal` in place of CLEAR-FPL;
- relabel precision, and the share of suspects relabelled.

If A2 fails while A1 passes, the flags work but repair does not. Repair is then the next suspect.

## Overlap check (2026-10-29, web search)

The tool is not new. What could be new is where the failure comes from, and fixing it inside CLEAR.

| idea | already exists | what differs here |
|---|---|---|
| Temperature scaling | Guo et al. 2017, standard | - |
| Temperature scaling when the labels are noisy | ATS (arXiv 1810.11586); NTS; TransTS (Sci. China 2026) fits T together with a noise matrix | they calibrate a classifier on a noisy validation set; here a noise DETECTOR's referee is calibrated, from the training clients' own labels, sharpen-only |
| Calibration in federated learning | FedCal (ICML 2024, arXiv 2405.15458); private federated post-hoc calibration (arXiv 2510.01987) | they aim at calibrated outputs (ECE); here calibration is a means to make a fixed noise threshold transfer across domains |
| Calibrating CLIP, also on EuroSAT | empirical study (arXiv 2402.07417); CoTS label-free T for test-time prompt tuning (arXiv 2609.17386) | no label noise and no federation |
| CLIP as a noisy-label detector | CLIPCleaner (arXiv 2408.10012), DeFT (NeurIPS 2024), NLPrompt (arXiv 2412.01256) | they note "domain gap" only in words; none found measures that the detector fails through UNDERCONFIDENCE rather than wrong predictions |
| Noisy-client detection in FL | FedNoRo (GMM over clients), FedCorr (LID + GMM), Fed-NCL, FedELC | they split clients relative to each other; CLEAR keeps a per-client absolute rule |

Defensible claim: "A CLIP-based noisy-client detector fails on far domains (MNIST, EuroSAT) because
its referee is underconfident, not because CLIP is wrong. Calibrating the referee's temperature from
the federation's labels (median, sharpen-only) restores the detector without per-domain tuning."
The finding is the main contribution; the fix is a small, known tool used in a new place.
Not claimed: a new calibration method.
