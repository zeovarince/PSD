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

# Analisis Time Series: Migrasi Data & Pengolahan di KNIME

Sebelum pemodelan time series dilakukan, data historis polutan yang tersimpan dalam tiga file CSV perlu dipindahkan ke cloud database agar bisa diakses dari berbagai platform secara terpusat. Dokumen ini mencakup alur lengkap mulai dari pembuatan database PostgreSQL di Aiven, migrasi data via Python, hingga pengolahan di KNIME Analytics Platform beserta penjelasan matematis setiap fitur statistik yang dihasilkan.

---

## Migrasi Data ke Aiven PostgreSQL

### Buat Akun dan Database di Aiven

Aiven adalah layanan cloud database terkelola yang mendukung PostgreSQL, MySQL, Kafka, dan lainnya. Data polutan disimpan di sini agar bisa ditarik dari KNIME tanpa perlu memindahkan file CSV secara manual.

**Langkah-langkah:**

1. Buka [console.aiven.io](https://console.aiven.io) dan daftarkan akun baru atau login jika sudah punya.
2. Setelah masuk ke dashboard, klik **Create Service**.
3. Pilih **PostgreSQL** sebagai jenis layanan.
4. Pilih cloud provider (Google Cloud, AWS, atau Azure) dan region terdekat — pilih **Google Cloud / asia-southeast1 (Singapore)** untuk latensi minimal dari Indonesia.
5. Pilih plan **Free** untuk keperluan tugas, lalu klik **Create Service**.
6. Tunggu beberapa menit hingga status layanan berubah dari *Rebuilding* menjadi **Running**.

Setelah layanan aktif, buka halaman **Overview** layanan tersebut. Di sana tersedia informasi koneksi yang dibutuhkan:

- **Host**: alamat server (contoh: `xxxxx.aivencloud.com`)
- **Port**: nomor port PostgreSQL (biasanya 24065 atau 14699)
- **Database**: `defaultdb`
- **Username**: `avnadmin`
- **Password**: password yang digenerate otomatis oleh Aiven
- **URI**: connection string lengkap dalam format `postgresql://user:pass@host:port/db?sslmode=require`

### Migrasi Data via Python

Data dipindahkan menggunakan Python dengan library `sqlalchemy` dan `psycopg2`. Tidak perlu membuat tabel secara manual di PG Studio — perintah `to_sql` dengan parameter `if_exists='replace'` secara otomatis membuat tabel baru sesuai struktur dataframe yang dikirim. Jika tabel sudah ada dari run sebelumnya, tabel lama dihapus dulu agar data tidak duplikat.

```{code-cell} ipython3
!pip install pandas sqlalchemy psycopg2-binary

import pandas as pd
from sqlalchemy import create_engine, text

# 1. Baca ketiga file CSV
# Pastikan nama file SO2 dan CO sudah sesuai dengan yang Anda miliki
df_no2 = pd.read_csv('NO2_KAMAL-UTM.csv')
df_so2 = pd.read_csv('SO2_KAMAL-UTM.csv') # Ganti jika nama file berbeda
df_co = pd.read_csv('CO_KAMAL-UTM.csv')   # Ganti jika nama file berbeda

# 2. Gabungkan (Merge) ketiga dataframe berdasarkan 'date' dan 'feature_index'
# Menggunakan 'outer' join agar tanggal yang ada di satu file tapi tidak ada di file lain tetap masuk (menjadi NaN/Null)
df_gabung = pd.merge(df_no2, df_so2, on=['date', 'feature_index'], how='outer')
df_gabung = pd.merge(df_gabung, df_co, on=['date', 'feature_index'], how='outer')

print("Data berhasil digabung! Berikut 5 baris pertamanya:")
print(df_gabung.head())

# 3. Konfigurasi Koneksi Database
# PENTING: Ganti dengan URL database Anda yang aktif!
DATABASE_URI = "masukan url aiven anda"
engine = create_engine(DATABASE_URI)
table_name = 'kualitas_udara_kamal'

# 4. Hapus (Drop) tabel lama jika sudah ada, lalu unggah data baru
try:
    with engine.connect() as conn:
        # Hapus tabel lama agar bersih
        conn.execute(text(f"DROP TABLE IF EXISTS {table_name};"))
        conn.commit()
        print(f"Tabel lama '{table_name}' berhasil dihapus (jika ada).")
    
    # Upload data yang sudah digabung (if_exists='replace' juga otomatis menimpa tabel)
    df_gabung.to_sql(name=table_name, con=engine, if_exists='replace', index=False)
    print(f"Tabel baru '{table_name}' berhasil dibuat dan data telah diunggah!")

except Exception as e:
    print(f"Terjadi kesalahan pada database: {e}")
```

`to_sql` dengan `if_exists='replace'` secara otomatis membuat tabel `kualitas_udara_kamal` di Aiven beserta seluruh kolom dan tipe datanya — tidak perlu menulis `CREATE TABLE` manual di PG Studio. Setelah cell selesai dijalankan, tabel sudah tersedia di database dan siap ditarik dari KNIME.

---

## Integrasi dan Pengolahan Time Series di KNIME

KNIME Analytics Platform adalah tools analitik berbasis node yang memungkinkan penarikan data dari database, transformasi, dan analisis statistik secara visual tanpa menulis banyak kode. Workflow yang dibangun menggunakan empat node utama sesuai gambar: **PostgreSQL Connector → DB Query Reader → Column Filter → Statistics**, dengan cabang ke **Table View** dan **CSV Writer**.

### Node 1: PostgreSQL Connector

![KNIME PostgreSQL Connector](/materi/assets/sqlconector.png)

Node ini membangun koneksi ke database Aiven. Tanpa koneksi yang berhasil di node ini, seluruh node berikutnya tidak bisa berjalan.

**Konfigurasi:**

1. Tambahkan node **PostgreSQL Connector** dari panel node di kiri (cari dengan kata kunci "PostgreSQL").
2. Double-click node untuk membuka konfigurasi.
3. Isi bagian **Connection Settings**:
   - **Hostname**: host dari Aiven (contoh: `posgrespsd-xxx.aivencloud.com`)
   - **Port**: port dari Aiven (contoh: `24065`)
   - **Database name**: `defaultdb`
   - **Username**: `avnadmin`
   - **Password**: password dari Aiven
4. Buka tab **JDBC Parameters**, klik **Add**, lalu tambahkan:
   - **Parameter name**: `sslmode`
   - **Value**: `require`

   Langkah ini wajib dilakukan karena Aiven menolak koneksi yang tidak menggunakan SSL.
5. Klik **OK**, lalu klik kanan node dan pilih **Execute** untuk menguji koneksi. Indikator hijau di bawah node menandakan koneksi berhasil.

### Node 2: DB Query Reader

![DB Query Reader](/materi/assets/dbqueryreader.png)

Node ini menarik data dari tabel `kualitas_udara_kamal` di Aiven ke dalam memori KNIME. Berbeda dengan DB Table Selector yang hanya memilih tabel, DB Query Reader memungkinkan penulisan query SQL kustom sehingga bisa memfilter kolom atau baris tertentu sejak awal.

**Konfigurasi:**

1. Tambahkan node **DB Query Reader** dan hubungkan output port PostgreSQL Connector ke input port DB Query Reader.
2. Double-click untuk membuka konfigurasi.
3. Di kolom **SQL Query**, ketikkan:

```sql
SELECT date, NO2, SO2, CO FROM kualitas_udara_kamal ORDER BY date ASC;
```

4. Klik **OK**, lalu execute node. Output port menghasilkan tabel dengan 370 baris dan 4 kolom yang siap diolah.

### Node 3: Column Filter

![Column Filter](/materi/assets/columnfilter.png)

Node ini menyaring kolom yang tidak diperlukan untuk analisis statistik. Kolom `feature_index` misalnya hanya berisi nilai 0 di seluruh baris dan tidak memberi informasi apapun untuk analisis polutan.

**Konfigurasi:**

1. Tambahkan node **Column Filter** dan hubungkan output DB Query Reader ke inputnya.
2. Double-click untuk membuka konfigurasi.
3. Pindahkan kolom yang ingin **dipertahankan** ke panel kanan (Includes):
   - `date`, `NO2`, `SO2`, `CO`
4. Kolom `feature_index` biarkan di panel kiri (Excludes) sehingga tidak ikut ke output.
5. Klik **OK** dan execute.

### Node 4: Statistics

![Statistics 1](/materi/assets/statistic1.png)
![Statistics 2](/materi/assets/statistic2.png)  

Node Statistics adalah inti dari eksplorasi data di KNIME. Node ini secara otomatis menghitung seluruh metrik statistik deskriptif untuk semua kolom numerik sekaligus dalam satu eksekusi, tanpa perlu menulis kode apapun.

**Konfigurasi:**

1. Tambahkan node **Statistics** dan hubungkan output Column Filter ke inputnya.
2. Double-click untuk membuka konfigurasi.
3. Pada tab **Column Selection**, pastikan kolom `NO2`, `SO2`, dan `CO` dipilih (centang semua).
4. Klik **OK** dan execute. Output node berupa tabel ringkasan statistik untuk ketiga polutan.

### Node: Table View

Node Table View menampilkan isi data dalam format tabel yang bisa di-scroll dan di-filter langsung di KNIME. Hubungkan output Column Filter ke Table View untuk melihat keseluruhan 370 baris data mentah.

**Konfigurasi:** Tidak ada konfigurasi khusus. Hubungkan ke output Column Filter, execute, lalu double-click untuk membuka tampilan tabel.

### Node: CSV Writer

Node CSV Writer menyimpan output dari node sebelumnya ke file CSV di komputer lokal. Ini berguna untuk menyimpan hasil setelah transformasi di KNIME tanpa harus kembali ke Python.

**Konfigurasi:**

1. Tambahkan node **CSV Writer** dan hubungkan ke output Statistics (atau Column Filter jika ingin menyimpan data mentah).
2. Double-click untuk konfigurasi.
3. Di **Output location**, klik Browse dan tentukan path file output (contoh: `C:/Users/nama/Desktop/statistik_polutan.csv`).
4. Centang **Write column header** agar nama kolom ikut tersimpan.
5. Klik **OK** dan execute.

---

## Penjelasan Rumus dan Contoh Perhitungan Node Statistics

Node Statistics menghasilkan sembilan metrik untuk setiap kolom numerik. Berikut penjelasan lengkap tiap metrik beserta rumus matematis dan contoh perhitungan manual menggunakan 5 data NO2 pertama yang valid dari dataset ini:

| Tanggal    | NO2 (mol/m²)     |
|------------|-----------------|
| 2025-08-25 | 0.000020        |
| 2025-08-26 | 0.000035        |
| 2025-08-27 | 0.000086        |
| 2025-08-28 | 0.000010        |
| 2025-08-29 | 0.000034        |

Jumlah data $n = 5$. Setelah diurutkan: **0.000010, 0.000020, 0.000034, 0.000035, 0.000086**

---

### a) Missing Values

Menghitung jumlah baris yang bernilai kosong (`NULL`) pada suatu kolom. Nilai ini penting untuk menentukan strategi penanganan data sebelum pemodelan — apakah perlu interpolasi, imputasi mean, atau penghapusan baris.

$$\text{Missing Values} = \text{jumlah baris dengan nilai NULL pada kolom tersebut}$$

**Contoh (5 data sampel):** Tidak ada nilai NULL pada 5 baris ini → Missing Values = **0**

**Nilai aktual seluruh dataset:**

| Polutan | Missing Values | Persentase |
|---------|---------------|------------|
| NO2     | 176           | 47,6%      |
| CO      | 168           | 45,4%      |
| SO2     | 136           | 36,8%      |

Missing value yang tinggi ini bukan kegagalan sensor, melainkan akibat tutupan awan yang menghalangi pengukuran satelit Sentinel-5P dan gap orbit harian.

---

### b) Minimum & Maximum

Nilai terkecil dan terbesar dalam kolom. Digunakan untuk mendeteksi outlier atau nilai tidak wajar, seperti konsentrasi polutan yang negatif.

$$\text{Min} = \min(x_1, x_2, \dots, x_n) \qquad \text{Max} = \max(x_1, x_2, \dots, x_n)$$

**Contoh (5 data sampel NO2):**

$$\text{Min} = 0.000010 \text{ mol/m}^2 \qquad \text{Max} = 0.000086 \text{ mol/m}^2$$

**Nilai aktual seluruh dataset:**

| Polutan | Min          | Max          |
|---------|-------------|-------------|
| NO2     | -0.000011   | 0.000147    |
| CO      | 0.020132    | 0.044651    |
| SO2     | -0.002125   | 0.001092    |

NO2 dan SO2 memiliki nilai minimum negatif yang secara fisik tidak mungkin terjadi. Ini adalah noise retrieval algoritma TROPOMI pada hari dengan konsentrasi gas yang sangat rendah.

---

### c) Mean (Rata-rata)

Nilai rata-rata aritmatika dari seluruh data valid. Mean sensitif terhadap outlier karena nilai ekstrem menarik rata-rata ke arahnya.

$$\bar{x} = \frac{1}{n}\sum_{i=1}^{n} x_i$$

**Contoh (5 data sampel NO2):**

$$\bar{x} = \frac{0.000020 + 0.000035 + 0.000086 + 0.000010 + 0.000034}{5} = \frac{0.000185}{5} = 0.000037 \text{ mol/m}^2$$

**Nilai aktual seluruh dataset:**

| Polutan | Mean        |
|---------|------------|
| NO2     | 0.000035   |
| CO      | 0.028868   |
| SO2     | 0.000064   |

---

### d) Median (Nilai Tengah)

Nilai tengah setelah data diurutkan dari kecil ke besar. Median lebih robust terhadap outlier dibanding mean karena posisinya tidak terpengaruh nilai ekstrem di ujung distribusi.

$$\text{Median} = x_{\left(\frac{n+1}{2}\right)} \quad \text{untuk } n \text{ ganjil}$$

**Contoh (5 data sampel NO2):**

Data terurut: 0.000010, 0.000020, **0.000034**, 0.000035, 0.000086

Posisi tengah = $\frac{5+1}{2} = 3$ → nilai ke-3 = **0.000034 mol/m²**

**Nilai aktual seluruh dataset:**

| Polutan | Mean        | Median      | Selisih     |
|---------|------------|------------|------------|
| NO2     | 0.000035   | 0.000028   | 0.000007   |
| CO      | 0.028868   | 0.029059   | 0.000191   |
| SO2     | 0.000064   | 0.000064   | 0.000000   |

Selisih mean-median NO2 yang positif mengkonfirmasi distribusi right-skewed: beberapa hari dengan NO2 sangat tinggi menarik mean ke atas dari median.

---

### e) Overall Sum

Total penjumlahan seluruh nilai valid dalam kolom. Berguna untuk menghitung total beban polutan kumulatif selama periode pengamatan.

$$\text{Sum} = \sum_{i=1}^{n} x_i$$

**Contoh (5 data sampel NO2):**

$$\text{Sum} = 0.000020 + 0.000035 + 0.000086 + 0.000010 + 0.000034 = 0.000185 \text{ mol/m}^2$$

**Nilai aktual seluruh dataset:**

| Polutan | Sum        |
|---------|-----------|
| NO2     | 0.006705  |
| CO      | 5.831238  |
| SO2     | 0.014999  |

---

### f) Variance (Varians)

Mengukur seberapa jauh data menyebar dari nilai rata-ratanya. Semakin besar varians, semakin tidak konsisten konsentrasi polutan dari hari ke hari. Rumus menggunakan pembagi $n-1$ (varians sampel) karena data ini adalah sampel dari kondisi atmosfer yang sebenarnya.

$$s^2 = \frac{1}{n-1}\sum_{i=1}^{n}(x_i - \bar{x})^2$$

**Contoh (5 data sampel NO2, $\bar{x} = 0.000037$):**

| $x_i$     | $x_i - \bar{x}$  | $(x_i - \bar{x})^2$         |
|-----------|-----------------|----------------------------|
| 0.000020  | -0.000017       | $2.89 \times 10^{-10}$     |
| 0.000035  | -0.000002       | $4.00 \times 10^{-12}$     |
| 0.000086  | +0.000049       | $2.401 \times 10^{-9}$     |
| 0.000010  | -0.000027       | $7.29 \times 10^{-10}$     |
| 0.000034  | -0.000003       | $9.00 \times 10^{-12}$     |

$$s^2 = \frac{3.432 \times 10^{-9}}{5-1} = 8.58 \times 10^{-10} \text{ (mol/m}^2)^2$$

**Nilai aktual seluruh dataset:**

| Polutan | Variance              |
|---------|----------------------|
| NO2     | $5.31 \times 10^{-10}$ |
| CO      | $1.47 \times 10^{-5}$  |
| SO2     | $1.04 \times 10^{-7}$  |

---

### g) Standard Deviation (Simpangan Baku)

Akar kuadrat dari varians. Satuannya sama dengan satuan data asli (mol/m²), sehingga lebih mudah diinterpretasikan: nilai ini menyatakan seberapa jauh rata-rata penyimpangan tiap hari dari nilai rata-rata tahunan.

$$s = \sqrt{s^2}$$

**Contoh (5 data sampel NO2):**

$$s = \sqrt{8.58 \times 10^{-10}} = 0.0000293 \text{ mol/m}^2 = 2.93 \times 10^{-5} \text{ mol/m}^2$$

Artinya, secara rata-rata nilai NO2 dalam 5 hari sampel ini menyimpang sekitar $2.93 \times 10^{-5}$ mol/m² dari rata-ratanya.

**Nilai aktual seluruh dataset:**

| Polutan | Std Dev    | Interpretasi                                   |
|---------|-----------|-----------------------------------------------|
| NO2     | 0.000023  | Fluktuasi harian sedang relatif terhadap mean |
| CO      | 0.003832  | Variasi paling kecil secara relatif (CV ~13%) |
| SO2     | 0.000322  | Variasi besar karena dominasi nilai negatif   |

---

### h) Skewness (Kemencengan Distribusi)

Mengukur simetri sebaran data. Skewness = 0 berarti distribusi simetris sempurna. Skewness positif (right-skewed) berarti ekor distribusi memanjang ke kanan — banyak hari dengan nilai rendah, sedikit hari dengan lonjakan tinggi. Skewness negatif (left-skewed) berarti sebaliknya.

$$\text{Skewness} = \frac{\frac{1}{n}\sum_{i=1}^{n}(x_i-\bar{x})^3}{s^3}$$

**Contoh (5 data sampel NO2):** Skewness $\approx 1.03$ (right-skewed ringan karena nilai 0.000086 jauh di atas yang lain)

**Nilai aktual seluruh dataset:**

| Polutan | Skewness | Interpretasi                                             |
|---------|---------|----------------------------------------------------------|
| NO2     | 1.67    | Right-skewed kuat — beberapa hari polusi sangat tinggi   |
| CO      | 0.23    | Hampir simetris — konsentrasi CO relatif stabil          |
| SO2     | -1.05   | Left-skewed — ditarik oleh banyaknya nilai negatif noise |

---

### i) Kurtosis (Keruncingan Distribusi)

Mengukur seberapa "runcing" puncak distribusi dibanding distribusi normal. Kurtosis > 0 berarti distribusi lebih runcing dari normal dengan ekor lebih tebal (banyak nilai ekstrem). Kurtosis < 0 berarti distribusi lebih landai dan merata.

$$\text{Kurtosis} = \frac{\frac{1}{n}\sum_{i=1}^{n}(x_i-\bar{x})^4}{s^4} - 3$$

**Contoh (5 data sampel NO2):** Kurtosis $\approx -0.29$ (distribusi sedikit lebih landai dari normal)

**Nilai aktual seluruh dataset:**

| Polutan | Kurtosis | Interpretasi                                                        |
|---------|---------|---------------------------------------------------------------------|
| NO2     | 3.98    | Distribusi sangat runcing — ada beberapa hari outlier ekstrem       |
| CO      | 0.74    | Sedikit lebih runcing dari normal — distribusi cukup terpusat       |
| SO2     | 9.29    | Sangat runcing dan berekor tebal karena campuran noise dan nilai nyata |

---

### Tabel Ringkasan Statistik Aktual (Seluruh Dataset)

| Fitur              | NO2              | CO           | SO2              |
|--------------------|-----------------|-------------|-----------------|
| Missing Values     | 176 (47,6%)     | 168 (45,4%) | 136 (36,8%)     |
| Minimum            | -0.000011       | 0.020132    | -0.002125       |
| Maximum            | 0.000147        | 0.044651    | 0.001092        |
| Mean               | 0.000035        | 0.028868    | 0.000064        |
| Median             | 0.000028        | 0.029059    | 0.000064        |
| Overall Sum        | 0.006705        | 5.831238    | 0.014999        |
| Variance           | 5.31e-10        | 1.47e-05    | 1.04e-07        |
| Standard Deviation | 0.000023        | 0.003832    | 0.000322        |
| Skewness           | 1.67            | 0.23        | -1.05           |
| Kurtosis           | 3.98            | 0.74        | 9.29            |

---

## Kesimpulan

Data polutan dari tiga file CSV berhasil digabung dan diunggah ke cloud Aiven PostgreSQL menggunakan Python dengan total 370 baris. Koneksi dari KNIME ke Aiven dibangun melalui empat node: PostgreSQL Connector (dengan `sslmode=require`), DB Query Reader, Column Filter, dan Statistics. Node Statistics menghasilkan sembilan metrik statistik deskriptif yang memberi gambaran menyeluruh tentang distribusi NO2, CO, dan SO2 di wilayah Kamal-UTM. Dari hasil ini terlihat bahwa CO memiliki distribusi paling stabil (skewness 0.23), NO2 right-skewed kuat akibat beberapa hari dengan emisi tinggi (skewness 1.67), dan SO2 didominasi noise retrieval TROPOMI yang menghasilkan banyak nilai negatif (kurtosis 9.29).