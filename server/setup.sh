#!/usr/bin/env bash
# One-time setup on the Linux server. Run from the repo root:  bash server/setup.sh
# Optional: DATA_ROOT=/path/with/space bash server/setup.sh   (default ~/fpl_data, needs ~2.5 GB)
# Caltech101, DTD and OxfordPets; datasets already present are skipped.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DATA_ROOT="${DATA_ROOT:-$HOME/fpl_data}"
CLIP_CACHE="${CLIP_CACHE:-$HOME/.cache/clip}"

echo "== python packages"
python -c "import torch, torchvision; print('torch', torch.__version__, '| cuda', torch.cuda.is_available(), '|', torch.cuda.device_count(), 'GPU')" \
  || { echo "PyTorch with CUDA is missing: install it first (see server/README.md)"; exit 1; }
python -m pip install -q ftfy regex gdown h5py opencv-python-headless termcolor tensorboard \
  scikit-learn scipy pandas matplotlib tqdm colorama

echo "== Caltech101 -> $DATA_ROOT/caltech101"
D="$DATA_ROOT/caltech101"
mkdir -p "$D"
if [ ! -d "$D/101_ObjectCategories" ]; then
  wget -q --show-progress -O /tmp/caltech-101.zip https://data.caltech.edu/records/mzrjq-6wc02/files/caltech-101.zip
  rm -rf /tmp/caltech_zip && unzip -q /tmp/caltech-101.zip -d /tmp/caltech_zip
  tar -xzf "$(find /tmp/caltech_zip -name 101_ObjectCategories.tar.gz | head -1)" -C "$D"
  rm -rf /tmp/caltech-101.zip /tmp/caltech_zip
fi
cp -n "$ROOT/splits/split_zhou_Caltech101.json" "$D/"
echo "classes: $(ls "$D/101_ObjectCategories" | wc -l) (expect 102 incl. BACKGROUND_Google)"

fetch() {  # fetch <out> <url> [<url> ...]: first mirror that gives a real file wins
  local out="$1"; shift
  for u in "$@"; do
    if wget -q --show-progress --timeout=60 --tries=2 -O "$out" "$u" && [ "$(stat -c%s "$out")" -gt 1000000 ]; then return 0; fi
    echo "  failed: $u"
  done
  echo "every mirror failed for $out"; return 1
}

echo "== DTD -> $DATA_ROOT/dtd"
if [ ! -d "$DATA_ROOT/dtd/images" ]; then
  fetch /tmp/dtd.tar.gz https://thor.robots.ox.ac.uk/dtd/dtd-r1.0.1.tar.gz         https://www.robots.ox.ac.uk/~vgg/data/dtd/download/dtd-r1.0.1.tar.gz
  tar -xzf /tmp/dtd.tar.gz -C "$DATA_ROOT" && rm /tmp/dtd.tar.gz
fi
cp -n "$ROOT/splits/split_zhou_DescribableTextures.json" "$DATA_ROOT/dtd/"

echo "== OxfordPets -> $DATA_ROOT/oxford_pets"
mkdir -p "$DATA_ROOT/oxford_pets"
for part in images annotations; do
  if [ ! -d "$DATA_ROOT/oxford_pets/$part" ]; then
    fetch "/tmp/$part.tar.gz" "https://thor.robots.ox.ac.uk/pets/$part.tar.gz"           "https://www.robots.ox.ac.uk/~vgg/data/pets/data/$part.tar.gz"
    tar -xzf "/tmp/$part.tar.gz" -C "$DATA_ROOT/oxford_pets" && rm "/tmp/$part.tar.gz"
  fi
done
cp -n "$ROOT/splits/split_zhou_OxfordPets.json" "$DATA_ROOT/oxford_pets/"

echo "== CLIP RN50 weights -> $CLIP_CACHE"
FLIP_CLIP_CACHE="$CLIP_CACHE" PYTHONPATH="$ROOT/flip" python -c "
from flcore.models.clip.clip import load_clip_to_cpu
m = load_clip_to_cpu('RN50'); print('CLIP RN50 ok')"

echo "== done. Next: python server/run_queue.py --queue server/queue_caltech.txt --gpus 0 --per-gpu 2"
