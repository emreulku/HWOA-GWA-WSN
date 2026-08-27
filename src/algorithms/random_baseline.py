"""
Random Placement Baseline for WSN Target Coverage.

Her iterasyonda tüm sensörler yeniden tamamen rastgele konumlandırılır
ve şimdiye kadar bulunan en iyi konfigürasyon saklanır.

Amaç:
  Meta-sezgisel algoritmaların "körden iyi mi?" sorusunu yanıtlamak.
  Hakem ve okuyucu için alt referans noktası sağlamak.

Not:
  Bu basit baseline, saf rastgele arama gücünü temsil eder.
  Hiçbir öğrenme, bellek veya toplumsal dinamik içermez.
"""

import numpy as np
from environment import WSNEnvironment

def _can_evaluate(env, n=1):
    """Return True when at least n objective evaluations remain."""
    checker = getattr(env, "can_evaluate", None)
    return True if checker is None else bool(checker(n))



def run_random_baseline(env: WSNEnvironment,
                        n_particles: int = 30,   # aynı arayüz için uyumlu parametre adı
                        max_iter: int    = 1000,
                        seed: int        = 0) -> dict:
    """
    Her iterasyonda n_particles rastgele konfigürasyon üretir;
    tüm koşum boyunca bulunan en iyi sonucu döndürür.

    Parameters
    ----------
    env         : WSNEnvironment
    n_particles : her iterasyonda değerlendirilen rastgele aday sayısı
    max_iter    : iterasyon sayısı
    seed        : tekrarlanabilirlik için rastgele tohum

    Returns
    -------
    dict: history, best_positions, best_coverage,
          last_improvement_iter, displacement
    """
    rng = np.random.default_rng(seed)
    dim = env.n_sensors * 2

    best_f   = -1.0
    best_pos = rng.uniform(0, env.area_size, (env.n_sensors, 2))

    history               = []
    last_improvement_iter = max_iter

    for it in range(max_iter):
        if not _can_evaluate(env, n_particles):
            break
        # n_particles aday üret, hepsini değerlendir
        candidates = rng.uniform(0, env.area_size, (n_particles, env.n_sensors, 2))
        fitnesses  = np.array([env.coverage_rate_vectorized(candidates[k])
                               for k in range(n_particles)])

        best_in_iter = int(np.argmax(fitnesses))
        if fitnesses[best_in_iter] > best_f:
            best_f                = fitnesses[best_in_iter]
            best_pos              = candidates[best_in_iter].copy()
            last_improvement_iter = it + 1

        history.append(best_f * 100)

        if best_f >= 1.0:
            history += [100.0] * (max_iter - it - 1)
            last_improvement_iter = it + 1
            break

    return {
        "history":               history,
        "best_positions":        best_pos,
        "best_coverage":         best_f * 100,
        "last_improvement_iter": last_improvement_iter,
        "displacement":          env.total_displacement(best_pos),
    }
