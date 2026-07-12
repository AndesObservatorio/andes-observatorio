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

