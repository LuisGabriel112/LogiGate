import os
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


# Jalamos la URL de forma segura desde el archivo .env
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

# Si por alguna razón estás corriendo local sin el .env cargado, un fallback seguro:
if not SQLALCHEMY_DATABASE_URL:
    SQLALCHEMY_DATABASE_URL = "postgresql://postgres:dLlSHDh1TYIOeTMq@db.tednvpvvmyzqxzmybfsm.supabase.co:5432/postgres"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def init_db():
    from models import Registro, User, RegistroDanos
    Base.metadata.create_all(bind=engine)
    
    # Bloque para añadir columnas si no existen (útil en tus demos)
    with engine.connect() as conn:
        for ddl in (
            "ALTER TABLE registros_danos ADD COLUMN interpretacion TEXT;",
            "ALTER TABLE registros_danos ADD COLUMN registro_id INTEGER;"
        ):
            try:
                conn.execute(text(ddl))
                conn.commit()
            except Exception:
                pass  # La columna ya existe o hubo un error manejado

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()