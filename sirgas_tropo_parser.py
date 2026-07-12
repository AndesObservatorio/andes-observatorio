"""
Parser del formato SINEX TRO (troposférico) usado por SIRGAS.

Estrategia clave: el orden de las columnas dentro del bloque +TROP/SOLUTION
NO es fijo entre archivos (distintos Centros de Análisis pueden reportar
distintos parámetros y en distinto orden). Por eso este parser primero lee
el bloque +TROP/DESCRIPTION -> "SOLUTION FIELDS" para saber el orden real
de columnas de ESE archivo en particular, y recién después parsea
+TROP/SOLUTION usando ese mapeo. Asumir posiciones fijas (como hace el
parser actual de velocidades) sería frágil y rompería silenciosamente
si un Centro de Análisis cambia el formato.

Bloques relevantes:
  +SITE/ID            -> código de estación, DOMES, coordenadas aproximadas
  +TROP/STACOORDINATES -> coordenadas cartesianas (ITRF) usadas en el ajuste
  +TROP/DESCRIPTION    -> qué columnas trae +TROP/SOLUTION y en qué orden
  +TROP/SOLUTION       -> los datos: estación, época, y los valores de columna
"""

import gzip
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# Nombres de columna del bloque TROP/SOLUTION que nos interesa mapear a nuestro esquema.
# (hay más columnas posibles como NSAT, GDOP, PRESS, etc. que ignoramos por ahora)
FIELD_MAP = {
    "TROTOT": "ztd_total_mm",
    "STDDEV": "ztd_stddev_mm",   # nota: STDDEV aparece más de una vez en algunos archivos;
                                 # nos quedamos con la que sigue inmediatamente a TROTOT
    "TRODRY": "ztd_dry_mm",
    "TROWET": "ztd_wet_mm",
    "TGNTOT": "gradient_north_mm",
    "TGETOT": "gradient_east_mm",
    "IWV": "iwv_kg_m2",
}


def _open_text(path: str):
    if path.endswith(".gz"):
        return gzip.open(path, "rt", encoding="latin-1")
    return open(path, "r", encoding="latin-1")


def _sinex_epoch_to_datetime(epoch_str: str) -> Optional[datetime]:
    """
    Convierte una época SINEX a datetime UTC. Soporta dos formatos confirmados
    en archivos reales de SIRGAS:
      Legacy (hasta ~2022?): 'yy:ddd:sssss'   año 2 dígitos, ej. '20:350:00000' -> 2020-12-15
      Actual (2026 en adelante): 'yyyy:ddd:sssss' año 4 dígitos, ej. '2026:157:00000' -> 2026-06-06
    """
    try:
        y, ddd, sssss = epoch_str.split(":")
        if len(y) == 4:
            year = int(y)
        else:
            year = int(y)
            year += 2000 if year < 80 else 1900  # convención SINEX estándar para año de 2 dígitos
        base = datetime(year, 1, 1) + timedelta(days=int(ddd) - 1)
        return base + timedelta(seconds=int(sssss))
    except (ValueError, AttributeError):
        return None


def _extract_station_code(raw_code: str) -> str:
    """
    Normaliza el código de estación a 4 caracteres, soportando ambos formatos:
      Legacy: ya viene como 4 caracteres (ej. 'AACR')
      Actual: viene como 9 caracteres ESTACION+MONUMENTO+PAIS (ej. 'ANTC00CHL' -> 'ANTC')
    """
    raw_code = raw_code.strip()
    if len(raw_code) == 9 and raw_code[:4].isalpha() and raw_code[4:6].isdigit():
        return raw_code[:4].upper()
    return raw_code[:4].upper() if len(raw_code) >= 4 else raw_code.upper()


def _extract_block(lines: List[str], block_name: str) -> List[str]:
    """Extrae las líneas de contenido entre +BLOCK_NAME y -BLOCK_NAME (sin los headers ni comentarios '*')."""
    start_tag = f"+{block_name}"
    end_tag = f"-{block_name}"
    content = []
    inside = False
    for line in lines:
        if line.startswith(start_tag):
            inside = True
            continue
        if line.startswith(end_tag):
            break
        if inside and not line.startswith("*"):
            content.append(line.rstrip("\n"))
    return content


def _extract_block_header(lines: List[str], block_name: str) -> Optional[str]:
    """
    Extrae la última línea de comentario ('*...') dentro de un bloque antes de
    los datos -- es el encabezado real de la tabla (ej. '*SITE ___EPOCH___ TROTOT STDDEV #T').
    Es más confiable que una etiqueta separada en TROP/DESCRIPTION porque
    siempre coincide exactamente con las columnas que realmente vienen después.
    """
    start_tag = f"+{block_name}"
    end_tag = f"-{block_name}"
    inside = False
    last_header = None
    for line in lines:
        if line.startswith(start_tag):
            inside = True
            continue
        if line.startswith(end_tag):
            break
        if inside and line.startswith("*"):
            last_header = line.rstrip("\n")
    return last_header


def _parse_field_order(lines: List[str]) -> List[str]:
    """
    Determina el orden real de columnas de datos en +TROP/SOLUTION (después de
    estación+época). Dos estrategias, en orden de confiabilidad:

    1. Leer el encabezado de comentario de la propia tabla +TROP/SOLUTION
       (ej. '*SITE ___EPOCH___ TROTOT STDDEV #T') -- siempre coincide exactamente
       con las columnas de datos que le siguen, sin importar qué etiqueta se
       use en TROP/DESCRIPTION (que varió entre versiones de SIRGAS: se vio
       'SOLUTION_FIELDS_1' en archivos de 2020 y 'TROPO PARAMETER NAMES' en
       archivos de 2026, con distinto número de columnas listadas).
    2. Si ese encabezado no está disponible, recurre a la etiqueta en
       TROP/DESCRIPTION (soporta ambas variantes conocidas).
    """
    solution_header = _extract_block_header(lines, "TROP/SOLUTION")
    if solution_header:
        parts = solution_header.lstrip("*").split()
        # Descarta las columnas de identificación (estación y época), que
        # siempre son las primeras y contienen la palabra 'EPOCH' o son 'SITE'.
        data_fields = [p for p in parts if p.upper() != "SITE" and "EPOCH" not in p.upper()]
        if data_fields:
            return data_fields

    desc_lines = _extract_block(lines, "TROP/DESCRIPTION")
    for line in desc_lines:
        cleaned = line.strip()
        parts = cleaned.split()
        if not parts:
            continue
        first_normalized = parts[0].upper().replace("_", " ")
        if first_normalized.startswith("SOLUTION FIELDS"):
            return parts[1:]
        if len(parts) >= 2 and parts[0].upper() == "SOLUTION" and parts[1].upper().startswith("FIELDS"):
            return parts[2:]
        if first_normalized.startswith("TROPO PARAMETER NAMES"):
            # Etiqueta vista en archivos 2026: 'TROPO PARAMETER NAMES   TROTOT STDDEV ACOK'
            idx = next((i for i, p in enumerate(parts) if p.upper() == "NAMES"), None)
            if idx is not None:
                return parts[idx + 1:]

    logger.warning("No se encontró el orden de columnas; se usará orden por defecto")
    return ["TROTOT", "STDDEV", "TRODRY", "TROWET", "TGNTOT", "STDDEV", "TGETOT", "STDDEV"]


def parse_tro_file(path: str) -> Dict:
    """
    Parsea un archivo SINEX TRO completo.
    Retorna un dict:
        {
            "stations": {codigo: {"domes": ..., "x":..,"y":..,"z":..}},
            "observations": [
                {"station": codigo, "epoch": datetime, "ztd_total_mm": ..., ...},
                ...
            ]
        }
    """
    with _open_text(path) as f:
        lines = f.readlines()

    result = {"stations": {}, "observations": []}

    # --- Estaciones: SITE/ID y TROP/STA_COORDINATES ---
    # Formato real confirmado: CODE PT DOMES T STATION_DESCRIPTION... APPROX_LON APPROX_LAT APP_H
    # (el DOMES está en la posición 2, no en la 1 -- antes va la columna PT)
    # CODE puede venir como 4 caracteres (legacy) o 9 caracteres ESTACION+MONUMENTO+PAIS (2026+)
    for line in _extract_block(lines, "SITE/ID"):
        parts = line.split()
        if len(parts) >= 3:
            code = _extract_station_code(parts[0])
            domes = parts[2]
            result["stations"].setdefault(code, {})["domes"] = domes

    for line in _extract_block(lines, "TROP/STA_COORDINATES"):
        parts = line.split()
        if len(parts) < 4:
            continue
        code = _extract_station_code(parts[0])
        # Las columnas finales (SYSTEM, REMRK) no son numéricas; se buscan las 3
        # primeras columnas numéricas consecutivas de izquierda a derecha después
        # del código de estación y el número de soln, en vez de asumir posición fija.
        numeric_values = []
        for token in parts[1:]:
            try:
                numeric_values.append(float(token))
            except ValueError:
                if len(numeric_values) >= 3:
                    break  # ya encontramos X,Y,Z; lo que sigue no nos interesa
                continue
        if len(numeric_values) >= 3:
            x, y, z = numeric_values[-3:]
            result["stations"].setdefault(code, {}).update({"x": x, "y": y, "z": z})

    # --- Orden de columnas de este archivo en particular ---
    field_order = _parse_field_order(lines)

    # --- Observaciones: TROP/SOLUTION ---
    solution_lines = _extract_block(lines, "TROP/SOLUTION")
    seen_stddev_count = 0
    for line in solution_lines:
        parts = line.split()
        if len(parts) < 3:
            continue
        code = _extract_station_code(parts[0])
        epoch = _sinex_epoch_to_datetime(parts[1])
        if epoch is None:
            continue

        values = parts[2:]
        obs = {"station": code, "epoch": epoch}
        stddev_seen = 0
        for field_name, raw_value in zip(field_order, values):
            try:
                value = float(raw_value)
            except ValueError:
                continue

            if field_name == "STDDEV":
                # La primera STDDEV tras TROTOT es la que nos interesa (ztd_stddev_mm);
                # las siguientes (gradientes) las ignoramos por simplicidad en esta v1.
                stddev_seen += 1
                if stddev_seen == 1:
                    obs["ztd_stddev_mm"] = value
                continue

            target = FIELD_MAP.get(field_name)
            if target:
                obs[target] = value

        result["observations"].append(obs)

    return result
