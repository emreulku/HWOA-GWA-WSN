"""
Whale Optimization Algorithm (WOA) for WSN Target Coverage.
Mirjalili & Lewis (2016) — Advances in Engineering Software 95:51-67.

NOTE ON NAMING: This file was previously labelled "WSA" (Whale Swarm
Algorithm, Zhu et al. 2017), which is a different algorithm.  The update
equations here follow WOA (bubble-net shrinking encirclement + spiral).
The hybrid algorithm built on top of this is therefore named WOA-GWA;
within the thesis/paper it is referred to as HWOA-GWA (or HWSA-GWA with
an explicit clarification footnote).

Modifications vs. vanilla WOA:
  - Greedy personal-best memory replaces the random-whale exploration
    branch, improving convergence stability while preserving diversity.
    This is labelled "Modified WOA (mWOA)" in the paper.
  - Fully random initialisation for maximum population diversity.
"""

import numpy as np
from environment import WSNEnvironment

def _can_evaluate(env, n=1):
    """Return True when at least n objective evaluations remain."""
    checker = getattr(env, "can_evaluate", None)
    return True if checker is None else bool(checker(n))



def run_woa(env: WSNEnvironment,
            n_whales: int = 30,
            max_iter: int = 1000,
            b: float      = 1.0,
            seed: int     = 0) -> dict:

    rng = np.random.default_rng(seed)
    dim = env.n_sensors * 2

    # Fully random initialisation → maximum diversity
    X       = rng.uniform(0, env.area_size, (n_whales, dim))
    if not _can_evaluate(env, n_whales):
        raise ValueError("NFE budget is smaller than the mWOA initialization cost.")
    fitness = np.array([env.coverage_rate_vectorized(X[i].reshape(-1, 2))
                        for i in range(n_whales)])

    pbest   = X.copy()
    pbest_f = fitness.copy()

    best_idx = int(np.argmax(fitness))
    leader   = X[best_idx].copy()
    leader_f = fitness[best_idx]

    history               = []
    last_improvement_iter = max_iter

    for it in range(max_iter):
        a = 2.0 * (1.0 - it / max_iter)   # 2 → 0

        new_X = X.copy()
        for i in range(n_whales):
            r1 = rng.random(dim)
            r2 = rng.random(dim)
            A  = 2.0 * a * r1 - a
            C  = 2.0 * r2
            p  = rng.random()

            if p < 0.5:
                if np.mean(np.abs(A)) < 1:
                    # Shrinking encircling
                    D        = np.abs(C * leader - X[i])
                    new_X[i] = np.clip(leader - A * D, 0, env.area_size)
                else:
                    # Memory-guided exploration via personal best
                    D        = np.abs(C * pbest[i] - X[i])
                    new_X[i] = np.clip(pbest[i] - A * D, 0, env.area_size)
            else:
                # Spiral bubble-net
                D        = np.abs(leader - X[i])
                l        = rng.uniform(-1, 1, dim)
                new_X[i] = np.clip(
                    D * np.exp(b * l) * np.cos(2 * np.pi * l) + leader,
                    0, env.area_size)

        if not _can_evaluate(env, n_whales):
            break
        X       = new_X
        fitness = np.array([env.coverage_rate_vectorized(X[i].reshape(-1, 2))
                            for i in range(n_whales)])

        improved          = fitness > pbest_f
        pbest[improved]   = X[improved]
        pbest_f[improved] = fitness[improved]

        best_i = int(np.argmax(pbest_f))
        if pbest_f[best_i] > leader_f:
            leader                = pbest[best_i].copy()
            leader_f              = pbest_f[best_i]
            last_improvement_iter = it + 1

        history.append(leader_f * 100)

        if leader_f >= 1.0:
            history    += [100.0] * (max_iter - it - 1)
            last_improvement_iter = it + 1
            break

    best_positions = leader.reshape(-1, 2)
    return {
        "history":        history,
        "best_positions": best_positions,
        "best_coverage":  leader_f * 100,
        "last_improvement_iter": last_improvement_iter,
        "displacement":   env.total_displacement(best_positions),
    }
