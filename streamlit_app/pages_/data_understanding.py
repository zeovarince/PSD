"""
Halaman 1: Data Understanding & Pengumpulan Data LULC Jawa Timur.
Menjelaskan landasan hukum/standar, tujuan kebijakan, instrumen satelit Sentinel-2A,
formula indeks spektral, dan filosofi komparasi dua basis (polygon vs pixel).
"""

import streamlit as st
import pandas as pd
from content.static_text import (
    TUJUAN_ANALISIS, PILAR_KEBIJAKAN, AOI_INFO,
    TABEL_ACUAN_KLASIFIKASI, KOMPONEN_DATA, TABEL_BAND,
    CATATAN_BAND_DILEWATI, TABEL_INDEKS, PERBEDAAN_BASIS, WARNA_KELAS
)

def render_data_understanding():
    st.markdown('<span class="mercury-pill mercury-pill-cobalt">Bab 1 — Fondasi Metodologis</span>', unsafe_allow_html=True)
    st.title("Data Understanding & Kerangka Analisis LULC")
    st.markdown(
        '<p class="mercury-lead">Pemetaan Land Use and Land Cover (LULC) Provinsi Jawa Timur 6 kelas '
        'berbasis data multispektral Sentinel-2A Level-2A Copernicus Data Space Ecosystem untuk '
        'analisis spasial kebijakan tata ruang dan konservasi lingkungan.</p>',
        unsafe_allow_html=True
    )
    
    # ---------------- 1. Tujuan Analisis & Pilar Kebijakan ----------------
    st.markdown("## 1. Tujuan Analisis & Implikasi Kebijakan")
    st.markdown(f"""
    <div class="mercury-card">
        <p style="font-size:1.02rem; line-height:1.6; color:#ededf3; margin-bottom:18px;">
            {TUJUAN_ANALISIS}
        </p>
        <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap:16px;">
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    for idx, pilar in enumerate(PILAR_KEBIJAKAN):
        target_col = col1 if idx % 2 == 0 else col2
        with target_col:
            st.markdown(f"""
            <div class="mercury-card" style="padding:18px; background-color:#242433; margin-bottom:12px;">
                <div style="font-weight:500; font-size:1rem; color:#ededf3; margin-bottom:6px;">
                    📌 {pilar['judul']}
                </div>
                <div style="color:#c3c3cc; font-size:0.88rem; line-height:1.5;">
                    {pilar['deskripsi']}
                </div>
            </div>
            """, unsafe_allow_html=True)

    # ---------------- 2. Wilayah Studi (AOI) ----------------
    st.markdown("## 2. Wilayah Studi (Area of Interest)")
    c_aoi1, c_aoi2 = st.columns([1, 1])
    with c_aoi1:
        st.markdown(f"""
        <div class="mercury-card">
            <div class="mercury-card-title">🌐 Koordinat Batas Area Studi</div>
            <p style="color:#c3c3cc; font-size:0.92rem; line-height:1.6;">
                Kotak pembatas geografis (Bounding Box) mencakup seluruh daratan Provinsi Jawa Timur, 
                Pulau Madura, kepulauan sekitarnya, serta perairan Selat Madura dan Samudra Hindia:
            </p>
            <ul style="color:#ededf3; font-size:0.92rem; line-height:1.8;">
                <li><strong>Batas Barat:</strong> {AOI_INFO['bujur_barat']}</li>
                <li><strong>Batas Timur:</strong> {AOI_INFO['bujur_timur']}</li>
                <li><strong>Batas Utara:</strong> {AOI_INFO['lintang_utara']}</li>
                <li><strong>Batas Selatan:</strong> {AOI_INFO['lintang_selatan']}</li>
                <li><strong>Sistem Koordinat:</strong> {AOI_INFO['proyeksi']}</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    with c_aoi2:
        st.markdown("""
        <div class="mercury-card">
            <div class="mercury-card-title">🗺️ Karakteristik Geografis Jawa Timur</div>
            <p style="color:#c3c3cc; font-size:0.92rem; line-height:1.6;">
                Wilayah Jawa Timur memiliki kontras morfologi yang sangat kaya:
            </p>
            <ul style="color:#ededf3; font-size:0.92rem; line-height:1.7;">
                <li><strong>Dataran Rendah & Pesisir:</strong> Sentra lumbung sawah irigasi teknis dan tambak di Pantura.</li>
                <li><strong>Gugusan Hutan Mangrove:</strong> Kawasan estuari Ujung Pangkah, Wonorejo Surabaya, dan Teluk Pacitan.</li>
                <li><strong>Kawasan Vulkanik:</strong> Busur pegunungan Bromo-Tengger-Semeru, Arjuno, dan Ijen dengan danau kaldera/ranu.</li>
                <li><strong>Kawasan Metropolis:</strong> Aglomerasi Gerbangkertosusila dengan laju ekspansi fisik intensif.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    # ---------------- 3. Acuan Klasifikasi Nasional ----------------
    st.markdown("## 3. Acuan Standar Klasifikasi Lahan di Indonesia")
    st.markdown("""
    Klasifikasi lahan dalam riset ini merujuk pada standar nasional resmi **SNI 7645-1:2014** 
    (Klasifikasi Penutup Lahan Skala Menengah) dan **Klasifikasi Penutupan Lahan KLHK**. 
    Enam kelas penelitian merupakan penyederhanaan terukur yang kompatibel dengan resolusi citra satelit Sentinel-2:
    """)
    
    rows_sni = ""
    for item in TABEL_ACUAN_KLASIFIKASI:
        w = item["warna"]
        rows_sni += f"""
        <tr>
            <td style="text-align:center;">{item['no']}</td>
            <td>
                <span style="display:inline-block;width:12px;height:12px;border-radius:50%;background-color:{w};margin-right:8px;"></span>
                <strong style="color:#ededf3;">{item['kelas']}</strong>
            </td>
            <td><code>{w}</code></td>
            <td style="color:#c3c3cc;">{item['padanan']}</td>
            <td><span class="mercury-pill">{item['sni']}</span></td>
        </tr>
        """
        
    st.markdown(f"""
    <div class="mercury-table-container">
        <table class="mercury-table">
            <thead>
                <tr>
                    <th style="width:50px;text-align:center;">No</th>
                    <th>Kelas Penelitian</th>
                    <th>Kode Warna Peta</th>
                    <th>Padanan pada Acuan KLHK</th>
                    <th>Padanan SNI 7645-1:2014</th>
                </tr>
            </thead>
            <tbody>
                {rows_sni}
            </tbody>
        </table>
    </div>
    """, unsafe_allow_html=True)

    # ---------------- 4. Kolekting Data Sentinel-2 ----------------
    st.markdown("## 4. Pengumpulan & Pra-pengolahan Data Citra")
    df_komp = pd.DataFrame(KOMPONEN_DATA)
    st.dataframe(df_komp, hide_index=True, use_container_width=True)

    # ---------------- 5. Deskripsi Band Sentinel-2A ----------------
    st.markdown("## 5. Deskripsi Band Sentinel-2A Multispectral Instrument (MSI)")
    st.markdown("""
    Sentinel-2A membawa instrumen optik MSI dengan 13 kanal spektral. Pada produk **Level-2A (L2A)**, 
    nilai digital (Digital Number - DN) dikonversi menjadi nilai reflektansi permukaan 
    (*Bottom-Of-Atmosphere / BOA*) menggunakan relasi:
    """)
    st.latex(r"\rho = \frac{DN}{10000}")
    st.markdown(
        f"<p style='color:#c3c3cc; font-size:0.9rem; margin-bottom:16px;'>{CATATAN_BAND_DILEWATI}</p>", 
        unsafe_allow_html=True
    )
    
    df_band = pd.DataFrame(TABEL_BAND)
    st.dataframe(df_band, hide_index=True, use_container_width=True)

    # ---------------- 6. Fitur Ekstraksi (8 Indeks Spektral) ----------------
    st.markdown("## 6. Fitur Ekstraksi Spektral (18 Fitur Total)")
    st.markdown("""
    Model memanfaatkan **18 fitur prediktor**: 10 band reflektansi dasar dan **8 indeks spektral matematis** 
    yang mengombinasikan respon biologis dan fisik tutupan permukaan:
    """)
    
    col_idx1, col_idx2 = st.columns(2)
    for i, idx in enumerate(TABEL_INDEKS):
        c_target = col_idx1 if i % 2 == 0 else col_idx2
        with c_target:
            with st.container():
                st.markdown(f"""
                <div class="mercury-card" style="padding:18px; margin-bottom:14px;">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
                        <span style="font-size:1.1rem; font-weight:500; color:#ededf3;">{idx['Nama']}</span>
                        <span class="mercury-pill mercury-pill-cobalt">{idx['Kepanjangan']}</span>
                    </div>
                    <p style="color:#c3c3cc; font-size:0.85rem; margin-bottom:10px;">{idx['Fungsi']}</p>
                </div>
                """, unsafe_allow_html=True)
                st.latex(idx["Rumus"])

    # ---------------- 7. Klasifikasi Dua Basis: Polygon vs Pixel ----------------
    st.markdown("## 7. Metodologi Komparasi Dua Basis Observasi")
    st.markdown("""
    Eksperimen klasifikasi dieksekusi dalam dua paradigma pengamatan yang berbeda untuk mengevaluasi 
    trade-off antara ketelitian spasial dan independensi data:
    """)
    
    df_beda = pd.DataFrame(PERBEDAAN_BASIS)
    st.dataframe(df_beda, hide_index=True, use_container_width=True)
    
    st.markdown("""
    <div class="mercury-card" style="margin-top:20px; border-left: 3px solid #5266eb;">
        <strong style="color:#ededf3;">📌 Panduan Eksplorasi:</strong>
        <p style="color:#c3c3cc; font-size:0.92rem; margin:6px 0 0 0;">
            Gunakan menu di sidebar untuk meninjau secara mendalam <strong>Basis Polygon</strong> (analisis pada level bidang lahan 1-sampel) 
            atau <strong>Basis Pixel</strong> (analisis sampling titik acak 10 meter). Tiap basis menyajikan 5 tahapan lengkap mulai dari pemrosesan data, 
            split train/val/test, evaluasi Naive Bayes, evaluasi KNN, hingga perbandingan dan peta interaktif.
        </p>
    </div>
    """, unsafe_allow_html=True)
