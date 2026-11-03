# Baselines asked by the supervisor (2026-10-25)

| group | baseline | status |
|---|---|---|
| Standard FL | FedAvg + CoOp | = PromptFL, already run in every scenario (`D_<sc>_none`, `N_<x>_none`) |
| Standard FL | FedProx + CoOp | done 2026-10-26 (`server/queue_baselines.txt`); result below |
| Noise-resilient FL | FedCorr + CoOp | implemented 2026-10-26, server queue `server/queue_fedcorr.txt`; plan `../fedcorr/fedcorr_plan.md` |
| Noise-resilient FL | FedLNL + CoOp | to confirm which paper is meant |
| Prompt FL | FedTP | to confirm which paper is meant |

## FedProx + CoOp

PromptFL with the FedProx proximal term (Li et al., MLSys 2020) on the learnable prompt: each
local step adds (mu / 2) * ||P − P_global||^2 to the loss (`--prox_mu`, flip/flcore/clients/
client_fedavg.py `_prox`). mu = 0.01, the value commonly used for prompt-FL baselines; fixed
before the run, not tuned. Same FLIP setting and seeds as every other arm, so it pairs with
PromptFL, MAE, NLPrompt and CLEAR-FPL.

Runs: Pets, DTD, Caltech101; the five gate D scenarios (`S_<sc>_prox`) and every-client-noisy
sym / pair at 25 / 50 / 75% (`N_<x>_prox`); 33 runs, 5 seeds each.

Reported, not judged: FedProx is a heterogeneity method with no label-noise handling, so it is
expected near PromptFL under noise.

### Result (2026-10-26)

All 33 runs finished (server, 33.8 GPU-hours). Full tables are in `baselines_results.md`, made by `python tools/analyze_baselines.py`. The FedProx column is also in `DTD_comparison.md` and `Pets_Caltech_comparison.md`.

**FedProx is PromptFL under noise, as expected.**

Mean over the 11 settings:

| | PromptFL | FedProx |
|---|---|---|
| Pets | 67.44 | 67.84 |
| DTD | 42.09 | 42.04 |
| Caltech | 76.77 | 76.47 |

- Paired differences with PromptFL lie within ±0.9 in 31 of the 33 settings. The other two are Caltech N_pair50 −2.25 (p = 0.11) and N_pair75 −2.30 (p = 0.033).
- Only two differences are significant, and both are losses:
  - Pets S_inst: −0.90 (p = 0.008);
  - Caltech N_pair75: −2.30 (p = 0.033).
- The proximal term handles client drift. It does nothing against wrong labels.

**CLEAR-FPL − FedProx (paired over 5 seeds):**
- Positive and significant (p < 0.05) in 26 of the 33 settings: every noisy setting on Pets and Caltech, and on DTD S_pair, S_het, N_sym50/75 and N_pair50/75.
- Not significant in the other 7:
  - the three clean federations: Pets +0.05, DTD −0.69, Caltech +0.08;
  - DTD S_sym +2.10, S_inst +0.84, N_sym25 −0.94, N_pair25 +0.68.

## FedProx on MNIST and EuroSAT (set up 2026-10-31)

The user asked for this so that MNIST and EuroSAT get the same baseline columns as Pets, DTD and Caltech101.

**Runs.** Arms `S_<sc>_prox` and `N_<x>_prox` are unchanged: mu = 0.01, the same args as the 33 runs above. They cover the same 11 settings, 5 seeds each, and the same seeds as PromptFL, FedCorr, NLPrompt and CLEAR-FPL on these datasets.

| notebook | runs | estimated time |
|---|---|---|
| `kaggle/prox_mnist` | 11 | about 8-10 h; PromptFL MNIST took 0.75 h per run |
| `kaggle/prox_eurosat` | 11 | about 5-6 h; PromptFL EuroSAT took 0.47 h per run |

The code zip is the one already uploaded (2026-10-30), unchanged.

**Results.** Extract them to `baselines/prox_mnist/` and `baselines/prox_eurosat/`. `python tools/analyze_baselines.py` adds the FedProx column to the MNIST and EuroSAT tables.

**Reported, not judged**, as on the other datasets: FedProx has no label-noise handling, so it is expected near PromptFL.

**Result, 2026-10-31: on MNIST and EuroSAT, FedProx is plain FedAvg by construction.**
- Every client holds at most 12 images (5-12 over all seeds), the batch size is 16 and there is 1 local epoch. So each round is exactly one SGD step, taken from the global prompt.
- At that step w equals w_global. The proximal gradient mu * (w - w_global) is therefore exactly 0, so the term never acts.
- The logs confirm it. In all 6 N settings, FedProx and PromptFL have identical train losses and accuracies, round by round and seed by seed (difference +0.00, p = nan).
- In the 5 S settings the differences (MNIST -0.88 to +0.99, EuroSAT -3.26 to +0.18, none significant) do not come from FedProx. The PromptFL comparators there are the gate-D runs, which carry extra logging flags (`--diag_scores`, `--log_signals`, `--correction_every 5`) that change the random stream. The client data and the noise are identical.
- For the paper: report FedProx on MNIST/EuroSAT as identical to PromptFL in this few-shot setting, with this reason, not as a separate result. On Pets, DTD and Caltech101, clients hold 10-95 images, so there are several steps per round and the term does act (it is still within about 1 point of PromptFL).
