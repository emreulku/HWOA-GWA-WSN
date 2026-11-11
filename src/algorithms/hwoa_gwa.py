"""
HWOA-GWA: Hibrit Balina Optimizasyonu - Gri Kurt Algoritması
(Hybrid Modified Whale Optimization - Grey Wolf Algorithm)
=======================================================

Motivasyon:
  - mWOA tek başına: yavaş yakınsama (spiral adımı büyük boyutlarda
    etkisizleşir, lider çeşitliliği yetersiz)
  - GWA tek başına: yüksek varyans (alfa seçimi seed'e duyarlı,
    keşif/sömürü dengesi bozuk)

HWOA-GWA çözümü:
  ┌─────────────────────────────────────────────────────────┐
  │  GWA Katmanı   → α/β/δ hiyerarşisi ile yön belirler    │
  │  mWOA Katmanı  → spiral mekanizması ile hareket eder    │
  │  Adaptif p(t)  → erken=keşif (spiral), geç=sömürü(GWA) │
  └─────────────────────────────────────────────────────────┘

Parametreler:
  b      : spiral logaritma sabiti (WOA'dan)
  p_init : başlangıç spiral olasılığı (yüksek = daha fazla keşif)
  p_end  : bitiş spiral olasılığı (düşük = daha fazla sömürü)

Ablation modu:
  mode="full"    → tam hibrit (hem spiral hem hiyerarşi)
  mode="spiral"  → sadece mWOA spirali, alfa liderine yönelik
  mode="hier"    → sadece GWA hiyerarşisi, doğrusal çekim

Revizyon (protokol v0.3, C1/C3):
  - p_init / p_end runner tarafından geçirilebilir (varsayılanlar değişmedi).
  - İsteğe bağlı `diag` kaydedici. diag=None iken kod yolu gönderilmiş
    sürümle (3e15fcb) aynıdır. Kaydedici yalnızca algoritmanın zaten
    hesapladığı dizilerin kopyalarını okur: ek amaç fonksiyonu çağrısı ve
    ek rastgele sayı çekimi yoktur.
"""

import numpy as np

SPIRAL, HIER = 0, 1  # diag kayıtlarında operatör kodları
from environment import WSNEnvironment

def _can_evaluate(env, n=1):
    """Return True when at least n objective evaluations remain."""
    checker = getattr(env, "can_evaluate", None)
    return True if checker is None else bool(checker(n))



def run_hwoa_gwa(env: WSNEnvironment,
                 n_agents: int  = 30,
                 max_iter: int  = 1000,
                 b: float       = 1.0,
                 p_init: float  = 0.8,   # erken iterasyonda spiral oranı
                 p_end: float   = 0.2,   # son iterasyonda spiral oranı
                 mode: str      = "full", # "full" | "spiral" | "hier"
                 seed: int      = 0,
                 diag=None) -> dict:
    """
    Returns
    -------
    dict: history, best_positions, best_coverage, stable_iter, displacement
    """
    rng = np.random.default_rng(seed)
    dim = env.n_sensors * 2

    # ── Başlangıç: tam rastgele ────────────────────────────────────────
    X       = rng.uniform(0, env.area_size, (n_agents, dim))
    if not _can_evaluate(env, n_agents):
        raise ValueError("NFE budget is smaller than the HWOA-GWA initialization cost.")
    fitness = np.array([env.coverage_rate_vectorized(X[i].reshape(-1, 2))
                        for i in range(n_agents)])

    # Greedy personal best
    pbest   = X.copy()
    pbest_f = fitness.copy()

    # GWA liderlik hiyerarşisi
    sorted_idx = np.argsort(pbest_f)[::-1]
    alpha_pos  = pbest[sorted_idx[0]].copy()
    alpha_f    = pbest_f[sorted_idx[0]]
    beta_pos   = pbest[sorted_idx[1]].copy()
    delta_pos  = pbest[sorted_idx[2]].copy()

    if diag is not None:
        diag.on_init(X.copy(), fitness.copy(), alpha_f)

    history     = []
    last_improvement_iter = max_iter

    for it in range(max_iter):
        # Doğrusal azalan GWA parametresi
        a = 2.0 * (1.0 - it / max_iter)

        # Adaptif spiral olasılığı: başta yüksek (keşif), sonda düşük (sömürü)
        p_spiral = p_init - (p_init - p_end) * (it / max_iter)

        # diag: gerçekten çalışan operatör, dalların içinde kaydedilir
        ops = np.full(n_agents, -1, dtype=np.int8) if diag is not None else None

        new_X = X.copy()
        for i in range(n_agents):

            if mode == "spiral":
                # ── Ablation: sadece mWOA spirali (bubble-net), alfa liderine yönelik ─
                # (Yorum düzeltmesi: önceki versiyonda "rastgele lider"
                #  yazıyordu ama kod alpha_pos kullanıyordu; tutarsızlık giderildi.)
                D        = np.abs(alpha_pos - X[i]) + 1e-10
                l        = rng.uniform(-1, 1, dim)
                new_X[i] = np.clip(
                    D * np.exp(b * l) * np.cos(2 * np.pi * l) + alpha_pos,
                    0, env.area_size)
                if ops is not None:
                    ops[i] = SPIRAL

            elif mode == "hier":
                # ── Ablation: sadece GWA hiyerarşisi ─────────────────
                A1 = 2*a*rng.random(dim) - a;  C1 = 2*rng.random(dim)
                A2 = 2*a*rng.random(dim) - a;  C2 = 2*rng.random(dim)
                A3 = 2*a*rng.random(dim) - a;  C3 = 2*rng.random(dim)
                X1 = alpha_pos - A1 * np.abs(C1 * alpha_pos - X[i])
                X2 = beta_pos  - A2 * np.abs(C2 * beta_pos  - X[i])
                X3 = delta_pos - A3 * np.abs(C3 * delta_pos - X[i])
                new_X[i] = np.clip((X1+X2+X3)/3.0, 0, env.area_size)
                if ops is not None:
                    ops[i] = HIER

            else:
                # ── Full hibrit ───────────────────────────────────────
                if rng.random() < p_spiral:
                    # mWOA spiral (bubble-net) → α liderine sarmal saldırı
                    D        = np.abs(alpha_pos - X[i]) + 1e-10
                    l        = rng.uniform(-1, 1, dim)
                    new_X[i] = np.clip(
                        D * np.exp(b * l) * np.cos(2 * np.pi * l) + alpha_pos,
                        0, env.area_size)
                    if ops is not None:
                        ops[i] = SPIRAL
                else:
                    # GWA doğrusal çekim → α/β/δ üçlüsünden yönlendirme
                    A1 = 2*a*rng.random(dim)-a;  C1 = 2*rng.random(dim)
                    A2 = 2*a*rng.random(dim)-a;  C2 = 2*rng.random(dim)
                    A3 = 2*a*rng.random(dim)-a;  C3 = 2*rng.random(dim)
                    X1 = alpha_pos - A1 * np.abs(C1 * alpha_pos - X[i])
                    X2 = beta_pos  - A2 * np.abs(C2 * beta_pos  - X[i])
                    X3 = delta_pos - A3 * np.abs(C3 * delta_pos - X[i])
                    new_X[i] = np.clip((X1+X2+X3)/3.0, 0, env.area_size)
                    if ops is not None:
                        ops[i] = HIER

        if not _can_evaluate(env, n_agents):
            break
        X_prev  = X if diag is not None else None
        X       = new_X
        fitness = np.array([env.coverage_rate_vectorized(X[i].reshape(-1, 2))
                            for i in range(n_agents)])

        pbest_f_prev = pbest_f.copy() if diag is not None else None

        # Personal best güncelle
        improved          = fitness > pbest_f
        pbest[improved]   = X[improved]
        pbest_f[improved] = fitness[improved]

        # Liderlik hiyerarşisini taze tut
        sorted_idx = np.argsort(pbest_f)[::-1]
        global_src = -1
        if pbest_f[sorted_idx[0]] > alpha_f:
            alpha_f     = pbest_f[sorted_idx[0]]
            alpha_pos   = pbest[sorted_idx[0]].copy()
            last_improvement_iter = it + 1
            if diag is not None:
                global_src = int(ops[sorted_idx[0]])
        beta_pos  = pbest[sorted_idx[1]].copy()
        delta_pos = pbest[sorted_idx[2]].copy()

        if diag is not None:
            diag.on_iter(it, p_spiral, ops.copy(), X_prev.copy(), X.copy(),
                         fitness.copy(), pbest_f_prev, alpha_f, global_src)

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
