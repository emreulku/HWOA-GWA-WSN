"""
Modified Grey Wolf Algorithm (mGWA) for WSN Target Coverage.
Mirjalili, Mirjalili & Lewis (2014).

Modification vs. canonical GWA:
  Greedy personal-best (pbest) memory added.
  Standard GWA moves wolves directly toward alpha/beta/delta
  without memory; here each wolf also tracks its own best-ever
  position. This reduces variance across runs without altering
  the core alpha-beta-delta leadership hierarchy.
  This version is referred to as mGWA in the paper.

Original algorithm note:

  - A, C vektörleri tam boyutlu (dim-sized)
  - Alpha/beta/delta her iterasyonda tüm popülasyondan yeniden seçilir
  - Tam rastgele başlangıç → geniş arama alanı
  - Greedy pbest hafızası → koşumlar arası varyansı azaltır (mGWA katkısı)
"""

import numpy as np
from environment import WSNEnvironment

def _can_evaluate(env, n=1):
    """Return True when at least n objective evaluations remain."""
    checker = getattr(env, "can_evaluate", None)
    return True if checker is None else bool(checker(n))



def run_gwa(env: WSNEnvironment,
            n_wolves: int = 30,
            max_iter: int = 1000,
            seed: int     = 0) -> dict:

    rng = np.random.default_rng(seed)
    dim = env.n_sensors * 2

    # Tamamen rastgele başlangıç → geniş keşif alanı (population diversity)
    X       = rng.uniform(0, env.area_size, (n_wolves, dim))
    if not _can_evaluate(env, n_wolves):
        raise ValueError("NFE budget is smaller than the mGWA initialization cost.")
    fitness = np.array([env.coverage_rate_vectorized(X[i].reshape(-1, 2))
                        for i in range(n_wolves)])

    # Greedy personal best hafızası
    pbest   = X.copy()
    pbest_f = fitness.copy()

    sorted_idx = np.argsort(fitness)[::-1]
    alpha_pos = pbest[sorted_idx[0]].copy(); alpha_f = pbest_f[sorted_idx[0]]
    beta_pos  = pbest[sorted_idx[1]].copy()
    delta_pos = pbest[sorted_idx[2]].copy()

    history     = []
    last_improvement_iter = max_iter

    for it in range(max_iter):
        a = 2.0 * (1.0 - it / max_iter)   # 2 → 0

        new_X = X.copy()
        for i in range(n_wolves):
            # Tam boyutlu A ve C vektörleri
            A1 = 2*a*rng.random(dim) - a;  C1 = 2*rng.random(dim)
            A2 = 2*a*rng.random(dim) - a;  C2 = 2*rng.random(dim)
            A3 = 2*a*rng.random(dim) - a;  C3 = 2*rng.random(dim)

            D_alpha = np.abs(C1 * alpha_pos - X[i])
            D_beta  = np.abs(C2 * beta_pos  - X[i])
            D_delta = np.abs(C3 * delta_pos - X[i])

            X1 = alpha_pos - A1 * D_alpha
            X2 = beta_pos  - A2 * D_beta
            X3 = delta_pos - A3 * D_delta

            new_X[i] = np.clip((X1 + X2 + X3) / 3.0, 0, env.area_size)

        if not _can_evaluate(env, n_wolves):
            break
        X       = new_X
        fitness = np.array([env.coverage_rate_vectorized(X[i].reshape(-1, 2))
                            for i in range(n_wolves)])

        # Personal best güncelle
        improved          = fitness > pbest_f
        pbest[improved]   = X[improved]
        pbest_f[improved] = fitness[improved]

        # Alpha/beta/delta: personal best'lerden seç (daha stabil)
        sorted_idx = np.argsort(pbest_f)[::-1]
        if pbest_f[sorted_idx[0]] > alpha_f:
            alpha_f   = pbest_f[sorted_idx[0]]
            alpha_pos = pbest[sorted_idx[0]].copy()
            last_improvement_iter = it + 1
        beta_pos  = pbest[sorted_idx[1]].copy()
        delta_pos = pbest[sorted_idx[2]].copy()

        history.append(alpha_f * 100)

        if alpha_f >= 1.0:
            history    += [100.0] * (max_iter - it - 1)
            last_improvement_iter = it + 1
            break

    best_positions = alpha_pos.reshape(-1, 2)
    return {
        "history":        history,
        "best_positions": best_positions,
        "best_coverage":  alpha_f * 100,
        "last_improvement_iter": last_improvement_iter,
        "displacement":   env.total_displacement(best_positions),
    }
