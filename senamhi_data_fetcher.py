#!/usr/bin/env python3
"""
Script para descargar y procesar datos de estaciones del SENAMHI (Perú).
Dado que no hay una API pública directa, este script demuestra la estructura para procesar
archivos descargados manualmente o desde un endpoint conocido.
"""

import requests
import json
import csv
import os
from datetime import datetime

# ============================================================
# CONFIGURACIÓN
# ============================================================
# URL de ejemplo para descarga de datos (reemplazar con la URL real)
# Fuente: https://www.senamhi.gob.pe/?p=descarga-datos
DESCARGA_URL = "https://www.senamhi.gob.pe/data/datos_historicos.csv"

# ============================================================
# FUNCIONES
# ============================================================
def descargar_datos_senamhi():
    """Descarga datos del SENAMHI desde la URL configurada."""
    print("🔄 Descargando datos del SENAMHI...")
    try:
        response = requests.get(DESCARGA_URL, timeout=30)
        response.raise_for_status()
        content = response.text
        print("✅ Datos descargados del SENAMHI")
        return content
    except requests.exceptions.RequestException as e:
        print(f"❌ Error al descargar datos del SENAMHI: {e}")
        return None

def procesar_datos_senamhi(csv_content):
    """Procesa datos del SENAMHI en formato CSV."""
    if not csv_content:
        return None
    
    lines = csv_content.strip().split('\n')
    if len(lines) < 2:
        print("⚠️ El archivo CSV está vacío o mal formado.")
        return None
    
    processed = []
    try:
        reader = csv.DictReader(lines)
        for row in reader:
            processed.append({
                'estacion': row.get('ESTACION', 'N/A'),
                'departamento': row.get('DEPARTAMENTO', 'N/A'),
                'provincia': row.get('PROVINCIA', 'N/A'),
                'latitud': row.get('LATITUD', 'N/A'),
                'longitud': row.get('LONGITUD', 'N/A'),
                'temperatura_max': row.get('TEMP_MAX', 'N/A'),
                'temperatura_min': row.get('TEMP_MIN', 'N/A'),
                'precipitacion': row.get('PRECIPITACION', 'N/A'),
                'fecha': row.get('FECHA', 'N/A')
            })
    except Exception as e:
        print(f"⚠️ Error procesando CSV del SENAMHI: {e}")
        return None
    
    return processed

def guardar_json(data, filename='senamhi_datos.json'):
    """Guarda los datos procesados en un archivo JSON."""
    if not data:
        return
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ Datos guardados en {filename}")

# ============================================================
# EJECUCIÓN PRINCIPAL
# ============================================================
if __name__ == "__main__":
    print("=" * 50)
    print("🌦️ DESCARGADOR DE DATOS SENAMHI")
    print("=" * 50)
    
    raw_data = descargar_datos_senamhi()
    
    if raw_data:
        processed_data = procesar_datos_senamhi(raw_data)
        
        if processed_data:
            guardar_json(processed_data)
            print(f"\n📊 Resumen de datos:")
            print(f"   - Total de registros: {len(processed_data)}")
        else:
            print("❌ No se pudieron procesar los datos del SENAMHI.")
    else:
        print("❌ No se pudieron descargar los datos del SENAMHI.")
