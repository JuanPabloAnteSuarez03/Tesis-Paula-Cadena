from database import Base
from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.orm import relationship

class AnalisisUnitario(Base):
    __tablename__ = "analisis_unitarios"

    id = Column(Integer, primary_key=True)
    codigo = Column(String, unique=True, nullable=False)
    descripcion = Column(String, nullable=False)
    unidad = Column(String, nullable=False)
    total = Column(Float, nullable=False)

    # Relación con la tabla intermedia que conecta análisis y recursos
    recursos_asociados = relationship("AnalisisUnitarioRecurso", back_populates="analisis")
    presupuestos_asociados = relationship("PresupuestoAnalisisUnitario", back_populates="analisis")
