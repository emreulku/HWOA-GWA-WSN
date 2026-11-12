"""
E1-E5 orchestrator (protocol v1.0 §8, §8a; execution fixes in deviation log v1.0-d1).

Usage:
  python -I run_experiments.py --zip ZIP --src NEW_SRC --protocol PROTOCOL.md \
      --exp E1 --out OUT_DIR [--workers 2] [--commit HASH] [--limit N] [--export] [--smoke]

- Builds the experiment matrix from the protocol (unique keys).
- Checkpoints every completed run in OUT_DIR/<exp>.sqlite (one row per key,
  committed immediately); a rerun resumes and skips stored keys.
- The checkpoint carries a fingerprint (source/runner hashes, protocol hash,
  matrix hash, ZIP hash, Python/package versions, BLAS thread settings,
  smoke flag). Any mismatch stops. The commit is a label, set once.
- BLAS thread variables are FORCED to 1 before numpy is imported; the
  original values are recorded. If threadpoolctl is available, every
  loaded BLAS/OpenMP pool must report 1 thread, otherwise the script stops.
- E4 is sequential in this process. Its completion keys are the 300 measured
  runs only. Every process (session) performs its own warm-up run for each
  (method, scenario) that still has measured runs pending, before measuring;
  warm-ups and sessions are logged in separate tables.
- --export writes an explicit list of output files plus a manifest that
  lists their hashes (the manifest never lists itself), and only succeeds if
  the stored key set equals the expected key set.
"""
import os
_BLAS_VARS = ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS")
_BLAS_ORIGINAL = {v: os.environ.get(v) for v in _BLAS_VARS}
for _v in _BLAS_VARS:
    os.environ[_v] = "1"                      # forced, before numpy is imported

import argparse, hashlib, io, json, platform, sqlite3, sys, time, uuid
from pathlib import Path
from multiprocessing import get_context
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import revkit as rk

SCEN = ("S1", "S2", "S3")
OLD_ENVS = (42, 17, 99)
NEW_ENVS = tuple(range(1001, 1011))
TRIALS = tuple(range(30))
GRID = [f"G({a},{b})" for a in (0.2, 0.5, 0.8) for b in (0.2, 0.5, 0.8)]
TEN = ["Random", "PSO", "cACO", "mWOA", "mGWA", "CSA", "FULL", "SPIRAL", "CONST05", "NOPB"]
KEY_FIELDS = ("exp", "method", "sc", "env_seed", "trial", "role")
EXPECTED = {"E1": 2430, "E2": 540, "E3": 270, "E4": 300, "E5": 9000, "E5b": 900}


def blas_status():
    st = dict(forced={v: os.environ.get(v) for v in _BLAS_VARS}, original=_BLAS_ORIGINAL)
    try:
        from threadpoolctl import threadpool_info
        pools = threadpool_info()
        st["threadpoolctl"] = [dict(api=p.get("user_api"), lib=p.get("internal_api"),
                                    threads=p.get("num_threads")) for p in pools]
        st["all_single_threaded"] = all(p.get("num_threads") == 1 for p in pools)
    except ImportError:
        st["threadpoolctl"] = None
        st["all_single_threaded"] = None
    return st


def matrix(exp, smoke=False):
    S = []
    def add(methods, envs, trials, diag, role="run"):
        for m in methods:
            for sc in SCEN:
                for e in envs:
                    for t in trials:
                        S.append(dict(exp=exp, method=m, sc=sc, env_seed=e, trial=t, diag=diag,
                                      role=role, key=(exp, m, sc, e, t, role)))
    if exp == "E1":
        add(GRID, OLD_ENVS, TRIALS, True)
    elif exp == "E2":
        add(["SPIRAL", "HIER"], OLD_ENVS, TRIALS, True)
    elif exp == "E3":
        add(["NOPB"], OLD_ENVS, TRIALS, True)
    elif exp == "E4":
        add(TEN, (42,), range(10), False, role="measured")
    elif exp == "E5":
        add(TEN, NEW_ENVS, TRIALS, False)
    elif exp == "E5b":                       # protocol addendum v1.0-d2 (E5b)
        add(["G(0.8,0.8)"], NEW_ENVS, TRIALS, False)
    else:
        raise SystemExit(f"unknown experiment {exp} (E6 is optional and not implemented in v1.0)")
    keys = [s["key"] for s in S]
    assert len(keys) == len(set(keys)), "duplicate keys in matrix"
    assert len(S) == EXPECTED[exp], (exp, len(S))
    if smoke:  # pre-check subset (§8a); the smoke flag is part of the fingerprint, not of the key
        if exp == "E4":
            S = [s for s in S if s["method"] in ("FULL", "PSO") and s["sc"] == "S1" and s["trial"] < 3]
        else:
            S = [s for s in S if s["sc"] == "S1" and s["env_seed"] == 42 and s["trial"] in (0, 1)]
    return S


# ── serialization ───────────────────────────────────────────────────────
def _npz(**arrs):
    b = io.BytesIO(); np.savez_compressed(b, **arrs); return b.getvalue()


def pack_diag(rows):
    it = np.array([r["it"] for r in rows[1:]], dtype=np.int16)
    def stack(f, dt):
        return np.array([r[f] for r in rows[1:]], dtype=dt)
    na = rows[1]["imp"] is None if len(rows) > 1 else True
    return _npz(it=it, p=stack("p", np.float64), ops=stack("ops", np.int8),
                step=stack("step", np.float32),
                imp=(np.zeros((0,), np.int8) if na else stack("imp", np.int8)),
                delta=(np.zeros((0,), np.float32) if na else stack("delta", np.float32)),
                pbest_na=np.array(na), gsrc=stack("gsrc", np.int8),
                Dg=np.array([r["Dg"] for r in rows]), Dp=np.array([r["Dp"] for r in rows]),
                best=np.array([r["best"] for r in rows], dtype=np.int16))


SCALARS = ("coverage", "disp", "nfe_actual", "last_imp", "max_iter_used", "init_cost", "iter_cost",
           "stop_reason", "n_gen", "nfe_aligned", "padded_len", "runtime")


def execute(spec):
    r = rk.run_one(dict(sc=spec["sc"], env_seed=spec["env_seed"], trial=spec["trial"],
                        method=spec["method"], diag=spec["diag"]))
    row = {k: (r[k].item() if hasattr(r[k], "item") else r[k]) for k in SCALARS}
    row["targets_covered"] = int(r["obs_best"][-1])
    row["phen_time"] = r.get("phen_time")
    row["call"] = r["call"]
    hist = _npz(obs_nfe=r["obs_nfe"].astype(np.int32), obs_raw=r["obs_raw"],
                obs_best=r["obs_best"].astype(np.int16))
    diag = pack_diag(r["diag"]) if "diag" in r else None
    return spec["key"], row, hist, diag


# ── fingerprint / checkpoint ────────────────────────────────────────────
def fingerprint(args, exp, specs, g1):
    here = Path(__file__).parent
    meta = dict(exp=exp, smoke=bool(args.smoke),
                protocol_sha256=rk.sha256_file(args.protocol),
                zip_sha256=g1["zip_sha256"], src_hashes=g1["new_tree_hashes"],
                added_files=g1["added_files"], changed_files=g1["changed_files"],
                runner_hashes={f: rk.sha256_file(here / f) for f in ("revkit.py", Path(__file__).name)},
                matrix_sha256=hashlib.sha256(json.dumps([s["key"] for s in specs]).encode()).hexdigest(),
                n_expected=len(specs), versions=rk.env_versions(),
                blas_forced={v: os.environ.get(v) for v in _BLAS_VARS})
    meta["fingerprint"] = hashlib.sha256(json.dumps(meta, sort_keys=True).encode()).hexdigest()
    meta["commit"] = args.commit                      # label, not fingerprinted
    return meta


def open_db(path, meta):
    db = sqlite3.connect(path)
    db.execute("CREATE TABLE IF NOT EXISTS meta (value TEXT NOT NULL)")
    db.execute("CREATE TABLE IF NOT EXISTS runs (key TEXT PRIMARY KEY, row TEXT, hist BLOB, diag BLOB, t REAL, session TEXT)")
    db.execute("CREATE TABLE IF NOT EXISTS sessions (session TEXT PRIMARY KEY, started REAL, pid INTEGER, blas TEXT)")
    db.execute("CREATE TABLE IF NOT EXISTS warmups (session TEXT, method TEXT, sc TEXT, runtime REAL, t REAL)")
    prev = db.execute("SELECT value FROM meta").fetchone()
    if prev is None:
        db.execute("INSERT INTO meta VALUES (?)", (json.dumps(meta, sort_keys=True),)); db.commit()
    else:
        old = json.loads(prev[0])
        if old["fingerprint"] != meta["fingerprint"]:
            diff = sorted(k for k in meta if k != "commit" and meta.get(k) != old.get(k))
            raise SystemExit(f"CHECKPOINT MISMATCH in {path}: fields differ: {diff}. Use a new --out.")
        if old.get("commit") != meta["commit"]:
            if old.get("commit") == "PENDING":
                db.execute("UPDATE meta SET value = ?", (json.dumps(meta, sort_keys=True),)); db.commit()
            elif meta["commit"] != "PENDING":
                raise SystemExit(f"COMMIT MISMATCH: checkpoint {old.get('commit')} vs {meta['commit']}")
            else:
                meta["commit"] = old["commit"]
    return db


def stored_keys(db):
    return {tuple(json.loads(k)) for (k,) in db.execute("SELECT key FROM runs")}


def _init(src):
    rk.init_tree(src)


def run(args):
    exp = args.exp
    _, g1 = rk.verify_sources(args.zip, args.src)
    specs = matrix(exp, args.smoke)
    meta = fingerprint(args, exp, specs, g1)
    blas = blas_status()
    if exp == "E4" and blas["all_single_threaded"] is False:
        raise SystemExit(f"E4 STOP: BLAS/OpenMP pools are not single-threaded: {blas['threadpoolctl']}")
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    db = open_db(out / f"{exp}.sqlite", meta)
    session = uuid.uuid4().hex
    db.execute("INSERT INTO sessions VALUES (?,?,?,?)", (session, time.time(), os.getpid(), json.dumps(blas)))
    db.commit()
    have = stored_keys(db)
    todo = [s for s in specs if tuple(s["key"]) not in have]
    if args.limit:
        todo = todo[:args.limit]
    print(f"{exp}: {len(have)}/{len(specs)} stored, running {len(todo)} (session {session[:8]})", flush=True)
    t0 = time.time(); n = 0

    def store(res):
        nonlocal n
        key, row, hist, diag = res
        db.execute("INSERT INTO runs VALUES (?,?,?,?,?,?)",
                   (json.dumps(list(key)), json.dumps(row), hist, diag, time.time(), session))
        db.commit(); n += 1
        if n % 50 == 0:
            print(f"  {n}/{len(todo)} in {time.time()-t0:.0f}s", flush=True)

    if exp == "E4":                                     # sequential, this process
        rk.init_tree(args.src)
        warmed = set()
        for s in todo:
            pair = (s["method"], s["sc"])
            if pair not in warmed:                      # warm-up in THIS session before measuring
                w = rk.run_one(dict(sc=s["sc"], env_seed=42, trial=0, method=s["method"]))
                db.execute("INSERT INTO warmups VALUES (?,?,?,?,?)",
                           (session, s["method"], s["sc"], w["runtime"], time.time()))
                db.commit(); warmed.add(pair)
            store(execute(s))
    else:
        with get_context("fork").Pool(args.workers, initializer=_init, initargs=(str(args.src),)) as p:
            for res in p.imap_unordered(execute, todo, chunksize=1):
                store(res)
    print(f"{exp}: stored {n} new runs in {time.time()-t0:.0f}s; total {len(stored_keys(db))}/{len(specs)}", flush=True)
    if args.export:
        export(db, specs, meta, out, exp)


def export(db, specs, meta, out, exp):
    expected = {tuple(s["key"]) for s in specs}
    have = stored_keys(db)
    missing, extra = expected - have, have - expected
    if missing or extra:
        raise SystemExit(f"{exp}: INCOMPLETE - missing {len(missing)}, unexpected {len(extra)}; not exported")
    import csv
    rows, H, D = [], {}, {}
    for k, row, hist, diag, sess in db.execute("SELECT key, row, hist, diag, session FROM runs ORDER BY key"):
        key = json.loads(k); row = json.loads(row)
        assert len(key) == len(KEY_FIELDS), key
        kd = dict(zip(KEY_FIELDS, key))
        tag = "|".join(map(str, key))
        rows.append(dict(smoke=meta["smoke"], **kd, session=sess,
                         **{c: row[c] for c in row if c != "call"}))
        h = np.load(io.BytesIO(hist))
        for f in h.files: H[f"{tag}|{f}"] = h[f]
        if diag is not None:
            d = np.load(io.BytesIO(diag))
            for f in d.files: D[f"{tag}|{f}"] = d[f]
    outputs = [f"{exp}_runs.csv", f"{exp}_histories.npz"]
    with open(out / outputs[0], "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    np.savez_compressed(out / outputs[1], **H)
    if D:
        outputs.append(f"{exp}_diagnostics.npz")
        np.savez_compressed(out / outputs[-1], **D)
    sessions = [dict(session=s, started=t, pid=p, blas=json.loads(b))
                for s, t, p, b in db.execute("SELECT * FROM sessions ORDER BY started")]
    warm = [dict(session=s, method=m, sc=c, runtime=r, t=t)
            for s, m, c, r, t in db.execute("SELECT * FROM warmups ORDER BY t")]
    outputs.append(f"{exp}_sessions.json")
    (out / outputs[-1]).write_text(json.dumps(dict(sessions=sessions, warmups=warm), indent=2))
    if exp == "E4":
        sysinfo = dict(platform=platform.platform(), processor=platform.processor(),
                       machine=platform.machine(), cpu_count=os.cpu_count(), versions=rk.env_versions(),
                       blas=blas_status())
        try:
            sysinfo["cpu_model"] = next(l.split(":", 1)[1].strip() for l in open("/proc/cpuinfo") if l.startswith("model name"))
            sysinfo["mem_total"] = next(l.split(":", 1)[1].strip() for l in open("/proc/meminfo") if l.startswith("MemTotal"))
        except Exception:
            pass
        outputs.append("E4_system_info.json")
        (out / outputs[-1]).write_text(json.dumps(sysinfo, indent=2))
    files = {name: rk.sha256_file(out / name) for name in outputs}      # explicit list; manifest excluded
    man = dict(meta, completed=len(have), expected=len(expected), complete=True, outputs=files,
               note="Completion criterion: stored key set == expected key set (protocol §8a). "
                    "The manifest lists the hashes of the files in 'outputs' and never itself.")
    (out / f"{exp}_manifest.json").write_text(json.dumps(man, indent=2))
    print(f"{exp}: exported {len(rows)} runs; manifest written", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--zip", required=True); ap.add_argument("--src", required=True)
    ap.add_argument("--protocol", required=True); ap.add_argument("--exp", required=True)
    ap.add_argument("--out", required=True); ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--commit", default="PENDING"); ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--export", action="store_true"); ap.add_argument("--smoke", action="store_true")
    run(ap.parse_args())
