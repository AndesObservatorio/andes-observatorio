"""
Genera assets/geojson/anomalia_ztd.json a partir de la BD andes_observa.db.

Calcula para cada estación:
- ZTD promedio histórico (todos los datos)
- ZTD último valor registrado
- Anomalía = último - promedio
- Rango (min, max)
- Categoría según anomalía (muy húmedo / húmedo / normal / seco)
"""
import sqlite3
import json
from datetime import datetime

DB_PATH = 'data/andes_observa.db'
OUTPUT_PATH = 'assets/geojson/anomalia_ztd.json'

# Nombres de estaciones (ya definidos en el dashboard)
NOMBRES = {
    'AN02': {'nombre': 'Ancón', 'pais': 'Perú'},
    'ANTC': {'nombre': 'Antofagasta', 'pais': 'Chile'},
    'AP01': {'nombre': 'Arequipa Norte', 'pais': 'Perú'},
    'AREQ': {'nombre': 'Arequipa', 'pais': 'Perú'},
    'BOGT': {'nombre': 'Bogotá', 'pais': 'Colombia'},
    'CALI': {'nombre': 'Cali', 'pais': 'Colombia'},
    'CS01': {'nombre': 'Cusco', 'pais': 'Perú'},
    'GLPS': {'nombre': 'Galápagos', 'pais': 'Ecuador'},
    'IQQE': {'nombre': 'Iquique', 'pais': 'Chile'},
    'LPGS': {'nombre': 'La Plata', 'pais': 'Argentina'},
    'QUI3': {'nombre': 'Quito', 'pais': 'Ecuador'},
    'RDSD': {'nombre': 'Santo Domingo', 'pais': 'Rep. Dominicana'},
    'SANT': {'nombre': 'Santiago', 'pais': 'Chile'},
}

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Obtener coordenadas y datos por estación
cursor.execute("SELECT code, lat, lon FROM stations;")
stations_coords = {row['code']: {'lat': row['lat'], 'lon': row['lon']} for row in cursor.fetchall()}

# Para cada estación, calcular estadísticas
estaciones = []
cursor.execute("SELECT id, code FROM stations;")
for station in cursor.fetchall():
    station_id = station['id']
    code = station['code']

    # ZTD promedio histórico
    cursor.execute("""
        SELECT AVG(ztd_total_mm) as promedio,
               COUNT(*) as n,
               MIN(epoch) as inicio,
               MAX(epoch) as fin
        FROM tropo_observations
        WHERE station_id = ? AND ztd_total_mm IS NOT NULL
    """, (station_id,))
    stats = cursor.fetchone()

    if not stats['promedio']:
        continue

    # Último valor
    cursor.execute("""
        SELECT ztd_total_mm, epoch
        FROM tropo_observations
        WHERE station_id = ? AND ztd_total_mm IS NOT NULL
        ORDER BY epoch DESC LIMIT 1
    """, (station_id,))
    ultimo = cursor.fetchone()

    ztd_promedio = round(stats['promedio'], 1)
    ztd_ultimo = round(ultimo['ztd_total_mm'], 1)
    anomalia = round(ztd_ultimo - ztd_promedio, 1)

    # Categoría
    if anomalia > 10:
        categoria = 'muy_humedo'
    elif anomalia > 0:
        categoria = 'humedo'
    elif anomalia > -10:
        categoria = 'normal'
    else:
        categoria = 'seco'

    info = NOMBRES.get(code, {'nombre': code, 'pais': 'N/A'})
    coords = stations_coords.get(code, {})

    estaciones.append({
        'codigo': code,
        'nombre': info['nombre'],
        'pais': info['pais'],
        'lat': coords.get('lat'),
        'lon': coords.get('lon'),
        'n_obs': stats['n'],
        'periodo': {
            'inicio': stats['inicio'][:10] if stats['inicio'] else None,
            'fin': stats['fin'][:10] if stats['fin'] else None,
        },
        'ztd_promedio_mm': ztd_promedio,
        'ztd_ultimo_mm': ztd_ultimo,
        'anomalia_mm': anomalia,
        'categoria': categoria,
    })

conn.close()

# Ordenar por anomalía descendente (más húmedo primero)
estaciones.sort(key=lambda e: e['anomalia_mm'], reverse=True)

output = {
    'fuente': 'SIRGAS-TRO',
    'generado': datetime.now().strftime('%Y-%m-%d'),
    'total_estaciones': len(estaciones),
    'estaciones': estaciones,
}

with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"✅ {OUTPUT_PATH} generado")
print(f"   Total: {len(estaciones)} estaciones")
print(f"\n{'Código':<6} {'Anomalía (mm)':<15} {'Categoría':<12}")
print('-' * 40)
for e in estaciones:
    print(f"{e['codigo']:<6} {e['anomalia_mm']:>+10.1f}      {e['categoria']}")
