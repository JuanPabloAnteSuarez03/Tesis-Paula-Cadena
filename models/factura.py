# models/factura.py
from .database import Base
from sqlalchemy import Column, Integer, String, Date, Float
from sqlalchemy.orm import relationship


class Factura(Base):
    __tablename__ = "facturas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    numero_factura = Column(String, nullable=False)
    fecha = Column(Date, nullable=False)
    proveedor = Column(String, nullable=False, default="")

    # Relación 1:N con los ítems de la factura
    items = relationship(
        "FacturaItem",
        back_populates="factura",
        cascade="all, delete-orphan",
        order_by="FacturaItem.id",
    )

    @property
    def total(self) -> float:
        return sum(item.total for item in self.items)

