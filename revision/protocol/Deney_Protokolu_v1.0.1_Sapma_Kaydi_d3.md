# Deney Protokolü v1.0.1: Sapma kaydı d3 (analiz ve raporlama)

**Bağlı olduğu belgeler:**
- `Deney_Protokolu_v1.0.1.md` (SHA-256 `4dc90062…4ab8`)
- `Deney_Protokolu_v1.0.1_Ek_E5b.md` (SHA-256 `620fdc22…e55b`)

Bu iki belge **değiştirilmedi**; tarihsel sürümleri olduğu gibi korunuyor. Bu kayıt, deneyler tamamlandıktan sonra analiz ve raporlama katmanında yapılan sapmaları ve eklemeleri belgeliyor. Deney matrisi, koşular, algoritma kodu ve önceden tanımlanmış test aileleri değişmedi.

**İlk kayıt tarihi:** 2026-11-12 (proje çalışma belgesi).  
**Depoda yayımlanma tarihi:** 2026-11-14.  
Bu belgedeki kararların tümü E1–E5b sonuçları görüldükten sonra alındı; yayımlanma tarihi bunun aksini göstermez.  
İngilizce çevirisi: `Protocol_v1.0.1_Deviation_Record_d3_EN.md`.

| Kod | Protokoldeki karşılığı | Sapma ya da ekleme | Gerekçe | Bilgi durumu | Etkilenen sonuçlar |
|---|---|---|---|---|---|
| d3-1 | §6.5, son madde: "Brown–Forsythe testi yalnızca ek bilgi olarak verilir. Eşleştirilmiş veriyi bağımsız kabul ettiği belirtilir." | Ek Brown–Forsythe analizi yapılmadı. Önceden tanımlanmış, eşleştirilmiş, ortam düzeyindeki SD karşılaştırmaları (6 test, Holm) korundu. Yerine başka bir analiz eklenmedi. | Protokol bu testi yalnızca ek bilgi olarak öngörüyordu ve testin eşleştirilmiş yapıyı yok saydığını zaten belirtiyordu. Değişkenlik sorusunun doğrulayıcı yanıtı önceden tanımlanmış SD farkı testleridir. analysis-v3 betiklerinde Brown–Forsythe uygulanmamıştı; bu durum makale metni revize edilirken fark edildi. | Karar, E1–E5b sonuçları görüldükten sonra kaydedildi. Hiçbir doğrulayıcı sonuç bu karara bağlı değil. | Önceden tanımlanmış sayısal karşılaştırmalar değişmedi. Makaleden Brown–Forsythe ifadeleri ve `levene1960` atfı çıkarılıyor. |
| d3-2 | Protokolde yok | **Sonradan yapılan geometrik denetim:** S2 örneklerinin (13 ortam) tam kapsamaya ulaşılabilirliği, bir eşleştirme yapısıyla tanıklandı (`revision/analysis_v4/s2_full_coverage_witness.py`, tanık koordinatları ile). S1 ve S3'te N ≥ M olduğundan tam kapsama genel olarak kanıtlanıyor. | Makale revizyonu sırasında incelenen örneklerin optimumunun bilindiği fark edildi. | Sonuçlar görüldükten sonra. | Önceden tanımlanmış sayısal karşılaştırmalar değişmedi; bulguların yorum kapsamı ve sınırlılıkları güncellendi. Optimumun bilindiği ve basit bir geometrik yapıyla ulaşılabildiği için makalenin uygulama katkısı daraltıldı. Denetim, doğrulayıcı aileden ayrı ve sonradan yapılan bir denetim olarak raporlanıyor. |
| d3-3 | §5.1 (birincil sonuç değişkeni: hedef sayısı) | **Raporlama dönüşümü:** Optimumdan uzaklık Gap = M − K, aynı koşulardan türetilip raporlanıyor (analysis-v4). Ortalama Gap = M − ortalama K. | Bilinen optimum (d3-2) nedeniyle sonuçların yorumunu kolaylaştırıyor. | Sonuçlar görüldükten sonra. | Önceden tanımlanmış sayısal karşılaştırmalar değişmedi. Gap yeni bir başarı ölçütü ya da test ailesi değil; K'nin ters yönden ifadesi. Sonuçların optimuma göre okunmasını sağlıyor. |
| d3-4 | §4, "Bilinen bağımlılık": S1 ve S2 aynı hedef yerleşimini paylaşır (K9) | **Ek gözlem:** Aynı tohumla S3'ün ilk 75 hedefi de S1/S2'nin hedefleriyle aynı. 13 tohumun tamamında doğrulandı. | Hedefler aynı rastgele sayı akışından ilk sırada çekiliyor. | Revizyon sırasında fark edildi. | Önceden tanımlanmış sayısal karşılaştırmalar değişmedi; bulguların yorum kapsamı ve sınırlılıkları güncellendi. Analizler senaryoları ayrı ele alıyor; senaryolar arasında bağımsızlık ya da bağımsız tekrar iddia edilmiyor. |
