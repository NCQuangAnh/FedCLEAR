"""Framework figure of the improved FedCLEAR (CLEAR-FPL + referee-strength gate, capped noise-aware
temperature and suspect floor; arm `gatef`, results/side-research/calrepair/gatef_plan.md).

Drawn at the LNCS text width (12.2 cm), so the font sizes are the printed ones. Colours match
tools/plot_paper_fig.py: FedCLEAR's vermillion marks the steps used only once the gate is open.

Usage: python tools/plot_framework.py   -> report/clear_v2_framework.pdf and .png
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle

OUT = os.path.join(os.path.dirname(__file__), "..", "report")
plt.rcParams.update({
    "font.family": "serif", "font.serif": ["Times New Roman", "STIXGeneral"], "mathtext.fontset": "stix",
    "pdf.fonttype": 42, "ps.fonttype": 42, "savefig.dpi": 400,
})

W, H = 4.8, 3.14                     # inches: LNCS text width
INK, GREY = "#222222", "#6b6b6b"
CAL, CAL_FILL = "#D55E00", "#fbe6d8"  # FedCLEAR's colour in the result figures
SRV, SRV_FILL = "#0072B2", "#edf4fa"
TITLE, BODY, SMALL = 6.6, 6.0, 5.4
LINE = 0.098                         # inches between body lines

fig = plt.figure(figsize=(W, H))
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, W)
ax.set_ylim(0, H)
ax.set_aspect("equal")
ax.axis("off")


def rbox(x, y, w, h, fc, ec, lw=0.6, ls="-", r=0.035, z=2):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={r}",
                                fc=fc, ec=ec, lw=lw, ls=ls, zorder=z))


def block(x, y, w, h, title, lines, cal=False, sub=None, top_pad=None):
    """A step: bold title, optional italic subtitle, then body lines, centred as one stack.
    A body line is a string or (string, height factor) for lines with fractions or hats."""
    rbox(x, y, w, h, CAL_FILL if cal else "white", CAL if cal else INK, lw=0.75 if cal else 0.6, z=3)
    n_title = title.count("\n") + 1
    rows = [(title, TITLE, "bold", "normal", LINE * (1.1 * n_title))]
    if sub:
        rows.append((sub, SMALL, "normal", "italic", LINE * 0.95))
    for t in lines:
        t, f = (t, 1.0) if isinstance(t, str) else t
        rows.append((t, BODY, "normal", "normal", LINE * f))
    total = sum(r[4] for r in rows)
    top = y + h / 2 + total / 2 if top_pad is None else y + h - top_pad
    cx = x + w / 2
    for t, size, weight, style, hh in rows:
        ax.text(cx, top - hh / 2, t, ha="center", va="center", fontsize=size, fontweight=weight,
                fontstyle=style, color=CAL if (cal and weight == "bold") else INK, zorder=4,
                linespacing=1.15 if weight == "bold" else 1.0)
        top -= hh


def arrow(pts, color=INK, lw=0.7, ls="-", z=5):
    """Poly-line through pts, arrow head at the last point."""
    for a, b in zip(pts[:-2], pts[1:-1]):
        ax.plot([a[0], b[0]], [a[1], b[1]], color=color, lw=lw, ls=ls, solid_capstyle="butt", zorder=z)
    ax.add_patch(FancyArrowPatch(pts[-2], pts[-1], arrowstyle="-|>", mutation_scale=5.5, color=color,
                                 lw=lw, ls=ls, shrinkA=0, shrinkB=0, zorder=z))


def label(x, y, t, ha="left", color=INK, size=BODY, style="normal"):
    ax.text(x, y, t, ha=ha, va="center", fontsize=size, color=color, fontstyle=style, zorder=6,
            linespacing=1.15)


# ---------------------------------------------------------------- columns of the client pipeline
C = {}
x = 0.10
for name, w, gap in [("data", 0.40, 0.09), ("ref", 0.84, 0.09), ("flag", 0.70, 0.15), ("sus", 0.80, 0.13),
                     ("fix", 0.66, 0.09), ("train", 0.58, 0.0)]:
    C[name] = (x, x + w)
    x += w + gap
mid = {k: (a + b) / 2 for k, (a, b) in C.items()}

# ---------------------------------------------------------------- panels
CY0, CY1 = 0.26, 1.98          # client panel
SY0, SY1 = 2.40, 3.06          # server panel
for d in (0.06, 0.03):         # the other K - 1 clients behind client k
    rbox(0.04 + d, CY0 + d, 4.65, CY1 - CY0, "white", "#9a9a9a", lw=0.5, r=0.06, z=0)
rbox(0.04, CY0, 4.65, CY1 - CY0, "#f6f6f6", GREY, lw=0.7, r=0.06, z=1)
rbox(0.04, SY0, 4.65 + 0.06, SY1 - SY0, SRV_FILL, SRV, lw=0.7, r=0.06, z=1)
ax.text(mid["data"], (SY0 + SY1) / 2, "Server", ha="center", va="center", fontsize=7.6, fontweight="bold",
        color=SRV, zorder=4)
ax.text(mid["data"], 1.66, "Client $k$", ha="center", va="center", fontsize=7.6, fontweight="bold",
        color=INK, zorder=4)
ax.text(mid["data"], 1.50, "($K$ clients,\nin parallel)", ha="center", va="center", fontsize=SMALL,
        color=GREY, zorder=4, linespacing=1.1)

# ---------------------------------------------------------------- client: every-round pipeline (bottom row)
MY0, MY1 = 0.36, 1.04
MM = (MY0 + MY1) / 2
block(C["data"][0], MY0, C["data"][1] - C["data"][0], MY1 - MY0, "Data", [], top_pad=0.035)
# small image stack inside the data block
for i, dx in enumerate((0.0, 0.035, 0.07)):
    ax.add_patch(Rectangle((C["data"][0] + 0.085 + dx, MM - 0.085 + 0.03 * i), 0.13, 0.13, fc="#dfe9f3",
                           ec=GREY, lw=0.4, zorder=4))
label(mid["data"], MY0 + 0.09, r"$(\mathbf{x}_i,\tilde{y}_i)$", ha="center", size=BODY)
block(C["ref"][0], MY0, C["ref"][1] - C["ref"][0], MY1 - MY0, "Reference",
      [(r"$\mathbf{P}_i=\frac{1}{2}\,(p_{\mathbf{v}^r}+p_{\mathrm{zs}})$", 1.45), "global prompt $\\mathbf{v}^r$",
       "+ zero-shot CLIP"])
block(C["flag"][0], MY0, C["flag"][1] - C["flag"][0], MY1 - MY0, "Client test",
      [(r"$S_k=\frac{1}{n_k}\,\Sigma_i\, s_i$", 1.45), r"flagged if $S_k>\tau$", r"else keep $\mathcal{D}_k$"])
block(C["sus"][0], MY0, C["sus"][1] - C["sus"][0], MY1 - MY0, "Suspects", [
      (r"$P_{i,\tilde{y}_i}<\delta$", 1.15), r"at most $\lfloor\gamma\, n_k\rfloor$"], sub="gate closed / $r\\leq R$")
block(C["fix"][0], MY0, C["fix"][1] - C["fix"][0], MY1 - MY0, "Correction",
      [(r"relabel to $\hat{y}_i$", 1.1), r"if $\mathrm{max}_c\, P_{i,c}\geq\kappa$,", "else set aside"])
block(C["train"][0], MY0, C["train"][1] - C["train"][0], MY1 - MY0, "Local\ntraining",
      [(r"CoOp on $\hat{\mathcal{D}}^r_k$", 1.2), r"$\rightarrow\mathbf{v}^r_k$"])
for a, b in [("data", "ref"), ("ref", "flag"), ("flag", "sus"), ("sus", "fix"), ("fix", "train")]:
    arrow([(C[a][1], MM), (C[b][0], MM)])

# ---------------------------------------------------------------- client: calibrated repair (top row)
KY0, KY1 = 1.20, 1.84
rbox(C["ref"][0] - 0.045, KY0 - 0.055, C["sus"][1] - C["ref"][0] + 0.09, KY1 - KY0 + 0.11, "none", CAL,
     lw=0.5, ls=(0, (3, 2)), r=0.05, z=2)
block(C["ref"][0], KY0, C["flag"][1] - C["ref"][0], KY1 - KY0, "Noise-aware calibration", [
      (r"$\tilde{y}_i\sim(1-\varepsilon_k)\,\mathbf{P}^T_i+\varepsilon_k/C,\quad\mathbf{P}^T_i\propto\mathbf{P}_i^{1/T}$", 1.3),
      (r"$\ell_k(t)=\mathrm{max}_{\varepsilon}\,\log L_k(t,\varepsilon)$ for 25 values of $t$", 1.2),
      (r"$\varepsilon^0_k$: $\varepsilon_k$ frozen at the first calibrated round", 1.15)], cal=True)
block(C["sus"][0], KY0, C["sus"][1] - C["sus"][0], KY1 - KY0, "Suspects", [
      (r"$\pi_i<\alpha$: $\tilde{y}_i$ outside", 1.1), (r"the 95% set of $\mathbf{P}^T_i$", 1.15),
      (r"at least $\varepsilon^0_k\, n_k$", 1.15)], cal=True, sub="gate open, $r>R$")
# Reference -> calibration, flag -> calibrated suspects, calibration -> calibrated suspects -> correction
arrow([(mid["ref"] - 0.12, MY1), (mid["ref"] - 0.12, KY0)], color=CAL)
label(mid["ref"] - 0.09, (MY1 + KY0) / 2 + 0.005, r"$\mathbf{P}_i$", color=CAL, size=SMALL)
xs = (C["flag"][1] + C["sus"][0]) / 2
arrow([(C["flag"][1], MM + 0.17), (xs, MM + 0.17), (xs, KY0 + 0.16), (C["sus"][0], KY0 + 0.16)], color=CAL)
arrow([(C["flag"][1], KY1 - 0.16), (C["sus"][0], KY1 - 0.16)], color=CAL)
xf = C["fix"][0] + 0.14
yf = KY0 + 0.12
arrow([(C["sus"][1], yf), (xf, yf), (xf, MY1)], color=CAL)

# ---------------------------------------------------------------- server
BY0, BY1 = SY0 + 0.08, SY1 - 0.08
block(C["ref"][0], BY0, C["flag"][1] - C["ref"][0], BY1 - BY0, "Temperature calibration", [
      (r"$T=\min\{\,\mathrm{arg\,max}_t\;\Sigma_k\,\ell_k(t),\ 1\,\}$", 1.3)], cal=True,
      sub="every round once the gate is open")
GX0, GX1 = C["sus"][0], 3.80
block(GX0, BY0, GX1 - GX0, BY1 - BY0, "Referee-strength gate", [
      (r"open if LB$_{95}$(relabelled / suspects) $\geq g$", 1.2)], sub="decided once, after round $R$")
AX0 = 3.89
block(AX0, BY0, C["train"][1] - AX0, BY1 - BY0, "Aggregation",
      [(r"$\mathbf{v}^{r+1}=\Sigma_k\, w_k\,\mathbf{v}^r_k$", 1.25), (r"$w_k=\hat{n}^r_k/\hat{n}^r$", 1.2)])

# ---------------------------------------------------------------- communication
xT, xL = mid["ref"] - 0.12, mid["flag"] + 0.05
arrow([(xT, BY0), (xT, KY1)], color=CAL, lw=0.8)
label(xT - 0.04, (CY1 + SY0) / 2, "$T$", ha="right", color=CAL)
arrow([(xL, KY1), (xL, BY0)], color=CAL, lw=0.8)
label(xL + 0.04, (CY1 + SY0) / 2, r"$\ell_k(t)$, 25 values", color=CAL)
xg = mid["sus"]
arrow([(xg, BY0), (xg, KY1)], lw=0.8)
label(xg + 0.04, (CY1 + SY0) / 2, "open / closed")
xc = 3.74
arrow([(xc, MY1), (xc, BY0)], lw=0.8)
label(xc - 0.04, 1.66, "suspects,\nrelabelled\n($r\\leq R$)", ha="right", size=SMALL)
xv, xu = 4.18, 4.47
arrow([(xv, BY0), (xv, MY1)], lw=0.8)
label(xv - 0.04, 1.50, r"$\mathbf{v}^{r}$", ha="right")
arrow([(xu, MY1), (xu, BY0)], lw=0.8)
ax.text(xu + 0.04, 1.58, r"$\mathbf{v}^r_k$", ha="left", va="center", fontsize=BODY, zorder=6)
ax.text(xu + 0.04, 1.42, r"$\hat{n}^r_k$", ha="left", va="center", fontsize=BODY, zorder=6)

# ---------------------------------------------------------------- legend
LY = 0.11
lx = 0.55
rbox(lx, LY - 0.045, 0.16, 0.09, "white", INK, lw=0.6, r=0.015)
label(lx + 0.21, LY, "used in every round")
lx = 1.75
rbox(lx, LY - 0.045, 0.16, 0.09, CAL_FILL, CAL, lw=0.75, r=0.015)
label(lx + 0.21, LY, "used only once the gate is open (rounds $r>R$)")

os.makedirs(OUT, exist_ok=True)
base = os.path.join(OUT, "clear_v2_framework")
fig.savefig(base + ".pdf", bbox_inches="tight", pad_inches=0.02)
fig.savefig(base + ".png", bbox_inches="tight", pad_inches=0.02)
print(os.path.abspath(base) + ".pdf / .png")
