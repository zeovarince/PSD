# Laporan Analisis LULC (Land Use and Land Cover) Jawa Timur

## 1. Data Understanding & Tujuan Analisis

**Tujuan Analisis:**
Tujuan utama dari analisis Land Use and Land Cover (LULC) ini adalah untuk memetakan dan mengklasifikasikan penutupan dan penggunaan lahan di wilayah Jawa Timur menjadi enam kelas utama berdasarkan citra satelit Sentinel-2A. Pemetaan ini sangat penting untuk perencanaan tata ruang, pemantauan degradasi lingkungan, pengelolaan sumber daya air, serta analisis dampak perubahan iklim dan urbanisasi.

**Referensi Standar di Indonesia:**
Acuan utama klasifikasi penutup lahan di Indonesia didasarkan pada **SNI 7645-1:2014** (Klasifikasi Penutup Lahan - Bagian 1: Skala 1:1.000.000 hingga 1:250.000) dan **SNI 7645:2010**. SNI ini mendefinisikan kelas-kelas penutup lahan yang dapat disesuaikan dengan skala resolusi satelit yang digunakan. Dalam proyek ini, kita mengambil beberapa kelas penting yang relevan dengan kondisi Jawa Timur:
1. Sawah (Pertanian Lahan Basah)
2. Bangunan (Lahan Terbangun / Permukiman)
3. Mangrove (Hutan Bakau)
4. Lahan Hijau (Hutan / Vegetasi Kerapatan Tinggi)
5. Perairan Terbuka (Laut)
6. Danau (Perairan Darat / Ranu)

## 2. Collecting Data

Data dikumpulkan melalui proses digitasi poligon (Region of Interest / ROI) menggunakan perangkat lunak GIS pada wilayah Jawa Timur. Hasil digitasi disimpan dalam format *shapefile* (`.shp`) yang mencakup 6 folder kelas di atas.
Untuk mengekstraksi nilai piksel dari poligon-poligon ini, kita menggunakan layanan cloud **Google Earth Engine (GEE)** dengan koleksi citra `COPERNICUS/S2_SR_HARMONIZED` (Sentinel-2A Surface Reflectance) yang memiliki resolusi spasial hingga 10 meter.

- **Jumlah Kelas:** 6 Kelas
- **Jumlah Data Training dan Testing:** (Secara dinamis diekstraksi dari piksel poligon, biasanya dibagi dengan rasio 70% Training dan 30% Testing atau 80:20). Jumlah titik piksel bergantung pada luasan hasil digitasi.

## 3. Deskripsi Band Sentinel-2A

Citra Sentinel-2A memiliki beberapa saluran (band) yang merespon panjang gelombang tertentu, yang sangat berguna untuk membedakan karakteristik objek di permukaan bumi:
- **Band 2 (Blue - 490 nm, 10m):** Sensitif terhadap aerosol atmosfer dan air jernih, berguna untuk pemetaan badan air pesisir (laut).
- **Band 3 (Green - 560 nm, 10m):** Sensitif terhadap puncak reflektansi hijau vegetasi, berguna untuk membedakan jenis vegetasi.
- **Band 4 (Red - 665 nm, 10m):** Menyerap klorofil, sangat penting untuk menghitung indeks vegetasi (NDVI).
- **Band 8 (NIR - 842 nm, 10m):** Memantulkan struktur daun dan biomasa. Membedakan antara vegetasi (reflektansi tinggi) dan air (reflektansi sangat rendah).
- **Band 11 (SWIR 1 - 1610 nm, 20m):** Berguna untuk mengukur kelembaban tanah dan kanopi tanaman, serta menembus asap tipis.
- **Band 12 (SWIR 2 - 2190 nm, 20m):** Sangat sensitif terhadap air dalam tanah dan batuan. Berguna untuk membedakan lahan terbangun, tanah kosong, dan badan air.

## 4. Ekstraksi Fitur (Spectral Indices) dan Rumus

Selain nilai pantulan asli (reflectance) dari tiap band, indeks spektral diekstraksi untuk memperjelas batas antar kelas:

1. **NDVI (Normalized Difference Vegetation Index):**
   Memisahkan lahan bervegetasi dengan tanah/bangunan.
   $$ NDVI = \frac{(B8 - B4)}{(B8 + B4)} $$

2. **NDWI (Normalized Difference Water Index):**
   Mendeteksi badan air dan wilayah tergenang.
   $$ NDWI = \frac{(B3 - B8)}{(B3 + B8)} $$

3. **MNDWI (Modified Normalized Difference Water Index):**
   Modifikasi NDWI menggunakan SWIR untuk lebih baik menekan sinyal dari lahan terbangun saat mendeteksi air.
   $$ MNDWI = \frac{(B3 - B11)}{(B3 + B11)} $$

4. **NDBI (Normalized Difference Built-up Index):**
   Menonjolkan area terbangun / bangunan / permukiman.
   $$ NDBI = \frac{(B11 - B8)}{(B11 + B8)} $$

5. **EVI (Enhanced Vegetation Index):**
   Mendeteksi vegetasi tinggi (seperti hutan/mangrove) dengan mengoreksi pengaruh atmosfer dan background tanah.
   $$ EVI = 2.5 \times \frac{(B8 - B4)}{(B8 + 6 \times B4 - 7.5 \times B2 + 1)} $$

## 5. Pemodelan Machine Learning

Eksperimen menggunakan **Random Forest** atau **XGBoost Classifier**. XGBoost (Extreme Gradient Boosting) seringkali menghasilkan akurasi klasifikasi tertinggi pada data penginderaan jauh berdimensi tinggi karena mampu menangani multikolinearitas antar band dan interaksi non-linear indeks spektral dengan sangat baik. Penggunaan XGBoost dipadukan dengan teknik validasi silang akan dievaluasi melalui *Confusion Matrix*, dan akurasi (F1-Score, Overall Accuracy).
