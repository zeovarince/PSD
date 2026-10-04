"""
Script untuk menjalankan K-Means clustering pada fitur gabungan 3 polutan
dan menghasilkan CSV hasil clustering untuk peta interaktif.
"""
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
from pathlib import Path
import os

# Paths
BASE = Path(__file__).resolve().parent.parent
FITUR_NO2 = BASE / "ekstraksi_fitur_no2.csv"
FITUR_SO2 = BASE / "ekstraksi_fitur_so2.csv"
FITUR_CO  = BASE / "ekstraksi_fitur_co.csv"
OUTPUT_DIR = BASE / "source" / "cluster_daerah"

KOLOM_IDENTITAS = ["id", "nama", "daerah"]

def load_and_merge():
    """Baca 3 file fitur polutan dan gabungkan (204 fitur per daerah)."""
    df_no2 = pd.read_csv(FITUR_NO2)
    df_so2 = pd.read_csv(FITUR_SO2)
    df_co  = pd.read_csv(FITUR_CO)

    # Ambil fitur saja (buang kolom identitas)
    fitur_no2 = df_no2.drop(columns=KOLOM_IDENTITAS).add_prefix("NO2_")
    fitur_so2 = df_so2.drop(columns=KOLOM_IDENTITAS).add_prefix("SO2_")
    fitur_co  = df_co.drop(columns=KOLOM_IDENTITAS).add_prefix("CO_")

    # Gabungkan
    df = pd.concat([df_no2[KOLOM_IDENTITAS], fitur_no2, fitur_so2, fitur_co], axis=1)
    return df

def run_clustering(df, jenis, n_pca, k_values=[2, 3, 4]):
    """Jalankan PCA + K-Means dan simpan CSV."""
    X = df.drop(columns=KOLOM_IDENTITAS)
    
    # Standardisasi
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # PCA
    pca = PCA(n_components=n_pca, random_state=42)
    X_pca = pca.fit_transform(X_scaled)
    
    results = {}
    for k in k_values:
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = kmeans.fit_predict(X_pca)
        
        sil = silhouette_score(X_pca, labels)
        
        df_result = df[KOLOM_IDENTITAS].copy()
        df_result["Cluster"] = [f"cluster_{l}" for l in labels]
        
        filename = f"hasil_clustering_{jenis}_k{k}.csv"
        df_result.to_csv(OUTPUT_DIR / filename, index=False)
        
        results[k] = {
            "silhouette": sil,
            "labels": labels,
            "filename": filename,
        }
        
        print(f"  {jenis} PCA-{n_pca} K={k}: Silhouette = {sil:.3f} -> {filename}")
    
    return results

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    print("Loading data...")
    df = load_and_merge()
    print(f"Data shape: {df.shape} ({len(df)} daerah, {df.shape[1] - len(KOLOM_IDENTITAS)} fitur)")
    
    print("\n--- Fitur Polynomial (PCA 37) ---")
    results_poly = run_clustering(df, "polynomial", n_pca=37)
    
    print("\n--- Fitur Linear (PCA 37) ---")
    results_linear = run_clustering(df, "linear", n_pca=37)
    
    # Juga buat koordinat_daerah.csv
    print("\nDone! CSV files saved to:", OUTPUT_DIR)

if __name__ == "__main__":
    main()
