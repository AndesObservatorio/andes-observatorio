"""
Configuración de estaciones GNSS/SIRGAS para Andes Observatorio.

Este módulo centraliza QUÉ estaciones procesa el pipeline troposférico
(sirgas_tropo_fetcher.py / sirgas_tropo_ingest.py), para no tener que tocar
la lógica de descarga o parseo cuando se quiera cambiar la cobertura.

Hoy: solo las estaciones que ya muestra el dashboard de Andes Observatorio
     (región andina: Colombia, Ecuador, Perú, Bolivia, Chile, Argentina).
Más adelante: agregar más regiones (o pasar a cobertura global de SIRGAS-CON)
     es tan simple como sumar entradas a REGIONES o usar scope="global"
     en get_active_stations(), sin tocar ningún otro archivo del pipeline.
"""

from typing import Dict, List, Optional

# Estaciones actualmente visibles en el dashboard (dashboard.html / sirgas_processor.py),
# con sus coordenadas aproximadas de referencia (lon, lat) para mostrar en mapas si se necesita.
REGIONES: Dict[str, List[Dict]] = {
    "andes": [
        {"id": "BOGT", "pais": "Colombia", "lon": -74.08, "lat": 4.64},
        {"id": "BOG2", "pais": "Colombia", "lon": -74.08, "lat": 4.64},
        {"id": "CALI", "pais": "Colombia", "lon": -76.53, "lat": 3.45},
        {"id": "QUIT", "pais": "Ecuador", "lon": -78.50, "lat": -0.18},
        {"id": "LIMA", "pais": "Perú", "lon": -77.03, "lat": -12.04},
        {"id": "AREQ", "pais": "Perú", "lon": -71.53, "lat": -16.40},
        {"id": "CUZ1", "pais": "Perú", "lon": -71.97, "lat": -13.52},
        {"id": "LPBZ", "pais": "Bolivia", "lon": -68.12, "lat": -16.50},
        {"id": "SANT", "pais": "Chile", "lon": -70.66, "lat": -33.45},
        {"id": "ANTC", "pais": "Chile", "lon": -70.55, "lat": -23.78},
        {"id": "CONZ", "pais": "Chile", "lon": -72.98, "lat": -36.83},
        {"id": "MEND", "pais": "Argentina", "lon": -68.83, "lat": -32.89},
    ],
    # --- Ejemplo de cómo se vería agregar otra región en el futuro, sin tocar nada más ---
    # "centroamerica": [
    #     {"id": "PMSA", "pais": "Panamá", "lon": -79.55, "lat": 8.98},
    #     {"id": "SSIA", "pais": "Costa Rica", "lon": -84.14, "lat": 9.93},
    # ],
}


def get_active_stations(scope: str = "andes") -> Optional[List[str]]:
    """
    Devuelve la lista de códigos de estación activos según el alcance (scope) pedido.

    scope="andes"  -> solo las estaciones del dashboard actual (default)
    scope="global" -> None, que en fetch_range()/ingest.py significa
                      "sin filtro", es decir: TODAS las estaciones de SIRGAS-CON
    scope=<nombre de una región definida en REGIONES> -> esa región puntual

    Para agregar cobertura global more adelante no hay que cambiar esta función:
    ya soporta scope="global" desde ahora. Solo hay que decidir correrlo así.
    """
    if scope == "global":
        return None
    if scope not in REGIONES:
        raise ValueError(
            f"Región desconocida: '{scope}'. Opciones disponibles: "
            f"{list(REGIONES.keys()) + ['global']}"
        )
    return [s["id"] for s in REGIONES[scope]]


def get_station_metadata(scope: str = "andes") -> List[Dict]:
    """Devuelve la lista completa de metadatos (id, país, lon, lat) de una región."""
    if scope not in REGIONES:
        raise ValueError(f"Región desconocida: '{scope}'")
    return REGIONES[scope]

