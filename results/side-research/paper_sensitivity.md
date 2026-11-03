# Offline checks for the paper (tools/paper_sensitivity.py)

## tau: share of client-rounds flagged (scenario 1, basic repair, rounds 10-50)

| dataset | clients | tau=0.0 | tau=0.025 | tau=0.05 | tau=0.1 | tau=0.2 | tau=0.5 |
|---|---|---|---|---|---|---|---|
| Pets | clean | 11.6% | 9.6% | 7.5% | 2.8% | 1.6% | 0.0% |
| Pets | noisy | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| Caltech101 | clean | 0.2% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| Caltech101 | noisy | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| DTD | clean | 4.7% | 4.6% | 4.4% | 4.0% | 2.8% | 0.1% |
| DTD | noisy | 98.8% | 98.7% | 98.6% | 98.4% | 97.0% | 86.8% |
| MNIST | clean | 0.2% | 0.1% | 0.1% | 0.1% | 0.0% | 0.0% |
| MNIST | noisy | 43.6% | 41.7% | 40.0% | 37.7% | 27.7% | 9.9% |
| EuroSAT | clean | 11.9% | 10.6% | 9.8% | 8.8% | 7.3% | 3.1% |
| EuroSAT | noisy | 45.6% | 43.5% | 42.2% | 40.7% | 34.1% | 8.3% |

## gate: decisions replayed on the basic-repair runs (11 settings x 5 seeds per dataset)

| dataset | open, R_g=5, g=0.12 | open R_g=3 | open R_g=10 | same decision as R_g=5 (R_g=3 / 10) | open g=0.06 | open g=0.09 | open g=0.12 | open g=0.15 | open g=0.18 |
|---|---|---|---|---|---|---|---|---|---|
| Pets | 53/55 | 54/55 | 53/55 | 54/55 / 55/55 | 54/55 | 54/55 | 53/55 | 52/55 | 52/55 |
| Caltech101 | 50/55 | 50/55 | 50/55 | 55/55 / 55/55 | 50/55 | 50/55 | 50/55 | 50/55 | 50/55 |
| DTD | 47/55 | 40/55 | 48/55 | 48/55 / 54/55 | 54/55 | 48/55 | 47/55 | 39/55 | 29/55 |
| MNIST | 5/55 | 5/55 | 6/55 | 55/55 / 54/55 | 7/55 | 6/55 | 5/55 | 4/55 | 2/55 |
| EuroSAT | 1/55 | 1/55 | 1/55 | 55/55 / 55/55 | 7/55 | 3/55 | 1/55 | 1/55 | 0/55 |

All datasets: same decision with R_g=3 in 267/275 runs, with R_g=10 in 273/275.

## gamma: flagged client-rounds whose suspects reached the 60% cap (basic repair, rounds 1-50)

| dataset | scenario 1 | scenario 2 |
|---|---|---|
| Pets | 11.9% of 4189 | 34.6% of 15000 |
| Caltech101 | 14.3% of 3501 | 33.2% of 15000 |
| DTD | 54.5% of 3928 | 72.6% of 14763 |
| MNIST | 44.0% of 1283 | 59.9% of 4999 |
| EuroSAT | 59.9% of 2691 | 56.0% of 9118 |

## eps: the frozen estimate eps0 vs the estimate at round 50 vs the true rate (gatef, scenario 2, gate open)

| dataset | setting | true noise | eps0 (first calibrated round) | eps at round 50 |
|---|---|---|---|---|
| Pets | N sym25 | 0.25 | 0.27 | 0.28 |
| Pets | N sym50 | 0.50 | 0.52 | 0.52 |
| Pets | N sym75 | 0.75 | 0.75 | 0.76 |
| Pets | N pair25 | 0.25 | 0.25 | 0.26 |
| Pets | N pair50 | 0.50 | 0.49 | 0.50 |
| Pets | N pair75 | 0.75 | 0.72 | 0.72 |
| Caltech101 | N sym25 | 0.25 | 0.25 | 0.26 |
| Caltech101 | N sym50 | 0.50 | 0.51 | 0.52 |
| Caltech101 | N sym75 | 0.75 | 0.75 | 0.76 |
| Caltech101 | N pair25 | 0.25 | 0.25 | 0.25 |
| Caltech101 | N pair50 | 0.50 | 0.48 | 0.49 |
| Caltech101 | N pair75 | 0.75 | 0.70 | 0.72 |
| DTD | N sym25 | 0.25 | 0.27 | 0.33 |
| DTD | N sym50 | 0.50 | 0.51 | 0.56 |
| DTD | N sym75 | 0.75 | 0.77 | 0.81 |
| DTD | N pair25 | 0.25 | 0.26 | 0.29 |
| DTD | N pair50 | 0.50 | 0.52 | 0.57 |
| DTD | N pair75 | 0.75 | 0.78 | 0.81 |

## stats: per-seed average over the settings, mean +- sd over 5 seeds; FedCLEAR vs each baseline, paired t-test over seeds (difference, p, seeds won)

| dataset | scenario | PromptFL | FedProx | FedCorr | NLPrompt | FedRG | FedCLEAR |
|---|---|---|---|---|---|---|---|
| Pets | 1 | 81.1$\pm$2.3 (+6.7, p=0.004, 5/5) | 81.5$\pm$2.3 (+6.4, p=0.004, 5/5) | 80.5$\pm$1.4 (+7.4, p=0.000, 5/5) | 87.8$\pm$0.4 (+0.0, p=0.767, 2/5) | 87.2$\pm$0.3 (+0.6, p=0.037, 5/5) | 87.8$\pm$0.3 |
| Caltech101 | 1 | 87.1$\pm$0.5 (+2.7, p=0.001, 5/5) | 87.3$\pm$0.6 (+2.5, p=0.004, 5/5) | 88.3$\pm$0.9 (+1.6, p=0.048, 5/5) | 89.5$\pm$0.6 (+0.3, p=0.376, 2/5) | 89.7$\pm$0.5 (+0.2, p=0.424, 3/5) | 89.8$\pm$0.5 |
| MNIST | 1 | 62.0$\pm$2.9 (+1.3, p=0.340, 3/5) | 62.4$\pm$2.6 (+0.9, p=0.264, 3/5) | 59.9$\pm$2.8 (+3.4, p=0.022, 5/5) | 54.4$\pm$5.5 (+8.8, p=0.007, 5/5) | 58.2$\pm$4.3 (+5.0, p=0.022, 5/5) | 63.2$\pm$2.6 |
| DTD | 1 | 51.6$\pm$1.2 (+2.4, p=0.015, 5/5) | 51.4$\pm$0.9 (+2.6, p=0.014, 5/5) | 47.5$\pm$2.1 (+6.5, p=0.001, 5/5) | 48.5$\pm$1.4 (+5.5, p=0.000, 5/5) | 52.4$\pm$2.0 (+1.6, p=0.105, 4/5) | 54.0$\pm$0.8 |
| EuroSAT | 1 | 59.5$\pm$2.9 (+0.6, p=0.636, 3/5) | 58.2$\pm$2.9 (+1.9, p=0.260, 3/5) | 44.9$\pm$12.4 (+15.2, p=0.041, 5/5) | 49.2$\pm$5.0 (+10.9, p=0.000, 5/5) | 57.6$\pm$5.7 (+2.5, p=0.205, 3/5) | 60.1$\pm$3.9 |
| Pets | 2 | 56.0$\pm$2.3 (+30.2, p=0.000, 5/5) | 56.5$\pm$2.8 (+29.7, p=0.000, 5/5) | 63.0$\pm$3.2 (+23.2, p=0.000, 5/5) | 83.8$\pm$2.0 (+2.4, p=0.024, 5/5) | 82.7$\pm$1.7 (+3.5, p=0.004, 5/5) | 86.2$\pm$0.7 |
| Caltech101 | 2 | 68.2$\pm$2.6 (+19.4, p=0.000, 5/5) | 67.4$\pm$3.0 (+20.1, p=0.000, 5/5) | 73.5$\pm$2.8 (+14.0, p=0.000, 5/5) | 87.1$\pm$1.4 (+0.4, p=0.435, 2/5) | 87.8$\pm$0.7 (-0.3, p=0.622, 1/5) | 87.5$\pm$1.5 |
| MNIST | 2 | 47.3$\pm$2.3 (+2.5, p=0.161, 3/5) | 47.3$\pm$2.3 (+2.5, p=0.161, 3/5) | 43.2$\pm$6.4 (+6.5, p=0.128, 4/5) | 41.2$\pm$5.7 (+8.6, p=0.084, 4/5) | 42.7$\pm$1.6 (+7.0, p=0.036, 5/5) | 49.7$\pm$5.4 |
| DTD | 2 | 34.1$\pm$1.4 (+12.1, p=0.000, 5/5) | 34.2$\pm$1.7 (+12.0, p=0.000, 5/5) | 35.7$\pm$1.1 (+10.5, p=0.000, 5/5) | 42.8$\pm$1.4 (+3.5, p=0.001, 5/5) | 45.8$\pm$1.1 (+0.4, p=0.381, 4/5) | 46.2$\pm$0.8 |
| EuroSAT | 2 | 36.6$\pm$2.1 (+3.8, p=0.038, 4/5) | 36.6$\pm$2.1 (+3.8, p=0.038, 4/5) | 35.2$\pm$4.2 (+5.2, p=0.030, 5/5) | 35.1$\pm$3.7 (+5.3, p=0.016, 5/5) | 37.3$\pm$4.1 (+3.2, p=0.115, 4/5) | 40.4$\pm$2.2 |

## cost: per run, FedCLEAR (gatef) vs FedRG on the same Kaggle notebooks (MNIST, EuroSAT)

| dataset | method | runs | wall s / round | slowest client s / round | peak GPU MB |
|---|---|---|---|---|---|
| MNIST | FedRG | 55 | 10.03 | 0.65 | 1260 |
| MNIST | FedCLEAR | 25 | 9.79 | 0.61 | 4790 |
| EuroSAT | FedRG | 55 | 6.91 | 0.60 | 1260 |
| EuroSAT | FedCLEAR | 55 | 5.87 | 0.48 | 4793 |

## delta: basic suspect rule replayed on stage 0 (PromptFL reference, rounds 10-50, 3 seeds)

| dataset | delta=0.05: recall / suspect precision / correct marked / relabel precision | delta=0.1: recall / suspect precision / correct marked / relabel precision | delta=0.2: recall / suspect precision / correct marked / relabel precision | delta=0.3: recall / suspect precision / correct marked / relabel precision |
|---|---|---|---|---|
| Pets | 81% / 99% / 0.1% / 88% | 85% / 98% / 0.3% / 87% | 88% / 93% / 0.9% / 85% | 90% / 87% / 2.0% / 83% |
| Caltech101 | 90% / 96% / 0.5% / 92% | 91% / 94% / 0.8% / 91% | 92% / 90% / 1.3% / 90% | 93% / 87% / 2.0% / 89% |
| DTD | 75% / 81% / 2.3% / 82% | 79% / 73% / 3.7% / 80% | 81% / 70% / 4.4% / 79% | 81% / 70% / 4.5% / 79% |
| MNIST | 11% / 97% / 0.1% / 98% | 24% / 81% / 1.7% / 98% | 29% / 74% / 3.2% / 98% | 29% / 74% / 3.2% / 98% |
| EuroSAT | 12% / 85% / 0.7% / 96% | 29% / 73% / 3.3% / 98% | 33% / 63% / 6.0% / 92% | 33% / 63% / 6.1% / 92% |

## clip: client flags identical to clip=10 (stage 0)

| dataset | clip 5 | clip 20 | no clip |
|---|---|---|---|
| Pets | 99.4% | 100.0% | 100.0% |
| Caltech101 | 99.7% | 100.0% | 100.0% |
| DTD | 100.0% | 100.0% | 100.0% |
| MNIST | 100.0% | 100.0% | 100.0% |
| EuroSAT | 100.0% | 100.0% | 100.0% |

## merge: client flags at tau=0.05 and AUROC, with and without the look-alike merge (stage 0)

| dataset | merge: clean flagged / noisy flagged / AUROC | no merge: clean flagged / noisy flagged / AUROC |
|---|---|---|
| Pets | 1.4% / 91.6% / 0.988 | 0.3% / 91.6% / 0.987 |
| Caltech101 | 0.0% / 96.0% / 0.994 | 0.0% / 95.6% / 0.992 |
| DTD | 0.4% / 84.5% / 0.996 | 0.0% / 83.5% / 0.996 |
| MNIST | 0.0% / 33.8% / 0.880 | 0.0% / 33.6% / 0.900 |
| EuroSAT | 3.1% / 44.4% / 0.857 | 3.6% / 36.7% / 0.875 |
