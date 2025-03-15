from database import engine, Base

from analisis_unitario import AnalisisUnitario
from recurso import Recurso
from analisis_unitario_recurso import AnalisisUnitarioRecurso
from presupuesto_analisis_unitario import PresupuestoAnalisisUnitario
from presupuesto import Presupuesto

print("📢 Eliminando y recreando las tablas en PostgreSQL...")
Base.metadata.drop_all(bind=engine)  # Elimina todas las tablas
Base.metadata.create_all(bind=engine)  # Crea todas las tablasprint("📢 Tablas registradas en SQLAlchemy:")
print(Base.metadata.tables.keys())  # Debería mostrar los nombres de las tablas
print("✅ Tablas recreadas exitosamente.")
