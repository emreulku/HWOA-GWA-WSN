"""Generate the confirmatory-results tables (Markdown) directly from the analysis CSVs.
Usage: python -I make_report.py <results_E5_dir> <out_md>
Interval notation keeps open/closed ends from the analysis output.
"""
import sys, json
from pathlib import Path
import pandas as pd

RES, OUT = Path(sys.argv[1]), Path(sys.argv[2])


def sg(v):
    return "0" if v == 0 else f"{v:+g}"


def iv(r):
    lo = "[" if r.ci_lo_closed else "("
    hi = "]" if r.ci_hi_closed else ")"
    return f"{lo}{r.ci_lo:g}, {r.ci_hi:g}{hi}"


STAT = {"ornekler arasinda tutarli fark": "tutarlı fark",
        "ornekler arasinda tutarli fark gosterilemedi": "tutarlı fark gösterilemedi"}
PRAC = {"pratikte anlamli": "pratikte anlamlı", "pratikte ihmal edilebilir": "pratikte ihmal edilebilir",
        "belirsiz": "belirsiz", "n/a": "—"}


def table(df, label_col, extra=None):
    head = f"| {label_col} | Senaryo | k | HL (hedef) | %95 GA | p | Holm p | İstatistiksel sonuç | Pratik anlamlılık |"
    rows = [head, "|" + "---|" * 9]
    for r in df.itertuples():
        rows.append(f"| {getattr(r, 'comparison')} | {r.sc} | {r.k} | {sg(r.HL)} | {iv(r)} | {r.p:.6g} | "
                    f"{r.p_holm:.4g} | {STAT[r.stat_result]} | {PRAC.get(str(r.practical), '—')} |")
    return "\n".join(rows)


prim = pd.read_csv(RES / "E5_primary_P1_P4.csv")
var = pd.read_csv(RES / "E5_variability.csv"); var["practical"] = "n/a"
base = pd.read_csv(RES / "E5_baselines.csv")
e5b = pd.read_csv(RES / "E5b_G0808_minus_FULL.csv")

envtab = ["| Karşılaştırma | Senaryo | Ortam düzeyi ortanca farklar (env 1001…1010) |", "|---|---|---|"]
for r in pd.concat([prim, e5b]).itertuples():
    envtab.append(f"| {r.comparison} | {r.sc} | {', '.join(sg(v) for v in json.loads(r.env_values))} |")

md = f"""<!-- Bu dosya make_report.py tarafından analiz CSV'lerinden otomatik üretildi. Elle düzenlemeyin. -->
## Otomatik tablolar

**Notlar**
- **HL**, ortam düzeyindeki değerlere (her ortamın 30 eşleştirilmiş denemesinin ortanca farkı; değişkenlik ailesinde SD farkı) uygulanan Hodges–Lehmann tahminidir. Bütün koşuların ortalama farkı değildir.
- **%95 GA**, karşılaştırma bazındadır (test tersine çevirme). **Eşzamanlı güven aralığı değildir.** Holm düzeltmesi yalnızca p değerlerine, ilgili aile içinde uygulanmıştır. Bu nedenle sıfırı dışlayan bir aralık ile Holm p ≥ 0.05 birlikte görülebilir.
- Aralık uçları analizden geldiği gibi gösterilir: köşeli parantez kapalı, normal parantez açık uç.
- k: sıfırdan farklı ortam düzeyi değer sayısı (n = 10).

### Birincil aile (P1–P4, 12 test, Holm)
{table(prim, "Karşılaştırma")}

### Değişkenlik ailesi (SD farkı, 6 test, Holm)
{table(var, "Karşılaştırma")}

### Baseline ailesi (15 test, Holm)
{table(base, "Karşılaştırma")}

### Ek E5b (G(0.8,0.8) − FULL, 3 test, Holm)
{table(e5b, "Karşılaştırma")}

### Ortam düzeyi değerler (P1–P4 ve E5b)
{chr(10).join(envtab)}
"""
OUT.write_text(md)
print("written", OUT)
