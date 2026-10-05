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

### Fitur yang digunakan untuk klasifikasi

Random Forest tidak menerima nama kelas atau bentuk petak secara langsung. Model menerima satu baris angka untuk setiap piksel. Satu baris tersebut berisi **10 fitur**, yaitu enam nilai reflektansi dan empat indeks spektral berikut.

| Fitur | Sumber atau rumus | Informasi yang dibawa | Peran dalam membedakan sawah dan non-sawah |
| :--- | :--- | :--- | :--- |
| `B2` | Biru, 490 nm | Respons permukaan pada cahaya biru | Membantu membedakan air, tanah, dan permukaan terbangun; juga sensitif terhadap pengaruh atmosfer dan kekeruhan air. |
| `B3` | Hijau, 560 nm | Pantulan cahaya hijau | Membantu mengenali vegetasi dan air; genangan biasanya memiliki respons berbeda dari vegetasi sawah. |
| `B4` | Merah, 665 nm | Pantulan cahaya merah | Diserap kuat oleh klorofil. Nilainya bersama `B8` menjadi dasar NDVI. |
| `B8` | Inframerah dekat/NIR, 842 nm | Pantulan struktur internal daun | Umumnya tinggi pada vegetasi sehat dan menjadi pembeda penting antara vegetasi sawah dengan air atau lahan terbuka. |
| `B11` | SWIR-1, 1610 nm | Kandungan air dan karakter permukaan | Membantu memisahkan tanah, vegetasi, air, dan area terbangun; digunakan dalam MNDWI dan NDBI. |
| `B12` | SWIR-2, 2190 nm | Kelembapan dan kondisi material permukaan | Melengkapi informasi `B11` untuk membedakan tanah kering, vegetasi, air, dan material non-vegetasi. |
| `NDVI` | $(B8-B4)/(B8+B4)$ | Kerapatan dan kehijauan vegetasi | Nilai tinggi umumnya menunjukkan vegetasi aktif, termasuk tanaman padi pada fase vegetatif. |
| `NDWI` | $(B3-B8)/(B3+B8)$ | Indikasi air atau genangan | Membantu mengenali sawah berair atau baru ditanami, sekaligus memisahkannya dari vegetasi yang memiliki `B8` tinggi. |
| `MNDWI` | $(B3-B11)/(B3+B11)$ | Air dengan pengurangan pengaruh tanah dan area terbangun | Berguna untuk mendeteksi genangan ketika air bercampur dengan tanah atau berada di sekitar permukaan terbangun. |
| `NDBI` | $(B11-B8)/(B11+B8)$ | Indikasi permukaan terbangun | Membantu mengurangi kesalahan antara non-sawah terbangun dan sawah, karena area terbangun cenderung memiliki respons SWIR lebih tinggi daripada NIR. |

Semua indeks berada pada rentang teoritis sekitar $-1$ sampai $1$. Nilai aktual dapat dipengaruhi oleh tutupan awan yang tersisa, bayangan, kelembapan tanah, fase pertumbuhan padi, dan pencampuran piksel. Karena itu, satu fitur tidak dipakai sebagai aturan ambang tunggal. Random Forest menggabungkan pola dari semua fitur untuk menentukan kelas setiap piksel.

**Daftar fitur input model:** `B2`, `B3`, `B4`, `B8`, `B11`, `B12`, `NDVI`, `NDWI`, `MNDWI`, dan `NDBI`. Urutan ini harus sama antara urutan band pada GeoTIFF, isi `NAMA_BAND`, dan kolom `X` yang diberikan ke model.

Earth Engine mengekspor sepuluh band pada resolusi 10 m dalam proyeksi UTM zona 49S (EPSG:32749) sebagai GeoTIFF float32, dengan urutan B2, B3, B4, B8, B11, B12, NDVI, NDWI, MNDWI, NDBI. Band B11 dan B12 beresolusi asli 20 m, dan Earth Engine menyamakannya ke 10 m.

```{code-cell} ipython3
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

**Output:** jumlah citra yang dipakai dan ukuran `sentinel2A_komposit.tif` dicetak
otomatis oleh sel di atas setelah Earth Engine berhasil diautentikasi. Nilainya
bergantung pada periode, tutupan awan, dan koleksi yang tersedia saat eksekusi.

## 3. Ekstraksi Sampel dan Pelatihan Model

Skrip memproyeksikan tiap poligon ke CRS citra dan mengecilkan batasnya 5 m ke dalam, supaya piksel tepi petak yang bercampur dengan penutup lahan lain tidak ikut. Poligon yang kosong setelah pengecilan memakai batas aslinya. Semua piksel yang pusatnya jatuh di dalam poligon menjadi sampel, dan tiap sampel membawa nomor petaknya. Piksel tanpa data tidak masuk.

Dalam klasifikasi ini, **satu data berarti satu piksel berlabel**. Setiap data mempunyai **10 fitur**, yaitu `B2`, `B3`, `B4`, `B8`, `B11`, `B12`, `NDVI`, `NDWI`, `MNDWI`, dan `NDBI`. Jadi, bentuk matriks `X` adalah `(jumlah data piksel, 10)`, sedangkan `y` berisi satu label kelas untuk setiap baris `X`. Jumlah data bergantung pada jumlah piksel yang masuk ke dalam petak sampel dan lolos pemeriksaan validitas citra.

Pembagian data latih dan uji mengikuti nomor petak: 70% petak melatih model dan 30% petak menguji model. Piksel dari satu petak tidak muncul di kedua sisi, jadi akurasi uji tidak menghitung piksel bertetangga yang nilainya hampir sama sebagai bukti terpisah.

### Model Random Forest

Random Forest adalah kumpulan banyak pohon keputusan. Setiap pohon belajar dari sampel dan subset fitur yang berbeda, lalu hasil akhirnya ditentukan melalui voting mayoritas. Pendekatan ini sesuai untuk data Sentinel-2A karena hubungan antara reflektansi, indeks vegetasi, genangan, dan kelas lahan tidak harus linear.

Pada penelitian ini digunakan `RandomForestClassifier` dengan pengaturan berikut:

| Parameter | Nilai | Fungsi |
| :--- | :---: | :--- |
| `n_estimators` | `300` | Jumlah pohon keputusan. Lebih banyak pohon membuat hasil voting lebih stabil, dengan waktu komputasi yang lebih besar. |
| `class_weight` | `'balanced'` | Memberi bobot lebih besar pada kelas yang jumlah pikselnya lebih sedikit setelah ekstraksi sampel. |
| `random_state` | `42` | Membuat pembagian data dan hasil model dapat diulang. |
| `n_jobs` | `-1` | Menggunakan seluruh inti prosesor yang tersedia. |

Model pertama dilatih hanya pada petak latih, kemudian diuji pada petak yang benar-benar berbeda. Setelah akurasi dan kappa dihitung, model dilatih ulang menggunakan seluruh sampel berlabel. Model akhir inilah yang digunakan untuk memprediksi setiap piksel pada citra dan menghasilkan `klasifikasi_sawah.tif`.

```{code-cell} ipython3
!pip -q install rasterio
import json
from pathlib import Path

import numpy as np
import rasterio
from rasterio.features import rasterize
from rasterio.warp import transform
from shapely.geometry import Polygon, mapping
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GroupShuffleSplit
from sklearn.metrics import confusion_matrix, accuracy_score, cohen_kappa_score

TIF = 'sentinel2A_komposit.tif'
OUT_KLAS = 'klasifikasi_sawah.tif'
OUT_GAMBAR = Path('segmentasi_sawah_non_sawah.png')
NAMA_BAND = ['B2', 'B3', 'B4', 'B8', 'B11', 'B12', 'NDVI', 'NDWI', 'MNDWI', 'NDBI']
BUFFER_M = 5      # kecilkan tiap petak sekian meter dari tepinya supaya tidak mengambil piksel campuran

# ---------- GeoJSON petak sampel ----------
# Lampiran poligon sawah disimpan sebagai `sawah.geojson`, sedangkan lampiran
# persegi P1-P50 disimpan sebagai `non_sawah.geojson` di folder kerja notebook.
# Kedua file harus berupa FeatureCollection dengan geometri LineString tertutup
# atau Polygon dalam EPSG:4326.
FILE_SAWAH = Path('sawah.geojson')
FILE_NON_SAWAH = Path('non_sawah.geojson')


def baca_geojson(path):
    if not path.exists():
        raise FileNotFoundError(
            f'{path} belum ditemukan. Simpan lampiran GeoJSON dengan nama tersebut '
            'di folder kerja notebook.'
        )
    with path.open(encoding='utf-8') as f:
        data = json.load(f)
    if data.get('type') != 'FeatureCollection':
        raise ValueError(f'{path} harus bertipe FeatureCollection')
    features = data.get('features', [])
    if not features:
        raise ValueError(f'{path} tidak berisi feature')
    return data


TITIK_SAWAH = baca_geojson(FILE_SAWAH)
TITIK_NON_SAWAH = baca_geojson(FILE_NON_SAWAH)
print(f'Label sawah: {len(TITIK_SAWAH["features"])} petak')
print(f'Label non-sawah: {len(TITIK_NON_SAWAH["features"])} petak')

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
assert len(np.unique(grup)) >= 4, 'Minimal empat petak harus masuk citra untuk split per petak'

jumlah_fitur = X.shape[1]
jumlah_data = X.shape[0]
jumlah_piksel_sawah = int((y == 1).sum())
jumlah_piksel_non_sawah = int((y == 0).sum())
jumlah_petak = len(np.unique(grup))
print('\nRingkasan data berlabel:')
print(f'  Jumlah data piksel       : {jumlah_data}')
print(f'  Jumlah fitur per piksel  : {jumlah_fitur}')
print(f'  Ukuran matriks X         : {X.shape}')
print(f'  Piksel label sawah (1)   : {jumlah_piksel_sawah}')
print(f'  Piksel label non-sawah (0): {jumlah_piksel_non_sawah}')
print(f'  Jumlah petak             : {jumlah_petak}')

# ---------- latih dan uji (data uji = petak yang tidak dipakai melatih) ----------
tr, te = next(GroupShuffleSplit(n_splits=1, test_size=0.3, random_state=42).split(X, y, grup))
petak_train = len(np.unique(grup[tr]))
petak_test = len(np.unique(grup[te]))
print('\nPembagian data berdasarkan petak:')
print(f'  Data train               : {len(tr)} piksel ({petak_train} petak)')
print(f'  Data testing             : {len(te)} piksel ({petak_test} petak)')
print(f'  Train sawah / non-sawah  : {(y[tr] == 1).sum()} / {(y[tr] == 0).sum()} piksel')
print(f'  Test sawah / non-sawah   : {(y[te] == 1).sum()} / {(y[te] == 0).sum()} piksel')
rf = RandomForestClassifier(n_estimators=300, random_state=42, n_jobs=-1, class_weight='balanced')
rf.fit(X[tr], y[tr])
pred = rf.predict(X[te])
akurasi = accuracy_score(y[te], pred)
kappa = cohen_kappa_score(y[te], pred)
matriks = confusion_matrix(y[te], pred, labels=[0, 1])
print('\nAkurasi  :', round(akurasi, 4))
print('Kappa    :', round(kappa, 4))
print('Matriks kebingungan (baris = aktual, kolom = prediksi; urutan: non-sawah, sawah):')
print(matriks)
print('\nPentingnya tiap band:')
peringkat_fitur = sorted(zip(NAMA_BAND, rf.feature_importances_), key=lambda t: -t[1])
print('Fitur       Kepentingan')
for nama_fitur, nilai in peringkat_fitur:
    print(f'  {nama_fitur:8s} {nilai:.4f} ({nilai * 100:.2f}%)')

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
luas_sawah_ha = n_sawah * luas_px / 10000
luas_non_ha = n_non * luas_px / 10000
luas_valid_ha = (n_sawah + n_non) * luas_px / 10000
persen_sawah = 100 * n_sawah / (n_sawah + n_non)
persen_non = 100 * n_non / (n_sawah + n_non)
print(f'\nSawah: {n_sawah} piksel (~{luas_sawah_ha:.1f} ha) | Non-sawah: {n_non} piksel (~{luas_non_ha:.1f} ha)')
print(f'Persentase area valid: sawah {persen_sawah:.1f}% | non-sawah {persen_non:.1f}%')
print('Tersimpan:', OUT_KLAS)

# ---------- gambar segmentasi ----------
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm, ListedColormap

rgb = np.clip(np.nan_to_num(arr[[2, 1, 0]]).transpose(1, 2, 0) / 0.3, 0, 1)
kelas_cmap = ListedColormap(['#d95f02', '#1b9e77', '#ffffff'])
kelas_norm = BoundaryNorm([-0.5, 0.5, 1.5, 255.5], kelas_cmap.N)
kelas = np.ma.masked_where(hasil == 255, hasil)

fig, ax = plt.subplots(1, 3, figsize=(16, 5.5), constrained_layout=True)
ax[0].imshow(rgb)
ax[0].set_title('Citra Sentinel-2A (RGB)')
ax[1].imshow(kelas, cmap=kelas_cmap, norm=kelas_norm, interpolation='nearest')
ax[1].set_title('Segmentasi Sawah dan Non-Sawah')
ax[2].imshow(rgb)
ax[2].imshow(kelas, cmap=kelas_cmap, norm=kelas_norm, alpha=0.48, interpolation='nearest')
ax[2].set_title('Overlay Citra dan Hasil Segmentasi')
for a in ax:
    a.axis('off')
fig.legend(
    handles=[
        plt.Rectangle((0, 0), 1, 1, color='#1b9e77', label='Sawah'),
        plt.Rectangle((0, 0), 1, 1, color='#d95f02', label='Non-sawah'),
    ],
    loc='lower center', ncol=2, frameon=False,
)
fig.savefig(OUT_GAMBAR, dpi=200, bbox_inches='tight')
print('Tersimpan:', OUT_GAMBAR.resolve())
plt.show()

try:
    from google.colab import files
    files.download(OUT_KLAS)
except Exception:
    pass
```

`akurasi`, `kappa`, `matriks`, `rf.feature_importances_`, `luas_sawah_ha`, dan `luas_non_ha`
adalah output terukur dari sel di atas. Sel evaluasi berikut memakai variabel tersebut
secara langsung, jadi tidak ada angka dummy yang perlu disalin manual.

## 4. Hasil Evaluasi

Output numerik berikut dibuat langsung dari hasil klasifikasi, bukan ditulis sebagai
teks manual. Jalankan sel ini setelah sel pelatihan selesai.

```{code-cell} ipython3
hasil_evaluasi = {
    'Jumlah fitur': f'{jumlah_fitur}',
    'Jumlah data piksel berlabel': f'{jumlah_data:,}',
    'Piksel label sawah': f'{jumlah_piksel_sawah:,}',
    'Piksel label non-sawah': f'{jumlah_piksel_non_sawah:,}',
    'Data train': f'{len(tr):,} piksel ({petak_train} petak)',
    'Data testing': f'{len(te):,} piksel ({petak_test} petak)',
    'Akurasi petak uji': f'{akurasi:.4f}',
    'Kappa': f'{kappa:.4f}',
    'Luas sawah hasil klasifikasi (ha)': f'{luas_sawah_ha:.2f}',
    'Luas non-sawah hasil klasifikasi (ha)': f'{luas_non_ha:.2f}',
}
print('| Metrik | Nilai |')
print('| :--- | ---: |')
for metrik, nilai in hasil_evaluasi.items():
    print(f'| {metrik} | {nilai} |')

segmentasi = {
    'Sawah': (n_sawah, luas_sawah_ha, persen_sawah),
    'Non-sawah': (n_non, luas_non_ha, persen_non),
}
print('\n| Kelas segmentasi | Piksel | Luas (ha) | Persentase area valid |')
print('| :--- | ---: | ---: | ---: |')
for kelas, (jumlah, luas, persentase) in segmentasi.items():
    print(f'| {kelas} | {jumlah:,} | {luas:.2f} | {persentase:.2f}% |')
```

Gambar hasil segmentasi tersimpan sebagai `segmentasi_sawah_non_sawah.png` dan
menampilkan citra RGB, peta kelas, serta overlay. Warna hijau menunjukkan sawah,
sedangkan warna oranye menunjukkan non-sawah.

```{code-cell} ipython3
from IPython.display import Image, display

display(Image(filename=OUT_GAMBAR))
```

```{code-cell} ipython3
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

Interpretasi dibuat dari hasil sel: band/indeks paling berpengaruh adalah fitur dengan
`rf.feature_importances_` terbesar, sedangkan kelas yang paling sering salah ditentukan
dari jumlah terbesar pada elemen diagonal luar `matriks` (baris aktual, kolom prediksi).

## 5. Keterbatasan

Pembagian uji per petak mengurangi kebocoran data antara piksel bertetangga, dan sisa kemiripan spektral antarpetak yang berdekatan tetap menaikkan akurasi uji. Sawah berganti fase dari genangan ke vegetatif lalu bera dalam satu musim, dan satu komposit median menangkap kondisi tengah periode itu. Sebagian petak sawah berasal dari pembagian hamparan, jadi batas antarpetak mengikuti hitungan geometri dan tidak selalu berimpit dengan pematang. Petak kecil di bawah 1.000 m² menyumbang kurang dari sepuluh piksel setelah pengecilan batas. Evaluasi memakai satu pembagian acak dari satu wilayah studi, sehingga angka akurasi belum menguji kemampuan model di lokasi lain.
