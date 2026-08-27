"""
Continuous ACO Variant for WSN Target Coverage.
Inspired by Dorigo & Stutzle (2004).

IMPORTANT — This is NOT classical (graph/path-based) ACO.
Classical ACO builds discrete solutions via probabilistic
path construction on a graph. This implementation adapts the
pheromone-guidance concept to a continuous sensor placement
space and is therefore referred to in the paper as:
  "Continuous ACO-inspired sensor perturbation algorithm"
  or "sensor-wise pheromone-guided continuous ACO variant".

Design:
  - Each ant perturbs the current best layout by step_size.
  - Per-sensor pheromone scalars bias which sensors move.
  - Pheromone reinforcement uses the PREVIOUS best position
    (bug fix: avoids zero-delta after global best update).
  - step_size=12.0 ≈ 12% of area_size (100m); chosen by
    sensitivity analysis — see paper Section 5.
"""

import numpy as np
from environment import WSNEnvironment

def _can_evaluate(env, n=1):
    """Return True when at least n objective evaluations remain."""
    checker = getattr(env, "can_evaluate", None)
    return True if checker is None else bool(checker(n))



def run_aco(env: WSNEnvironment,
            n_ants: int = 30,
            max_iter: int = 1000,
            rho: float = 0.1,       # evaporation rate
            alpha: float = 1.0,     # pheromone importance
            step_size: float = 12.0, # max displacement per ant per iter
            seed: int = 0) -> dict:
    """
    Continuous-space ACO where each ant refines the best-known
    sensor placement. Pheromone levels bias ants toward moves that
    previously improved coverage.

    Returns
    -------
    dict with keys: history, best_positions, best_coverage,
                    stable_iter, displacement
    """
    rng = np.random.default_rng(seed)

    # ── Initialise colony around initial sensor positions ─────────────
    best_pos  = env.initial_sensors.copy()
    if not _can_evaluate(env, 1):
        raise ValueError("NFE budget is smaller than the cACO initialization cost.")
    best_f    = env.coverage_rate_vectorized(best_pos)

    # Pheromone matrix: one scalar per sensor (aggregated over dims)
    pheromone = np.ones(env.n_sensors)

    history               = []
    last_improvement_iter = max_iter

    for it in range(max_iter):
        # Keep iterations atomic: do not start an ant generation unless
        # the full colony can be evaluated within the remaining budget.
        if not _can_evaluate(env, n_ants):
            break
        ant_solutions = []
        ant_fitness   = []

        for _ in range(n_ants):
            # Pheromone-weighted probability for each sensor to move
            prob       = (pheromone ** alpha)
            prob       = prob / prob.sum()
            # Each sensor moves with probability proportional to pheromone
            move_mask  = rng.random(env.n_sensors) < prob
            delta      = rng.uniform(-step_size, step_size,
                                     (env.n_sensors, 2))
            delta[~move_mask] = 0.0

            candidate  = np.clip(best_pos + delta, 0, env.area_size)
            f          = env.coverage_rate_vectorized(candidate)
            ant_solutions.append(candidate)
            ant_fitness.append(f)

        best_ant_idx = int(np.argmax(ant_fitness))

        # Evaporate first, then reinforce — order matters
        pheromone = (1 - rho) * pheromone

        # BUG FIX: compute delta BEFORE updating best_pos so the
        # difference is non-zero when a new global best is found.
        # We compare the best ant's solution against the PREVIOUS best_pos.
        prev_best_pos = best_pos.copy()
        if ant_fitness[best_ant_idx] > best_f:
            best_f      = ant_fitness[best_ant_idx]
            best_pos    = ant_solutions[best_ant_idx].copy()
            last_improvement_iter = it + 1

        # Reinforce sensors that actually moved relative to the previous best
        best_delta = np.linalg.norm(
            ant_solutions[best_ant_idx] - prev_best_pos, axis=1)
        pheromone += ant_fitness[best_ant_idx] * (best_delta > 0).astype(float)
        pheromone  = np.clip(pheromone, 0.01, 10.0)

        history.append(best_f * 100)

        if best_f >= 1.0:
            history += [100.0] * (max_iter - it - 1)
            last_improvement_iter = it + 1
            break

    return {
        "history":        history,
        "best_positions": best_pos,
        "best_coverage":  best_f * 100,
        "last_improvement_iter": last_improvement_iter,
        "displacement":   env.total_displacement(best_pos),
    }
