#!/usr/bin/env python3
"""
Análisis de velocidades tectónicas SIRGAS.
Calcula estadísticas y clasifica por tipo de deformación.
"""
import requests
import json
import numpy as np

API_BASE = "https://andes-observatorio.onrender.com"

def clasificar_velocidad(magnitud):
    """Clasificación geodésica según magnitud."""
    if magnitud <= 5:
        return "Intraplaca estable"
    elif magnitud <= 15:
        return "Deformación media"
    elif magnitud <= 25:
        return "Actividad tectónica"
    else:
        return "Borde de placa"

def analizar_sirgas():
    print("📡 Descargando velocidades SIRGAS...")
    r = requests.get(f"{API_BASE}/api/v1/geodesia/velocidades", timeout=30)
    data = r.json()
    estaciones = data['estaciones']
    
    resultados = []
    for est in estaciones:
        vn = est.get('velocidad_norte', 0)
        ve = est.get('velocidad_este', 0)
        vu = est.get('velocidad_up', 0)
        magnitud = np.sqrt(vn**2 + ve**2)
        
        # Azimut (desde el Norte, horario)
        azimut = np.degrees(np.arctan2(ve, vn))
        if azimut < 0:
            azimut += 360
        
        resultados.append({
            'codigo': est['codigo'],
            'velocidad_norte': round(vn, 2),
            'velocidad_este': round(ve, 2),
            'velocidad_up': round(vu, 2),
            'magnitud_horizontal': round(magnitud, 2),
            'azimut': round(azimut, 1),
            'clasificacion': clasificar_velocidad(magnitud)
        })
    
    # Estadísticas globales
    magnitudes = [r['magnitud_horizontal'] for r in resultados]
    
    resumen = {
        'total_estaciones': len(resultados),
        'magnitud_media': round(np.mean(magnitudes), 2),
        'magnitud_min': round(min(magnitudes), 2),
        'magnitud_max': round(max(magnitudes), 2),
        'std': round(np.std(magnitudes), 2),
        'estaciones': resultados
    }
    
    with open('assets/geojson/analisis_sirgas.json', 'w') as f:
        json.dump(resumen, f, indent=2)
    
    print(f"✅ {len(resultados)} estaciones analizadas")
    print(f"   Magnitud media: {resumen['magnitud_media']} mm/año")
    print(f"   Rango: {resumen['magnitud_min']} a {resumen['magnitud_max']} mm/año")

if __name__ == "__main__":
    analizar_sirgas()
