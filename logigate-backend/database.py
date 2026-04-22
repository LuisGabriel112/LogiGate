from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Estructura: postgresql://usuario:contraseña@host:puerto/nombre_bd
# Cambia la IP por 127.0.0.1 (localhost)
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:S1stemas24@localhost:5432/logigate"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def init_db():
    from models import Registro, User  # noqa: F401 — importar para registrar los modelos
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()