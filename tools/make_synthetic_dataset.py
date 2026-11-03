"""Create a tiny synthetic ImageFolder dataset in the layout FLIP expects.

FLIP skips its split-by-json preprocessing when <data_root>/<name>/{train,val,test}
already exist, so random images are enough to exercise the whole pipeline on CPU.
Accuracy on this data is meaningless; the goal is only "does every code path run".

Usage:
    python tools/make_synthetic_dataset.py --data_root smoke_data --name dtd
"""
import argparse
import os

import numpy as np
from PIL import Image


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_root", required=True)
    parser.add_argument("--name", default="dtd", help="must be a dataset key known to FLIP")
    parser.add_argument("--num_classes", type=int, default=6, help=">=5, FLIP always computes top-5")
    parser.add_argument("--train", type=int, default=8)
    parser.add_argument("--val", type=int, default=2)
    parser.add_argument("--test", type=int, default=4)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    if args.num_classes < 5:
        raise SystemExit("num_classes must be >= 5 because FLIP evaluates top-5 accuracy")

    rng = np.random.default_rng(args.seed)
    root = os.path.join(args.data_root, args.name)
    for split, n in (("train", args.train), ("val", args.val), ("test", args.test)):
        for c in range(args.num_classes):
            folder = os.path.join(root, split, f"class{c:02d}")
            os.makedirs(folder, exist_ok=True)
            for i in range(n):
                # the per-class offset has to stay inside uint8: 20 * c overflowed at
                # 13 classes, which capped the smoke set below what a 10-client
                # Dirichlet split needs
                off = int(160 * c / max(args.num_classes - 1, 1))
                img = (rng.random((240, 240, 3)) * 80).astype("uint8") + np.uint8(off)
                Image.fromarray(img).save(os.path.join(folder, f"c{c:02d}_{i}.jpg"))
    print(f"synthetic '{args.name}' written to {root}")


if __name__ == "__main__":
    main()
