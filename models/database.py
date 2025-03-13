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
            
            # Crear la tabla de recursos
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS recursos (
                id SERIAL PRIMARY KEY,
                codigo TEXT NOT NULL UNIQUE,
                descripcion TEXT NOT NULL,
                unidad TEXT NOT NULL,
                valor_unitario REAL NOT NULL
            );
            """)
            
            # Crear la tabla de relación entre presupuestos y recursos
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS presupuesto_recursos (
                id SERIAL PRIMARY KEY,
                presupuesto_id INTEGER REFERENCES presupuestos(id) ON DELETE CASCADE,
                recurso_id INTEGER UNIQUE REFERENCES recursos(id) ON DELETE CASCADE,
                cantidad REAL NOT NULL DEFAULT 1
            );
            """)
            # Crear la tabla de analisis_unitarios
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS analisis_unitarios (
                id SERIAL PRIMARY KEY,
                codigo TEXT NOT NULL UNIQUE,
                descripcion TEXT NOT NULL,
                unidad TEXT NOT NULL,
                total REAL NOT NULL
            );
            """)
            # Crear la tabla de relacion entre analisis_unitarios y recursos
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS analisis_unitarios_recursos (
                id SERIAL PRIMARY KEY,
                descripcion_recurso TEXT NOT NULL,
                codigo_recurso TEXT NOT NULL REFERENCES recursos(codigo) ON DELETE CASCADE,
                codigo_analisis TEXT NOT NULL REFERENCES analisis_unitarios(codigo) ON DELETE CASCADE,
                unidad_recurso TEXT NOT NULL,
                cantidad_recurso FLOAT NOT NULL,
                desper FLOAT NOT NULL,
                vr_unitario FLOAT NOT NULL,
                vr_parcial FLOAT NOT NULL
            );
            """)
        conn.commit()
        print("Tablas creadas correctamente.")
        
    except Exception as e:
        print("Error al crear las tablas:", e)
        
    finally:
        conn.close()

# Cargar datos desde un archivo CSV
def cargar_datos_recursos_desde_csv(csv_file):
    conn = get_db_connection()
    if conn is None:
        return
    
    try:
        with conn.cursor() as cursor:
            # Verificar si la tabla ya contiene datos
            cursor.execute("SELECT COUNT(*) FROM recursos;")
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
                    INSERT INTO recursos (codigo, descripcion, unidad, valor_unitario)
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

def cargar_analisis_unitarios(csv_file):
    conn = get_db_connection()
    if conn is None:
        return
    
    try:
        df = pd.read_csv(csv_file)
        # Opcional: eliminar duplicados
        df.drop_duplicates(subset=['codigo'], inplace=True)

        with conn.cursor() as cursor:
            for _, row in df.iterrows():
                try:
                    cursor.execute("""
                        INSERT INTO analisis_unitarios (codigo, descripcion, unidad, total)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (codigo) DO NOTHING;
                    """, (
                        row['codigo'], 
                        row['descripcion'], 
                        row['unidad'], 
                        row['total']
                    ))
                except Exception as e:
                    print(f"Error al insertar {row['codigo']}: {e}")

        conn.commit()
        print("Datos de análisis unitarios cargados correctamente.")
    except Exception as e:
        print("Error al cargar datos de análisis unitarios:", e)
    finally:
        conn.close()

def clean_string(s):
    """
    Limpia la cadena s reemplazando dobles quotes ("") por comillas simples o
    simplemente eliminándolas, según la necesidad.
    """
    if not isinstance(s, str):
        return s
    # Ejemplo: reemplaza dobles quotes con una sola comilla
    return s.replace('""', '"')

def cargar_relacion_analisis_unitarios_recursos(csv_file):
    conn = get_db_connection()
    if conn is None:
        return
    
    try:
        df = pd.read_csv(csv_file)

        with conn.cursor() as cursor:
            for _, row in df.iterrows():
                try:
                    cursor.execute("""
                        INSERT INTO analisis_unitarios_recursos 
                        (codigo_recurso, descripcion_recurso, unidad_recurso, cantidad_recurso, desper, vr_unitario, vr_parcial, codigo_analisis)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
                    """, (
                        str(row['codigo_recurso']),
                        str(row['descripcion_recurso']),
                        str(row['unidad_recurso']),
                        row['cantidad_recurso'],
                        row['desper'],
                        row['vr_unitario'],
                        row['vr_parcial'],
                        str(row['codigo_analisis'])
                    ))
                except psycopg2.Error as e:
                    # Se realiza rollback para limpiar el estado de la transacción
                    conn.rollback()
                    print(f"Error al insertar {row['codigo_recurso']} - {row['codigo_analisis']}: {e.pgerror}")
                    print("SQL:", cursor.query)
                    # Opcionalmente, continuar o detener la ejecución según convenga
        conn.commit()
        print("Datos de relación entre análisis unitarios y recursos cargados correctamente.")
    except Exception as e:
        print("Error al cargar datos de relación entre análisis unitarios y recursos:", e)
    finally:
        conn.close()



# Ejecutar funciones
crear_tablas()
cargar_datos_recursos_desde_csv('../data_gobernacion/recursos_unicos.csv')
cargar_analisis_unitarios('../data_gobernacion/analisis_unitarios.csv')
cargar_relacion_analisis_unitarios_recursos('../data_gobernacion/recursos_analisis.csv')
