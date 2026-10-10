from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import os
import requests

from typing import Optional

app = FastAPI(title="Andes Observatorio - API Geodésica")

# Rate limiting simple
from collections import defaultdict
import time
rate_limit = defaultdict(list)
RATE_LIMIT = 60  # solicitudes
RATE_WINDOW = 60  # segundos

@app.middleware("http")
async def rate_limiter(request, call_next):
    client = request.client.host if request.client else "unknown"
    now = time.time()
    rate_limit[client] = [t for t in rate_limit[client] if now - t < RATE_WINDOW]
    if len(rate_limit[client]) >= RATE_LIMIT:
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=429, content={"error": "Too many requests"})
    rate_limit[client].append(now)
    response = await call_next(request)
    return response

# Configurar CORS para permitir solicitudes desde el dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ruta real a la base de datos que genera sirgas_tropo_ingest.py
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "andes_observa.db")

def get_db_connection():
    """Establece conexión con la base de datos SQLite"""
    if not os.path.exists(DB_PATH):
        return None
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/")
@app.get("/api/config")
def get_config():
    import os
    return {"openweather_api_key": os.environ.get("OPENWEATHER_API_KEY", "")}

async def root():
    return {
        "message": "Andes Observatorio - API Geodésica",
        "version": "1.0",
        "endpoints": {
            "/api/v1/geodesia/velocidades": "Velocidades de estaciones SIRGAS",
            "/api/v1/geodesia/estacion/{id}": "Datos de una estación específica",
            "/api/v1/geodesia/tropo/estaciones": "Lista de estaciones con datos troposféricos",
            "/api/v1/geodesia/tropo/{codigo}/serie": "Serie histórica de ZTD para una estación",
        },
    }

@app.get("/api/v1/geodesia/velocidades")
async def get_velocidades():
    """Endpoint para obtener velocidades de estaciones"""
    return {
        "estaciones": [
            {"codigo": "BOGT", "velocidad_norte": 12.3, "velocidad_este": -15.7, "velocidad_up": 2.1},
            {"codigo": "QUIT", "velocidad_norte": 8.5, "velocidad_este": -10.2, "velocidad_up": 1.5},
            {"codigo": "LIMA", "velocidad_norte": 10.2, "velocidad_este": -8.5, "velocidad_up": 0.5},
            {"codigo": "LPBZ", "velocidad_norte": 15.8, "velocidad_este": -12.3, "velocidad_up": 1.2},
            {"codigo": "SANT", "velocidad_norte": 18.5, "velocidad_este": -20.1, "velocidad_up": 0.8},
            {"codigo": "RIOG", "velocidad_norte": 22.1, "velocidad_este": -15.8, "velocidad_up": 1.0},
            {"codigo": "CARI", "velocidad_norte": 7.2, "velocidad_este": -5.4, "velocidad_up": 0.3},
        ]
    }

@app.get("/api/v1/geodesia/estacion/{codigo}")
async def get_estacion(codigo: str):
    """Obtener datos de una estación específica"""
    return {
        "codigo": codigo,
        "nombre": f"Estación {codigo}",
        "lat": 4.7110,
        "lon": -74.0721,
    }

@app.get("/api/v1/geodesia/tropo/estaciones")
async def get_estaciones_tropo():
    """
    Lista todas las estaciones con datos troposféricos disponibles.
    """
    conn = get_db_connection()
    if not conn:
        return {"error": "Base de datos no encontrada", "estaciones": []}

    try:
        cursor = conn.execute("""
            SELECT
                s.code AS codigo,
                s.lat AS lat,
                s.lon AS lon,
                COUNT(*) AS total_registros,
                MIN(t.epoch) AS primera_fecha,
                MAX(t.epoch) AS ultima_fecha
            FROM tropo_observations t
            JOIN stations s ON s.id = t.station_id
            GROUP BY s.code, s.lat, s.lon
            ORDER BY s.code
        """)
        rows = cursor.fetchall()
        return {"estaciones": [dict(row) for row in rows]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/api/v1/geodesia/tropo/{codigo}/serie")
async def get_serie_tropo(
    codigo: str,
    desde: Optional[str] = Query(None, description="Fecha inicio (YYYY-MM-DD)"),
    hasta: Optional[str] = Query(None, description="Fecha fin (YYYY-MM-DD)"),
    limite: Optional[int] = Query(1000, description="Límite de registros"),
):
    """
    Obtiene la serie histórica de Retardo Troposférico Cenital (ZTD)
    para una estación específica.
    """
    conn = get_db_connection()
    if not conn:
        return {"error": "Base de datos no encontrada", "datos": []}

    try:
        query = """
            SELECT
                t.epoch AS fecha,
                t.ztd_total_mm AS valor,
                t.ztd_stddev_mm AS error,
                t.iwv_kg_m2
            FROM tropo_observations t
            JOIN stations s ON s.id = t.station_id
            WHERE s.code = ?
        """
        params = [codigo.upper()]

        if desde:
            query += " AND t.epoch >= ?"
            params.append(desde)
        if hasta:
            query += " AND t.epoch <= ?"
            params.append(hasta)

        query += " ORDER BY t.epoch ASC LIMIT ?"
        params.append(limite)

        cursor = conn.execute(query, params)
        rows = cursor.fetchall()

        if not rows:
            return {
                "estacion": codigo.upper(),
                "datos": [],
                "mensaje": f"No hay datos para la estación {codigo.upper()}",
            }

        return {
            "estacion": codigo.upper(),
            "total_registros": len(rows),
            "datos": [dict(row) for row in rows],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/api/v1/ambiental/aqi/{ciudad}")
def get_aqi(ciudad: str):
    try:
        # ═══════════════════════════════════════════════════════════
        # DICCIONARIO COMPLETO DE CIUDADES ANDINAS
        # Acepta tanto nombre largo (Bogota) como código SIRGAS (BOGT)
        # ═══════════════════════════════════════════════════════════
        CIUDADES = {
            # Colombia
            "Bogota": (4.6097, -74.0817), "BOGT": (4.6097, -74.0817),
            "BOG2": (4.6097, -74.0817),
            "Medellin": (6.2442, -75.5812),
            "Cali": (3.4516, -76.5320), "CALI": (3.4516, -76.5320),
            # Ecuador
            "Quito": (-0.1807, -78.4678), "QUIT": (-0.1807, -78.4678),
            # Perú
            "Lima": (-12.0464, -77.0428), "LIMA": (-12.0464, -77.0428),
            "Arequipa": (-16.4090, -71.5375), "AREQ": (-16.4090, -71.5375),
            "Cusco": (-13.5319, -71.9675), "CUZ1": (-13.5319, -71.9675),
            "AN02": (-12.05, -77.04),
            "AP01": (-16.4, -71.53),
            # Bolivia
            "La Paz": (-16.5000, -68.1500), "LPBZ": (-16.5000, -68.1500),
            "LPGS": (-16.5000, -68.1500),
            # Chile
            "Santiago": (-33.4489, -70.6693), "SANT": (-33.4489, -70.6693),
            "Antofagasta": (-23.6509, -70.3975), "ANTC": (-23.6509, -70.3975),
            "Concepcion": (-36.8201, -73.0444), "CONZ": (-36.8201, -73.0444),
            # Argentina
            "Mendoza": (-32.8895, -68.8458), "MEND": (-32.8895, -68.8458),
            # Venezuela
            "Caracas": (10.4806, -66.9036), "CARI": (10.4806, -66.9036),
            # Brasil
            "RioGrande": (-32.0350, -52.0986), "RIOG": (-32.0350, -52.0986),
            # Bolivia (GLPS - Galápagos es Ecuador, pero por compatibilidad)
            "GLPS": (-0.7428, -90.3156),
            # Ecuador (IQQE - Iquique es Chile)
            "IQQE": (-20.2208, -70.1408),
            # RDSD - Río de Janeiro?
            "RDSD": (-22.9068, -43.1729),
            # CS01 - sin identificar, usar Bogotá
            "CS01": (4.6097, -74.0817),
        }
        
        # Buscar coordenadas — si no existe, devolver error claro
        if ciudad not in CIUDADES:
            return {
                "ciudad": ciudad,
                "valor": "Ciudad no soportada",
                "unidad": "",
                "error": f"Ciudad '{ciudad}' no está en el catálogo. Ciudades soportadas: {len(CIUDADES)}"
            }
        
        lat, lon = CIUDADES[ciudad]
        
        # ═══════════════════════════════════════════════════════════
        # CONSULTA A OPENAQ (con timeout y mejor manejo de errores)
        # ═══════════════════════════════════════════════════════════
        API_KEY = "190380ae0610cef5dcddb05d6bf70dbbb9a3d81f37e590301273ce4911b355f5"
        headers = {"X-API-Key": API_KEY}
        
        url = f"https://api.openaq.org/v3/locations?coordinates={lat},{lon}&radius=25000&limit=1&parameter=pm25"
        r = requests.get(url, headers=headers, timeout=10)
        
        if r.status_code != 200:
            return {"ciudad": ciudad, "valor": "OpenAQ no disponible", "unidad": "", "http_status": r.status_code}
        
        data = r.json()
        if not data.get('results'):
            return {"ciudad": ciudad, "valor": "Sin estación cercana", "unidad": ""}
        
        loc = data['results'][0]
        for sensor in loc.get('sensors', []):
            if sensor['parameter']['name'] == 'pm25':
                sensor_id = sensor['id']
                url2 = f"https://api.openaq.org/v3/sensors/{sensor_id}/measurements?limit=1&parameter=pm25"
                r2 = requests.get(url2, headers=headers, timeout=10)
                d2 = r2.json()
                if d2.get('results'):
                    valor = d2['results'][0].get('value', '--')
                    return {"ciudad": ciudad, "valor": valor, "unidad": "µg/m³", "lat": lat, "lon": lon}
                return {"ciudad": ciudad, "valor": "Sin mediciones recientes", "unidad": ""}
        
        return {"ciudad": ciudad, "valor": "Ubicación sin PM2.5", "unidad": ""}
    except Exception as e:
        return {"error": str(e), "ciudad": ciudad}

@app.get("/health")
def health_check():
    return {"status": "ok", "version": "3.0", "timestamp": __import__("datetime").datetime.now().isoformat()}

@app.get("/health")
def health_check():
    import datetime
    return {"status": "ok", "version": "3.0", "timestamp": datetime.datetime.now().isoformat()}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
