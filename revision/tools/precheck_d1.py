"""Pre-check for execution fixes (deviation v1.0-d1): BLAS forcing, E4 per-session warm-up,
double export hashes, smoke CSV columns. Usage: python -I precheck_d1.py ZIP SRC PROTOCOL WORKDIR OUT_JSON"""
import sys, os, json, sqlite3, subprocess, time, csv, hashlib
from pathlib import Path
ZIP, SRC, PROTO, WD, OUT = sys.argv[1:6]
WD = Path(WD); WD.mkdir(parents=True, exist_ok=True)
RUN = [sys.executable, "-I", str(Path(__file__).parent / "run_experiments.py"), "--zip", ZIP, "--src", SRC, "--protocol", PROTO]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
res = {}

# --- E4 smoke: hostile env (OMP=4), kill after first measured run, resume twice, export twice
e4 = WD / "e4"; env = dict(os.environ, OMP_NUM_THREADS="4", OPENBLAS_NUM_THREADS="4", MKL_NUM_THREADS="4")
p = subprocess.Popen(RUN + ["--exp", "E4", "--out", str(e4), "--smoke"], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
db = e4 / "E4.sqlite"
for _ in range(600):
    time.sleep(0.2)
    try:
        if sqlite3.connect(db).execute("select count(*) from runs").fetchone()[0] >= 1: break
    except Exception: pass
p.kill(); p.wait()
n_after_kill = sqlite3.connect(db).execute("select count(*) from runs").fetchone()[0]
subprocess.run(RUN + ["--exp", "E4", "--out", str(e4), "--smoke", "--limit", "2"], env=env, check=True, capture_output=True)
subprocess.run(RUN + ["--exp", "E4", "--out", str(e4), "--smoke", "--export"], env=env, check=True, capture_output=True)
c = sqlite3.connect(db)
sessions = [r[0] for r in c.execute("select session from sessions order by started")]
blas = [json.loads(r[0]) for r in c.execute("select blas from sessions order by started")]
runs = c.execute("select key, session, t from runs").fetchall()
warm = c.execute("select session, method, sc, t from warmups").fetchall()
ok_warm = True; detail = []
for k, s, t in runs:
    m, sc = json.loads(k)[1], json.loads(k)[2]
    w = [wt for ws, wm, wsc, wt in warm if ws == s and wm == m and wsc == sc]
    good = bool(w) and min(w) < t
    ok_warm &= good; detail.append(dict(key=json.loads(k), session=s[:8], warmed_before=good))
res["E4"] = dict(stored_after_kill=n_after_kill, sessions=len(sessions), measured=len(runs), warmups=len(warm),
                 every_measured_run_preceded_by_same_session_warmup=ok_warm, detail=detail,
                 blas_forced=[b["forced"] for b in blas], blas_original=[b["original"] for b in blas],
                 all_single_threaded=[b["all_single_threaded"] for b in blas])
# double export: manifest hashes must match files after the 2nd export, manifest not self-listed
def manifest_ok(d, exp):
    m = json.loads((d / f"{exp}_manifest.json").read_text())
    return (f"{exp}_manifest.json" not in m["outputs"]
            and all(sha(d / f) == h for f, h in m["outputs"].items())), sorted(m["outputs"])
subprocess.run(RUN + ["--exp", "E4", "--out", str(e4), "--smoke", "--export"], env=env, check=True, capture_output=True)
res["E4"]["double_export_hashes_valid"], res["E4"]["outputs"] = manifest_ok(e4, "E4")

# --- E1 smoke: CSV columns, double export
e1 = WD / "e1"
subprocess.run(RUN + ["--exp", "E1", "--out", str(e1), "--smoke", "--export"], check=True, capture_output=True)
subprocess.run(RUN + ["--exp", "E1", "--out", str(e1), "--smoke", "--export"], check=True, capture_output=True)
rows = list(csv.DictReader(open(e1 / "E1_runs.csv")))
res["E1"] = dict(n=len(rows),
                 columns_ok=all(r["exp"] == "E1" and r["method"].startswith("G(") and r["sc"] == "S1"
                                and r["env_seed"] == "42" and r["trial"] in ("0", "1") and r["role"] == "run"
                                and r["smoke"] == "True" for r in rows),
                 header=list(rows[0].keys())[:8])
res["E1"]["double_export_hashes_valid"], res["E1"]["outputs"] = manifest_ok(e1, "E1")
v = subprocess.run([sys.executable, "-I", str(Path(__file__).parent / "smoke_verify.py"), str(e1 / "E1.sqlite"), SRC,
                    str(WD / "smoke_verify.json")], capture_output=True, text=True)
res["E1"]["stored_equals_direct"] = json.loads((WD / "smoke_verify.json").read_text())["passed"]
res["passed"] = (res["E4"]["every_measured_run_preceded_by_same_session_warmup"] and res["E4"]["sessions"] >= 3
                 and all(b == {"OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1"} for b in res["E4"]["blas_forced"])
                 and all(x is not False for x in res["E4"]["all_single_threaded"])
                 and res["E4"]["double_export_hashes_valid"] and res["E4"]["measured"] == 6
                 and res["E1"]["columns_ok"] and res["E1"]["n"] == 18 and res["E1"]["double_export_hashes_valid"]
                 and res["E1"]["stored_equals_direct"])
Path(OUT).write_text(json.dumps(res, indent=2)); print(json.dumps(res, indent=1)[:3000])
