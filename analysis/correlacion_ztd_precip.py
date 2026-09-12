#!/usr/bin/env python3
"""
Mecanismo C: Correlación ZTD vs Precipitación
Analiza si la anomalía de ZTD predice precipitación intensa.
"""
import requests
import pandas as pd
import numpy as np
from scipy import stats
from datetime import datetime, timedelta
import json

API_BASE = "https://andes-observatorio.onrender.com"
STATION = "BOGT"  # Estación Bogotá

def descargar_ztd(codigo):
    """Descarga serie ZTD desde la API."""
    url = f"{API_BASE}/api/v1/geodesia/tropo/{codigo}/serie?limite=5000"
    r = requests.get(url, timeout=30)
    data = r.json()
    df = pd.DataFrame(data['datos'])
    df['fecha'] = pd.to_datetime(df['fecha'])
    df = df.set_index('fecha')
    return df

def descargar_precip_bogota():
    """
    Descarga precipitación mensual de CHIRPS para Bogotá.
    (Simplificado: usar CHIRPS ya procesado)
    """
    # Usar el GeoJSON de CHIRPS
    with open('assets/geojson/chirps_julio2026.geojson', 'r') as f:
        data = json.load(f)
    
    # Filtrar puntos cercanos a Bogotá (4.64, -74.08)
    bogota_puntos = []
    for feat in data['features']:
        lon, lat = feat['geometry']['coordinates']
        if abs(lat - 4.64) < 1 and abs(lon + 74.08) < 1:
            bogota_puntos.append({
                'fecha': '2026-07',
                'precip_mm': feat['properties']['precip_mm']
            })
    
    df = pd.DataFrame(bogota_puntos)
    df['fecha'] = pd.to_datetime(df['fecha'])
    return df.groupby('fecha').mean()

if __name__ == "__main__":
    print("=" * 60)
    print("MECANISMO C: Correlación ZTD vs Precipitación")
    print("=" * 60)
    
    print(f"\n📡 Descargando ZTD de {STATION}...")
    ztd = descargar_ztd(STATION)
    print(f"  → {len(ztd)} registros")
    print(f"  → Desde {ztd.index.min()} hasta {ztd.index.max()}")
    
    print(f"\n🌧️  Descargando precipitación de Bogotá...")
    precip = descargar_precip_bogota()
    print(f"  → {len(precip)} registros")
    
    # Análisis de correlación
    print(f"\n📊 Calculando estadísticas...")
    print(f"  ZTD media: {ztd['valor'].mean():.2f} mm")
    print(f"  ZTD std:   {ztd['valor'].std():.2f} mm")
    print(f"  ZTD min:   {ztd['valor'].min():.2f} mm")
    print(f"  ZTD max:   {ztd['valor'].max():.2f} mm")
    
    # Guardar datos para el dashboard
    ztd.to_csv('analysis/ztd_bogota.csv')
    print(f"\n✅ Guardado: analysis/ztd_bogota.csv")
