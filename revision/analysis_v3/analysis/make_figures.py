"""Figures for the revision (static, print). Usage:
python -I make_figures.py <E1_E5_data> <E5b_data> <results_E123> <results_E5> <out_dir>
F1 Convergence on the NFE axis (E5/E5b, confirmatory environments): median and IQR band.
F2 Operator mechanism of FULL (E1, exploratory): spiral share, direct pbest improvement,
   best-so-far update events, genotypic and phenotypic diversity.
F3 Schedule grid (E1, exploratory): mean difference to FULL in targets.
F4 Confirmatory effects (E5, E5b): HL estimates with 95% CIs, threshold +-1 target.
"""
import sys
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

D5, D5b, R123, R5, OUT = map(Path, sys.argv[1:6]); OUT.mkdir(parents=True, exist_ok=True)
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
S = {"FULL": "#2a78d6", "G(0.8,0.8)": "#eb6834", "SPIRAL": "#1baf7a", "mGWA": "#eda100",
     "PSO": "#e87ba4", "cACO": "#008300"}           # validated categorical order (light)
LS = {"FULL": "-", "G(0.8,0.8)": "-", "SPIRAL": "--", "mGWA": "--", "PSO": ":", "cACO": ":"}
MK = {"FULL": "o", "G(0.8,0.8)": "s", "SPIRAL": "^", "mGWA": "v", "PSO": "D", "cACO": "P"}   # secondary encoding
NT = {"S1": 75, "S2": 75, "S3": 120}
plt.rcParams.update({"font.size": 9, "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2,
                     "ytick.color": INK2, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8,
                     "axes.spines.top": False, "axes.spines.right": False, "lines.linewidth": 2,
                     "lines.solid_capstyle": "round", "legend.frameon": False, "savefig.dpi": 300})


def save(fig, name):
    fig.savefig(OUT / f"{name}.png", bbox_inches="tight"); fig.savefig(OUT / f"{name}.pdf", bbox_inches="tight")
    plt.close(fig)


# ── F1 convergence ────────────────────────────────────────────────────────
GRIDN = np.arange(25, 6251, 25)
runs5 = pd.read_csv(D5 / "E5_runs.csv"); runs5b = pd.read_csv(D5b / "E5b_runs.csv")
H5 = np.load(D5 / "E5_histories.npz"); H5b = np.load(D5b / "E5b_histories.npz")


def curves(runs, H, exp, method):
    out = {}
    for sc in ("S1", "S2", "S3"):
        sub = runs[(runs.method == method) & (runs.sc == sc)]
        M = []
        for r in sub.itertuples():
            tag = f"{exp}|{method}|{sc}|{r.env_seed}|{r.trial}|run"
            nfe, best = H[tag + "|obs_nfe"], H[tag + "|obs_best"]
            idx = np.searchsorted(nfe, GRIDN, side="right") - 1
            v = np.where(idx >= 0, best[np.clip(idx, 0, None)], np.nan) / NT[sc] * 100
            M.append(v)
        M = np.array(M); assert len(M) == 300
        out[sc] = (np.nanmedian(M, 0), np.nanpercentile(M, 25, 0), np.nanpercentile(M, 75, 0))
    return out


C = {m: curves(runs5, H5, "E5", m) for m in ("FULL", "SPIRAL", "mGWA", "PSO", "cACO")}
C["G(0.8,0.8)"] = curves(runs5b, H5b, "E5b", "G(0.8,0.8)")
fig, axs = plt.subplots(1, 3, figsize=(10.5, 3.4))
for ax, sc in zip(axs, ("S1", "S2", "S3")):
    for m in S:
        med, q1, q3 = C[m][sc]
        ax.fill_between(GRIDN, q1, q3, color=S[m], alpha=0.10, lw=0, step="post")
        ax.plot(GRIDN, med, color=S[m], ls=LS[m], label=m, marker=MK[m], ms=5, mec="white", mew=0.8,
                drawstyle="steps-post",
                markevery=(list(S).index(m) * 6 + 10, 40))
    ax.set_title(f"{sc} ({NT[sc]} hedef)", color=INK, fontsize=9.5, loc="left")
    ax.set_xlabel("NFE"); ax.set_xlim(0, 6250)
axs[0].set_ylabel("Best-so-far kapsama (%)")
axs[2].set_ylim(80, 100.5)
handles, labels = axs[0].get_legend_handles_labels()
fig.legend(handles, labels, ncol=6, loc="lower center", bbox_to_anchor=(0.5, -0.08))
fig.suptitle("Şekil R1. Yakınsama (E5/E5b)", x=0.01, ha="left", fontsize=10, color=INK)
fig.tight_layout(rect=(0, 0.03, 1, 0.95)); save(fig, "F1_convergence_E5")

# ── F1b: FULL vs CONST05 (P1) and FULL vs NOPB (P4), same convention ─────
C2 = {m: curves(runs5, H5, "E5", m) for m in ("CONST05", "NOPB")}
fig, axs = plt.subplots(2, 3, figsize=(10.5, 6.0), sharex=True)
for row, other in enumerate(("CONST05", "NOPB")):
    for col, sc in enumerate(("S1", "S2", "S3")):
        ax = axs[row, col]
        for m, colr, ls, mk in (("FULL", S["FULL"], "-", "o"), (other, INK2, "--", "x")):
            med, q1, q3 = (C[m] if m == "FULL" else C2[m])[sc]
            ax.fill_between(GRIDN, q1, q3, color=colr, alpha=0.10, lw=0, step="post")
            ax.plot(GRIDN, med, color=colr, ls=ls, marker=mk, ms=5, drawstyle="steps-post", markevery=(10 if m == "FULL" else 30, 40),
                    mec="white" if mk == "o" else colr, mew=0.8, label=m)
        ax.set_title(f"({'abc'[col] if row == 0 else 'def'[col]}) {sc}: FULL ve {other}", loc="left", fontsize=9.5)
        if row == 1: ax.set_xlabel("NFE")
        if col == 0: ax.set_ylabel("Best-so-far kapsama (%)")
        ax.set_xlim(0, 6250)
    axs[row, 0].legend(fontsize=8, loc="lower right")
fig.suptitle("Şekil R1b. Yakınsama: zaman planı (FULL ve CONST05) ve bellek (FULL ve NOPB), E5",
             x=0.01, ha="left", fontsize=10, color=INK)
fig.tight_layout(rect=(0, 0, 1, 0.96)); save(fig, "F1b_convergence_P1_P4")

# ── F2 mechanism (E1 exploratory) ─────────────────────────────────────────
mb = pd.read_csv(R123 / "E123_mechanism_bins.csv")
F = mb[mb.M == "FULL"].sort_values("bin"); x = (F["bin"].values + 0.5) * 625
pt = 0.8 - 0.6 * (x - 25) / 6225
fig, axs = plt.subplots(2, 3, figsize=(10.5, 6.0)); a = axs.ravel()
a[0].plot(x, F.S_n, color=S["FULL"], marker="o", ms=4, label="Gözlenen spiral payı")
a[0].fill_between(x, F.S_n_q1, F.S_n_q3, color=S["FULL"], alpha=0.10, lw=0)
a[0].plot(x, pt, color=INK2, lw=1, ls="--", label="p(t), plan")
a[0].set_title("(a) Spiral operatör payı", loc="left", fontsize=9.5); a[0].set_ylim(0, 1); a[0].legend(fontsize=8)
a[1].plot(x, F.S_imp, color=S["FULL"], marker="o", ms=4, label="Spiral hamleler")
a[1].plot(x, F.H_imp, color=S["G(0.8,0.8)"], marker="s", ms=4, ls="--", label="Hiyerarşik hamleler")
a[1].set_title("(b) Doğrudan pbest iyileşme oranı", loc="left", fontsize=9.5); a[1].legend(fontsize=8)
w = 230
a[2].bar(x - w / 2 - 6, F.global_src_S, width=w, color=S["FULL"], label="Spiral")
a[2].bar(x + w / 2 + 6, F.global_src_H, width=w, color=S["G(0.8,0.8)"], label="Hiyerarşik")
a[2].set_title("(c) Best-so-far güncelleme olayları\n(toplam, 270 koşu)", loc="left", fontsize=9.5); a[2].legend(fontsize=8)
for M, col, ls in (("FULL", S["FULL"], "-"), ("SPIRAL", S["SPIRAL"], "--"), ("HIER", S["mGWA"], "--"),
                   ("NOPB", INK2, ":")):
    g = mb[mb.M == M].sort_values("bin")
    a[3].plot(x, g.Dg, color=col, ls=ls, label=M if M != "HIER" else "HIER (= mGWA)")
    a[4].plot(x, g.Dp, color=col, ls=ls, label=M if M != "HIER" else "HIER (= mGWA)")
a[3].set_title("(d) Genotipik çeşitlilik D_g (m, dilim sonu)", loc="left", fontsize=9.5)
a[4].set_title("(e) Fenotipik çeşitlilik D_p (dilim sonu)", loc="left", fontsize=9.5)
a[3].legend(fontsize=8)
a[5].axis("off")
a[5].text(0, 0.95, "Keşif analizi (E1–E3): env 42, 17, 99;\nS1–S3 × 3 ortam × 30 deneme = 270 koşu/yöntem.\n\n"
          "(a, b, d, e): koşular üzerinden ortanca;\n(a) bandı IQR.\n(c): toplam olay sayısı, ortanca değil.\n\n"
          "Doğrudan iyileşme, operatörün çeşitlilik\nüzerinden dolaylı katkısını ayırmaz.",
          va="top", fontsize=8.5, color=INK2, transform=a[5].transAxes)
for ax in a[:5]:
    ax.set_xlabel("NFE (625'lik dilim ortası)"); ax.set_xlim(0, 6250)
fig.suptitle("Şekil R2. FULL'da operatör davranışı (E1–E3, keşif)", x=0.01, ha="left", fontsize=10, color=INK)
fig.tight_layout(rect=(0, 0, 1, 0.96)); save(fig, "F2_mechanism_E1")

# ── F3 grid heatmap (E1 exploratory) ──────────────────────────────────────
e1 = pd.read_csv(D5 / "E1_runs.csv"); assert len(e1) == 2430
surf = e1.groupby(["method", "sc"]).targets_covered.mean().unstack()      # full precision; rounded only in labels
cmap = LinearSegmentedColormap.from_list("div", ["#e34948", "#f0efec", "#2a78d6"])
vals = (0.2, 0.5, 0.8)
fig, axs = plt.subplots(1, 3, figsize=(11, 3.3), gridspec_kw=dict(wspace=0.25))
lim = max(abs((surf[sc] - surf.loc["G(0.8,0.2)", sc]).values).max() for sc in ("S1", "S2", "S3"))
for ax, sc in zip(axs, ("S1", "S2", "S3")):
    Z = np.array([[surf.loc[f"G({pi},{pe})", sc] - surf.loc["G(0.8,0.2)", sc] for pe in vals] for pi in vals])
    im = ax.imshow(Z, cmap=cmap, vmin=-lim, vmax=lim, origin="lower")
    for i in range(3):
        for j in range(3):
            txt = "FULL" if (vals[i], vals[j]) == (0.8, 0.2) else f"{Z[i, j]:+.2f}"
            ax.text(j, i, txt, ha="center", va="center", fontsize=8.5, color=INK)
    ax.set_xticks(range(3), [str(v) for v in vals]); ax.set_yticks(range(3), [str(v) for v in vals])
    ax.set_xlabel("p_end"); ax.grid(False)
    if sc == "S1":
        ax.set_ylabel("p_init")
    ax.set_title(f"{sc}", loc="left", fontsize=9.5)
cb = fig.colorbar(im, ax=axs, shrink=0.85); cb.set_label("Ortalama fark, hedef (hücre − FULL)")
fig.suptitle("Şekil R3. Seçim olasılığı planı duyarlılığı (E1, keşif; 90 koşu/hücre)",
             x=0.01, ha="left", fontsize=10, color=INK)
save(fig, "F3_grid_E1")

# ── F4 confirmatory effects forest plot ───────────────────────────────────
p = pd.read_csv(R5 / "E5_primary_P1_P4.csv"); b = pd.read_csv(R5 / "E5b_G0808_minus_FULL.csv")
lab = {"P1": "FULL − CONST05", "P2": "FULL − mGWA (HIER)", "P3": "FULL − SPIRAL", "P4": "FULL − NOPB",
       "G(0.8,0.8)-FULL": "G(0.8,0.8) − FULL (E5b)"}
rows = pd.concat([p, b])
fig, axs = plt.subplots(1, 3, figsize=(10.5, 3.2), sharey=True, sharex=True)
order = ["P1", "P2", "P3", "P4", "G(0.8,0.8)-FULL"]
for ax, sc in zip(axs, ("S1", "S2", "S3")):
    for k, c in enumerate(order):
        r = rows[(rows.comparison == c) & (rows.sc == sc)].iloc[0]
        y = len(order) - 1 - k
        sig = r.p_holm < 0.05
        ax.plot([r.ci_lo, r.ci_hi], [y, y], color=INK2, lw=2, solid_capstyle="butt")
        for xe, closed in ((r.ci_lo, r.ci_lo_closed), (r.ci_hi, r.ci_hi_closed)):   # interval ends
            if closed:
                ax.plot([xe, xe], [y - 0.18, y + 0.18], color=INK2, lw=2)        # closed end: bar
            else:
                ax.plot(xe, y, marker="o", ms=4.5, mfc="white", mec=INK2, mew=1.4, zorder=4)  # open end
        ax.plot(r.HL, y, "o", ms=7, color=S["FULL"] if sig else "white",
                mec=S["FULL"], mew=2, zorder=3)
    ax.axvline(0, color=INK2, lw=1); ax.axvspan(-1, 1, color=GRID, alpha=0.6, lw=0)
    ax.set_title(sc, loc="left", fontsize=9.5); ax.set_xlabel("HL, hedef (ortam düzeyi)")
axs[0].set_yticks(range(len(order)), [lab[c] for c in order[::-1]])
fig.suptitle("Şekil R4. Doğrulayıcı etkiler (E5, E5b)", x=0.01, ha="left", fontsize=10, color=INK)
fig.tight_layout(rect=(0, 0, 1, 0.92)); save(fig, "F4_confirmatory_effects")
print("figures written to", OUT)
