# models/pago_nomina.py
from .database import Base
from sqlalchemy import Column, Integer, String, Float, Date, Text


class PagoNomina(Base):
    __tablename__ = "pagos_nomina"

    id = Column(Integer, primary_key=True, autoincrement=True)
    fecha = Column(Date, nullable=False)
    trabajador = Column(String, nullable=False)
    cargo = Column(String, nullable=False, default="")
    # "JORNAL" o "GLOBAL"
    modalidad = Column(String, nullable=False, default="JORNAL")
    dias = Column(Float, nullable=False, default=1.0)
    valor = Column(Float, nullable=False, default=0.0)
    total = Column(Float, nullable=False, default=0.0)
    observacion = Column(Text, nullable=True, default="")

