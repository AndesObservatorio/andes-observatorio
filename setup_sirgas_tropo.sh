#!/bin/bash
# Script de instalación del módulo troposférico SIRGAS para Andes Observatorio
# Uso: correr desde dentro de la carpeta del repo clonado, ej:
#   cd ~/andes-observatorio && bash setup_sirgas_tropo.sh
set -e

echo "Creando estructura de carpetas..."
mkdir -p db config data/tropo_raw

echo "Creando db/__init__.py..."
touch db/__init__.py

echo "Creando config/__init__.py..."
touch config/__init__.py

echo "Creando db/database.py..."
cat > db/database.py << 'ARCHIVO_EOF'
"""
Configuración de la base de datos para Andes Observatorio.

Por defecto usa SQLite local (data/andes_observa.db), ideal para desarrollo
y para instancias pequeñas. Para producción, define la variable de entorno
DATABASE_URL apuntando a Postgres, por ejemplo:

    export DATABASE_URL="postgresql+psycopg2://usuario:password@host:5432/andes_observa"

No se requiere ningún otro cambio en el código: SQLAlchemy abstrae el dialecto.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DEFAULT_SQLITE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "andes_observa.db",
)

DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{DEFAULT_SQLITE_PATH}")

# connect_args solo es necesario para SQLite (permite uso multi-hilo con FastAPI/uvicorn)
_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=_connect_args, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()


def get_db():
    """Dependencia para FastAPI: entrega una sesión y la cierra al terminar."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Crea todas las tablas si no existen. Importa los modelos antes de llamar esto."""
    from db import models  # noqa: F401 (registra los modelos en Base.metadata)
    Base.metadata.create_all(bind=engine)

ARCHIVO_EOF

echo "Creando db/models.py..."
cat > db/models.py << 'ARCHIVO_EOF'
"""
Modelos de base de datos para los productos troposféricos de SIRGAS (ZTD).

Esquema:
    Station            -> catálogo de estaciones GNSS (una fila por estación)
    TropoObservation    -> una fila por estación x época horaria (el histórico ZTD)
    IngestedFile        -> registro de qué archivos SINEX TRO ya se procesaron,
                           para hacer la ingesta idempotente (no duplicar datos
                           si el pipeline se corre de nuevo sobre el mismo archivo)
"""

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, ForeignKey, UniqueConstraint, Index
)
from sqlalchemy.orm import relationship
from db.database import Base


class Station(Base):
    __tablename__ = "stations"

    id = Column(Integer, primary_key=True)
    code = Column(String(9), unique=True, nullable=False, index=True)  # ej. BOGT, BOGT00COL
    domes_number = Column(String(20), nullable=True)
    pos_x = Column(Float, nullable=True)  # coordenadas ITRF cartesianas (metros), si están en el archivo
    pos_y = Column(Float, nullable=True)
    pos_z = Column(Float, nullable=True)
    lat = Column(Float, nullable=True)   # derivadas de X,Y,Z si se calculan aparte
    lon = Column(Float, nullable=True)
    height = Column(Float, nullable=True)

    observations = relationship("TropoObservation", back_populates="station", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Station {self.code}>"


class TropoObservation(Base):
    """
    Una observación troposférica (ZTD) de una estación en una época dada.
    Los nombres de columna siguen la convención SINEX TRO (ver TROP/DESCRIPTION):
      TROTOT = retardo troposférico total (ZTD), en mm
      TROWET = componente húmeda, en mm
      TRODRY = componente seca (hidrostática), en mm
      STDDEV = desviación estándar del TROTOT, en mm
      IWV    = vapor de agua integrado, si está disponible
    """
    __tablename__ = "tropo_observations"

    id = Column(Integer, primary_key=True)
    station_id = Column(Integer, ForeignKey("stations.id"), nullable=False)
    epoch = Column(DateTime, nullable=False, index=True)  # UTC

    ztd_total_mm = Column(Float, nullable=True)      # TROTOT
    ztd_stddev_mm = Column(Float, nullable=True)      # STDDEV de TROTOT
    ztd_dry_mm = Column(Float, nullable=True)         # TRODRY
    ztd_wet_mm = Column(Float, nullable=True)         # TROWET
    gradient_north_mm = Column(Float, nullable=True)  # TGNTOT
    gradient_east_mm = Column(Float, nullable=True)   # TGETOT
    iwv_kg_m2 = Column(Float, nullable=True)          # IWV, si el AC lo reporta

    source_file = Column(String(255), nullable=True)  # nombre del archivo .TRO de origen

    station = relationship("Station", back_populates="observations")

    __table_args__ = (
        UniqueConstraint("station_id", "epoch", name="uq_station_epoch"),
        Index("ix_tropo_station_epoch", "station_id", "epoch"),
    )


class IngestedFile(Base):
    """Lleva registro de qué archivos SINEX TRO ya fueron descargados/procesados."""
    __tablename__ = "ingested_files"

    id = Column(Integer, primary_key=True)
    filename = Column(String(255), unique=True, nullable=False)
    file_hash = Column(String(64), nullable=True)  # sha256 del contenido, detecta si el AC republicó el archivo
    rows_inserted = Column(Integer, default=0)
    status = Column(String(20), default="ok")  # ok | error | empty
    detail = Column(String(500), nullable=True)
    processed_at = Column(DateTime, nullable=False)

ARCHIVO_EOF

echo "Creando config/stations.py..."
cat > config/stations.py << 'ARCHIVO_EOF'
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

ARCHIVO_EOF

echo "Creando sirgas_tropo_fetcher.py..."
cat > sirgas_tropo_fetcher.py << 'ARCHIVO_EOF'
"""
Descargador de productos troposféricos (ZTD) de SIRGAS-CON (toda la red, ~400+ estaciones).

Fuente oficial: ftp://ftp.sirgas.org/pub/gps/SIRGAS-ZPD/ (redirige a www3.dgfi.tum.de)
Estructura confirmada explorando el FTP manualmente:
    /pub/gps/SIRGAS-ZPD/<yyyy>/<ddd>/{ESTACION}{ddd}0.{yy}zpd.gz

Es decir: UN ARCHIVO POR ESTACIÓN POR DÍA (no un solo archivo combinado).
Formato interno: SINEX TRO real (confirmado con contenido real de un archivo).
Muestreo horario, disponible desde enero 2014. Latencia real de publicación: ~30 días.

Nota de citación: el uso de estos productos implica citar:
Mackern M.V., Mateo M.L., Camisay M.F., Morichetti P.V. (2020).
Tropospheric Products from High-Level GNSS Processing in Latin America.
IAG Symposia Series, Vol 152. doi: 10.1007/1345_2020_121
"""

import os
import time
import ftplib
import logging
from datetime import date, timedelta
from typing import List, Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

FTP_HOST = "ftp.sirgas.org"
FTP_BASE_PATH = "/pub/gps/SIRGAS-ZPD"
RAW_CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "tropo_raw")

MAX_RETRIES_PER_FILE = 3
RECONNECT_PAUSE_SECONDS = 5


def _remote_dir_for_date(day: date) -> str:
    """Confirmado en el FTP real: /pub/gps/SIRGAS-ZPD/<año>/<día-del-año de 3 dígitos>/"""
    doy = day.timetuple().tm_yday
    return f"{FTP_BASE_PATH}/{day.year}/{doy:03d}"


def connect(timeout: int = 30) -> ftplib.FTP:
    """Abre conexión FTP anónima en modo pasivo (necesario detrás de NAT/WSL)."""
    ftp = ftplib.FTP(FTP_HOST, timeout=timeout)
    ftp.login()  # acceso anónimo público
    ftp.set_pasv(True)
    return ftp


def list_available_files(day: date, ftp: ftplib.FTP) -> List[str]:
    """
    Lista los archivos ZPD disponibles para un día dado (toda la red SIRGAS-CON:
    ~400+ archivos, uno por estación, patrón {ESTACION}{DDD}0.{YY}zpd.gz).
    """
    remote_dir = _remote_dir_for_date(day)
    try:
        files = ftp.nlst(remote_dir)
    except ftplib.error_perm as e:
        logger.warning(f"No se encontró directorio remoto {remote_dir}: {e}")
        return []
    return [f for f in files if f.lower().endswith("zpd.gz")]


def _download_with_connection(ftp: ftplib.FTP, remote_path: str, local_path: str) -> bool:
    """Intenta descargar un archivo usando una conexión ya abierta. True si tuvo éxito."""
    try:
        with open(local_path, "wb") as f:
            ftp.retrbinary(f"RETR {remote_path}", f.write)
        return True
    except ftplib.all_errors as e:
        logger.warning(f"Fallo descargando {remote_path}: {e}")
        if os.path.exists(local_path):
            os.remove(local_path)  # no dejar archivos parciales/corruptos
        return False


def fetch_range(
    start: date,
    end: date,
    dest_dir: str = RAW_CACHE_DIR,
    station_filter: Optional[List[str]] = None,
) -> List[str]:
    """
    Descarga todos los archivos ZPD disponibles entre start y end (inclusive),
    para TODAS las estaciones de SIRGAS-CON por defecto, o solo las indicadas
    en station_filter (lista de códigos de 4 caracteres, ej. ['BOGT', 'QUIT']).

    Reutiliza una única conexión FTP para todo el rango (mucho más eficiente
    que abrir una conexión por archivo, relevante porque son ~400 archivos/día).
    Si la conexión se cae a mitad de camino, reconecta automáticamente y sigue
    donde quedó, en vez de reiniciar todo el proceso.
    """
    os.makedirs(dest_dir, exist_ok=True)
    downloaded: List[str] = []

    ftp = connect()
    total_days = (end - start).days + 1
    current = start
    day_index = 0

    while current <= end:
        day_index += 1
        try:
            remote_files = list_available_files(current, ftp=ftp)
        except ftplib.all_errors as e:
            logger.warning(f"Conexión perdida listando {current}: {e}. Reconectando...")
            time.sleep(RECONNECT_PAUSE_SECONDS)
            ftp = connect()
            remote_files = list_available_files(current, ftp=ftp)

        if station_filter:
            wanted = {s.upper() for s in station_filter}
            remote_files = [
                f for f in remote_files if os.path.basename(f)[:4].upper() in wanted
            ]

        logger.info(
            f"[{day_index}/{total_days}] {current.isoformat()}: "
            f"{len(remote_files)} archivos a revisar"
        )

        for remote_path in remote_files:
            filename = os.path.basename(remote_path)
            local_path = os.path.join(dest_dir, filename)

            if os.path.exists(local_path) and os.path.getsize(local_path) > 0:
                downloaded.append(local_path)
                continue  # ya en caché, idempotencia a nivel de archivo

            success = False
            for attempt in range(1, MAX_RETRIES_PER_FILE + 1):
                if _download_with_connection(ftp, remote_path, local_path):
                    success = True
                    break
                # La conexión pudo haberse caído; reconectar antes del siguiente intento
                time.sleep(RECONNECT_PAUSE_SECONDS)
                try:
                    ftp = connect()
                except ftplib.all_errors as e:
                    logger.error(f"No se pudo reconectar (intento {attempt}): {e}")

            if success:
                downloaded.append(local_path)
            else:
                logger.error(f"Se agotaron los reintentos para {filename}, se omite")

        current += timedelta(days=1)

    ftp.quit()
    logger.info(f"Descarga completa: {len(downloaded)} archivos disponibles en {dest_dir}")
    return downloaded


if __name__ == "__main__":
    import argparse

    arg_parser = argparse.ArgumentParser(description="Descargador de productos troposféricos SIRGAS")
    arg_parser.add_argument("--days-back", type=int, default=45, help="Cuántos días hacia atrás cubrir")
    arg_parser.add_argument("--latency-days", type=int, default=30, help="Latencia de publicación de SIRGAS")
    arg_parser.add_argument(
        "--stations", type=str, default=None,
        help="Lista opcional de códigos separados por coma (ej. BOGT,QUIT,AACR). Si se omite, trae TODAS."
    )
    args = arg_parser.parse_args()

    end_date = date.today() - timedelta(days=args.latency_days)
    start_date = end_date - timedelta(days=args.days_back)
    stations = args.stations.split(",") if args.stations else None

    files = fetch_range(start_date, end_date, station_filter=stations)
    print(f"Archivos descargados/disponibles: {len(files)}")

ARCHIVO_EOF

echo "Creando sirgas_tropo_parser.py..."
cat > sirgas_tropo_parser.py << 'ARCHIVO_EOF'
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
    Convierte una época SINEX 'yy:ddd:sssss' (año de 2 dígitos, día del año,
    segundos desde medianoche) a datetime UTC.
    Ej: '14:001:00000' -> 2014-01-01 00:00:00
    """
    try:
        yy, ddd, sssss = epoch_str.split(":")
        year = int(yy)
        year += 2000 if year < 80 else 1900  # convención SINEX estándar
        base = datetime(year, 1, 1) + timedelta(days=int(ddd) - 1)
        return base + timedelta(seconds=int(sssss))
    except (ValueError, AttributeError):
        return None


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


def _parse_field_order(lines: List[str]) -> List[str]:
    """
    Lee +TROP/DESCRIPTION y devuelve la lista ordenada de nombres de columna
    tal como aparecen tras el campo estación+época en +TROP/SOLUTION.
    Busca la línea que empieza con 'SOLUTION FIELDS_1' (o similar) dentro del bloque.
    """
    desc_lines = _extract_block(lines, "TROP/DESCRIPTION")
    for line in desc_lines:
        cleaned = line.strip()
        parts = cleaned.split()
        if not parts:
            continue
        # La etiqueta puede venir como un solo token 'SOLUTION_FIELDS_1' (formato
        # confirmado en archivos reales de SIRGAS) o como dos tokens separados
        # 'SOLUTION FIELDS_1' en otros Centros de Análisis. Detectamos cuál caso
        # es contando cuántos tokens iniciales pertenecen a la etiqueta.
        first_normalized = parts[0].upper().replace("_", " ")
        if first_normalized.startswith("SOLUTION FIELDS"):
            return parts[1:]  # etiqueta era un solo token
        if len(parts) >= 2 and parts[0].upper() == "SOLUTION" and parts[1].upper().startswith("FIELDS"):
            return parts[2:]  # etiqueta eran dos tokens separados por espacio
    logger.warning("No se encontró 'SOLUTION FIELDS' en TROP/DESCRIPTION; se usará orden por defecto")
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

    # --- Estaciones: SITE/ID y TROP/STACOORDINATES ---
    # Formato real confirmado: CODE PT DOMES T STATION_DESCRIPTION... APPROX_LON APPROX_LAT APP_H
    # (el DOMES está en la posición 2, no en la 1 -- antes va la columna PT)
    for line in _extract_block(lines, "SITE/ID"):
        parts = line.split()
        if len(parts) >= 3:
            code = parts[0]
            domes = parts[2]
            result["stations"].setdefault(code, {})["domes"] = domes

    for line in _extract_block(lines, "TROP/STA_COORDINATES"):
        parts = line.split()
        if len(parts) < 4:
            continue
        code = parts[0]
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
        code = parts[0]
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

ARCHIVO_EOF

echo "Creando sirgas_tropo_ingest.py..."
cat > sirgas_tropo_ingest.py << 'ARCHIVO_EOF'
"""
Pipeline de ingesta de datos troposféricos SIRGAS -> Base de datos.

Uso típico (correr periódicamente, ej. semanal, vía cron o GitHub Actions):

    python sirgas_tropo_ingest.py --days-back 60

Es idempotente: si un archivo ya fue procesado exitosamente (mismo hash),
se omite. Si el contenido cambió (el AC republicó el archivo corregido),
se vuelve a procesar.
"""

import argparse
import hashlib
import logging
import os
from datetime import date, datetime, timedelta

from db.database import SessionLocal, init_db
from db.models import Station, TropoObservation, IngestedFile
from sirgas_tropo_fetcher import fetch_range, RAW_CACHE_DIR
from sirgas_tropo_parser import parse_tro_file
from config.stations import get_active_stations

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def _file_hash(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _get_or_create_station(db, code: str, meta: dict) -> Station:
    station = db.query(Station).filter_by(code=code).one_or_none()
    if station is None:
        station = Station(
            code=code,
            domes_number=meta.get("domes"),
            pos_x=meta.get("x"),
            pos_y=meta.get("y"),
            pos_z=meta.get("z"),
        )
        db.add(station)
        db.flush()  # asigna station.id sin cerrar la transacción
    return station


def ingest_file(db, local_path: str) -> int:
    """Procesa un único archivo .TRO local. Retorna cuántas filas insertó (0 si se omitió)."""
    filename = os.path.basename(local_path)
    file_hash = _file_hash(local_path)

    existing = db.query(IngestedFile).filter_by(filename=filename).one_or_none()
    if existing and existing.file_hash == file_hash and existing.status == "ok":
        logger.info(f"Sin cambios, se omite: {filename}")
        return 0

    try:
        parsed = parse_tro_file(local_path)
    except Exception as e:
        logger.error(f"Error parseando {filename}: {e}")
        db.merge(IngestedFile(
            filename=filename, file_hash=file_hash, rows_inserted=0,
            status="error", detail=str(e)[:500], processed_at=datetime.utcnow(),
        ))
        db.commit()
        return 0

    stations_cache = {}
    inserted = 0
    for obs in parsed["observations"]:
        code = obs["station"]
        if code not in stations_cache:
            stations_cache[code] = _get_or_create_station(db, code, parsed["stations"].get(code, {}))
        station = stations_cache[code]

        # Upsert manual: evita duplicar la misma estación+época (UniqueConstraint en el modelo)
        exists = db.query(TropoObservation.id).filter_by(
            station_id=station.id, epoch=obs["epoch"]
        ).first()
        if exists:
            continue

        db.add(TropoObservation(
            station_id=station.id,
            epoch=obs["epoch"],
            ztd_total_mm=obs.get("ztd_total_mm"),
            ztd_stddev_mm=obs.get("ztd_stddev_mm"),
            ztd_dry_mm=obs.get("ztd_dry_mm"),
            ztd_wet_mm=obs.get("ztd_wet_mm"),
            gradient_north_mm=obs.get("gradient_north_mm"),
            gradient_east_mm=obs.get("gradient_east_mm"),
            iwv_kg_m2=obs.get("iwv_kg_m2"),
            source_file=filename,
        ))
        inserted += 1

    db.merge(IngestedFile(
        filename=filename, file_hash=file_hash, rows_inserted=inserted,
        status="ok" if parsed["observations"] else "empty",
        detail=None, processed_at=datetime.utcnow(),
    ))
    db.commit()
    logger.info(f"{filename}: {inserted} observaciones insertadas")
    return inserted


def run(days_back: int = 60, latency_days: int = 30, station_filter=None):
    """
    Descarga y procesa los archivos disponibles en la ventana
    [hoy - days_back - latency, hoy - latency].
    station_filter=None significa "sin filtro" (TODAS las estaciones de SIRGAS-CON);
    normalmente no se llama a run() directamente con eso, sino a través del CLI
    de abajo, que resuelve station_filter según --scope/--stations.
    """
    init_db()
    end = date.today() - timedelta(days=latency_days)
    start = end - timedelta(days=days_back)

    logger.info(f"Descargando archivos SIRGAS-ZPD entre {start} y {end}...")
    local_files = fetch_range(start, end, dest_dir=RAW_CACHE_DIR, station_filter=station_filter)
    logger.info(f"{len(local_files)} archivos disponibles para procesar")

    db = SessionLocal()
    total_inserted = 0
    try:
        for i, path in enumerate(local_files, start=1):
            total_inserted += ingest_file(db, path)
            if i % 100 == 0:
                logger.info(f"Progreso ingesta: {i}/{len(local_files)} archivos procesados")
    finally:
        db.close()

    logger.info(f"Ingesta completa. Total de observaciones nuevas: {total_inserted}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Ingesta de datos troposféricos SIRGAS para Andes Observatorio"
    )
    parser.add_argument("--days-back", type=int, default=60, help="Cuántos días hacia atrás cubrir")
    parser.add_argument("--latency-days", type=int, default=30, help="Latencia de publicación de SIRGAS")
    parser.add_argument(
        "--scope", type=str, default="andes",
        help=(
            "Qué estaciones procesar: 'andes' (default, las del dashboard actual), "
            "'global' (TODAS las de SIRGAS-CON, ~400+ estaciones), o el nombre de "
            "otra región que se agregue en config/stations.py"
        ),
    )
    parser.add_argument(
        "--stations", type=str, default=None,
        help="Override manual: lista de códigos separados por coma (ej. BOGT,QUIT). Ignora --scope si se usa."
    )
    args = parser.parse_args()

    if args.stations:
        stations = args.stations.split(",")
        logger.info(f"Usando lista manual de estaciones: {stations}")
    else:
        stations = get_active_stations(scope=args.scope)
        if stations is None:
            logger.info("Scope 'global': se procesarán TODAS las estaciones de SIRGAS-CON")
        else:
            logger.info(f"Scope '{args.scope}': {len(stations)} estaciones -> {stations}")

    run(days_back=args.days_back, latency_days=args.latency_days, station_filter=stations)

ARCHIVO_EOF

echo "Creando sirgas_api.py..."
cat > sirgas_api.py << 'ARCHIVO_EOF'
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

ARCHIVO_EOF

echo "Creando requirements.txt..."
cat > requirements.txt << 'ARCHIVO_EOF'
fastapi==0.104.1
uvicorn==0.24.0
requests==2.31.0
sqlalchemy==2.0.35
psycopg2-binary==2.9.9

ARCHIVO_EOF

echo "Creando README.md..."
cat > README.md << 'ARCHIVO_EOF'
# Andes-Observa
mardown
# 🌄 Andes Observatorio

[![GitHub Pages](https://img.shields.io/badge/website-up-brightgreen)](https://andesobservatorio.github.io/andes-observatorio/)
[![OpenWeatherMap](https://img.shields.io/badge/API-OpenWeatherMap-blue)](https://openweathermap.org/)
[![Leaflet](https://img.shields.io/badge/maps-Leaflet-green)](https://leafletjs.com/)
[![Chart.js](https://img.shields.io/badge/charts-Chart.js-red)](https://www.chart.js/)

## 📊 Monitoreo ambiental de la región andina en tiempo real

**Andes Observatorio** es una plataforma interactiva que monitorea y visualiza datos ambientales de los países de la región andina en tiempo real. Combina datos meteorológicos, áreas protegidas y visualización geográfica para ofrecer una herramienta completa de monitoreo.

---

## ✨ Características principales

| Característica | Descripción |
|----------------|-------------|
| 🌡️ **Temperatura en vivo** | Datos reales de OpenWeatherMap para 7 capitales andinas |
| 🗺️ **Mapa interactivo** | Visualización geográfica con marcadores y popups |
| 📈 **Gráficos comparativos** | Temperaturas por país y áreas protegidas |
| 🔄 **Actualización automática** | Datos refrescados cada 10 minutos |
| 📍 **Selector de ciudades** | Cambia entre capitales andinas fácilmente |

---

## 🗺️ Países incluidos

| País | Capital | Temperatura promedio |
|------|---------|---------------------|
| 🇨🇴 Colombia | Bogotá | 14-18°C |
| 🇪🇨 Ecuador | Quito | 16-20°C |
| 🇵🇪 Perú | Lima | 18-22°C |
| 🇧🇴 Bolivia | La Paz | 12-16°C |
| 🇨🇱 Chile | Santiago | 12-18°C |
| 🇦🇷 Argentina | Buenos Aires | 16-22°C |
| 🇧🇷 Brasil | Brasilia | 20-26°C |

> Próximamente: 🇻🇪 Venezuela, 🇵🇦 Panamá

---

## 🛠️ Tecnologías utilizadas

| Tecnología | Uso |
|------------|-----|
| HTML5, CSS3, JavaScript | Frontend |
| [Chart.js](https://www.chart.js/) | Gráficos interactivos |
| [Leaflet](https://leafletjs.com/) | Mapas interactivos |
| [OpenWeatherMap API](https://openweathermap.org/) | Datos climáticos en tiempo real |
| GitHub Pages | Alojamiento gratuito |

---

## 📁 Estructura del proyecto
# Andes-Observa
andes-observatorio/
│
├── index.html # Landing page institucional
├── dashboard.html # Dashboard interactivo principal
├── README.md # Documentación del proyecto
│
└── assets/ # (futuro) Imágenes y recursos
text


---

## 🚀 Ver en vivo

### 🔗 [https://andesobservatorio.github.io/andes-observatorio/](https://andesobservatorio.github.io/andes-observatorio/)

### Acceso directo:
- **Landing page:** [index.html](https://andesobservatorio.github.io/andes-observatorio/)
- **Dashboard:** [dashboard.html](https://andesobservatorio.github.io/andes-observatorio/dashboard.html)

---

## 📸 Capturas de pantalla

*(Puedes agregar imágenes de tu dashboard aquí después)*

---

## 🛰️ Módulo geodésico SIRGAS

Además del dashboard ambiental, el proyecto expone una API geodésica basada en datos de la red **SIRGAS-CON**:

| Dato | Endpoint | Fuente |
|------|----------|--------|
| Velocidades de estaciones | `GET /api/v1/geodesia/velocidades` | `SIR22P01_velocities.txt` (SIRGAS) |
| Estación puntual | `GET /api/v1/geodesia/estacion/{id}` | ídem |
| Estaciones con datos troposféricos | `GET /api/v1/geodesia/tropo/estaciones` | Base de datos local |
| Serie histórica de ZTD por estación | `GET /api/v1/geodesia/tropo/{codigo}/serie?desde=&hasta=` | Base de datos local |

### Parámetros troposféricos (ZTD)

Se ingiere el **Retardo Troposférico Cenital (ZTD)** que SIRGAS publica en formato **SINEX TRO**, con muestreo horario, desde enero de 2014, vía `ftp://ftp.sirgas.org/pub/gps/SIRGAS-ZPD/` (redirige a `www3.dgfi.tum.de`). SIRGAS publica estos productos semanalmente con ~30 días de latencia, por lo que no es un dato "en vivo": se ingiere periódicamente a una base de datos (SQLite en desarrollo, Postgres en producción vía `DATABASE_URL`).

**Estructura real del FTP** (confirmada explorando manualmente el servidor):
```
/pub/gps/SIRGAS-ZPD/<año>/<día-del-año, 3 dígitos>/{ESTACION}{ddd}0.{yy}zpd.gz
```
Es decir: **un archivo comprimido (.gz) por estación por día** — toda la red SIRGAS-CON tiene ~400+ estaciones.

**Cobertura de estaciones (config/stations.py):**
Por defecto, el pipeline solo procesa las 12 estaciones que ya muestra el dashboard actual (`scope="andes"`: Colombia, Ecuador, Perú, Bolivia, Chile, Argentina). El código ya está preparado para escalar a cobertura mundial sin tocar el fetcher ni el parser — solo hay que:

```bash
# Uso normal (default): solo las estaciones del dashboard
python sirgas_tropo_ingest.py --days-back 60

# Escalar a TODAS las estaciones de SIRGAS-CON (~400+), sin cambiar código:
python sirgas_tropo_ingest.py --days-back 60 --scope global

# Agregar una nueva región (ej. Centroamérica) más adelante: solo se
# agrega una entrada en config/stations.py -> REGIONES, y se usa:
python sirgas_tropo_ingest.py --days-back 60 --scope centroamerica

# Override manual puntual, ignorando el scope:
python sirgas_tropo_ingest.py --days-back 60 --stations BOGT,QUIT,AACR,LPGS
```

Pipeline:
```
config/stations.py        -> qué estaciones procesar (por región/scope, o "global" = todas)
sirgas_tropo_fetcher.py   -> descarga los .zpd.gz diarios por FTP, reutilizando una
                              única conexión (reconecta automáticamente si se cae),
                              con caché local para no volver a bajar lo ya descargado
sirgas_tropo_parser.py    -> parsea el formato SINEX TRO real (lee el orden de columnas
                              del propio archivo vía TROP/DESCRIPTION, no lo asume fijo)
sirgas_tropo_ingest.py    -> orquesta descarga + parseo + guardado idempotente en DB
```

Para correr la ingesta manualmente:
```bash
pip install -r requirements.txt
python sirgas_tropo_ingest.py --days-back 60
```

**Citación obligatoria:** el uso de estos productos requiere citar a Mackern M.V., Mateo M.L., Camisay M.F., Morichetti P.V. (2020). *Tropospheric Products from High-Level GNSS Processing in Latin America*. IAG Symposia Series, Vol 152. doi: 10.1007/1345_2020_121

---

## 🎯 Próximas mejoras

- [ ] Agregar Venezuela y Panamá al dashboard
- [ ] Gráfico de tendencia histórica de temperatura
- [ ] Sección de noticias ambientales
- [ ] Calidad del aire (AQI) en tiempo real
- [ ] Datos de deforestación por país

---

## 📧 Contacto

| Medio | Información |
|-------|-------------|
| 📧 Correo | andesobservatorio@gmail.com |
| 📞 Teléfono | +57 3337211047 |
| 🌐 Web | [GitHub Pages](https://andesobservatorio.github.io/andes-observatorio/) |

---

## 📄 Licencia

Este proyecto es de código abierto y está disponible para fines educativos y de conservación ambiental.

---

*🌄 Andes Observatorio - Monitoreo de ecosistemas andinos para su protección y conservación*

*Datos actualizados en tiempo real desde OpenWeatherMap*

ARCHIVO_EOF

echo ""
echo "Listo. Estructura creada:"
find . -maxdepth 2 -name '*.py' -o -maxdepth 2 -name '*.txt' -o -maxdepth 2 -name '*.md' | sort
echo ""
echo "Siguiente paso: pip3 install --break-system-packages -r requirements.txt"