from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import os
from typing import Optional

app = FastAPI(title="Andes Observatorio - API Geodésica")

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
                COUNT(*) AS total_registros,
                MIN(t.epoch) AS primera_fecha,
                MAX(t.epoch) AS ultima_fecha
            FROM tropo_observations t
            JOIN stations s ON s.id = t.station_id
            GROUP BY s.code
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
