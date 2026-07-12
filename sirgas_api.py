from datetime import datetime, date
from typing import List, Dict, Optional

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import uvicorn

from sirgas_processor import SirgasProcessor
from db.database import get_db, init_db
from db.models import Station, TropoObservation

app = FastAPI(
    title="Andes Observatorio - Geodesic API",
    description="API para proveer datos de velocidades y parámetros troposféricos (ZTD) de estaciones SIRGAS-CON",
    version="1.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

processor = SirgasProcessor()

@app.get("/api/v1/geodesia/velocidades", response_model=List[Dict])
async def get_velocidades():
    data = processor.get_geodesic_data()
    return data

@app.get("/api/v1/geodesia/estacion/{station_id}")
async def get_estacion(station_id: str):
    data = processor.get_geodesic_data()
    station = next((s for s in data if s["id"].upper() == station_id.upper()), None)
    if station:
        return station
    return {"error": "Estación no encontrada"}

@app.on_event("startup")
def on_startup():
    # Crea las tablas si no existen (no falla si la base ya está migrada)
    init_db()


@app.get("/api/v1/geodesia/tropo/estaciones")
async def listar_estaciones_tropo(db: Session = Depends(get_db)):
    """Lista las estaciones que tienen al menos una observación troposférica (ZTD) cargada."""
    stations = (
        db.query(Station)
        .join(TropoObservation, TropoObservation.station_id == Station.id)
        .distinct()
        .all()
    )
    return [
        {
            "codigo": s.code,
            "domes": s.domes_number,
            "pos_x": s.pos_x, "pos_y": s.pos_y, "pos_z": s.pos_z,
        }
        for s in stations
    ]


@app.get("/api/v1/geodesia/tropo/{codigo_estacion}/serie")
async def serie_troposferica(
    codigo_estacion: str,
    desde: Optional[date] = Query(None, description="Fecha inicial (YYYY-MM-DD)"),
    hasta: Optional[date] = Query(None, description="Fecha final (YYYY-MM-DD)"),
    limite: int = Query(1000, le=10000, description="Máximo de registros a devolver"),
    db: Session = Depends(get_db),
):
    """Serie histórica de ZTD (retardo troposférico cenital) para una estación."""
    station = db.query(Station).filter_by(code=codigo_estacion.upper()).one_or_none()
    if station is None:
        raise HTTPException(status_code=404, detail=f"Estación '{codigo_estacion}' no encontrada")

    q = db.query(TropoObservation).filter(TropoObservation.station_id == station.id)
    if desde:
        q = q.filter(TropoObservation.epoch >= datetime.combine(desde, datetime.min.time()))
    if hasta:
        q = q.filter(TropoObservation.epoch <= datetime.combine(hasta, datetime.max.time()))

    observations = q.order_by(TropoObservation.epoch.asc()).limit(limite).all()

    return {
        "estacion": codigo_estacion.upper(),
        "cantidad": len(observations),
        "serie": [
            {
                "epoch": o.epoch.isoformat(),
                "ztd_total_mm": o.ztd_total_mm,
                "ztd_stddev_mm": o.ztd_stddev_mm,
                "ztd_dry_mm": o.ztd_dry_mm,
                "ztd_wet_mm": o.ztd_wet_mm,
                "gradient_north_mm": o.gradient_north_mm,
                "gradient_east_mm": o.gradient_east_mm,
                "iwv_kg_m2": o.iwv_kg_m2,
            }
            for o in observations
        ],
        "cita_requerida": (
            "Mackern M.V., Mateo M.L., Camisay M.F., Morichetti P.V. (2020). "
            "Tropospheric Products from High-Level GNSS Processing in Latin America. "
            "IAG Symposia Series, Vol 152. doi: 10.1007/1345_2020_121"
        ),
    }


@app.get("/")
async def root():
    return {
        "message": "Andes Observatorio - Geodesic API",
        "status": "active",
        "endpoints": [
            "/api/v1/geodesia/velocidades",
            "/api/v1/geodesia/estacion/{id}",
            "/api/v1/geodesia/tropo/estaciones",
            "/api/v1/geodesia/tropo/{codigo_estacion}/serie",
        ],
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)

