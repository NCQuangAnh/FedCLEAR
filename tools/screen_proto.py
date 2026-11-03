"""Screen 2 of results/side-research/image_referee/screen_plan.md: an image-side referee from class
prototypes, on the real MNIST / EuroSAT images of this machine (.smoke/data_{mnist,eurosat}).

Per seed: 8 images per class from the local train pool, each class spread over 10 clients with
Dirichlet(0.1) proportions, label noise as flcore/datasets/noise.py with the arms' flags. Referees
for every training image, from CLIP RN50 (repository templates and class names):
  z            zero-shot CLIP, softmax(100 cos(f, text_k))
  proto_fed    softmax(100 cos(f, mu_k)), mu_k = normalised mean feature of the images labelled k
               over all clients (per-class sums and counts are what clients would send)
  proto_local  the same with the client's own images only (classes it lacks are left out)
  mix          1/2 (z + proto_fed)
Main measure: image-level AUROC of the given label's probability, wrong vs correct labels.
Reference: the same AUROC of CLEAR's e on the stage 0 runs (rounds 10-50, 3 seeds).
Exploratory: proto_loo (the client removes its own image from its label's sum), CL marks on each
referee (screen_cl.py's rule), N sym75 / pair75.

Usage: python tools/screen_proto.py   (writes results/side-research/image_referee/screen_proto.md;
features are cached in results/side-research/image_referee/feats_<ds>.npz)
"""
import os
import sys

import numpy as np
import torch
from PIL import Image

from analyze_baselines import SR
from screen_cl import cl_marks
from screen_stage0 import load_run

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "flip"))
from flcore.models.clip import clip  # noqa: E402
from flcore.models.text.prompt import CUSTOM_TEMPLATES  # noqa: E402
from flcore.datasets.eurosat import NEW_CNAMES_EURO  # noqa: E402

OUT_DIR = os.path.join(SR, "image_referee")
DATA = {"mnist": os.path.join(ROOT, ".smoke", "data_mnist", "mnist"),
        "eurosat": os.path.join(ROOT, ".smoke", "data_eurosat", "eurosat")}
LOGGED_ZS = {"mnist": 57.72, "eurosat": 26.11}
SEEDS, SHOTS, CLIENTS, ALPHA, SCALE = 20, 8, 10, 0.1, 100.0
# (setting, noise type, rate, mode, noisy client fraction), as the arms' flags
SETTINGS = [("D sym", "sym", 0.4, "uniform", 0.3), ("D pair", "pair", 0.4, "uniform", 0.3),
            ("D het", "sym", 0.8, "hetero", 0.5), ("D clean", "sym", 0.0, "uniform", 0.0),
            ("N sym50", "sym", 0.5, "uniform", 1.0), ("N pair50", "pair", 0.5, "uniform", 1.0),
            ("N sym75", "sym", 0.75, "uniform", 1.0), ("N pair75", "pair", 0.75, "uniform", 1.0)]
MAIN = ["D sym", "D pair", "D het", "N sym50", "N pair50"]          # the stage 0 settings
REFS = ["z", "proto_fed", "proto_local", "mix", "proto_loo"]


def features(ds):
    path = os.path.join(OUT_DIR, f"feats_{ds}.npz")
    if os.path.exists(path):
        d = dict(np.load(path, allow_pickle=True))
        for s in ("train", "test"):
            d[f"{s}_f"] = d[f"{s}_f"].reshape(len(d[f"{s}_y"]), -1)   # encode_image gives (1, 1, D)
        return d
    model, pre = clip.load(os.path.expanduser("~/.cache/clip/RN50.pt"), device="cpu")
    model.eval()
    classes = sorted(os.listdir(os.path.join(DATA[ds], "train")))
    names = [NEW_CNAMES_EURO.get(c, c) if ds == "eurosat" else c for c in classes]
    out = {"classes": np.array(names)}
    with torch.no_grad():
        tmpl = CUSTOM_TEMPLATES[ds]
        tok = clip.tokenize([tmpl.format(n.replace("_", " ")) for n in names])
        t = model.encode_text(tok).float()
        out["text"] = (t / t.norm(dim=-1, keepdim=True)).numpy()
        for split in ("train", "test"):
            feats, ys = [], []
            for k, c in enumerate(classes):
                d = os.path.join(DATA[ds], split, c)
                for f in sorted(os.listdir(d)):
                    x = pre(Image.open(os.path.join(d, f))).unsqueeze(0)
                    v = model.encode_image(x)
                    v = (v[0] if isinstance(v, tuple) else v).float()
                    feats.append((v / v.norm(dim=-1, keepdim=True)).numpy()[0])
                    ys.append(k)
            out[f"{split}_f"], out[f"{split}_y"] = np.stack(feats), np.array(ys)
    np.savez(path, **out)
    return features(ds)


def softmax(x):
    x = x - x.max(axis=1, keepdims=True)
    e = np.exp(x)
    return e / e.sum(axis=1, keepdims=True)


def federation(F, Y, K, setting, rng):
    """Few-shot draw, Dirichlet split and label noise; returns features, true, given, client ids."""
    _, ntype, rate, mode, frac = setting
    idx = np.concatenate([rng.choice(np.where(Y == k)[0], SHOTS, replace=False) for k in range(K)])
    true = Y[idx]
    cid = np.empty(len(idx), dtype=int)
    for k in range(K):
        pos = np.where(true == k)[0]
        p = rng.dirichlet(np.full(CLIENTS, ALPHA))
        cid[pos] = rng.choice(CLIENTS, size=len(pos), p=p)
    given = true.copy()
    num_noisy = int(round(frac * CLIENTS))
    noisy = sorted(rng.permutation(CLIENTS)[:num_noisy].tolist())
    for j, c in enumerate(noisy):
        r = rate * (j + 1) / num_noisy if mode == "hetero" else rate
        pos = np.where(cid == c)[0]
        kf = int(round(r * len(pos)))
        for i in pos[rng.permutation(len(pos))[:kf]]:
            if ntype == "pair":
                given[i] = (true[i] + 1) % K
            else:
                given[i] = rng.choice([c2 for c2 in range(K) if c2 != true[i]])
    return F[idx], true, given, cid


def referees(f, given, cid, text, K):
    out = {"z": softmax(SCALE * f @ text.T)}
    S = np.zeros((K, f.shape[1]))
    for k in range(K):
        if (given == k).any():
            S[k] = f[given == k].sum(axis=0)
    norm = lambda m: m / np.maximum(np.linalg.norm(m, axis=-1, keepdims=True), 1e-12)
    present = np.array([(given == k).any() for k in range(K)])
    logits = SCALE * f @ norm(S).T
    logits[:, ~present] = -np.inf
    out["proto_fed"] = softmax(logits)
    loo = np.empty_like(logits)
    for i in range(len(f)):
        Si = S.copy()
        Si[given[i]] -= f[i]
        li = SCALE * f[i] @ norm(Si).T
        li[~present] = -np.inf
        if not Si[given[i]].any():
            li[given[i]] = -np.inf
        loo[i] = li
    out["proto_loo"] = softmax(np.where(np.isfinite(loo).any(axis=1, keepdims=True), loo, 0.0))
    loc = np.empty_like(logits)
    for c in np.unique(cid):
        m = cid == c
        Sc = np.zeros_like(S)
        for k in range(K):
            if (given[m] == k).any():
                Sc[k] = f[m][given[m] == k].sum(axis=0)
        lc = SCALE * f[m] @ norm(Sc).T
        lc[:, ~Sc.any(axis=1)] = -np.inf
        loc[m] = lc
    out["proto_local"] = softmax(loc)
    out["mix"] = 0.5 * (out["z"] + out["proto_fed"])
    return out


def auroc(score_wrong, wrong):
    """P(score of a wrong label > score of a correct one), ties half."""
    s, w = np.asarray(score_wrong, float), np.asarray(wrong, bool)
    if w.all() or not w.any():
        return float("nan")
    order = np.argsort(s, kind="mergesort")
    ranks = np.empty(len(s))
    sv = s[order]
    i = 0
    while i < len(s):
        j = i
        while j + 1 < len(s) and sv[j + 1] == sv[i]:
            j += 1
        ranks[order[i:j + 1]] = (i + j) / 2 + 1
        i = j + 1
    nw = w.sum()
    return float((ranks[w].sum() - nw * (nw + 1) / 2) / (nw * (len(s) - nw)))


def stage0_auroc(ds, tag):
    data, _ = load_run(ds, tag)
    sc, wr = [], []
    for _, clients in data.items():
        for _, lp, y, t in clients:
            sc.append(-np.exp(lp[np.arange(len(y)), y]))
            wr.append(y != t)
    return np.concatenate(sc), np.concatenate(wr)


def main():
    md = ["# Screen 2: image-side referee from class prototypes (MNIST / EuroSAT, local images)", "",
          "Generated by `tools/screen_proto.py`; rules in `screen_plan.md` (written before the run). "
          f"{SEEDS} seeds per setting, {SHOTS} shots per class, {CLIENTS} clients, Dirichlet {ALPHA}. "
          "AUROC = image level, wrong vs correct labels, on the given label's probability.", ""]
    verdict = {}
    for ds in ("mnist", "eurosat"):
        d = features(ds)
        K = len(d["classes"])
        zs_acc = 100 * float((softmax(SCALE * d["test_f"] @ d["text"].T).argmax(1) == d["test_y"]).mean())
        sane = abs(zs_acc - LOGGED_ZS[ds]) <= 10
        md += [f"## {ds}", "", f"Sanity: zero-shot accuracy on the local test images {zs_acc:.1f}% "
               f"(logged {LOGGED_ZS[ds]}%): {'ok' if sane else 'NOT representative, screen void'}", "",
               "| setting | " + " | ".join(REFS) + " | CLEAR e (stage 0) |", "|---|" + "---|" * (len(REFS) + 1)]
        pooled = {r: ([], []) for r in REFS}
        cl = {r: np.zeros(4) for r in REFS}
        for st_ in SETTINGS:
            name = st_[0]
            acc = {r: ([], []) for r in REFS}
            for s in range(SEEDS):
                rng = np.random.default_rng(1000 * s + SETTINGS.index(st_))
                f, true, given, cid = federation(d["train_f"], d["train_y"], K, st_, rng)
                refs = referees(f, given, cid, d["text"], K)
                wrong = given != true
                for r in REFS:
                    py = refs[r][np.arange(len(given)), given]
                    acc[r][0].append(-py)
                    acc[r][1].append(wrong)
                    if name in MAIN:
                        pooled[r][0].append(-py)
                        pooled[r][1].append(wrong)
                        clients = [(0, np.log(np.maximum(refs[r], 1e-30)), given, true)]
                        m = cl_marks(clients, K)
                        cl[r] += [(m & wrong).sum(), wrong.sum(), (m & ~wrong).sum(), (~wrong).sum()]
            row = [auroc(np.concatenate(acc[r][0]), np.concatenate(acc[r][1])) for r in REFS]
            ref = "—"
            tag = {"D sym": "D_sym_fp", "D pair": "D_pair_fp", "D het": "D_het_fp",
                   "N sym50": "N_sym50_fp", "N pair50": "N_pair50_fp"}.get(name)
            if tag:
                ref = f"{auroc(*stage0_auroc(ds, tag)):.3f}"
            md.append(f"| {name} | " + " | ".join("—" if np.isnan(v) else f"{v:.3f}" for v in row) + f" | {ref} |")
        pa = {r: auroc(np.concatenate(pooled[r][0]), np.concatenate(pooled[r][1])) for r in REFS}
        s0 = [stage0_auroc(ds, t) for t in ("D_sym_fp", "D_pair_fp", "D_het_fp", "N_sym50_fp", "N_pair50_fp")]
        a0 = auroc(np.concatenate([a for a, _ in s0]), np.concatenate([b for _, b in s0]))
        md.append(f"| **pooled (stage 0 settings)** | " + " | ".join(f"**{pa[r]:.3f}**" for r in REFS) + f" | **{a0:.3f}** |")
        md += ["", "CL marks on each referee (exploratory; stage 0 settings pooled):", "",
               "| referee | recall | false marks |", "|---|---|---|"]
        for r in REFS:
            md.append(f"| {r} | {100 * cl[r][0] / cl[r][1]:.1f}% | {100 * cl[r][2] / cl[r][3]:.1f}% |")
        ok = sane and pa["proto_fed"] >= a0 + 0.05 and pa["proto_fed"] >= pa["z"] + 0.05
        verdict[ds] = (ok, sane, pa["proto_fed"], a0, pa["z"])
        md.append("")
    m, e = verdict["mnist"], verdict["eurosat"]
    md += ["## Rules", "",
           f"- P1 MNIST: proto_fed {m[2]:.3f} vs CLEAR e {m[3]:.3f} and z {m[4]:.3f} (need +0.05 over both)"
           f"{'' if m[1] else ' — sanity failed'}: {'pass' if m[0] else 'FAIL'}",
           f"- P2 EuroSAT (confirmation): proto_fed {e[2]:.3f} vs CLEAR e {e[3]:.3f} and z {e[4]:.3f}"
           f"{'' if e[1] else ' — sanity failed'}: {'pass' if e[0] else 'FAIL'}", ""]
    open(os.path.join(OUT_DIR, "screen_proto.md"), "w", encoding="utf-8").write("\n".join(md))
    print("\n".join(md))


if __name__ == "__main__":
    main()
