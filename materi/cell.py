import json, sys

NB_PATH = r'c:\Users\ARIEL\OneDrive\Documents\PSD\materi\klasifikasijatim.ipynb'

with open(NB_PATH, encoding='utf-8') as f:
    nb = json.load(f)

# Print semua code cells (first 300 chars each)
for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code':
        src = ''.join(cell['source'])
        snippet = src[:300].encode('ascii', 'ignore').decode()
        sys.stdout.buffer.write(f"=== Cell {i} ===\n{snippet}\n".encode('utf-8', errors='replace'))


