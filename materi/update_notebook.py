import nbformat as nbf
import json

notebook_path = r'c:\Users\ARIEL\OneDrive\Documents\PSD\materi\klasifikasi6kelas.ipynb'

with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = nbf.read(f, as_version=4)

# Update Cell 1 (Info TIF)
nb.cells[1].source = """from pathlib import Path
import rasterio
import numpy as np
import pandas as pd
import os

# Cari GeoTIFF di folder kerja atau subfolder materi.
nama_tif = 'sentinel2A_jatim.tif'
kandidat_tif = [Path(nama_tif), Path('materi') / nama_tif]
TIF = next((path for path in kandidat_tif if path.exists()), kandidat_tif[0])

if not TIF.exists():
    print('GeoTIFF belum ditemukan.')
    print('Lokasi yang diperiksa:')
    for path in kandidat_tif:
        print(f'  - {path.resolve()}')
    print('\\n⚠️ KARENA TIF TIDAK DITEMUKAN, NOTEBOOK INI AKAN MENGGUNAKAN DATASET EKSPERIMEN CSV SEBAGAI FALLBACK!')
else:
    with rasterio.open(TIF) as src:
        jumlah_band = src.count
        ukuran_citra = (src.width, src.height)
        crs_citra = src.crs

    print(f'GeoTIFF ditemukan: {TIF.resolve()}')
    print(f'Ukuran citra: {ukuran_citra[0]} x {ukuran_citra[1]} piksel')
    print(f'Jumlah band: {jumlah_band}')
    print(f'CRS: {crs_citra}')"""

# Update Cell 2 (Extracion / ML)
new_code_2 = """import geopandas as gpd
from rasterio.features import rasterize
from rasterio.warp import transform
from shapely.geometry import Polygon, mapping
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, GroupShuffleSplit
from sklearn.metrics import confusion_matrix, accuracy_score, classification_report, cohen_kappa_score

OUT_KLAS = Path('klasifikasi_6kelas_jatim.tif')
OUT_GAMBAR = Path('segmentasi_6kelas.png')
NAMA_BAND = ['B2', 'B3', 'B4', 'B8', 'B11', 'B12', 'NDVI', 'NDWI', 'MNDWI', 'NDBI']
BUFFER_M = 5

classes = {'sawah': 0, 'bangunan': 1, 'mangrove': 2, 'lahanhijau': 3, 'laut': 4, 'danau': 5}
base_path = Path('c:/Users/ARIEL/OneDrive/Documents/PSD/materi')

if TIF.exists():
    def baca_shapefile(cls_name):
        shp_name = "input.shp" if cls_name == "danau" else f"{cls_name}.shp"
        path = base_path / cls_name / shp_name
        if not path.exists():
            return None
        return gpd.read_file(path)

    with rasterio.open(TIF) as src:
        arr = src.read().astype('float32')
        profil = src.profile
        tf, crs = src.transform, src.crs

    n_band, H, W = arr.shape
    valid = np.isfinite(arr).all(axis=0) & (arr[:6].sum(axis=0) > 0)
    
    def petak_ke_polygon(gdf):
        hasil = []
        if gdf.crs != crs:
            gdf = gdf.to_crs(crs)
        for idx, row in gdf.iterrows():
            polygon = row.geometry
            if polygon is None or polygon.is_empty or polygon.area == 0: continue
            if not polygon.is_valid: polygon = polygon.buffer(0)
            kecil = polygon.buffer(-BUFFER_M)
            hasil.append(kecil if not kecil.is_empty and kecil.area > 0 else polygon)
        return hasil

    def ambil(gdf, kelas, offset):
        if gdf is None: return np.empty((0, n_band), dtype='float32'), np.empty(0, dtype=int), np.empty(0, dtype=int)
        polygons = petak_ke_polygon(gdf)
        if not polygons: return np.empty((0, n_band), dtype='float32'), np.empty(0, dtype=int), np.empty(0, dtype=int)
        shapes = [(mapping(polygon), offset + index + 1) for index, polygon in enumerate(polygons)]
        ids = rasterize(shapes, out_shape=(H, W), transform=tf, fill=0, dtype='int32')
        mask = (ids > 0) & valid
        features = arr[:, mask].T
        groups = ids[mask]
        return features, np.full(len(features), kelas, dtype=int), groups

    X_all, y_all, g_all = [], [], []
    offset = 0
    for cls, label in classes.items():
        gdf = baca_shapefile(cls)
        if gdf is not None:
            X_c, y_c, g_c = ambil(gdf, label, offset)
            X_all.append(X_c)
            y_all.append(y_c)
            g_all.append(g_c)
            offset += 10000
    
    X = np.vstack(X_all)
    y = np.concatenate(y_all)
    grup = np.concatenate(g_all)
    
    splitter = GroupShuffleSplit(n_splits=1, test_size=0.3, random_state=42)
    train_index, test_index = next(splitter.split(X, y, grup))
    X_train, X_test = X[train_index], X[test_index]
    y_train, y_test = y[train_index], y[test_index]

else:
    # FALLBACK KE DATASET CSV JIKA TIF TIDAK ADA
    print("Menggunakan dataset CSV (dataset_klasifikasi_jatim.csv) karena TIF tidak ada.")
    df = pd.read_csv(base_path / 'dataset_klasifikasi_jatim.csv')
    X = df.drop(columns=['label']).values
    y = df['label'].values
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42, stratify=y)
    n_band = X.shape[1]

# TRAIN MODEL
rf = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1, class_weight='balanced')
rf.fit(X_train, y_train)
pred = rf.predict(X_test)
akurasi = accuracy_score(y_test, pred)
matriks = confusion_matrix(y_test, pred, labels=list(classes.values()))

print('\\n=== HASIL RANDOM FOREST ===')
print(f'Akurasi                     : {akurasi:.4f}')
print('Matriks kebingungan:')
print(matriks)
print('\\nClassification Report:')
print(classification_report(y_test, pred, target_names=list(classes.keys())))

# Jika TIF ada, prediksi seluruh raster
if TIF.exists():
    rf.fit(X, y)
    flat = arr.reshape(n_band, -1)
    hasil_flat = np.full(H * W, 255, dtype='uint8')
    valid_index = np.flatnonzero(valid.ravel())
    
    for start in range(0, len(valid_index), 200000):
        index = valid_index[start:start + 200000]
        hasil_flat[index] = rf.predict(flat[:, index].T).astype('uint8')
    hasil = hasil_flat.reshape(H, W)

    for key in ('blockxsize', 'blockysize', 'tiled', 'interleave'):
        profil.pop(key, None)
    profil.update(count=1, dtype='uint8', nodata=255, compress='lzw')
    with rasterio.open(OUT_KLAS, 'w', **profil) as dst:
        dst.write(hasil, 1)
    print(f'\\nTersimpan Raster Prediksi: {OUT_KLAS.resolve()}')"""
nb.cells[2].source = new_code_2

# Output JSON
with open(notebook_path, 'w', encoding='utf-8') as f:
    nbf.write(nb, f)
