"""
Descargador de productos troposféricos (ZTD) de SIRGAS-CON.

Fuente oficial: ftp://ftp.sirgas.org/pub/gps/SIRGAS-ZPD/
Redirige a: www3.dgfi.tum.de

Estructura confirmada:
    /pub/gps/SIRGAS-ZPD/<yyyy>/<ddd>/{ESTACION}{ddd}0.{yy}zpd.gz
    o formato nuevo: SIR0OPSFIN_<YYYYDDD>0000_01D_01H_<ESTACION>00<PAIS>_TRO.TRO.gz
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
    """Construye la ruta remota para un día específico."""
    doy = day.timetuple().tm_yday
    return f"{FTP_BASE_PATH}/{day.year}/{doy:03d}"


def connect(timeout: int = 30) -> ftplib.FTP:
    """Abre conexión FTP anónima en modo pasivo."""
    ftp = ftplib.FTP(FTP_HOST, timeout=timeout)
    ftp.login()
    ftp.set_pasv(True)  # Modo pasivo es obligatorio detrás de NAT/firewalls
    return ftp


def list_available_files(day: date, ftp: ftplib.FTP) -> List[str]:
    """Lista los archivos disponibles para un día dado."""
    remote_dir = _remote_dir_for_date(day)
    try:
        files = ftp.nlst(remote_dir)
    except ftplib.error_perm as e:
        logger.warning(f"No se encontró directorio remoto {remote_dir}: {e}")
        return []
    
    # Filtrar archivos .zpd.gz y .tro.gz (ambos formatos)
    return [f for f in files if f.lower().endswith("zpd.gz") or f.lower().endswith("tro.gz")]


def extract_station_code(filename: str) -> Optional[str]:
    """Extrae el código de 4 caracteres de la estación desde el nombre del archivo."""
    base = os.path.basename(filename)
    
    # Formato nuevo: SIR0OPSFIN_20261570000_01D_01H_BOGT00COL_TRO.TRO.gz
    if "_" in base:
        parts = base.split("_")
        for part in parts:
            if len(part) == 9 and part[:4].isalpha() and part[4:6].isdigit():
                return part[:4].upper()
            if len(part) == 4 and part.isalpha():
                return part.upper()
        return None
    
    # Formato antiguo: BOGT1570.20zpd.gz
    return base[:4].upper() if len(base) >= 4 else None


def _download_with_connection(ftp: ftplib.FTP, remote_path: str, local_path: str) -> bool:
    """Descarga un archivo usando la conexión existente."""
    try:
        with open(local_path, "wb") as f:
            ftp.retrbinary(f"RETR {remote_path}", f.write)
        return True
    except ftplib.all_errors as e:
        logger.warning(f"Fallo descargando {remote_path}: {e}")
        if os.path.exists(local_path):
            os.remove(local_path)
        return False


def fetch_range(
    start: date,
    end: date,
    dest_dir: str = RAW_CACHE_DIR,
    station_filter: Optional[List[str]] = None,
) -> List[str]:
    """Descarga archivos entre start y end (inclusive)."""
    os.makedirs(dest_dir, exist_ok=True)
    downloaded = []

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
            remote_files = [f for f in remote_files if extract_station_code(f) in wanted]

        logger.info(
            f"[{day_index}/{total_days}] {current.isoformat()}: {len(remote_files)} archivos"
        )

        for remote_path in remote_files:
            filename = os.path.basename(remote_path)
            local_path = os.path.join(dest_dir, filename)

            if os.path.exists(local_path) and os.path.getsize(local_path) > 0:
                downloaded.append(local_path)
                continue

            success = False
            for attempt in range(1, MAX_RETRIES_PER_FILE + 1):
                if _download_with_connection(ftp, remote_path, local_path):
                    success = True
                    break
                time.sleep(RECONNECT_PAUSE_SECONDS)
                try:
                    ftp = connect()
                except ftplib.all_errors as e:
                    logger.error(f"No se pudo reconectar (intento {attempt}): {e}")

            if success:
                downloaded.append(local_path)
            else:
                logger.error(f"Se agotaron los reintentos para {filename}")

        current += timedelta(days=1)

    ftp.quit()
    logger.info(f"Descarga completa: {len(downloaded)} archivos en {dest_dir}")
    return downloaded


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--days-back", type=int, default=45)
    parser.add_argument("--latency-days", type=int, default=30)
    parser.add_argument("--stations", type=str, default=None)
    args = parser.parse_args()

    end_date = date.today() - timedelta(days=args.latency_days)
    start_date = end_date - timedelta(days=args.days_back)
    stations = args.stations.split(",") if args.stations else None

    files = fetch_range(start_date, end_date, station_filter=stations)
    print(f"Archivos descargados: {len(files)}")
