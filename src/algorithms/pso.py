"""
Particle Swarm Optimization (PSO) for WSN Target Coverage.
Kennedy & Eberhart (1995).
Each particle encodes the positions of all n_sensors sensors
as a flat vector of length 2*n_sensors.
"""

import numpy as np
from environment import WSNEnvironment

def _can_evaluate(env, n=1):
    """Return True when at least n objective evaluations remain."""
    checker = getattr(env, "can_evaluate", None)
    return True if checker is None else bool(checker(n))



def run_pso(env: WSNEnvironment,
            n_particles: int = 30,
            max_iter: int = 1000,
            w: float = 0.7,
            c1: float = 1.5,
            c2: float = 1.5,
            seed: int = 0) -> dict:
    """
    Parameters
    ----------
    env        : WSNEnvironment instance
    n_particles: swarm size
    max_iter   : number of iterations
    w          : inertia weight
    c1         : cognitive (personal best) coefficient
    c2         : social (global best) coefficient
    seed       : random seed for reproducibility

    Returns
    -------
    dict with keys:
        history          : list of best coverage at each iteration
        best_positions   : (n_sensors, 2) array of final sensor positions
        best_coverage    : float — maximum coverage achieved
        stable_iter      : iteration at which best coverage stopped improving
        displacement     : total displacement from initial positions
    """
    rng  = np.random.default_rng(seed)
    dim  = env.n_sensors * 2

    # ── Initialise swarm — FULL RANDOM (uniform across search space) ─
    # Previously half the particles were seeded near initial_sensors,
    # giving PSO an unfair head-start over other algorithms.
    # All algorithms now share the same full-random initialisation policy.
    X = rng.uniform(0, env.area_size, (n_particles, dim))

    # Velocity clamp: max displacement per step = 20 % of area
    v_max = env.area_size * 0.20
    V     = rng.uniform(-v_max * 0.1, v_max * 0.1, X.shape)
    if not _can_evaluate(env, n_particles):
        raise ValueError("NFE budget is smaller than the PSO initialization cost.")
    pbest    = X.copy()
    pbest_f  = np.array([env.coverage_rate_vectorized(X[i].reshape(-1, 2))
                         for i in range(n_particles)])

    gbest_idx = np.argmax(pbest_f)
    gbest     = pbest[gbest_idx].copy()
    gbest_f   = pbest_f[gbest_idx]

    history               = []
    last_improvement_iter = max_iter

    for it in range(max_iter):
        r1 = rng.uniform(0, 1, X.shape)
        r2 = rng.uniform(0, 1, X.shape)

        V  = w * V + c1 * r1 * (pbest - X) + c2 * r2 * (gbest - X)
        V  = np.clip(V, -v_max, v_max)          # velocity clamp
        X  = np.clip(X + V, 0, env.area_size)

        if not _can_evaluate(env, n_particles):
            break
        fitness = np.array([env.coverage_rate_vectorized(X[i].reshape(-1, 2))
                            for i in range(n_particles)])

        # Update personal bests
        improved = fitness > pbest_f
        pbest[improved]   = X[improved]
        pbest_f[improved] = fitness[improved]

        # Update global best
        best_idx = np.argmax(pbest_f)
        if pbest_f[best_idx] > gbest_f:
            gbest_f               = pbest_f[best_idx]
            gbest                 = pbest[best_idx].copy()
            last_improvement_iter = it + 1

        history.append(gbest_f * 100)

        if gbest_f >= 1.0:
            history += [100.0] * (max_iter - it - 1)
            last_improvement_iter = it + 1
            break

    best_positions = gbest.reshape(-1, 2)
    return {
        "history":        history,
        "best_positions": best_positions,
        "best_coverage":  gbest_f * 100,
        "last_improvement_iter": last_improvement_iter,
        "displacement":   env.total_displacement(best_positions),
    }
