import json

NB_PATH = r'c:\Users\ARIEL\OneDrive\Documents\PSD\materi\klasifikasijatim.ipynb'

with open(NB_PATH, encoding='utf-8') as f:
    nb = json.load(f)

for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        src = "".join(cell['source'])
        if 'def buat_peta_interaktif' in src:
            # We will just split by 'def buat_peta_interaktif' and replace it entirely!
            
            NEW_FUNC = """def buat_peta_interaktif(gdf_pred, nama_model, judul_peta, nama_file_html):
    \"\"\"
    Membuat peta Folium bergaya "segmentasi" lengkap:
      • Basemap Esri Satellite + Google Hybrid (online)
      • Citra satelit tertanam (offline tile mosaic)
      • Overlay hasil klasifikasi ML pixel-by-pixel (RGBA raster)
      • Titik sampel per kelas
      • Batas AOI & Legenda
    \"\"\"
    # ── Hitung AOI, tapi batasi agar tidak melebih Jawa Timur (tidak masuk ke Bali)
    lon_min = max(gdf_pred.geometry.centroid.x.min() - 0.05, 110.8)
    lon_max = min(gdf_pred.geometry.centroid.x.max() + 0.05, 114.55) # Batas timur Banyuwangi/Bali
    lat_min = max(gdf_pred.geometry.centroid.y.min() - 0.05, -8.8)
    lat_max = min(gdf_pred.geometry.centroid.y.max() + 0.05, -6.6)
    aoi = [lon_min, lat_min, lon_max, lat_max]

    # ── Unduh citra satelit (cached ke file)
    sat_file = "satelit_aoi_z10.jpeg"
    import os
    import io
    from PIL import Image
    import folium
    from folium.raster_layers import ImageOverlay
    
    if os.path.exists(sat_file):
        mosaik = Image.open(sat_file)
        bounds_sat = [[lat_min - 0.2, lon_min - 0.2], [lat_max + 0.2, lon_max + 0.2]]
    else:
        aoi_luas = [lon_min - 0.1, lat_min - 0.1, lon_max + 0.1, lat_max + 0.1]
        mosaik, bounds_sat = ambil_satelit(aoi_luas, z=10)
        mosaik.save(sat_file, quality=85)
    
    sat_bytes = io.BytesIO()
    mosaik.save(sat_bytes, format="JPEG", quality=85)
    sat_b64 = "data:image/jpeg;base64," + __import__("base64").b64encode(sat_bytes.getvalue()).decode()

    # ── Buat raster RGBA klasifikasi Pixel-by-Pixel
    model = model_gnb if nama_model == "gnb" else model_knn
    rgba_img = raster_ke_rgba(mosaik, model, scaler, tinggi=350)
    
    rgba_bytes = io.BytesIO()
    rgba_img.save(rgba_bytes, format="PNG")
    rgba_b64 = "data:image/png;base64," + __import__("base64").b64encode(rgba_bytes.getvalue()).decode()
    
    # ── Inisialisasi peta
    pusat = [(lat_min + lat_max) / 2, (lon_min + lon_max) / 2]
    peta  = folium.Map(location=pusat, zoom_start=8, tiles=None, control_scale=True)

    # Basemap online
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Tiles &copy; Esri", name="Esri Satellite (online)", max_zoom=19, overlay=False, control=True,
    ).add_to(peta)
    folium.TileLayer(
        tiles="https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}",
        attr="Google Hybrid", name="Google Hybrid (dengan label)", max_zoom=20, overlay=False, control=True, show=False,
    ).add_to(peta)

    # Layer satelit tertanam (base64)
    ImageOverlay(image=sat_b64, bounds=bounds_sat, opacity=1.0,
                 name="Satelit (tertanam)", interactive=False, zindex=1).add_to(peta)

    # Layer hasil klasifikasi
    ImageOverlay(image=rgba_b64, bounds=bounds_sat, opacity=0.72,
                 name=f"Hasil Klasifikasi: {judul_peta}",
                 interactive=False, zindex=5).add_to(peta)

    # Titik sampel per kelas (tersembunyi by default)
    for k, v in KELAS.items():
        grup = folium.FeatureGroup(name=f"Sampel: {v['nama']}", show=False)
        sub  = gdf_pred[gdf_pred["kelas"] == v["nama"]]
        for _, row in sub.iterrows():
            folium.CircleMarker(
                location=[row.geometry.centroid.y, row.geometry.centroid.x],
                radius=4, color="white", weight=1,
                fill=True, fill_color=v["warna"], fill_opacity=0.9,
                popup=f"{v['nama']}"
            ).add_to(grup)
        grup.add_to(peta)

    # Kotak batas area studi
    grup_aoi = folium.FeatureGroup(name="Batas area studi")
    folium.Rectangle([[lat_min, lon_min], [lat_max, lon_max]], color="white", weight=1.5, fill=False, dash_array="6").add_to(grup_aoi)
    grup_aoi.add_to(peta)

    # Legenda LULC
    item_html = "".join(f'<div style="margin:2px 0"><span style="display:inline-block;width:14px;height:14px;background:{v["warna"]};border:1px solid #333;margin-right:6px;vertical-align:middle"></span>{v["nama"]}</div>' for v in KELAS.values())
    legenda = f'<div style="position:fixed;bottom:30px;left:30px;z-index:9999;background:rgba(255,255,255,0.92);padding:10px 14px;border:1px solid #888;border-radius:8px;font:13px Arial;box-shadow:2px 2px 6px rgba(0,0,0,.3);"><b>Legenda LULC</b><br>{item_html}</div>'
    peta.get_root().html.add_child(folium.Element(legenda))

    folium.LayerControl(collapsed=False).add_to(peta)
    peta.fit_bounds([[lat_min, lon_min], [lat_max, lon_max]])

    peta.save(nama_file_html)
    print(f"Peta disimpan: {nama_file_html}")
    return peta
"""
            
            # Find the start of the function and the end of the cell
            start_idx = src.find('def buat_peta_interaktif')
            if start_idx != -1:
                # the cell ends with `peta_gnb` calls. Let's find `# ── Tampilkan peta GNB`
                end_idx = src.find('# ── Tampilkan peta GNB')
                if end_idx != -1:
                    new_src = src[:start_idx] + NEW_FUNC + "\n\n" + src[end_idx:]
                    cell['source'] = [new_src]
                    print("Function buat_peta_interaktif completely replaced!")
                else:
                    print("Could not find end of function.")

with open(NB_PATH, 'w', encoding='utf-8') as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

