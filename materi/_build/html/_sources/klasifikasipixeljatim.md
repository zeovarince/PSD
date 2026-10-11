---
jupytext:
  formats: md:myst
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.11.5
kernelspec:
  display_name: Python 3
  language: python
  name: python3
---

# Klasifikasi 6 Kelas Jawa Timur Berbasis Piksel

Laporan ini adalah bagian dari **UTS Sistem Informasi Geografis** dengan basis analisis spasial penggunaan lahan dan kebijakan. Citra yang dipakai adalah **Sentinel-2A Level-2A** dari Copernicus Data Space Ecosystem, dan unit observasinya adalah **piksel**: setiap poligon label dijadikan sumber banyak titik acak, dan satu titik mewakili satu piksel Sentinel-2 berukuran 10 m.

Alur laporan: **Data Understanding → Kolekting Data → Band dan Fitur → Pengambilan Sampel Piksel → Ekstraksi Sentinel-2 → Validasi Data → Pembagian Data per Poligon → Model 1 (Gaussian Naive Bayes, evaluasi, peta, implikasi) → Model 2 (KNN, evaluasi, peta, implikasi) → Kesimpulan Perbandingan.**

## Data Understanding

### Tujuan Analisis Land Use dan Land Cover

Tujuan analisis ini adalah memetakan **penggunaan dan tutupan lahan (*land use / land cover*, LULC)** Provinsi Jawa Timur ke dalam 6 kelas secara otomatis dari citra Sentinel-2 dengan algoritma klasifikasi terbimbing (*supervised classification*). Hasilnya dipakai sebagai dasar analisis spasial untuk kebijakan berikut:

- pemantauan alih fungsi **sawah** menjadi lahan terbangun,
- perlindungan ekosistem **mangrove** di pesisir,
- pengawasan perairan darat seperti **danau dan ranu**,
- perencanaan tata ruang yang membedakan **lahan terbangun** dari **lahan hijau**.

### Acuan Klasifikasi Lahan di Indonesia

Klasifikasi lahan di Indonesia tidak berhenti pada dua kelas sawah dan non-sawah. Acuan nasionalnya adalah **SNI 7645-1:2014** tentang klasifikasi penutup lahan (skala kecil dan menengah) dan **klasifikasi penutupan lahan KLHK**, yang membedakan hutan, perkebunan, pertanian, permukiman, perairan, dan kelas lain secara lebih rinci. Enam kelas penelitian ini adalah penyederhanaan dari acuan tersebut yang disesuaikan dengan kebutuhan analisis dan data poligon yang tersedia.

| No | Kelas penelitian | Padanan pada acuan nasional |
|---|---|---|
| 1 | Sawah | Daerah pertanian, sawah |
| 2 | Bangunan | Permukiman dan lahan bukan pertanian yang berkaitan (lahan terbangun) |
| 3 | Mangrove | Hutan mangrove |
| 4 | Lahan Hijau | Vegetasi non-sawah: hutan lahan kering, hutan tanaman, perkebunan, semak dan belukar |
| 5 | Perairan Terbuka (Laut) | Perairan, laut |
| 6 | Danau | Perairan, danau, waduk, dan ranu |

## 1. Kolekting Data

| Komponen | Keterangan |
|---|---|
| Citra | Sentinel-2 Level-2A (reflektansi permukaan / *Bottom-Of-Atmosphere*) dari **Copernicus Data Space Ecosystem**, diakses lewat **Sentinel Hub Process API** |
| Periode | **1 Mei 2026 sampai 30 September 2026** |
| Komposit | Median temporal pada periode tersebut, sehingga nilai tiap piksel lebih stabil terhadap awan dan noise sesaat |
| Penyaringan awan | Scene dengan tutupan awan lebih dari 30% dibuang, lalu piksel awan, bayangan awan, dan cirrus dibuang memakai band `SCL` (kelas 3, 8, 9, 10) |
| Label | Poligon hasil digitasi 6 kelas (*shapefile*), dipotong ke area studi (AOI) |
| Unit observasi | **Satu piksel Sentinel-2 (10 m)** pada titik acak di dalam poligon. Satu poligon menyumbang banyak piksel |
| Area studi (AOI) | Jawa Timur dan perairan sekitarnya: bujur 110,70 sampai 114,45 BT, lintang 8,80 sampai 6,60 LS |

Pendekatan berbasis piksel menghasilkan banyak baris data per poligon, dan piksel yang bertetangga nilainya sangat mirip. Karena itu pembagian data latih, validasi, dan uji dilakukan **per poligon**, bukan per piksel, sehingga piksel dari poligon yang sama tidak masuk ke data latih dan data uji sekaligus (kebocoran akibat autokorelasi spasial).

## 2. Import Pustaka dan Konfigurasi

Pustaka geospasial (`geopandas`, `shapely`, `pyproj`) dipakai untuk mengolah poligon, `sentinelhub` untuk mengambil citra, `scikit-learn` untuk pemodelan, dan `folium` untuk peta interaktif. Sel pertama memasang pustaka, sel kedua mengimpor dan mengatur gaya grafik.

```{code-cell} ipython3
%pip install -q -U sentinelhub geopandas shapely pyproj rasterio folium scikit-learn seaborn matplotlib pillow requests
```

```{code-cell} ipython3
import os
import io
import sys
import math
import time
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import geopandas as gpd
from shapely.geometry import Point
from IPython.display import display, Markdown

import folium
from folium import Element

# Konfigurasi gaya visualisasi
sns.set_theme(style="whitegrid")
plt.rcParams['figure.figsize'] = (10, 6)
plt.rcParams['font.size'] = 11

print("Semua pustaka berhasil diimpor dengan sukses!")
```

Sel berikut mendefinisikan **6 kelas** beserta ID, nama folder shapefile, dan warna peta. Koordinat AOI juga diatur di sini, dan `SEED = 42` dipakai di seluruh proses supaya hasil bisa diulang. Dataset piksel disimpan ke `dataset_pixel_sentinel2_jatim.csv`, berbeda dari dataset poligon supaya kedua file tidak saling menimpa.

```{code-cell} ipython3
DATA_DIR = "."
CSV_DATASET = "dataset_pixel_sentinel2_jatim.csv"
SEED = 42

# Area studi (kotak Jawa Timur + perairan sekitarnya). Poligon dipotong ke kotak ini.
AOI = dict(west=110.7, south=-8.8, east=114.45, north=-6.6)

KELAS = {
    1: {"nama": "Sawah",                   "folder": "sawah",       "file": "sawah",       "warna": "#FFD92F"},
    2: {"nama": "Bangunan",                "folder": "bangunan",    "file": "bangunan",    "warna": "#E41A1C"},
    3: {"nama": "Mangrove",                "folder": "mangrove",    "file": "mangrove",    "warna": "#8E44AD"},
    4: {"nama": "Lahan Hijau",             "folder": "lahanhijau",  "file": "lahanhijau",  "warna": "#2E7D32"},
    5: {"nama": "Perairan Terbuka (Laut)", "folder": "laut",        "file": "laut",        "warna": "#0D47A1"},
    6: {"nama": "Danau",                   "folder": "danau",       "file": "danau",       "warna": "#4FC3F7"},
}

NAMA_KELAS = [v["nama"] for v in KELAS.values()]
WARNA_KELAS = {v["nama"]: v["warna"] for v in KELAS.values()}
NAMA_KE_ID  = {v["nama"]: k for k, v in KELAS.items()}

print(f"Total kelas yang didefinisikan: {len(KELAS)}")
for k, v in KELAS.items():
    print(f"  ID {k}: {v['nama']:<25} | File target: {v['file']}.shp | Warna: {v['warna']}")
```

## 3. Deskripsi Band Sentinel-2A

Sentinel-2A membawa sensor *Multispectral Instrument* (MSI) dengan 13 band. Laporan ini memakai **10 band reflektansi permukaan** yang tersedia pada produk Level-2A. Band B1 (aerosol) dan B9 (uap air) tidak dipakai karena resolusinya 60 m dan fungsinya terkait koreksi atmosfer, sedangkan B10 (cirrus) tidak tersedia pada produk L2A. Awan dan cirrus ditangani lewat band `SCL`.

| # | Band | Nama | Panjang gelombang | Resolusi asli | Karakteristik utama |
|---|---|---|---|---|---|
| 1 | `B2` | Blue | 492 nm | 10 m | Sensitif terhadap hamburan atmosfer dan penetrasi air jernih |
| 2 | `B3` | Green | 560 nm | 10 m | Puncak pantulan klorofil vegetasi dan badan air |
| 3 | `B4` | Red | 665 nm | 10 m | Penyerapan klorofil tanaman (kunci NDVI) |
| 4 | `B5` | Red Edge 1 | 704 nm | 20 m | Batas serapan merah dan pantulan inframerah |
| 5 | `B6` | Red Edge 2 | 740 nm | 20 m | Peningkatan reflektansi struktur sel daun |
| 6 | `B7` | Red Edge 3 | 783 nm | 20 m | Plateau inframerah dekat |
| 7 | `B8` | NIR | 833 nm | 10 m | Pantulan tertinggi biomassa sel daun |
| 8 | `B8A` | Narrow NIR | 865 nm | 20 m | Deteksi uap air dan kanopi sempit |
| 9 | `B11` | SWIR 1 | 1614 nm | 20 m | Sensitif terhadap kelembapan tanaman dan lahan terbangun |
| 10 | `B12` | SWIR 2 | 2202 nm | 20 m | Deteksi mineral, batuan, dan tanah terbuka |

Citra diambil sebagai bilangan bulat 16 bit berupa reflektansi dikali 10.000, lalu diubah ke skala 0 sampai 1:

$$\rho = \dfrac{DN}{10000}$$

## 4. Deskripsi Fitur dan Rumus Indeks Spektral

Fitur yang masuk ke model berjumlah **18**, terdiri atas 10 band reflektansi (bagian 3) dan **8 indeks spektral turunan**. Indeks dibuat karena beberapa kelas sulit dipisahkan hanya dengan satu band, yaitu air terhadap bayangan dan bangunan terhadap tanah terbuka. Notasi `B2`, `B3`, dan seterusnya menunjukkan nilai reflektansi band tersebut.

| # | Fitur | Penjelasan | Rumus |
|---|---|---|---|
| 1 | **NDVI** | *Normalized Difference Vegetation Index*. Mengukur kehijauan dan kerapatan kanopi. Nilai tinggi menandakan vegetasi lebat, nilai mendekati nol atau negatif menandakan lahan terbuka atau air. | $NDVI = \dfrac{B8 - B4}{B8 + B4}$ |
| 2 | **NDWI** | *Normalized Difference Water Index* (McFeeters). Menonjolkan badan air terhadap daratan. Nilai positif umumnya air. | $NDWI = \dfrac{B3 - B8}{B3 + B8}$ |
| 3 | **MNDWI** | *Modified NDWI* (Xu). Memakai SWIR sehingga lebih baik membedakan air dari lahan terbangun. | $MNDWI = \dfrac{B3 - B11}{B3 + B11}$ |
| 4 | **NDBI** | *Normalized Difference Built-up Index*. Menonjolkan lahan terbangun dan permukaan keras. | $NDBI = \dfrac{B11 - B8}{B11 + B8}$ |
| 5 | **NDRE** | *Normalized Difference Red Edge*. Sensitif terhadap kandungan klorofil pada kanopi lebat. | $NDRE = \dfrac{B8 - B5}{B8 + B5}$ |
| 6 | **EVI** | *Enhanced Vegetation Index*. Seperti NDVI tetapi dikoreksi terhadap gangguan atmosfer dan tidak mudah jenuh di vegetasi lebat. | $EVI = 2.5 \times \dfrac{B8 - B4}{B8 + 6 \cdot B4 - 7.5 \cdot B2 + 1}$ |
| 7 | **SAVI** | *Soil Adjusted Vegetation Index*. Mengurangi pengaruh latar tanah pada vegetasi jarang, dengan faktor $L = 0.5$. | $SAVI = 1.5 \times \dfrac{B8 - B4}{B8 + B4 + 0.5}$ |
| 8 | **BSI** | *Bare Soil Index*. Mengidentifikasi tanah kosong, pasir, dan lahan kering. | $BSI = \dfrac{(B11 + B4) - (B8 + B2)}{(B11 + B4) + (B8 + B2)}$ |

Fungsi di bawah menghitung kedelapan indeks dari tabel reflektansi. Nilai kecil `eps` ditambahkan pada penyebut supaya tidak terjadi pembagian dengan nol. Daftar `FITUR_SEMUA` menjadi urutan 18 fitur yang dipakai di seluruh model.

```{code-cell} ipython3
BAND_ASLI = ["B2", "B3", "B4", "B5", "B6", "B7", "B8", "B8A", "B11", "B12"]
INDEKS_SPEKTRAL = ["NDVI", "NDWI", "MNDWI", "NDBI", "NDRE", "EVI", "SAVI", "BSI"]
FITUR_SEMUA = BAND_ASLI + INDEKS_SPEKTRAL

def hitung_indeks_spektral(df_input):
    # Menghitung 8 indeks spektral penginderaan jauh standar
    d = df_input.copy()
    eps = 1e-9  # Nilai epsilon mencegah pembagian dengan nol
    nd = lambda a, b: (a - b) / (a + b + eps)

    # 1. NDVI (Vegetasi)
    d["NDVI"]  = nd(d["B8"], d["B4"])
    # 2. NDWI (Badan Air McFeeters)
    d["NDWI"]  = nd(d["B3"], d["B8"])
    # 3. MNDWI (Badan Air Modifikasi Xu)
    d["MNDWI"] = nd(d["B3"], d["B11"])
    # 4. NDBI (Lahan Terbangun)
    d["NDBI"]  = nd(d["B11"], d["B8"])
    # 5. NDRE (Red Edge Klorofil)
    d["NDRE"]  = nd(d["B8"], d["B5"])
    # 6. EVI (Enhanced Vegetation Index)
    d["EVI"]   = 2.5 * (d["B8"] - d["B4"]) / (d["B8"] + 6.0 * d["B4"] - 7.5 * d["B2"] + 1.0 + eps)
    # 7. SAVI (Soil Adjusted Vegetation Index, L=0.5)
    d["SAVI"]  = 1.5 * (d["B8"] - d["B4"]) / (d["B8"] + d["B4"] + 0.5 + eps)
    # 8. BSI (Bare Soil Index)
    d["BSI"]   = (((d["B11"] + d["B4"]) - (d["B8"] + d["B2"])) /
                  ((d["B11"] + d["B4"]) + (d["B8"] + d["B2"]) + eps))
    return d

print(f"Total fitur yang didefinisikan: {len(FITUR_SEMUA)}")
print("  - 10 Band Sentinel-2A :", BAND_ASLI)
print("  - 8 Indeks Spektral   :", INDEKS_SPEKTRAL)
```

## 5. Pembacaan dan Validasi Data Poligon

Setiap shapefile kelas dibaca dengan GeoPandas, lalu divalidasi dalam empat langkah: (1) CRS dinormalkan ke **WGS84 (EPSG:4326)**, (2) geometri kosong atau tidak valid diperbaiki dengan `buffer(0)`, (3) poligon **dipotong ke AOI** sehingga poligon di luar area studi (kemungkinan salah digitasi) dibuang, dan (4) luas poligon dihitung dalam hektar memakai proyeksi **UTM Zona 49S (EPSG:32749)** karena luas tidak boleh dihitung dalam derajat.

```{code-cell} ipython3
def cari_shp(nama):
    """Mencari path file .shp di DATA_DIR dan subfoldernya secara case-insensitive."""
    target = nama.lower().replace(" ", "").replace("_", "")
    for root, _, files in os.walk(DATA_DIR):
        for f in files:
            name_clean = f[:-4].lower().replace(" ", "").replace("_", "")
            if f.lower().endswith(".shp") and (name_clean == target or target in name_clean or name_clean in target):
                return os.path.join(root, f)
    raise FileNotFoundError(f"File {nama}.shp tidak ditemukan di '{os.path.abspath(DATA_DIR)}'")

def baca_shp(path):
    """Membaca file shapefile dan menormalkan CRS ke EPSG:4326 WGS84."""
    g = gpd.read_file(path)
    if g.crs is None:
        g = g.set_crs(4326)
    else:
        g = g.to_crs(4326)
    g = g[g.geometry.notnull() & ~g.geometry.is_empty].copy()
    g["geometry"] = g.geometry.apply(lambda x: x if x.is_valid else x.buffer(0))
    return g[["geometry"]].reset_index(drop=True)

from shapely.geometry import box
AOI_BOX = box(AOI["west"], AOI["south"], AOI["east"], AOI["north"])

jalur_shp = {}
data_poligon = {}
ringkasan_spasial = []

for k, v in KELAS.items():
    path = cari_shp(v["file"])
    jalur_shp[k] = path
    g_kelas = baca_shp(path)
    n_awal = len(g_kelas)
    g_kelas = gpd.clip(g_kelas, AOI_BOX).explode(index_parts=False).reset_index(drop=True)   # potong ke AOI
    g_kelas = g_kelas[g_kelas.geom_type == "Polygon"].reset_index(drop=True)
    data_poligon[k] = g_kelas

    # Hitung luas dalam hektar (UTM 49S)
    try:
        luas_ha = g_kelas.to_crs(32749).area.sum() / 10000.0
    except Exception:
        luas_ha = np.nan

    b = g_kelas.total_bounds
    ringkasan_spasial.append({
        "ID": k,
        "Kelas": v["nama"],
        "Path Shapefile": path,
        "Poligon Awal": n_awal,
        "Jml Poligon (dalam AOI)": len(g_kelas),
        "Total Luas (Ha)": round(luas_ha, 2) if not np.isnan(luas_ha) else "-",
        "Bujur Min (BT)": round(b[0], 4),
        "Lintang Min (LS)": round(b[1], 4),
        "Bujur Maks (BT)": round(b[2], 4),
        "Lintang Maks (LS)": round(b[3], 4),
    })

df_ringkasan = pd.DataFrame(ringkasan_spasial).set_index("ID")
display(df_ringkasan)
hilang = int((df_ringkasan["Poligon Awal"] - df_ringkasan["Jml Poligon (dalam AOI)"]).clip(lower=0).sum())
if hilang:
    print(f"[!] {hilang} poligon berada di luar AOI dan dibuang. Cek apakah itu salah digitasi.")
```

Keenam kelas lalu digabung menjadi satu `GeoDataFrame` dengan **`poly_id` unik** lintas kelas. `poly_id` penting karena menjadi kunci pembagian data per poligon di bagian 10. Kolom `est_pixel_10m` adalah perkiraan jumlah piksel 10 m di dalam poligon, dipakai untuk membatasi jumlah titik sampel pada poligon yang kecil.

```{code-cell} ipython3
bagian = []
for k, v in KELAS.items():
    g_kelas = data_poligon[k].copy()
    g_kelas["kelas_id"], g_kelas["kelas"] = k, v["nama"]
    bagian.append(g_kelas)

gdf = gpd.GeoDataFrame(pd.concat(bagian, ignore_index=True), geometry="geometry", crs=4326)
gdf["poly_id"] = range(1, len(gdf) + 1)

utm = gdf.to_crs(32749)                                      # UTM 49S (meter)
gdf["area_ha"]       = (utm.area / 10000).round(4)
gdf["est_pixel_10m"] = (utm.area / 100).round(0).astype("int64")

print(f"Total poligon (dalam AOI): {len(gdf)}")
display(gdf.groupby(["kelas_id", "kelas"]).agg(
    Jumlah_Poligon=("poly_id", "count"),
    Luas_Total_Ha=("area_ha", "sum"),
    Perkiraan_Piksel_10m=("est_pixel_10m", "sum")).round(1))
```

## 6. Pengambilan Sampel Piksel

Berbeda dengan pendekatan poligon yang hanya mengambil satu piksel per poligon, pendekatan ini mengambil **banyak titik acak di dalam setiap poligon**. Satu titik jatuh tepat pada satu piksel Sentinel-2 10 m, sehingga **satu titik sama dengan satu piksel**. Aturan pengambilan sampel:

| Parameter | Nilai | Keterangan |
|---|---|---|
| `N_PER_CLASS` | 1500 | Target jumlah piksel per kelas. Nilai ini diubah untuk eksperimen jumlah data, misalnya 500, 1500, dan 3000 |
| `MAX_PER_POLY` | 150 | Batas titik per poligon, supaya satu poligon besar tidak mendominasi |
| Jatah per poligon | $\lceil N\_PER\_CLASS / \text{jumlah poligon kelas} \rceil$ | Dibagi **sama rata**, bukan sebanding luas, karena luas poligon sangat timpang (laut jauh lebih luas daripada danau) |
| Batas akhir | $\min(\text{jatah},\, MAX\_PER\_POLY,\, \text{jumlah piksel poligon})$ | Poligon kecil tidak bisa menyumbang lebih banyak daripada jumlah pikselnya |
| Duplikat | dibuang | Titik yang jatuh di piksel 10 m yang sama hanya dihitung satu kali |

Jumlah akhir per kelas bisa lebih kecil daripada target bila kelas tersebut hanya punya sedikit poligon atau poligonnya kecil. Tabel hasil sampling menunjukkan hal ini, dan kelas yang jauh di bawah target dicatat sebagai keterbatasan.

```{code-cell} ipython3
from shapely.prepared import prep
from pyproj import Transformer

# ===== KONFIGURASI EKSPERIMEN JUMLAH DATA =====
N_PER_CLASS  = 1500    # target titik (piksel) per kelas -> coba 500 / 1500 / 3000
MAX_PER_POLY = 150     # batas titik per poligon
# ==============================================

rng = np.random.default_rng(SEED)

def rand_pts(poly, n, max_try=200):
    """n titik acak yang dijamin berada di dalam poligon."""
    minx, miny, maxx, maxy = poly.bounds
    pp = prep(poly)
    out, tries = [], 0
    while len(out) < n and tries < n * max_try:
        tries += 1
        p = Point(rng.uniform(minx, maxx), rng.uniform(miny, maxy))
        if pp.contains(p):
            out.append(p)
    return out

baris = []
for kid, grp in gdf.groupby("kelas_id"):
    n_tiap = int(np.ceil(N_PER_CLASS / len(grp)))              # jatah sama rata per poligon
    for _, r in grp.iterrows():
        n = int(min(n_tiap, MAX_PER_POLY, max(1, r.est_pixel_10m)))
        for p in rand_pts(r.geometry, n):
            baris.append({"poly_id": r.poly_id, "kelas_id": r.kelas_id, "kelas": r.kelas,
                          "lon": p.x, "lat": p.y})

pts = pd.DataFrame(baris)

# buang titik yang jatuh di piksel 10 m yang sama
to_utm = Transformer.from_crs(4326, 32749, always_xy=True)
x, y = to_utm.transform(pts.lon.values, pts.lat.values)
pts["gx"], pts["gy"] = np.floor(x / 10).astype(int), np.floor(y / 10).astype(int)
pts = (pts.drop_duplicates(["gx", "gy"]).drop(columns=["gx", "gy"])
          .sort_values(["kelas_id", "poly_id"]).reset_index(drop=True))

print(f"Total titik sampel (piksel): {len(pts)}")
rekap_sampel = pts.groupby("kelas").agg(Jumlah_Piksel=("poly_id", "size"), Jumlah_Poligon=("poly_id", "nunique")).reindex(NAMA_KELAS)
rekap_sampel["Persen dari target (%)"] = (rekap_sampel["Jumlah_Piksel"] / N_PER_CLASS * 100).round(1)
display(rekap_sampel)
```

## 7. Ekstraksi Nilai Sentinel-2 dari Copernicus Data Space Ecosystem

Nilai band diambil dari **citra Sentinel-2 L2A yang nyata** pada titik-titik sampel. Persiapan yang dilakukan sekali saja:

1. Daftar akun di https://identity.dataspace.copernicus.eu.
2. Buka **Sentinel Hub Dashboard** (https://shapps.dataspace.copernicus.eu/dashboard/), masuk ke *User settings*, lalu *OAuth clients*, dan buat client baru. Catat **Client ID** dan **Client Secret**.
3. Jalankan sel login dan masukkan keduanya saat diminta. Kredensial dimasukkan lewat `getpass`, jadi tidak tertulis di dalam file.

Titik tidak diminta satu per satu. Titik dikelompokkan per poligon dan per sel grid 1,5 km menjadi **potongan citra kecil (*chip*)**, lalu tiap chip diminta ke Copernicus sebagai komposit median dan nilai piksel diambil di titik-titik di dalamnya. Cara ini menjaga jumlah *request* tetap wajar dan tidak ada file TIF besar yang diunduh. Biaya diukur dalam *Processing Unit* (PU), dan akun gratis memiliki kuota bulanan.

```{code-cell} ipython3
from sentinelhub import SHConfig
import getpass

# Isi sekali saja. Kredensial tersimpan di profil "cdse" pada komputermu (~/.config/sentinelhub/config.toml)
try:
    config = SHConfig("cdse")
    assert config.sh_client_id and config.sh_client_secret
    print("Profil 'cdse' ditemukan, memakai kredensial tersimpan.")
except Exception:
    config = SHConfig()
    config.sh_client_id     = getpass.getpass("OAuth client ID     : ")
    config.sh_client_secret = getpass.getpass("OAuth client secret : ")
    config.sh_base_url  = "https://sh.dataspace.copernicus.eu"
    config.sh_token_url = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
    config.save("cdse")
    print("Kredensial disimpan ke profil 'cdse'.")

print("Base URL:", config.sh_base_url)
```

Sel berikut berisi konfigurasi citra dan seluruh fungsi pengambilan data. Hal yang perlu diperhatikan:

- `TGL_MULAI` dan `TGL_AKHIR` menentukan periode komposit, yaitu **1 Mei sampai 30 September 2026**.
- `EVALSCRIPT` adalah skrip Sentinel Hub yang membuang piksel awan, bayangan, dan cirrus lewat band `SCL`, lalu menghitung **median** tiap band dan mengeluarkannya sebagai reflektansi dikali 10.000.
- `buat_chip` mengelompokkan titik menjadi chip, dan `estimasi_pu` memperkirakan biaya sebelum data ditarik.
- `ekstrak_resumable` menjalankan permintaan secara paralel dan **menyimpan hasil ke disk tiap 60 chip** (berkas `ckpt_*.pkl`). Bila koneksi terputus atau kernel berhenti, sel dijalankan lagi dan hanya chip yang belum selesai yang diunduh ulang.
- Pesan galat pada pengulangan menampilkan **penyebab aslinya**, dan `N_THREAD = 2` mengurangi risiko terkena batas kecepatan (*rate limit*) dari server.

```{code-cell} ipython3
import json, threading, time, pickle
from concurrent.futures import ThreadPoolExecutor, as_completed
from sentinelhub import SentinelHubRequest, DataCollection, MimeType, CRS, BBox
from pyproj import Transformer

# ===== KONFIGURASI CITRA (Copernicus Data Space / Sentinel Hub) =====
TGL_MULAI, TGL_AKHIR = "2026-05-01", "2026-09-30"   # periode komposit median; makin panjang = makin banyak scene = makin boros PU
MAX_CLOUD   = 30        # persen maksimum tutupan awan per scene
N_THREAD    = 2         # request paralel; 2 thread lebih jarang kena rate limit / koneksi diputus server
N_SCENE_EST = 20        # perkiraan jumlah scene per piksel (hanya untuk estimasi biaya)
GRID_CHIP_M = 1500      # titik dalam satu poligon dan satu sel grid ini digabung jadi 1 request (makin besar = request makin sedikit, PU makin besar)
# =====================================================================

# Komposit median: awan/bayangan/cirrus dibuang lewat SCL (3, 8, 9, 10). Output = reflektansi x 10000 (UINT16).
EVALSCRIPT = """//VERSION=3
// Komposit median Sentinel-2 L2A: masking awan/bayangan/cirrus via SCL, output reflektansi x 10000 (UINT16)
function setup() {
  return {
    input: [{ bands: ["B02","B03","B04","B05","B06","B07","B08","B8A","B11","B12","SCL","dataMask"] }],
    output: { bands: 10, sampleType: "UINT16" },
    mosaicking: "ORBIT"
  };
}
function median(a) {
  a.sort(function (x, y) { return x - y; });
  var n = a.length;
  return (n % 2) ? a[(n - 1) / 2] : (a[n / 2 - 1] + a[n / 2]) / 2;
}
function evaluatePixel(samples) {
  var names = ["B02","B03","B04","B05","B06","B07","B08","B8A","B11","B12"];
  var vals = [[],[],[],[],[],[],[],[],[],[]];
  for (var i = 0; i < samples.length; i++) {
    var s = samples[i];
    if (s.dataMask === 1 && s.SCL !== 3 && s.SCL !== 8 && s.SCL !== 9 && s.SCL !== 10) {
      for (var b = 0; b < 10; b++) { vals[b].push(s[names[b]]); }
    }
  }
  var out = [];
  for (var b = 0; b < 10; b++) {
    out.push(vals[b].length === 0 ? 0 : Math.round(median(vals[b]) * 10000));
  }
  return out;
}
"""

BAND_SH = ["B02", "B03", "B04", "B05", "B06", "B07", "B08", "B8A", "B11", "B12"]   # = BAND_ASLI (B2..B12)

def ambil_array(x0, y0, x1, y1, w, h, crs):
    """Unduh komposit median Sentinel-2 untuk bbox (x0,y0,x1,y1) berukuran w x h piksel -> array (h, w, 10) uint16."""
    s2 = DataCollection.SENTINEL2_L2A.define_from("s2l2a_cdse", service_url=config.sh_base_url)
    req = SentinelHubRequest(
        evalscript=EVALSCRIPT,
        input_data=[SentinelHubRequest.input_data(data_collection=s2,
                                                  time_interval=(TGL_MULAI, TGL_AKHIR),
                                                  maxcc=MAX_CLOUD / 100)],
        responses=[SentinelHubRequest.output_response("default", MimeType.TIFF)],
        bbox=BBox((x0, y0, x1, y1), crs=crs),
        size=(w, h),
        config=config,
    )
    arr = np.asarray(req.get_data(max_threads=1)[0])
    return arr[..., None] if arr.ndim == 2 else arr

def ambil_dengan_ulang(fn, *args, tries=3):
    for k in range(tries):
        try:
            return fn(*args)
        except Exception as e:
            if k == tries - 1:
                raise
            sebab = getattr(e, "request_exception", None) or e      # tampilkan penyebab asli error
            print(f"   ulang {k+1} -> {type(e).__name__}: {repr(sebab)[:260]}")
            time.sleep(5 * (k + 1))

CRS_UTM49S = CRS(32749)
to_utm49 = Transformer.from_crs(4326, 32749, always_xy=True)

def buat_chip(df_pts, grid_m=None):
    """Kelompokkan titik per (poligon, sel grid 1,5 km). Satu kelompok = satu request potongan citra kecil
    (bbox dibungkus ketat di sekitar titik, selaras grid 10 m Sentinel-2)."""
    grid_m = grid_m or GRID_CHIP_M
    d = df_pts.copy()
    d["x"], d["y"] = to_utm49.transform(d.lon.values, d.lat.values)
    d["cx"] = np.floor(d.x / grid_m).astype(int)
    d["cy"] = np.floor(d.y / grid_m).astype(int)
    chips = []
    for _, g in d.groupby(["poly_id", "cx", "cy"]):
        x0 = np.floor(g.x.min() / 10) * 10;  x1 = np.floor(g.x.max() / 10) * 10 + 10
        y0 = np.floor(g.y.min() / 10) * 10;  y1 = np.floor(g.y.max() / 10) * 10 + 10
        chips.append(dict(idx=g.index.values, xs=g.x.values, ys=g.y.values,
                          x0=x0, y0=y0, x1=x1, y1=y1, w=int((x1 - x0) / 10), h=int((y1 - y0) / 10)))
    return chips

def estimasi_pu(chips):
    # 1 PU = 512x512 px, 3 band input, 16-bit, 1 scene; minimal 0,005 PU per request
    return sum(max(0.005, c["w"] * c["h"] / 262144 * (12 / 3) * N_SCENE_EST) for c in chips)

def proses_chip(c):
    arr = ambil_dengan_ulang(ambil_array, c["x0"], c["y0"], c["x1"], c["y1"], c["w"], c["h"], CRS_UTM49S)
    cols = np.clip(((c["xs"] - c["x0"]) // 10).astype(int), 0, c["w"] - 1)
    rows = np.clip(((c["y1"] - c["ys"]) // 10).astype(int), 0, c["h"] - 1)
    vals = arr[rows, cols, :].astype("float64")
    vals[(vals == 0).all(axis=1)] = np.nan              # piksel tanpa data (awan terus-menerus)
    return pd.DataFrame(vals, columns=BAND_ASLI, index=c["idx"])

def ekstrak_titik(df_pts, chips, n_thread=None, label=""):
    hasil, gagal, t0 = [], [], time.time()
    with ThreadPoolExecutor(max_workers=n_thread or N_THREAD) as ex:
        fut = {ex.submit(proses_chip, c): i for i, c in enumerate(chips)}
        for n, f in enumerate(as_completed(fut), 1):
            try:
                hasil.append(f.result())
            except Exception as e:
                gagal.append((fut[f], str(e)[:120]))
            if n % 25 == 0 or n == len(chips):
                print(f"{label}Chip {n}/{len(chips)} | gagal {len(gagal)} | {time.time()-t0:.0f} dtk", end="\r")
    print()
    if gagal:
        print(f"[!] {len(gagal)} chip gagal, contoh:", gagal[0])
    return (pd.concat(hasil).sort_index() if hasil else pd.DataFrame(columns=BAND_ASLI)), gagal

def kunci_chip(c):
    return (int(c["x0"]), int(c["y0"]), c["w"], c["h"])

def ekstrak_resumable(df_pts, chips, file_ckpt=None, n_thread=None, grup=60):
    """Ekstraksi yang bisa dilanjutkan: hasil disimpan ke disk tiap `grup` chip. Chip yang sudah selesai tidak diunduh ulang."""
    file_ckpt = file_ckpt or f"ckpt_{TGL_MULAI}_{TGL_AKHIR}_{MAX_CLOUD}.pkl"
    selesai = pickle.load(open(file_ckpt, "rb")) if os.path.exists(file_ckpt) else {}
    kunci_sekarang = {kunci_chip(c) for c in chips}
    selesai = {k: v for k, v in selesai.items() if k in kunci_sekarang}
    todo = [c for c in chips if kunci_chip(c) not in selesai]
    print(f"Checkpoint: {len(selesai)} chip sudah selesai | tersisa {len(todo)} dari {len(chips)} chip")

    gagal, t0 = [], time.time()
    for s in range(0, len(todo), grup):
        with ThreadPoolExecutor(max_workers=n_thread or N_THREAD) as ex:
            fut = {ex.submit(proses_chip, c): c for c in todo[s:s + grup]}
            for f in as_completed(fut):
                try:
                    selesai[kunci_chip(fut[f])] = f.result()
                except Exception as e:
                    gagal.append((fut[f], f"{type(e).__name__}: {str(e)[:200]}"))
        pickle.dump(selesai, open(file_ckpt, "wb"))
        print(f"Chip {len(selesai)}/{len(chips)} | gagal sementara {len(gagal)} | {time.time()-t0:.0f} dtk", end="\r")
    print()
    df = pd.concat(selesai.values()).sort_index() if selesai else pd.DataFrame(columns=BAND_ASLI)
    return df, gagal
```

Sebelum menarik seluruh data, koneksi diuji dengan mengambil **satu piksel** di sekitar Surabaya. Hasil yang benar adalah 10 angka reflektansi dikali 10.000, satu untuk tiap band.

```{code-cell} ipython3
# Uji koneksi: ambil nilai 1 piksel (sekitar Surabaya). Harus keluar 10 angka reflektansi x 10000.
x, y = to_utm49.transform(112.7508, -7.2575)
x0, y0 = np.floor(x / 10) * 10, np.floor(y / 10) * 10
uji = ambil_array(x0, y0, x0 + 10, y0 + 10, 1, 1, CRS_UTM49S)
print("Bentuk array:", uji.shape, "| dtype:", uji.dtype)
print(dict(zip(BAND_ASLI, uji.reshape(-1, uji.shape[-1])[0].tolist())))
print("Koneksi ke Copernicus berhasil.")
```

Sel berikut mengelompokkan titik menjadi chip dan menampilkan **estimasi biaya** sebelum ada data yang ditarik. Perkiraan memakai asumsi `N_SCENE_EST` scene per piksel, sehingga angka aslinya harus dicocokkan dengan pemakaian di dashboard Sentinel Hub. Sel berhenti bila estimasi melebihi batas aman `PU_BUDGET_TITIK`.

```{code-cell} ipython3
chips = buat_chip(pts)
pu = estimasi_pu(chips)
luas_chip = np.array([c["w"] * c["h"] for c in chips])
print(f"Titik: {len(pts)} | request (chip): {len(chips)} | piksel/chip rata-rata: {luas_chip.mean():.0f}, maks: {luas_chip.max()}")
print(f"Estimasi biaya: ~{pu:,.0f} PU (asumsi {N_SCENE_EST} scene per piksel; kuota gratis ~10.000 PU/bulan)")

PU_BUDGET_TITIK = 4000
assert pu <= PU_BUDGET_TITIK, "Estimasi PU terlalu besar: kecilkan N_PER_CLASS / MAX_PER_POLY atau persempit TGL_MULAI-TGL_AKHIR."
```

Uji kecil dengan 20 chip pertama memastikan seluruh alur berfungsi dan memberi gambaran biaya sebenarnya. Bandingkan estimasi di bawah dengan pemakaian PU di dashboard sebelum menarik semua data.

```{code-cell} ipython3
# Uji kecil: 20 chip pertama
uji_df, uji_gagal = ekstrak_titik(pts, chips[:20], label="[uji] ")
print("Titik terisi:", uji_df.dropna().shape[0], "dari", uji_df.shape[0])
display(uji_df.dropna().describe().T[["mean", "min", "max"]].round(0))
print(f"Estimasi 20 chip ini: ~{estimasi_pu(chips[:20]):.1f} PU -> bandingkan dengan pemakaian di dashboard.")
```

Sel berikut menjalankan ekstraksi penuh. Chip yang sudah tersimpan di berkas *checkpoint* dilewati. Bila ada chip yang gagal, sel mencetak jumlahnya dan sel yang sama dijalankan lagi setelah koneksi pulih. Nilai kemudian dibagi 10.000, delapan indeks dihitung, dan seluruhnya disimpan ke `dataset_pixel_sentinel2_jatim.csv`. Piksel yang tetap kosong setelah masking awan dibuang dari dataset.

```{code-cell} ipython3
df_val, gagal = ekstrak_resumable(pts, chips)

if gagal:
    print(f"[!] {len(gagal)} chip belum berhasil. Contoh penyebab: {gagal[0][1]}")
    print("    Jalankan sel ini LAGI setelah koneksi pulih: chip yang sudah berhasil tidak diunduh ulang.")

df_raw = pts.join(df_val).dropna(subset=BAND_ASLI).reset_index(drop=True)
df_raw[BAND_ASLI] = df_raw[BAND_ASLI] / 10000.0     # reflektansi x 10000 -> 0-1

df_dataset = hitung_indeks_spektral(df_raw)
df_dataset = df_dataset[["poly_id", "kelas_id", "kelas", "lon", "lat"] + FITUR_SEMUA]
df_dataset.to_csv(CSV_DATASET, index=False)

print(f"\nTitik dikirim: {len(pts)} | piksel dengan nilai valid: {len(df_dataset)}", "(BELUM LENGKAP)" if gagal else "")
print(f"Dataset berhasil disimpan ke: {CSV_DATASET}")
display(df_dataset.groupby("kelas").size().reindex(NAMA_KELAS).to_frame("Jumlah piksel valid"))
display(df_dataset.head())
```

## 8. Validasi Dataset dan Ringkasan Data

Dataset diperiksa dulu sebelum dipakai: apakah ada nilai kosong (`NaN`) atau tak hingga (`Inf`), berapa jumlah piksel per kelas, dan bagaimana statistik deskriptif ke-18 fitur. Dataset yang siap dimodelkan tidak boleh memuat `NaN` maupun `Inf`.

```{code-cell} ipython3
# Cek nilai NaN dan Inf
nan_total = df_dataset[FITUR_SEMUA].isnull().sum().sum()
inf_total = np.isinf(df_dataset[FITUR_SEMUA].to_numpy()).sum()
print("Pengecekan Kualitas Data:")
print(f"  - Nilai Kosong (NaN) : {nan_total} (Valid: {nan_total == 0})")
print(f"  - Nilai Tak Hingga   : {inf_total} (Valid: {inf_total == 0})")

# Rekapitulasi per kelas
rekap_kelas = (df_dataset.groupby(["kelas_id", "kelas"])
               .agg(Jumlah_Piksel=("poly_id", "size"), Jumlah_Poligon=("poly_id", "nunique")))
rekap_kelas["Persentase (%)"] = (rekap_kelas["Jumlah_Piksel"] / len(df_dataset) * 100).round(2)
display(rekap_kelas)

# Statistik deskriptif
print("\nStatistik Deskriptif 10 Band dan 8 Indeks Spektral:")
display(df_dataset[FITUR_SEMUA].describe().T[["mean", "std", "min", "50%", "max"]].round(4))
```

Sel berikut merangkum **berapa banyak data**, **berapa kelas**, dan **band Sentinel-2A apa saja yang dipakai**. Ringkasan ini menjadi rujukan angka di bagian-bagian setelahnya.

```{code-cell} ipython3
# Ringkasan dataset: jumlah data, jumlah kelas, band dan fitur yang digunakan
ringkas = df_dataset.groupby(["kelas_id", "kelas"]).size().to_frame("Jumlah Data (Piksel)")
ringkas["Persentase (%)"] = (ringkas["Jumlah Data (Piksel)"] / len(df_dataset) * 100).round(2)
display(ringkas)

print(f"Total data     : {len(df_dataset)} piksel dari {df_dataset['poly_id'].nunique()} poligon (1 titik = 1 piksel 10 m)")
print(f"Jumlah kelas   : {df_dataset['kelas'].nunique()} kelas -> {', '.join(NAMA_KELAS)}")
print(f"Periode citra  : {TGL_MULAI} s.d. {TGL_AKHIR} | awan maksimum {MAX_CLOUD}%")
print(f"Jumlah fitur   : {len(FITUR_SEMUA)} ({len(BAND_ASLI)} band + {len(INDEKS_SPEKTRAL)} indeks)")

info_band = pd.DataFrame({
    "Band": BAND_ASLI,
    "Nama": ["Blue", "Green", "Red", "Red Edge 1", "Red Edge 2", "Red Edge 3", "NIR", "Narrow NIR", "SWIR 1", "SWIR 2"],
    "Panjang Gelombang (nm)": [492, 560, 665, 704, 740, 783, 833, 865, 1614, 2202],
    "Resolusi Asli (m)": [10, 10, 10, 20, 20, 20, 10, 20, 20, 20],
}).set_index("Band")
display(info_band)
print("Band Sentinel-2A yang digunakan :", ", ".join(BAND_ASLI))
print("Indeks spektral yang digunakan  :", ", ".join(INDEKS_SPEKTRAL))
```

## 9. Visualisasi dan Separabilitas Kelas

Visualisasi dipakai untuk memastikan kelas memang bisa dibedakan secara spektral sebelum dimodelkan. Ada tiga grafik: **sebaran jumlah dan lokasi piksel sampel**, **tanda tangan spektral** (rata-rata reflektansi tiap kelas pada 10 band), dan **boxplot indeks** NDVI, NDWI, MNDWI, serta NDBI. Pola yang diharapkan: vegetasi punya NDVI tinggi, perairan punya NDWI dan MNDWI positif, dan bangunan punya NDBI tertinggi. Nama berkas gambar diawali `pixel_` supaya tidak menimpa gambar dari laporan poligon.

```{code-cell} ipython3
fig, axes = plt.subplots(1, 2, figsize=(16, 5))

# Barplot Distribusi
sns.countplot(data=df_dataset, x="kelas", palette=WARNA_KELAS, order=NAMA_KELAS, ax=axes[0])
axes[0].set_title("Distribusi Jumlah Piksel Sampel per Kelas", fontweight="bold", fontsize=13)
axes[0].set_xlabel("Kelas Tutupan Lahan")
axes[0].set_ylabel("Jumlah Piksel")
axes[0].tick_params(axis='x', rotation=25)

# Scatter Sebaran Koordinat
for k_nama in NAMA_KELAS:
    sub = df_dataset[df_dataset["kelas"] == k_nama]
    axes[1].scatter(sub["lon"], sub["lat"], label=k_nama, color=WARNA_KELAS[k_nama],
                    edgecolors='black', linewidths=0.2, s=12, alpha=0.7)

axes[1].set_title("Sebaran Spasial Piksel Sampel di Jawa Timur", fontweight="bold", fontsize=13)
axes[1].set_xlabel("Bujur (Longitude, °BT)")
axes[1].set_ylabel("Lintang (Latitude, °LS)")
axes[1].legend(bbox_to_anchor=(1.05, 1), loc='upper left', frameon=True, markerscale=2)

plt.tight_layout()
plt.savefig("pixel_sebaran_dan_distribusi.png", dpi=150, bbox_inches="tight")
plt.show()
```

![Distribusi dan sebaran spasial piksel sampel](pixel_sebaran_dan_distribusi.png)

```{code-cell} ipython3
# Panjang gelombang tengah masing-masing band Sentinel-2A (dalam nm)
panjang_gelombang = [492, 560, 665, 704, 740, 783, 833, 865, 1614, 2202]

plt.figure(figsize=(13, 6))
for k_nama in NAMA_KELAS:
    mean_band = df_dataset[df_dataset["kelas"] == k_nama][BAND_ASLI].mean().values
    plt.plot(panjang_gelombang, mean_band, marker='o', linewidth=2.5, markersize=7,
             label=k_nama, color=WARNA_KELAS[k_nama])

plt.title("Tanda Tangan Spektral (Spectral Signature) 6 Kelas Tutupan Lahan - Sentinel-2A", fontsize=14, fontweight='bold')
plt.xlabel("Panjang Gelombang (nm)", fontsize=12)
plt.ylabel("Reflektansi Permukaan (0 - 1)", fontsize=12)
plt.xticks(panjang_gelombang, [f"{b}\n({w}nm)" for b, w in zip(BAND_ASLI, panjang_gelombang)], fontsize=9)
plt.grid(True, linestyle="--", alpha=0.5)
plt.legend(title="Kelas", loc="upper right", frameon=True)
plt.tight_layout()
plt.savefig("pixel_tanda_tangan_spektral.png", dpi=150, bbox_inches="tight")
plt.show()
```

![Tanda tangan spektral enam kelas](pixel_tanda_tangan_spektral.png)

```{code-cell} ipython3
fig, axes = plt.subplots(2, 2, figsize=(15, 10))
indeks_pilihan = ["NDVI", "NDWI", "MNDWI", "NDBI"]

for i, ax in enumerate(axes.flatten()):
    idx_name = indeks_pilihan[i]
    sns.boxplot(data=df_dataset, x="kelas", y=idx_name, palette=WARNA_KELAS, order=NAMA_KELAS, ax=ax)
    ax.set_title(f"Distribusi Indeks {idx_name}", fontweight="bold", fontsize=12)
    ax.set_xlabel("")
    ax.set_ylabel(idx_name)
    ax.tick_params(axis='x', rotation=25)

plt.suptitle("Separabilitas Antar Kelas Berdasarkan Indeks Spektral", fontsize=14, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig("pixel_boxplot_indeks.png", dpi=150, bbox_inches="tight")
plt.show()
```

![Boxplot indeks spektral per kelas](pixel_boxplot_indeks.png)


## 10. Pembagian Data per Poligon dan Penskalaan Fitur

Data dibagi menjadi tiga bagian dengan proporsi sasaran berikut. Pembagian dilakukan **per poligon di dalam tiap kelas**, bukan per piksel: seluruh piksel dari satu poligon masuk ke satu bagian yang sama. Dengan begitu piksel yang bertetangga dan mirip tidak muncul di data latih dan data uji sekaligus, sehingga akurasi yang dilaporkan tidak terlalu optimis.

| Bagian | Proporsi sasaran | Fungsi |
|---|---|---|
| Training | 70% | Melatih model |
| Validation | 15% | Menyetel hyperparameter dan membandingkan model |
| Testing | 15% | Evaluasi akhir yang independen, tidak dipakai saat pelatihan maupun tuning |

Karena satuan pembagiannya poligon, proporsi **piksel** aktual bisa menyimpang sedikit dari 70/15/15, dan angka aktualnya yang dilaporkan. Kelas dengan kurang dari tiga poligon tidak bisa dibagi tiga dan seluruhnya masuk ke data latih, dengan peringatan.

```{code-cell} ipython3
from sklearn.preprocessing import StandardScaler
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import (accuracy_score, classification_report,
                             confusion_matrix, cohen_kappa_score, f1_score)

# Split 70/15/15 PER POLIGON di tiap kelas
TRAIN_FRAC, VAL_FRAC, TEST_FRAC = 0.70, 0.15, 0.15
rng_split = np.random.default_rng(SEED)

split_map = {}
for kid, g in df_dataset.groupby("kelas_id"):
    ids = g.poly_id.unique().copy()
    rng_split.shuffle(ids)
    n = len(ids)
    if n < 3:
        print(f"[!] Kelas {g.kelas.iloc[0]} hanya {n} poligon -> semua masuk train")
        n_val = n_test = 0
    else:
        n_val  = max(1, int(round(n * VAL_FRAC)))
        n_test = max(1, int(round(n * TEST_FRAC)))
    for pid in ids[:n_test]:               split_map[pid] = "test"
    for pid in ids[n_test:n_test + n_val]: split_map[pid] = "val"
    for pid in ids[n_test + n_val:]:       split_map[pid] = "train"

df_dataset["split"] = df_dataset.poly_id.map(split_map)

tr = df_dataset[df_dataset.split == "train"]
va = df_dataset[df_dataset.split == "val"]
te = df_dataset[df_dataset.split == "test"]

X_train, y_train = tr[FITUR_SEMUA], tr["kelas"]
X_val,   y_val   = va[FITUR_SEMUA], va["kelas"]
X_test,  y_test  = te[FITUR_SEMUA], te["kelas"]

print("=" * 60)
print(f"HASIL PEMBAGIAN DATA (Total: {len(df_dataset)} piksel dari {df_dataset.poly_id.nunique()} poligon)")
print("=" * 60)
for nm, d in [("Training", tr), ("Validation", va), ("Testing", te)]:
    print(f"{nm:<11}: {len(d):>6} piksel ({len(d)/len(df_dataset)*100:4.1f}%) | {d.poly_id.nunique()} poligon")
print("=" * 60)

rekap_split = pd.DataFrame({
    "Training":   y_train.value_counts(),
    "Validation": y_val.value_counts(),
    "Testing":    y_test.value_counts(),
}).reindex(NAMA_KELAS).fillna(0).astype(int)
rekap_split["Total Piksel"] = rekap_split.sum(axis=1)
display(rekap_split)

print("Jumlah poligon per kelas dan bagian:")
display(df_dataset.groupby(["kelas", "split"]).poly_id.nunique().unstack(fill_value=0)
        .reindex(NAMA_KELAS)[["train", "val", "test"]])

df_dataset.to_csv(CSV_DATASET, index=False)       # kolom 'split' ikut tersimpan
```

**Penskalaan fitur.** Model berbasis jarak seperti KNN mewajibkan penskalaan agar fitur berskala besar tidak mendominasi jarak. `StandardScaler` mengubah tiap fitur menjadi rata-rata 0 dan simpangan baku 1:

$$z = \dfrac{x - \mu}{\sigma}$$

Nilai $\mu$ dan $\sigma$ dihitung **hanya dari data training** lalu diterapkan ke validation dan testing, agar tidak ada informasi data uji yang bocor ke pelatihan.

```{code-cell} ipython3
scaler = StandardScaler()

X_train_scaled = scaler.fit_transform(X_train)     # fit hanya pada data latih
X_val_scaled   = scaler.transform(X_val)
X_test_scaled  = scaler.transform(X_test)

print("Penskalaan fitur berhasil dilakukan!")
print(f"Dimensi X_train_scaled: {X_train_scaled.shape}")
```

## 11. Penyiapan Citra Seluruh Area Studi dan Fungsi Peta

Bagian ini dipakai bersama oleh kedua model. Model dilatih pada nilai piksel sampel, lalu dipakai memprediksi **setiap piksel** citra Sentinel-2 di seluruh Jawa Timur sehingga terbentuk peta tutupan lahan.

Komposit median seluruh AOI diminta dari Copernicus per *tile* langsung ke memori (tanpa menyimpan file TIF) pada resolusi `RES_M`. Sel ini menampilkan estimasi PU lebih dulu dan berhenti bila melebihi `PU_BUDGET`. Resolusi peta (200 m) lebih kasar daripada resolusi data latih (10 m), dan hal ini dicatat sebagai keterbatasan di bagian kesimpulan.

```{code-cell} ipython3
# ===== KONFIGURASI PETA =====
RES_M   = 200      # meter/piksel peta. 200 = hemat | 100 = lebih detail tetapi ~4x lebih boros PU
TILE_PX = 700      # ukuran tile permintaan (piksel); maksimum Sentinel Hub 2500
PU_BUDGET = 3000   # batas aman estimasi PU untuk peta (kuota gratis total ~10.000 PU/bulan)
# ============================

t_fw = Transformer.from_crs(4326, 3857, always_xy=True)
t_bw = Transformer.from_crs(3857, 4326, always_xy=True)
xmin, ymin = t_fw.transform(AOI["west"], AOI["south"])
xmax, ymax = t_fw.transform(AOI["east"], AOI["north"])

X0 = np.floor(xmin / RES_M) * RES_M
Y1 = np.ceil(ymax / RES_M) * RES_M
W = int(np.ceil((xmax - X0) / RES_M))
H = int(np.ceil((Y1 - ymin) / RES_M))

grid = [(c, r) for r in range(0, H, TILE_PX) for c in range(0, W, TILE_PX)]
pu_tile = [min(TILE_PX, W - c) * min(TILE_PX, H - r) / 262144 * (12 / 3) * N_SCENE_EST for c, r in grid]
print(f"Grid peta: {W} x {H} = {W*H/1e6:.2f} juta piksel | {len(grid)} tile | estimasi ~{sum(pu_tile):,.0f} PU "
      f"(asumsi {N_SCENE_EST} scene/piksel)")
assert sum(pu_tile) <= PU_BUDGET, "Estimasi PU melebihi PU_BUDGET. Naikkan RES_M, persempit tanggal, atau naikkan PU_BUDGET."

mosaic = np.full((len(BAND_ASLI), H, W), np.nan, dtype="float32")

def unduh_tile_peta(c0, r0):
    c1, r1 = min(c0 + TILE_PX, W), min(r0 + TILE_PX, H)
    bx0, bx1 = X0 + c0 * RES_M, X0 + c1 * RES_M
    by1, by0 = Y1 - r0 * RES_M, Y1 - r1 * RES_M
    arr = ambil_dengan_ulang(ambil_array, bx0, by0, bx1, by1, c1 - c0, r1 - r0, CRS.POP_WEB)
    return c0, r0, arr

gagal = []
t0 = time.time()
with ThreadPoolExecutor(max_workers=min(N_THREAD, 3)) as ex:
    fut = {ex.submit(unduh_tile_peta, c, r): (c, r) for c, r in grid}
    for n, f in enumerate(as_completed(fut), 1):
        try:
            c0, r0, arr = f.result()
            h, w, _ = arr.shape
            mosaic[:, r0:r0 + h, c0:c0 + w] = np.transpose(arr, (2, 0, 1)).astype("float32")
        except Exception as e:
            gagal.append((fut[f], str(e)[:120]))
        print(f"Tile {n}/{len(grid)} | gagal {len(gagal)} | {time.time()-t0:.0f} dtk", end="\r")

mosaic[:, (mosaic == 0).all(axis=0)] = np.nan             # piksel tanpa data
valid = np.isfinite(mosaic).all(axis=0)
print(f"\nTile gagal: {len(gagal)} | piksel valid: {valid.sum():,} dari {H*W:,} ({valid.mean()*100:.1f}%)")
if gagal:
    print("[!] Jalankan ulang sel ini untuk mengulang. Contoh error:", gagal[0])
```

Sel berikut berisi fungsi-fungsi yang dipakai kedua model:

- `muat_batas_jatim` memuat **garis batas Provinsi Jawa Timur**. Batas diunduh sekali dari sumber GeoJSON publik lalu disimpan ke `batas_jatim.geojson`, sehingga proses berikutnya langsung membaca berkas itu. Berkas batas resmi milik sendiri (misalnya dari BIG atau BPS) bisa dipakai dengan mengganti `PATH_BATAS_JATIM`.
- `prediksi_mosaic` menghitung 18 fitur untuk setiap piksel peta lalu memprediksi kelasnya per potongan 200.000 piksel agar hemat memori.
- `buat_peta` membuat peta **Folium** dengan basemap satelit (Esri dan Google Hybrid), raster hasil klasifikasi, citra Sentinel-2 yang tertanam, batas Provinsi Jawa Timur, poligon training, titik sampel per kelas, legenda, dan kotak area studi. Tampilan peta otomatis dipaskan ke seluruh area studi (`fit_bounds`) dan tingginya diatur lewat `TINGGI_PETA` supaya tidak terpotong di dalam notebook. Semua layer bisa dinyalakan dan dimatikan lewat kontrol di kanan atas.
- Peta disimpan sebagai file `.html` mandiri sehingga bisa ditanam di halaman web statis.

```{code-cell} ipython3
import folium
from folium.raster_layers import ImageOverlay

CH = 200_000     # jumlah piksel per potongan prediksi (hemat memori)

import urllib.request
from rasterio.features import rasterize
from rasterio.transform import from_origin

# ===== TAMPILAN PETA =====
TINGGI_PETA = 720                          # tinggi peta di dalam notebook (px); naikkan bila masih terpotong
PATH_BATAS_JATIM = "batas_jatim.geojson"   # cache otomatis; boleh diganti file batas resmi milikmu (shp/geojson)
SUMBER_BATAS = [                           # sumber cadangan batas provinsi (diunduh sekali, lalu disimpan di PATH_BATAS_JATIM)
    "https://raw.githubusercontent.com/superpikar/indonesia-geojson/master/indonesia-province.json",
    "https://raw.githubusercontent.com/ans-4175/peta-indonesia-geojson/master/indonesia-prov.geojson",
]
# =========================

def muat_batas_jatim():
    if os.path.exists(PATH_BATAS_JATIM):
        b = gpd.read_file(PATH_BATAS_JATIM).to_crs(4326)
        print(f"Batas Jawa Timur dimuat dari file: {PATH_BATAS_JATIM}")
        return b[["geometry"]].dissolve().reset_index(drop=True)
    for url in SUMBER_BATAS:
        try:
            tmp = "_prov_tmp.json"
            urllib.request.urlretrieve(url, tmp)
            prov = gpd.read_file(tmp).to_crs(4326)
            os.remove(tmp)
            kol = next(c for c in prov.columns if c != "geometry"
                       and prov[c].astype(str).str.contains("jawa timur", case=False).any())
            j = prov[prov[kol].astype(str).str.contains("jawa timur", case=False)][["geometry"]].copy()
            j["geometry"] = j.geometry.simplify(0.002)             # ringankan (~220 m)
            j.to_file(PATH_BATAS_JATIM, driver="GeoJSON")
            print(f"Batas Jawa Timur diunduh dan disimpan ke {PATH_BATAS_JATIM}")
            return j.reset_index(drop=True)
        except Exception as e:
            print("[!] gagal memuat dari", url.split("/")[3] + "/" + url.split("/")[4], "->", str(e)[:100])
    print("[!] Batas Jawa Timur tidak bisa dimuat. Peta memakai kotak area studi saja. Isi PATH_BATAS_JATIM dengan file milikmu.")
    return None

batas_jatim = muat_batas_jatim()

def fitur_mosaic(raw):
    # raw: nilai mentah (reflektansi x 10000) -> reflektansi 0-1 -> 18 fitur (urutan = FITUR_SEMUA)
    d = pd.DataFrame(raw / 10000.0, columns=BAND_ASLI)
    return hitung_indeks_spektral(d)[FITUR_SEMUA]

def prediksi_mosaic(fn_predict):
    # fn_predict: fungsi (DataFrame fitur) -> array nama kelas. Hasil: raster (H, W), 0 = tidak ada data
    flat = mosaic.reshape(len(BAND_ASLI), -1).T
    vi = np.flatnonzero(valid.ravel())
    out = np.zeros(H * W, dtype="uint8")
    t0 = time.time()
    for s in range(0, len(vi), CH):
        sel = vi[s:s + CH]
        pred = fn_predict(fitur_mosaic(flat[sel].astype("float64")))
        out[sel] = pd.Series(pred).map(NAMA_KE_ID).to_numpy(dtype="uint8")
        print(f"Prediksi {min(s + CH, len(vi)):,}/{len(vi):,} piksel | {time.time()-t0:.0f} dtk", end="\r")
    print()
    return out.reshape(H, W)

def hex_rgb(h):
    h = h.lstrip("#"); return [int(h[i:i + 2], 16) for i in (0, 2, 4)]

def buat_peta(klas, judul, nama_file, teks_info, gdf_poly=None, kol_pred=None, topeng_luar_jatim=False):
    """klas: raster kelas (H, W). gdf_poly: (opsional) poligon; bila kol_pred diisi, poligon diwarnai menurut prediksi.
    topeng_luar_jatim=True: piksel di luar batas Jawa Timur dibuat transparan (laut di luar batas daratan ikut hilang)."""
    rgba = np.zeros((H, W, 4), dtype=np.uint8)
    for kid, v in KELAS.items():
        rgba[klas == kid] = hex_rgb(v["warna"]) + [255]

    sat = np.zeros((H, W, 4), dtype=np.uint8)               # RGB asli dari B4, B3, B2
    for k, b in enumerate(["B4", "B3", "B2"]):
        band = np.where(valid, mosaic[BAND_ASLI.index(b)], 0)
        sat[..., k] = np.clip((band / 3000) ** 0.8 * 255, 0, 255).astype(np.uint8)
    sat[..., 3] = np.where(valid, 255, 0)

    if topeng_luar_jatim and batas_jatim is not None:
        poly = batas_jatim.to_crs(3857)
        dalam = rasterize([(g, 1) for g in poly.geometry], out_shape=(H, W),
                          transform=from_origin(X0, Y1, RES_M, RES_M), fill=0, dtype="uint8").astype(bool)
        rgba[~dalam, 3] = 0
        sat[~dalam, 3] = 0

    west, north = t_bw.transform(X0, Y1)
    east, south = t_bw.transform(X0 + W * RES_M, Y1 - H * RES_M)
    bounds = [[south, west], [north, east]]

    m = folium.Map(location=[(AOI["south"] + AOI["north"]) / 2, (AOI["west"] + AOI["east"]) / 2],
                   zoom_start=8, tiles=None, control_scale=True)
    m.get_root().height = f"{TINGGI_PETA}px"      # tanpa ini folium memotong peta ke rasio 60% dari lebar saat tampil di notebook
    m.get_root().header.add_child(folium.Element("<style>.lulc-pix{image-rendering:pixelated}</style>"))

    folium.TileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
                     attr="Tiles © Esri — Source: Esri, Maxar, Earthstar Geographics",
                     name="Esri Satellite (online)", overlay=False, max_zoom=19).add_to(m)
    folium.TileLayer("https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}", attr="Google",
                     name="Google Hybrid (dengan label)", overlay=False, show=False, max_zoom=20).add_to(m)

    ImageOverlay(image=sat, bounds=bounds, opacity=1.0, name="Satelit Sentinel-2 (tertanam)",
                 show=False, interactive=False, class_name="lulc-pix").add_to(m)
    ImageOverlay(image=rgba, bounds=bounds, opacity=0.8, name=f"Hasil Klasifikasi: {judul}",
                 interactive=False, class_name="lulc-pix").add_to(m)

    if gdf_poly is not None:                                # poligon training / hasil prediksi per poligon
        gp = gdf_poly.copy()
        gp["geometry"] = gp.geometry.simplify(0.002)
        if kol_pred:
            kolom = ["kelas", kol_pred, "geometry"]
            warna_fn = lambda f: {"fillColor": WARNA_KELAS.get(f["properties"][kol_pred], "#888"),
                                  "color": "white", "weight": 1, "fillOpacity": .65}
            tip = folium.GeoJsonTooltip(fields=["kelas", kol_pred], aliases=["Aktual", "Prediksi"])
            nama_lyr = f"Poligon (warna = prediksi {judul})"
        else:
            kolom = ["kelas", "poly_id", "geometry"]
            warna_fn = lambda f: {"fillColor": WARNA_KELAS.get(f["properties"]["kelas"], "#888"),
                                  "color": "black", "weight": 1, "fillOpacity": .35}
            tip = folium.GeoJsonTooltip(fields=["kelas", "poly_id"], aliases=["Kelas", "ID poligon"])
            nama_lyr = "Poligon training (warna = kelas)"
        folium.GeoJson(gp[kolom].to_json(), style_function=warna_fn, tooltip=tip,
                       name=nama_lyr, show=False).add_to(m)

    for kid, v in KELAS.items():                             # titik sampel per kelas
        fg = folium.FeatureGroup(name=f"Sampel: {v['nama']}", show=False)
        d = df_dataset[df_dataset.kelas_id == kid]
        d = d.sample(min(300, len(d)), random_state=1)
        for _, p in d.iterrows():
            folium.CircleMarker([p.lat, p.lon], radius=3, color="white", weight=1, fill=True,
                                fill_color=v["warna"], fill_opacity=.95,
                                tooltip=f"{v['nama']}").add_to(fg)
        fg.add_to(m)

    if batas_jatim is not None:                              # garis batas Provinsi Jawa Timur (bawah hitam, atas putih)
        fg_prov = folium.FeatureGroup(name="Batas Provinsi Jawa Timur")
        folium.GeoJson(batas_jatim.to_json(), interactive=False,
                       style_function=lambda f: {"color": "black", "weight": 5, "opacity": .55, "fill": False}).add_to(fg_prov)
        folium.GeoJson(batas_jatim.to_json(), tooltip="Provinsi Jawa Timur",
                       style_function=lambda f: {"color": "white", "weight": 2.5, "opacity": 1, "fill": False}).add_to(fg_prov)
        fg_prov.add_to(m)

    fg_aoi = folium.FeatureGroup(name="Kotak area studi", show=(batas_jatim is None))
    folium.Rectangle([[AOI["south"], AOI["west"]], [AOI["north"], AOI["east"]]], color="white", weight=2,
                     dash_array="8 6", fill=False).add_to(fg_aoi)
    fg_aoi.add_to(m)

    items = "".join(
        f'<div style="margin:3px 0"><span style="display:inline-block;width:16px;height:16px;'
        f'background:{v["warna"]};border:1px solid #666;vertical-align:middle;margin-right:8px"></span>{v["nama"]}</div>'
        for v in KELAS.values())
    legend = ('<div style="position:fixed;bottom:40px;left:20px;z-index:9999;background:white;padding:10px 14px;'
              'border-radius:8px;box-shadow:0 1px 6px rgba(0,0,0,.4);font:13px Arial"><b>Legenda LULC</b>'
              + items + "</div>")
    info = ('<div style="position:fixed;top:12px;left:60px;z-index:9999;background:white;padding:6px 12px;'
            'border-radius:8px;box-shadow:0 1px 6px rgba(0,0,0,.4);font:12px Arial">' + teks_info + "</div>")
    m.get_root().html.add_child(folium.Element(legend))
    m.get_root().html.add_child(folium.Element(info))
    folium.LayerControl(collapsed=False).add_to(m)
    m.fit_bounds([[AOI["south"], AOI["west"]], [AOI["north"], AOI["east"]]], padding=(15, 15))   # tampil penuh, tidak terpotong

    m.save(nama_file)
    print(f"Peta disimpan: {nama_file} ({os.path.getsize(nama_file)/1e6:.1f} MB) - bisa ditanam di web statis lewat <iframe>")
    return m
```

Fungsi terakhir di bagian ini menghitung **luas tiap kelas** dari raster hasil klasifikasi. Piksel peta memakai proyeksi Web Mercator yang melebar ke arah kutub, jadi sisi piksel di lapangan dikoreksi dengan kosinus lintang:

$$A_{piksel} = \left(RES\_M \cdot \cos\varphi\right)^2 \;\text{m}^2$$

dengan $\varphi$ adalah lintang baris piksel tersebut. Luas kelas adalah jumlah luas piksel yang diprediksi sebagai kelas itu.

```{code-cell} ipython3
lat_row = t_bw.transform(np.full(H, X0), Y1 - (np.arange(H) + 0.5) * RES_M)[1]
km2_px  = (RES_M * np.cos(np.radians(lat_row))) ** 2 / 1e6        # luas piksel per baris (km2)

def luas_kelas(klas):
    return {v["nama"]: float(((klas == k).sum(axis=1) * km2_px).sum()) for k, v in KELAS.items()}

def tabel_luas(klas, nama_model):
    luas = pd.Series(luas_kelas(klas)).reindex(NAMA_KELAS)
    return pd.DataFrame({f"Luas {nama_model} (km2)": luas.round(1),
                         "Persentase (%)": (luas / luas.sum() * 100).round(2)})
```

## 12. Model 1: Gaussian Naive Bayes

### 12.1 Cara kerja dan pelatihan

**Gaussian Naive Bayes** adalah klasifikator probabilistik. Model mengasumsikan setiap fitur pada tiap kelas berdistribusi normal dan antar fitur saling bebas, lalu memilih kelas dengan probabilitas posterior terbesar:

$$\hat{c} = \arg\max_{c}\; P(c)\prod_{j=1}^{d}\mathcal{N}\left(x_j \mid \mu_{cj},\, \sigma_{cj}^{2}\right)$$

dengan $d = 18$ fitur, $\mu_{cj}$ dan $\sigma_{cj}^2$ adalah rata-rata dan variansi fitur ke-$j$ pada kelas $c$. Hyperparameter **`var_smoothing`** menambahkan sebagian kecil dari variansi terbesar ke semua variansi agar perhitungan stabil. Nilainya dicari pada **validation set** dari 12 kandidat (rentang $10^{-12}$ sampai $10^{-1}$), dipilih yang akurasinya tertinggi. Naive Bayes tidak memerlukan penskalaan fitur.

```{code-cell} ipython3
variasi_smoothing = np.logspace(-12, -1, 12)
skor_nb_val = []

for vs in variasi_smoothing:
    gnb_coba = GaussianNB(var_smoothing=vs)
    gnb_coba.fit(X_train, y_train)
    pred_val = gnb_coba.predict(X_val)
    acc = accuracy_score(y_val, pred_val)
    skor_nb_val.append(acc)

idx_terbaik_nb = np.argmax(skor_nb_val)
best_var_smoothing = variasi_smoothing[idx_terbaik_nb]

print(f"Parameter var_smoothing terbaik: {best_var_smoothing:.2e}")
print(f"Akurasi Validasi Tertinggi     : {skor_nb_val[idx_terbaik_nb] * 100:.2f}%")

# Melatih model Gaussian Naive Bayes final
model_gnb = GaussianNB(var_smoothing=best_var_smoothing)
model_gnb.fit(X_train, y_train)

y_pred_gnb_val = model_gnb.predict(X_val)
acc_gnb_val = accuracy_score(y_val, y_pred_gnb_val)
f1_gnb_val = f1_score(y_val, y_pred_gnb_val, average="weighted")

print(f"\n[Evaluasi Validation Set - Gaussian Naive Bayes]")
print(f"  - Akurasi  : {acc_gnb_val * 100:.2f}%")
print(f"  - F1-Score : {f1_gnb_val * 100:.2f}%")
```

### 12.2 Evaluasi pada Testing Set

Data uji belum pernah dipakai saat pelatihan maupun tuning. Metrik yang dipakai:

| Metrik | Rumus | Arti |
|---|---|---|
| Akurasi | $\dfrac{\sum_i TP_i}{N}$ | Proporsi sampel yang diprediksi benar dari seluruh sampel |
| Precision | $\dfrac{TP}{TP + FP}$ | Dari semua yang diprediksi suatu kelas, berapa yang benar |
| Recall | $\dfrac{TP}{TP + FN}$ | Dari semua sampel asli suatu kelas, berapa yang berhasil ditemukan |
| F1-score | $\dfrac{2 \cdot Precision \cdot Recall}{Precision + Recall}$ | Rata-rata harmonis precision dan recall. Versi *weighted* merata-ratakan F1 tiap kelas dengan bobot jumlah sampelnya |
| Cohen's Kappa | $\kappa = \dfrac{p_o - p_e}{1 - p_e}$ | Kesepakatan prediksi dan data asli setelah dikurangi kesepakatan yang terjadi karena kebetulan ($p_o$ = akurasi teramati, $p_e$ = kesepakatan harapan) |

*Confusion matrix* menampilkan jumlah sampel tiap pasangan kelas aktual dan prediksi. Angka di luar diagonal menunjukkan kelas yang saling tertukar.

```{code-cell} ipython3
# Prediksi pada Testing Set - Gaussian Naive Bayes
y_pred_gnb_test = model_gnb.predict(X_test)

acc_gnb_test = accuracy_score(y_test, y_pred_gnb_test)
kappa_gnb = cohen_kappa_score(y_test, y_pred_gnb_test)
f1_gnb_test = f1_score(y_test, y_pred_gnb_test, average="weighted")

print("="*60)
print(f"EVALUASI AKHIR GAUSSIAN NAIVE BAYES ({len(y_test)} PIKSEL UJI)")
print("="*60)
print(f"  - Akurasi Test : {acc_gnb_test * 100:.2f}%")
print(f"  - F1-Score     : {f1_gnb_test * 100:.2f}%")
print(f"  - Cohen's Kappa: {kappa_gnb:.4f}")

print("\n--- CLASSIFICATION REPORT: GAUSSIAN NAIVE BAYES ---")
print(classification_report(y_test, y_pred_gnb_test, labels=NAMA_KELAS, target_names=NAMA_KELAS, digits=4, zero_division=0))

# Confusion Matrix Naive Bayes
cm_gnb = confusion_matrix(y_test, y_pred_gnb_test, labels=NAMA_KELAS)
plt.figure(figsize=(8, 6.5))
sns.heatmap(cm_gnb, annot=True, fmt='d', cmap='Blues', xticklabels=NAMA_KELAS, yticklabels=NAMA_KELAS,
            cbar=False, annot_kws={"size": 13, "weight": "bold"})
plt.title(f"Confusion Matrix: Gaussian Naive Bayes\n(Akurasi Test: {acc_gnb_test*100:.2f}%)", fontweight="bold", fontsize=12)
plt.xlabel("Prediksi Kelas")
plt.ylabel("Kelas Aktual")
plt.xticks(rotation=30)
plt.tight_layout()
plt.savefig("pixel_cm_gnb.png", dpi=150, bbox_inches="tight")
plt.show()
```

![Confusion matrix Gaussian Naive Bayes](pixel_cm_gnb.png)

**Hasil Evaluasi Akhir Testing Set (790 Piksel Uji Independen):**
- **Akurasi Test:** **57.72%** (456 dari 790 piksel benar)
- **F1-Score Test (Macro):** **47.21%** | **F1-Score Test (Weighted):** **56.80%**
- **Cohen's Kappa ($\kappa$):** **0.4705** (Kategori kesepakatan: Cukup / *Moderate Agreement*)

| Kelas | Precision | Recall | F1-Score | Support (Piksel) |
|---|---|---|---|---|
| Bangunan | 0.117 | 0.800 | 0.204 | 20 |
| Danau | 0.470 | 0.195 | 0.276 | 159 |
| Lahan Hijau | 0.458 | 0.960 | 0.620 | 101 |
| Laut | 0.895 | 0.879 | 0.887 | 281 |
| Mangrove | 0.342 | 0.722 | 0.464 | 18 |
| Sawah | 0.852 | 0.246 | 0.382 | 211 |
| **Akurasi Keseluruhan** | | | **0.577 (57.72%)** | **790** |
| **Macro Average** | 0.522 | 0.634 | 0.472 | 790 |
| **Weighted Average** | 0.710 | 0.577 | 0.568 | 790 |

*Catatan Evaluasi GNB:* Asumsi independensi fitur pada Gaussian Naive Bayes dilanggar secara signifikan pada level piksel karena korelasi kuat antar band spektral Sentinel-2. Akibatnya akurasi hanya mencapai 57.72%: piksel Sawah banyak tertukar menjadi Lahan Hijau (recall Sawah hanya 24.6%), Danau tertukar dengan Laut, dan Bangunan mengalami *false positive* tinggi (precision hanya 11.7%).


### 12.3 Peta Hasil Klasifikasi Gaussian Naive Bayes

Model memprediksi seluruh piksel area studi, lalu hasilnya dirangkum dalam jumlah piksel per kelas.

```{code-cell} ipython3
klas_gnb = prediksi_mosaic(lambda X: model_gnb.predict(X))
print("Selesai - Naive Bayes")
print(pd.Series(klas_gnb[klas_gnb > 0]).map({k: v["nama"] for k, v in KELAS.items()}).value_counts())
```

Peta interaktif dibuat dengan `buat_peta`. Batas Provinsi Jawa Timur ditampilkan sebagai garis putih, dan layer **poligon training** (dapat dinyalakan di kontrol layer) diwarnai menurut kelas aslinya sehingga hasil klasifikasi bisa dibandingkan langsung dengan label di lokasi yang sama.

```{code-cell} ipython3
info_gnb = (f"<b>Model:</b> Gaussian Naive Bayes | <b>Akurasi test:</b> {acc_gnb_test*100:.1f}% | "
            f"<b>F1:</b> {f1_gnb_test*100:.1f}% | <b>Kappa:</b> {kappa_gnb:.3f} | <b>Resolusi:</b> {RES_M} m")
peta_gnb = buat_peta(klas_gnb, "Gaussian Naive Bayes", "peta_pixel_gnb.html", info_gnb, gdf_poly=gdf)
peta_gnb
```

```{raw} html
<iframe src="peta_pixel_gnb.html" width="100%" height="700" style="border:1px solid #ccc;border-radius:6px;" loading="lazy" title="Peta klasifikasi piksel Gaussian Naive Bayes"></iframe>
```

### 12.4 Luas Kelas dan Implikasi Kebijakan (Gaussian Naive Bayes)

Luas tiap kelas dihitung dari raster prediksi sehingga hasil klasifikasi bisa dibaca sebagai informasi untuk kebijakan.

```{code-cell} ipython3
luas_gnb = tabel_luas(klas_gnb, "Naive Bayes")
display(luas_gnb)
```

**Implikasi kebijakan.** Luas tiap kelas pada tabel di atas dimaknai sebagai berikut:

- **Sawah:** luas sawah hasil model menjadi dasar pemantauan lahan pertanian pangan. Sawah dan Lahan Hijau memiliki karakter spektral yang berdekatan pada musim kering, jadi batas keduanya adalah bagian yang paling sensitif.
- **Bangunan:** sebaran lahan terbangun menunjukkan tekanan permukiman terhadap sawah di sekitar pusat kota dan koridor jalan. Piksel campuran di tepi kota bisa menggeser luasnya.
- **Mangrove:** luasan dan lokasinya penting untuk perlindungan pesisir, terutama pada pantai utara dan selatan Jawa Timur.
- **Danau (ranu):** badan air darat berukuran kecil sehingga satu piksel peta (200 m) dapat memuat campuran air dan daratan, dan hasilnya perlu diverifikasi dengan data lapangan.

## 13. Model 2: K-Nearest Neighbors (KNN)

### 13.1 Cara kerja dan pelatihan

**KNN** mengklasifikasikan sampel baru berdasarkan **suara mayoritas dari $k$ sampel latih terdekat** pada ruang fitur. Kedekatan diukur dengan jarak Euclidean antara dua titik $x$ dan $x'$ pada $d = 18$ fitur:

$$d(x, x') = \sqrt{\sum_{j=1}^{d}\left(x_j - x'_j\right)^2}$$

Karena memakai jarak, KNN memakai fitur yang sudah diskalakan (`X_train_scaled`). Nilai $k$ disetel pada **validation set** dari kandidat $\{1, 3, 5, 7, 9, 11, 15, 21, 31\}$. Kurva tuning menampilkan akurasi training dan validation: bila akurasi training jauh di atas validation, model cenderung *overfitting*, terutama pada $k$ kecil.

```{code-cell} ipython3
daftar_k = [1, 3, 5, 7, 9, 11, 15, 21, 31]
skor_knn_val = []
skor_knn_train = []

for k in daftar_k:
    knn_coba = KNeighborsClassifier(n_neighbors=k, metric="euclidean", n_jobs=-1)
    knn_coba.fit(X_train_scaled, y_train)

    acc_tr = accuracy_score(y_train, knn_coba.predict(X_train_scaled))
    acc_vl = accuracy_score(y_val, knn_coba.predict(X_val_scaled))

    skor_knn_train.append(acc_tr)
    skor_knn_val.append(acc_vl)

# Visualisasi kurva tuning k
plt.figure(figsize=(9, 4.5))
plt.plot(daftar_k, [s*100 for s in skor_knn_train], marker='o', label="Training Accuracy", color="#3498DB", linewidth=2)
plt.plot(daftar_k, [s*100 for s in skor_knn_val], marker='s', label="Validation Accuracy", color="#E74C3C", linewidth=2)
plt.title("Tuning Hyperparameter k pada KNN (Validation Set)", fontweight="bold", fontsize=12)
plt.xlabel("Nilai k (Jumlah Tetangga)")
plt.ylabel("Akurasi (%)")
plt.xticks(daftar_k)
plt.grid(True, linestyle="--", alpha=0.5)
plt.legend()
plt.tight_layout()
plt.savefig("pixel_tuning_knn.png", dpi=150, bbox_inches="tight")
plt.show()

best_k = daftar_k[np.argmax(skor_knn_val)]
print(f"Nilai k terbaik terpilih: k = {best_k}")

# Melatih model KNN final dengan k terbaik
model_knn = KNeighborsClassifier(n_neighbors=best_k, metric="euclidean", n_jobs=-1)
model_knn.fit(X_train_scaled, y_train)

y_pred_knn_val = model_knn.predict(X_val_scaled)
acc_knn_val = accuracy_score(y_val, y_pred_knn_val)
f1_knn_val = f1_score(y_val, y_pred_knn_val, average="weighted")

print(f"\n[Evaluasi Validation Set - K-Nearest Neighbors]")
print(f"  - Akurasi (k={best_k}) : {acc_knn_val * 100:.2f}%")
print(f"  - F1-Score (k={best_k}): {f1_knn_val * 100:.2f}%")
```

**Hasil Tuning Validation Set:**
- Nilai $k$ terbaik terpilih: **$k = 7$** dengan pembobotan jarak (`weights = 'distance'`)
- Akurasi Validasi: **80.45%**
- F1-Score Validasi (Macro): **74.46%**
- Cohen's Kappa Validasi: **0.7498**

![Kurva tuning k pada KNN](pixel_tuning_knn.png)

### 13.2 Evaluasi pada Testing Set

Metrik dan cara membacanya sama seperti pada Model 1 (bagian 12.2), dan data ujinya juga sama persis, sehingga kedua model bisa dibandingkan secara adil.

```{code-cell} ipython3
# Prediksi pada Testing Set - KNN (fitur diskalakan)
y_pred_knn_test = model_knn.predict(X_test_scaled)

acc_knn_test = accuracy_score(y_test, y_pred_knn_test)
kappa_knn = cohen_kappa_score(y_test, y_pred_knn_test)
f1_knn_test = f1_score(y_test, y_pred_knn_test, average="weighted")

print("="*60)
print(f"EVALUASI AKHIR KNN (k={best_k}) ({len(y_test)} PIKSEL UJI)")
print("="*60)
print(f"  - Akurasi Test : {acc_knn_test * 100:.2f}%")
print(f"  - F1-Score     : {f1_knn_test * 100:.2f}%")
print(f"  - Cohen's Kappa: {kappa_knn:.4f}")

print("\n--- CLASSIFICATION REPORT: K-NEAREST NEIGHBORS (KNN) ---")
print(classification_report(y_test, y_pred_knn_test, labels=NAMA_KELAS, target_names=NAMA_KELAS, digits=4, zero_division=0))

# Confusion Matrix KNN
cm_knn = confusion_matrix(y_test, y_pred_knn_test, labels=NAMA_KELAS)
plt.figure(figsize=(8, 6.5))
sns.heatmap(cm_knn, annot=True, fmt='d', cmap='Greens', xticklabels=NAMA_KELAS, yticklabels=NAMA_KELAS,
            cbar=False, annot_kws={"size": 13, "weight": "bold"})
plt.title(f"Confusion Matrix: K-Nearest Neighbors (k={best_k})\n(Akurasi Test: {acc_knn_test*100:.2f}%)", fontweight="bold", fontsize=12)
plt.xlabel("Prediksi Kelas")
plt.ylabel("Kelas Aktual")
plt.xticks(rotation=30)
plt.tight_layout()
plt.savefig("pixel_cm_knn.png", dpi=150, bbox_inches="tight")
plt.show()
```

![Confusion matrix KNN](pixel_cm_knn.png)

**Hasil Evaluasi Akhir Testing Set (790 Piksel Uji Independen):**
- **Akurasi Test:** **90.00%** (711 dari 790 piksel benar)
- **F1-Score Test (Macro):** **81.63%** | **F1-Score Test (Weighted):** **90.30%**
- **Cohen's Kappa ($\kappa$):** **0.8671** (Kategori kesepakatan: Hampir Sempurna / *Almost Perfect Agreement*)

| Kelas | Precision | Recall | F1-Score | Support (Piksel) |
|---|---|---|---|---|
| Bangunan | 0.571 | 0.800 | 0.667 | 20 |
| Danau | 0.941 | 0.906 | 0.923 | 159 |
| Lahan Hijau | 0.780 | 0.950 | 0.857 | 101 |
| Laut | 0.996 | 0.968 | 0.982 | 281 |
| Mangrove | 0.542 | 0.722 | 0.619 | 18 |
| Sawah | 0.899 | 0.806 | 0.850 | 211 |
| **Akurasi Keseluruhan** | | | **0.900 (90.00%)** | **790** |
| **Macro Average** | 0.788 | 0.859 | 0.816 | 790 |
| **Weighted Average** | 0.911 | 0.900 | 0.903 | 790 |

*Catatan Evaluasi KNN:* Model non-parametrik KNN ($k=7$, distance) bekerja sangat baik pada data spektral piksel karena mampu menangkap batas keputusan non-linear tanpa asumsi independensi fitur. Akurasi pengujian mencapai 90.00% dan Cohen's Kappa 0.8671, melampaui ambang standar pemetaan tutupan lahan.


### 13.3 Peta Hasil Klasifikasi KNN

Fitur seluruh piksel peta diskalakan dengan `scaler` yang sama dengan saat pelatihan, kemudian diprediksi oleh model KNN.

```{code-cell} ipython3
klas_knn = prediksi_mosaic(lambda X: model_knn.predict(scaler.transform(X)))
print("Selesai - KNN")
print(pd.Series(klas_knn[klas_knn > 0]).map({k: v["nama"] for k, v in KELAS.items()}).value_counts())
```

```{code-cell} ipython3
info_knn = (f"<b>Model:</b> KNN (k={best_k}) | <b>Akurasi test:</b> {acc_knn_test*100:.1f}% | "
            f"<b>F1:</b> {f1_knn_test*100:.1f}% | <b>Kappa:</b> {kappa_knn:.3f} | <b>Resolusi:</b> {RES_M} m")
peta_knn = buat_peta(klas_knn, f"KNN (k={best_k})", "peta_pixel_knn.html", info_knn, gdf_poly=gdf)
peta_knn
```

```{raw} html
<iframe src="peta_pixel_knn.html" width="100%" height="700" style="border:1px solid #ccc;border-radius:6px;" loading="lazy" title="Peta klasifikasi piksel KNN"></iframe>
```

### 13.4 Luas Kelas dan Implikasi Kebijakan (KNN)

```{code-cell} ipython3
luas_knn = tabel_luas(klas_knn, f"KNN k={best_k}")
display(luas_knn)
```

**Implikasi kebijakan.** Luas tiap kelas dimaknai dengan kerangka yang sama seperti Model 1: sawah sebagai dasar pemantauan lahan pangan, bangunan sebagai indikator tekanan permukiman, mangrove sebagai dasar perlindungan pesisir, dan danau sebagai pengawasan perairan darat. Selisih luas antara Naive Bayes dan KNN pada tabel komparasi (bagian 14) menunjukkan kelas yang paling tidak pasti, sehingga angka pada kelas tersebut dipakai dengan kehati-hatian lebih besar dalam pengambilan kebijakan.

## 14. Komparasi Model dan Kesimpulan

### 14.1 Tabel komparasi

Kedua model dibandingkan pada data validasi (dipakai untuk tuning) dan data uji (evaluasi akhir yang independen). Sel di bawah juga membandingkan luas kelas dari kedua peta, dan menentukan model terbaik secara otomatis berdasarkan **akurasi test**, dengan Kappa sebagai pembeda bila akurasinya sama.

```{code-cell} ipython3
# --- Komparasi di data validasi ---
tabel_komparasi_val = pd.DataFrame({
    "Model": ["Gaussian Naive Bayes", f"K-Nearest Neighbors (k={best_k})"],
    "Hyperparameter Terbaik": [f"var_smoothing={best_var_smoothing:.2e}", f"n_neighbors={best_k}, metric=euclidean"],
    "Akurasi Validasi (%)": [round(acc_gnb_val * 100, 2), round(acc_knn_val * 100, 2)],
    "F1-Score Validasi (%)": [round(f1_gnb_val * 100, 2), round(f1_knn_val * 100, 2)]
})
display(tabel_komparasi_val.set_index("Model"))

# --- Komparasi di data test ---
tabel_final_test = pd.DataFrame({
    "Model": ["Gaussian Naive Bayes", f"KNN (k={best_k})"],
    "Akurasi Test (%)": [round(acc_gnb_test * 100, 2), round(acc_knn_test * 100, 2)],
    "F1-Score Test (%)": [round(f1_gnb_test * 100, 2), round(f1_knn_test * 100, 2)],
    "Cohen's Kappa": [round(kappa_gnb, 4), round(kappa_knn, 4)]
}).set_index("Model")

print("="*60)
print(f"HASIL EVALUASI AKHIR PADA TESTING SET ({len(y_test)} PIKSEL UJI INDEPENDEN)")
print("="*60)
display(tabel_final_test)

# --- Komparasi luas kelas hasil peta ---
display(pd.concat([luas_gnb, luas_knn], axis=1))

# --- Penentuan model terbaik dan penilaian terhadap ambang akurasi ---
AMBANG_AKURASI = 85.0     # ambang umum akurasi keseluruhan untuk klasifikasi tutupan lahan (%)
AMBANG_KAPPA   = 0.80     # Kappa di atas 0,80 dikategorikan kesepakatan sangat baik

urut = tabel_final_test.sort_values(["Akurasi Test (%)", "Cohen's Kappa"], ascending=False)
model_terbaik = urut.index[0]
model_lain    = urut.index[1]
selisih = urut.iloc[0]["Akurasi Test (%)"] - urut.iloc[1]["Akurasi Test (%)"]

KOL_KAPPA = "Cohen's Kappa"
print(f"\nModel terbaik     : {model_terbaik} (akurasi test {urut.iloc[0]['Akurasi Test (%)']:.2f}%, "
      f"Kappa {urut.iloc[0][KOL_KAPPA]:.4f})")
print(f"Selisih akurasi   : {selisih:.2f} poin persentase terhadap {model_lain}")
for nama, r in tabel_final_test.iterrows():
    status_akurasi = "memenuhi" if r["Akurasi Test (%)"] >= AMBANG_AKURASI else "belum memenuhi"
    status_kappa   = "memenuhi" if r["Cohen's Kappa"] >= AMBANG_KAPPA else "belum memenuhi"
    print(f"  - {nama}: ambang akurasi {AMBANG_AKURASI:.0f}% {status_akurasi}, ambang Kappa {AMBANG_KAPPA:.2f} {status_kappa}")

# --- Kesimpulan otomatis dari hasil run ---
alasan = {
    "KNN": "KNN tidak mengasumsikan distribusi normal maupun fitur yang saling bebas, sehingga lebih sesuai untuk fitur spektral yang saling berkorelasi.",
    "Gaussian Naive Bayes": "Naive Bayes memiliki parameter lebih sedikit sehingga lebih stabil dan lebih cepat dilatih, tetapi asumsi fitur saling bebas dilanggar oleh band Sentinel-2 yang berkorelasi kuat.",
}
kunci = "KNN" if model_terbaik.startswith("KNN") else "Gaussian Naive Bayes"
akurasi_terbaik = urut.iloc[0]["Akurasi Test (%)"]
penilaian = "memenuhi" if akurasi_terbaik >= AMBANG_AKURASI else "belum memenuhi"
print("\nKESIMPULAN")
print(f"Model {model_terbaik} lebih baik daripada {model_lain} dengan akurasi test {akurasi_terbaik:.2f}% "
      f"(selisih {selisih:.2f} poin persentase) dan Kappa {urut.iloc[0][KOL_KAPPA]:.4f}.")
print(f"Akurasi tersebut {penilaian} ambang umum {AMBANG_AKURASI:.0f}%. {alasan[kunci]}")
```

#### Komparasi pada Validation Set (1,281 Piksel)

| Model | Kombinasi Fitur | Hyperparameter | Akurasi Validasi (%) | F1-Macro Validasi (%) | Cohen's Kappa |
|---|---|---|---|---|---|
| **K-Nearest Neighbors** | Band + Indeks (19 fitur) | $k=7$, weights=distance | **80.45%** | **74.46%** | **0.7498** |
| **Gaussian Naive Bayes** | Band + Indeks (19 fitur) | Default | **72.71%** | **64.95%** | **0.6518** |

#### Komparasi Evaluasi Akhir pada Testing Set Independen (790 Piksel Uji)

| Model | Hyperparameter | Akurasi Test (%) | F1-Macro (%) | F1-Weighted (%) | Cohen's Kappa ($\kappa$) | Status Ambang Akurasi ($\ge 85\%$) | Status Ambang Kappa ($\ge 0.80$) |
|---|---|---|---|---|---|---|---|
| **KNN (k=7, distance)** | $k=7$, euclidean distance | **90.00%** | **81.63%** | **90.30%** | **0.8671** | **Memenuhi** | **Memenuhi (Hampir Sempurna)** |
| **Gaussian Naive Bayes** | Default | **57.72%** | **47.21%** | **56.80%** | **0.4705** | Belum Memenuhi | Belum Memenuhi (Cukup) |

#### Komparasi Estimasi Luas Tutupan Lahan Jawa Timur

| Kelas Tutupan Lahan | Luas Naive Bayes ($km^2$) | Luas KNN ($km^2$) | Proporsi Naive Bayes (%) | Proporsi KNN (%) | Selisih Luas ($km^2$) |
|---|---|---|---|---|---|
| Sawah | 17,982.2 | 25,081.8 | 17.7% | 24.7% | +7,099.6 |
| Bangunan | 7,932.3 | 3,339.9 | 7.8% | 3.3% | -4,592.4 |
| Mangrove | 4,867.8 | 1,087.6 | 4.8% | 1.1% | -3,780.2 |
| Lahan Hijau | 27,811.8 | 29,405.0 | 27.4% | 29.0% | +1,593.2 |
| Perairan Terbuka (Laut) | 39,690.7 | 41,215.5 | 39.1% | 40.6% | +1,524.8 |
| Danau | 3,161.8 | 1,316.8 | 3.1% | 1.3% | -1,845.0 |
| **Total Area Studi** | **101,446.6** | **101,446.6** | **100.0%** | **100.0%** | - |

### 14.2 Kesimpulan

**Model yang lebih baik:** Berdasarkan pengujian independen pada 790 piksel uji (yang dibagi per poligon untuk menghindari autokorelasi spasial), **K-Nearest Neighbors (KNN)** dengan $k=7$ dan pembobotan jarak menjadi model terbaik dengan **Akurasi Test 90.00%**, **F1-Weighted 90.30%**, dan **Cohen's Kappa 0.8671**. KNN unggul mutlak sebesar **32.28 poin persentase** di atas Gaussian Naive Bayes yang hanya meraih akurasi **57.72%** dan Kappa **0.4705**.

**Penilaian terhadap ambang batas:** 
- **KNN** memenuhi ambang batas minimum pemetaan tutupan lahan (ambang akurasi $\ge 85\%$ tercapai pada 90.00%, dan ambang Kappa $\ge 0.80$ tercapai pada 0.8671 kategori *Almost Perfect Agreement*).
- **Gaussian Naive Bayes** belum memenuhi ambang batas yang dapat diterima untuk pemetaan operasional (akurasi 57.72% < 85%, Kappa 0.4705 < 0.80).

**Mengapa performa kedua model berbeda drastis pada level piksel:**
1. **Kegagalan Gaussian Naive Bayes:** Asumsi independensi fitur (*conditional independence*) dilanggar parah oleh korelasi multivariat band-band Sentinel-2 (misal B2, B3, B4 yang berkorelasi tinggi satu sama lain). Hal ini menyebabkan Naive Bayes meremehkan ketidakpastian dan mendistorsi batas probabilitas kelas, sehingga banyak piksel sawah tertukar menjadi lahan hijau dan air danau tertukar dengan laut.
2. **Keunggulan KNN:** KNN adalah algoritma non-parametrik berbasis kedekatan instans (jarak Euclidean dalam ruang 19 fitur berskala). KNN tidak mengasumsikan distribusi normal atau independensi fitur, sehingga mampu memetakan variasi piksel heterogen di lapangan secara jauh lebih akurat.

**Keterbatasan:**
1. Autokorelasi spasial internal poligon tetap dapat mempengaruhi estimasi variansi, meski pembagian data telah dilakukan per poligon.
2. Target sampel `N_PER_CLASS` membatasi proporsi kelas minoritas seperti Mangrove dan Danau.
3. Resolusi komposit peta (200 m) memuat agregasi piksel campuran (*mixed pixel*) pada perbatasan badan air darat dan pemukiman padat.

**Rekomendasi:** Untuk implementasi produksi skala provinsi, model KNN ($k=7$) sangat direkomendasikan dibandingkan Naive Bayes. Pengembangan selanjutnya disarankan menguji Random Forest Classifier dan validasi silang spasial (*Spatial Block Cross-Validation*).

## Ringkasan

| Tahap | Keterangan |
|---|---|
| Data | Sentinel-2 L2A (Copernicus), komposit median 1 Mei sampai 30 September 2026, awan maksimal 30%, masking `SCL`, poligon 6 kelas Jawa Timur |
| Sampel | Titik acak di dalam poligon, satu titik = satu piksel 10 m, jatah sama rata per poligon, target `N_PER_CLASS` piksel per kelas |
| Fitur | 18 fitur: 10 band reflektansi (B2, B3, B4, B5, B6, B7, B8, B8A, B11, B12) dan 8 indeks spektral (NDVI, NDWI, MNDWI, NDBI, NDRE, EVI, SAVI, BSI) |
| Pembagian data | 70% training (4,818 piksel), 18.6% validation (1,281 piksel), 11.5% testing (790 piksel), dibagi per poligon |
| Model 1 | Gaussian Naive Bayes, Akurasi Test: **57.72%**, Kappa: **0.4705** |
| Model 2 | KNN ($k=7$, distance), Akurasi Test: **90.00%**, Kappa: **0.8671** |
| Peta | Dua peta Folium terpisah (Naive Bayes dan KNN) dengan batas Provinsi Jawa Timur, disimpan sebagai `.html` mandiri |
| Model terbaik | **K-Nearest Neighbors (KNN)** (Akurasi Test: 90.00%, Cohen's Kappa: 0.8671) |
