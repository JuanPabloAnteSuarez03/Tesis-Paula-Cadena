import psycopg2
from psycopg2 import sql

# Datos de conexión
DB_NAME = "app_presupuestos"
DB_USER = "postgres"
DB_PASSWORD = "123Randy"
DB_HOST = "localhost"
DB_PORT = "5432"

def get_db_connection():
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        return conn
    except Exception as e:
        print("Error al conectar con la base de datos:", e)
        return None

# Crear tabla si no existe
def crear_tablas():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS presupuestos (
        id SERIAL PRIMARY KEY,
        nombre TEXT NOT NULL,
        costo_total REAL NOT NULL
    );
    """)
    conn.commit()
    conn.close()

crear_tablas()
