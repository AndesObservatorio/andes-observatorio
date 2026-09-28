"""
Filtra volcanes andinos del CSV de Smithsonian GVP y genera GeoJSON.

Entrada: data/volcanes/volcano_db.csv
Salida:  assets/geojson/volcanes_andinos.json
"""
import csv
import json
from datetime import datetime

INPUT_CSV = 'data/volcanes/volcano_db.csv'
OUTPUT_PATH = 'assets/geojson/volcanes_andinos.json'

# Países andinos (según columna "Country")
PAISES_ANDINOS = {
    'Colombia': 'Colombia',
    'Ecuador': 'Ecuador',
    'Peru': 'Perú',
    'Bolivia': 'Bolivia',
    'Chile': 'Chile',
    'Argentina': 'Argentina',
}

volcanes = []

with open(INPUT_CSV, 'r', encoding='latin-1') as f:
    reader = csv.DictReader(f)
    for row in reader:
        pais_en = row.get('Country', '').strip()
        if pais_en not in PAISES_ANDINOS:
            continue
        
        try:
            lat = float(row.get('Latitude', '').strip())
            lon = float(row.get('Longitude', '').strip())
        except (ValueError, AttributeError):
            continue
        
        # Filtrar solo Sudamérica andina
        if not (-56 <= lat <= 13 and -82 <= lon <= -34):
            continue
        
        try:
            elev = float(row.get('Elev', '').strip())
        except (ValueError, AttributeError):
            elev = None
        
        volcanes.append({
            'type': 'Feature',
            'properties': {
                'numero': row.get('Number', '').strip(),
                'nombre': row.get('Volcano Name', '').strip(),
                'pais': PAISES_ANDINOS[pais_en],
                'pais_en': pais_en,
                'region': row.get('Region', '').strip(),
                'elevacion_m': elev,
                'tipo': row.get('Type', '').strip(),
                'estado': row.get('Status', '').strip(),
                'ultima_erupcion': row.get('Last Known', '').strip(),
            },
            'geometry': {
                'type': 'Point',
                'coordinates': [lon, lat]
            }
        })

# Ordenar por nombre
volcanes.sort(key=lambda v: v['properties']['nombre'])

# Agrupar por país para estadísticas
por_pais = {}
for v in volcanes:
    pais = v['properties']['pais']
    por_pais[pais] = por_pais.get(pais, 0) + 1

output = {
    'type': 'FeatureCollection',
    'fuente': 'Smithsonian Global Volcanism Program',
    'generado': datetime.now().strftime('%Y-%m-%d'),
    'total': len(volcanes),
    'por_pais': por_pais,
    'features': volcanes
}

with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"✅ {OUTPUT_PATH} generado")
print(f"   Total: {len(volcanes)} volcanes andinos")
print(f"\nPor país:")
for pais, n in sorted(por_pais.items(), key=lambda x: -x[1]):
    print(f"  {pais}: {n}")
