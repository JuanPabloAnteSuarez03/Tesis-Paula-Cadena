from sqlalchemy.ext.hybrid import hybrid_property
from .database import Base
from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship

class AnalisisUnitarioRecurso(Base):
    __tablename__ = "analisis_unitarios_recursos"

    id = Column(Integer, primary_key=True)
    codigo_analisis = Column(String, ForeignKey("analisis_unitarios.codigo"), nullable=False)
    codigo_recurso = Column(String, ForeignKey("recursos.codigo"), nullable=False)
    descripcion_recurso = Column(String, nullable=False)
    unidad_recurso = Column(String, nullable=False)
    cantidad_recurso = Column(Float, nullable=False, default=0.0)
    desper = Column(Float, nullable=False, default=0.0)
    vr_unitario = Column(Float, nullable=False, default=0.0)

    # 🔹 AHORA `vr_parcial` es una columna real
    vr_parcial = Column(Float, nullable=False, default=0.0)

    # Relación inversa
    analisis = relationship("AnalisisUnitario", back_populates="recursos_asociados")
    recurso = relationship("Recurso", back_populates="analisis")

    __table_args__ = (UniqueConstraint("codigo_analisis", "codigo_recurso"),)
