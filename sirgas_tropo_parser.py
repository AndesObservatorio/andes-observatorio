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
FIELD_MAP = {
    "TROTOT": "ztd_total_mm",
    "STDDEV": "ztd_stddev_mm",
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
    Convierte una época SINEX a datetime UTC. Soporta dos formatos:
      Formato 1: '20:350:00000' -> 2020-12-15 (año 2 dígitos)
      Formato 2: '2025:350:00000' -> 2025-12-15 (año 4 dígitos)
    """
    try:
        parts = epoch_str.split(":")
        if len(parts) != 3:
            return None
        
        y, ddd, sssss = parts
        year = int(y)
        
        # Si el año tiene 4 dígitos, usarlo directamente
        if len(y) == 4:
            pass  # year ya es correcto
        else:
            # Si tiene 2 dígitos, aplicar la convención SINEX
            if year >= 70:
                year += 1900
            else:
                year += 2000
        
        base = datetime(year, 1, 1) + timedelta(days=int(ddd) - 1)
        return base + timedelta(seconds=int(sssss))
    except (ValueError, AttributeError) as e:
        logger.warning(f"Error parseando fecha '{epoch_str}': {e}")
        return None


def _extract_station_code(raw_code: str) -> str:
    """Normaliza el código de estación a 4 caracteres."""
    raw_code = raw_code.strip()
    if len(raw_code) == 9 and raw_code[:4].isalpha() and raw_code[4:6].isdigit():
        return raw_code[:4].upper()
    return raw_code[:4].upper() if len(raw_code) >= 4 else raw_code.upper()


def _extract_block(lines: List[str], block_name: str) -> List[str]:
    """Extrae las líneas de contenido entre +BLOCK_NAME y -BLOCK_NAME."""
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
    """Extrae la última línea de comentario dentro de un bloque."""
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
    """Determina el orden real de columnas en +TROP/SOLUTION."""
    solution_header = _extract_block_header(lines, "TROP/SOLUTION")
    if solution_header:
        parts = solution_header.lstrip("*").split()
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
            idx = next((i for i, p in enumerate(parts) if p.upper() == "NAMES"), None)
            if idx is not None:
                return parts[idx + 1:]

    logger.warning("No se encontró el orden de columnas; se usará orden por defecto")
    return ["TROTOT", "STDDEV", "TRODRY", "TROWET", "TGNTOT", "STDDEV", "TGETOT", "STDDEV"]


def parse_tro_file(path: str) -> Dict:
    """Parsea un archivo SINEX TRO completo."""
    with _open_text(path) as f:
        lines = f.readlines()

    result = {"stations": {}, "observations": []}

    # Estaciones: SITE/ID
    for line in _extract_block(lines, "SITE/ID"):
        parts = line.split()
        if len(parts) >= 3:
            code = _extract_station_code(parts[0])
            domes = parts[2]
            result["stations"].setdefault(code, {})["domes"] = domes

    # Estaciones: TROP/STA_COORDINATES
    for line in _extract_block(lines, "TROP/STA_COORDINATES"):
        parts = line.split()
        if len(parts) < 4:
            continue
        code = _extract_station_code(parts[0])
        numeric_values = []
        for token in parts[1:]:
            try:
                numeric_values.append(float(token))
            except ValueError:
                if len(numeric_values) >= 3:
                    break
                continue
        if len(numeric_values) >= 3:
            x, y, z = numeric_values[-3:]
            result["stations"].setdefault(code, {}).update({"x": x, "y": y, "z": z})

    # Orden de columnas
    field_order = _parse_field_order(lines)

    # Observaciones: TROP/SOLUTION
    solution_lines = _extract_block(lines, "TROP/SOLUTION")
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
                stddev_seen += 1
                if stddev_seen == 1:
                    obs["ztd_stddev_mm"] = value
                continue

            target = FIELD_MAP.get(field_name)
            if target:
                obs[target] = value

        result["observations"].append(obs)

    return result
