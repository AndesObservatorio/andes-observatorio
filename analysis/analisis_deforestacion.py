#!/usr/bin/env python3
"""
Análisis de deforestación en la región andina.
Fuente: Global Forest Watch (datos 2024)
"""
import json

# Datos oficiales de GFW 2024 (pérdida de cobertura arbórea, umbral 30%)
DEFORESTACION = {
    'Brasil': {'perdida_ha': 1245000, 'area_total_km2': 8515767, 'periodo': '2024'},
    'Colombia': {'perdida_ha': 174103, 'area_total_km2': 1141748, 'periodo': '2024'},
    'Bolivia': {'perdida_ha': 298000, 'area_total_km2': 1098581, 'periodo': '2024'},
    'Perú': {'perdida_ha': 144682, 'area_total_km2': 1285216, 'periodo': '2024'},
    'Venezuela': {'perdida_ha': 89000, 'area_total_km2': 916445, 'periodo': '2024'},
    'Ecuador': {'perdida_ha': 26000, 'area_total_km2': 256369, 'periodo': '2024'},
}

# Coordenadas aproximadas de áreas críticas de deforestación
ZONAS_CRITICAS = [
    {'nombre': 'Amazonía Brasil', 'lat': -3.5, 'lon': -62.0, 'intensidad': 'alta', 'pais': 'Brasil'},
    {'nombre': 'Caquetá Colombia', 'lat': 1.0, 'lon': -75.0, 'intensidad': 'alta', 'pais': 'Colombia'},
    {'nombre': 'Guaviare Colombia', 'lat': 2.5, 'lon': -72.5, 'intensidad': 'alta', 'pais': 'Colombia'},
    {'nombre': 'Madre de Dios Perú', 'lat': -12.5, 'lon': -70.0, 'intensidad': 'alta', 'pais': 'Perú'},
    {'nombre': 'Santa Cruz Bolivia', 'lat': -17.0, 'lon': -63.0, 'intensidad': 'alta', 'pais': 'Bolivia'},
    {'nombre': 'Amazonía Ecuador', 'lat': -1.5, 'lon': -76.0, 'intensidad': 'media', 'pais': 'Ecuador'},
    {'nombre': 'Llanos Venezuela', 'lat': 7.5, 'lon': -68.0, 'intensidad': 'media', 'pais': 'Venezuela'},
]

def main():
    # Calcular porcentajes
    resultados = []
    for pais, datos in DEFORESTACION.items():
        perdida_km2 = datos['perdida_ha'] / 100
        porcentaje = (perdida_km2 / datos['area_total_km2']) * 100
        resultados.append({
            'pais': pais,
            'perdida_ha': datos['perdida_ha'],
            'perdida_km2': round(perdida_km2, 2),
            'porcentaje': round(porcentaje, 4),
            'periodo': datos['periodo']
        })
    
    # Ordenar por pérdida descendente
    resultados.sort(key=lambda x: x['perdida_ha'], reverse=True)
    
    resumen = {
        'total_paises': len(resultados),
        'perdida_total_ha': sum(r['perdida_ha'] for r in resultados),
        'periodo': '2024',
        'fuente': 'Global Forest Watch',
        'umbral_cobertura': '30%',
        'paises': resultados,
        'zonas_criticas': ZONAS_CRITICAS
    }
    
    with open('assets/geojson/analisis_deforestacion.json', 'w') as f:
        json.dump(resumen, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Análisis de deforestación completado")
    print(f"   Países: {resumen['total_paises']}")
    print(f"   Pérdida total: {resumen['perdida_total_ha']:,} ha (2024)")
    for r in resultados:
        print(f"   {r['pais']}: {r['perdida_ha']:,} ha ({r['porcentaje']}%)")

if __name__ == "__main__":
    main()
