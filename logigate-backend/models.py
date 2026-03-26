from sqlalchemy import Column, Integer, String, Float, Text, DateTime
from sqlalchemy.sql import func
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    nombre = Column(String, nullable=False)
    rol = Column(String, default="guardia")  # "guardia" | "admin"


class Registro(Base):
    __tablename__ = "registros"

    id = Column(Integer, primary_key=True, index=True)
    placa = Column(String, index=True, nullable=False)
    empresa = Column(String, nullable=True)
    tipo_unidad = Column(String, nullable=True)
    conductor = Column(String, nullable=True)
    estado = Column(String, nullable=False)        # "entrada" | "salida" | "denegado"
    confianza = Column(Float, nullable=True)
    danos_visibles = Column(Integer, default=0)   # 0 = no, 1 = si
    sellos_rotos = Column(Integer, default=0)
    notas = Column(Text, nullable=True)
    autorizado_por = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
