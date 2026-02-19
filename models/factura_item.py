# models/factura_item.py
from .database import Base
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship


class FacturaItem(Base):
    __tablename__ = "factura_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    factura_id = Column(Integer, ForeignKey("facturas.id", ondelete="CASCADE"), nullable=False)
    insumo = Column(String, nullable=False)
    cantidad = Column(Float, nullable=False, default=1.0)
    precio_unitario = Column(Float, nullable=False, default=0.0)
    aplica_iva = Column(Boolean, nullable=False, default=False)
    total = Column(Float, nullable=False, default=0.0)

    # Relación inversa con Factura
    factura = relationship("Factura", back_populates="items")

