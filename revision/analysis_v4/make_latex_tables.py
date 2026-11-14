"""analysis-v4: LaTeX tables for Section 6, generated from the archived analysis outputs
(analysis-v3 CSVs) and the v4 coverage/Gap summary. No new tests.
Usage: python -I make_latex_tables.py <outputs_dir> <v4_out_dir>"""
import sys, math
from pathlib import Path
import pandas as pd
O, V = Path(sys.argv[1]), Path(sys.argv[2])
R5 = O / "results_E5"

def num(x, d=2):
    s = f"{x:.{d}f}".rstrip("0").rstrip(".") if d else f"{x:.0f}"
    return s.replace("-", "\\(-\\)") if s.startswith("-") else ("+" + s if x > 0 else s)
def ci(r, d=2, strip=True):
    lo = "[" if r.ci_lo_closed else "("; hi = "]" if r.ci_hi_closed else ")"
    def f(v, up):
        if math.isinf(v): return "\\(-\\infty\\)" if v < 0 else "\\(\\infty\\)"
        q = 10 ** d                                   # outward rounding for display only
        w = (math.ceil(v * q - 1e-9) if up else math.floor(v * q + 1e-9)) / q
        t = f"{w:.{d}f}"
        return t.rstrip("0").rstrip(".") if strip else t
    s = f"{lo}{f(r.ci_lo, False)}, {f(r.ci_hi, True)}{hi}"
    assert r.ci_connected, "disconnected acceptance set: report enclosing interval with flag"
    return s.replace("-", "\\(-\\)") if "infty" not in s else s
def pv(p): return "<0.001" if p < 0.001 else f"{p:.3f}"
PR = {"pratikte anlamli": "relevant", "pratikte ihmal edilebilir": "negligible",
      "pratik anlamlilik belirsiz": "undetermined", "belirsiz": "undetermined", "n/a": "--"}

# ---- Table: confirmatory coverage summary (E5, E5b) ----
t = pd.read_csv(V / "T_results_E5_E5b_gap.csv")
lab = {"FULL": "FULL", "CONST05": "CONST05", "SPIRAL": "Spiral-only", "mGWA": "mGWA\\textsuperscript{a}",
       "NOPB": "NOPB", "G(0.8,0.8)": "\\(G(0.8,0.8)\\)", "mWOA": "mWOA", "PSO": "PSO", "cACO": "cACO",
       "CSA": "CSA", "Random": "Random"}
L = []
for m in lab:
    cells = []
    for sc in ["S1", "S2", "S3"]:
        r = t[(t.method == m) & (t.sc == sc)].iloc[0]
        cells += [f"{r.mean_K:.2f} ({r.sd_K_pooled:.2f})", f"{r.mean_gap:.2f}"]
    L.append(lab[m] + " & " + " & ".join(cells) + " \\\\")
    if m in ("NOPB", "G(0.8,0.8)"): L.append("\\hline")
(V / "table_coverage_rows.tex").write_text("\n".join(L) + "\n")

# ---- Table: confirmatory comparisons ----
P = pd.read_csv(R5 / "E5_primary_P1_P4.csv"); B = pd.read_csv(R5 / "E5_baselines.csv")
Vb = pd.read_csv(R5 / "E5_variability.csv"); G = pd.read_csv(R5 / "E5b_G0808_minus_FULL.csv")
name = {"P1": "P1: FULL \\(-\\) CONST05", "P2": "P2: FULL \\(-\\) hierarchy-only", "P3": "P3: FULL \\(-\\) spiral-only",
        "P4": "P4: FULL \\(-\\) NOPB"}
rows = []
def emit(title, groups, dec=2):
    rows.append(f"\\multicolumn{{6}}{{@{{}}l}}{{\\emph{{{title}}}}} \\\\")
    for label, g in groups:
        for i, sc in enumerate(["S1", "S2", "S3"]):
            r = g[g.sc == sc].iloc[0]
            cls = PR.get(r.practical, "--") if isinstance(r.practical, str) else "--"
            rows.append((label if i == 0 else "") + f" & {sc} & {num(r.HL, dec)} & {ci(r, dec)} & {pv(r.p_holm)} & {cls} \\\\")
emit("Primary family (12 tests)", [(name[c], P[P.comparison == c]) for c in ["P1", "P2", "P3", "P4"]])
emit("E5b family (3 tests)", [("\\(G(0.8,0.8)\\) \\(-\\) FULL", G)])
emit("Baseline family (15 tests)", [(f"FULL \\(-\\) {c.split(':')[1]}", B[B.comparison == c])
                                     for c in ["BASE:PSO", "BASE:cACO", "BASE:mWOA", "BASE:CSA", "BASE:Random"]])
emit("Variability family, SD difference (6 tests)", [(f"SD: FULL \\(-\\) {c.split(':')[1]}", Vb[Vb.comparison == c])
                                                     for c in ["SD:mGWA", "SD:mWOA"]])
(V / "table_comparisons_rows.tex").write_text("\n".join(rows) + "\n")
# practical classification summary for text checks
for df, nm in [(P, "P"), (G, "G"), (B, "B")]:
    print(nm, [(r.comparison, r.sc, PR[r.practical]) for r in df.itertuples()])

# ---- Table: E4 run time ----
T1 = pd.read_csv(O / "tables" / "T1_E4_runtime_nfe.csv")
labr = {"FULL": "FULL", "CONST05": "CONST05", "SPIRAL": "Spiral-only", "NOPB": "NOPB",
        "mGWA": "mGWA", "mWOA": "mWOA", "PSO": "PSO", "cACO": "cACO", "CSA": "CSA",
        "Random": "Random"}
RR = []
for m, l in labr.items():
    cells = []
    for sc in ["S1", "S2", "S3"]:
        r = T1[(T1.method == m) & (T1.sc == sc)].iloc[0]
        cells.append(f"{r.median_s:.2f}" + (f" ({int(r.early_stops)})" if r.early_stops else ""))
    RR.append(l + " & " + " & ".join(cells) + " \\\\")
(V / "table_runtime_rows.tex").write_text("\n".join(RR) + "\n")

# ---- v4b: split comparison tables, runtime with IQR, S3 evaluation use ----
def mm(x, d=2, strip=True):
    s = f"{x:.{d}f}"
    s = s.rstrip("0").rstrip(".") if strip else s
    return f"\\({s}\\)" if not s.startswith("-") else f"\\(-{s[1:]}\\)"
def ci_m(r, d=2, strip=True):
    return "\\(" + ci(r, d, strip).replace("\\(-\\)", "-").replace("\\(", "").replace("\\)", "") + "\\)"
def long_rows(groups, practical=True, dec=2, strip=True):
    out = []
    for label, g in groups:
        for sc in ["S1", "S2", "S3"]:
            r = g[g.sc == sc].iloc[0]
            row = f"{label} & {sc} & {mm(r.HL, dec, strip)} & {ci_m(r, dec, strip)} & {r.p_holm:.5f}"
            if practical:
                row += " & " + PR[r.practical].capitalize()
            out.append(row + " \\\\")
    return "\n".join(out) + "\n"
comp = [("P1: FULL\\(-\\)CONST05", P[P.comparison == "P1"]), ("P2: FULL\\(-\\)hierarchy-only", P[P.comparison == "P2"]),
        ("P3: FULL\\(-\\)spiral-only", P[P.comparison == "P3"]), ("P4: FULL\\(-\\)NOPB", P[P.comparison == "P4"]),
        ("\\(G(0.8,0.8)\\)\\(-\\)FULL", G)]
(V / "table_component_rows.tex").write_text(long_rows(comp))
base = [(f"FULL\\(-\\){c.split(':')[1]}", B[B.comparison == c]) for c in ["BASE:PSO", "BASE:cACO", "BASE:mWOA", "BASE:CSA", "BASE:Random"]]
(V / "table_baseline_rows.tex").write_text(long_rows(base))
var = [(f"FULL\\(-\\){c.split(':')[1]}", Vb[Vb.comparison == c]) for c in ["SD:mGWA", "SD:mWOA"]]
(V / "table_variability_rows.tex").write_text(long_rows(var, practical=False, strip=False))
RR = []
for m, l in labr.items():
    cells = []
    for sc in ["S1", "S2", "S3"]:
        r = T1[(T1.method == m) & (T1.sc == sc)].iloc[0]
        cells.append(f"{r.median_s:.2f} [{r.q1_s:.2f}, {r.q3_s:.2f}]")
    RR.append(l + " & " + " & ".join(cells) + " \\\\")
(V / "table_runtime_iqr_rows.tex").write_text("\n".join(RR) + "\n")
T2 = pd.read_csv(O / "tables" / "T2_E5_nfe_earlystop.csv")
NN = []
for m, l in list(labr.items()) + [("G(0.8,0.8)", "\\(G(0.8,0.8)\\) (E5b)")]:
    r = T2[(T2.method == m) & (T2.sc == "S3")].iloc[0]
    NN.append(f"{l} & {int(r.budget_nfe):,} & {r.mean_nfe:,.1f} & {int(r.min_nfe):,} & {int(r.full_cov)} & {int(r.early_stops)} \\\\")
(V / "table_nfe_s3_rows.tex").write_text("\n".join(NN) + "\n")
