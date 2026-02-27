import os
import sys
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker

# Datos de conexión (modo PostgreSQL para desarrollo)
DB_NAME = "app_presupuestos"
DB_USER = "postgres"
DB_PASSWORD = "123Randy"
DB_HOST = "localhost"
DB_PORT = "5432"


def _running_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def _default_local_sqlite_path() -> Path:
    local_appdata = Path(os.getenv("LOCALAPPDATA", str(Path.home())))
    data_dir = local_appdata / "Control360" / "AppPresupuestos"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / "app_presupuestos.db"


def _resolve_backend() -> str:
    # Prioridad de selección:
    # 1) APP_DB_BACKEND explícito
    # 2) ejecutable empaquetado -> sqlite local
    # 3) default desarrollo -> postgres
    backend = os.getenv("APP_DB_BACKEND", "").strip().lower()
    if backend in ("postgres", "postgresql", "sqlite"):
        return "sqlite" if backend == "sqlite" else "postgresql"
    if _running_frozen():
        return "sqlite"
    return "postgresql"


def _resolve_database_url() -> tuple[str, str]:
    # APP_DB_URL permite override total.
    db_url = os.getenv("APP_DB_URL", "").strip()
    if db_url:
        if db_url.startswith("sqlite"):
            return "sqlite", db_url
        return "postgresql", db_url

    backend = _resolve_backend()
    if backend == "sqlite":
        db_path = os.getenv("APP_DB_PATH", "").strip()
        if db_path:
            sqlite_path = Path(db_path)
        else:
            sqlite_path = _default_local_sqlite_path()
        sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        return "sqlite", f"sqlite:///{sqlite_path}"

    # Postgres (compatibilidad actual)
    return (
        "postgresql",
        f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}",
    )


DB_BACKEND, DATABASE_URL = _resolve_database_url()

if DB_BACKEND == "sqlite":
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        pool_pre_ping=True,
    )

    @event.listens_for(engine, "connect")
    def _sqlite_pragma_on_connect(dbapi_connection, connection_record):
        try:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
        except Exception:
            pass
else:
    # Forzar codificación del cliente para libpq antes de cualquier conexión
    os.environ.setdefault("PGCLIENTENCODING", "LATIN1")

    def _creator_connect():
        """Create a psycopg2 connection with safe params (avoid DSN string)."""
        import psycopg2

        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
        )
        try:
            conn.set_client_encoding("LATIN1")
        except Exception:
            pass
        return conn

    engine = create_engine(
        "postgresql+psycopg2://",
        creator=_creator_connect,
        pool_pre_ping=True,
    )

    @event.listens_for(engine, "connect")
    def _set_client_encoding(dbapi_connection, connection_record):
        try:
            cursor = dbapi_connection.cursor()
            cursor.execute("SET client_encoding TO 'LATIN1'")
            cursor.close()
        except Exception:
            pass

# Crear la sesión
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para definir modelos
Base = declarative_base()


def get_db_connection():
    """
    Conexión de bajo nivel para utilidades legacy.
    Nota: en modo sqlite retorna sqlite3.Connection.
    """
    if DB_BACKEND == "sqlite":
        import sqlite3

        db_path = DATABASE_URL.replace("sqlite:///", "", 1)
        try:
            conn = sqlite3.connect(db_path)
            conn.execute("PRAGMA foreign_keys=ON")
            return conn
        except Exception as e:
            print("Error al conectar con la base de datos SQLite:", e)
            return None

    import psycopg2

    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            options="-c client_encoding=LATIN1",
        )
        try:
            conn.set_client_encoding("LATIN1")
        except Exception:
            pass
        return conn
    except Exception as e:
        print("Error al conectar con la base de datos:", e)
        return None
