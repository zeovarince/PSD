# Fitur-Fitur TSFEL pada Time Series

Data yang digunakan pada seluruh perhitungan manual adalah 20 data time series berikut:

$$x = \{2, 4, 5, 4, 9, 7, 3, 7, 9, 7, 11, 10, 12, 13, 12, 14, 15, 16, 15, 17\}$$

dengan $N = 20$, $\bar{x} = 9{,}6$, dan periode $t = \{1, 2, \ldots, 20\}$.

---

## Domain Statistical (21 Fitur)

Fitur statistik merangkum distribusi nilai sinyal secara global tanpa mempertimbangkan urutan waktu. Fitur-fitur ini menangkap bentuk, sebaran, dan keruncingan distribusi data sehingga cocok digunakan ketika kita ingin mengetahui karakteristik umum sinyal seperti seberapa besar nilainya, seberapa variatif, dan apakah distribusinya simetris atau condong ke satu arah.

---

### 1. `abs_energy`

**Definisi dan Kegunaan.** `abs_energy` adalah total energi sinyal, dihitung sebagai jumlah kuadrat dari seluruh nilai sampel. Fitur ini digunakan untuk mengukur besarnya "daya total" yang terkandung dalam sinyal. Semakin besar nilainya, semakin tinggi intensitas keseluruhan sinyal. Fitur ini berguna ketika ingin membandingkan magnitude global antar segmen sinyal yang berbeda.

**Rumus.**

$$E = \sum_{i=1}^{N} x_i^2$$

**Perhitungan Manual.**

$$E = 2^2 + 4^2 + 5^2 + 4^2 + 9^2 + 7^2 + 3^2 + 7^2 + 9^2 + 7^2 + 11^2 + 10^2 + 12^2 + 13^2 + 12^2 + 14^2 + 15^2 + 16^2 + 15^2 + 17^2$$

$$= 4 + 16 + 25 + 16 + 81 + 49 + 9 + 49 + 81 + 49 + 121 + 100 + 144 + 169 + 144 + 196 + 225 + 256 + 225 + 289 = \mathbf{2248}$$

**Implementasi Python.**

```python
import numpy as np

x = np.array([2, 4, 5, 4, 9, 7, 3, 7, 9, 7, 11, 10, 12, 13, 12, 14, 15, 16, 15, 17])
abs_energy = np.sum(x ** 2)
print(f"abs_energy = {abs_energy}")  # Output: 2248
```

---

### 2. `average_power`

**Definisi dan Kegunaan.** `average_power` adalah rata-rata daya sinyal per sampel, yaitu energi total yang dinormalisasi terhadap panjang sinyal $N$. Fitur ini memberikan gambaran rata-rata intensitas sinyal per titik waktu, sehingga dapat dibandingkan antar sinyal dengan panjang berbeda. Digunakan ketika panjang sinyal bervariasi dan perbandingan energi harus adil.

**Rumus.**

$$P = \frac{1}{N} \sum_{i=1}^{N} x_i^2$$

**Perhitungan Manual.**

$$P = \frac{E}{N} = \frac{2248}{20} = \mathbf{112{,}4}$$

**Implementasi Python.**

```python
import numpy as np

x = np.array([2, 4, 5, 4, 9, 7, 3, 7, 9, 7, 11, 10, 12, 13, 12, 14, 15, 16, 15, 17])
average_power = np.mean(x ** 2)
print(f"average_power = {average_power}")  # Output: 112.4
```

---

### 3. `calc_max`

**Definisi dan Kegunaan.** `calc_max` adalah nilai sampel terbesar dalam sinyal. Fitur ini digunakan untuk mendeteksi puncak tertinggi yang pernah dicapai sinyal dalam periode pengamatan. Berguna untuk mengidentifikasi kondisi ekstrem tertinggi, misalnya konsentrasi polutan tertinggi atau beban puncak.

**Rumus.**

$$x_{\max} = \max(x_i)$$

**Perhitungan Manual.**

Dari data $\{2, 4, 5, 4, 9, 7, 3, 7, 9, 7, 11, 10, 12, 13, 12, 14, 15, 16, 15, 17\}$, nilai terbesar adalah:

$$x_{\max} = \mathbf{17}$$

**Implementasi Python.**

```python
import numpy as np

x = np.array([2, 4, 5, 4, 9, 7, 3, 7, 9, 7, 11, 10, 12, 13, 12, 14, 15, 16, 15, 17])
calc_max = np.max(x)
print(f"calc_max = {calc_max}")  # Output: 17
```

---

### 4. `calc_mean`

**Definisi dan Kegunaan.** `calc_mean` adalah rata-rata aritmetika dari seluruh nilai sinyal. Fitur ini merepresentasikan nilai sentral atau "level" rata-rata sinyal. Digunakan pada hampir semua analisis awal sebagai tolok ukur dasar untuk memahami posisi nilai sinyal secara keseluruhan.

**Rumus.**

$$\bar{x} = \frac{1}{N} \sum_{i=1}^{N} x_i$$

**Perhitungan Manual.**

$$\bar{x} = \frac{2 + 4 + 5 + 4 + 9 + 7 + 3 + 7 + 9 + 7 + 11 + 10 + 12 + 13 + 12 + 14 + 15 + 16 + 15 + 17}{20} = \frac{192}{20} = \mathbf{9{,}6}$$

**Implementasi Python.**

```python
import numpy as np

x = np.array([2, 4, 5, 4, 9, 7, 3, 7, 9, 7, 11, 10, 12, 13, 12, 14, 15, 16, 15, 17])
calc_mean = np.mean(x)
print(f"calc_mean = {calc_mean}")  # Output: 9.6
```

---

### 5. `calc_median`

**Definisi dan Kegunaan.** `calc_median` adalah nilai tengah sinyal ketika seluruh sampel diurutkan dari kecil ke besar. Median lebih robust terhadap outlier dibandingkan mean karena tidak terpengaruh oleh nilai-nilai ekstrem. Digunakan ketika distribusi data menceng atau terdapat pencilan yang signifikan.

**Rumus.**

$$\tilde{x} = \text{median}(x)$$

**Perhitungan Manual.**

Data diurutkan: $\{2, 3, 4, 4, 5, 7, 7, 7, 9, 9, 10, 11, 12, 12, 13, 14, 15, 15, 16, 17\}$.

Karena $N = 20$ (genap), median adalah rata-rata nilai ke-10 dan ke-11:

$$\tilde{x} = \frac{x_{(10)} + x_{(11)}}{2} = \frac{9 + 10}{2} = \mathbf{9{,}5}$$

**Implementasi Python.**

```python
import numpy as np

x = np.array([2, 4, 5, 4, 9, 7, 3, 7, 9, 7, 11, 10, 12, 13, 12, 14, 15, 16, 15, 17])
calc_median = np.median(x)
print(f"calc_median = {calc_median}")  # Output: 9.5
```

---

### 6. `calc_min`

**Definisi dan Kegunaan.** `calc_min` adalah nilai sampel terkecil dalam sinyal. Fitur ini digunakan untuk mendeteksi kondisi ekstrem terendah, misalnya nilai minimum konsentrasi suatu zat atau titik lembah terdalam dalam deret waktu.

**Rumus.**

$$x_{\min} = \min(x_i)$$

**Perhitungan Manual.**

Dari data, nilai terkecil adalah:

$$x_{\min} = \mathbf{2}$$

**Implementasi Python.**

```python
import numpy as np

x = np.array([2, 4, 5, 4, 9, 7, 3, 7, 9, 7, 11, 10, 12, 13, 12, 14, 15, 16, 15, 17])
calc_min = np.min(x)
print(f"calc_min = {calc_min}")  # Output: 2
```

---

### 7. `calc_std`

**Definisi dan Kegunaan.** `calc_std` adalah simpangan baku (standard deviation) dari sinyal, yang mengukur seberapa jauh nilai-nilai sampel menyebar dari rata-rata. Nilai besar berarti sinyal sangat fluktuatif; nilai kecil berarti sinyal stabil di sekitar mean. Digunakan untuk mengukur volatilitas atau variabilitas sinyal.

**Rumus.**

$$\sigma = \sqrt{\frac{1}{N} \sum_{i=1}^{N} (x_i - \bar{x})^2}$$

**Perhitungan Manual.**

Dengan $\bar{x} = 9{,}6$, hitung $(x_i - 9{,}6)^2$ untuk setiap sampel:

$$(2-9{,}6)^2=57{,}76,\quad (4-9{,}6)^2=31{,}36,\quad (5-9{,}6)^2=21{,}16,\quad (4-9{,}6)^2=31{,}36,\quad (9-9{,}6)^2=0{,}36$$
$$(7-9{,}6)^2=6{,}76,\quad (3-9{,}6)^2=43{,}56,\quad (7-9{,}6)^2=6{,}76,\quad (9-9{,}6)^2=0{,}36,\quad (7-9{,}6)^2=6{,}76$$
$$(11-9{,}6)^2=1{,}96,\quad (10-9{,}6)^2=0{,}16,\quad (12-9{,}6)^2=5{,}76,\quad (13-9{,}6)^2=11{,}56,\quad (12-9{,}6)^2=5{,}76$$
$$(14-9{,}6)^2=19{,}36,\quad (15-9{,}6)^2=29{,}16,\quad (16-9{,}6)^2=40{,}96,\quad (15-9{,}6)^2=29{,}16,\quad (17-9{,}6)^2=54{,}76$$

$$\sum (x_i - \bar{x})^2 = 404{,}80 \implies \sigma = \sqrt{\frac{404{,}80}{20}} = \sqrt{20{,}24} \approx \mathbf{4{,}4989}$$

**Implementasi Python.**

```python
import numpy as np

x = np.array([2, 4, 5, 4, 9, 7, 3, 7, 9, 7, 11, 10, 12, 13, 12, 14, 15, 16, 15, 17])
calc_std = np.std(x)        # population std (ddof=0)
print(f"calc_std = {calc_std:.6f}")  # Output: 4.498889
```

---

### 8. `calc_var`

**Definisi dan Kegunaan.** `calc_var` adalah variansi sinyal, yaitu rata-rata kuadrat simpangan dari mean. Variansi adalah kuadrat dari simpangan baku dan mencerminkan total fluktuasi sinyal. Digunakan ketika ingin mengukur dispersi dalam satuan kuadrat dari data asli.

**Rumus.**

$$\sigma^2 = \frac{1}{N} \sum_{i=1}^{N} (x_i - \bar{x})^2$$

**Perhitungan Manual.**

Menggunakan hasil sebelumnya:

$$\sigma^2 = \frac{404{,}80}{20} = \mathbf{20{,}24}$$

**Implementasi Python.**

```python
import numpy as np

x = np.array([2, 4, 5, 4, 9, 7, 3, 7, 9, 7, 11, 10, 12, 13, 12, 14, 15, 16, 15, 17])
calc_var = np.var(x)        # population variance (ddof=0)
print(f"calc_var = {calc_var:.4f}")  # Output: 20.2400
```

---

### 9. `ecdf`

**Definisi dan Kegunaan.** `ecdf` (*Empirical Cumulative Distribution Function*) menghitung proporsi data yang bernilai lebih kecil atau sama dengan suatu nilai tertentu $x$. Fitur ini memberikan gambaran distribusi kumulatif data secara empiris tanpa asumsi distribusi parametrik. Digunakan untuk memahami sebaran data dan menentukan persentil secara langsung dari data.

**Rumus.**

$$F_n(x) = \frac{1}{N} \sum_{i=1}^{N} \mathbf{1}[x_i \leq x]$$

**Perhitungan Manual.**

Dievaluasi pada $x = \bar{x} = 9{,}6$. Hitung berapa banyak data yang $\leq 9{,}6$:

Data yang memenuhi: $\{2, 4, 5, 4, 9, 7, 3, 7, 9, 7\}$ sebanyak 10 data.

$$F_n(9{,}6) = \frac{10}{20} = \mathbf{0{,}5}$$

**Implementasi Python.**

```python
import numpy as np

x = np.array([2, 4, 5, 4, 9, 7, 3, 7, 9, 7, 11, 10, 12, 13, 12, 14, 15, 16, 15, 17])

def ecdf_at(data, value):
    return np.sum(data <= value) / len(data)

print(f"ECDF at 9.6 = {ecdf_at(x, 9.6)}")  # Output: 0.5
```

---

### 10. `ecdf_percentile`

**Definisi dan Kegunaan.** `ecdf_percentile` adalah nilai sinyal pada persentil tertentu dari ECDF, secara default persentil ke-25 (Q1) dan ke-75 (Q3). Fitur ini merepresentasikan batas bawah dan batas atas dari 50% data tengah. Digunakan untuk memahami rentang distribusi yang paling representatif dari data.

**Rumus.**

$$F_n^{-1}(p) = \inf\{x : F_n(x) \geq p\}$$

**Perhitungan Manual.**

Data terurut: $\{2, 3, 4, 4, 5, 7, 7, 7, 9, 9, 10, 11, 12, 12, 13, 14, 15, 15, 16, 17\}$.

- **P25 (Q1):** Posisi $= 0{,}25 \times 20 = 5$, interpolasi antara nilai ke-5 dan ke-6: $Q_1 = \frac{5+7}{2} \times \ldots = \mathbf{6{,}5}$ (hasil NumPy linear interpolation).
- **P75 (Q3):** Posisi $= 0{,}75 \times 20 = 15$, interpolasi: $Q_3 = \mathbf{13{,}25}$.

**Implementasi Python.**

```python
import numpy as np

x = np.array([2, 4, 5, 4, 9, 7, 3, 7, 9, 7, 11, 10, 12, 13, 12, 14, 15, 16, 15, 17])
p25 = np.percentile(x, 25)
p75 = np.percentile(x, 75)
print(f"P25 = {p25}, P75 = {p75}")  # Output: P25 = 6.5, P75 = 13.25
```

---

### 11. `ecdf_percentile_count`

**Definisi dan Kegunaan.** `ecdf_percentile_count` menghitung jumlah sampel yang bernilai di bawah atau sama dengan nilai persentil tertentu. Fitur ini menginformasikan secara langsung berapa banyak data yang jatuh di bawah batas Q1 dan Q3. Berguna sebagai validasi distribusi dan pengecekan keseimbangan data.

**Rumus.**

$$C_p = \sum_{i=1}^{N} \mathbf{1}[x_i \leq F_n^{-1}(p)]$$

**Perhitungan Manual.**

- **Count $\leq$ Q1 = 6,5:** Data yang memenuhi: $\{2, 4, 5, 4, 3\}$ → **5 data**.
- **Count $\leq$ Q3 = 13,25:** Data yang memenuhi: semua kecuali $\{14, 15, 16, 15, 17\}$ → **15 data**.

**Implementasi Python.**

```python
import numpy as np

x = np.array([2, 4, 5, 4, 9, 7, 3, 7, 9, 7, 11, 10, 12, 13, 12, 14, 15, 16, 15, 17])
p25, p75 = np.percentile(x, 25), np.percentile(x, 75)
count_p25 = np.sum(x <= p25)
count_p75 = np.sum(x <= p75)
print(f"Count <= P25: {count_p25}")  # Output: 5
print(f"Count <= P75: {count_p75}")  # Output: 15
```

---

### 12. `ecdf_slope`

**Definisi dan Kegunaan.** `ecdf_slope` adalah kemiringan ECDF di antara dua titik persentil (P25 dan P75). Nilai yang besar berarti banyak data terkonsentrasi dalam rentang sempit (distribusi runcing), sedangkan nilai kecil mengindikasikan distribusi yang menyebar. Fitur ini menggambarkan kepadatan distribusi di area tengah data.

**Rumus.**

$$\text{slope} = \frac{F_n(p_2) - F_n(p_1)}{x_{p_2} - x_{p_1}}$$

**Perhitungan Manual.**

$$\text{slope} = \frac{0{,}75 - 0{,}25}{13{,}25 - 6{,}5} = \frac{0{,}50}{6{,}75} \approx \mathbf{0{,}0741}$$

**Implementasi Python.**

```python
import numpy as np

x = np.array([2, 4, 5, 4, 9, 7, 3, 7, 9, 7, 11, 10, 12, 13, 12, 14, 15, 16, 15, 17])
p25, p75 = np.percentile(x, 25), np.percentile(x, 75)
N = len(x)
f_p25 = np.sum(x <= p25) / N
f_p75 = np.sum(x <= p75) / N
ecdf_slope = (f_p75 - f_p25) / (p75 - p25)
print(f"ecdf_slope = {ecdf_slope:.6f}")  # Output: 0.074074
```

---

### 13. `entropy`

**Definisi dan Kegunaan.** `entropy` adalah entropi Shannon yang dihitung dari histogram sinyal. Fitur ini mengukur ketidakpastian atau kerumitan distribusi nilai sinyal. Nilai entropi tinggi berarti data tersebar merata di banyak bin (distribusi merata, tidak bisa diprediksi); nilai rendah berarti sebagian besar data terkonsentrasi di sedikit nilai (distribusi terpekat, mudah diprediksi).

**Rumus.**

$$H = -\sum_{k} p_k \log_2(p_k)$$

**Perhitungan Manual.**

Data dibagi menjadi 10 bin. Hasil histogram: frekuensi tiap bin adalah $[2, 2, 1, 3, 2, 1, 3, 1, 3, 2]$, sehingga probabilitasnya:

$$p = [0{,}10,\ 0{,}10,\ 0{,}05,\ 0{,}15,\ 0{,}10,\ 0{,}05,\ 0{,}15,\ 0{,}05,\ 0{,}15,\ 0{,}10]$$

$$H = -(0{,}10 \log_2 0{,}10) \times 5\ -\ (0{,}05 \log_2 0{,}05) \times 3\ -\ (0{,}15 \log_2 0{,}15) \times 3 \approx \mathbf{3{,}2087}$$

**Implementasi Python.**

```python
import numpy as np

x = np.array([2, 4, 5, 4, 9, 7, 3, 7, 9, 7, 11, 10, 12, 13, 12, 14, 15, 16, 15, 17])
hist, _ = np.histogram(x, bins=10)
probs = hist / len(x)
probs = probs[probs > 0]
entropy = -np.sum(probs * np.log2(probs))
print(f"entropy = {entropy:.6f}")  # Output: 3.208695
```

---

### 14. `hist_mode`

**Definisi dan Kegunaan.** `hist_mode` adalah nilai tengah bin histogram yang memiliki frekuensi tertinggi, atau modus dari distribusi sinyal. Fitur ini mengidentifikasi nilai atau rentang nilai yang paling sering muncul dalam sinyal, berguna untuk mengetahui kondisi dominan yang paling umum terjadi.

**Rumus.**

$$\hat{x} = \text{center of } \arg\max_{\text{bin}} \; \text{count}_k$$

**Perhitungan Manual.**

Dari 10 bin dengan rentang $[2, 17]$, lebar bin $= 1{,}5$. Frekuensi tiap bin: $[2, 2, 1, 3, 2, 1, 3, 1, 3, 2]$. Tiga bin dengan frekuensi tertinggi (3) adalah bin ke-4, ke-7, dan ke-9. Bin pertama yang tertinggi adalah bin ke-4 dengan center:

$$\hat{x} = \mathbf{7{,}25}$$

**Implementasi Python.**

```python
import numpy as np

x = np.array([2, 4, 5, 4, 9, 7, 3, 7, 9, 7, 11, 10, 12, 13, 12, 14, 15, 16, 15, 17])
hist, bin_edges = np.histogram(x, bins=10)
bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
hist_mode = bin_centers[np.argmax(hist)]
print(f"hist_mode = {hist_mode:.4f}")  # Output: 7.2500
```

---

### 15. `interq_range`

**Definisi dan Kegunaan.** `interq_range` (*Interquartile Range*, IQR) adalah selisih antara kuartil ke-75 (Q3) dan kuartil ke-25 (Q1). Fitur ini mengukur sebaran 50% data di bagian tengah distribusi dan sangat robust terhadap outlier karena tidak mempertimbangkan nilai-nilai ekstrem.

**Rumus.**

$$IQR = Q_3 - Q_1$$

**Perhitungan Manual.**

$$IQR = 13{,}25 - 6{,}5 = \mathbf{6{,}75}$$

**Implementasi Python.**

```python
import numpy as np
from scipy.stats import iqr

x = np.array([2, 4, 5, 4, 9, 7, 3, 7, 9, 7, 11, 10, 12, 13, 12, 14, 15, 16, 15, 17])
interq_range = iqr(x)
# atau: np.percentile(x, 75) - np.percentile(x, 25)
print(f"interq_range = {interq_range}")  # Output: 6.75
```

---

### 16. `kurtosis`

**Definisi dan Kegunaan.** `kurtosis` mengukur keruncingan (peakedness) distribusi data relatif terhadap distribusi normal. TSFEL menggunakan *excess kurtosis* (Fisher): nilai 0 berarti normal, nilai negatif berarti distribusi lebih rata (*platikurtik*), dan nilai positif berarti distribusi lebih runcing (*leptokurtik*) dengan ekor lebih panjang. Berguna untuk mendeteksi apakah ada nilai ekstrem yang sering muncul.

**Rumus.**

$$\kappa = \frac{\mu_4}{\sigma^4} - 3, \quad \text{di mana } \mu_4 = \frac{1}{N}\sum_{i=1}^{N}(x_i - \bar{x})^4$$

**Perhitungan Manual.**

$$\mu_4 = \frac{1}{20}\sum (x_i - 9{,}6)^4 = \frac{14741{,}344}{20} = 737{,}067$$

$$\sigma^4 = (4{,}4989)^4 = 409{,}658$$

$$\kappa = \frac{737{,}067}{409{,}658} - 3 = 1{,}799 - 3 = \mathbf{-1{,}2008}$$

Nilai negatif mengindikasikan distribusi data lebih datar dari distribusi normal (platikurtik), artinya data relatif tersebar merata tanpa ada nilai dominan yang sangat ekstrem.

**Implementasi Python.**

```python
import numpy as np
from scipy.stats import kurtosis

x = np.array([2, 4, 5, 4, 9, 7, 3, 7, 9, 7, 11, 10, 12, 13, 12, 14, 15, 16, 15, 17])
kurt = kurtosis(x, fisher=True)   # excess kurtosis
print(f"kurtosis = {kurt:.6f}")   # Output: -1.200773
```

---

### 17. `mean_abs_deviation`

**Definisi dan Kegunaan.** `mean_abs_deviation` (MAD berbasis mean) adalah rata-rata dari nilai absolut simpangan setiap sampel terhadap mean. Berbeda dengan variansi yang mengkuadratkan simpangan, MAD menggunakan nilai absolut sehingga lebih tidak sensitif terhadap outlier ekstrem. Digunakan sebagai alternatif yang lebih robust untuk mengukur dispersi.

**Rumus.**

$$MAD_\mu = \frac{1}{N} \sum_{i=1}^{N} |x_i - \bar{x}|$$

**Perhitungan Manual.**

$$|x_i - 9{,}6| = [7{,}6,\ 5{,}6,\ 4{,}6,\ 5{,}6,\ 0{,}6,\ 2{,}6,\ 6{,}6,\ 2{,}6,\ 0{,}6,\ 2{,}6,\ 1{,}4,\ 0{,}4,\ 2{,}4,\ 3{,}4,\ 2{,}4,\ 4{,}4,\ 5{,}4,\ 6{,}4,\ 5{,}4,\ 7{,}4]$$

$$MAD_\mu = \frac{78{,}0}{20} = \mathbf{3{,}9}$$

**Implementasi Python.**

```python
import numpy as np

x = np.array([2, 4, 5, 4, 9, 7, 3, 7, 9, 7, 11, 10, 12, 13, 12, 14, 15, 16, 15, 17])
mean_abs_dev = np.mean(np.abs(x - np.mean(x)))
print(f"mean_abs_deviation = {mean_abs_dev:.6f}")  # Output: 3.9
```

---

### 18. `median_abs_deviation`

**Definisi dan Kegunaan.** `median_abs_deviation` (MAD berbasis median) adalah median dari nilai absolut simpangan setiap sampel terhadap median sinyal. Fitur ini lebih robust dibandingkan `mean_abs_deviation` karena menggunakan dua kali operasi median, sehingga sangat tahan terhadap outlier. Digunakan ketika data mengandung nilai pencilan yang signifikan.

**Rumus.**

$$MAD_m = \text{median}(|x_i - \tilde{x}|)$$

**Perhitungan Manual.**

Dengan $\tilde{x} = 9{,}5$:

$$|x_i - 9{,}5| = [7{,}5,\ 5{,}5,\ 4{,}5,\ 5{,}5,\ 0{,}5,\ 2{,}5,\ 6{,}5,\ 2{,}5,\ 0{,}5,\ 2{,}5,\ 1{,}5,\ 0{,}5,\ 2{,}5,\ 3{,}5,\ 2{,}5,\ 4{,}5,\ 5{,}5,\ 6{,}5,\ 5{,}5,\ 7{,}5]$$

Data diurutkan: $[0{,}5,\ 0{,}5,\ 0{,}5,\ 1{,}5,\ 2{,}5,\ 2{,}5,\ 2{,}5,\ 2{,}5,\ 2{,}5,\ \mathbf{3{,}5},\ \mathbf{4{,}5},\ 4{,}5,\ 5{,}5,\ 5{,}5,\ 5{,}5,\ 5{,}5,\ 6{,}5,\ 6{,}5,\ 7{,}5,\ 7{,}5]$

Median dari 20 nilai = rata-rata nilai ke-10 dan ke-11: $\frac{3{,}5 + 4{,}5}{2} = \mathbf{4{,}0}$

**Implementasi Python.**

```python
import numpy as np

x = np.array([2, 4, 5, 4, 9, 7, 3, 7, 9, 7, 11, 10, 12, 13, 12, 14, 15, 16, 15, 17])
median_abs_dev = np.median(np.abs(x - np.median(x)))
print(f"median_abs_deviation = {median_abs_dev}")  # Output: 4.0
```

---

### 19. `pk_pk_distance`

**Definisi dan Kegunaan.** `pk_pk_distance` (*peak-to-peak distance*) adalah selisih antara nilai maksimum dan nilai minimum sinyal. Fitur ini mengukur amplitudo total atau jangkauan penuh sinyal, sehingga berguna untuk mengetahui seberapa besar variasi keseluruhan yang terjadi dalam periode pengamatan.

**Rumus.**

$$D_{pk} = x_{\max} - x_{\min}$$

**Perhitungan Manual.**

$$D_{pk} = 17 - 2 = \mathbf{15}$$

**Implementasi Python.**

```python
import numpy as np

x = np.array([2, 4, 5, 4, 9, 7, 3, 7, 9, 7, 11, 10, 12, 13, 12, 14, 15, 16, 15, 17])
pk_pk_distance = np.max(x) - np.min(x)
print(f"pk_pk_distance = {pk_pk_distance}")  # Output: 15
```

---

### 20. `rms`

**Definisi dan Kegunaan.** `rms` (*Root Mean Square*) adalah akar kuadrat dari rata-rata kuadrat seluruh nilai sinyal. Fitur ini mengukur amplitudo efektif atau daya rata-rata sinyal, dengan mempertimbangkan baik besar maupun kontribusi kuadratik setiap sampel. Selalu lebih besar atau sama dengan mean absolut.

**Rumus.**

$$RMS = \sqrt{\frac{1}{N} \sum_{i=1}^{N} x_i^2}$$

**Perhitungan Manual.**

$$RMS = \sqrt{\frac{2248}{20}} = \sqrt{112{,}4} \approx \mathbf{10{,}6019}$$

**Implementasi Python.**

```python
import numpy as np

x = np.array([2, 4, 5, 4, 9, 7, 3, 7, 9, 7, 11, 10, 12, 13, 12, 14, 15, 16, 15, 17])
rms = np.sqrt(np.mean(x ** 2))
print(f"rms = {rms:.6f}")  # Output: 10.601887
```

---

### 21. `skewness`

**Definisi dan Kegunaan.** `skewness` mengukur kemiringan atau asimetri distribusi data. Nilai positif berarti distribusi berekor ke kanan (banyak nilai kecil, sedikit nilai sangat besar); nilai negatif berarti berekor ke kiri (banyak nilai besar, sedikit nilai sangat kecil); nilai mendekati nol berarti distribusi hampir simetris.

**Rumus.**

$$\gamma_1 = \frac{\mu_3}{\sigma^3}, \quad \text{di mana } \mu_3 = \frac{1}{N}\sum_{i=1}^{N}(x_i - \bar{x})^3$$

**Perhitungan Manual.**

$$\mu_3 = \frac{1}{20}\sum (x_i - 9{,}6)^3 = \frac{-90{,}96}{20} = -4{,}548$$

$$\sigma^3 = (4{,}4989)^3 = 91{,}058$$

$$\gamma_1 = \frac{-4{,}548}{91{,}058} \approx \mathbf{-0{,}0499}$$

Nilai hampir nol mengindikasikan distribusi data hampir simetris, dengan ekor sedikit condong ke kiri.

**Implementasi Python.**

```python
import numpy as np
from scipy.stats import skew

x = np.array([2, 4, 5, 4, 9, 7, 3, 7, 9, 7, 11, 10, 12, 13, 12, 14, 15, 16, 15, 17])
skewness = skew(x)
print(f"skewness = {skewness:.6f}")  # Output: -0.049946
```

---

## Domain Temporal (21 Fitur)

Fitur temporal menangkap karakteristik sinyal dalam domain waktu, meliputi pola perubahan antar sampel, korelasi, tren, serta kompleksitas struktural dan fraktal dari deret waktu. Fitur-fitur ini berguna ketika urutan data (siapa yang datang sebelum atau sesudah) menjadi informasi penting yang tidak boleh diabaikan.

---

### 1. `auc`

**Definisi dan Kegunaan.** `auc` (*Area Under the Curve*) adalah luas di bawah kurva sinyal terhadap waktu, dihitung menggunakan aturan trapesoid. Fitur ini merepresentasikan "akumulasi total" nilai sinyal sepanjang periode, berguna untuk mengukur total paparan atau volume suatu fenomena selama rentang waktu tertentu.

**Rumus.**

$$AUC = \sum_{i=1}^{N-1} \frac{x_i + x_{i+1}}{2} \cdot \Delta t$$

**Perhitungan Manual.**

Dengan $\Delta t = 1$, AUC adalah jumlah rata-rata setiap pasangan nilai berurutan:

$$\frac{2+4}{2} + \frac{4+5}{2} + \frac{5+4}{2} + \ldots + \frac{15+17}{2}$$
$$= 3 + 4{,}5 + 4{,}5 + 6{,}5 + 8 + 5 + 5 + 8 + 8 + 9 + 10{,}5 + 11 + 12{,}5 + 12{,}5 + 13 + 14{,}5 + 15{,}5 + 15{,}5 + 16 = \mathbf{182{,}5}$$

**Implementasi Python.**

```python
import numpy as np

x = np.array([2, 4, 5, 4, 9, 7, 3, 7, 9, 7, 11, 10, 12, 13, 12, 14, 15, 16, 15, 17])
t = np.arange(1, len(x) + 1, dtype=float)
auc = np.trapezoid(x, t)
print(f"auc = {auc}")  # Output: 182.5
```

---

### 2. `autocorr`

**Definisi dan Kegunaan.** `autocorr` dalam TSFEL mengacu pada lag optimal dari fungsi autokorelasi, yaitu lag $\tau$ yang memberikan korelasi tertinggi antara sinyal dengan versi gesernya sendiri. Fitur ini menunjukkan periode pengulangan pola dominan dalam sinyal. Semakin tinggi korelasi pada lag tertentu, semakin kuat periodisitas di lag tersebut.

**Rumus.**

$$R(\tau) = \frac{\sum_{i=1}^{N-\tau}(x_i - \bar{x})(x_{i+\tau} - \bar{x})}{\sum_{i=1}^{N}(x_i - \bar{x})^2}, \quad \tau^* = \arg\max_\tau R(\tau)$$

**Perhitungan Manual.**

Korelasi Pearson dihitung untuk setiap lag:

- Lag 1: $r = 0{,}8594$
- Lag 2: $r = 0{,}8277$
- Lag 3: $r = 0{,}8948$ ← tertinggi
- Lag 4: $r = 0{,}7787$
- Lag 5: $r = 0{,}8016$

$$\tau^* = \mathbf{3}, \quad r = \mathbf{0{,}8948}$$

Nilai ini mengindikasikan pola dalam sinyal cenderung berulang setiap 3 periode.

**Implementasi Python.**

```python
import numpy as np

x = np.array([2, 4, 5, 4, 9, 7, 3, 7, 9, 7, 11, 10, 12, 13, 12, 14, 15, 16, 15, 17])
N = len(x)
autocorrs = {lag: np.corrcoef(x[:N-lag], x[lag:])[0, 1] for lag in range(1, N//2 + 1)}
best_lag = max(autocorrs, key=autocorrs.get)
print(f"Best lag = {best_lag}, r = {autocorrs[best_lag]:.6f}")  # Output: lag=3, r=0.894762
```

---

### 3. `calc_centroid`

**Definisi dan Kegunaan.** `calc_centroid` adalah centroid temporal, yaitu titik waktu "pusat massa" sinyal, dihitung sebagai rata-rata waktu yang dibobot oleh nilai absolut sinyal. Fitur ini menunjukkan di mana energi sinyal paling terpusat secara temporal. Nilai centroid yang besar menunjukkan energi dominan berada di akhir periode.

**Rumus.**

$$C_t = \frac{\sum_{i=1}^{N} t_i \cdot |x_i|}{\sum_{i=1}^{N} |x_i|}$$

**Perhitungan Manual.**

$$\sum t_i \cdot |x_i| = 1{\cdot}2 + 2{\cdot}4 + 3{\cdot}5 + \ldots + 20{\cdot}17 = 2498$$

$$\sum |x_i| = 2 + 4 + 5 + \ldots + 17 = 192$$

$$C_t = \frac{2498}{192} \approx \mathbf{13{,}0573}$$

Centroid berada di periode 13, menunjukkan bobot energi lebih banyak berada di paruh kedua (nilai-nilai lebih tinggi terjadi di akhir periode).

**Implementasi Python.**

```python
import numpy as np

x = np.array([2, 4, 5, 4, 9, 7, 3, 7, 9, 7, 11, 10, 12, 13, 12, 14, 15, 16, 15, 17])
t = np.arange(1, len(x) + 1, dtype=float)
centroid = np.sum(t * np.abs(x)) / np.sum(np.abs(x))
print(f"calc_centroid = {centroid:.6f}")  # Output: 13.057292
```

---

### 4. `distance`

**Definisi dan Kegunaan.** `distance` mengukur total panjang kurva sinyal dalam ruang waktu-nilai, yaitu total jarak Euclidean yang "ditempuh" sinyal dari satu titik ke titik berikutnya. Fitur ini menangkap seberapa berkelok atau aktif lintasan sinyal, berbeda dengan `sum_abs_diff` yang hanya memperhitungkan arah vertikal.

**Rumus.**

$$D = \sum_{i=1}^{N-1} \sqrt{(\Delta t)^2 + (x_{i+1} - x_i)^2}$$

**Perhitungan Manual.**

Dengan $\Delta t = 1$, selisih berurutan $\Delta x = [2, 1, -1, 5, -2, -4, 4, 2, -2, 4, -1, 2, 1, -1, 2, 1, 1, -1, 2]$:

$$D = \sqrt{1+4} + \sqrt{1+1} + \sqrt{1+1} + \sqrt{1+25} + \ldots$$
$$= 2{,}236 + 1{,}414 + 1{,}414 + 5{,}099 + 2{,}236 + 4{,}123 + 4{,}123 + 2{,}236 + 2{,}236 + 4{,}123 + 1{,}414 + 2{,}236 + 1{,}414 + 1{,}414 + 2{,}236 + 1{,}414 + 1{,}414 + 1{,}414 + 2{,}236 \approx \mathbf{44{,}435}$$

**Implementasi Python.**

```python
import numpy as np

x = np.array([2, 4, 5, 4, 9, 7, 3, 7, 9, 7, 11, 10, 12, 13, 12, 14, 15, 16, 15, 17])
distance = np.sum(np.sqrt(1 + np.diff(x) ** 2))
print(f"distance = {distance:.6f}")  # Output: 44.434521
```

---

### 5. `mean_abs_diff`

**Definisi dan Kegunaan.** `mean_abs_diff` adalah rata-rata dari nilai absolut selisih antar sampel berurutan. Fitur ini mengukur rata-rata laju perubahan sinyal per langkah waktu, tanpa memperhatikan arah perubahan. Semakin besar nilainya, semakin berfluktuasi sinyal dari satu periode ke periode berikutnya.

**Rumus.**

$$\overline{|\Delta x|} = \frac{1}{N-1} \sum_{i=1}^{N-1} |x_{i+1} - x_i|$$

**Perhitungan Manual.**

$$|\Delta x| = [2, 1, 1, 5, 2, 4, 4, 2, 2, 4, 1, 2, 1, 1, 2, 1, 1, 1, 2]$$

$$\overline{|\Delta x|} = \frac{39}{19} \approx \mathbf{2{,}0526}$$

**Implementasi Python.**

```python
import numpy as np

x = np.array([2, 4, 5, 4, 9, 7, 3, 7, 9, 7, 11, 10, 12, 13, 12, 14, 15, 16, 15, 17])
mean_abs_diff = np.mean(np.abs(np.diff(x)))
print(f"mean_abs_diff = {mean_abs_diff:.6f}")  # Output: 2.052632
```

---

### 6. `mean_diff`

**Definisi dan Kegunaan.** `mean_diff` adalah rata-rata dari selisih antar sampel berurutan dengan mempertahankan tanda positif/negatif. Fitur ini mencerminkan tren naik atau turun secara global dalam sinyal. Nilai positif berarti rata-rata sinyal naik, nilai negatif berarti turun.

**Rumus.**

$$\overline{\Delta x} = \frac{1}{N-1} \sum_{i=1}^{N-1} (x_{i+1} - x_i)$$

**Perhitungan Manual.**

$$\Delta x = [2, 1, -1, 5, -2, -4, 4, 2, -2, 4, -1, 2, 1, -1, 2, 1, 1, -1, 2]$$

$$\overline{\Delta x} = \frac{15}{19} \approx \mathbf{0{,}7895}$$

Nilai positif mengkonfirmasi sinyal secara rata-rata naik sekitar 0,79 unit per periode.

**Implementasi Python.**

```python
import numpy as np

x = np.array([2, 4, 5, 4, 9, 7, 3, 7, 9, 7, 11, 10, 12, 13, 12, 14, 15, 16, 15, 17])
mean_diff = np.mean(np.diff(x))
print(f"mean_diff = {mean_diff:.6f}")  # Output: 0.789474
```

---

### 7. `median_abs_diff`

**Definisi dan Kegunaan.** `median_abs_diff` adalah median dari nilai absolut selisih antar sampel berurutan. Fitur ini lebih robust dari `mean_abs_diff` terhadap perubahan-perubahan ekstrem yang tiba-tiba (spike), karena menggunakan median bukan mean. Berguna ketika sinyal mengandung lonjakan mendadak yang tidak mewakili pola umum.

**Rumus.**

$$\text{median\_abs\_diff} = \text{median}(|x_{i+1} - x_i|)$$

**Perhitungan Manual.**

$$|\Delta x| \text{ diurutkan} = [1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 4, 4, 4, 5]$$

Median dari 19 nilai = nilai ke-10:

$$\text{median\_abs\_diff} = \mathbf{2{,}0}$$

**Implementasi Python.**

```python
import numpy as np

x = np.array([2, 4, 5, 4, 9, 7, 3, 7, 9, 7, 11, 10, 12, 13, 12, 14, 15, 16, 15, 17])
median_abs_diff = np.median(np.abs(np.diff(x)))
print(f"median_abs_diff = {median_abs_diff}")  # Output: 2.0
```

---

### 8. `median_diff`

**Definisi dan Kegunaan.** `median_diff` adalah median dari selisih antar sampel berurutan (dengan tanda). Fitur ini memberikan estimasi tren yang lebih robust dibandingkan `mean_diff` karena tidak terpengaruh oleh lonjakan atau penurunan tiba-tiba yang bersifat outlier. Nilai positif tetap mengindikasikan tren naik dominan.

**Rumus.**

$$\text{median\_diff} = \text{median}(x_{i+1} - x_i)$$

**Perhitungan Manual.**

$$\Delta x \text{ diurutkan} = [-4, -2, -2, -1, -1, -1, -1, 1, 1, \mathbf{1}, \mathbf{1}, 2, 2, 2, 2, 2, 4, 4, 5]$$

Median dari 19 nilai = nilai ke-10:

$$\text{median\_diff} = \mathbf{1{,}0}$$

**Implementasi Python.**

```python
import numpy as np

x = np.array([2, 4, 5, 4, 9, 7, 3, 7, 9, 7, 11, 10, 12, 13, 12, 14, 15, 16, 15, 17])
median_diff = np.median(np.diff(x))
print(f"median_diff = {median_diff}")  # Output: 1.0
```

---

### 9. `negative_turning`

**Definisi dan Kegunaan.** `negative_turning` menghitung jumlah titik balik negatif, yaitu titik di mana sinyal mencapai puncak lokal (nilai naik lalu turun). Fitur ini mengukur frekuensi terjadinya penurunan setelah kenaikan dalam sinyal. Semakin banyak titik balik negatif, semakin sering sinyal berosilasi.

**Rumus.**

$$\sum_{i=2}^{N-1} \mathbf{1}[x_{i-1} < x_i \text{ dan } x_i > x_{i+1}]$$

**Perhitungan Manual.**

Periksa setiap titik interior:

- t=3: $4 < 5 > 4$ ✓ (puncak lokal)
- t=5: $4 < 9 > 7$ ✓
- t=9: $7 < 9 > 7$ ✓
- t=11: $7 < 11 > 10$ ✓
- t=14: $12 < 13 > 12$ ✓
- t=18: $15 < 16 > 15$ ✓

$$\text{negative\_turning} = \mathbf{6}$$

**Implementasi Python.**

```python
import numpy as np

x = np.array([2, 4, 5, 4, 9, 7, 3, 7, 9, 7, 11, 10, 12, 13, 12, 14, 15, 16, 15, 17])
neg_turn = sum(1 for i in range(1, len(x)-1) if x[i-1] < x[i] > x[i+1])
print(f"negative_turning = {neg_turn}")  # Output: 6
```

---

### 10. `neighbourhood_peaks`

**Definisi dan Kegunaan.** `neighbourhood_peaks` menghitung jumlah puncak lokal yang terdeteksi dengan mempertimbangkan jarak minimum antar puncak (neighborhood). Berbeda dengan `negative_turning` yang hanya melihat tiga titik berturut-turut, fitur ini mensyaratkan bahwa sebuah puncak harus lebih tinggi dari semua nilai dalam jangkauan $n$ di kiri dan kanannya, sehingga hanya puncak yang benar-benar signifikan yang terhitung.

**Rumus.**

$x_i$ adalah puncak jika $x_i > x_j \; \forall j \in [i-n, i+n],\ j \neq i$, dengan $n = 5$ (default TSFEL).

**Perhitungan Manual.**

Dengan `distance=5`, hanya puncak yang berjarak minimal 5 dari puncak lain yang dihitung:

- Puncak di t=5 (nilai 9): dominan dalam jangkauan [1..10]
- Puncak di t=11 (nilai 11): dominan dalam jangkauan [6..16]  
- Puncak di t=18 (nilai 16): dominan dalam jangkauan [13..20]

$$\text{neighbourhood\_peaks} = \mathbf{3}$$

**Implementasi Python.**

```python
import numpy as np
from scipy.signal import find_peaks

x = np.array([2, 4, 5, 4, 9, 7, 3, 7, 9, 7, 11, 10, 12, 13, 12, 14, 15, 16, 15, 17])
peaks, _ = find_peaks(x, distance=5)
print(f"neighbourhood_peaks = {len(peaks)}")  # Output: 3
print(f"Peak positions (1-based): {peaks + 1}")  # Output: [5, 11, 18]
```

---

### 11. `positive_turning`

**Definisi dan Kegunaan.** `positive_turning` menghitung jumlah titik balik positif, yaitu titik lembah lokal (sinyal turun lalu naik). Fitur ini mengukur frekuensi pemulihan atau kenaikan setelah penurunan dalam sinyal. Nilai yang tinggi mengindikasikan sinyal sering berbalik arah ke atas, menandakan osilasi yang aktif.

**Rumus.**

$$\sum_{i=2}^{N-1} \mathbf{1}[x_{i-1} > x_i \text{ dan } x_i < x_{i+1}]$$

**Perhitungan Manual.**

Periksa setiap titik interior:

- t=4: $5 > 4 < 9$ ✓ (lembah lokal)
- t=7: $7 > 3 < 7$ ✓
- t=10: $9 > 7 < 11$ ✓
- t=12: $11 > 10 < 12$ ✓
- t=15: $13 > 12 < 14$ ✓
- t=19: $16 > 15 < 17$ ✓

$$\text{positive\_turning} = \mathbf{6}$$

**Implementasi Python.**

```python
import numpy as np

x = np.array([2, 4, 5, 4, 9, 7, 3, 7, 9, 7, 11, 10, 12, 13, 12, 14, 15, 16, 15, 17])
pos_turn = sum(1 for i in range(1, len(x)-1) if x[i-1] > x[i] < x[i+1])
print(f"positive_turning = {pos_turn}")  # Output: 6
```

---

### 12. `slope`

**Definisi dan Kegunaan.** `slope` adalah kemiringan dari garis regresi linear yang di-fitting pada deret waktu terhadap indeks waktu. Fitur ini mengukur tren jangka panjang sinyal secara keseluruhan. Nilai positif berarti sinyal cenderung naik; nilai negatif berarti cenderung turun; nilai mendekati nol berarti stasioner.

**Rumus.**

$$\beta = \frac{\sum_{i=1}^{N}(t_i - \bar{t})(x_i - \bar{x})}{\sum_{i=1}^{N}(t_i - \bar{t})^2}$$

**Perhitungan Manual.**

Dengan $\bar{t} = 10{,}5$ dan $\bar{x} = 9{,}6$:

$$\sum (t_i - \bar{t})(x_i - \bar{x}) = 491{,}0$$

$$\sum (t_i - \bar{t})^2 = 665{,}0$$

$$\beta = \frac{491{,}0}{665{,}0} \approx \mathbf{0{,}7383}$$

Intercept: $\alpha = \bar{x} - \beta \cdot \bar{t} = 9{,}6 - 0{,}7383 \times 10{,}5 \approx 1{,}847$.

Artinya rata-rata sinyal naik sekitar 0,74 unit per periode.

**Implementasi Python.**

```python
import numpy as np
from scipy.stats import linregress

x = np.array([2, 4, 5, 4, 9, 7, 3, 7, 9, 7, 11, 10, 12, 13, 12, 14, 15, 16, 15, 17])
t = np.arange(1, len(x) + 1, dtype=float)
slope, intercept, *_ = linregress(t, x)
print(f"slope = {slope:.6f}")      # Output: 0.738346
print(f"intercept = {intercept:.6f}")  # Output: 1.847368
```

---

### 13. `sum_abs_diff`

**Definisi dan Kegunaan.** `sum_abs_diff` adalah jumlah total dari nilai absolut selisih antar sampel berurutan, juga dikenal sebagai *total variation* sinyal. Fitur ini mengukur total "jarak vertikal" yang ditempuh sinyal sepanjang waktu. Nilai besar berarti sinyal sangat aktif dan sering berubah; nilai kecil berarti sinyal relatif halus.

**Rumus.**

$$TV = \sum_{i=1}^{N-1} |x_{i+1} - x_i|$$

**Perhitungan Manual.**

$$|\Delta x| = [2, 1, 1, 5, 2, 4, 4, 2, 2, 4, 1, 2, 1, 1, 2, 1, 1, 1, 2]$$

$$TV = 2+1+1+5+2+4+4+2+2+4+1+2+1+1+2+1+1+1+2 = \mathbf{39}$$

**Implementasi Python.**

```python
import numpy as np

x = np.array([2, 4, 5, 4, 9, 7, 3, 7, 9, 7, 11, 10, 12, 13, 12, 14, 15, 16, 15, 17])
sum_abs_diff = np.sum(np.abs(np.diff(x)))
print(f"sum_abs_diff = {sum_abs_diff}")  # Output: 39.0
```

---

### 14. `zero_cross`

**Definisi dan Kegunaan.** `zero_cross` menghitung berapa kali sinyal yang telah digeser terhadap mean-nya melewati nilai nol (berpindah tanda dari positif ke negatif atau sebaliknya). Fitur ini mengukur frekuensi osilasi sinyal terhadap nilai rata-ratanya. Banyak persilangan nol mengindikasikan sinyal sering berosilasi di sekitar mean; sedikit persilangan mengindikasikan tren satu arah.

**Rumus.**

$$ZC = \sum_{i=1}^{N-1} \mathbf{1}[\text{sign}(x_i - \bar{x}) \neq \text{sign}(x_{i+1} - \bar{x})]$$

**Perhitungan Manual.**

Sinyal digeser: $x_i - 9{,}6$:

$$[-7{,}6,\ -5{,}6,\ -4{,}6,\ -5{,}6,\ -0{,}6,\ -2{,}6,\ -6{,}6,\ -2{,}6,\ -0{,}6,\ -2{,}6,\ 1{,}4,\ 0{,}4,\ 2{,}4,\ 3{,}4,\ 2{,}4,\ 4{,}4,\ 5{,}4,\ 6{,}4,\ 5{,}4,\ 7{,}4]$$

Tanda: $[-,-,-,-,-,-,-,-,-,-,+,+,+,+,+,+,+,+,+,+]$

Perubahan tanda terjadi hanya 1 kali, yaitu antara t=10 (negatif) dan t=11 (positif):

$$ZC = \mathbf{1}$$

Hal ini konsisten dengan tren monoton naik: sinyal berada di bawah mean selama 10 periode pertama, kemudian di atas mean selama 10 periode terakhir.

**Implementasi Python.**

```python
import numpy as np

x = np.array([2, 4, 5, 4, 9, 7, 3, 7, 9, 7, 11, 10, 12, 13, 12, 14, 15, 16, 15, 17])
x_centered = x - np.mean(x)
zero_cross = np.sum(np.diff(np.sign(x_centered)) != 0)
print(f"zero_cross = {zero_cross}")  # Output: 1
```

---

### 15. `dfa`

**Definisi dan Kegunaan.** `dfa` (*Detrended Fluctuation Analysis*) mengukur korelasi jangka panjang dalam sinyal melalui eksponen skala $\alpha$. Sinyal dibagi menjadi segmen-segmen, setiap segmen di-detrend (dihilangkan tren linearnya), lalu fluktuasi RMS dihitung. Nilai $\alpha \approx 0{,}5$ menandakan sinyal acak (tidak berkorelasi), $\alpha > 0{,}5$ menandakan korelasi persisten (tren kuat), dan $\alpha < 0{,}5$ menandakan anti-korelasi.

**Rumus.**

$$F(n) \sim n^\alpha \implies \alpha = \text{slope regresi } \log F(n) \text{ terhadap } \log n$$

**Perhitungan Manual.**

Cumulative sum dari sinyal ter-detrend dihitung, lalu dibagi menjadi segmen dengan skala $n \in \{4, 5, 6, 8, 10\}$:

| $n$ | $F(n)$ |
|-----|--------|
| 4   | 0,578  |
| 5   | 0,991  |
| 6   | 1,316  |
| 8   | 1,715  |
| 10  | 2,255  |

Dari regresi $\log F(n)$ terhadap $\log n$:

$$\alpha \approx \mathbf{1{,}407}$$

Nilai $\alpha > 1$ mengindikasikan sinyal memiliki korelasi jangka panjang yang sangat kuat, konsisten dengan tren naik yang dominan.

**Implementasi Python.**

```python
import numpy as np
from scipy.stats import linregress

def dfa(ts, scales=[4, 5, 6, 8, 10]):
    ts = np.array(ts, dtype=float)
    N = len(ts)
    cumsum = np.cumsum(ts - np.mean(ts))
    flucts = []
    used_scales = []
    for n in scales:
        segs = N // n
        if segs < 2:
            continue
        rms_list = []
        for seg in range(segs):
            chunk = cumsum[seg*n:(seg+1)*n]
            tc = np.arange(len(chunk), dtype=float)
            sl, ic, *_ = linregress(tc, chunk)
            rms_list.append(np.sqrt(np.mean((chunk - (sl*tc + ic))**2)))
        flucts.append(np.mean(rms_list))
        used_scales.append(n)
    alpha, *_ = linregress(np.log(used_scales), np.log(flucts))
    return alpha

x = [2, 4, 5, 4, 9, 7, 3, 7, 9, 7, 11, 10, 12, 13, 12, 14, 15, 16, 15, 17]
print(f"DFA alpha = {dfa(x):.6f}")  # Output: ~1.407346
```

---

### 16. `higuchi_fractal_dimension`

**Definisi dan Kegunaan.** `higuchi_fractal_dimension` (HFD) mengukur dimensi fraktal sinyal menggunakan metode Higuchi, yang mengestimasi kompleksitas atau "kekasaran" kurva sinyal. Nilai mendekati 1 berarti sinyal sangat halus (seperti garis lurus), sedangkan nilai mendekati 2 berarti sinyal sangat kompleks dan acak (seperti noise putih). Berguna untuk membedakan sinyal deterministik dari sinyal stokastik.

**Rumus.**

$$L_m(k) = \frac{N-1}{\lfloor(N-m)/k\rfloor \cdot k^2} \sum_{i=1}^{\lfloor(N-m)/k\rfloor} |x_{m+ik} - x_{m+(i-1)k}|, \quad L(k) \sim k^{-D}$$

**Perhitungan Manual.**

Dihitung untuk $k = 1, 2, 3, 4, 5$:

| $k$ | $L(k)$ |
|-----|--------|
| 1   | 39,000 |
| 2   | 10,028 |
| 3   | 5,301  |
| 4   | 3,859  |
| 5   | 2,989  |

Dari regresi $\log L(k)$ terhadap $\log k$, kemiringan = $-D$:

$$HFD = D \approx \mathbf{1{,}6026}$$

Nilai ini menunjukkan sinyal cukup kompleks dan irregular, berada di antara tren halus dan noise acak.

**Implementasi Python.**

```python
import numpy as np
from scipy.stats import linregress

def higuchi_fd(ts, kmax=5):
    ts = np.array(ts, dtype=float)
    N = len(ts)
    Lk = []
    for k in range(1, kmax + 1):
        Lm_list = []
        for m in range(1, k + 1):
            idxs = np.arange(m - 1, N, k)
            if len(idxs) < 2:
                continue
            Lmk = ((N-1) / (np.floor((N-m)/k) * k**2)) * np.sum(np.abs(np.diff(ts[idxs])))
            Lm_list.append(Lmk)
        if Lm_list:
            Lk.append(np.mean(Lm_list))
    k_vals = np.arange(1, len(Lk) + 1, dtype=float)
    slope, *_ = linregress(np.log(k_vals), np.log(Lk))
    return -slope

x = [2, 4, 5, 4, 9, 7, 3, 7, 9, 7, 11, 10, 12, 13, 12, 14, 15, 16, 15, 17]
print(f"Higuchi FD = {higuchi_fd(x):.6f}")  # Output: ~1.602556
```

---

### 17. `hurst_exponent`

**Definisi dan Kegunaan.** `hurst_exponent` (H) mengukur memori jangka panjang atau persistensi sinyal menggunakan analisis R/S (*Rescaled Range*). Nilai $H > 0{,}5$ menandakan sinyal persisten (tren cenderung berlanjut), $H < 0{,}5$ menandakan anti-persisten (sinyal cenderung berbalik), dan $H = 0{,}5$ menandakan gerak Brown (acak sempurna).

**Rumus.**

$$E\left[\frac{R(n)}{S(n)}\right] = C \cdot n^H \implies H = \text{slope regresi } \log(R/S) \text{ terhadap } \log n$$

**Perhitungan Manual.**

Contoh untuk lag $n=4$ ($x = [2, 4, 5, 4]$):

- Cumulative deviation dari mean: $[-1{,}75, 0{,}25, 1{,}25, 0{,}25]$
- $R = \max - \min = 1{,}25 - (-1{,}75) = 3{,}00$... sebenarnya $R = 1{,}75$, $S = 1{,}258$
- $R/S = 1{,}3908$

Setelah regresi log-log untuk berbagai lag:

$$H \approx \mathbf{0{,}8503}$$

Nilai $H > 0{,}5$ sangat kuat mengkonfirmasi sinyal memiliki tren persisten yang kuat (naik terus), konsisten dengan tren linear yang terlihat dalam data.

**Implementasi Python.**

```python
import numpy as np
from scipy.stats import linregress

def hurst(ts):
    ts = np.array(ts, dtype=float)
    N = len(ts)
    RS_vals, n_vals = [], []
    for lag in range(4, N//2 + 1, 2):
        sub = ts[:lag]
        dev = np.cumsum(sub - np.mean(sub))
        R = np.max(dev) - np.min(dev)
        S = np.std(sub, ddof=1)
        if S > 0:
            RS_vals.append(R / S)
            n_vals.append(lag)
    slope, *_ = linregress(np.log(n_vals), np.log(RS_vals))
    return slope

x = [2, 4, 5, 4, 9, 7, 3, 7, 9, 7, 11, 10, 12, 13, 12, 14, 15, 16, 15, 17]
print(f"Hurst exponent = {hurst(x):.6f}")  # Output: ~0.850311
```

---

### 18. `lempel_ziv`

**Definisi dan Kegunaan.** `lempel_ziv` mengukur kompleksitas sinyal menggunakan algoritma kompresi Lempel-Ziv. Sinyal pertama-tama diubah menjadi representasi biner (di atas atau di bawah median), kemudian kompleksitas diukur dari berapa banyak sub-pola baru yang muncul. Nilai tinggi berarti sinyal lebih acak dan tidak berulang; nilai rendah berarti sinyal repetitif dan mudah dikompres.

**Rumus.**

$$C_{LZ} = \frac{c(n)}{n / \log_2 n}$$

**Perhitungan Manual.**

Dengan median $= 9{,}5$, konversi ke biner: nilai $\geq 9{,}5$ menjadi `1`, lainnya menjadi `0`:

$$\text{biner} = 00000000001111111111$$

Hitung $c(n)$ = jumlah sub-string unik baru yang ditambahkan selama parsing sequential: $c(n) = 7$.

$$\frac{n}{\log_2 n} = \frac{20}{\log_2 20} = \frac{20}{4{,}322} = 4{,}628$$

$$C_{LZ} = \frac{7}{4{,}628} \approx \mathbf{1{,}5127}$$

Nilai di atas 1 mengindikasikan sinyal memiliki kompleksitas moderat; representasi biner yang sangat terstruktur (sepuluh 0 diikuti sepuluh 1) menyebabkan kompleksitas tidak terlalu tinggi meski ada banyak sub-pola.

**Implementasi Python.**

```python
import numpy as np

def lempel_ziv(ts):
    med = np.median(ts)
    binary = ''.join(['1' if v >= med else '0' for v in ts])
    n = len(binary)
    i, c, l = 0, 1, 1
    while i + l <= n:
        if binary[i:i+l] in binary[:i]:
            l += 1
        else:
            c += 1
            i += l
            l = 1
    return c / (n / np.log2(n)), binary

x = [2, 4, 5, 4, 9, 7, 3, 7, 9, 7, 11, 10, 12, 13, 12, 14, 15, 16, 15, 17]
lz, binary = lempel_ziv(x)
print(f"Lempel-Ziv = {lz:.6f}")   # Output: ~1.512675
print(f"Binary: {binary}")         # Output: 00000000001111111111
```

---

### 19. `maximum_fractal_length`

**Definisi dan Kegunaan.** `maximum_fractal_length` (MFL) adalah logaritma dari panjang fraktal sinyal pada skala terkecil, yang terkait dengan energi perubahan sinyal. Fitur ini mengukur kompleksitas geometri kurva sinyal berdasarkan rata-rata kuadrat selisih antar sampel. Nilai yang lebih besar mengindikasikan perubahan antar sampel yang lebih besar secara rata-rata.

**Rumus.**

$$MFL = \log\!\left(\sqrt{\frac{1}{N-1}\sum_{i=1}^{N-1}(x_{i+1} - x_i)^2}\right)$$

**Perhitungan Manual.**

$$(\Delta x)^2 = [4, 1, 1, 25, 4, 16, 16, 4, 4, 16, 1, 4, 1, 1, 4, 1, 1, 1, 4]$$

$$\sum = 109, \quad \frac{109}{19} \approx 5{,}7368, \quad \sqrt{5{,}7368} \approx 2{,}3952$$

$$MFL = \ln(2{,}3952) \approx \mathbf{0{,}8735}$$

**Implementasi Python.**

```python
import numpy as np

x = np.array([2, 4, 5, 4, 9, 7, 3, 7, 9, 7, 11, 10, 12, 13, 12, 14, 15, 16, 15, 17])
mfl = np.log(np.sqrt(np.mean(np.diff(x) ** 2)))
print(f"maximum_fractal_length = {mfl:.6f}")  # Output: 0.873454
```

---

### 20. `mse`

**Definisi dan Kegunaan.** `mse` (*Multiscale Entropy*) mengukur kompleksitas sinyal pada berbagai skala temporal menggunakan *Sample Entropy* (SampEn). Pada setiap skala $\tau$, sinyal terlebih dahulu di-*coarse-grain* (dirata-ratakan per blok), kemudian SampEn dihitung. Nilai MSE yang tinggi di berbagai skala menunjukkan dinamika yang kaya dan tidak tereduksi, sedangkan nilai rendah mengindikasikan sinyal yang terlalu reguler atau acak.

**Rumus.**

$$y_j^{(\tau)} = \frac{1}{\tau} \sum_{i=(j-1)\tau+1}^{j\tau} x_i, \quad SampEn(m, r, N) = -\ln\frac{A}{B}$$

**Perhitungan Manual.**

Untuk $\tau=2$, sinyal di-*coarse-grain*:

$$y^{(2)} = [3{,}0,\ 4{,}5,\ 8{,}0,\ 5{,}0,\ 8{,}0,\ 10{,}5,\ 12{,}5,\ 13{,}0,\ 15{,}5,\ 16{,}0]$$

SampEn dengan $m=2$, $r=0{,}2\sigma$ dihitung pada sinyal asli (skala 1) dan coarse-grain (skala 2). Pada data ini yang memiliki tren kuat, pola sangat berulang sehingga hampir semua template match, menghasilkan nilai SampEn mendekati 0 yang menunjukkan regularitas tinggi.

**Implementasi Python.**

```python
import numpy as np

def sample_entropy(ts, m=2, r_factor=0.2):
    ts = np.array(ts, dtype=float)
    r = r_factor * np.std(ts, ddof=1)
    N = len(ts)
    def count_m(m):
        return sum(1 for i in range(N-m) for j in range(N-m)
                   if i != j and np.max(np.abs(ts[j:j+m] - ts[i:i+m])) < r)
    A, B = count_m(m+1), count_m(m)
    return -np.log(A/B) if A > 0 and B > 0 else 0

x = [2, 4, 5, 4, 9, 7, 3, 7, 9, 7, 11, 10, 12, 13, 12, 14, 15, 16, 15, 17]
# Scale 1
se1 = sample_entropy(x)
# Scale 2 (coarse-grain)
cg2 = [(x[2*i] + x[2*i+1]) / 2 for i in range(len(x) // 2)]
se2 = sample_entropy(cg2)
print(f"MSE tau=1: {se1:.4f}, tau=2: {se2:.4f}")
```

---

### 21. `petrosian_fractal_dimension`

**Definisi dan Kegunaan.** `petrosian_fractal_dimension` (PFD) adalah estimasi cepat dimensi fraktal sinyal berdasarkan jumlah perubahan tanda pada turunan pertamanya. Tidak seperti Higuchi yang membutuhkan iterasi pada berbagai skala, Petrosian hanya memerlukan satu perhitungan sehingga sangat efisien secara komputasi. Berguna ketika kecepatan komputasi lebih diutamakan daripada presisi estimasi fraktal.

**Rumus.**

$$PFD = \frac{\log_{10}(N)}{\log_{10}(N) + \log_{10}\!\left(\dfrac{N}{N + 0{,}4 \cdot N_\delta}\right)}$$

**Perhitungan Manual.**

Hitung $\Delta x$ dan perubahan tanda-nya:

$$\text{sign}(\Delta x) = [+,+,-,+,-,-,+,+,-,+,-,+,+,-,+,+,+,-,+]$$

Perubahan tanda terjadi di posisi: $[3, 4, 5, 7, 9, 10, 11, 12, 14, 15, 18, 19]$ → $N_\delta = 12$.

$$PFD = \frac{\log_{10}(20)}{\log_{10}(20) + \log_{10}\!\left(\dfrac{20}{20 + 0{,}4 \times 12}\right)} = \frac{1{,}3010}{1{,}3010 + \log_{10}\!\left(\dfrac{20}{24{,}8}\right)}$$

$$= \frac{1{,}3010}{1{,}3010 + \log_{10}(0{,}8065)} = \frac{1{,}3010}{1{,}3010 - 0{,}0934} \approx \mathbf{1{,}0774}$$

**Implementasi Python.**

```python
import numpy as np

x = np.array([2, 4, 5, 4, 9, 7, 3, 7, 9, 7, 11, 10, 12, 13, 12, 14, 15, 16, 15, 17])
N = len(x)
delta_x = np.diff(x)
N_delta = np.sum(np.diff(np.sign(delta_x)) != 0)
pfd = np.log10(N) / (np.log10(N) + np.log10(N / (N + 0.4 * N_delta)))
print(f"Petrosian FD = {pfd:.6f}")  # Output: 1.077361
```

---

## Domain Spectral (26 Fitur)

Fitur spektral diperoleh melalui transformasi sinyal ke domain frekuensi menggunakan Fast Fourier Transform (FFT) atau dekomposisi wavelet. Fitur-fitur ini menangkap kandungan frekuensi, distribusi daya, dan karakteristik osilasi yang tidak terlihat secara langsung di domain waktu. Pada data ini dengan $N=20$ dan $f_s = 1$ sampel/periode, frekuensi yang tersedia berkisar dari $0$ hingga $0{,}5$ dengan resolusi $\Delta f = 0{,}05$.

---

### 1. `fundamental_frequency`

**Definisi dan Kegunaan.** `fundamental_frequency` adalah frekuensi komponen dengan daya spektral tertinggi dalam Power Spectral Density (PSD). Fitur ini mengidentifikasi periodisitas dominan sinyal. Untuk sinyal dengan tren kuat, komponen DC (frekuensi 0) biasanya mendominasi.

**Rumus.**

$$f_0 = \arg\max_f |X(f)|^2$$

**Perhitungan Manual.**

Dari FFT data, daya terbesar berada di frekuensi $f = 0$ (komponen DC) dengan $|X(0)|^2 = 192^2 = 36864$:

$$f_0 = \mathbf{0{,}0 \text{ Hz}}$$

**Implementasi Python.**

```python
import numpy as np

x = np.array([2, 4, 5, 4, 9, 7, 3, 7, 9, 7, 11, 10, 12, 13, 12, 14, 15, 16, 15, 17])
X = np.fft.rfft(x)
freqs = np.fft.rfftfreq(len(x), d=1.0)
P = np.abs(X) ** 2
fundamental_frequency = freqs[np.argmax(P)]
print(f"fundamental_frequency = {fundamental_frequency} Hz")  # Output: 0.0
```

---

### 2. `human_range_energy`

**Definisi dan Kegunaan.** `human_range_energy` mengukur total energi spektral dalam rentang frekuensi 0,6–2,5 Hz, yang merupakan rentang persepsi manusia untuk sinyal audio dan getaran. Untuk data time series non-audio (seperti data harian atau periodik), nilai ini umumnya nol karena frekuensi sinyal berada di luar rentang tersebut.

**Rumus.**

$$E_{hr} = \sum_{f \in [0{,}6,\ 2{,}5]} |X(f)|^2$$

**Perhitungan Manual.**

Frekuensi yang tersedia: $[0; 0{,}05; 0{,}10; \ldots; 0{,}50]$. Tidak ada frekuensi dalam rentang $[0{,}6; 2{,}5]$:

$$E_{hr} = \mathbf{0}$$

**Implementasi Python.**

```python
import numpy as np

x = np.array([2, 4, 5, 4, 9, 7, 3, 7, 9, 7, 11, 10, 12, 13, 12, 14, 15, 16, 15, 17])
X = np.fft.rfft(x)
freqs = np.fft.rfftfreq(len(x), d=1.0)
P = np.abs(X) ** 2
mask = (freqs >= 0.6) & (freqs <= 2.5)
human_range_energy = np.sum(P[mask])
print(f"human_range_energy = {human_range_energy}")  # Output: 0.0
```

---

### 3. `lpcc`

**Definisi dan Kegunaan.** `lpcc` (*Linear Prediction Cepstral Coefficients*) adalah koefisien cepstral yang diturunkan dari model Linear Predictive Coding (LPC). Koefisien ini menangkap "amplop spektral" sinyal, yaitu karakteristik spektrum yang berubah secara lambat. Awalnya dikembangkan untuk pemrosesan suara, fitur ini juga berguna untuk menangkap pola umum distribusi frekuensi dalam time series.

**Rumus.**

Dari koefisien LP $a_k$ (diperoleh lewat Levinson-Durbin):

$$c_n = -a_n - \sum_{k=1}^{n-1} \frac{k}{n} c_k \cdot a_{n-k}$$

**Perhitungan Manual.**

Dengan model LP orde 4 pada data ini:

$$LPCC = [-0{,}8038,\ 0{,}5082,\ -0{,}4467,\ 0{,}4620]$$

**Implementasi Python.**

```python
import numpy as np
from scipy.signal import lfilter

def compute_lpcc(ts, n_lpcc=4):
    ts = np.array(ts, dtype=float)
    # Autokorelasi
    r = np.array([np.dot(ts[:len(ts)-k], ts[k:]) for k in range(n_lpcc+1)])
    # Levinson-Durbin
    a = np.zeros(n_lpcc+1)
    e = r[0]
    for i in range(1, n_lpcc+1):
        lam = r[i] - np.dot(a[1:i], r[i-1:0:-1])
        k = lam / e if e != 0 else 0
        a_new = a.copy()
        for j in range(1, i):
            a_new[j] = a[j] - k * a[i-j]
        a_new[i] = k
        e *= (1 - k**2)
        a = a_new
    lp = a[1:]
    # Konversi ke cepstrum
    c = np.zeros(n_lpcc)
    c[0] = -lp[0]
    for n_i in range(1, n_lpcc):
        c[n_i] = -lp[n_i] - sum((k+1)/n_i * c[k] * lp[n_i-k-1] for k in range(n_i))
    return c

x = [2, 4, 5, 4, 9, 7, 3, 7, 9, 7, 11, 10, 12, 13, 12, 14, 15, 16, 15, 17]
lpcc = compute_lpcc(x, n_lpcc=4)
print(f"LPCC = {[round(c, 4) for c in lpcc]}")
# Output: [-0.8038, 0.5082, -0.4467, 0.462]
```

---

### 4. `max_frequency`

**Definisi dan Kegunaan.** `max_frequency` adalah frekuensi yang memiliki daya spektral terbesar di bawah frekuensi Nyquist ($f_s/2$). Dalam konteks TSFEL, fitur ini serupa dengan `fundamental_frequency` tetapi secara eksplisit dibatasi pada rentang frekuensi di bawah Nyquist untuk menghindari aliasing.

**Rumus.**

$$f_{\max} = \arg\max_{f \leq f_s/2} |X(f)|^2$$

**Perhitungan Manual.**

Frekuensi Nyquist $= 0{,}5$ Hz. Semua frekuensi yang tersedia sudah di bawah Nyquist. Daya terbesar tetap pada $f = 0$:

$$f_{\max} = \mathbf{0{,}0 \text{ Hz}}$$

**Implementasi Python.**

```python
import numpy as np

x = np.array([2, 4, 5, 4, 9, 7, 3, 7, 9, 7, 11, 10, 12, 13, 12, 14, 15, 16, 15, 17])
X = np.fft.rfft(x)
freqs = np.fft.rfftfreq(len(x), d=1.0)
P = np.abs(X) ** 2
max_frequency = freqs[np.argmax(P)]
print(f"max_frequency = {max_frequency} Hz")  # Output: 0.0
```

---

### 5. `max_power_spectrum`

**Definisi dan Kegunaan.** `max_power_spectrum` adalah nilai daya spektral tertinggi dalam PSD sinyal, yaitu amplitudo puncak terbesar di seluruh spektrum frekuensi. Fitur ini memberikan gambaran seberapa kuat komponen frekuensi dominan sinyal dibandingkan komponen lainnya.

**Rumus.**

$$P_{\max} = \max_f |X(f)|^2$$

**Perhitungan Manual.**

$$|X(0)|^2 = |192|^2 = \mathbf{36864}$$

**Implementasi Python.**

```python
import numpy as np

x = np.array([2, 4, 5, 4, 9, 7, 3, 7, 9, 7, 11, 10, 12, 13, 12, 14, 15, 16, 15, 17])
X = np.fft.rfft(x)
max_power_spectrum = np.max(np.abs(X) ** 2)
print(f"max_power_spectrum = {max_power_spectrum:.2f}")  # Output: 36864.0
```

---

### 6. `median_frequency`

**Definisi dan Kegunaan.** `median_frequency` adalah frekuensi yang membagi total daya spektral menjadi dua bagian sama besar. Frekuensi di bawahnya mengandung 50% daya total, dan sisanya di atas. Fitur ini berguna untuk mengetahui di mana "pusat gravitasi" energi berada dalam domain frekuensi.

**Rumus.**

$$f_m : \sum_{f \leq f_m} P(f) = \frac{1}{2} \sum_{\text{all}} P(f)$$

**Perhitungan Manual.**

Total daya $= 40930$, setengahnya $= 20465$. Kumulatif daya:

- $f=0$: kum $= 36864$ ← sudah melewati 20465

Dengan demikian setengah daya pertama sudah tercapai di komponen DC pertama:

$$f_m = \mathbf{0{,}0 \text{ Hz}}$$

**Implementasi Python.**

```python
import numpy as np

x = np.array([2, 4, 5, 4, 9, 7, 3, 7, 9, 7, 11, 10, 12, 13, 12, 14, 15, 16, 15, 17])
X = np.fft.rfft(x)
freqs = np.fft.rfftfreq(len(x), d=1.0)
P = np.abs(X) ** 2
cumP = np.cumsum(P)
idx = np.searchsorted(cumP, np.sum(P) / 2)
median_frequency = freqs[min(idx, len(freqs)-1)]
print(f"median_frequency = {median_frequency} Hz")  # Output: 0.0
```

---

### 7. `mfcc`

**Definisi dan Kegunaan.** `mfcc` (*Mel-Frequency Cepstral Coefficients*) adalah koefisien cepstral yang dihitung pada skala Mel (logaritmik), yang meniru cara persepsi telinga manusia terhadap frekuensi. Setiap koefisien menangkap aspek berbeda dari tekstur spektral sinyal. Meskipun awalnya untuk pengenalan suara, koefisien ini juga menangkap pola spektral umum pada time series lainnya.

**Rumus.**

$$MFCC_n = \sum_{k=1}^{K} \log S(k) \cdot \cos\!\left[n\!\left(k - \tfrac{1}{2}\right)\frac{\pi}{K}\right]$$

**Perhitungan Manual.**

Menggunakan DCT pada log-amplitudo FFT ($K=11$ komponen):

$$MFCC = [30{,}819,\ 5{,}577,\ 3{,}409,\ 2{,}614]$$

**Implementasi Python.**

```python
import numpy as np

x = np.array([2, 4, 5, 4, 9, 7, 3, 7, 9, 7, 11, 10, 12, 13, 12, 14, 15, 16, 15, 17])
X = np.fft.rfft(x)
A = np.abs(X)
K = len(A)
n_mfcc = 4
log_A = np.log(A + 1e-10)
mfccs = [np.sum(log_A * np.cos(n * (np.arange(K) + 0.5) * np.pi / K))
         for n in range(n_mfcc)]
print(f"MFCC = {[round(c, 4) for c in mfccs]}")
# Output: [30.8189, 5.5772, 3.409, 2.6138]
```

---

### 8. `power_bandwidth`

**Definisi dan Kegunaan.** `power_bandwidth` adalah lebar pita frekuensi yang mengandung 95% total daya sinyal, dihitung sebagai selisih antara frekuensi batas atas dan batas bawah yang masing-masing mengandung 2,5% daya paling tepi. Fitur ini menggambarkan seberapa lebar atau sempit konten frekuensi sinyal yang bermakna.

**Rumus.**

$$BW = f_{\text{high}} - f_{\text{low}}, \quad \text{di mana } \int_{f_{\text{low}}}^{f_{\text{high}}} P(f)\,df = 0{,}95 \int P(f)\,df$$

**Perhitungan Manual.**

Total daya $= 40930$. Batas bawah (2,5%): $0{,}025 \times 40930 = 1023{,}25$, tercapai di $f = 0$. Batas atas (97,5%): $0{,}975 \times 40930 = 39906{,}75$, kumulatif mencapai ini di $f = 0{,}15$.

$$BW = 0{,}15 - 0{,}0 = \mathbf{0{,}15 \text{ Hz}}$$

**Implementasi Python.**

```python
import numpy as np

x = np.array([2, 4, 5, 4, 9, 7, 3, 7, 9, 7, 11, 10, 12, 13, 12, 14, 15, 16, 15, 17])
X = np.fft.rfft(x)
freqs = np.fft.rfftfreq(len(x), d=1.0)
P = np.abs(X) ** 2
cumP = np.cumsum(P)
total_P = np.sum(P)
idx_low = np.searchsorted(cumP, 0.025 * total_P)
idx_high = np.searchsorted(cumP, 0.975 * total_P)
power_bandwidth = freqs[min(idx_high, len(freqs)-1)] - freqs[min(idx_low, len(freqs)-1)]
print(f"power_bandwidth = {power_bandwidth:.4f} Hz")  # Output: 0.15
```

---

### 9. `spectral_centroid`

**Definisi dan Kegunaan.** `spectral_centroid` adalah "pusat massa" frekuensi yang dibobot oleh daya spektral. Fitur ini mencerminkan di mana energi sinyal dominan berada dalam domain frekuensi. Nilai centroid yang rendah (mendekati 0) berarti energi terkonsentrasi di frekuensi rendah (tren lambat), sedangkan nilai tinggi mengindikasikan dominasi frekuensi tinggi (osilasi cepat).

**Rumus.**

$$SC = \frac{\sum_f f \cdot |X(f)|^2}{\sum_f |X(f)|^2}$$

**Perhitungan Manual.**

$$SC = \frac{0 \cdot 36864 + 0{,}05 \cdot 2354{,}27 + 0{,}10 \cdot 343{,}78 + \ldots}{40930}$$

$$= \frac{529{,}97}{40930} \approx \mathbf{0{,}01295 \text{ Hz}}$$

**Implementasi Python.**

```python
import numpy as np

x = np.array([2, 4, 5, 4, 9, 7, 3, 7, 9, 7, 11, 10, 12, 13, 12, 14, 15, 16, 15, 17])
X = np.fft.rfft(x)
freqs = np.fft.rfftfreq(len(x), d=1.0)
P = np.abs(X) ** 2
spectral_centroid = np.sum(freqs * P) / np.sum(P)
print(f"spectral_centroid = {spectral_centroid:.6f} Hz")  # Output: 0.012951
```

---

### 10. `spectral_decrease`

**Definisi dan Kegunaan.** `spectral_decrease` mengukur kecenderungan penurunan amplitudo spektrum dari frekuensi rendah ke tinggi. Nilai negatif berarti amplitudo menurun seiring naiknya frekuensi (spektrum condong ke rendah); nilai positif berarti amplitudo meningkat. Berguna untuk menentukan apakah sinyal kaya frekuensi rendah atau tinggi.

**Rumus.**

$$SD = \frac{\sum_{k=2}^{K} \frac{|X(k)| - |X(1)|}{k-1}}{\sum_{k=2}^{K}|X(k)|}$$

**Perhitungan Manual.**

Amplitudo FFT: $A = [192{,}0,\ 48{,}52,\ 18{,}54,\ 20{,}30,\ 15{,}09,\ 5{,}10,\ 8{,}56,\ 19{,}98,\ 7{,}44,\ 11{,}77,\ 6{,}0]$

Numerator $= \sum_{k=2}^{11} \frac{A_k - A_1}{k-1}$, dimana $A_1 = 192{,}0$:

$$= \frac{48{,}52-192}{1} + \frac{18{,}54-192}{2} + \ldots \approx -363{,}49$$

Denominator $= 48{,}52 + 18{,}54 + \ldots + 6{,}0 = 161{,}30$

$$SD = \frac{-363{,}49}{161{,}30} \approx \mathbf{-3{,}0125}$$

**Implementasi Python.**

```python
import numpy as np

x = np.array([2, 4, 5, 4, 9, 7, 3, 7, 9, 7, 11, 10, 12, 13, 12, 14, 15, 16, 15, 17])
X = np.fft.rfft(x)
A = np.abs(X)
K = len(A)
numerator = np.sum((A[1:] - A[0]) / np.arange(1, K))
denominator = np.sum(A[1:])
spectral_decrease = numerator / denominator
print(f"spectral_decrease = {spectral_decrease:.6f}")  # Output: -3.012460
```

---

### 11. `spectral_distance`

**Definisi dan Kegunaan.** `spectral_distance` mengukur jarak Euclidean antara dua spektrum daya, atau antara spektrum sinyal dengan referensi tertentu. Fitur ini berguna untuk membandingkan seberapa berbeda kandungan frekuensi satu sinyal dengan lainnya. Dalam TSFEL single-signal, ini sering dihitung sebagai norma dari vektor PSD itu sendiri.

**Rumus.**

$$D_s = \sqrt{\sum_f (P_1(f) - P_2(f))^2}$$

**Perhitungan Manual.**

Dengan referensi nol ($P_2 = 0$):

$$D_s = \sqrt{36864^2 + 2354{,}27^2 + \ldots} = \sqrt{\sum P^2} \approx \mathbf{36946{,}26}$$

**Implementasi Python.**

```python
import numpy as np

x = np.array([2, 4, 5, 4, 9, 7, 3, 7, 9, 7, 11, 10, 12, 13, 12, 14, 15, 16, 15, 17])
X = np.fft.rfft(x)
P = np.abs(X) ** 2
spectral_distance = np.sqrt(np.sum(P ** 2))
print(f"spectral_distance = {spectral_distance:.4f}")  # Output: 36946.2555
```

---

### 12. `spectral_entropy`

**Definisi dan Kegunaan.** `spectral_entropy` adalah entropi Shannon yang dihitung dari distribusi daya spektral. Nilai tinggi (mendekati 1 atau $\log_2 K$) berarti daya tersebar merata di seluruh frekuensi (sinyal lebih acak secara spektral), sedangkan nilai rendah berarti energi terkonsentrasi di sedikit frekuensi (sinyal lebih periodik atau terdeterminasi).

**Rumus.**

$$H_s = -\sum_f p(f) \log_2 p(f), \quad p(f) = \frac{|X(f)|^2}{\sum|X(f)|^2}$$

**Perhitungan Manual.**

Proporsi daya: $p = [0{,}9007,\ 0{,}0575,\ 0{,}0084,\ 0{,}0101,\ 0{,}0056,\ 0{,}0006,\ 0{,}0018,\ 0{,}0098,\ 0{,}0014,\ 0{,}0034,\ 0{,}0009]$

$$H_s = -(0{,}9007 \log_2 0{,}9007) - (0{,}0575 \log_2 0{,}0575) - \ldots \approx \mathbf{0{,}6771}$$

Nilai rendah menunjukkan energi sangat terkonsentrasi di komponen DC (frekuensi 0), mencerminkan dominasi tren dibandingkan osilasi.

**Implementasi Python.**

```python
import numpy as np

x = np.array([2, 4, 5, 4, 9, 7, 3, 7, 9, 7, 11, 10, 12, 13, 12, 14, 15, 16, 15, 17])
X = np.fft.rfft(x)
P = np.abs(X) ** 2
p = P / np.sum(P)
p_nz = p[p > 0]
spectral_entropy = -np.sum(p_nz * np.log2(p_nz))
print(f"spectral_entropy = {spectral_entropy:.6f}")  # Output: 0.677096
```

---

### 13. `spectral_kurtosis`

**Definisi dan Kegunaan.** `spectral_kurtosis` mengukur keruncingan distribusi daya spektral terhadap centroid frekuensinya. Nilai tinggi berarti daya sangat terkonsentrasi di sekitar frekuensi tertentu (spektrum sangat peaked); nilai rendah berarti daya tersebar luas. Berguna untuk mendeteksi komponen frekuensi yang sangat dominan atau sinyal yang mengandung narrow-band noise.

**Rumus.**

$$K_s = \frac{\sum_f (f - SC)^4 \cdot P(f)}{\left(\sum_f (f - SC)^2 \cdot P(f)\right)^2}$$

**Perhitungan Manual.**

Dengan $SC = 0{,}01295$ Hz, hitung momen ke-4 dan ke-2 berbobot daya:

$$K_s \approx \mathbf{0{,}000945}$$

Nilai sangat kecil menunjukkan distribusi daya sangat datar relatif terhadap centroid — energi terlalu terpusat di frekuensi 0 sehingga momen-momen tinggi kecil.

**Implementasi Python.**

```python
import numpy as np

x = np.array([2, 4, 5, 4, 9, 7, 3, 7, 9, 7, 11, 10, 12, 13, 12, 14, 15, 16, 15, 17])
X = np.fft.rfft(x)
freqs = np.fft.rfftfreq(len(x), d=1.0)
P = np.abs(X) ** 2
SC = np.sum(freqs * P) / np.sum(P)
spectral_kurtosis = np.sum((freqs - SC)**4 * P) / (np.sum((freqs - SC)**2 * P))**2
print(f"spectral_kurtosis = {spectral_kurtosis:.6f}")  # Output: 0.000945
```

---

### 14. `spectral_positive_turning`

**Definisi dan Kegunaan.** `spectral_positive_turning` menghitung jumlah puncak lokal (titik balik positif) dalam kurva PSD, yaitu frekuensi di mana daya lebih besar dari kedua tetangganya. Fitur ini mencerminkan berapa banyak pita frekuensi yang aktif atau memiliki energi signifikan dalam sinyal.

**Rumus.**

$f_i$ adalah puncak spektral jika $P(f_{i-1}) < P(f_i) > P(f_{i+1})$

**Perhitungan Manual.**

PSD: $[36864,\ 2354{,}27,\ 343{,}78,\ 412{,}14,\ 227{,}59,\ 26{,}0,\ 73{,}22,\ 399{,}10,\ 55{,}41,\ 138{,}49,\ 36{,}0]$

Puncak lokal pada indeks (0-based):

- Indeks 3: $343{,}78 < 412{,}14 > 227{,}59$ ✓
- Indeks 7: $73{,}22 < 399{,}10 > 55{,}41$ ✓
- Indeks 9: $55{,}41 < 138{,}49 > 36{,}0$ ✓

$$\text{spectral\_positive\_turning} = \mathbf{3}$$

**Implementasi Python.**

```python
import numpy as np

x = np.array([2, 4, 5, 4, 9, 7, 3, 7, 9, 7, 11, 10, 12, 13, 12, 14, 15, 16, 15, 17])
X = np.fft.rfft(x)
P = np.abs(X) ** 2
pos_turns = sum(1 for i in range(1, len(P)-1) if P[i-1] < P[i] > P[i+1])
print(f"spectral_positive_turning = {pos_turns}")  # Output: 3
```

---

### 15. `spectral_roll_off`

**Definisi dan Kegunaan.** `spectral_roll_off` adalah frekuensi di mana 85% (atau 95%) dari total energi spektral sudah terakumulasi. Frekuensi ini menandai batas atas efektif spektrum sinyal. Di atas frekuensi ini, hanya tersisa 15% energi. Berguna untuk menentukan bandwidth efektif sinyal.

**Rumus.**

$$f_{ro} : \sum_{f \leq f_{ro}} P(f) = 0{,}85 \sum_{\text{all}} P(f)$$

**Perhitungan Manual.**

$85\%$ dari $40930 = 34790{,}5$. Kumulatif pertama adalah $36864$ (komponen DC), yang sudah melewati threshold:

$$f_{ro} = \mathbf{0{,}0 \text{ Hz}}$$

**Implementasi Python.**

```python
import numpy as np

x = np.array([2, 4, 5, 4, 9, 7, 3, 7, 9, 7, 11, 10, 12, 13, 12, 14, 15, 16, 15, 17])
X = np.fft.rfft(x)
freqs = np.fft.rfftfreq(len(x), d=1.0)
P = np.abs(X) ** 2
cumP = np.cumsum(P)
idx = np.searchsorted(cumP, 0.85 * np.sum(P))
roll_off = freqs[min(idx, len(freqs)-1)]
print(f"spectral_roll_off = {roll_off} Hz")  # Output: 0.0
```

---

### 16. `spectral_roll_on`

**Definisi dan Kegunaan.** `spectral_roll_on` adalah frekuensi di mana energi spektral mulai terakumulasi secara signifikan, yaitu titik di mana 5% dari total energi telah terkumpul. Ini adalah batas bawah efektif spektrum sinyal, menandai frekuensi terendah yang berkontribusi secara bermakna.

**Rumus.**

$$f_{rn} : \sum_{f \leq f_{rn}} P(f) = 0{,}05 \sum_{\text{all}} P(f)$$

**Perhitungan Manual.**

$5\%$ dari $40930 = 2046{,}5$. Kumulatif pertama ($36864$) jauh melewati threshold, sehingga:

$$f_{rn} = \mathbf{0{,}0 \text{ Hz}}$$

**Implementasi Python.**

```python
import numpy as np

x = np.array([2, 4, 5, 4, 9, 7, 3, 7, 9, 7, 11, 10, 12, 13, 12, 14, 15, 16, 15, 17])
X = np.fft.rfft(x)
freqs = np.fft.rfftfreq(len(x), d=1.0)
P = np.abs(X) ** 2
cumP = np.cumsum(P)
idx = np.searchsorted(cumP, 0.05 * np.sum(P))
roll_on = freqs[min(idx, len(freqs)-1)]
print(f"spectral_roll_on = {roll_on} Hz")  # Output: 0.0
```

---

### 17. `spectral_skewness`

**Definisi dan Kegunaan.** `spectral_skewness` mengukur kemiringan distribusi daya spektral relatif terhadap centroid frekuensinya. Nilai positif menunjukkan ekor distribusi daya memanjang ke frekuensi tinggi; nilai negatif ke frekuensi rendah. Berguna untuk mengetahui apakah sinyal lebih kaya frekuensi tinggi atau rendah secara asimetris.

**Rumus.**

$$\gamma_s = \frac{\sum_f (f - SC)^3 \cdot P(f)}{\left(\sum_f (f - SC)^2 \cdot P(f)\right)^{3/2}}$$

**Perhitungan Manual.**

Dengan $SC = 0{,}01295$, hitung momen ke-3 berbobot daya lalu normalisasi:

$$\gamma_s \approx \mathbf{5{,}7407}$$

Nilai positif tinggi mengindikasikan distribusi daya sangat condong ke frekuensi tinggi (ekor kanan panjang), meskipun sebagian besar energi ada di DC.

**Implementasi Python.**

```python
import numpy as np

x = np.array([2, 4, 5, 4, 9, 7, 3, 7, 9, 7, 11, 10, 12, 13, 12, 14, 15, 16, 15, 17])
X = np.fft.rfft(x)
freqs = np.fft.rfftfreq(len(x), d=1.0)
P = np.abs(X) ** 2
SC = np.sum(freqs * P) / np.sum(P)
spread = np.sqrt(np.sum((freqs - SC)**2 * P) / np.sum(P))
spectral_skewness = np.sum((freqs - SC)**3 * P) / (np.sum(P) * spread**3)
print(f"spectral_skewness = {spectral_skewness:.6f}")  # Output: 5.740683
```

---

### 18. `spectral_slope`

**Definisi dan Kegunaan.** `spectral_slope` adalah kemiringan regresi linear yang di-fitting pada amplitudo spektrum terhadap frekuensi. Nilai negatif berarti amplitudo spektrum cenderung turun seiring meningkatnya frekuensi (energi dominan di frekuensi rendah), yang umum terjadi pada sinyal dengan tren.

**Rumus.**

$$\beta_s = \frac{\sum_f (f - \bar{f})(|X(f)| - \overline{|X|})}{\sum_f (f - \bar{f})^2}$$

**Perhitungan Manual.**

Dengan $\bar{f} = 0{,}25$ dan $\overline{|X|} \approx 17{,}39$:

$$\beta_s \approx \mathbf{-203{,}18}$$

Nilai negatif besar mengkonfirmasi amplitudo spektrum turun drastis dari frekuensi 0 (amplitudo 192) ke frekuensi tinggi.

**Implementasi Python.**

```python
import numpy as np

x = np.array([2, 4, 5, 4, 9, 7, 3, 7, 9, 7, 11, 10, 12, 13, 12, 14, 15, 16, 15, 17])
X = np.fft.rfft(x)
freqs = np.fft.rfftfreq(len(x), d=1.0)
A = np.abs(X)
f_mean, A_mean = np.mean(freqs), np.mean(A)
spectral_slope = np.sum((freqs - f_mean) * (A - A_mean)) / np.sum((freqs - f_mean)**2)
print(f"spectral_slope = {spectral_slope:.4f}")  # Output: -203.1782
```

---

### 19. `spectral_spread`

**Definisi dan Kegunaan.** `spectral_spread` adalah simpangan baku frekuensi berbobot daya terhadap centroid spektral. Fitur ini mengukur lebar efektif spektrum, yaitu seberapa luas sebaran frekuensi yang aktif di sekitar centroid. Nilai kecil berarti energi terkonsentrasi sempit di sekitar centroid; nilai besar berarti energi tersebar luas.

**Rumus.**

$$SS = \sqrt{\frac{\sum_f (f - SC)^2 \cdot P(f)}{\sum_f P(f)}}$$

**Perhitungan Manual.**

$$SS = \sqrt{\frac{\sum_f (f - 0{,}01295)^2 \cdot P(f)}{40930}} \approx \mathbf{0{,}0550 \text{ Hz}}$$

**Implementasi Python.**

```python
import numpy as np

x = np.array([2, 4, 5, 4, 9, 7, 3, 7, 9, 7, 11, 10, 12, 13, 12, 14, 15, 16, 15, 17])
X = np.fft.rfft(x)
freqs = np.fft.rfftfreq(len(x), d=1.0)
P = np.abs(X) ** 2
SC = np.sum(freqs * P) / np.sum(P)
spectral_spread = np.sqrt(np.sum((freqs - SC)**2 * P) / np.sum(P))
print(f"spectral_spread = {spectral_spread:.6f} Hz")  # Output: 0.055008
```

---

### 20. `spectral_variation`

**Definisi dan Kegunaan.** `spectral_variation` mengukur perubahan spektrum antar frame menggunakan korelasi silang normalisasi. Nilai mendekati 0 berarti spektrum sangat berubah antar frame (sinyal non-stasioner); nilai mendekati 1 berarti spektrum hampir sama antar frame (sinyal stasioner). Berguna untuk mendeteksi apakah karakter frekuensi sinyal berubah dari waktu ke waktu.

**Rumus.**

$$SV = 1 - \frac{\sum_f |X_t(f)| \cdot |X_{t+1}(f)|}{\sqrt{\sum_f |X_t(f)|^2 \cdot \sum_f |X_{t+1}(f)|^2}}$$

**Perhitungan Manual.**

Untuk sinyal tunggal (tanpa pembagian frame), dihitung autokorelasi spektrum dengan dirinya sendiri:

$$SV = 1 - \frac{\sum A^2}{\|A\|^2} = 1 - 1 = \mathbf{0{,}0}$$

**Implementasi Python.**

```python
import numpy as np

x = np.array([2, 4, 5, 4, 9, 7, 3, 7, 9, 7, 11, 10, 12, 13, 12, 14, 15, 16, 15, 17])
X = np.fft.rfft(x)
A = np.abs(X)
# Contoh: variasi antara dua half-signal
X1 = np.fft.rfft(x[:10])
X2 = np.fft.rfft(x[10:])
A1, A2 = np.abs(X1), np.abs(X2)
# Pastikan panjang sama
min_len = min(len(A1), len(A2))
sv = 1 - np.dot(A1[:min_len], A2[:min_len]) / (np.linalg.norm(A1[:min_len]) * np.linalg.norm(A2[:min_len]))
print(f"spectral_variation = {sv:.6f}")
```

---

### 21. `spectrogram_mean_coeff`

**Definisi dan Kegunaan.** `spectrogram_mean_coeff` adalah rata-rata koefisien daya dari spektrogram (Short-Time Fourier Transform, STFT) pada setiap band frekuensi sepanjang waktu. Fitur ini mewakili intensitas rata-rata energi di setiap pita frekuensi sepanjang keseluruhan sinyal, memberikan gambaran distribusi temporal-frekuensi yang teragregasi.

**Rumus.**

$$\bar{S}_k = \frac{1}{T} \sum_{t=1}^{T} |STFT(t, k)|^2$$

**Perhitungan Manual.**

STFT dengan `nperseg=8`, `noverlap=4` menghasilkan 5 band frekuensi dan 6 frame. Rata-rata daya per band:

$$\bar{S} = [80{,}47,\ 25{,}55,\ 2{,}63,\ 1{,}45,\ 1{,}01]$$

Band pertama (frekuensi rendah) memiliki rata-rata daya tertinggi, konsisten dengan dominasi tren.

**Implementasi Python.**

```python
import numpy as np
from scipy.signal import stft

x = np.array([2, 4, 5, 4, 9, 7, 3, 7, 9, 7, 11, 10, 12, 13, 12, 14, 15, 16, 15, 17])
f, t, Zxx = stft(x, fs=1.0, nperseg=8, noverlap=4)
mean_coeff = np.mean(np.abs(Zxx) ** 2, axis=1)
print(f"spectrogram_mean_coeff = {[round(c, 4) for c in mean_coeff]}")
# Output: [80.4713, 25.5487, 2.6287, 1.4461, 1.011]
```

---

### 22. `wavelet_abs_mean`

**Definisi dan Kegunaan.** `wavelet_abs_mean` adalah rata-rata nilai absolut dari koefisien wavelet pada level dekomposisi tertentu. Fitur ini mengukur amplitudo rata-rata detail sinyal yang ditangkap oleh wavelet di skala tersebut. Nilai besar berarti terdapat fluktuasi signifikan pada skala frekuensi yang dianalisis.

**Rumus.**

$$\overline{|W|} = \frac{1}{N_w} \sum_j |W_j|$$

**Perhitungan Manual.**

Dengan wavelet db4, level 1, koefisien detail ($cD$):

$$cD = [-0{,}1771,\ 0{,}3639,\ 2{,}8592,\ -3{,}3865,\ 1{,}7232,\ 1{,}9677,\ 0{,}2915,\ -1{,}3003,\ 0{,}2247,\ -1{,}2736,\ 0{,}4196,\ 1{,}0001,\ -0{,}0558]$$

$$\overline{|cD|} = \frac{|-0{,}1771| + |0{,}3639| + \ldots}{13} = \frac{15{,}0431}{13} \approx \mathbf{1{,}1572}$$

**Implementasi Python.**

```python
import numpy as np
import pywt

x = np.array([2, 4, 5, 4, 9, 7, 3, 7, 9, 7, 11, 10, 12, 13, 12, 14, 15, 16, 15, 17], dtype=float)
coeffs = pywt.wavedec(x, 'db4', level=1)
cD = coeffs[1]   # detail coefficients level 1
wavelet_abs_mean = np.mean(np.abs(cD))
print(f"wavelet_abs_mean = {wavelet_abs_mean:.6f}")  # Output: 1.157165
```

---

### 23. `wavelet_energy`

**Definisi dan Kegunaan.** `wavelet_energy` adalah total energi koefisien wavelet pada level yang dianalisis, dihitung sebagai jumlah kuadrat seluruh koefisien. Fitur ini mengukur berapa besar energi sinyal yang ditangkap pada skala dekomposisi tersebut. Berguna untuk mengidentifikasi di skala mana energi sinyal paling signifikan.

**Rumus.**

$$E_w = \sum_j W_j^2$$

**Perhitungan Manual.**

$$E_w = (-0{,}1771)^2 + (0{,}3639)^2 + (2{,}8592)^2 + \ldots + (-0{,}0558)^2$$
$$= 0{,}0313 + 0{,}1324 + 8{,}1750 + 11{,}4684 + \ldots \approx \mathbf{31{,}2762}$$

**Implementasi Python.**

```python
import numpy as np
import pywt

x = np.array([2, 4, 5, 4, 9, 7, 3, 7, 9, 7, 11, 10, 12, 13, 12, 14, 15, 16, 15, 17], dtype=float)
coeffs = pywt.wavedec(x, 'db4', level=1)
cD = coeffs[1]
wavelet_energy = np.sum(cD ** 2)
print(f"wavelet_energy = {wavelet_energy:.6f}")  # Output: 31.276201
```

---

### 24. `wavelet_entropy`

**Definisi dan Kegunaan.** `wavelet_entropy` adalah entropi Shannon dari distribusi energi koefisien wavelet. Nilai tinggi berarti energi tersebar merata di banyak koefisien (sinyal kompleks); nilai rendah berarti energi terkonsentrasi di sedikit koefisien (sinyal lebih teratur). Berguna untuk mengukur kompleksitas sinyal pada skala spesifik.

**Rumus.**

$$H_w = -\sum_j p_j \log_2 p_j, \quad p_j = \frac{W_j^2}{\sum_k W_k^2}$$

**Perhitungan Manual.**

Proporsi energi per koefisien: $p_j = W_j^2 / 31{,}276$. Dengan 13 koefisien:

$$H_w = -\sum_j p_j \log_2 p_j \approx \mathbf{2{,}4650}$$

**Implementasi Python.**

```python
import numpy as np
import pywt

x = np.array([2, 4, 5, 4, 9, 7, 3, 7, 9, 7, 11, 10, 12, 13, 12, 14, 15, 16, 15, 17], dtype=float)
coeffs = pywt.wavedec(x, 'db4', level=1)
cD = coeffs[1]
E_w = np.sum(cD ** 2)
p_w = cD**2 / E_w
p_nz = p_w[p_w > 0]
wavelet_entropy = -np.sum(p_nz * np.log2(p_nz))
print(f"wavelet_entropy = {wavelet_entropy:.6f}")  # Output: 2.465008
```

---

### 25. `wavelet_std`

**Definisi dan Kegunaan.** `wavelet_std` adalah simpangan baku dari koefisien wavelet, mengukur seberapa bervariasi amplitudo koefisien di sekitar rata-ratanya. Nilai besar menandakan fluktuasi yang heterogen antar koefisien (beberapa sangat besar, beberapa sangat kecil); nilai kecil menandakan koefisien yang lebih homogen.

**Rumus.**

$$\sigma_w = \sqrt{\frac{1}{N_w} \sum_j (W_j - \bar{W})^2}$$

**Perhitungan Manual.**

Dengan $\bar{W} = \frac{\sum cD}{13} \approx 0{,}2021$:

$$\sigma_w = \sqrt{\frac{\sum (W_j - 0{,}2021)^2}{13}} \approx \mathbf{1{,}5376}$$

**Implementasi Python.**

```python
import numpy as np
import pywt

x = np.array([2, 4, 5, 4, 9, 7, 3, 7, 9, 7, 11, 10, 12, 13, 12, 14, 15, 16, 15, 17], dtype=float)
coeffs = pywt.wavedec(x, 'db4', level=1)
cD = coeffs[1]
wavelet_std = np.std(cD, ddof=0)
print(f"wavelet_std = {wavelet_std:.6f}")  # Output: 1.537565
```

---

### 26. `wavelet_var`

**Definisi dan Kegunaan.** `wavelet_var` adalah variansi koefisien wavelet, yaitu kuadrat dari simpangan baku wavelet. Fitur ini mencerminkan total fluktuasi energi pada skala dekomposisi yang dianalisis. Semakin besar nilainya, semakin heterogen distribusi energi di antara koefisien-koefisien wavelet.

**Rumus.**

$$\sigma_w^2 = \frac{1}{N_w} \sum_j (W_j - \bar{W})^2$$

**Perhitungan Manual.**

$$\sigma_w^2 = (1{,}5376)^2 \approx \mathbf{2{,}3641}$$

**Implementasi Python.**

```python
import numpy as np
import pywt

x = np.array([2, 4, 5, 4, 9, 7, 3, 7, 9, 7, 11, 10, 12, 13, 12, 14, 15, 16, 15, 17], dtype=float)
coeffs = pywt.wavedec(x, 'db4', level=1)
cD = coeffs[1]
wavelet_var = np.var(cD, ddof=0)
print(f"wavelet_var = {wavelet_var:.6f}")  # Output: 2.364107
```

---

*Seluruh perhitungan menggunakan data: $x = \{2, 4, 5, 4, 9, 7, 3, 7, 9, 7, 11, 10, 12, 13, 12, 14, 15, 16, 15, 17\}$, $N=20$, $\bar{x}=9{,}6$, $\tilde{x}=9{,}5$, $f_s = 1$ sampel/periode.*
