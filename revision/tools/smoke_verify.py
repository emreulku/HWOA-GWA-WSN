"""Verify smoke checkpoint: unique keys, stored == direct single runs, diagnostics decodable and equal."""
import sys, json, io, sqlite3
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).parent)); import revkit as rk
DB, SRC, OUT = sys.argv[1:4]
rk.init_tree(SRC)
db = sqlite3.connect(DB)
rows = db.execute("SELECT key,row,hist,diag FROM runs").fetchall()
keys = [tuple(json.loads(k)) for k, *_ in rows]
res = dict(n=len(rows), unique=len(set(keys)) == len(keys), mismatches=[])
for k, row, hist, diag in rows:
    key = json.loads(k); exp, m, sc, e, t, role = key
    row = json.loads(row); h = np.load(io.BytesIO(hist)); d = np.load(io.BytesIO(diag))
    r = rk.run_one(dict(sc=sc, env_seed=e, trial=t, method=m, diag=True))
    ok = (row["coverage"] == r["coverage"] and row["nfe_actual"] == r["nfe_actual"]
          and row["last_imp"] == r["last_imp"] and row["stop_reason"] == r["stop_reason"]
          and np.array_equal(h["obs_raw"], r["obs_raw"]) and np.array_equal(h["obs_nfe"], r["obs_nfe"])
          and np.array_equal(d["ops"], np.array([x["ops"] for x in r["diag"][1:]]))
          and np.allclose(d["Dg"], [x["Dg"] for x in r["diag"]]) and np.array_equal(d["best"], [x["best"] for x in r["diag"]])
          and d["ops"].shape == (r["n_gen"], rk.POP) and not bool(d["pbest_na"]))
    if not ok: res["mismatches"].append(key)
res["passed"] = res["unique"] and not res["mismatches"] and res["n"] == 18
Path(OUT).write_text(json.dumps(res, indent=2)); print(res)
