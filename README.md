# HWOA-GWA: Adaptive Spiral–Hierarchical Operator Switching for WSN Target Coverage

This repository contains the source code, experimental results, and
figures accompanying the paper:

> **Adaptive Spiral–Hierarchical Operator Switching for Target Coverage
> Optimization in Wireless Sensor Networks**  
> *[Author names], Cluster Computing, [Year]*

---

## Overview

HWOA-GWA is a hybrid metaheuristic that coordinates two complementary
search operators for mobile wireless sensor network (WSN) target coverage:

- **Spiral operator** (from the Whale Optimization Algorithm, WOA):
  nonlinear movement around the current best solution.
- **Hierarchical operator** (from the Grey Wolf Optimizer, GWO):
  guidance from the top-three ranked solutions (α, β, δ).

The probability of selecting the spiral operator decreases linearly
over the optimization process:

```
p_s(t) = p_init - (p_init - p_end) * t / T
p_init = 0.8,  p_end = 0.2
```

This adaptive schedule promotes exploration early and exploitation later.

---

## Repository Structure

```
HWOA-GWA-WSN/
├── src/
│   ├── environment.py           # WSN environment (Boolean disk coverage)
│   ├── statistical_experiment.py # Main experiment runner
│   └── algorithms/
│       ├── hwoa_gwa.py          # Proposed method (HWOA-GWA)
│       ├── pso.py               # Particle Swarm Optimization
│       ├── aco.py               # Continuous ACO variant (cACO)
│       ├── woa.py               # Modified WOA (mWOA)
│       ├── gwa.py               # Modified GWA (mGWA)
│       ├── csa.py               # Cuckoo Search Algorithm
│       └── random_baseline.py   # Random Search baseline
│
├── results/
│   ├── benchmark_results/       # Coverage, displacement, runtime (90 runs each)
│   │   ├── results_long.csv     # Full long-format dataset (primary)
│   │   ├── stats_pooled.csv     # Pooled summary statistics
│   │   └── stats_by_seed.csv    # Per-instance statistics
│   ├── statistical_tests/
│   │   ├── friedman_results.csv # Friedman omnibus test
│   │   ├── wilcoxon_pairwise.csv # Paired Wilcoxon + Holm correction
│   │   └── levene_variance.csv  # Brown-Forsythe variance test
│   ├── ablation/
│   │   └── ablation_results.csv # Full vs spiral-only vs hierarchy-only
│   └── run_manifest.json        # Experiment metadata
│
├── figures/                     # All generated figures
├── scripts/                     # Utility scripts
├── requirements.txt
└── README.md
```

---

## Experimental Design

| Parameter | Value |
|---|---|
| Deployment area | 100 × 100 m² |
| Sensing radius | r = 5 m |
| Scenario S1 | 100 sensors, 75 targets (ratio 1.33) |
| Scenario S2 | 50 sensors, 75 targets (ratio 0.67) |
| Scenario S3 | 200 sensors, 120 targets (ratio 1.67) |
| Population size | 25 |
| Max NFE budget | 6,250 (initialization included) |
| Environment seeds | 42, 17, 99 |
| Stochastic trials | 30 per instance |
| **Runs per method/scenario** | **3 × 30 = 90** |

All algorithms operate under the **same hard NFE budget**. Only complete
generations are executed; partial updates exceeding the budget are not initiated.

---

## Reproducing the Experiments

### Requirements

```bash
pip install -r requirements.txt
```

### Run all experiments

```bash
cd src
python statistical_experiment.py
```

Output files are written to `/mnt/user-data/outputs/` by default.
Edit the `OUTDIR` variable in `statistical_experiment.py` to change
the output directory.

**Estimated runtime:** ~2 hours on a 2-core machine.

### Algorithms

| Code label | Full name | Notes |
|---|---|---|
| `Random` | Random Search Baseline | Equal NFE budget |
| `PSO` | Particle Swarm Optimization | Full-random init, velocity clamp |
| `cACO` | Continuous ACO Variant | Not classical graph ACO |
| `mWOA` | Modified WOA | + greedy personal-best memory |
| `mGWA` | Modified GWA | + greedy personal-best memory |
| `CSA` | Cuckoo Search Algorithm | Lévy flights |
| `HWOA-GWA` | **Proposed method** | Adaptive spiral–hierarchical switching |

---

## Key Results

| Scenario | Best method | HWOA-GWA | vs mWOA | vs mGWA |
|---|---|---|---|---|
| S1 | cACO (98.13%) | 86.56% | +3.24%* | +3.12%* |
| S2 | cACO (83.30%) | 67.33% | +3.48%* | +1.60 ns |
| S3 | cACO (99.91%) | 96.45% | +1.06%* | +4.55%* |

*Holm-adjusted Wilcoxon p < 0.05. ns = not significant.

HWOA-GWA substantially reduces mGWA run-to-run variability
(CV: 9.67% → 5.58% in S1; 15.56% → 7.47% in S2; 5.10% → 2.03% in S3;
Brown-Forsythe p < 0.001 in all scenarios).

---

## Citation

If you use this code or data, please cite:

```bibtex
@article{hwoa_gwa_2025,
  author  = {[Authors]},
  title   = {Adaptive Spiral--Hierarchical Operator Switching for
             Target Coverage Optimization in Wireless Sensor Networks},
  journal = {Cluster Computing},
  year    = {2025},
  doi     = {[DOI]}
}
```

---

## License

MIT License — see `LICENSE` for details.
