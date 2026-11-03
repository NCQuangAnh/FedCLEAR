# CLEAR-FPL v2: the noise-rate audit (pre-registered 2026-10-25)

Background:
- offline screen: `results/side-research/idea_audit/offline_findings.md`;
- theory: `report/clear2_theory.md`.

## Method (`--sure true --sure_audit true`)

Each client does the following once, before training, with frozen zero-shot CLIP only:

1. Estimate its noise rate as ρ̂ = Σ(S_i − m_i) / Σ(S_i − c_i), with standard error se.
2. Flag itself when ρ̂ / se > z₀.₉₅ = 1.645, a one-sided test at 5%.
3. If flagged, choose its round(ρ̂·n) images with the lowest zero-shot probability of the given label.

Every round, each chosen image is relabelled to the top class of P = ½(global + zero-shot) when P is at least 0.5 sure. Otherwise it is left out of that round. The server runs plain FedAvg.

What is gone:
- τ = 0.05;
- the image threshold 0.1;
- the 60% cap.

What is left:
- α = 0.05, the conventional test level;
- 0.5, the "more likely right than wrong" relabel rule;
- the ½ mix, used only to choose the new label.

The last two get a sensitivity check if v2 is adopted.

## Arms

5 seeds, 50 rounds, FLIP protocol, the same seeds and flags as `S_<sc>_full` and `N_<x>_clear`:

| arm | meaning |
|---|---|
| `v2` (main) | audit, label not merged |
| `v2m` | audit, label merged with its nearest CLIP class (meant to add power on DTD) |
| `N_{pair50,pair75,sym75}_diag` | PromptFL with per-image logs, for findings F2 and F3 at high noise |

Each method arm covers 11 settings: S_sym, S_pair, S_inst, S_het, S_clean, plus N_sym and N_pair at 25, 50 and 75.

Where the runs happen:
- Pets and DTD on Kaggle: `kaggle/clear2_{pets,dtd}_{1,2,3}`, 22 method runs plus 3 diag runs per dataset;
- Caltech on the server: `server/queue_clear2.txt`, 22 runs, after `queue_baselines`.

Reference: CLEAR-FPL as run (`S_<sc>_full`, `N_<x>_clear`), paired by seed. The no-cap CLEAR from the cap study is reported next to it.

## Decision rules (fixed before any run)

Means are over 5 seeds of last10, compared per dataset.

1. **Adopt v2 as CLEAR-FPL** if, on Pets and on DTD:
   - **R1:** mean(N_sym75, N_pair75) of v2 − CLEAR > +0.5; and
   - **R2:** the mean over the other 9 settings of v2 − CLEAR ≥ −0.3.

   Caltech then confirms it with R1 > 0 and R2 ≥ −0.3. If Caltech fails, v2 is still reported, with Caltech as a stated failure.
2. **Merge.** Use `v2m` instead of `v2` if its 11-setting mean on DTD is at least 0.3 higher and on Pets is no more than 0.3 lower. The adoption rule (1) is then applied to the chosen variant.
3. **If v2 fails R2 only through DTD S_sym / S_inst**, the outcome is stated in advance:
   - CLEAR (with the cap-study decision applied) stays the method;
   - v2 and the findings are reported as analysis;
   - DTD is explained through the detection limit (prediction P3).
4. **If v2 fails R1**, CLEAR stays, and v2 is reported as an ablation.

## Predictions (checked from the `sure` records; reported whatever happens)

- **P1, estimate error:** mean |ρ̂ − true noise| over clients is ≤ 0.10 on Pets and DTD and ≤ 0.05 on Caltech.
- **P2, false flags:** honest clients are flagged at ≤ 5%, in every scenario (the test level).
- **P3, detection limit:** a client whose true noise is above its detection limit 1.645·se is flagged in ≥ 80% of cases; one below it in ≤ 50%.
- **P4, all-noisy 75%:** the share of noise reached (suspects that are noisy ÷ noisy images) is higher than CLEAR's 0.75-0.79.
- **F2, from the diag runs:** at N_sym75 and N_pair75, the global model's estimate on clients is biased by more than the zero-shot estimate. At N_pair75 the global model predicts the wrong (pair) label for a larger share of noisy images than at gate D pair 40%.
- **F3:** the AUROC gap g − z at N_pair75 is larger (more negative) than at gate D pair.
