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

# K-Means Clustering Polutan

Dokumen ini menjelaskan proses pengelompokan (clustering) area berdasarkan karakteristik deret waktu polutan NO2, SO2, dan CO. Data ekstraksi fitur menggunakan TSFEL dikumpulkan dari seluruh daerah bersama teman sekelas, kemudian diproses menggunakan algoritma K-Means dengan jumlah klaster K=3.

Setiap polutan diuji dalam dua skenario: **tanpa reduksi dimensi (Non-PCA)** dan **dengan reduksi dimensi PCA** (68 fitur → 37 komponen utama), sehingga kita dapat membandingkan apakah PCA memengaruhi distribusi dan kualitas klaster yang terbentuk.

---

## Alur Kerja (Workflow) KNIME

Eksperimen ini menggunakan dua workflow berbeda di KNIME, masing-masing untuk skenario tanpa dan dengan PCA.

### Workflow Tanpa PCA

![Workflow K-Means Tanpa PCA](/assets/1790545022814_image.png)

Penjelasan fungsi setiap node:

1. **CSV Reader**: Membaca file CSV hasil ekstraksi fitur (`ekstraksi_fitur_[polutan].csv`) langsung ke dalam environment KNIME. File ini berisi kolom identitas (`id`, `nama`, `daerah`) dan 68 kolom fitur statistik hasil ekstraksi TSFEL.

2. **k-Means**: Algoritma inti yang membagi seluruh data ke dalam K=3 kelompok berdasarkan kedekatan jarak Euclidean antar titik fitur. Karena tidak ada preprocessing reduksi dimensi, K-Means bekerja langsung pada ruang fitur berdimensi 68.

3. **Scatter Plot**: Memvisualisasikan hasil pengelompokan. Sumbu X menampilkan nama daerah dan sumbu Y menampilkan label cluster yang ditetapkan, sehingga distribusi tiap daerah ke klasternya terlihat jelas.

### Workflow Dengan PCA

![Workflow K-Means Dengan PCA](/assets/1790545014826_image.png)

Penjelasan fungsi setiap node:

1. **CSV Reader**: Membaca file CSV hasil ekstraksi fitur, sama seperti workflow non-PCA.

2. **PCA (Principal Component Analysis)**: Mereduksi dimensi data dari 68 fitur asli menjadi 37 komponen utama (*Principal Components*). PCA bekerja dengan mentransformasikan fitur-fitur yang berkorelasi tinggi menjadi variabel baru yang ortogonal (tidak saling berkorelasi). Penerapan PCA di sini berguna untuk mengatasi *curse of dimensionality* sehingga perhitungan jarak pada K-Means menjadi lebih representatif, mengurangi beban komputasi, dan menyaring noise dari fitur yang tidak relevan.

3. **k-Means**: Menjalankan algoritma clustering pada 37 komponen PCA hasil reduksi. Daerah dengan pola polusi serupa menempati klaster yang sama.

4. **Scatter Plot**: Visualisasi hasil clustering, identik dengan workflow non-PCA.

---

## Polutan NO2

### Tanpa PCA

*Scatter Plot KNIME (NO2 — Tanpa PCA):*

![Scatter Plot K-Means NO2 Tanpa PCA](/assets/NONPCAScatterPlotNO2.png)

*Implementasi Python:*

```{code-cell}
:tags: [hide-input]
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

CSV_PATH = "ekstraksi_fitur_no2.csv"
KOLOM_IDENTITAS = ['id', 'nama', 'daerah']
K = 3

df = pd.read_csv(CSV_PATH)
fitur = df.drop(KOLOM_IDENTITAS, axis=1)

X = StandardScaler().fit_transform(fitur)

kmeans = KMeans(n_clusters=K, random_state=42, n_init=10)
df['cluster'] = kmeans.fit_predict(X)
df['cluster_label'] = 'cluster_' + df['cluster'].astype(str)

print(f"Inertia: {kmeans.inertia_:.4f}")
print("\nJumlah data per cluster:")
print(df['cluster_label'].value_counts().sort_index())
print("\nDetail daerah per cluster:")
for c in sorted(df['cluster'].unique()):
    daerah = df[df['cluster'] == c]['daerah'].tolist()
    print(f"  cluster_{c} ({len(daerah)} daerah): {daerah}")

label_cluster = [f"cluster_{i}" for i in range(K)]
y = df['cluster']
x = range(len(df))

plt.figure(figsize=(16, 5))
colors = ['#6b8bd6', '#e07b5a', '#5ab87e']
scatter_colors = [colors[c] for c in y]
plt.scatter(x, y, s=60, c=scatter_colors)
plt.xticks(x, df['daerah'], rotation=90, fontsize=7)
plt.yticks(range(K), label_cluster)
plt.ylim(-0.5, K - 0.5)
plt.title("Scatter Plot K-Means NO2 Tanpa PCA (K=3)", loc="left", fontweight="bold")
plt.xlabel("Daerah")
plt.ylabel("Cluster")
plt.grid(True, color="#eeeeee")
plt.tight_layout()
plt.show()
```

### Dengan PCA

*Scatter Plot KNIME (NO2 — Dengan PCA):*

![Scatter Plot K-Means NO2 Dengan PCA](/assets/ScatterPlotNO2.png)

*Implementasi Python:*

```{code-cell}
:tags: [hide-input]
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

CSV_PATH = "ekstraksi_fitur_no2.csv"
KOLOM_IDENTITAS = ['id', 'nama', 'daerah']
K = 3
N_KOMPONEN_PCA = 37

df = pd.read_csv(CSV_PATH)
fitur = df.drop(KOLOM_IDENTITAS, axis=1)

X_scaled = StandardScaler().fit_transform(fitur)
X_pca = PCA(n_components=N_KOMPONEN_PCA, random_state=42).fit_transform(X_scaled)

print(f"Reduksi dimensi: {fitur.shape[1]} fitur → {N_KOMPONEN_PCA} komponen PCA")

kmeans = KMeans(n_clusters=K, random_state=42, n_init=10)
df['cluster'] = kmeans.fit_predict(X_pca)
df['cluster_label'] = 'cluster_' + df['cluster'].astype(str)

print(f"Inertia: {kmeans.inertia_:.4f}")
print("\nJumlah data per cluster:")
print(df['cluster_label'].value_counts().sort_index())
print("\nDetail daerah per cluster:")
for c in sorted(df['cluster'].unique()):
    daerah = df[df['cluster'] == c]['daerah'].tolist()
    print(f"  cluster_{c} ({len(daerah)} daerah): {daerah}")

label_cluster = [f"cluster_{i}" for i in range(K)]
y = df['cluster']
x = range(len(df))

plt.figure(figsize=(16, 5))
colors = ['#6b8bd6', '#e07b5a', '#5ab87e']
scatter_colors = [colors[c] for c in y]
plt.scatter(x, y, s=60, c=scatter_colors)
plt.xticks(x, df['daerah'], rotation=90, fontsize=7)
plt.yticks(range(K), label_cluster)
plt.ylim(-0.5, K - 0.5)
plt.title("Scatter Plot K-Means NO2 Dengan PCA (K=3, n_components=37)", loc="left", fontweight="bold")
plt.xlabel("Daerah")
plt.ylabel("Cluster")
plt.grid(True, color="#eeeeee")
plt.tight_layout()
plt.show()
```

### Perbandingan dan Interpretasi NO2

Baik tanpa PCA maupun dengan PCA, hasil clustering NO2 menghasilkan distribusi yang **identik** — nilai inertia sama (1001.2819) dan pembagian daerah ke klaster tidak berubah sama sekali. Ini menunjukkan bahwa 37 komponen PCA sudah menangkap hampir seluruh varians penting dari 68 fitur asli, sehingga informasi yang hilang saat reduksi dimensi tidak berdampak pada keputusan clustering.

Dari scatter plot, tiga kelompok terbentuk dengan karakteristik berikut:

- **Cluster 0 (20 daerah)** — kelompok terbesar, memuat daerah dengan pola polusi NO2 yang paling umum dan stabil. Daerah seperti Manyar, Asemrowo Surabaya, Menganti Gresik, hingga Kwanyar Bangkalan masuk di sini. Fluktuasi NO2 di daerah-daerah ini bergerak dalam rentang yang serupa sepanjang periode observasi.

- **Cluster 2 (16 daerah)** — kelompok menengah dengan pola polusi yang sedikit berbeda dari mayoritas. Daerah seperti Cerme Gresik, Widodaren Ngawi, Wonoayu, dan Nunukan menunjukkan karakteristik time-series NO2 yang homogen satu sama lain namun berbeda dari cluster 0.

- **Cluster 1 (1 daerah)** — **Kamal, Banyuajuh** berdiri sendiri secara terisolasi. Karakteristik pergerakan NO2 di titik ini sama sekali tidak menyerupai daerah manapun dalam dataset, mengindikasikan adanya sumber emisi lokal yang spesifik di wilayah tersebut.

---

## Polutan SO2

### Tanpa PCA

*Scatter Plot KNIME (SO2 — Tanpa PCA):*

![Scatter Plot K-Means SO2 Tanpa PCA](/assets/NONPCAScatterPlotSO2.png)

*Implementasi Python:*

```{code-cell}
:tags: [hide-input]
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

CSV_PATH = "ekstraksi_fitur_so2.csv"
KOLOM_IDENTITAS = ['id', 'nama', 'daerah']
K = 3

df = pd.read_csv(CSV_PATH)
fitur = df.drop(KOLOM_IDENTITAS, axis=1)

X = StandardScaler().fit_transform(fitur)

kmeans = KMeans(n_clusters=K, random_state=42, n_init=10)
df['cluster'] = kmeans.fit_predict(X)
df['cluster_label'] = 'cluster_' + df['cluster'].astype(str)

print(f"Inertia: {kmeans.inertia_:.4f}")
print("\nJumlah data per cluster:")
print(df['cluster_label'].value_counts().sort_index())
print("\nDetail daerah per cluster:")
for c in sorted(df['cluster'].unique()):
    daerah = df[df['cluster'] == c]['daerah'].tolist()
    print(f"  cluster_{c} ({len(daerah)} daerah): {daerah}")

label_cluster = [f"cluster_{i}" for i in range(K)]
y = df['cluster']
x = range(len(df))

plt.figure(figsize=(16, 5))
colors = ['#6b8bd6', '#e07b5a', '#5ab87e']
scatter_colors = [colors[c] for c in y]
plt.scatter(x, y, s=60, c=scatter_colors)
plt.xticks(x, df['daerah'], rotation=90, fontsize=7)
plt.yticks(range(K), label_cluster)
plt.ylim(-0.5, K - 0.5)
plt.title("Scatter Plot K-Means SO2 Tanpa PCA (K=3)", loc="left", fontweight="bold")
plt.xlabel("Daerah")
plt.ylabel("Cluster")
plt.grid(True, color="#eeeeee")
plt.tight_layout()
plt.show()
```

### Dengan PCA

*Scatter Plot KNIME (SO2 — Dengan PCA):*

![Scatter Plot K-Means SO2 Dengan PCA](/assets/ScatterPlotSO2.png)

*Implementasi Python:*

```{code-cell}
:tags: [hide-input]
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

CSV_PATH = "ekstraksi_fitur_so2.csv"
KOLOM_IDENTITAS = ['id', 'nama', 'daerah']
K = 3
N_KOMPONEN_PCA = 37

df = pd.read_csv(CSV_PATH)
fitur = df.drop(KOLOM_IDENTITAS, axis=1)

X_scaled = StandardScaler().fit_transform(fitur)
X_pca = PCA(n_components=N_KOMPONEN_PCA, random_state=42).fit_transform(X_scaled)

print(f"Reduksi dimensi: {fitur.shape[1]} fitur → {N_KOMPONEN_PCA} komponen PCA")

kmeans = KMeans(n_clusters=K, random_state=42, n_init=10)
df['cluster'] = kmeans.fit_predict(X_pca)
df['cluster_label'] = 'cluster_' + df['cluster'].astype(str)

print(f"Inertia: {kmeans.inertia_:.4f}")
print("\nJumlah data per cluster:")
print(df['cluster_label'].value_counts().sort_index())
print("\nDetail daerah per cluster:")
for c in sorted(df['cluster'].unique()):
    daerah = df[df['cluster'] == c]['daerah'].tolist()
    print(f"  cluster_{c} ({len(daerah)} daerah): {daerah}")

label_cluster = [f"cluster_{i}" for i in range(K)]
y = df['cluster']
x = range(len(df))

plt.figure(figsize=(16, 5))
colors = ['#6b8bd6', '#e07b5a', '#5ab87e']
scatter_colors = [colors[c] for c in y]
plt.scatter(x, y, s=60, c=scatter_colors)
plt.xticks(x, df['daerah'], rotation=90, fontsize=7)
plt.yticks(range(K), label_cluster)
plt.ylim(-0.5, K - 0.5)
plt.title("Scatter Plot K-Means SO2 Dengan PCA (K=3, n_components=37)", loc="left", fontweight="bold")
plt.xlabel("Daerah")
plt.ylabel("Cluster")
plt.grid(True, color="#eeeeee")
plt.tight_layout()
plt.show()
```

### Perbandingan dan Interpretasi SO2

Clustering SO2 juga menghasilkan hasil yang **identik** antara skenario non-PCA dan PCA (inertia 691.6448). Distribusi klasternya membentuk pola yang jauh lebih ekstrem dibanding NO2:

- **Cluster 0 (35 daerah)** — hampir seluruh daerah dalam dataset masuk ke satu kelompok besar. Fluktuasi SO2 di sebagian besar wilayah memiliki profil deret waktu yang sangat seragam. Daerah mulai dari Kerek Tuban, Cerme Gresik, Asemrowo Surabaya, hingga Kwanyar Bangkalan semuanya berbagi pola yang sama.

- **Cluster 1 (1 daerah)** — **Kamal, Banyuajuh** kembali terisolasi, konsisten dengan temuan pada NO2. Lokasi ini menjadi anomali pada dua polutan sekaligus, yang memperkuat dugaan adanya sumber emisi khusus di kawasan tersebut.

- **Cluster 2 (1 daerah)** — **Kamal, Bangkalan** berdiri sendiri di klaster tersendiri. Dua titik observasi di sekitar wilayah Kamal (Banyuajuh dan Bangkalan) keduanya memisahkan diri dari massa utama, meski keduanya tidak saling berkelompok. Area Kamal secara keseluruhan menunjukkan dinamika SO2 yang berbeda dari wilayah lain dalam dataset.

---

## Polutan CO

### Tanpa PCA

*Scatter Plot KNIME (CO — Tanpa PCA):*

![Scatter Plot K-Means CO Tanpa PCA](/assets/NONPCAScatterPlotCO.png)

*Implementasi Python:*

```{code-cell}
:tags: [hide-input]
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

CSV_PATH = "ekstraksi_fitur_co.csv"
KOLOM_IDENTITAS = ['id', 'nama', 'daerah']
K = 3

df = pd.read_csv(CSV_PATH)
fitur = df.drop(KOLOM_IDENTITAS, axis=1)

X = StandardScaler().fit_transform(fitur)

kmeans = KMeans(n_clusters=K, random_state=42, n_init=10)
df['cluster'] = kmeans.fit_predict(X)
df['cluster_label'] = 'cluster_' + df['cluster'].astype(str)

print(f"Inertia: {kmeans.inertia_:.4f}")
print("\nJumlah data per cluster:")
print(df['cluster_label'].value_counts().sort_index())
print("\nDetail daerah per cluster:")
for c in sorted(df['cluster'].unique()):
    daerah = df[df['cluster'] == c]['daerah'].tolist()
    print(f"  cluster_{c} ({len(daerah)} daerah): {daerah}")

label_cluster = [f"cluster_{i}" for i in range(K)]
y = df['cluster']
x = range(len(df))

plt.figure(figsize=(16, 5))
colors = ['#6b8bd6', '#e07b5a', '#5ab87e']
scatter_colors = [colors[c] for c in y]
plt.scatter(x, y, s=60, c=scatter_colors)
plt.xticks(x, df['daerah'], rotation=90, fontsize=7)
plt.yticks(range(K), label_cluster)
plt.ylim(-0.5, K - 0.5)
plt.title("Scatter Plot K-Means CO Tanpa PCA (K=3)", loc="left", fontweight="bold")
plt.xlabel("Daerah")
plt.ylabel("Cluster")
plt.grid(True, color="#eeeeee")
plt.tight_layout()
plt.show()
```

### Dengan PCA

*Scatter Plot KNIME (CO — Dengan PCA):*

![Scatter Plot K-Means CO Dengan PCA](/assets/ScatterPlotCO.png)

*Implementasi Python:*

```{code-cell}
:tags: [hide-input]
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

CSV_PATH = "ekstraksi_fitur_co.csv"
KOLOM_IDENTITAS = ['id', 'nama', 'daerah']
K = 3
N_KOMPONEN_PCA = 37

df = pd.read_csv(CSV_PATH)
fitur = df.drop(KOLOM_IDENTITAS, axis=1)

X_scaled = StandardScaler().fit_transform(fitur)
X_pca = PCA(n_components=N_KOMPONEN_PCA, random_state=42).fit_transform(X_scaled)

print(f"Reduksi dimensi: {fitur.shape[1]} fitur → {N_KOMPONEN_PCA} komponen PCA")

kmeans = KMeans(n_clusters=K, random_state=42, n_init=10)
df['cluster'] = kmeans.fit_predict(X_pca)
df['cluster_label'] = 'cluster_' + df['cluster'].astype(str)

print(f"Inertia: {kmeans.inertia_:.4f}")
print("\nJumlah data per cluster:")
print(df['cluster_label'].value_counts().sort_index())
print("\nDetail daerah per cluster:")
for c in sorted(df['cluster'].unique()):
    daerah = df[df['cluster'] == c]['daerah'].tolist()
    print(f"  cluster_{c} ({len(daerah)} daerah): {daerah}")

label_cluster = [f"cluster_{i}" for i in range(K)]
y = df['cluster']
x = range(len(df))

plt.figure(figsize=(16, 5))
colors = ['#6b8bd6', '#e07b5a', '#5ab87e']
scatter_colors = [colors[c] for c in y]
plt.scatter(x, y, s=60, c=scatter_colors)
plt.xticks(x, df['daerah'], rotation=90, fontsize=7)
plt.yticks(range(K), label_cluster)
plt.ylim(-0.5, K - 0.5)
plt.title("Scatter Plot K-Means CO Dengan PCA (K=3, n_components=37)", loc="left", fontweight="bold")
plt.xlabel("Daerah")
plt.ylabel("Cluster")
plt.grid(True, color="#eeeeee")
plt.tight_layout()
plt.show()
```

### Perbandingan dan Interpretasi CO

Clustering CO menghasilkan distribusi yang **identik** antara non-PCA dan PCA (inertia 660.2141). Pola yang terbentuk serupa dengan SO2:

- **Cluster 1 (35 daerah)** — mayoritas besar daerah masuk ke satu kelompok dominan. Karakteristik deret waktu CO di daerah-daerah ini sangat homogen: Kerek Tuban, Cerme Gresik, Asemrowo Surabaya, Widodaren Ngawi, dan puluhan daerah lainnya menunjukkan fluktuasi CO dalam kisaran yang sebanding.

- **Cluster 0 (1 daerah)** — **Kamal, Bangkalan** berdiri sendiri. Ada aktivitas emisi CO yang terjadi di daerah ini dan tidak ditemukan di daerah manapun dalam dataset.

- **Cluster 2 (1 daerah)** — **Kamal, Banyuajuh** kembali muncul sebagai anomali tersendiri. Konsistensinya sebagai outlier di ketiga polutan (NO2, SO2, CO) menjadikan titik ini sebagai lokasi observasi paling unik dalam keseluruhan dataset.

---

## Kesimpulan

Dari seluruh eksperimen clustering K-Means dengan K=3 pada tiga polutan, tiga poin utama yang dapat ditarik:

**PCA tidak mengubah hasil clustering.** Di ketiga polutan, nilai inertia dan distribusi daerah ke klaster identik antara skenario non-PCA dan PCA. Ini terjadi karena 37 komponen PCA yang dipilih sudah merepresentasikan hampir seluruh varians dari 68 fitur asli. Meski hasilnya sama, PCA tetap bermanfaat karena mereduksi beban komputasi dan menghilangkan fitur-fitur yang berkorelasi tinggi — keuntungan yang lebih terasa signifikan bila dataset lebih besar.

**Kamal, Banyuajuh adalah anomali konsisten.** Titik observasi ini terisolasi di klaster tersendiri pada ketiga polutan. Tidak ada daerah lain dalam dataset yang menunjukkan pola serupa, baik untuk NO2, SO2, maupun CO. Ini sinyal kuat bahwa ada karakteristik emisi yang sangat spesifik di lokasi tersebut yang layak ditelusuri lebih lanjut.

**Pola polusi SO2 dan CO lebih seragam dibanding NO2.** Pada SO2 dan CO, satu klaster mendominasi dengan 35 dari 37 daerah. NO2 terbagi lebih merata menjadi 20 dan 16 daerah. Variasi karakteristik deret waktu NO2 antar daerah lebih tinggi — daerah-daerah memiliki profil NO2 yang lebih beragam dibanding dua polutan lainnya.