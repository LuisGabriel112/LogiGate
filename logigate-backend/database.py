from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# URL de conexion local SQLite (Demo Fix)
SQLALCHEMY_DATABASE_URL = "sqlite:///./logigate.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def init_db():
    from models import Registro, User, RegistroDanos
    Base.metadata.create_all(bind=engine)
    with engine.connect() as conn:
        for ddl in (
            "ALTER TABLE registros_danos ADD COLUMN interpretacion TEXT",
            "ALTER TABLE registros_danos ADD COLUMN registro_id INTEGER",
        ):
            try:
                conn.execute(text(ddl))
                conn.commit()
            except Exception:
                pass  # column already exists

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
