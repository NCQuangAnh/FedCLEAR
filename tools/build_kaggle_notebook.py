"""Generate the Kaggle notebooks, one per phase, from one set of shared cells.

    kaggle/phase1_reproduce.ipynb   reproduce the FLIP baselines (done, kept as the record)
    kaggle/phase2_gate_a.ipynb      phase 2: label noise and the ORACLE ceilings

Both notebooks share the environment, dataset download and run-helper cells; only the
config, plan and collect cells differ. Those three are filled in per phase, so a phase-2
session cannot accidentally re-run phase 1, and phase 1 stays frozen as a thesis artifact.

Keeping the notebooks as generated code makes them diffable and easy to regenerate.

Usage:
    python tools/build_kaggle_notebook.py
"""
import copy
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DST = {1: os.path.join(ROOT, "kaggle", "phase1_reproduce.ipynb"),
       2: os.path.join(ROOT, "kaggle", "phase2_gate_a.ipynb"),
       3: os.path.join(ROOT, "kaggle", "phase3_gate_b.ipynb"),
       4: os.path.join(ROOT, "kaggle", "phase4_gate_c.ipynb"),
       5: os.path.join(ROOT, "kaggle", "phase5_gate_d.ipynb"),
       6: os.path.join(ROOT, "kaggle", "phase6_gate_e.ipynb")}


def md(text):
    return {"cell_type": "markdown", "metadata": {}, "source": text.strip("\n").splitlines(keepends=True)}


def code(text):
    return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [],
            "source": text.strip("\n").splitlines(keepends=True)}


PHASE_CONFIG = {}
PHASE_CONFIG[1] = """
OUT = f"{WORK}/phase1"
PHASE, RESULT_NAME = 1, "phase1_results"
# MODE = "reproduce":          ZS-CLIP + PromptFL + FedOTP. Done 2026-09-18 on T4 with
#                              TRAIN_TRANSFORM = "paper": 9/9 cells pass in 4.76 h
# MODE = "diagnose_transform": PromptFL only, with the two candidate train transforms
#                              ("default_norm" = upstream + Normalize, "paper" = Appendix B.4)
# MODE = "verify_cache":       1 run x 5 rounds with and without the test-feature cache; the
#                              curves must match exactly (they did, on all three datasets)
MODE = "reproduce"
DATASETS = ["dtd", "caltech101", "oxford_pets"]
TIMES = 3
BUDGET_HOURS = 5.0     # never start a run that is expected to push this notebook past this many hours
"""
PHASE_CONFIG[3] = """
OUT = f"{WORK}/phase3"
PHASE, RESULT_NAME = 3, "phase3_results"
# MODE = "gate_b":       the 7 jobs, seeds 0/1/2. Done 2026-09-19 on T4 in 6.09 h; several
#                        effects came out smaller than 2 sd of their own paired difference.
# MODE = "gate_b_seeds": more seeds for the jobs the verdict depends on. Seeds 3-4 for four
#                        jobs ran 2026-09-19 (2.25 h); the collect cell pools every run.
MODE = "gate_b_seeds"
DATASETS = ["dtd", "oxford_pets"]
TIMES = 3
BUDGET_HOURS = 4.0     # never start a run that is expected to push this notebook past this many hours
# roles are disjoint: 3 noisy clients, 2 malicious, 5 honest
NOISY_FRAC, NOISY_RATE, MAL_FRAC = 0.3, 0.4, 0.2
# seed extension: `--seed 5 --times 2` produces seeds 5 and 6. Seeds 0-4 are already in hand;
# this round targets B1 only, where the paired difference is still under the 2 sd bar
# (DTD +4.13 ± 3.43, p = 0.054; Pets +3.58 ± 1.95, p = 0.015). ~1.2 h.
EXTRA_SEED_START, EXTRA_SEED_COUNT = 5, 2
EXTRA_SEED_JOBS = ["N_control", "P0_disguise"]
"""
PHASE_CONFIG[4] = """
OUT = f"{WORK}/phase4"
PHASE, RESULT_NAME = 4, "phase4_results"
# MODE = "gate_c": done 2026-09-20 on DTD and OxfordPets (6.40 h). Neither passed, and they
#                  failed on DIFFERENT criteria: s_sem works only where zero-shot is already
#                  near the ceiling, s_conc only where training moves the prompt a lot.
#                  Results and the regime hypothesis: results/Phase4/gate_c_results.md
# MODE = "gate_c_regime": the held-out test of that hypothesis on Caltech101, whose training
#                  gain over zero-shot (4.52) sits between Pets (2.40) and DTD (13.83).
#                  Predictions were written down before running, in section 6 of that file:
#                  s_sem in [0.70, 0.95] and s_conc in [0.50, 0.75]. ~3 h.
# MODE = "gate_c_regime": done 2026-09-20 on Caltech101 (3.14 h). The s_sem prediction landed
#                  inside its range (0.938 in [0.70, 0.95]) but s_conc came out at 0.987, far
#                  ABOVE the predicted [0.50, 0.75]: the training-gain hypothesis is falsified.
#                  Class count fits the ordering instead (102 > 47 > 37 vs 0.987 > 0.780 > 0.487),
#                  but it is confounded with training gain across those three datasets.
# MODE = "gate_c_confound": the two datasets that break the confound, with opposite predictions
#                  written down first (results/Phase4/gate_c_results.md section 8):
#                    EuroSAT   10 classes, large training gain
#                    Food101  101 classes, small training gain
#                  ~4.8 h.
# MODE = "gate_c_confound": done 2026-09-21. EuroSAT finished both jobs in 45 min; Food101's
#                  control alone took 6.77 h and the budget guard correctly skipped the job the
#                  whole experiment was for. s_conc on EuroSAT P0_disguise = 0.593.
# MODE = "gate_c_confound_food": the one missing cell, and the only informative arm, on its own.
#                  ~6.8 h. Predictions unchanged, section 8 of results/Phase4/gate_c_results.md:
#                  class count governs -> s_conc >= 0.85; training gain governs -> <= 0.65.
MODE = "gate_c_confound_food"
DATASETS = ["eurosat", "food101"]
TIMES = 5               # seeds 0-4 in one go; the detection study needs paired seeds
BUDGET_HOURS = 8.5      # never start a run that is expected to push this notebook past this many hours
# same roles as gate B: 3 noisy clients, 2 malicious, 5 honest
NOISY_FRAC, NOISY_RATE, MAL_FRAC = 0.3, 0.4, 0.2
# which attacks to score the signals against; the regime test needs only the control and the
# disguised attack, which is the scenario the criteria are judged on
ATTACKS = ["none", "noise_disguise"]
"""
PHASE_CONFIG[5] = """
OUT = f"{WORK}/phase5"
PHASE, RESULT_NAME = 5, "phase5_results"
# MODE = "gate_d" ran 2026-09-20 (7.03 h, 5 of 6 jobs; caltech101_P0_disguise hit the budget
#   guard). It FAILS every pre-registered criterion, and the reason matters: r_align separates
#   refusers from honest clients almost perfectly but with the OPPOSITE sign to the prediction,
#   and the control was built wrong -- its malicious-role clients still refused the probe, so
#   refusal and poisoning could not be told apart. See results/Phase5/gate_d_results.md.
# MODE = "gate_d_control": the repaired control. A malicious-role client now complies when no
#   attack is configured, so this run isolates refusal from poisoning. Two jobs, ~2.2 h.
MODE = "gate_d_control"
DATASETS = ["dtd", "oxford_pets"]
TIMES = 5               # seeds 0-4; the detection study needs paired seeds
BUDGET_HOURS = 9.0      # never start a run that is expected to push this notebook past this many hours
# same roles as gate B and C: 3 noisy clients, 2 malicious, 5 honest
NOISY_FRAC, NOISY_RATE, MAL_FRAC = 0.3, 0.4, 0.2
CORRECTION_EVERY = 5    # probe every N rounds; 10 probes over a 50-round run
ATTACK_LIE = "mimic"    # the strong attacker: reports the honest gain, sends the uncorrected prompt
ATTACKS = ["none"]
"""
PHASE_CONFIG[6] = """
OUT = f"{WORK}/phase6"
PHASE, RESULT_NAME = 6, "phase6_results"
# MODE = "gate_e": done 2026-09-21 on DTD and OxfordPets (10.88 h, 10/10 jobs). E2 passes
#                  decisively (refusal AUC 0.93-1.00, and 0.91-0.99 against merely NOISY
#                  clients, with clean controls at chance). E1 and E3 fail, and the reason is
#                  that nothing was ever done with the detection: every config aggregated the
#                  refusers it had caught. results/Phase6/gate_e_results.md
# MODE = "gate_f": the missing half. Exclusion on refusal (--refusal_rule, calibrated offline
#                  on the Gate E probe records), the audit dose as a variable, and the
#                  composition with a robust rule. Criteria in section 9 of that file.
#                  ~4.9 h per dataset, so run ONE dataset per session.
#                  Two sessions per dataset: "gate_f" (F1 and F3, ~5.6 h) then
#                  "gate_f_dose" (F2, ~4.3 h).
#                  Gate F ran 2026-09-21: F1 and F3 both fail. Identifying the attacker
#                  correctly buys +0.65 +- 1.41 -- removal is the wrong lever.
# MODE = "gate_g": the one thing the correction was never given: a confidence gate. Gate E and
#                  gate F both relabelled EVERY sample with the global model's argmax, and on
#                  DTD that model is only ~52% accurate while a 40%-noise client still has 60%
#                  of its labels right, so the naive version overwrites good labels with worse
#                  guesses. Sweep how much of the data gets relabelled. ~6.6 h.
#                  H arms ran 2026-09-23: H_soft +3.19 (p=0.002) is the best of the project;
#                  the class rule loses in both regimes (-0.07 hard, -0.55 soft) and is dropped.
# MODE = "gate_i_seeds": five more seeds for the two arms whose difference is still open.
# MODE = "gate_i_score": RETIRED, and the branch now refuses to build a plan. It measured
#                  -1.14 (p=0.035) against the rank ramp, but two bugs were found underneath
#                  it afterwards, so the same flags no longer run the same code. gate_j_score
#                  is the rerun; do not compare anything to 49.61 / 49.16.
# MODE = "gate_i_pets": the headline result on a second dataset. Ran 2026-09-23: H_band
#                  +9.62 (p=0.0008), beating `median` by +5.01 -- the first time the method
#                  clears the field's standard defence. It also REVERSES the soft-vs-hard
#                  reading: soft won on DTD by 0.86 (p=0.40), hard wins on Pets by 4.33
#                  (p=0.0057). Precision explains both (DTD 66%, Pets 85%), so the mode is a
#                  function of precision, not a fixed choice. results/Phase_bonus/I_results.md
# MODE = "gate_j_auto": the server picks the mode itself from `dis_baseline`. Consistency
#                  check on DTD and Pets, the two datasets the 0.22 threshold was fitted on.
# MODE = "gate_j_score": the honest rerun of gate_i_score. Bug 1: the budget rescale only
#                  ever shrank, so the score arm spent 79% of the budget the rank arm spent
#                  (2128 against 2695 units per run) -- a full dose against a three-quarter
#                  dose, not a test of the idea. Bug 2: min-max normalisation let one tail
#                  sample flatten the rest. Two arms now, minmax against robust, so the rerun
#                  says WHICH fix mattered.
# MODE = "gate_j_regime": the held-out test, on EuroSAT then Caltech101. Four arms, because
#                  testing a selection rule needs both options plus the rule.
# >>> READY FOR THE NEXT RUN (set 2026-10-16): gate D stage 1, the runs skipped by the time budget. Notebook kaggle/gate_d1_fill_dtd.ipynb.
# >>> Nothing below needs editing for that run.
MODE = "gate_q_noise"    # gate_k_relabel | gate_q_noise | gate_r_device | gate_k_proto | gate_k_prior | gate_k_diag | gate_l_device | gate_i_seeds | gate_j_auto | gate_j_score | gate_j_regime | gate_i_score | gate_i_pets | gate_h_filter | gate_h_oracle | gate_g_diag | gate_g_warmup | gate_g_control | gate_g | gate_g_atk
# The six sessions queued after the I runs, in order. Criteria for each were written down
# before any of them started, in results/Phase_bonus/gate_j_plan.md.
#   1  gate_i_seeds    ["dtd"]          TIMES 5   ~4.0 h   the rerun; the first attempt was
#                                                          invalid because the branch skipped
#                                                          base() and ran with no noise at all
#   2a gate_j_auto     ["dtd"]          TIMES 5   ~1.3 h   server picks the mode; must land on
#   2b gate_j_auto     ["oxford_pets"]  TIMES 5   ~1.3 h   H_soft on DTD and H_band on Pets
#   3  gate_j_score    ["dtd"]          TIMES 5   ~2.6 h   score weighting, rerun after two
#                                                          bugs; minmax against robust
#   4a gate_j_regime   ["eurosat"]      TIMES 5   ~3.0 h   held-out test, all 4 arms
#   4b gate_j_regime   ["caltech101"]   TIMES 5   ~6.0 h   REGIME_ARMS = ["A0_refuse","H_soft"]
#   4c gate_j_regime   ["caltech101"]   TIMES 5   ~6.0 h   REGIME_ARMS = ["H_band","H_auto"]
#   5a gate_k_relabel  ["oxford_pets"]  TIMES 5   ~4.0 h   K_base + 2 relabel arms, data-only attacker
#   5b gate_k_relabel  ["caltech101"]   TIMES 5   ~9.0 h   same three arms; BUDGET_HOURS = 10
#   6c gate_l_device   ["caltech101"]   TIMES 5   ~9 h   L_ARMS = ["L_base","L_down","L_tdr"]; BUDGET 10
#   6x gate_l_device   ["caltech101", "dtd"]  ~9.5 h  L_ARMS = {"caltech101": ["L_tdr_early"],
#                                              "dtd": L_ALL}; BUDGET_HOURS = 10
#   6y gate_l_device   ["caltech101", "oxford_pets"]  ~9.5 h  L_ARMS = {"caltech101": ["L_oracle60"],
#                                              "oxford_pets": L_ALL}; BUDGET_HOURS = 10
#   (6x/6y replace the old 6a, 6b, 6d: two sessions in parallel instead of three)
#   R1 gate_r_device   ["oxford_pets"]  TIMES 5   ~6 h   R_ARMS default (4 arms); BUDGET 11.5
#   R2 gate_r_device   ["caltech101"]   TIMES 5   ~7 h   R_ARMS = ["R_none","R_clip"]; BUDGET 11.5
#   R3 gate_r_device   ["caltech101"]   TIMES 5   ~8 h   R_ARMS = ["R_prec","R_oracle60"]; BUDGET 11.5
#   R4 gate_r_device   ["oxford_pets"]  TIMES 5   ~3 h   R_ARMS = ["R_prec_once","R_prec_refresh"]; BUDGET 11.5
#   R5 gate_r_device   ["caltech101"]   TIMES 5   ~8 h   same arms (kaggle/gate_r2_*.ipynb, one per session)
#   R6/R7 gate_r_device  pets / caltech  ~3 h / ~8 h   R_ARMS = ["R_prec_once_hide","R_prec_once_turncoat"] (kaggle/gate_r3_*.ipynb)
#   R8/R9 gate_r_device  pets / caltech  ~4 h / ~11 h  R_ARMS = ["R_prec_forge","R_prec_once_forge"] (kaggle/gate_r4_*.ipynb)
# Hours are the raw table doubled: the measured overhead of the probe rounds and the filter is
# about 2x on top of the per-round estimate (the H_ session planned 2.5 h and took 5.26 h).
# After 4b, paste its A0_refuse per-seed values into REFERENCE["caltech101"] so 4c can pair
# against them; without that the collect cell prints absolute numbers and says so.
DATASETS = ["dtd"]      # gate D stage 1 (grouped ~10-11 h per notebook)
TIMES = 5
BUDGET_HOURS = 11.5
NOISY_FRAC, NOISY_RATE, MAL_FRAC = 0.3, 0.4, 0.2
CORRECTION_EVERY = 5
AUDIT_PROB = 1.0        # probability that a probe round's contribution is taken from the probe
# gate F only. The ban rule was fixed before this run by replaying the Gate E probe records:
# running mean of r_align, threshold median - k*spread, spread floored at FLOOR*|median|.
DOSE_EVERY = 2          # the second audit dose: 25 of 50 rounds instead of 10
# gate_f_dose reuses the references measured in the gate_f session instead of re-running them
# (1.1 h saved). Seeds are deterministic, so this pairing is exact, not approximate: gate E
# A1_refuse_audit and gate F A3_exclude agree to the digit on the seed where no ban fired.
REFERENCE = {
    "dtd": {"L_base": [45.70, 52.84, 47.47, 51.34, 48.94],
            "L_down": [46.40, 53.22, 47.05, 51.34, 50.06],
            "L_tdr": [47.83, 53.13, 48.80, 51.95, 49.09],
            "L_tdr_early": [46.68, 53.66, 48.01, 51.37, 49.22],
            "L_oracle60": [50.23, 53.04, 54.54, 52.44, 50.65],
            "L_clip": [46.15, 53.26, 48.34, 51.95, 49.22],
            "L_clip_down": [47.66, 52.98, 48.73, 51.95, 50.07],
            "N_excl": [49.38, 51.18, 50.49, 50.83, 51.40],
            "N_control": [51.28, 53.20, 52.21, 52.09, 51.52],
            "A0_refuse": [43.82, 50.65, 45.33, 49.75, 48.23],
            # the ungated correction, measured in the gate E session
            "N_audit": [51.33, 53.59, 54.02, 52.48, 53.16],
            "A1_refuse_audit": [44.06, 52.67, 49.04, 49.00, 49.88],
            "H_auto": [46.38, 52.82, 50.16, 52.94, 51.52]},
    "oxford_pets": {"N_control": [82.58, 80.84, 81.05, 82.18, 79.52],
                    "A0_refuse": [76.27, 78.79, 72.07, 77.96, 74.32],
                    "N_audit": [83.70, 82.28, 82.42, 82.50, 80.30],
                    "A1_refuse_audit": [77.01, 80.94, 72.33, 79.59, 74.58],
                    # gate I / J, same seeds 0-4
                    "H_soft": [83.16, 83.81, 78.50, 81.18, 79.23],
                    "H_band": [86.35, 87.25, 83.24, 84.16, 86.52],
                    "H_auto": [85.33, 87.43, 84.59, 82.90, 85.50],
                    # gate K (data-only attacker), same seeds
                    "K_base": [86.75, 87.24, 84.94, 84.43, 83.87],
                    "K_fix": [87.49, 86.86, 84.08, 85.95, 85.25],
                    "K_fixconf": [87.70, 86.75, 83.62, 85.94, 83.66],
                    "K_proto": [87.42, 88.81, 86.06, 87.34, 86.57],
                    "K_restore": [87.86, 88.67, 87.73, 87.81, 87.34],
                    # gate L (device attacker), same seeds
                    "L_base": [80.81, 83.77, 76.54, 81.10, 78.09],
                    "L_down": [81.47, 84.96, 77.70, 81.81, 81.56],
                    "L_tdr": [81.57, 86.84, 80.18, 84.14, 78.52],
                    "L_tdr_early": [84.09, 86.26, 80.47, 82.91, 79.33],
                    "L_oracle60": [88.14, 87.81, 86.61, 85.73, 85.24],
                    "L_clip": [81.57, 86.84, 80.15, 83.20, 78.51],
                    "L_clip_down": [82.32, 86.84, 81.63, 84.64, 82.08],
                    "N_excl": [82.18, 87.39, 84.77, 82.72, 79.34],
                    # gate R (8 honest + 2 device attackers), same seeds
                    "R_none": [83.38, 85.32, 81.72, 85.22, 81.26],
                    "R_clip": [84.59, 87.42, 84.12, 87.17, 83.93],
                    "R_prec": [86.17, 88.66, 86.03, 86.84, 88.28],
                    "R_oracle60": [87.18, 88.19, 87.53, 87.64, 87.69],
                    "R_prec_once": [86.04, 88.53, 86.41, 86.61, 88.08],
                    "R_prec_refresh": [86.17, 88.66, 86.03, 86.84, 88.28],
                    "R_prec_once_hide": [87.12, 88.18, 86.67, 87.55, 86.7],
                    "R_prec_once_turncoat": [86.32, 88.71, 87.65, 87.04, 87.84],
                    "Q_none": [82.58, 80.84, 76.09, 83.2, 79.61],
                    "Q_filter": [87.72, 87.52, 86.63, 86.69, 86.3],
                    "Q_fixconf": [88.23, 87.95, 84.14, 87.21, 86.83],
                    "Q_mae": [87.8, 88.64, 88.25, 88.23, 87.67]},
    # gate J regime; both Caltech sessions verified to share splits and roles seed by seed
    "caltech101": {"A0_refuse": [83.95, 85.61, 80.75, 86.40, 85.88],
                   "H_soft": [86.90, 88.58, 83.91, 87.77, 88.39],
                   "H_band": [86.73, 90.17, 88.41, 88.90, 89.37],
                   "H_auto": [88.38, 89.95, 87.57, 88.85, 88.86],
                   "K_base": [87.49, 90.28, 88.62, 88.85, 88.86],
                   "K_fix": [89.21, 91.14, 89.62, 88.19, 89.20],
                   "K_fixconf": [88.96, 90.84, 89.35, 88.91, 89.29],
                   "K_proto": [87.14, 88.88, 89.25, 87.94, 88.92],
                   "K_restore": [90.20, 90.79, 89.86, 89.67, 90.53],
                   # gate L session 6c/6y (device attacker), for the L_tdr rerun to pair against
                   "L_base": [82.19, 86.98, 82.31, 85.77, 84.80],
                   "L_down": [80.19, 88.91, 86.75, 87.03, 85.21],
                   "L_oracle60": [86.61, 90.47, 89.57, 88.58, 88.97],
                   "L_clip": [85.95, 88.21, 87.08, 87.49, 87.06],
                   "L_clip_down": [85.31, 88.23, 87.06, 87.49, 86.37],
                   # gate R (8 honest + 2 device attackers), same seeds
                   "R_none": [84.28, 87.5, 83.29, 86.03, 86.06],
                   "R_clip": [87.51, 88.76, 86.04, 87.95, 88.12],
                   "R_prec": [89.95, 90.65, 88.73, 88.98, 90.12],
                   "R_oracle60": [90.03, 90.06, 89.44, 88.67, 89.61],
                   "R_prec_once": [89.98, 90.65, 88.89, 88.98, 89.97],
                   "R_prec_refresh": [89.95, 90.65, 88.73, 88.98, 90.12],
                   "R_prec_once_hide": [89.47, 89.95, 88.4, 89.02, 90.23],
                   "R_prec_once_turncoat": [89.78, 90.27, 88.49, 88.77, 90.7],
                   "Q_none": [87.55, 88.35, 88.13, 87.57, 87.33],
                   "Q_filter": [89.19, 90.88, 89.08, 89.1, 89.82],
                   "Q_fixconf": [89.58, 90.75, 89.51, 89.15, 89.88],
                   "Q_mae": [90.36, 89.91, 89.49, 89.67, 89.5]},
}
# gate G: the fraction of each client's samples to LEAVE ALONE. 0.0 is the ungated version
# already measured; 0.9 relabels only the surest 10%.
CONF_QUANTILES = [0.5, 0.75, 0.9]
# gate I: the soft filter reached +3.19 (p=0.002) and is the best result of the project, but
# head to head against the hard filter it is only +0.86 +- 2.07 (p=0.40). Five more seeds
# settles that without a new idea. Seeds 0-4 are already in hand.
SEED_START, SEED_COUNT = 5, 5
# gate_j_regime: which of the four arms this session runs. Caltech101 is 20.6 s/round, so all
# four at 5 seeds is ~12 h -- past what one session holds. Splitting the arms across two
# sessions keeps 5 seeds, which a held-out test needs far more than it needs to finish in one
# sitting. The pairing stays exact across sessions because the seeds are deterministic: gate E
# A1_refuse_audit and gate F A3_exclude agreed to the digit on the seed where no ban fired.
REGIME_ARMS = ["A0_refuse", "H_soft", "H_band", "H_auto"]
# gate_l_device: which arms this session runs -- a list for every dataset, or a dict
# {dataset: [arms]} (e.g. {"dtd": L_ALL, "caltech101": ["L_tdr_early"]}) to merge sessions
K_ARMS = ["K_proto_band"]     # gate_k_proto: any of K_proto, K_proto_band, K_restore
Q_ARMS = ["D_inst_none", "D_sym_mae", "D_het_dbr"]     # gate D stage 1, results/side-research/gate_D/gate_d1_plan.md
R_ARMS = ["R_prec_once_forge"]     # gate_r_device rerun (R4b): forge against the data direction
L_ALL = ["L_base", "L_down", "L_tdr", "L_tdr_early", "L_oracle60"]
L_ARMS = L_ALL
WARMUP_ROUNDS = [5, 10, 20]     # gate_g_warmup: rounds before the noisy clients join
REFUSAL = ("--refusal_rule", "mad", "--refusal_k", "2.0",
           "--refusal_floor", "0.12", "--refusal_patience", "3")
"""
PHASE_CONFIG[2] = """
OUT = f"{WORK}/phase2"
PHASE, RESULT_NAME = 2, "phase2_results"
MODE = "gate_a"
# 2026-09-18 on T4 (2.72 h): DTD and OxfordPets done, and they disagree on criterion ii
# (H_client = -0.3/+0.6 on DTD, +2.9/+3.4 on Pets), so the pre-registered rule says run
# Caltech101 to break the tie. Results: results/Phase2/gate_a_results.md
DATASETS = ["caltech101"]
TIMES = 3
BUDGET_HOURS = 3.0     # never start a run that is expected to push this notebook past this many hours
# one (noise type, rate, noisy-client fraction, rate mode) per scenario to gate on
NOISE_SETTINGS = [("sym", 0.4, 0.5, "uniform"), ("pair", 0.4, 0.5, "uniform")]
RUN_INVARIANCE = False  # the D check already passed on DTD, on GPU with AMP and the cache
"""

COLLECT_CELL = {}
COLLECT_CELL[6] = '''
# --- gate E: the criteria of docs/phase6_plan.md section 3 ---------------------------------
sys.path.insert(0, f"{CODE}/tools")
from parse_flip_log import parse_log
import math


def per_seed_last10(log_path):
    return [statistics.fmean(c[-10:]) for c in parse_log(log_path)[0]]


def paired(a, b):
    n = min(len(a), len(b))
    d = [a[i] - b[i] for i in range(n)]
    m = statistics.fmean(d)
    sd = statistics.stdev(d) if n > 1 else 0.0
    t = m / (sd / math.sqrt(n)) if sd > 0 else float("inf")
    return m, sd, t, n


def auc(pos, neg):
    if not pos or not neg:
        return float("nan")
    return sum((1.0 if p > n else 0.5 if p == n else 0.0) for p in pos for n in neg) / (len(pos) * len(neg))


def refusal_auc(tag):
    # -r_align, refusers against everyone who complied
    ref, comp = [], []
    for path in glob.glob(f"{OUT}/runs/{tag}/**/noise_seed_*.json", recursive=True):
        blob = json.load(open(path))
        acc = {}
        for rec in blob.get("probes", []):
            if all(abs(v["r_align"] - 1.0) < 1e-9 for v in rec["clients"].values()):
                continue
            for cid, v in rec["clients"].items():
                acc.setdefault((int(cid), v["role"]), []).append(v["r_align"])
        for (cid, role), vals in acc.items():
            (ref if role == "malicious" else comp).append(-statistics.fmean(vals))
    return auc(ref, comp)


acc, idx = {}, load_index()
for tag, e in sorted(idx.items()):
    if e["returncode"] == 0:
        acc[(e["dataset"], e["variant"])] = per_seed_last10(e["log"])
for ds, jobs in globals().get("REFERENCE", {}).items():
    for job, vals in jobs.items():
        acc.setdefault((ds, job), vals)      # only fills what this session did not run

print("| dataset | job | last10 | damage vs control | share of the refusing attack |")
print("|" + "---|" * 5)
rows = []
for (ds, job), vals in sorted(acc.items()):
    ctrl = acc.get((ds, "N_control"))
    dmg = paired(ctrl, vals)[0] if ctrl else float("nan")
    rows.append({"dataset": ds, "job": job, "last10": round(statistics.fmean(vals), 2),
                 "damage": round(dmg, 2), "per_seed": [round(x, 2) for x in vals]})
    base = acc.get((ds, "A0_refuse"))
    share = ""
    if base and ctrl and job.startswith("A"):
        d0 = paired(ctrl, base)[0]
        share = f"{dmg / d0 * 100:.0f}%" if d0 else ""
    print(f"| {ds} | {job} | {rows[-1]['last10']:.2f} | {dmg:+.2f} | {share} |")

print()
verdict = {}
for ds in sorted({r["dataset"] for r in rows}):
    ctrl, a0, a2 = acc.get((ds, "N_control")), acc.get((ds, "A0_refuse")), acc.get((ds, "A2_comply_audit"))
    if not (ctrl and a0 and a2):
        print(f"{ds}: incomplete, need N_control, A0_refuse and A2_comply_audit")
        continue
    d0, _, _, _ = paired(ctrl, a0)
    d2, _, _, _ = paired(ctrl, a2)
    # E1 asks what complying costs the attacker: the damage it keeps, relative to refusing
    kept = d2 / d0 if d0 else float("nan")
    m, sd, t, n = paired(a2, a0)     # positive = complying leaves the federation better off
    e1 = kept <= 0.5 and abs(t) > 2.0
    e2 = refusal_auc(f"{ds}_A0_refuse") >= 0.90
    best_fixed = None   # gate B measured the fixed rules; the audit protocol is compared to A0
    print(f"{ds}: attack damage refusing {d0:+.2f}, complying {d2:+.2f} -> keeps {kept*100:.0f}%")
    print(f"    E1 complying costs it at least half: {'PASS' if e1 else 'fail'}"
          f"  (difference {m:+.2f} ± {sd:.2f}, t = {t:.2f}, n = {n})")
    print(f"    E2 refusal detectable, AUC {refusal_auc(f'{ds}_A0_refuse'):.3f}: {'PASS' if e2 else 'fail'}")
    naud, aud = acc.get((ds, "N_control")), acc.get((ds, "N_audit"))
    if naud and aud:
        c = paired(naud, aud)[0]
        print(f"    cost of auditing a clean federation: {c:+.2f} points (positive = audit hurts)")
    verdict[ds] = (e1, e2)

json.dump({"rows": rows, "verdict": {k: list(v) for k, v in verdict.items()}},
          open(f"{OUT}/phase6_gate_e.json", "w"), indent=1)
ok1 = sum(v[0] for v in verdict.values())
ok2 = sum(v[1] for v in verdict.values())
print("")
print(f"E1 on {ok1}/{len(verdict)} datasets, E2 on {ok2}/{len(verdict)}")
print(f"GATE E {'PASSES so far' if ok1 >= 2 and ok2 >= 2 else 'does not pass yet'}"
      f" (E3, the end-to-end accuracy gain, needs the full protocol run)")


def ban_table(tag):
    # who the online rule actually banned, against the true roles. The rule never sees these.
    got = {"honest": [0, 0], "noisy": [0, 0], "malicious": [0, 0]}
    for path in glob.glob(f"{OUT}/runs/{tag}/**/noise_seed_*.json", recursive=True):
        blob = json.load(open(path))
        recs = blob.get("refusal", [])
        roles = {int(c): v["role"] for r in blob.get("probes", []) for c, v in r["clients"].items()}
        banned = set(recs[-1]["banned_total"]) if recs else set()
        for c, r in roles.items():
            got[r][0] += c in banned
            got[r][1] += 1
    return got


if MODE.startswith("gate_g"):
    print("")
    print("=== correction quality: does the teacher beat the labels it overwrites? ===")
    import re
    for tag in sorted(load_index()):
        rows = []
        try:
            for line in open(f"{OUT}/logs/{tag}.txt", encoding="utf-8", errors="ignore"):
                i = line.find("CORRECTION_AUDIT ")
                if i >= 0:
                    rows.append(json.loads(line[i + len("CORRECTION_AUDIT "):]))
        except OSError:
            continue
        if not rows:
            continue
        f = sum(r["fixed"] for r in rows); b = sum(r["broken"] for r in rows)
        print(f"  {tag}: coverage {statistics.fmean(r['coverage'] for r in rows) * 100:.0f}%  "
              f"labels {statistics.fmean(r['label_acc'] for r in rows) * 100:.0f}% right, "
              f"teacher {statistics.fmean(r['teacher_acc'] for r in rows) * 100:.0f}% "
              f"({statistics.fmean(r['teacher_acc_used'] for r in rows) * 100:.0f}% where used)  "
              f"-> FIXED {f}, BROKEN {b}, net {f - b:+d}")
    print("  net > 0 means the correction repairs more labels than it destroys.")

    print("")
    print("=== gate G: does a confidence gate make the correction worth more? ===")
    print("criteria pre-registered in results/Phase6/gate_g_plan.md")
    for ds in sorted({d for d, _ in acc}):
        ctrl, ung = acc.get((ds, "N_control")), acc.get((ds, "N_audit"))
        a0, a1 = acc.get((ds, "A0_refuse")), acc.get((ds, "A1_refuse_audit"))
        print(f"--- {ds}")
        print("  no attacker: how much the correction beats plain FedAvg")
        base = paired(acc[(ds, "N_audit")], ctrl)[0] if (ctrl and ung) else float("nan")
        print(f"    ungated (conf 0)            {statistics.fmean(ung):6.2f}  {base:+.2f}")
        g1 = 0
        for q in CONF_QUANTILES:
            k = (ds, f"N_audit_q{int(q * 100)}")
            if k not in acc:
                continue
            gain = paired(acc[k], ctrl)[0]
            m, sd, t, n = paired(acc[k], ung)
            g1 += m >= 1.0
            print(f"    leave {q * 100:.0f}% alone              {statistics.fmean(acc[k]):6.2f}  "
                  f"{gain:+.2f}   vs ungated {m:+.2f} +- {sd:.2f}, t = {t:.2f}")
        print(f"    G1 (>= +1.0 over ungated on at least 2 of 3 thresholds): "
              f"{'PASS' if g1 >= 2 else 'fail'}  [{g1}/3]")
        if (ds, "N_audit_dose") in acc and ctrl:
            m, sd, t, n = paired(acc[(ds, "N_audit_dose")], ctrl)
            print(f"    dose 25/50, no attacker      {statistics.fmean(acc[(ds, 'N_audit_dose')]):6.2f}  "
                  f"{m:+.2f} +- {sd:.2f}, t = {t:.2f}   [dose 10/50 gave +0.86]")
        print("  with the attacker: how much it beats no defence")
        if a0 and a1:
            print(f"    ungated (conf 0)            {statistics.fmean(a1):6.2f}  "
                  f"{paired(a1, a0)[0]:+.2f}")
        g2 = 0
        for q in CONF_QUANTILES:
            k = (ds, f"A1_audit_q{int(q * 100)}")
            if k not in acc or not a0:
                continue
            m, sd, t, n = paired(acc[k], a0)
            g2 += m >= 2.0
            print(f"    leave {q * 100:.0f}% alone              {statistics.fmean(acc[k]):6.2f}  "
                  f"{m:+.2f} +- {sd:.2f}, t = {t:.2f}")
        print(f"    G2 (>= +2.0 over no defence on at least 1 threshold): "
              f"{'PASS' if g2 >= 1 else 'fail'}  [{g2}/3]")
        # what the gate actually did, by role, rather than what it was asked to do
        for q in CONF_QUANTILES:
            for pre in ("N_audit", "A1_audit"):
                tag = f"{ds}_{pre}_q{int(q * 100)}"
                byrole = {}
                for path in glob.glob(f"{OUT}/runs/{tag}/**/noise_seed_*.json", recursive=True):
                    for rec in json.load(open(path)).get("probes", []):
                        for v in rec["clients"].values():
                            if "r_replaced" in v:
                                byrole.setdefault(v["role"], []).append(v["r_replaced"])
                if byrole:
                    print(f"    relabelled in {tag}: " + ", ".join(
                        f"{r} {statistics.fmean(x) * 100:.0f}%" for r, x in sorted(byrole.items())))

if MODE.startswith("gate_f"):
    print("")
    print("=== gate F, criteria pre-registered in results/Phase6/gate_e_results.md section 9 ===")
    for ds in sorted({d for d, _ in acc}):
        ctrl = acc.get((ds, "N_control"))
        if not ctrl:
            print(f"{ds}: no N_control, nothing is comparable")
            continue

        def dmg(job):
            return paired(ctrl, acc[(ds, job)])[0] if (ds, job) in acc else None

        if MODE == "gate_f":
            d0, d3 = dmg("A0_refuse"), dmg("A3_exclude")
            if d0 and d3 is not None:
                kept = d3 / d0
                m, sd, t, n = paired(acc[(ds, "A3_exclude")], acc[(ds, "A0_refuse")])
                print(f"{ds} F1: damage refusing {d0:+.2f}, refusing under exclusion {d3:+.2f}"
                      f" -> keeps {kept * 100:.0f}%  ({'PASS' if kept <= 0.25 else 'fail'};"
                      f" difference {m:+.2f} +- {sd:.2f}, t = {t:.2f}, n = {n})")
            for tag in (f"{ds}_A3_exclude", f"{ds}_M1_median_full"):
                b = ban_table(tag)
                if sum(v[1] for v in b.values()):
                    print("      bans in " + tag + ": "
                          + ", ".join(f"{r} {v[0]}/{v[1]}" for r, v in b.items()))
            if (ds, "M0_median") in acc and (ds, "M1_median_full") in acc:
                m, sd, t, n = paired(acc[(ds, "M1_median_full")], acc[(ds, "M0_median")])
                print(f"{ds} F3: median alone {statistics.fmean(acc[(ds, 'M0_median')]):.2f},"
                      f" median + audit + exclusion {statistics.fmean(acc[(ds, 'M1_median_full')]):.2f}"
                      f" -> {m:+.2f} +- {sd:.2f} ({'PASS' if m >= 2.0 else 'fail'}, t = {t:.2f})")
        else:
            d5, d4 = dmg("A5_refuse_dose"), dmg("A4_comply_dose")
            if d5 and d4 is not None:
                kept = d4 / d5
                m, sd, t, n = paired(acc[(ds, "A4_comply_dose")], acc[(ds, "A5_refuse_dose")])
                print(f"{ds} F2 at 25/50 audited rounds: refusing {d5:+.2f}, complying {d4:+.2f}"
                      f" -> keeps {kept * 100:.0f}%  ({'PASS' if kept <= 0.60 else 'fail'};"
                      f" difference {m:+.2f} +- {sd:.2f}, t = {t:.2f}, n = {n})")
                print("      gate E measured 82% (DTD) and 77% (Pets) at 10 of 50 rounds")
            for job, what in (("O_drop_mal", "perfect removal from round 0"),
                              ("A6_fast_ban", "same rule, first decision at round 4")):
                d = dmg(job)
                if d is not None:
                    print(f"{ds} {job}: damage {d:+.2f} ({what});"
                          f" gate F measured +4.50 with no defence and +3.85 with a late ban")
                    b = ban_table(f"{ds}_{job}")
                    if sum(v[1] for v in b.values()) and b["malicious"][0]:
                        print("      bans: " + ", ".join(f"{r} {v[0]}/{v[1]}" for r, v in b.items()))
'''
COLLECT_CELL[5] = '''
# --- gate D: the criteria of docs/phase5_plan.md section 5 ---------------------------------
sys.path.insert(0, f"{CODE}/tools")

PROBE_KEYS = ["r_align", "r_gain", "r_unearned", "r_conc_drop", "r_kl_drop"]


def auc(pos, neg):
    if not pos or not neg:
        return float("nan")
    return sum((1.0 if p > n else 0.5 if p == n else 0.0) for p in pos for n in neg) / (len(pos) * len(neg))


def load_probes(tag):
    rows = []
    for path in sorted(glob.glob(f"{OUT}/runs/{tag}/**/noise_seed_*.json", recursive=True)):
        blob = json.load(open(path))
        seed = int(path.rsplit("_", 1)[-1].split(".")[0])
        acc = {}
        for rec in blob.get("probes", []):
            vals = list(rec["clients"].values())
            # the cosine schedule zeroes the learning rate on the last round: both extra passes
            # then move nothing and every alignment is exactly 1
            if all(abs(v["r_align"] - 1.0) < 1e-9 for v in vals):
                continue
            for cid, v in rec["clients"].items():
                a = acc.setdefault((seed, int(cid), v["role"]), {k: [] for k in PROBE_KEYS})
                for k in a:
                    if k in v:
                        a[k].append(v[k])
        # s_upd comes from the same file, and is the signal D3 has to beat
        upd = {}
        for rec in blob.get("signals", []):
            for cid, v in rec["clients"].items():
                upd.setdefault((seed, int(cid)), []).append(v["s_upd"])
        for (sd, cid, role), v in acc.items():
            row = {"seed": sd, "client": cid, "role": role,
                   **{k: statistics.fmean(x) for k, x in v.items() if x}}
            if (sd, cid) in upd:
                row["s_upd"] = statistics.fmean(upd[(sd, cid)])
            rows.append(row)
    return rows


results = []
for tag, e in sorted(load_index().items()):
    if e["returncode"] != 0:
        continue
    rows = load_probes(tag)
    if not rows:
        print(f"{tag}: no probe records")
        continue
    by = lambda role, key: [r[key] for r in rows if r["role"] == role and key in r]
    rec = {"dataset": e["dataset"], "job": e["variant"], "n_scored": len(rows)}
    for k in PROBE_KEYS + ["s_upd"]:
        rec[f"auc_{k}"] = round(auc(by("malicious", k), by("noisy", k)), 3)
    rec["means"] = {role: {k: round(statistics.fmean(by(role, k)), 4)
                           for k in PROBE_KEYS if by(role, k)}
                    for role in ("honest", "noisy", "malicious")}
    results.append(rec)

json.dump(results, open(f"{OUT}/phase5_gate_d.json", "w"), indent=1)
print("| dataset | job | r_align | r_gain | r_unearned | r_conc_drop | s_upd (to beat) |")
print("|" + "---|" * 7)
for r in results:
    print(f"| {r['dataset']} | {r['job']} | {r['auc_r_align']:.3f} | {r['auc_r_gain']:.3f} | "
          f"{r['auc_r_unearned']:.3f} | {r['auc_r_conc_drop']:.3f} | {r['auc_s_upd']:.3f} |")

print()
attacked = [r for r in results if r["job"] == "P0_disguise"]
d1 = [r["dataset"] for r in attacked if r["auc_r_align"] >= 0.80]
pets = next((r for r in attacked if r["dataset"] == "oxford_pets"), None)
d2 = pets is not None and pets["auc_r_align"] >= 0.75
d3 = [r["dataset"] for r in attacked
      if r["dataset"] in d1 and r["auc_r_align"] - r["auc_s_upd"] >= 0.10]
print(f"D1 r_align >= 0.80 on at least 2 of 3 datasets: {sorted(d1)} -> {'PASS' if len(d1) >= 2 else 'fail'}")
print(f"D2 r_align >= 0.75 on OxfordPets: {pets['auc_r_align'] if pets else 'n/a'} -> {'PASS' if d2 else 'fail'}")
print(f"D3 beats s_upd by >= 0.10 where D1 holds: {sorted(d3)} -> "
      f"{'PASS' if d1 and len(d3) == len(d1) else 'fail'}")
print(f"GATE D {'PASSES' if len(d1) >= 2 and d2 and d1 and len(d3) == len(d1) else 'does not pass'}")

for r in results:
    if r["job"] == "N_control":
        # the malicious clients behaved honestly here, so the probe must NOT single them out
        print(f"control {r['dataset']}: r_align {r['auc_r_align']:.3f} "
              f"(near 0.5 means no false alarm)")
'''
COLLECT_CELL[4] = '''
# --- gate C: can the signals tell the three roles apart? -----------------------------------
# Criteria are pre-registered in docs/phase4_plan.md section 3. Scores are averaged over
# rounds 10-50 per client per seed, then ranked; AUC is the Mann-Whitney statistic.
ROUND_FROM, ROUND_TO = 10, 50


def auc(pos, neg):
    # probability that a random positive outranks a random negative, ties counted as half
    if not pos or not neg:
        return float("nan")
    wins = sum((1.0 if p > n else 0.5 if p == n else 0.0) for p in pos for n in neg)
    return wins / (len(pos) * len(neg))


def load_signals(tag):
    rows = []
    for path in sorted(glob.glob(f"{OUT}/runs/{tag}/**/noise_seed_*.json", recursive=True)):
        blob = json.load(open(path))
        seed = int(path.rsplit("_", 1)[-1].split(".")[0])
        acc = {}
        for rec in blob.get("signals", []):
            if not (ROUND_FROM <= rec["round"] <= ROUND_TO):
                continue
            # the cosine schedule drives the learning rate to zero on the final round, so
            # every client returns the global prompt unchanged and every signal is 0
            if all(v["s_upd"] == 0 for v in rec["clients"].values()):
                continue
            for cid, v in rec["clients"].items():
                key = (seed, int(cid), v["role"])
                a = acc.setdefault(key, {k: [] for k in
                                          ("s_sem", "s_conc", "s_conc_n", "s_conc_kl", "s_upd")})
                for k in a:
                    if k in v:
                        a[k].append(v[k])
        for (seed_i, cid, role), v in acc.items():
            rows.append({"seed": seed_i, "client": cid, "role": role,
                         **{k: statistics.fmean(x) for k, x in v.items() if x}})
    return rows


results = []
for tag, e in sorted(load_index().items()):
    if e["returncode"] != 0:
        continue
    rows = load_signals(tag)
    if not rows:
        print(f"{tag}: no signal records")
        continue
    ds, job = e["dataset"], e["variant"]
    by = lambda role, key: [r[key] for r in rows if r["role"] == role and key in r]
    # the full pairwise picture, not just the two headline numbers
    pair = {"conc_malicious_vs_honest": auc(by("malicious", "s_conc"), by("honest", "s_conc")),
            "conc_noisy_vs_honest": auc(by("noisy", "s_conc"), by("honest", "s_conc")),
            "sem_malicious_vs_honest": auc(by("malicious", "s_sem"), by("honest", "s_sem")),
            "mean_s_sem": {r: round(statistics.fmean(by(r, "s_sem")), 5) for r in
                           ("honest", "noisy", "malicious") if by(r, "s_sem")},
            "mean_s_conc": {r: round(statistics.fmean(by(r, "s_conc")), 5) for r in
                            ("honest", "noisy", "malicious") if by(r, "s_conc")}}
    # C1: s_sem, problem clients (noisy or malicious) against honest ones
    c1 = auc(by("noisy", "s_sem") + by("malicious", "s_sem"), by("honest", "s_sem"))
    # C2: s_conc, malicious against noisy -- the criterion that decides the thesis direction
    c2 = auc(by("malicious", "s_conc"), by("noisy", "s_conc"))
    # C3: the same separation using the Krum-style deviation signal, the one to beat
    c3 = auc(by("malicious", "s_upd"), by("noisy", "s_upd"))
    # scale-free variants of the concentration signal, on the same separation
    for k in ("s_conc_n", "s_conc_kl"):
        pair[f"auc_{k}_malicious_vs_noisy"] = round(auc(by("malicious", k), by("noisy", k)), 3)
    per_seed = []
    for sd in sorted({r["seed"] for r in rows}):
        sub = [r for r in rows if r["seed"] == sd]
        g = lambda role, key: [r[key] for r in sub if r["role"] == role and key in r]
        per_seed.append({"seed": sd,
                         "c2": auc(g("malicious", "s_conc"), g("noisy", "s_conc")),
                         "c3": auc(g("malicious", "s_upd"), g("noisy", "s_upd"))})
    results.append({"dataset": ds, "job": job, "pairwise": pair,
                    "auc_sem_problem_vs_honest": round(c1, 3),
                    "auc_conc_malicious_vs_noisy": round(c2, 3),
                    "auc_upd_malicious_vs_noisy": round(c3, 3),
                    "gain_over_deviation": round(c2 - c3, 3), "per_seed": per_seed,
                    "n_clients_scored": len(rows)})

json.dump(results, open(f"{OUT}/phase4_gate_c.json", "w"), indent=1)
print("| dataset | job | C1 s_sem (problem vs honest) | C2 s_conc (malicious vs noisy) | s_upd, same task | C2 - s_upd |")
print("|" + "---|" * 6)
for r in results:
    print(f"| {r['dataset']} | {r['job']} | {r['auc_sem_problem_vs_honest']:.3f} | "
          f"{r['auc_conc_malicious_vs_noisy']:.3f} | {r['auc_upd_malicious_vs_noisy']:.3f} | "
          f"{r['gain_over_deviation']:+.3f} |")

print()
for ds in sorted({r["dataset"] for r in results}):
    dis = next((r for r in results if r["dataset"] == ds and r["job"] == "P0_disguise"), None)
    if not dis:
        continue
    c1_ok = dis["auc_sem_problem_vs_honest"] >= 0.80
    c2_ok = dis["auc_conc_malicious_vs_noisy"] >= 0.80
    c3_ok = dis["gain_over_deviation"] >= 0.10
    print(f"{ds} (disguised attack): C1 {dis['auc_sem_problem_vs_honest']:.3f} -> {'PASS' if c1_ok else 'fail'}"
          f" | C2 {dis['auc_conc_malicious_vs_noisy']:.3f} -> {'PASS' if c2_ok else 'fail'}"
          f" | C3 gain {dis['gain_over_deviation']:+.3f} -> {'PASS' if c3_ok else 'fail'}")
    print(f"    GATE C {'PASSES' if c1_ok and c2_ok and c3_ok else 'does not pass'} on this dataset")
    if MODE.startswith("gate_c_confound"):
        # two hypotheses, opposite predictions, fixed before this run
        conc = dis["auc_conc_malicious_vs_noisy"]
        by_classes = {"eurosat": conc <= 0.65, "food101": conc >= 0.85}.get(ds)
        by_gain = {"eurosat": conc >= 0.75, "food101": conc <= 0.65}.get(ds)
        print(f"    s_conc = {conc:.3f}")
        print(f"      class-count hypothesis  -> {'supported' if by_classes else 'contradicted'}")
        print(f"      training-gain hypothesis -> {'supported' if by_gain else 'contradicted'}")
'''
COLLECT_CELL[3] = '''
# --- gate B: the criteria of docs/phase3_plan.md section 3, merged across seed runs ---------
sys.path.insert(0, f"{CODE}/tools")
from parse_flip_log import parse_log

# Seeds already measured (results/Phase3/gate_b_results.md): 0-4 for the four key jobs,
# 0-2 for the rest. A further seed-extension run is pooled in below, positionally — which is
# valid because every job's seed list starts at 0 and runs in order.
SEEDS_DONE = {
    ("dtd", "N_control"): [51.34, 51.74, 52.83, 53.44, 52.62],
    ("dtd", "P0_disguise"): [43.74, 51.94, 45.34, 49.60, 50.69],
    ("dtd", "P1_targeted"): [46.06, 51.86, 53.07],
    ("dtd", "P2_signflip"): [33.29, 42.71, 36.28],
    ("dtd", "D0_disguise_multikrum"): [43.82, 52.30, 48.66, 49.47, 45.72],
    ("dtd", "D1_disguise_median"): [47.15, 49.22, 49.39, 49.50, 48.07],
    ("dtd", "D2_signflip_multikrum"): [39.62, 47.26, 41.72],
    ("oxford_pets", "N_control"): [82.53, 80.00, 79.69, 81.74, 82.50],
    ("oxford_pets", "P0_disguise"): [77.86, 79.54, 75.74, 78.51, 76.91],
    ("oxford_pets", "P1_targeted"): [79.91, 78.18, 76.36],
    ("oxford_pets", "P2_signflip"): [58.85, 70.91, 57.76],
    ("oxford_pets", "D0_disguise_multikrum"): [75.88, 83.74, 67.58, 78.95, 74.27],
    ("oxford_pets", "D1_disguise_median"): [79.46, 82.84, 79.30, 82.40, 80.06],
    ("oxford_pets", "D2_signflip_multikrum"): [67.66, 77.20, 59.12],
}
# multikrum exclusion rate per role already measured, with the number of seeds behind it
EXCL_DONE = {
    ("dtd", "D0_disguise_multikrum"): ({"honest": 0.173, "noisy": 0.132, "malicious": 0.369}, 5),
    ("dtd", "D2_signflip_multikrum"): ({"honest": 0.116, "noisy": 0.161, "malicious": 0.467}, 3),
    ("oxford_pets", "D0_disguise_multikrum"): ({"honest": 0.019, "noisy": 0.336, "malicious": 0.449}, 5),
    ("oxford_pets", "D2_signflip_multikrum"): ({"honest": 0.021, "noisy": 0.405, "malicious": 0.340}, 3),
}


def per_seed_last10(log_path):
    return [statistics.fmean(c[-10:]) for c in parse_log(log_path)[0]]


def exclusion_by_role(tag):
    counts = {"honest": 0, "noisy": 0, "malicious": 0}
    present = {"honest": 0, "noisy": 0, "malicious": 0}
    rounds, files = 0, glob.glob(f"{OUT}/runs/{tag}/**/noise_seed_*.json", recursive=True)
    for path in files:
        blob = json.load(open(path))
        for r in blob.get("roles") or []:
            present[r] = present.get(r, 0) + 1
        for rec in blob.get("agg_records", []):
            rounds += 1
            for role in rec.get("excluded_roles", []):
                counts[role] = counts.get(role, 0) + 1
    if not rounds:
        return None, 0
    per_role = {r: present[r] / max(len(files), 1) for r in present}
    return {r: counts[r] / rounds / max(per_role[r], 1) for r in counts}, len(files)


# collect this session's runs, then pool with the stored seed 0/1/2 values
seen, excl_new = {}, {}
for tag, e in sorted(load_index().items()):
    if e["returncode"] != 0:
        continue
    seen[(e["dataset"], e["variant"])] = per_seed_last10(e["log"])
    ex, n = exclusion_by_role(tag)
    if ex:
        excl_new[(e["dataset"], e["variant"])] = (ex, n)

pooled = {}
for key in set(SEEDS_DONE) | set(seen):
    pooled[key] = list(SEEDS_DONE.get(key, [])) + list(seen.get(key, []))

print("| dataset | job | last10 | n seeds | damage vs control (paired) | conclusive |")
print("|" + "---|" * 6)
out = []
for (ds, job), vals in sorted(pooled.items()):
    ctrl = pooled.get((ds, "N_control"))
    n = min(len(ctrl), len(vals)) if ctrl else 0
    d = [ctrl[i] - vals[i] for i in range(n)] if ctrl else []
    m = statistics.fmean(d) if d else float("nan")
    sd = statistics.stdev(d) if len(d) > 1 else 0.0
    conclusive = bool(d) and abs(m) >= 2 * sd
    rec = {"dataset": ds, "job": job, "last10": round(statistics.fmean(vals), 2),
           "n_seeds": len(vals), "per_seed_last10": [round(x, 2) for x in vals],
           "damage": round(m, 2), "damage_sd": round(sd, 2), "conclusive": conclusive}
    out.append(rec)
    print(f"| {ds} | {job} | {rec['last10']:.2f} | {rec['n_seeds']} | {m:+.2f} ± {sd:.2f} | "
          f"{'yes' if conclusive else 'NO'} |")

# pool the exclusion rates, weighting each run by how many seeds it holds
excl = {}
for key in set(EXCL_DONE) | set(excl_new):
    old, w_old = EXCL_DONE.get(key, (None, 0))
    # excl_new holds (rates, n_seeds); unpack once, then use the names, never re-index
    new, w_new = excl_new.get(key, (None, 0))
    roles = {}
    for r in ("honest", "noisy", "malicious"):
        num = (old[r] * w_old if old else 0) + (new[r] * w_new if new else 0)
        den = w_old + w_new
        roles[r] = round(num / den, 3) if den else None
    excl[key] = roles

print()
print("| dataset | job | excluded/round: honest | noisy | malicious | noisy/honest | noisy/malicious |")
print("|" + "---|" * 7)
for key, r in sorted(excl.items()):
    if None in r.values():
        continue
    ratio_h = r["noisy"] / r["honest"] if r["honest"] else float("inf")
    ratio_m = r["noisy"] / r["malicious"] if r["malicious"] else float("inf")
    print(f"| {key[0]} | {key[1]} | {r['honest']:.3f} | {r['noisy']:.3f} | {r['malicious']:.3f} | "
          f"{ratio_h:.1f}x | {ratio_m:.2f}x |")

json.dump({"damage": out, "exclusion": {f"{k[0]}|{k[1]}": v for k, v in excl.items()}},
          open(f"{OUT}/phase3_gate_b.json", "w"), indent=1)

print()
for ds in sorted({r["dataset"] for r in out}):
    get = lambda v: next((r for r in out if r["dataset"] == ds and r["job"] == v), None)
    dis, kr, med = get("P0_disguise"), get("D0_disguise_multikrum"), get("D1_disguise_median")
    if not (dis and kr and med):
        print(f"{ds}: incomplete, need P0/D0/D1")
        continue
    b1 = dis["damage"] >= 2.0 and dis["conclusive"]
    b2 = min(kr["damage"], med["damage"]) >= 2.0
    e = excl.get((ds, "D0_disguise_multikrum"), {})
    b3 = e and e["noisy"] >= e["malicious"]
    b3p = e and e["honest"] and e["noisy"] >= 5 * e["honest"] and e["noisy"] >= 0.5 * e["malicious"]
    print(f"{ds}: B1 disguised attack costs {dis['damage']:+.2f} ± {dis['damage_sd']:.2f} over {dis['n_seeds']} seeds"
          f" -> {'PASS' if b1 else 'fail (or not conclusive)'}")
    print(f"    B2 {kr['damage']:+.2f} with multikrum, {med['damage']:+.2f} with median -> {'PASS' if b2 else 'fail'}")
    print(f"    B3  (noisy >= malicious)            -> {'PASS' if b3 else 'fail'}")
    print(f"    B3' (noisy >= 5x honest and >= 0.5x malicious, revised after seeing the 3-seed data)"
          f" -> {'PASS' if b3p else 'fail'}")
    print(f"    cost of multikrum vs no defense: {kr['damage'] - dis['damage']:+.2f} "
          f"(positive = the defense made it worse)")
'''
COLLECT_CELL[1] = '''
# --- collect results and check the pre-registered criteria ---------------------------------
sys.path.insert(0, f"{CODE}/tools")
from parse_flip_log import summarize_log

# FLIP arXiv:2503.22263v1 Table 1, identical to the NeurIPS 2025 camera-ready Table 1
# (RN50, global accuracy, mean +- sd over 3 runs)
PAPER = {
    ("caltech101", "ZSCLIP"): (86.0, 0.0), ("caltech101", "PromptFL"): (91.5, 0.5), ("caltech101", "FedOTP"): (91.8, 0.1),
    ("dtd", "ZSCLIP"): (41.7, 0.0), ("dtd", "PromptFL"): (57.6, 1.3), ("dtd", "FedOTP"): (58.0, 0.8),
    ("oxford_pets", "ZSCLIP"): (85.7, 0.0), ("oxford_pets", "PromptFL"): (89.4, 0.5), ("oxford_pets", "FedOTP"): (89.1, 0.1),
}

rows = []
for tag, e in sorted(load_index().items()):
    if tag.startswith("timing") or e["returncode"] != 0:
        continue
    ds, method, variant = e["dataset"], e.get("method") or tag.rsplit("_", 1)[-1], e.get("variant", "default")
    s = summarize_log(e["log"])
    paper_mean, paper_sd = PAPER[(ds, method)]
    if method == "ZSCLIP":
        ours, ours_sd, last, last10, tol = s["zero_shot"], 0.0, None, None, 0.5
    else:
        ours, ours_sd = s["best"]["mean"], s["best"]["sd"]
        last, last10, tol = s["last"]["mean"], s["last10_mean"]["mean"], max(1.0, 2 * paper_sd)
    diff = ours - paper_mean
    rows.append({"dataset": ds, "method": method, "variant": variant,
                 "ours_best": round(ours, 2), "ours_sd": round(ours_sd, 2),
                 "ours_best_per_run": None if method == "ZSCLIP" else [round(r["best"], 2) for r in s["runs"]],
                 "paper": paper_mean, "paper_sd": paper_sd, "diff": round(diff, 2), "tolerance": tol,
                 "pass": abs(diff) <= tol + 1e-9, "ours_last": None if last is None else round(last, 2),
                 "ours_last10": None if last10 is None else round(last10, 2), "minutes": round(e["seconds"] / 60, 1)})

json.dump(rows, open(f"{OUT}/phase1_summary.json", "w"), indent=1)
print("| dataset | method | variant | ours best | paper | diff | tol | pass | ours last | ours last10 | min |")
print("|" + "---|" * 11)
for r in rows:
    print(f"| {r['dataset']} | {r['method']} | {r['variant']} | {r['ours_best']:.2f}±{r['ours_sd']:.2f} | {r['paper']}±{r['paper_sd']} | "
          f"{r['diff']:+.2f} | {r['tolerance']} | {'OK' if r['pass'] else 'FAIL'} | {r['ours_last']} | {r['ours_last10']} | {r['minutes']} |")
'''
COLLECT_CELL[2] = '''
# --- gate A: the pre-registered criteria of docs/phase2_plan.md section 4 -------------------
sys.path.insert(0, f"{CODE}/tools")
from parse_flip_log import summarize_log, parse_log

# A = 0%-noise PromptFL, per seed 0/1/2, measured 2026-09-18 (results/Phase1/3datasets)
PHASE1_CLEAN = {"dtd": [57.27, 57.21, 55.67], "caltech101": [90.67, 91.24, 90.91],
                "oxford_pets": [88.36, 89.26, 89.62]}
# E = the zero-shot floor
ZS_CLEAN = {"dtd": 41.78, "caltech101": 85.76, "oxford_pets": 85.69}


def paired(xs, ys):
    # mean and sd of the per-seed difference; runs are ordered by seed, so index i is seed i
    n = min(len(xs), len(ys))
    d = [xs[i] - ys[i] for i in range(n)]
    return statistics.fmean(d), (statistics.stdev(d) if n > 1 else 0.0), d


Bs, Cs, rows = {}, {}, []
for tag, e in sorted(load_index().items()):
    if e["returncode"] != 0:
        continue
    bests = [r["best"] for r in summarize_log(e["log"])["runs"]]
    if "_C_" in tag:          # one C per dataset: the noise type is irrelevant once they are gone
        Cs[e["dataset"]] = (bests, round(e["seconds"] / 60, 1))
    elif "_B_" in tag:
        Bs[(e["dataset"], e["variant"])] = (bests, round(e["seconds"] / 60, 1), e["log"])

print("| dataset | noise | B (no defense) | B last10 | C (drop noisy) | A (clean) | A-B | C-B | B>ZS | min |")
print("|" + "---|" * 10)
for (ds, label), (B, b_min, b_log) in sorted(Bs.items()):
    if ds not in Cs:
        print(f"| {ds} | {label} | B done, C missing |")
        continue
    C, c_min = Cs[ds]
    A = PHASE1_CLEAN[ds]
    hs_mean, hs_sd, _ = paired(A, B)      # H_sample = A - B
    hc_mean, hc_sd, _ = paired(C, B)      # H_client = C - B
    row = {"dataset": ds, "noise": label,
           "B": round(statistics.fmean(B), 2), "B_per_seed": [round(x, 2) for x in B],
           "C": round(statistics.fmean(C), 2), "C_per_seed": [round(x, 2) for x in C],
           "A": round(statistics.fmean(A), 2),
           "H_sample": round(hs_mean, 2), "H_sample_sd": round(hs_sd, 2),
           "H_client": round(hc_mean, 2), "H_client_sd": round(hc_sd, 2),
           "B_above_zs": statistics.fmean(B) > ZS_CLEAN[ds],
           "crit_i": hs_mean >= 3.0, "crit_ii": hc_mean >= 2.0,
           "conclusive_i": abs(hs_mean) >= 2 * hs_sd, "conclusive_ii": abs(hc_mean) >= 2 * hc_sd,
           "minutes": b_min + c_min,
           # last10 matters as much as best here: under noise the model peaks early and then
           # memorises the wrong labels, and `best` hides most of that
           "B_last10": round(statistics.fmean(
               statistics.fmean(c[-10:]) for c in parse_log(b_log)[0]), 2)}
    rows.append(row)
    print(f"| {ds} | {label} | {row['B']:.2f} | {row['B_last10']:.2f} | {row['C']:.2f} | {row['A']:.2f} | "
          f"{hs_mean:+.2f}±{hs_sd:.2f} | {hc_mean:+.2f}±{hc_sd:.2f} | "
          f"{'yes' if row['B_above_zs'] else 'NO'} | {row['minutes']:.0f} |")

json.dump(rows, open(f"{OUT}/phase2_gate_a.json", "w"), indent=1)
print()
for label in sorted({r["noise"] for r in rows}):
    sub = [r for r in rows if r["noise"] == label]
    i_ok = sum(r["crit_i"] for r in sub)
    ii_ok = sum(r["crit_ii"] for r in sub)
    iii_ok = sum(r["B_above_zs"] for r in sub)
    shaky = [r["dataset"] for r in sub if not (r["conclusive_i"] and r["conclusive_ii"])]
    print(f"{label}: criterion i (A-B >= 3.0) on {i_ok}/{len(sub)} datasets, "
          f"ii (C-B >= 2.0) on {ii_ok}/{len(sub)}, iii (B > ZS) on {iii_ok}/{len(sub)}")
    verdict = "PASSES" if i_ok >= 2 and ii_ok >= 2 and iii_ok == len(sub) else "does not pass"
    print(f"    GATE A {verdict} (needs i and ii on >= 2 datasets and iii everywhere)")
    if shaky:
        print(f"    effect smaller than 2 sd of the paired difference on {shaky}: "
              f"add seeds 3 and 4 before concluding")
if len(DATASETS) < 3:
    print(f"\\nnote: criteria i and ii are counted over 3 datasets; this session ran {DATASETS}. "
          f"Run the rest before reading the verdict as final.")
'''

PLAN_CELL = {}
PLAN_CELL[6] = '''
# --- plan: does the dilemma actually cost the attacker anything? ----------------------------
# Four runs per dataset, identical except for what the attacker does and whether the server
# audits. The comparison A2 against A0 is the whole question: an attacker that complies with
# the correction should lose its attack, because the correction comes from a model that does
# not share its target class.
PLAN = []
for ds in DATASETS:
    # Every mode up to gate J ran the mixed attacker (poisoned data AND refused the probe);
    # they keep it so their numbers reproduce. From gate K on, the attacker is data-only.
    LEGACY_MODES = {"gate_e", "gate_f", "gate_f_dose", "gate_g", "gate_g_diag", "gate_g_warmup",
                    "gate_g_control", "gate_g_atk", "gate_h_filter", "gate_h_diag",
                    "gate_h_oracle", "gate_i_seeds", "gate_i_score", "gate_i_pets",
                    "gate_j_auto", "gate_j_score", "gate_j_regime"}
    attacker = ("legacy" if MODE in LEGACY_MODES
                else "device" if MODE in ("gate_l_device", "gate_r_device") else "data")

    def base(every=None):
        return ("--attacker_model", attacker, "--data_transform", TRAIN_TRANSFORM,
                "--noise_type", "sym", "--noise_rate", str(NOISY_RATE),
                "--noisy_client_frac", str(NOISY_FRAC),
                "--malicious_client_frac", str(MAL_FRAC),
                "--log_signals", "true",
                "--correction_every", str(every or CORRECTION_EVERY))
    atk = ("--attack_type", "noise_disguise", "--attack_rate", str(NOISY_RATE))
    audit = ("--probe_audit_prob", str(AUDIT_PROB))
    comply = ("--attack_probe_comply", "true")
    # shared by every sample-filter branch, so a new branch cannot reference a name that only
    # exists inside another one
    base_f = atk + ("--correction_audit", "true")
    band = ("--filter_clean_band", "0.10")

    def job(tag, extra, every=None, times=None):
        PLAN.append((ds, "CoOp", times or TIMES, GLOBAL_ROUNDS, f"{ds}_{tag}",
                     base(every) + tuple(extra), "PromptFL", tag))

    if MODE == "gate_e":
        # what a clean federation pays for being audited at all
        job("N_control", ("--attack_type", "none"))
        job("N_audit", ("--attack_type", "none") + audit)
        # the attacker refuses the correction: same as gate D, and the audit does not save it,
        # because the probe prompt it returns still carries the poison
        job("A0_refuse", atk)
        job("A1_refuse_audit", atk + audit)
        # the attacker takes the other horn: it complies, stays invisible, and lets the server's
        # own labels overwrite its poison whenever a probe round is audited
        job("A2_comply_audit", atk + audit + comply)
    elif MODE == "gate_f":
        # references: re-run only what REFERENCE does not already hold for this dataset.
        # Seeds are deterministic, so borrowing across sessions is exact, not approximate --
        # verified on the seed where no ban fired, which matched to two decimals.
        have = REFERENCE.get(ds, {})
        if "N_control" not in have:
            job("N_control", ("--attack_type", "none"))
        if "A0_refuse" not in have:
            job("A0_refuse", atk)
        # F1: catch the refuser AND stop aggregating it. Gate E only ever did the catching.
        job("A3_exclude", atk + audit + REFUSAL)
        # F3: does the protocol compose with the one fixed rule that worked in gate B?
        job("M0_median", atk + ("--agg_rule", "median"))
        job("M1_median_full", atk + audit + REFUSAL + ("--agg_rule", "median"))
    elif MODE == "gate_f_dose":
        # F2: the audit dose as a variable. Gate E audited 10 of 50 rounds and the complying
        # attacker kept 77-82% of its damage; these repeat that contrast at 25 of 50.
        # No N_control here: seeds are deterministic, so pairing against the gate F session's
        # control is exact. That was verified, not assumed -- gate E A1_refuse_audit seed 3 and
        # gate F A3_exclude seed 3 agree to the digit on the seed where no ban fired.
        job("A5_refuse_dose", atk + audit, every=DOSE_EVERY)
        job("A4_comply_dose", atk + audit + comply, every=DOSE_EVERY)
        # why F1 failed, two competing explanations, one job each:
        # (a) removal is simply the wrong response, even done perfectly and instantly
        job("O_drop_mal", atk + ("--attack_oracle", "drop_malicious"))
        # (b) removal is right but our detector is too slow: first ban lands at round 10-30.
        #     probing every 2 rounds with patience 2 moves the first decision to round 4
        job("A6_fast_ban", atk + audit + ("--refusal_rule", "mad", "--refusal_k", "2.0",
                                          "--refusal_floor", "0.12", "--refusal_patience", "2"),
            every=DOSE_EVERY)
    elif MODE == "gate_g_diag":
        # One job, one seed, ~14 min. Is the correction even better than the labels it
        # overwrites? The whole repair direction rests on that and nobody has measured it.
        # The table is printed by this cell, so a committed run does not have to finish first.
        job("DIAG_audit", ("--attack_type", "none") + audit + ("--correction_audit", "true"),
            times=1)
    elif MODE == "gate_g":
        job("DIAG_audit", ("--attack_type", "none") + audit + ("--correction_audit", "true"),
            times=1)
        # no attacker: the correction measured as an AGGREGATION RULE. This half answers G1
        # and carries the diagnostic, so run it first and on its own.
        for q in CONF_QUANTILES:
            gate = ("--correction_conf", str(q), "--correction_conf_mode", "quantile",
                    "--correction_audit", "true")
            job(f"N_audit_q{int(q * 100)}", ("--attack_type", "none") + audit + gate)
        # the gap the dose session left: the correction at 25/50 rounds was only ever measured
        # WITH an attacker. If it is an aggregation rule rather than a defence, the higher dose
        # has to pay off with no adversary present too. Cheapest direct test of the main claim.
        job("N_audit_dose", ("--attack_type", "none") + audit, every=DOSE_EVERY)
    elif MODE == "gate_g_warmup":
        # Can a trusted subset build a teacher good enough for correction to pay?  The diag
        # measured the teacher at 47.0% on noisy clients' data while their own labels were
        # 60.4% right, so correction destroyed 8.5 labels for every one it repaired. Staged
        # participation is the direct attack on that number.
        #
        # This assumes the server trusts some clients -- FLTrust's clean-root assumption in
        # another wrapper. It must be declared and compared against, not slipped in. It is also
        # a bet against data scarcity: gate A measured that on DTD losing five clients costs
        # 7.11 points while their noise only costs 6.82.
        for w in WARMUP_ROUNDS:
            job(f"N_warm{w}", ("--attack_type", "none") + audit
                + ("--warmup_rounds", str(w), "--correction_audit", "true"))
    elif MODE == "gate_g_control":
        # The control the whole direction rests on. Identical in every way -- same extra epoch,
        # same returned prompt, same audit aggregating it -- except the labels are NOT
        # corrected. N_audit gained +0.86 on DTD and +1.01 on Pets. If that survives here, the
        # gain never was label repair.
        job("N_audit_ownlabels", ("--attack_type", "none") + audit
            + ("--correction_labels", "own", "--correction_audit", "true"))
    elif MODE == "gate_h_filter":
        # The method, finally. Two operating points chosen from the offline scoring of the
        # diagnostic run, and deliberately at opposite ends of the precision/recall trade:
        #   rho  -- drops 31% of the damaged samples and 4.3% of the clean ones, and touched
        #           ZERO samples of any honest client
        #   both -- drops 94.8% of the damaged samples for 15.1% of the clean ones
        # The exchange rate between the two is the thing no amount of offline tuning can give.
        # v1 result: F_rho +1.40 (80% of what it dropped really was damaged, honest clients
        # untouched) and F_both -10.27, which collapsed through a feedback loop -- an absolute
        # class threshold fires everywhere once the teacher weakens, and the filter is what
        # weakens it. rho is now a hard budget, so an honest client is never touched whatever
        # the teacher does, and the baseline is a low quantile because the median is itself
        # damaged when half the federation is.
        # G_rho reached +2.33 (p=0.023) at 71.1% precision, and the fitted exchange rate --
        # one clean sample dropped costs 1.34x one damaged sample gained -- says that is 84%
        # of everything 71.1% precision allows. Recall is spent; precision is the lever now.
        job("H_soft", base_f + ("--sample_filter", "rho", "--filter_soft", "true") + band)
        job("H_split", base_f + ("--sample_filter", "both", "--filter_min_class", "5") + band)
        job("H_full", base_f + ("--sample_filter", "both", "--filter_min_class", "5",
                                "--filter_soft", "true") + band)
        # the amnesty on its own, against G_rho: it should remove every false drop on an
        # honest client (3.5% of their data, all of it clean) and change nothing else
        job("H_band", base_f + ("--sample_filter", "rho") + band)
    elif MODE == "gate_i_seeds":
        # Same two configurations, seeds 5-9. Paired against each other on the new seeds and
        # pooled with 0-4 afterwards, so the comparison keeps its pairing.
        # These must go through job(), like every other branch. Appending to PLAN by hand
        # skipped base(), which is what carries the noise, the roles, the transform and the
        # probe schedule -- the first attempt ran three jobs with no noise and no attacker at
        # all, so all three returned the same clean-federation number and two hours were lost.
        seed = ("--seed", str(SEED_START))
        job(f"H_soft_s{SEED_START}",
            base_f + ("--sample_filter", "rho", "--filter_soft", "true") + band + seed,
            times=SEED_COUNT)
        job(f"H_band_s{SEED_START}",
            base_f + ("--sample_filter", "rho") + band + seed, times=SEED_COUNT)
        job(f"A0_refuse_s{SEED_START}", atk + seed, times=SEED_COUNT)
    elif MODE == "gate_i_score":
        # RETIRED -- do not run this again, and do not compare anything to its recorded
        # numbers (I_score 49.61, I_score_floor 49.16). Two bugs were fixed underneath it
        # afterwards: the budget rescale only ever shrank, and min-max normalisation let one
        # tail sample flatten the rest. The same flags now execute different code, so a rerun
        # would produce numbers that look comparable and are not. gate_j_score is the rerun.
        raise SystemExit("gate_i_score is retired; use gate_j_score (see gate_j_plan.md)")
    elif MODE == "__gate_i_score_original__":
        # kept only so the original plan stays readable in the history
        job("I_score", base_f + ("--sample_filter", "rho", "--filter_soft", "true",
                                 "--filter_soft_mode", "score") + band)
        job("I_score_floor", base_f + ("--sample_filter", "rho", "--filter_soft", "true",
                                       "--filter_soft_mode", "score",
                                       "--filter_w_min", "0.15") + band)
    elif MODE == "gate_i_pets":
        # The headline result needs a second dataset. A0_refuse and N_control on Pets are
        # already in REFERENCE, so only the two treated arms have to run.
        job("H_soft", base_f + ("--sample_filter", "rho", "--filter_soft", "true") + band)
        job("H_band", base_f + ("--sample_filter", "rho") + band)
    elif MODE == "gate_j_score":
        # The score idea, retested after two bugs found by measuring what the first attempt
        # actually spent rather than by re-reading the reasoning.
        #   bug 1  the rescale only shrank. The rank ramp spends its budget exactly (2695 units
        #          per run on DTD); the score version spent 2128, 79% of the same budget. The
        #          -1.14 (p=0.035) was a full dose against a three-quarter dose.
        #   bug 2  min-max normalisation lets one tail sample set the scale and flattens the
        #          rest. On a simulated client with 12 damaged of 40 it lands 60.8% of its
        #          weight on damaged samples; median/IQR scaling lands 77.5% at the same spend.
        # Two arms, so the retest says WHICH fix mattered instead of just whether the pair did.
        score = ("--sample_filter", "rho", "--filter_soft", "true", "--filter_soft_mode", "score")
        job("J_score_minmax", base_f + score + ("--filter_score_norm", "minmax") + band)
        job("J_score_robust", base_f + score + ("--filter_score_norm", "robust") + band)
    elif MODE == "gate_j_auto":
        # PRIORITY 2. The mode is no longer a flag; the server picks it each probe round from
        # `dis_baseline`, the low quantile of the clients' disagreement, which it already
        # computes and which needs no label. Threshold 0.22, calibrated offline on the 460
        # probe rounds of the H_ and I_ runs (tools/simulate_filter_mode.py) -- so THIS run is
        # a consistency check on the data the threshold came from, not a test of it. The test
        # is gate_j_regime on a dataset the threshold has never seen.
        #
        # Criterion, written before running:
        #   on DTD  H_auto must land within 0.5 of H_soft (50.75) and the replay says it picks
        #           soft on 83.0% of active rounds
        #   on Pets H_auto must land within 0.5 of H_band (85.50); the replay says 82.6% hard
        # Anything else means the mode decision does not survive contact with the training loop
        # -- most likely because switching mode mid-run is not the same as running that mode
        # from round 0, which is a real risk and the reason this arm exists at all.
        job("H_auto", base_f + ("--sample_filter", "rho", "--filter_soft", "auto") + band)
    elif MODE == "gate_l_device":
        # The attacker owns its machine: refuses the probe, never filters, lies about its
        # disagreement. The client-side method cannot touch it, so this measures (a) how much
        # the current method loses to it, and (b) whether the server can take it back by
        # down-weighting the clients that refuse. Criteria: results/Phase_bonus/gate_l_plan.md.
        auto = base_f + ("--sample_filter", "rho", "--filter_soft", "auto") + band \
            + ("--log_asr", "true")
        arms = {
            "L_base": auto,
            # weight set by the detector's own evidence, not a hand-picked constant
            "L_down": auto + REFUSAL + ("--refusal_action", "downweight",
                                        "--refusal_weight_mode", "proportional"),
            # same detector as L_down, different treatment: the flagged client keeps its weight
            # but loses the part of its update that pulls other classes towards one class
            "L_tdr": auto + REFUSAL + ("--refusal_action", "flag", "--tdr", "true",
                                       "--tdr_scope", "flagged"),
            # oracle on WHO only: TDR may cut the true attackers from round 0. Gap to L_tdr = the
            # most any fix for the ~15 undetected early rounds (rollback included) could buy
            "L_tdr_early": auto + REFUSAL + ("--refusal_action", "flag", "--tdr", "true",
                                             "--tdr_scope", "flagged", "--tdr_oracle_who", "true"),
            # ceiling: the attackers train on their clean 60% only
            "L_oracle60": auto + ("--sample_oracle", "drop_dirty_mal"),
        }
        # Why does L_tdr work when its target guess is right 0-8% of the time? Four arms that
        # differ from L_tdr in one thing each (results/Phase_ex/L/L_results.md, next steps):
        tdr = arms["L_tdr"]
        arms.update({
            # target from the client's own excess probe mass, the signal that voted right offline
            "L_tdr_conc": tdr + ("--tdr_target", "conc"),
            # ORACLE target: what perfect targeting is worth
            "L_tdr_true": tdr + ("--tdr_target", "true"),
            # CONTROL: a fixed random class per client -- damping without targeting
            "L_tdr_rand": tdr + ("--tdr_target", "random"),
            # CONTROL: never cut, keep only the 2x-median norm clip that L_tdr applies to everyone
            "L_clip": tdr + ("--tdr_z", "1e9"),
            # the clip (the mechanism, per the 7a/7b follow-up) plus proportional down-weighting
            # of flagged clients: do the two add up?
            "L_clip_down": auto + REFUSAL + ("--refusal_action", "downweight",
                                             "--refusal_weight_mode", "proportional",
                                             "--tdr", "true", "--tdr_z", "1e9"),
            # gate N (results/Phase_ex/L/gate_n_plan.md): cross-client validation. The clip is
            # now standalone (--norm_clip), the same arithmetic as L_clip without TDR's cost.
            # N_log records the validation scores and must reproduce L_clip seed by seed;
            # N_excl is the ORACLE ceiling of any down-weighting rule; N_xval_* act on the score.
            "N_log": auto + ("--norm_clip", "2.0", "--xval", "log"),
            "N_excl": auto + ("--norm_clip", "2.0", "--oracle_mal_weight", "0"),
            "N_xval_loo": auto + ("--norm_clip", "2.0", "--xval", "weight", "--xval_score", "loo"),
            "N_xval_self": auto + ("--norm_clip", "2.0", "--xval", "weight",
                                   "--xval_score", "self"),
            # gate P (results/Phase_ex/L/gate_p_plan.md): clients also send per-label k-means
            # centroids of their image features; the server checks each against the global model
            # and rebuilds the update the verified ones imply. P_log records only (and must equal
            # L_clip); P_rec swaps the rebuilt update in for flagged clients; P_rec_hide faces an
            # attacker that sends prototypes of its clean images only.
            "P_log": auto + ("--norm_clip", "2.0", "--proto", "log"),
            "P_rec": auto + ("--norm_clip", "2.0", "--proto", "replace"),
            "P_rec_hide": auto + ("--norm_clip", "2.0", "--proto", "replace",
                                  "--proto_lie", "hide"),
        })
        # L_ARMS is a list (same arms on every dataset) or {dataset: [arms]} to merge sessions
        for a in (L_ARMS.get(ds, []) if isinstance(L_ARMS, dict) else L_ARMS):
            job(a, arms[a])
    elif MODE == "gate_r_device":
        # Gate R (results/Phase_ex/R/gate_r_plan.md): the device attacker ALONE. 8 honest + 2
        # device attackers, no careless client, so what the server-side defences do against the
        # attacker is measured without noise mixed in. Same seeds as gate L.
        solo = ("--noisy_client_frac", "0", "--log_asr", "true")
        auto = base_f + ("--sample_filter", "rho", "--filter_soft", "auto") + band + solo
        r_arms = {
            "R_none": base_f + solo,                                     # no defence at all
            "R_base": auto,                                              # client filter only
            "R_clip": auto + ("--norm_clip", "2.0"),                     # + 2x-median norm clip
            "R_prec": auto + ("--norm_clip", "2.0", "--proto", "replace"),   # + prototype check
            "R_oracle60": auto + ("--sample_oracle", "drop_dirty_mal"),  # attackers learn clean 60% only
            # gate R2 (results/Phase_ex/R/gate_r2_plan.md): fewer prototype sends. The check
            # and rebuild still run every round, from the last prototypes the client sent
            "R_prec_once": auto + ("--norm_clip", "2.0", "--proto", "replace",
                                   "--proto_every", "once"),
            "R_prec_refresh": auto + ("--norm_clip", "2.0", "--proto", "replace",
                                      "--proto_every", "refresh"),
            # gate R3 (results/Phase_ex/R/gate_r3_plan.md): attackers aimed at the one send.
            # hide: sends prototypes of its clean images only; turncoat: also trains on its
            # clean images in round 0, so its round-0 update looks honest too
            "R_prec_once_hide": auto + ("--norm_clip", "2.0", "--proto", "replace",
                                        "--proto_every", "once", "--proto_lie", "hide"),
            "R_prec_once_turncoat": auto + ("--norm_clip", "2.0", "--proto", "replace",
                                            "--proto_every", "once", "--proto_lie", "turncoat"),
            # gate R4 (results/Phase_ex/R/gate_r4_plan.md): the attacker fabricates prototypes
            # that pass the label check AND whose rebuild points along its poisoned update
            "R_prec_forge": auto + ("--norm_clip", "2.0", "--proto", "replace",
                                    "--proto_lie", "forge"),
            "R_prec_once_forge": auto + ("--norm_clip", "2.0", "--proto", "replace",
                                         "--proto_every", "once", "--proto_lie", "forge"),
        }
        for a in R_ARMS:
            job(a, r_arms[a])
    elif MODE == "gate_q_noise":
        # Gate Q (results/Phase_bonus/gate_q_plan.md): the client-side method on NOISE ALONE.
        # 7 honest + 3 careless clients, no attacker at all, so what the filter and the relabel do
        # to careless clients is measured without an attacker mixed in. Same seeds, so the
        # all-clean oracle K_restore (every label correct, 10 clean clients) is the ceiling.
        # The later --malicious_client_frac 0 overrides base()'s MAL_FRAC (argparse keeps the last).
        clean_att = ("--attack_type", "none", "--malicious_client_frac", "0")
        filt = clean_att + ("--correction_audit", "true", "--sample_filter", "rho",
                            "--filter_soft", "auto") + band
        q_arms = {
            "Q_none": clean_att,
            "Q_filter": filt,
            "Q_fixconf": filt + ("--filter_relabel", "conf", "--filter_relabel_conf", "0.5"),
            # optional: an all-clean run of this exact configuration, if K_restore is not trusted
            # as the ceiling (it restores the same labels but was run with the attack switched on)
            "Q_clean": clean_att + ("--noise_type", "none", "--noise_rate", "0"),
            # gate Q-MAE (results/Phase_bonus/gate_q_mae_plan.md): the robust-loss competitor in the
            # same setting. MAE is the loss NLPrompt builds on; it changes only the client loss,
            # no filtering. Q_mae_fixconf asks whether the two combine
            "Q_mae": clean_att + ("--loss_type", "mae"),
            "Q_mae_fixconf": filt + ("--filter_relabel", "conf", "--filter_relabel_conf", "0.5",
                                     "--loss_type", "mae"),
        }
        # gate V (results/side-research/gate_V/gate_v_plan.md): other noise types. V_<noise>_<arm>,
        # noise pair (flip to the next class) or inst (instance-dependent, Xia et al. 2020), 40%
        # on the same 3 careless clients; sym reuses the stored Q_ runs. far = DBR-FPL whose
        # budget skips disagreements landing on a look-alike class of the label
        for nk, nt in (("pair", "pair"), ("inst", "instance"), ("sym", "sym")):
            nz = ("--noise_type", nt)
            q_arms[f"V_{nk}_none"] = clean_att + nz
            q_arms[f"V_{nk}_mae"] = clean_att + nz + ("--loss_type", "mae")
            q_arms[f"V_{nk}_dbr"] = q_arms["Q_fixconf"] + nz
            q_arms[f"V_{nk}_far"] = q_arms["Q_fixconf"] + nz + ("--filter_dis", "far",
                                                                 "--filter_far_k", "1")
        # gate D stage 1 (results/side-research/gate_D/gate_d1_plan.md): the diagnostic runs.
        # D_<scenario>_<arm>; every run logs each client's candidate noise scores every round
        # (logged only, training unchanged) and one row per image every 5 rounds.
        diag = ("--diag_scores", "true", "--diag_samples_every", "5")
        scen = {"sym": (),
                "pair": ("--noise_type", "pair"),
                "inst": ("--noise_type", "instance"),
                # 5 careless clients at 0.16 / 0.32 / 0.48 / 0.64 / 0.80 (FedCorr-style spread)
                "het": ("--noise_mode", "hetero", "--noise_rate", "0.8",
                        "--noisy_client_frac", "0.5"),
                # nobody is careless: every flag raised here is a false accusation
                # sym at rate 0 rather than type none: type none skips the injector, which left the
                # labels as numpy strings (the audit crashed) and wrote no noise json (no scores)
                "clean": ("--noise_rate", "0", "--noisy_client_frac", "0")}
        for sk, sx in scen.items():
            q_arms[f"D_{sk}_none"] = clean_att + sx + diag
            q_arms[f"D_{sk}_mae"] = clean_att + sx + diag + ("--loss_type", "mae")
            q_arms[f"D_{sk}_dbr"] = q_arms["Q_fixconf"] + sx + diag
        for a in (Q_ARMS.get(ds, []) if isinstance(Q_ARMS, dict) else Q_ARMS):
            job(a, q_arms[a])
    elif MODE == "gate_k_proto":
        # Gate K with cluster-level suspect selection (results/Phase_bonus/gate_k_proto_plan.md):
        # suspects are the images of label clusters the global model / zero-shot CLIP do not read
        # as their label; each suspect is then relabelled on its own. Same seeds as K_base /
        # K_fix / K_fixconf (stored in REFERENCE). K_restore is the all-clean ceiling measured in
        # this exact configuration: every damaged label, noisy and malicious, put back.
        plain = ("--data_transform", TRAIN_TRANSFORM,
                 "--noise_type", "sym", "--noise_rate", str(NOISY_RATE),
                 "--noisy_client_frac", str(NOISY_FRAC),
                 "--malicious_client_frac", str(MAL_FRAC), "--attacker_model", "data",
                 "--log_asr", "true") + atk
        k_arms = {
            "K_proto": base_f + ("--sample_filter", "proto", "--filter_relabel_conf", "0.5",
                                 "--log_asr", "true"),
            "K_restore": plain + ("--sample_oracle", "restore_dirty"),
            # K_proto plus K_fixconf's two safeguards: the clean band (clients near the clean
            # baseline are left alone) and the server's hard/soft decision (relabel/delete only in
            # hard rounds, with the global model as teacher; soft rounds down-weight suspects)
            "K_proto_band": base_f + ("--sample_filter", "proto", "--proto_band", "true",
                                      "--filter_soft", "auto") + band
                            + ("--filter_relabel_conf", "0.5", "--log_asr", "true"),
        }
        for a in K_ARMS:
            if a == "K_restore":
                PLAN.append((ds, "CoOp", TIMES, GLOBAL_ROUNDS, f"{ds}_{a}", k_arms[a],
                             "PromptFL", a))
            else:
                job(a, k_arms[a])
    elif MODE == "gate_k_prior":
        # Rule A from the gate_k_diag offline test: relabel by the global model's top 3
        # re-ranked with the client's own capped label histogram. Same seeds as K_base / K_fix /
        # K_fixconf, so it pairs against all three. Criteria: gate_k_plan.md, addendum 2.
        auto = base_f + ("--sample_filter", "rho", "--filter_soft", "auto") + band
        job("K_prior", auto + ("--filter_relabel", "prior"))
    elif MODE == "gate_k_diag":
        # K_fix rerun with every filter refresh logging each sample's label, true label and the
        # global model's top-3, so other relabel rules (client prior, stability, no relabel into
        # an over-full class) can be scored offline on the same suspects:
        # python tools/score_relabel_rules.py <runs dir>. Same seeds as K_fix, so its accuracy
        # must reproduce K_fix's -- a free check that the logging changed nothing.
        auto = base_f + ("--sample_filter", "rho", "--filter_soft", "auto") + band
        job("K_fix_log", auto + ("--filter_relabel", "all", "--filter_relabel_log", "true"))
    elif MODE == "gate_k_relabel":
        # Relabel suspects instead of deleting them, only where the global model is good.
        # Criteria written before running: results/Phase_bonus/gate_k_plan.md.
        # Both arms run under --filter_soft auto, so relabelling only happens in rounds where
        # the server has already judged the global model good enough to delete on.
        auto = base_f + ("--sample_filter", "rho", "--filter_soft", "auto") + band
        # the current method rerun with the data-only attacker, so K_fix/K_fixconf pair against
        # a baseline that differs from them in one thing only -- and so K_base against the old
        # H_auto measures what changing the attacker did on its own
        job("K_base", auto)
        job("K_fix", auto + ("--filter_relabel", "all"))
        job("K_fixconf", auto + ("--filter_relabel", "conf", "--filter_relabel_conf", "0.5"))
    elif MODE == "gate_j_regime":
        # PRIORITY 3. A dataset the 0.22 threshold has never seen. Four arms, because a held-out
        # test of a SELECTION rule needs both things it selects between plus the rule itself:
        #   A0_refuse   the no-defence reference this dataset does not have yet
        #   H_soft      down-weighting, forced
        #   H_band      deletion, forced
        #   H_auto      the server chooses
        # The rule passes only if H_auto matches whichever of H_soft/H_band wins. If it matches
        # the LOSER the rule is refuted, and that is a real possibility worth naming in advance:
        # baseline predicts precision at r = -0.53 BETWEEN datasets but essentially not within
        # one (on DTD the rounds it calls hard have LOWER precision, 0.618 vs 0.665), so the
        # whole rule rests on a between-dataset regularity fitted to two points.
        #
        # Expected placement on the threshold, from clean PromptFL accuracy (the teacher's own
        # ceiling, which is what the baseline measures):
        #   EuroSAT     10 classes, clean accuracy low  -> high baseline -> should pick SOFT
        #   Caltech101  102 classes, clean 90.9         -> low baseline  -> should pick HARD
        # Neither sits ON the boundary. Food101 does (clean ~76 puts it near 0.25) but costs
        # 96 s/round, ~20 h for these four arms, so it is the follow-up, not this session.
        #
        # Run ONE dataset per session: EuroSAT is ~1.5 h at 5 seeds, Caltech101 ~11.6 h, so
        # Caltech wants TIMES = 3 or a 12 h budget.
        arms = {
            "A0_refuse": atk,
            "H_soft": base_f + ("--sample_filter", "rho", "--filter_soft", "true") + band,
            "H_band": base_f + ("--sample_filter", "rho") + band,
            "H_auto": base_f + ("--sample_filter", "rho", "--filter_soft", "auto") + band,
        }
        unknown = [a for a in REGIME_ARMS if a not in arms]
        if unknown:
            raise ValueError(f"REGIME_ARMS: unknown {unknown}, pick from {sorted(arms)}")
        for a in REGIME_ARMS:
            job(a, arms[a])
    elif MODE == "gate_h_diag":
        # The one question the oracle ladder left open. L_drop recovered 6.02 of 8.39 points by
        # deleting exactly the damaged samples, so the whole remaining problem is a yes/no call
        # per sample. This logs every candidate signal next to the ground truth, once, cheaply.
        job("S_diag", atk + ("--sample_diag", "true", "--correction_audit", "true"), times=1)
    elif MODE == "gate_h_oracle":
        # Ceilings, not methods. Every defence so far acts on whole clients and gate F measured
        # that even perfect instant client removal buys ~1 point. These say what is available
        # at the sample level if it were solved perfectly, and how much of the gap labels
        # explain at all. No probes, so each job is a plain run.
        plain = ("--data_transform", TRAIN_TRANSFORM,
                 "--noise_type", "sym", "--noise_rate", str(NOISY_RATE),
                 "--noisy_client_frac", str(NOISY_FRAC),
                 "--malicious_client_frac", str(MAL_FRAC)) + atk

        def oracle(tag, extra):
            PLAN.append((ds, "CoOp", TIMES, GLOBAL_ROUNDS, f"{ds}_{tag}",
                         plain + tuple(extra), "PromptFL", tag))

        # F: every damaged label put back. Same split, same seeds, so this IS the all-clean
        # ceiling measured in exactly this configuration rather than borrowed from phase 1.
        oracle("L_restore", ("--sample_oracle", "restore_dirty"))
        # C: every damaged sample deleted. The poison goes and so does that data; the gap to
        # L_restore is the price of throwing a sample away instead of fixing it.
        oracle("L_drop", ("--sample_oracle", "drop_dirty"))
        # A: the client-level ceiling -- drop all five damaged clients, noisy and malicious.
        oracle("L_clientdrop", ("--attack_oracle", "drop_malicious",
                                "--noise_oracle", "drop_noisy"))
    elif MODE == "gate_g_atk":
        # with the attacker: the same thresholds measured as a DEFENCE. Answers G2. Split into
        # its own session so neither half sits near the budget guard.
        for q in CONF_QUANTILES:
            gate = ("--correction_conf", str(q), "--correction_conf_mode", "quantile",
                    "--correction_audit", "true")
            job(f"A1_audit_q{int(q * 100)}", atk + audit + gate)
    else:
        raise ValueError(MODE)

total_h = sum(estimate_seconds(*item[:4]) for item in PLAN) / 3600 * 1.15
print(f"{MODE}: {len(PLAN)} jobs on {DATASETS}, expected ~{total_h:.1f} h (BUDGET_HOURS = {BUDGET_HOURS})")
for item in PLAN:
    run_flip(*item)
print(f"notebook finished after {(time.time() - NOTEBOOK_START) / 3600:.2f} h")
# zip the runs NOW, before any analysis: an analysis bug must never cost the download (gate N
# session N2 died in the analysis cell, after 5 GPU hours of finished runs, and the package cell
# after it never ran). The last cell re-zips with whatever the analysis adds.
_early = shutil.make_archive(f"{WORK}/{RESULT_NAME}", "zip", OUT)
print("runs packaged:", _early)


def correction_report(tag):
    # Printed here rather than in the collect cell so a committed run shows it as soon as the
    # job ends. Ground truth comes from clean_targets, which the server never sees.
    rows = []
    try:
        for line in open(f"{OUT}/logs/{tag}.txt", encoding="utf-8", errors="ignore"):
            i = line.find("CORRECTION_AUDIT ")
            if i >= 0:
                rows.append(json.loads(line[i + len("CORRECTION_AUDIT "):]))
    except OSError:
        return
    if not rows:
        return
    print("")
    print(f"=== correction quality, {tag} ===")
    print(f"{'slice':22s} {'n':>6s} {'labels ok':>10s} {'teacher ok':>11s} "
          f"{'fixed':>7s} {'broken':>7s} {'net':>8s}")

    def line(sel, name):
        if not sel:
            return
        f = sum(x["fixed"] for x in sel)
        b = sum(x["broken"] for x in sel)
        print(f"{name:22s} {sum(x['n'] for x in sel):6d} "
              f"{statistics.fmean(x['label_acc'] for x in sel) * 100:9.1f}% "
              f"{statistics.fmean(x['teacher_acc'] for x in sel) * 100:10.1f}% "
              f"{f:7d} {b:7d} {f - b:+8d}")

    line(rows, "ALL")
    line([x for x in rows if x["label_acc"] < 0.9], "noisy clients")
    line([x for x in rows if x["label_acc"] >= 0.9], "clean clients")
    for lo, hi in ((0, 10), (10, 25), (25, 40), (40, 51)):
        line([x for x in rows if lo <= x["round"] < hi], f"  rounds {lo}-{hi}")
    line([x for x in rows if x["label_acc"] < 0.9 and x["round"] >= 25],
         "noisy, rounds 25+")
    print("net > 0 means the correction repairs more labels than it destroys.")


if MODE in ("gate_h_filter", "gate_i_seeds", "gate_i_score", "gate_i_pets",
            "gate_j_auto", "gate_j_regime", "gate_k_relabel", "gate_l_device", "gate_k_diag", "gate_k_prior", "gate_k_proto", "gate_q_noise", "gate_r_device"):
  sys.path.insert(0, f"{CODE}/tools")
  from parse_flip_log import parse_log

  # a session may run several datasets (gate L merges them): one report per dataset, so arms
  # of the same name on different datasets never overwrite each other
  def _ds_index(d):
      return {t: e for t, e in load_index().items() if e.get("dataset") == d}
  for _ds in DATASETS:
      print("")
      print(f"##### {_ds} #####")
      ref = REFERENCE.get(_ds, {})
      rows = {}
      for tag, e in sorted(_ds_index(_ds).items()):
          if e["returncode"] == 0:
              rows[e["variant"]] = [statistics.fmean(c[-10:]) for c in parse_log(e["log"])[0]]
      print("")
      print("=== sample-level filtering ===")
      print("  measured exchange rate: +0.326/1000 per damaged sample removed,")
      print("  -0.437/1000 per clean one -> break-even precision 57.3%")
      # A0_refuse may come from this run (gate_j_regime runs it) or from REFERENCE (DTD, Pets).
      # A dataset with neither gets absolute numbers only, which is honest -- better than
      # silently pairing against the wrong dataset's baseline, and the earlier hardcoded 47.56
      # would have done exactly that on EuroSAT or Caltech.
      nodef = rows.get("A0_refuse") or ref.get("A0_refuse")
      if nodef:
          print(f"  {'A0_refuse (no defence)':28s} {statistics.fmean(nodef):6.2f}")
      else:
          print(f"  no A0_refuse for {_ds}: differences against it are not shown")
      for tag, e in sorted(_ds_index(_ds).items()):
          if e["returncode"] != 0:
              continue
          vals = rows[e["variant"]]
          line = f"  {e['variant']:28s} {statistics.fmean(vals):6.2f}"
          if nodef and len(nodef) == len(vals):
              d = [a - b for a, b in zip(vals, nodef)]
              sd = statistics.stdev(d) if len(d) > 1 else 0.0
              line += f"   recovers {statistics.fmean(d):+5.2f} +- {sd:.2f}"
          print(line)
          # what the rule actually did to the data, by role
          acc, modes = {}, [0, 0]
          for path in glob.glob(f"{OUT}/runs/{tag}/**/noise_seed_*.json", recursive=True):
              for rec in json.load(open(path)).get("filter", []):
                  if rec.get("round", 0) > 0:
                      modes[0 if rec.get("hard") else 1] += 1
                  for v in rec["clients"].values():
                      a = acc.setdefault(v["role"], [0, 0, 0])
                      a[0] += v["dropped"]; a[1] += v["n"]; a[2] += v["dropped_damaged"]
          for role, (dr, n, dm) in sorted(acc.items()):
              print(f"      {role:10s} dropped {dr}/{n} ({100 * dr / max(n, 1):4.1f}%), "
                    f"of which actually damaged {dm} ({100 * dm / max(dr, 1):4.1f}%)")
          if sum(modes):
              print(f"      server chose HARD on {100 * modes[0] / sum(modes):4.1f}% of "
                    f"probe rounds, SOFT on {100 * modes[1] / sum(modes):4.1f}%")
      # arms measured in earlier sessions on the same seeds count as rows for the comparisons
      for k, v in ref.items():
          rows.setdefault(k, v)
      if MODE in ("gate_l_device", "gate_r_device"):
          for tag, e in sorted(_ds_index(_ds).items()):
              if e["returncode"] != 0:
                  continue
              asr, tacc = [], []
              for path in glob.glob(f"{OUT}/runs/{tag}/**/noise_seed_*.json", recursive=True):
                  recs = [r for r in json.load(open(path)).get("asr", []) if r["round"] >= 40]
                  for r in recs:
                      for v in r["clients"].values():
                          if v["asr"] is not None:
                              asr.append(v["asr"])
                          if v["target_acc"] is not None:
                              tacc.append(v["target_acc"])
              if asr:
                  print(f"  {e['variant']}: last-10 ASR {100 * statistics.fmean(asr):.2f}%, "
                        f"accuracy on the real target class {100 * statistics.fmean(tacc):.1f}%")
              by_role = {}
              for path in glob.glob(f"{OUT}/runs/{tag}/**/noise_seed_*.json", recursive=True):
                  for rec in json.load(open(path)).get("refusal", []):
                      for r in rec.get("roles_flagged") or []:
                          by_role[r] = by_role.get(r, 0) + 1
              print(f"  {e['variant']}: flagged decisions by role {by_role or 'none'}")
              xv = {"loo": {"mal": [], "oth": []}, "self": {"mal": [], "oth": []}}
              wr = {}
              for path in glob.glob(f"{OUT}/runs/{tag}/**/noise_seed_*.json", recursive=True):
                  for rec in json.load(open(path)).get("xval", []):
                      for v in rec["clients"].values():
                          g = "mal" if v["role"] == "malicious" else "oth"
                          for m in xv:
                              xv[m][g].append(v[m])
                          wr.setdefault(v["role"], []).append(v["weight"])
              pc, rp, sends, forged = {}, {}, [], {}
              for path in glob.glob(f"{OUT}/runs/{tag}/**/noise_seed_*.json", recursive=True):
                  per = {}
                  for rec in json.load(open(path)).get("proto", []):
                      for cid, v in rec["clients"].items():
                          per[cid] = per.get(cid, 0) + int(v.get("fresh", True))
                          rp.setdefault(v["role"], []).append(int(v["replaced"] or v["flag"]))
                          for lab, mass, pur, pred, conf, ok, *_ in v["cents"]:
                              kind = "flipped" if pur < 0.5 else "clean" if pur >= 0.9 else "mixed"
                              pc.setdefault((v["role"], kind), []).append(ok)
                  sends += list(per.values())
                  for rec in json.load(open(path)).get("proto", []):
                      for v in rec["clients"].values():
                          if v.get("forge"):
                              forged.setdefault("cos0", []).append(v["forge"]["cos_start"])
                              forged.setdefault("cos1", []).append(v["forge"]["cos_end"])
                              forged.setdefault("pass", []).append(v["forge"]["pass_end"])
              if sends:
                  print(f"  {e['variant']}: prototype sends per client per run "
                        f"{statistics.fmean(sends):.1f}")
              if forged:
                  print(f"  {e['variant']}: forged sends {len(forged['cos0'])}, cosine "
                        f"{statistics.fmean(forged['cos0']):.3f} -> {statistics.fmean(forged['cos1']):.3f}, "
                        f"centroids passing {100 * statistics.fmean(forged['pass']):.0f}%")
              if pc:
                  print(f"  {e['variant']}: prototype pass rate "
                        + ", ".join(f"{r}/{k} {100 * statistics.fmean(v):.0f}% (n={len(v)})"
                                    for (r, k), v in sorted(pc.items()))
                        + " | flagged rounds " + ", ".join(f"{r} {100 * statistics.fmean(v):.0f}%"
                                                           for r, v in sorted(rp.items())))
              if wr:
                  def _auc(p, n):
                      return sum((a > b) + 0.5 * (a == b) for a in p for b in n) / max(len(p) * len(n), 1)
                  print(f"  {e['variant']}: xval per-round AUC loo {_auc(xv['loo']['mal'], xv['loo']['oth']):.3f}, "
                        f"self {_auc(xv['self']['mal'], xv['self']['oth']):.3f}; mean weight by role "
                        + ", ".join(f"{r} {statistics.fmean(v):.2f}" for r, v in sorted(wr.items())))
              cuts, right, clip = {}, 0, {}
              for path in glob.glob(f"{OUT}/runs/{tag}/**/noise_seed_*.json", recursive=True):
                  for rec in json.load(open(path)).get("tdr", []):
                      for v in rec["clients"].values():
                          clip.setdefault(v["role"], []).append(v.get("clip_scale", 1.0))
                          if v.get("cut_norm", 0) > 0:
                              cuts[v["role"]] = cuts.get(v["role"], 0) + 1
                              right += int(v["role"] == "malicious"
                                           and v.get("target_hat") == v.get("true_target"))
              if cuts:
                  print(f"  {e['variant']}: TDR cuts by role {cuts}, right target on "
                        f"{right}/{cuts.get('malicious', 0)} malicious cuts; mean clip scale "
                        + ", ".join(f"{r} {statistics.fmean(v):.3f}" for r, v in sorted(clip.items())))
      if MODE in ("gate_k_relabel", "gate_k_proto", "gate_q_noise"):
          for tag, e in sorted(_ds_index(_ds).items()):
              if e["returncode"] != 0:
                  continue
              tot = {"relabeled": 0, "relabel_fixed": 0, "relabel_broken": 0}
              for path in glob.glob(f"{OUT}/runs/{tag}/**/noise_seed_*.json", recursive=True):
                  for rec in json.load(open(path)).get("filter", []):
                      for v in rec["clients"].values():
                          for k in tot:
                              tot[k] += v.get(k, 0)
              print(f"  {e['variant']}: relabelled {tot['relabeled']} label-rounds, "
                    f"fixed {tot['relabel_fixed']}, broke {tot['relabel_broken']}")
              sus = {}
              for path in glob.glob(f"{OUT}/runs/{tag}/**/noise_seed_*.json", recursive=True):
                  for rec in json.load(open(path)).get("filter", []):
                      for v in rec["clients"].values():
                          if "suspects" in v:
                              a_ = sus.setdefault(v["role"], [0, 0, 0])
                              a_[0] += v["suspects"]; a_[1] += v["suspects_damaged"]; a_[2] += v["damaged"]
              for r, (ns, nd, dm) in sorted(sus.items()):
                  print(f"      {r:10s} suspects {ns}, of which damaged {nd} "
                        f"({100 * nd / max(ns, 1):.1f}%), catching {100 * nd / max(dm, 1):.1f}% of the damage")
      # the head-to-heads
      for a, b in (("H_soft", "H_band"), ("H_auto", "H_soft"), ("H_auto", "H_band"),
                   ("K_fix", "K_base"), ("K_fixconf", "K_base"), ("K_fixconf", "K_fix"),
                   ("K_prior", "K_base"), ("K_prior", "K_fix"), ("K_prior", "K_fixconf"),
                   ("K_proto", "K_base"), ("K_proto", "K_fixconf"), ("K_restore", "K_fixconf"),
                   ("K_proto", "K_restore"), ("K_proto_band", "K_fixconf"),
                   ("K_proto_band", "K_proto"), ("K_proto_band", "K_restore"),
                   ("Q_filter", "Q_none"), ("Q_fixconf", "Q_none"), ("Q_fixconf", "Q_filter"),
                   ("K_restore", "Q_fixconf"), ("K_restore", "Q_none"),
                   ("R_clip", "R_none"), ("R_prec", "R_none"), ("R_prec", "R_clip"),
                   ("R_oracle60", "R_prec"), ("R_oracle60", "R_none"), ("R_base", "R_none"),
                   ("K_restore", "R_prec"), ("R_prec", "L_clip"), ("R_prec", "P_rec"),
                   ("R_prec_once", "R_prec"), ("R_prec_refresh", "R_prec"),
                   ("R_prec_once", "R_clip"), ("R_prec_refresh", "R_clip"),
                   ("R_prec_once", "R_prec_refresh"), ("R_oracle60", "R_prec_once"),
                   ("R_oracle60", "R_prec_refresh"),
                   ("R_prec_once_hide", "R_prec_once"), ("R_prec_once_turncoat", "R_prec_once"),
                   ("R_prec_once_hide", "R_clip"), ("R_prec_once_turncoat", "R_clip"),
                   ("R_prec_once_turncoat", "R_prec_once_hide"),
                   ("Q_mae", "Q_none"), ("Q_fixconf", "Q_mae"), ("Q_mae_fixconf", "Q_fixconf"),
                   ("Q_mae_fixconf", "Q_mae"), ("K_restore", "Q_mae"),
                   ("R_prec_forge", "R_prec"), ("R_prec_forge", "R_clip"),
                   ("R_prec_once_forge", "R_prec_once"), ("R_prec_once_forge", "R_clip"),
                   ("R_prec_once_forge", "R_prec_forge"),
                   ("K_base", "H_auto"), ("L_down", "L_base"), ("L_base", "H_auto"),
                   ("L_tdr", "L_base"), ("L_oracle60", "L_base"), ("L_down", "L_tdr"),
                   ("L_tdr_early", "L_tdr"), ("L_tdr_conc", "L_tdr"), ("L_tdr_true", "L_tdr"),
                   ("L_tdr_rand", "L_tdr"), ("L_clip", "L_tdr"), ("L_clip", "L_base"),
                   ("L_tdr_conc", "L_base"), ("L_tdr_true", "L_base"), ("L_clip_down", "L_clip"),
                   ("L_clip_down", "L_base"), ("N_log", "L_clip"), ("N_excl", "L_clip"),
                   ("N_xval_loo", "L_clip"), ("N_xval_self", "L_clip"), ("N_excl", "L_oracle60"),
                   ("P_log", "L_clip"), ("P_rec", "L_clip"), ("P_rec", "L_clip_down"),
                   ("P_rec", "N_excl"), ("P_rec", "L_oracle60"), ("P_rec_hide", "P_rec"),
                   ("V_sym_far", "Q_fixconf"), ("V_sym_far", "Q_mae"), ("V_sym_far", "Q_none"),
                   *[(f"V_{_n}_{_a}", f"V_{_n}_{_b}") for _n in ("pair", "inst")
                     for _a, _b in (("far", "dbr"), ("far", "mae"), ("dbr", "mae"),
                                    ("far", "none"), ("dbr", "none"), ("mae", "none"))],
                   *[("K_restore", f"V_{_n}_{_a}") for _n in ("pair", "inst")
                     for _a in ("far", "dbr", "mae", "none")],
                   *[(f"D_{_n}_{_a}", f"D_{_n}_{_b}") for _n in ("sym", "pair", "inst", "het", "clean")
                     for _a, _b in (("dbr", "none"), ("mae", "none"), ("dbr", "mae"))],
                   *[("K_restore", f"D_{_n}_{_a}") for _n in ("sym", "pair", "inst", "het", "clean")
                     for _a in ("none", "mae", "dbr")],
                   ("D_sym_dbr", "Q_fixconf"), ("D_sym_none", "Q_none"), ("D_sym_mae", "Q_mae")):
          if a in rows and b in rows and len(rows[a]) == len(rows[b]) and len(rows[a]) > 1:
              d = [x - y for x, y in zip(rows[a], rows[b])]
              m, sd = statistics.fmean(d), statistics.stdev(d)
              t = m / (sd / len(d) ** 0.5) if sd else float("inf")
              print(f"  {a} - {b}: {m:+5.2f} +- {sd:.2f}  t = {t:+5.2f}  (paired, n = {len(d)})")
      if MODE in ("gate_h_filter", "gate_i_seeds", "gate_i_score"):
          print("  L_drop  53.58  (+6.02) = perfect sample deletion")
          print("  L_restore 55.94 (+8.39) = perfect label repair, the all-clean ceiling")
      if MODE == "gate_j_regime":
          print("  PASS if H_auto matches whichever of H_soft / H_band is higher.")
          print("  FAIL if it matches the lower one: the 0.22 threshold was fitted on two")
          print("  datasets and this is the first one it has not seen.")

if MODE == "gate_h_diag":
    sys.path.insert(0, f"{CODE}/tools")
    import score_sample_signals as sss
    for tag, e in sorted(load_index().items()):
        if e["returncode"] == 0:
            recs = sss.derived(sss.load(f"{OUT}/runs/{tag}"))
            if not recs:
                print(f"{tag}: no samples_seed_*.json")
                continue
            print(f"=== {tag}: {len(recs)} sample-rounds ===")
            sss.report(recs, "ALL clients")
            for role in ("noisy", "malicious"):
                sss.report([r for r in recs if r["role"] == role], f"{role} clients only")
            sss.report([r for r in recs if r["round"] >= 25],
                       "ALL clients, rounds 25+ (teacher is stronger)")
    print("")
    print("AUC 1.0 = the signal ranks every damaged sample above every clean one.")
    print("Target to chase: L_drop = 53.58, which perfect detection would reach.")

if MODE == "gate_h_oracle":
    sys.path.insert(0, f"{CODE}/tools")
    from parse_flip_log import parse_log
    ref = REFERENCE.get(DATASETS[0], {})
    rows = {}
    for tag, e in sorted(load_index().items()):
        if e["returncode"] == 0:
            rows[e["variant"]] = [statistics.fmean(c[-10:]) for c in parse_log(e["log"])[0]]
    print("")
    print("=== the ladder: what each level of intervention could buy, perfectly done ===")
    order = [("A0_refuse", "no defence"), ("L_clientdrop", "drop all 5 damaged CLIENTS"),
             ("L_drop", "drop every damaged SAMPLE"), ("L_restore", "restore every damaged LABEL"),
             ("N_control", "no attacker at all (3 noisy remain)")]
    base = (rows.get("A0_refuse") or ref.get("A0_refuse"))
    for name, what in order:
        vals = rows.get(name) or ref.get(name)
        if not vals:
            continue
        line = f"  {name:14s} {statistics.fmean(vals):6.2f}  {what}"
        if base and name != "A0_refuse" and len(base) == len(vals):
            d = [a - b for a, b in zip(vals, base)]
            line += f"   recovers {statistics.fmean(d):+5.2f} of the gap"
        print(line)
    print("  L_restore is the all-clean ceiling measured in this exact configuration.")
    print("  L_restore - L_drop = the price of deleting a sample instead of repairing it.")
    print("  55.61 - L_restore = what label damage does NOT explain (scarcity, non-IID, drift).")

if MODE.startswith("gate_g"):
    sys.path.insert(0, f"{CODE}/tools")
    from parse_flip_log import parse_log

    idx = load_index()
    for tag in sorted(idx):
        correction_report(tag)

    print("")
    print("=== accuracy, paired by seed against the stored references ===")
    ref = REFERENCE.get(DATASETS[0], {})
    for tag, e in sorted(idx.items()):
        if e["returncode"] != 0:
            continue
        vals = [statistics.fmean(c[-10:]) for c in parse_log(e["log"])[0]]
        line = f"  {e['variant']:22s} {statistics.fmean(vals):6.2f}"
        for name in ("N_control", "N_audit"):
            base = ref.get(name)
            if base and len(base) == len(vals) and len(vals) > 1:
                d = [a - b for a, b in zip(vals, base)]
                line += (f"   vs {name} {statistics.fmean(d):+5.2f}"
                         f" +- {statistics.stdev(d):.2f}")
        print(line)
    print("  N_audit itself gained +0.86 over N_control on DTD; that is the number to beat.")
'''
PLAN_CELL[5] = '''
# --- plan: the disguised attack again, this time with the correction probe running ----------
PLAN = []
for ds in DATASETS:
    base = ("--data_transform", TRAIN_TRANSFORM,
            "--noise_type", "sym", "--noise_rate", str(NOISY_RATE),
            "--noisy_client_frac", str(NOISY_FRAC),
            "--malicious_client_frac", str(MAL_FRAC),
            # the probe is scored against CLIP's own class embeddings, which are only built
            # when the signal machinery is on; it also gives us s_upd for the D3 comparison
            "--log_signals", "true",
            "--correction_every", str(CORRECTION_EVERY),
            "--attack_lie", ATTACK_LIE)
    for attack in ATTACKS:
        tag = "N_control" if attack == "none" else "P0_disguise"
        extra = ("--attack_rate", str(NOISY_RATE)) if attack == "noise_disguise" else ()
        PLAN.append((ds, "CoOp", TIMES, GLOBAL_ROUNDS, f"{ds}_{tag}",
                     base + ("--attack_type", attack) + extra, "PromptFL", tag))

total_h = sum(estimate_seconds(*item[:4]) for item in PLAN) / 3600 * 1.1   # + probe overhead
print(f"{MODE}: {len(PLAN)} jobs on {DATASETS}, expected ~{total_h:.1f} h (BUDGET_HOURS = {BUDGET_HOURS})")
for item in PLAN:
    run_flip(*item)
print(f"notebook finished after {(time.time() - NOTEBOOK_START) / 3600:.2f} h")
'''
PLAN_CELL[4] = '''
# --- plan: the gate B configurations again, with per-client signals logged ------------------
PLAN = []
# the confound run already produced every cell but one; this mode runs only the missing one
ONLY = {"gate_c_confound_food": [("food101", "noise_disguise")]}.get(MODE)
if MODE == "gate_c_confound_food":
    # the training-gain axis of the hypothesis was never measured on these two datasets, and
    # zero-shot costs minutes, so pin the floor here instead of quoting the FLIP paper
    for ds in DATASETS:
        PLAN.append((ds, "CLIP", 1, GLOBAL_ROUNDS, f"{ds}_ZSCLIP",
                     ("--data_transform", TRAIN_TRANSFORM), "ZSCLIP", "ZSCLIP"))
for ds in DATASETS:
    base = ("--data_transform", TRAIN_TRANSFORM,
            "--noise_type", "sym", "--noise_rate", str(NOISY_RATE),
            "--noisy_client_frac", str(NOISY_FRAC),
            "--malicious_client_frac", str(MAL_FRAC),
            "--log_signals", "true")
    for attack in ATTACKS:
        if ONLY is not None and (ds, attack) not in ONLY:
            continue
        tag = {"none": "N_control", "noise_disguise": "P0_disguise",
               "targeted_flip": "P1_targeted", "signflip": "P2_signflip"}[attack]
        extra = ("--attack_rate", str(NOISY_RATE)) if attack == "noise_disguise" else ()
        PLAN.append((ds, "CoOp", TIMES, GLOBAL_ROUNDS, f"{ds}_{tag}",
                     base + ("--attack_type", attack) + extra, "PromptFL", tag))

total_h = sum(estimate_seconds(*item[:4]) for item in PLAN) / 3600
print(f"{MODE}: {len(PLAN)} jobs on {DATASETS}, expected ~{total_h:.1f} h (BUDGET_HOURS = {BUDGET_HOURS})")
for item in PLAN:
    run_flip(*item)
print(f"notebook finished after {(time.time() - NOTEBOOK_START) / 3600:.2f} h")
'''
PLAN_CELL[3] = '''
# --- plan: attacks and defenses on a fixed set of client roles ------------------------------
# Every job uses the same roles (3 noisy, 2 malicious, 5 honest) and the same partition, so
# the only thing that changes between them is the attack and the aggregation rule.
PLAN = []
JOB_ARGS = {}   # tag suffix -> (attack, aggregation rule, extra args), filled in below
for ds in DATASETS:
    base = ("--data_transform", TRAIN_TRANSFORM,
            "--noise_type", "sym", "--noise_rate", str(NOISY_RATE),
            "--noisy_client_frac", str(NOISY_FRAC),
            "--malicious_client_frac", str(MAL_FRAC))

    def job(tag, attack, agg="fedavg", extra=()):
        args = base + ("--attack_type", attack, "--agg_rule", agg) + tuple(extra)
        JOB_ARGS[tag] = args
        if MODE == "gate_b_seeds":
            if tag not in EXTRA_SEED_JOBS:
                return
            # same configuration, different seeds; the tag says so, and the collect cell
            # merges the per-seed lists with the seed 0/1/2 run
            PLAN.append((ds, "CoOp", EXTRA_SEED_COUNT, GLOBAL_ROUNDS, f"{ds}_{tag}_s{EXTRA_SEED_START}",
                         args + ("--seed", str(EXTRA_SEED_START)), "PromptFL", tag))
            return
        PLAN.append((ds, "CoOp", TIMES, GLOBAL_ROUNDS, f"{ds}_{tag}", args, "PromptFL", tag))

    # N: the control. Same roles and partition, but the malicious clients behave honestly.
    job("N_control", "none")
    # P: attacks, no defense
    job("P0_disguise", "noise_disguise", extra=("--attack_rate", str(NOISY_RATE)))
    job("P1_targeted", "targeted_flip")
    job("P2_signflip", "signflip")
    # D: the same attacks against standard robust aggregation
    job("D0_disguise_multikrum", "noise_disguise", "multikrum", ("--attack_rate", str(NOISY_RATE)))
    job("D1_disguise_median", "noise_disguise", "median", ("--attack_rate", str(NOISY_RATE)))
    job("D2_signflip_multikrum", "signflip", "multikrum")

total_h = sum(estimate_seconds(*item[:4]) for item in PLAN) / 3600
print(f"{MODE}: {len(PLAN)} jobs on {DATASETS}, expected ~{total_h:.1f} h (BUDGET_HOURS = {BUDGET_HOURS})")
for item in PLAN:
    run_flip(*item)
print(f"notebook finished after {(time.time() - NOTEBOOK_START) / 3600:.2f} h")
'''
PLAN_CELL[1] = '''
# --- plan --------------------------------------------------------------------------------
# each job: (dataset, algo, times, rounds, tag, extra CLI args, method label, train-transform variant)
PLAN = []
for ds in DATASETS:
    tf = ("--data_transform", TRAIN_TRANSFORM)
    if MODE == "reproduce":
        PLAN.append((ds, "CLIP", 1, GLOBAL_ROUNDS, f"{ds}_ZSCLIP", tf, "ZSCLIP", TRAIN_TRANSFORM))
        PLAN.append((ds, "CoOp", TIMES, GLOBAL_ROUNDS, f"{ds}_PromptFL", tf, "PromptFL", TRAIN_TRANSFORM))
        PLAN.append((ds, "OTP", TIMES, GLOBAL_ROUNDS, f"{ds}_FedOTP", tf, "FedOTP", TRAIN_TRANSFORM))
    elif MODE == "diagnose_transform":
        for variant in ("default_norm", "paper"):
            PLAN.append((ds, "CoOp", TIMES, GLOBAL_ROUNDS, f"{ds}_PromptFL_{variant}",
                         ("--data_transform", variant), "PromptFL", variant))
    elif MODE == "verify_cache":
        # same seed, 1 run, few rounds: the test-feature cache must not change any number
        for flag in ("false", "true"):
            PLAN.append((ds, "CoOp", 1, 5, f"{ds}_cache_{flag}",
                         tf + ("--cache_test_feats", flag), "PromptFL", TRAIN_TRANSFORM))
    else:
        raise ValueError(MODE)

total_h = sum(estimate_seconds(*item[:4]) for item in PLAN) / 3600
print(f"{MODE}: {len(PLAN)} jobs on {DATASETS}, expected ~{total_h:.1f} h (BUDGET_HOURS = {BUDGET_HOURS})")
for item in PLAN:
    run_flip(*item)
print(f"notebook finished after {(time.time() - NOTEBOOK_START) / 3600:.2f} h")

if MODE == "verify_cache":
    sys.path.insert(0, f"{CODE}/tools")
    from parse_flip_log import parse_log
    for ds in DATASETS:
        off, _ = parse_log(f"{OUT}/logs/{ds}_cache_false.txt")
        on, _ = parse_log(f"{OUT}/logs/{ds}_cache_true.txt")
        print(f"{ds}: cache off {off}\\n{' ' * len(ds)}  cache on  {on}\\n  identical: {off == on}")
'''
PLAN_CELL[2] = '''
# --- plan: B (noisy, no defense), C (same noise, ORACLE drop_noisy), D (invariance check) ---
# each job: (dataset, algo, times, rounds, tag, extra CLI args, method label, variant label)
PLAN = []
for ds in DATASETS:
    tf = ("--data_transform", TRAIN_TRANSFORM)
    for nt, rate, frac, nmode in NOISE_SETTINGS:
        noise = tf + ("--noise_type", nt, "--noise_rate", str(rate),
                      "--noisy_client_frac", str(frac), "--noise_mode", nmode)
        PLAN.append((ds, "CoOp", TIMES, GLOBAL_ROUNDS, f"{ds}_B_{nt}{int(rate * 100)}",
                     noise, "PromptFL", f"{nt}{int(rate * 100)}"))
    # C is run ONCE per dataset: once the noisy clients are gone, the noise type cannot
    # matter any more. Verified 2026-09-18: C was bit-identical for sym and pair.
    nt, rate, frac, nmode = NOISE_SETTINGS[0]
    PLAN.append((ds, "CoOp", TIMES, GLOBAL_ROUNDS, f"{ds}_C_drop{int(frac * 100)}",
                 tf + ("--noise_type", nt, "--noise_rate", str(rate), "--noisy_client_frac", str(frac),
                       "--noise_mode", nmode, "--noise_oracle", "drop_noisy"),
                 "PromptFL", f"drop{int(frac * 100)}"))
    if RUN_INVARIANCE and ds == DATASETS[0]:
        # inject then restore. Must reproduce a clean run exactly, otherwise the injector
        # touched something other than the labels and every A-B below is meaningless.
        inv = tf + ("--noise_type", "sym", "--noise_rate", "0.4", "--noisy_client_frac", "0.5")
        PLAN.append((ds, "CoOp", 1, 5, f"{ds}_D_clean_oracle",
                     inv + ("--noise_oracle", "clean"), "PromptFL", "clean_oracle"))
        PLAN.append((ds, "CoOp", 1, 5, f"{ds}_D_no_noise", tf, "PromptFL", "no_noise"))

total_h = sum(estimate_seconds(*item[:4]) for item in PLAN) / 3600
print(f"{MODE}: {len(PLAN)} jobs on {DATASETS}, expected ~{total_h:.1f} h (BUDGET_HOURS = {BUDGET_HOURS})")
for item in PLAN:
    run_flip(*item)
print(f"notebook finished after {(time.time() - NOTEBOOK_START) / 3600:.2f} h")

if RUN_INVARIANCE:
    sys.path.insert(0, f"{CODE}/tools")
    from parse_flip_log import parse_log
    ds = DATASETS[0]
    a, _ = parse_log(f"{OUT}/logs/{ds}_D_no_noise.txt")
    b, _ = parse_log(f"{OUT}/logs/{ds}_D_clean_oracle.txt")
    print(f"invariance check on {ds}:\\n  no noise      {a}\\n  clean oracle  {b}\\n  identical: {a == b}")
    if a != b:
        print("  STOP: the injector changes something besides the labels; the gate results are void")
'''

INTRO = {}
INTRO[6] = """
# Giai đoạn 6, Gate G: cho phần sửa nhãn cái nó chưa từng có

**Đã chạy:** Gate E (E2 đạt, E1/E3 trượt), Gate F (**F1 và F3 đều trượt** — nhận diện đúng
7–9/10 kẻ tấn công, chạm 0–1/25 người tốt, mà accuracy chỉ +0,65 ± 1,41). Kết luận: **loại bỏ
client là cần gạt sai.** Thứ duy nhất có lãi chắc chắn là **sửa nhãn** (+1,01 trên Pets,
p = 0,008), và nó lãi ngay cả khi không có kẻ địch nào.

**Nhưng phiên bản sửa nhãn đang dùng là bản ngây thơ nhất có thể:** nó ghi đè **mọi** nhãn bằng
`argmax` của model toàn cục, không hỏi model có chắc hay không.

| | Tỉ lệ nhãn đúng trên DTD |
|---|---|
| Client cẩu thả (lật 40%) | **60%** |
| "Đáp án" của model toàn cục | **~52%** |

Tức là trên DTD nó đang **lấy đáp án tệ hơn đè lên bài tốt hơn**. Không sửa được lên cao hơn
trình của thầy, nhưng ít nhất đừng để thầy xoá mất những câu học sinh vốn làm đúng.

**Gate G thêm ngưỡng tự tin**: chỉ nhận đáp án ở những ảnh model **chắc chắn**, còn lại giữ
nguyên nhãn của client. Dùng **quantile theo từng client** chứ không phải ngưỡng tuyệt đối, vì
CLIP có `logit_scale ≈ 100` nên softmax cực nhọn và một ngưỡng tuyệt đối hợp với Pets thì vô
nghĩa trên DTD.

Quét 3 mức, **cả hai chế độ** — không có kẻ tấn công (đo như một **luật gộp**) và có kẻ tấn công
(đo như một **phòng thủ**):

| Tiêu chí ghi trước | Ngưỡng |
|---|---|
| **G1** | Có ngưỡng hơn không ngưỡng **≥ +1,0 điểm ở ≥ 2 trong 3 mức** (để là xu hướng, không phải một điểm may) |
| **G2** | Khi có kẻ tấn công, hơn "không phòng thủ" **≥ +2,0 điểm ở ≥ 1 mức** (bản không ngưỡng đạt +1,37) |

6 job, khoảng **6,6 giờ**. `N_control`, `A0_refuse`, `N_audit`, `A1_refuse_audit` **không chạy
lại** — số nằm trong `REFERENCE` ở ô cấu hình, seed tất định nên ghép cặp chính xác tuyệt đối.
"""



INTRO[5] = """
# Giai đoạn 5, cổng Gate D: hỏi client thay vì đo client

Gate C cho thấy giới hạn của việc đọc hình học prompt: prompt nói client **đã học gì**, không nói
client **có cố ý hay không**. Và ở chỗ tín hiệu ngữ nghĩa hoạt động tốt nhất thì tín hiệu độ lệch
kiểu Krum cũng gần tốt bằng.

Notebook này chạy một tín hiệu khác hẳn. Cứ mỗi `CORRECTION_EVERY` round, client phải huấn luyện
thêm một lượt với **nhãn do model toàn cục đề xuất**, rồi gửi về prompt sau lượt đó cùng hai số loss.

Kẻ tấn công không làm theo được, vì bản sửa đến từ model toàn cục — mà model toàn cục không chia sẻ
lớp đích của nó. Làm theo tức là tự xoá cuộc tấn công.

| Loại client | mức giảm loss tự báo | hướng đi của lượt sửa |
|---|---|---|
| thật thà, nhãn sạch | thấp, nhãn vốn đã khớp | đi tiếp hướng cũ |
| thật thà, nhãn nhiễu | cao, được sửa thì lợi thật | **đổi hướng rõ rệt** |
| độc hại | cao (nói dối) | **vẫn đi hướng cũ** |

Mốc so sánh của `r_align` là **cập nhật đang được gộp**, thứ server đã có sẵn — không phải vật thứ
hai do client gửi, nếu không kẻ tấn công điều khiển được cả hai vế.

Kẻ tấn công ở đây là loại **mạnh** (`ATTACK_LIE = "mimic"`): chạy lượt sửa riêng tư, báo đúng mức
giảm mà nó sẽ đạt nếu thật thà, rồi gửi prompt huấn luyện trên nhãn của chính mình. Con số báo cáo
khi đó vô dụng, chỉ còn prompt tố cáo nó.

**Tiêu chí ghi trước (`docs/phase5_plan.md` mục 5)** — cố ý chặt hơn Gate C:
- D1: `r_align` tách độc hại khỏi nhiễu, AUC >= 0,80 **trên ít nhất 2 trong 3 dataset**;
- D2: AUC >= 0,75 trên **OxfordPets**, nơi mọi tín hiệu khác đều hỏng;
- D3: hơn `s_upd` ít nhất 0,10 ở những dataset D1 đạt.

**Điểm dừng đã cam kết: D1 trượt thì ngừng thêm tín hiệu mới và bắt đầu viết luận văn.**

Lượt `N_control` là đối chứng: client độc hại hành xử thật thà, nên probe **không được** chỉ mặt
chúng. Khoảng 5 giờ cho 2 cấu hình x 3 dataset x 5 seed.
"""
INTRO[4] = """
# Giai đoạn 4, cổng Gate C: tín hiệu có tách được ba loại client không?

Gate B đã đo: `multikrum` loại client **nhiễu** nhiều gấp 17,7 lần client thật thà, và bật nó lên
còn làm mô hình tệ hơn không phòng thủ. Lý do: nó chỉ nhìn **độ lớn** của độ lệch, mà nhiễu nhãn
cũng sinh ra độ lệch. Muốn tách, phải nhìn **hình dạng**.

Notebook này chạy lại đúng các cấu hình của Gate B, nhưng bật `--log_signals true`. Mỗi round,
server chấm từng client **chỉ từ prompt của client đó** và ghi kèm vai trò thật:

| Tín hiệu | Ý nghĩa | Kỳ vọng |
|---|---|---|
| `s_sem` | prompt của client kéo embedding lớp ra xa ngữ nghĩa zero-shot của CLIP bao nhiêu | cao ở **cả** nhiễu lẫn độc hại |
| `s_conc` | phần trôi đó dồn vào **một lớp** bao nhiêu | **tín hiệu tách nhiễu với độc hại**: nhiễu rải, tấn công dồn |
| `s_upd` | chuẩn của hiệu prompt, kiểu Krum | mốc phải vượt |

Server **không** thấy dữ liệu client, **không** cần tập sạch, **không** đụng tập test. Mẹo: không
gian ảnh và văn bản của CLIP là chung, nên embedding văn bản của một lớp đóng vai ảnh đại diện —
server có tập probe mà không cần tấm ảnh nào.

**Tiêu chí ghi trước (`docs/phase4_plan.md` mục 3),** đánh giá trên round 10-50, 5 seed:
- C1: `s_sem` tách (nhiễu hoặc độc hại) khỏi thật thà, AUC >= 0,80;
- C2: `s_conc` tách độc hại khỏi nhiễu, AUC >= 0,80 — **tiêu chí sống còn**;
- C3: `s_conc` hơn `s_upd` ở việc đó ít nhất 0,10 AUC.

Khoảng 5,8 giờ cho 4 cấu hình x 2 dataset x 5 seed. Chia hai phiên bằng cách sửa `DATASETS`.
"""
INTRO[3] = """
# Giai đoạn 3, cổng Gate B: tấn công giả làm nhiễu, và các phòng thủ sẵn có

Gate A đã đo được: loại bỏ client **nhiễu** gần như vô ích (trần −0,2 đến +3,4 điểm), còn với client
**độc hại** thì loại bỏ là bắt buộc. Hai cách xử lý ngược nhau, nên phải phân biệt được hai loại.

Notebook này chạy 7 lượt trên cùng một bộ vai trò client (3 nhiễu, 2 độc hại, 5 thật thà) và cùng một
cách chia dữ liệu. Chỉ kiểu tấn công và luật gộp thay đổi:

| Tag | Nội dung |
|---|---|
| `N_control` | **đối chứng**: client độc hại hành xử thật thà. Mọi thiệt hại đo so với lượt này |
| `P0_disguise` | tấn công **giả làm nhiễu**: đúng tỉ lệ lật như client nhiễu, nhưng nhãn dồn về một lớp đích |
| `P1_targeted` | tấn công có mục tiêu kinh điển, ồn ào |
| `P2_signflip` | tấn công mức cập nhật: đảo dấu cập nhật prompt |
| `D0_disguise_multikrum`, `D1_disguise_median` | vẫn tấn công giả nhiễu, nhưng server dùng phòng thủ chuẩn |
| `D2_signflip_multikrum` | đối chứng ngược: phòng thủ **phải** chặn được tấn công ồn ào |

**Chỉ số chính là `last10`**, theo quyết định sau Gate A (`best` chọn đỉnh trên tập test nên che mất
phần lớn thiệt hại của nhiễu).

**Tiêu chí ghi trước (`docs/phase3_plan.md` mục 3):**
- B1: tấn công giả nhiễu gây thiệt hại ≥ 2,0 điểm **vượt trên** phần nhiễu vốn đã có;
- B2: với `multikrum` và `median`, thiệt hại còn lại vẫn ≥ 2,0 điểm;
- B3: `multikrum` loại nhầm client **nhiễu** nhiều hơn hoặc bằng loại đúng client **độc hại**.

B3 là tiêu chí sống còn: nó kiểm chính giả thuyết của đồ án, rằng phòng thủ sẵn có không phân biệt
được client gán nhãn kém với kẻ tấn công. Server ghi lại mỗi round `multikrum` giữ ai, kèm vai trò
thật của từng client, nên đây là con số đo được chứ không phải lập luận.

**Chia theo quota:** `DATASETS = ["dtd"]` khoảng 3,1 giờ, rồi `["oxford_pets"]` khoảng 3,2 giờ.
"""
INTRO[1] = """
# Giai đoạn 1: tái lập PromptFL, FedOTP, ZS-CLIP trên FLIP

**Đã chạy xong 2026-09-18 trên T4: 9/9 ô đạt, 4,76 giờ.** Notebook này giữ lại để tái lập và để
làm bằng chứng trong luận văn. Giai đoạn 2 dùng notebook riêng: `phase2_gate_a.ipynb`.

**Mục tiêu:** tái lập Table 1 của FLIP (backbone RN50, 10 client, Dirichlet α=0.1, 8 shot/lớp, 50 round, 3 seed)
trên Caltech101, DTD, OxfordPets, trước khi thêm nhiễu nhãn và client độc hại.

**Chuẩn bị:**
1. Trên máy: `python tools/package_code.py` → upload `dist/fpl-triage-code.zip` thành **private** Kaggle Dataset
   (ví dụ tên `fpl-triage-code`), rồi *Add Data* vào notebook này.
2. Settings: Accelerator = GPU T4, **Internet = On** (tải dữ liệu, trọng số CLIP).
3. Chạy bằng **Save Version → Save & Run All (Commit)** để output được lưu lại.

**Chia theo quota GPU** (sửa `DATASETS` ở ô config):
- Lần 1: `["dtd"]`, khoảng 1,5 giờ trên T4.
- Lần 2: `["caltech101", "oxford_pets"]`, khoảng 3,5–5 giờ. Có thể tách làm hai lần, mỗi lần một dataset.

`BUDGET_HOURS` chặn không cho bắt đầu một job nếu dự kiến làm notebook vượt quá số giờ đó.
Job bị chặn sẽ in dòng `skip ...`, và lần chạy sau sẽ làm tiếp.

**Tiêu chí tái lập (ghi trước khi chạy, xem `docs/phase1_plan.md`):**
- PromptFL, FedOTP: |trung bình best_acc của ta − số paper| ≤ max(1.0; 2 × sd paper) điểm %.
- ZS-CLIP: |chênh lệch| ≤ 0.5 điểm %.

Ngoài `best_acc` (chỉ số paper dùng, bị thiên lệch do chọn max trên test), notebook còn báo `last` và
`last10_mean` để dùng cho các giai đoạn sau.
"""
INTRO[2] = """
# Giai đoạn 2, cổng Gate A: nhiễu nhãn có để lại dư địa nào không?

Đo **trước khi** thiết kế bất kỳ phương pháp nào. Đây là bài học từ FedSNC, nơi trần chỉ được đo ở
vòng 11 sau khi đã tốn 34 lần chạy.

Mỗi dataset, mỗi kịch bản nhiễu chạy hai lượt:
- **B**: có nhiễu, không phòng thủ. Mức phải vượt.
- **C**: cùng nhiễu đó, nhưng `--noise_oracle drop_noisy` loại hẳn client nhiễu. Đây là **trần của
  triage mức client**: một bộ phát hiện client hoàn hảo cũng không hơn được mức này.

Mốc **A** (nhiễu 0%) lấy từ giai đoạn 1, đã ghi cứng trong ô thu kết quả. Mốc **E** là sàn ZS-CLIP.
Hai đại lượng dư địa: `H_sample = A − B` và `H_client = C − B`.

Ngoài ra có phép kiểm **D** (`RUN_INVARIANCE`), 5 round: tiêm nhiễu rồi hoàn nhãn, phải cho kết quả
**giống hệt** lượt sạch. Nếu `identical: False` thì dừng, đừng đọc bảng cổng — chênh lệch khi đó
không biết đến từ nhiễu hay từ hạ tầng.

**Chuẩn bị:** như giai đoạn 1. Code phải là bản mới (có `flcore/datasets/noise.py`), nên phải upload
lại dataset bằng `python tools/package_code.py`.

**Chia theo quota GPU** (sửa `DATASETS`):
- Còn ≥ 4 giờ: để nguyên `["dtd", "oxford_pets"]`, khoảng 3,1 giờ.
- Còn ~2 giờ: chạy `["dtd"]` trước, lần sau `["oxford_pets"]`. `/kaggle/working` không mang sang phiên
  sau, nên lần hai phải để đúng dataset chưa chạy.

**Tiêu chí ghi trước (`docs/phase2_plan.md` mục 4).** Gate A đạt khi cả ba điều sau đúng:
- i: `A − B ≥ 3,0` điểm, trên ít nhất 2 trong 3 dataset (nhiễu thực sự gây thiệt hại);
- ii: `C − B ≥ 2,0` điểm, trên ít nhất 2 trong 3 dataset (triage mức client mua lại được);
- iii: `B > E`, tức có nhiễu thì huấn luyện vẫn hơn zero-shot.

Mọi so sánh ghép cặp theo seed. Nếu hiệu trung bình nhỏ hơn 2 lần sd của chính hiệu đó thì notebook
in cảnh báo và **không** được kết luận, phải thêm seed 3 và 4.
"""

CELLS = [
    md("__PHASE_INTRO__"),
    code("""
import glob, json, os, shutil, statistics, subprocess, sys, time

# --- config -------------------------------------------------------------------------
WORK = "/kaggle/working"
CLIP_CACHE = f"{WORK}/clip_cache"          # or an attached dataset holding the CLIP .pt files
DATA_ROOT = "/tmp/fpl_data"                # large, deliberately NOT under /kaggle/working
__PHASE_CONFIG__
# Train transform, decided by the 2026-09-17 diagnostic on DTD (PromptFL best over 3 runs):
#   default      53.29 +- 2.68  (upstream: crop/flip, NO normalize)   -> 4.3 points below the paper
#   default_norm 57.03 +- 2.16  (upstream + normalize)                -> passes
#   paper        57.51 +- 0.82  (Appendix B.4, also the lowest spread) -> passes, adopted
TRAIN_TRANSFORM = "paper"
CACHE_TEST_FEATS = True   # cache frozen image-encoder features for the test set
                          # (verified identical on CPU and on T4; 19-48% faster per round)
GLOBAL_ROUNDS = 50
BACKBONE = "RN50"
NUM_WORKERS = 4
RUN_TIMING = False     # the 2-round timing test already ran (T4: ~12 s/round on DTD)
NOTEBOOK_START = time.time()

# uploaded code: the dataset built by tools/package_code.py holds flip/ and tools/
CODE_INPUT_ROOT = "/kaggle/input/datasets/duyendinhhoang/fpl-triage"
if not os.path.isfile(f"{CODE_INPUT_ROOT}/flip/main.py"):
    hits = glob.glob("/kaggle/input/**/flip/main.py", recursive=True)
    assert hits, "Attach the private dataset built by tools/package_code.py"
    CODE_INPUT_ROOT = os.path.dirname(os.path.dirname(hits[0]))
assert os.path.isdir(f"{CODE_INPUT_ROOT}/tools"), f"tools/ missing under {CODE_INPUT_ROOT}"
CODE = f"{WORK}/code"
print("code found at", CODE_INPUT_ROOT)
"""),
    code("""
# --- environment ----------------------------------------------------------------------
subprocess.run("nvidia-smi", shell=True)
if not os.path.exists(CODE):
    shutil.copytree(CODE_INPUT_ROOT, CODE)
os.makedirs(f"{OUT}/logs", exist_ok=True)

# Kaggle decompresses .gz files inside uploaded datasets, which removes CLIP's BPE vocab.
# Restore it: re-gzip the decompressed copy if present, else fetch the identical file from openai/CLIP.
import gzip, hashlib, urllib.request
BPE = f"{CODE}/flip/flcore/models/clip/bpe_simple_vocab_16e6.txt.gz"
BPE_SHA256 = "924691ac288e54409236115652ad4aa250f48203de50a9e4722a6ecd48d6804a"
if not os.path.isfile(BPE):
    plain = BPE[:-3]
    if os.path.isfile(plain):
        with open(plain, "rb") as fi, gzip.open(BPE, "wb") as fo:
            shutil.copyfileobj(fi, fo)
        print("BPE vocab re-gzipped from", plain)
    else:
        urllib.request.urlretrieve("https://github.com/openai/CLIP/raw/main/clip/bpe_simple_vocab_16e6.txt.gz", BPE)
        got = hashlib.sha256(open(BPE, "rb").read()).hexdigest()
        assert got == BPE_SHA256, f"BPE vocab checksum mismatch: {got}"
        print("BPE vocab downloaded from openai/CLIP")

need = {"ftfy": "ftfy", "regex": "regex", "gdown": "gdown", "h5py": "h5py", "cv2": "opencv-python-headless",
        "termcolor": "termcolor", "tensorboard": "tensorboard", "sklearn": "scikit-learn"}
missing = []
for mod, pkg in need.items():
    try:
        __import__(mod)
    except ImportError:
        missing.append(pkg)
if missing:
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", *missing], check=True)

import torch
print("torch", torch.__version__, "| cuda", torch.cuda.is_available(),
      "|", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "-")
print("free disk /tmp: %.1f GB" % (shutil.disk_usage("/tmp").free / 1e9))
"""),
    code("""
# --- datasets (idempotent) ---------------------------------------------------------------
import gdown

SPLITS = {  # CoOp "split_zhou" files, same ones FLIP's docs/DATASETS.md points to
    "caltech101": ("1hyarUivQE36mY6jSomru6Fjd-JzwcCzN", "split_zhou_Caltech101.json"),
    "dtd": ("1u3_QfB467jqHgNXC00UIzbLZRQCg2S7x", "split_zhou_DescribableTextures.json"),
    "oxford_pets": ("1501r8Ber4nNKvmlFVQZ8SeUHTcdTTEqs", "split_zhou_OxfordPets.json"),
    "food101": ("1QK0tGi096I0Ba6kggatX1ee6dJFIcEJl", "split_zhou_Food101.json"),
    # EuroSAT needs no split file: FLIP splits it 80/10/10 itself, seeded by the run seed
}


def fetch(urls, dst):
    # The DFKI host that FLIP's docs point to for EuroSAT is gone, and it took wget 47 minutes
    # of a GPU session to admit it. Short timeouts, few retries, and a list of mirrors.
    for url in urls:
        print("$ wget", url)
        rc = subprocess.run(f"wget --timeout=30 --tries=2 -q -O {dst} {url}", shell=True).returncode
        if rc == 0 and os.path.getsize(dst) > 1_000_000:
            return url
        print(f"  failed (exit {rc}), trying the next mirror")
    raise RuntimeError(f"every mirror failed for {dst}: {urls}")


def sh(cmd):
    print("$", cmd)
    subprocess.run(cmd, shell=True, check=True)


# If a dataset is already attached to the notebook as Kaggle input, use it instead of
# downloading: no network, no GPU minutes spent waiting. Each entry lists the layouts we
# accept, most specific first.
INPUT_HINTS = {
    "food101": ["food101/images", "food-101/images"],
    "eurosat": ["eurosat/2750", "EuroSAT/2750", "2750"],
    "dtd": ["dtd/images"],
    "caltech101": ["caltech101/101_ObjectCategories", "101_ObjectCategories"],
    "oxford_pets": ["oxford_pets/images"],
}


def link_from_input(name):
    # point DATA_ROOT/<name> at an attached input; returns True if one was found
    for hint in INPUT_HINTS.get(name, []):
        hits = [h for h in glob.glob(f"/kaggle/input/**/{hint}", recursive=True) if os.path.isdir(h)]
        if not hits:
            continue
        src = hits[0]
        leaf = hint.rsplit("/", 1)[-1]
        d = f"{DATA_ROOT}/{name}"
        os.makedirs(d, exist_ok=True)
        if not os.path.exists(f"{d}/{leaf}"):
            os.symlink(src, f"{d}/{leaf}")
        for j in glob.glob(f"{os.path.dirname(src)}/*.json"):   # a split file shipped alongside
            if not os.path.exists(f"{d}/{os.path.basename(j)}"):
                shutil.copy(j, d)
        print(f"{name}: using attached input at {src} (no download)")
        return True
    return False


EUROSAT_CLASSES = ["AnnualCrop", "Forest", "HerbaceousVegetation", "Highway", "Industrial",
                   "Pasture", "PermanentCrop", "Residential", "River", "SeaLake"]


def verify_dataset(name):
    # fail here, in seconds, rather than after hours of GPU time on the wrong data
    d = f"{DATA_ROOT}/{name}"
    if name == "food101":
        split = f"{d}/split_zhou_Food101.json"
        assert os.path.exists(split), f"{split} missing"
        entries = json.load(open(split))["train"][:5]
        missing = [e[0] for e in entries if not os.path.exists(f"{d}/images/{e[0]}")]
        assert not missing, (
            f"{name}: the split file names images this copy does not have, e.g. {missing[0]}. "
            "The CoOp split is built on the ETHZ Food-101 release, whose images live at "
            "images/<class>/<numeric id>.jpg. UPMC-Food101 is a DIFFERENT collection: same class "
            "names, different web images, and its images carry real label noise, which would "
            "contaminate this experiment.")
        n_cls = len([x for x in os.listdir(f"{d}/images") if os.path.isdir(f"{d}/images/{x}")])
        assert n_cls == 101, f"{name}: expected 101 class folders under images/, found {n_cls}"
    if name == "eurosat":
        missing = [c for c in EUROSAT_CLASSES if not os.path.isdir(f"{d}/2750/{c}")]
        assert not missing, (
            f"{name}: missing class folders {missing} under 2750/. FLIP expects the original "
            "EuroSAT RGB layout, 2750/<class>/ for the 10 classes. A copy that is already split "
            "into train/ and validation/ folders will not work as it is.")
    print(f"{name}: layout verified")


def fetch_split(name):
    file_id, fname = SPLITS[name]
    dst = f"{DATA_ROOT}/{name}/{fname}"
    if not os.path.exists(dst):
        gdown.download(id=file_id, output=dst, quiet=True)


def prep_caltech101():
    d = f"{DATA_ROOT}/caltech101"
    from_input = link_from_input("caltech101")
    if not from_input and not os.path.isdir(f"{d}/101_ObjectCategories"):
        os.makedirs(d, exist_ok=True)
        sh("wget -q -O /tmp/caltech-101.zip https://data.caltech.edu/records/mzrjq-6wc02/files/caltech-101.zip")
        sh("rm -rf /tmp/caltech_zip && unzip -q /tmp/caltech-101.zip -d /tmp/caltech_zip")
        tgz = glob.glob("/tmp/caltech_zip/**/101_ObjectCategories.tar.gz", recursive=True)[0]
        sh(f"tar -xzf {tgz} -C {d}")
        sh("rm -rf /tmp/caltech-101.zip /tmp/caltech_zip")
    fetch_split("caltech101")


def prep_dtd():
    d = f"{DATA_ROOT}/dtd"
    from_input = link_from_input("dtd")
    if not from_input and not os.path.isdir(f"{d}/images"):
        os.makedirs(DATA_ROOT, exist_ok=True)
        sh("wget -q -O /tmp/dtd.tar.gz https://www.robots.ox.ac.uk/~vgg/data/dtd/download/dtd-r1.0.1.tar.gz")
        sh(f"tar -xzf /tmp/dtd.tar.gz -C {DATA_ROOT} && rm /tmp/dtd.tar.gz")
    fetch_split("dtd")


def prep_eurosat():
    d = f"{DATA_ROOT}/eurosat"
    from_input = link_from_input("eurosat")
    if not from_input and not os.path.isdir(f"{d}/2750"):
        os.makedirs(d, exist_ok=True)
        # the original madm.dfki.de host is dead; Zenodo 7711810 is the authors' own archive,
        # and the RGB archive is EuroSAT_RGB.zip (94.7 MB), not EuroSAT.zip
        fetch(["https://zenodo.org/records/7711810/files/EuroSAT_RGB.zip?download=1",
               "https://zenodo.org/api/records/7711810/files/EuroSAT_RGB.zip/content"],
              "/tmp/eurosat.zip")
        sh(f"unzip -q /tmp/eurosat.zip -d {d} && rm /tmp/eurosat.zip")
        # it unpacks as EuroSAT_RGB/<class>/; FLIP looks for 2750/<class>/
        if os.path.isdir(f"{d}/EuroSAT_RGB"):
            sh(f"mv {d}/EuroSAT_RGB {d}/2750")
    # EuroSAT has no split file: FLIP splits 80/10/10 itself, seeded by the run seed


def prep_food101():
    d = f"{DATA_ROOT}/food101"
    from_input = link_from_input("food101")
    if not from_input and not os.path.isdir(f"{d}/images"):
        os.makedirs(DATA_ROOT, exist_ok=True)
        # the datasets_extra path in FLIP's docs is a 404 now
        fetch(["https://data.vision.ee.ethz.ch/cvl/food-101.tar.gz",
               "https://s3.amazonaws.com/fast-ai-imageclas/food-101.tgz"],
              "/tmp/food-101.tar.gz")
        sh(f"tar -xzf /tmp/food-101.tar.gz -C {DATA_ROOT} && rm /tmp/food-101.tar.gz")
        # FLIP keys the folder by the dataset name, not by the archive's own name
        sh(f"mv {DATA_ROOT}/food-101 {d}")
    fetch_split("food101")


def prep_oxford_pets():
    d = f"{DATA_ROOT}/oxford_pets"
    from_input = link_from_input("oxford_pets")
    if not from_input and not os.path.isdir(f"{d}/images"):
        os.makedirs(d, exist_ok=True)
        for part in ("images", "annotations"):
            sh(f"wget -q -O /tmp/{part}.tar.gz https://www.robots.ox.ac.uk/~vgg/data/pets/data/{part}.tar.gz")
            sh(f"tar -xzf /tmp/{part}.tar.gz -C {d} && rm /tmp/{part}.tar.gz")
    fetch_split("oxford_pets")


ready = []
for name in DATASETS:
    t0 = time.time()
    try:
        globals()[f"prep_{name}"]()
        verify_dataset(name)
    except Exception as e:
        # a dataset that cannot be fetched or does not have the layout FLIP expects is skipped,
        # not fatal: the rest of the session still produces usable results
        print(f"{name}: SKIPPED -- {type(e).__name__}: {e}")
        continue
    ready.append(name)
    print(f"{name}: ready in {time.time() - t0:.0f}s")

assert ready, f"no dataset could be prepared out of {DATASETS}"
if ready != DATASETS:
    print(f"continuing with {ready} instead of {DATASETS}")
DATASETS = ready
"""),
    code("""
# --- run helper ------------------------------------------------------------------------
# Hyper-parameters follow FLIP's README / paper Appendix B.4 ("standard learning" protocol).
COMMON = [
    "--benchmark", "global", "--image_backbone", BACKBONE, "--optim_name", "sgd", "--lr_scheduler", "cos",
    "--split_alpha", "0.1", "--loss_type", "ce", "--central", "false", "--num_clients", "10",
    "--num_shot", "8", "--optim_momentum", "0.9", "--local_learning_rate", "0.002", "--batch_size", "16",
    "--eval_scaler", "2", "--num_prompt", "1", "--local_epochs", "1", "--prompt_batch_size", "2",
    "--precision", "amp", "--num_workers", str(NUM_WORKERS), "--data_root", DATA_ROOT, "--verbose2",
    "--cache_test_feats", "true" if CACHE_TEST_FEATS else "false",
]
INDEX = f"{OUT}/run_index.json"
PROGRESS_EVERY = 10    # print a progress line to the notebook output every N rounds
import re


def load_index():
    return json.load(open(INDEX)) if os.path.exists(INDEX) else {}


# T4 seconds per round WITH the test-feature cache on (CoOp measured 2026-09-18,
# OTP scaled by the CoOp->OTP ratio measured without the cache on 2026-09-17)
SEC_PER_ROUND_T4 = {
    ("dtd", "CoOp"): 9.0, ("dtd", "OTP"): 11.8,
    ("caltech101", "CoOp"): 20.6, ("caltech101", "OTP"): 32.9,
    ("oxford_pets", "CoOp"): 9.2, ("oxford_pets", "OTP"): 11.2,
    # measured 2026-09-21: EuroSAT 5.2 s/round (10 classes, 2.7k test images), Food101 95.6
    # s/round (101 classes, 25k test images). The first guess put Food101 at 32.0, which is why
    # the confound run spent its whole budget on one job; keep these honest.
    ("eurosat", "CoOp"): 5.2, ("eurosat", "OTP"): 7.0,
    ("food101", "CoOp"): 96.0, ("food101", "OTP"): 130.0,
}
ALGO_FACTOR = {"CoOp": 1.0, "OTP": 1.5}


def measured_sec_per_round(dataset, algo):
    import re
    rates = []
    for e in load_index().values():
        if e["dataset"] == dataset and e["algo"] == algo and e["returncode"] == 0:
            rates += [float(x) for x in re.findall(r"elapsed: ([\\d.]+)s", open(e["log"]).read())]
    return statistics.fmean(rates) if rates else None


def estimate_seconds(dataset, algo, times, rounds):
    if algo == "CLIP":
        return 120
    rate = measured_sec_per_round(dataset, algo)
    if rate is None and algo != "CoOp" and measured_sec_per_round(dataset, "CoOp"):
        rate = measured_sec_per_round(dataset, "CoOp") * ALGO_FACTOR[algo]
    if rate is None:
        return SEC_PER_ROUND_T4[(dataset, algo)] * (rounds + 1) * times
    return rate * (rounds + 1) * times + 60 * times   # + model/data init per run


def run_flip(dataset, algo, times, rounds, tag, extra=(), method=None, variant="default"):
    index = load_index()
    if index.get(tag, {}).get("returncode") == 0:
        print(f"skip {tag} (already done)")
        return index[tag]
    used_h = (time.time() - NOTEBOOK_START) / 3600
    need_h = estimate_seconds(dataset, algo, times, rounds) / 3600
    if used_h + need_h > BUDGET_HOURS:
        print(f"skip {tag}: needs ~{need_h:.1f} h, only {BUDGET_HOURS - used_h:.1f} h of BUDGET_HOURS left")
        return None
    print(f"start {tag} (expected ~{need_h * 60:.0f} min, notebook at {used_h:.2f} h)", flush=True)
    run_dir = f"{OUT}/runs/{tag}"
    os.makedirs(run_dir, exist_ok=True)
    log = f"{OUT}/logs/{tag}.txt"
    # PYTHONUNBUFFERED so FLIP's lines reach us as they are printed, not in 4 KB chunks
    env = dict(os.environ, PYTHONPATH=f"{CODE}/flip", FLIP_CLIP_CACHE=CLIP_CACHE, PYTHONUNBUFFERED="1")
    cmd = [sys.executable, f"{CODE}/flip/main.py", "--dataset", dataset, "--prompt_algo", algo,
           "--times", str(times), "--global_rounds", str(rounds), *COMMON, *extra]
    t0 = time.time()
    # Full output goes to the log file; a short progress line goes to the notebook output so a
    # committed run shows where it is (Kaggle only displays the notebook's own stdout).
    round_re = re.compile(r"round (\\d+), .*?top1: ([\\d.]+)%")
    run_no = 1
    with open(log, "w") as f:
        proc = subprocess.Popen(cmd, cwd=run_dir, env=env, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, text=True, bufsize=1)
        for line in proc.stdout:
            f.write(line)
            m = round_re.search(line)
            if m:
                rnd = int(m.group(1))
                if rnd % PROGRESS_EVERY == 0 or rnd == rounds:
                    print(f"  [{tag}] run {run_no}/{times} round {rnd}/{rounds} top1 {m.group(2)}% "
                          f"({(time.time() - t0) / 60:.1f} min)", flush=True)
                if rnd == rounds:
                    run_no += 1
            elif "CLIP acc" in line or "Traceback" in line or "Error" in line:
                print(f"  [{tag}] {line.strip()}", flush=True)
        proc.wait()
    entry = {"dataset": dataset, "algo": algo, "method": method, "variant": variant,
             "times": times, "rounds": rounds, "extra": list(extra),
             "returncode": proc.returncode, "seconds": round(time.time() - t0, 1), "log": log}
    index[tag] = entry
    json.dump(index, open(INDEX, "w"), indent=1)
    print(f"{tag}: rc={proc.returncode} in {entry['seconds'] / 60:.1f} min")
    if proc.returncode != 0:
        print("".join(open(log).readlines()[-30:]))
    return entry
"""),
    code("""
# --- timing test: 2 rounds, 1 run on DTD (skipped unless RUN_TIMING) -------------------------
import re

if RUN_TIMING:
    entry = run_flip("dtd", "CoOp", times=1, rounds=2, tag="timing_dtd_CoOp")
    per_round = [float(x) for x in re.findall(r"elapsed: ([\\d.]+)s", open(entry["log"]).read())]
    print("seconds per round:", per_round)
else:
    print("timing test skipped (RUN_TIMING = False)")
"""),
    code("__PHASE_PLAN__"),
    code("__PHASE_COLLECT__"),
    code("""
# --- package outputs (download this zip or Save Version) -------------------------------------
archive = shutil.make_archive(f"{WORK}/{RESULT_NAME}", "zip", OUT)
print(archive, "%.1f MB" % (os.path.getsize(archive) / 1e6))
"""),
]

# the three cells that differ per phase; everything else above is shared
SLOTS = {"__PHASE_INTRO__": INTRO, "__PHASE_CONFIG__": PHASE_CONFIG,
         "__PHASE_PLAN__": PLAN_CELL, "__PHASE_COLLECT__": COLLECT_CELL}


def build(phase):
    cells = copy.deepcopy(CELLS)
    for cell in cells:
        src = "".join(cell["source"])
        for marker, texts in SLOTS.items():
            if marker in src:
                src = src.replace(marker, texts[phase].strip("\n"))
        cell["source"] = src.strip("\n").splitlines(keepends=True)
    return cells


def main():
    for phase, dst in DST.items():
        nb = {
            "cells": build(phase),
            "metadata": {
                "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                "language_info": {"name": "python"},
            },
            "nbformat": 4,
            "nbformat_minor": 5,
        }
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with open(dst, "w", encoding="utf-8") as f:
            json.dump(nb, f, ensure_ascii=False, indent=1)
        print("wrote", dst)


if __name__ == "__main__":
    main()
