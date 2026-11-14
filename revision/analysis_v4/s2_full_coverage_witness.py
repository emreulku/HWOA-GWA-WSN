"""Independent post-hoc check: is CR = 1 attainable in the S2 instances (N=50, M=75)?
Witness: maximum matching of target pairs at distance <= 2r; one sensor at each pair midpoint,
one sensor on each unmatched target, remaining sensors at (0,0). Verified with the original
coverage function. This is an existence witness, not a minimum-sensor claim.
Usage: python -I s2_full_coverage_witness.py <repo_root_with_src> <out_dir>
Writes: s2_full_coverage_witness.csv (summary) and s2_witness_coordinates.csv
        (env_seed, kind, x, y) for independent re-checking."""
import sys, csv
from pathlib import Path
import numpy as np, networkx as nx
sys.path.insert(0, sys.argv[1])
from src.environment import WSNEnvironment

out = Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
rows, coords = [], []
for seed in [42, 17, 99] + list(range(1001, 1011)):
    env = WSNEnvironment(50, 75, seed=seed)
    T, r = env.targets, env.sensing_radius
    G = nx.Graph(); G.add_nodes_from(range(env.n_targets))
    G.add_edges_from((i, j) for i in range(env.n_targets) for j in range(i + 1, env.n_targets)
                     if np.linalg.norm(T[i] - T[j]) <= 2 * r)
    m = nx.max_weight_matching(G, maxcardinality=True)
    used = {k for e in m for k in e}
    S = [(T[i] + T[j]) / 2 for i, j in m] + [T[k] for k in range(env.n_targets) if k not in used]
    need = len(S)
    assert need <= env.n_sensors, f"env {seed}: witness needs {need} > {env.n_sensors} sensors"
    S = np.array(S + [np.zeros(2)] * (env.n_sensors - need))
    assert S.shape == (env.n_sensors, 2)
    assert np.isfinite(S).all()
    assert ((S >= 0) & (S <= env.area_size)).all()
    cr = env.coverage_rate_vectorized(S)
    assert cr == 1.0, f"env {seed}: CR = {cr}"
    rows.append(dict(env_seed=seed, pairs=len(m), sensors_needed=need, cr=cr))
    coords += [dict(env_seed=seed, kind="target", x=x, y=y) for x, y in T]
    coords += [dict(env_seed=seed, kind="sensor", x=x, y=y) for x, y in S]

for name, data in (("s2_full_coverage_witness.csv", rows), ("s2_witness_coordinates.csv", coords)):
    with open(out / name, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=data[0].keys()); w.writeheader(); w.writerows(data)
print(f"{len(rows)} instances, all CR = 1; sensors needed {min(r['sensors_needed'] for r in rows)}"
      f"-{max(r['sensors_needed'] for r in rows)}")
