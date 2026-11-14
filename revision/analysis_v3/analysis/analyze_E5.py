"""Confirmatory analysis of E5 (protocol v1.0.1 §6.3, §6.5, §6.6) + E4 runtime (§8, S7).
Usage: python -I analyze_E5.py <out_dir> <tools_dir> <result_dir>
"""
import sys, json
from pathlib import Path
import numpy as np, pandas as pd

OUT, TOOLS, RES = map(Path, sys.argv[1:4]); RES.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(TOOLS)); import revstats as R

E = 1
SC = ("S1", "S2", "S3"); ENVS = tuple(range(1001, 1011))
runs = pd.read_csv(OUT / "E5_runs.csv")
assert len(runs) == 9000 and (runs.smoke == False).all()
T = runs.set_index(["method", "sc", "env_seed", "trial"]).targets_covered.sort_index()


def env_level(a, b, sc, stat="median_diff"):
    """n = 10 environment-level values."""
    vals = []
    for e in ENVS:
        x, y = T.loc[(a, sc, e)].sort_index(), T.loc[(b, sc, e)].sort_index()
        assert (x.index == y.index).all() and len(x) == 30
        if stat == "median_diff":
            vals.append(float(np.median((x - y).values)))
        else:  # SD difference (ddof=1), not rounded
            vals.append(float(x.std(ddof=1) - y.std(ddof=1)))
    return np.array(vals)


def analyse(rows_spec, stat, family):
    rows = []
    for name, a, b, sc in rows_spec:
        v = env_level(a, b, sc, stat)
        s = R.summarize(v); ci = s["ci"]
        rows.append(dict(family=family, comparison=name, a=a, b=b, sc=sc, n_env=10, k=s["k_nonzero"],
                         all_zero=s["all_zero"], p=s["p"], method=s["method"], HL=s["HL"], r_rb=s["r_rb"],
                         ci_lo=float(ci["lo"]), ci_lo_closed=ci["lo_closed"], ci_hi=float(ci["hi"]),
                         ci_hi_closed=ci["hi_closed"], ci_connected=ci["connected"],
                         practical=(R.practical(ci, E) if stat == "median_diff" else "n/a"),
                         env_values=json.dumps(v.tolist()),
                         mean_a=T.loc[(a, sc)].mean(), mean_b=T.loc[(b, sc)].mean()))
    df = pd.DataFrame(rows); df["p_holm"] = R.holm(df.p.values)
    df["stat_result"] = np.where(df.p_holm < 0.05, "ornekler arasinda tutarli fark",
                                 "ornekler arasinda tutarli fark gosterilemedi")
    return df


P = [("P1", "FULL", "CONST05"), ("P2", "FULL", "mGWA"), ("P3", "FULL", "SPIRAL"), ("P4", "FULL", "NOPB")]
prim = analyse([(n, a, b, sc) for n, a, b in P for sc in SC], "median_diff", "primary_P1_P4")
prim.to_csv(RES / "E5_primary_P1_P4.csv", index=False)

var = analyse([(f"SD:{b}", "FULL", b, sc) for b in ("mGWA", "mWOA") for sc in SC], "sd_diff", "variability")
var.to_csv(RES / "E5_variability.csv", index=False)

base = analyse([(f"BASE:{b}", "FULL", b, sc) for b in ("PSO", "cACO", "mWOA", "CSA", "Random") for sc in SC],
               "median_diff", "baselines")
base.to_csv(RES / "E5_baselines.csv", index=False)

desc = runs.groupby(["method", "sc"]).targets_covered.agg(["mean", "std", "median"]).round(3)
desc["mean_pct"] = (desc["mean"] / runs.groupby(["method", "sc"]).sc.first().map({"S1": 75, "S2": 75, "S3": 120}) * 100).round(2)
desc.to_csv(RES / "E5_descriptive.csv")

# E4 runtime (measured runs only), median and IQR in seconds
e4 = pd.read_csv(OUT / "E4_runs.csv")
assert len(e4) == 300 and (e4.role == "measured").all()
rt = e4.groupby(["method", "sc"]).runtime.agg(median="median", q1=lambda s: s.quantile(.25),
                                              q3=lambda s: s.quantile(.75)).round(3)
rt.to_csv(RES / "E4_runtime.csv")
sysinfo = json.loads((OUT / "E4_system_info.json").read_text())

summary = dict(primary_tests=len(prim), variability_tests=len(var), baseline_tests=len(base),
               e4_system=dict(cpu=sysinfo.get("cpu_model"), cores=sysinfo.get("cpu_count"),
                              versions=sysinfo.get("versions")))
(RES / "E5_summary.json").write_text(json.dumps(summary, indent=2))
print(json.dumps(summary, indent=1))
