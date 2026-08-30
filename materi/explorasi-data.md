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

# Eksplorasi Data

Eksplorasi data adalah proses memahami karakteristik dataset sebelum masuk ke tahap pemodelan. Pada tahap ini diperiksa struktur data, distribusi nilai, keberadaan missing value, anomali, dan pola tersembunyi yang memberi konteks lebih dalam terhadap kondisi kualitas udara wilayah Kamal-UTM.

---

## Instalasi & Import Library

```{code-cell} ipython3
!pip install pandas matplotlib seaborn -q
```

```{code-cell} ipython3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns

print(f"pandas     : {pd.__version__}")
print(f"matplotlib : {plt.matplotlib.__version__}")
print(f"seaborn    : {sns.__version__}")
```

---

## Load Data

```{code-cell} ipython3
df_no2 = pd.read_csv("NO2_KAMAL-UTM.csv")
df_co  = pd.read_csv("CO_KAMAL-UTM.csv")
df_so2 = pd.read_csv("SO2_KAMAL-UTM.csv")

for df_pol, name in [(df_no2, "NO2"), (df_co, "CO"), (df_so2, "SO2")]:
    df_pol["date"] = pd.to_datetime(df_pol["date"])
    df_pol.drop(columns=["feature_index"], inplace=True)
    df_pol.sort_values("date", inplace=True)
    df_pol.reset_index(drop=True, inplace=True)

df = df_no2.merge(df_co, on="date", how="outer").merge(df_so2, on="date", how="outer")
df.sort_values("date", inplace=True)
df.reset_index(drop=True, inplace=True)

print(f"Total baris : {len(df)}")
print(f"Periode     : {df['date'].min().date()} s/d {df['date'].max().date()}")
```

---

## 1. Struktur dan Tipe Data

Pemeriksaan struktur data memastikan setiap kolom terbaca dengan tipe yang benar sebelum analisis lebih lanjut dilakukan.

```{code-cell} ipython3
print("=== Shape ===")
print(f"Baris : {df.shape[0]}")
print(f"Kolom : {df.shape[1]}")
print()
print("=== Kolom & Tipe Data ===")
print(df.dtypes)
```

```{code-cell} ipython3
print("=== Preview 10 Baris Pertama ===")
df.head(10)
```

```{code-cell} ipython3
print("=== Preview 10 Baris Terakhir ===")
df.tail(10)
```

```{code-cell} ipython3
df.info()
```

---

## 2. Analisis Statistik Deskriptif

Statistik deskriptif memberikan gambaran ringkas distribusi nilai setiap polutan. Perbedaan besar antara mean dan median mengindikasikan distribusi yang miring atau adanya outlier yang menarik nilai rata-rata ke satu arah.

```{code-cell} ipython3
df[["NO2", "CO", "SO2"]].describe().T
```

```{code-cell} ipython3
print("=== Mean vs Median ===")
for col in ["NO2", "CO", "SO2"]:
    mean   = df[col].mean()
    median = df[col].median()
    selisih = abs(mean - median)
    arah = "mean > median (right-skewed)" if mean > median else "mean < median (left-skewed)"
    print(f"{col:4s}  mean: {mean:.6f}  median: {median:.6f}  selisih: {selisih:.6f}  -> {arah}")
```

```{code-cell} ipython3
fig, axes = plt.subplots(1, 3, figsize=(15, 4))

for ax, col, color in zip(axes, ["NO2", "CO", "SO2"], ["#2980b9", "#27ae60", "#e67e22"]):
    data = df[col].dropna()
    ax.hist(data, bins=30, color=color, edgecolor='white', alpha=0.85)
    ax.axvline(data.mean(),   color='red',   linestyle='--', linewidth=1.2, label='Mean')
    ax.axvline(data.median(), color='black', linestyle=':',  linewidth=1.2, label='Median')
    ax.set_title(f"Distribusi {col}")
    ax.set_xlabel("mol/m²")
    ax.set_ylabel("Frekuensi")
    ax.legend(fontsize=8)

plt.suptitle("Distribusi Nilai Polutan — Kamal UTM (Agu 2025 – Agu 2026)", y=1.02)
plt.tight_layout()
plt.show()
```

---

## 3. Missing Values

Missing value pada data Sentinel-5P bukan berarti sensor rusak, melainkan karena tutupan awan tebal atau gap orbit satelit. Yang menarik adalah apakah ketiga polutan missing di hari yang sama — ini menunjukkan penyebabnya adalah kondisi atmosfer (awan), bukan masalah spesifik satu instrumen.

```{code-cell} ipython3
print("=== Jumlah Missing Value ===")
total = len(df)
for col in ["NO2", "CO", "SO2"]:
    jumlah = df[col].isnull().sum()
    persen = jumlah / total * 100
    print(f"{col:4s}  {jumlah:3d} hari missing  ({persen:.1f}% dari {total} hari)")

print()
semua_missing  = df[["NO2","CO","SO2"]].isnull().all(axis=1).sum()
ada_semua      = (~df[["NO2","CO","SO2"]].isnull().any(axis=1)).sum()
print(f"Hari semua polutan missing sekaligus : {semua_missing} hari")
print(f"Hari ketiga polutan lengkap          : {ada_semua} hari")
```

```{code-cell} ipython3
# Missing per bulan
df["bulan"] = df["date"].dt.to_period("M")

fig, axes = plt.subplots(3, 1, figsize=(14, 8), sharex=True)

for ax, col, color in zip(axes, ["NO2", "CO", "SO2"], ["#2980b9", "#27ae60", "#e67e22"]):
    miss = df.groupby("bulan")[col].apply(lambda x: x.isnull().sum())
    ax.bar(miss.index.astype(str), miss.values, color=color, alpha=0.8)
    ax.set_ylabel(f"Missing\n{col}")
    ax.set_ylim(0, 35)
    for i, v in enumerate(miss.values):
        if v > 0:
            ax.text(i, v + 0.3, str(v), ha='center', fontsize=7)

plt.xticks(rotation=45, ha='right')
plt.suptitle("Jumlah Missing Value per Bulan", y=1.01)
plt.tight_layout()
plt.show()

df.drop(columns=["bulan"], inplace=True)
```

```{code-cell} ipython3
# Timeline missing value
fig, axes = plt.subplots(3, 1, figsize=(14, 5), sharex=True)

for ax, col, color in zip(axes, ["NO2", "CO", "SO2"], ["#2980b9", "#27ae60", "#e67e22"]):
    missing = df[col].isnull()
    ax.scatter(df.loc[missing,  "date"], [col] * missing.sum(),
               color='red', s=8, alpha=0.6, label='Missing')
    ax.scatter(df.loc[~missing, "date"], [col] * (~missing).sum(),
               color=color, s=4, alpha=0.3, label='Ada data')
    ax.set_yticks([col])
    ax.legend(fontsize=7, loc='upper right')

plt.suptitle("Posisi Missing Value pada Timeline", y=1.01)
plt.tight_layout()
plt.show()
```

---

## 4. Deteksi Outlier

Outlier dideteksi dengan metode IQR. Perhatian khusus diberikan pada **nilai negatif** — secara fisik konsentrasi gas atmosfer tidak mungkin negatif, sehingga nilai ini merupakan noise pengukuran satelit yang perlu ditangani sebelum pemodelan.

```{code-cell} ipython3
print("=== Deteksi Outlier (Metode IQR) ===\n")

for col in ["NO2", "CO", "SO2"]:
    data  = df[col].dropna()
    Q1    = data.quantile(0.25)
    Q3    = data.quantile(0.75)
    IQR   = Q3 - Q1
    lower = Q1 - 1.5 * IQR
    upper = Q3 + 1.5 * IQR

    out_bawah = data[data < lower]
    out_atas  = data[data > upper]
    negatif   = data[data < 0]

    print(f"--- {col} ---")
    print(f"  Batas bawah IQR : {lower:.6f}")
    print(f"  Batas atas IQR  : {upper:.6f}")
    print(f"  Outlier bawah   : {len(out_bawah)} data")
    print(f"  Outlier atas    : {len(out_atas)} data")
    print(f"  Nilai negatif   : {len(negatif)} data")
    print()
```

```{code-cell} ipython3
fig, axes = plt.subplots(1, 3, figsize=(14, 5))

for ax, col, color in zip(axes, ["NO2", "CO", "SO2"], ["#2980b9", "#27ae60", "#e67e22"]):
    data = df[col].dropna()
    ax.boxplot(data, patch_artist=True,
               boxprops=dict(facecolor=color, alpha=0.6),
               medianprops=dict(color='black', linewidth=2),
               flierprops=dict(marker='o', markersize=4, color='red', alpha=0.5))
    ax.set_title(f"Boxplot {col}")
    ax.set_ylabel("mol/m²")
    ax.set_xticks([])

plt.suptitle("Deteksi Outlier — Boxplot IQR", y=1.01)
plt.tight_layout()
plt.show()
```

```{code-cell} ipython3
print("=== Baris dengan Nilai Negatif ===")
for col in ["NO2", "CO", "SO2"]:
    neg = df[df[col] < 0][["date", col]]
    if len(neg) > 0:
        print(f"\n{col} ({len(neg)} baris):")
        print(neg.to_string(index=False))
    else:
        print(f"\n{col}: tidak ada nilai negatif")
```

```{code-cell} ipython3
print("=== Nilai Maksimum (Puncak Polutan) ===")
for col in ["NO2", "CO", "SO2"]:
    idx = df[col].idxmax()
    print(f"{col}  max: {df.loc[idx, col]:.6f}  pada: {df.loc[idx, 'date'].date()}")
```

---

## 5. Analisis Pola Musiman

Wilayah Kamal-UTM berada di iklim tropis dengan dua musim utama: kemarau (April–Oktober) dan hujan (November–Maret). Pola musiman polutan penting untuk dipahami karena curah hujan, angin, dan suhu memengaruhi konsentrasi gas atmosfer secara signifikan.

```{code-cell} ipython3
df["month"]  = df["date"].dt.month
df["musim"]  = df["month"].apply(
    lambda m: "Kemarau (Apr-Oct)" if 4 <= m <= 10 else "Hujan (Nov-Mar)"
)

print("=== Rata-rata per Musim ===")
print(df.groupby("musim")[["NO2","CO","SO2"]].mean().to_string())
```

```{code-cell} ipython3
# Rata-rata per bulan — heatmap
bulan_label = ["Jan","Feb","Mar","Apr","Mei","Jun","Jul","Agu","Sep","Okt","Nov","Des"]
bulanan = df.groupby("month")[["NO2","CO","SO2"]].mean()
bulanan.index = bulan_label

fig, ax = plt.subplots(figsize=(12, 3))
sns.heatmap(bulanan.T, annot=True, fmt=".5f", cmap="YlOrRd",
            linewidths=0.5, ax=ax, annot_kws={"size": 8})
ax.set_title("Rata-rata Bulanan Polutan (mol/m²)")
ax.set_xlabel("Bulan")
plt.tight_layout()
plt.show()
```

```{code-cell} ipython3
# Boxplot per bulan per polutan
fig, axes = plt.subplots(3, 1, figsize=(14, 10), sharex=True)

for ax, col, color in zip(axes, ["NO2", "CO", "SO2"], ["#2980b9", "#27ae60", "#e67e22"]):
    data_per_bulan = [df[df["month"] == m][col].dropna().values for m in range(1, 13)]
    bp = ax.boxplot(data_per_bulan, patch_artist=True,
                    boxprops=dict(facecolor=color, alpha=0.5),
                    medianprops=dict(color='black', linewidth=1.5),
                    flierprops=dict(marker='o', markersize=3, alpha=0.4))
    ax.set_ylabel(f"{col} (mol/m²)")
    ax.set_xticks(range(1, 13))
    ax.set_xticklabels(bulan_label)
    ax.grid(True, axis='y', alpha=0.3)

plt.suptitle("Distribusi Polutan per Bulan — Kamal UTM", y=1.01)
plt.tight_layout()
plt.show()

df.drop(columns=["month", "musim"], inplace=True)
```

---

## 6. Analisis Tren (Rolling Average)

Rolling average 30 hari memperhalus fluktuasi harian sehingga tren jangka panjang lebih terlihat. Tren ini menunjukkan apakah konsentrasi polutan di wilayah Kamal-UTM secara umum meningkat, menurun, atau stabil selama periode pengamatan.

```{code-cell} ipython3
fig, axes = plt.subplots(3, 1, figsize=(15, 10), sharex=True)

for ax, col, color in zip(axes, ["NO2", "CO", "SO2"], ["#2980b9", "#27ae60", "#e67e22"]):
    d = df[["date", col]].dropna().set_index("date")
    roll = d[col].rolling("30D").mean()

    ax.plot(d.index, d[col], color=color, linewidth=0.6, alpha=0.4, label='Harian')
    ax.plot(roll.index, roll.values, color=color, linewidth=2.0, alpha=0.95, label='Rolling 30 hari')
    ax.fill_between(d.index, d[col], alpha=0.08, color=color)
    ax.set_ylabel(f"{col} (mol/m²)")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    ax.xaxis.set_major_locator(mdates.MonthLocator())

    # Anotasi tren
    awal  = roll.dropna().iloc[0]
    akhir = roll.dropna().iloc[-1]
    delta = akhir - awal
    arah  = "naik" if delta > 0 else "turun"
    ax.set_title(f"{col} — tren {arah} ({delta:+.6f} mol/m² selama periode)", fontsize=9)

plt.xticks(rotation=45, ha='right')
plt.suptitle("Tren Polutan (Rolling Average 30 Hari) — Kamal UTM", fontsize=12, y=1.01)
plt.tight_layout()
plt.show()
```

---

## 7. Korelasi Antar Polutan

Korelasi antar polutan menunjukkan apakah sumber emisi atau kondisi atmosfer yang memengaruhinya cenderung sama. Korelasi positif kuat antara dua polutan mengindikasikan kemungkinan sumber emisi yang sama, misalnya pembakaran bahan bakar yang menghasilkan sekaligus NO2 dan CO.

```{code-cell} ipython3
fig, ax = plt.subplots(figsize=(6, 5))

corr = df[["NO2", "CO", "SO2"]].corr()
sns.heatmap(corr, annot=True, fmt=".3f", cmap="coolwarm",
            center=0, ax=ax, linewidths=0.5, annot_kws={"size": 13})
ax.set_title("Matriks Korelasi Antar Polutan")
plt.tight_layout()
plt.show()

print("\nNilai korelasi:")
print(corr.to_string())
```

```{code-cell} ipython3
# Scatter plot antar polutan
fig, axes = plt.subplots(1, 3, figsize=(15, 4))

pairs = [("NO2", "CO"), ("NO2", "SO2"), ("CO", "SO2")]
colors_pair = ["#8e44ad", "#c0392b", "#16a085"]

for ax, (x, y), color in zip(axes, pairs, colors_pair):
    d = df[[x, y]].dropna()
    ax.scatter(d[x], d[y], color=color, alpha=0.4, s=15)
    # Garis regresi
    z = np.polyfit(d[x], d[y], 1)
    p = np.poly1d(z)
    xline = np.linspace(d[x].min(), d[x].max(), 100)
    ax.plot(xline, p(xline), color='black', linewidth=1.2, linestyle='--')
    ax.set_xlabel(f"{x} (mol/m²)")
    ax.set_ylabel(f"{y} (mol/m²)")
    ax.set_title(f"{x} vs {y}")
    ax.grid(True, alpha=0.3)

plt.suptitle("Scatter Plot Korelasi Antar Polutan", y=1.02)
plt.tight_layout()
plt.show()
```

---

## 8. Visualisasi Time Series Lengkap

```{code-cell} ipython3
fig, axes = plt.subplots(3, 1, figsize=(15, 10), sharex=True)

for ax, col, color in zip(axes, ["NO2", "CO", "SO2"], ["#2980b9", "#27ae60", "#e67e22"]):
    data_valid = df[df[col].notna()]
    ax.plot(data_valid["date"], data_valid[col],
            color=color, linewidth=0.9, alpha=0.8)
    ax.fill_between(data_valid["date"], data_valid[col], alpha=0.15, color=color)

    mean_val = data_valid[col].mean()
    ax.axhline(mean_val, color='red', linestyle='--',
               linewidth=0.8, alpha=0.7, label=f'Mean: {mean_val:.5f}')

    neg = df[df[col] < 0]
    if len(neg) > 0:
        ax.scatter(neg["date"], neg[col],
                   color='black', s=25, zorder=5, label=f'Nilai negatif ({len(neg)})')

    ax.set_ylabel(f"{col} (mol/m²)", fontsize=10)
    ax.legend(fontsize=8, loc='upper right')
    ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    ax.xaxis.set_major_locator(mdates.MonthLocator())

plt.xticks(rotation=45, ha='right')
plt.suptitle("Time Series Polutan Udara — Kamal UTM (Agu 2025 – Agu 2026)",
             fontsize=13, y=1.01)
plt.tight_layout()
plt.show()
```

```{code-cell} ipython3
# Rata-rata bulanan bar chart
df["bulan"] = df["date"].dt.to_period("M")
fig, axes = plt.subplots(3, 1, figsize=(14, 9), sharex=True)

for ax, col, color in zip(axes, ["NO2", "CO", "SO2"], ["#2980b9", "#27ae60", "#e67e22"]):
    bulanan = df.groupby("bulan")[col].mean()
    ax.bar(bulanan.index.astype(str), bulanan.values,
           color=color, alpha=0.8, edgecolor='white')
    ax.set_ylabel(f"{col} (mol/m²)", fontsize=9)
    ax.grid(True, axis='y', alpha=0.3)
    for i, v in enumerate(bulanan.values):
        if not pd.isna(v):
            ax.text(i, v, f"{v:.5f}", ha='center', va='bottom', fontsize=6)

plt.xticks(rotation=45, ha='right')
plt.suptitle("Rata-rata Bulanan Polutan — Kamal UTM", fontsize=12, y=1.01)
plt.tight_layout()
plt.show()

df.drop(columns=["bulan"], inplace=True)
```
