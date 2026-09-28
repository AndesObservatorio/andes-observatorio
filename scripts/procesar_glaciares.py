"""
Convierte los Shapefiles del RGI a GeoJSON para el dashboard.

Entrada: /home/asusan/OGGM/rgi/RGIV62/{16,17}_rgi62_*/*.shp
Salida:  assets/geojson/glaciares_andinos.json
"""
import geopandas as gpd
import json
from datetime import datetime

RGI_DIR = '/home/asusan/OGGM/rgi/RGIV62'
OUTPUT_PATH = 'assets/geojson/glaciares_andinos.json'

REGIONES = [
    ('16', 'Low Latitudes (Colombia, Ecuador, Perú, Bolivia)'),
    ('17', 'Southern Andes (Chile, Argentina)'),
]

# Mapeo de nombres de región
NOMBRES_REGION = {
    '01': 'Alaska',
    '16': 'Low Latitudes',
    '17': 'Southern Andes',
}

gdfs = []
for code, nombre in REGIONES:
    import glob
    shp_files = glob.glob(f'{RGI_DIR}/{code}_rgi62_*/{code}_rgi62_*.shp')
    if not shp_files:
        print(f"⚠️ No se encontró Shapefile para región {code}")
        continue
    shp_path = shp_files[0]
    print(f"📍 Cargando {nombre}...")
    print(f"   {shp_path}")
    gdf = gpd.read_file(shp_path)
    print(f"   → {len(gdf)} glaciares")
    print(f"   → CRS: {gdf.crs}")
    # Reproyectar a WGS84 (lat/lon) si es necesario
    if gdf.crs and gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(epsg=4326)
    gdfs.append(gdf)

if not gdfs:
    print("❌ No se cargaron datos")
    exit(1)

import pandas as pd
gdf_all = pd.concat(gdfs, ignore_index=True)
print(f"\n✅ Total glaciares cargados: {len(gdf_all)}")

# Ver columnas disponibles
print(f"\nColumnas disponibles:")
for col in gdf_all.columns:
    print(f"  - {col}")

# Simplificar geometrías para reducir tamaño
print("\n🔧 Simplificando geometrías...")
gdf_all['geometry'] = gdf_all['geometry'].simplify(tolerance=0.005, preserve_topology=True)

# Convertir a GeoJSON con campos seleccionados
features = []
for idx, row in gdf_all.iterrows():
    # Calcular centroide para el marcador
    centroid = row.geometry.centroid
    
    props = {
        'rgi_id': row.get('RGIId', ''),
        'nombre': row.get('Name', '') or '',
        'region': row.get('Region', ''),
        'area_km2': float(row.get('Area', 0)) if row.get('Area') else None,
        'elev_min_m': float(row.get('Zmin', 0)) if row.get('Zmin') else None,
        'elev_max_m': float(row.get('Zmax', 0)) if row.get('Zmax') else None,
        'lat': float(centroid.y),
        'lon': float(centroid.x),
        'pais': '',  # Se puede mapear después
    }
    # Asignar país según longitud/latitud
    if props['lat'] > 0:
        props['pais'] = 'Colombia'
    elif props['lat'] > -5:
        props['pais'] = 'Ecuador'
    elif props['lat'] > -18 and props['lon'] > -75:
        props['pais'] = 'Perú'
    elif props['lat'] > -23 and props['lon'] < -65:
        props['pais'] = 'Bolivia'
    elif props['lat'] > -40:
        props['pais'] = 'Chile/Argentina'
    else:
        props['pais'] = 'Argentina/Chile'
    
    features.append({
        'type': 'Feature',
        'properties': props,
        'geometry': json.loads(gpd.GeoSeries([row.geometry]).to_json())['features'][0]['geometry']
    })

output = {
    'type': 'FeatureCollection',
    'fuente': 'Randolph Glacier Inventory 6.2 (RGI)',
    'generado': datetime.now().strftime('%Y-%m-%d'),
    'total': len(features),
    'features': features
}

with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False)

print(f"\n✅ {OUTPUT_PATH} generado")
print(f"   Total glaciares: {len(features)}")
