# Deney Protokolü v1.0 (DONDURULMUŞ)

**Makale:** Adaptive Spiral–Hierarchical Operator Switching for Target Coverage Optimization in Wireless Sensor Networks (Cluster Computing, revizyon)
**Durum:** Dondurulmuş (2026-11-11). Hiçbir yeni deney (E1–E6) sonucu görülmeden yazıldı. Bu dosyanın SHA-256 değeri bütün deney checkpoint'lerinin ve manifest'lerinin parmak izine girer; dosyadaki her değişiklik devam eden deneyleri durdurur. Sonraki değişiklikler yalnızca §12'deki sapma kaydı ile, yeni bir sürüm numarasıyla yapılır.
**Referans sürüm:** `v1.0-submission` (aday commit `3e15fcb1499eefa2501b54ac47fe825b2ee0cbd6`, GitHub'da doğrulanacak). ZIP SHA-256 `28965848c11fe61dc15a2559cdf8c141d68d84dc4a53104f3856fe24b84d8f02`. GitHub etiketi doğrulanana kadar pilotun referansını ZIP ve kaynak dosya hash'leri sabitler.
**Dayanak:** `revizyon/A0_A1_Denetim_Raporu.md` (bulgular K1–K10, kod değişiklikleri C1–C7).

---

## 1. Kapsam ve genel kurallar

1. **Problem tanımı:** Kapsama odaklı sensör yerleşimi (coverage-oriented sensor placement). Algoritmalar başlangıç konuşlanmasını kullanmaz (cACO hariç, bkz. §8 E6). Hareket ya da enerji modeli yoktur.
2. **Displacement:** Her koşuda kaydedilir ve arşivde kalır, ama **hiçbir performans karşılaştırmasında, tabloda, şekilde ya da iddiada kullanılmaz.** Gerekçe: K1. Değer, çözüm üretiminde kullanılmayan bir referans yerleşime göre hesaplanıyor.
3. **Terminoloji:** Yöntem, *"stochastic operator selection with a deterministic time schedule"* olarak tanımlanır. Her ajan her iterasyonda operatörünü rastgele seçer, seçim olasılığı p(t) ise önceden belirlenmiş bir zaman planına göre değişir. Eiben, Hinterding & Michalewicz (1999) sınıflandırmasında p(t) için kullanılan kontrol türü *deterministic parameter control*'dür. "Adaptive" sözcüğü yöntem için kullanılmaz.
4. **Değişmezler:** Popülasyon 25, bütçe 6.250 NFE (başlatma dahil, katı üst sınır, yarım nesil başlatılmaz), alan 100 × 100 m, algılama yarıçapı 5 m, ikili disk modeli, %100 kapsamada erken durma. Bunlar gönderilmiş deneylerle aynıdır.
5. **Ana yöntem:** HWOA-GWA, p_init = 0.8, p_end = 0.2, doğrusal. Hiçbir sonuç ana yöntemin parametresini değiştirmez. Başka bir konfigürasyon daha iyi çıkarsa bu bir **bulgu** olarak raporlanır.
6. **Sapma kaydı:** Dondurmadan sonraki her değişiklik tarih, gerekçe ve etkilenen sonuçlarla birlikte §12'ye yazılır.

---

## 2. Araştırma soruları ve karşılaştırma eşlemesi

| Soru | Karşılaştırma | Deney | Tür | Hakem |
|---|---|---|---|---|
| **S1.** Zamana bağlı plan, sabit olasılıklı karışıma göre katkı sağlıyor mu? | **P1:** FULL − CONST05 | E1, E5 | **Birincil** | R1 (editöre not), R1-M2, R2-5, R3-1 |
| **S2.** Sonuçlar başlangıç/bitiş değerlerine ve yöne ne kadar duyarlı? | 9 grid hücresinin hepsi − FULL; sabit 0.2 ve 0.8 − FULL; ters plan (0.2→0.8) − FULL | E1 | İkincil / betimsel | R1-M2, R2-5 |
| **S3.** İki operatörün birlikte kullanımı, her birinin tek başına kullanımından iyi mi? Bu senaryoya bağlı mı? | **P2:** FULL − HIER (= mGWA); **P3:** FULL − SPIRAL | E1/E2, E5 | **Birincil** | R1-M3 |
| **S4.** pbest belleğinin rolü ne? | **P4:** FULL − NOPB | E3, E5 | **Birincil** | R3-1 |
| **S5.** FULL modunda operatörler arama sırasında nasıl davranıyor? | Operatör bazında kullanım, adım büyüklüğü, iyileşme oranı ve popülasyon çeşitliliği, NFE'ye göre | E1–E3 (diagnostics) | Betimsel | R1-M10, K3 |
| **S6.** Bulgular yeni problem örneklerine genelleniyor mu? | P1–P4, değişkenlik ve baseline'lar, 10 yeni ortamda, ortam düzeyinde | E5 | Doğrulayıcı (confirmatory) | R1-M4, R3-2 |
| **S7.** Gerçek hesaplama maliyeti ne? | Wall-clock süresi, 10 yöntem | E4 | Betimsel | R1-M7 |
| **S8.** Ara bütçe noktalarındaki performans nasıl? | Bütçenin %25/%50/%75/%100'ünde best-so-far kapsama | E1–E3, E5 geçmişleri | Betimsel | K4 |
| **S9.** (İsteğe bağlı) cACO'nun başlatması performansını açıklıyor mu? | cACO − cACO-R | E6 | Keşif amaçlı | K2, R1-M6 |

**Keşif / doğrulama ayrımı:** E1–E3, gönderilmiş makalede zaten kullanılmış 3 ortamda (seed 42, 17, 99) koşulur. Bu ortamların sonuçları görülmüş olduğu için E1–E3 **keşif ve duyarlılık** analizi sayılır. Birincil hipotezlerin (P1–P4) **doğrulayıcı** testi, daha önce hiç kullanılmamış 10 yeni ortamdaki E5 deneyidir.

**Ara bütçe noktalarının sınırı (S8):** Bunlar sabit 6.250 NFE'lik bütçeyle yapılan koşuların ara performansını gösterir. Farklı toplam bütçelerde sıralamanın değişip değişmediği sorusuna cevap vermez, çünkü p(t) ve a(t) toplam iterasyon sayısına göre ölçeklenir. Bu soru bu protokolün kapsamı dışındadır.

---

## 3. Yöntemler ve varyantlar

| Kod | Tanım | Kaynak |
|---|---|---|
| `FULL` | HWOA-GWA, p: 0.8 → 0.2, doğrusal (ana yöntem) | mevcut kod |
| `G(pi,pe)` | HWOA-GWA, p: pi → pe, doğrusal; pi, pe ∈ {0.2, 0.5, 0.8} | C1 |
| `CONST05` | = G(0.5, 0.5) | C1 |
| `SPIRAL` | Yalnızca spiral (α etrafında), mode = "spiral" | mevcut kod |
| `HIER` | Yalnızca hiyerarşik, mode = "hier". mGWA ile özdeş (K5, G3'te yeniden doğrulanır) | mevcut kod |
| `NOPB` | FULL-no-pbest: liderler (α, β, δ) ve spiral referansı mevcut popülasyondan seçilir. Raporlama için ayrı bir best-so-far arşivi tutulur | C2 |
| Baseline'lar | Random, PSO, cACO, mWOA, mGWA, CSA (değişiklik yok) | mevcut kod |
| `cACO-R` | cACO, başlangıç konuşlanması yerine uniform rastgele bir yerleşimden başlatılır (bkz. E6) | isteğe bağlı |

Notlar:
- `SPIRAL`, mWOA değildir. Şekil ve tablo etiketleri buna göre düzeltilir (K5).
- **Operatör uç noktaları:** Sabit p = 1 operatör açısından `SPIRAL`'e, sabit p = 0 `HIER`'e karşılık gelir. Ancak `SPIRAL` ve `HIER` modları operatör seçimi için rastgele sayı çekmez, bu yüzden G(1,1) ya da G(0,0) ile **aynı seed'de aynı yörüngeyi üretmeleri beklenmez**. Yalnızca dağılım olarak eşdeğerdirler.
- Doğrusal olmayan planlar (örneğin karesel ve karekök tabanlı) bu protokole alınmadı.

---

## 4. Problem örnekleri ve seed'ler

| Senaryo | Sensör | Hedef |
|---|---|---|
| S1 | 100 | 75 |
| S2 | 50 | 75 |
| S3 | 200 | 120 |

- **Mevcut ortamlar (E1–E4, E6):** env_seed ∈ {42, 17, 99}, her biri için 30 deneme (trial 0–29).
- **Yeni ortamlar (E5):** env_seed ∈ **{1001, 1002, …, 1010}**, her biri için 30 deneme. Bu liste herhangi bir sonuç görülmeden, mevcut seed'lerle çakışmayan sabit bir kuralla belirlendi.
- **Solver seed:** trial + env_seed × 1000 (mevcut kural). Yeni ortamlar için 1.001.000–1.010.029 aralığı oluşur, mevcut aralıklarla çakışma yoktur.
- **Bilinen bağımlılık:** S1 ve S2, her env_seed için aynı hedef yerleşimini kullanır (K9). Bu korunur ve metinde belirtilir.
- Aynı (senaryo, ortam, deneme) için bütün yöntemler aynı solver seed'i kullanır. Eşleştirme bu üçlü üzerinden yapılır. Yöntemler rastgele sayıları farklı sırayla tükettiği için "ortak rastgele sayı akışı" iddiası yapılmaz.

---

## 5. Ölçütler

### 5.1 Birincil sonuç değişkeni
- **Nihai best-so-far kapsama**, kapsanan **hedef sayısı** (tam sayı) olarak hesaplanır. Kapsama gözlemleri ve bunlardan türetilen bütün farklar ve istatistikler hedef sayısı birimindedir. Türetilmiş değerler (ortancalar, SD'ler, SD farkları, HL tahminleri) **yuvarlanmaz**. Yüzdeye çevirme ve yuvarlama **yalnızca sunumda** yapılır.
- Mevcut CSV'deki yüzde değerleri, hedef sayısıyla çarpılıp en yakın tam sayıya yuvarlanarak hedef sayısına çevrilir. Çevirme hatası 1e-6'dan büyükse durdurulur ve incelenir.
- 30 eşleştirilmiş farkın ortancası kesirli (x.5) olabilir. Bu değer yuvarlanmaz.
- **Pratik anlamlılık eşiği:** **Tek bir hedef** (S1/S2'de 1.33 puan, S3'te 0.83 puan).

### 5.2 İkincil ölçütler
- **Koşular arası değişkenlik:** Her (yöntem, senaryo, ortam) hücresi için SD, CV, IQR ve 5. yüzdelik.
- **Ara bütçe kapsaması:** Bütçenin %25, %50, %75 ve %100'ü, yani **1.562,5 / 3.125 / 4.687,5 / 6.250 NFE** eşikleri. Her eşik için **NFE değeri eşiği aşmayan son gözlem** kullanılır (eşik yukarı yuvarlanmaz). Örneğin 25 NFE'lik nesillerle çalışan yöntemlerde bu, 1.550 / 3.125 / 4.675 / 6.250 NFE'deki kayıtlardır. CSA gibi farklı adım büyüklüklerine sahip yöntemlerde de aynı kural uygulanır.
- **NFE kullanımı ve durma nedeni.**
- **Wall-clock süresi:** Yalnızca E4'ten (§8).

### 5.3 Mekanizma ölçütleri (S5, yalnızca diagnostics modu)
Algoritmanın davranışını etkileyen hiçbir şey değişmez: **ek amaç fonksiyonu çağrısı yapılmaz, ek rastgele sayı çekilmez**, popülasyon dizileri yalnızca kopya üzerinden okunur.

| Ölçüt | Tanım | Kayıt düzeyi |
|---|---|---|
| **Operatör seçimi** | o ∈ {S, H}. Kayıt, karşılaştırma ifadesinden değil, **çalışan dalın içinden** yapılır. Böylece kaydın gerçek dal seçimiyle eşleşmesi yapısal olarak sağlanır | ajan × iterasyon |
| **Adım büyüklüğü** | s = (1/n) Σⱼ ‖xⱼ(yeni) − xⱼ(eski)‖, sensör başına ortalama yer değiştirme (m), clip sonrasında | ajan × iterasyon |
| **pbest'e göre iyileşme** | I = 1 eğer f(x_yeni) > pbest_f(önceki); büyüklük Δ = max(0, f(x_yeni) − pbest_f(önceki)), hedef sayısı cinsinden. **NOPB'de tanımsızdır ve "uygulanamaz" (NA) olarak kaydedilir** | ajan × iterasyon |
| **Global iyileşme kaynağı** | Best-so-far'ı güncelleyen adayın o iterasyonda kullandığı operatör. pbest'li varyantlarda bu, α'yı güncelleyen ajandır. **NOPB'de raporlama arşivini güncelleyen adaydır** | iterasyon |
| **Genotipik çeşitlilik** | D_g = (1/N) Σᵢ ‖xᵢ − x̄‖ / √n, sensör başına metre. **Sınırlama:** sensör sırasına duyarlı, permütasyona göre değişmez değil | iterasyon |
| **Fenotipik çeşitlilik** | Her ajanın kapsanan-hedef maskesi (ikili, uzunluk m) için ortalama ikili Hamming uzaklığı / m. Permütasyondan bağımsız | iterasyon |

**Fenotipik çeşitliliğin hesaplanması:** Amaç fonksiyonu yalnızca skaler bir kapsama değeri döndürdüğü için kapsama maskeleri diagnostics kodu tarafından konumlardan **yeniden hesaplanır**. Bu hesaplama:
- **tanı amaçlı ek hesaplama** olarak sınıflandırılır ve manifest'te belirtilir,
- NFE sayacına girmez ve algoritma tarafından kullanılmaz,
- süresi G2'de ayrıca ölçülür ve raporlanır,
- E4 runtime ölçümlerinde **kapalıdır**.

**Raporlama:** Bütçe 10 eşit NFE dilimine (her biri 625 NFE) bölünür. Her dilim için operatör başına kullanım oranı, ortalama adım büyüklüğü, iyileşme oranı ve ortalama Δ ile dilimin sonundaki D_g ve fenotipik çeşitlilik raporlanır. Ortanca ve IQR, (ortam × deneme) üzerinden hesaplanır.

**Ön kayıtlı beklenti yoktur.** Makaledeki "spiral = keşif, hiyerarşi = sömürü" anlatısı bu ölçütler görülmeden korunmaz ya da reddedilmez. Mekanizma metni E1–E3 ölçümlerine göre yazılır.

### 5.4 Yakınsama geçmişi
- **İlk kayıt:** Başlatmanın sonundaki (NFE, best-so-far) çifti. Örneğin popülasyonu 25 olan yöntemlerde NFE = 25.
- **Sonraki kayıtlar:** Her iterasyon sonunda (NFE, best-so-far).
- **Doğal kayıt ve dolgu ayrımı:** Orijinal kod, %100 kapsamada erken durduğunda geçmişi yapay 100 değerleriyle `max_iter` uzunluğuna tamamlar. Arşivde ve eşdeğerlik testinde **yalnızca doğal iterasyon sonu kayıtları** kullanılır. Dolgu ayrı bir bayrakla işaretlenir.
- Şekillerde ve ara bütçe analizinde 25 NFE'lik ortak ızgaraya, "eşiği aşmayan son gözlem" kuralıyla basamak fonksiyonu olarak taşınır. Erken duran koşularda değer 100'de sabit kalır.
- Şekillerde x ekseni **NFE**'dir. Ortanca ve IQR bandı gösterilir (R1-m6).

---

## 6. İstatistik planı

### 6.1 Genel kurallar
- **Eşleştirme birimi:** (senaryo, ortam, deneme).
- **90 koşunun toplu hali** yalnızca **betimsel** olarak raporlanır. Toplu veri üzerinde çıkarımsal test yapılmaz (K6, R1-M4).
- Bütün testler çift taraflı, α = 0.05.
- **İstatistiksel sonuç ve pratik anlamlılık ayrı ayrı raporlanır.** Her karşılaştırma için hem Holm-düzeltilmiş p değeri hem de HL tahmini ve güven aralığı, pratik eşikle birlikte verilir. İkisi tek bir etikete indirgenmez.

### 6.2 Wilcoxon testinin uygulanması (bütün analizler için)
- **İstatistik:** Pratt sıralarıyla Wilcoxon signed-rank. Sıfır farklar mutlak değer sıralamasına dahil edilir, istatistiğe katkıları sıfırdır. Eşit mutlak farklar ortalama rank alır.
- **Sıfır hipotezi ve kesinlik:** p değeri, sıfır olmayan farkların işaretlerinin H₀ altında değiştirilebilir (exchangeable) olduğu varsayımına dayanan **işaret çevirme permütasyon testi** ile hesaplanır. Sıfır farkların işaretleri çevrilmez. Bu varsayım altında test, bağlar ve sıfırlar varken de kesindir.
- **İki taraflı p:** p = P(|T* − E₀[T*]| ≥ |T_obs − E₀[T*]|), T* permütasyon dağılımı, E₀[T*] = 0 (işaretli rank toplamı).
- **Hesaplama:** Yöntem, **test edilen fark vektörünün kendi** sıfır olmayan fark sayısı k'ye göre seçilir. k ≤ 15 ise bütün 2ᵏ işaret düzeni sayılır (kesin). k > 15 ise B = 100.000 rastgele işaret düzeni kullanılır (sabit seed 20261110) ve p = (b + 1) / (B + 1), b = gözlenen istatistik kadar ya da daha uç rastgele düzen sayısı. Bu kural güven kümesinin hesaplanmasında **her aday δ için ayrı ayrı** uygulanır: toplam gözlem sayısı 15'i geçse bile, d − δ için k ≤ 15 ise kesin sayım kullanılır. Monte Carlo gerektiren δ değerlerinde bütün δ'lar için aynı işaret matrisi kullanılır (ortak rastgele sayılar). Bu davranış, başarısızlıkta duran bir regresyon testiyle korunur (`test_revstats.py`, test 10).
- **Kesin aritmetik (tolerans ve yuvarlama yok):** Bütün karşılaştırmalar, saklanan double değerlerin kesin rasyonel temsili (`fractions.Fraction`) üzerinde yapılır. d − δ, sıfır tespiti (d − δ = 0), bağlar (|dᵢ − δ| = |dⱼ − δ|) ve kırılma noktaları kesin hesaplanır. Ranklar yarım tam sayıdır ve işaretli rank toplamları float'ta kesindir. Bu nedenle güven kümesine üyelik, **her δ için** testin kendisiyle yapı gereği aynıdır. Bu özellik regresyon testleriyle korunur (`test_revstats.py`): bütün kırılma noktaları ve bunların 10⁻³, 10⁻⁹, 10⁻¹² kadar sağı ve solu; on farkın tamamı 1 iken 1'e keyfi yakın noktalar (0.9999999995, 1 ± 10⁻¹², bitişik double'lar); ±1 hedef karar sınırını kesen 40 veri kümesi; on farkın tamamı 1/3 iken gerçek kayma; sürekli veride n = 10 (kesin) ve n = 30 (Monte Carlo). Bütün testlerde doğrudan test ile kümeye üyelik arasında uyuşmazlık sıfırdır.
- **Etkin örneklem:** Sıfır olmayan fark sayısı k her testte raporlanır.
- **Gözlenen farkların tamamı sıfırsa:** Hesaplamada **p = 1** kullanılır ve karşılaştırma **Holm ailesinde kalır** (aile büyüklüğü değişmez, birincil aile 12 test olarak korunur). Raporda "gözlenen farkların tamamı sıfır" ifadesi kullanılır. HL = 0. Güven aralığı §6.2a'daki kurala göre hesaplanır.
- **Holm ve sıfırlar:** n = 10 ortamda ulaşılabilecek en küçük p ≈ 0.00195'tir ve yalnızca 10 farkın hepsi sıfırdan farklı ve aynı yöndeyse elde edilir. Sıfır farklar ulaşılabilir en küçük p'yi büyütür. Örneğin k = 8 için p_min = 2/256 ≈ 0.0078. Bu değer 12 testlik ailenin **ilk** Holm eşiğini (0.05/12 ≈ 0.0042) geçemez. Ancak daha küçük p değerleri önceki adımları geçtiyse, ilerleyen bir Holm adımında (örneğin 0.05/6 ≈ 0.0083) yine anlamlı olabilir.

### 6.2a Etki büyüklüğü ve güven aralığı
- **Nokta tahmini:** Hodges–Lehmann (HL), yani Walsh ortalamalarının ortancası.
- **Güven aralığı (test tersine çevirme):** %95 güven kümesi, §6.2'deki testin aday kayma değerleri δ için tersine çevrilmesiyle tanımlanır: farklardan δ çıkarıldığında iki taraflı p ≥ 0.05 veren δ değerlerinin kümesi.
  - **Kırılma noktaları:** Pratt sıralı istatistik δ'ya göre parçalı sabittir ve yalnızca Walsh ortalamalarında, yani (dᵢ + dⱼ)/2 değerlerinde (i = j dahil, yani dᵢ'nin kendisi) değişir. Walsh ortalamaları kesin rasyonel olarak hesaplanır; birleştirme ya da yuvarlama yapılmaz.
  - **Değerlendirme:** (1) Her kırılma noktası ayrı ayrı test edilir. (2) Ardışık kırılma noktaları arasındaki her **açık aralık**, içinden alınan herhangi bir temsilci noktayla (orta nokta) test edilir; aralığın tamamı aynı sonucu verir. (3) En küçük kırılma noktasının solundaki ve en büyüğünün sağındaki iki **sınırsız aralık** da test edilir.
  - **Saklanan sonuç:** Kabul kümesi, ardışık kabul edilen parçaların birleştirilmesiyle oluşan aralıkların listesidir. Her aralık için alt ve üst sınır, **sınırların dahil olup olmadığı** (kapalı/açık) ve gerekiyorsa **sınırsız uçlar** (−∞ / +∞) saklanır.
  - **Raporlanan aralık:** Kabul kümesi tek bir aralıksa o aralık raporlanır. Birden fazla ayrık aralıktan oluşuyorsa, bütün aralıklar saklanır ve raporda kapsayıcı aralık (en küçük alt sınır, en büyük üst sınır) "bağlantısız kabul kümesi" notuyla verilir.
  - Bağlar ve sıfırlar nedeniyle gerçek kapsama oranı %95'ten farklı olabilir. Bu nedenle aralık "kesin" olarak adlandırılmaz.
  - §6.3'teki pratik anlamlılık kuralı, raporlanan aralığa **kesin aritmetikle** uygulanır (sınırlar ve kapalı/açık bilgisi dahil). Sınırsız bir uç varsa "pratik anlamlılık belirsiz" sonucu verilir.
- **Rank-biserial r:** Pratt sıralarıyla, eşleştirilmiş tanım.

### 6.3 Birincil analiz (doğrulayıcı, E5)
- **Birim: ortam.** Her (senaryo, karşılaştırma) için her ortamın 30 eşleştirilmiş farkının (hedef sayısı) ortancası alınır. n = 10 ortam düzeyinde fark elde edilir.
- **Test:** §6.2.
- **Etki büyüklüğü:** §6.2a (HL, test tersine çevirmeyle %95 güven aralığı, rank-biserial r).
- **Çoklu karşılaştırma:** Aile = P1–P4 × 3 senaryo = **12 test, Holm** düzeltmesi.
- **Raporlama:** İstatistiksel sonuç ve pratik anlamlılık **iki ayrı sütunda** raporlanır. Biri diğerine bağlı değildir.

| Sütun | Kural |
|---|---|
| **İstatistiksel sonuç** | Holm-düzeltilmiş p < 0.05 → "örnekler arasında tutarlı fark"; aksi halde → "örnekler arasında tutarlı bir fark gösterilemedi" |
| **Pratik anlamlılık** (eşik e = tek hedef = 1, hedef sayısı biriminde) | %95 GA'nın tamamı (−∞, −e] ∪ [e, +∞) içinde → "pratikte anlamlı"; GA'nın tamamı (−e, +e) içinde → "pratikte ihmal edilebilir"; diğer durumlar → "pratik anlamlılık belirsiz" |

HL nokta tahmini tek başına pratik anlamlılık kararı için kullanılmaz.

### 6.4 İkincil analiz (E1–E3, hücre düzeyi, keşif amaçlı)
- Her (senaryo, ortam) hücresinde 30 eşleştirilmiş fark üzerinde §6.2'deki test ve §6.2a'daki etki büyüklükleri (aynı test tersine çevirme yöntemi; bootstrap kullanılmaz). Pratik anlamlılık §6.3'teki kurala göre ayrı sütunda verilir.
- Holm düzeltmesi her ikincil aile içinde ayrı uygulanır: (a) P1–P4 hücre testleri (4 × 9 = 36 test), (b) grid hücreleri − FULL (8 × 9 = 72 test).
- **Tutarlılık özeti:** HL'nin işaretinin aynı olduğu hücre sayısı (örneğin 7/9).

### 6.5 Değişkenlik analizi (önceden tanımlanmış ikincil analiz)
- **Değişken:** Her (yöntem, senaryo, ortam) hücresinde 30 koşunun SD'si (ddof = 1), hedef sayısı cinsinden, **yuvarlanmadan**.
- **Karşılaştırma değişkeni: SD farkı** (FULL − karşılaştırılan yöntem). SD oranı, iki SD de sıfırdan büyükse **yalnızca betimsel** olarak verilir. Gerekçe: SD = 0 olan hücreler mevcut veride gerçekten var (örneğin S3, env 99, cACO).
- **Karşılaştırmalar:** FULL − mGWA (= HIER) ve FULL − mWOA.
- **Doğrulayıcı test (E5):** Her senaryoda 10 ortamın SD farkları üzerinde §6.2'deki test. Aile = 2 karşılaştırma × 3 senaryo = **6 test, Holm**.
- **Mevcut veri (3 ortam):** Gönderilmiş deneylerdeki 9/9 hücre bulgusu (FULL'un SD'si mGWA'dan düşük) **yalnızca betimsel** olarak raporlanır.
- Brown–Forsythe testi yalnızca ek bilgi olarak verilir. Eşleştirilmiş veriyi bağımsız kabul ettiği belirtilir.

### 6.6 Baseline karşılaştırmaları (E5, ikincil)
- FULL − {PSO, cACO, mWOA, CSA, Random}. Test, §6.3'teki gibi **her ortamın 30 eşleştirilmiş farkının ortancası** üzerinden yapılır (n = 10 ortam). Ortalama kapsama yalnızca betimsel olarak verilir. Aile = 5 × 3 = **15 test, Holm**.
- PSO ve cACO'nun FULL'dan iyi olduğu sonuçlar açıkça raporlanır.

### 6.7 Analiz aileleri özeti

| Aile | Deney | Test sayısı | Tür |
|---|---|---|---|
| P1–P4, kapsama | E5 | 12 | **Birincil, doğrulayıcı** |
| Değişkenlik (FULL − mGWA, FULL − mWOA) | E5 | 6 | İkincil, doğrulayıcı |
| Baseline'lar | E5 | 15 | İkincil |
| P1–P4, hücre düzeyi | E1–E3 | 36 | Keşif |
| Grid − FULL | E1 | 72 | Keşif |

---

## 7. Kod değişiklikleri ve geçiş kapıları

Her kapı geçilmeden bir sonraki aşamaya geçilmez. Bütün kontroller betiklerle yapılır ve sonuçları JSON olarak arşivlenir.

| Kapı | Kontrol | Başarı kriteri | Durum |
|---|---|---|---|
| **G0** | Gönderilmiş 2.070 koşunun yeniden üretilmesi | 0 uyuşmazlık, mutlak tolerans 1e-9, iki ortamda | **Geçti** |
| **G1** | Kaynak sabitleme: runner doğrulanmış ZIP'i kendisi açar ve `src/` dosyalarının SHA-256 değerlerini manifest'e yazar. Paralel olarak `v1.0-submission` etiketi doğrulanır | **Zorunlu, her betiğin başında:** (1) ZIP hash'i beklenen değere eşit, değilse durur; (2) yeni ağaçta yalnızca izin verilen dosyalar değişmiş (`algorithms/hwoa_gwa.py`; C2 sonrasında NOPB dosyası) ve **fazladan Python dosyası yok**; (3) referans CSV hash'i rapora yazılır. Etiket ↔ ZIP eşleşmesi gönderimden önce | Kısmen (ZIP hash'i doğrulandı, betik kontrolleri v0.4 ile eklendi) |
| **G2** | **Pilot** (C1 + C3): S1, env 42, deneme 0–2; FULL, SPIRAL, HIER, CONST05; diagnostics açık | **Zorunlu:** (a) kaydedilen operatör = gerçekten çalışan dal (dal içi kayıt + ayrı doğrulama), (b) her iterasyonda değerlendirilen ajan sayısı = 25, (c) SPIRAL'de yalnızca S, HIER'de yalnızca H, (d) NaN yok, (e) NFE, durma nedeni ve geçmiş uzunluğu tutarlı, (f) fenotipik çeşitlilik hesaplamasının süresi ölçülmüş. **Betimsel:** FULL'da spiral oranının p(t) ile binom aralığında olup olmadığı | **Geçti** (2026-11-10, `gates/G2_pilot.json`) |
| **G3** | **Eşdeğerlik A:** Orijinal kod ile yeni kodun varsayılanı, aynı seed'lerle yan yana: FULL 270 koşu, SPIRAL ve HIER S1'de 180 koşu, ayrıca mGWA ile HIER eşdeğerliği S1–S3'te 270 koşu | **Tam sayı alanlar** (nfe_actual, last_imp, max_iter_used, doğal geçmiş uzunluğu, gözlem NFE değerleri) ve stop_reason: **doğrudan eşitlik**. **Kayan noktalı alanlar** (coverage, displacement): mutlak fark ≤ 1e-9, ayrıca birebir eşit olanların sayısı raporlanır. **Geçmiş:** başlatma sonu kaydı dahil, doğal iterasyon sonu kayıtları hem **ham best-so-far değeri** (mutlak fark ≤ 1e-9) hem **hedef sayısı** (doğrudan eşitlik) olarak karşılaştırılır. Yapay %100 dolgusu karşılaştırmaya girmez | **Geçti** (2026-11-11, `gates/g345/G3_G5.json`) |
| **G4** | **Eşdeğerlik B:** Yeni kodda diagnostics açık ve kapalı, G3'teki koşu kümesinin tamamı | G3 ile aynı kriterler | **Geçti** (2026-11-11, `gates/g345/G3_G5.json`) |
| **G5** | **Konfigürasyon eşdeğerliği:** G(0.8, 0.2) parametrik çağrısı ile varsayılan FULL | G3 ile aynı kriterler | **Geçti** (2026-11-11, `gates/g345/G3_G5.json`) |
| **G6** | **C2 sağlamlık kontrolü** (eşdeğerlik beklenmez): NOPB'de raporlanan değer = arşiv; best-so-far **monoton azalmayan** (eşit kalan iterasyonlar geçerli); NFE kuralları korunuyor; pbest iyileşme alanı NA; global iyileşme kaynağı arşiv güncellemeleriyle tutarlı; dal kaydı RNG çağrı dizisiyle eşleşiyor; diagnostics açık/kapalı aynı sonuç. S1–S3, env 42, deneme 0–2 | Bütün kontroller geçer | **Geçti** (2026-11-11, `gates/G6_nopb.json`) |

**G3 gözlem katmanı:** Orijinal kod başlatma sonundaki (NFE, best-so-far) çiftini çıktı olarak vermez ve geçmişler CSV'de saklanmamıştır. Bu yüzden G3'ün referansı şöyle üretilir:
1. **Gözlemci:** Orijinal kodun NFE sayacı sarmalayıcısının (`NFECountingEnv`) bir alt sınıfı, her değerlendirmede (NFE, değerlendirilen fitness, yürüyen maksimum) kaydı tutar. Orijinal algoritma kaynak dosyalarına dokunulmaz. Başlatma sonu ve doğal iterasyon sonları bu kayıttan doğrudan ölçülür.
2. **Gözlemcinin etkisizliği:** Gözlemli orijinal koşuların nihai alanları (coverage, nfe_actual, last_imp, max_iter_used, stop_reason) önce gözlemsiz orijinal koşularla (G0 referansı) karşılaştırılır. Kriter G3 ile aynıdır.
3. **İç tutarlılık:** Her koşuda algoritmanın kendi raporladığı best-so-far (`history` ve `best_coverage`) gözlemcinin yürüyen maksimumuyla iterasyon sonlarında eşleşmelidir.
4. Ardından yeni kodun geçmişleri bu gözlemli referansla karşılaştırılır. SPIRAL/HIER ile G(1,1)/G(0,0) arasında yörünge eşdeğerliği **test edilmez** (bkz. §3).

**Kapı sonuçlarının yorumu:** G3–G5'teki sıfır farklar, **aynı algoritmanın aynı seed'lerle aynı çıktıyı ürettiğini** (kod eşdeğerliği) gösterir. Yöntemlerin performans bakımından eşit olduğu şeklinde yorumlanmaz.

**Önbellek ve kaynak kimliği:** Kapı ve deney betiklerinin ara sonuç dosyaları (önbellek), bir parmak izi ile birlikte saklanır: kaynak ağacının dosya hash'leri, runner dosyalarının hash'leri, koşu konfigürasyonlarının hash'i, ZIP ve referans CSV hash'leri, **Python ve paket sürümleri** (NumPy, SciPy, pandas). Önbellek yüklenirken parmak izi yeniden hesaplanır. **Uyuşmazlıkta betik durur**, eski sonuçlar kullanılmaz.

**Çalıştırma sayısı ve yeniden kullanım (G3–G5):** Tablodaki karşılaştırma sayısı, algoritma çalıştırma sayısından farklıdır. Gerçek çalıştırmalar:

| Çalıştırma kümesi | Ağaç | Diagnostics | Koşu | Kullanıldığı kapı |
|---|---|---|---|---|
| FULL S1–S3, SPIRAL S1, HIER S1, mGWA S1–S3 (gözlemli) | Orijinal | — | 270 + 90 + 90 + 270 = **720** | G3 (referans ve gözlemci etkisizliği) |
| FULL S1–S3, SPIRAL S1, HIER S1–S3 (varsayılan çağrı) | Yeni | Kapalı | 270 + 90 + 270 = **630** | G3, G4 |
| Aynı küme | Yeni | Açık | **630** | G4 |
| G(0.8, 0.2) parametrik çağrı, S1–S3 | Yeni | Kapalı | **270** | G5 |
| **Toplam** | | | **2.250** | |

Yeniden kullanım: Yeni ağaçtaki HIER S1 koşuları hem orijinal HIER S1 hem orijinal mGWA S1 ile karşılaştırılır. Gözlemci etkisizliği kontrolü, gözlemli orijinal koşuları G0 referans CSV'si ile karşılaştırır, ek koşu gerektirmez. Bu tablo ve gerçekleşen çalıştırma sayıları manifest'e yazılır.

**Runner kapısı (RUNNER):** Deney runner'ı yöntemleri açık bir tablo üzerinden çağırır. Tanınmayan yöntem adları, protokol ızgarası dışındaki G(pi,pe) hücreleri ve baseline'lar için diagnostics talebi reddedilir. Başlatma ve iterasyon NFE maliyetleri ile popülasyon parametre adları gönderilmiş runner'dan (`statistical_experiment._run_one`) birebir alınmıştır. Kontrol: 13 yöntem adı × 4 vaka (S1/S2/S3 env 42 deneme 0, S1 env 17 deneme 1). Orijinal 7 algoritma ile FULL/SPIRAL/HIER, gönderilmiş runner'ın çıktısıyla (kapsama, displacement, NFE, last_imp, max_iter, durma nedeni, doldurulmuş geçmiş) eşleşmeli. HIER ayrıca mGWA ile eşleşmeli. CONST05'e p = 0.5/0.5 geçmeli. NOPB doğru fonksiyonu çağırmalı. G(0.8,0.2) = FULL, G(0.5,0.5) = CONST05. Beş geçersiz istek reddedilmeli. Ayrıca bütün kayıtlarda NFE iterasyon sınırlarıyla hizalı olmalı ve algoritmanın kendi geçmişi gözlemcinin yürüyen maksimumuna eşit olmalı (best-so-far). Bunların hepsi **zorunlu** kriterdir. CONST05'in FULL'dan farklı çıkması **betimseldir**, çünkü doğru çalışan iki konfigürasyon bazı koşularda aynı sonucu üretebilir. **Durum: Geçti** (2026-11-11, `gates/RUNNER_check.json`). G3–G5, önceki runner sürümüyle üretilmiştir. Algoritma dosyaları değişmediği ve runner yönlendirmesi bu kapıda ayrıca doğrulandığı için G3–G5 tekrarlanmadı. G2 ve G6 yeni runner ile yeniden koşuldu ve geçti.

**Kod değişikliği sırası:** C1 + C3 → G2 → G3 → G4 → G5 → C2 → G6 → deneyler. C4–C7 (runtime, geçmiş saklama, manifest, istatistik modülü) algoritma davranışını etkilemediği için paralel geliştirilebilir.

---

## 8. Deney matrisi

| Deney | Yöntemler | Senaryo | Ortam × deneme | Koşu | Diagnostics | Amaç |
|---|---|---|---|---|---|---|
| **E1** | 9 grid hücresi (FULL dahil) | S1–S3 | 3 × 30 | 2.430 | Açık | S1, S2, S5, S8 |
| **E2** | SPIRAL (S2 ve S3 yeni, S1 yeniden), HIER (S1–S3) | S1–S3 | 3 × 30 | 540 | Açık | S3, S5 |
| **E3** | NOPB | S1–S3 | 3 × 30 | 270 | Açık | S4, S5 |
| **E4** | 10 yöntem (aşağıda) | S1–S3 | env 42, deneme 0–9 | **300 ölçülen + 30 ısınma** | **Kapalı** | S7 |
| **E5** | 10 yöntem (aşağıda) | S1–S3 | **10 yeni** × 30 | **9.000** | Kapalı | S6, P1–P4 doğrulama |
| **E6** | cACO-R (isteğe bağlı, ana paketin dışında) | S1–S3 | 3 × 30 | 270 | Kapalı | S9 |

**E4 ve E5'teki 10 yöntem:**
1. Random
2. PSO
3. cACO
4. mWOA
5. mGWA (= HIER)
6. CSA
7. FULL
8. SPIRAL
9. CONST05
10. NOPB

**Tahmini toplam süre** (koşu başına ≈2.4 s, 2 paralel işçi): E1–E3 ≈ 2,5–3 saat (G4'te diagnostics açık koşular kapalı olanların ≈2 katı sürdü: 630 koşu 1.812 s ve 911 s) (G2'de fenotipik çeşitlilik hesabının diagnostics koşularındaki çalışma süresinin iki ortamda ≈%46 ve ≈%52–53'ünü oluşturduğu ölçüldü; pay ortama bağlıdır, kesin süre ilk E1 parçasında yeniden ölçülür), E5 ≈ 3 saat, E4 ≈ 15–30 dakika. Toplam ≈ 5,5–6 saat.

### 8a. Yürütme kuralları
- **Orkestratör:** `revision/tools/run_experiments.py`. Deney matrisi bu protokolden üretilir. Her koşunun anahtarı (deney, yöntem, senaryo, env_seed, deneme, rol) benzersizdir. Beklenen koşu sayıları: E1 2.430, E2 540, E3 270, E4 330 (300 ölçülen + 30 ısınma), E5 9.000.
- **Checkpoint ve devam etme:** Her tamamlanan koşu hemen (sonuç satırı, NFE eksenli geçmiş, diagnostics) deneye özel bir SQLite dosyasına yazılır. Yeniden çalıştırmada kayıtlı anahtarlar atlanır.
- **Parmak izi:** Checkpoint; protokol dosyasının SHA-256'sı, ZIP hash'i, kaynak ağacı hash'leri, runner hash'leri, matris hash'i, Python/paket sürümleri ve BLAS iş parçacığı ayarlarıyla parmak izi taşır. Uyuşmazlıkta orkestratör durur. Revizyon commit'i bu içeriğin etiketi olarak kaydedilir; commit henüz bilinmiyorsa "PENDING" yazılır ve sonradan yalnızca bir kez doldurulabilir.
- **Tamamlanma kriteri:** Bir deney ancak kayıtlı anahtar kümesi beklenen anahtar kümesine **tam olarak** eşitse (eksik ve fazla anahtar yok) tamamlanmış sayılır ve dışa aktarılır. Aksi halde dışa aktarma reddedilir.
- **Ön kontrol (smoke test):** Tam deneylerden önce küçük bir E1 parçası ayrı bir klasörde çalıştırılır, yarıda kesilir ve devam ettirilir. Kesintiden sonra anahtarların eksiksiz ve tekrarsız olması, kayıtlı sonuçların doğrudan tek koşu sonuçlarıyla aynı olması ve diagnostics'in geri okunabilmesi kontrol edilir. Bu parçanın sonuçları performans analizine girmez.

### E4 runtime protokolü
- Tek süreç, sıralı koşular, diagnostics kapalı.
- `OMP_NUM_THREADS = MKL_NUM_THREADS = OPENBLAS_NUM_THREADS = 1`.
- Her (yöntem, senaryo) için bir ısınma koşusu yapılır ve atılır (10 × 3 = 30 ısınma koşusu).
- Ortanca ve IQR raporlanır.
- CPU modeli, çekirdek sayısı, RAM, işletim sistemi, Python ve paket sürümleri kaydedilir.
- Runtime değerleri NFE'nin yerine kullanılmaz. İkisi ayrı maliyet boyutları olarak raporlanır.

### E6 tasarımı (isteğe bağlı)
- **cACO:** Her ortam için sabit başlangıç yerleşimi (`env.initial_sensors`, mevcut davranış).
- **cACO-R:** Her deneme için **ayrı bir RNG** ile uniform örneklenen başlangıç yerleşimi. Bu RNG'nin seed'i solver seed'inden türetilir ama cACO'nun arama RNG'sinden bağımsızdır. Böylece arama sırasındaki rastgele sayı akışı değişmez.
- Karşılaştırma: cACO − cACO-R, hücre düzeyinde, §6.4'teki yöntemle (keşif amaçlı).

---

## 9. Çıktılar ve arşiv

| Dosya | İçerik |
|---|---|
| `runs_long.parquet` (ya da CSV) | Koşu başına bir satır: anahtarlar, yöntem/konfigürasyon kimliği, kapsanan hedef sayısı, coverage (%), disp (yalnızca arşiv), NFE, last_imp, stop_reason, max_iter_used |
| `histories.npz` | Koşu başına doğal (NFE, best-so-far) dizileri ve dolgu bayrağı |
| `diagnostics.npz` | §5.3'teki ölçütler, iterasyon düzeyinde |
| `runtime_benchmark.csv` + `system_info.json` | E4 |
| `manifest.json` | Protokol sürümü ve hash'i, **iki ayrı commit**: `v1.0-submission` (gönderilmiş makaleyi üreten orijinal kod, `3e15fcb`) ve **revizyon commit'i** (deneyleri üreten kod), önbellek parmak izleri, ZIP ve kaynak dosya hash'leri, paket sürümleri, konfigürasyon hash'i, diagnostics ek hesaplamalarının listesi, başlangıç/bitiş zamanı |
| `gates/G*.json` | Kapı kontrol sonuçları |
| `figures/` + `scripts/` | Bütün şekiller ve onları üreten betikler (R1-m10) |

**Arşiv:** Revizyon gönderim planına dahildir. Zenodo'ya yüklenir. DOI, arşiv yayımlandığında makaleye ve yanıt mektubuna eklenir.

---

## 10. Karar kapısı: geri beslemeli varyant (FB-SEL)
Geri beslemeli bir operatör seçimi (**FB-SEL**, feedback-based operator selection) revizyona yalnızca **aşağıdaki koşulların hepsi** sağlanırsa eklenir. Karar, E1–E5 sonuçlarının yönüne bağlı değildir.
1. G0–G6 geçilmiş olmalı.
2. E1–E5 tamamlanmış olmalı.
3. Revizyon son tarihi ve hesaplama bütçesi ayrı bir karşılaştırmaya izin vermeli.
4. FB-SEL politikası, herhangi bir sonucu görülmeden tanımlanıp bu protokole yeni bir sürüm olarak eklenmiş olmalı.

Bu koşullar sağlanmazsa FB-SEL future work olarak kalır. FB-SEL, C2 (NOPB) ile ilgisizdir.

---

## 11. Makaleye yansıma kuralları
- Displacement'a dayalı her iddia, tablo sütunu ve şekil çıkarılır.
- Mekanizma metni yalnızca E1–E3'teki §5.3 ölçümlerine dayanır.
- **Doğrulayıcı performans iddiaları** yalnızca E5'teki birincil (§6.3) ve ikincil doğrulayıcı (§6.5, §6.6) analizlere dayanır ve §6.3'teki raporlama tablosuna göre ifade edilir.
- **Değişkenlik iddiası** (FULL − mGWA, FULL − mWOA) §6.5'e göre raporlanır. Mevcut 3 ortamdaki 9/9 bulgusu yalnızca betimsel olarak verilir.
- E1–E3 bulguları "keşif / duyarlılık" olarak etiketlenir.
- cACO açıklaması, E6 yapılmazsa **hipotez** olarak sunulur.
- Yanıt mektubu, yeniden üretim için şu ifadeyi kullanır: *"All 2,070 runs were independently reproduced in two software environments using the same archived source and reference data. Across all runs, the five numerical fields agreed within an absolute tolerance of 10⁻⁹, and the stopping reason matched exactly."*

---

## 12. Sapma kaydı

| Tarih | Sürüm | Değişiklik | Gerekçe | Etkilenen sonuçlar |
|---|---|---|---|---|
| 2026-11-10 | v0.1 | İlk taslak | — | — |
| 2026-11-11 | v1.0 | Dondurma: RUNNER paragrafındaki eski "FULL'dan farklı olmalı" ifadesinin kaldırılması; §8a yürütme kuralları (orkestratör, checkpoint, parmak izi, tamamlanma kriteri, ön kontrol) | Ekip onayı | Yok |
| 2026-11-11 | v0.7 | Toleransın kaldırılması; testin, güven kümesinin ve pratik anlamlılık kuralının kesin rasyonel aritmetikle hesaplanması ve sınır noktası regresyon testleri; RUNNER kapısında NFE hizası ve best-so-far geçmişinin zorunlu, CONST05 ≠ FULL kontrolünün betimsel olması | Ekip incelemesi | Yok |
| 2026-11-11 | v0.6 | Güven kümesinde ondalık yuvarlama yerine sabit göreli tolerans (τ) ile sıfır/bağ ve kırılma noktası birleştirme, regresyon testleri 11–13; açık yöntem tablosu, tanınmayan adların reddi ve RUNNER kapısı; önbellek parmak izine Python/paket sürümleri | Ekip incelemesi | Yok |
| 2026-11-11 | v0.5 | Kesin/Monte Carlo seçiminin her δ için k'ye göre yapılması ve regresyon testi; önbellek parmak izi ve uyuşmazlıkta durma kuralı; G6 tanımının genişletilmesi ve G6 sonucu; manifest'te iki commit ayrımı; kapı sonuçlarının yorumuna ilişkin not | Ekip incelemesi | Yok |
| 2026-11-11 | v0.4 | Tüm farklar sıfırken p = 1 ile Holm ailesinde kalma; güven kümesinin kırılma noktaları, açık aralıklar ve sınırsız uçlarla tam tersine çevrilmesi; G1 kontrollerinin zorunlu ve durdurucu hale gelmesi; G3'te ham ve hedef sayısı düzeyinde geçmiş karşılaştırması ve tam sayı alanların doğrudan eşitliği; G3–G5 çalıştırma sayıları ve yeniden kullanım tablosu; pilot sonuçlarının kullanımına ilişkin ifade; dondurma sürümü; süre tahmini | Ekip incelemesi (G2 bağımsız tekrarı) | Yok |
| 2026-11-10 | v0.3 | Pratt sıralı işaret çevirme testinin varsayımı, iki taraflı p tanımı ve Monte Carlo (b+1)/(B+1) kuralı; test tersine çevirmeyle güven aralığı ve "kesin" ifadesinin kaldırılması; istatistiksel sonuç ve GA tabanlı pratik anlamlılığın ayrı sütunlarda raporlanması; türetilmiş değerlerin yuvarlanmaması; baseline testinin ortanca fark üzerinden yapılması; Holm ve sıfırlar notunun düzeltilmesi; G3 gözlem katmanı; NOPB'de pbest iyileşmesinin NA olması ve global iyileşme kaynağının arşiv güncellemesi olması; G6'da monoton azalmayan kuralı | Ekip incelemesi | Yok (henüz sonuç yok) |
| 2026-11-10 | v0.2 | Ekip kararları işlendi (ekteki 7 karar onaylandı); hedef sayısı tabanlı analiz; Wilcoxon'da sıfır/eşit fark kuralları ve işaret çevirme permütasyon testi; ayrı p ve pratik eşik raporlaması; SD farkına dayalı değişkenlik analizi ve Holm aileleri; fenotipik çeşitliliğin tanı amaçlı ek hesaplama olarak sınıflandırılması; G2 zorunlu/betimsel kriter ayrımı; geçmişte başlatma kaydı ve doğal kayıt/dolgu ayrımı; ara bütçe eşikleri (1.562,5 / 4.687,5); operatör uç noktalarında yörünge eşdeğerliği beklenmemesi; terminoloji; FB-SEL adı; E4 yöntem listesi; E6 tasarımı | Ekip incelemesi | Yok (henüz sonuç yok) |

---

## Ek: Onaylanan kararlar (v0.2'den itibaren)
1. E5 için yeni ortam seed'leri: {1001, …, 1010}.
2. E5: 10 yöntem, 9.000 koşu.
3. Yalnızca doğrusal planlar.
4. E6 isteğe bağlı, ana paketin dışında.
5. Birincil aile: P1–P4 × 3 senaryo = 12 test, Holm.
6. Pratik anlamlılık eşiği: tek hedef.
7. Zenodo arşivi gönderim planında. DOI yayımlandığında eklenir.

**Dondurma:** v0.7 ekip tarafından onaylandı ve bu belge v1.0 olarak donduruldu. G2–G5 kod doğrulaması olduğu için v1.0'dan önce çalıştırılabilir. **Pilot ve kapı koşularının sonuçları yalnızca kod doğrulaması için kullanılır, performans analizine dahil edilmez.**
