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

