"""Run a queue of FLIP runs on a Linux GPU server (the Kaggle notebooks, without Kaggle).

Each run is one arm of tools/make_notebook.py (same flags, same COMMON settings), 5 seeds,
50 rounds. Runs are spread over the GPUs listed in --gpus, --per-gpu at a time on each. Finished
runs (returncode 0 in run_index.json) are skipped, so the script can simply be started again
after a crash or a lost SSH session.

Usage (from the repo root):
    mkdir -p results/server
    python server/run_queue.py --queue server/queue_caltech.txt --gpus 0 --per-gpu 2
    python server/run_queue.py --queue server/queue_caltech.txt --status     # progress only
Output: results/server/<queue name>/{runs,logs,run_index.json}
"""
import argparse
import json
import os
import re
import statistics
import subprocess
import sys
import threading
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from make_notebook import ARM_ARGS  # noqa: E402  (the single source of every arm's flags)

COMMON = ["--benchmark", "global", "--image_backbone", "RN50", "--optim_name", "sgd",
          "--lr_scheduler", "cos", "--split_alpha", "0.1", "--loss_type", "ce", "--central", "false",
          "--num_clients", "10", "--num_shot", "8", "--optim_momentum", "0.9",
          "--local_learning_rate", "0.002", "--batch_size", "16", "--eval_scaler", "2",
          "--num_prompt", "1", "--local_epochs", "1", "--prompt_batch_size", "2", "--precision", "amp",
          "--log_metrics", "true",    # macro P/R/F1 + round cost -> metrics_seed_<seed>.json
          "--verbose2", "--cache_test_feats", "true"]
TIMES, ROUNDS = 5, 50
ROUND_RE = re.compile(r"round (\d+), .*?top1: ([\d.]+)%")
ZS_RE = re.compile(r"CLIP acc: ([\d.]+)%")      # --prompt_algo CLIP: one accuracy per seed, no rounds
lock = threading.Lock()


def read_queue(path):
    """Lines 'dataset arm'; '#' starts a comment."""
    jobs = []
    for line in open(path, encoding="utf-8"):
        line = line.split("#", 1)[0].strip()
        if line:
            ds, arm = line.split()
            assert arm in ARM_ARGS, f"unknown arm {arm}"
            jobs.append((ds, arm))
    return jobs


def load_index(path):
    return json.load(open(path)) if os.path.exists(path) else {}


def last10(log):
    seeds, cur = [], None
    for line in open(log, errors="replace"):
        m = ROUND_RE.search(line)
        if m:
            if int(m.group(1)) == 0:
                cur = []
                seeds.append(cur)
            cur.append(float(m.group(2)))
    zs = [float(m.group(1)) for m in map(ZS_RE.search, open(log, errors="replace")) if m]
    return [round(statistics.fmean(s[-10:]), 2) for s in seeds if len(s) == ROUNDS + 1] or zs


def run_one(ds, arm, gpu, out, args):
    tag = f"{ds}_{arm}"
    run_dir, log = f"{out}/runs/{tag}", f"{out}/logs/{tag}.txt"
    os.makedirs(run_dir, exist_ok=True)
    env = dict(os.environ, PYTHONPATH=f"{ROOT}/flip", PYTHONUNBUFFERED="1",
               CUDA_VISIBLE_DEVICES=str(gpu), FLIP_CLIP_CACHE=args.clip_cache)
    cmd = [sys.executable, f"{ROOT}/flip/main.py", "--dataset", ds, "--prompt_algo", "CoOp",
           "--times", str(TIMES), "--global_rounds", str(ROUNDS), *COMMON,
           "--num_workers", str(args.workers), "--data_root", args.data_root, *ARM_ARGS[arm]]
    t0 = time.time()
    print(f"[gpu {gpu}] start {tag}", flush=True)
    with open(log, "w") as f:
        rc = subprocess.run(cmd, cwd=run_dir, env=env, stdout=f, stderr=subprocess.STDOUT).returncode
    with lock:
        index = load_index(f"{out}/run_index.json")
        index[tag] = {"dataset": ds, "arm": arm, "args": list(ARM_ARGS[arm]), "returncode": rc,
                      "seconds": round(time.time() - t0, 1), "gpu": gpu}
        json.dump(index, open(f"{out}/run_index.json", "w"), indent=1)
    vals = last10(log)
    print(f"[gpu {gpu}] {tag}: rc={rc} in {(time.time() - t0) / 3600:.2f} h  last10 {vals}", flush=True)
    if rc != 0:
        print("".join(open(log, errors="replace").readlines()[-20:]), flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--queue", required=True)
    ap.add_argument("--gpus", default="0", help="comma-separated GPU ids")
    ap.add_argument("--per-gpu", type=int, default=1, help="runs at the same time on one GPU")
    ap.add_argument("--workers", type=int, default=4, help="data-loader workers per run")
    ap.add_argument("--data-root", default=os.path.expanduser("~/fpl_data"))
    ap.add_argument("--clip-cache", default=os.path.expanduser("~/.cache/clip"))
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--smoke", action="store_true", help="1 seed, 2 rounds, fp32: a quick check")
    args = ap.parse_args()
    global TIMES, ROUNDS
    if args.smoke:
        TIMES, ROUNDS = 1, 2
        COMMON[COMMON.index("--precision") + 1] = "fp32"
    name = os.path.splitext(os.path.basename(args.queue))[0]
    out = os.path.join(ROOT, "results", "server", name)
    os.makedirs(f"{out}/logs", exist_ok=True)
    jobs = read_queue(args.queue)
    index = load_index(f"{out}/run_index.json")
    done = [j for j in jobs if index.get(f"{j[0]}_{j[1]}", {}).get("returncode") == 0]
    todo = [j for j in jobs if j not in done]
    print(f"{name}: {len(done)}/{len(jobs)} done, {len(todo)} to run")
    if args.status:
        for ds, arm in jobs:
            e = index.get(f"{ds}_{arm}")
            state = "—" if not e else ("ok" if e["returncode"] == 0 else f"FAILED rc={e['returncode']}")
            log = f"{out}/logs/{ds}_{arm}.txt"
            extra = last10(log) if os.path.exists(log) else []
            print(f"  {ds}_{arm}: {state} {extra}")
        return

    # fail here, in a second, rather than burning through the queue with the same error
    chk = subprocess.run([sys.executable, "-c", "import torch, torchvision; "
                          "assert torch.cuda.is_available(), 'CUDA not available'; "
                          "print('torch', torch.__version__, torch.cuda.device_count(), 'GPU')"],
                         capture_output=True, text=True)
    if chk.returncode != 0 and not args.smoke:
        err = (chk.stderr.strip().splitlines() or ["unknown error"])[-1]
        print(f"{sys.executable} cannot run the jobs: {err}\n"
              "Activate the environment that has PyTorch with CUDA (see server/README.md), "
              "then start again.")
        sys.exit(1)
    print(chk.stdout.strip())

    pending = list(todo)
    slots = [int(g) for g in args.gpus.split(",") for _ in range(args.per_gpu)]
    fast_fails = []

    def worker(gpu):
        while True:
            with lock:
                if not pending:
                    return
                ds, arm = pending.pop(0)
            t0 = time.time()
            run_one(ds, arm, gpu, out, args)
            rc = load_index(f"{out}/run_index.json").get(f"{ds}_{arm}", {}).get("returncode")
            with lock:
                if rc != 0 and time.time() - t0 < 120:
                    fast_fails.append(arm)
                    if len(fast_fails) >= 3:
                        pending.clear()
                        print("3 runs failed right at start: stopping the queue. Read the error "
                              "above, fix it, and start again (finished runs are kept).", flush=True)
                else:
                    fast_fails.clear()

    threads = [threading.Thread(target=worker, args=(g,)) for g in slots]
    for t in threads:
        t.start()
        time.sleep(5)          # stagger the starts (data loading and CLIP load on the same disk)
    for t in threads:
        t.join()
    print("all done")


if __name__ == "__main__":
    main()
