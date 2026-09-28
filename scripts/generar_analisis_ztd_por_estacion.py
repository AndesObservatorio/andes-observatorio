"""
Genera assets/geojson/analisis_ztd_por_estacion.json

Para cada estación con datos largos (BOGT, CALI, SANT, AREQ, ANTC):
1. Lee la serie ZTD diaria de la BD
2. Descarga precipitación diaria de Open-Meteo
3. Empareja por fecha
4. Calcula Spearman
"""
import sqlite3
import json
import urllib.request
import urllib.parse
from datetime import datetime, timedelta
from scipy import stats
from collections import defaultdict

DB_PATH = 'data/andes_observa.db'
OUTPUT_PATH = 'assets/geojson/analisis_ztd_por_estacion.json'

# Estaciones con datos largos (4000+ obs)
ESTACIONES_LARGAS = ['BOGT', 'CALI', 'SANT', 'AREQ', 'ANTC']

# Coordenadas (desde la BD)
def obtener_coords(cursor, code):
    cursor.execute("SELECT lat, lon FROM stations WHERE code = ?", (code,))
    row = cursor.fetchone()
    return (row['lat'], row['lon']) if row else (None, None)


def ztd_diario(cursor, code):
    """Promedio diario de ZTD para una estación."""
    cursor.execute("""
        SELECT DATE(epoch) as dia, AVG(ztd_total_mm) as ztd
        FROM tropo_observations o
        JOIN stations s ON o.station_id = s.id
        WHERE s.code = ? AND ztd_total_mm IS NOT NULL
        GROUP BY DATE(epoch)
        ORDER BY dia
    """, (code,))
    return {row['dia']: round(row['ztd'], 2) for row in cursor.fetchall()}


def precip_openmeteo(lat, lon, fecha_inicio, fecha_fin):
    """Descarga precipitación diaria de Open-Meteo."""
    params = {
        'latitude': lat,
        'longitude': lon,
        'start_date': fecha_inicio,
        'end_date': fecha_fin,
        'daily': 'precipitation_sum',
        'timezone': 'America/Bogota',
    }
    url = 'https://archive-api.open-meteo.com/v1/archive?' + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            data = json.loads(response.read().decode('utf-8'))
        fechas = data['daily']['time']
        precip = data['daily']['precipitation_sum']
        return {f: round(p or 0, 2) for f, p in zip(fechas, precip)}
    except Exception as e:
        print(f"  ⚠️ Error descargando precipitación: {e}")
        return {}


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    resultados = {}

    for code in ESTACIONES_LARGAS:
        print(f"\n📍 Procesando {code}...")

        # Coordenadas
        lat, lon = obtener_coords(cursor, code)
        if not lat or not lon:
            print(f"  ⚠️ Sin coordenadas")
            continue
        print(f"  📌 Coords: {lat}, {lon}")

        # Serie ZTD diaria
        ztd = ztd_diario(cursor, code)
        if not ztd:
            print(f"  ⚠️ Sin datos ZTD")
            continue
        print(f"  📊 {len(ztd)} días con ZTD")

        # Rango temporal
        fechas = sorted(ztd.keys())
        inicio, fin = fechas[0], fechas[-1]

        # Descargar precipitación
        print(f"  🌧️ Descargando precipitación {inicio} → {fin}")
        precip = precip_openmeteo(lat, lon, inicio, fin)
        print(f"  📊 {len(precip)} días con precipitación")

        # Emparejar por fecha
        pares = []
        for dia in fechas:
            if dia in precip:
                pares.append({
                    'fecha': dia,
                    'ztd': ztd[dia],
                    'precip': precip[dia]
                })

        if len(pares) < 20:
            print(f"  ⚠️ Solo {len(pares)} días emparejados (muy pocos)")
            continue

        # Calcular anomalía ZTD (ZTD - promedio)
        ztd_valores = [p['ztd'] for p in pares]
        promedio = sum(ztd_valores) / len(ztd_valores)
        for p in pares:
            p['ztd_anomaly'] = round(p['ztd'] - promedio, 2)

        # Spearman
        anomalies = [p['ztd_anomaly'] for p in pares]
        precip_list = [p['precip'] for p in pares]
        r, p_value = stats.spearmanr(anomalies, precip_list)

        print(f"  ✅ Correlación Spearman: r = {r:.3f}, p = {p_value:.4f}")

        resultados[code] = {
            'estacion': code,
            'lat': lat,
            'lon': lon,
            'n_observaciones': len(pares),
            'periodo': {'inicio': inicio, 'fin': fin},
            'ztd_promedio_mm': round(promedio, 2),
            'correlacion': {
                'spearman_r': round(float(r), 4),
                'p_value': float(p_value),
                'significativa': bool(p_value < 0.05)
            },
            'datos': pares[:500]  # Limitar a 500 puntos para el JSON
        }

    conn.close()

    output = {
        'fuente': 'SIRGAS-CON (ZTD) + Open-Meteo (precipitación)',
        'generado': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'estaciones': resultados,
    }

    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n✅ {OUTPUT_PATH} generado")
    print(f"   Total: {len(resultados)} estaciones procesadas")
    print(f"\n{'Estación':<8} {'r':<10} {'p-value':<12} {'n':<6} {'Sig.'}")
    print('-' * 50)
    for code, datos in resultados.items():
        r = datos['correlacion']['spearman_r']
        p = datos['correlacion']['p_value']
        n = datos['n_observaciones']
        sig = '✅' if datos['correlacion']['significativa'] else '❌'
        print(f"{code:<8} {r:>6.3f}    {p:>8.4f}    {n:>4}    {sig}")


if __name__ == '__main__':
    main()
