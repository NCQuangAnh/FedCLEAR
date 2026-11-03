# Gate Q-MAE results (run 2026-10-14, Kaggle, 5 seeds, last10)

Plan: `gate_q_mae_plan.md` (written before the run). Setting: 7 honest + 3 careless clients (40%
symmetric noise), FLIP protocol, CLIP RN50, 8 shots, 50 rounds. `Q_mae` = PromptFL with the MAE loss
(the loss NLPrompt builds on, not the full NLPrompt). References `Q_none`, `Q_filter`, `Q_fixconf`
(= DBR-FPL), `K_restore` (10 clean clients, ceiling) are the stored runs, same seeds.

| | Q_none | Q_filter | DBR-FPL | **PromptFL + MAE** | MAE + DBR-FPL | ceiling |
|---|---|---|---|---|---|---|
| OxfordPets | 80.46 ± 2.83 | 86.97 ± 0.61 | 86.87 ± 1.63 | **88.12 ± 0.39** | 85.52 ± 3.12 | 87.88 ± 0.49 |
| Caltech101 | 87.79 ± 0.43 | 89.61 ± 0.77 | 89.77 ± 0.60 | **89.79 ± 0.36** | 89.70 ± 0.28 | 90.21 ± 0.46 |
| gap closed Pets / Caltech | 0 / 0 | 88% / 75% | 86% / 82% | **103% / 83%** | 68% / 79% | 100% |

Paired differences (t-test, wins out of 5):

| | Pets | Caltech |
|---|---|---|
| DBR-FPL − MAE (criterion 1) | −1.25, p = 0.176, 1/5 | −0.01, p = 0.969, 3/5 |
| MAE − Q_none | +7.65, p = 0.004, 5/5 | +2.00, p = 0.001, 5/5 |
| MAE + DBR-FPL − DBR-FPL | −1.36, p = 0.425, 2/5 | −0.07, p = 0.792, 2/5 |
| MAE + DBR-FPL − MAE | −2.60, p = 0.114, 0/5 | −0.09, p = 0.337, 1/5 |
| Q_filter − MAE | −1.15, p = 0.015, 0/5 | −0.17, p = 0.667, 2/5 |
| ceiling − MAE | −0.24, p = 0.118, 2/5 | +0.42, p = 0.145, 3/5 |

Convergence (5-seed mean curve, rounds to 98% / 99% of the ceiling; DBR-FPL from the gate Q analysis):
Pets MAE 7 / 10, MAE + DBR-FPL 7 / never, DBR-FPL 11 / -; Caltech MAE 9 / 21, MAE + DBR-FPL 9 / 25,
DBR-FPL 5 / -. Time per round is not compared with the stored arms: this session ran on a different
machine (Q_mae 10.9 s on Pets against 13.3 s for the stored Q_none), and MAE costs the same as CE.

## Verdict

**Criterion 1 fails.** DBR-FPL does not beat PromptFL + MAE: it is lower on Pets (−1.25, not
significant, 1 win in 5) and equal on Caltech. As written in the plan, the thesis must say that a
one-line loss change does as well as the filter in this setting (7 + 3 careless clients, 40%
symmetric noise); on Pets MAE alone reaches the ceiling.

Further observations:
- The expectation in the plan (MAE underfits Caltech's 100 classes) was wrong: MAE closes 83% of the gap there.
- MAE and DBR-FPL do not combine: the combination is lower than either alone on Pets. One seed (4)
  collapses to 80.3 and stays there for the last 15 rounds; the other four seeds are 85.0-88.0.
  A likely reason, not checked: under MAE the confident images dominate even less, so the
  disagreement d and the confidence ranking that drive the filter change.
- MAE is also the most stable arm (sd 0.39 Pets, 0.36 Caltech).
- DBR-FPL's remaining claims must rest on what MAE does not cover: the data-poisoning attackers
  (gate K), asymmetric or class-dependent noise, and the per-client report of who is noisy. None of
  these has been tested against MAE yet.
