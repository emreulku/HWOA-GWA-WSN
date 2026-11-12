# Deney Protokolü v1.0.1 — Ek E5b (sapma kaydı v1.0-d2)

**Bağlı olduğu protokol:** `Deney_Protokolu_v1.0.1.md` (SHA-256 `4dc9006226d4a44fc02df3d9e3b6859bc219e08fb0dd6630cca024908bfc4ab8`). Ana protokol **değiştirilmedi**. E1–E5, v1.0.1 ve revizyon commit'i `a1193e83e2b5616937eb7e4beef31c992851cda7` ile yürütülür.
**Kayıt tarihi:** 2026-11-11. Bu ek, **E5'in hiçbir performans sonucu görülmeden** yazıldı. Ek yazılırken E5 checkpoint'inden yalnızca tamamlanan koşu sayısı izlendi.
**Gerekçe:** E1 keşif analizinde (`E1_E3_Kesif_Analizi.md`, §2), sabit G(0.8,0.8) konfigürasyonu, görülmüş üç ortamın 9/9 hücresinde FULL'a göre Holm sonrası anlamlı ve pratikte anlamlı üstünlük gösterdi. Bu konfigürasyon sonuçlar görüldükten sonra seçildiği için bulgu keşif düzeyindedir. Bu ek, onu daha önce kullanılmamış ortamlarda bağımsız olarak sınar.

## 1. Kapsam
- **Ana yöntem değişmez:** FULL (p: 0.8 → 0.2, doğrusal) makalenin ana yöntemi olarak kalır (protokol §1.5).
- E5b, keşif sonucunda seçilmiş bir konfigürasyonun **bağımsız doğrulamasıdır**. Makalede bu statüyle sunulur.

## 2. Deney E5b
| Alan | Değer |
|---|---|
| Yöntem | G(0.8,0.8): p_init = p_end = 0.8, doğrusal (sabit) |
| Senaryo | S1, S2, S3 |
| Ortam | E5 ile aynı 10 yeni ortam: env_seed ∈ {1001, …, 1010} |
| Deneme | 0–29 (solver seed = trial + env_seed × 1000, E5 ile aynı) |
| Koşu | 1 × 3 × 10 × 30 = **900** |
| Diagnostics | Kapalı |
| Anahtar | (E5b, G(0.8,0.8), sc, env_seed, trial, run) |

Karşılaştırma için FULL koşuları **E5'ten** alınır (aynı senaryo, ortam ve deneme, aynı solver seed). Eşleştirme birimi (senaryo, ortam, deneme).

## 3. Analiz kuralları (E5 sonuçları görülmeden sabitlendi)
- **Karşılaştırma:** G(0.8,0.8) − FULL, kapsanan hedef sayısı.
- **Birim:** Ortam. Her (senaryo, ortam) için 30 eşleştirilmiş farkın ortancası alınır; senaryo başına n = 10 ortam düzeyinde fark.
- **Test:** Protokol §6.2: Pratt sıralı Wilcoxon istatistiği, işaret çevirme permütasyon testi (k ≤ 15 kesin), kesin rasyonel aritmetik.
- **Etki büyüklüğü ve güven aralığı:** Protokol §6.2a (HL, test tersine çevirmeyle %95 güven kümesi, rank-biserial r).
- **Çoklu karşılaştırma:** 3 senaryo = **3 test**. Bu karşılaştırmalar ayrı bir analiz ailesi olarak ele alınır ve Holm düzeltmesi bu üç teste uygulanır. Protokolün birincil 12 testlik ailesinin (P1–P4) ve diğer ikincil ailelerin büyüklüğü değişmez. FULL verileri bu aileyle diğer aileler arasında ortak kullanıldığından, aileler arasında istatistiksel bağımsızlık varsayılmaz.
- **Raporlama:** Protokol §6.3 tablosu. İstatistiksel sonuç (Holm-düzeltilmiş p) ve pratik anlamlılık (güven aralığı ile tek hedef eşiği) ayrı sütunlarda verilir.
- **Ek betimsel bilgi:** Ortam düzeyinde SD farkı (G(0.8,0.8) − FULL) yalnızca betimsel olarak verilir; bu ek için doğrulayıcı test tanımlanmaz.

## 4. Yürütme
- **Kod:** Revizyon commit'inin üzerine yalnızca E5b matrisini ekleyen sürümlenmiş bir commit (`run_experiments.py`: E5b tanımı, beklenen sayı 900). Algoritma dosyaları, runner (`revkit.py`) ve istatistik modülü değişmez.
- **Parmak izi:** E5b checkpoint'inin parmak izinde protokol dosyası olarak **bu ek** kullanılır. E5b ayrı bir çıktı klasöründe koşar.
- **Tamamlanma kriteri:** Kayıtlı anahtar kümesi = beklenen 900 anahtar (protokol §8a).
- **Sıra:** E5, v1.0.1 ile tamamlanır ve dışa aktarılır. E5b, yeni commit doğrulandıktan sonra koşar. E5 ve E5b analizleri, kendi önceden tanımlanmış aileleriyle yapılır.

## 5. Sapma kaydı
| Tarih | Kod | Değişiklik | Gerekçe | Etkilenen sonuçlar |
|---|---|---|---|---|
| 2026-11-11 | v1.0-d2 | E5b eklendi: G(0.8,0.8), 900 koşu, 3 testlik ayrı Holm ailesi | E1 keşif bulgusunun bağımsız doğrulaması | Yok (E5 sonuçları görülmedi; E1–E5 tanımları değişmedi) |
