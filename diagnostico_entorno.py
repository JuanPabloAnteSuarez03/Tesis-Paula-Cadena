import sys
import locale
import os
from sqlalchemy import create_engine
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

def diagnostico_basico():
    print("🔍 Diagnóstico del entorno:\n")
    print(f"📦 Versión de Python: {sys.version}")
    print(f"🗂️  Codificación por defecto del sistema: {sys.getdefaultencoding()}")
    print(f"🌍 Locale preferido: {locale.getpreferredencoding()}")
    print(f"📁 Ruta actual: {os.getcwd()}")
    print()

def probar_conexion_postgres():
    print("🔌 Verificando conexión a PostgreSQL...\n")
    
    # Reemplaza con la cadena real del cliente
    DB_NAME = "app_presupuestos"
    DB_USER = "postgres"
    DB_PASSWORD = "Diego"
    DB_HOST = "localhost"
    DB_PORT = "5432"

    DB_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

    try:
        engine = create_engine(DB_URL)
        with engine.connect() as conn:
            resultado = conn.execute(text("SELECT version();"))
            print(f"✅ Conexión exitosa. Versión de PostgreSQL:\n{resultado.fetchone()[0]}")
    except SQLAlchemyError as e:
        print("❌ Error de conexión:")
        print(e)
    except Exception as e:
        print("❌ Otro error inesperado:")
        print(e)

if __name__ == "__main__":
    diagnostico_basico()
    probar_conexion_postgres()
