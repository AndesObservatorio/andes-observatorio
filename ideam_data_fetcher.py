#!/usr/bin/env python3
"""
Script para descargar datos de estaciones del IDEAM desde el portal de datos abiertos de Colombia.
Utiliza la API SODA (Socrata) para consultar los datos.
"""

import requests
import json
import csv
import os
from datetime import datetime

# ============================================================
# CONFIGURACIÓN
# ============================================================
# URL de la API SODA para datos de estaciones del IDEAM
# Fuente: https://www.datos.gov.co/Ambiente/Datos-de-Estaciones-de-IDEAM-y-de-Terceros/3w6p-7g9q
API_URL = "https://www.datos.gov.co/resource/3w6p-7g9q.json"

# Parámetros de consulta (limitamos a 1000 registros para prueba)
PARAMS = {
    "$limit": 1000,
    "$order": "fecha DESC"
}

# ============================================================
# FUNCIONES
# ============================================================
def descargar_datos_ideam():
    """Descarga datos de estaciones del IDEAM desde la API SODA."""
    print("🔄 Descargando datos del IDEAM...")
    try:
        response = requests.get(API_URL, params=PARAMS, timeout=30)
        response.raise_for_status()
        data = response.json()
        print(f"✅ Descargados {len(data)} registros del IDEAM")
        return data
    except requests.exceptions.RequestException as e:
        print(f"❌ Error al descargar datos del IDEAM: {e}")
        return None

def procesar_datos_ideam(data):
    """Procesa los datos del IDEAM y los estructura para el dashboard."""
    if not data:
        return None
    
    processed = []
    for record in data:
        try:
            # Extraer campos relevantes
            estacion = record.get('estacion', 'N/A')
            municipio = record.get('municipio', 'N/A')
            departamento = record.get('departamento', 'N/A')
            latitud = record.get('latitud', 'N/A')
            longitud = record.get('longitud', 'N/A')
            temperatura = record.get('temperatura', 'N/A')
            humedad = record.get('humedad', 'N/A')
            precipitacion = record.get('precipitacion', 'N/A')
            fecha = record.get('fecha', 'N/A')
            
            processed.append({
                'estacion': estacion,
                'municipio': municipio,
                'departamento': departamento,
                'latitud': latitud,
                'longitud': longitud,
                'temperatura': temperatura,
                'humedad': humedad,
                'precipitacion': precipitacion,
                'fecha': fecha
            })
        except Exception as e:
            print(f"⚠️ Error procesando registro: {e}")
            continue
    
    return processed

def guardar_json(data, filename='ideam_datos.json'):
    """Guarda los datos procesados en un archivo JSON."""
    if not data:
        return
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ Datos guardados en {filename}")

def guardar_csv(data, filename='ideam_datos.csv'):
    """Guarda los datos procesados en un archivo CSV."""
    if not data:
        return
    keys = data[0].keys()
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(data)
    print(f"✅ Datos guardados en {filename}")

# ============================================================
# EJECUCIÓN PRINCIPAL
# ============================================================
if __name__ == "__main__":
    print("=" * 50)
    print("🌦️ DESCARGADOR DE DATOS IDEAM")
    print("=" * 50)
    
    # Descargar datos
    raw_data = descargar_datos_ideam()
    
    if raw_data:
        # Procesar datos
        processed_data = procesar_datos_ideam(raw_data)
        
        if processed_data:
            # Guardar en JSON
            guardar_json(processed_data)
            
            # Guardar en CSV
            guardar_csv(processed_data)
            
            print("\n📊 Resumen de datos:")
            print(f"   - Total de registros: {len(processed_data)}")
            print(f"   - Archivos generados: ideam_datos.json, ideam_datos.csv")
        else:
            print("❌ No se pudieron procesar los datos del IDEAM.")
    else:
        print("❌ No se pudieron descargar los datos del IDEAM.")
