import psycopg2
import pandas as pd

# Datos de conexión
DB_NAME = "app_presupuestos"
DB_USER = "postgres"
DB_PASSWORD = "123Randy"
DB_HOST = "localhost"
DB_PORT = "5432"

# Conectar a la base de datos
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
    
def crear_tabla_presupuesto():
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

# Crear la tabla articulos
def crear_tabla_articulos():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS articulos (
        id SERIAL PRIMARY KEY,
        codigo TEXT NOT NULL UNIQUE,
        descripcion TEXT NOT NULL,
        unidad TEXT NOT NULL,
        valor_unitario REAL NOT NULL
    );
    """)
    conn.commit()
    conn.close()
    print("Tabla 'articulos' creada correctamente.")

# Cargar los datos del CSV a la base de datos
import pandas as pd

def cargar_datos_desde_csv(csv_file):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verificar si la tabla está vacía
    cursor.execute("SELECT COUNT(*) FROM articulos;")
    if cursor.fetchone()[0] > 0:
        print("La tabla ya contiene datos. No se cargará el CSV.")
        return
    
    # Cargar el CSV con pandas
    df = pd.read_csv(csv_file)
    
    # Eliminar filas duplicadas basadas en el código
    df = df.drop_duplicates(subset=['Codigo'])
    
    # Iterar sobre las filas del DataFrame e insertar los datos
    for _, row in df.iterrows():
        try:
            cursor.execute("""
            INSERT INTO articulos (codigo, descripcion, unidad, valor_unitario)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (codigo) DO NOTHING;
            """, (row['Codigo'], row['Descripcion'], row['Unidad'], row['Valor Unitario']))
        except Exception as e:
            print(f"Error al insertar el código {row['Codigo']}: {e}")
    
    conn.commit()
    conn.close()
    print("Datos cargados correctamente.")

# Ejecutar funciones
crear_tabla_presupuesto()
crear_tabla_articulos()
cargar_datos_desde_csv('data_gobernacion/articulos_unicos.csv')
