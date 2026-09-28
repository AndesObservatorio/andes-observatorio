"""
Filtra glaciares que están CERCA de volcanes activos.

Criterio: distancia < 10 km al volcán más cercano.

Salida: assets/geojson/glaciares_volcanes.json
"""
import geopandas as gpd
import json
import glob
from datetime import datetime
import pandas as pd
from shapely.geometry import Point

RGI_DIR = '/home/asusan/OGGM/rgi/RGIV62'
VOLCANES_PATH = 'assets/geojson/volcanes_andinos.json'
OUTPUT_PATH = 'assets/geojson/glaciares_volcanes.json'

DISTANCIA_MAXIMA_KM = 10  # km

# ═══ 1. CARGAR VOLCANES ═══
print("📍 Cargando volcanes...")
with open(VOLCANES_PATH, 'r', encoding='utf-8') as f:
    volcanes_data = json.load(f)

volcanes = []
for v in volcanes_data['features']:
    lon, lat = v['geometry']['coordinates']
    volcanes.append({
        'nombre': v['properties']['nombre'],
        'pais': v['properties']['pais'],
        'lat': lat,
        'lon': lon,
        'elev_m': v['properties'].get('elevacion_m'),
        'tipo': v['properties'].get('tipo'),
        'ultima_erupcion': v['properties'].get('ultima_erupcion'),
    })
print(f"   {len(volcanes)} volcanes cargados")

# GeoDataFrame de volcanes
gdf_vol = gpd.GeoDataFrame(
    volcanes,
    geometry=[Point(v['lon'], v['lat']) for v in volcanes],
    crs='EPSG:4326'
)

# ═══ 2. CARGAR GLACIARES ═══
print("\n📍 Cargando glaciares...")
gdfs = []
for code in ['16', '17']:
    shp_files = glob.glob(f'{RGI_DIR}/{code}_rgi62_*/{code}_rgi62_*.shp')
    if shp_files:
        gdf = gpd.read_file(shp_files[0])
        if gdf.crs and gdf.crs.to_epsg() != 4326:
            gdf = gdf.to_crs(epsg=4326)
        gdfs.append(gdf)

gdf_glac = pd.concat(gdfs, ignore_index=True)
print(f"   {len(gdf_glac)} glaciares cargados")

# ═══ 3. CALCULAR DISTANCIA A VOLCÁN MÁS CERCANO ═══
print(f"\n🔍 Buscando glaciares a menos de {DISTANCIA_MAXIMA_KM} km de un volcán...")

# Reproyectar a UTM para cálculo de distancia en metros
gdf_glac_proj = gdf_glac.to_crs(epsg=3857)  # Web Mercator (metros aproximados)
gdf_vol_proj = gdf_vol.to_crs(epsg=3857)

# Para cada glaciar, encontrar el volcán más cercano
glaciares_cerca = []
for idx, glaciar in gdf_glac_proj.iterrows():
    centroide = glaciar.geometry.centroid
    distancias = gdf_vol_proj.geometry.distance(centroide)
    dist_min = distancias.min()
    vol_idx = distancias.idxmin()
    dist_km = dist_min / 1000
    
    if dist_km <= DISTANCIA_MAXIMA_KM:
        vol = volcanes[vol_idx]
        glaciares_cerca.append({
            'rgi_id': glaciar.get('RGIId', ''),
            'nombre': glaciar.get('Name', '') or f"RGI {glaciar.get('RGIId', '')}",
            'area_km2': float(glaciar.get('Area', 0)),
            'elev_min_m': float(glaciar.get('Zmin', 0)) if glaciar.get('Zmin') else None,
            'elev_max_m': float(glaciar.get('Zmax', 0)) if glaciar.get('Zmax') else None,
            'lat': round(gdf_glac.loc[idx, 'geometry'].centroid.y, 4),
            'lon': round(gdf_glac.loc[idx, 'geometry'].centroid.x, 4),
            'volcan_nombre': vol['nombre'],
            'volcan_pais': vol['pais'],
            'volcan_lat': vol['lat'],
            'volcan_lon': vol['lon'],
            'volcan_elev_m': vol['elev_m'],
            'volcan_tipo': vol['tipo'],
            'volcan_ultima_erupcion': vol['ultima_erupcion'],
            'distancia_km': round(dist_km, 2),
            'geometry': glaciar.geometry  # Guardar geometría proyectada
        })

print(f"   ✅ {len(glaciares_cerca)} glaciares cerca de volcanes")

# ═══ 4. CREAR GEOJSON ═══
features = []
for g in glaciares_cerca:
    # Reproyectar geometría a WGS84
    geom = gpd.GeoSeries([g['geometry']], crs='EPSG:3857').to_crs(epsg=4326).iloc[0]
    
    props = {k: v for k, v in g.items() if k != 'geometry'}
    
    geom_json = json.loads(gpd.GeoSeries([geom]).to_json())['features'][0]['geometry']
    
    features.append({
        'type': 'Feature',
        'properties': props,
        'geometry': geom_json
    })

output = {
    'type': 'FeatureCollection',
    'fuente': 'RGI 6.2 + Smithsonian GVP',
    'criterio': f'Glaciares a menos de {DISTANCIA_MAXIMA_KM} km de volcanes activos',
    'generado': datetime.now().strftime('%Y-%m-%d'),
    'total': len(features),
    'features': features
}

with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False)

import os
tamano_mb = os.path.getsize(OUTPUT_PATH) / 1024 / 1024
print(f"\n✅ {OUTPUT_PATH}")
print(f"   Glaciares: {len(features)}")
print(f"   Tamaño: {tamano_mb:.2f} MB")

# Estadísticas por volcán
print(f"\n📊 Glaciares por volcán:")
por_volcan = {}
for g in glaciares_cerca:
    vol = g['volcan_nombre']
    por_volcan[vol] = por_volcan.get(vol, 0) + 1

for vol, n in sorted(por_volcan.items(), key=lambda x: -x[1])[:20]:
    print(f"   {vol}: {n} glaciares")
