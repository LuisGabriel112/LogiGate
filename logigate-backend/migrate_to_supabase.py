from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Importamos Base y los modelos desde tu código actual
# Nota: Asegúrate de estar en la carpeta logigate-backend
try:
    from database import Base
    from models import User, Registro, RegistroDanos
except ImportError:
    print("❌ Error: Asegúrate de ejecutar este script desde la carpeta 'logigate-backend'")
    exit()

load_dotenv()

# Configuración
SQLITE_URL = "sqlite:///./logigate.db"
SUPABASE_URL = os.getenv("DATABASE_URL")

def migrate():
    if not SUPABASE_URL:
        print("❌ ERROR: No se encontró DATABASE_URL en el archivo .env")
        return

    print("--- Iniciando Migración a Supabase ---")
    
    # Conexiones
    sqlite_engine = create_engine(SQLITE_URL)
    supabase_engine = create_engine(SUPABASE_URL)
    
    # Crear las tablas en Supabase (si no existen)
    print("1. Creando tablas en Supabase...")
    Base.metadata.create_all(bind=supabase_engine)

    # Sesiones
    SqliteSession = sessionmaker(bind=sqlite_engine)
    SupabaseSession = sessionmaker(bind=supabase_engine)
    
    src = SqliteSession()
    dst = SupabaseSession()

    try:
        # Migrar Usuarios
        print("2. Migrando usuarios...")
        users = src.query(User).all()
        for u in users:
            dst.merge(u) # merge evita duplicados
        
        # Migrar Registros
        print("3. Migrando registros...")
        regs = src.query(Registro).all()
        for r in regs:
            dst.merge(r)

        # Migrar Daños
        print("4. Migrando registros de daños...")
        danos = src.query(RegistroDanos).all()
        for d in danos:
            dst.merge(d)

        dst.commit()
        print("✅ ¡MIGRACIÓN COMPLETADA CON ÉXITO!")
        print("Ahora tus datos locales están en la nube de Supabase.")
    except Exception as e:
        print(f"❌ Error durante la migración: {e}")
        dst.rollback()
    finally:
        src.close()
        dst.close()

if __name__ == "__main__":
    migrate()
