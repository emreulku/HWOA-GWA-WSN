"""
statistical_experiment.py — v3 (Submission-Ready)
==================================================
Düzeltmeler:
  1. PAIRED long-format DataFrame — (sc_tag, env_seed, trial) anahtarıyla
     Wilcoxon/Friedman eşleşmesi garantili
  2. NFE counter — environment wrapper ile gerçek function evaluation sayısı
  3. Eşit bütçe — MAX_NFE = POP × BASE_ITER, tüm algoritmalar aynı bütçe
     (S3 artık hafifletilmiş değil; bütçe sabitleniyor)
  4. Robustness metrikleri — mean, std, CV, median, IQR, min, p5, p95
  5. Varyans testi — Levene (Brown-Forsythe) HWOA-GWA vs parent algoritmalar
  6. Ablation — full / spiral-only / hier-only aynı seed yapısında
  7. Holm-adjusted p-değerleri sayısal olarak raporlanıyor (boolean değil)

Çıktılar
--------
  results_long.csv        — satır: (sc, env_seed, trial, algo, metrik)
  stats_pooled.csv        — robustness metrikleri dahil özet
  stats_by_seed.csv       — env_seed bazında özet
  friedman_results.csv    — omnibus test
  wilcoxon_pairwise.csv   — Holm-adjusted pairwise
  levene_variance.csv     — HWOA-GWA vs parent varyans testi
  ablation_results.csv    — full / spiral / hier karşılaştırma
  results_raw.pkl         — ham pickle
  + IEEE figürleri
"""

import sys, os, time, warnings, pickle
from multiprocessing import Pool, cpu_count
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
from scipy import stats
from itertools import combinations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ═══════════════════════════════════════════════════════════════════
# YAPILANDIRMA
# ═══════════════════════════════════════════════════════════════════

ENV_SEEDS  = [42, 17, 99]
N_TRIALS   = 30
POP_SIZE   = 25
BASE_ITER  = 250                    # taban iterasyon
MAX_NFE    = POP_SIZE * BASE_ITER   # = 6250, tum algoritmalar bu bütceyle calisir

SCENARIOS = [
    dict(tag="S1", n_sensors=100, n_targets=75,
         label="S1: 100 sensör / 75 hedef"),
    dict(tag="S2", n_sensors=50,  n_targets=75,
         label="S2: 50 sensör / 75 hedef"),
    dict(tag="S3", n_sensors=200, n_targets=120,
         label="S3: 200 sensör / 120 hedef"),
]

ALGO_MAP = {
    "Random":   "Random Search Baseline",
    "PSO":      "PSO",
    "cACO":     "cACO (Continuous ACO Variant)",
    "mWOA":     "mWOA (Modified WOA)",
    "mGWA":     "mGWA (Modified GWA)",
    "CSA":      "CSA",
    "HWOA-GWA": "HWOA-GWA (Proposed)",
}
ALGOS      = list(ALGO_MAP.keys())
ALGO_LABEL = ALGO_MAP

ABLATION_MODES = ["full", "spiral", "hier"]

OUTDIR = os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "results", "benchmark_results")

PALETTE = {
    "Random":   "#999999", "PSO":  "#0072B2", "cACO": "#D55E00",
    "mWOA":     "#009E73", "mGWA": "#CC79A7", "CSA":  "#E69F00",
    "HWOA-GWA": "#56B4E9",
}
MARKERS = {
    "Random":"x","PSO":"o","cACO":"s","mWOA":"^",
    "mGWA":"D","CSA":"v","HWOA-GWA":"*",
}
IEEE_RC = {
    "font.family":"serif","font.size":10,"axes.titlesize":11,
    "axes.labelsize":10,"xtick.labelsize":9,"ytick.labelsize":9,
    "legend.fontsize":8,"figure.dpi":300,"lines.linewidth":1.5,
    "axes.grid":True,"grid.linestyle":":","grid.alpha":0.5,
}


# ═══════════════════════════════════════════════════════════════════
# NFE SAYACI — environment wrapper
# ═══════════════════════════════════════════════════════════════════

class NFECountingEnv:
    """
    Hard-cap objective-evaluation wrapper.

    Initialization evaluations are included in the NFE budget.
    Algorithms must call can_evaluate(k) before evaluating a complete
    initialization/generation/iteration block. The wrapper also protects
    against accidental budget overruns by raising RuntimeError.
    """
    def __init__(self, env, max_nfe: int):
        self._env = env
        self.max_nfe = int(max_nfe)
        self.nfe = 0

        self.n_sensors       = env.n_sensors
        self.n_targets       = env.n_targets
        self.area_size       = env.area_size
        self.sensing_radius  = env.sensing_radius
        self.targets         = env.targets
        self.initial_sensors = env.initial_sensors

    @property
    def remaining_nfe(self):
        return self.max_nfe - self.nfe

    @property
    def budget_exhausted(self):
        return self.remaining_nfe <= 0

    def can_evaluate(self, n=1):
        return self.nfe + int(n) <= self.max_nfe

    def _consume(self):
        if not self.can_evaluate(1):
            raise RuntimeError(
                f"Hard NFE budget exceeded: attempted evaluation "
                f"{self.nfe + 1} with MAX_NFE={self.max_nfe}."
            )
        self.nfe += 1

    def coverage_rate_vectorized(self, sensor_positions):
        self._consume()
        return self._env.coverage_rate_vectorized(sensor_positions)

    def coverage_rate(self, sensor_positions):
        self._consume()
        return self._env.coverage_rate(sensor_positions)

    def total_displacement(self, final_positions):
        return self._env.total_displacement(final_positions)


# ═══════════════════════════════════════════════════════════════════
# WORKER
# ═══════════════════════════════════════════════════════════════════

def _run_one(args):
    (sc_tag, n_sensors, n_targets, env_seed,
     algo_key, trial, max_nfe, ablation_mode) = args

    import sys, os, time
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from environment            import WSNEnvironment
    from algorithms.pso         import run_pso
    from algorithms.aco         import run_aco
    from algorithms.woa         import run_woa
    from algorithms.gwa         import run_gwa
    from algorithms.csa         import run_csa
    from algorithms.hwoa_gwa    import run_hwoa_gwa
    from algorithms.random_baseline import run_random_baseline

    # NFE'ye gore max_iter hesapla (her algoritmanin iter basina NFE'si farkli olabilir)
    # Varsayilan: iter_basina_nfe = pop_size (ozel durumlar asagida)
    pop = 25

    RUNNERS = {
        "Random":   (run_random_baseline, "n_particles"),
        "PSO":      (run_pso,             "n_particles"),
        "cACO":     (run_aco,             "n_ants"),
        "mWOA":     (run_woa,             "n_whales"),
        "mGWA":     (run_gwa,             "n_wolves"),
        "CSA":      (run_csa,             "n_nests"),
        "HWOA-GWA": (run_hwoa_gwa,        "n_agents"),
    }

    # NFE per iteration:
    # CSA abandon sonrasi re-evaluate yapiyor: n_nests + n_abandon kez.
    # NFE bütçesi: init dahil hard cap
    # Her algoritmanin init maliyeti ve iter basina NFE'si farklidir.
    pa_csa = 0.25
    init_nfe_map = {
        "Random":   0,
        "PSO":      pop,
        "cACO":     1,
        "mWOA":     pop,
        "mGWA":     pop,
        "CSA":      pop,
        "HWOA-GWA": pop,
    }
    iter_nfe_map = {
        "Random":   pop,
        "PSO":      pop,
        "cACO":     pop,
        "mWOA":     pop,
        "mGWA":     pop,
        "CSA":      1 + max(1, int(pa_csa * pop)),
        "HWOA-GWA": pop,
    }
    init_cost = init_nfe_map[algo_key]
    iter_cost = iter_nfe_map[algo_key]
    if max_nfe < init_cost:
        raise ValueError(
            f"MAX_NFE={max_nfe} is below initialization cost "
            f"{init_cost} for {algo_key}."
        )
    max_iter = max(0, (max_nfe - init_cost) // iter_cost)

    raw_env = WSNEnvironment(
        n_sensors=n_sensors, n_targets=n_targets,
        area_size=100.0, sensing_radius=5.0, seed=env_seed,
    )
    env = NFECountingEnv(raw_env, max_nfe)

    runner, kw = RUNNERS[algo_key]
    solver_seed = trial + env_seed * 1000

    kwargs = {kw: pop, "max_iter": max_iter, "seed": solver_seed}
    if algo_key == "HWOA-GWA" and ablation_mode != "full":
        kwargs["mode"] = ablation_mode

    t0  = time.time()
    res = runner(env, **kwargs)
    dt  = time.time() - t0

    h = res["history"]
    if len(h) < max_iter:
        h = h + [h[-1]] * (max_iter - len(h))

    return {
        "sc_tag":        sc_tag,
        "env_seed":      env_seed,
        "algo":          algo_key,
        "ablation":      ablation_mode,
        "trial":         trial,
        "coverage":      res["best_coverage"],
        "disp":          res["displacement"],
        "runtime":       dt,
        "last_imp":      res.get("last_improvement_iter", max_iter),
        "nfe_actual":    env.nfe,
        "nfe_budget":    max_nfe,
        "nfe_util_pct":  round(100.0 * env.nfe / max_nfe, 3),
        "stop_reason":   ("full_coverage" if res["best_coverage"] >= 100.0
                          else "budget_or_schedule"),
        "max_iter_used": max_iter,
        "history":       h[:max_iter],
    }


# ═══════════════════════════════════════════════════════════════════
# DENEY KOSUCULARI
# ═══════════════════════════════════════════════════════════════════

def build_tasks(include_ablation=True):
    tasks = []
    # Ana deneyler
    for sc in SCENARIOS:
        for env_seed in ENV_SEEDS:
            for algo in ALGOS:
                for trial in range(N_TRIALS):
                    tasks.append((
                        sc["tag"], sc["n_sensors"], sc["n_targets"],
                        env_seed, algo, trial, MAX_NFE, "full"
                    ))
    # Ablasyon: sadece HWOA-GWA, spiral ve hier modlari
    if include_ablation:
        sc = SCENARIOS[0]   # S1 uzerinde ablasyon yeterli
        for env_seed in ENV_SEEDS:
            for mode in ["spiral", "hier"]:
                for trial in range(N_TRIALS):
                    tasks.append((
                        sc["tag"] + "_abl", sc["n_sensors"], sc["n_targets"],
                        env_seed, "HWOA-GWA", trial, MAX_NFE, mode
                    ))
    return tasks


def run_experiments(tasks):
    n_cpu = max(1, cpu_count())
    total = len(tasks)
    print(f"  Toplam kosun: {total}  |  CPU: {n_cpu}\n")
    t0 = time.time()
    raw = []
    with Pool(processes=n_cpu) as pool:
        for i, r in enumerate(pool.imap_unordered(_run_one, tasks, chunksize=4)):
            raw.append(r)
            if (i+1) % 150 == 0:
                el  = time.time()-t0
                eta = el/(i+1)*(total-i-1)
                print(f"  [{100*(i+1)/total:5.1f}%] "
                      f"gecen:{el/60:.1f}dk  kalan:{eta/60:.1f}dk", flush=True)
    print(f"\n  Toplam sure: {(time.time()-t0)/60:.1f} dk")
    return raw


# ═══════════════════════════════════════════════════════════════════
# LONG-FORMAT DATAFRAME — PAIRED GUARANTEE
# ═══════════════════════════════════════════════════════════════════

def to_long_df(raw):
    """
    Her satir: (sc_tag, env_seed, trial, algo, ablation, coverage, ...)
    (sc_tag, env_seed, trial) uclüsü Wilcoxon pairing anahtari.
    """
    rows = []
    for r in raw:
        rows.append({
            "sc_tag":        r["sc_tag"],
            "env_seed":      r["env_seed"],
            "algo":          r["algo"],
            "ablation":      r["ablation"],
            "trial":         r["trial"],
            "coverage":      r["coverage"],
            "disp":          r["disp"],
            "runtime":       r["runtime"],
            "last_imp":      r["last_imp"],
            "nfe_actual":    r["nfe_actual"],
            "nfe_budget":    r["nfe_budget"],
            "nfe_util_pct":  r["nfe_util_pct"],
            "stop_reason":   r["stop_reason"],
            "max_iter_used": r["max_iter_used"],
        })
    return pd.DataFrame(rows)


def pivot_for_tests(long_df, sc_tag, metric="coverage"):
    """
    (env_seed, trial) × algo pivot tablosu.
    Her satir ayni (env_seed, trial) ciftini paylasir — paired.
    """
    sub = long_df[(long_df["sc_tag"] == sc_tag) &
                  (long_df["ablation"] == "full")].copy()
    piv = sub.pivot_table(index=["env_seed","trial"],
                          columns="algo", values=metric,
                          aggfunc="first")
    # Eksik satir yoksa return et
    piv = piv.dropna()
    # Mevcut sutunlardan ALGOS sirasiyla sec (eksik algo toleransi)
    available = [a for a in ALGOS if a in piv.columns]
    return piv[available]


# ═══════════════════════════════════════════════════════════════════
# ISTATISTIK
# ═══════════════════════════════════════════════════════════════════

def robustness_stats(vals):
    """mean, std, CV, median, IQR, min, p5, p95 — tam robustness seti."""
    v = np.array(vals, dtype=float)
    if len(v) == 0:
        nan = float("nan")
        return {k: nan for k in ("mean","std","cv","median","iqr","min","p5","p95","max")}
    ddof = 1 if len(v) > 1 else 0
    std  = np.std(v, ddof=ddof)
    mean = np.mean(v)
    return {
        "mean":   round(mean,                                        2),
        "std":    round(std,                                         2),
        "cv":     round(std/mean*100 if mean > 0 else 0,            2),
        "median": round(np.median(v),                               2),
        "iqr":    round(float(np.percentile(v,75)-np.percentile(v,25)), 2),
        "min":    round(np.min(v),                                  2),
        "p5":     round(float(np.percentile(v, 5)),                 2),
        "p95":    round(float(np.percentile(v,95)),                 2),
        "max":    round(np.max(v),                                  2),
    }


def compute_stats_pooled(long_df):
    rows = []
    for sc in SCENARIOS:
        tag = sc["tag"]
        sub = long_df[(long_df["sc_tag"]==tag) & (long_df["ablation"]=="full")]
        for algo in ALGOS:
            a = sub[sub["algo"]==algo]
            rs = robustness_stats(a["coverage"])
            rows.append({
                "Senaryo": tag, "Algoritma": algo,
                "Etiket":  ALGO_LABEL[algo], "N": len(a),
                **{f"Cov_{k}": v for k,v in rs.items()},
                "Disp_mean": round(a["disp"].mean(),   1),
                "Disp_std":  round(a["disp"].std(ddof=1), 1),
                "RT_mean_s": round(a["runtime"].mean(), 2),
                "RT_std_s":  round(a["runtime"].std(ddof=1), 2),
                "LastImp_mean": round(a["last_imp"].mean(), 1),
                "LastImp_std":  round(a["last_imp"].std(ddof=1), 1),
                "NFE_mean":     round(a["nfe_actual"].mean(), 1),
                "NFE_min":      int(a["nfe_actual"].min()) if len(a) > 0 else 0,
                "NFE_max":      int(a["nfe_actual"].max()) if len(a) > 0 else 0,
                "NFE_util_pct": round(a["nfe_util_pct"].mean(), 3),
            })
    return pd.DataFrame(rows)


def compute_stats_by_seed(long_df):
    rows = []
    for sc in SCENARIOS:
        tag = sc["tag"]
        for env_seed in ENV_SEEDS:
            sub = long_df[(long_df["sc_tag"]==tag) &
                          (long_df["env_seed"]==env_seed) &
                          (long_df["ablation"]=="full")]
            for algo in ALGOS:
                a = sub[sub["algo"]==algo]["coverage"]
                if len(a) == 0: continue
                rows.append({
                    "Senaryo":  tag, "Env_Seed": env_seed, "Algoritma": algo,
                    "Cov_mean": round(a.mean(),        2),
                    "Cov_std":  round(a.std(ddof=1),   2),
                    "Cov_med":  round(a.median(),      2),
                })
    return pd.DataFrame(rows)


def friedman_test(long_df):
    rows = []
    for sc in SCENARIOS:
        tag = sc["tag"]
        piv = pivot_for_tests(long_df, tag, "coverage")
        if len(piv) < 3: continue
        stat, p = stats.friedmanchisquare(*[piv[a].values for a in ALGOS])
        rows.append({"Senaryo":tag, "Chi2":round(stat,3),
                     "p":round(p,6), "N_obs":len(piv),
                     "Anlamli":"Evet" if p<0.05 else "Hayir"})
    return pd.DataFrame(rows)


def wilcoxon_pairwise(long_df):
    """
    PAIRED Wilcoxon: her satir ayni (env_seed, trial) ciftini paylasir.
    Holm-adjusted p-degerleri sayisal olarak raporlanir.
    """
    rows = []
    for sc in SCENARIOS:
        tag = sc["tag"]
        piv = pivot_for_tests(long_df, tag, "coverage")
        if len(piv) < 3: continue

        available_algos = list(piv.columns)
        pairs  = list(combinations(available_algos, 2))
        pvals  = []
        wstats = []
        for a1, a2 in pairs:
            try:    s, p = stats.wilcoxon(piv[a1].values, piv[a2].values)
            except: s, p = np.nan, np.nan
            pvals.append(p); wstats.append(s)

        # Holm: adjusted p-values
        valid_idx = [i for i,p in enumerate(pvals) if not np.isnan(p)]
        srt = sorted(valid_idx, key=lambda i: pvals[i])
        m   = len(valid_idx)
        adj_p = [np.nan] * len(pairs)
        for rank, i in enumerate(srt):
            raw_p = pvals[i]
            adj   = min(1.0, raw_p * (m - rank))
            # Holm monotonicity
            if rank > 0:
                adj = max(adj, adj_p[srt[rank-1]])
            adj_p[i] = adj

        for idx, (a1, a2) in enumerate(pairs):
            p_raw = pvals[idx]; p_adj = adj_p[idx]
            sig   = (not np.isnan(p_adj)) and p_adj < 0.05
            rows.append({
                "Senaryo":  tag, "A1": a1, "A2": a2,
                "W":        round(wstats[idx],2) if not np.isnan(wstats[idx]) else np.nan,
                "p_raw":    round(p_raw,5)       if not np.isnan(p_raw)       else np.nan,
                "p_holm":   round(p_adj,5)       if not np.isnan(p_adj)       else np.nan,
                "Sig_0.05": "Evet" if sig else "Hayir",
                "A1_mean":  round(piv[a1].mean(), 2),
                "A2_mean":  round(piv[a2].mean(), 2),
                "Ustun":    (a1 if piv[a1].mean() > piv[a2].mean() else a2)
                             if sig else "Anlamsiz",
            })
    return pd.DataFrame(rows)


def levene_variance_test(long_df):
    """
    HWOA-GWA vs parent algoritmalar (mWOA, mGWA) arasinda varyans farki.
    Brown-Forsythe variant: center='median' (outlier'lara daha robust).
    Ek olarak tum algoritma ciftleri arasi.
    """
    rows = []
    parent_pairs = [("HWOA-GWA","mWOA"), ("HWOA-GWA","mGWA"),
                    ("HWOA-GWA","PSO"),  ("HWOA-GWA","cACO")]

    for sc in SCENARIOS:
        tag = sc["tag"]
        piv = pivot_for_tests(long_df, tag, "coverage")
        if len(piv) < 3: continue
        avail = set(piv.columns)
        for a1, a2 in parent_pairs:
            if a1 not in avail or a2 not in avail: continue
            stat, p = stats.levene(piv[a1].values, piv[a2].values,
                                   center="median")
            rows.append({
                "Senaryo": tag, "A1": a1, "A2": a2,
                "BF_stat": round(stat, 3),
                "p":       round(p,    5),
                "Sig_0.05":"Evet" if p<0.05 else "Hayir",
                "A1_std":  round(piv[a1].std(ddof=1), 2),
                "A2_std":  round(piv[a2].std(ddof=1), 2),
                "A1_daha_kararli": "Evet" if piv[a1].std(ddof=1) < piv[a2].std(ddof=1) else "Hayir",
            })
    return pd.DataFrame(rows)


def ablation_stats(long_df):
    """full / spiral / hier karsilastirmasi — S1 uzerinde."""
    tag = "S1_abl"
    rows = []
    for mode in ABLATION_MODES:
        if mode == "full":
            sub = long_df[(long_df["sc_tag"]=="S1") &
                          (long_df["algo"]=="HWOA-GWA") &
                          (long_df["ablation"]=="full")]
        else:
            sub = long_df[(long_df["sc_tag"]==tag) &
                          (long_df["algo"]=="HWOA-GWA") &
                          (long_df["ablation"]==mode)]
        if len(sub) == 0: continue
        rs = robustness_stats(sub["coverage"])
        rows.append({"Mod": mode, "N": len(sub),
                     **{f"Cov_{k}":v for k,v in rs.items()},
                     "Disp_mean": round(sub["disp"].mean(), 1)})
    return pd.DataFrame(rows)


# ═══════════════════════════════════════════════════════════════════
# FIGURLER
# ═══════════════════════════════════════════════════════════════════

def _get_histories(raw, sc_tag, algo, ablation="full"):
    h_list = [r["history"] for r in raw
              if r["sc_tag"]==sc_tag and r["algo"]==algo
              and r["ablation"]==ablation]
    if not h_list: return None
    mi = min(len(h) for h in h_list)
    return np.array([h[:mi] for h in h_list])


def fig_convergence(raw):
    with plt.rc_context(IEEE_RC):
        for sc in SCENARIOS:
            tag = sc["tag"]
            fig, ax = plt.subplots(figsize=(6.5, 4.5))
            max_len = 0
            for algo in ALGOS:
                mat = _get_histories(raw, tag, algo)
                if mat is None: continue
                mi   = mat.shape[1]; max_len = max(max_len, mi)
                iters= np.arange(1, mi+1)
                mean = mat.mean(0); std = mat.std(0, ddof=1)
                ls   = "-" if algo in ("PSO","HWOA-GWA","cACO") else "--"
                ax.plot(iters, mean, color=PALETTE[algo], lw=1.5, ls=ls,
                        label=algo, marker=MARKERS[algo],
                        markevery=max(1,mi//5), markersize=5)
                ax.fill_between(iters, np.maximum(mean-std,0), mean+std,
                                color=PALETTE[algo], alpha=0.10)
            ax.set_xlabel("Iterasyon (esit NFE bütcesi)")
            ax.set_ylabel("Kapsama Orani (%)")
            ax.set_title(f"Yakinasma — {sc['label']}\n"
                         f"MAX_NFE={MAX_NFE} | "
                         f"{len(ENV_SEEDS)} env × {N_TRIALS} trial = "
                         f"{len(ENV_SEEDS)*N_TRIALS} kosun")
            ax.legend(loc="lower right", ncol=2, fontsize=7)
            fig.tight_layout()
            fig.savefig(os.path.join(OUTDIR,f"conv_{tag}.png"),
                        dpi=300, bbox_inches="tight")
            plt.close(fig)


def fig_boxplot_coverage(long_df):
    with plt.rc_context(IEEE_RC):
        fig, axes = plt.subplots(1, len(SCENARIOS),
                                 figsize=(5*len(SCENARIOS), 4.8))
        for ax, sc in zip(axes, SCENARIOS):
            tag = sc["tag"]
            sub = long_df[(long_df["sc_tag"]==tag) & (long_df["ablation"]=="full")]
            data_bp = [sub[sub["algo"]==a]["coverage"].values for a in ALGOS]
            bp = ax.boxplot(data_bp, patch_artist=True,
                            medianprops=dict(color="black",lw=1.8),
                            whiskerprops=dict(lw=1.2), capprops=dict(lw=1.2),
                            flierprops=dict(marker="o",ms=2,alpha=0.5))
            for patch, algo in zip(bp["boxes"], ALGOS):
                patch.set_facecolor(PALETTE[algo]); patch.set_alpha(0.78)
            ax.set_xticks(range(1,len(ALGOS)+1))
            ax.set_xticklabels(ALGOS, rotation=40, ha="right", fontsize=8)
            ax.set_ylabel("Kapsama Orani (%)"); ax.set_title(sc["label"])
        n_tot = len(ENV_SEEDS)*N_TRIALS
        fig.suptitle(f"Kapsama Dagilimi ({n_tot} kosun = "
                     f"{len(ENV_SEEDS)} env × {N_TRIALS} trial)",
                     fontsize=11, fontweight="bold")
        fig.tight_layout()
        fig.savefig(os.path.join(OUTDIR,"boxplot_coverage.png"),
                    dpi=300, bbox_inches="tight")
        plt.close(fig)


def fig_robustness_radar(long_df):
    """
    CV, IQR, p5 uzerinden robustness profili — radar chart.
    Dusuk deger = daha kararli.
    """
    metrics = ["cv","iqr","p5_inv"]  # p5_inv = 100-p5 (dusuk = iyi)
    with plt.rc_context(IEEE_RC):
        fig, axes = plt.subplots(1, len(SCENARIOS),
                                 figsize=(5*len(SCENARIOS), 4.5))
        for ax, sc in zip(axes, SCENARIOS):
            tag = sc["tag"]
            sub = long_df[(long_df["sc_tag"]==tag) & (long_df["ablation"]=="full")]
            x   = np.arange(len(ALGOS))
            # CV bar grubu
            cvs = []
            for algo in ALGOS:
                v = sub[sub["algo"]==algo]["coverage"].values
                cv = np.std(v,ddof=1)/np.mean(v)*100 if np.mean(v)>0 else 0
                cvs.append(cv)
            bars = ax.bar(x, cvs, color=[PALETTE[a] for a in ALGOS],
                          alpha=0.80, edgecolor="black", lw=0.8)
            ax.set_xticks(x)
            ax.set_xticklabels(ALGOS, rotation=40, ha="right", fontsize=8)
            ax.set_ylabel("Coefficient of Variation (%)\n(Dusuk = Daha Kararli)")
            ax.set_title(sc["label"])
        fig.suptitle("Robustness: Coefficient of Variation\n"
                     "(HWOA-GWA'nin parent algoritmalara gore kararliligi)",
                     fontsize=10, fontweight="bold")
        fig.tight_layout()
        fig.savefig(os.path.join(OUTDIR,"robustness_cv.png"),
                    dpi=300, bbox_inches="tight")
        plt.close(fig)


def fig_coverage_vs_displacement(long_df):
    with plt.rc_context(IEEE_RC):
        fig, axes = plt.subplots(1, len(SCENARIOS),
                                 figsize=(5*len(SCENARIOS), 4.8))
        for ax, sc in zip(axes, SCENARIOS):
            tag = sc["tag"]
            sub = long_df[(long_df["sc_tag"]==tag) & (long_df["ablation"]=="full")]
            for algo in ALGOS:
                a  = sub[sub["algo"]==algo]
                cx = a["coverage"].mean()
                dy = a["disp"].mean()/1000
                cs = a["coverage"].std(ddof=1)
                ds = a["disp"].std(ddof=1)/1000
                ax.errorbar(dy, cx, xerr=ds, yerr=cs,
                            fmt=MARKERS[algo], color=PALETTE[algo],
                            markersize=9, lw=1.4, capsize=3,
                            label=algo, zorder=5)
            ax.set_xlabel("Ort. Yer Degistirme (km)\n[mobility-induced energy proxy]")
            ax.set_ylabel("Ort. Kapsama Orani (%)")
            ax.set_title(sc["label"])
            ax.legend(loc="lower right", ncol=2, fontsize=7)
        fig.suptitle("Kapsama vs. Hareket Maliyeti Tradeoff\n"
                     "(Yer degistirme: mobility-induced energy proxy)",
                     fontsize=10, fontweight="bold")
        fig.tight_layout()
        fig.savefig(os.path.join(OUTDIR,"scatter_coverage_vs_disp.png"),
                    dpi=300, bbox_inches="tight")
        plt.close(fig)


def fig_ablation(long_df):
    with plt.rc_context(IEEE_RC):
        fig, ax = plt.subplots(figsize=(6, 4))
        mode_labels = {"full":"HWOA-GWA (full)",
                       "spiral":"mWOA only (spiral)",
                       "hier":"mGWA only (hierarchy)"}
        mode_colors = {"full":"#56B4E9","spiral":"#009E73","hier":"#CC79A7"}
        x = np.arange(len(ABLATION_MODES))
        for i, mode in enumerate(ABLATION_MODES):
            if mode == "full":
                sub = long_df[(long_df["sc_tag"]=="S1") &
                              (long_df["algo"]=="HWOA-GWA") &
                              (long_df["ablation"]=="full")]
            else:
                sub = long_df[(long_df["sc_tag"]=="S1_abl") &
                              (long_df["algo"]=="HWOA-GWA") &
                              (long_df["ablation"]==mode)]
            if len(sub) == 0: continue
            v   = sub["coverage"].values
            ax.bar(i, np.mean(v), yerr=np.std(v,ddof=1), capsize=6,
                   color=mode_colors[mode], alpha=0.85, edgecolor="black",
                   label=mode_labels[mode])
            ax.scatter([i]*len(v), v, color="black", alpha=0.25, s=8, zorder=5)
        ax.set_xticks(x)
        ax.set_xticklabels([mode_labels[m] for m in ABLATION_MODES],
                           rotation=15, ha="right")
        ax.set_ylabel("Kapsama Orani (%)")
        ax.set_title("Ablasyon Analizi — S1\n"
                     "Her komponentin katkilari (ort. +/- std, N="
                     f"{len(ENV_SEEDS)*N_TRIALS})")
        fig.tight_layout()
        fig.savefig(os.path.join(OUTDIR,"ablation_s1.png"),
                    dpi=300, bbox_inches="tight")
        plt.close(fig)


def fig_by_seed(long_df):
    with plt.rc_context(IEEE_RC):
        for sc in SCENARIOS:
            tag = sc["tag"]
            fig, axes = plt.subplots(1, len(ENV_SEEDS),
                                     figsize=(4.5*len(ENV_SEEDS), 4.5), sharey=True)
            for ax, env_seed in zip(axes, ENV_SEEDS):
                sub = long_df[(long_df["sc_tag"]==tag) &
                              (long_df["env_seed"]==env_seed) &
                              (long_df["ablation"]=="full")]
                bp = ax.boxplot(
                    [sub[sub["algo"]==a]["coverage"].values for a in ALGOS],
                    patch_artist=True, medianprops=dict(color="black",lw=1.5))
                for patch, algo in zip(bp["boxes"], ALGOS):
                    patch.set_facecolor(PALETTE[algo]); patch.set_alpha(0.75)
                ax.set_xticks(range(1,len(ALGOS)+1))
                ax.set_xticklabels(ALGOS, rotation=40, ha="right", fontsize=7)
                ax.set_title(f"env_seed={env_seed}", fontsize=9)
                if ax is axes[0]: ax.set_ylabel("Kapsama Orani (%)")
            fig.suptitle(f"{sc['label']} — Problem Ornegi Degiskenligi",
                         fontsize=10, fontweight="bold")
            fig.tight_layout()
            fig.savefig(os.path.join(OUTDIR,f"boxplot_by_seed_{tag}.png"),
                        dpi=300, bbox_inches="tight")
            plt.close(fig)


# ═══════════════════════════════════════════════════════════════════
# ANA AKIS
# ═══════════════════════════════════════════════════════════════════

def main():
    os.makedirs(OUTDIR, exist_ok=True)
    tasks = build_tasks(include_ablation=True)
    total = len(tasks)
    print(f"\n{'='*62}")
    print(f"  MAX_NFE={MAX_NFE} (POP={POP_SIZE} × BASE_ITER={BASE_ITER})")
    print(f"  {len(SCENARIOS)} senaryo × {len(ENV_SEEDS)} env_seed × "
          f"{len(ALGOS)} algo × {N_TRIALS} trial")
    print(f"  + Ablasyon (S1, spiral+hier × {len(ENV_SEEDS)} env × {N_TRIALS} trial)")
    print(f"  Toplam kosun: {total}")
    print(f"{'='*62}\n")

    t0  = time.time()
    raw = run_experiments(tasks)

    # Long-format DataFrame
    long_df = to_long_df(raw)
    long_df.to_csv(os.path.join(OUTDIR,"results_long.csv"),
                   index=False, encoding="utf-8-sig")

    # Pickle
    with open(os.path.join(OUTDIR,"results_raw.pkl"),"wb") as fh:
        pickle.dump({"raw":raw,"long_df":long_df}, fh)

    # Istatistik
    df_pooled   = compute_stats_pooled(long_df)
    df_by_seed  = compute_stats_by_seed(long_df)
    df_friedman = friedman_test(long_df)
    df_wilcoxon = wilcoxon_pairwise(long_df)
    df_levene   = levene_variance_test(long_df)
    df_ablation = ablation_stats(long_df)

    df_pooled.to_csv(  os.path.join(OUTDIR,"stats_pooled.csv"),    index=False, encoding="utf-8-sig")
    df_by_seed.to_csv( os.path.join(OUTDIR,"stats_by_seed.csv"),   index=False, encoding="utf-8-sig")
    df_friedman.to_csv(os.path.join(OUTDIR,"friedman_results.csv"),index=False, encoding="utf-8-sig")
    df_wilcoxon.to_csv(os.path.join(OUTDIR,"wilcoxon_pairwise.csv"),index=False,encoding="utf-8-sig")
    df_levene.to_csv(  os.path.join(OUTDIR,"levene_variance.csv"), index=False, encoding="utf-8-sig")
    df_ablation.to_csv(os.path.join(OUTDIR,"ablation_results.csv"),index=False, encoding="utf-8-sig")

    print("\n-- Friedman -----------------------------------------------")
    print(df_friedman.to_string(index=False))
    print("\n-- Levene (Brown-Forsythe) Varyans Testi ------------------")
    print(df_levene.to_string(index=False))
    print("\n-- Ablasyon -----------------------------------------------")
    print(df_ablation.to_string(index=False))
    print("\n-- Ozet (Cov_mean, Cov_std, Cov_cv, Cov_p5) --------------")
    print(df_pooled[["Senaryo","Algoritma","Cov_mean","Cov_std",
                     "Cov_cv","Cov_p5","Disp_mean","RT_mean_s",
                     "NFE_mean"]].to_string(index=False))

    print("\n  Figurler uretiliyor...")
    fig_convergence(raw)
    fig_boxplot_coverage(long_df)
    fig_by_seed(long_df)
    fig_coverage_vs_displacement(long_df)
    fig_robustness_radar(long_df)
    fig_ablation(long_df)
    print(f"  Tamamlandi — toplam {(time.time()-t0)/60:.1f} dk")


if __name__ == "__main__":
    main()
