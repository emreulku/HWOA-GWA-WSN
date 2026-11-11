"""G3-G5 equivalence gates (protocol v0.4 §7).
Usage: python -I g345.py <zip> <new_src> <reference_csv> <out_dir> <workers>
"""
import sys, json, time, pickle, platform, hashlib
from pathlib import Path
from multiprocessing import get_context
import numpy as np, pandas as pd

ZIP, NEW, REF, OUT = map(Path, sys.argv[1:5]); W = int(sys.argv[5])
sys.path.insert(0, str(Path(__file__).parent))
import revkit as rk

orig_src, g1 = rk.verify_sources(ZIP, NEW)
ref_sha = rk.sha256_file(REF)
OUT.mkdir(parents=True, exist_ok=True)
SEEDS, TRIALS = (42, 17, 99), range(30)


def specs(algo, mode, scen, **kw):
    return [dict(sc=sc, env_seed=e, trial=t, algo=algo, mode=mode, **kw)
            for sc in scen for e in SEEDS for t in TRIALS]


ALL = ("S1", "S2", "S3")
SETS = {
    "orig_obs": ("orig", specs("HWOA-GWA", "full", ALL) + specs("HWOA-GWA", "spiral", ("S1",))
                 + specs("HWOA-GWA", "hier", ("S1",)) + specs("mGWA", "full", ALL)),
    "new_off": ("new", specs("HWOA-GWA", "full", ALL) + specs("HWOA-GWA", "spiral", ("S1",))
                + specs("HWOA-GWA", "hier", ALL)),
    "new_on": ("new", specs("HWOA-GWA", "full", ALL, diag=True) + specs("HWOA-GWA", "spiral", ("S1",), diag=True)
               + specs("HWOA-GWA", "hier", ALL, diag=True)),
    "new_param": ("new", specs("HWOA-GWA", "full", ALL, pass_p=True, p_init=0.8, p_end=0.2)),
}


def fingerprint(name):
    """Identity of a run set: source tree, runner code, configuration, references."""
    tree, sp = SETS[name]
    src = orig_src if tree == "orig" else NEW
    meta = dict(set=name, tree=tree, src_hashes=rk.tree_hashes(src),
                runner_hashes={f: rk.sha256_file(Path(__file__).parent / f)
                               for f in ("revkit.py", Path(__file__).name)},
                specs_sha256=hashlib.sha256(json.dumps(sp, sort_keys=True).encode()).hexdigest(),
                zip_sha256=g1["zip_sha256"], reference_csv_sha256=ref_sha,
                versions=rk.env_versions())
    meta["fingerprint"] = hashlib.sha256(json.dumps(meta, sort_keys=True).encode()).hexdigest()
    return meta


def run_set(name):
    path = OUT / f"{name}.pkl"
    meta = fingerprint(name)
    if path.exists():
        cached = pickle.loads(path.read_bytes())
        if not isinstance(cached, dict) or cached.get("meta", {}).get("fingerprint") != meta["fingerprint"]:
            raise SystemExit(f"CACHE MISMATCH for {name}: {path} was produced by a different "
                             "source/runner/configuration/reference. Delete it or use a new out_dir.")
        return cached["results"]
    tree, sp = SETS[name]
    src = orig_src if tree == "orig" else NEW
    t0 = time.time()
    with get_context("fork").Pool(W, initializer=rk.init_tree, initargs=(str(src),)) as p:
        res = p.map(rk.run_one, sp, chunksize=2)
    for r in res:
        r.pop("diag", None)            # diagnostics content not needed for equivalence
    path.write_bytes(pickle.dumps(dict(meta=meta, results=res)))
    print(f"{name}: {len(res)} runs in {time.time()-t0:.0f}s", flush=True)
    return res


def k(r):  # comparison key without mode-specific p fields
    sc, e, algo, mode, t, *_ = r["key"]; return (sc, e, algo, mode, t)


INT = ("nfe_actual", "last_imp", "max_iter_used", "n_gen", "padded_len")
FLT = ("coverage", "disp")


def compare(A, B, label, map_b=None):
    """A, B: lists of run dicts. map_b: function mapping A key -> B key."""
    bi = {k(r): r for r in B}
    fails, maxd, exact, n = [], {f: 0.0 for f in FLT + ("hist_raw",)}, {f: 0 for f in FLT}, 0
    for a in A:
        kb = map_b(k(a)) if map_b else k(a)
        if kb not in bi:
            continue
        b = bi[kb]; n += 1; bad = []
        for f in INT:
            if int(a[f]) != int(b[f]): bad.append(f)
        if a["stop_reason"] != b["stop_reason"]: bad.append("stop_reason")
        for f in FLT:
            dlt = abs(a[f] - b[f]); maxd[f] = max(maxd[f], dlt); exact[f] += dlt == 0
            if dlt > 1e-9: bad.append(f)
        if not np.array_equal(a["obs_nfe"], b["obs_nfe"]): bad.append("obs_nfe")
        if not np.array_equal(a["obs_best"], b["obs_best"]): bad.append("hist_targets")
        if a["obs_raw"].shape != b["obs_raw"].shape:
            bad.append("hist_raw_shape")
        else:
            dlt = float(np.abs(a["obs_raw"] - b["obs_raw"]).max(initial=0))
            maxd["hist_raw"] = max(maxd["hist_raw"], dlt)
            if dlt > 1e-9: bad.append("hist_raw")
        if bad: fails.append(dict(key=kb, fields=bad))
    return dict(label=label, compared=n, failures=len(fails), fail_detail=fails[:20],
                max_abs_diff=maxd, exactly_equal=exact)


def internal(R, label):
    """Algorithm's own history vs observer running max at iteration ends."""
    bad = 0; mx = 0.0
    for r in R:
        dlt = float(np.abs(r["natural_raw"] - r["obs_raw"][1:]).max(initial=0)); mx = max(mx, dlt)
        if dlt > 1e-9 or not np.array_equal(r["natural_hist"], r["obs_best"][1:]):
            bad += 1
    return dict(label=label, runs=len(R), failures=bad, max_abs_diff=mx)


t_all = time.time()
R = {n: run_set(n) for n in SETS}

# G3 step 2: observer neutrality vs G0 reference CSV
ref = pd.read_csv(REF, encoding="utf-8-sig")
def ref_key(r):
    sc, e, algo, mode, t = k(r)
    if mode in ("spiral", "hier"):
        q = ref[(ref.sc_tag == sc + "_abl") & (ref.ablation == mode)]
    else:
        q = ref[(ref.sc_tag == sc) & (ref.algo == algo) & (ref.ablation == "full")]
    return q[(q.env_seed == e) & (q.trial == t)].iloc[0]
neut_fail = 0
for r in R["orig_obs"]:
    q = ref_key(r)
    ok = (abs(q.coverage - r["coverage"]) <= 1e-9 and abs(q.disp - r["disp"]) <= 1e-9
          and int(q.nfe_actual) == r["nfe_actual"] and int(q.last_imp) == r["last_imp"]
          and int(q.max_iter_used) == r["max_iter_used"] and q.stop_reason == r["stop_reason"])
    neut_fail += not ok
neutrality = dict(runs=len(R["orig_obs"]), failures=neut_fail)

orig_hm = [r for r in R["orig_obs"] if r["key"][2] == "HWOA-GWA"]
orig_mgwa = [r for r in R["orig_obs"] if r["key"][2] == "mGWA"]
new_hier = [r for r in R["new_off"] if r["key"][3] == "hier"]
G3 = dict(
    observer_neutrality_vs_G0=neutrality,
    internal_consistency_orig=internal(R["orig_obs"], "orig_obs"),
    internal_consistency_new=internal(R["new_off"] + R["new_on"] + R["new_param"], "new_all"),
    new_vs_orig=compare(R["new_off"], orig_hm, "new default vs original (FULL S1-S3, SPIRAL S1, HIER S1)"),
    hier_vs_mgwa=compare(new_hier, orig_mgwa, "new HIER vs original mGWA (S1-S3)",
                         map_b=lambda kk: (kk[0], kk[1], "mGWA", "full", kk[4])),
)
G4 = dict(diag_on_vs_off=compare(R["new_on"], R["new_off"], "diagnostics on vs off (630)"))
G5 = dict(param_vs_default=compare(R["new_param"],
                                   [r for r in R["new_off"] if r["key"][3] == "full"],
                                   "G(0.8,0.2) vs default FULL (270)"))

def ok3():
    return (neutrality["failures"] == 0 and G3["internal_consistency_orig"]["failures"] == 0
            and G3["internal_consistency_new"]["failures"] == 0
            and G3["new_vs_orig"]["failures"] == 0 and G3["new_vs_orig"]["compared"] == 450
            and G3["hier_vs_mgwa"]["failures"] == 0 and G3["hier_vs_mgwa"]["compared"] == 270)
passed = dict(G3=ok3(),
              G4=G4["diag_on_vs_off"]["failures"] == 0 and G4["diag_on_vs_off"]["compared"] == 630,
              G5=G5["param_vs_default"]["failures"] == 0 and G5["param_vs_default"]["compared"] == 270)

manifest = dict(protocol="v0.4",
                note=("Gate runs are used only for code verification, not performance analysis. "
                      "Zero differences here mean that the same algorithm with the same seeds produced "
                      "identical outputs (code equivalence); they say nothing about performance equality "
                      "between methods."),
                run_set_fingerprints={n: fingerprint(n)["fingerprint"] for n in SETS},
                zip_sha256=g1["zip_sha256"], reference_csv_sha256=ref_sha,
                changed_files=g1["changed_files"], added_files=g1["added_files"], extra_files=g1["extra_files"],
                new_tree_hashes=g1["new_tree_hashes"],
                executions={n: len(v) for n, v in R.items()},
                total_executions=sum(len(v) for v in R.values()),
                reuse="new HIER S1 compared with both original HIER S1 and original mGWA S1; "
                      "observer neutrality uses the G0 reference CSV (no extra runs)",
                versions=dict(python=platform.python_version(), numpy=np.__version__, pandas=pd.__version__),
                workers=W, wall_time_s=round(time.time() - t_all))
report = dict(passed=passed, G3=G3, G4=G4, G5=G5, manifest=manifest)
(OUT / "G3_G5.json").write_text(json.dumps(report, indent=2, default=str))
print(json.dumps(dict(passed=passed, manifest=manifest["executions"]), default=str))
