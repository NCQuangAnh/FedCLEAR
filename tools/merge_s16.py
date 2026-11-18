"""Merge extracted 16-shot Kaggle zips into results/16-shot/<Dataset>/<FedCLEAR|PromptFL>/.

Usage: python tools/merge_s16.py <dir with one extracted folder per notebook> results/16-shot <notebook> [...]
Checks rc 0, refuses duplicates, adds the notebook name to each run_index.json entry.
"""
import json, shutil, sys
from pathlib import Path
src_root = Path(sys.argv[1]); dst_root = Path(sys.argv[2]); nbs = sys.argv[3:]
DS = {"caltech101": "Caltech101", "eurosat": "EuroSAT", "mnist": "MNIST", "oxford_pets": "Pets", "dtd": "DTD"}
ME = {"gatefcn16": "FedCLEAR", "pflcn16": "PromptFL", "pflcn32": "PromptFL", "gatefcn32": "FedCLEAR", "pflcn64": "PromptFL", "gatefcn64": "FedCLEAR", "pflcnfull": "PromptFL", "gatefcnfull": "FedCLEAR", "gatefcn8": "FedCLEAR", "pflcn8": "PromptFL", "zscn": "ZeroShot"}
for nb in nbs:
    src = src_root / nb
    idx = json.loads((src / "run_index.json").read_text())
    for name, e in idx.items():
        assert e["returncode"] == 0, name
        dst = dst_root / DS[e["dataset"]] / ME[e["arm"].rsplit("_", 1)[-1]]
        (dst / "logs").mkdir(parents=True, exist_ok=True); (dst / "runs").mkdir(exist_ok=True)
        assert not (dst / "runs" / name).exists() and not (dst / "logs" / f"{name}.txt").exists(), f"exists {name}"
        shutil.copytree(src / "runs" / name, dst / "runs" / name)
        shutil.copy2(src / "logs" / f"{name}.txt", dst / "logs" / f"{name}.txt")
        p = dst / "run_index.json"
        d = json.loads(p.read_text()) if p.exists() else {}
        d[name] = {**e, "notebook": nb}
        p.write_text(json.dumps(d, indent=1))
        print(f"{nb}: {name} -> {dst.relative_to(dst_root)} ({e['seconds']/3600:.2f} h)")
