"""16-shot table for the paper: per dataset and scenario, the average accuracy of PromptFL and FedCLEAR
at 8 and 16 shots (mean over 5 seeds of the per-seed average over the scenario's settings, last-10 rule),
plus the per-setting facts quoted in the text (wins, paired t-tests at 16 shots, 75% pairwise noise).

Usage: python tools/make_s16_table.py            prints the LaTeX table and the facts
"""
import os
import statistics as st
import sys

sys.path.insert(0, os.path.dirname(__file__))
import analyze_baselines as ab
import analyze_s16 as a16
import make_paper_tables as mp

NAMES = ["Pets", "Caltech101", "DTD", "MNIST", "EuroSAT"]
BS = chr(92)


def avg(name, method, shots, rows):
    f = a16.s16 if shots == 16 else a16.s8
    v = [f(name, method, k, s) for k, s in rows]
    assert all(x and len(x) == 5 for x in v), (name, method, shots)
    return st.fmean(st.fmean(x[i] for x in v) for i in range(5))


def table():
    L = [BS + "begin{table}[H]", BS + "centering",
         BS + "caption{Average accuracy (" + BS + "%) of PromptFL and FedCLEAR with 8 and 16 labelled images per "
         "class, per scenario and dataset (mean of the last 10 rounds over 5 seeds, averaged over the five "
         "settings of the first scenario and the six of the second). The 16-shot runs give EuroSAT its "
         "standard class names; its 8-shot runs used the folder names. Bold: the more accurate method at 16 shots.}",
         BS + "label{tab:shots}", BS + "setlength{" + BS + "tabcolsep}{4pt}",
         BS + "begin{tabular}{lcccccccc}", BS + "toprule[1.2pt]",
         " & " + BS + "multicolumn{4}{c}{" + BS + "textbf{Scenario 1}} & " + BS + "multicolumn{4}{c}{" + BS
         + "textbf{Scenario 2}} " + BS * 2,
         BS + "cmidrule(lr){2-5}" + BS + "cmidrule(lr){6-9}",
         " & " + " & ".join([BS + "multicolumn{2}{c}{PromptFL} & " + BS + "multicolumn{2}{c}{FedCLEAR}"] * 2)
         + " " + BS * 2,
         BS + "cmidrule(lr){2-3}" + BS + "cmidrule(lr){4-5}" + BS + "cmidrule(lr){6-7}" + BS + "cmidrule(lr){8-9}",
         "Dataset & " + " & ".join(["8 & 16"] * 4) + " " + BS * 2, BS + "midrule"]
    for name in NAMES:
        cells = []
        for rows in (mp.S1, mp.S2):
            v = {(m, k): avg(name, m, k, rows) for m in ("PromptFL", "FedCLEAR") for k in (8, 16)}
            best16 = max(v[("PromptFL", 16)], v[("FedCLEAR", 16)])
            for m in ("PromptFL", "FedCLEAR"):
                for k in (8, 16):
                    t = f"{v[(m, k)]:.1f}"
                    if k == 16 and round(v[(m, k)], 1) == round(best16, 1):
                        t = BS + "textbf{" + t + "}"
                    cells.append(t)
        L.append(f"{name} & " + " & ".join(cells) + " " + BS * 2)
    L += [BS + "bottomrule[1.2pt]", BS + "end{tabular}", BS + "end{table}"]
    return "\n".join(L)


def facts():
    wins, sig_up, sig_down = {}, [], []
    for name in NAMES:
        w = 0
        for k, s in mp.S1 + mp.S2:
            c, p = a16.s16(name, "FedCLEAR", k, s), a16.s16(name, "PromptFL", k, s)
            d, pv = ab.paired(c, p)[:2]
            w += d > 0
            if pv < 0.05:
                (sig_up if d > 0 else sig_down).append((name, k, s, round(d, 2), round(pv, 3)))
        wins[name] = w
    print("wins at 16 shots (of 11):", wins, "total", sum(wins.values()))
    print("significantly better (p<0.05):", len(sig_up))
    print("significantly worse:", sig_down)
    for name in NAMES:
        for m in ("PromptFL", "FedCLEAR"):
            a, b = a16.s8(name, m, "N", "pair75"), a16.s16(name, m, "N", "pair75")
            print(f"{name} {m} N pair75: 8 {st.fmean(a):.2f} 16 {st.fmean(b):.2f}")


if __name__ == "__main__":
    print(table())
    facts()
