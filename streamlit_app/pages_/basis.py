"""
Modul generik untuk merender halaman Basis Polygon dan Basis Pixel.
Menjamin struktur yang identik, modular, dinamis tanpa hardcode, 
dan mengimplementasikan sub-navigasi horizontal non-tabs untuk efisiensi render peta Folium.
"""

from __future__ import annotations
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os

from data_loader import load_results, load_map_html, list_figures
from components_ui import (
    render_metric_row, render_tuning_curve, render_confusion_matrix,
    render_classification_report_table, render_comparison_bar_chart,
    render_dataset_dist_chart, render_winner_banner, render_metric_card,
    render_interactive_map
)
from content.static_text import (
    WARNA_KELAS, KETERBATASAN, IMPLIKASI_KEBIJAKAN, PERBEDAAN_BASIS
)

def render_basis(basis: str):
    """
    Fungsi utama perender basis ('polygon' atau 'pixel').
    """
    is_poly = (basis.lower() == "polygon")
    basis_title = "Basis Polygon" if is_poly else "Basis Pixel"
    pill_label = "Model Segmentasi Bidang Lahan" if is_poly else "Model Sampling Spektral Titik"
    
    st.markdown(f'<span class="mercury-pill mercury-pill-cobalt">{pill_label}</span>', unsafe_allow_html=True)
    st.title(f"Klasifikasi LULC Jawa Timur — {basis_title}")
    
    lead_text = (
        "Analisis tutupan lahan di mana unit observasi adalah satu poligon utuh (1 titik spektral representatif "
        "per poligon) untuk memetakan kepatuhan zonasi bidang lahan."
        if is_poly else
        "Analisis tutupan lahan di mana unit observasi adalah titik piksel acak Sentinel-2 (resolusi 10 m) dengan "
        "skema sampling terstrata per-poligon untuk mencegah kebocoran data spasial."
    )
    st.markdown(f'<p class="mercury-lead">{lead_text}</p>', unsafe_allow_html=True)
    
    # Load data from assets/<basis>/results.json
    data = load_results(basis)
    if data is None:
        st.warning(f"File hasil 'assets/{basis}/results.json' belum ditemukan. Silakan jalankan sel ekspor di notebook atau periksa folder assets.")
        return
        
    dataset_info = data.get("dataset", {})
    models_info = data.get("models", {})
    model_nb = models_info.get("nb", {})
    model_knn = models_info.get("knn", {})
    ambang = data.get("ambang", {"akurasi": 85.0, "kappa": 0.80})
    
    # Sub-navigasi horizontal menggunakan st.radio (horizontal) / st.segmented_control
    # Menghindari st.tabs agar iframe peta Folium yang berat hanya dirender saat sub-bagian C atau D aktif!
    sub_menus = [
        "A. Pemrosesan Data",
        "B. Split & Model",
        "C. Model 1: Naive Bayes",
        "D. Model 2: KNN",
        "E. Perbandingan & Evaluasi"
    ]
    
    st.markdown("<div style='margin-bottom: 8px; color:#c3c3cc; font-size:0.85rem; font-weight:500;'>ALUR TAHAPAN ANALISIS:</div>", unsafe_allow_html=True)
    try:
        # Streamlit >= 1.36 memiliki st.segmented_control
        selected_sub = st.segmented_control("Tahapan Analisis", sub_menus, default=sub_menus[0], label_visibility="collapsed")
    except Exception:
        selected_sub = st.radio("Tahapan Analisis", sub_menus, horizontal=True, label_visibility="collapsed")
        
    st.markdown("<hr style='border:0; border-top:1px solid rgba(226,227,237,0.1); margin:14px 0 24px 0;'>", unsafe_allow_html=True)
    
    # =========================================================================
    # SUB A: PEMROSESAN DATA
    # =========================================================================
    if selected_sub == "A. Pemrosesan Data":
        st.markdown(f"## Tahap A — Pemrosesan Data ({basis_title})")
        
        # Penjelasan Alur Pemrosesan
        if is_poly:
            st.markdown("""
            <div class="mercury-card">
                <div class="mercury-card-title">⚙️ Rangkaian Pipeline Data Poligon</div>
                <ol style="color:#ededf3; font-size:0.92rem; line-height:1.8; margin-left:18px;">
                    <li><strong>Pembacaan Shapefile:</strong> Memuat 6 folder shapefile poligon hasil digitasi lapangan (sawah, bangunan, mangrove, lahanhijau, laut, danau).</li>
                    <li><strong>Normalisasi Geospasial:</strong> Penyeragaman Coordinate Reference System (CRS) ke <code>EPSG:4326 (WGS 84)</code>.</li>
                    <li><strong>Sanitasi Geometri:</strong> Perbaikan topologi poligon (<code>buffer(0)</code>) dan pemotongan (clipping) tepat ke AOI Jawa Timur.</li>
                    <li><strong>Penentuan Titik Representatif:</strong> Pengambilan titik representatif (<code>representative_point()</code>) di dalam interior poligon untuk menghindari titik luar poligon cekung.</li>
                    <li><strong>Ekstraksi Reflektansi BOA:</strong> Ekstraksi 10 band Sentinel-2A dan perhitungan 8 indeks spektral pada titik centroid poligon.</li>
                    <li><strong>Validasi Kualitas:</strong> Pembersihan baris mengandung nilai <code>NaN</code>, <code>Inf</code>, atau tutupan awan.</li>
                </ol>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="mercury-card">
                <div class="mercury-card-title">⚙️ Rangkaian Pipeline Sampling Piksel</div>
                <ol style="color:#ededf3; font-size:0.92rem; line-height:1.8; margin-left:18px;">
                    <li><strong>Pembacaan Poligon Induk:</strong> Memuat seluruh layer poligon referensi 6 kelas dan clip ke AOI Jawa Timur.</li>
                    <li><strong>Sampling Titik Acak Terdistribusi:</strong> Menghasilkan titik acak di dalam poligon dengan kuota terkontrol:
                        <ul style="color:#c3c3cc; margin-top:4px;">
                            <li><code>N_PER_CLASS = 1500</code>: Target sampel piksel seimbang per kelas tutupan lahan.</li>
                            <li><code>MAX_PER_POLY = 150</code>: Batas maksimum titik per poligon guna menghindari dominasi satu poligon raksasa.</li>
                            <li>Jatah seimbang proporsional dialokasikan ke tiap poligon berdasarkan luasan.</li>
                        </ul>
                    </li>
                    <li><strong>Deduplikasi Spasial:</strong> Titik acak yang jatuh pada piksel Sentinel-2 10 m yang sama dibuang untuk mencegah duplikasi data.</li>
                    <li><strong>Ekstraksi 18 Fitur:</strong> 10 band BOA L2A dan 8 indeks spektral dihitung untuk setiap koordinat piksel.</li>
                    <li><strong>Pemisahan Metadata:</strong> Setiap piksel membawa atribut <code>poligon_id</code> untuk mengunci pembagian data anti-data leakage.</li>
                </ol>
            </div>
            """, unsafe_allow_html=True)
            
        # Ringkasan Dataset
        st.markdown("### Ringkasan Dimensi Dataset")
        c1, c2, c3 = st.columns(3)
        with c1:
            render_metric_card("Total Sampel Data", f"{dataset_info.get('n_total', 0):,}", f"Unit: {'Poligon' if is_poly else 'Piksel'}")
        with c2:
            render_metric_card("Jumlah Kelas", f"{dataset_info.get('n_classes', 6)} Kelas", "SNI 7645-1:2014")
        with c3:
            render_metric_card("Fitur Spektral", f"{len(dataset_info.get('features', []))} Fitur", "10 Band + 8 Indeks")
            
        # Distribusi Sampel per Kelas
        st.markdown("### Distribusi Sampel per Kelas")
        split_per_class = dataset_info.get("split_per_class", [])
        if split_per_class:
            c_dist1, c_dist2 = st.columns([1, 1.2])
            with c_dist1:
                df_sp = pd.DataFrame(split_per_class)
                st.dataframe(df_sp, hide_index=True, use_container_width=True)
            with c_dist2:
                render_dataset_dist_chart(split_per_class)
                
        # Gambar PNG Hasil Notebook (jika tersedia di assets)
        figs = list_figures(basis)
        if figs:
            st.markdown("### Visualisasi Eksplorasi Spektral dari Notebook")
            for fig_path in figs:
                fname = os.path.basename(fig_path)
                st.image(fig_path, caption=fname, use_column_width=True)

    # =========================================================================
    # SUB B: SPLIT & MODEL
    # =========================================================================
    elif selected_sub == "B. Split & Model":
        st.markdown(f"## Tahap B — Pembagian Data & Konfigurasi Model ({basis_title})")
        
        # Metodologi Pembagian Data
        st.markdown("""
        <div class="mercury-card">
            <div class="mercury-card-title">📊 Skema Partisi Data (Train / Val / Test)</div>
        """, unsafe_allow_html=True)
        
        if is_poly:
            st.markdown("""
            <p style="color:#ededf3; font-size:0.92rem; line-height:1.7;">
                Pada <strong>Basis Polygon</strong>, dataset dibagi menggunakan metode <strong>Stratified Random Split</strong>:
            </p>
            <ul style="color:#c3c3cc; font-size:0.9rem; line-height:1.7;">
                <li><strong>Training Set (70%):</strong> Digunakan untuk melatih parameter model dan kurva probabilitas.</li>
                <li><strong>Validation Set (15%):</strong> Digunakan untuk tuning hyperparameter (<code>var_smoothing</code> pada Naive Bayes dan <code>k</code> pada KNN).</li>
                <li><strong>Testing Set (15%):</strong> Data evaluasi independen yang belum pernah dilihat model untuk mengukur generalisasi akhir.</li>
            </ul>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <p style="color:#ededf3; font-size:0.92rem; line-height:1.7;">
                Pada <strong>Basis Pixel</strong>, pemisahan dilakukan secara ketat <strong>Per-Poligon (Grouped Stratified)</strong>:
            </p>
            <ul style="color:#c3c3cc; font-size:0.9rem; line-height:1.7;">
                <li><strong>Pencegahan Kebocoran Data (Data Leakage):</strong> Piksel-piksel yang berada di dalam satu poligon yang sama memiliki autokorelasi spasial tinggi. Jika piksel dari poligon yang sama terbagi ke data latih dan data uji, akurasi akan mengalami inflasi semu (overfitting spasial).</li>
                <li>Seluruh piksel dari suatu poligon hanya boleh masuk ke satu partisi (100% latih, 100% validasi, atau 100% uji).</li>
            </ul>
            </div>
            """, unsafe_allow_html=True)
            
        # Tabel Split Aktual
        st.markdown("### Komposisi Partisi Aktual per Kelas")
        split_per_class = dataset_info.get("split_per_class", [])
        if split_per_class:
            df_split = pd.DataFrame(split_per_class)
            st.dataframe(df_split, hide_index=True, use_container_width=True)
            
        split_tot = dataset_info.get("split_total", {})
        c_s1, c_s2, c_s3 = st.columns(3)
        n_all = dataset_info.get("n_total", 1)
        with c_s1:
            n_tr = split_tot.get("train", 0)
            render_metric_card("Training Set (70%)", f"{n_tr:,}", f"{(n_tr/n_all)*100:.1f}% dari total")
        with c_s2:
            n_va = split_tot.get("val", 0)
            render_metric_card("Validation Set (15%)", f"{n_va:,}", f"{(n_va/n_all)*100:.1f}% dari total")
        with c_s3:
            n_te = split_tot.get("test", 0)
            render_metric_card("Testing Set (15%)", f"{n_te:,}", f"{(n_te/n_all)*100:.1f}% dari total")
            
        # Penskalaan Fitur StandardScaler
        st.markdown("### Penskalaan Fitur (StandardScaler)")
        st.markdown("""
        Fitur spektral memiliki rentang nilai yang bervariasi (band reflektansi berkisar 0–1, sedangkan indeks seperti NDBI dapat bernilai negatif).
        Model berbasis jarak Euclidean (KNN) mewajibkan penskalaan fitur:
        """)
        st.latex(r"z = \frac{x - \mu}{\sigma}")
        st.markdown("""
        <p style="color:#c3c3cc; font-size:0.88rem;">
            Penskalaan dihitung (<code>fit</code>) <strong>hanya pada Training Set</strong>, lalu parameter mean ($\mu$) 
            dan standar deviasi ($\sigma$) tersebut ditransformasikan ke Validation dan Testing Set untuk mencegah kebocoran informasi.
        </p>
        """, unsafe_allow_html=True)
        
        # Ringkasan Konfigurasi Model
        st.markdown("### Konfigurasi Model yang Diuji")
        model_rows = [
            {
                "Model": "Gaussian Naive Bayes",
                "Tipe": "Probabilistik Parametrik",
                "Hyperparameter Disetel": "var_smoothing",
                "Rentang Kandidat": "12 kandidat logaritmik (1e-12 hingga 1e-1)",
                "Parameter Terbaik": str(model_nb.get("best_params", {}))
            },
            {
                "Model": "K-Nearest Neighbors (KNN)",
                "Tipe": "Berbasis Jarak / Instans Non-parametrik",
                "Hyperparameter Disetel": "n_neighbors (k), bobot jarak",
                "Rentang Kandidat": "k ∈ [1, 3, 5, 7, 9, 11, 15, 21, 31]",
                "Parameter Terbaik": str(model_knn.get("best_params", {}))
            }
        ]
        st.dataframe(pd.DataFrame(model_rows), hide_index=True, use_container_width=True)

    # =========================================================================
    # SUB C: MODEL 1 - GAUSSIAN NAIVE BAYES
    # =========================================================================
    elif selected_sub == "C. Model 1: Naive Bayes":
        st.markdown(f"## Tahap C — Model 1: Gaussian Naive Bayes ({basis_title})")
        
        # 1. Cara Kerja & Rumus
        st.markdown("""
        <div class="mercury-card">
            <div class="mercury-card-title">📐 Cara Kerja Gaussian Naive Bayes</div>
            <p style="color:#ededf3; font-size:0.92rem; line-height:1.6;">
                Gaussian Naive Bayes menghitung probabilitas posterior bahwa sebuah sampel observasi $x$ dengan $d = 18$ fitur 
                termasuk dalam kelas $c \in \{1,\dots,6\}$, dengan mengasumsikan distribusi normal dan independensi bersyarat antar fitur:
            </p>
        """, unsafe_allow_html=True)
        st.latex(r"P(c \mid x) \propto P(c) \prod_{j=1}^{d} \frac{1}{\sqrt{2\pi\sigma_{cj}^2}} \exp\left(-\frac{(x_j - \mu_{cj})^2}{2\sigma_{cj}^2}\right)")
        st.markdown(f"""
            <p style="color:#c3c3cc; font-size:0.88rem; margin-top:8px;">
                Hyperparameter <code>var_smoothing</code> menambahkan konstanta kestabilan numerik terhadap variansi terbesar fitur:
                <strong>{model_nb.get('best_params', {})}</strong>.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # 2. Kurva Tuning Hyperparameter
        st.markdown("### Tuning Hyperparameter `var_smoothing`")
        render_tuning_curve(model_nb.get("tuning", {}), "nb")
        
        # 3. Kartu Metrik Evaluasi Testing Set
        st.markdown("### Metrik Kinerja Pengujian Akhir (Testing Set)")
        render_metric_row(model_nb.get("test", {}), model_nb.get("val", {}))
        
        # 4. Confusion Matrix & Classification Report
        st.markdown("### Matriks Konfusi & Laporan Klasifikasi per Kelas")
        c_m1, c_m2 = st.columns([1.1, 1.3])
        with c_m1:
            render_confusion_matrix(model_nb.get("confusion_matrix", {}), "Gaussian Naive Bayes")
        with c_m2:
            render_classification_report_table(model_nb.get("report_per_class", {}))
            
        # 5. Peta Hasil Klasifikasi (Folium Embed)
        st.markdown("### Peta Interaktif Klasifikasi: Gaussian Naive Bayes")
        st.markdown("""
        <p style="color:#c3c3cc; font-size:0.88rem; margin-bottom:12px;">
            Peta Folium resolusi komposit 200 m di Jawa Timur. Anda dapat memperbesar, menggeser, 
            mengganti basemap (Esri Satellite / Google Hybrid), dan menyalakan layer poligon referensi.
        </p>
        """, unsafe_allow_html=True)
        
        map_filename = "peta_gnb.html" if is_poly else "peta_pixel_gnb.html"
        map_rel_path = f"assets/{basis}/{map_filename}"
        render_interactive_map(map_rel_path, f"Gaussian Naive Bayes ({basis_title})")
            
        # 6. Tabel Luas Kelas & Implikasi Kebijakan
        st.markdown("### Estimasi Luas Tutupan Lahan & Implikasi Kebijakan")
        luas_list = model_nb.get("luas_kelas", [])
        if luas_list:
            df_luas = pd.DataFrame(luas_list)
            st.dataframe(df_luas, hide_index=True, use_container_width=True)
            
        st.markdown("#### Analisis Dampak Kebijakan Lahan:")
        for k_nama, imp in IMPLIKASI_KEBIJAKAN.items():
            w_col = WARNA_KELAS.get(k_nama, "#8c9bff")
            st.markdown(
                f'<div style="margin-bottom:8px; font-size:0.9rem; color:#ededf3;">'
                f'<span style="display:inline-block;width:10px;height:10px;border-radius:50%;background-color:{w_col};margin-right:6px;"></span>'
                f'<strong>{k_nama}:</strong> <span style="color:#c3c3cc;">{imp}</span>'
                f'</div>',
                unsafe_allow_html=True
            )

    # =========================================================================
    # SUB D: MODEL 2 - K-NEAREST NEIGHBORS (KNN)
    # =========================================================================
    elif selected_sub == "D. Model 2: KNN":
        st.markdown(f"## Tahap D — Model 2: K-Nearest Neighbors ({basis_title})")
        
        # 1. Cara Kerja & Rumus
        st.markdown("""
        <div class="mercury-card">
            <div class="mercury-card-title">📐 Cara Kerja K-Nearest Neighbors (KNN)</div>
            <p style="color:#ededf3; font-size:0.92rem; line-height:1.6;">
                KNN mengklasifikasikan sampel baru berdasarkan suara mayoritas atau pembobotan jarak terhadap 
                $k$ sampel tetangga terdekat pada ruang 18 fitur yang telah diskalakan (StandardScaler). 
                Jarak antara dua vektor fitur $x$ dan $x'$ dihitung dengan metrik Euclidean:
            </p>
        """, unsafe_allow_html=True)
        st.latex(r"d(x, x') = \sqrt{\sum_{j=1}^{d} (x_j - x'_j)^2}")
        st.markdown(f"""
            <p style="color:#c3c3cc; font-size:0.88rem; margin-top:8px;">
                Hyperparameter optimal terpilih pada Validation Set: 
                <strong>{model_knn.get('best_params', {})}</strong>.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # 2. Kurva Tuning Hyperparameter
        st.markdown("### Tuning Hyperparameter $k$ (Jumlah Tetangga Terdekat)")
        render_tuning_curve(model_knn.get("tuning", {}), "knn")
        
        # 3. Kartu Metrik Evaluasi Testing Set
        st.markdown("### Metrik Kinerja Pengujian Akhir (Testing Set)")
        render_metric_row(model_knn.get("test", {}), model_knn.get("val", {}))
        
        # 4. Confusion Matrix & Classification Report
        st.markdown("### Matriks Konfusi & Laporan Klasifikasi per Kelas")
        c_m1, c_m2 = st.columns([1.1, 1.3])
        with c_m1:
            render_confusion_matrix(model_knn.get("confusion_matrix", {}), "K-Nearest Neighbors")
        with c_m2:
            render_classification_report_table(model_knn.get("report_per_class", {}))
            
        # 5. Peta Hasil Klasifikasi (Folium Embed)
        st.markdown("### Peta Interaktif Klasifikasi: K-Nearest Neighbors")
        st.markdown("""
        <p style="color:#c3c3cc; font-size:0.88rem; margin-bottom:12px;">
            Peta Folium klasifikasi KNN di Jawa Timur. Anda dapat membandingkan batas petak 
            dan konsistensi sebaran piksel terhadap citra satelit Google Hybrid.
        </p>
        """, unsafe_allow_html=True)
        
        map_filename = "peta_knn.html" if is_poly else "peta_pixel_knn.html"
        map_rel_path = f"assets/{basis}/{map_filename}"
        render_interactive_map(map_rel_path, f"K-Nearest Neighbors ({basis_title})")
            
        # 6. Tabel Luas Kelas & Implikasi Kebijakan
        st.markdown("### Estimasi Luas Tutupan Lahan & Implikasi Kebijakan")
        luas_list = model_knn.get("luas_kelas", [])
        if luas_list:
            df_luas = pd.DataFrame(luas_list)
            st.dataframe(df_luas, hide_index=True, use_container_width=True)
            
        st.markdown("#### Analisis Dampak Kebijakan Lahan:")
        for k_nama, imp in IMPLIKASI_KEBIJAKAN.items():
            w_col = WARNA_KELAS.get(k_nama, "#8c9bff")
            st.markdown(
                f'<div style="margin-bottom:8px; font-size:0.9rem; color:#ededf3;">'
                f'<span style="display:inline-block;width:10px;height:10px;border-radius:50%;background-color:{w_col};margin-right:6px;"></span>'
                f'<strong>{k_nama}:</strong> <span style="color:#c3c3cc;">{imp}</span>'
                f'</div>',
                unsafe_allow_html=True
            )

    # =========================================================================
    # SUB E: PERBANDINGAN & EVALUASI DUA MODEL
    # =========================================================================
    elif selected_sub == "E. Perbandingan & Evaluasi":
        st.markdown(f"## Tahap E — Komparasi Model & Kesimpulan ({basis_title})")
        
        # Kalkulasi Pemenang Otomatis dari results.json
        nb_test = model_nb.get("test", {})
        knn_test = model_knn.get("test", {})
        
        acc_nb = nb_test.get("accuracy", 0.0) * 100
        acc_knn = knn_test.get("accuracy", 0.0) * 100
        kappa_nb = nb_test.get("kappa", 0.0)
        kappa_knn = knn_test.get("kappa", 0.0)
        
        if acc_knn > acc_nb or (acc_knn == acc_nb and kappa_knn > kappa_nb):
            winner_name = model_knn.get("nama", "K-Nearest Neighbors")
            best_acc = acc_knn
            best_kappa = kappa_knn
            margin = acc_knn - acc_nb
            other_name = model_nb.get("nama", "Gaussian Naive Bayes")
            alasan_winner = (
                "KNN unggul karena algoritma berbasis instans non-parametrik tidak bergantung pada asumsi "
                "distribusi normal atau independensi fitur. KNN mampu memisahkan interaksi multivariat "
                "antar-band spektral secara fleksibel."
            )
        else:
            winner_name = model_nb.get("nama", "Gaussian Naive Bayes")
            best_acc = acc_nb
            best_kappa = kappa_nb
            margin = acc_nb - acc_knn
            other_name = model_knn.get("nama", "K-Nearest Neighbors")
            alasan_winner = (
                "Gaussian Naive Bayes memiliki jumlah parameter yang sangat sedikit dan teratur, "
                "sehingga bekerja lebih stabil pada dataset poligon homogen tanpa terpengaruh derau lokal tetangga terdekat."
            )
            
        render_winner_banner(winner_name, best_acc, best_kappa, margin, other_name, alasan_winner)
        
        # 1. Tabel Perbandingan Metrik Lengkap
        st.markdown("### 1. Tabel Komparasi Kinerja Validasi & Pengujian")
        comp_rows = [
            {
                "Model": model_nb.get("nama", "Gaussian Naive Bayes"),
                "Hyperparameter": str(model_nb.get("best_params", {})),
                "Akurasi Val (%)": f"{model_nb.get('val', {}).get('accuracy', 0.0)*100:.2f}%",
                "F1 Val (%)": f"{model_nb.get('val', {}).get('f1_weighted', 0.0)*100:.2f}%",
                "Akurasi Test (%)": f"{acc_nb:.2f}%",
                "F1 Test (%)": f"{nb_test.get('f1_weighted', 0.0)*100:.2f}%",
                "Cohen's Kappa": f"{kappa_nb:.4f}",
                "Status Ambang": "Memenuhi (≥85%)" if acc_nb >= 85.0 else "Belum Memenuhi"
            },
            {
                "Model": model_knn.get("nama", "K-Nearest Neighbors"),
                "Hyperparameter": str(model_knn.get("best_params", {})),
                "Akurasi Val (%)": f"{model_knn.get('val', {}).get('accuracy', 0.0)*100:.2f}%",
                "F1 Val (%)": f"{model_knn.get('val', {}).get('f1_weighted', 0.0)*100:.2f}%",
                "Akurasi Test (%)": f"{acc_knn:.2f}%",
                "F1 Test (%)": f"{knn_test.get('f1_weighted', 0.0)*100:.2f}%",
                "Cohen's Kappa": f"{kappa_knn:.4f}",
                "Status Ambang": "Memenuhi (≥85%)" if acc_knn >= 85.0 else "Belum Memenuhi"
            }
        ]
        st.dataframe(pd.DataFrame(comp_rows), hide_index=True, use_container_width=True)
        
        # 2. Grafik Komparasi Bar Chart
        st.markdown("### 2. Grafik Komparasi Metrik Pengujian (Testing Set)")
        render_comparison_bar_chart(model_nb, model_knn)
        
        # 3. Komparasi Luas Kelas
        st.markdown("### 3. Komparasi Estimasi Luas Tutupan Lahan Hasil Pemetaan")
        luas_nb_list = model_nb.get("luas_kelas", [])
        luas_knn_list = model_knn.get("luas_kelas", [])
        
        if luas_nb_list and luas_knn_list:
            df_lnb = pd.DataFrame(luas_nb_list).set_index("kelas")
            df_lknn = pd.DataFrame(luas_knn_list).set_index("kelas")
            
            # Gabungkan berdampingan
            df_merge = pd.DataFrame({
                "Luas NB (ha)": df_lnb.get("luas_ha", 0.0),
                "Proporsi NB (%)": df_lnb.get("persen", 0.0),
                "Luas KNN (ha)": df_lknn.get("luas_ha", 0.0),
                "Proporsi KNN (%)": df_lknn.get("persen", 0.0)
            })
            st.dataframe(df_merge.reset_index(), hide_index=True, use_container_width=True)
            
        # 4. Keterbatasan Khusus Basis Ini
        st.markdown("### 4. Keterbatasan Khusus & Pertimbangan Kritis")
        st.markdown("""
        <div class="mercury-card">
            <div class="mercury-card-title">⚠️ Catatan Metodologi & Batasan Pengamatan</div>
            <ul style="color:#ededf3; font-size:0.92rem; line-height:1.75; margin-left:18px;">
        """, unsafe_allow_html=True)
        
        ket_list = KETERBATASAN.get(basis.lower(), [])
        for k_item in ket_list:
            st.markdown(f"<li>{k_item}</li>", unsafe_allow_html=True)
            
        st.markdown("</ul></div>", unsafe_allow_html=True)
