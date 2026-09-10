#!/usr/bin/env python3
"""
Descarga precipitación mensual CHIRPS para la región andina.
Nueva estructura: by_month/chirps-v2.0.AAAA.MM.days_p05.nc
"""
import os
import requests
from datetime import datetime
import sys

BASE_URL = "https://data.chc.ucsb.edu/products/CHIRPS-2.0/global_daily/netcdf/p05/by_month/"
OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "chirps")
os.makedirs(OUT_DIR, exist_ok=True)

def descargar_mes(anio, mes):
    archivo = f"chirps-v2.0.{anio}.{mes:02d}.days_p05.nc"
    destino = os.path.join(OUT_DIR, archivo)
    if os.path.exists(destino):
        print(f"✓ Ya existe: {archivo}")
        return destino
    url = BASE_URL + archivo
    print(f"⬇️  Descargando {archivo} (~90 MB)...")
    try:
        r = requests.get(url, stream=True, timeout=300)
        if r.status_code != 200:
            print(f"✗ Error {r.status_code}")
            return None
        with open(destino, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"✓ Guardado: {destino}")
        return destino
    except Exception as e:
        print(f"✗ Error: {e}")
        return None

def main():
    if len(sys.argv) == 3:
        anio = int(sys.argv[1])
        mes = int(sys.argv[2])
    else:
        # Por defecto: mes anterior al actual
        hoy = datetime.now()
        if hoy.month == 1:
            anio = hoy.year - 1
            mes = 12
        else:
            anio = hoy.year
            mes = hoy.month - 1
    descargar_mes(anio, mes)

if __name__ == "__main__":
    main()
