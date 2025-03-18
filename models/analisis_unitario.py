from .database import Base
from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import select, func
from .analisis_unitario_recurso import AnalisisUnitarioRecurso

class AnalisisUnitario(Base):
    __tablename__ = "analisis_unitarios"
    id = Column(Integer, primary_key=True)
    codigo = Column(String, unique=True, nullable=False)
    descripcion = Column(String, nullable=False)
    unidad = Column(String, nullable=False)
    total = Column(Float, nullable=False)  # Esta columna podría ser eliminada si usas solo el híbrido

    recursos_asociados = relationship("AnalisisUnitarioRecurso", back_populates="analisis")
    presupuestos_asociados = relationship("PresupuestoAnalisisUnitario", back_populates="analisis")

    @hybrid_property
    def total_calculado(self):
        return sum(r.vr_parcial for r in self.recursos_asociados)

    @total_calculado.expression
    def total_calculado(cls):
        return (
            select(func.coalesce(func.sum(AnalisisUnitarioRecurso.vr_parcial), 0.0))
            .where(AnalisisUnitarioRecurso.codigo_analisis == cls.codigo)
            .label("total_calculado")
        )
