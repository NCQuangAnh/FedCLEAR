"""Parse FLIP stdout logs into per-run accuracy curves and summary metrics.

FLIP only stores the best test accuracy over all rounds (a selection-biased number).
We also report the last-round accuracy and the mean of the last 10 rounds, parsed
from the per-round log lines:
    round 12, train loss: 0.873±3.1%, top1: 57.21%, elapsed: ...
A single process started with --times N logs N runs back to back; each run restarts
at "round 0".

Usage:
    python tools/parse_flip_log.py logs/dtd_CoOp.txt [more logs...] --json out.json
"""
import argparse
import json
import re
import statistics

ROUND_RE = re.compile(r"round (\d+), train loss: .*?top1: ([\d.]+)%")
ZS_RE = re.compile(r"CLIP acc: ([\d.]+)%")


def parse_log(path):
    runs, curve = [], []
    zero_shot = None
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            m = ROUND_RE.search(line)
            if m:
                rnd, acc = int(m.group(1)), float(m.group(2))
                if rnd == 0 and curve:
                    runs.append(curve)
                    curve = []
                curve.append(acc)
                continue
            z = ZS_RE.search(line)
            if z:
                zero_shot = float(z.group(1))
    if curve:
        runs.append(curve)
    return runs, zero_shot


def summarize_run(curve, last_k=10):
    return {
        "rounds": len(curve),
        "best": max(curve),
        "last": curve[-1],
        f"last{last_k}_mean": statistics.fmean(curve[-last_k:]),
    }


def mean_sd(values):
    if not values:
        return None
    sd = statistics.stdev(values) if len(values) > 1 else 0.0
    return {"mean": statistics.fmean(values), "sd": sd, "n": len(values)}


def summarize_log(path):
    runs, zero_shot = parse_log(path)
    if zero_shot is not None and not runs:
        return {"log": path, "zero_shot": zero_shot}
    per_run = [summarize_run(c) for c in runs]
    out = {"log": path, "runs": per_run, "curves": runs}
    for key in ("best", "last", "last10_mean"):
        out[key] = mean_sd([r[key] for r in per_run])
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("logs", nargs="+")
    parser.add_argument("--json", help="write the full summary here")
    args = parser.parse_args()

    summaries = [summarize_log(p) for p in args.logs]
    for s in summaries:
        if "zero_shot" in s:
            print(f"{s['log']}: zero-shot {s['zero_shot']:.2f}")
            continue
        parts = [f"{k} {s[k]['mean']:.2f}±{s[k]['sd']:.2f}" for k in ("best", "last", "last10_mean") if s[k]]
        print(f"{s['log']}: runs={len(s['runs'])} | " + " | ".join(parts))
    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(summaries, f, indent=1)


if __name__ == "__main__":
    main()
