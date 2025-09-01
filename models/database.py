import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base

# Datos de conexión
DB_NAME = "app_presupuestos"
DB_USER = "postgres"
DB_PASSWORD = "123Randy"
DB_HOST = "localhost"
DB_PORT = "5432"

# Forzar codificación del cliente para libpq antes de cualquier conexión
os.environ.setdefault("PGCLIENTENCODING", "LATIN1")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Crear el motor de conexión (engine)
# Forzamos un fallback de codificación del cliente a LATIN1 para tolerar datos legacy
# con acentos/ñ almacenados en codificación distinta a UTF-8.
def _creator_connect():
    """Create a psycopg2 connection with safe params (avoid DSN string).
    Also set a tolerant client encoding.
    """
    import psycopg2
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
    )
    try:
        conn.set_client_encoding('LATIN1')
    except Exception:
        pass
    return conn

engine = create_engine(
    "postgresql+psycopg2://",
    creator=_creator_connect,
    pool_pre_ping=True,
)

# Redundante pero seguro: asegurar codificación del cliente al establecer conexión
@event.listens_for(engine, "connect")
def _set_client_encoding(dbapi_connection, connection_record):
    try:
        cursor = dbapi_connection.cursor()
        cursor.execute("SET client_encoding TO 'LATIN1'")
        cursor.close()
    except Exception:
        # No bloquear si el servidor no acepta el comando por alguna razón
        pass

# Crear la sesión
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para definir modelos
Base = declarative_base()

def get_db_connection():
    """
    Conecta a la base de datos usando psycopg2 (útil para operaciones directas)
    """
    import psycopg2
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            options='-c client_encoding=LATIN1'
        )
        # Asegurar misma codificación en el cliente psycopg2
        try:
            conn.set_client_encoding('LATIN1')
        except Exception:
            pass
        return conn
    except Exception as e:
        print("Error al conectar con la base de datos:", e)
        return None
