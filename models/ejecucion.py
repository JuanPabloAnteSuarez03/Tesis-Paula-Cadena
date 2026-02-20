# models/ejecucion.py
from .database import Base
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime


class Ejecucion(Base):
    __tablename__ = "ejecuciones"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    nombre     = Column(String, nullable=False, unique=True)
    creado_en  = Column(DateTime, default=datetime.utcnow)

    facturas     = relationship("Factura",    back_populates="ejecucion",
                                cascade="all, delete-orphan")
    pagos_nomina = relationship("PagoNomina", back_populates="ejecucion",
                                cascade="all, delete-orphan")

