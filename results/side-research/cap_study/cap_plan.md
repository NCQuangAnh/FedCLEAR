# Cap study: drop the 60% repair cap, test the 0.1 suspect threshold (pre-registered 2026-10-25)

## Why

CLEAR-FPL repairs a flagged client by treating images with P(label) < 0.1 as suspects, touching at
most 60% of the client's images. Both numbers were set by hand in gate_d2_plan.md, with no
justification and no ablation.

What the logs show:
- **Gate N 75%:** the cap binds in 93-100% of flagged client-rounds. Suspects are 96-100% truly
  noisy, yet only 75-79% of the noise is caught, because the cap allows at most 60/75 = 80%.
  This is the likely cause of the 75% losses to MAE and NLPrompt.
- **Gate D het:** the cap binds in 40-67% of rounds, on the 64% and 80% clients.
- **Offline replay** on PromptFL per-image logs (gate D, all datasets):
  - removing the cap changes nothing outside het;
  - the threshold 0.1 touches about 3% of correct images on Pets and Caltech, but about 25% on DTD.

## Arms

5 seeds, 50 rounds, FLIP protocol, the same seeds and flags as `S_<sc>_full` and `N_<x>_clear`. Only
the repair parameters change.

| arm | `--sure_max_frac` | `--sure_img_thr` |
|---|---|---|
| `nc` | 1.0 | 0.1 |
| `nc05` | 1.0 | 0.05 |
| `nc20` | 1.0 | 0.2 |

Each arm covers 11 settings: S_sym, S_pair, S_inst, S_het, S_clean, plus N_sym and N_pair at 25, 50
and 75. That is run on Pets and DTD, 66 runs in total, in notebooks `kaggle/cap_{pets,dtd}_{1..4}`.
Reference: the current CLEAR-FPL (`S_<sc>_full`, `N_<x>_clear`), paired by seed.

## Decision rules (fixed before any run)

1. **Drop the cap** (adopt `nc`) if, on both Pets and DTD:
   - the mean over N_sym75 and N_pair75 rises by more than 0.5 over CLEAR-FPL; and
   - the mean over the other 9 settings drops by no more than 0.3.

   Otherwise the cap stays and is reported as a limitation, with this study as its ablation.
2. **Threshold sensitivity** (among the no-cap arms, compared over the 11-setting mean, per dataset):
   - all three thresholds within 1.0 of each other on both datasets: report "insensitive", keep 0.1;
   - otherwise pick the best threshold on Pets and confirm it on DTD, the way τ was fixed. It is
     confirmed if it is not worse than 0.1 on DTD by more than 0.3; otherwise keep 0.1.
3. **Next step:** the chosen variant becomes CLEAR-FPL. Its 11 Caltech runs go to the server queue
   after FedProx, and the comparison tables are redone.

## Also reported (no decision attached)

Per arm, from the `sure` records over rounds 10-49:
- share of noise caught;
- share of correct images touched;
- relabels that fix a label against relabels that break one;
- false flag rate.
