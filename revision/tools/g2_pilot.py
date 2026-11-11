"""G2 pilot (protocol v0.3 §7): 12 runs, revision tree, diagnostics on.
Usage: python -I g2_pilot.py <zip> <new_src> <reference_csv> <out_json>
"""
import sys, json, time, platform, zipfile, tempfile, hashlib
from pathlib import Path
import numpy as np, pandas as pd

ZIP, NEW, REF, OUT = map(Path, sys.argv[1:5])
sys.path.insert(0, str(Path(__file__).parent))
import revkit as rk

# ── G1 (mandatory, stops on failure) ──
orig_src, g1 = rk.verify_sources(ZIP, NEW)
changed = g1["changed_files"]; zip_sha = g1["zip_sha256"]; h_new = g1["new_tree_hashes"]
ref_sha = rk.sha256_file(REF)

rk.init_tree(NEW)

# ── independent branch check: RNG call-sequence spy ─────────────────────
class Spy:
    def __init__(self, g): self.g, self.log = g, []
    def __getattr__(self, name):
        f = getattr(self.g, name)
        def w(*a, **k):
            size = k.get("size", a[-1] if (name == "uniform" and len(a) == 3) or (name == "random" and a) else None)
            self.log.append((name, size))
            return f(*a, **k)
        return w

spies = []
_real = np.random.default_rng
def spy_rng(seed):
    s = Spy(_real(seed)); spies.append(s); return s
rk._T["hwoa"].np = type(sys)("np_proxy")
rk._T["hwoa"].np.__dict__.update({k: getattr(np, k) for k in dir(np) if not k.startswith("__")})
rk._T["hwoa"].np.random = type(sys)("random_proxy")
rk._T["hwoa"].np.random.default_rng = spy_rng

def branches_from_log(log, n_agents, mode):
    """Reconstruct executed branch per agent from the draw sequence (skip init draw)."""
    seq = log[1:]  # first call = initial population uniform
    out, i = [], 0
    while i < len(seq):
        name, size = seq[i]
        if mode == "full":
            assert name == "random" and size is None, seq[i]
            nxt = seq[i + 1][0]
            if nxt == "uniform": out.append(0); i += 2
            else: out.append(1); i += 7
        elif mode == "spiral":
            assert name == "uniform"; out.append(0); i += 1
        else:
            assert name == "random"; out.append(1); i += 6
    return np.array(out).reshape(-1, n_agents)

configs = [("FULL", dict(mode="full", pass_p=True, p_init=0.8, p_end=0.2)),
           ("SPIRAL", dict(mode="spiral")),
           ("HIER", dict(mode="hier")),
           ("CONST05", dict(mode="full", pass_p=True, p_init=0.5, p_end=0.5))]
ref = pd.read_csv(REF, encoding="utf-8-sig")

checks, desc, runs = [], {}, []
t_all = time.perf_counter()
for name, cfg in configs:
    for trial in range(3):
        spies.clear()
        spec = dict(sc="S1", env_seed=42, trial=trial, algo="HWOA-GWA", diag=True, **cfg)
        r = rk.run_one(spec)
        rows = r["diag"]; it_rows = rows[1:]
        ops = np.array([x["ops"] for x in it_rows])
        mode = cfg["mode"]
        spy_ops = branches_from_log(spies[0].log, rk.POP, mode)
        c = {}
        c["a_branch_matches_rng_sequence"] = bool(ops.shape == spy_ops.shape and (ops == spy_ops).all())
        c["b_25_evaluations_per_iteration"] = bool((r["nfe_actual"] - rk.POP) % rk.POP == 0
                                                  and r["n_gen"] == len(it_rows)
                                                  and (ops >= 0).all() and ops.shape[1] == rk.POP)
        if name == "SPIRAL": c["c_mode_ops"] = bool((ops == 0).all())
        elif name == "HIER": c["c_mode_ops"] = bool((ops == 1).all())
        else: c["c_mode_ops"] = bool(set(np.unique(ops)) <= {0, 1})
        vals = np.concatenate([[x["Dg"], x["Dp"]] for x in rows] +
                              [np.r_[x["step"], x["delta"]] for x in it_rows])
        c["d_no_nan"] = bool(np.isfinite(vals).all())
        c["e_hist_consistent"] = bool(np.array_equal(r["natural_hist"], r["obs_best"][1:])
                                      and np.abs(r["natural_raw"] - r["obs_raw"][1:]).max(initial=0) <= 1e-9
                                      and r["obs_best"][0] == rows[0]["best"]
                                      and r["padded_len"] == r["max_iter_used"]
                                      and r["nfe_actual"] == rk.POP * (r["n_gen"] + 1))
        c["f_phen_time_measured"] = r["phen_time"] > 0
        # reference match (submitted results) for configurations that exist there
        if name in ("FULL", "SPIRAL", "HIER"):
            if name == "FULL":
                q = ref[(ref.sc_tag == "S1") & (ref.algo == "HWOA-GWA") & (ref.ablation == "full")]
            else:
                q = ref[(ref.sc_tag == "S1_abl") & (ref.ablation == name.lower())]
            q = q[(q.env_seed == 42) & (q.trial == trial)].iloc[0]
            c["ref_match_submitted"] = bool(abs(q.coverage - r["coverage"]) <= 1e-9
                                            and q.nfe_actual == r["nfe_actual"]
                                            and q.last_imp == r["last_imp"]
                                            and q.stop_reason == r["stop_reason"])
        checks.append(dict(config=name, trial=trial, **c))
        runs.append((name, r))

# descriptive: spiral fraction vs p(t) in 10 NFE bins (FULL, CONST05)
for name in ("FULL", "CONST05"):
    pin, pen = (0.8, 0.2) if name == "FULL" else (0.5, 0.5)
    sel = [r for n, r in runs if n == name]
    rows_out = []
    for b in range(10):
        lo, hi = b * 25, (b + 1) * 25          # 249 iterations ~ 10 bins of 25
        k = n = 0; ps = []
        for r in sel:
            for x in r["diag"][1:]:
                if lo <= x["it"] < hi:
                    k += int((x["ops"] == 0).sum()); n += len(x["ops"]); ps.append(x["p"])
        if n == 0: continue
        pbar = float(np.mean(ps)); se = np.sqrt(pbar * (1 - pbar) / n)
        rows_out.append(dict(bin=b, n=n, spiral_frac=round(k / n, 4), p_mean=round(pbar, 4),
                             inside_95=bool(abs(k / n - pbar) <= 1.96 * se)))
    desc[f"spiral_fraction_{name}"] = rows_out

rt = {n: [] for n, _ in configs}; pt = {n: [] for n, _ in configs}
for n, r in runs: rt[n].append(r["runtime"]); pt[n].append(r["phen_time"])
desc["runtime_s_mean"] = {n: round(float(np.mean(v)), 3) for n, v in rt.items()}
desc["phenotypic_time_share"] = {n: round(float(np.sum(pt[n]) / np.sum(rt[n])), 3) for n in rt}
desc["Dg_init_m (expected ~40 for uniform init)"] = round(float(np.mean([r["diag"][0]["Dg"] for _, r in runs])), 2)

mandatory = ["a_branch_matches_rng_sequence", "b_25_evaluations_per_iteration", "c_mode_ops",
             "d_no_nan", "e_hist_consistent", "f_phen_time_measured"]
passed = all(all(c[k] for k in mandatory) for c in checks)
report = dict(gate="G2", protocol="v0.3", passed=passed,
              note="Pilot results are used only for code verification and are not part of any performance analysis.",
              zip_sha256=zip_sha, reference_csv_sha256=ref_sha, changed_files_vs_zip=changed,
              added_files=g1["added_files"], extra_files=g1["extra_files"],
              revision_tree_hashes=h_new,
              versions=dict(python=platform.python_version(), numpy=np.__version__, pandas=pd.__version__),
              checks=checks, descriptive=desc,
              wall_time_s=round(time.perf_counter() - t_all, 1))
OUT.write_text(json.dumps(report, indent=2, default=str))
print(json.dumps(dict(passed=passed, checks=checks, descriptive=desc), indent=1, default=str))
