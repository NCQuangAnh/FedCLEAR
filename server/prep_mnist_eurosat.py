"""One-time data step for queue_mnist_eurosat*: download MNIST and EuroSAT and build their
train/val/test folders BEFORE the two queues start, so two parallel runs never write the same
folders at once. Run from the repo root:  PYTHONPATH=flip python server/prep_mnist_eurosat.py
Optional: --data-root (default ~/fpl_data, same default as run_queue.py).
"""
import argparse
import os
import shutil
import urllib.request
import zipfile

from flcore.datasets.eurosat import EuroSAT
from flcore.datasets.mnist import MNIST

EUROSAT_CLASSES = ["AnnualCrop", "Forest", "HerbaceousVegetation", "Highway", "Industrial",
                   "Pasture", "PermanentCrop", "Residential", "River", "SeaLake"]
# the original DFKI host is dead; Zenodo 7711810 is the authors' own archive (RGB, 94.7 MB)
EUROSAT_URLS = ["https://zenodo.org/records/7711810/files/EuroSAT_RGB.zip?download=1",
                "https://zenodo.org/api/records/7711810/files/EuroSAT_RGB.zip/content"]


def get_eurosat(d):
    if os.path.isdir(f"{d}/2750"):
        return
    os.makedirs(d, exist_ok=True)
    zpath = f"{d}/EuroSAT_RGB.zip"
    for url in EUROSAT_URLS:
        try:
            print("downloading", url)
            urllib.request.urlretrieve(url, zpath)
            if os.path.getsize(zpath) > 1_000_000:
                break
        except Exception as e:  # noqa: BLE001  try the next mirror, fail below if none worked
            print("  failed:", e)
    else:
        raise RuntimeError("every EuroSAT mirror failed")
    with zipfile.ZipFile(zpath) as z:
        z.extractall(d)
    os.remove(zpath)
    # it unpacks as EuroSAT_RGB/<class>/; FLIP looks for 2750/<class>/
    shutil.move(f"{d}/EuroSAT_RGB", f"{d}/2750")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", default=os.path.expanduser("~/fpl_data"))
    root = ap.parse_args().data_root

    MNIST(f"{root}/mnist", 0).preprocess()

    d = f"{root}/eurosat"
    get_eurosat(d)
    missing = [c for c in EUROSAT_CLASSES if not os.path.isdir(f"{d}/2750/{c}")]
    assert not missing, f"EuroSAT: class folders {missing} missing under {d}/2750"
    # seed 0 = the seed of the first run, i.e. the split a fresh run would make itself (80/10/10)
    EuroSAT(d, 0).preprocess()

    for name in ("mnist", "eurosat"):
        counts = [sum(len(os.listdir(f"{root}/{name}/{s}/{c}")) for c in os.listdir(f"{root}/{name}/{s}"))
                  for s in ("train", "val", "test")]
        print(f"{name}: train/val/test images {counts}")
    print("data ready")


if __name__ == "__main__":
    main()
