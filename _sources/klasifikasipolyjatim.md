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

# Klasifikasi 6 Kelas Jawa Timur Berbasis Polygon

Laporan ini adalah bagian dari **UTS Sistem Informasi Geografis** dengan basis analisis spasial penggunaan lahan dan kebijakan. Citra yang dipakai adalah **Sentinel-2A Level-2A** dari Copernicus Data Space Ecosystem, dan unit observasinya adalah **poligon**: satu poligon mewakili satu sampel dengan satu piksel representatif.

Alur laporan: **Data Understanding → Kolekting Data → Band dan Fitur → Ekstraksi Berbasis Polygon → Validasi Data → Pembagian Data → Model 1 (Gaussian Naive Bayes, evaluasi, peta, implikasi) → Model 2 (KNN, evaluasi, peta, implikasi) → Kesimpulan Perbandingan.**

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
| Unit observasi | **Satu poligon = satu sampel**, nilai spektral diambil pada satu piksel 10 m di titik representatif poligon |
| Area studi (AOI) | Jawa Timur dan perairan sekitarnya: bujur 110,70 sampai 114,45 BT, lintang 8,80 sampai 6,60 LS |

Pendekatan berbasis poligon menghasilkan satu baris data per poligon, sehingga tidak ada piksel bertetangga yang saling mirip masuk ke data latih dan data uji sekaligus (autokorelasi spasial).

## 2. Import Pustaka dan Konfigurasi

Pustaka geospasial (`geopandas`, `shapely`, `pyproj`) dipakai untuk mengolah poligon, `sentinelhub` untuk mengambil citra, `scikit-learn` untuk pemodelan, dan `folium` untuk peta interaktif. Sel pertama memasang pustaka, sel kedua mengimpor dan mengatur gaya grafik.

```{code-cell} ipython3
%pip install -q -U sentinelhub geopandas shapely pyproj rasterio folium scikit-learn seaborn matplotlib pillow requests
```

```{code-cell} ipython3
import os
import sys
import math
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
from folium.plugins import MiniMap

# Konfigurasi gaya visualisasi
sns.set_theme(style="whitegrid")
plt.rcParams['figure.figsize'] = (10, 6)
plt.rcParams['font.size'] = 11

print("Semua pustaka berhasil diimpor dengan sukses!")
```

Sel berikut mendefinisikan **6 kelas** beserta ID, nama folder shapefile, dan warna peta. Koordinat AOI juga diatur di sini, dan `SEED = 42` dipakai di seluruh proses supaya hasil bisa diulang.

```{code-cell} ipython3
DATA_DIR = "."
CSV_DATASET = "dataset_sentinel2_jatim.csv"
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
    gdf = baca_shp(path)
    n_awal = len(gdf)
    gdf = gpd.clip(gdf, AOI_BOX).explode(index_parts=False).reset_index(drop=True)   # potong ke AOI
    gdf = gdf[gdf.geom_type == "Polygon"].reset_index(drop=True)
    data_poligon[k] = gdf

    # Hitung luas dalam hektar (UTM 49S)
    try:
        luas_ha = gdf.to_crs(32749).area.sum() / 10000.0
    except Exception:
        luas_ha = np.nan

    b = gdf.total_bounds
    ringkasan_spasial.append({
        "ID": k,
        "Kelas": v["nama"],
        "Path Shapefile": path,
        "Poligon Awal": n_awal,
        "Jml Poligon (dalam AOI)": len(gdf),
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


## 6. Ekstraksi Titik Koordinat Berbasis Poligon

Untuk setiap poligon diambil satu titik dengan `representative_point()`, yang **dijamin berada di dalam poligon**, berbeda dengan titik pusat (*centroid*) yang bisa jatuh di luar poligon berbentuk cekung. Titik inilah yang nanti dipakai untuk membaca nilai piksel Sentinel-2.

```{code-cell} ipython3
daftar_titik = []

for k, v in KELAS.items():
    gdf = data_poligon[k]
    for idx_poly, geom in enumerate(gdf.geometry):
        pt = geom.representative_point()
        daftar_titik.append({
            "kelas_id": k,
            "kelas": v["nama"],
            "poligon_id": idx_poly,
            "lon": pt.x,
            "lat": pt.y
        })

df_titik = pd.DataFrame(daftar_titik).reset_index(drop=True)
df_titik.index.name = "idx"

print(f"Total poligon terekstraksi dari 6 shapefile: {len(df_titik)}")
rekap_poligon = df_titik.groupby(["kelas_id", "kelas"]).size().to_frame("Jumlah Poligon")
display(rekap_poligon)
display(df_titik.head(10))
```

## 7. Ekstraksi Nilai Sentinel-2 dari Copernicus Data Space Ecosystem

Nilai band diambil dari **citra Sentinel-2 L2A yang nyata** pada titik representatif tiap poligon. Persiapan yang dilakukan sekali saja:

1. Daftar akun di https://identity.dataspace.copernicus.eu.
2. Buka **Sentinel Hub Dashboard** (https://shapps.dataspace.copernicus.eu/dashboard/), masuk ke *User settings*, lalu *OAuth clients*, dan buat client baru. Catat **Client ID** dan **Client Secret**.
3. Jalankan sel login dan masukkan keduanya saat diminta. Kredensial dimasukkan lewat `getpass`, jadi tidak tertulis di dalam file.

Karena satu poligon hanya butuh satu piksel, biaya pemrosesannya kecil, sekitar 0,005 *Processing Unit* (PU) per poligon.

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
- `buat_chip` mengelompokkan titik per poligon dan sel grid 1,5 km supaya jumlah *request* tetap sedikit, sedangkan `ekstrak_titik` menjalankannya paralel dengan pengulangan otomatis bila gagal.

```{code-cell} ipython3
import json, threading, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from sentinelhub import SentinelHubRequest, DataCollection, MimeType, CRS, BBox
from pyproj import Transformer

# ===== KONFIGURASI CITRA (Copernicus Data Space / Sentinel Hub) =====
TGL_MULAI, TGL_AKHIR = "2026-05-01", "2026-09-30"   # periode komposit median; makin panjang = makin banyak scene = makin boros PU
MAX_CLOUD   = 30        # persen maksimum tutupan awan per scene
N_THREAD    = 4         # request paralel (batas gratis ~300 request/menit)
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
            print("   ulang", k + 1, "->", str(e)[:140]); time.sleep(5 * (k + 1))

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

Sel berikut menjalankan ekstraksi penuh. `poly_id` dibuat unik lintas kelas (`kelas_id * 100000 + poligon_id`), titik dikelompokkan menjadi *chip*, dan chip yang gagal diulang satu kali. Nilai kemudian dibagi 10.000, delapan indeks dihitung, dan seluruhnya disimpan ke `dataset_sentinel2_jatim.csv`. Piksel yang tetap kosong setelah masking awan dibuang dari dataset.

```{code-cell} ipython3
# Titik representatif tiap poligon -> chip 1 piksel. poly_id dibuat unik lintas kelas.
df_pts = df_titik.copy()
df_pts["poly_id"] = df_pts["kelas_id"] * 100000 + df_pts["poligon_id"]

chips = buat_chip(df_pts)
print(f"Poligon: {len(df_pts)} | request (chip): {len(chips)} | estimasi ~{estimasi_pu(chips):,.1f} PU")

df_val, gagal = ekstrak_titik(df_pts, chips)
if gagal:                                           # ulangi chip yang gagal satu kali
    print("Mengulang chip yang gagal...")
    ulang, gagal2 = ekstrak_titik(df_pts, [chips[i] for i, _ in gagal], n_thread=2, label="[ulang] ")
    df_val = pd.concat([df_val, ulang]).sort_index()

df_raw = df_titik.join(df_val).dropna(subset=BAND_ASLI).reset_index(drop=True)
df_raw[BAND_ASLI] = df_raw[BAND_ASLI] / 10000.0     # reflektansi x 10000 -> 0-1

df_dataset = hitung_indeks_spektral(df_raw)
df_dataset.to_csv(CSV_DATASET, index=False)

print(f"\nPoligon dikirim: {len(df_titik)} | poligon dengan nilai valid: {len(df_dataset)}")
print(f"Dataset berhasil disimpan ke: {CSV_DATASET}")
display(df_dataset.groupby("kelas").size().reindex(NAMA_KELAS).to_frame("Jumlah poligon valid"))
display(df_dataset.head())
```

## 8. Validasi Dataset dan Ringkasan Data

Dataset diperiksa dulu sebelum dipakai: apakah ada nilai kosong (`NaN`) atau tak hingga (`Inf`), berapa jumlah data per kelas, dan bagaimana statistik deskriptif ke-18 fitur. Dataset yang siap dimodelkan tidak boleh memuat `NaN` maupun `Inf`.

```{code-cell} ipython3
# Cek nilai NaN dan Inf
nan_total = df_dataset[FITUR_SEMUA].isnull().sum().sum()
inf_total = np.isinf(df_dataset[FITUR_SEMUA].to_numpy()).sum()
print("Pengecekan Kualitas Data:")
print(f"  - Nilai Kosong (NaN) : {nan_total} (Valid: {nan_total == 0})")
print(f"  - Nilai Tak Hingga   : {inf_total} (Valid: {inf_total == 0})")

# Rekapitulasi per kelas
rekap_kelas = df_dataset.groupby(["kelas_id", "kelas"]).size().to_frame("Jumlah Poligon")
rekap_kelas["Persentase (%)"] = (rekap_kelas["Jumlah Poligon"] / len(df_dataset) * 100).round(2)
display(rekap_kelas)

# Statistik deskriptif
print("\nStatistik Deskriptif 10 Band dan 8 Indeks Spektral:")
display(df_dataset[FITUR_SEMUA].describe().T[["mean", "std", "min", "50%", "max"]].round(4))
```

Sel berikut merangkum **berapa banyak data**, **berapa kelas**, dan **band Sentinel-2A apa saja yang dipakai**. Ringkasan ini menjadi rujukan angka di bagian-bagian setelahnya.

```{code-cell} ipython3
# Ringkasan dataset: jumlah data, jumlah kelas, band dan fitur yang digunakan
ringkas = df_dataset.groupby(["kelas_id", "kelas"]).size().to_frame("Jumlah Data (Poligon)")
ringkas["Persentase (%)"] = (ringkas["Jumlah Data (Poligon)"] / len(df_dataset) * 100).round(2)
display(ringkas)

print(f"Total data     : {len(df_dataset)} poligon (1 poligon = 1 sampel)")
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

Visualisasi dipakai untuk memastikan kelas memang bisa dibedakan secara spektral sebelum dimodelkan. Ada tiga grafik: **sebaran jumlah dan lokasi poligon**, **tanda tangan spektral** (rata-rata reflektansi tiap kelas pada 10 band), dan **boxplot indeks** NDVI, NDWI, MNDWI, serta NDBI. Pola yang diharapkan: vegetasi punya NDVI tinggi, perairan punya NDWI dan MNDWI positif, dan bangunan punya NDBI tertinggi.

```{code-cell} ipython3
fig, axes = plt.subplots(1, 2, figsize=(16, 5))

# Barplot Distribusi
sns.countplot(data=df_dataset, x="kelas", palette=WARNA_KELAS, order=NAMA_KELAS, ax=axes[0])
axes[0].set_title("Distribusi Jumlah Poligon per Kelas", fontweight="bold", fontsize=13)
axes[0].set_xlabel("Kelas Tutupan Lahan")
axes[0].set_ylabel("Jumlah Poligon")
axes[0].tick_params(axis='x', rotation=25)

# Scatter Sebaran Koordinat
for k_nama in NAMA_KELAS:
    sub = df_dataset[df_dataset["kelas"] == k_nama]
    axes[1].scatter(sub["lon"], sub["lat"], label=k_nama, color=WARNA_KELAS[k_nama],
                    edgecolors='black', s=50, alpha=0.85)

axes[1].set_title("Sebaran Spasial Sampel Poligon di Jawa Timur", fontweight="bold", fontsize=13)
axes[1].set_xlabel("Bujur (Longitude, °BT)")
axes[1].set_ylabel("Lintang (Latitude, °LS)")
axes[1].legend(bbox_to_anchor=(1.05, 1), loc='upper left', frameon=True)

plt.tight_layout()
plt.savefig("sebaran_dan_distribusi.png", dpi=150, bbox_inches="tight")
plt.show()
```

![Distribusi dan sebaran spasial poligon](sebaran_dan_distribusi.png)

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
plt.savefig("tanda_tangan_spektral.png", dpi=150, bbox_inches="tight")
plt.show()
```

![Tanda tangan spektral enam kelas](tanda_tangan_spektral.png)

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
plt.savefig("boxplot_indeks.png", dpi=150, bbox_inches="tight")
plt.show()
```

![Boxplot indeks spektral per kelas](boxplot_indeks.png)


## 10. Pembagian Data dan Penskalaan Fitur

Data dibagi menjadi tiga bagian dengan `stratify`, sehingga proporsi tiap kelas tetap sama di setiap bagian:

| Bagian | Proporsi | Fungsi |
|---|---|---|
| Training | 70% | Melatih model |
| Validation | 15% | Menyetel hyperparameter dan membandingkan model |
| Testing | 15% | Evaluasi akhir yang independen, tidak dipakai saat pelatihan maupun tuning |

```{code-cell} ipython3
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import (accuracy_score, classification_report,
                             confusion_matrix, cohen_kappa_score, f1_score)

X = df_dataset[FITUR_SEMUA].copy()
y = df_dataset["kelas"].copy()

# Split 70% Training dan 30% Temp
X_train, X_temp, y_train, y_temp = train_test_split(
    X, y, test_size=0.30, random_state=SEED, stratify=y
)

# Split 30% Temp menjadi 15% Validation dan 15% Testing
X_val, X_test, y_val, y_test = train_test_split(
    X_temp, y_temp, test_size=0.50, random_state=SEED, stratify=y_temp
)

print("="*60)
print(f"HASIL PEMBAGIAN DATA POLIGON (Total: {len(df_dataset)} Poligon)")
print("="*60)
print(f"1. Training Set   (70%) : {len(X_train)} sampel")
print(f"2. Validation Set (15%) : {len(X_val)} sampel")
print(f"3. Testing Set    (15%) : {len(X_test)} sampel")
print("="*60)

rekap_split = pd.DataFrame({
    "Training (70%)": y_train.value_counts(),
    "Validation (15%)": y_val.value_counts(),
    "Testing (15%)": y_test.value_counts(),
    "Total Sampel": y.value_counts()
}).reindex(NAMA_KELAS)

display(rekap_split)
```


**Penskalaan fitur.** Model berbasis jarak seperti KNN mewajibkan penskalaan agar fitur berskala besar tidak mendominasi jarak. `StandardScaler` mengubah tiap fitur menjadi rata-rata 0 dan simpangan baku 1:

$$z = \dfrac{x - \mu}{\sigma}$$

Nilai $\mu$ dan $\sigma$ dihitung **hanya dari data training** lalu diterapkan ke validation dan testing, agar tidak ada informasi data uji yang bocor ke pelatihan. Sel yang sama juga menyiapkan `gdf_spasial`, yaitu tabel poligon asli beserta geometrinya, yang nanti dipakai untuk mewarnai poligon di peta menurut prediksi model.

```{code-cell} ipython3
scaler = StandardScaler()

X_train_scaled = scaler.fit_transform(X_train)
X_val_scaled   = scaler.transform(X_val)
X_test_scaled  = scaler.transform(X_test)
X_all_scaled   = scaler.transform(X)

print("Penskalaan fitur berhasil dilakukan!")
print(f"Dimensi X_train_scaled: {X_train_scaled.shape}")

# Menyiapkan GeoDataFrame Master berisi geometri poligon asli untuk visualisasi spasial
geometri_poligon = []
for idx, r in df_dataset.iterrows():
    k_id = int(r["kelas_id"])
    p_id = int(r["poligon_id"])
    geom_poly = data_poligon[k_id].iloc[p_id].geometry
    # Sederhanakan sedikit koordinat agar render peta cepat dan mulus
    geometri_poligon.append(geom_poly.simplify(0.0001))

gdf_spasial = gpd.GeoDataFrame(df_dataset.copy(), geometry=geometri_poligon, crs="EPSG:4326")
print(f"GeoDataFrame master spasial siap: {len(gdf_spasial)} poligon.")
```

## 11. Penyiapan Citra Seluruh Area Studi dan Fungsi Peta

Bagian ini dipakai bersama oleh kedua model. Model dilatih pada nilai satu piksel representatif tiap poligon, lalu dipakai memprediksi **setiap piksel** citra Sentinel-2 di seluruh Jawa Timur sehingga terbentuk peta tutupan lahan.

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

Sel berikut berisi tiga fungsi utama yang dipakai kedua model:

- `prediksi_mosaic` menghitung 18 fitur untuk setiap piksel peta lalu memprediksi kelasnya per potongan 200.000 piksel agar hemat memori.
- `buat_peta` membuat peta **Folium** dengan basemap satelit (Esri dan Google Hybrid), raster hasil klasifikasi, citra Sentinel-2 yang tertanam, poligon yang diwarnai menurut prediksi, titik sampel per kelas, legenda, dan batas area studi. Semua layer bisa dinyalakan dan dimatikan lewat kontrol di kanan atas.
- Peta disimpan sebagai file `.html` mandiri sehingga bisa ditanam di halaman web statis.

```{code-cell} ipython3
import folium
from folium.raster_layers import ImageOverlay

CH = 200_000     # jumlah piksel per potongan prediksi (hemat memori)

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

def buat_peta(klas, judul, nama_file, teks_info, gdf_poly=None, kol_pred=None):
    """klas: raster kelas (H, W). gdf_poly: (opsional) poligon; bila kol_pred diisi, poligon diwarnai menurut prediksi."""
    rgba = np.zeros((H, W, 4), dtype=np.uint8)
    for kid, v in KELAS.items():
        rgba[klas == kid] = hex_rgb(v["warna"]) + [255]

    sat = np.zeros((H, W, 4), dtype=np.uint8)               # RGB asli dari B4, B3, B2
    for k, b in enumerate(["B4", "B3", "B2"]):
        band = np.where(valid, mosaic[BAND_ASLI.index(b)], 0)
        sat[..., k] = np.clip((band / 3000) ** 0.8 * 255, 0, 255).astype(np.uint8)
    sat[..., 3] = np.where(valid, 255, 0)

    west, north = t_bw.transform(X0, Y1)
    east, south = t_bw.transform(X0 + W * RES_M, Y1 - H * RES_M)
    bounds = [[south, west], [north, east]]

    m = folium.Map(location=[(AOI["south"] + AOI["north"]) / 2, (AOI["west"] + AOI["east"]) / 2],
                   zoom_start=8, tiles=None, control_scale=True)
    m.get_root().header.add_child(folium.Element("<style>.lulc-pix{image-rendering:pixelated}</style>"))

    folium.TileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
                     attr="Tiles © Esri, Source: Esri, Maxar, Earthstar Geographics",
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

    fg_aoi = folium.FeatureGroup(name="Batas area studi")
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

# Simpan hasil prediksi untuk evaluasi dan peta spasial
gdf_spasial["pred_gnb"] = model_gnb.predict(X)

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
print(f"EVALUASI AKHIR GAUSSIAN NAIVE BAYES ({len(y_test)} SAMPEL POLIGON UJI)")
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
plt.savefig("cm_gnb.png", dpi=150, bbox_inches="tight")
plt.show()
```

![Confusion matrix Gaussian Naive Bayes](cm_gnb.png)


### 12.3 Peta Hasil Klasifikasi Gaussian Naive Bayes

Model memprediksi seluruh piksel area studi, lalu hasilnya dirangkum dalam jumlah piksel per kelas.

```{code-cell} ipython3
klas_gnb = prediksi_mosaic(lambda X: model_gnb.predict(X))
print("Selesai - Naive Bayes")
print(pd.Series(klas_gnb[klas_gnb > 0]).map({k: v["nama"] for k, v in KELAS.items()}).value_counts())
```

Peta interaktif dibuat dengan `buat_peta`. Layer **poligon** diwarnai menurut kelas prediksi, dan tooltip-nya menampilkan kelas aktual berdampingan dengan prediksi, jadi kesalahan model langsung terlihat di lokasinya.

```{code-cell} ipython3
info_gnb = (f"<b>Model:</b> Gaussian Naive Bayes | <b>Akurasi test:</b> {acc_gnb_test*100:.1f}% | "
            f"<b>F1:</b> {f1_gnb_test*100:.1f}% | <b>Kappa:</b> {kappa_gnb:.3f} | <b>Resolusi:</b> {RES_M} m")
peta_gnb = buat_peta(klas_gnb, "Gaussian Naive Bayes", "peta_gnb.html", info_gnb,
                     gdf_poly=gdf_spasial, kol_pred="pred_gnb")
peta_gnb
```

```{raw} html
<iframe src="peta_gnb.html" width="100%" height="620" style="border:1px solid #ccc;border-radius:6px;" loading="lazy" title="Peta klasifikasi Gaussian Naive Bayes"></iframe>
```

### 12.4 Luas Kelas dan Implikasi Kebijakan (Gaussian Naive Bayes)

Luas tiap kelas dihitung dari raster prediksi sehingga hasil klasifikasi bisa dibaca sebagai informasi untuk kebijakan.

```{code-cell} ipython3
luas_gnb = tabel_luas(klas_gnb, "Naive Bayes")
display(luas_gnb)
```

**Implikasi kebijakan.** Luas tiap kelas pada tabel di atas dimaknai sebagai berikut:

- **Sawah:** luas sawah hasil model menjadi dasar pemantauan lahan pertanian pangan. Sawah dan Lahan Hijau memiliki karakter spektral yang berdekatan pada musim kering, jadi batas keduanya adalah bagian yang paling sensitif.
- **Bangunan:** sebaran lahan terbangun menunjukkan tekanan permukiman terhadap sawah di sekitar pusat kota dan koridor jalan.
- **Mangrove:** luasan dan lokasinya penting untuk perlindungan pesisir, terutama pada pantai utara dan selatan Jawa Timur.
- **Danau (ranu):** badan air darat berukuran kecil sehingga satu piksel peta dapat memuat campuran air dan daratan, dan hasilnya perlu diverifikasi dengan data lapangan.

## 13. Model 2: K-Nearest Neighbors (KNN)

### 13.1 Cara kerja dan pelatihan

**KNN** mengklasifikasikan sampel baru berdasarkan **suara mayoritas dari $k$ sampel latih terdekat** pada ruang fitur. Kedekatan diukur dengan jarak Euclidean antara dua titik $x$ dan $x'$ pada $d = 18$ fitur:

$$d(x, x') = \sqrt{\sum_{j=1}^{d}\left(x_j - x'_j\right)^2}$$

Karena memakai jarak, KNN memakai fitur yang sudah diskalakan (`X_train_scaled`). Nilai $k$ disetel pada **validation set** dari kandidat $\{1, 3, 5, 7, 9, 11, 15\}$. Kurva tuning menampilkan akurasi training dan validation: bila akurasi training jauh di atas validation, model cenderung *overfitting*, terutama pada $k$ kecil.

```{code-cell} ipython3
daftar_k = [1, 3, 5, 7, 9, 11, 15]
skor_knn_val = []
skor_knn_train = []

for k in daftar_k:
    knn_coba = KNeighborsClassifier(n_neighbors=k, metric="euclidean")
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
plt.savefig("tuning_knn.png", dpi=150, bbox_inches="tight")
plt.show()

best_k = daftar_k[np.argmax(skor_knn_val)]
print(f"Nilai k terbaik terpilih: k = {best_k}")

# Melatih model KNN final dengan k terbaik
model_knn = KNeighborsClassifier(n_neighbors=best_k, metric="euclidean")
model_knn.fit(X_train_scaled, y_train)

# Simpan hasil prediksi untuk evaluasi dan peta spasial
gdf_spasial["pred_knn"] = model_knn.predict(X_all_scaled)

y_pred_knn_val = model_knn.predict(X_val_scaled)
acc_knn_val = accuracy_score(y_val, y_pred_knn_val)
f1_knn_val = f1_score(y_val, y_pred_knn_val, average="weighted")

print(f"\n[Evaluasi Validation Set - K-Nearest Neighbors]")
print(f"  - Akurasi (k={best_k}) : {acc_knn_val * 100:.2f}%")
print(f"  - F1-Score (k={best_k}): {f1_knn_val * 100:.2f}%")
```

![Kurva tuning k pada KNN](tuning_knn.png)

### 13.2 Evaluasi pada Testing Set

Metrik dan cara membacanya sama seperti pada Model 1 (bagian 12.2), dan data ujinya juga sama persis, sehingga kedua model bisa dibandingkan secara adil.

```{code-cell} ipython3
# Prediksi pada Testing Set - KNN (fitur diskalakan)
y_pred_knn_test = model_knn.predict(X_test_scaled)

acc_knn_test = accuracy_score(y_test, y_pred_knn_test)
kappa_knn = cohen_kappa_score(y_test, y_pred_knn_test)
f1_knn_test = f1_score(y_test, y_pred_knn_test, average="weighted")

print("="*60)
print(f"EVALUASI AKHIR KNN (k={best_k}) ({len(y_test)} SAMPEL POLIGON UJI)")
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
plt.savefig("cm_knn.png", dpi=150, bbox_inches="tight")
plt.show()
```

![Confusion matrix KNN](cm_knn.png)


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
peta_knn = buat_peta(klas_knn, f"KNN (k={best_k})", "peta_knn.html", info_knn,
                     gdf_poly=gdf_spasial, kol_pred="pred_knn")
peta_knn
```

```{raw} html
<iframe src="peta_knn.html" width="100%" height="620" style="border:1px solid #ccc;border-radius:6px;" loading="lazy" title="Peta klasifikasi KNN"></iframe>
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
print(f"HASIL EVALUASI AKHIR PADA TESTING SET ({len(y_test)} SAMPEL POLIGON INDEPENDEN)")
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
    "Gaussian Naive Bayes": "Naive Bayes memiliki parameter lebih sedikit sehingga lebih stabil pada data poligon yang berukuran kecil.",
}
kunci = "KNN" if model_terbaik.startswith("KNN") else "Gaussian Naive Bayes"
akurasi_terbaik = urut.iloc[0]["Akurasi Test (%)"]
penilaian = "memenuhi" if akurasi_terbaik >= AMBANG_AKURASI else "belum memenuhi"
print("\nKESIMPULAN")
print(f"Model {model_terbaik} lebih baik daripada {model_lain} dengan akurasi test {akurasi_terbaik:.2f}% "
      f"(selisih {selisih:.2f} poin persentase) dan Kappa {urut.iloc[0][KOL_KAPPA]:.4f}.")
print(f"Akurasi tersebut {penilaian} ambang umum {AMBANG_AKURASI:.0f}%. {alasan[kunci]}")
```

### 14.2 Kesimpulan

**Model yang lebih baik.** Penentuan model terbaik, selisih akurasi, dan penilaian terhadap ambang ditampilkan langsung oleh keluaran sel komparasi di atas, berdasarkan akurasi pada data uji dengan Kappa sebagai pembeda bila akurasinya sama.

**Berapa akurasi yang dianggap baik.** Dalam pemetaan tutupan lahan, **akurasi keseluruhan sekitar 85% atau lebih** umum dipakai sebagai ambang minimum yang dapat diterima. Untuk Cohen's Kappa, nilai **0,61 sampai 0,80** dikategorikan *substansial* dan **0,81 sampai 1,00** dikategorikan *hampir sempurna*. Akurasi tinggi saja belum cukup: recall tiap kelas juga diperiksa, karena akurasi keseluruhan bisa tetap tinggi walau satu kelas kecil seperti Danau atau Mangrove banyak salah.

**Keterbatasan.**

1. Dataset berbasis poligon kecil, hanya satu piksel per poligon, sehingga data uji juga kecil dan akurasi bisa berubah cukup besar bila pembagian data berbeda.
2. Periode citra hanya 1 Mei sampai 30 September 2026, sehingga perbedaan musim tanam sawah tidak tertangkap.
3. Resolusi peta (`RES_M`) lebih kasar daripada resolusi data latih 10 m, jadi piksel peta bisa berisi campuran beberapa kelas, terutama di pesisir dan danau kecil.
4. Kelas Lahan Hijau menggabungkan hutan, perkebunan, dan semak, sehingga bisa tertukar dengan Sawah dan Mangrove.

**Rekomendasi.** Tambahkan model lain (Random Forest dan Gradient Boosting) dan validasi silang berlapis (*stratified k-fold*) untuk membandingkan model yang lebih kuat, lalu perbanyak poligon latih pada kelas yang paling sering tertukar.

## Ringkasan

| Tahap | Keterangan |
|---|---|
| Data | Sentinel-2 L2A (Copernicus), komposit median 1 Mei sampai 30 September 2026, awan maksimal 30%, masking `SCL`, poligon 6 kelas Jawa Timur |
| Fitur | 18 fitur: 10 band reflektansi (B2, B3, B4, B5, B6, B7, B8, B8A, B11, B12) dan 8 indeks spektral (NDVI, NDWI, MNDWI, NDBI, NDRE, EVI, SAVI, BSI) |
| Pembagian data | 70% training, 15% validation, 15% testing, stratified |
| Model 1 | Gaussian Naive Bayes, `var_smoothing` disetel pada validation set |
| Model 2 | KNN, jarak Euclidean, $k$ disetel pada validation set |
| Model terbaik | Ditentukan oleh sel komparasi berdasarkan akurasi test dan Kappa |