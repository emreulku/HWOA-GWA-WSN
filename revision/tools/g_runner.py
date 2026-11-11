"""Runner check (before E1-E5): every protocol method is dispatched correctly.
Usage: python -I g_runner.py <zip> <new_src> <out_json>
"""
import sys, json, time
from pathlib import Path
from multiprocessing import get_context
import numpy as np

ZIP, NEW, OUT = map(Path, sys.argv[1:4])
sys.path.insert(0, str(Path(__file__).parent))
import revkit as rk
orig_src, g1 = rk.verify_sources(ZIP, NEW)
SC = {"S1": (100, 75), "S2": (50, 75), "S3": (200, 120)}
CASES = [("S1", 42, 0), ("S2", 42, 0), ("S3", 42, 0), ("S1", 17, 1)]
ORIG7 = ["Random", "PSO", "cACO", "mWOA", "mGWA", "CSA", "HWOA-GWA"]


def orig_run(a):  # submitted runner, submitted tree
    import statistical_experiment as se
    return se._run_one(a)


def padded(h, max_iter):
    h = list(h)
    if len(h) < max_iter: h = h + [h[-1]] * (max_iter - len(h))
    return h[:max_iter]


t0 = time.time()
otasks = [(sc, *SC[sc], e, a, t, rk.MAX_NFE, "full") for sc, e, t in CASES for a in ORIG7]
otasks += [(sc, *SC[sc], e, "HWOA-GWA", t, rk.MAX_NFE, m) for sc, e, t in CASES for m in ("spiral", "hier")]
with get_context("fork").Pool(2, initializer=rk.init_tree, initargs=(str(orig_src),)) as p:
    O = p.map(orig_run, otasks)
O = {(r["sc_tag"], r["env_seed"], r["algo"], r["ablation"], r["trial"]): r for r in O}

methods = ["Random", "PSO", "cACO", "mWOA", "mGWA", "CSA", "FULL", "SPIRAL", "HIER", "CONST05", "NOPB",
           "G(0.8,0.2)", "G(0.5,0.5)"]
ntasks = [dict(sc=sc, env_seed=e, trial=t, method=m) for sc, e, t in CASES for m in methods]
with get_context("fork").Pool(2, initializer=rk.init_tree, initargs=(str(NEW),)) as p:
    N = p.map(rk.run_one, ntasks)
N = {(r["key"][0], r["key"][1], r["method"], r["key"][4]): r for r in N}

FIELDS = ("coverage", "disp", "nfe_actual", "last_imp", "max_iter_used", "stop_reason")
def same(n, o):
    ok = all((abs(n[f] - o[f]) <= 1e-9) if isinstance(o[f], float) else (n[f] == o[f]) for f in FIELDS)
    return ok and np.array_equal(np.array(padded(n["history"], n["max_iter_used"])), np.array(o["history"]))
def same_new(a, b):
    return all(a[f] == b[f] for f in FIELDS) and np.array_equal(a["obs_raw"], b["obs_raw"])

checks = []
target = {"Random": ("Random", "full"), "PSO": ("PSO", "full"), "cACO": ("cACO", "full"),
          "mWOA": ("mWOA", "full"), "mGWA": ("mGWA", "full"), "CSA": ("CSA", "full"),
          "FULL": ("HWOA-GWA", "full"), "SPIRAL": ("HWOA-GWA", "spiral"), "HIER": ("HWOA-GWA", "hier")}
for sc, e, t in CASES:
    for m in methods:
        n = N[(sc, e, m, t)]
        c = dict(sc=sc, env_seed=e, trial=t, method=m, fn=n["call"]["fn"],
                 kwargs={k: v for k, v in n["call"]["kwargs"].items() if k not in ("seed",)})
        if m in target:
            c["equals_submitted_runner"] = bool(same(n, O[(sc, e, *target[m][:1], target[m][1], t)]))
        if m == "HIER":
            c["equals_submitted_mGWA"] = bool(same(n, O[(sc, e, "mGWA", "full", t)]))
        if m == "CONST05":
            c["p_passed"] = n["call"]["kwargs"].get("p_init") == 0.5 and n["call"]["kwargs"].get("p_end") == 0.5
            c["differs_from_FULL"] = bool(not same_new(n, N[(sc, e, "FULL", t)]))
        if m == "NOPB":
            c["nopb_fn"] = n["call"]["fn"].endswith("run_hwoa_gwa_nopb")
        if m == "G(0.8,0.2)":
            c["equals_FULL"] = bool(same_new(n, N[(sc, e, "FULL", t)]))
        if m == "G(0.5,0.5)":
            c["equals_CONST05"] = bool(same_new(n, N[(sc, e, "CONST05", t)]))
        # descriptive: NFE alignment and own-history vs observer running max
        c["nfe_aligned"] = bool(n["nfe_aligned"])
        c["history_is_best_so_far"] = bool(len(n["natural_raw"]) == len(n["obs_raw"]) - (1 if n["init_cost"] > 0 else 0)
                                           and np.abs(n["natural_raw"] - n["obs_raw"][(1 if n["init_cost"] > 0 else 0):]).max(initial=0) <= 1e-9)
        checks.append(c)

# rejection checks
rk.init_tree(NEW)
rejections = {}
for bad in [dict(method="PSO2"), dict(method="G(0.3,0.5)"), dict(method="HWOA-GWA"),
            dict(method="PSO", diag=True), dict(algo="pso")]:
    try:
        rk.run_one(dict(sc="S1", env_seed=42, trial=0, **bad)); rejections[str(bad)] = "NOT REJECTED"
    except (ValueError, KeyError, RuntimeError) as ex:
        rejections[str(bad)] = f"rejected: {type(ex).__name__}: {ex}"

# mandatory criteria; CONST05 differs_from_FULL is descriptive only
crit = ["equals_submitted_runner", "equals_submitted_mGWA", "p_passed", "nopb_fn",
        "equals_FULL", "equals_CONST05", "nfe_aligned", "history_is_best_so_far"]
DESCRIPTIVE = ["differs_from_FULL"]
passed = all(all(c[k] for k in crit if k in c) for c in checks) and \
         all(v.startswith("rejected") for v in rejections.values())
rep = dict(gate="RUNNER", passed=passed, mandatory_criteria=crit, descriptive_criteria=DESCRIPTIVE, zip_sha256=g1["zip_sha256"], added_files=g1["added_files"],
           runner_sha256=rk.sha256_file(Path(__file__).parent / "revkit.py"), versions=rk.env_versions(),
           note="Runner dispatch check; results are used only for code verification.",
           checks=checks, rejections=rejections,
           executions=dict(submitted_runner=len(otasks), revision_runner=len(ntasks)),
           wall_time_s=round(time.time() - t0, 1))
OUT.write_text(json.dumps(rep, indent=2, default=lambda o: o.item() if hasattr(o, "item") else str(o)))
print("passed", passed)
for c in checks:
    print({k: v for k, v in c.items() if k not in ("kwargs",)})
print(json.dumps(rejections, indent=1))
