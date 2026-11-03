# Offline idea screening (2026-10-25)

## Data and limits

**Data:** the per-image logs of the gate D stage 1 PromptFL runs (`D_<sc>_none`, 5 seeds, logged every 5 rounds, rounds 25-45). Each image row has the given label, the true label, and for three sources the probability of the given label, the argmax, the max probability, the entropy and Σp². The sources are:
- g: the global prompt;
- z: zero-shot CLIP with the dataset template;
- e: ½(g+z), the distribution CLEAR uses.

**Limits:**
- The global model in these runs had no repair, so this is a screen, not a result.
- No per-image logs exist at 75% noise (the gate N runs did not log them).

**Scripts:** `scripts/a2.py` … `a7.py`. Run them from the repo root.

## Estimator

Symmetric-noise moment estimator of a client's noise rate:

ρ̂ = (S − P̄) / (S − (1 − S)/(K − 1)), where S = mean Σ_k p_k² and P̄ = mean p(label).

- It has no tuned parameter.
- It is unbiased when the source is calibrated in the sense E[p_Y] = E[Σp²].
- The standard error comes from the per-image terms, and the flag is a one-sided z-test at 5%.

## Results

### F1. Calibration, not accuracy, makes a good noise auditor (a1, a3)

| | zero-shot acc / mean conf | global acc (r45) / mean conf | ρ̂ error (MAE), zero-shot | ρ̂ error (MAE), global |
|---|---|---|---|---|
| Pets | 0.81 / 0.76 | 0.85 / 0.64 | 0.05-0.07 | 0.14-0.35 |
| DTD | 0.41 / 0.39 | 0.66 / 0.53 | 0.08-0.11 | 0.17-0.31 |
| Caltech | 0.82 / 0.81 | 0.88 / 0.80 | 0.02-0.03 | 0.03-0.23 |

On DTD, zero-shot CLIP is right only 41% of the time, yet it estimates each client's noise rate to within about 0.1, with no training, no clean data and no other clients. The global model is more accurate but a worse auditor.

Z-test flag rates (honest clients / noisy clients):

| | audit | CLEAR's `e.xs_m > 0.05` |
|---|---|---|
| Pets | 0.00 / 0.84-1.00 | 0.00-0.04 / 0.87-1.00 |
| DTD | 0.02-0.04 / 0.67-0.87 | 0.00-0.01 / 0.69-0.96 |
| Caltech | 0.00 / 0.96-1.00 | 0.00 / 0.93-1.00 |

The audit's honest flag rate stays at or below the nominal 5%.

### F2. Noise in the federation makes the federated referee underconfident, honest clients included (a7)

ρ̂ on honest clients (true value 0):

| | clean | sym | pair | het |
|---|---|---|---|---|
| Pets, g / e / z | −0.06 / −0.08 / −0.05 | −0.20 / −0.17 / −0.06 | −0.14 / −0.14 / −0.06 | −0.39 / −0.27 / −0.06 |
| DTD, g / e / z | −0.09 / −0.31 / −0.04 | −0.19 / −0.31 / −0.03 | −0.15 / −0.31 / −0.03 | −0.32 / −0.38 / −0.01 |
| Caltech, g / e / z | −0.03 / −0.06 / −0.02 | −0.13 / −0.10 / −0.02 | −0.11 / −0.09 / −0.02 | −0.23 / −0.15 / −0.02 |

- The global model's bias grows with the amount of noise in the federation, while zero-shot stays flat.
- The ½ mix is badly underconfident on DTD even when every client is clean. Averaging two sources that disagree flattens P.
- This explains why CLEAR touches about 25% of correct DTD images with the 0.1 threshold, and why the stage 3 "budget" failed: its expected count came from the underconfident mix.
- FedNoiL saw "early" underconfidence of the global model and patched it with a softmax temperature. Here the bias does not fade with rounds; it scales with the federation's noise.

### F3. Consensus capture under systematic noise (a2, a6)

Share of noisy images whose wrong (pair) label the global model predicts, by the share of the true class that the noisy client holds:
- DTD: 0.04 / 0.07 / 0.15 / 0.17 for 0-25 / 25-50 / 50-75 / 75-100%;
- Caltech: 0.01 / 0.02 / 0.04 / 0.07;
- Pets: 0.14 / 0.07 / 0.24 / 0.19.

Under symmetric noise there is no such trend, and zero-shot never adopts the wrong label (0.00-0.04).

Per-image ranking inside noisy clients (AUROC):

| | z | g | e |
|---|---|---|---|
| Pets pair | 0.99 | 0.92 | 0.97 |
| DTD pair | 0.93 | 0.87 | 0.90 |
| Pets sym | 0.99 | 0.99 | 0.99 |
| DTD sym | 0.93 | 0.93 | 0.94 |

Systematic noise contaminates the federation's own referee; random noise does not. This was measured at 40% on 3 clients. At pair 50-75% on every client it should be much stronger, but that is not yet measured.

### Repair simulation (a5)

Rule: budget = round(ρ̂·n) of the least plausible images, relabel to the mix argmax if its top probability is at least 0.5, otherwise drop.

- The training set after repair is about as clean as with CLEAR.
- In het it is better than CLEAR with the cap, for example Caltech wrong labels left 19 against 35.
- On DTD sym/inst it keeps more correct images but leaves more wrong ones.

Relabel accuracy when the source is at least 50% sure:
- e: 0.85-0.92;
- z: 0.75-0.89;
- g: 0.70-0.90.

## Rejected

- **Bayes EM with a uniform noise likelihood:** ρ underestimated, catches only 30-86% of the noise.
- **Threshold calibrated on honest clients:** this is federated conformal prediction, and it has no reference when every client is noisy.
- **Triangulation (z = g ≠ label):** recall 0.40-0.80.
- **Ownership-weighted z/g mix:** ranks worse than e.
