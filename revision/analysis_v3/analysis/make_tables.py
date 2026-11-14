"""Tables for the revision (from raw outputs and the experiment code).
Usage: python -I make_tables.py <E1_E5_data_dir> <out_dir> <E5b_data_dir>
T1: E4 runtime median/IQR + NFE used + early stops (10 measured runs per cell)
T2: E5 NFE used + early stops (300 runs per cell)
T3: Algorithm parameters, initialization and stopping (from the code of commit a1193e8)
"""
import sys
from pathlib import Path
import pandas as pd

D, OUT, D5b = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]); OUT.mkdir(parents=True, exist_ok=True)
ORDER = ["FULL", "CONST05", "SPIRAL", "NOPB", "mGWA", "mWOA", "PSO", "cACO", "CSA", "Random"]

e4 = pd.read_csv(D / "E4_runs.csv"); assert len(e4) == 300 and (e4.role == "measured").all()
def flags(df):
    df["full_cov"] = df.stop_reason == "full_coverage"
    df["budget_nfe"] = df.init_cost + df.iter_cost * df.max_iter_used        # NFE if run to the end
    df["early"] = df.nfe_actual < df.budget_nfe                              # stopped before budget
    assert (df.early <= df.full_cov).all(), "early stop without full coverage"
    return df


e4 = flags(e4)
t1 = e4.groupby(["method", "sc"]).agg(median_s=("runtime", "median"),
                                      q1_s=("runtime", lambda s: s.quantile(.25)),
                                      q3_s=("runtime", lambda s: s.quantile(.75)),
                                      mean_nfe=("nfe_actual", "mean"), min_nfe=("nfe_actual", "min"),
                                      budget_nfe=("budget_nfe", "max"),
                                      full_cov=("full_cov", "sum"), early_stops=("early", "sum"),
                                      n=("runtime", "size")).reset_index()
t1["method"] = pd.Categorical(t1.method, ORDER); t1 = t1.sort_values(["method", "sc"])
t1.to_csv(OUT / "T1_E4_runtime_nfe.csv", index=False)

e5 = flags(pd.concat([pd.read_csv(D / "E5_runs.csv"), pd.read_csv(D5b / "E5b_runs.csv")], ignore_index=True))
assert len(e5) == 9900
t2 = e5.groupby(["exp", "method", "sc"]).agg(mean_nfe=("nfe_actual", "mean"), min_nfe=("nfe_actual", "min"),
                                      budget_nfe=("budget_nfe", "max"), full_cov=("full_cov", "sum"),
                                      early_stops=("early", "sum"), n=("nfe_actual", "size")).reset_index()
t2["method"] = pd.Categorical(t2.method, ORDER + ["G(0.8,0.8)"]); t2 = t2.sort_values(["method", "sc"])
t2.to_csv(OUT / "T2_E5_nfe_earlystop.csv", index=False)


def md_t1():
    rows = ["| Yöntem | Senaryo | Süre ortanca (s) | IQR (s) | Bütçe sonu NFE | Ort. kullanılan NFE | En az NFE | Tam kapsama (/10) | Bütçe dolmadan durma (/10) |",
            "|---|---|---|---|---|---|---|---|---|"]
    for r in t1.itertuples():
        rows.append(f"| {r.method} | {r.sc} | {r.median_s:.2f} | {r.q1_s:.2f}–{r.q3_s:.2f} | {int(r.budget_nfe):,} | "
                    f"{r.mean_nfe:,.1f} | {int(r.min_nfe):,} | {int(r.full_cov)} | {int(r.early_stops)} |")
    return "\n".join(rows)


def md_t2():
    rows = ["| Yöntem | Bütçe sonu NFE | S1: ort. NFE · tam kapsama · bütçe dolmadan durma (/300) | S2 | S3 |",
            "|---|---|---|---|---|"]
    for m in ORDER + ["G(0.8,0.8)"]:
        c = []
        for sc in ("S1", "S2", "S3"):
            r = t2[(t2.method == m) & (t2.sc == sc)].iloc[0]
            c.append(f"{r.mean_nfe:,.1f} · {int(r.full_cov)} · {int(r.early_stops)}")
        c = [f"{int(t2[t2.method == m].budget_nfe.max()):,}"] + c
        lab = f"{m} (E5b)" if m == "G(0.8,0.8)" else m
        rows.append(f"| {lab} | " + " | ".join(c) + " |")
    return "\n".join(rows)


T3 = """| Yöntem | Popülasyon | Başlatma | NFE maliyeti (başlatma / iterasyon) | Bellek / seçkincilik | Parametreler | Durdurma |
|---|---|---|---|---|---|---|
| FULL (HWOA-GWA) | 25 | Uniform rastgele, 25 çözüm | 25 / 25 | Ajan başına açgözlü pbest; liderler (α, β, δ) ve spiral referansı pbest'ten | p: 0.8 → 0.2 (doğrusal); b = 1; a: 2 → 0; pbest belleği; liderler pbest'ten | NFE üst sınırı 6.250 veya %100 kapsama |
| CONST05 / G(pi,pe) | 25 | Aynı | 25 / 25 | FULL ile aynı (pbest) | p sabit 0.5 / p: pi → pe; diğerleri FULL ile aynı | Aynı |
| SPIRAL | 25 | Aynı | 25 / 25 | Ajan başına pbest; spiral referansı α pbest'ten | Yalnızca α etrafında spiral, b = 1 (mWOA değildir) | Aynı |
| HIER (= mGWA) | 25 | Aynı | 25 / 25 | Ajan başına açgözlü pbest; liderler pbest'ten (mGWA'nın kendi tasarımı) | Yalnızca α/β/δ hiyerarşik güncelleme, a: 2 → 0 | Aynı |
| NOPB | 25 | Aynı | 25 / 25 | **pbest yok**; liderler mevcut popülasyondan; yalnızca raporlama arşivi | FULL ile aynı, pbest yok: liderler mevcut popülasyondan, ayrı raporlama arşivi | Aynı |
| mWOA | 25 | Uniform rastgele | 25 / 25 | Ajan başına pbest; lider en iyi pbest; keşif dalı pbest'i kullanır | b = 1; çevreleme, pbest yönlendirmeli keşif ve spiral dalları | Aynı |
| PSO | 25 | Uniform rastgele; hızlar ±%2 alan | 25 / 25 | Standart pbest ve gbest | w = 0.7, c1 = c2 = 1.5, v_max = alanın %20'si | Aynı |
| cACO | 25 karınca | **Başlangıç konuşlanması** (`initial_sensors`), tek çözüm | 1 / 25 | Tek en iyi çözüm (seçkinci); karıncalar onu pertürbe eder; sensör başına feromon belleği | ρ = 0.1, α = 1, adım = 12 m (koddaki nota göre duyarlılık analiziyle seçilmiş); sensör başına feromon ağırlıklı hareket olasılığı; her karınca mevcut en iyi yerleşimi pertürbe eder | Aynı |
| CSA | 25 yuva | Uniform rastgele | 25 / 7 | Rastgele bir yuvanın açgözlü değiştirilmesi; en iyi çözüm Lévy adımına yön verir; en kötü 6 yuva koşulsuz yenilenir | pa = 0.25 (iterasyon başına 6 yuva terk); Lévy β = 1.5; adım ölçeği 0.1·alan·(1 − t/T) + 0.5 | Aynı |
| Random | 25 | — | 0 / 25 | Yalnızca best-so-far arşivi; aramada kullanılmaz | Her iterasyonda 25 uniform rastgele yerleşim | Aynı |

Notlar:
- Bütün yöntemler aynı **6.250 NFE üst sınırıyla** çalışır. Gerçekte kullanılan NFE, başlatma ve iterasyon maliyetlerinin bütçeye tam bölünmemesi (cACO 6.226, CSA 6.248) ve %100 kapsamada erken durma nedeniyle yöntemler arasında farklıdır (T1, T2).
- **Bellek:** pbest belleği FULL'a özgü değildir. SPIRAL, HIER/mGWA, mWOA ve PSO da ajan başına pbest kullanır. P4 (FULL − NOPB), belleğin **FULL içindeki** etkisini gösterir; belleğin FULL'a özgü ya da yeni olduğunu göstermez.
- **Tam kapsama ve bütçe dolmadan durma ayrı sayılır (T1, T2):** Bir koşu bütçenin son değerlendirmesinde %100 kapsamaya ulaşabilir (örneğin PSO/S3, env 1004, deneme 14). Bu koşu tam kapsama sütununda sayılır, bütçe dolmadan durma sütununda sayılmaz.
- **Ortak bir parametre ayarlama (tuning) protokolü uygulanmamıştır.** Parametreler literatürdeki yaygın değerlerden alınmış ya da kodda sabitlenmiştir. Yalnızca cACO'nun adım büyüklüğü için koddaki notta bir duyarlılık analizinden söz edilir. HWOA-GWA'nın p planı için duyarlılık analizi bu revizyonda yapılmıştır (E1).
- cACO, diğer yöntemlerden farklı olarak rastgele bir popülasyonla değil, ortamın başlangıç konuşlanmasından başlar. Bu başlatma farkının performansa etkisi ayrı olarak test edilmemiştir.
- Kaynak: `src/algorithms/*.py` ve `revision/tools/revkit.py` (commit `a1193e8`)."""

md = f"""# Revizyon tabloları (ham çıktılardan ve koddan üretildi)

## T1. Hesaplama maliyeti (E4): duvar saati süresi, kullanılan NFE ve erken durma
G(0.8,0.8) için E4 kapsamında runtime ölçümü yapılmadı. Bu varyant için bir runtime karşılaştırması ya da üstünlüğü iddia edilmez.
Ortam: Intel Xeon @ 2.10 GHz, 2 çekirdek, tek iş parçacıklı BLAS, sıralı koşular, oturum bazlı ısınma; env 42, deneme 0–9.

{md_t1()}

## T2. E5 ve E5b'de kullanılan NFE, tam kapsama ve erken durma (10 yeni ortam × 30 deneme)
"Tam kapsama": %100 kapsamaya ulaşan koşu. "Bütçe dolmadan durma": kullanılan NFE, yöntemin bütçe sonu NFE'sinden az. Bir koşu son bütçe noktasında tam kapsamaya ulaşabilir; bu durumda yalnızca ilk sayıya girer (PSO/S3'te 1, G(0.8,0.8)/S3'te 2 koşu).

{md_t2()}

## T3. Algoritma parametreleri, başlatma ve durdurma

{T3}
"""
(OUT / "Revizyon_Tablolari.md").write_text(md)
print(t1[t1.early_stops > 0].to_string(index=False)); print(t2[t2.early_stops > 0].to_string(index=False))
