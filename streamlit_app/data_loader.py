"""
Data loader module with @st.cache_data caching.
Loads results.json, Folium HTML maps, and figures safely without crashing.
"""

from __future__ import annotations
import os
import json
import glob
from typing import Optional, Dict, List, Any
import streamlit as st

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

@st.cache_data(show_spinner=False)
def load_results(basis: str) -> Optional[Dict[str, Any]]:
    """
    Memuat data hasil ekspor results.json untuk basis 'polygon' atau 'pixel'.
    Mengembalikan dictionary jika berhasil, atau None jika file tidak ditemukan/korup.
    """
    candidates = [
        os.path.join(ASSETS_DIR, basis, "results.json"),
        os.path.join(BASE_DIR, "assets", basis, "results.json"),
        os.path.join(os.path.dirname(BASE_DIR), "streamlit_app", "assets", basis, "results.json"),
        os.path.join(os.path.dirname(BASE_DIR), "assets", basis, "results.json")
    ]
    
    target_path = None
    for p in candidates:
        norm_p = os.path.normpath(p)
        if os.path.exists(norm_p):
            target_path = norm_p
            break
            
    if not target_path:
        return None
        
    try:
        with open(target_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Gagal membaca file JSON {target_path}: {e}")
        return None

@st.cache_data(show_spinner=False)
def load_map_html(rel_or_abs_path: str) -> Optional[str]:
    """
    Membaca konten file HTML Folium.
    Mendukung path relatif terhadap streamlit_app atau root repo, serta path absolut.
    """
    candidates = [
        rel_or_abs_path,
        os.path.join(BASE_DIR, rel_or_abs_path),
        os.path.join(ASSETS_DIR, rel_or_abs_path),
        os.path.join(os.path.dirname(BASE_DIR), rel_or_abs_path),
        os.path.join(os.path.dirname(BASE_DIR), "streamlit_app", rel_or_abs_path),
        os.path.join(os.path.dirname(BASE_DIR), "materi", os.path.basename(rel_or_abs_path))
    ]
    
    target_path = None
    for p in candidates:
        norm_p = os.path.normpath(p)
        if os.path.exists(norm_p) and os.path.isfile(norm_p):
            target_path = norm_p
            break
            
    if not target_path:
        return None
        
    try:
        with open(target_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        st.error(f"Gagal membaca file peta {target_path}: {e}")
        return None

@st.cache_data(show_spinner=False)
def list_figures(basis: str) -> List[str]:
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
    candidates = [
        os.path.join(BASE_DIR, "content", "style.css"),
        os.path.join(os.path.dirname(BASE_DIR), "streamlit_app", "content", "style.css"),
        os.path.join(os.path.dirname(BASE_DIR), "content", "style.css")
    ]
    for c in candidates:
        norm_c = os.path.normpath(c)
        if os.path.exists(norm_c):
            try:
                with open(norm_c, "r", encoding="utf-8") as f:
                    return f.read()
            except Exception:
                pass
    return ""
