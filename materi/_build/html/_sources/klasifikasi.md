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

# Klasifikasi Lahan Sawah dan Non-Sawah dari Komposit Sentinel-2A

Klasifikasi ini memisahkan dua kelas, sawah dan non-sawah, pada komposit citra Sentinel-2A Level-2A berformat GeoTIFF. Saya mengunduh komposit untuk wilayah yang mencakup 100 petak sampel, mengambil nilai spektral semua piksel di dalam petak, melatih Random Forest, lalu menguji model pada petak yang tidak ikut pelatihan. Peta hasil berupa GeoTIFF dengan kode 1 untuk sawah, 0 untuk non-sawah, dan 255 untuk piksel tanpa data.

## Pustaka

```bash
pip install earthengine-api rasterio scikit-learn shapely matplotlib
```

Earth Engine menyediakan arsip Sentinel-2 dan mengekspor komposit. Rasterio dan Shapely mengolah raster dan poligon, sementara scikit-learn melatih model.

## 1. Wilayah Studi dan Sampel

Wilayah studi berbentuk persegi panjang dengan batas barat 112.7060, timur 112.7270, selatan -7.1495, dan utara -7.1325 (EPSG:4326). Ukurannya sekitar 2,3 km × 1,9 km, dan semua petak sampel berada di dalamnya.

| Kelas | Kode | Jumlah petak | Bentuk sampel |
| :--- | :---: | :---: | :--- |
| **Sawah** | `1` | 50 | Poligon petak sawah tak beraturan |
| **Non-Sawah** | `0` | 50 | Persegi 62 m × 62 m (P1 sampai P50) |
| **Total** | n/a | **100** | Seimbang, 50 petak per kelas |

Petak sawah berasal dari digitasi hamparan sawah di atas citra satelit. Saya menggambar sebagian petak langsung, membagi hamparan lain menjadi petak kecil dengan pembagian geometris, dan menyesuaikan bentuk beberapa petak setelahnya. Petak non-sawah berupa 50 persegi berukuran 62 m × 62 m yang tersebar di luar hamparan sawah. Kedua kelas berformat GeoJSON poligon (LineString tertutup) di EPSG:4326.

## 2. Akuisisi Komposit Sentinel-2A

Earth Engine menyediakan koleksi Sentinel-2 Level-2A (`COPERNICUS/S2_SR_HARMONIZED`) yang berisi reflektansi permukaan. Skrip memilih citra yang menutupi wilayah studi pada periode yang ditetapkan, membuang citra dengan tutupan awan di atas 40%, dan menyaring citra dari satelit Sentinel-2A lewat atribut `SPACECRAFT_NAME`. Pada tiap citra, skrip menutup piksel awan, bayangan awan, cirrus, salju, dan piksel jenuh berdasarkan Scene Classification Layer (SCL). Median dari citra yang lolos menjadi komposit bebas awan.

Komposit memuat enam band reflektansi: B2 (biru), B3 (hijau), B4 (merah), B8 (inframerah dekat), B11 dan B12 (inframerah gelombang pendek). Skrip menambahkan empat indeks turunan:

$$\text{NDVI} = \frac{B8 - B4}{B8 + B4} \qquad \text{NDWI} = \frac{B3 - B8}{B3 + B8}$$

$$\text{MNDWI} = \frac{B3 - B11}{B3 + B11} \qquad \text{NDBI} = \frac{B11 - B8}{B11 + B8}$$

NDVI mengukur kerapatan vegetasi, sedangkan NDWI dan MNDWI menandai air, termasuk genangan pada sawah yang baru ditanami. NDBI menandai lahan terbangun.

Earth Engine mengekspor sepuluh band pada resolusi 10 m dalam proyeksi UTM zona 49S (EPSG:32749) sebagai GeoTIFF float32, dengan urutan B2, B3, B4, B8, B11, B12, NDVI, NDWI, MNDWI, NDBI. Band B11 dan B12 beresolusi asli 20 m, dan Earth Engine menyamakannya ke 10 m.

```python
import ee, requests

ee.Authenticate()
ee.Initialize(project='ID-PROJECT-GEE')   # ganti dengan Project ID Google Cloud

# ---------- pengaturan ----------
START, END = '2024-06-01', '2024-09-30'   # periode citra (musim kemarau, relatif bebas awan)
MAX_AWAN = 40                             # persen awan maksimum per citra
HANYA_S2A = True                          # True = hanya satelit Sentinel-2A; False = semua Sentinel-2 L2A
OUT_TIF = 'sentinel2A_komposit.tif'

AOI = ee.Geometry.Rectangle([112.7060, -7.1495, 112.7270, -7.1325])   # barat, selatan, timur, utara

koleksi = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
           .filterBounds(AOI).filterDate(START, END)
           .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', MAX_AWAN)))
print('Semua Sentinel-2 L2A:', koleksi.size().getInfo(), 'citra')
if HANYA_S2A:
    koleksi = koleksi.filter(ee.Filter.eq('SPACECRAFT_NAME', 'Sentinel-2A'))
n = koleksi.size().getInfo()
print('Dipakai             :', n, 'citra')
if n == 0:
    raise SystemExit('Tidak ada citra. Geser START/END, naikkan MAX_AWAN, atau set HANYA_S2A = False.')

def mask_awan(img):
    scl = img.select('SCL')   # buang no-data, jenuh, bayangan awan, awan, cirrus, salju
    bagus = (scl.neq(0).And(scl.neq(1)).And(scl.neq(3)).And(scl.neq(8))
             .And(scl.neq(9)).And(scl.neq(10)).And(scl.neq(11)))
    return img.updateMask(bagus)

BAND = ['B2', 'B3', 'B4', 'B8', 'B11', 'B12']
komposit = koleksi.map(mask_awan).select(BAND).median().divide(10000)
ndvi = komposit.normalizedDifference(['B8', 'B4']).rename('NDVI')
ndwi = komposit.normalizedDifference(['B3', 'B8']).rename('NDWI')
mndwi = komposit.normalizedDifference(['B3', 'B11']).rename('MNDWI')
ndbi = komposit.normalizedDifference(['B11', 'B8']).rename('NDBI')
citra = komposit.addBands([ndvi, ndwi, mndwi, ndbi]).toFloat().clip(AOI)

url = citra.getDownloadURL({'region': AOI, 'scale': 10, 'crs': 'EPSG:32749', 'format': 'GEO_TIFF'})
r = requests.get(url, timeout=900)
if r.content[:2] not in (b'II', b'MM'):          # bukan file TIFF = pesan error dari GEE
    raise RuntimeError(r.text[:500])
open(OUT_TIF, 'wb').write(r.content)
print(f'Tersimpan {OUT_TIF}: {len(r.content) / 1e6:.1f} MB | urutan band: B2, B3, B4, B8, B11, B12, NDVI, NDWI, MNDWI, NDBI')

from google.colab import files
files.download(OUT_TIF)
```

**Output:**

```text
[ISI: tempel output sel di atas, yaitu jumlah citra yang dipakai dan ukuran file TIF]
```

## 3. Ekstraksi Sampel dan Pelatihan Model

Skrip memproyeksikan tiap poligon ke CRS citra dan mengecilkan batasnya 5 m ke dalam, supaya piksel tepi petak yang bercampur dengan penutup lahan lain tidak ikut. Poligon yang kosong setelah pengecilan memakai batas aslinya. Semua piksel yang pusatnya jatuh di dalam poligon menjadi sampel, dan tiap sampel membawa nomor petaknya. Piksel tanpa data tidak masuk.

Pembagian data latih dan uji mengikuti nomor petak: 70% petak melatih model dan 30% petak menguji model. Piksel dari satu petak tidak muncul di kedua sisi, jadi akurasi uji tidak menghitung piksel bertetangga yang nilainya hampir sama sebagai bukti terpisah.

Model Random Forest memakai 300 pohon dan bobot kelas seimbang. Setelah evaluasi, saya melatih ulang model pada semua piksel dan memakainya untuk mengklasifikasi seluruh citra. Skrip menulis hasilnya ke `klasifikasi_sawah.tif`.

```python
!pip -q install rasterio
import json, numpy as np, rasterio
from rasterio.features import rasterize
from rasterio.warp import transform
from shapely.geometry import Polygon, mapping
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GroupShuffleSplit
from sklearn.metrics import confusion_matrix, accuracy_score, cohen_kappa_score

TIF = 'sentinel2A_komposit.tif'
OUT_KLAS = 'klasifikasi_sawah.tif'
NAMA_BAND = ['B2', 'B3', 'B4', 'B8', 'B11', 'B12', 'NDVI', 'NDWI', 'MNDWI', 'NDBI']
BUFFER_M = 5      # kecilkan tiap petak sekian meter dari tepinya supaya tidak mengambil piksel campuran

# ---------- tempel GeoJSON petak di sini ----------
TITIK_SAWAH = {"type": "FeatureCollection", "features": []}       # tempel GeoJSON 50 petak sawah
TITIK_NON_SAWAH = {"type": "FeatureCollection", "features": []}   # tempel GeoJSON 50 petak non-sawah

# ---------- baca citra ----------
with rasterio.open(TIF) as src:
    arr = src.read().astype('float32')          # (band, baris, kolom)
    profil = src.profile
    tf, crs = src.transform, src.crs
n_band, H, W = arr.shape
assert n_band == len(NAMA_BAND), f'TIF punya {n_band} band, NAMA_BAND berisi {len(NAMA_BAND)}'
valid = np.isfinite(arr).all(axis=0) & (arr[:6].sum(axis=0) > 0)
print(f'Citra: {W} x {H} piksel, {n_band} band, CRS {crs}')


def petak_ke_polygon(fc):
    hasil = []
    for f in fc.get('features', []):
        g = f.get('geometry') or {}
        if g.get('type') == 'LineString':
            ring = g['coordinates']
        elif g.get('type') == 'Polygon':
            ring = g['coordinates'][0]
        else:
            continue
        if len(ring) < 3:
            continue
        lon = [p[0] for p in ring]
        lat = [p[1] for p in ring]
        xs, ys = transform('EPSG:4326', crs, lon, lat)
        poly = Polygon(zip(xs, ys))
        if not poly.is_valid:
            poly = poly.buffer(0)
        if poly.is_empty or poly.area == 0:
            continue
        kecil = poly.buffer(-BUFFER_M)
        hasil.append(kecil if (not kecil.is_empty and kecil.area > 0) else poly)
    return hasil


def ambil(fc, kelas, offset):
    polys = petak_ke_polygon(fc)
    if not polys:
        return np.empty((0, n_band), 'float32'), np.empty(0, int), np.empty(0, int)
    shapes = [(mapping(p), offset + i + 1) for i, p in enumerate(polys)]
    ids = rasterize(shapes, out_shape=(H, W), transform=tf, fill=0, dtype='int32')
    m = (ids > 0) & valid
    X = arr[:, m].T
    grup = ids[m]
    print(f'Kelas {kelas}: {len(polys)} petak dibaca, {len(np.unique(grup))} petak punya piksel di dalam citra, {len(X)} piksel terpakai')
    return X, np.full(len(X), kelas), grup


X1, y1, g1 = ambil(TITIK_SAWAH, 1, 0)
X0, y0, g0 = ambil(TITIK_NON_SAWAH, 0, 10000)
X = np.vstack([X1, X0])
y = np.concatenate([y1, y0])
grup = np.concatenate([g1, g0])
assert len(np.unique(y)) == 2, 'Kedua kelas harus punya petak yang jatuh di dalam citra'

# ---------- latih dan uji (data uji = petak yang tidak dipakai melatih) ----------
tr, te = next(GroupShuffleSplit(n_splits=1, test_size=0.3, random_state=42).split(X, y, grup))
rf = RandomForestClassifier(n_estimators=300, random_state=42, n_jobs=-1, class_weight='balanced')
rf.fit(X[tr], y[tr])
pred = rf.predict(X[te])
print('\nAkurasi  :', round(accuracy_score(y[te], pred), 4))
print('Kappa    :', round(cohen_kappa_score(y[te], pred), 4))
print('Matriks kebingungan (baris = aktual, kolom = prediksi; urutan: non-sawah, sawah):')
print(confusion_matrix(y[te], pred, labels=[0, 1]))
print('\nPentingnya tiap band:')
for n, v in sorted(zip(NAMA_BAND, rf.feature_importances_), key=lambda t: -t[1]):
    print(f'  {n:6s} {v:.3f}')

# model akhir dilatih ulang memakai semua piksel
rf.fit(X, y)

# ---------- klasifikasi seluruh citra ----------
flat = arr.reshape(n_band, -1)
h = np.full(H * W, 255, dtype='uint8')
idx = np.flatnonzero(valid.ravel())
for i in range(0, len(idx), 200000):
    j = idx[i:i + 200000]
    h[j] = rf.predict(flat[:, j].T).astype('uint8')
hasil = h.reshape(H, W)

for k in ('blockxsize', 'blockysize', 'tiled', 'interleave'):
    profil.pop(k, None)
profil.update(count=1, dtype='uint8', nodata=255, compress='lzw')
with rasterio.open(OUT_KLAS, 'w', **profil) as dst:
    dst.write(hasil, 1)

luas_px = abs(tf.a * tf.e)
n_sawah = int((hasil == 1).sum())
n_non = int((hasil == 0).sum())
print(f'\nSawah: {n_sawah} piksel (~{n_sawah * luas_px / 10000:.1f} ha) | Non-sawah: {n_non} piksel (~{n_non * luas_px / 10000:.1f} ha)')
print('Tersimpan:', OUT_KLAS)

# ---------- pratinjau ----------
import matplotlib.pyplot as plt
rgb = np.clip(np.nan_to_num(arr[[2, 1, 0]]).transpose(1, 2, 0) / 0.3, 0, 1)
fig, ax = plt.subplots(1, 2, figsize=(12, 6))
ax[0].imshow(rgb); ax[0].set_title('Sentinel-2A (RGB)')
ax[1].imshow(np.ma.masked_equal(hasil, 255), cmap='RdYlGn', vmin=0, vmax=1)
ax[1].set_title('Klasifikasi (hijau = sawah, merah = non-sawah)')
for a in ax:
    a.axis('off')
plt.show()

try:
    from google.colab import files
    files.download(OUT_KLAS)
except Exception:
    pass
```

**Output:**

```text
[ISI: tempel output sel di atas, yaitu jumlah piksel per kelas, akurasi, kappa, confusion matrix, kontribusi band, dan luas tiap kelas]
```

## 4. Hasil Evaluasi

Output sel klasifikasi memberi angka berikut.

| Metrik | Nilai |
| :--- | :---: |
| Akurasi petak uji | [ISI] |
| Kappa | [ISI] |
| Luas sawah hasil klasifikasi (ha) | [ISI] |
| Luas non-sawah hasil klasifikasi (ha) | [ISI] |

```python
import matplotlib.pyplot as plt
from sklearn.metrics import ConfusionMatrixDisplay

fig, ax = plt.subplots(1, 2, figsize=(12, 4.5))
ConfusionMatrixDisplay.from_predictions(y[te], pred, labels=[0, 1], display_labels=['Non-Sawah', 'Sawah'],
                                        cmap='Greens', ax=ax[0], colorbar=False)
ax[0].set_title('Confusion Matrix (petak uji)')

urut = np.argsort(rf.feature_importances_)
ax[1].barh(range(len(urut)), rf.feature_importances_[urut], color='#2ecc71', edgecolor='black')
ax[1].set_yticks(range(len(urut)))
ax[1].set_yticklabels([NAMA_BAND[i] for i in urut])
ax[1].set_xlabel('Nilai kepentingan')
ax[1].set_title('Kontribusi band dan indeks')
plt.tight_layout()
plt.show()
```

[ISI: tulis interpretasi dua sampai tiga kalimat. Sebut band atau indeks yang paling berpengaruh pada diagram kontribusi dan kelas yang paling sering salah pada confusion matrix.]

## 5. Keterbatasan

Pembagian uji per petak mengurangi kebocoran data antara piksel bertetangga, dan sisa kemiripan spektral antarpetak yang berdekatan tetap menaikkan akurasi uji. Sawah berganti fase dari genangan ke vegetatif lalu bera dalam satu musim, dan satu komposit median menangkap kondisi tengah periode itu. Sebagian petak sawah berasal dari pembagian hamparan, jadi batas antarpetak mengikuti hitungan geometri dan tidak selalu berimpit dengan pematang. Petak kecil di bawah 1.000 m² menyumbang kurang dari sepuluh piksel setelah pengecilan batas. Evaluasi memakai satu pembagian acak dari satu wilayah studi, sehingga angka akurasi belum menguji kemampuan model di lokasi lain.
