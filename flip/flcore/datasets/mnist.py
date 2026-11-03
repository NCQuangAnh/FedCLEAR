import os
import random
import shutil

from .base import DataPreProcess
from .utils import check_dirs_exist


class MNIST(DataPreProcess):
    """MNIST as image folders, so it goes through the same ImageFolder path as the other datasets.

    The first run downloads MNIST with torchvision and writes it out as PNG files:
    test = the official 10k test set, val = 10% of the official training set, train = the rest.
    The val split uses a fixed seed (0), not the run seed, so every run sees the same folders.
    Class folders are named 0..9; the CLIP template turns them into 'a photo of the number: "3".'
    """

    dataset_dir = "mnist"

    def __init__(self, dataset_path, seed):
        self.dataset_dir = dataset_path
        self.seed = seed

    def preprocess(self,):
        if check_dirs_exist(self.dataset_dir, ['train', 'val', 'test']):
            print('Dataset has already been preprocessed!')
            return
        from torchvision.datasets import MNIST as TvMNIST
        os.makedirs(self.dataset_dir, exist_ok=True)
        raw = os.path.join(self.dataset_dir, 'raw')
        train_set = TvMNIST(raw, train=True, download=True)
        test_set = TvMNIST(raw, train=False, download=True)

        idx = list(range(len(train_set)))
        random.Random(0).shuffle(idx)
        n_val = len(idx) // 10
        parts = {'val': [(train_set, i) for i in idx[:n_val]],
                 'train': [(train_set, i) for i in idx[n_val:]],
                 'test': [(test_set, i) for i in range(len(test_set))]}

        # build in a private folder and move each split into place at the end, so a run that is
        # killed half way (or two runs starting together) never leaves a half-written split behind
        tmp = os.path.join(self.dataset_dir, f'.build_{os.getpid()}')
        for split, items in parts.items():
            for c in range(10):
                os.makedirs(os.path.join(tmp, split, str(c)), exist_ok=True)
            for ds, i in items:
                img, label = ds[i]
                img.save(os.path.join(tmp, split, str(int(label)), f'{split}_{i:05d}.png'))
            print(f'MNIST {split}: {len(items)} images')
        for split in parts:
            target = os.path.join(self.dataset_dir, split)
            if not os.path.exists(target):
                os.rename(os.path.join(tmp, split), target)
        shutil.rmtree(tmp, ignore_errors=True)
        print('MNIST train/val/test folders done!')
