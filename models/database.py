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
    
# Crear las tablas necesarias
def crear_tablas():
    conn = get_db_connection()
    if conn is None:
        return
    
    try:
        with conn.cursor() as cursor:
            # Crear la tabla de presupuestos
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS presupuestos (
                id SERIAL PRIMARY KEY,
                nombre TEXT NOT NULL
            );
            """)
            
            # Crear la tabla de articulos
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS articulos (
                id SERIAL PRIMARY KEY,
                codigo TEXT NOT NULL UNIQUE,
                descripcion TEXT NOT NULL,
                unidad TEXT NOT NULL,
                valor_unitario REAL NOT NULL
            );
            """)
            
            # Crear la tabla de relación entre presupuestos y artículos
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS presupuesto_articulos (
                id SERIAL PRIMARY KEY,
                presupuesto_id INTEGER REFERENCES presupuestos(id) ON DELETE CASCADE,
                articulo_id INTEGER REFERENCES articulos(id) ON DELETE CASCADE,
                cantidad REAL NOT NULL DEFAULT 1
            );
            """)
            
        conn.commit()
        print("Tablas creadas correctamente.")
        
    except Exception as e:
        print("Error al crear las tablas:", e)
        
    finally:
        conn.close()

# Cargar datos desde un archivo CSV
def cargar_datos_desde_csv(csv_file):
    conn = get_db_connection()
    if conn is None:
        return
    
    try:
        with conn.cursor() as cursor:
            # Verificar si la tabla ya contiene datos
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
            print("Datos cargados correctamente.")
    
    except Exception as e:
        print("Error al cargar datos desde el CSV:", e)
    
    finally:
        conn.close()

# Ejecutar funciones
crear_tablas()
cargar_datos_desde_csv('data_gobernacion/articulos_unicos.csv')
