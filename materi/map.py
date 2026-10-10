import json

NB_PATH = r'c:\Users\ARIEL\OneDrive\Documents\PSD\materi\klasifikasijatim.ipynb'

with open(NB_PATH, encoding='utf-8') as f:
    nb = json.load(f)

# === Jawa Timur batas koordinat yang benar ===
# Barat  : 110.7 (dekat Pacitan/Blitar)
# Timur  : 114.45 (Banyuwangi, sebelum Bali)
# Selatan: -8.8  (Samudra Hindia selatan)
# Utara  : -6.6  (Laut Jawa utara)

CELL_28_NEW = '''import math, io, requests
import folium
import numpy as np
import pandas as pd
from folium.raster_layers import ImageOverlay
from PIL import Image
from concurrent.futures import ThreadPoolExecutor

# AOI Jawa Timur (bukan termasuk Bali)
AOI = [110.7, -8.8, 114.45, -6.6]  # [lon_min, lat_min, lon_max, lat_max]

# ─── Unduh mosaik citra satelit Esri untuk AOI ───────────────────────────────
def ambil_satelit(aoi, z=10):
    n = 2 ** z
    def _xy(lon, lat):
        x = (lon + 180) / 360 * n
        y = (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n
        return x, y
    def _lon(x): return x / n * 360 - 180
    def _lat(y): return math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * y / n))))

    x0, y0 = _xy(aoi[0], aoi[3])
    x1, y1 = _xy(aoi[2], aoi[1])
    xa, xb = int(x0), int(x1)
    ya, yb = int(y0), int(y1)

    mosaik = Image.new("RGB", ((xb - xa + 1) * 256, (yb - ya + 1) * 256), (200, 200, 200))
    url = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"

    def _unduh(xy_):
        tx, ty = xy_
        try:
            r = requests.get(url.format(z=z, x=tx, y=ty),
                             headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
            return tx, ty, Image.open(io.BytesIO(r.content)).convert("RGB")
        except Exception:
            return tx, ty, None

    ubin = [(tx, ty) for tx in range(xa, xb + 1) for ty in range(ya, yb + 1)]
    with ThreadPoolExecutor(max_workers=8) as ex:
        for tx, ty, im in ex.map(_unduh, ubin):
            if im is not None:
                mosaik.paste(im, ((tx - xa) * 256, (ty - ya) * 256))

    bounds = [[_lat(yb + 1), _lon(xa)], [_lat(ya), _lon(xb + 1)]]
    return mosaik, bounds


# ─── Prediksi Piksel Raster (efek "Taburan" pixel-by-pixel) ──────────────────
def raster_ke_rgba(mosaik, model, scaler, tinggi=350):
    """
    Resize citra satelit RGB, sintesis 18 fitur Sentinel-2 dari nilai RGB-nya,
    prediksi pixel-by-pixel menggunakan model ML, hasilkan overlay RGBA.
    """
    w, h = mosaik.size
    lebar = max(1, int(tinggi * w / h))

    img_resized = mosaik.resize((lebar, tinggi))
    arr = np.array(img_resized).astype(np.float32) / 255.0

    R = arr[:, :, 0].flatten()
    G = arr[:, :, 1].flatten()
    B = arr[:, :, 2].flatten()

    # Aproksimasi band Sentinel-2 dari RGB
    B4 = R * 0.25           # Red
    B3 = G * 0.25           # Green
    B2 = B * 0.25           # Blue
    is_veg = (G > R + 0.02)
    B8 = np.where(is_veg, G * 0.45, R * 0.2)  # NIR tinggi di vegetasi
    B5 = B4 + 0.02
    B6 = np.clip(B8 - 0.05, 0, 1)
    B7 = np.clip(B8 - 0.02, 0, 1)
    B8A = np.clip(B8 + 0.01, 0, 1)
    B11 = R * 0.35 + 0.05
    B12 = R * 0.25 + 0.05

    eps = 1e-8
    df_img = pd.DataFrame({"B2": B2, "B3": B3, "B4": B4, "B5": B5,
                            "B6": B6, "B7": B7, "B8": B8, "B8A": B8A,
                            "B11": B11, "B12": B12})
    df_img["NDVI"]  = (B8 - B4) / (B8 + B4 + eps)
    df_img["NDWI"]  = (B3 - B8) / (B3 + B8 + eps)
    df_img["MNDWI"] = (B3 - B11) / (B3 + B11 + eps)
    df_img["NDBI"]  = (B11 - B8) / (B11 + B8 + eps)
    df_img["NDRE"]  = (B8 - B5) / (B8 + B5 + eps)
    df_img["EVI"]   = 2.5 * (B8 - B4) / (B8 + 6.0 * B4 - 7.5 * B2 + 1.0)
    df_img["SAVI"]  = ((B8 - B4) / (B8 + B4 + 0.5)) * 1.5
    df_img["BSI"]   = ((B11 + B4) - (B8 + B2)) / ((B11 + B4) + (B8 + B2) + eps)

    X_scaled = scaler.transform(df_img[FITUR_SEMUA])
    preds = model.predict(X_scaled)

    def hex_to_rgb(h):
        h = h.lstrip("#")
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

    lbl_warna = {}
    for k, v in KELAS.items():
        r, g, b = hex_to_rgb(v["warna"])
        lbl_warna[v["nama"]] = (r, g, b, 155)  # Alpha ~60%

    img_arr = np.zeros((tinggi, lebar, 4), dtype=np.uint8)
    preds_2d = preds.reshape((tinggi, lebar))
    for i in range(tinggi):
        for j in range(lebar):
            img_arr[i, j] = lbl_warna.get(preds_2d[i, j], (0, 0, 0, 0))

    return Image.fromarray(img_arr, mode="RGBA")


# ─── Fungsi utama pembuat peta ────────────────────────────────────────────────
def buat_peta_interaktif(gdf_pred, nama_model, judul_peta, nama_file_html):
    """
    Peta Folium bergaya "segmentasi taburan":
      • Basemap Esri Satellite + Google Hybrid
      • Satelit tertanam (tile mosaic offline)
      • Overlay klasifikasi ML pixel-by-pixel (RGBA)
      • Titik sampel per kelas (default: hidden)
      • Batas AOI Jawa Timur + Legenda
    """
    import os, base64

    lon_min, lat_min, lon_max, lat_max = AOI
    bounds_aoi = [[lat_min, lon_min], [lat_max, lon_max]]

    # Unduh/load satelit tertanam
    sat_file = "satelit_aoi_z10.jpeg"
    if os.path.exists(sat_file):
        mosaik = Image.open(sat_file)
        bounds_sat = [[lat_min, lon_min], [lat_max, lon_max]]
    else:
        print(f"Mengunduh tile satelit AOI Jawa Timur (z=10)... mohon tunggu.")
        mosaik, bounds_sat = ambil_satelit(AOI, z=10)
        mosaik.save(sat_file, quality=85)
        print(f"Satelit disimpan: {sat_file}")

    sat_bytes = io.BytesIO()
    mosaik.save(sat_bytes, format="JPEG", quality=85)
    sat_b64 = "data:image/jpeg;base64," + base64.b64encode(sat_bytes.getvalue()).decode()

    # Prediksi pixel-by-pixel
    model = model_gnb if nama_model == "gnb" else model_knn
    print(f"Membuat overlay klasifikasi {nama_model.upper()} pixel-by-pixel...")
    rgba_img = raster_ke_rgba(mosaik, model, scaler, tinggi=350)
    rgba_bytes = io.BytesIO()
    rgba_img.save(rgba_bytes, format="PNG")
    rgba_b64 = "data:image/png;base64," + base64.b64encode(rgba_bytes.getvalue()).decode()
    print("Overlay selesai dibuat.")

    # Inisialisasi peta
    pusat = [(lat_min + lat_max) / 2, (lon_min + lon_max) / 2]
    peta  = folium.Map(location=pusat, zoom_start=8, tiles=None, control_scale=True)

    # Basemap online
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Tiles &copy; Esri &mdash; Source: Esri, Maxar, Earthstar Geographics",
        name="Esri Satellite (online)", max_zoom=19, overlay=False, control=True,
    ).add_to(peta)
    folium.TileLayer(
        tiles="https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}",
        attr="Google Hybrid", name="Google Hybrid (dengan label)",
        max_zoom=20, overlay=False, control=True, show=False,
    ).add_to(peta)

    # Layer satelit tertanam
    ImageOverlay(image=sat_b64, bounds=bounds_sat, opacity=1.0,
                 name="Satelit (tertanam)", interactive=False, zindex=1).add_to(peta)

    # Layer overlay klasifikasi
    ImageOverlay(image=rgba_b64, bounds=bounds_sat, opacity=0.68,
                 name=f"Hasil Klasifikasi: {judul_peta}",
                 interactive=False, zindex=5).add_to(peta)

    # Titik sampel per kelas (tersembunyi by default)
    for k, v in KELAS.items():
        grup = folium.FeatureGroup(name=f"Sampel: {v['nama']}", show=False)
        sub  = gdf_pred[gdf_pred["kelas"] == v["nama"]]
        for _, row in sub.iterrows():
            cx, cy = row.geometry.centroid.x, row.geometry.centroid.y
            folium.CircleMarker(
                location=[cy, cx], radius=4, color="white", weight=1,
                fill=True, fill_color=v["warna"], fill_opacity=0.9,
                popup=f"{v['nama']} ({cx:.4f}, {cy:.4f})"
            ).add_to(grup)
        grup.add_to(peta)

    # Batas AOI
    grup_aoi = folium.FeatureGroup(name="Batas area studi")
    folium.Rectangle(bounds_aoi, color="white", weight=1.5,
                     fill=False, dash_array="6").add_to(grup_aoi)
    grup_aoi.add_to(peta)

    # Legenda LULC
    items = "".join(
        f\'<div style="margin:2px 0"><span style="display:inline-block;width:14px;height:14px;\'\
        f\'background:{v["warna"]};border:1px solid #333;margin-right:6px;vertical-align:middle"></span>{v["nama"]}</div>\'
        for v in KELAS.values()
    )
    legend = (
        f\'<div style="position:fixed;bottom:30px;left:30px;z-index:9999;background:rgba(255,255,255,0.92);\'\
        f\'padding:10px 14px;border:1px solid #888;border-radius:8px;font:13px Arial;box-shadow:2px 2px 6px rgba(0,0,0,.3);">\'\
        f\'<b>Legenda LULC</b><br>{items}</div>\'
    )
    peta.get_root().html.add_child(folium.Element(legend))

    folium.LayerControl(collapsed=False).add_to(peta)
    peta.fit_bounds(bounds_aoi)

    peta.save(nama_file_html)
    print(f"Peta disimpan: {nama_file_html}")
    return peta


# Tampilkan peta GNB
peta_gnb = buat_peta_interaktif(gdf_spasial, "gnb", "Gaussian Naive Bayes", "peta_gnb.html")
peta_gnb
'''

CELL_32_NEW = '''# Tampilkan peta KNN
peta_knn = buat_peta_interaktif(gdf_spasial, "knn", "K-Nearest Neighbors", "peta_knn.html")
peta_knn
'''

nb['cells'][28]['source'] = [CELL_28_NEW]
nb['cells'][28]['outputs'] = []
nb['cells'][28]['execution_count'] = None

nb['cells'][32]['source'] = [CELL_32_NEW]
nb['cells'][32]['outputs'] = []
nb['cells'][32]['execution_count'] = None

with open(NB_PATH, 'w', encoding='utf-8') as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

print("Berhasil! Cell 28 dan Cell 32 diperbarui dengan AOI Jawa Timur yang benar.")

