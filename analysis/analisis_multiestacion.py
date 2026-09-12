#!/usr/bin/env python3
"""
Análisis ZTD vs Precipitación para las 13 estaciones SIRGAS.
Genera JSON con resultados por estación.
"""
import requests
import pandas as pd
import numpy as np
from scipy import stats
import json

API_BASE = "https://andes-observatorio.onrender.com"

# Coordenadas de las 13 estaciones
ESTACIONES = {
    'AN02': (12.05, -77.04),  # ¡OJO! Necesitamos coordenadas correctas
    'ANTC': (-23.65, -70.40),
    'AP01': (-16.40, -71.53),
    'AREQ': (-16.47, -71.49),
    'BOGT': (4.64, -74.08),
    'CALI': (3.45, -76.53),
    'CS01': (-13.53, -71.97),
    'GLPS': (-0.74, -90.30),
    'IQQE': (-20.27, -69.86),
    'LPGS': (-34.90, -57.93),
    'QUI3': (-0.18, -78.47),
    'RDSD': (18.48, -69.91),
    'SANT': (-33.44, -70.66),
}

def descargar_ztd(codigo):
    url = f"{API_BASE}/api/v1/geodesia/tropo/{codigo}/serie?limite=5000"
    try:
        r = requests.get(url, timeout=30)
        data = r.json()
        df = pd.DataFrame(data['datos'])
        df['fecha'] = pd.to_datetime(df['fecha'])
        df = df.set_index('fecha')
        return df['valor'].resample('D').mean()
    except Exception as e:
        print(f"  ❌ {codigo}: {e}")
        return None

def descargar_precip(lat, lon, inicio, fin):
    url = f"https://archive-api.open-meteo.com/v1/archive?latitude={lat}&longitude={lon}&start_date={inicio}&end_date={fin}&daily=precipitation_sum&timezone=auto"
    try:
        r = requests.get(url, timeout=30)
        data = r.json()
        df = pd.DataFrame({
            'fecha': pd.to_datetime(data['daily']['time']),
            'precip_mm': data['daily']['precipitation_sum']
        })
        return df.set_index('fecha')
    except Exception as e:
        print(f"  ❌ Precip: {e}")
        return None

def analizar_estacion(codigo, lat, lon):
    print(f"\n📍 Analizando {codigo} ({lat}, {lon})...")
    
    # ZTD
    ztd = descargar_ztd(codigo)
    if ztd is None or len(ztd) < 30:
        return None
    
    inicio = str(ztd.index.min().date())
    fin = str(ztd.index.max().date())
    
    # Precipitación
    precip = descargar_precip(lat, lon, inicio, fin)
    if precip is None:
        return None
    
    # Alinear
    merged = pd.DataFrame({'ztd': ztd, 'precip': precip['precip_mm']}).dropna()
    if len(merged) < 30:
        return None
    
    # Anomalía ZTD
    merged['ztd_anomaly'] = merged['ztd'] - merged['ztd'].rolling(30, center=True).mean()
    merged_clean = merged.dropna()
    
    if len(merged_clean) < 20:
        return None
    
    # Correlación
    r, p = stats.spearmanr(merged_clean['ztd_anomaly'], merged_clean['precip'])
    
    resultado = {
        'codigo': codigo,
        'lat': lat,
        'lon': lon,
        'n_obs': len(merged_clean),
        'spearman_r': round(r, 3),
        'p_value': round(p, 6),
        'significativa': bool(p < 0.05)
    }
    
    print(f"  ✅ N={len(merged_clean)}, r={r:.3f}, p={p:.4f} {'⭐' if p < 0.05 else ''}")
    return resultado

def main():
    resultados = []
    for codigo, (lat, lon) in ESTACIONES.items():
        res = analizar_estacion(codigo, lat, lon)
        if res:
            resultados.append(res)
    
    # Guardar
    with open('assets/geojson/analisis_multiestacion.json', 'w') as f:
        json.dump({
            'total_estaciones': len(resultados),
            'estaciones_significativas': sum(1 for r in resultados if r['significativa']),
            'resultados': resultados
        }, f, indent=2)
    
    print(f"\n{'='*60}")
    print(f"✅ Análisis completado: {len(resultados)} estaciones")
    print(f"   Significativas (p<0.05): {sum(1 for r in resultados if r['significativa'])}")
    print(f"   Guardado: assets/geojson/analisis_multiestacion.json")

if __name__ == "__main__":
    main()
