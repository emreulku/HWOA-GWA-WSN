"""G6: C2 (NOPB) robustness checks (protocol v0.4 §7). No equivalence expected.
Usage: python -I g6.py <zip> <new_src> <out_json>
"""
import sys, json, time, platform
from pathlib import Path
import numpy as np

ZIP, NEW, OUT = map(Path, sys.argv[1:4])
sys.path.insert(0, str(Path(__file__).parent))
import revkit as rk
orig_src, g1 = rk.verify_sources(ZIP, NEW)
rk.init_tree(NEW)
mod = rk._T["nopb"]

# RNG call-sequence spy (values unchanged)
class Spy:
    def __init__(self, g): self.g, self.log = g, []
    def __getattr__(self, name):
        f = getattr(self.g, name)
        def w(*a, **k):
            size = a[-1] if (name == "uniform" and len(a) == 3) or (name == "random" and a) else None
            self.log.append((name, size)); return f(*a, **k)
        return w
spies = []; _real = np.random.default_rng
proxy = type(sys)("np_proxy"); proxy.__dict__.update({k: getattr(np, k) for k in dir(np) if not k.startswith("__")})
proxy.random = type(sys)("rp"); proxy.random.default_rng = lambda s: (spies.append(Spy(_real(s))) or spies[-1])

def branches(log):
    seq, out, i = log[1:], [], 0
    while i < len(seq):
        assert seq[i] == ("random", None)
        if seq[i + 1][0] == "uniform": out.append(0); i += 2
        else: out.append(1); i += 7
    return np.array(out).reshape(-1, rk.POP)

checks = []; t0 = time.time()
for sc in ("S1", "S2", "S3"):
    for trial in range(3):
        base = dict(sc=sc, env_seed=42, trial=trial, algo="NOPB", mode="full")
        mod.np = proxy; spies.clear()
        on = rk.run_one(dict(base, diag=True))
        spy_ops = branches(spies[0].log)
        mod.np = np
        off = rk.run_one(dict(base, diag=False))
        full = rk.run_one(dict(sc=sc, env_seed=42, trial=trial, algo="HWOA-GWA", mode="full"))
        rows = on["diag"][1:]
        ops = np.array([x["ops"] for x in rows])
        hist = on["obs_raw"]
        c = dict(sc=sc, trial=trial)
        c["reported_equals_archive"] = abs(on["coverage"] - on["obs_raw"][-1]) <= 1e-9 \
            and np.array_equal(on["natural_hist"], on["obs_best"][1:]) \
            and float(np.abs(on["natural_raw"] - on["obs_raw"][1:]).max(initial=0)) <= 1e-9
        c["best_so_far_non_decreasing"] = bool((np.diff(hist) >= -1e-12).all())
        c["nfe_rules"] = on["nfe_actual"] == rk.POP * (on["n_gen"] + 1) and on["nfe_actual"] <= rk.MAX_NFE \
            and (on["stop_reason"] == "full_coverage") == (on["coverage"] >= 100.0)
        c["pbest_fields_NA"] = all(x["imp"] is None and x["delta"] is None for x in rows)
        inc = np.diff(np.r_[on["diag"][0]["best"], [x["best"] for x in rows]]) > 0
        gs = np.array([x["gsrc"] for x in rows])
        c["global_source_consistent"] = bool(((gs >= 0) == inc).all() and set(gs[gs >= 0]) <= {0, 1})
        c["branch_matches_rng_sequence"] = bool(ops.shape == spy_ops.shape and (ops == spy_ops).all())
        c["diag_on_equals_off"] = all(on[f] == off[f] for f in ("coverage", "nfe_actual", "last_imp", "stop_reason", "n_gen")) \
            and np.array_equal(on["obs_raw"], off["obs_raw"])
        c["differs_from_FULL"] = bool(not np.array_equal(on["obs_raw"], full["obs_raw"]))  # sanity: a distinct variant
        checks.append(c)

keys = [k for k in checks[0] if k not in ("sc", "trial")]
passed = all(all(c[k] for k in keys if k != "differs_from_FULL") for c in checks)
rep = dict(gate="G6", protocol="v0.4", passed=passed,
           note="Gate runs are used only for code verification, not performance analysis. "
                "differs_from_FULL is a descriptive sanity flag, not a pass criterion.",
           zip_sha256=g1["zip_sha256"], changed_files=g1["changed_files"], added_files=g1["added_files"], extra_files=g1["extra_files"],
           new_tree_hashes=g1["new_tree_hashes"], checks=checks, executions=len(checks) * 3,
           versions=dict(python=platform.python_version(), numpy=np.__version__),
           wall_time_s=round(time.time() - t0, 1))
OUT.write_text(json.dumps(rep, indent=2, default=lambda o: o.item() if hasattr(o, "item") else str(o)))
print(json.dumps(dict(passed=passed, checks=checks), default=lambda o: o.item() if hasattr(o, "item") else str(o), indent=0))
