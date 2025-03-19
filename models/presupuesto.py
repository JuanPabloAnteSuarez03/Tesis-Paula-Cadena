from .database import Base
from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import select, func
from .presupuesto_analisis_unitario import PresupuestoAnalisisUnitario

class Presupuesto(Base):
    __tablename__ = "presupuestos"

    id = Column(Integer, primary_key=True)
    codigo = Column(String, unique=True, nullable=False)
    descripcion = Column(String, nullable=False)
    total = Column(Float, nullable=False)

    # Relación 1:N con la tabla intermedia que conecta presupuestos y análisis unitarios
    analisis_asociados = relationship("PresupuestoAnalisisUnitario", back_populates="presupuesto")

    @hybrid_property
    def total_calculado(self):
        return sum(a.vr_total for a in self.analisis_asociados)
    
    @total_calculado.expression
    def total_calculado(cls):
        return (
            select(func.coalesce(func.sum(PresupuestoAnalisisUnitario.vr_total), 0.0))
            .where(PresupuestoAnalisisUnitario.codigo_presupuesto == cls.codigo)
            .label("total_calculado")
        )
