"""
Komponen UI visual interaktif untuk Streamlit.
Mengadopsi Mercury Design System (Dark Onyx, Graphite Cards, Cobalt Accent, Ivory Text)
dan Plotly untuk visualisasi data interaktif.
"""

from __future__ import annotations
import os
from typing import Optional, Dict, List, Any
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

from content.static_text import WARNA_KELAS
from data_loader import load_map_html

# Base Plotly theme layout (HANYA konfigurasi latar belakang dan font canvas global)
# Menghindari duplikasi kwargs xaxis/yaxis di fig.update_layout()
MERCURY_BASE_LAYOUT = dict(
    paper_bgcolor="#1e1e2a",
    plot_bgcolor="#1e1e2a",
    font=dict(color="#ededf3", family="Inter, sans-serif", size=12),
    margin=dict(l=40, r=40, t=50, b=40)
)

def apply_mercury_axes(fig: go.Figure) -> go.Figure:
    """Menerapkan styling sumbu standar Mercury tanpa menimpa properti spesifik per plot."""
    fig.update_xaxes(
        gridcolor="rgba(226, 227, 237, 0.08)",
        zerolinecolor="rgba(226, 227, 237, 0.15)",
        tickfont=dict(color="#c3c3cc")
    )
    fig.update_yaxes(
        gridcolor="rgba(226, 227, 237, 0.08)",
        zerolinecolor="rgba(226, 227, 237, 0.15)",
        tickfont=dict(color="#c3c3cc")
    )
    return fig

def render_metric_card(label: str, value: str, subtext: str = None):
    """Merender satu kartu metrik bergaya Mercury."""
    sub_html = f'<div class="mercury-metric-sub">{subtext}</div>' if subtext else ''
    st.markdown(f"""
    <div class="mercury-metric-box">
        <div class="mercury-metric-label">{label}</div>
        <div class="mercury-metric-value">{value}</div>
        {sub_html}
    </div>
    """, unsafe_allow_html=True)

def render_metric_row(test_metrics: dict, val_metrics: dict = None):
    """
    Merender jajaran kartu metrik evaluasi pengujian (5 metrik utama) + validasi.
    """
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        acc = test_metrics.get("accuracy", 0.0) if test_metrics else 0.0
        v_acc = val_metrics.get("accuracy", None) if val_metrics else None
        sub = f"Val: {v_acc*100:.1f}%" if v_acc is not None else None
        render_metric_card("Akurasi Test", f"{acc*100:.2f}%", sub)
        
    with col2:
        f1 = test_metrics.get("f1_weighted", 0.0) if test_metrics else 0.0
        v_f1 = val_metrics.get("f1_weighted", None) if val_metrics else None
        sub = f"Val: {v_f1*100:.1f}%" if v_f1 is not None else None
        render_metric_card("F1-Score (W)", f"{f1*100:.2f}%", sub)
        
    with col3:
        kappa = test_metrics.get("kappa", 0.0) if test_metrics else 0.0
        k_cat = "Hampir Sempurna" if kappa >= 0.8 else ("Substansial" if kappa >= 0.6 else "Moderat")
        render_metric_card("Cohen's Kappa", f"{kappa:.4f}", k_cat)
        
    with col4:
        prec = test_metrics.get("precision_weighted", 0.0) if test_metrics else 0.0
        render_metric_card("Precision (W)", f"{prec*100:.2f}%", "Rata-rata tertimbang")
        
    with col5:
        rec = test_metrics.get("recall_weighted", 0.0) if test_metrics else 0.0
        render_metric_card("Recall (W)", f"{rec*100:.2f}%", "Sensitivitas model")

def render_tuning_curve(tuning_dict: dict, model_type: str):
    """
    Grafik kurva tuning hyperparameter interaktif (GNB var_smoothing atau KNN k).
    """
    if not tuning_dict or "x" not in tuning_dict:
        st.info("Data kurva tuning tidak tersedia.")
        return
        
    fig = go.Figure()
    x_vals = tuning_dict.get("x", [])
    
    if model_type.lower() == "nb" or "var_smoothing" in str(model_type).lower():
        y_val = [v * 100 if v <= 1.0 else v for v in tuning_dict.get("val_acc", [])]
        fig.add_trace(go.Scatter(
            x=x_vals,
            y=y_val,
            mode="lines+markers",
            name="Akurasi Validasi (%)",
            line=dict(color="#5266eb", width=3),
            marker=dict(size=8, color="#ffffff")
        ))
        fig.update_layout(
            **MERCURY_BASE_LAYOUT,
            title="Tuning var_smoothing (Gaussian Naive Bayes) pada Validation Set",
            xaxis_title="Parameter var_smoothing (Skala Logaritmik)",
            yaxis_title="Akurasi Validasi (%)",
            height=360
        )
        apply_mercury_axes(fig)
        fig.update_xaxes(type="log")
    else:
        # KNN tuning
        y_train = [v * 100 if v <= 1.0 else v for v in tuning_dict.get("train_acc", [])]
        y_val = [v * 100 if v <= 1.0 else v for v in tuning_dict.get("val_acc", [])]
        
        if y_train:
            fig.add_trace(go.Scatter(
                x=x_vals,
                y=y_train,
                mode="lines+markers",
                name="Training Accuracy",
                line=dict(color="#70707d", width=2, dash="dash"),
                marker=dict(size=6)
            ))
        fig.add_trace(go.Scatter(
            x=x_vals,
            y=y_val,
            mode="lines+markers",
            name="Validation Accuracy",
            line=dict(color="#5266eb", width=3),
            marker=dict(size=8, color="#ffffff")
        ))
        fig.update_layout(
            **MERCURY_BASE_LAYOUT,
            title="Tuning Nilai k (K-Nearest Neighbors) pada Validation Set",
            xaxis_title="Jumlah Tetangga Terdekat (k)",
            yaxis_title="Akurasi (%)",
            height=360
        )
        apply_mercury_axes(fig)
        fig.update_xaxes(tickmode="linear", tick0=1, dtick=2)
        
    st.plotly_chart(fig, use_container_width=True)

def render_confusion_matrix(cm_dict: dict, model_name: str):
    """
    Heatmap Confusion Matrix interaktif Plotly dengan skema warna yang terbaca jelas.
    """
    if not cm_dict or "matrix" not in cm_dict:
        st.info("Data confusion matrix tidak ditemukan.")
        return
        
    labels = cm_dict.get("labels", [])
    matrix = cm_dict.get("matrix", [])
    
    # Text annotations inside cells
    annotations = []
    for i, row in enumerate(matrix):
        for j, val in enumerate(row):
            is_diag = (i == j)
            font_color = "#ffffff" if is_diag else ("#c3c3cc" if val > 0 else "rgba(195,195,204,0.3)")
            x_label = labels[j] if j < len(labels) else str(j)
            y_label = labels[i] if i < len(labels) else str(i)
            annotations.append(dict(
                x=x_label,
                y=y_label,
                text=str(val),
                showarrow=False,
                font=dict(color=font_color, size=13, family="Inter")
            ))
            
    fig = go.Figure(data=go.Heatmap(
        z=matrix,
        x=labels,
        y=labels,
        colorscale=[
            [0.0, "#171721"],
            [0.1, "#1e1e2a"],
            [0.5, "#303975"],
            [1.0, "#5266eb"]
        ],
        showscale=False
    ))
    
    fig.update_layout(
        **MERCURY_BASE_LAYOUT,
        title=f"Confusion Matrix: {model_name} (Testing Set)",
        xaxis_title="Prediksi Kelas",
        yaxis_title="Kelas Aktual",
        annotations=annotations,
        height=420
    )
    apply_mercury_axes(fig)
    fig.update_yaxes(autorange="reversed")
    
    st.plotly_chart(fig, use_container_width=True)

def render_classification_report_table(report_dict: dict):
    """
    Tabel HTML presisi untuk Classification Report per kelas.
    Aman dari missing keys, summary rows (accuracy, macro avg), dan tipe non-dict.
    """
    if not report_dict:
        st.info("Laporan klasifikasi per kelas tidak tersedia.")
        return
        
    rows_html = ""
    for k, metrics in report_dict.items():
        if not isinstance(metrics, dict):
            continue
        # Lewati baris ringkasan jika ada
        if str(k).lower() in ["accuracy", "macro avg", "weighted avg"]:
            continue
            
        prec = metrics.get("precision", 0.0)
        rec = metrics.get("recall", 0.0)
        f1 = metrics.get("f1", metrics.get("f1-score", 0.0))
        sup = metrics.get("support", 0)
        badge_color = WARNA_KELAS.get(k, "#8c9bff")
        
        rows_html += f"""
        <tr>
            <td style="display:flex;align-items:center;gap:8px;">
                <span style="display:inline-block;width:10px;height:10px;border-radius:50%;background-color:{badge_color};"></span>
                <strong>{k}</strong>
            </td>
            <td>{prec*100:.2f}%</td>
            <td>{rec*100:.2f}%</td>
            <td><strong>{f1*100:.2f}%</strong></td>
            <td>{sup}</td>
        </tr>
        """
        
    html = f"""
    <div class="mercury-table-container">
        <table class="mercury-table">
            <thead>
                <tr>
                    <th>Kelas Tutupan Lahan</th>
                    <th>Precision</th>
                    <th>Recall</th>
                    <th>F1-Score</th>
                    <th>Support (Sampel Uji)</th>
                </tr>
            </thead>
            <tbody>
                {rows_html}
            </tbody>
        </table>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def render_comparison_bar_chart(model_nb: dict, model_knn: dict):
    """
    Bar chart perbandingan metrik utama Naive Bayes vs KNN.
    """
    metrics = ["Akurasi", "F1 (Weighted)", "Kappa (x100)", "Precision", "Recall"]
    
    t_nb = model_nb.get("test", {}) if model_nb else {}
    t_knn = model_knn.get("test", {}) if model_knn else {}
    
    nb_vals = [
        t_nb.get("accuracy", 0.0) * 100,
        t_nb.get("f1_weighted", 0.0) * 100,
        t_nb.get("kappa", 0.0) * 100,
        t_nb.get("precision_weighted", 0.0) * 100,
        t_nb.get("recall_weighted", 0.0) * 100
    ]
    
    knn_vals = [
        t_knn.get("accuracy", 0.0) * 100,
        t_knn.get("f1_weighted", 0.0) * 100,
        t_knn.get("kappa", 0.0) * 100,
        t_knn.get("precision_weighted", 0.0) * 100,
        t_knn.get("recall_weighted", 0.0) * 100
    ]
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=metrics,
        y=nb_vals,
        name=model_nb.get("nama", "Gaussian Naive Bayes") if model_nb else "Naive Bayes",
        marker=dict(color="#70707d"),
        text=[f"{v:.1f}%" for v in nb_vals],
        textposition="outside"
    ))
    fig.add_trace(go.Bar(
        x=metrics,
        y=knn_vals,
        name=model_knn.get("nama", "KNN") if model_knn else "KNN",
        marker=dict(color="#5266eb"),
        text=[f"{v:.1f}%" for v in knn_vals],
        textposition="outside"
    ))
    
    fig.update_layout(
        **MERCURY_BASE_LAYOUT,
        barmode="group",
        title="Perbandingan Metrik Evaluasi: Naive Bayes vs KNN (Testing Set)",
        height=380,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    apply_mercury_axes(fig)
    fig.update_yaxes(range=[0, 115], title_text="Persentase (%)")
    
    st.plotly_chart(fig, use_container_width=True)

def render_dataset_dist_chart(split_list: list):
    """
    Bar chart distribusi sampel per kelas dan pembagian data (Train, Val, Test).
    """
    if not split_list:
        return
        
    df = pd.DataFrame(split_list)
    classes = df["kelas"].tolist()
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=classes,
        y=df["train"],
        name="Training (70%)",
        marker=dict(color="#5266eb")
    ))
    fig.add_trace(go.Bar(
        x=classes,
        y=df["val"],
        name="Validation (15%)",
        marker=dict(color="#8c9bff")
    ))
    fig.add_trace(go.Bar(
        x=classes,
        y=df["test"],
        name="Testing (15%)",
        marker=dict(color="#272735")
    ))
    
    fig.update_layout(
        **MERCURY_BASE_LAYOUT,
        barmode="stack",
        title="Distribusi Sampel per Kelas Berdasarkan Split Data",
        yaxis_title="Jumlah Sampel",
        height=360,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    apply_mercury_axes(fig)
    st.plotly_chart(fig, use_container_width=True)

def render_winner_banner(winner_name: str, best_acc: float, best_kappa: float, margin: float, other_name: str, alasan_teks: str):
    """
    Banner sorotan model pemenang dengan rekomendasi otomatis.
    """
    status_acc = "Memenuhi Ambang Batas (≥ 85%)" if best_acc >= 85.0 else "Belum Memenuhi Ambang Batas (85%)"
    status_kappa = "Memenuhi Ambang Kappa (≥ 0.80 - Hampir Sempurna)" if best_kappa >= 0.80 else "Belum Memenuhi Ambang Kappa (0.80)"
    
    st.markdown(f"""
    <div class="mercury-winner-banner">
        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px;">
            <div>
                <span class="mercury-pill mercury-pill-cobalt">🏆 Model Terbaik Terpilih</span>
                <h2 style="margin:8px 0 4px 0; color:#ededf3; font-size:1.6rem;">{winner_name}</h2>
                <div style="color:#c3c3cc; font-size:0.95rem;">
                    Unggul <strong>+{margin:.2f}%</strong> akurasi pengujian dibandingkan <em>{other_name}</em>
                </div>
            </div>
            <div style="display:flex; gap:12px; margin-top:8px;">
                <div class="mercury-metric-box" style="padding:12px 16px; border:1px solid rgba(82,102,235,0.4);">
                    <div class="mercury-metric-label">Akurasi Test</div>
                    <div style="font-size:1.4rem; font-weight:500; color:#ededf3;">{best_acc:.2f}%</div>
                </div>
                <div class="mercury-metric-box" style="padding:12px 16px; border:1px solid rgba(82,102,235,0.4);">
                    <div class="mercury-metric-label">Cohen's Kappa</div>
                    <div style="font-size:1.4rem; font-weight:500; color:#ededf3;">{best_kappa:.4f}</div>
                </div>
            </div>
        </div>
        <hr style="border:0; border-top:1px solid rgba(226,227,237,0.1); margin:16px 0;">
        <div style="font-size:0.92rem; color:#ededf3; line-height:1.6;">
            <strong>Analisis Keputusan:</strong> {alasan_teks}
        </div>
        <div style="display:flex; gap:10px; margin-top:14px; flex-wrap:wrap;">
            <span class="mercury-pill mercury-pill-success">{status_acc}</span>
            <span class="mercury-pill mercury-pill-cobalt">{status_kappa}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_interactive_map(map_rel_path: str, model_title: str):
    """
    Merender peta interaktif Folium HTML dengan toolbar unduh dan status file.
    Menjamin fallback yang aman dan jelas jika file peta belum tersedia.
    """
    map_content = load_map_html(map_rel_path)
    filename = os.path.basename(map_rel_path)
    
    if map_content:
        size_mb = len(map_content) / (1024 * 1024)
        c_bar1, c_bar2 = st.columns([3, 1])
        with c_bar1:
            st.markdown(f"""
            <div style="display:flex; align-items:center; gap:8px; margin-bottom:8px;">
                <span class="mercury-pill mercury-pill-cobalt">Peta Siap ({size_mb:.1f} MB)</span>
                <span style="color:#c3c3cc; font-size:0.85rem;">
                    Gunakan kontrol layer di pojok kanan atas peta untuk switch basemap & batas poligon.
                </span>
            </div>
            """, unsafe_allow_html=True)
        with c_bar2:
            st.download_button(
                label="📥 Unduh HTML",
                data=map_content,
                file_name=filename,
                mime="text/html",
                key=f"dl_map_{filename}"
            )
            
        components.html(map_content, height=720, scrolling=True)
    else:
        st.markdown(f"""
        <div class="mercury-card" style="border: 1px solid rgba(228, 26, 28, 0.4); padding: 20px;">
            <div style="color: #ff6b6b; font-weight: 500; font-size: 1.05rem; margin-bottom: 8px;">
                ⚠️ File Peta Belum Ditemukan: <code>{filename}</code>
            </div>
            <p style="color: #c3c3cc; font-size: 0.9rem; line-height: 1.6; margin: 0;">
                Aplikasi mencari peta di jalur: <code>{map_rel_path}</code>.<br>
                Pastikan file peta HTML telah di-generate dari notebook atau sudah di-commit ke repositori GitHub 
                agar Streamlit Cloud dapat memuatnya.
            </p>
        </div>
        """, unsafe_allow_html=True)
