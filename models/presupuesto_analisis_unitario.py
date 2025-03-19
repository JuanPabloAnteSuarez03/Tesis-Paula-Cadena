from .database import Base
from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.schema import UniqueConstraint

class PresupuestoAnalisisUnitario(Base):
    __tablename__ = "presupuestos_analisis_unitarios"

    id = Column(Integer, primary_key=True)
    codigo_presupuesto = Column(String, ForeignKey("presupuestos.codigo"), nullable=False)
    codigo_analisis = Column(String, ForeignKey("analisis_unitarios.codigo"), nullable=False)
    descripcion_analisis = Column(String, nullable=False)
    unidad_analisis = Column(String, nullable=False)
    cantidad_analisis = Column(Float, nullable=False, default=0.0)
    vr_unitario = Column(Float, nullable=False, default=0.0)
    vr_total = Column(Float, nullable=False, default=0.0)

    presupuesto = relationship("Presupuesto", back_populates="analisis_asociados")
    analisis = relationship("AnalisisUnitario", back_populates="presupuestos_asociados")

