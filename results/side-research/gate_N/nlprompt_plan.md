# NLPrompt as a comparator (written 2026-10-19, before any run)

## What is run

NLPrompt (Pan et al., CVPR 2025) on every client, following the official code
(github.com/qunovo/NLPrompt) with its default settings: before each local epoch (= each round)
an OT split of the client's data, using the current prompt's prediction, Sinkhorn with entropy
0.01 and cost −log_softmax(prob); samples whose OT pseudo label equals their label train with CE,
the rest with 1 − p(label) (their GCE with q = 1). Code: flip/flcore/nlprompt.py.

Two variants, because NLPrompt's uniform class marginal assumes every class is equally present,
which a Dirichlet-0.1 client never satisfies:
- `nlp`: uniform class marginal, as published;
- `nlph`: the client's own label histogram as class marginal (the natural federated version).

Federated adaptation: one local epoch mixes CE and MAE per sample. The official code instead runs
one pass over the clean subset and then one over the noisy subset.

## Runs (5 seeds, Pets / DTD / Caltech101)

- Gate D scenarios (sym, pair, inst, het, clean): `S_<sc>_nlp`, `S_<sc>_nlph`. These are paired
  with CLEAR-FPL `S_<sc>_full` (same flags apart from the method).
- Gate N scenarios (all clients noisy, sym / pair x 25 / 50 / 75%): `N_<noise><rate>_nlp`,
  `N_<noise><rate>_nlph`.

## Criteria, fixed now

For each combo, take the better of the two NLPrompt variants (the stronger competitor).
- **Gate D noisy combos (12):** CLEAR − best NLPrompt ≥ −0.5 in at least 9 of 12.
- **Gate N at 25% and 50% (12):** CLEAR − best NLPrompt ≥ −0.5 in at least 9 of 12.
- **Clean (3 datasets):** reported.

Reported, not judged:
- the OT split's precision and recall against the true noise (`nlp` records);
- uniform vs histogram marginal.
