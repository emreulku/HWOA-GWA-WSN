"""Regenerate every analysis output of the revision from the raw data, then compare
with the archived outputs (outputs/) byte for byte.

Usage (from the archive root):  python -I run_all.py [target_dir]
Default target_dir: regen/   (outputs/ itself is never overwritten)

Steps
  1. verify_package.py          raw-data SHA-256 against the experiment manifests
  2. tools/test_revstats.py     statistics module tests
  3. analysis/analyze_E123.py   E1-E3 exploratory families, mechanism bins
  4. analysis/analyze_E5.py     E5 confirmatory families + E4 runtime
  5. analysis/analyze_E5b.py    E5b family
  6. analysis/make_report.py    Markdown tables of the confirmatory results
  7. analysis/make_tables.py    T1, T2, T3
  8. analysis/make_figures.py   F1, F1b, F2, F3, F4 (PNG and PDF)
  9. compare target_dir with OUTPUTS_SHA256.txt; numerical/text outputs must match
     exactly, figure files are reported separately (a byte difference is a warning
     that calls for a visual check, not by itself a result error)

SOURCE_DATE_EPOCH is fixed so that matplotlib writes reproducible PDF metadata.
BLAS threads are fixed to 1, as in the experiment runner.
"""
import hashlib, os, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TGT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else ROOT / "regen"
if TGT == (ROOT / "outputs").resolve():
    sys.exit("refusing to overwrite outputs/")

env = dict(os.environ, SOURCE_DATE_EPOCH="1767225600", MPLBACKEND="Agg",
           OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
D, D5b, T, A = ROOT / "data/E1_E5", ROOT / "data/E5b", ROOT / "tools", ROOT / "analysis"
R123, R5 = TGT / "results_E123", TGT / "results_E5"

steps = [
    [ROOT / "verify_package.py"],
    [T / "test_revstats.py", T],
    [A / "analyze_E123.py", D, T, R123],
    [A / "analyze_E5.py", D, T, R5],
    [A / "analyze_E5b.py", D, D5b, T, R5],
    [A / "make_report.py", R5, R5 / "E5_tablolar_otomatik.md"],
    [A / "make_tables.py", D, TGT / "tables", D5b],
    [A / "make_figures.py", D, D5b, R123, R5, TGT / "figures"],
]
TGT.mkdir(parents=True, exist_ok=True)
for s in steps:
    cmd = [sys.executable, "-I", *map(str, s)]
    print(">> python -I", " ".join(Path(c).name for c in cmd[2:]), flush=True)
    subprocess.run(cmd, check=True, env=env, cwd=ROOT)

expected = {}
for line in (ROOT / "OUTPUTS_SHA256.txt").read_text().splitlines():
    h, rel = line.split("  ", 1)
    expected[rel.removeprefix("outputs/")] = h
got = {p.relative_to(TGT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
       for p in TGT.rglob("*") if p.is_file()}
def is_fig(rel): return rel.startswith("figures/")
bad_num, bad_fig = [], []
for rel, h in sorted(expected.items()):
    g = got.get(rel)
    status = "OK" if g == h else ("MISSING" if g is None else "DIFFERENT")
    if status == "OK": continue
    if is_fig(rel) and status == "DIFFERENT":
        bad_fig.append(rel); print(f"{status:9s} {rel}  (figure; byte difference - inspect visually)")
    else:
        bad_num.append(rel); print(f"{status:9s} {rel}")
extra = sorted(set(got) - set(expected))
for rel in extra: print(f"EXTRA     {rel}")
n_fig = sum(map(is_fig, expected)); n_num = len(expected) - n_fig
print(f"numerical/text: {n_num - len(bad_num)}/{n_num} identical")
print(f"figures: {n_fig - len(bad_fig)}/{n_fig} identical"
      + ("" if not bad_fig else " (warning: figure bytes can differ with Matplotlib/font versions; compare visually with outputs/figures, see README §3)"))
print(f"extra files: {len(extra)}")
sys.exit(1 if bad_num or extra else 0)
