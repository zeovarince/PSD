
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


# Polutan Kamal (Revisi)
## Sumber Data

### Sentinel-5P & TROPOMI

Data polutan dalam proyek ini berasal dari satelit **Sentinel-5P** milik European Space Agency (ESA), bagian dari program Copernicus. Sentinel-5P diluncurkan pada Oktober 2017 dan mengorbit Bumi sekali sehari pada ketinggian sekitar 824 km. Instrumen utamanya, **TROPOMI** (*TROPOspheric Monitoring Instrument*), mengukur konsentrasi gas atmosfer troposfer dengan resolusi spasial 3,5 x 5,5 km per piksel.

Data yang digunakan adalah produk **Level 2 (L2)**: data yang sudah dikoreksi geometri dan radiometri, tapi masih dalam format orbit granul. Dari sinilah dilakukan agregasi temporal (per hari) dan spasial (mean seluruh wilayah kajian).

### OpenEO  Platform Akses Data

Akses ke data Sentinel-5P dilakukan melalui platform **OpenEO Copernicus Data Space**, sebuah antarmuka terbuka yang memungkinkan pengguna memproses data satelit langsung di server tanpa perlu mengunduh file mentah berukuran besar.

- **Web Editor OpenEO:** [editor.openeo.org](https://editor.openeo.org/?server=https%3A%2F%2Fopeneo.dataspace.copernicus.eu%2Fopeneo%2F1.2)
- **Dokumentasi API:** [openeo.dataspace.copernicus.eu](https://openeo.dataspace.copernicus.eu)
- **GeoJSON Wilayah Kajian:** [geojson.io](https://geojson.io)

---

## Instalasi Library

```{code-cell} ipython3
!pip install openeo folium shapely pandas -q
```

---

## Import Library

```{code-cell} ipython3
import openeo
import folium
import pandas as pd
from shapely.geometry import Polygon
```

---

## Wilayah Kajian & Peta Interaktif

Pengambilan data dibatasi pada bounding box wilayah **Kamal - Kampus UTM, Bangkalan**. Batas wilayah didefinisikan menggunakan GeoJSON Polygon yang bisa dilihat dan diedit di [geojson.io](https://geojson.io).

**GeoJSON wilayah kajian:**

```json
{
  "type": "Feature",
  "properties": {},
  "geometry": {
    "type": "Polygon",
    "coordinates": [
      [
        [112.6950, -7.1900],
        [112.7450, -7.1900],
        [112.7450, -7.1400],
        [112.6950, -7.1400],
        [112.6950, -7.1900]
      ]
    ]
  }
}
```

```{code-cell} ipython3
# Koordinat batas wilayah Kamal-UTM (format GeoJSON: [lon, lat])
geojson_coords = [
    [112.6950, -7.1900],
    [112.7450, -7.1900],
    [112.7450, -7.1400],
    [112.6950, -7.1400],
    [112.6950, -7.1900]
]

# Hitung centroid wilayah
area_polygon = Polygon(geojson_coords)
centroid_lon = area_polygon.centroid.x
centroid_lat = area_polygon.centroid.y

print(f"Centroid Latitude  : {centroid_lat:.6f}")
print(f"Centroid Longitude : {centroid_lon:.6f}")

# Buat peta interaktif
peta_wilayah = folium.Map(
    location=[centroid_lat, centroid_lon],
    zoom_start=13,
    tiles='OpenStreetMap'
)

# Polygon batas wilayah kajian
folium.Polygon(
    locations=[(lat, lon) for lon, lat in geojson_coords],
    color='#e74c3c',
    weight=3,
    fill=True,
    fill_color='#e74c3c',
    fill_opacity=0.15,
    tooltip='Batas Wilayah Kajian - Kamal UTM',
    popup=folium.Popup(
        '<b>Wilayah Kajian</b><br>Kamal - Kampus UTM, Bangkalan<br>'
        'Polutan: NO2<br>'
        'Periode: Agu 2025 - Agu 2026',
        max_width=250
    )
).add_to(peta_wilayah)

# Marker centroid
folium.Marker(
    location=[centroid_lat, centroid_lon],
    popup=folium.Popup(
        f'<b>Titik Pusat Wilayah</b><br>'
        f'Lat: {centroid_lat:.5f}<br>'
        f'Lon: {centroid_lon:.5f}<br>'
        f'Sumber data: Sentinel-5P via OpenEO',
        max_width=250
    ),
    tooltip='Titik Pengambilan Data Satelit (OpenEO)',
    icon=folium.Icon(color='blue', icon='cloud', prefix='fa')
).add_to(peta_wilayah)

peta_wilayah
```

---

## Pengambilan Data (Crawling via OpenEO)

API Sentinel-5P L2 di OpenEO hanya mendukung **satu band per job**. Data NO2 diambil dalam satu job dengan dua parameter kunci dalam pipeline ini:

- `aggregate_temporal_period(reducer="mean", period="day")`  menghindari duplikasi data dalam satu hari karena satelit kadang merekam satu wilayah lebih dari sekali per hari
- `aggregate_spatial(reducer="mean", geometries=aoi)`  merata-ratakan seluruh piksel dalam bounding box menjadi satu nilai per hari

```{code-cell} ipython3
connection = openeo.connect("https://openeo.dataspace.copernicus.eu")
connection.authenticate_oidc()
```

### Crawling data NO2

```{code-cell} ipython3
aoi = {
    "type": "Feature",
    "properties": {},
    "geometry": {
        "type": "Polygon",
        "coordinates": [
            [
                [112.6950, -7.1900],
                [112.7450, -7.1900],
                [112.7450, -7.1400],
                [112.6950, -7.1400],
                [112.6950, -7.1900]
            ]
        ]
    }
}

s5p = connection.load_collection(
    "SENTINEL_5P_L2",
    temporal_extent=["2025-08-31", "2026-08-31"],
    spatial_extent={
        "west":  112.6950,
        "south": -7.1900,
        "east":  112.7450,
        "north": -7.1400
    },
    bands=["NO2"],
)

s5p_daily = s5p.aggregate_temporal_period(reducer="mean", period="day")
s5p_aoi   = s5p_daily.aggregate_spatial(reducer="mean", geometries=aoi)

job = s5p_aoi.execute_batch(
    title="Polutan_Kamal_NO2",
    outputfile="no2_kamal.csv",
    out_format="CSV"
)

job.start_and_wait()
print("Job selesai:", job.status())
```

---

## Deskripsi Fitur (Polutan)

File CSV hasil crawling memiliki dua kolom utama: `date` (tanggal pengukuran) dan nilai konsentrasi polutan dalam satuan **mol/m2** (kolom troposfer vertikal). Berikut penjelasan polutan yang digunakan.

---

### NO2  Nitrogen Dioksida

**Apa itu NO2?**

Nitrogen dioksida adalah gas anorganik berwarna coklat kemerahan yang termasuk kelompok nitrogen oksida (NOx). Di atmosfer, NO2 terbentuk melalui dua jalur: oksidasi nitrogen monoksida (NO) yang dilepaskan saat pembakaran pada suhu tinggi, dan reaksi fotokimia di troposfer yang melibatkan sinar matahari.

**Proses pembentukan:**

Saat bahan bakar dibakar pada suhu tinggi di mesin kendaraan, kapal, atau boiler industri, nitrogen dan oksigen di udara bereaksi membentuk NO. Di atmosfer, NO teroksidasi menjadi NO2 dalam hitungan menit hingga jam, tergantung kondisi atmosfer dan ketersediaan ozon.

**Sumber di wilayah Kamal-UTM:**

Kendaraan bermotor di jalur utama Surabaya-Madura menjadi sumber dominan, terutama di jam sibuk pagi dan sore. Mesin kapal ferry di Pelabuhan Kamal mengeluarkan emisi NOx besar karena menggunakan mesin diesel berdaya tinggi yang beroperasi terus-menerus. Angin dari arah barat juga sesekali membawa NO2 dari kawasan industri Petrokimia Gresik ke wilayah Madura.

**Satuan dan nilai referensi:**

| Parameter | Nilai |
|---|---|
| Satuan data satelit | mol/m2 (kolom troposfer) |
| Ambang batas WHO (tahunan) | 10 ug/m3 |
| Ambang batas WHO (24 jam) | 25 ug/m3 |
| Nilai latar belakang bersih | < 1 x 10^-5 mol/m2 |
| Nilai tinggi (perkotaan padat) | > 5 x 10^-5 mol/m2 |

**Dampak kesehatan:**

Paparan NO2 jangka pendek menyebabkan iritasi saluran pernapasan atas, batuk, dan sesak napas. Pada penderita asma, kenaikan konsentrasi 50 ug/m3 sudah cukup memicu serangan. Paparan jangka panjang dikaitkan dengan penurunan fungsi paru, peningkatan risiko infeksi saluran pernapasan, dan pada anak-anak menyebabkan gangguan perkembangan paru.

**Dampak lingkungan:**

NO2 adalah prekursor utama pembentukan ozon troposfer (O3) melalui reaksi fotokimia, yang kemudian membentuk kabut fotokimia (smog). Gas ini juga berkontribusi pada hujan asam setelah bereaksi dengan uap air membentuk asam nitrat (HNO3).