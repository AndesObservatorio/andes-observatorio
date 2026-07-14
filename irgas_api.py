[1mdiff --git a/sirgas_api.py b/sirgas_api.py[m
[1mindex 65362a5..09d9df6 100644[m
[1m--- a/sirgas_api.py[m
[1m+++ b/sirgas_api.py[m
[36m@@ -1,127 +1,146 @@[m
[31m-from datetime import datetime, date[m
[31m-from typing import List, Dict, Optional[m
[31m-[m
[31m-from fastapi import FastAPI, Depends, HTTPException, Query[m
[32m+[m[32mfrom fastapi import FastAPI, HTTPException, Query[m
 from fastapi.middleware.cors import CORSMiddleware[m
[31m-from sqlalchemy.orm import Session[m
[31m-import uvicorn[m
[31m-[m
[31m-from sirgas_processor import SirgasProcessor[m
[31m-from db.database import get_db, init_db[m
[31m-from db.models import Station, TropoObservation[m
[32m+[m[32mfrom fastapi.responses import JSONResponse[m
[32m+[m[32mimport sqlite3[m
[32m+[m[32mimport os[m
[32m+[m[32mfrom datetime import datetime, timedelta[m
[32m+[m[32mfrom typing import Optional, List[m
 [m
[31m-app = FastAPI([m
[31m-    title="Andes Observatorio - Geodesic API",[m
[31m-    description="API para proveer datos de velocidades y parámetros troposféricos (ZTD) de estaciones SIRGAS-CON",[m
[31m-    version="1.1.0"[m
[31m-)[m
[32m+[m[32mapp = FastAPI(title="Andes Observatorio - API Geodésica")[m
 [m
[32m+[m[32m# Configurar CORS para permitir solicitudes desde el dashboard[m
 app.add_middleware([m
     CORSMiddleware,[m
     allow_origins=["*"],[m
[31m-    allow_credentials=True,[m
     allow_methods=["*"],[m
     allow_headers=["*"],[m
 )[m
 [m
[31m-processor = SirgasProcessor()[m
[31m-[m
[31m-@app.get("/api/v1/geodesia/velocidades", response_model=List[Dict])[m
[31m-async def get_velocidades():[m
[31m-    data = processor.get_geodesic_data()[m
[31m-    return data[m
[31m-[m
[31m-@app.get("/api/v1/geodesia/estacion/{station_id}")[m
[31m-async def get_estacion(station_id: str):[m
[31m-    data = processor.get_geodesic_data()[m
[31m-    station = next((s for s in data if s["id"].upper() == station_id.upper()), None)[m
[31m-    if station:[m
[31m-        return station[m
[31m-    return {"error": "Estación no encontrada"}[m
[31m-[m
[31m-@app.on_event("startup")[m
[31m-def on_startup():[m
[31m-    # Crea las tablas si no existen (no falla si la base ya está migrada)[m
[31m-    init_db()[m
[32m+[m[32m# Ruta a la base de datos[m
[32m+[m[32mDB_PATH = os.path.join(os.path.dirname(__file__), "db", "sirgas_tropo.db")[m
 [m
[32m+[m[32mdef get_db_connection():[m
[32m+[m[32m    """Establece conexión con la base de datos SQLite"""[m
[32m+[m[32m    if not os.path.exists(DB_PATH):[m
[32m+[m[32m        return None[m
[32m+[m[32m    conn = sqlite3.connect(DB_PATH)[m
[32m+[m[32m    conn.row_factory = sqlite3.Row[m
[32m+[m[32m    return conn[m
 [m
[31m-@app.get("/api/v1/geodesia/tropo/estaciones")[m
[31m-async def listar_estaciones_tropo(db: Session = Depends(get_db)):[m
[31m-    """Lista las estaciones que tienen al menos una observación troposférica (ZTD) cargada."""[m
[31m-    stations = ([m
[31m-        db.query(Station)[m
[31m-        .join(TropoObservation, TropoObservation.station_id == Station.id)[m
[31m-        .distinct()[m
[31m-        .all()[m
[31m-    )[m
[31m-    return [[m
[31m-        {[m
[31m-            "codigo": s.code,[m
[31m-            "domes": s.domes_number,[m
[31m-            "pos_x": s.pos_x, "pos_y": s.pos_y, "pos_z": s.pos_z,[m
[32m+[m[32m@app.get("/")[m
[32m+[m[32masync def root():[m
[32m+[m[32m    return {[m
[32m+[m[32m        "message": "Andes Observatorio - API Geodésica",[m
[32m+[m[32m        "version": "1.0",[m
[32m+[m[32m        "endpoints": {[m
[32m+[m[32m            "/api/v1/geodesia/velocidades": "Velocidades de estaciones SIRGAS",[m
[32m+[m[32m            "/api/v1/geodesia/estacion/{id}": "Datos de una estación específica",[m
[32m+[m[32m            "/api/v1/geodesia/tropo/estaciones": "Lista de estaciones con datos troposféricos",[m
[32m+[m[32m            "/api/v1/geodesia/tropo/{codigo}/serie": "Serie histórica de ZTD para una estación"[m
         }[m
[31m-        for s in stations[m
[31m-    ][m
[31m-[m
[31m-[m
[31m-@app.get("/api/v1/geodesia/tropo/{codigo_estacion}/serie")[m
[31m-async def serie_troposferica([m
[31m-    codigo_estacion: str,[m
[31m-    desde: Optional[date] = Query(None, description="Fecha inicial (YYYY-MM-DD)"),[m
[31m-    hasta: Optional[date] = Query(None, description="Fecha final (YYYY-MM-DD)"),[m
[31m-    limite: int = Query(1000, le=10000, description="Máximo de registros a devolver"),[m
[31m-    db: Session = Depends(get_db),[m
[31m-):[m
[31m-    """Serie histórica de ZTD (retardo troposférico cenital) para una estación."""[m
[31m-    station = db.query(Station).filter_by(code=codigo_estacion.upper()).one_or_none()[m
[31m-    if station is None:[m
[31m-        raise HTTPException(status_code=404, detail=f"Estación '{codigo_estacion}' no encontrada")[m
[31m-[m
[31m-    q = db.query(TropoObservation).filter(TropoObservation.station_id == station.id)[m
[31m-    if desde:[m
[31m-        q = q.filter(TropoObservation.epoch >= datetime.combine(desde, datetime.min.time()))[m
[31m-    if hasta:[m
[31m-        q = q.filter(TropoObservation.epoch <= datetime.combine(hasta, datetime.max.time()))[m
[31m-[m
[31m-    observations = q.order_by(TropoObservation.epoch.asc()).limit(limite).all()[m
[32m+[m[32m    }[m
 [m
[32m+[m[32m@app.get("/api/v1/geodesia/velocidades")[m
[32m+[m[32masync def get_velocidades():[m
[32m+[m[32m    """Endpoint para obtener velocidades de estaciones (simulado por ahora)"""[m
     return {[m
[31m-        "estacion": codigo_estacion.upper(),[m
[31m-        "cantidad": len(observations),[m
[31m-        "serie": [[m
[31m-            {[m
[31m-                "epoch": o.epoch.isoformat(),[m
[31m-                "ztd_total_mm": o.ztd_total_mm,[m
[31m-                "ztd_stddev_mm": o.ztd_stddev_mm,[m
[31m-                "ztd_dry_mm": o.ztd_dry_mm,[m
[31m-                "ztd_wet_mm": o.ztd_wet_mm,[m
[31m-                "gradient_north_mm": o.gradient_north_mm,[m
[31m-                "gradient_east_mm": o.gradient_east_mm,[m
[31m-                "iwv_kg_m2": o.iwv_kg_m2,[m
[31m-            }[m
[31m-            for o in observations[m
[31m-        ],[m
[31m-        "cita_requerida": ([m
[31m-            "Mackern M.V., Mateo M.L., Camisay M.F., Morichetti P.V. (2020). "[m
[31m-            "Tropospheric Products from High-Level GNSS Processing in Latin America. "[m
[31m-            "IAG Symposia Series, Vol 152. doi: 10.1007/1345_2020_121"[m
[31m-        ),[m
[32m+[m[32m        "estaciones": [[m
[32m+[m[32m            {"codigo": "BOGT", "velocidad_norte": 12.3, "velocidad_este": -15.7, "velocidad_up": 2.1},[m
[32m+[m[32m            {"codigo": "QUIT", "velocidad_norte": 8.5, "velocidad_este": -10.2, "velocidad_up": 1.5}[m
[32m+[m[32m        ][m
     }[m
 [m
[31m-[m
[31m-@app.get("/")[m
[31m-async def root():[m
[32m+[m[32m@app.get("/api/v1/geodesia/estacion/{codigo}")[m
[32m+[m[32masync def get_estacion(codigo: str):[m
[32m+[m[32m    """Obtener datos de una estación específica"""[m
     return {[m
[31m-        "message": "Andes Observatorio - Geodesic API",[m
[31m-        "status": "active",[m
[31m-        "endpoints": [[m
[31m-            "/api/v1/geodesia/velocidades",[m
[31m-            "/api/v1/geodesia/estacion/{id}",[m
[31m-            "/api/v1/geodesia/tropo/estaciones",[m
[31m-            "/api/v1/geodesia/tropo/{codigo_estacion}/serie",[m
[31m-        ],[m
[32m+[m[32m        "codigo": codigo,[m
[32m+[m[32m        "nombre": f"Estación {codigo}",[m
[32m+[m[32m        "lat": 4.7110,[m
[32m+[m[32m        "lon": -74.0721[m
     }[m
 [m
[32m+[m[32m@app.get("/api/v1/geodesia/tropo/estaciones")[m
[32m+[m[32masync def get_estaciones_tropo():[m
[32m+[m[32m    """Lista todas las estaciones con datos troposféricos disponibles"""[m
[32m+[m[32m    conn = get_db_connection()[m
[32m+[m[32m