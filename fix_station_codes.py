import sqlite3
import os

DB_PATH = "data/andes_observa.db"

# Verificar si la base de datos existe
if not os.path.exists(DB_PATH):
    print("❌ Base de datos no encontrada")
    exit(0)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Ver estaciones actuales
cursor.execute("SELECT id, code FROM stations")
stations = cursor.fetchall()

print("📊 Estaciones antes de normalizar:")
for s in stations:
    print(f"  ID: {s[0]}, Código: '{s[1]}'")

# Normalizar códigos (quitar sufijos @PAIS)
for s in stations:
    code = s[1]
    # Si el código tiene @, quedarse con la parte antes del @
    if '@' in code:
        new_code = code.split('@')[0]
        print(f"  Normalizando: '{code}' -> '{new_code}'")
        cursor.execute("UPDATE stations SET code = ? WHERE id = ?", (new_code, s[0]))

# Eliminar duplicados (mantener el ID más bajo)
cursor.execute("""
    DELETE FROM stations 
    WHERE id NOT IN (
        SELECT MIN(id) 
        FROM stations 
        GROUP BY code
    )
""")

conn.commit()

# Verificar resultado
cursor.execute("SELECT id, code FROM stations")
stations = cursor.fetchall()
print("\n📊 Estaciones después de normalizar:")
for s in stations:
    print(f"  ID: {s[0]}, Código: '{s[1]}'")

conn.close()
print("✅ Estaciones normalizadas")
