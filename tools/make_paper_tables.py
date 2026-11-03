"""Rebuild the four result tables of samplepaper.tex in the layout of FedRG's Table 1 (CVPR 2026).

Rows are methods, grouped (ZS-CLIP reference / federated prompt learning / noisy-label methods /
FedCLEAR). Columns: the dataset on the first header row, the noise setting below it (scenario 2:
noise type, then rate). booktabs rules, no vertical lines. Cells are the mean over 5 seeds of the
last-10-round accuracy, one decimal (no +-sd: 12-21 value columns do not leave room for it). Among the trained methods the best
mean in each column is bold and the second underlined; ZS-CLIP is not ranked.

Usage: python tools/make_paper_tables.py <samplepaper.tex> [<clear arm>]
  Replaces the four tables in place (found by their tab:scenario* / tab:s*_* labels) and gives
  them unique labels: tab:s1_pc, tab:s2_pc, tab:s1_mde, tab:s2_mde. The FedCLEAR arm is `clear`
  (CLEAR-FPL v1) unless another is given (e.g. `gatef`; settings without that arm fall back to clear).
"""
import os
import re
import statistics as st
import sys

sys.path.insert(0, os.path.dirname(__file__))
import analyze_baselines as ab
from analyze_calrepair import tag

BS = chr(92)
DS = {"Pets": "oxford_pets", "Caltech101": "caltech101", "MNIST": "mnist", "DTD": "dtd", "EuroSAT": "eurosat"}
# 2026-11-03, the user chose the original NLPrompt (uniform class prior) on every dataset;
# the client-histogram variant ("NLPrompt (hist)") is no longer in the paper
NLP = {n: "NLPrompt" for n in ("Pets", "Caltech101", "DTD", "MNIST", "EuroSAT")}
ZS = {"Pets": 85.69, "Caltech101": 85.76, "MNIST": 57.72, "DTD": 41.78, "EuroSAT": 26.11}
S1 = [("S", "sym"), ("S", "pair"), ("S", "inst"), ("S", "het"), ("S", "clean")]
S2 = [("N", f"{t}{r}") for t in ("sym", "pair") for r in (25, 50, 75)]
# paper name, key in analyze_baselines (None: NLPrompt variant of the dataset), group
METHODS = [("PromptFL", "PromptFL", 1), ("FedProx", "FedProx", 1),
           ("FedCorr", "FedCorr", 2), ("NLPrompt", None, 2), ("FedRG", "FedRG", 2), ("FedCLEAR", "CLEAR", 3)]
DEC = 1             # decimals in the cells; ranks use the shown (rounded) values, so ties share a mark
LABELS = {(1, "pc"): "tab:s1_pc", (2, "pc"): "tab:s2_pc", (1, "mde"): "tab:s1_mde", (2, "mde"): "tab:s2_mde"}


def seeds(name, key, kind, setting, arm):
    if key == "CLEAR":
        v = ab.last10(tag(DS[name], kind, setting, arm)) if arm != "clear" else None
        v = v or ab.last10(tag(DS[name], kind, setting, "clear"))
    else:
        v = ab.last10(ab.tag(DS[name], key or NLP[name], kind, setting))
    assert v and len(v) == 5, (name, key, setting, v)
    return v


def column_means(name, scenario, arm):
    """per method: the mean of each setting and of the per-seed average over the settings"""
    rows = S1 if scenario == 1 else S2
    out = []
    for _, key, _ in METHODS:
        v = [seeds(name, key, k, s, arm) for k, s in rows]
        v.append([st.fmean(x[i] for x in v) for i in range(5)])
        out.append([round(st.fmean(c), DEC) for c in v])
    return out


def table(scenario, names, label, arm):
    """Columns: dataset on the first header row, noise setting below it (FedRG's Table 1 layout).
    Cells are means only: with 12-21 value columns the +-sd no longer fits the LNCS text width."""
    rows = S1 if scenario == 1 else S2
    per = len(rows) + 1                                    # settings + Avg. per dataset
    ncol = 1 + per * len(names)
    note = ("mean of the last 10 rounds over 5 seeds. Among the trained methods, the best result in each "
            "column is in bold and the second best is underlined; ZS-CLIP does not use training labels, is "
            "shown for reference and is not ranked.")
    span = lambda k: f"{2 + k * per}-{1 + (k + 1) * per}"
    head = [BS + "textbf{Dataset} & " + " & ".join(BS + f"multicolumn{{{per}}}{{c}}{{" + BS + f"textbf{{{n}}}}}" for n in names) + " " + BS * 2,
            "".join(BS + f"cmidrule(lr){{{span(k)}}}" for k in range(len(names)))]
    if scenario == 1:
        cap = "Test accuracy (" + BS + "%) in the first scenario (clean and noisy clients): " + note
        head.append("Method & " + " & ".join(["Sym. & Pair. & Inst. & Var. & Clean & Avg."] * len(names))
                    + " " + BS * 2)
    else:
        cap = ("Test accuracy (" + BS + "%) in the second scenario (all ten clients are noisy), by noise type "
               "and noise rate (" + BS + "%): " + note)
        sub = BS + "multicolumn{3}{c}{Sym.} & " + BS + "multicolumn{3}{c}{Pair.} & "
        head.append("Noise type & " + " & ".join([sub + BS + "multirow{2}{*}{Avg.}"] * len(names)) + " " + BS * 2)
        head.append("".join(BS + f"cmidrule(lr){{{2 + k * per + o}-{4 + k * per + o}}}"
                            for k in range(len(names)) for o in (0, 3)))
        head.append("Method / rate (" + BS + "%) & " + " & ".join(["25 & 50 & 75 & 25 & 50 & 75 &"] * len(names)) + " " + BS * 2)
    means = [column_means(n, scenario, arm) for n in names]          # dataset -> method -> column
    body = ["ZS-CLIP & " + " & ".join(f"{ZS[n]:.{DEC}f}" for n in names for _ in range(per)) + " " + BS * 2]
    group = 0
    for j, (lab, _, g) in enumerate(METHODS):
        if g != group:
            body.append(BS + "midrule")
            group = g
        cells = []
        for d in range(len(names)):
            for c in range(per):
                mu = means[d][j][c]
                # rank = 1 + number of methods strictly better; a tie for first leaves no second
                rank = 1 + sum(means[d][i][c] > mu for i in range(len(METHODS)))
                t = f"{mu:.{DEC}f}"
                if rank == 1:
                    t = BS + "textbf{" + t + "}"
                elif rank == 2:
                    t = BS + "underline{" + t + "}"
                cells.append(t)
        body.append((BS + "textbf{" + lab + "}" if g == 3 else lab) + " & " + " & ".join(cells) + " " + BS * 2)
    # portrait only: a sidewaystable went to a page of its own and the table after it was pushed to
    # the end of the paper. One decimal and narrow gaps keep the 18-21 value columns readable.
    env = "table"
    L = [BS + "begin{table}[H]", BS + "centering", BS + "caption{" + cap + "}", BS + "label{" + label + "}",
         BS + "setlength{" + BS + f"tabcolsep}}{{{2 if len(names) > 2 else 3}pt}}",
         BS + "resizebox{" + BS + "linewidth}{!}{%", BS + "begin{tabular}{l" + "c" * (ncol - 1) + "}",
         BS + "toprule[1.2pt]"] + head + [BS + "midrule"] + body + [BS + "bottomrule[1.2pt]", BS + "end{tabular}}",
         BS + f"end{{{env}}}"]
    return "\n".join(L)


def main():
    path = sys.argv[1]
    arm = sys.argv[2] if len(sys.argv) > 2 else "clear"
    tex = open(path, encoding="utf-8").read()
    spans = []
    tex = tex.replace(BS + "usepackage{rotating}\n", "")       # left by the landscape version
    for m in re.finditer(r"(?m)^" + re.escape(BS + "begin{") + "(sideways)?table}", tex):
        env = "sidewaystable" if m.group(1) else "table"
        e = tex.index(BS + f"end{{{env}}}", m.start()) + len(BS + f"end{{{env}}}")
        body = tex[m.start():e]
        lab = re.search(re.escape(BS + "label{") + r"([^}]*)\}", body).group(1)
        if lab.startswith("tab:scenario") or lab in LABELS.values():
            spans.append((m.start(), e, "pc" if "{Pets}" in body else "mde",
                          1 if ("Inst." in body) else 2))
    assert sorted((s, g) for _, _, g, s in spans) == sorted(LABELS), spans
    out, last = [], 0
    for s, e, g, sc in spans:
        names = ["Pets", "Caltech101"] if g == "pc" else ["MNIST", "DTD", "EuroSAT"]
        out += [tex[last:s], table(sc, names, LABELS[(sc, g)], arm)]
        last = e
    tex = "".join(out) + tex[last:]
    open(path, "w", encoding="utf-8", newline="\n").write(tex)
    print("ok", path)


if __name__ == "__main__":
    main()
