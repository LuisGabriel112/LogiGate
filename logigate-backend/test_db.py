from sqlalchemy import create_engine, text

# Reemplaza con tus datos reales de pgAdmin
# "postgresql://usuario:password@host:puerto/nombre_bd"
DATABASE_URL = "postgresql://postgres:S1stemas24@localhost:5432/logigate"

engine = create_engine(DATABASE_URL)

def check_connection():
    try:
        # Intentamos conectar y ejecutar una consulta simple
        with engine.connect() as connection:
            result = connection.execute(text("SELECT version();"))
            row = result.fetchone()
            print("✅ ¡Conexión exitosa!")
            print(f"🔹 Versión de Postgres: {row[0]}")
    except Exception as e:
        print("❌ Error al conectar a la base de datos:")
        print(f"👉 {e}")

if __name__ == "__main__":
    check_connection()