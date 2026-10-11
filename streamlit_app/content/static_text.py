"""
Modul teks statis dan metadata referensi resmi untuk LULC Jawa Timur.
Berdasarkan SNI 7645-1:2014, KLHK, dan laporan Sentinel-2A UTS SIG.
"""

# Warna standar resmi kelas tutupan lahan Jawa Timur
WARNA_KELAS = {
    "Sawah": "#FFD92F",
    "Bangunan": "#E41A1C",
    "Mangrove": "#8E44AD",
    "Lahan Hijau": "#2E7D32",
    "Perairan Terbuka (Laut)": "#0D47A1",
    "Danau": "#4FC3F7"
}

# 1. Tujuan Analisis dan Kebijakan
TUJUAN_ANALISIS = (
    "Memetakan penggunaan dan tutupan lahan (Land Use / Land Cover - LULC) Provinsi Jawa Timur "
    "ke dalam 6 kelas secara objektif dan terstandar dari citra satelit multispektral Sentinel-2 Level-2A. "
    "Hasil klasifikasi terbimbing ini menjadi basis instrumen pendukung kebijakan perencanaan ruang dan konservasi."
)

PILAR_KEBIJAKAN = [
    {
        "judul": "Pemantauan Alih Fungsi Sawah",
        "deskripsi": "Mengawasi laju konversi lahan pertanian pangan berkelanjutan (LP2B) menjadi permukiman atau kawasan industri di koridor aglomerasi Surabaya Raya dan Pantura."
    },
    {
        "judul": "Perlindungan Ekosistem Mangrove",
        "deskripsi": "Memantau kelestarian hutan bakau pesisir utara dan selatan Jawa Timur sebagai benteng alami dari abrasi, intrusi air laut, serta penyerap karbon pesisir (blue carbon)."
    },
    {
        "judul": "Pengawasan Perairan Darat (Danau & Ranu)",
        "deskripsi": "Memonitor fluktuasi badan air tawar seperti waduk, situ, dan ranu vulkanik guna menjaga ketahanan cadangan air baku irigasi dan pembangkit listrik."
    },
    {
        "judul": "Pengendalian Tata Ruang & RTH",
        "deskripsi": "Memastikan batas pemisah yang tegas antara lahan terbangun (zona perkotaan) dan tutupan vegetasi hijau alami untuk mendukung target 30% Ruang Terbuka Hijau (RTH)."
    }
]

# Wilayah Studi AOI
AOI_INFO = {
    "nama": "Provinsi Jawa Timur dan Perairan Sekitarnya",
    "bujur_barat": "110,70° BT",
    "bujur_timur": "114,45° BT",
    "lintang_selatan": "8,80° LS",
    "lintang_utara": "6,60° LS",
    "proyeksi": "WGS 84 (EPSG:4326) / Proyeksi Luas UTM Zona 49S"
}

# Acuan Klasifikasi Nasional SNI 7645-1:2014 & KLHK
TABEL_ACUAN_KLASIFIKASI = [
    {
        "no": 1,
        "kelas": "Sawah",
        "padanan": "Daerah pertanian, sawah irigasi / tadah hujan",
        "sni": "Pertanian Lahan Basah",
        "warna": WARNA_KELAS["Sawah"]
    },
    {
        "no": 2,
        "kelas": "Bangunan",
        "padanan": "Permukiman dan lahan bukan pertanian yang berkaitan (lahan terbangun)",
        "sni": "Lahan Terbangun / Permukiman",
        "warna": WARNA_KELAS["Bangunan"]
    },
    {
        "no": 3,
        "kelas": "Mangrove",
        "padanan": "Hutan mangrove pesisir",
        "sni": "Hutan Bakau / Mangrove",
        "warna": WARNA_KELAS["Mangrove"]
    },
    {
        "no": 4,
        "kelas": "Lahan Hijau",
        "padanan": "Vegetasi non-sawah: hutan lahan kering, hutan tanaman, perkebunan, semak belukar",
        "sni": "Hutan & Lahan Terbuka Bervegetasi",
        "warna": WARNA_KELAS["Lahan Hijau"]
    },
    {
        "no": 5,
        "kelas": "Perairan Terbuka (Laut)",
        "padanan": "Perairan laut pesisir dan samudra",
        "sni": "Perairan Laut",
        "warna": WARNA_KELAS["Perairan Terbuka (Laut)"]
    },
    {
        "no": 6,
        "kelas": "Danau",
        "padanan": "Perairan darat: danau alami, waduk, ranu, situ",
        "sni": "Badan Air Darat",
        "warna": WARNA_KELAS["Danau"]
    }
]

# Kolekting Data Sentinel-2
KOMPONEN_DATA = [
    {"Komponen": "Citra Satelit", "Keterangan": "Sentinel-2A Level-2A (Bottom-Of-Atmosphere / Surface Reflectance)"},
    {"Komponen": "Penyedia Data", "Keterangan": "Copernicus Data Space Ecosystem (CDSE) via Sentinel Hub Process API"},
    {"Komponen": "Rentang Periode", "Keterangan": "1 Mei 2026 – 30 September 2026 (periode musim kemarau stabil)"},
    {"Komponen": "Metode Komposit", "Keterangan": "Median temporal bebas awan (mengurangi gangguan atmosfer dan anomali sesaat)"},
    {"Komponen": "Penyaringan Awan", "Keterangan": "Scene awan > 30% dibuang; masking piksel awan dan cirrus berbasis Scene Classification Layer (SCL kelas 3, 8, 9, 10)"},
    {"Komponen": "Data Label", "Keterangan": "Shapefile poligon digitasi 6 kelas terverifikasi di Jawa Timur"},
    {"Komponen": "Resolusi Raster", "Keterangan": "Resolusi asli band 10 m; raster klasifikasi komposit visual 200 m per piksel"}
]

# Deskripsi 10 Band Sentinel-2A
TABEL_BAND = [
    {"Band": "B2", "Nama": "Blue", "Panjang Gelombang": "490 nm", "Resolusi": "10 m", "Karakteristik": "Sensitif terhadap hamburan aerosol dan penetrasi air jernih."},
    {"Band": "B3", "Nama": "Green", "Panjang Gelombang": "560 nm", "Resolusi": "10 m", "Karakteristik": "Puncak pantulan klorofil daun sehat dan deteksi badan air."},
    {"Band": "B4", "Nama": "Red", "Panjang Gelombang": "665 nm", "Resolusi": "10 m", "Karakteristik": "Penyerapan kuat oleh klorofil; diferensiasi vegetasi vs tanah terbuka."},
    {"Band": "B5", "Nama": "Red Edge 1", "Panjang Gelombang": "705 nm", "Resolusi": "20 m", "Karakteristik": "Batas peralihan serapan merah ke pantulan inframerah."},
    {"Band": "B6", "Nama": "Red Edge 2", "Panjang Gelombang": "740 nm", "Resolusi": "20 m", "Karakteristik": "Sensitif terhadap konsentrasi klorofil dan transisi kanopi."},
    {"Band": "B7", "Nama": "Red Edge 3", "Panjang Gelombang": "783 nm", "Resolusi": "20 m", "Karakteristik": "Sensitif terhadap biomassa dan struktur anatomi mesofil daun."},
    {"Band": "B8", "Nama": "NIR (Near Infrared)", "Panjang Gelombang": "842 nm", "Resolusi": "10 m", "Karakteristik": "Reflektansi puncak biomassa sel vegetasi; kontras tajam terhadap air."},
    {"Band": "B8A", "Nama": "Narrow NIR", "Panjang Gelombang": "865 nm", "Resolusi": "20 m", "Karakteristik": "Pita sempit bebas serapan uap air; deteksi kanopi sempit."},
    {"Band": "B11", "Nama": "SWIR 1", "Panjang Gelombang": "1610 nm", "Resolusi": "20 m", "Karakteristik": "Sensitif terhadap kelembapan tanaman dan struktur mineral lahan terbangun."},
    {"Band": "B12", "Nama": "SWIR 2", "Panjang Gelombang": "2190 nm", "Resolusi": "20 m", "Karakteristik": "Penetrasi awan tipis; membedakan batuan, tanah gersang, dan permukiman."}
]

CATATAN_BAND_DILEWATI = (
    "Band B1 (Costal Aerosol - 60 m) dan B9 (Water Vapour - 60 m) tidak digunakan karena resolusi spasialnya rendah (60 m) "
    "dan fungsinya khusus untuk koreksi atmosfer. Band B10 (Cirrus - 60 m) tidak tersedia pada produk Level-2A "
    "karena telah terkoreksi otomatis dalam kanal SCL."
)

# 8 Indeks Spektral + Rumus LaTeX
TABEL_INDEKS = [
    {
        "Nama": "NDVI",
        "Kepanjangan": "Normalized Difference Vegetation Index",
        "Rumus": r"NDVI = \frac{B8 - B4}{B8 + B4}",
        "Fungsi": "Mengukur densitas dan kehijauan vegetasi aktif."
    },
    {
        "Nama": "NDWI",
        "Kepanjangan": "Normalized Difference Water Index",
        "Rumus": r"NDWI = \frac{B3 - B8}{B3 + B8}",
        "Fungsi": "Mendeteksi keterbukaan badan air dan kelembapan permukaan."
    },
    {
        "Nama": "MNDWI",
        "Kepanjangan": "Modified Normalized Difference Water Index",
        "Rumus": r"MNDWI = \frac{B3 - B11}{B3 + B11}",
        "Fungsi": "Membedakan badan air dari lahan terbangun dengan menekan sinyal perkotaan."
    },
    {
        "Nama": "NDBI",
        "Kepanjangan": "Normalized Difference Built-up Index",
        "Rumus": r"NDBI = \frac{B11 - B8}{B11 + B8}",
        "Fungsi": "Menonjolkan konsentrasi area terbangun, beton, dan atap permukiman."
    },
    {
        "Nama": "NDRE",
        "Kepanjangan": "Normalized Difference Red Edge",
        "Rumus": r"NDRE = \frac{B8 - B5}{B8 + B5}",
        "Fungsi": "Mendeteksi kandungan klorofil saat kanopi rapat di mana NDVI telah jenuh."
    },
    {
        "Nama": "EVI",
        "Kepanjangan": "Enhanced Vegetation Index",
        "Rumus": r"EVI = 2.5 \cdot \frac{B8 - B4}{B8 + 6 \cdot B4 - 7.5 \cdot B2 + 1}",
        "Fungsi": "Mengoreksi pengaruh atmosfer dan latar belakang tanah pada vegetasi lebat."
    },
    {
        "Nama": "SAVI",
        "Kepanjangan": "Soil Adjusted Vegetation Index",
        "Rumus": r"SAVI = \frac{(B8 - B4) \cdot 1.5}{B8 + B4 + 0.5}",
        "Fungsi": "Koreksi pantulan tanah terbuka pada area vegetasi jarang."
    },
    {
        "Nama": "BSI",
        "Kepanjangan": "Bare Soil Index",
        "Rumus": r"BSI = \frac{(B11 + B4) - (B8 + B2)}{(B11 + B4) + (B8 + B2)}",
        "Fungsi": "Memetakan lahan tanah terbuka gundul tanpa vegetasi."
    }
]

# Perbedaan Basis Polygon vs Pixel
PERBEDAAN_BASIS = [
    {
        "Fitur": "Unit Observasi",
        "Polygon": "1 poligon = 1 sampel (1 piksel 10 m pada titik representatif poligon)",
        "Pixel": "Banyak titik acak dalam poligon (1 titik acak = 1 piksel 10 m)"
    },
    {
        "Fitur": "Strategi Sampling",
        "Polygon": "Tidak ada sub-sampling; semua poligon digitasi diikutsertakan",
        "Pixel": "Target N_PER_CLASS = 1500, MAX_PER_POLY = 150, deduplikasi spasial"
    },
    {
        "Fitur": "Pembagian Data (Split)",
        "Polygon": "Stratified random split per sampel poligon (70% Train, 15% Val, 15% Test)",
        "Pixel": "Stratified per-poligon (anti-kebocoran autokorelasi spasial antar tetangga piksel)"
    },
    {
        "Fitur": "Karakteristik & Risiko",
        "Polygon": "Jumlah sampel uji kecil (43 sampel); akurasi rentan fluktuatif",
        "Pixel": "Sampel uji independen besar (790 piksel); autokorelasi internal poligon tetap diisolasi"
    },
    {
        "Fitur": "Model Pemenang",
        "Polygon": "Gaussian Naive Bayes (Akurasi 100.00% pada sampel poligon bersih)",
        "Pixel": "KNN k=7 distance (Akurasi 90.00% vs Naive Bayes 57.72%)"
    }
]

# Keterbatasan Metodologi
KETERBATASAN = {
    "polygon": [
        "Ukuran dataset uji poligon relatif kecil (43 sampel poligon independen), sehingga satu kesalahan prediksi berbobot 2.33% pada akurasi total.",
        "Reflektansi pada titik representatif poligon mengasumsikan homogenitas internal, yang mungkin mengabaikan variasi mikro di dalam satu bidang lahan besar.",
        "Periode pengamatan terbatas pada musim kemarau (Mei–September 2026), belum menangkap dinamika rotasi tanam sawah pada musim hujan.",
        "Resolusi raster peta komposit Folium (200 m) lebih kasar dari data pelatihan 10 m, memicu potensi piksel campuran (mixed pixel) pada batas sempit."
    ],
    "pixel": [
        "Piksel dari poligon yang sama memiliki autokorelasi spasial yang kuat. Meskipun pemisahan telah dilakukan per poligon, variasi spektral uji dibatasi oleh jumlah poligon per kelas.",
        "Kelas minoritas seperti Mangrove dan Danau memiliki luasan poligon terbatas sehingga jumlah piksel yang berhasil diekstraksi lebih sedikit dibanding target.",
        "Pada level piksel, asumsi independensi fitur Gaussian Naive Bayes dilanggar keras oleh korelasi antar-band Sentinel-2, menyebabkan performa GNB jatuh ke 57.72%.",
        "Kelas Lahan Hijau mencakup spektrum luas (hutan lebat, kebun, semak), sehingga batas spektralnya beririsan dengan tepi Sawah dan Mangrove."
    ]
}

# Implikasi Kebijakan per Kelas
IMPLIKASI_KEBIJAKAN = {
    "Sawah": "Luas sawah menjadi acuan mutlak pengendalian Lahan Pertanian Pangan Berkelanjutan (LP2B). Selisih estimasi antara model menunjukkan perlunya konfirmasi lapangan sebelum menerbitkan izin alih fungsi.",
    "Bangunan": "Sebaran piksel terbangun mencerminkan arah ekspansi perkotaan di sepanjang jalan arteri. Pemantauan ketat diperlukan agar tidak merambah sabuk hijau penyangga.",
    "Mangrove": "Luas ekosistem mangrove di pesisir utara dan selatan Jawa Timur harus dipertahankan secara zonasi untuk menahan abrasi dan menyerap emisi karbon pesisir.",
    "Lahan Hijau": "Merupakan paru-paru wilayah dan kawasan tangkapan air. Penurunan luas vegetasi hijau menjadi indikator awal degradasi DAS dan potensi risiko banjir/longsor.",
    "Perairan Terbuka (Laut)": "Batas perairan laut membatasi garis pantai dan sempadan pantai. Konsistensi klasifikasi badan air memperjelas dinamika sedimentasi muara sungai.",
    "Danau": "Badan air darat dan waduk berukuran kompak memerlukan pemantauan eutrofikasi dan sedimentasi agar fungsi suplai irigasi dan air minum tetap berlanjut."
}
