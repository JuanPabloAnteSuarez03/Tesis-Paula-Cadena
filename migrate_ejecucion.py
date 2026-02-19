"""
migrate_ejecucion.py
Crea las tablas de Ejecución (facturas, factura_items, pagos_nomina)
sin tocar las tablas existentes.
Ejecutar una sola vez:  python migrate_ejecucion.py
"""
from models.database import engine, Base

# Importar los modelos para que SQLAlchemy los registre en Base.metadata
from models.factura import Factura          # noqa: F401
from models.factura_item import FacturaItem  # noqa: F401
from models.pago_nomina import PagoNomina   # noqa: F401

# Importar también los modelos existentes para no perderlos si se llama create_all
from models.analisis_unitario import AnalisisUnitario  # noqa: F401
from models.recurso import Recurso                     # noqa: F401
from models.analisis_unitario_recurso import AnalisisUnitarioRecurso  # noqa: F401
from models.presupuesto_analisis_unitario import PresupuestoAnalisisUnitario  # noqa: F401
from models.presupuesto import Presupuesto             # noqa: F401
from models.profesional import Profesional             # noqa: F401

if __name__ == "__main__":
    print("Creando tablas nuevas (checkfirst=True — no elimina las existentes)...")
    # checkfirst=True → solo crea si la tabla NO existe
    Base.metadata.create_all(bind=engine, checkfirst=True)
    print("✅ Tablas creadas (o ya existían):")
    for name in sorted(Base.metadata.tables.keys()):
        print(f"   · {name}")

