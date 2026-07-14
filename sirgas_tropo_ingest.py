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

