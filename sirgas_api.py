from fastapi import FastAPI
from sirgas_processor import SirgasProcessor
from typing import List, Dict
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(
    title="Andes Observatorio - Geodesic API",
    description="API para proveer datos de velocidades de estaciones SIRGAS-CON",
    version="1.0.0"
)

# Configurar CORS para permitir peticiones desde el dashboard
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
    """
    Retorna las velocidades de las estaciones SIRGAS-CON procesadas.
    Estos datos son consumidos por el componente de mapa para dibujar vectores.
    """
    data = processor.get_geodesic_data()
    return data

@app.get("/api/v1/geodesia/estacion/{station_id}")
async def get_estacion(station_id: str):
    """
    Retorna los detalles de una estación geodésica específica.
    """
    data = processor.get_geodesic_data()
    station = next((s for s in data if s["id"].upper() == station_id.upper()), None)
    if station:
        return station
    return {"error": "Estación no encontrada"}

@app.get("/")
async def root():
    return {"message": "Andes Observatorio - Geodesic API", "status": "active", "endpoints": ["/api/v1/geodesia/velocidades", "/api/v1/geodesia/estacion/{id}"]}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
