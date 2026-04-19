from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Estructura: postgresql://usuario:contraseña@host:puerto/nombre_bd
# Cambia la IP por 127.0.0.1 (localhost)
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:S1stemas24@192.168.100.47:5432/logigate"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependencia para obtener la sesión en tus rutas
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()