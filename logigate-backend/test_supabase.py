import os
import sqlalchemy
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

db_url = os.getenv("DATABASE_URL")

print(f"--- Probando Conexión a Supabase ---")
if not db_url:
    print("❌ ERROR: No se encontró DATABASE_URL en el archivo .env")
else:
    # Ocultar password para el print
    safe_url = db_url.split("@")[-1] if "@" in db_url else db_url
    print(f"URL detectada (host): {safe_url}")
    
    try:
        engine = create_engine(db_url)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version();"))
            print(f"✅ ¡CONEXIÓN EXITOSA!")
            print(f"Versión de DB: {result.fetchone()[0]}")
    except Exception as e:
        print(f"❌ ERROR DE CONEXIÓN:")
        print(str(e))
