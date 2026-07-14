import sqlite3
import os

DB_PATH = "db/sirgas_tropo.db"

# Asegurar que la carpeta db existe
os.makedirs("db", exist_ok=True)

# Conectar y crear la tabla
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

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

cursor.execute("CREATE INDEX IF NOT EXISTS idx_troposferico_station_time ON troposferico (station_code, timestamp)")

conn.commit()
conn.close()

print(f"✅ Base de datos creada en {DB_PATH}")
