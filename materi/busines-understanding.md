# Business Understanding
---
## Memahami Business Understanding
Business Understanding adalah tahap pertama dalam kerangka CRISP-DM (*Cross Industry Standard Process for Data Mining*). Sebelum menyentuh data, seorang data scientist perlu memahami dulu apa masalah yang ingin diselesaikan dan mengapa masalah itu penting. Tahap ini menentukan arah seluruh proyek salah rumus di sini, seluruh analisis berikutnya ikut meleset.

Secara sederhana, Business Understanding menjawab tiga pertanyaan:

- Apa yang ingin diketahui?
- Mengapa itu perlu diketahui?
- Bagaimana rencana untuk menjawabnya?

---

## Latar Belakang & Konteks Wilayah

Kamal adalah kecamatan di ujung barat Pulau Madura, Kabupaten Bangkalan. Kawasan ini menjadi pintu masuk utama Madura sebelum Jembatan Suramadu beroperasi, dan hingga kini tetap menjadi titik penyeberangan ferry Surabaya–Madura yang aktif. Kendaraan berat, kapal feri, dan lalu lintas kendaraan pribadi menghasilkan emisi gas buang setiap hari di sepanjang kawasan pelabuhan dan jalan arteri menuju jembatan.

Universitas Trunojoyo Madura (UTM) berdiri di sisi utara kawasan ini, berjarak dekat dengan jalur utama Kamal. Ribuan mahasiswa dan tenaga pengajar beraktivitas di area yang secara geografis terjepit antara kawasan pesisir berpolusi tinggi dan jalur kendaraan padat.

Data kualitas udara untuk wilayah Bangkalan, khususnya Kamal, hampir tidak tersedia secara publik. Stasiun pemantauan udara darat terdekat ada di Surabaya. Proyek ini mengisi kekosongan itu dengan memanfaatkan data satelit Sentinel-5P yang mencakup seluruh wilayah tanpa membutuhkan sensor fisik di lapangan.

---

## Tujuan Proyek

**Tujuan bisnis:** Mengetahui kondisi kualitas udara di wilayah Kamal–Kampus UTM, Bangkalan berdasarkan konsentrasi polutan atmosfer selama satu tahun terakhir.

**Tujuan teknis:** Mengumpulkan data konsentrasi NO2, CO, dan SO2 dari satelit Sentinel-5P untuk periode Agustus 2025–Agustus 2026, mengagregasinya per hari dalam bounding box wilayah Kamal–UTM, dan memvisualisasikannya sebagai time series.

**Contoh sederhana (konteks serupa):**

Sebuah dinas lingkungan hidup menerima keluhan warga soal sesak napas di sekitar kawasan industri. Tujuan bisnisnya: *"Apakah kualitas udara di kawasan itu memang buruk, dan kapan kondisi terburuknya terjadi?"* Dari situ baru muncul tujuan teknis: kumpulkan data konsentrasi PM2.5 dan NO2 harian selama satu tahun, lalu visualisasikan trennya.

---

## Manfaat

Proyek ini menghasilkan data yang berguna untuk tiga kepentingan:

1. **Kesehatan civitas akademika** — Data tren harian NO2 dan CO memungkinkan identifikasi periode konsentrasi polutan tinggi yang berisiko bagi mahasiswa dan staf UTM yang beraktivitas di luar ruangan.

2. **Baseline data lingkungan Bangkalan** — Bangkalan belum punya rekam jejak data kualitas udara yang terdokumentasi. Data satu tahun ini bisa menjadi referensi awal untuk perbandingan di masa depan.

3. **Gambaran dampak transportasi** — Pola time series polutan bisa memperlihatkan apakah ada lonjakan konsentrasi di jam-jam tertentu atau musim tertentu, yang bisa dikaitkan dengan aktivitas ferry dan kendaraan di Selat Madura.

---

## Rencana & Batasan Proyek

### Rencana

| Komponen | Detail |
|---|---|
| Sumber data | Sentinel-5P L2 via OpenEO/Copernicus |
| Wilayah | Bounding box Kamal–UTM (112.7098°E–112.7424°E, 7.1272°S–7.1709°S) |
| Periode | 25 Agustus 2025 – 31 Agustus 2026 |
| Polutan | NO2, CO, SO2 |
| Tools | Python (OpenEO client), GeoJSON, Pandas, Matplotlib |
| Agregasi | Mean harian per area (temporal + spasial) |
| Output | File CSV + grafik time series + web statis (repo: PSD) |

**Contoh sederhana (konteks serupa):**

Tim dinas tadi membuat rencana: pasang sensor di 5 titik kawasan industri, rekam data setiap jam selama 12 bulan, olah dengan Python, hasilkan laporan tren bulanan. Tanpa rencana ini, tim bisa mengumpulkan data yang formatnya tidak konsisten atau periodenya tidak cukup untuk ditarik kesimpulan.

### Batasan & Risiko

**Batasan teknis:**
- Resolusi spasial Sentinel-5P sekitar 3,5 × 5,5 km — variasi polutan antar titik dalam satu kelurahan tidak tertangkap
- Batas wilayah berupa bounding box persegi, bukan batas administratif Kecamatan Kamal yang sesungguhnya
- Ada hari-hari tanpa data karena tutupan awan tebal atau gap orbit satelit

**Asumsi:**
- Sentinel-5P merekam wilayah Bangkalan secara konsisten dalam periode yang dipilih
- Agregasi mean spasial cukup merepresentasikan kondisi udara di bounding box

**Risiko:**
- Data tidak lengkap untuk periode tertentu → perlu strategi penanganan missing value di tahap Data Understanding
- Job crawling di OpenEO gagal atau timeout → perlu retry dan verifikasi output CSV