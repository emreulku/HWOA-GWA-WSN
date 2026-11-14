# analysis-v4 (manuscript tables and figures, post-hoc check)

Builds on the analysis-v3 archive `HWOA_revizyon_nihai_arsiv.zip` (SHA-256 `67cc5297…190b`), which is unchanged.
No new runs and no new tests. Raw data, experiment commits (`a1193e8`, `24acbdb`) and analysis-v3 outputs are used as they are.

| Script | Output | Purpose |
|---|---|---|
| `make_results_table.py` | `out/T_results_E5_E5b_gap.csv` | Confirmatory coverage summary with Gap = M − K (mean Gap = M − mean K) |
| `make_latex_tables.py` | `out/table_*_rows.tex` | LaTeX rows for Section 6 tables, generated from analysis-v3 CSVs (CI ends keep open/closed status; SD bounds rounded outward for display) |
| `make_figures_en.py` | `figures_en/Figure03–07` | English versions of figures F4, F1, F1b, F3, F2 (same data and layout as analysis-v3; labels translated, titles removed) |
| `s2_full_coverage_witness.py` | `s2_*.csv` | Post-hoc S2 full-coverage witness (deviation record d3-2) |
| `make_figure1.py`, `make_figure2.py` | Figures 1–2 | Method schematic (superseded by the team version) and target layouts |

Commands (from the analysis-v3 archive root, `R=..` path to this folder):
```
python -I $R/make_results_table.py data/E1_E5 data/E5b $R/out
python -I $R/make_latex_tables.py outputs $R/out
SOURCE_DATE_EPOCH=1767225600 python -I $R/make_figures_en.py data/E1_E5 data/E5b outputs/results_E123 outputs/results_E5 $R/figures_en
python -I $R/s2_full_coverage_witness.py <repo_root_with_src> $R
python -I $R/make_figure2.py <repo_root_with_src> $R
```
`SHA256SUMS.txt` lists every file in this folder.
