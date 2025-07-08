from .database import Base
from sqlalchemy import Column, Integer, String, Float, Boolean
from sqlalchemy.orm import relationship

class Profesional(Base):
    """Modelo que representa a un profesional utilizado para el cálculo de costos de administración (AIU)."""
    __tablename__ = "profesionales"

    id = Column(Integer, primary_key=True)
    nombre = Column(String, unique=True, nullable=False)
    cargo = Column(String, nullable=False)
    salario_mensual = Column(Float, nullable=False)
    necesario = Column(Boolean, default=False)

    def __repr__(self):
        return f"<Profesional(nombre={self.nombre}, cargo={self.cargo}, salario_mensual={self.salario_mensual}, necesario={self.necesario})>" 