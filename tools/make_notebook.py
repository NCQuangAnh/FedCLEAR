"""Build a clean Kaggle notebook for a list of runs.

Replaces tools/build_kaggle_notebook.py for new experiments (that one is kept only so the old
notebooks can be rebuilt). Every arm is spelled out as plain command-line flags in ARM_ARGS, the
notebook holds only what a run needs, and one call writes one notebook.

Usage (from the repo root):
    python tools/make_notebook.py <name> <dataset>:<arm>,<arm> [<dataset>:<arm>,...]
    e.g. python tools/make_notebook.py gate_d2_pets_1 oxford_pets:S_sym_full,S_pair_full
Writes kaggle/<name>.ipynb.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# --- arms ---------------------------------------------------------------------------------------
# Scenario flags. Careless clients are the same clients for a given seed in every scenario.
SCENARIOS = {
    "sym": ("--noise_type", "sym", "--noise_rate", "0.4", "--noisy_client_frac", "0.3"),
    "pair": ("--noise_type", "pair", "--noise_rate", "0.4", "--noisy_client_frac", "0.3"),
    "inst": ("--noise_type", "instance", "--noise_rate", "0.4", "--noisy_client_frac", "0.3"),
    "het": ("--noise_type", "sym", "--noise_mode", "hetero", "--noise_rate", "0.8",
            "--noisy_client_frac", "0.5"),
    "clean": ("--noise_type", "sym", "--noise_rate", "0", "--noisy_client_frac", "0"),
}
BASE = ("--attacker_model", "data", "--data_transform", "paper",
        "--attack_type", "none", "--malicious_client_frac", "0")
# gate D stage 2 (results/side-research/gate_D/gate_d2_plan.md)
METHODS = {
    "full": ("--sure", "true"),
    "budget": ("--sure", "true", "--sure_budget", "excess"),                # gate D stage 3
    "keep": ("--sure", "true", "--sure_unsure", "keep"),                    # gate D stage 3
    "nlp": ("--nlprompt", "uniform"),                                       # NLPrompt, as published
    "nlph": ("--nlprompt", "hist"),                                         # NLPrompt, client histogram
    "prox": ("--prox_mu", "0.01"),                                          # FedProx + CoOp baseline
    "corr": ("--fedcorr", "true"),           # FedCorr + CoOp baseline (results/side-research/fedcorr)
    "rg": ("--fedrg", "true"),               # FedRG (CVPR 2026), CLIP-adapted (results/side-research/fedrg)
    # zero-shot CLIP, FLIP's own --prompt_algo CLIP (overrides CoOp): no training, test set only
    "zs": ("--prompt_algo", "CLIP"),
    "all": ("--sure", "true", "--sure_scope", "all"),                       # no client decision
    "noclip": ("--sure", "true", "--sure_dist", "g", "--sure_tau", "0.072"),  # no zero-shot mix
    # no look-alike merge (plain excess surprise); tau = its own Pets clean p95 (0.0725), same rule
    # as noclip. MNIST/EuroSAT diagnosis, results/side-research/mnist_eurosat/plan.md
    "nomerge": ("--sure", "true", "--sure_score", "xs", "--sure_tau", "0.072"),
    "d": ("--sure", "true", "--sure_dist", "g", "--sure_score", "dis",        # old score
          "--sure_tau", "0.304"),
    # cap study (results/side-research/cap_study/cap_plan.md): no 60% cap, suspect threshold 0.1 / 0.05 / 0.2
    "nc": ("--sure", "true", "--sure_max_frac", "1.0"),
    "nc05": ("--sure", "true", "--sure_max_frac", "1.0", "--sure_img_thr", "0.05"),
    "nc20": ("--sure", "true", "--sure_max_frac", "1.0", "--sure_img_thr", "0.2"),
    # CLEAR-FPL v2 (results/side-research/clear2/clear2_plan.md): noise-rate audit from zero-shot CLIP
    "v2": ("--sure", "true", "--sure_audit", "true"),
    "v2m": ("--sure", "true", "--sure_audit", "true", "--sure_audit_merge", "true"),
    # CLEAR-FPL + calibrated repair (results/side-research/calrepair/calrepair_plan.md): pooled
    # noise-aware temperature, extra flag on the calibrated score, prediction-set suspects, no cap
    "cal": ("--sure", "true", "--sure_cal", "noise"),
    # referee-strength gate (results/side-research/calrepair/gate_confirm_plan.md): CLEAR-FPL for
    # rounds 0-5, then cal's repair without its extra flag only if relabelled / suspects is high
    "gate": ("--sure", "true", "--sure_cal", "noise", "--sure_cal_flag", "false", "--sure_gate", "0.12"),
    # gate with the temperature capped at 1 (results/side-research/calrepair/gatec_plan.md): the
    # calibration may sharpen P but never soften it (the Pets N pair75 collapse)
    "gatec": ("--sure", "true", "--sure_cal", "noise", "--sure_cal_flag", "false", "--sure_gate", "0.12",
              "--sure_cal_tmax", "1"),
    # gatec plus a suspect floor at the client's own noise estimate (results/side-research/calrepair/
    # gatef_plan.md): in calibrated mode a flagged client never suspects fewer images than it
    # estimates are wrong (the DTD N pair75 seed 5 collapse)
    "gatef": ("--sure", "true", "--sure_cal", "noise", "--sure_cal_flag", "false", "--sure_gate", "0.12",
              "--sure_cal_tmax", "1", "--sure_cal_floor", "true"),
}
ARM_ARGS = {f"S_{sc}_{m}": BASE + SCENARIOS[sc] + METHODS[m] for sc in SCENARIOS for m in METHODS}

# gate D stage 1 arms, flags exactly as those runs used them (comparators: none / MAE / DBR-FPL)
D_BASE = ("--attacker_model", "data", "--data_transform", "paper", "--noise_type", "sym",
          "--noise_rate", "0.4", "--noisy_client_frac", "0.3", "--malicious_client_frac", "0.2",
          "--log_signals", "true", "--correction_every", "5", "--attack_type", "none",
          "--malicious_client_frac", "0")
D_SCEN = {"sym": (), "pair": ("--noise_type", "pair"), "inst": ("--noise_type", "instance"),
          "het": ("--noise_mode", "hetero", "--noise_rate", "0.8", "--noisy_client_frac", "0.5"),
          "clean": ("--noise_rate", "0", "--noisy_client_frac", "0")}
D_DIAG = ("--diag_scores", "true", "--diag_samples_every", "5")
D_DBR = ("--correction_audit", "true", "--sample_filter", "rho", "--filter_soft", "auto",
         "--filter_clean_band", "0.10", "--filter_relabel", "conf", "--filter_relabel_conf", "0.5")
for _sc, _x in D_SCEN.items():
    ARM_ARGS[f"D_{_sc}_none"] = D_BASE + _x + D_DIAG
    ARM_ARGS[f"D_{_sc}_mae"] = D_BASE + _x + D_DIAG + ("--loss_type", "mae")
    ARM_ARGS[f"D_{_sc}_dbr"] = D_BASE + D_DBR + _x + D_DIAG

HELD_OUT = ("--seed", "5", "--times", "3")
CONFIRM = ("--seed", "8", "--times", "3")      # gatef_plan.md stage H: fresh seeds 8, 9, 10
# gate N (results/side-research/gate_N/gate_n_plan.md): NLPrompt-style noise in FL. Every client is
# noisy at the same rate, symmetric or pair (NLPrompt's "asym": flip to the next class).
for _nt, _tag in (("sym", "sym"), ("pair", "pair")):
    for _r in ("25", "50", "75"):
        _sc = ("--noise_type", _nt, "--noise_rate", str(int(_r) / 100), "--noisy_client_frac", "1.0")
        ARM_ARGS[f"N_{_tag}{_r}_none"] = BASE + _sc
        ARM_ARGS[f"N_{_tag}{_r}_mae"] = BASE + _sc + ("--loss_type", "mae")
        ARM_ARGS[f"N_{_tag}{_r}_dbr"] = BASE + _sc + ("--correction_every", "5") + D_DBR
        ARM_ARGS[f"N_{_tag}{_r}_clear"] = BASE + _sc + ("--sure", "true")
        ARM_ARGS[f"N_{_tag}{_r}_nlp"] = BASE + _sc + ("--nlprompt", "uniform")
        ARM_ARGS[f"N_{_tag}{_r}_nlph"] = BASE + _sc + ("--nlprompt", "hist")
        ARM_ARGS[f"N_{_tag}{_r}_prox"] = BASE + _sc + ("--prox_mu", "0.01")
        for _m in ("nc", "nc05", "nc20", "v2", "v2m", "corr", "zs", "cal", "gate", "gatec", "gatef", "rg"):
            ARM_ARGS[f"N_{_tag}{_r}_{_m}"] = BASE + _sc + METHODS[_m]
        # gatec_plan.md stage 2: held-out seeds 5, 6, 7 (every earlier run used seeds 0-4), with
        # CLEAR-FPL on the same seeds as the comparator
        ARM_ARGS[f"N_{_tag}{_r}_gatech"] = ARM_ARGS[f"N_{_tag}{_r}_gatec"] + HELD_OUT
        ARM_ARGS[f"N_{_tag}{_r}_clearh"] = ARM_ARGS[f"N_{_tag}{_r}_clear"] + HELD_OUT
        # gatef_plan.md: development on seeds 5-7 (gatefh), confirmation on fresh seeds 8-10
        ARM_ARGS[f"N_{_tag}{_r}_gatefh"] = ARM_ARGS[f"N_{_tag}{_r}_gatef"] + HELD_OUT
        ARM_ARGS[f"N_{_tag}{_r}_gatefc"] = ARM_ARGS[f"N_{_tag}{_r}_gatef"] + CONFIRM
        ARM_ARGS[f"N_{_tag}{_r}_clearc"] = ARM_ARGS[f"N_{_tag}{_r}_clear"] + CONFIRM
        # PromptFL with per-image logs at high noise: the referee findings (clear2_plan.md, F2/F3)
        ARM_ARGS[f"N_{_tag}{_r}_diag"] = BASE + _sc + D_DIAG

# 20-client study (results/side-research/clients20/c20_plan.md): same scenarios with --num_clients 20,
# which overrides COMMON's 10 (argparse keeps the last value). The fractions stay, so sym / pair /
# inst have 6 noisy clients at 40%, het has 10 noisy clients at 8%, 16%, ..., 80%, N_ all 20.
# c20 = CLEAR-FPL, c20p = PromptFL (plain CoOp + FedAvg) as its reference.
C20 = ("--num_clients", "20")
for _sc in SCENARIOS:
    ARM_ARGS[f"S_{_sc}_c20"] = BASE + SCENARIOS[_sc] + METHODS["full"] + C20
    ARM_ARGS[f"S_{_sc}_c20p"] = BASE + SCENARIOS[_sc] + C20
for _nt, _tag in (("sym", "sym"), ("pair", "pair")):
    for _r in ("25", "50", "75"):
        ARM_ARGS[f"N_{_tag}{_r}_c20"] = ARM_ARGS[f"N_{_tag}{_r}_clear"] + C20
        ARM_ARGS[f"N_{_tag}{_r}_c20p"] = ARM_ARGS[f"N_{_tag}{_r}_none"] + C20

# stage 0 of the referee study (results/side-research/referee_calib/margin_plan.md): PromptFL
# exactly as the gate D / gate N runs, logged only, plus every class's log-probability per image
# (--diag_full_probs), 3 seeds (--times overrides the notebook's 5; argparse keeps the last value)
FP = ("--diag_full_probs", "true", "--times", "3")
for _sc, _x in D_SCEN.items():
    ARM_ARGS[f"D_{_sc}_fp"] = D_BASE + _x + D_DIAG + FP
for _nt, _tag in (("sym", "sym"), ("pair", "pair")):
    for _r in ("25", "50", "75"):
        ARM_ARGS[f"N_{_tag}{_r}_fp"] = ARM_ARGS[f"N_{_tag}{_r}_none"] + D_DIAG + FP

# seconds per round on a Kaggle T4 for a --sure run; replaced by the measured rate after the
# first run of a session
SEC_PER_ROUND = {"oxford_pets": 22.0, "dtd": 25.0, "caltech101": 50.0,
                 "mnist": 12.0, "eurosat": 10.0}   # MNIST / EuroSAT: guesses, PromptFL EuroSAT measured 5.2   # --sure runs; D_ runs with scores take ~1.3x


def md(text):
    return {"cell_type": "markdown", "metadata": {}, "source": text.strip("\n").splitlines(True)}


def code(text):
    return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [],
            "source": text.strip("\n").splitlines(True)}


def build(name, plan, budget=11.5, hard=11.8):
    runs = "\n".join(f"#   {ds}: {', '.join(arms)}" for ds, arms in plan.items())
    arm_lines = ",\n".join(f'    "{a}": {json.dumps(list(ARM_ARGS[a]))}'
                           for arms in plan.values() for a in arms)
    cells = [
        md(f"""
# {name}

1. Add the private dataset made by `python tools/package_code.py` (`dist/fpl-triage-code.zip`) as input.
2. Run all cells. Nothing needs editing.
3. Download `/kaggle/working/{name}.zip` at the end.
"""),
        code(f"""
import glob, json, os, re, shutil, statistics, subprocess, sys, threading, time

NAME = "{name}"
PLAN = {json.dumps(plan)}
# runs in this notebook:
{runs}
ARM_ARGS = {{
{arm_lines}
}}
TIMES, ROUNDS = 5, 50
BUDGET_HOURS = {budget}          # a run that would end past this is skipped, not started
HARD_HOURS = {hard}          # a run still going at this point is killed, so the zip is always made
SEC_PER_ROUND = {json.dumps(SEC_PER_ROUND)}

WORK = "/kaggle/working"
OUT = f"{{WORK}}/{{NAME}}"
DATA_ROOT = "/tmp/fpl_data"
CLIP_CACHE = f"{{WORK}}/clip_cache"
CODE = f"{{WORK}}/code"
NOTEBOOK_START = time.time()
hits = glob.glob("/kaggle/input/**/flip/main.py", recursive=True)
assert hits, "attach the dataset built by tools/package_code.py"
CODE_INPUT = os.path.dirname(os.path.dirname(hits[0]))
print("code:", CODE_INPUT)
"""),
        code("""
subprocess.run("nvidia-smi", shell=True)
if not os.path.exists(CODE):
    shutil.copytree(CODE_INPUT, CODE)
os.makedirs(f"{OUT}/logs", exist_ok=True)

# Kaggle unpacks .gz files inside datasets, which removes CLIP's BPE vocab: put it back
import gzip, hashlib, urllib.request
BPE = f"{CODE}/flip/flcore/models/clip/bpe_simple_vocab_16e6.txt.gz"
if not os.path.isfile(BPE):
    if os.path.isfile(BPE[:-3]):
        with open(BPE[:-3], "rb") as fi, gzip.open(BPE, "wb") as fo:
            shutil.copyfileobj(fi, fo)
    else:
        urllib.request.urlretrieve("https://github.com/openai/CLIP/raw/main/clip/bpe_simple_vocab_16e6.txt.gz", BPE)
        assert hashlib.sha256(open(BPE, "rb").read()).hexdigest() == \\
            "924691ac288e54409236115652ad4aa250f48203de50a9e4722a6ecd48d6804a"

need = {"ftfy": "ftfy", "regex": "regex", "gdown": "gdown", "h5py": "h5py",
        "cv2": "opencv-python-headless", "termcolor": "termcolor",
        "tensorboard": "tensorboard", "sklearn": "scikit-learn", "pyarrow": "pyarrow"}
missing = []
for mod, pkg in need.items():
    try:
        __import__(mod)
    except ImportError:
        missing.append(pkg)
if missing:
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", *missing], check=True)
import torch
print("torch", torch.__version__, "| cuda", torch.cuda.is_available())
"""),
        code("""
import gdown

SPLITS = {"caltech101": ("1hyarUivQE36mY6jSomru6Fjd-JzwcCzN", "split_zhou_Caltech101.json"),
          "dtd": ("1u3_QfB467jqHgNXC00UIzbLZRQCg2S7x", "split_zhou_DescribableTextures.json"),
          "oxford_pets": ("1501r8Ber4nNKvmlFVQZ8SeUHTcdTTEqs", "split_zhou_OxfordPets.json")}


def sh(cmd):
    print("$", cmd)
    subprocess.run(cmd, shell=True, check=True)


def fetch(urls, dst):
    # the Oxford VGG host sometimes answers 500; thor.robots.ox.ac.uk serves the same files
    for url in urls:
        rc = subprocess.run(f"wget -q --timeout=60 --tries=2 -O {dst} {url}", shell=True).returncode
        if rc == 0 and os.path.getsize(dst) > 1_000_000:
            print("got", url)
            return
        print("failed", url)
    raise RuntimeError(f"every mirror failed: {urls}")


# Hugging Face mirrors with the original file names and JPEG bytes, used when both Oxford hosts are
# down (checked 2026-10-31: banded_0002.jpg has the same md5 as the server's Oxford copy)
HF_MIRRORS = {
    "dtd": ("split_zhou_DescribableTextures.json", "https://huggingface.co/datasets/jxie/dtd/resolve/main/data/",
            ["train-00000-of-00001-ebe06d6bffa9b3c3.parquet",
             "validation-00000-of-00001-4c0e2e1fd7fbd259.parquet",
             "test-00000-of-00001-b49cbb6beb34aad1.parquet"]),
    "oxford_pets": ("split_zhou_OxfordPets.json",
                    "https://huggingface.co/datasets/timm/oxford-iiit-pet/resolve/main/data/",
                    ["train-00000-of-00001.parquet", "test-00000-of-00001.parquet"]),
}


def from_hf(name, d):
    # every image goes where Zhou's split file expects it (images/<rel>); all of them must be there
    import pyarrow.parquet as pq
    split_file, base, parts = HF_MIRRORS[name]
    split = json.load(open(f"{CODE}/splits/{split_file}"))
    where = {p.split("/")[-1]: p for part in split.values() for p, _, _ in part}
    written = set()
    for part in parts:
        sh(f"wget -q --timeout=60 --tries=3 -O /tmp/mirror.parquet {base}{part}")
        for img in pq.read_table("/tmp/mirror.parquet", columns=["image"]).column("image").to_pylist():
            rel = where.get(os.path.basename(img["path"] or ""))
            if rel:
                os.makedirs(os.path.dirname(f"{d}/images/{rel}"), exist_ok=True)
                with open(f"{d}/images/{rel}", "wb") as f:
                    f.write(img["bytes"])
                written.add(rel)
        os.remove("/tmp/mirror.parquet")
    lost = set(where.values()) - written
    assert not lost, f"{len(lost)} {name} images not in the mirror, e.g. {sorted(lost)[:3]}"
    print(name, "from the Hugging Face mirror:", len(written), "images")


def prepare(name):
    d = f"{DATA_ROOT}/{name}"
    os.makedirs(d, exist_ok=True)
    if name == "caltech101" and not os.path.isdir(f"{d}/101_ObjectCategories"):
        sh("wget -q -O /tmp/c.zip https://data.caltech.edu/records/mzrjq-6wc02/files/caltech-101.zip")
        sh("rm -rf /tmp/cz && unzip -q /tmp/c.zip -d /tmp/cz")
        tgz = glob.glob("/tmp/cz/**/101_ObjectCategories.tar.gz", recursive=True)[0]
        sh(f"tar -xzf {tgz} -C {d} && rm -rf /tmp/c.zip /tmp/cz")
    if name == "dtd" and not os.path.isdir(f"{d}/images"):
        try:
            fetch(["https://thor.robots.ox.ac.uk/dtd/dtd-r1.0.1.tar.gz",
                   "https://www.robots.ox.ac.uk/~vgg/data/dtd/download/dtd-r1.0.1.tar.gz"], "/tmp/dtd.tar.gz")
            sh(f"tar -xzf /tmp/dtd.tar.gz -C {DATA_ROOT} && rm /tmp/dtd.tar.gz")
        except RuntimeError:
            from_hf("dtd", d)
    if name == "oxford_pets" and not os.path.isdir(f"{d}/images"):
        try:
            for part in ("images", "annotations"):
                fetch([f"https://thor.robots.ox.ac.uk/pets/{part}.tar.gz",
                       f"https://www.robots.ox.ac.uk/~vgg/data/pets/data/{part}.tar.gz"], f"/tmp/{part}.tar.gz")
                sh(f"tar -xzf /tmp/{part}.tar.gz -C {d} && rm /tmp/{part}.tar.gz")
        except RuntimeError:
            from_hf("oxford_pets", d)     # only images/ and the split file are read
    if name in ("mnist", "eurosat"):
        # no CoOp split file: MNIST is written out from torchvision, EuroSAT comes from Zenodo, and
        # both get their train/val/test folders here with seed 0, as server/prep_mnist_eurosat.py does
        sys.path[:0] = [f"{CODE}/flip", f"{CODE}/server"]
        from prep_mnist_eurosat import EuroSAT, MNIST, get_eurosat
        if name == "mnist":
            MNIST(d, 0).preprocess()
        else:
            get_eurosat(d)
            EuroSAT(d, 0).preprocess()
        print(name, "ready")
        return
    file_id, fname = SPLITS[name]
    if not os.path.exists(f"{d}/{fname}"):
        if os.path.isfile(f"{CODE}/splits/{fname}"):      # shipped with the code
            shutil.copy(f"{CODE}/splits/{fname}", d)
        else:
            gdown.download(id=file_id, output=f"{d}/{fname}", quiet=True)
    print(name, "ready")


for ds in PLAN:
    prepare(ds)
"""),
        code("""
COMMON = ["--benchmark", "global", "--image_backbone", "RN50", "--optim_name", "sgd",
          "--lr_scheduler", "cos", "--split_alpha", "0.1", "--loss_type", "ce", "--central", "false",
          "--num_clients", "10", "--num_shot", "8", "--optim_momentum", "0.9",
          "--local_learning_rate", "0.002", "--batch_size", "16", "--eval_scaler", "2",
          "--num_prompt", "1", "--local_epochs", "1", "--prompt_batch_size", "2", "--precision", "amp",
          "--log_metrics", "true",    # macro P/R/F1 + round cost -> metrics_seed_<seed>.json
          "--num_workers", "4", "--data_root", DATA_ROOT, "--verbose2", "--cache_test_feats", "true"]
INDEX = f"{OUT}/run_index.json"
ROUND_RE = re.compile(r"round (\\d+), .*?top1: ([\\d.]+)%, elapsed: ([\\d.]+)s")
rates = {}


def run(ds, arm):
    index = json.load(open(INDEX)) if os.path.exists(INDEX) else {}
    tag = f"{ds}_{arm}"
    if index.get(tag, {}).get("returncode") == 0:
        return
    used = (time.time() - NOTEBOOK_START) / 3600
    seeds = TIMES                # an arm may override the seed count with its own --times
    for i, a in enumerate(ARM_ARGS[arm][:-1]):
        if a == "--times":
            seeds = int(ARM_ARGS[arm][i + 1])
    # rate per (dataset, method): a CLEAR run is ~1.45x a FedRG run on the same data. A method not
    # measured yet uses the dataset's slowest measured rate x 1.5, else the default guess
    method = arm.rsplit("_", 1)[-1]
    known = [r for (d, _), r in rates.items() if d == ds]
    rate = rates.get((ds, method), 1.5 * max(known) if known else SEC_PER_ROUND[ds])
    need = rate * (ROUNDS + 1) * seeds / 3600 + 0.1
    if used + need > BUDGET_HOURS:
        print(f"SKIPPED {tag}: needs ~{need:.1f} h, {BUDGET_HOURS - used:.1f} h left")
        return
    print(f"start {tag} (~{need:.1f} h, notebook at {used:.1f} h)", flush=True)
    run_dir, log = f"{OUT}/runs/{tag}", f"{OUT}/logs/{tag}.txt"
    os.makedirs(run_dir, exist_ok=True)
    env = dict(os.environ, PYTHONPATH=f"{CODE}/flip", FLIP_CLIP_CACHE=CLIP_CACHE, PYTHONUNBUFFERED="1")
    cmd = [sys.executable, f"{CODE}/flip/main.py", "--dataset", ds, "--prompt_algo", "CoOp",
           "--times", str(TIMES), "--global_rounds", str(ROUNDS), *COMMON, *ARM_ARGS[arm]]
    t0, seen = time.time(), []
    with open(log, "w") as f:
        proc = subprocess.Popen(cmd, cwd=run_dir, env=env, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, text=True, bufsize=1)
        left = HARD_HOURS * 3600 - (time.time() - NOTEBOOK_START)
        killer = threading.Timer(max(left, 0), proc.kill)
        killer.start()
        for line in proc.stdout:
            f.write(line)
            m = ROUND_RE.search(line)
            if m:
                seen.append(float(m.group(3)))
                if int(m.group(1)) % 10 == 0:
                    print(f"  [{tag}] round {m.group(1)} top1 {m.group(2)}% "
                          f"({(time.time() - t0) / 60:.0f} min)", flush=True)
            elif "Traceback" in line or "Error" in line:
                print(f"  [{tag}] {line.strip()}", flush=True)
        proc.wait()
        killer.cancel()
    if proc.returncode != 0 and time.time() - NOTEBOOK_START >= HARD_HOURS * 3600:
        print(f"KILLED {tag} at the hard limit of {HARD_HOURS} h", flush=True)
    if seen:
        rates[(ds, method)] = statistics.fmean(seen)
    index[tag] = {"dataset": ds, "arm": arm, "args": list(ARM_ARGS[arm]),
                  "returncode": proc.returncode, "seconds": round(time.time() - t0, 1)}
    json.dump(index, open(INDEX, "w"), indent=1)
    print(f"{tag}: rc={proc.returncode} in {(time.time() - t0) / 3600:.2f} h")
    if proc.returncode != 0:
        print("".join(open(log).readlines()[-30:]))


for ds, arms in PLAN.items():
    for arm in arms:
        run(ds, arm)
"""),
        code("""
# last10 accuracy per run, then the zip to download
for tag in sorted(json.load(open(INDEX)) if os.path.exists(INDEX) else {}):
    seeds, cur = [], None
    for line in open(f"{OUT}/logs/{tag}.txt", errors="replace"):
        m = ROUND_RE.search(line)
        if m:
            if int(m.group(1)) == 0:
                cur = []
                seeds.append(cur)
            cur.append(float(m.group(2)))
    vals = [statistics.fmean(s[-10:]) for s in seeds if len(s) > 10]
    if vals:
        print(f"{tag}: {statistics.fmean(vals):.2f} over {len(vals)} seeds {[round(v, 2) for v in vals]}")
archive = shutil.make_archive(f"{WORK}/{NAME}", "zip", OUT)
print(archive, "%.1f MB" % (os.path.getsize(archive) / 1e6))
"""),
    ]
    nb = {"cells": cells, "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python",
                                                      "name": "python3"},
                                       "language_info": {"name": "python"}},
          "nbformat": 4, "nbformat_minor": 5}
    path = os.path.join(ROOT, "kaggle", f"{name}.ipynb")
    json.dump(nb, open(path, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    return path


def main():
    # optional --hours=H: the notebook must be done within H hours (skip runs past H - 0.4 h,
    # kill a run still going at H - 0.25 h; the zip is made after that)
    args = sys.argv[1:]
    hours = [float(a.split("=", 1)[1]) for a in args if a.startswith("--hours=")]
    args = [a for a in args if not a.startswith("--hours=")]
    name, specs = args[0], args[1:]
    limits = {"budget": round(hours[0] - 0.4, 2), "hard": round(hours[0] - 0.25, 2)} if hours else {}
    plan = {}
    for spec in specs:
        ds, arms = spec.split(":")
        plan[ds] = [a for a in arms.split(",") if a]
        unknown = [a for a in plan[ds] if a not in ARM_ARGS]
        assert not unknown, f"unknown arms {unknown}"
    print("wrote", build(name, plan, **limits))


if __name__ == "__main__":
    main()
