"""
Genera assets/geojson/analisis_ztd_completo.json

Análisis avanzado del Mecanismo C para 5 estaciones:
1. Serie temporal doble eje (ZTD vs precipitación)
2. Correlación con lag (0-72h / 0-3 días)
3. ROC-AUC para predecir precipitación intensa
4. Tendencia de largo plazo del ZTD
"""
import sqlite3
import json
import urllib.request
import urllib.parse
from datetime import datetime
from scipy import stats
import numpy as np

DB_PATH = 'data/andes_observa.db'
OUTPUT_PATH = 'assets/geojson/analisis_ztd_completo.json'

ESTACIONES = ['BOGT', 'CALI', 'SANT', 'AREQ', 'ANTC']

def obtener_coords(cursor, code):
    cursor.execute("SELECT lat, lon FROM stations WHERE code = ?", (code,))
    row = cursor.fetchone()
    return (row['lat'], row['lon']) if row else (None, None)


def ztd_diario(cursor, code):
    """Promedio diario de ZTD."""
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
    """Precipitación diaria de Open-Meteo."""
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


def calcular_roc_auc(y_true, y_score):
    """ROC-AUC manual sin sklearn."""
    # Ordenar por score descendente
    orden = np.argsort(-np.array(y_score))
    y_true = np.array(y_true)[orden]
    n_pos = y_true.sum()
    n_neg = len(y_true) - n_pos
    if n_pos == 0 or n_neg == 0:
        return 0.5, [], []
    
    tpr_list = [0]
    fpr_list = [0]
    tp = 0
    fp = 0
    for y in y_true:
        if y == 1:
            tp += 1
        else:
            fp += 1
        tpr_list.append(tp / n_pos)
        fpr_list.append(fp / n_neg)
    
    # AUC con método trapezoidal
    auc = 0
    for i in range(1, len(fpr_list)):
        auc += (fpr_list[i] - fpr_list[i-1]) * (tpr_list[i] + tpr_list[i-1]) / 2
    
    return abs(auc), fpr_list, tpr_list


def analisis_estacion(cursor, code):
    """Ejecuta los 4 análisis para una estación."""
    print(f"\n📍 {code}")
    
    lat, lon = obtener_coords(cursor, code)
    if not lat or not lon:
        return None
    print(f"  📌 Coords: {lat}, {lon}")
    
    # ZTD diario
    ztd = ztd_diario(cursor, code)
    if len(ztd) < 20:
        return None
    print(f"  📊 {len(ztd)} días ZTD")
    
    fechas = sorted(ztd.keys())
    inicio, fin = fechas[0], fechas[-1]
    
    # Precipitación
    precip = precip_openmeteo(lat, lon, inicio, fin)
    print(f"  🌧️ {len(precip)} días precipitación")
    
    # Emparejar
    pares = []
    for dia in fechas:
        if dia in precip:
            pares.append({'fecha': dia, 'ztd': ztd[dia], 'precip': precip[dia]})
    
    if len(pares) < 20:
        return None
    
    # Anomalía ZTD
    valores_ztd = [p['ztd'] for p in pares]
    promedio_ztd = sum(valores_ztd) / len(valores_ztd)
    for p in pares:
        p['ztd_anomaly'] = round(p['ztd'] - promedio_ztd, 2)
    
    anomalies = np.array([p['ztd_anomaly'] for p in pares])
    precip_arr = np.array([p['precip'] for p in pares])
    fechas_arr = [p['fecha'] for p in pares]
    
    # ═══ 1. Spearman global ═══
    r_spearman, p_spearman = stats.spearmanr(anomalies, precip_arr)
    print(f"  ✅ Spearman: r = {r_spearman:.3f}, p = {p_spearman:.4f}")
    
    # ═══ 2. Correlación con lag (0-3 días) ═══
    lags_analysis = []
    for lag in range(0, 4):
        if lag == 0:
            a, p = anomalies, precip_arr
        else:
            a = anomalies[:-lag]
            p = precip_arr[lag:]
        if len(a) > 10:
            r, pv = stats.spearmanr(a, p)
            lags_analysis.append({
                'lag_dias': lag,
                'r': round(float(r), 4),
                'p_value': float(pv)
            })
    print(f"  ✅ Lags 0-3 días: {len(lags_analysis)} puntos")
    
    # ═══ 3. ROC-AUC para predecir precipitación intensa ═══
    threshold_p90 = np.percentile(precip_arr, 90)
    y_true = (precip_arr >= threshold_p90).astype(int)
    auc, fpr, tpr = calcular_roc_auc(y_true, anomalies)
    print(f"  ✅ ROC-AUC: {auc:.3f}")
    
    # ═══ 4. Tendencia de largo plazo ═══
    # Regresión lineal del ZTD vs tiempo
    x = np.arange(len(valores_ztd))
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, valores_ztd)
    # Convertir slope a mm/mes (30 días)
    slope_mm_mes = slope * 30
    print(f"  ✅ Tendencia: {slope_mm_mes:+.2f} mm/mes (p={p_value:.4f})")
    
    return {
        'estacion': code,
        'lat': lat,
        'lon': lon,
        'n_observaciones': len(pares),
        'periodo': {'inicio': inicio, 'fin': fin},
        'ztd_promedio_mm': round(promedio_ztd, 2),
        # 1. Spearman
        'correlacion': {
            'spearman_r': round(float(r_spearman), 4),
            'p_value': float(p_spearman),
            'significativa': bool(p_spearman < 0.05)
        },
        # 2. Lags
        'lags': lags_analysis,
        # 3. ROC-AUC
        'roc_auc': {
            'auc': round(float(auc), 4),
            'threshold_p90_mm': round(float(threshold_p90), 2),
            'n_eventos': int(y_true.sum()),
            'fpr': [round(float(v), 4) for v in fpr[:50]],
            'tpr': [round(float(v), 4) for v in tpr[:50]]
        },
        # 4. Tendencia
        'tendencia': {
            'slope_mm_mes': round(float(slope_mm_mes), 4),
            'p_value': float(p_value),
            'significativa': bool(p_value < 0.05)
        },
        # Datos para scatter
        'datos': pares[:500]
    }


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    resultados = {}
    for code in ESTACIONES:
        resultado = analisis_estacion(cursor, code)
        if resultado:
            resultados[code] = resultado
    
    conn.close()
    
    output = {
        'fuente': 'SIRGAS-CON (ZTD) + Open-Meteo (precipitación)',
        'generado': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'analisis': 'Mecanismo C completo (Spearman + lag + ROC-AUC + tendencia)',
        'estaciones': resultados
    }
    
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ {OUTPUT_PATH} generado")
    print(f"\n{'Estación':<8} {'Spearman':<10} {'AUC':<8} {'Tendencia':<15} {'Lag óptimo'}")
    print('-' * 65)
    for code, d in resultados.items():
        r = d['correlacion']['spearman_r']
        auc = d['roc_auc']['auc']
        slope = d['tendencia']['slope_mm_mes']
        # Encontrar lag con máxima correlación
        lags = d['lags']
        mejor_lag = max(lags, key=lambda x: abs(x['r'])) if lags else {'lag_dias': 0}
        print(f"{code:<8} {r:>+6.3f}     {auc:>6.3f}   {slope:>+8.2f} mm/mes   {mejor_lag['lag_dias']} días")


if __name__ == '__main__':
    main()
