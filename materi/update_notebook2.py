import nbformat as nbf

notebook_path = r'c:\Users\ARIEL\OneDrive\Documents\PSD\materi\klasifikasi6kelas.ipynb'

with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = nbf.read(f, as_version=4)

# Fix Cell 4 (Metrik) to always print metrics
nb.cells[3].source = """jumlah_data = len(X)
jumlah_fitur = X.shape[1]

hasil_evaluasi = {
    'Jumlah fitur': jumlah_fitur,
    'Jumlah data piksel berlabel': jumlah_data,
    'Ukuran X': X.shape,
    'Data train': f'{len(X_train)} piksel',
    'Data testing': f'{len(X_test)} piksel',
    'Akurasi uji': f'{akurasi:.4f}',
}

print('| Metrik | Nilai |')
print('| :--- | ---: |')
for metrik, nilai in hasil_evaluasi.items():
    print(f'| {metrik} | {nilai} |')
"""

# Fix Cell 5 (Confusion Matrix Plot) so it runs even if TIF is missing
nb.cells[5].source = """from sklearn.metrics import ConfusionMatrixDisplay
import matplotlib.pyplot as plt
import numpy as np

fig, ax = plt.subplots(1, 2, figsize=(14, 5))
ConfusionMatrixDisplay.from_predictions(
    y_test,
    pred,
    labels=list(classes.values()),
    display_labels=[k.capitalize() for k in classes.keys()],
    cmap='Blues',
    ax=ax[0],
    colorbar=False,
    xticks_rotation=45
)
ax[0].set_title('Confusion Matrix (Petak Uji)')

urut = np.argsort(rf.feature_importances_)
# Kita ambil NAMA_BAND sesuai fitur yang ada
NAMA_BAND = ['B2', 'B3', 'B4', 'B8', 'B11', 'B12', 'NDVI', 'NDWI', 'MNDWI', 'NDBI']
fitur_label = NAMA_BAND[:len(urut)] if len(urut) <= len(NAMA_BAND) else [f'Feature {i}' for i in range(len(urut))]

ax[1].barh(range(len(urut)), rf.feature_importances_[urut], color='#2ecc71', edgecolor='black')
ax[1].set_yticks(range(len(urut)))
ax[1].set_yticklabels([fitur_label[index] for index in urut])
ax[1].set_xlabel('Nilai Kepentingan')
ax[1].set_title('Kepentingan Band dan Indeks (6 Kelas)')
plt.tight_layout()
plt.show()"""

with open(notebook_path, 'w', encoding='utf-8') as f:
    nbf.write(nb, f)
