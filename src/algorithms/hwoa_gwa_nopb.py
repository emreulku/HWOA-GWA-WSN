"""
HWOA-GWA-NOPB (protocol v0.4, C2): FULL HWOA-GWA without personal-best memory.

Differences from hwoa_gwa.run_hwoa_gwa(mode="full"):
  - Leaders (alpha, beta, delta) and the spiral reference (alpha) are taken
    from the CURRENT population after each evaluation, not from pbest.
  - A separate best-so-far archive is kept only for reporting
    (best_coverage, history, last_improvement_iter, early stop). The archive
    is never fed back into the search.

Everything else is unchanged: same initialization, same p(t) schedule, same
operators, same random-number draw order per agent, same NFE rules.
"""

import numpy as np
from environment import WSNEnvironment

SPIRAL, HIER = 0, 1


def _can_evaluate(env, n=1):
    checker = getattr(env, "can_evaluate", None)
    return True if checker is None else bool(checker(n))


def run_hwoa_gwa_nopb(env: WSNEnvironment,
                      n_agents: int = 30,
                      max_iter: int = 1000,
                      b: float      = 1.0,
                      p_init: float = 0.8,
                      p_end: float  = 0.2,
                      seed: int     = 0,
                      diag=None) -> dict:
    rng = np.random.default_rng(seed)
    dim = env.n_sensors * 2

    X = rng.uniform(0, env.area_size, (n_agents, dim))
    if not _can_evaluate(env, n_agents):
        raise ValueError("NFE budget is smaller than the initialization cost.")
    fitness = np.array([env.coverage_rate_vectorized(X[i].reshape(-1, 2))
                        for i in range(n_agents)])

    # leaders from the current population
    order = np.argsort(fitness)[::-1]
    alpha_pos, beta_pos, delta_pos = (X[order[0]].copy(), X[order[1]].copy(),
                                      X[order[2]].copy())
    # reporting archive (not used by the search)
    best_f   = fitness[order[0]]
    best_pos = X[order[0]].copy()

    if diag is not None:
        diag.on_init(X.copy(), fitness.copy(), best_f)

    history = []
    last_improvement_iter = max_iter

    for it in range(max_iter):
        a = 2.0 * (1.0 - it / max_iter)
        p_spiral = p_init - (p_init - p_end) * (it / max_iter)
        ops = np.full(n_agents, -1, dtype=np.int8) if diag is not None else None

        new_X = X.copy()
        for i in range(n_agents):
            if rng.random() < p_spiral:
                D = np.abs(alpha_pos - X[i]) + 1e-10
                l = rng.uniform(-1, 1, dim)
                new_X[i] = np.clip(D * np.exp(b * l) * np.cos(2 * np.pi * l) + alpha_pos,
                                   0, env.area_size)
                if ops is not None:
                    ops[i] = SPIRAL
            else:
                A1 = 2*a*rng.random(dim)-a;  C1 = 2*rng.random(dim)
                A2 = 2*a*rng.random(dim)-a;  C2 = 2*rng.random(dim)
                A3 = 2*a*rng.random(dim)-a;  C3 = 2*rng.random(dim)
                X1 = alpha_pos - A1 * np.abs(C1 * alpha_pos - X[i])
                X2 = beta_pos  - A2 * np.abs(C2 * beta_pos  - X[i])
                X3 = delta_pos - A3 * np.abs(C3 * delta_pos - X[i])
                new_X[i] = np.clip((X1 + X2 + X3) / 3.0, 0, env.area_size)
                if ops is not None:
                    ops[i] = HIER

        if not _can_evaluate(env, n_agents):
            break
        X_prev = X if diag is not None else None
        X = new_X
        fitness = np.array([env.coverage_rate_vectorized(X[i].reshape(-1, 2))
                            for i in range(n_agents)])

        order = np.argsort(fitness)[::-1]
        alpha_pos, beta_pos, delta_pos = (X[order[0]].copy(), X[order[1]].copy(),
                                          X[order[2]].copy())

        global_src = -1
        if fitness[order[0]] > best_f:              # archive update (reporting only)
            best_f   = fitness[order[0]]
            best_pos = X[order[0]].copy()
            last_improvement_iter = it + 1
            if diag is not None:
                global_src = int(ops[order[0]])

        if diag is not None:
            # pbest_prev=None -> pbest-improvement fields recorded as NA
            diag.on_iter(it, p_spiral, ops.copy(), X_prev.copy(), X.copy(),
                         fitness.copy(), None, best_f, global_src)

        history.append(best_f * 100)
        if best_f >= 1.0:
            history += [100.0] * (max_iter - it - 1)
            last_improvement_iter = it + 1
            break

    best_positions = best_pos.reshape(-1, 2)
    return {
        "history":        history,
        "best_positions": best_positions,
        "best_coverage":  best_f * 100,
        "last_improvement_iter": last_improvement_iter,
        "displacement":   env.total_displacement(best_positions),
    }
