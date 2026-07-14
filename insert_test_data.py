import sqlite3
import os
from datetime import datetime, timedelta

DB_PATH = "db/sirgas_tropo.db"

# Asegurar que la carpeta db existe
os.makedirs("db", exist_ok=True)

# Conectar a la base de datos
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Crear la tabla si no existe
cursor.execute("""
    CREATE TABLE IF NOT EXISTS troposferico (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        station_code TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        ztd REAL NOT NULL,
        ztd_error REAL,
        UNIQUE(station_code, timestamp)
    )
""")

# Insertar datos de prueba para BOGT (Bogotá)
estaciones = ["BOGT", "QUIT", "LPGS", "SANT"]
now = datetime.now()

for estacion in estaciones:
    for i in range(30):  # 30 días de datos
        fecha = now - timedelta(days=i)
        ztd = 2.3 + 0.1 * (i % 5)  # Valores simulados
        cursor.execute("""
            INSERT OR IGNORE INTO troposferico (station_code, timestamp, ztd, ztd_error)
            VALUES (?, ?, ?, ?)
        """, (estacion, fecha.isoformat(), ztd, 0.02))

conn.commit()
conn.close()

print(f"✅ Datos de prueba insertados para {len(estaciones)} estaciones")
