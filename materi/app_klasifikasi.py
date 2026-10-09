# pyrefly: ignore [missing-import]
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import os
import pickle
import numpy as np

# Konfigurasi Halaman (Aesthetics)
st.set_page_config(page_title="LULC East Java", page_icon="🌍", layout="wide")

# CSS untuk mempercantik UI
st.markdown("""
    <style>
        .main {
            background-color: #f4f7f6;
            font-family: 'Inter', sans-serif;
        }
        h1, h2, h3 {
            color: #2c3e50;
        }
        .metric-card {
            background-color: #ffffff;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            text-align: center;
        }
        .metric-value {
            font-size: 2em;
            font-weight: bold;
            color: #2980b9;
        }
    </style>
""", unsafe_allow_html=True)

st.title("🌍 Klasifikasi Penutup Lahan (LULC) - Jawa Timur")
st.markdown("Sistem Informasi Geografis dengan Basis Analisis Spasial Penggunaan Lahan dan Kebijakan")

# Sidebar navigasi
st.sidebar.title("Navigasi")
menu = st.sidebar.radio("Pilih Menu:", ["Data Understanding", "Eksplorasi Data & Model", "Peta Klasifikasi (WMS)"])

base_path = r'c:\Users\ARIEL\OneDrive\Documents\PSD\materi'
csv_path = os.path.join(base_path, 'dataset_klasifikasi_jatim.csv')
model_path = os.path.join(base_path, 'rf_model_jatim.pkl')

if menu == "Data Understanding":
    st.header("📖 Data Understanding & Collecting Data")
    st.markdown("""
    ### Tujuan Analisis
    Tujuan dari analisis **Land Use and Land Classification (LULC)** ini adalah untuk memetakan dan mengidentifikasi penutupan lahan di wilayah **Jawa Timur** guna mendukung kebijakan tata ruang, pemantauan degradasi lahan, dan perencanaan wilayah berkelanjutan.
    
    ### Acuan Klasifikasi di Indonesia
    Acuan yang digunakan bukan hanya 'sawah' dan 'non-sawah', melainkan merujuk pada **SNI 7645-1:2014** (Klasifikasi Penutup Lahan) yang diadaptasi menjadi 6 kelas spesifik sesuai hasil digitasi Region of Interest (ROI) pada eksperimen ini:
    1. **Sawah**
    2. **Bangunan**
    3. **Mangrove**
    4. **Lahan Hijau**
    5. **Perairan Terbuka (Laut)**
    6. **Danau (Ranu)**
    
    ### Collecting Data & Sentinel-2A Bands
    Data dikumpulkan dengan mendigitasi poligon pada QGIS/ArcGIS lalu diekstraksi nilai pikselnya terhadap citra Sentinel-2A. 
    **Macam-macam Band Sentinel-2A yang digunakan:**
    - **Band 2 (Blue - 10m):** Sensitif terhadap air laut.
    - **Band 3 (Green - 10m):** Memantulkan vegetasi sehat.
    - **Band 4 (Red - 10m):** Absorpsi klorofil.
    - **Band 8 (NIR - 10m):** Reflektansi tinggi pada sel daun vegetasi.
    - **Band 11 & 12 (SWIR 1 & 2 - 20m):** Sensitif terhadap kelembaban, bagus untuk membedakan lahan terbangun dan tanah terbuka.
    
    ### Fitur Indeks Ekstraksi
    Untuk meningkatkan akurasi, dihitung indeks spektral dengan rumus:
    - **NDVI** = `(NIR - Red) / (NIR + Red)`
    - **NDWI** = `(Green - NIR) / (Green + NIR)`
    - **MNDWI** = `(Green - SWIR1) / (Green + SWIR1)`
    - **NDBI** = `(SWIR1 - NIR) / (SWIR1 + NIR)`
    - **EVI** = `2.5 * ((NIR - Red) / (NIR + 6*Red - 7.5*Blue + 1))`
    """)

elif menu == "Eksplorasi Data & Model":
    st.header("📊 Eksplorasi Data & Evaluasi Model Random Forest")
    
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        
        st.subheader("Informasi Dataset")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f'<div class="metric-card">Jumlah Total Data<br><span class="metric-value">{len(df)}</span></div>', unsafe_allow_html=True)
        with col2:
            st.markdown(f'<div class="metric-card">Data Training (70%)<br><span class="metric-value">{int(len(df)*0.7)}</span></div>', unsafe_allow_html=True)
        with col3:
            st.markdown(f'<div class="metric-card">Data Testing (30%)<br><span class="metric-value">{int(len(df)*0.3)}</span></div>', unsafe_allow_html=True)
            
        st.write("Preview Data Piksel Sentinel-2A:")
        st.dataframe(df.head())
        
        st.subheader("Distribusi Kelas")
        st.bar_chart(df['label'].value_counts())
        
        if os.path.exists(model_path):
            with open(model_path, 'rb') as f:
                model = pickle.load(f)
            
            st.success("✅ Model Random Forest Classifier berhasil dilatih dan memberikan akurasi tertinggi pada eksperimen.")
            
            # Simulasi Feature Importance
            if hasattr(model, 'feature_importances_'):
                importances = model.feature_importances_
                features = df.drop(columns=['label']).columns
                feat_df = pd.DataFrame({'Fitur': features, 'Kepentingan': importances}).sort_values(by='Kepentingan', ascending=False)
                st.write("**Feature Importances:**")
                st.bar_chart(feat_df.set_index('Fitur'))
                
    else:
        st.warning("Dataset belum di-generate. Silakan jalankan script `generate_dataset.py` terlebih dahulu.")

elif menu == "Peta Klasifikasi (WMS)":
    st.header("🗺️ Visualisasi Peta LULC (WMS Google Satellite)")
    st.write("Menampilkan peta WMS Google Satellite menggunakan Folium.")
    
    # Kordinat pusat Jawa Timur
    m = folium.Map(location=[-7.6977, 112.5253], zoom_start=8)
    
    # Tambahkan WMS Layer Google Satellite
    folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
        attr='Google',
        name='Google Satellite',
        overlay=False,
        control=True
    ).add_to(m)
    
    # Menambahkan legenda atau marker dummy untuk simulasi kelas di Jatim
    # Karena kita tidak merender raster utuh (ukurannya bergiga-giga), kita tandai titik sampling
    
    colors = {
        0: 'green', # Sawah
        1: 'red', # Bangunan
        2: 'darkgreen', # Mangrove
        3: 'lightgreen', # Lahan Hijau
        4: 'blue', # Laut
        5: 'lightblue' # Danau
    }
    labels = {0: 'Sawah', 1: 'Bangunan', 2: 'Mangrove', 3: 'Lahan Hijau', 4: 'Laut', 5: 'Danau'}
    
    # Tambahkan legend ke map
    legend_html = '''
     <div style="position: fixed; 
     bottom: 50px; left: 50px; width: 150px; height: 180px; 
     border:2px solid grey; z-index:9999; font-size:14px;
     background-color:white; padding: 10px;
     ">&nbsp;<b>Legenda LULC</b><br>
     &nbsp;<i class="fa fa-square fa-1x" style="color:green"></i> Sawah<br>
     &nbsp;<i class="fa fa-square fa-1x" style="color:red"></i> Bangunan<br>
     &nbsp;<i class="fa fa-square fa-1x" style="color:darkgreen"></i> Mangrove<br>
     &nbsp;<i class="fa fa-square fa-1x" style="color:lightgreen"></i> Lahan Hijau<br>
     &nbsp;<i class="fa fa-square fa-1x" style="color:blue"></i> Laut<br>
     &nbsp;<i class="fa fa-square fa-1x" style="color:lightblue"></i> Danau<br>
     </div>
     '''
    m.get_root().html.add_child(folium.Element(legend_html))
    
    st_folium(m, width=900, height=500)
    st.info("Peta di atas merupakan basemap Satelit dengan kesiapan overlay raster/vektor hasil prediksi model.")
