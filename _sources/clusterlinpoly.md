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

# Clustering Linear dan Polynomial

Dokumen ini menyajikan hasil pengelompokan (*clustering*) daerah berdasarkan gabungan tiga polutan udara, yaitu **NO2, SO2, dan CO**. Deret waktu tiap polutan diekstraksi menjadi 68 fitur menggunakan TSFEL, lalu ketiganya digabung dalam satu tabel sehingga setiap daerah memiliki **204 fitur** (68 fitur x 3 polutan).

Berbeda dengan pekan sebelumnya yang memproses tiap polutan secara terpisah, pada tahap ini seluruh polutan dikelompokkan sekaligus. Dua jenis fitur diuji, yaitu **fitur linear** dan **fitur polynomial**. Untuk masing-masing jenis, data direduksi dengan PCA ke **203, 74, dan 37 dimensi**, kemudian dikelompokkan dengan K-Means pada **K = 2, K = 3, dan K = 4**. Kualitas setiap hasil dinilai dengan *Silhouette Coefficient*, dan hasil terbaik dipetakan secara interaktif menggunakan Folium.

---

## 1. Alur Kerja (Workflow) KNIME

Eksperimen dijalankan di KNIME Analytics Platform dengan dua workflow yang strukturnya sama. Perbedaannya hanya pada tabel sumber di database: satu berisi fitur linear dan satu berisi fitur polynomial.

```{figure} ./img/clustering_knime/workflow_linear.png
---
name: workflow-linear
align: center
width: 90%
---
Workflow KNIME untuk fitur linear
```

```{figure} ./img/clustering_knime/workflow_polynomial.png
---
name: workflow-polynomial
align: center
width: 90%
---
Workflow KNIME untuk fitur polynomial
```

### 1.1 Fungsi Setiap Node

1. **MySQL Connector**: membangun koneksi dari KNIME ke server database MySQL.

2. **DB Table Selector**: memilih tabel yang menyimpan fitur gabungan tiga polutan (204 fitur per daerah).

3. **DB Reader**: menjalankan query dan memuat isi tabel ke dalam memori KNIME agar bisa diproses node berikutnya.

4. **Column Filter**: menyaring kolom yang dipakai untuk pemodelan. Kolom identitas seperti `id` dan nama daerah dikeluarkan karena tidak memiliki nilai analitik untuk clustering.

5. **PCA (Principal Component Analysis)**: mereduksi dimensi data. Hasil Column Filter dibagi ke tiga node PCA yang berjalan paralel, masing-masing menghasilkan **203**, **74**, dan **37** komponen utama.

6. **k-Means**: algoritma clustering berbasis jarak Euclidean. Setiap keluaran PCA dihubungkan ke tiga node k-Means dengan **K = 2, K = 3, dan K = 4**. Total ada 3 dimensi x 3 nilai K = 9 hasil clustering untuk satu jenis fitur.

7. **Scatter Plot**: menampilkan sebaran data beserta label cluster hasil k-Means.

8. **Silhouette Coefficient**: menghitung skor silhouette tiap hasil clustering. Skor mendekati 1 berarti anggota cluster rapat dan terpisah jelas dari cluster lain, sedangkan skor mendekati 0 atau negatif berarti batas antar cluster tumpang tindih.

### 1.2 Skenario Eksperimen

| Jenis Fitur | Dimensi (PCA) | K = 2 | K = 3 | K = 4 |
| :---: | :---: | :---: | :---: | :---: |
| Linear | 203 | ✓ | ✓ | ✓ |
| Linear | 74 | ✓ | ✓ | ✓ |
| Linear | 37 | ✓ | ✓ | ✓ |
| Polynomial | 203 | ✓ | ✓ | ✓ |
| Polynomial | 74 | ✓ | ✓ | ✓ |
| Polynomial | 37 | ✓ | ✓ | ✓ |

Total terdapat 18 hasil clustering yang dievaluasi.

---
## 2. Hasil Clustering Fitur Linear

Bagian ini memuat scatter plot dan nilai *Silhouette Coefficient* untuk setiap kombinasi dimensi PCA dan jumlah cluster pada fitur linear.

### 2.1 PCA 203 Dimensi

**K = 2**

- **Silhouette Coefficient**: …

```{figure} ./img/clustering_knime/linear_pca203_k2.png
---
name: scatter-linear-pca203-k2
align: center
width: 70%
---
Scatter plot K-Means fitur linear, PCA 203 dimensi, K = 2
```

**K = 3**

- **Silhouette Coefficient**: …

```{figure} ./img/clustering_knime/linear_pca203_k3.png
---
name: scatter-linear-pca203-k3
align: center
width: 70%
---
Scatter plot K-Means fitur linear, PCA 203 dimensi, K = 3
```

**K = 4**

- **Silhouette Coefficient**: …

```{figure} ./img/clustering_knime/linear_pca203_k4.png
---
name: scatter-linear-pca203-k4
align: center
width: 70%
---
Scatter plot K-Means fitur linear, PCA 203 dimensi, K = 4
```

### 2.2 PCA 74 Dimensi

**K = 2**

- **Silhouette Coefficient**: …

```{figure} ./img/clustering_knime/linear_pca74_k2.png
---
name: scatter-linear-pca74-k2
align: center
width: 70%
---
Scatter plot K-Means fitur linear, PCA 74 dimensi, K = 2
```

**K = 3**

- **Silhouette Coefficient**: …

```{figure} ./img/clustering_knime/linear_pca74_k3.png
---
name: scatter-linear-pca74-k3
align: center
width: 70%
---
Scatter plot K-Means fitur linear, PCA 74 dimensi, K = 3
```

**K = 4**

- **Silhouette Coefficient**: …

```{figure} ./img/clustering_knime/linear_pca74_k4.png
---
name: scatter-linear-pca74-k4
align: center
width: 70%
---
Scatter plot K-Means fitur linear, PCA 74 dimensi, K = 4
```

### 2.3 PCA 37 Dimensi

**K = 2**

- **Silhouette Coefficient**: …

```{figure} ./img/clustering_knime/linear_pca37_k2.png
---
name: scatter-linear-pca37-k2
align: center
width: 70%
---
Scatter plot K-Means fitur linear, PCA 37 dimensi, K = 2
```

**K = 3**

- **Silhouette Coefficient**: …

```{figure} ./img/clustering_knime/linear_pca37_k3.png
---
name: scatter-linear-pca37-k3
align: center
width: 70%
---
Scatter plot K-Means fitur linear, PCA 37 dimensi, K = 3
```

**K = 4**

- **Silhouette Coefficient**: …

```{figure} ./img/clustering_knime/linear_pca37_k4.png
---
name: scatter-linear-pca37-k4
align: center
width: 70%
---
Scatter plot K-Means fitur linear, PCA 37 dimensi, K = 4
```

---

## 3. Hasil Clustering Fitur Polynomial

Bagian ini memuat scatter plot dan nilai *Silhouette Coefficient* untuk setiap kombinasi dimensi PCA dan jumlah cluster pada fitur polynomial.

### 3.1 PCA 203 Dimensi

**K = 2**

- **Silhouette Coefficient**: …

```{figure} ./img/clustering_knime/polynomial_pca203_k2.png
---
name: scatter-polynomial-pca203-k2
align: center
width: 70%
---
Scatter plot K-Means fitur polynomial, PCA 203 dimensi, K = 2
```

**K = 3**

- **Silhouette Coefficient**: …

```{figure} ./img/clustering_knime/polynomial_pca203_k3.png
---
name: scatter-polynomial-pca203-k3
align: center
width: 70%
---
Scatter plot K-Means fitur polynomial, PCA 203 dimensi, K = 3
```

**K = 4**

- **Silhouette Coefficient**: …

```{figure} ./img/clustering_knime/polynomial_pca203_k4.png
---
name: scatter-polynomial-pca203-k4
align: center
width: 70%
---
Scatter plot K-Means fitur polynomial, PCA 203 dimensi, K = 4
```

### 3.2 PCA 74 Dimensi

**K = 2**

- **Silhouette Coefficient**: …

```{figure} ./img/clustering_knime/polynomial_pca74_k2.png
---
name: scatter-polynomial-pca74-k2
align: center
width: 70%
---
Scatter plot K-Means fitur polynomial, PCA 74 dimensi, K = 2
```

**K = 3**

- **Silhouette Coefficient**: …

```{figure} ./img/clustering_knime/polynomial_pca74_k3.png
---
name: scatter-polynomial-pca74-k3
align: center
width: 70%
---
Scatter plot K-Means fitur polynomial, PCA 74 dimensi, K = 3
```

**K = 4**

- **Silhouette Coefficient**: …

```{figure} ./img/clustering_knime/polynomial_pca74_k4.png
---
name: scatter-polynomial-pca74-k4
align: center
width: 70%
---
Scatter plot K-Means fitur polynomial, PCA 74 dimensi, K = 4
```

### 3.3 PCA 37 Dimensi

**K = 2**

- **Silhouette Coefficient**: …

```{figure} ./img/clustering_knime/polynomial_pca37_k2.png
---
name: scatter-polynomial-pca37-k2
align: center
width: 70%
---
Scatter plot K-Means fitur polynomial, PCA 37 dimensi, K = 2
```

**K = 3**

- **Silhouette Coefficient**: …

```{figure} ./img/clustering_knime/polynomial_pca37_k3.png
---
name: scatter-polynomial-pca37-k3
align: center
width: 70%
---
Scatter plot K-Means fitur polynomial, PCA 37 dimensi, K = 3
```

**K = 4**

- **Silhouette Coefficient**: …

```{figure} ./img/clustering_knime/polynomial_pca37_k4.png
---
name: scatter-polynomial-pca37-k4
align: center
width: 70%
---
Scatter plot K-Means fitur polynomial, PCA 37 dimensi, K = 4
```

---

## 4. Ringkasan Silhouette Coefficient

Tabel berikut merangkum seluruh skor silhouette. Skor tertinggi pada setiap kolom dicetak tebal.

### Fitur Linear

| Jumlah Cluster | Silhouette **203 Dimensi** | Silhouette **74 Dimensi** | Silhouette **37 Dimensi** |
| :---: | :---: | :---: | :---: |
| **K = 2** | … | … | … |
| **K = 3** | … | … | … |
| **K = 4** | … | … | … |

### Fitur Polynomial

| Jumlah Cluster | Silhouette **203 Dimensi** | Silhouette **74 Dimensi** | Silhouette **37 Dimensi** |
| :---: | :---: | :---: | :---: |
| **K = 2** | … | … | … |
| **K = 3** | … | … | … |
| **K = 4** | … | … | … |

---

## 5. Perbandingan Hasil Antar Reduksi Dimensi

Perbandingan dilakukan pada nilai K yang sama, dengan melihat skor silhouette dan susunan anggota cluster di PCA 203, PCA 74, dan PCA 37.

**Dasar teori.** Jumlah daerah observasi (baris data) hanya **37**, sedangkan jumlah fiturnya 204. Matriks data dengan 37 baris memiliki *rank* maksimum 37, sehingga seluruh variasi yang ada di antara daerah sudah tertampung dalam paling banyak 37 komponen utama. Konsekuensinya, PCA 203 dan PCA 74 tidak membuang informasi struktural, dan PCA 37 hanya membuang ruang kosong. Jarak Euclidean antar daerah tetap sama di ketiga dimensi, sehingga K-Means pada kondisi yang sama diharapkan memberi susunan cluster dan skor silhouette yang sama.

**Temuan eksperimen.**

- Fitur linear: …
- Fitur polynomial: …

**Implikasi praktis.** Karena hasilnya tidak bergantung pada jumlah komponen, PCA 37 menjadi pilihan paling efisien. Dimensinya paling kecil sehingga komputasi K-Means paling ringan, sementara kualitas clustering tidak berkurang.

---

## 6. Penentuan Cluster Terbaik

Konfigurasi terbaik dipilih dari skor *Silhouette Coefficient* tertinggi. Nilai yang mendekati 1 menunjukkan cluster yang padat dan terpisah jelas.

| Jenis Fitur | Dimensi Terbaik | K Terbaik | Silhouette |
| :---: | :---: | :---: | :---: |
| Linear | … | … | … |
| Polynomial | … | … | … |

**Analisis per reduksi dimensi.**

- **PCA 203**: K terbaik = …, alasan: …
- **PCA 74**: K terbaik = …, alasan: …
- **PCA 37**: K terbaik = …, alasan: …

**Perbandingan linear dan polynomial.** …

---

## 7. Pemetaan Segmentasi Wilayah

Hasil clustering ditampilkan pada peta interaktif Folium. Untuk setiap jenis fitur dibuat **tiga peta**, satu untuk tiap nilai K (2, 3, dan 4). Peta bersumber dari hasil clustering PCA 37 dimensi sebagai wakil, karena pembagian cluster antar reduksi dimensi dibandingkan pada bagian sebelumnya. Klik marker untuk melihat nama daerah, cluster, dan koordinatnya. Layer cluster dapat dinyalakan dan dimatikan lewat kontrol di kanan atas.

File CSV yang dibaca berada di `./source/cluster_daerah/` dengan pola nama `hasil_clustering_<jenis>_k<K>.csv` (contoh: `hasil_clustering_linear_k2.csv`). Setiap file memuat kolom `daerah` dan `Cluster` (label dari KNIME, misalnya `cluster_0`).

Koordinat daerah dicari dengan urutan prioritas berikut: (1) kolom `latitude` dan `longitude` di CSV, (2) file `koordinat_daerah.csv` di folder yang sama, (3) kamus `KAMUS_KOORDINAT` di kode, yang berisi titik perkiraan pusat kota atau kabupaten. Titik dari kamus diberi pergeseran kecil agar marker tidak bertumpuk, sehingga posisinya bersifat perkiraan. Daerah yang koordinatnya tidak ditemukan dilewati dan namanya dicetak di output sel.

### Persiapan Fungsi Peta

```{code-cell} ipython3
:tags: [hide-input]

import warnings
import zlib
from pathlib import Path

import folium
import numpy as np
import pandas as pd
from folium.plugins import MiniMap

warnings.filterwarnings("ignore")

FOLDER_HASIL = Path("./source/cluster_daerah")
FILE_KOORDINAT = FOLDER_HASIL / "koordinat_daerah.csv"

PALET_WARNA = {
    "Cluster 0": "#e53935",
    "Cluster 1": "#1e88e5",
    "Cluster 2": "#43a047",
    "Cluster 3": "#fb8c00",
}

# Isi dengan skor Silhouette Coefficient dari KNIME (PCA 37).
# Nilai None akan ditampilkan sebagai tanda "-" pada legenda.
SILHOUETTE = {
    "linear": {2: None, 3: None, 4: None},
    "polynomial": {2: None, 3: None, 4: None},
}

NAMA_JENIS = {"linear": "Linear", "polynomial": "Polynomial"}


# Titik perkiraan pusat kota/kabupaten, dipakai jika CSV tidak punya koordinat.
# Urutan penting: kata kunci yang lebih spesifik diletakkan lebih dulu.
KAMUS_KOORDINAT = {
    "baron": (-7.6033, 112.0601),
    "sreseh": (-7.1983, 113.0805),
    "banyu ajuh": (-7.1585, 112.7280),
    "banyuajuh": (-7.1620, 112.7310),
    "kamal": (-7.1662, 112.7214),
    "labang": (-7.1294, 112.7936),
    "kwanyar": (-7.1604, 112.8569),
    "kecamatan bangkalan": (-7.0325, 112.7450),
    "bangkalan": (-7.0455, 112.7351),
    "gresik": (-7.1566, 112.6555),
    "paciran": (-6.8767, 112.3414),
    "jabon": (-7.5419, 112.7686),
    "widang": (-6.9850, 112.1647),
    "kalianget": (-7.0519, 113.9408),
    "kota sumenep": (-7.0086, 113.8617),
    "sumenep": (-7.0167, 113.8542),
    "tikala": (1.4820, 124.8540),
    "wonokromo": (-7.3006, 112.7383),
    "surabaya": (-7.2575, 112.7521),
    "pilangkenceng": (-7.4931, 111.6664),
    "madiun": (-7.6298, 111.5239),
    "sidoarjo": (-7.4478, 112.7183),
    "tuban": (-6.8976, 112.0463),
    "lamongan": (-7.1193, 112.4167),
    "sampang": (-7.1872, 113.2394),
    "pamekasan": (-7.1568, 113.4746),
    "malang": (-7.9666, 112.6326),
    "denpasar": (-8.6705, 115.2126),
    "jakarta": (-6.2088, 106.8456),
    "ngawi": (-7.4039, 111.4460),
    "nunukan": (4.1333, 117.6667),
}


def cari_koordinat(nama_daerah):
    """Mencari titik perkiraan dari kamus, dengan pergeseran kecil yang konsisten per nama."""
    nama = str(nama_daerah).lower()
    for kata_kunci, (lat, lon) in KAMUS_KOORDINAT.items():
        if kata_kunci in nama:
            rng = np.random.default_rng(zlib.crc32(nama.encode("utf-8")))
            return lat + rng.uniform(-0.015, 0.015), lon + rng.uniform(-0.015, 0.015)
    return None, None


def lengkapi_koordinat(df):
    """Prioritas: kolom di CSV, lalu koordinat_daerah.csv, lalu kamus."""
    if {"latitude", "longitude"}.issubset(df.columns):
        return df
    if FILE_KOORDINAT.exists():
        koordinat = pd.read_csv(FILE_KOORDINAT)[["daerah", "latitude", "longitude"]]
        return df.merge(koordinat, on="daerah", how="left")
    hasil = [cari_koordinat(nama) for nama in df["daerah"]]
    df["latitude"] = [h[0] for h in hasil]
    df["longitude"] = [h[1] for h in hasil]
    return df


def muat_data(jenis, k):
    """Membaca CSV hasil clustering dan memastikan koordinat tersedia."""
    path = FOLDER_HASIL / f"hasil_clustering_{jenis}_k{k}.csv"
    df = pd.read_csv(path)

    kolom_cluster = next((c for c in df.columns if c.lower() == "cluster"), None)
    if kolom_cluster is None:
        raise ValueError(f"Kolom 'Cluster' tidak ditemukan di {path}")

    df["Cluster_Label"] = df[kolom_cluster].astype(str).apply(
        lambda x: f"Cluster {x.split('_')[-1]}"
    )

    df = lengkapi_koordinat(df)
    df[["latitude", "longitude"]] = df[["latitude", "longitude"]].astype(float)

    hilang = df[df["latitude"].isna() | df["longitude"].isna()]
    if len(hilang) > 0:
        print("Daerah tanpa koordinat (dilewati):", ", ".join(hilang["daerah"].astype(str)))
        print("Tambahkan ke KAMUS_KOORDINAT atau koordinat_daerah.csv.")
    return df.dropna(subset=["latitude", "longitude"]).reset_index(drop=True)


def render_peta(df, nama_dataset, k_val, sil_score=None):
    """Membuat peta Folium interaktif untuk satu hasil clustering."""
    pusat = [df["latitude"].mean(), df["longitude"].mean()]
    m = folium.Map(location=pusat, zoom_start=8, tiles=None, control_scale=True)
    folium.TileLayer("OpenStreetMap", name="OpenStreetMap (default)").add_to(m)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}",
        attr="Esri",
        name="Esri Street Map",
    ).add_to(m)

    daftar_cluster = sorted(df["Cluster_Label"].unique())
    grup = {}
    for nama in daftar_cluster:
        fg = folium.FeatureGroup(name=nama, show=True)
        fg.add_to(m)
        grup[nama] = fg

    for _, row in df.sort_values("Cluster_Label").iterrows():
        nama = row["Cluster_Label"]
        nomor = nama.split()[-1]
        kode = f"C{nomor}"
        warna = PALET_WARNA.get(nama, "#757575")

        ikon_html = (
            f'<div style="background-color: {warna}; color: white; border-radius: 50%; '
            f'width: 30px; height: 30px; display: flex; align-items: center; '
            f'justify-content: center; font-family: Arial, sans-serif; font-size: 10px; '
            f'font-weight: bold; border: 2px solid white; '
            f'box-shadow: 0 2px 6px rgba(0,0,0,0.45);">{kode}</div>'
        )
        popup_html = (
            f'<div style="font-family: Arial; font-size: 12px; min-width: 160px;">'
            f'<b>{row["daerah"]}</b><hr style="margin: 4px 0;">'
            f'<b>Klaster:</b> {nama} ({kode})<br>'
            f'<b>Koordinat:</b> {row["latitude"]:.4f}, {row["longitude"]:.4f}</div>'
        )

        folium.Marker(
            location=[row["latitude"], row["longitude"]],
            icon=folium.DivIcon(html=ikon_html, icon_size=(30, 30), icon_anchor=(15, 15)),
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=f'{row["daerah"]} ({kode})',
        ).add_to(grup[nama])

    sw = df[["latitude", "longitude"]].min().values.tolist()
    ne = df[["latitude", "longitude"]].max().values.tolist()
    m.fit_bounds([sw, ne], padding=(30, 30))

    MiniMap(toggle_display=True, position="bottomright").add_to(m)
    folium.LayerControl(collapsed=False, position="topright").add_to(m)

    jumlah = df["Cluster_Label"].value_counts()
    item_legenda = ""
    for nama in daftar_cluster:
        warna = PALET_WARNA.get(nama, "#757575")
        item_legenda += (
            f'<div style="display: flex; align-items: center; margin-bottom: 6px; '
            f'font-size: 13px; color: #333;">'
            f'<span style="display:inline-block; width: 14px; height: 14px; '
            f'border-radius: 50%; background-color: {warna}; margin-right: 10px;"></span>'
            f'<span>{nama}: {jumlah.get(nama, 0)} wilayah</span></div>'
        )

    teks_sil = f"{sil_score:.3f}" if sil_score is not None else "-"
    legenda = (
        f'<div style="position: fixed; bottom: 45px; left: 20px; z-index: 9999; '
        f'background-color: white; padding: 16px 20px; border-radius: 12px; '
        f'box-shadow: 0 4px 15px rgba(0,0,0,0.18); '
        f'font-family: Segoe UI, Tahoma, Geneva, Verdana, sans-serif; min-width: 240px;">'
        f'<div style="font-size: 15px; font-weight: 700; color: #1a1a1a; margin-bottom: 4px;">'
        f'Segmentasi Cluster</div>'
        f'<div style="font-size: 12px; color: #777; margin-bottom: 12px;">'
        f'Dataset: {nama_dataset} | k={k_val} | Sil={teks_sil}</div>'
        f'{item_legenda}'
        f'<div style="font-size: 11px; color: #999; margin-top: 10px;">Klik marker untuk detail</div>'
        f'</div>'
    )
    m.get_root().html.add_child(folium.Element(legenda))
    return m


def peta(jenis, k):
    df = muat_data(jenis, k)
    return render_peta(
        df,
        nama_dataset=f"{NAMA_JENIS[jenis]} (PCA-37)",
        k_val=k,
        sil_score=SILHOUETTE[jenis][k],
    )
```

### A. Peta Cluster Fitur Linear

#### A.1 Peta K = 2

```{code-cell} ipython3
:tags: [hide-input]

peta("linear", 2)
```

#### A.2 Peta K = 3

```{code-cell} ipython3
:tags: [hide-input]

peta("linear", 3)
```

#### A.3 Peta K = 4

```{code-cell} ipython3
:tags: [hide-input]

peta("linear", 4)
```

**Interpretasi peta fitur linear.** …

### B. Peta Cluster Fitur Polynomial

#### B.1 Peta K = 2

```{code-cell} ipython3
:tags: [hide-input]

peta("polynomial", 2)
```

#### B.2 Peta K = 3

```{code-cell} ipython3
:tags: [hide-input]

peta("polynomial", 3)
```

#### B.3 Peta K = 4

```{code-cell} ipython3
:tags: [hide-input]

peta("polynomial", 4)
```

**Interpretasi peta fitur polynomial.** …

---

## 8. Kesimpulan

Dari eksperimen clustering K-Means pada gabungan tiga polutan dengan fitur linear dan polynomial, diperoleh kesimpulan berikut:

1. **Pengaruh reduksi dimensi.** …
2. **Jumlah cluster terbaik.** …
3. **Perbandingan fitur linear dan polynomial.** …
4. **Pola spasial.** …
