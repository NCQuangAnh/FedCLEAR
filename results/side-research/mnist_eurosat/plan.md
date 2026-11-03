# MNIST + EuroSAT study: plan (written 2026-10-28, before any run)

Question, from the supervisor: CLIP was trained on natural photos, so on natural-image test sets
(Pets, DTD, Caltech) it is stable even with noisy labels. What happens on images far from CLIP's
photos? Two datasets, both 10 classes:
- MNIST: handwritten digits, grey, 28x28. Not a standard prompt-learning benchmark; used here as a
  stress test where CLIP's prior knowledge is weak. Run first, as the supervisor asked.
- EuroSAT: satellite land-use images. One of CoOp's 11 standard datasets, also weak for zero-shot CLIP.

Claim to test: on such data, methods need training (prompt learning), and handling label noise
matters more, because CLIP alone cannot cover for the bad labels.

## Setup
Identical to the 10-client runs on Pets / DTD / Caltech (FLIP, CLIP RN50, CoOp, 10 clients,
Dirichlet 0.1, 8 shots, 50 rounds, 5 seeds, last10). Same arms, same flags, same seeds:

| setting | noisy clients | noise per noisy client |
|---|---|---|
| S_sym / S_pair / S_inst | 3 of 10 | 40% |
| S_het | 5 of 10 | 16, 32, 48, 64, 80% |
| S_clean | 0 | 0 |
| N_sym25 ... N_pair75 | 10 of 10 | 25 / 50 / 75% |

- CLEAR-FPL: `S_<sc>_full`, `N_<x>_clear`. Queue `server/queue_mnist_eurosat.txt`, 22 runs.
- PromptFL: `D_<sc>_none`, `N_<x>_none`, plus `S_clean_zs` (zero-shot CLIP, no training).
  Queue `server/queue_mnist_eurosat_promptfl.txt`, 23 runs (EuroSAT zero-shot already known:
  26.11%, results/Phase4/food101-eurosat, RN50, same template).
- Runs on Kaggle (2026-10-28 decision): notebooks `kaggle/{mnist,eurosat}_{clear,promptfl}.ipynb`,
  same arms. The server queues hold the same runs as a fallback.

Data (`server/prep_mnist_eurosat.py`, run once before the queues):
- MNIST (`flip/flcore/datasets/mnist.py`): test = official 10k, val = 10% of the official train set
  (seed 0), train = the other 54k. Class names 0-9, CLIP's template `a photo of the number: "{}".`
- EuroSAT: Zenodo 7711810 RGB archive, FLIP's own 80/10/10 split with seed 0
  (21600 / 2700 / 2700). Template `a centered satellite photo of {}.`

## Decision rules (fixed now), checked per dataset
- R1, gain kept: CLEAR-FPL minus PromptFL, averaged over the 10 noisy settings, is above 0, and
  CLEAR wins with paired t-test p < 0.05 over 5 seeds in at least 5 of the 10 noisy settings.
- R2, clean not hurt: on S_clean, CLEAR is not below PromptFL by more than 1 point.
- R3, client detection: client-level AUROC at the first check, over the 4 mixed settings, is at
  least 0.90.
- R4, training is needed: on S_clean, PromptFL is at least 10 points above zero-shot CLIP.
- Reported, not decided:
  - the noise drop (PromptFL S_clean minus each noisy setting) next to the same drop on
    Pets / DTD / Caltech. This is the supervisor's "natural images stay stable" point;
  - the CLEAR gain next to the gain on Pets / DTD / Caltech.

If a rule fails: report which one and where, as a limitation. The first thing to check is whether
zero-shot CLIP is too weak for CLEAR's image check, since CLEAR mixes zero-shot CLIP into it.

## Diagnostic follow-up (written 2026-10-28, after results.md, before these runs)

`results.md` shows CLEAR under-flags on both datasets. Noisy clients' median score stays below
tau = 0.05 (MNIST -0.07, EuroSAT -0.05 at round 50), so only 37% / 44% of noisy client-rounds are
flagged. The question is which CLIP use shrinks the score. There are 16 runs, the 4 mixed settings
(sym / pair / inst / het) x 2 datasets x 2 switches, 5 seeds, on Kaggle:
- `S_<sc>_noclip` (`kaggle/{mnist,eurosat}_noclip.ipynb`): referee = global prompt only, no
  zero-shot CLIP (`--sure_dist g`, tau 0.072). This is the same arm as gate D2 on Pets / DTD /
  Caltech, so a natural-image reference exists.
- `S_<sc>_nomerge` (`kaggle/{mnist,eurosat}_nomerge.ipynb`): no look-alike merge from CLIP's text
  space (`--sure_score xs`, tau 0.072 = its own Pets clean p95, the same rule as every tau).
Comparator: the existing `S_<sc>_full` and `D_<sc>_none` runs (same seeds, same flags otherwise).

Rules, per dataset and per switch, pooled over the 4 mixed settings, rounds 1-50:
- C1, the switch is the cause of under-flagging: the noisy-client flag rate rises by at least 20
  points over `full`, while the honest-client flag rate stays at or below 10%.
- C2, it pays off: the mean of the 4 paired accuracy differences switch − full is above 0.
- Reported: relabel precision, honest flag rate, AUROC first/last round, switch − PromptFL.
Reading: if C1 holds for `noclip`, the CLIP mix in the referee (point 1) is the cause, and Step 2
(adaptive CLIP trust) is the right fix. If it holds for `nomerge`, point 2 is the cause (side fix A).
If C1 holds for neither, the fixed threshold itself (point 4) is the cause, and a self-calibrating
flag rule should come before adaptive CLIP trust.
