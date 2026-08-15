#!/usr/bin/env python3
"""
API simulada de SIRGAS para Andes Observatorio
Ejecutar: python3 api_sirgas.py
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import random
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)  # Permitir peticiones desde el frontend

# Datos base de estaciones (25 estaciones)
ESTACIONES = [
    {"id": "BOGT", "lat": 4.6400, "lon": -74.0800, "ve": 2.1, "vn": 1.8, "ztd": 2150, "alt": 2640, "pais": "Colombia"},
    {"id": "BUGA", "lat": 3.9000, "lon": -76.3000, "ve": 1.9, "vn": 1.6, "ztd": 2200, "alt": 1800, "pais": "Colombia"},
    {"id": "PERE", "lat": 4.8000, "lon": -75.7000, "ve": 2.0, "vn": 1.7, "ztd": 2180, "alt": 1600, "pais": "Colombia"},
    {"id": "QUIT", "lat": -0.1800, "lon": -78.4700, "ve": 1.5, "vn": 1.2, "ztd": 2080, "alt": 2850, "pais": "Ecuador"},
    {"id": "GUAY", "lat": -2.1700, "lon": -79.9200, "ve": 1.3, "vn": 1.0, "ztd": 2250, "alt": 100, "pais": "Ecuador"},
    {"id": "LIMA", "lat": -12.0400, "lon": -77.0400, "ve": 3.0, "vn": 2.5, "ztd": 1950, "alt": 150, "pais": "Perú"},
    {"id": "AREQ", "lat": -16.4000, "lon": -71.5300, "ve": 1.2, "vn": 0.9, "ztd": 1980, "alt": 2335, "pais": "Perú"},
    {"id": "CUZC", "lat": -13.5300, "lon": -71.9700, "ve": 1.8, "vn": 1.4, "ztd": 1900, "alt": 3400, "pais": "Perú"},
    {"id": "LPBZ", "lat": -16.5000, "lon": -68.1500, "ve": 0.8, "vn": 1.0, "ztd": 1850, "alt": 3640, "pais": "Bolivia"},
    {"id": "SANT", "lat": -33.4500, "lon": -70.6600, "ve": 1.8, "vn": 1.5, "ztd": 1750, "alt": 570, "pais": "Chile"},
    {"id": "ANTC", "lat": -23.7800, "lon": -70.5500, "ve": 2.2, "vn": 1.9, "ztd": 1900, "alt": 200, "pais": "Chile"},
    {"id": "BUEN", "lat": -34.6000, "lon": -58.3800, "ve": 1.0, "vn": 0.8, "ztd": 1900, "alt": 50, "pais": "Argentina"}
]

@app.route('/api/estaciones', methods=['GET'])
def get_estaciones():
    """Devuelve todas las estaciones con sus velocidades y ZTD"""
    return jsonify({
        "total": len(ESTACIONES),
        "estaciones": ESTACIONES,
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/estaciones/<id>', methods=['GET'])
def get_estacion(id):
    """Devuelve una estación específica"""
    estacion = next((e for e in ESTACIONES if e["id"] == id), None)
    if estacion:
        return jsonify(estacion)
    return jsonify({"error": "Estación no encontrada"}), 404

@app.route('/api/series/<id>', methods=['GET'])
def get_series(id):
    """Devuelve serie temporal de ZTD para una estación"""
    estacion = next((e for e in ESTACIONES if e["id"] == id), None)
    if not estacion:
        return jsonify({"error": "Estación no encontrada"}), 404
    
    # Generar 30 días de datos con variación
    datos = []
    base = estacion["ztd"]
    for i in range(30, -1, -1):
        fecha = datetime.now() - timedelta(days=i)
        valor = base + (random.random() - 0.5) * 40
        datos.append({
            "fecha": fecha.isoformat(),
            "ztd": round(valor, 1)
        })
    
    return jsonify({
        "estacion": id,
        "datos": datos,
        "total": len(datos)
    })

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "service": "SIRGAS API"})

if __name__ == '__main__':
    print("🚀 API SIRGAS corriendo en http://localhost:5000")
    print("📊 Endpoints:")
    print("   GET /api/estaciones  - Todas las estaciones")
    print("   GET /api/estaciones/<id> - Estación específica")
    print("   GET /api/series/<id> - Serie ZTD")
    print("   GET /api/health - Health check")
    app.run(host='0.0.0.0', port=5000, debug=True)
