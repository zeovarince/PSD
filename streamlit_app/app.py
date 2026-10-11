"""
Sistem Informasi LULC Jawa Timur — Web Streamlit UTS Sistem Informasi Geografis
Entry point aplikasi dengan navigasi sidebar 3 halaman:
1. Data Understanding
2. Basis Polygon
3. Basis Pixel
"""

import streamlit as st
from data_loader import load_css
from pages_.data_understanding import render_data_understanding
from pages_.basis import render_basis

# 1. Konfigurasi Halaman Global
st.set_page_config(
    page_title="LULC Jawa Timur — Sistem Informasi Geografis",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Injeksi Stylesheet Mercury Design System
custom_css = load_css()
if custom_css:
    st.markdown(f"<style>{custom_css}</style>", unsafe_allow_html=True)

# 3. Sidebar Navigasi & Branding
with st.sidebar:
    st.markdown("""
    <div style="padding: 12px 0 16px 0;">
        <span class="mercury-pill mercury-pill-cobalt">UTS SIG 2026</span>
        <h2 style="font-size: 1.35rem; margin: 10px 0 4px 0; color: #ededf3; font-weight: 500;">
            🛰️ LULC Jawa Timur
        </h2>
        <div style="color: #c3c3cc; font-size: 0.85rem; line-height: 1.4;">
            Sistem Informasi Geografis berbasis Sentinel-2A Multispektral
        </div>
    </div>
    <hr style="border: 0; border-top: 1px solid rgba(226, 227, 237, 0.1); margin: 0 0 16px 0;">
    """, unsafe_allow_html=True)
    
    st.markdown("<div style='font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.05em; color: #70707d; margin-bottom: 8px; font-weight: 500;'>MENU UTAMA</div>", unsafe_allow_html=True)
    
    halaman = st.radio(
        "Pilih Halaman",
        ["1. Data Understanding", "2. Basis Polygon", "3. Basis Pixel"],
        index=0,
        label_visibility="collapsed"
    )
    
    st.markdown("""
    <hr style="border: 0; border-top: 1px solid rgba(226, 227, 237, 0.1); margin: 24px 0 16px 0;">
    <div style="background-color: #1e1e2a; border-radius: 8px; padding: 14px; font-size: 0.82rem; color: #c3c3cc; line-height: 1.5; border: 1px solid rgba(226, 227, 237, 0.06);">
        <div style="color: #ededf3; font-weight: 500; margin-bottom: 4px;">📌 Metadata Riset:</div>
        • <strong>Data:</strong> Sentinel-2A Level-2A<br>
        • <strong>Periode:</strong> Mei–Sep 2026 (Komposit)<br>
        • <strong>Kelas:</strong> 6 Kelas LULC (SNI 7645)<br>
        • <strong>Fitur:</strong> 18 Fitur (10 Band + 8 Indeks)<br>
        • <strong>Model:</strong> Naive Bayes vs KNN
    </div>
    <div style="margin-top: 16px; font-size: 0.75rem; color: #70707d; text-align: center;">
        Universitas Trunojoyo Madura<br>Teknik Informatika © 2026
    </div>
    """, unsafe_allow_html=True)

# 4. Router Halaman
if halaman == "1. Data Understanding":
    render_data_understanding()
elif halaman == "2. Basis Polygon":
    render_basis("polygon")
elif halaman == "3. Basis Pixel":
    render_basis("pixel")
