#!/usr/bin/env python3
"""Convierte CHIRPS NetCDF a GeoJSON optimizado para Leaflet."""
import xarray as xr
import numpy as np
import json
import os
import sys

nc_path = sys.argv[1] if len(sys.argv) > 1 else None
if not nc_path:
    print("Uso: python procesar_chirps.py <archivo.nc>")
    sys.exit(1)

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "geojson")
os.makedirs(OUT_DIR, exist_ok=True)

print(f"📂 Abriendo {nc_path}...")
ds = xr.open_dataset(nc_path)
var = list(ds.data_vars)[0]

# Recorte región andina
ds_andes = ds.sel(
    latitude=slice(-60, 15),
    longitude=slice(-90, -30)
)

# PROMEDIO MENSUAL: reducimos la resolución tomando cada 10 puntos
# (0.5° → 5° = ~500 km, suficiente para visualización regional)
ds_sub = ds_andes.isel(
    latitude=slice(None, None, 10),
    longitude=slice(None, None, 10)
)

print(f"Grid submuestreado: {ds_sub.sizes.get('latitude', 0)} x {ds_sub.sizes.get('longitude', 0)}")

arr = ds_sub[var].mean(dim="time").values
lats = ds_sub["latitude"].values
lons = ds_sub["longitude"].values

features = []
for i, lat in enumerate(lats):
    for j, lon in enumerate(lons):
        val = float(arr[i, j])
        if np.isnan(val) or val <= 0:
            continue
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [float(lon), float(lat)]},
            "properties": {"precip_mm": round(val, 1)}
        })

nombre = os.path.basename(nc_path).replace(".nc", ".geojson")
salida = os.path.join(OUT_DIR, nombre)
with open(salida, "w") as f:
    json.dump({"type": "FeatureCollection", "features": features}, f)

# Tamaño del archivo
tamano_mb = os.path.getsize(salida) / 1024 / 1024
print(f"✅ {salida} ({len(features)} puntos, {tamano_mb:.1f} MB)")
