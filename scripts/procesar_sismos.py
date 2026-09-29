"""
Procesa el catálogo sísmico del USGS:
- Filtra M >= 4.5 (para reducir tamaño)
- Simplifica campos
- Convierte fecha Unix a ISO
- Genera assets/geojson/sismos_andinos.json
"""
import json
from datetime import datetime

INPUT = 'data/sismos/sismos_sudamerica.geojson'
OUTPUT = 'assets/geojson/sismos_andinos.json'

MAGNITUD_MINIMA = 4.5

print(f"📥 Cargando {INPUT}...")
with open(INPUT, 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"   Total original: {len(data['features'])} sismos")

# ═══ FILTRAR Y SIMPLIFICAR ═══
features_simplificados = []
for feat in data['features']:
    props = feat['properties']
    mag = props.get('mag', 0)
    
    # Filtrar por magnitud
    if mag < MAGNITUD_MINIMA:
        continue
    
    coords = feat['geometry']['coordinates']
    lon, lat, depth = coords[0], coords[1], coords[2] if len(coords) > 2 else 0
    
    # Convertir timestamp Unix (ms) a ISO
    time_ms = props.get('time', 0)
    fecha_iso = datetime.utcfromtimestamp(time_ms / 1000).strftime('%Y-%m-%d')
    
    features_simplificados.append({
        'type': 'Feature',
        'properties': {
            'mag': round(mag, 1),
            'lugar': props.get('place', 'N/A'),
            'fecha': fecha_iso,
            'prof_km': round(depth, 1) if depth else 0,
            'url': props.get('url', '')
        },
        'geometry': {
            'type': 'Point',
            'coordinates': [round(lon, 4), round(lat, 4)]
        }
    })

print(f"   Filtrados (M≥{MAGNITUD_MINIMA}): {len(features_simplificados)} sismos")

# Ordenar por magnitud descendente
features_simplificados.sort(key=lambda s: s['properties']['mag'], reverse=True)

# Estadísticas
mags = [s['properties']['mag'] for s in features_simplificados]
por_ano = {}
for s in features_simplificados:
    ano = s['properties']['fecha'][:4]
    por_ano[ano] = por_ano.get(ano, 0) + 1

output = {
    'type': 'FeatureCollection',
    'fuente': 'USGS Earthquake Catalog',
    'generado': datetime.now().strftime('%Y-%m-%d'),
    'criterio': f'M ≥ {MAGNITUD_MINIMA} · 2015-2025 · Sudamérica',
    'total': len(features_simplificados),
    'stats': {
        'mag_min': min(mags),
        'mag_max': max(mags),
        'por_ano': por_ano
    },
    'features': features_simplificados
}

with open(OUTPUT, 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False)

import os
tamano_mb = os.path.getsize(OUTPUT) / 1024 / 1024

print(f"\n✅ {OUTPUT}")
print(f"   Total: {len(features_simplificados)} sismos")
print(f"   Tamaño: {tamano_mb:.2f} MB")
print(f"   Magnitud: {min(mags)} - {max(mags)}")
print(f"\n📊 Sismos por año:")
for ano, n in sorted(por_ano.items()):
    print(f"   {ano}: {n}")
