"""E5b analysis (protocol addendum v1.0-d2, §3): G(0.8,0.8) - FULL, env-level, 3 tests, Holm.
Usage: python -I analyze_E5b.py <E5_out> <E5b_out> <tools_dir> <result_dir>
"""
import sys, json
from pathlib import Path
import numpy as np, pandas as pd

O5, O5b, TOOLS, RES = map(Path, sys.argv[1:5]); RES.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(TOOLS)); import revstats as R
SC = ("S1", "S2", "S3"); ENVS = tuple(range(1001, 1011)); E = 1
full = pd.read_csv(O5 / "E5_runs.csv"); full = full[full.method == "FULL"]
g = pd.read_csv(O5b / "E5b_runs.csv")
assert len(full) == 900 and len(g) == 900 and (g.smoke == False).all()
F = full.set_index(["sc", "env_seed", "trial"]).targets_covered.sort_index()
G = g.set_index(["sc", "env_seed", "trial"]).targets_covered.sort_index()
assert (F.index == G.index).all()
rows, sdrows = [], []
for sc in SC:
    med, sdd = [], []
    for e in ENVS:
        x, y = G.loc[(sc, e)], F.loc[(sc, e)]
        med.append(float(np.median((x - y).values))); sdd.append(float(x.std(ddof=1) - y.std(ddof=1)))
    s = R.summarize(np.array(med)); ci = s["ci"]
    rows.append(dict(comparison="G(0.8,0.8)-FULL", sc=sc, n_env=10, k=s["k_nonzero"], p=s["p"], HL=s["HL"],
                     r_rb=s["r_rb"], ci_lo=float(ci["lo"]), ci_lo_closed=ci["lo_closed"], ci_hi=float(ci["hi"]),
                     ci_hi_closed=ci["hi_closed"], ci_connected=ci["connected"],
                     practical=R.practical(ci, E), env_values=json.dumps(med),
                     mean_G=G.loc[sc].mean(), mean_FULL=F.loc[sc].mean()))
    sdrows.append(dict(sc=sc, sd_diff_env_median=float(np.median(sdd)), env_sd_diffs=json.dumps(sdd),
                       envs_with_lower_sd=int(sum(v < 0 for v in sdd))))
df = pd.DataFrame(rows); df["p_holm"] = R.holm(df.p.values)
df["stat_result"] = np.where(df.p_holm < 0.05, "ornekler arasinda tutarli fark",
                             "ornekler arasinda tutarli fark gosterilemedi")
df.to_csv(RES / "E5b_G0808_minus_FULL.csv", index=False)
pd.DataFrame(sdrows).to_csv(RES / "E5b_sd_descriptive.csv", index=False)
print(df[["sc", "k", "HL", "ci_lo", "ci_hi", "p", "p_holm", "stat_result", "practical", "mean_G", "mean_FULL"]].to_string(index=False))
print(pd.DataFrame(sdrows)[["sc", "sd_diff_env_median", "envs_with_lower_sd"]].to_string(index=False))
