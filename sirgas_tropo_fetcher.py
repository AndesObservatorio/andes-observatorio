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
    ~400+ archivos, uno por estación).

    SIRGAS cambió la convención de nombres en algún momento entre 2020 y 2026:
      Legacy (hasta ~2022?): {ESTACION}{DDD}0.{YY}zpd.gz              ej. UYDU3500.20zpd.gz
      Actual (estilo IGS largo): SIR0OPSFIN_{YYYYDDD}0000_01D_01H_{ESTACION}00{PAIS}_TRO.TRO.gz
                                                                       ej. SIR0OPSFIN_20261570000_01D_01H_AACR00CRI_TRO.TRO.gz
    Se aceptan ambos formatos para no romper si se procesan años viejos.
    """
    remote_dir = _remote_dir_for_date(day)
    try:
        files = ftp.nlst(remote_dir)
    except ftplib.error_perm as e:
        logger.warning(f"No se encontró directorio remoto {remote_dir}: {e}")
        return []
    return [
        f for f in files
        if f.lower().endswith("zpd.gz") or f.lower().endswith("tro.gz")
    ]


def extract_station_code(filename: str) -> Optional[str]:
    """
    Extrae el código de 4 caracteres de la estación a partir del nombre de archivo,
    soportando ambos formatos de nombre que usa/usó SIRGAS (ver list_available_files).
    """
    base = os.path.basename(filename)
    if "_" in base:
        # Formato largo estilo IGS: SIR0OPSFIN_20261570000_01D_01H_AACR00CRI_TRO.TRO.gz
        parts = base.split("_")
        # El campo de estación es el que tiene forma XXXX00CCC (9 caracteres): 4 letras
        # de estación + 2 dígitos de monumento + 3 letras de país.
        for part in parts:
            if len(part) == 9 and part[:4].isalpha() and part[4:6].isdigit():
                return part[:4].upper()
        return None
    else:
        # Formato legacy: {ESTACION}{DDD}0.{YY}zpd.gz -> los primeros 4 caracteres
        return base[:4].upper() if len(base) >= 4 else None


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
                f for f in remote_files if extract_station_code(f) in wanted
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
