"""Per-client noise readings of every method that logs one: can it tell noisy clients from clean
ones (AUROC), and how far is its implied share of mislabelled images from the true share.

Nothing here is used by the methods for these purposes except where noted; the implied shares are
read off what each method already logs:
- CLEAR-FPL: score s (flags when s > 0.05); share = suspects / n (0 when not flagged; capped at 60%)
- DBR-FPL: mean top-1 disagreement d; share = rho (its excess drop rate)
- NLPrompt (orig / hist): share = images sent to MAE / n (also its ranking score)
- FedCorr: accumulated LID (ranking); share = mu-hat of its noise GMM (0 outside the noisy set),
  in pre-processing (rounds 0-4) only, against the labels at that time (it relabels for good)

Clean-vs-noisy ranking: the 4 settings that hold both kinds of client (S sym / pair / inst / het).
Share error: all 11 settings, mean over clients, seeds and settings.

Usage: python tools/analyze_client_estimates.py  (writes results/side-research/client_estimates.md)
"""
import glob
import json
import os
import statistics as st

from analyze_baselines import SR

DATASETS = [("oxford_pets", "Pets"), ("dtd", "DTD"), ("caltech101", "Caltech101")]
MIXED = ["sym", "pair", "inst", "het"]
ALL = [("S", s) for s in MIXED + ["clean"]] + [("N", f"{n}{r}") for n in ("sym", "pair")
                                                for r in ("25", "50", "75")]
METHODS = {  # name -> (gate D tag, N tag, record key)
    "CLEAR-FPL": ("S_{}_full", "N_{}_clear", "sure"),
    "DBR-FPL": ("D_{}_dbr", "N_{}_dbr", "filter"),
    "NLPrompt (gốc)": ("S_{}_nlp", "N_{}_nlp", "nlp"),
    "NLPrompt (chỉnh)": ("S_{}_nlph", "N_{}_nlph", "nlp"),
    "FedCorr": ("S_{}_corr", "N_{}_corr", "fedcorr"),
}
_INDEX = None


def files(tag):
    """noise_seed_*.json of a run tag, one per seed (the first found)."""
    global _INDEX
    if _INDEX is None:
        _INDEX = {}
        for f in glob.glob(os.path.join(SR, "**", "noise_seed_*.json"), recursive=True):
            parts = f.replace("\\", "/").split("/")
            run = parts[len(parts) - 2 - parts[::-1].index("results")]   # the dir above the last "results"
            _INDEX.setdefault(run, {}).setdefault(os.path.basename(f), f)
    return list(_INDEX.get(tag, {}).values())


def auroc(pos, neg):
    if not pos or not neg:
        return None
    return sum((p > q) + 0.5 * (p == q) for p in pos for q in neg) / (len(pos) * len(neg))


def readings(rec, key):
    """[(round label, {client: (score, share, true share now, true share at the start)})] for the
    first and last reading; the two true shares differ only for FedCorr, which relabels for good."""
    true0 = {str(c["id"]): c["realized_rate"] for c in rec["noise"]["clients"]}
    if key == "fedcorr":
        st1 = [r for r in rec["fedcorr"] if r["stage"] == 1]
        out, before = [], dict(true0)
        for r in st1:
            out.append({str(i): (r["lid_acc"][i], r["mu"][i] if i in r["noisy_set"] else 0.0,
                                 before[str(i)], true0[str(i)]) for i in range(len(r["mu"]))})
            before = {str(i): v for i, v in enumerate(r["noise_after"])}
        return [("first", out[0]), ("last", out[-1])]
    rs = rec[key]
    res = []
    for lab, r in (("first", rs[0]), ("last", rs[-1])):
        d = {}
        for c, v in r["clients"].items():
            n = v.get("n") or 0
            if not n:
                continue
            if key == "sure":
                d[c] = (v["score"], v["suspects"] / n if v["flag"] else 0.0, true0[c], true0[c])
            elif key == "filter":
                d[c] = (v["mean_dis"], v["rho"], true0[c], true0[c])
            else:
                share = 1 - v["clean_split"] / n
                d[c] = (share, share, true0[c], true0[c])
        res.append((lab, d))
    return res


def main():
    rows_a, rows_e, used = [], [], []
    for name, (tg, tn, key) in METHODS.items():
        cells_a, cells_e = {}, {}
        for ds, dn in DATASETS:
            au = {"first": [], "last": []}
            er = {"first": [], "last": []}
            nruns = nseeds = 0
            for kind, sc in ALL:
                tag = f"{ds}_" + (tg if kind == "S" else tn).format(sc)
                fs = files(tag)
                if fs:
                    nruns += 1
                    nseeds += len(fs)
                for f in fs:
                    rec = json.load(open(f, encoding="utf-8"))
                    if not rec.get(key):
                        continue
                    for lab, d in readings(rec, key):
                        er[lab] += [abs(s - t) for _, s, t, _ in d.values()]
                        if kind == "S" and sc in MIXED:
                            a = auroc([x for x, _, _, t in d.values() if t > 0],
                                      [x for x, _, _, t in d.values() if t == 0])
                            if a is not None:
                                au[lab].append(a)
            used.append(f"{name} {dn}: {nruns}/11 settings, {nseeds} seed files")
            for lab in ("first", "last"):
                cells_a[(dn, lab)] = f"{st.fmean(au[lab]):.2f}" if au[lab] else "—"
                cells_e[(dn, lab)] = f"{100 * st.fmean(er[lab]):.0f}" if er[lab] else "—"
        for lab, txt in (("first", "vòng đầu"), ("last", "vòng cuối")):
            if name == "FedCorr":
                txt = "vòng 0" if lab == "first" else "vòng 4 (hết tiền xử lý)"
            rows_a.append(f"| {name} | {txt} | " + " | ".join(cells_a[(dn, lab)] for _, dn in DATASETS) + " |")
            rows_e.append(f"| {name} | {txt} | " + " | ".join(cells_e[(dn, lab)] for _, dn in DATASETS) + " |")
    md = ["# Mỗi phương pháp đọc được gì về từng client", "",
          "Sinh bởi `tools/analyze_client_estimates.py`. Cách đọc từng số: xem docstring của script.", "",
          "## Phân biệt client nhiễu / client sạch (AUROC; 4 kịch bản có cả hai loại client, 5 seed)", "",
          "| Phương pháp | Thời điểm | Pets | DTD | Caltech101 |", "|---|---|---|---|---|", *rows_a, "",
          "## Sai số ước lượng tỉ lệ ảnh sai nhãn của client (điểm phần trăm; 11 kịch bản, 5 seed)", "",
          "| Phương pháp | Thời điểm | Pets | DTD | Caltech101 |", "|---|---|---|---|---|", *rows_e, "",
          "## Run đã dùng", "", *[f"- {u}" for u in used], ""]
    text = "\n".join(md)
    open(os.path.join(SR, "client_estimates.md"), "w", encoding="utf-8").write(text)
    print(text)


if __name__ == "__main__":
    main()
