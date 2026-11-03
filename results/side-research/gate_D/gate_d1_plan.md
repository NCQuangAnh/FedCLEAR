# Gate D stage 1 plan: which score names the careless clients? (written 2026-10-14, before any run)

Supersedes `gate_V/gate_v_plan.md` (never run): stage 1 logs every candidate score, so one set
of runs compares them all instead of two.

## Why

DBR-FPL's client score is the disagreement `d` with the global model. It mixes two causes:
wrong labels, and images the model is unsure about (look-alike or rare classes). On Pets an
honest client holding american bulldog and pit bull reached d = 0.43, the same as the careless
clients, and was "repaired". MAE matches DBR-FPL's accuracy under symmetric noise (gate Q-MAE),
so the method must earn its place by naming the careless clients reliably, across noise types.
MAE stays a comparator only; it is not part of the method.

## Candidate scores (all logged every round, training unchanged: flcore/diag.py)

Computed by each client on its own data and given labels, from the global prompt (`g`), frozen
zero-shot CLIP (`z`), their average (`e`), and after training from its own prompt (`l`):

| primary candidate | what it is |
|---|---|
| d (old, global) | share of images where the global model's top class is not the label (DBR-FPL now) |
| d_far | same, not counting a top class that is the label's nearest class in CLIP text space |
| loss, global / loss, local | mean cross-entropy of the label: the loss-based detector |
| LID, local | local intrinsic dimension of the local model's outputs: FedCorr's (CVPR 2022) score |
| surprise, global | mean of [-log P(label) - entropy(P)]: surprise beyond what the model expects |
| surprise, global+CLIP | same with P = average of global and zero-shot CLIP |
| surprise, global+CLIP, merged | same, the label merged with its nearest class |
| excess prob, global+CLIP | mean of [sum_k P_k^2 - P(label)], the bounded version |
| share xp > 0.5, global+CLIP | share of images whose excess prob exceeds 0.5 |

Every other logged combination is reported as exploratory.

Verified on CPU before the run: with the scores on, the training log (every client loss and
accuracy, every round accuracy) is identical to the same run with them off.

## Runs (Pets only, 5 seeds, 50 rounds, FLIP protocol, CLIP RN50, 8 shots)

| scenario | careless clients | arms |
|---|---|---|
| `sym` | 3 at 40% symmetric | none, mae, dbr |
| `pair` | 3 at 40% pair flip (next class) | none, mae, dbr |
| `inst` | 3 at ~40% instance-dependent (Xia et al. 2020) | none, mae, dbr |
| `het` | 5 at 16 / 32 / 48 / 64 / 80% symmetric | none, mae, dbr |
| `clean` | none | none, mae, dbr |

`none` = PromptFL (CE), `mae` = PromptFL + MAE, `dbr` = DBR-FPL as in gate Q (`Q_fixconf`).
Five notebooks, one per scenario (`kaggle/gate_d1_pets_<scenario>.ipynb`), runnable in parallel.

## Selection rule, fixed now (coded in `tools/analyze_d1.py`)

1. Per round 10-49 and seed: AUROC of the score at separating clients with damaged labels from
   the rest, in the `none` arm (no intervention, so the score is judged on its own). Mean over
   rounds and seeds, then over the four noisy scenarios.
2. **Winner:** the primary candidate with the highest mean AUROC; ties within 0.01 go to the
   lower false-flag rate (below).
3. Reported with it:
   - an absolute threshold per score = 95th percentile of honest client-rounds in `clean`;
     recall and false-flag rate it gives in each noisy scenario;
   - `het`: Spearman correlation between score and true noise rate (can it rank HOW noisy);
   - the same table on the `dbr` and `mae` arms, and per-image rankings (exploratory).

The winner, its threshold and the image-level ranking go into the stage 2 method, which is then
frozen and run on Pets and on Caltech101 (held out: nothing is tuned on Caltech).

## Checks, fixed now

- **Reproduction:** `D_sym_none`, `D_sym_mae`, `D_sym_dbr` rerun `Q_none`, `Q_mae`, `Q_fixconf`
  with the scores on. Training is unchanged by construction, so each seed should match the
  stored value to within GPU non-determinism (expected exact or < 0.1).
- **What would sink the idea:** if no surprise variant beats `d (old)` by at least 0.02 mean
  AUROC, the "surprise" explanation of the false accusations is wrong and stage 2 keeps `d`
  (or the winner, whatever it is) without claiming H1.

## Addendum (2026-10-15, before any DTD / Caltech run): stage 1 on DTD and Caltech101

The same 15 diagnostic runs (5 scenarios x none / mae / dbr) are added on DTD and Caltech101.
To keep the selection honest, these runs do NOT take part in choosing the score:

- the winner is chosen on Pets alone, by the rule above, once `D_clean` on Pets is rerun;
- DTD and Caltech then serve as a **confirmation** of that choice: the Pets winner must keep a
  mean AUROC within 0.02 of the best primary candidate on each of them, and must beat
  `d (old)` on each. If it fails on either dataset, that is reported and the choice is revisited
  openly (not silently re-picked);
- DTD is the hard case (CLIP ~45-55% zero-shot): it is where "surprise" and plain "loss" are
  expected to separate, and where MAE may underfit.

Stage 2 (the frozen method) still runs on all three datasets afterwards.
