"""
Análisis de correlación cruzada: Sismos superficiales vs Precipitación.

Hipótesis (Mecanismo B):
    Cambios en la carga hidrológica → deformación cortical
    → modulación de la microsismicidad regional.

Análisis:
    1. Serie temporal mensual de sismos superficiales (M ≥ 4.5)
    2. Serie temporal mensual de precipitación (CHIRPS)
    3. Correlación cruzada con lag (0-12 meses)

Salida:
    assets/geojson/analisis_sismos_precip.json
"""
import json
from datetime import datetime
from collections import defaultdict
from scipy import stats
import numpy as np

SISMOS_PATH = 'assets/geojson/sismos_andinos.json'
CHIRPS_PATH = 'assets/geojson/chirps_julio2026.geojson'
OUTPUT_PATH = 'assets/geojson/analisis_sismos_precip.json'

PROF_MAXIMA_KM = 30  # Solo sismos superficiales

# ═══════════════════════════════════════════════════════════
# 1. CARGAR SISMOS Y AGRUPAR POR MES
# ═══════════════════════════════════════════════════════════
print("📥 Cargando sismos...")
with open(SISMOS_PATH, 'r', encoding='utf-8') as f:
    sismos_data = json.load(f)

sismos_superf = []
for s in sismos_data['features']:
    p = s['properties']
    if p.get('prof_km', 999) <= PROF_MAXIMA_KM:
        sismos_superf.append(p)

print(f"   Total sismos: {len(sismos_data['features'])}")
print(f"   Superficiales (<{PROF_MAXIMA_KM} km): {len(sismos_superf)}")

# Agrupar por mes
sismos_por_mes = defaultdict(int)
for s in sismos_superf:
    mes = s['fecha'][:7]  # YYYY-MM
    sismos_por_mes[mes] += 1

# ═══════════════════════════════════════════════════════════
# 2. CARGAR PRECIPITACIÓN CHIRPS Y AGRUPAR POR MES
# ═══════════════════════════════════════════════════════════
print("\n📥 Cargando precipitación CHIRPS...")
with open(CHIRPS_PATH, 'r', encoding='utf-8') as f:
    chirps_data = json.load(f)

# CHIRPS actual es solo julio 2026 — usar como referencia
# Para un análisis real, se necesitaría CHIRPS mensual 2015-2025
precip_por_mes = defaultdict(list)
for p in chirps_data['features']:
    props = p['properties']
    mes = props.get('mes', '2026-07')  # Ajustar según estructura
    precip_por_mes[mes].append(props.get('precip_mm', 0))

print(f"   Total puntos CHIRPS: {len(chirps_data['features'])}")
print(f"   Meses disponibles: {len(precip_por_mes)}")

# ═══════════════════════════════════════════════════════════
# 3. ALINEAR SERIES TEMPORALES
# ═══════════════════════════════════════════════════════════
# Nota: los datos reales de CHIRPS son limitados (solo julio 2026)
# Para el análisis completo se necesita descargar CHIRPS mensual 2015-2025
# Por ahora generamos un placeholder con la estructura correcta

meses_comunes = sorted(set(sismos_por_mes.keys()))

print(f"\n📊 Meses con sismos: {len(meses_comunes)}")
print(f"   Desde: {meses_comunes[0] if meses_comunes else 'N/A'}")
print(f"   Hasta: {meses_comunes[-1] if meses_comunes else 'N/A'}")

# ═══════════════════════════════════════════════════════════
# 4. GENERAR JSON CON LA ESTRUCTURA
# ═══════════════════════════════════════════════════════════
serie_mensual = []
for mes in meses_comunes:
    serie_mensual.append({
        'mes': mes,
        'sismos': sismos_por_mes[mes],
        'precip_mm': None  # Placeholder hasta descargar CHIRPS completo
    })

output = {
    'fuente': 'USGS + CHIRPS',
    'generado': datetime.now().strftime('%Y-%m-%d'),
    'criterio': f'Sismos superficiales (<{PROF_MAXIMA_KM} km, M≥4.5) vs precipitación',
    'total_sismos_superficiales': len(sismos_superf),
    'periodo': {
        'inicio': meses_comunes[0] if meses_comunes else None,
        'fin': meses_comunes[-1] if meses_comunes else None
    },
    'serie_mensual': serie_mensual,
    'nota': 'CHIRPS mensual 2015-2025 pendiente de descarga para análisis completo',
    'sismos_por_mes': dict(sismos_por_mes)
}

with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

import os
tamano_kb = os.path.getsize(OUTPUT_PATH) / 1024

print(f"\n✅ {OUTPUT_PATH}")
print(f"   Tamaño: {tamano_kb:.1f} KB")
print(f"   Meses en serie: {len(serie_mensual)}")

# Mostrar primeros 5 meses
print(f"\n📊 Primeros 5 meses:")
for s in serie_mensual[:5]:
    print(f"   {s['mes']}: {s['sismos']} sismos")
