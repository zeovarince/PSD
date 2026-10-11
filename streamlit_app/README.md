# 🛰️ Sistem Informasi LULC Jawa Timur — Web Streamlit

Web aplikasi visual interaktif untuk tugas **UTS Sistem Informasi Geografis (SIG)** yang menyajikan hasil klasifikasi tutupan dan penggunaan lahan (*Land Use / Land Cover* - LULC) Provinsi Jawa Timur ke dalam 6 kelas berdasarkan citra satelit **Sentinel-2A Level-2A** dari **Copernicus Data Space Ecosystem**.

Aplikasi mengadopsi **Mercury Design System** (Dark mode alpina, kanvas Onyx `#171721`, kartu Graphite `#1e1e2a`, teks Ivory `#ededf3`, dan aksen Cobalt `#5266eb`).

---

## 📌 Fitur Utama

1. **Halaman 1: Data Understanding**
   - Latar belakang, tujuan, dan 4 pilar kebijakan (alih fungsi sawah, mangrove, danau, dan tata ruang).
   - Batas wilayah studi (AOI Jawa Timur).
   - Acuan standar klasifikasi nasional SNI 7645-1:2014 dan KLHK.
   - Deskripsi 10 kanal spektral Sentinel-2A dan formula 8 indeks spektral matematis (NDVI, NDWI, MNDWI, NDBI, NDRE, EVI, SAVI, BSI) dengan LaTeX.
   - Filosofi komparasi dua basis observasi (*Polygon vs Pixel*).

2. **Halaman 2 & 3: Basis Polygon & Basis Pixel**
   Struktur sub-bagian identik menggunakan navigasi segmented control non-tabs:
   - **A. Pemrosesan Data:** Pipeline pra-pengolahan geospasial, sanitasi topologi, sampling terstrata, dan ringkasan dimensi dataset.
   - **B. Split & Model:** Rekapitulasi partisi 70% Training, 15% Validation, 15% Testing per kelas, strategi pencegahan *data leakage* autokorelasi spasial, dan *StandardScaler*.
   - **C. Model 1 (Gaussian Naive Bayes):** Teori probabilistik, kurva tuning `var_smoothing`, kartu metrik pengujian, confusion matrix heatmap, classification report per kelas, embed peta interaktif Folium, dan estimasi luas.
   - **D. Model 2 (KNN):** Algoritma jarak Euclidean, kurva tuning nilai $k$, kartu metrik pengujian, confusion matrix heatmap, classification report per kelas, embed peta interaktif Folium, dan estimasi luas.
   - **E. Perbandingan & Evaluasi:** Banner model terbaik dinamis dari data, tabel komparasi validasi dan pengujian berdampingan, bar chart perbandingan metrik, komparasi luas wilayah, dan catatan keterbatasan kritis.

---

## 📂 Struktur Project

```
streamlit_app/
├── .streamlit/
│   └── config.toml               # Tema Mercury Dark (#171721, #1e1e2a, #5266eb)
├── assets/
│   ├── polygon/
│   │   ├── results.json          # Hasil ekspor metrik evaluasi & tuning poligon
│   │   ├── peta_gnb.html         # Peta interaktif Folium GNB poligon
│   │   └── peta_knn.html         # Peta interaktif Folium KNN poligon
│   └── pixel/
│       ├── results.json          # Hasil ekspor metrik evaluasi & tuning piksel
│       ├── peta_pixel_gnb.html   # Peta interaktif Folium GNB piksel
│       └── peta_pixel_knn.html   # Peta interaktif Folium KNN piksel
├── content/
│   ├── __init__.py
│   ├── static_text.py            # Metadata, formula LaTeX, tabel SNI/KLHK, kebijakan
│   └── style.css                 # Custom CSS Mercury Design Tokens
├── pages_/
│   ├── __init__.py
│   ├── data_understanding.py     # Renderer Halaman 1
│   └── basis.py                  # Renderer Halaman 2 & 3 (Polygon dan Pixel)
├── components_ui.py              # Komponen visual Plotly, kartu metrik, tabel, banner
├── data_loader.py                # Modul pembaca assets dengan @st.cache_data
├── app.py                        # Entry point aplikasi Streamlit
├── requirements.txt              # Dependensi ringan (streamlit, pandas, numpy, plotly)
└── README.md
```

---

## 🚀 Cara Menjalankan secara Lokal

1. **Pastikan berada di folder project:**
   ```bash
   cd c:\Users\ARIEL\OneDrive\Documents\PSD\streamlit_app
   ```

2. **Pasang dependensi:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Jalankan Streamlit:**
   ```bash
   streamlit run app.py
   ```
   Aplikasi akan otomatis terbuka di browser pada alamat `http://localhost:8501`.

---

## 🔄 Cara Memperbarui Data Hasil Ekspor Notebook

Jika Anda menjalankan iterasi baru di notebook `klasifikasi_polygon_jatim.ipynb` atau `klasifikasi_pixel_jatim.ipynb`:
1. Eksekusi sel ekspor `export_results.py` di akhir notebook.
2. Salin file hasil `results.json` dan file peta `peta_*.html` ke folder yang sesuai:
   - Untuk poligon: letakkan di `assets/polygon/`
   - Untuk piksel: letakkan di `assets/pixel/`
3. Aplikasi web akan otomatis mendeteksi dan memperbarui seluruh metrik, tabel, dan grafik tanpa perlu mengubah kode aplikasi.

---

## ☁️ Deploy ke Streamlit Community Cloud

1. Buat repository baru di GitHub (misal: `lulc-jatim-sig`).
2. Push isi folder `streamlit_app/` ini ke branch utama repository.
3. Buka [share.streamlit.io](https://share.streamlit.io) dan login dengan akun GitHub Anda.
4. Klik **New app**, pilih repository, branch, dan tentukan `Main file path` ke `app.py`.
5. Klik **Deploy**! Aplikasi Anda kini dapat diakses secara publik oleh dosen dan mahasiswa.
