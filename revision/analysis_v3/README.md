# HWOA-GWA revision: data, analysis and figures archive

This archive holds the raw experiment data of the revision, the analysis and visualization scripts, the outputs they produce (result tables, manuscript tables and figures), and SHA-256 hashes for every file. One command regenerates all outputs from the raw data and checks them byte for byte against the archived copies.

## 1. Provenance: three separately traceable versions

| Layer | Version | What it fixes | How to check |
|---|---|---|---|
| Submitted code | commit `3e15fcb1499eefa2501b54ac47fe825b2ee0cbd6`, tag `v1.0-submission`; GitHub ZIP SHA-256 `28965848…8f02` | Algorithm and baseline implementations as submitted | `zip_sha256` field of every experiment manifest |
| Experiment code, E1–E5 | commit `a1193e83e2b5616937eb7e4beef31c992851cda7`; protocol v1.0.1, SHA-256 `4dc90062…4ab8` | Diagnostic hooks, NOPB variant, experiment runner, statistics module | `commit` and `protocol_sha256` in `data/E1_E5/*_manifest.json`; `verification/COMMIT_verify.json` |
| Experiment code, E5b | commit `24acbdbe531fb6ba9e03e54ba72caae29a0fbcf8`; protocol addendum, SHA-256 `620fdc22…e55b` | E5b entry in the runner (pre-registered G(0.8,0.8) − FULL test) | `data/E5b/E5b_manifest.json`; `verification/COMMIT2_verify.json` |
| Analysis and visualization | **analysis-v3**, identified by the script hashes in §4 (to be committed separately on top of `24acbdb`; planned, see §5) | Statistical analysis, tables, figures | `OUTPUTS_SHA256.txt` and `run_all.py` |

The analysis scripts were written and corrected **after** the experiments ended. None of the corrections changed the raw data. They changed only how results are computed or shown: closed/open confidence-interval end flags, T2 separating full coverage from early stopping, T3 memory column, F3 computed from unrounded run values, F4 interval-end markers, F1 step drawing. Changing an analysis script does not affect the experiment commits; the raw data remain bound to those commits by the manifests.

The statistics module (`tools/revstats.py`, `tools/test_revstats.py`) is the one from the experiment commits. Its git blob ids equal those in the `24acbdb` tree (`revision/tools/`), and its SHA-256 is the same in `a1193e8` and `24acbdb`.

## 2. Contents

```
data/E1_E5/      E1–E5 raw runs (*_runs.csv), NFE-axis histories (*_histories.npz),
                 E1–E3 operator diagnostics (*_diagnostics.npz), session/warm-up logs,
                 E4 system info, manifests (commit a1193e8)
data/E5b/        Same for E5b (commit 24acbdb)
tools/           revstats.py + tests (from the experiment commits)
analysis/        analysis-v3 scripts
outputs/         Archived outputs of analysis-v3
  results_E123/  E1–E3 exploratory families a/b, descriptives, variability, anytime, mechanism bins
  results_E5/    E5 primary P1–P4, variability, baselines; E5b; E4 runtime; E5_tablolar_otomatik.md
  tables/        T1 (E4 runtime/NFE), T2 (E5+E5b NFE/full coverage/early stop), Revizyon_Tablolari.md (T1–T3)
  figures/       F1, F1b, F2, F3, F4 (PNG 300 dpi and PDF)
docs/            Interpretation notes (Turkish): exploratory analysis, confirmatory results,
                 figure captions, evaluation of the sources suggested by Reviewer 2
verification/    Commit-ZIP verification reports of a1193e8 and 24acbdb
verify_package.py   Raw data against manifest hashes and expected run counts
run_all.py          Full regeneration and byte-for-byte comparison
OUTPUTS_SHA256.txt  Hashes of outputs/
SHA256SUMS.txt      Hashes of every file in the archive (except itself)
```

## 3. Running

Environment used to produce `outputs/`: Python 3.13.18, NumPy 2.5.3, pandas 3.0.5, SciPy 1.18.1, Matplotlib 3.11.2.

**What was reproduced byte for byte.** The 20 numerical and text outputs of this archive (result CSV/JSON files, tables, the Markdown report) were reproduced byte for byte in the two audited environments. In other environments, byte identity is checked with `run_all.py`; it is not guaranteed for every Python or package version. The 10 figure files (5 figures × PNG/PDF) can differ in bytes when the Matplotlib version, fonts or rendering libraries differ. A byte difference in a figure is therefore not, by itself, treated as an error in the results, but it is not proof that the difference comes from the environment either: such figures should be inspected visually against the archived ones. The archived figures were inspected visually. `run_all.py` reports the two groups separately and fails only if a numerical/text output differs or is missing, or an extra file appears. Fixing `SOURCE_DATE_EPOCH` removes the PDF creation date from the hash, but does not make figures identical across Matplotlib versions.

From the archive root:

```
python -I run_all.py              # regenerates into regen/ and compares with outputs/ (about 40 s)
```

Expected result: `numerical/text: 20/20 identical`. In the original environment also `figures: 10/10 identical`; elsewhere the figure line may report byte differences, which call for a visual check.

Individual steps (as run by `run_all.py`; `R` = target folder):

```
python -I verify_package.py
python -I tools/test_revstats.py tools
python -I analysis/analyze_E123.py data/E1_E5 tools R/results_E123
python -I analysis/analyze_E5.py   data/E1_E5 tools R/results_E5
python -I analysis/analyze_E5b.py  data/E1_E5 data/E5b tools R/results_E5
python -I analysis/make_report.py  R/results_E5 R/results_E5/E5_tablolar_otomatik.md
python -I analysis/make_tables.py  data/E1_E5 R/tables data/E5b
python -I analysis/make_figures.py data/E1_E5 data/E5b R/results_E123 R/results_E5 R/figures
```

`run_all.py` sets `SOURCE_DATE_EPOCH=1767225600` (reproducible PDF metadata) and one BLAS thread. If you run the steps by hand without `SOURCE_DATE_EPOCH`, the PDF hashes also change through their creation-date field, even in the original environment.

Checking the whole archive:

```
sha256sum -c SHA256SUMS.txt                       # Linux / macOS / Git Bash
```

## 4. analysis-v3 script identity

| File | SHA-256 | git blob id |
|---|---|---|
| `analysis/analyze_E123.py` | `207a8e67c3bad6673519e3855a2f199539ee1ccf1d10db2e41946ca93fc30cbb` | `3b71eb0ec152072023959c756edcab605a4db272` |
| `analysis/analyze_E5.py` | `dbaed5d26c0c97b5b820c3498ff4faac8c802e228dfb5e98bee486c908ba6b89` | `5b85c196bb01ecb074801a3f5484a648b7bc5275` |
| `analysis/analyze_E5b.py` | `96e8217539539e9e003548627f39d4d8538e8943b528e6e5f50498aa674da557` | `6470082f52d1950143608a9b79e2ea01986ab4da` |
| `analysis/make_report.py` | `e7d29eb9e3a6d39e074aaed48042d1d55bc7e327b754a72c4437717071aace67` | `6a720bd466d6b13360a93e3aadb1b899fc3bb2fe` |
| `analysis/make_tables.py` | `5f933db28810d8fbd9f8dae9be1fd7c294f75ad831ecf6c54303d8197b4bb15f` | `6f29d66d3b5097716783644db24eccdf9c364265` |
| `analysis/make_figures.py` | `807da41cb27a71eba33263f6636a0b16b7a16226b1e6cf6d8942b080527c9c5f` | `5ce586021d35db46dc7b2dc87c582e4079903ee8` |
| `tools/revstats.py` | `c29a67b5e8d2d232aa519eb7c204503157d14f72fd8167f250a506ad7f8c2d2a` | `4a9760b1167a98ae31a2b546d7b33701be71c056` (= `24acbdb`) |
| `tools/test_revstats.py` | `2fd8cd07ce7d6d44ae52af0f1f33e812c3069a30a633c7e0b52558002d548670` | `f1d88d072a661d1e936b1fdd56b623efac381f4b` (= `24acbdb`) |

The git blob id lets anyone check that a file in the repository is byte-identical to the file here (`git ls-tree -r <commit> revision/analysis`).

## 5. Linking analysis-v3 to the repository

Planned (not yet done at the time this archive was built): the six `analysis/` scripts will be committed unchanged to `revision/analysis/` as a separate commit on top of `24acbdb` on the `revision` branch, and tagged `v2.0-revision-analysis`. The experiment commits will not be modified. After that commit, `git ls-tree -r v2.0-revision-analysis revision/analysis` must list the blob ids in §4. The resulting commit SHA will be recorded in the revision documentation.

## 6. Status of results

- E5 and E5b: confirmatory (pre-registered tests, new environments 1001–1010, Holm correction within each family).
- E1–E3: exploratory / sensitivity (environments 42, 17, 99 were used in the submitted manuscript).
- Comparisons of G(0.8,0.8) with PSO and cACO: descriptive only; no pre-registered test.
- Confidence intervals are non-simultaneous test-inversion sets. Interval ends keep their open/closed status (`ci_lo_closed`, `ci_hi_closed`).
