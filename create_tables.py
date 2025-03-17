from models.database import engine, Base
from models.analisis_unitario import AnalisisUnitario
from models.recurso import Recurso
from models.analisis_unitario_recurso import AnalisisUnitarioRecurso
from models.presupuesto_analisis_unitario import PresupuestoAnalisisUnitario
from models.presupuesto import Presupuesto

print("📢 Eliminando y recreando las tablas en PostgreSQL...")
Base.metadata.drop_all(bind=engine)  # Elimina todas las tablas
Base.metadata.create_all(bind=engine)  # Crea todas las tablasprint("📢 Tablas registradas en SQLAlchemy:")
print(Base.metadata.tables.keys())  # Debería mostrar los nombres de las tablas
print("✅ Tablas recreadas exitosamente.")
