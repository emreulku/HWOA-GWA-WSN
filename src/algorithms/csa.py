"""
Cuckoo Search Algorithm (CSA) — Düzeltilmiş versiyon.

Sorun: step_scale=0.1 seyrek ağlarda (S2) çok küçük kalıyor,
       sensörler neredeyse hiç hareket etmiyor.

Düzeltmeler:
  - Adaptif step_scale: erken iterasyonlarda büyük, sonra küçülür
  - Lévy adımı alan boyutuna (area_size) göre normalize edilir
  - Tamamen rastgele başlangıç
"""

import math
import numpy as np
from environment import WSNEnvironment

def _can_evaluate(env, n=1):
    """Return True when at least n objective evaluations remain."""
    checker = getattr(env, "can_evaluate", None)
    return True if checker is None else bool(checker(n))



def _levy(dim: int, rng: np.random.Generator, beta: float = 1.5) -> np.ndarray:
    sigma = (math.gamma(1+beta) * math.sin(math.pi*beta/2) /
             (math.gamma((1+beta)/2) * beta * 2**((beta-1)/2))) ** (1/beta)
    u = rng.normal(0, sigma, dim)
    v = rng.normal(0, 1,     dim)
    return u / (np.abs(v) ** (1/beta))


def run_csa(env: WSNEnvironment,
            n_nests: int    = 30,
            max_iter: int   = 1000,
            pa: float       = 0.25,
            seed: int       = 0) -> dict:

    rng = np.random.default_rng(seed)
    dim = env.n_sensors * 2

    # Tamamen rastgele başlangıç
    nests   = rng.uniform(0, env.area_size, (n_nests, dim))
    if not _can_evaluate(env, n_nests):
        raise ValueError("NFE budget is smaller than the CSA initialization cost.")
    fitness = np.array([env.coverage_rate_vectorized(nests[i].reshape(-1, 2))
                        for i in range(n_nests)])

    best_idx = int(np.argmax(fitness))
    best_pos = nests[best_idx].copy()
    best_f   = fitness[best_idx]

    history     = []
    last_improvement_iter = max_iter

    for it in range(max_iter):
        n_abandon = max(1, int(pa * n_nests))
        required_nfe = 1 + n_abandon
        # Keep a CSA iteration atomic: one Levy evaluation plus all
        # abandoned-nest re-evaluations must fit in the remaining budget.
        if not _can_evaluate(env, required_nfe):
            break
        # Adaptif adım boyutu: başta büyük, giderek küçülür
        step_scale = env.area_size * 0.1 * (1 - it / max_iter) + 0.5

        # Lévy uçuşu
        i        = rng.integers(0, n_nests)
        levy     = _levy(dim, rng)
        new_nest = np.clip(
            nests[i] + step_scale * levy * (nests[i] - best_pos),
            0, env.area_size)
        new_f = env.coverage_rate_vectorized(new_nest.reshape(-1, 2))

        j = rng.integers(0, n_nests)
        if new_f > fitness[j]:
            nests[j]   = new_nest
            fitness[j] = new_f

        # En kötü pa oranını terk et
        worst_idx = np.argsort(fitness)[:n_abandon]
        for k in worst_idx:
            r1, r2   = rng.integers(0, n_nests, 2)
            nests[k] = np.clip(
                nests[k] + rng.random(dim) * (nests[r1] - nests[r2]),
                0, env.area_size)
            fitness[k] = env.coverage_rate_vectorized(nests[k].reshape(-1, 2))

        cur_best = int(np.argmax(fitness))
        if fitness[cur_best] > best_f:
            best_f      = fitness[cur_best]
            best_pos    = nests[cur_best].copy()
            last_improvement_iter = it + 1

        history.append(best_f * 100)
        if best_f >= 1.0:
            history    += [100.0] * (max_iter - it - 1)
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
