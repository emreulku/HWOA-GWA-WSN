"""Figure 2 (revision): target layouts of exploratory instance 42.
Usage: python -I make_figure2.py <repo_root_with_src> <out_dir>"""
import sys
from pathlib import Path
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
sys.path.insert(0, sys.argv[1]); from src.environment import WSNEnvironment
out = Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
plt.rcParams.update({"font.family": "serif", "font.serif": ["STIXGeneral", "DejaVu Serif"],
                     "mathtext.fontset": "stix", "font.size": 8, "axes.linewidth": 0.6, "pdf.fonttype": 42})
INK, MUTED, TGT = "#0b0b0b", "#52514e", "#eb6834"
e75 = WSNEnvironment(100, 75, seed=42); e75b = WSNEnvironment(50, 75, seed=42)
assert np.array_equal(e75.targets, e75b.targets)          # S1 and S2 share targets
e120 = WSNEnvironment(200, 120, seed=42)
assert np.array_equal(e75.targets, e120.targets[:75])      # S3 starts with the same 75 targets
fig, axs = plt.subplots(1, 2, figsize=(7.0, 3.55), sharey=True)
for ax, env, title in [(axs[0], e75, "(a) S1 ($N=100$) and S2 ($N=50$): $M=75$ targets"),
                       (axs[1], e120, "(b) S3 ($N=200$): $M=120$ targets")]:
    ax.scatter(env.targets[:, 0], env.targets[:, 1], marker="x", s=16, lw=0.9, color=TGT, label="target")
    ax.add_patch(Circle((92, 8), 5, fill=False, ec=INK, lw=0.7))
    ax.text(92, 15, r"$r=5$ m", ha="center", fontsize=7, color=INK)
    ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.set_aspect("equal")
    ax.set_xticks(range(0, 101, 20)); ax.set_yticks(range(0, 101, 20))
    ax.grid(color="#e4e3df", lw=0.4); ax.set_axisbelow(True)
    ax.set_title(title, fontsize=8.5, color=INK, loc="left")
    ax.set_xlabel("$x$ (m)")
    ax.tick_params(width=0.6, length=3)
axs[0].set_ylabel("$y$ (m)")
fig.tight_layout(w_pad=1.5)
fig.savefig(out / "Figure02_WSN_Scenarios.pdf"); fig.savefig(out / "Figure02_WSN_Scenarios.png", dpi=600)
print("ok")
