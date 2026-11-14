"""analysis-v4: confirmatory coverage summary with the gap to full coverage (Gap = M - K).
Derived from the same E5/E5b runs as analysis-v3; no new runs, no new tests.
Usage: python -I make_results_table.py <data/E1_E5> <data/E5b> <out_dir>"""
import sys
from pathlib import Path
import numpy as np, pandas as pd

D5, D5b, OUT = (Path(a) for a in sys.argv[1:4]); OUT.mkdir(parents=True, exist_ok=True)
M = {"S1": 75, "S2": 75, "S3": 120}
r = pd.concat([pd.read_csv(D5 / "E5_runs.csv"), pd.read_csv(D5b / "E5b_runs.csv")])
r = r[(r.role == "run") & (~r.smoke.astype(bool))]
r["M"] = r.sc.map(M)
r["K"] = np.rint(r.coverage * r.M / 100).astype(int)
assert (np.abs(r.K - r.coverage * r.M / 100) < 1e-6).all()      # protocol §5.1 conversion check
order = ["FULL", "CONST05", "SPIRAL", "mGWA", "NOPB", "G(0.8,0.8)", "mWOA", "PSO", "cACO", "CSA", "Random"]
rows = []
for sc in ["S1", "S2", "S3"]:
    for m in order:
        g = r[(r.sc == sc) & (r.method == m)]
        assert len(g) == 300, (sc, m, len(g))
        env_sd = g.groupby("env_seed").K.std(ddof=1)
        rows.append(dict(sc=sc, method=m, M=M[sc], n=len(g), mean_K=g.K.mean(), median_K=g.K.median(),
                         sd_K_pooled=g.K.std(ddof=1), median_env_sd=env_sd.median(),
                         mean_CR_pct=100 * g.K.mean() / M[sc], mean_gap=M[sc] - g.K.mean(),
                         full_coverage=int((g.K == M[sc]).sum())))
t = pd.DataFrame(rows)
t.to_csv(OUT / "T_results_E5_E5b_gap.csv", index=False)
print(t.round(2).to_string(index=False))
