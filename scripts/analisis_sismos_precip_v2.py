"""
Análisis de correlación cruzada: Sismos superficiales vs Precipitación.

Usa Open-Meteo para obtener precipitación mensual 2015-2025
en las coordenadas de las estaciones SIRGAS.
"""
import json
import urllib.request
import urllib.parse
from datetime import datetime
from collections import defaultdict
from scipy import stats
import numpy as np

SISMOS_PATH = 'assets/geojson/sismos_andinos.json'
ESTACIONES_PATH = 'assets/geojson/anomalia_ztd.json'
OUTPUT_PATH = 'assets/geojson/analisis_sismos_precip.json'

PROF_MAXIMA_KM = 30
FECHA_INICIO = '2015-01-01'
FECHA_FIN = '2025-12-31'


def cargar_sismos_mensuales():
    """Agrupa sismos superficiales por mes."""
    print("📥 Cargando sismos...")
    with open(SISMOS_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    sismos_por_mes = defaultdict(int)
    sismos_superf = []
    
    for s in data['features']:
        p = s['properties']
        if p.get('prof_km', 999) <= PROF_MAXIMA_KM:
            sismos_superf.append(p)
            mes = p['fecha'][:7]
            sismos_por_mes[mes] += 1
    
    print(f"   Total sismos: {len(data['features'])}")
    print(f"   Superficiales: {len(sismos_superf)}")
    return dict(sismos_por_mes), sismos_superf


def descargar_precip_estacion(lat, lon, code):
    """Descarga precipitación mensual de Open-Meteo para una estación."""
    params = {
        'latitude': lat,
        'longitude': lon,
        'start_date': FECHA_INICIO,
        'end_date': FECHA_FIN,
        'daily': 'precipitation_sum',
        'timezone': 'UTC',
    }
    url = 'https://archive-api.open-meteo.com/v1/archive?' + urllib.parse.urlencode(params)
    
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            data = json.loads(response.read().decode('utf-8'))
        
        fechas = data['daily']['time']
        precip = data['daily']['precipitation_sum']
        
        # Agrupar por mes (suma de precipitación diaria)
        por_mes = defaultdict(float)
        for f, p in zip(fechas, precip):
            mes = f[:7]
            por_mes[mes] += (p or 0)
        
        print(f"   ✅ {code}: {len(por_mes)} meses descargados")
        return dict(por_mes)
    except Exception as e:
        print(f"   ❌ {code}: {e}")
        return {}


def main():
    sismos_por_mes, sismos_superf = cargar_sismos_mensuales()
    
    # Cargar estaciones
    print("\n📥 Cargando estaciones SIRGAS...")
    with open(ESTACIONES_PATH, 'r', encoding='utf-8') as f:
        estaciones_data = json.load(f)
    
    estaciones = estaciones_data['estaciones']
    print(f"   {len(estaciones)} estaciones")
    
    # Descargar precipitación de las 5 estaciones con datos largos
    estaciones_largas = ['BOGT', 'CALI', 'SANT', 'AREQ', 'ANTC']
    
    print(f"\n🌧️ Descargando precipitación de Open-Meteo...")
    precip_por_estacion = {}
    for est in estaciones:
        if est['codigo'] in estaciones_largas and est.get('lat') and est.get('lon'):
            precip = descargar_precip_estacion(est['lat'], est['lon'], est['codigo'])
            precip_por_estacion[est['codigo']] = precip
    
    # Promedio regional de precipitación
    print(f"\n📊 Calculando promedio regional...")
    meses_todos = set()
    for p in precip_por_estacion.values():
        meses_todos.update(p.keys())
    
    precip_promedio = {}
    for mes in sorted(meses_todos):
        valores = [p[mes] for p in precip_por_estacion.values() if mes in p]
        if valores:
            precip_promedio[mes] = sum(valores) / len(valores)
    
    print(f"   {len(precip_promedio)} meses con precipitación promedio")
    
    # ═══ CORRELACIÓN CRUZADA ═══
    print(f"\n🔬 Análisis de correlación cruzada...")
    
    # Meses comunes entre sismos y precipitación
    meses_comunes = sorted(set(sismos_por_mes.keys()) & set(precip_promedio.keys()))
    print(f"   Meses comunes: {len(meses_comunes)}")
    
    if len(meses_comunes) < 12:
        print("   ⚠️ Muy pocos meses para análisis confiable")
        return
    
    sismos_serie = np.array([sismos_por_mes[m] for m in meses_comunes])
    precip_serie = np.array([precip_promedio[m] for m in meses_comunes])
    
    # Correlaciones con lag (0 a 12 meses)
    lags = []
    for lag in range(0, 13):
        if lag == 0:
            s, p = sismos_serie, precip_serie
        else:
            s = sismos_serie[:-lag]
            p = precip_serie[lag:]
        
        if len(s) > 10:
            r, pval = stats.spearmanr(s, p)
            lags.append({
                'lag_meses': lag,
                'r': round(float(r), 4),
                'p_value': float(pval),
                'significativa': bool(pval < 0.05)
            })
    
    # Encontrar mejor lag
    mejor_lag = max(lags, key=lambda x: abs(x['r']))
    print(f"   Mejor correlación: lag {mejor_lag['lag_meses']} meses (r={mejor_lag['r']:.3f}, p={mejor_lag['p_value']:.4f})")
    
    # ═══ GENERAR JSON ═══
    serie_mensual = []
    for mes in meses_comunes:
        serie_mensual.append({
            'mes': mes,
            'sismos': sismos_por_mes[mes],
            'precip_mm': round(precip_promedio[mes], 1)
        })
    
    output = {
        'fuente': 'USGS + Open-Meteo (ERA5)',
        'generado': datetime.now().strftime('%Y-%m-%d'),
        'criterio': f'Sismos superficiales (<{PROF_MAXIMA_KM} km, M≥4.5) vs precipitación regional',
        'total_sismos_superficiales': len(sismos_superf),
        'periodo': {
            'inicio': meses_comunes[0],
            'fin': meses_comunes[-1],
            'n_meses': len(meses_comunes)
        },
        'estaciones_usadas': estaciones_largas,
        'correlacion': {
            'mejor_lag_meses': mejor_lag['lag_meses'],
            'r_spearman': mejor_lag['r'],
            'p_value': mejor_lag['p_value'],
            'significativa': mejor_lag['significativa']
        },
        'lags': lags,
        'serie_mensual': serie_mensual,
        'nota': 'Análisis exploratorio. La señal sísmica-tectónica domina sobre la modulación por carga.'
    }
    
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    import os
    tamano_kb = os.path.getsize(OUTPUT_PATH) / 1024
    
    print(f"\n✅ {OUTPUT_PATH}")
    print(f"   Tamaño: {tamano_kb:.1f} KB")
    print(f"   Período: {meses_comunes[0]} → {meses_comunes[-1]}")
    print(f"   Meses: {len(meses_comunes)}")
    print(f"\n📊 Correlaciones por lag:")
    for l in lags[:6]:
        sig = '✅' if l['significativa'] else '  '
        print(f"   Lag {l['lag_meses']:>2} meses: r = {l['r']:>+6.3f}, p = {l['p_value']:.4f} {sig}")


if __name__ == '__main__':
    main()
