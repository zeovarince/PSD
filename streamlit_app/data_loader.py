"""
Data loader module with @st.cache_data caching.
Loads results.json, Folium HTML maps, and figures safely without crashing.
"""

import os
import json
import glob
import streamlit as st

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

@st.cache_data(show_spinner=False)
def load_results(basis: str) -> dict | None:
    """
    Memuat data hasil ekspor results.json untuk basis 'polygon' atau 'pixel'.
    Mengembalikan dictionary jika berhasil, atau None jika file tidak ditemukan/korup.
    """
    json_path = os.path.join(ASSETS_DIR, basis, "results.json")
    if not os.path.exists(json_path):
        return None
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Gagal membaca {json_path}: {e}")
        return None

@st.cache_data(show_spinner=False)
def load_map_html(rel_or_abs_path: str) -> str | None:
    """
    Membaca konten file HTML Folium.
    Mendukung path relatif terhadap folder streamlit_app atau path absolut.
    """
    if os.path.isabs(rel_or_abs_path):
        full_path = rel_or_abs_path
    else:
        full_path = os.path.join(BASE_DIR, rel_or_abs_path)
        
    if not os.path.exists(full_path):
        return None
    try:
        with open(full_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        st.error(f"Gagal membaca file peta {full_path}: {e}")
        return None

@st.cache_data(show_spinner=False)
def list_figures(basis: str) -> list[str]:
    """
    Mengambil daftar file gambar PNG hasil ekspor di assets/<basis>/.
    """
    basis_dir = os.path.join(ASSETS_DIR, basis)
    if not os.path.exists(basis_dir):
        return []
    pattern = os.path.join(basis_dir, "*.png")
    return sorted(glob.glob(pattern))

def load_css() -> str:
    """
    Membaca stylesheet Mercury CSS.
    """
    css_path = os.path.join(BASE_DIR, "content", "style.css")
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as f:
            return f.read()
    return ""
