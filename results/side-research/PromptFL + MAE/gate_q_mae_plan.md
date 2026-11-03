# Gate Q-MAE plan: a robust-loss competitor in the same setting (written 2026-10-14, before any run)

## Why

DBR-FPL has so far been compared only with doing nothing (`Q_none`) and with its own filter-only
variant (`Q_filter`). A thesis needs at least one existing idea run in the same setting. The
cheapest and most cited one for noisy prompt learning is to change the loss: MAE (mean absolute
error between the softmax and the one-hot label) is bounded, so a wrong label cannot dominate the
gradient the way it does under cross-entropy. MAE is the robust loss NLPrompt (CVPR 2025) builds
on. This gate runs MAE alone, which is **not** the full NLPrompt method (NLPrompt also purifies
the data with optimal transport); the thesis must call it "PromptFL + MAE", not "NLPrompt".

## Arms (`MODE = "gate_q_noise"`, 7 honest + 3 careless at 40% symmetric noise, seeds 0-4)

| Arm | What |
|---|---|
| `Q_mae` | PromptFL with the MAE loss instead of CE, no filter (`--loss_type mae`) |
| `Q_mae_fixconf` | DBR-FPL with the MAE loss: do the two combine? |
| references, stored | `Q_none` (CE, no filter), `Q_filter`, `Q_fixconf` (= DBR-FPL), `K_restore` (ceiling) |

Pets and Caltech in one session (~8 h). Same seeds, so every comparison is paired.

## Criteria, fixed now

1. **DBR-FPL beats the robust-loss competitor:** `Q_fixconf − Q_mae` > 0 on both datasets, and
   significant (paired t-test p < 0.05) on at least one.
2. **Reported, not judged:**
   - `Q_mae − Q_none`: does MAE alone help in few-shot federated prompt learning;
   - `Q_mae_fixconf − Q_fixconf`: does MAE add anything on top of DBR-FPL;
   - the share of the gap closed by each arm, the convergence (rounds to 98% of the ceiling) and
     the time per round, as in the gate Q analysis.

If criterion 1 fails (MAE alone matches or beats DBR-FPL), the thesis must say that a one-line loss
change does as well as the filter in this setting, and DBR-FPL's claim then rests on the case with
data-poisoning attackers (gate K) and on its relabelling.

Expectation, written before the run: MAE is known to learn slowly when the number of classes is
large (its gradient vanishes on hard examples), so it may underfit Caltech's 100 classes in 50
rounds.
