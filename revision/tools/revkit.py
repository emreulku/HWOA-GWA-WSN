"""
revkit: revision-experiment helpers (protocol v0.3).

Kept outside the algorithm source tree. A worker process imports exactly one
source tree (submitted original or revision copy), selected via `init_tree`.
"""
import hashlib, os, sys, time
from pathlib import Path
import numpy as np

POP = 25
MAX_NFE = 6250
SCEN = {"S1": (100, 75), "S2": (50, 75), "S3": (200, 120)}

_T = {}  # per-process tree handles


def sha256_file(p):
    with open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def tree_hashes(src):
    src = Path(src)
    return {str(p.relative_to(src)): sha256_file(p) for p in sorted(src.rglob("*.py"))}


EXPECTED_ZIP_SHA256 = "28965848c11fe61dc15a2559cdf8c141d68d84dc4a53104f3856fe24b84d8f02"
ALLOWED_CHANGES = {"algorithms/hwoa_gwa.py", "algorithms/hwoa_gwa_nopb.py"}


def verify_sources(zip_path, new_src, allowed=ALLOWED_CHANGES):
    """G1 (mandatory, stops on failure). Returns (orig_src, info)."""
    import tempfile, zipfile
    zsha = sha256_file(zip_path)
    if zsha != EXPECTED_ZIP_SHA256:
        raise SystemExit(f"G1 FAIL: ZIP sha256 {zsha} != expected")
    tmp = Path(tempfile.mkdtemp(prefix="orig_"))
    zipfile.ZipFile(zip_path).extractall(tmp)
    orig_src = tmp / "HWOA-GWA-WSN-main" / "src"
    h_o, h_n = tree_hashes(orig_src), tree_hashes(new_src)
    extra = sorted(set(h_n) - set(h_o) - set(allowed))
    missing = sorted(set(h_o) - set(h_n))
    changed = sorted(k for k in set(h_o) & set(h_n) if h_o[k] != h_n[k])
    if extra or missing or not set(changed) <= set(allowed):
        raise SystemExit(f"G1 FAIL: extra={extra} missing={missing} changed={changed}")
    added = sorted(set(h_n) - set(h_o))           # allowed new files (e.g. NOPB)
    return orig_src, dict(zip_sha256=zsha, changed_files=changed, added_files=added, extra_files=extra,
                          orig_tree_hashes=h_o, new_tree_hashes=h_n)


def init_tree(src):
    """Pool initializer: bind this process to one source tree."""
    sys.path.insert(0, str(src))
    import environment, statistical_experiment
    from algorithms import hwoa_gwa, gwa, pso, aco, woa, csa, random_baseline
    _T.update(src=str(src), env=environment, se=statistical_experiment,
              hwoa=hwoa_gwa, gwa=gwa,
              fn={"Random": random_baseline.run_random_baseline, "PSO": pso.run_pso,
                  "cACO": aco.run_aco, "mWOA": woa.run_woa, "mGWA": gwa.run_gwa,
                  "CSA": csa.run_csa, "HWOA-GWA": hwoa_gwa.run_hwoa_gwa})
    try:                                   # only present in the revision tree
        from algorithms import hwoa_gwa_nopb
        _T["nopb"] = hwoa_gwa_nopb
        _T["fn"]["NOPB"] = hwoa_gwa_nopb.run_hwoa_gwa_nopb
    except ImportError:
        _T["nopb"] = None


# ── NFE observer (subclass of the tree's own counting wrapper) ──────────
def make_observer(raw_env):
    base = _T["se"].NFECountingEnv

    class ObservedEnv(base):
        def __init__(self, env, max_nfe):
            super().__init__(env, max_nfe)
            self.evals = []

        def coverage_rate_vectorized(self, pos):
            f = super().coverage_rate_vectorized(pos)
            self.evals.append(f)
            return f

    return ObservedEnv(raw_env, MAX_NFE)


# ── C3 diagnostics recorder ─────────────────────────────────────────────
class Recorder:
    def __init__(self, raw_env):
        self.targets = raw_env.targets
        self.r = raw_env.sensing_radius
        self.m = raw_env.n_targets
        self.n = raw_env.n_sensors
        self.rows = []
        self.phen_time = 0.0

    def _masks(self, P):
        t0 = time.perf_counter()
        S = P.reshape(P.shape[0], -1, 2)                       # N x n x 2
        d = np.linalg.norm(S[:, None, :, :] - self.targets[None, :, None, :], axis=3)
        M = (d <= self.r).any(axis=2)                          # N x m
        N = M.shape[0]
        c = M.sum(axis=0)
        ham = (c * (N - c)).sum() / (N * (N - 1) / 2) / self.m
        self.phen_time += time.perf_counter() - t0
        return M, float(ham)

    def _geno(self, P):
        return float(np.linalg.norm(P - P.mean(0), axis=1).mean() / np.sqrt(self.n))

    def on_init(self, X, fit, alpha_f):
        _, ham = self._masks(X)
        self.rows.append(dict(it=-1, p=np.nan, ops=None, step=None, imp=None,
                              delta=None, gsrc=-1, Dg=self._geno(X), Dp=ham,
                              best=round(alpha_f * self.m)))

    def on_iter(self, it, p, ops, Xprev, X, fit, pbest_prev, alpha_f, gsrc):
        step = np.linalg.norm((X - Xprev).reshape(X.shape[0], -1, 2), axis=2).mean(1)
        if pbest_prev is None:                       # NOPB: not applicable
            imp = None; delta = None
        else:
            imp = fit > pbest_prev
            delta = np.maximum(0.0, fit - pbest_prev) * self.m
        _, ham = self._masks(X)
        self.rows.append(dict(it=it, p=p, ops=ops, step=step, imp=imp, delta=delta,
                              gsrc=gsrc, Dg=self._geno(X), Dp=ham,
                              best=round(alpha_f * self.m)))


# ── explicit method table (protocol v0.5 §3, §8) ───────────────────────
# Population keyword, initialization NFE cost and per-iteration NFE cost are
# copied from the submitted runner (statistical_experiment._run_one).
_PA_CSA = 0.25
BASE = {   # fn key, pop kw, init cost, iter cost
    "Random":   ("Random",   "n_particles", 0,   POP),
    "PSO":      ("PSO",      "n_particles", POP, POP),
    "cACO":     ("cACO",     "n_ants",      1,   POP),
    "mWOA":     ("mWOA",     "n_whales",    POP, POP),
    "mGWA":     ("mGWA",     "n_wolves",    POP, POP),
    "CSA":      ("CSA",      "n_nests",     POP, 1 + max(1, int(_PA_CSA * POP))),
    "HWOA-GWA": ("HWOA-GWA", "n_agents",    POP, POP),
    "NOPB":     ("NOPB",     "n_agents",    POP, POP),
}
# protocol method name -> (base, extra kwargs)
METHODS = {
    "Random": ("Random", {}), "PSO": ("PSO", {}), "cACO": ("cACO", {}),
    "mWOA": ("mWOA", {}), "mGWA": ("mGWA", {}), "CSA": ("CSA", {}),
    "FULL": ("HWOA-GWA", {}),                                    # submitted defaults 0.8 -> 0.2
    "SPIRAL": ("HWOA-GWA", {"mode": "spiral"}),
    "HIER": ("HWOA-GWA", {"mode": "hier"}),
    "CONST05": ("HWOA-GWA", {"p_init": 0.5, "p_end": 0.5}),
    "NOPB": ("NOPB", {}),
}
GRID_VALUES = (0.2, 0.5, 0.8)


def resolve(spec):
    """Return (base, extra kwargs) for a spec. Unknown names are rejected."""
    m = spec["method"]
    if m in METHODS:
        base, extra = METHODS[m]
        return base, dict(extra)
    if m.startswith("G(") and m.endswith(")"):                   # grid cell G(pi,pe)
        pi, pe = (float(x) for x in m[2:-1].split(","))
        if pi not in GRID_VALUES or pe not in GRID_VALUES:
            raise ValueError(f"grid cell outside protocol grid: {m}")
        return "HWOA-GWA", {"p_init": pi, "p_end": pe}
    if m == "HWOA-GWA" and "mode" in spec:                      # gate-compatibility path
        extra = {} if spec["mode"] == "full" else {"mode": spec["mode"]}
        if spec.get("pass_p"):
            extra.update(p_init=spec["p_init"], p_end=spec["p_end"])
        return "HWOA-GWA", extra
    raise ValueError(f"unknown method: {m!r}")


def run_one(spec):
    """spec: dict(sc, env_seed, trial, method, [diag]). Legacy key 'algo' is
    accepted as 'method' (gate scripts)."""
    spec = dict(spec)
    if "method" not in spec:
        spec["method"] = spec.pop("algo")
    base, extra = resolve(spec)
    fkey, popkw, init_cost, iter_cost = BASE[base]
    fn = _T["fn"].get(fkey)
    if fn is None:
        raise RuntimeError(f"{fkey} is not available in this source tree")
    if spec.get("diag") and base not in ("HWOA-GWA", "NOPB"):
        raise ValueError(f"diagnostics are defined only for HWOA-GWA variants, not {spec['method']}")

    env_mod = _T["env"]
    n_s, n_t = SCEN[spec["sc"]]
    raw = env_mod.WSNEnvironment(n_sensors=n_s, n_targets=n_t, area_size=100.0,
                                 sensing_radius=5.0, seed=spec["env_seed"])
    env = make_observer(raw)
    max_iter = max(0, (MAX_NFE - init_cost) // iter_cost)
    seed = spec["trial"] + spec["env_seed"] * 1000
    rec = Recorder(raw) if spec.get("diag") else None

    kw = {popkw: POP, "max_iter": max_iter, "seed": seed, **extra}
    if rec is not None:
        kw["diag"] = rec
    t0 = time.perf_counter()
    res = fn(env, **kw)
    dt = time.perf_counter() - t0

    ev = np.array(env.evals)
    n_gen = (len(ev) - init_cost) // iter_cost
    aligned = (len(ev) - init_cost) % iter_cost == 0
    runmax = np.maximum.accumulate(ev)
    first = init_cost if init_cost > 0 else iter_cost
    obs_nfe = np.arange(first, init_cost + iter_cost * n_gen + 1, iter_cost)
    obs_raw = runmax[obs_nfe - 1] * 100.0
    obs_best = np.rint(runmax[obs_nfe - 1] * n_t).astype(int)
    natural_raw = np.array(res["history"][:n_gen], dtype=float)
    natural = np.rint(natural_raw / 100 * n_t).astype(int)

    out = dict(key=(spec["sc"], spec["env_seed"], spec["method"], spec.get("mode", "full"),
                    spec["trial"], extra.get("p_init"), extra.get("p_end")),
               method=spec["method"], base=base, call=dict(fn=fn.__module__ + "." + fn.__name__,
                                                           kwargs={k: v for k, v in kw.items() if k != "diag"}),
               coverage=res["best_coverage"], disp=res["displacement"],
               nfe_actual=env.nfe, last_imp=res.get("last_improvement_iter", max_iter),
               max_iter_used=max_iter, init_cost=init_cost, iter_cost=iter_cost,
               stop_reason=("full_coverage" if res["best_coverage"] >= 100.0
                            else "budget_or_schedule"),
               n_gen=n_gen, nfe_aligned=aligned, obs_nfe=obs_nfe, obs_best=obs_best,
               obs_raw=obs_raw, natural_hist=natural, natural_raw=natural_raw,
               padded_len=len(res["history"]), history=list(res["history"]), runtime=dt)
    if rec is not None:
        out["diag"] = rec.rows
        out["phen_time"] = rec.phen_time
    return out


def env_versions():
    import platform, numpy, scipy, pandas
    return dict(python=platform.python_version(), numpy=numpy.__version__,
                scipy=scipy.__version__, pandas=pandas.__version__)
