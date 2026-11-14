"""Figure 1 (revision): HWOA-GWA with scheduled spiral--hierarchical operator selection.
Vector output (PDF) + PNG preview. Values follow the implementation:
P = 25, B = 6250 -> T = (6250 - 25) // 25 = 249; t = 0..T-1; p_s(t) = 0.8 - 0.6 t / T."""
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

plt.rcParams.update({"font.family": "serif", "font.serif": ["STIXGeneral", "DejaVu Serif"],
                     "mathtext.fontset": "stix", "font.size": 8, "axes.linewidth": 0.6,
                     "pdf.fonttype": 42})
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#d9d8d4"
SPI, HIE = "#2a78d6", "#eb6834"          # spiral / hierarchical
FILL = "#f4f4f2"

T, p0, p1 = 249, 0.8, 0.2
t = np.arange(T); ps = p0 - (p0 - p1) * t / T

fig = plt.figure(figsize=(7.0, 5.9))
axA = fig.add_axes([0.075, 0.715, 0.90, 0.25])
axB = fig.add_axes([0.0, 0.0, 1.0, 0.615]); axB.set_xlim(0, 100); axB.set_ylim(0, 64); axB.axis("off")

# ---------------- panel (a) ----------------
axA.axvspan(0, T * (p0 - 0.5) / (p0 - p1), color=SPI, alpha=0.07, lw=0)
axA.axvspan(T * (p0 - 0.5) / (p0 - p1), T, color=HIE, alpha=0.07, lw=0)
axA.axhline(0.5, color=MUTED, lw=0.6, ls=(0, (3, 3)))
axA.plot(t, ps, color=INK, lw=1.4, solid_capstyle="round")
axA.plot([0], [p0], "o", color=INK, ms=4)
axA.plot([T - 1], [ps[-1]], "o", color=INK, ms=4)
axA.plot([T], [p1], "o", mfc="white", mec=INK, ms=4, mew=0.9)
axA.annotate(r"$p_s(0)=p_{\mathrm{init}}=0.8$", (0, p0), (10, 0.86), fontsize=7.5, color=INK)
axA.annotate(r"last executed iteration $t=T-1=248$: $p_s\approx0.2024$", (T - 1, ps[-1]),
             (122, 0.20), fontsize=7.5, color=INK,
             arrowprops=dict(arrowstyle="-", lw=0.5, color=MUTED))
axA.annotate(r"nominal $t=T=249$: $p_{\mathrm{end}}=0.2$ (not executed)", (T, p1), (122, 0.06),
             fontsize=7.5, color=MUTED, arrowprops=dict(arrowstyle="-", lw=0.5, color=MUTED))
axA.text(6, 0.33, "spiral operator more likely\n" r"($p_s>0.5$)", color=SPI, fontsize=7.5, va="center")
axA.text(130, 0.70, "hierarchical operator more likely\n" r"($p_s<0.5$)", color=HIE, fontsize=7.5, va="center")
axA.text(T + 3, 0.535, "0.5", color=MUTED, fontsize=7, va="center")
axA.text(196, 0.93, r"$p_s(t)=p_{\mathrm{init}}-(p_{\mathrm{init}}-p_{\mathrm{end}})\,t/T$",
         fontsize=8, ha="center", color=INK)
axA.set_xlim(0, T + 12); axA.set_ylim(0, 1.0)
axA.set_xticks([0, 50, 100, 150, 200, 249]); axA.set_yticks([0, 0.2, 0.5, 0.8, 1.0])
axA.set_xlabel(r"iteration $t$", color=INK); axA.set_ylabel(r"$p_s(t)$", color=INK)
for sp in ("top", "right"): axA.spines[sp].set_visible(False)
axA.tick_params(width=0.6, length=3, colors=INK)
axA.set_title(r"(a) Scheduled spiral-selection probability $p_s(t)$  (deterministic; no feedback from the search)",
              fontsize=8.5, loc="left", color=INK, pad=4)

# ---------------- panel (b) ----------------
axB.text(0.8, 62.6, "(b) One run of HWOA-GWA: steps 1–4 once, steps 5–9 repeated",
         fontsize=8.5, color=INK, va="top")

def box(x, y, w, h, title, lines, fc="white", ec=INK, lw=0.7, tsize=7.6, lsize=7.0):
    axB.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.8",
                                 fc=fc, ec=ec, lw=lw))
    axB.text(x + w / 2, y + h - 1.4, title, ha="center", va="top", fontsize=tsize,
             fontweight="bold", color=INK)
    for k, ln in enumerate(lines):
        axB.text(x + w / 2, y + h - 5.4 - 3.3 * k, ln, ha="center", va="top", fontsize=lsize, color=INK)

def arrow(p, q, **kw):
    axB.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=8, lw=0.8,
                                  color=kw.pop("color", INK), shrinkA=0, shrinkB=0, **kw))

# initialization (once)
axB.add_patch(FancyBboxPatch((0.8, 19), 16.5, 34, boxstyle="round,pad=0,rounding_size=0.8",
                             fc=FILL, ec=MUTED, lw=0.6, ls=(0, (3, 2))))
axB.text(9.05, 51.8, "Initialization (once)", ha="center", va="top", fontsize=7.6, fontweight="bold")
init = ["1. Sample $P$ deployments\nuniformly in $\\mathcal{F}$",
        "2. Evaluate $CR$\n($P$ evaluations)",
        "3. $\\mathrm{pbest}_i \\leftarrow \\mathbf{X}_i$",
        "4. Rank pbest:\n$\\alpha$, $\\beta$, $\\delta$"]
for k, s in enumerate(init):
    axB.text(9.05, 46.5 - 7.2 * k, s, ha="center", va="top", fontsize=7.0, linespacing=1.15)

# step 5: operator selection
x5, y5, w5, h5 = 20.5, 9, 27.5, 44
axB.add_patch(FancyBboxPatch((x5, y5), w5, h5, boxstyle="round,pad=0,rounding_size=0.8",
                             fc="white", ec=INK, lw=0.7))
axB.text(x5 + w5 / 2, y5 + h5 - 1.4, "5. Operator selection", ha="center", va="top",
         fontsize=7.6, fontweight="bold")
axB.text(x5 + w5 / 2, y5 + h5 - 5.2, "for each candidate $i$: draw $u\\sim U(0,1)$",
         ha="center", va="top", fontsize=7.0)
# spiral sub-box
sx, sy, sw, sh = x5 + 1.2, 28.6, w5 - 2.4, 12.6
axB.add_patch(FancyBboxPatch((sx, sy), sw, sh, boxstyle="round,pad=0,rounding_size=0.6",
                             fc="white", ec=SPI, lw=0.9))
axB.text(sx + 1, sy + sh - 1.2, "$u<p_s(t)$: spiral update", color=SPI, fontsize=7.0,
         fontweight="bold", va="top")
axB.text(sx + 1, sy + sh - 4.6, "around leader $\\alpha$\n(best-so-far, from pbest)", fontsize=6.6, va="top")
th = np.linspace(0, 4.2 * np.pi, 300); rr = 0.25 * np.exp(0.17 * th)
cx, cy = sx + sw - 5.2, sy + sh / 2 - 0.3
axB.plot(cx + rr * np.cos(th) * 0.95, cy + rr * np.sin(th) * 1.0, color=SPI, lw=0.9)
axB.plot([cx], [cy], "o", color=INK, ms=3.2); axB.text(cx - 2.6, cy - 2.4, r"$\alpha$", fontsize=7)
# hierarchical sub-box
hx, hy, hw, hh = x5 + 1.2, 14.6, w5 - 2.4, 12.6
axB.add_patch(FancyBboxPatch((hx, hy), hw, hh, boxstyle="round,pad=0,rounding_size=0.6",
                             fc="white", ec=HIE, lw=0.9))
axB.text(hx + 1, hy + hh - 1.2, "$u\\geq p_s(t)$: hierarchical update", color=HIE, fontsize=7.0,
         fontweight="bold", va="top")
axB.text(hx + 1, hy + hh - 4.6, "average of moves guided\nby $\\alpha$, $\\beta$, $\\delta$", fontsize=6.6, va="top")
tx, ty = hx + hw - 4.2, hy + 4.2
for (dx, dy, lab) in [(-3.6, 4.6, r"$\alpha$"), (0.6, 5.6, r"$\beta$"), (3.0, 1.2, r"$\delta$")]:
    axB.plot([tx + dx], [ty + dy], "o", color=INK, ms=3.0)
    axB.text(tx + dx + 0.5, ty + dy + 0.4, lab, fontsize=6.8)
    arrow((tx + dx, ty + dy), (tx, ty), color=HIE, linestyle=(0, (2, 1.5)))
axB.plot([tx], [ty], "o", mfc="white", mec=INK, ms=3.4)
axB.text(x5 + w5 / 2, y5 + 0.7, "drawings are schematic updates in the\ndecision space, not physical sensor movement",
         ha="center", va="bottom", fontsize=6.2, color=MUTED, style="italic")

# steps 6-9
bw, bh, by = 11.6, 30, 23
xs = [51.0, 63.6, 76.2, 88.2 - 0.0]
box(xs[0], by, bw, bh, "6. Projection", ["$\\mathbf{X}_i=\\Pi_{\\mathcal{F}}(\\widetilde{\\mathbf{X}}_i)$",
                                          "(clip each", "coordinate", "to $[0,L]$)"])
box(xs[1], by, bw, bh, "7. Evaluate", ["budget check:", "$P$ evaluations", "must fit; then", "compute $CR$",
                                        "for all $P$"])
box(xs[2], by, bw, bh, "8. Memory", ["replace $\\mathrm{pbest}_i$", "only if $CR$", "strictly", "improves"])
box(xs[3], by - 2, 11.2, bh + 2, "9. Leaders", ["rank pbest;", "$\\alpha$ replaced", "only on strict", "improvement;",
                                               "$\\beta,\\delta$ = 2nd,", "3rd pbest"])

# flow arrows
arrow((17.3, 36), (x5, 36))
arrow((x5 + w5, 36), (xs[0], 36))
for a_, b_ in zip(xs[:-1], xs[1:]):
    arrow((a_ + bw, 36), (b_, 36))
# loop 9 -> 5
yl = 4.5
axB.plot([xs[3] + 5.6, xs[3] + 5.6], [by - 2, yl], color=INK, lw=0.8)
axB.plot([xs[3] + 5.6, x5 + w5 / 2], [yl, yl], color=INK, lw=0.8)
arrow((x5 + w5 / 2, yl), (x5 + w5 / 2, y5))
axB.text((xs[3] + 5.6 + x5 + w5 / 2) / 2 + 6, yl + 0.8,
         "repeat with $t\\leftarrow t+1$ (new $u$ for every candidate)", ha="center", fontsize=7.0)
# stop condition
axB.text(xs[3] + 5.6, 54.2, "stop if $CR(\\mathbf{X}_\\alpha)=1$,\n$t=T$, or budget\nexhausted; return $\\mathbf{X}_\\alpha$",
         ha="center", va="bottom", fontsize=6.6, color=INK)
arrow((xs[3] + 5.6, by + bh), (xs[3] + 5.6, 53.8))

fig.savefig("/home/claude/m0/fig1/Figure01_HWOA_GWA_scheduled_selection.pdf")
fig.savefig("/home/claude/m0/fig1/Figure01_HWOA_GWA_scheduled_selection_preview.png", dpi=220)
print("ok")
