# models/recurso.py
from .database import Base
from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.orm import relationship

class Recurso(Base):
    __tablename__ = "recursos"

    id = Column(Integer, primary_key=True)
    codigo = Column(String, unique=True, nullable=False)
    descripcion = Column(String, nullable=False)
    unidad = Column(String, nullable=False)
    valor_unitario = Column(Float, nullable=False)

    # Aquí usamos el nombre en cadena; asegúrate de que el modelo AnalisisUnitarioRecurso esté importado
    analisis = relationship("AnalisisUnitarioRecurso", back_populates="recurso")
