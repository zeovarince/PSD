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

# Data Understanding

Data Understanding adalah tahap kedua dalam kerangka CRISP-DM. Setelah tujuan proyek jelas, tahap ini fokus pada satu hal: memahami data yang akan dipakai sebelum mulai mengolahnya. Ini mencakup dari mana data berasal, apa saja isi kolom-kolomnya, dan apakah ada nilai yang aneh atau tidak masuk akal.

---

## Sumber Data

### Sentinel-5P & TROPOMI

Data polutan dalam proyek ini berasal dari satelit **Sentinel-5P** milik European Space Agency (ESA), bagian dari program Copernicus. Sentinel-5P diluncurkan pada Oktober 2017 dan mengorbit Bumi sekali sehari pada ketinggian sekitar 824 km. Instrumen utamanya, **TROPOMI** (*TROPOspheric Monitoring Instrument*), mengukur konsentrasi gas atmosfer troposfer dengan resolusi spasial 3,5 × 5,5 km per piksel — resolusi tertinggi di antara satelit pemantau atmosfer yang tersedia secara publik.

Data yang digunakan adalah produk **Level 2 (L2)**: data yang sudah dikoreksi geometri dan radiometri, tapi masih dalam format orbit granul (belum diagregasi ke grid tetap). Dari sinilah kemudian dilakukan agregasi temporal (per hari) dan spasial (mean seluruh wilayah kajian).

### OpenEO — Platform Akses Data

Akses ke data Sentinel-5P dilakukan melalui platform **OpenEO Copernicus Data Space**, sebuah antarmuka terbuka yang memungkinkan pengguna memproses data satelit langsung di server tanpa perlu mengunduh file mentah berukuran besar.

- **Web Editor OpenEO:** [editor.openeo.org](https://editor.openeo.org/?server=https%3A%2F%2Fopeneo.dataspace.copernicus.eu%2Fopeneo%2F1.2)
- **Dokumentasi API:** [openeo.dataspace.copernicus.eu](https://openeo.dataspace.copernicus.eu)

**Instalasi library Python:**

```python
pip install openeo
```

**Koneksi dan autentikasi:**

```python
import openeo

connection = openeo.connect("https://openeo.dataspace.copernicus.eu")
connection.authenticate_oidc()
```

Autentikasi menggunakan OIDC (OpenID Connect) — login sekali lewat browser, token tersimpan otomatis untuk sesi berikutnya.

---

## Wilayah Kajian & Peta Interaktif

Pengambilan data dibatasi pada bounding box wilayah **Kamal–Kampus UTM, Bangkalan**. Batas wilayah didefinisikan menggunakan GeoJSON Polygon yang bisa dilihat dan diedit di [geojson.io](https://geojson.io).

**GeoJSON wilayah kajian:**

```json
{
  "type": "Feature",
  "properties": {},
  "geometry": {
    "type": "Polygon",
    "coordinates": [
      [
        [112.74249370782024, -7.170992207550057],
        [112.70985213794359, -7.170992207550057],
        [112.70985213794359, -7.127292848708009],
        [112.74249370782024, -7.127292848708009],
        [112.74249370782024, -7.170992207550057]
      ]
    ]
  }
}
```

**Visualisasi peta interaktif wilayah kajian:**

```python
import folium
from shapely.geometry import Polygon

# Koordinat batas wilayah Kamal-UTM (format GeoJSON: [lon, lat])
geojson_coords = [
    [112.74249370782024, -7.170992207550057],
    [112.70985213794359, -7.170992207550057],
    [112.70985213794359, -7.127292848708009],
    [112.74249370782024, -7.127292848708009],
    [112.74249370782024, -7.170992207550057]
]

# Hitung centroid wilayah sebagai titik pusat peta
area_polygon = Polygon(geojson_coords)
centroid_lon = area_polygon.centroid.x
centroid_lat = area_polygon.centroid.y
print(f"Titik Pusat Wilayah -> Latitude: {centroid_lat:.5f}, Longitude: {centroid_lon:.5f}")

# Buat peta interaktif
peta_wilayah = folium.Map(location=[centroid_lat, centroid_lon], zoom_start=13)

# Tambah polygon batas wilayah kajian
folium.Polygon(
    locations=[(lat, lon) for lon, lat in geojson_coords],
    color='#e74c3c',
    weight=3,
    fill=True,
    fill_opacity=0.2,
    tooltip='Batas Wilayah Kajian - Kamal UTM'
).add_to(peta_wilayah)

# Tandai titik centroid sebagai lokasi pengambilan data
folium.Marker(
    location=[centroid_lat, centroid_lon],
    popup='Titik Pengambilan Data Satelit (OpenEO)',
    icon=folium.Icon(color='blue', icon='cloud')
).add_to(peta_wilayah)

peta_wilayah
```

---

## Pengambilan Data (Crawling via OpenEO)

API Sentinel-5P L2 di OpenEO hanya mendukung **satu band per job**. Karena itu, pengambilan data NO2, CO, dan SO2 dilakukan dalam tiga job terpisah secara berurutan.

Dua parameter kunci dalam pipeline ini:
- `aggregate_temporal_period(reducer="mean", period="day")` → menghindari duplikasi data dalam satu hari (satelit kadang merekam satu wilayah lebih dari sekali sehari)
- `aggregate_spatial(reducer="mean", geometries=aoi)` → merata-ratakan seluruh piksel dalam bounding box menjadi satu nilai per hari

**Job 1 — NO2:**

```python
import openeo

connection = openeo.connect("https://openeo.dataspace.copernicus.eu")
connection.authenticate_oidc()

aoi = {
    "type": "Feature",
    "properties": {},
    "geometry": {
        "type": "Polygon",
        "coordinates": [
            [
                [112.74249370782024, -7.170992207550057],
                [112.70985213794359, -7.170992207550057],
                [112.70985213794359, -7.127292848708009],
                [112.74249370782024, -7.127292848708009],
                [112.74249370782024, -7.170992207550057]
            ]
        ]
    }
}

s5post = connection.load_collection(
    "SENTINEL_5P_L2",
    temporal_extent=["2025-08-25", "2026-08-29"],
    spatial_extent={
        "west": 112.709852,
        "south": -7.170992,
        "east": 112.742493,
        "north": -7.127292
    },
    bands=["NO2"],
)

s5p_daily = s5post.aggregate_temporal_period(reducer="mean", period="day")
s5p_aoi = s5p_daily.aggregate_spatial(reducer="mean", geometries=aoi)

job = s5p_aoi.execute_batch(
    title="Polutan_Kamal-UTM_NO2",
    outputfile="polutan_kamal_utm_NO2.csv",
    out_format="CSV"
)

job.start_and_wait()
print("Job selesai:", job.status())
```

**Job 2 — CO:**

```python
# Sama persis dengan Job NO2, ganti bagian berikut:
    bands=["CO"],
# dan
    title="Polutan_Kamal-UTM_CO",
    outputfile="polutan_kamal_utm_CO.csv",
```

**Job 3 — SO2:**

```python
# Sama persis dengan Job NO2, ganti bagian berikut:
    bands=["SO2"],
# dan
    title="Polutan_Kamal-UTM_SO2",
    outputfile="polutan_kamal_utm_SO2.csv",
```

---

## Deskripsi Fitur (Polutan)

Setiap file CSV hasil crawling memiliki dua kolom utama: `date` (tanggal pengukuran) dan nilai konsentrasi polutan dalam satuan **mol/m²** (kolom troposfer vertikal). Berikut penjelasan masing-masing polutan secara mendalam.

---

### NO2 — Nitrogen Dioksida

**Apa itu NO2?**

Nitrogen dioksida adalah gas anorganik berwarna coklat kemerahan yang termasuk dalam kelompok nitrogen oksida (NOx). Di atmosfer, NO2 terbentuk melalui dua jalur utama: oksidasi nitrogen monoksida (NO) yang dilepaskan saat pembakaran pada suhu tinggi, dan reaksi fotokimia di troposfer yang melibatkan sinar matahari. Gas ini menjadi salah satu indikator utama polusi udara perkotaan karena erat kaitannya dengan aktivitas transportasi dan industri.

**Proses pembentukan:**

Saat bahan bakar dibakar pada suhu tinggi (di mesin kendaraan, kapal, atau boiler industri), nitrogen dan oksigen di udara bereaksi membentuk NO. Di atmosfer, NO kemudian teroksidasi menjadi NO2 dalam hitungan menit hingga jam, tergantung kondisi atmosfer dan ketersediaan ozon.

**Sumber di wilayah Kamal-UTM:**

Kawasan Kamal memiliki beberapa sumber NO2 yang aktif setiap hari. Kendaraan bermotor berbahan bakar bensin dan solar di jalur utama Surabaya–Madura menjadi sumber dominan, terutama di jam sibuk pagi dan sore. Mesin kapal ferry di Pelabuhan Kamal mengeluarkan emisi NOx dalam volume besar karena menggunakan mesin diesel berdaya tinggi yang beroperasi terus-menerus. Selain itu, angin dari arah barat (dari Surabaya dan Gresik) sesekali membawa NO2 dari kawasan industri Petrokimia Gresik ke wilayah Madura.

**Satuan & nilai referensi:**

| Parameter | Nilai |
|---|---|
| Satuan data satelit | mol/m² (kolom troposfer) |
| Ambang batas WHO (tahunan) | 10 µg/m³ |
| Ambang batas WHO (24 jam) | 25 µg/m³ |
| Nilai latar belakang bersih | < 1 × 10⁻⁵ mol/m² |
| Nilai tinggi (perkotaan padat) | > 5 × 10⁻⁵ mol/m² |

**Dampak kesehatan:**

Paparan NO2 jangka pendek (beberapa jam) pada konsentrasi tinggi menyebabkan iritasi pada saluran pernapasan atas, batuk, dan sesak napas. Pada penderita asma, konsentrasi NO2 yang meningkat 50 µg/m³ saja sudah cukup memicu serangan. Paparan jangka panjang (bertahun-tahun) dikaitkan dengan penurunan fungsi paru, peningkatan risiko infeksi saluran pernapasan, dan pada anak-anak menyebabkan gangguan perkembangan paru.

**Dampak lingkungan:**

NO2 adalah prekursor utama pembentukan ozon troposfer (O3) melalui reaksi fotokimia, yang kemudian membentuk kabut fotokimia (smog). Gas ini juga berkontribusi pada hujan asam setelah bereaksi dengan uap air membentuk asam nitrat (HNO3).

---

### CO — Karbon Monoksida

**Apa itu CO?**

Karbon monoksida adalah gas tidak berwarna, tidak berbau, dan tidak berasa — sifat-sifat itulah yang membuatnya berbahaya. Gas ini terbentuk dari pembakaran tidak sempurna senyawa organik yang mengandung karbon, ketika suplai oksigen tidak cukup untuk mengoksidasi seluruh karbon menjadi CO2. Di troposfer, CO menjadi indikator kuat aktivitas pembakaran di permukaan bumi, baik dari kendaraan, industri, maupun kebakaran biomassa.

**Proses pembentukan:**

Pembakaran sempurna menghasilkan CO2. Tapi ketika campuran bahan bakar-udara tidak ideal (terlalu kaya bahan bakar, suhu pembakaran rendah, atau waktu pembakaran singkat), reaksi oksidasi berhenti di tengah jalan dan menghasilkan CO. Ini terjadi paling banyak pada mesin kendaraan tua tanpa catalytic converter, mesin diesel dalam kondisi beban penuh, dan pembakaran sampah terbuka.

**Sumber di wilayah Kamal-UTM:**

Kendaraan tua yang masih banyak beroperasi di jalur Kamal — terutama truk dan angkutan barang yang melayani pelabuhan — menjadi sumber CO signifikan. Kapal ferry berbahan bakar HSD (High Speed Diesel) juga melepaskan CO dalam jumlah besar saat mesin baru dinyalakan atau saat kapal bermanuver di dermaga. Pembakaran sampah terbuka yang masih umum di kawasan pesisir Madura turut menyumbang lonjakan konsentrasi CO sesekali, terutama di musim kemarau.

**Satuan & nilai referensi:**

| Parameter | Nilai |
|---|---|
| Satuan data satelit | mol/m² (kolom troposfer) |
| Ambang batas WHO (rata-rata 8 jam) | 10.000 µg/m³ (10 mg/m³) |
| Ambang batas WHO (rata-rata 1 jam) | 35.000 µg/m³ (35 mg/m³) |
| Nilai latar belakang bersih | ~1 × 10⁻² mol/m² |
| Nilai tinggi (dekat sumber) | > 3 × 10⁻² mol/m² |

**Dampak kesehatan:**

CO berikatan dengan hemoglobin dalam darah membentuk karboksihemoglobin (COHb) — ikatannya 200 kali lebih kuat dibanding oksigen. Akibatnya, sel darah merah tidak bisa mengangkut oksigen ke jaringan tubuh. Pada konsentrasi rendah, gejala yang muncul adalah sakit kepala dan pusing yang sering salah dikira migrain. Konsentrasi sedang menyebabkan mual, disorientasi, dan kelelahan ekstrem. Konsentrasi tinggi bisa menyebabkan kehilangan kesadaran dan kematian. Kelompok paling rentan adalah ibu hamil (CO menghambat perkembangan janin), bayi, lansia, dan penderita penyakit jantung.

**Dampak lingkungan:**

CO berkontribusi pada pembentukan ozon troposfer karena bereaksi dengan radikal hidroksil (OH) — yang seharusnya memecah metana dan gas rumah kaca lain di atmosfer. Dengan "memakan" OH, CO secara tidak langsung memperpanjang umur metana di atmosfer dan memperkuat efek rumah kaca.

---

### SO2 — Sulfur Dioksida

**Apa itu SO2?**

Sulfur dioksida adalah gas tidak berwarna dengan bau tajam dan menyengat yang menjadi penanda kuat aktivitas industri berat dan pembakaran bahan bakar fosil berkadar sulfur tinggi. Di atmosfer, SO2 memiliki umur yang relatif singkat (1–4 hari) sebelum teroksidasi menjadi sulfat, tapi dalam periode singkat itu sudah cukup menyebabkan dampak kesehatan dan lingkungan yang serius.

**Proses pembentukan:**

Bahan bakar fosil — terutama batubara dan solar kualitas rendah — mengandung senyawa sulfur organik. Saat dibakar, sulfur tersebut teroksidasi menjadi SO2. Semakin tinggi kadar sulfur dalam bahan bakar, semakin besar emisi SO2 yang dihasilkan. Bahan bakar kapal laut secara historis memiliki kadar sulfur jauh lebih tinggi dibanding bahan bakar kendaraan darat, meski regulasi internasional (IMO 2020) sudah mulai menekan kadar sulfur ini.

**Sumber di wilayah Kamal-UTM:**

Sumber utama SO2 di wilayah Kamal bukan dari kendaraan darat, melainkan dari kapal ferry yang menggunakan bahan bakar HSD atau MFO (Marine Fuel Oil). Mesin kapal beroperasi dengan bahan bakar berkadar sulfur lebih tinggi dibanding bensin kendaraan, dan emisinya dilepaskan langsung di area pelabuhan. Selain itu, industri di Surabaya bagian utara (Gresik) yang menggunakan batubara atau bahan bakar industri lain bisa membawa SO2 ke arah timur tergantung arah angin. Aktivitas vulkanik di Jawa Timur (Gunung Bromo, Semeru) juga sesekali berkontribusi pada lonjakan SO2 regional yang tertangkap satelit.

**Satuan & nilai referensi:**

| Parameter | Nilai |
|---|---|
| Satuan data satelit | mol/m² (kolom troposfer) |
| Ambang batas WHO (rata-rata 24 jam) | 40 µg/m³ |
| Ambang batas WHO (rata-rata 10 menit) | 500 µg/m³ |
| Nilai latar belakang bersih | < 5 × 10⁻⁴ mol/m² |
| Nilai tinggi (dekat industri/pelabuhan) | > 1 × 10⁻³ mol/m² |

**Dampak kesehatan:**

SO2 diserap di saluran pernapasan atas karena sangat mudah larut dalam air. Iritasi hidung, tenggorokan, dan bronkus terjadi bahkan pada konsentrasi rendah. Pada penderita asma, SO2 pada konsentrasi 0,4 ppm sudah cukup memicu bronkospasme — penyempitan tiba-tiba saluran napas. Paparan jangka panjang dikaitkan dengan bronkitis kronis dan penurunan fungsi paru. Anak-anak yang tumbuh di daerah dengan SO2 tinggi menunjukkan kapasitas paru di bawah rata-rata dibanding kelompok sebaya di daerah bersih.

**Dampak lingkungan:**

SO2 adalah penyebab utama hujan asam. Di atmosfer, SO2 teroksidasi menjadi SO3, lalu bereaksi dengan uap air membentuk asam sulfat (H2SO4). Hujan asam merusak ekosistem danau dan sungai, melarutkan mineral tanah, dan menghambat pertumbuhan tanaman. Di kawasan pesisir seperti Kamal, hujan asam juga mempercepat korosi struktur besi dan beton pada fasilitas pelabuhan.
