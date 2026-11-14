"""Exploratory analysis of E1-E3 (protocol v1.0.1 §5.2, §5.3, §6.4, §6.5 descriptive part).
Usage: python -I analyze_E123.py <out_dir> <tools_dir> <result_dir>
All E1-E3 findings are EXPLORATORY / SENSITIVITY (seen environments 42, 17, 99).
"""
import sys, json
from pathlib import Path
import numpy as np, pandas as pd

OUT, TOOLS, RES = map(Path, sys.argv[1:4]); RES.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(TOOLS)); import revstats as R

E = 1  # practical threshold: one target
runs = pd.concat([pd.read_csv(OUT / f"{e}_runs.csv") for e in ("E1", "E2", "E3")], ignore_index=True)
assert (runs.smoke == False).all() and len(runs) == 2430 + 540 + 270
runs["M"] = runs.method.replace({"G(0.8,0.2)": "FULL", "G(0.5,0.5)": "CONST05"})
T = runs.set_index(["M", "sc", "env_seed", "trial"]).targets_covered.sort_index()
SC, ENVS = ("S1", "S2", "S3"), (42, 17, 99)


def cell(m, sc, e):
    return T.loc[(m, sc, e)].sort_index()


def test(a, b, sc, e):
    x, y = cell(a, sc, e), cell(b, sc, e)
    assert (x.index == y.index).all() and len(x) == 30
    s = R.summarize((x - y).values)
    ci = s["ci"]
    return dict(sc=sc, env=e, n=30, k=s["k_nonzero"], p=s["p"], method=s["method"], HL=s["HL"],
                r_rb=s["r_rb"], ci_lo=float(ci["lo"]), ci_lo_closed=ci["lo_closed"], ci_hi=float(ci["hi"]),
                ci_hi_closed=ci["hi_closed"],
                ci_connected=ci["connected"], practical=R.practical(ci, E),
                mean_a=x.mean(), mean_b=y.mean(), sd_a=x.std(ddof=1), sd_b=y.std(ddof=1))


# ── §6.4 (a): P1-P4 cell tests, Holm over 36 ─────────────────────────────
P = {"P1": ("FULL", "CONST05"), "P2": ("FULL", "HIER"), "P3": ("FULL", "SPIRAL"), "P4": ("FULL", "NOPB")}
rows = []
for name, (a, b) in P.items():
    for sc in SC:
        for e in ENVS:
            rows.append(dict(comparison=name, a=a, b=b, **test(a, b, sc, e)))
fa = pd.DataFrame(rows); fa["p_holm"] = R.holm(fa.p.values)
fa["stat_result"] = np.where(fa.p_holm < 0.05, "tutarli fark", "fark gosterilemedi")
fa.to_csv(RES / "E123_family_a_P1_P4_cells.csv", index=False)

# ── §6.4 (b): grid cells - FULL, Holm over 72 ─────────────────────────────
G = [f"G({a},{b})" for a in (0.2, 0.5, 0.8) for b in (0.2, 0.5, 0.8)]
G = [g.replace("G(0.5,0.5)", "CONST05") for g in G if g != "G(0.8,0.2)"]
rows = []
for g in G:
    for sc in SC:
        for e in ENVS:
            rows.append(dict(cell_cfg=g, **test(g, "FULL", sc, e)))
fb = pd.DataFrame(rows); fb["p_holm"] = R.holm(fb.p.values)
fb["stat_result"] = np.where(fb.p_holm < 0.05, "tutarli fark", "fark gosterilemedi")
fb.to_csv(RES / "E123_family_b_grid_minus_FULL.csv", index=False)

# ── descriptive: means/SD per method x cell, grid surface ────────────────
desc = runs.groupby(["M", "sc", "env_seed"]).targets_covered.agg(["mean", "std", "median"]).reset_index()
desc.to_csv(RES / "E123_descriptive_cells.csv", index=False)
surf = runs[runs.exp == "E1"].groupby(["method", "sc"]).targets_covered.mean().unstack().round(2)
surf.to_csv(RES / "E123_grid_surface_mean_targets.csv")

# ── §6.5 descriptive variability (SD difference FULL - other), E1-E3 only ─
var = []
for other in ("HIER", "SPIRAL", "CONST05", "NOPB"):
    for sc in SC:
        for e in ENVS:
            a, b = cell("FULL", sc, e), cell(other, sc, e)
            var.append(dict(other=other, sc=sc, env=e, sd_full=a.std(ddof=1), sd_other=b.std(ddof=1),
                            sd_diff=a.std(ddof=1) - b.std(ddof=1)))
var = pd.DataFrame(var); var.to_csv(RES / "E123_variability_descriptive.csv", index=False)

# ── §5.2 anytime coverage (last observation with NFE <= threshold) ────────
TH = (1562.5, 3125.0, 4687.5, 6250.0)
any_rows = []
for e_name in ("E1", "E2", "E3"):
    H = np.load(OUT / f"{e_name}_histories.npz")
    sub = runs[runs.exp == e_name]
    for r in sub.itertuples():
        tag = f"{e_name}|{r.method}|{r.sc}|{r.env_seed}|{r.trial}|run"
        nfe, best = H[tag + "|obs_nfe"], H[tag + "|obs_best"]
        vals = [int(best[np.searchsorted(nfe, t, side="right") - 1]) if (nfe <= t).any() else np.nan for t in TH]
        # early-stopped runs keep 100% (all targets) after stopping
        any_rows.append(dict(M=r.M, sc=r.sc, env=r.env_seed, trial=r.trial,
                             **{f"nfe_{t:g}": v for t, v in zip(TH, vals)}))
anyt = pd.DataFrame(any_rows)
anyt_s = anyt.groupby(["M", "sc"])[[f"nfe_{t:g}" for t in TH]].median()
anyt_s.to_csv(RES / "E123_anytime_median_targets.csv")

# ── §5.3 mechanism metrics in 10 NFE bins (625 NFE each) ──────────────────
MECH = {"FULL": ("E1", "G(0.8,0.2)"), "CONST05": ("E1", "G(0.5,0.5)"), "SPIRAL": ("E2", "SPIRAL"),
        "HIER": ("E2", "HIER"), "NOPB": ("E3", "NOPB")}
mech = []
for M, (e_name, meth) in MECH.items():
    D = np.load(OUT / f"{e_name}_diagnostics.npz")
    acc = {b: dict(S_n=[], H_n=[], S_step=[], H_step=[], S_imp=[], H_imp=[], S_dlt=[], H_dlt=[],
                   Dg=[], Dp=[], gS=[], gH=[]) for b in range(10)}
    for sc in SC:
        for env in ENVS:
            for t in range(30):
                tag = f"{e_name}|{meth}|{sc}|{env}|{t}|run"
                it, ops, step = D[tag + "|it"], D[tag + "|ops"], D[tag + "|step"]
                na = bool(D[tag + "|pbest_na"])
                imp = None if na else D[tag + "|imp"]; dl = None if na else D[tag + "|delta"]
                gs, Dg, Dp = D[tag + "|gsrc"], D[tag + "|Dg"], D[tag + "|Dp"]
                nfe_end = 25 * (it.astype(int) + 2)              # NFE after iteration `it`
                b_of = np.minimum((nfe_end - 1) // 625, 9)
                for b in range(10):
                    sel = b_of == b
                    if not sel.any():
                        continue
                    o = ops[sel]; st = step[sel]
                    a = acc[b]
                    a["S_n"].append((o == 0).mean()); a["H_n"].append((o == 1).mean())
                    a["S_step"].append(st[o == 0].mean() if (o == 0).any() else np.nan)
                    a["H_step"].append(st[o == 1].mean() if (o == 1).any() else np.nan)
                    if not na:
                        im = imp[sel]; d = dl[sel]
                        a["S_imp"].append(im[o == 0].mean() if (o == 0).any() else np.nan)
                        a["H_imp"].append(im[o == 1].mean() if (o == 1).any() else np.nan)
                        a["S_dlt"].append(d[o == 0].mean() if (o == 0).any() else np.nan)
                        a["H_dlt"].append(d[o == 1].mean() if (o == 1).any() else np.nan)
                    g = gs[sel]; a["gS"].append(int((g == 0).sum())); a["gH"].append(int((g == 1).sum()))
                    last = np.where(sel)[0][-1] + 1                  # Dg/Dp index 0 = init
                    a["Dg"].append(Dg[last]); a["Dp"].append(Dp[last])
    for b in range(10):
        a = acc[b]
        def med(v):
            v = np.array(v, float); v = v[~np.isnan(v)]
            return (np.median(v), np.percentile(v, 25), np.percentile(v, 75)) if len(v) else (np.nan,) * 3
        row = dict(M=M, bin=b, nfe=f"{625*b+1}-{625*(b+1)}")
        for f in ("S_n", "H_n", "S_step", "H_step", "S_imp", "H_imp", "S_dlt", "H_dlt", "Dg", "Dp"):
            m, q1, q3 = med(a[f]); row[f] = m; row[f + "_q1"] = q1; row[f + "_q3"] = q3
        row["global_src_S"] = int(np.sum(a["gS"])); row["global_src_H"] = int(np.sum(a["gH"]))
        mech.append(row)
mech = pd.DataFrame(mech); mech.to_csv(RES / "E123_mechanism_bins.csv", index=False)

summary = dict(n_runs=len(runs), family_a_tests=len(fa), family_b_tests=len(fb),
               note="E1-E3 are exploratory (environments 42, 17, 99 were seen in the submitted paper).")
(RES / "E123_summary.json").write_text(json.dumps(summary, indent=2))
print("done", summary)
