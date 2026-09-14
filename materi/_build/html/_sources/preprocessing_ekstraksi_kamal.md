---
jupytext:
  formats: md:myst
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.11.5
kernelspec:
  display_name: Python 3
  language: python
  name: python3
---

# Preprocessing dan Ekstraksi Fitur

Tahap ini melanjutkan data kualitas udara **Kecamatan Kamal, Bangkalan** (NO2) yang
sudah dikumpulkan pada tugas sebelumnya. Sebelum data dipakai untuk ekstraksi fitur,
data perlu melalui tiga tahap preprocessing: **deteksi & perbaikan outlier**, **imputasi missing value**, lalu **ekstraksi fitur** dengan TSFEL.

## 1. Deteksi & Perbaikan Outlier

Deteksi outlier dilakukan dengan **Isolation Forest** (asumsi 5% data adalah anomali),
lalu nilai yang terdeteksi sebagai outlier diganti `NaN` dan diisi ulang dengan
interpolasi linear terhadap waktu.

```{code-cell} ipython3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.ensemble import IsolationForest

CONTAMINATION = 0.05
pol = "NO2"

# 1. Load data hasil crawling
df = pd.read_csv("no2_kamal.csv")
df["date"] = pd.to_datetime(df["date"])
df = df.sort_values("date").reset_index(drop=True)
df[pol] = pd.to_numeric(df[pol], errors="coerce")
df = df.dropna(subset=[pol]).copy()

# 2. Deteksi outlier dengan Isolation Forest
model = IsolationForest(contamination=CONTAMINATION, random_state=42)
pred = model.fit_predict(df[[pol]])
df["anomaly"] = pred  # -1 = outlier, 1 = normal
outliers = df[df["anomaly"] == -1]
print(f"[{pol}] Jumlah outlier terdeteksi: {len(outliers)} dari {len(df)} data")

# 3. Ganti outlier jadi NaN, lalu interpolasi
df_fixed = df.copy()
df_fixed.loc[df_fixed["anomaly"] == -1, pol] = np.nan
df_fixed[pol] = df_fixed[pol].interpolate(method="linear").ffill().bfill()

# 4. Plot sebelum vs sesudah
fig, axes = plt.subplots(2, 1, figsize=(15, 8), sharex=True)
axes[0].plot(df["date"], df[pol], label=f"{pol} (asli)", linewidth=1)
axes[0].scatter(outliers["date"], outliers[pol], color="red",
                marker="o", label="Outlier (Isolation Forest)", zorder=5)
axes[0].set_title(f"Sebelum Perbaikan - Deteksi Outlier {pol}")
axes[0].legend()

axes[1].plot(df_fixed["date"], df_fixed[pol], color="green", linewidth=1,
             label=f"{pol} (setelah outlier diganti & diinterpolasi)")
axes[1].set_title(f"Sesudah Perbaikan Outlier {pol}")
axes[1].legend()

plt.tight_layout()
plt.savefig(f"outlier_{pol}_before_after.png", dpi=150)
plt.show()

df_fixed[["date", pol]].to_csv(f"{pol}_Kamal_Timeseries_fixed.csv", index=False)
```


## 2. Imputasi Missing Value

Missing value pada data mentah diisi penuh menggunakan interpolasi linear terhadap waktu, dilanjutkan forward-fill dan backward-fill untuk nilai yang tersisa di ujung deret. Setelah proses ini tidak ada lagi nilai kosong yang masuk ke tahap ekstraksi fitur.

```{code-cell} ipython3
pol = "NO2"

df_fixed = pd.read_csv(f"{pol}_Kamal_Timeseries_fixed.csv")
df_fixed["date"] = pd.to_datetime(df_fixed["date"])
df_fixed = df_fixed.sort_values("date").reset_index(drop=True)

# Buat index harian lengkap 31 Agu 2025 – 31 Agu 2026
full_index = pd.date_range(start="2025-08-31", end="2026-08-31", freq="D")
df_full = df_fixed.set_index("date").reindex(full_index)
df_full.index.name = "date"

n_missing = df_full[pol].isna().sum()
print(f"Missing value sebelum imputasi: {n_missing} hari")

df_full[pol] = df_full[pol].interpolate(method="time").ffill().bfill()

n_missing_after = df_full[pol].isna().sum()
print(f"Missing value setelah imputasi: {n_missing_after} hari")
print(f"Total data setelah imputasi   : {len(df_full)} hari")

df_imputed = df_full.reset_index()
df_imputed.to_csv(f"{pol}_Kamal_Timeseries_imputed.csv", index=False)
```

## 3. Ekstraksi Fitur dengan TSFEL

Ekstraksi fitur memakai [TSFEL](https://tsfel.readthedocs.io/), menghasilkan **68 fitur** dari 3 domain (statistical, temporal, spectral) untuk polutan NO2. TSFEL versi terbaru memisahkan beberapa fitur non-linear (`dfa`, `higuchi_fractal_dimension`, `hurst_exponent`, `lempel_ziv`, `maximum_fractal_length`, `petrosian_fractal_dimension`, `mse`) ke domain *fractal* tersendiri; karena tugas ini hanya meminta 3 domain, fitur-fitur tersebut digabungkan ke kelompok **Temporal** sesuai pengelompokan awal TSFEL.

### Penjelasan Fitur per Domain

Setiap fitur yang diekstrak TSFEL merepresentasikan karakteristik tertentu dari deret waktu NO2. Berikut penjelasan dan rumus matematis masing-masing fitur berdasarkan domain-nya. Notasi yang digunakan: $x = \{x_1, x_2, \ldots, x_N\}$ adalah sinyal dengan $N$ sampel, $\bar{x}$ adalah rata-rata, dan $t_i$ adalah nilai waktu ke-$i$.

---

#### Domain Statistical (21 Fitur)

Fitur statistik merangkum distribusi nilai sinyal secara global tanpa mempertimbangkan urutan waktu. Fitur-fitur ini menangkap bentuk, sebaran, dan keruncingan distribusi data NO2.

| # | Fitur | Penjelasan | Rumus |
|---|---|---|---|
| 1 | **abs_energy** | Total energi sinyal; jumlah kuadrat seluruh nilai sampel. Nilai besar menunjukkan konsentrasi NO2 yang tinggi secara keseluruhan. | $E = \sum_{i=1}^{N} x_i^2$ |
| 2 | **average_power** | Rata-rata daya sinyal per sampel; energi yang dinormalisasi terhadap panjang sinyal. | $P = \dfrac{1}{N}\sum_{i=1}^{N} x_i^2$ |
| 3 | **calc_max** | Nilai maksimum dari seluruh sampel sinyal; puncak konsentrasi NO2 tertinggi dalam periode. | $x_{\max} = \max(x_i)$ |
| 4 | **calc_mean** | Rata-rata aritmetika sinyal; representasi nilai sentral konsentrasi NO2. | $\bar{x} = \dfrac{1}{N}\sum_{i=1}^{N} x_i$ |
| 5 | **calc_median** | Nilai tengah ketika data diurutkan; lebih robust terhadap outlier dibanding mean. | $\tilde{x} = \text{median}(x)$ |
| 6 | **calc_min** | Nilai minimum dari seluruh sampel; konsentrasi NO2 terendah dalam periode. | $x_{\min} = \min(x_i)$ |
| 7 | **calc_std** | Simpangan baku; mengukur seberapa jauh nilai menyebar dari rata-rata. | $\sigma = \sqrt{\dfrac{1}{N}\sum_{i=1}^{N}(x_i - \bar{x})^2}$ |
| 8 | **calc_var** | Variansi sinyal; kuadrat dari simpangan baku, mencerminkan fluktuasi total. | $\sigma^2 = \dfrac{1}{N}\sum_{i=1}^{N}(x_i - \bar{x})^2$ |
| 9 | **ecdf** | Nilai Empirical Cumulative Distribution Function pada titik tertentu; proporsi data yang bernilai ≤ titik tersebut. | $F_n(x) = \dfrac{1}{N}\sum_{i=1}^{N} \mathbf{1}[x_i \leq x]$ |
| 10 | **ecdf_percentile** | Nilai sinyal pada persentil tertentu (default P25 & P75) dari ECDF; batas bawah dan atas distribusi. | $F_n^{-1}(p) = \inf\{x : F_n(x) \geq p\}$ |
| 11 | **ecdf_percentile_count** | Jumlah sampel yang jatuh di bawah nilai persentil tertentu. | $\displaystyle\sum_{i=1}^{N} \mathbf{1}[x_i \leq F_n^{-1}(p)]$ |
| 12 | **ecdf_slope** | Kemiringan ECDF antara dua persentil; mencerminkan kepadatan distribusi di rentang tersebut. Nilai besar berarti banyak data terkonsentrasi di rentang sempit. | $\text{slope} = \dfrac{F_n(p_2) - F_n(p_1)}{x_{p_2} - x_{p_1}}$ |
| 13 | **entropy** | Entropi Shannon berbasis histogram; mengukur ketidakpastian atau kerumitan distribusi nilai sinyal. Nilai mendekati 1 berarti distribusi merata. | $H = -\sum_{k} p_k \log_2(p_k)$ |
| 14 | **hist_mode** | Nilai tengah bin histogram dengan frekuensi tertinggi (modus distribusi). | $\hat{x} = \arg\max_{\text{bin}} \;\text{count}_k$ |
| 15 | **interq_range** | Rentang interkuartil; selisih kuartil atas (Q3) dan kuartil bawah (Q1). Mengukur sebaran 50% data tengah, robust terhadap outlier. | $IQR = Q_3 - Q_1$ |
| 16 | **kurtosis** | Keruncingan distribusi relatif terhadap distribusi normal. Nilai negatif = distribusi lebih rata (platikurtik); positif = lebih runcing (leptokurtik). | $\kappa = \dfrac{\mu_4}{\sigma^4}$, di mana $\mu_4 = \dfrac{1}{N}\sum(x_i-\bar{x})^4$ |
| 17 | **mean_abs_deviation** | Rata-rata simpangan absolut dari mean; ukuran dispersi yang tidak sensitif terhadap arah simpangan. | $MAD_\mu = \dfrac{1}{N}\sum_{i=1}^{N} |x_i - \bar{x}|$ |
| 18 | **median_abs_deviation** | Median dari simpangan absolut terhadap median sinyal; lebih robust dari MAD berbasis mean. | $MAD_m = \text{median}(|x_i - \tilde{x}|)$ |
| 19 | **pk_pk_distance** | Jarak puncak ke lembah; selisih nilai maksimum dan minimum. Mengukur amplitudo keseluruhan sinyal. | $D_{pk} = x_{\max} - x_{\min}$ |
| 20 | **rms** | Root Mean Square; ukuran amplitudo efektif atau daya rata-rata sinyal. | $RMS = \sqrt{\dfrac{1}{N}\sum_{i=1}^{N} x_i^2}$ |
| 21 | **skewness** | Kemiringan distribusi. Nilai positif = distribusi berekor ke kanan; negatif = berekor ke kiri. | $\gamma_1 = \dfrac{\mu_3}{\sigma^3}$, di mana $\mu_3 = \dfrac{1}{N}\sum(x_i-\bar{x})^3$ |

---

#### Domain Temporal (21 Fitur, termasuk sub-kategori Fraktal)

Fitur temporal menangkap karakteristik sinyal dalam domain waktu, meliputi pola perubahan antar sampel, korelasi, tren, serta kompleksitas struktural dan fraktal dari deret waktu NO2.

| # | Fitur | Penjelasan | Rumus |
|---|---|---|---|
| 1 | **auc** | Area Under Curve; luas di bawah kurva sinyal terhadap waktu menggunakan aturan trapesoid. Mewakili "akumulasi" NO2 sepanjang periode. | $AUC = \sum_{i=1}^{N-1} \dfrac{(x_i + x_{i+1})}{2} \cdot \Delta t$ |
| 2 | **autocorr** | Lag optimal dari fungsi autokorelasi; menunjukkan periode pengulangan pola dominan dalam sinyal. | $R(\tau) = \sum_{i=1}^{N-\tau} x_i \cdot x_{i+\tau}$, $\;\tau^* = \arg\max_\tau R(\tau)$ |
| 3 | **calc_centroid** | Centroid temporal; "pusat massa" waktu dari sinyal, titik waktu di mana energi sinyal terpusat. | $C_t = \dfrac{\sum_{i=1}^{N} t_i \cdot |x_i|}{\sum_{i=1}^{N} |x_i|}$ |
| 4 | **distance** | Total jarak Euclidean yang ditempuh sinyal sepanjang waktu (panjang kurva). Mengukur seberapa "berkelok" lintasan sinyal. | $D = \sum_{i=1}^{N-1} \sqrt{(\Delta t)^2 + (x_{i+1}-x_i)^2}$ |
| 5 | **mean_abs_diff** | Rata-rata nilai absolut dari selisih antar sampel berurutan; ukuran rata-rata laju perubahan sinyal. | $\overline{|\Delta x|} = \dfrac{1}{N-1}\sum_{i=1}^{N-1}|x_{i+1}-x_i|$ |
| 6 | **mean_diff** | Rata-rata dari selisih antar sampel berurutan (dengan tanda); mencerminkan tren naik atau turun secara global. | $\overline{\Delta x} = \dfrac{1}{N-1}\sum_{i=1}^{N-1}(x_{i+1}-x_i)$ |
| 7 | **median_abs_diff** | Median dari nilai absolut selisih antar sampel; lebih robust dari mean_abs_diff terhadap perubahan ekstrem. | $\text{median}(|x_{i+1}-x_i|)$ |
| 8 | **median_diff** | Median dari selisih antar sampel berurutan; estimasi tren robust terhadap outlier. | $\text{median}(x_{i+1}-x_i)$ |
| 9 | **negative_turning** | Jumlah titik balik negatif (puncak lokal ke lembah); menghitung frekuensi penurunan NO2. | $\sum_{i=2}^{N-1} \mathbf{1}[x_{i-1} < x_i \;\text{dan}\; x_i > x_{i+1}]$ |
| 10 | **neighbourhood_peaks** | Jumlah puncak lokal dalam lingkungan tertentu; mengidentifikasi berapa banyak puncak signifikan dalam sinyal. | Titik $x_i$ adalah puncak jika $x_i > x_j \;\forall j \in [i-n, i+n],\; j \neq i$ |
| 11 | **positive_turning** | Jumlah titik balik positif (lembah lokal ke puncak); menghitung frekuensi kenaikan NO2. | $\sum_{i=2}^{N-1} \mathbf{1}[x_{i-1} > x_i \;\text{dan}\; x_i < x_{i+1}]$ |
| 12 | **slope** | Kemiringan regresi linear deret waktu; tren jangka panjang naik atau turun dalam periode pengamatan. | $\beta = \dfrac{\sum(t_i - \bar{t})(x_i - \bar{x})}{\sum(t_i - \bar{t})^2}$ |
| 13 | **sum_abs_diff** | Jumlah total nilai absolut dari selisih antar sampel; ukuran total variasi sinyal (total variation). | $TV = \sum_{i=1}^{N-1}|x_{i+1}-x_i|$ |
| 14 | **zero_cross** | Jumlah persilangan sinyal terhadap nol (atau terhadap rata-rata setelah di-detrend); mengukur frekuensi osilasi. | $ZC = \sum_{i=1}^{N-1} \mathbf{1}[\text{sign}(x_i) \neq \text{sign}(x_{i+1})]$ |
| 15 | **dfa** | *Detrended Fluctuation Analysis*; mengukur korelasi jangka panjang dalam sinyal. Nilai $\alpha \approx 0.5$ = acak; $\alpha > 0.5$ = korelasi persisten; $\alpha < 0.5$ = anti-korelasi. | $F(n) \sim n^\alpha$, $\;\alpha$ diperoleh dari regresi log-log $\log F(n)$ terhadap $\log n$ |
| 16 | **higuchi_fractal_dimension** | Dimensi fraktal Higuchi; mengukur kompleksitas atau "kekasaran" sinyal. Nilai antara 1 (halus) dan 2 (sangat kompleks/acak). | $L_m(k) = \dfrac{N-1}{\lfloor(N-m)/k\rfloor \cdot k^2}\sum_{i=1}^{\lfloor(N-m)/k\rfloor}|x_{m+ik}-x_{m+(i-1)k}|$, $\;L(k) \sim k^{-D}$ |
| 17 | **hurst_exponent** | Eksponen Hurst; mengukur memori jangka panjang sinyal. $H > 0.5$ = tren persisten; $H < 0.5$ = mean-reverting; $H = 0.5$ = acak (Brownian). | $E[R(n)/S(n)] = C \cdot n^H$ |
| 18 | **lempel_ziv** | Kompleksitas Lempel-Ziv; mengukur kebaruan pola dalam sinyal biner (setelah thresholding). Nilai tinggi berarti sinyal lebih acak dan tidak berulang. | $C_{LZ} = \dfrac{c(n)}{n / \log_2 n}$, di mana $c(n)$ = jumlah sub-string unik |
| 19 | **maximum_fractal_length** | Panjang fraktal maksimum dari sinyal; terkait dengan kompleksitas geometri kurva sinyal pada skala terkecil. | $MFL = \log\left(\sqrt{\dfrac{1}{N}\sum_{i=1}^{N-1}(x_{i+1}-x_i)^2}\right)$ |
| 20 | **mse** | *Multiscale Entropy*; mengukur kompleksitas sinyal pada berbagai skala temporal. Nilai tinggi menunjukkan dinamika yang kaya dan tidak tereduksi pada skala kasar. | $SampEn(m, r, N)$ dihitung pada versi *coarse-grained* $y^{(\tau)}_j = \dfrac{1}{\tau}\sum_{i=(j-1)\tau+1}^{j\tau} x_i$ |
| 21 | **petrosian_fractal_dimension** | Dimensi fraktal Petrosian; estimasi cepat kompleksitas sinyal berbasis jumlah perubahan tanda turunan pertama. | $PFD = \dfrac{\log_{10}(N)}{\log_{10}(N) + \log_{10}\!\left(\dfrac{N}{N + 0.4 \cdot N_\delta}\right)}$, $N_\delta$ = jumlah perubahan tanda $\Delta x$ |

---

#### Domain Spectral (26 Fitur)

Fitur spektral diperoleh melalui transformasi sinyal ke domain frekuensi (umumnya menggunakan FFT atau wavelet). Fitur-fitur ini menangkap kandungan frekuensi, distribusi daya, dan karakteristik osilasi dari deret waktu NO2.

| # | Fitur | Penjelasan | Rumus |
|---|---|---|---|
| 1 | **fundamental_frequency** | Frekuensi fundamental; komponen frekuensi dengan daya tertinggi dalam spektrum. Mencerminkan periodisitas dominan NO2. | $f_0 = \arg\max_{f} |X(f)|^2$ |
| 2 | **human_range_energy** | Energi dalam rentang frekuensi persepsi manusia (0.6–2.5 Hz); umumnya nol untuk data harian. | $E_{hr} = \sum_{f \in [0.6, 2.5]} |X(f)|^2$ |
| 3 | **lpcc** | *Linear Prediction Cepstral Coefficients*; koefisien cepstral dari model AR; menangkap envelope spektral sinyal. | Dari koefisien LP $a_k$: $c_n = -a_n - \sum_{k=1}^{n-1}\frac{k}{n}c_k a_{n-k}$ |
| 4 | **max_frequency** | Frekuensi yang memiliki daya spektral terbesar; serupa dengan fundamental_frequency tetapi mengacu pada indeks frekuensi tertinggi di bawah Nyquist. | $f_{\max} = \arg\max_{f \leq f_s/2} |X(f)|^2$ |
| 5 | **max_power_spectrum** | Nilai daya spektral maksimum; amplitudo puncak tertinggi dalam Power Spectral Density (PSD). | $P_{\max} = \max_f |X(f)|^2$ |
| 6 | **median_frequency** | Frekuensi yang membagi daya spektral total menjadi dua bagian sama besar. | $f_m : \sum_{f \leq f_m} P(f) = \dfrac{1}{2}\sum_{\text{all}} P(f)$ |
| 7 | **mfcc** | *Mel Frequency Cepstral Coefficients*; koefisien cepstral pada skala Mel; menangkap tekstur spektral seperti yang dipersepsi secara logaritmik. | $MFCC_n = \sum_{k} \log S(k) \cos\!\left[n\!\left(k - \tfrac{1}{2}\right)\tfrac{\pi}{K}\right]$ |
| 8 | **power_bandwidth** | Lebar pita daya; rentang frekuensi yang mengandung sebagian besar daya sinyal (biasanya 95%). | $BW = f_{\text{high}} - f_{\text{low}}$ di mana $\int_{f_{\text{low}}}^{f_{\text{high}}} P(f)\,df = 0.95 \int P(f)\,df$ |
| 9 | **spectral_centroid** | Centroid spektral; "pusat massa" frekuensi berbobot daya. Mencerminkan letak energi sinyal dalam domain frekuensi. | $SC = \dfrac{\sum_f f \cdot |X(f)|^2}{\sum_f |X(f)|^2}$ |
| 10 | **spectral_decrease** | Penurunan spektral; mengukur seberapa cepat amplitudo spektrum turun dari frekuensi rendah ke tinggi. | $SD = \dfrac{\sum_{k=2}^{K} \dfrac{|X(k)| - |X(1)|}{k-1}}{\sum_{k=2}^{K}|X(k)|}$ |
| 11 | **spectral_distance** | Jarak antara dua spektrum (atau antara spektrum dan referensi); mengukur perbedaan kandungan frekuensi. | $D_s = \sqrt{\sum_f (P_1(f) - P_2(f))^2}$ |
| 12 | **spectral_entropy** | Entropi Shannon dari distribusi daya spektral; nilai tinggi = daya tersebar merata di seluruh frekuensi (lebih acak). | $H_s = -\sum_f p(f) \log_2 p(f)$, $\;p(f) = \dfrac{|X(f)|^2}{\sum|X(f)|^2}$ |
| 13 | **spectral_kurtosis** | Keruncingan distribusi daya spektral; mengukur peakedness distribusi daya di frekuensi tertentu. | $K_s = \dfrac{\sum_f (f - SC)^4 \cdot P(f)}{\left(\sum_f (f - SC)^2 \cdot P(f)\right)^2}$ |
| 14 | **spectral_positive_turning** | Jumlah titik balik positif (puncak lokal) dalam spektrum daya; mencerminkan berapa banyak pita frekuensi aktif. | Titik $f_i$ adalah puncak spektral jika $P(f_{i-1}) < P(f_i) > P(f_{i+1})$ |
| 15 | **spectral_roll_off** | Frekuensi di mana 85% (atau 95%) energi spektral terakumulasi; batas atas efektif spektrum sinyal. | $f_{ro} : \sum_{f \leq f_{ro}} P(f) = 0.85 \sum_{\text{all}} P(f)$ |
| 16 | **spectral_roll_on** | Frekuensi di mana energi spektral mulai terakumulasi secara signifikan (batas bawah efektif spektrum). | $f_{rn} : \sum_{f \leq f_{rn}} P(f) = 0.05 \sum_{\text{all}} P(f)$ |
| 17 | **spectral_skewness** | Kemiringan distribusi daya spektral; menunjukkan apakah energi lebih terkonsentrasi di frekuensi rendah atau tinggi. | $\gamma_s = \dfrac{\sum_f (f - SC)^3 \cdot P(f)}{\left(\sum_f (f - SC)^2 \cdot P(f)\right)^{3/2}}$ |
| 18 | **spectral_slope** | Kemiringan regresi linear spektrum amplitudo; menggambarkan tren umum penurunan atau kenaikan amplitudo terhadap frekuensi. | $\beta_s = \dfrac{\sum_f (f - \bar{f})(|X(f)| - \overline{|X|})}{\sum_f (f - \bar{f})^2}$ |
| 19 | **spectral_spread** | Penyebaran spektral; simpangan baku frekuensi berbobot daya terhadap centroid spektral. Mengukur lebar efektif spektrum. | $SS = \sqrt{\dfrac{\sum_f (f - SC)^2 \cdot P(f)}{\sum_f P(f)}}$ |
| 20 | **spectral_variation** | Variasi spektral; mengukur perubahan spektrum antar frame (korelasi silang spektrum). Nilai mendekati 0 = sangat berubah; 1 = stasioner. | $SV = 1 - \dfrac{\sum_f |X_t(f)| \cdot |X_{t+1}(f)|}{\sqrt{\sum_f |X_t(f)|^2 \cdot \sum_f |X_{t+1}(f)|^2}}$ |
| 21 | **spectrogram_mean_coeff** | Rata-rata koefisien dari spektrogram (STFT); mewakili intensitas rata-rata energi di setiap band frekuensi sepanjang waktu. | $\bar{S}_k = \dfrac{1}{T}\sum_{t=1}^{T} |STFT(t, k)|^2$ |
| 22 | **wavelet_abs_mean** | Rata-rata nilai absolut koefisien wavelet; mengukur amplitudo rata-rata fitur sinyal yang ditangkap oleh dekomposisi wavelet. | $\overline{|W|} = \dfrac{1}{N_w}\sum_{j}|W_j|$ |
| 23 | **wavelet_energy** | Energi koefisien wavelet; jumlah kuadrat koefisien wavelet, mengukur total energi pada skala dekomposisi tertentu. | $E_w = \sum_{j} W_j^2$ |
| 24 | **wavelet_entropy** | Entropi Shannon dari distribusi energi wavelet antar level; nilai tinggi = energi tersebar merata di banyak skala (kompleks). | $H_w = -\sum_{j} p_j \log_2 p_j$, $\;p_j = \dfrac{W_j^2}{\sum_k W_k^2}$ |
| 25 | **wavelet_std** | Simpangan baku koefisien wavelet; mengukur variabilitas amplitudo pada skala yang dianalisis. | $\sigma_w = \sqrt{\dfrac{1}{N_w}\sum_j (W_j - \bar{W})^2}$ |
| 26 | **wavelet_var** | Variansi koefisien wavelet; kuadrat dari simpangan baku wavelet, mencerminkan fluktuasi energi pada skala tertentu. | $\sigma_w^2 = \dfrac{1}{N_w}\sum_j (W_j - \bar{W})^2$ |

---

```{code-cell} ipython3
import pandas as pd

pol = "NO2"
result_df = pd.read_csv(f"{pol}_Kamal_TSFEL.csv")

STATISTICAL = [
    "abs_energy", "average_power", "calc_max", "calc_mean", "calc_median",
    "calc_min", "calc_std", "calc_var", "ecdf", "ecdf_percentile",
    "ecdf_percentile_count", "ecdf_slope", "entropy", "hist_mode",
    "interq_range", "kurtosis", "mean_abs_deviation", "median_abs_deviation",
    "pk_pk_distance", "rms", "skewness"
]
TEMPORAL = [
    "auc", "autocorr", "calc_centroid", "dfa", "distance",
    "higuchi_fractal_dimension", "hurst_exponent", "lempel_ziv",
    "maximum_fractal_length", "mean_abs_diff", "mean_diff",
    "median_abs_diff", "median_diff", "mse", "negative_turning",
    "neighbourhood_peaks", "petrosian_fractal_dimension",
    "positive_turning", "slope", "sum_abs_diff", "zero_cross"
]
SPECTRAL = [
    "fundamental_frequency", "human_range_energy", "lpcc", "max_frequency",
    "max_power_spectrum", "median_frequency", "mfcc", "power_bandwidth",
    "spectral_centroid", "spectral_decrease", "spectral_distance",
    "spectral_entropy", "spectral_kurtosis", "spectral_positive_turning",
    "spectral_roll_off", "spectral_roll_on", "spectral_skewness",
    "spectral_slope", "spectral_spread", "spectral_variation",
    "spectrogram_mean_coeff", "wavelet_abs_mean", "wavelet_energy",
    "wavelet_entropy", "wavelet_std", "wavelet_var"
]

print(f"=== Statistical Domain ({len(STATISTICAL)} fitur) ===")
for f in STATISTICAL:
    print(f"| {f} | {result_df[f].values[0]} |")

print(f"\n=== Temporal Domain ({len(TEMPORAL)} fitur) ===")
for f in TEMPORAL:
    print(f"| {f} | {result_df[f].values[0]} |")

print(f"\n=== Spectral Domain ({len(SPECTRAL)} fitur) ===")
for f in SPECTRAL:
    print(f"| {f} | {result_df[f].values[0]} |")
```

### Hasil ekstraksi fitur per domain

**Statistical Domain (21 fitur)**

| Fitur | NO2 |
| --- | --- |
| abs_energy | 8.004483812520137e-07 |
| average_power | 2.193009263704147e-09 |
| calc_max | 8.261699258582667e-05 |
| calc_mean | 4.304078602292036e-05 |
| calc_median | 4.281815054127946e-05 |
| calc_min | -1.074266492651077e-05 |
| calc_std | 1.8289564610563453e-05 |
| calc_var | 3.3450817364397506e-10 |
| ecdf | 0.0150273224043715 |
| ecdf_percentile | 4.262600214133272e-05 |
| ecdf_percentile_count | 182.5 |
| ecdf_slope | 16798.33038578079 |
| entropy | 0.9993583051330968 |
| hist_mode | 4.060514670527482e-05 |
| interq_range | 2.93190165393753e-05 |
| kurtosis | -0.7653806440586406 |
| mean_abs_deviation | 1.527524349419392e-05 |
| median_abs_deviation | 1.4418096179724671e-05 |
| pk_pk_distance | 9.335965751233744e-05 |
| rms | 4.6765558214510725e-05 |
| skewness | -0.0484239574991572 |

**Temporal Domain (21 fitur, termasuk sub-kategori fraktal)**

| Fitur | NO2 |
| --- | --- |
| auc | 0.0157404357614723 |
| autocorr | 11.0 |
| calc_centroid | 166.6274749901177 |
| dfa | 1.0650859251687137 |
| distance | 365.0000000236696 |
| higuchi_fractal_dimension | 1.7864516865906903 |
| hurst_exponent | 0.8803015029826863 |
| lempel_ziv | 0.1530054644808743 |
| maximum_fractal_length | -2.488890466514544 |
| mean_abs_diff | 7.365990754743968e-06 |
| mean_diff | -2.9038234708722294e-08 |
| median_abs_diff | 4.423392965691168e-06 |
| median_diff | 4.016578064433205e-07 |
| mse | 0.8092219596587233 |
| negative_turning | 60.0 |
| neighbourhood_peaks | 18.0 |
| petrosian_fractal_dimension | 1.021493424787648 |
| positive_turning | 60.0 |
| slope | -3.355667328498242e-08 |
| sum_abs_diff | 0.0026885866254815 |
| zero_cross | 2.0 |

**Spectral Domain (26 fitur)**

| Fitur | NO2 |
| --- | --- |
| fundamental_frequency | 0.0027322404371584 |
| human_range_energy | 0.0 |
| lpcc | 0.718735662231064 |
| max_frequency | 0.4207650273224044 |
| max_power_spectrum | 84.43438787262676 |
| median_frequency | 0.0491803278688524 |
| mfcc | 17.634818598055492 |
| power_bandwidth | 0.2486338797814207 |
| spectral_centroid | 0.116987781071585 |
| spectral_decrease | -2.117715250437212 |
| spectral_distance | -2.776739725085843 |
| spectral_entropy | 0.6253514711926725 |
| spectral_kurtosis | 2.953248019217717 |
| spectral_positive_turning | 57.0 |
| spectral_roll_off | 0.4207650273224044 |
| spectral_roll_on | 0.0 |
| spectral_skewness | 1.0989809936527493 |
| spectral_slope | -0.0343237171288835 |
| spectral_spread | 0.1425901303285489 |
| spectral_variation | 0.2474728843010087 |
| spectrogram_mean_coeff | 4.3894200449494655e-10 |
| wavelet_abs_mean | 1.4975436285281366e-06 |
| wavelet_energy | 2.512626063016688e-05 |
| wavelet_entropy | 2.1182052206750783 |
| wavelet_std | 2.507356733958021e-05 |
| wavelet_var | 6.99915761051232e-10 |

## Ringkasan

| Tahap | Keterangan |
| --- | --- |
| Preprocessing | Data difilter sesuai Kecamatan Kamal, missing value diimputasi penuh (0 nilai kosong tersisa), outlier dideteksi dengan Isolation Forest (~5% data) dan diperbaiki lewat interpolasi waktu |
| Ekstraksi fitur | 68 fitur time series diekstrak dengan TSFEL untuk NO2, terbagi ke domain Statistical (21), Temporal (21, termasuk fraktal), dan Spectral (26) |