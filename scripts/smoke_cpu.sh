#!/usr/bin/env bash
# CPU smoke test: runs ZS-CLIP, PromptFL (CoOp) and FedOTP for 2 rounds on a synthetic
# 6-class dataset. Checks that every code path executes; accuracy is meaningless.
#
# Needs: torch, torchvision, ftfy, regex, h5py, termcolor, tensorboard, opencv-python-headless,
# scikit-learn, matplotlib, pandas, tqdm. Downloads CLIP RN50 (~244 MB) on first run.
#
# Usage (from the project root):  bash scripts/smoke_cpu.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WORK="${ROOT}/.smoke"
mkdir -p "${WORK}"
cd "${WORK}"

if [ ! -d data/dtd ]; then
  python "${ROOT}/tools/make_synthetic_dataset.py" --data_root data --name dtd
fi

# Windows Python (e.g. under Git Bash) expects ';' between PYTHONPATH entries
SEP="$(python -c 'import os; print(os.pathsep)')"
export PYTHONPATH="${ROOT}/flip${PYTHONPATH:+${SEP}${PYTHONPATH}}"

for algo in CLIP CoOp OTP; do
  echo "=== ${algo}"
  python "${ROOT}/flip/main.py" \
    --dataset dtd --data_root "${WORK}/data" --prompt_algo "${algo}" \
    --image_backbone RN50 --num_clients 2 --num_shot 8 --split_mode iid \
    --global_rounds 1 --batch_size 8 --precision fp32 --num_workers 0 --times 1 \
    --lr_scheduler cos --local_learning_rate 0.002 > "log_${algo}.txt" 2>&1
  python "${ROOT}/tools/parse_flip_log.py" "log_${algo}.txt"
done
echo "smoke test passed"
