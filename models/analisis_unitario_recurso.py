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

    @hybrid_property
    def calcular_vr_parcial(self):
        """Calcula el valor parcial dinámicamente."""
        return self.cantidad_recurso * (1 + self.desper) * self.vr_unitario

    @calcular_vr_parcial.expression
    def calcular_vr_parcial(cls):
        """Expresión SQL para calcular `vr_parcial` en consultas."""
        return cls.cantidad_recurso * (1 + cls.desper) * cls.vr_unitario

    def actualizar_vr_parcial(self):
        """Método para actualizar el valor parcial manualmente antes de guardar."""
        self.vr_parcial = self.calcular_vr_parcial
