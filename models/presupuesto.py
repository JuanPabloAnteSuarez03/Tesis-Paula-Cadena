from .database import Base
from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.orm import relationship

class Presupuesto(Base):
    __tablename__ = "presupuestos"

    id = Column(Integer, primary_key=True)
    codigo = Column(String, unique=True, nullable=False)
    descripcion = Column(String, nullable=False)
    total = Column(Float, nullable=False)

    # Relación 1:N con la tabla intermedia que conecta presupuestos y análisis unitarios
    analisis_asociados = relationship("PresupuestoAnalisisUnitario", back_populates="presupuesto")
