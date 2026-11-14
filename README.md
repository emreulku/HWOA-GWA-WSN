# HWOA-GWA: Spiral–Hierarchical Operator Selection for WSN Target Coverage

Code, protocols and analysis scripts for the manuscript
"Spiral–Hierarchical Operator Selection for Target Coverage in Wireless Sensor Networks: A Component-Level Evaluation" (Cluster Computing, under revision).

## Overview

HWOA-GWA is a population-based optimizer for static target coverage placement in a two-dimensional region with a binary disk sensing model. Each candidate keeps a personal-best memory. At every iteration, each candidate draws one of two existing operators at random:

- **Spiral operator** (Whale Optimization Algorithm, WOA): spiral move around the best-so-far solution.
- **Hierarchical operator** (Grey Wolf Optimizer, GWO): guidance from the three best personal bests (α, β, δ).

The spiral-selection probability follows a fixed linear schedule:

```
p_s(t) = 0.8 - 0.6 * t / T,   t = 0, ..., T-1
```

The schedule does not use feedback from the search; it is deterministic parameter control, not adaptive control.

## Versions

| Version | Identifier | Content |
|---|---|---|
| Submitted manuscript | tag `v1.0-submission`, commit `3e15fcb` | Algorithms and the original experiment runner |
| Revision experiments E1–E5 | commit `a1193e8` | Diagnostics, NOPB variant, runner, statistics module, protocol v1.0.1 |
| Revision experiment E5b | commit `24acbdb` | Pre-registered G(0.8,0.8) − FULL test (protocol addendum) |
| Revision analysis | tag and release `v2.0-revision`, commit `2f89232` | Analysis v3/v4, manuscript tables and figures, geometric audit |
| Protocol deviation record | commit `60a9078` | `revision/protocol/` (Turkish original and [English translation](https://github.com/emreulku/HWOA-GWA-WSN/blob/60a907844dbc2e103772a686056841ff690d683f/revision/protocol/Protocol_v1.0.1_Deviation_Record_d3_EN.md)) |

## Repository layout

```
src/                     Environment, algorithm implementations, original experiment runner
revision/protocol/       Experiment protocol v1.0 / v1.0.1, E5b addendum, deviation record d3
revision/tools/          Revision experiment runner, statistics module and checks
revision/gates/          Pre-run check reports
revision/analysis_v3/    Statistical analysis, tables and figures (revision)
revision/analysis_v4/    Manuscript tables, English figures, Gap table, S2 full-coverage witness
results/, figures/       Outputs of the submitted version (v1.0); superseded by the revision
```

`results/` and `figures/` are kept for traceability of the submitted version. They contain analyses (Friedman, Brown–Forsythe, coefficient of variation, S1-only ablation) that are not used in the revised manuscript.

## Revision data

Raw data are not stored in git. They are attached to release [`v2.0-revision`](https://github.com/emreulku/HWOA-GWA-WSN/releases/tag/v2.0-revision):

- `HWOA_revizyon_nihai_arsiv.zip`: raw runs and convergence histories (E1–E5, E5b), operator diagnostics (E1–E3), manifests, analysis-v3 scripts and outputs, `SHA256SUMS.txt`
- `HWOA_revizyon_analysis_v4.zip`: analysis-v4 scripts and outputs (manuscript tables, Figures 3–7, Gap table, S2 witness)
- `RELEASE_SHA256SUMS.txt`: SHA-256 of both archives

Install the analysis environment first (`revision/requirements-revision.txt`; NetworkX is needed only for the geometric audit). The commands use `python -I`, which ignores user-site packages, so install the packages into the environment of the Python you run.

To verify and reproduce:

```
pip install -r revision/requirements-revision.txt
sha256sum -c RELEASE_SHA256SUMS.txt
unzip HWOA_revizyon_nihai_arsiv.zip && cd HWOA_revizyon_nihai_arsiv
python -I verify_package.py      # raw data against manifest hashes and run counts
python -I run_all.py             # regenerates analysis-v3 outputs and compares them byte for byte
```

The analysis-v4 commands are listed in `revision/analysis_v4/README.md`. The scripts in `revision/analysis_v3/` and `revision/analysis_v4/` are byte-identical to the copies inside the two archives.

## Experimental setting (revision)

| Item | Value |
|---|---|
| Region, sensing radius | 100 × 100 m, r = 5 m |
| Scenarios (sensors / targets) | S1 100/75, S2 50/75, S3 200/120 |
| Evaluation limit | 6,250 objective-function evaluations, actual counts reported |
| Exploratory instances (E1–E3) | environment seeds 42, 17, 99 |
| Confirmatory instances (E5, E5b) | environment seeds 1001–1010 |
| Runs | 30 per instance and method |
| Compared methods | Random Search, PSO, cACO, mWOA, mGWA, CSA |

All instances have a known optimum: full coverage is attainable by a simple geometric construction (S1/S3 because N ≥ M; S2 by the witness in `revision/analysis_v4/`).

## Original submission snapshot (v1.0)

The text, results and figures of the originally submitted manuscript correspond to tag `v1.0-submission`. They are superseded by the revision and are kept only for traceability.

```
pip install -r requirements.txt
cd src
python statistical_experiment.py
```

Output location is set by `OUTDIR` in `src/statistical_experiment.py`.

## Notes on source comments

Some comments in the frozen source files predate the revision and are kept unchanged so that the experiment commits stay byte-identical. In particular, comments in `src/algorithms/hwoa_gwa.py` describe the schedule as adaptive and as exploration-to-exploitation; the revised manuscript describes it as a deterministic schedule and does not make that claim. The comment in `src/algorithms/aco.py` that refers to a sensitivity analysis in "paper Section 5" refers to no analysis in the revised manuscript; the cACO step size was retained from the submitted implementation without tuning.

## Citation

Please cite the article once published. Until then:

```bibtex
@misc{hwoa_gwa_code,
  author = {Bayat, Gozde and Ulku, Eyup Emre and Dogan, Buket and Ulku, Ilayda},
  title  = {{HWOA-GWA}: Code and data for "Spiral--Hierarchical Operator Selection
            for Target Coverage in Wireless Sensor Networks: A Component-Level Evaluation"},
  year   = {2026},
  note   = {Release v2.0-revision},
  url    = {https://github.com/emreulku/HWOA-GWA-WSN}
}
```

## License

MIT License — see `LICENSE` for details.
