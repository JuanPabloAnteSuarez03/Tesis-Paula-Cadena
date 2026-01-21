import psycopg2
import pandas as pd
from .database import get_db_connection

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
            
            # Cargar el CSV con pandas, tolerando codificaciones comunes en Windows
            df = pd.read_csv(csv_file, encoding_errors='ignore', encoding='latin-1')
            
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
        df = pd.read_csv(csv_file, encoding_errors='ignore', encoding='latin-1')
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
        df = pd.read_csv(csv_file, encoding_errors='ignore', encoding='latin-1')

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

def cargar_profesionales_desde_excel(excel_file, sheet_name=0):
    """Carga los profesionales desde un archivo de Excel a la tabla `profesionales`.

    El archivo debe contener al menos las columnas:
        - `Nombre` o `Profesional`: nombre del profesional.
        - `Cargo` (opcional): cargo del profesional (si no existe, se usa el nombre).
        - `Salario` o `Salario_Mensual`: salario mensual recomendado.
        - `Necesario`: booleano o texto ("sí"/"no") indicando si el profesional es obligatorio.
    """
    conn = get_db_connection()
    if conn is None:
        return

    try:
        # Leemos sin encabezados para poder detectar la fila donde realmente
        # están los títulos (en tu archivo no viene en la primera fila).
        df_raw = pd.read_excel(excel_file, sheet_name=sheet_name, header=None)

        # Buscar la fila que contenga palabras clave para usarla como encabezado.
        header_idx = None
        keywords = ["valor mensual", "valor total", "dedicación", "cargo", "profesional"]
        for idx in range(min(len(df_raw), 20)):
            row_vals = df_raw.iloc[idx]
            row_lower = [str(x).lower() if not pd.isna(x) else "" for x in row_vals]
            if any(any(k in cell for k in keywords) for cell in row_lower):
                header_idx = idx
                break

        if header_idx is None:
            print("❌ No se encontró fila de encabezados (no aparece ninguna palabra clave).")
            return

        # Crear el DataFrame definitivo tomando como header la fila detectada
        raw_headers = [str(x).strip().lower() if not pd.isna(x) else "nan" for x in df_raw.iloc[header_idx]]
        
        # HACER CABECERAS ÚNICAS para evitar el error "The truth value of a Series is ambiguous"
        seen = {}
        unique_headers = []
        for h in raw_headers:
            if h in seen:
                seen[h] += 1
                unique_headers.append(f"{h}_{seen[h]}")
            else:
                seen[h] = 0
                unique_headers.append(h)
        
        df = df_raw.iloc[header_idx + 1:].copy()
        df.columns = unique_headers

        # Intentar localizar la columna de salario
        salario_col = next((col for col in df.columns if any(k in str(col) for k in ["valor mensual", "valor total en pesos"])), None)
        if salario_col is None:
            print("❌ No se encontró la columna de Salario. Encabezados:", df.columns.tolist())
            return

        # Intentar localizar la columna de nombre/cargo
        # Buscamos la columna que contenga "cargo" o "profesional", o la que esté a la izquierda de dedicación/salario
        nombre_col = next((col for col in df.columns if any(k in str(col) for k in ["cargo", "profesional", "nombre"])), None)
        if not nombre_col:
            salario_idx = list(df.columns).index(salario_col)
            # Retroceder desde el salario buscando una columna que no sea "nan"
            for i in range(salario_idx - 1, -1, -1):
                if "nan" not in df.columns[i]:
                    nombre_col = df.columns[i]
                    break
        
        if not nombre_col:
            nombre_col = df.columns[1] # Fallback a la segunda columna

        # Limpiar filas vacías/NaN y detectar sección obligatoria / opcional
        profesionales_rows = []
        mandatory = True
        for _, row in df.iterrows():
            nombre_val = row[nombre_col]
            if pd.isna(nombre_val) or str(nombre_val).strip().lower() in ["", "nan", "none"]:
                continue
            
            nombre_raw = str(nombre_val).strip()
            if 'valor total' in nombre_raw.lower() and 'profesionales' in nombre_raw.lower():
                mandatory = False
                continue
            
            profesionales_rows.append((row, mandatory))

        with conn.cursor() as cursor:
            for row, es_mandatorio in profesionales_rows:
                nombre = str(row[nombre_col]).strip()
                cargo = nombre # Por defecto el cargo es el nombre si no hay otra columna
                
                try:
                    salario_val = row[salario_col]
                    if pd.isna(salario_val):
                        salario = 0.0
                    else:
                        salario_str = str(salario_val).replace("$", "").replace(".", "").replace(",", ".")
                        salario = float(salario_str)
                except (ValueError, TypeError):
                    salario = 0.0
                
                necesario = es_mandatorio

                cursor.execute(
                    """
                    INSERT INTO profesionales (nombre, cargo, salario_mensual, necesario)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (nombre) DO UPDATE SET
                        cargo = EXCLUDED.cargo,
                        salario_mensual = EXCLUDED.salario_mensual,
                        necesario = EXCLUDED.necesario;
                    """,
                    (nombre, cargo, salario, necesario)
                )
        conn.commit()
        print("✅ Profesionales cargados correctamente desde Excel.")
    except Exception as e:
        print("Error al cargar profesionales:", e)
    finally:
        conn.close()

def cargar_profesionales_desde_csv(csv_file):
    """Carga profesionales desde un CSV en formato limpio.

    El CSV debe tener al menos las columnas:
        - `Cargo` (o `Profesional` / `Nombre`)
        - `Valor Mensual`
        - `Es Obligatorio` (TRUE/FALSE) – opcional; si falta se asume FALSE
    """
    conn = get_db_connection()
    if conn is None:
        return

    try:
        df = pd.read_csv(csv_file)
        # Normalizar columnas
        df.columns = [c.strip().lower() for c in df.columns]

        def find_col(*options):
            for opt in options:
                if opt.lower() in df.columns:
                    return opt.lower()
            return None

        nombre_col = find_col('cargo', 'profesional', 'nombre')
        salario_col = find_col('valor mensual', 'salario', 'salario mensual')
        obligatorio_col = find_col('es obligatorio', 'obligatorio', 'necesario')

        if nombre_col is None or salario_col is None:
            print("❌ Columnas requeridas (Cargo/Valor Mensual) no encontradas en", csv_file)
            print("   Encabezados:", df.columns.tolist())
            return

        with conn.cursor() as cursor:
            for _, row in df.iterrows():
                nombre_raw = row[nombre_col]
                if pd.isna(nombre_raw):
                    continue
                nombre = str(nombre_raw).strip()
                if not nombre or nombre.lower() in ("nan", "none"):
                    continue

                # Salario
                try:
                    salario_text = str(row[salario_col])
                    salario_clean = salario_text.replace("$", "").replace(" ", "").replace(".", "").replace(",", ".")
                    salario = float(salario_clean)
                except (ValueError, TypeError):
                    continue

                # Obligatorio
                obligatorio_val = row[obligatorio_col] if obligatorio_col else False
                if isinstance(obligatorio_val, str):
                    obligatorio = obligatorio_val.strip().lower() in ["true", "t", "1", "si", "sí"]
                else:
                    obligatorio = bool(obligatorio_val)

                cursor.execute(
                    """
                    INSERT INTO profesionales (nombre, cargo, salario_mensual, necesario)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (nombre) DO UPDATE SET
                        salario_mensual = EXCLUDED.salario_mensual,
                        necesario = EXCLUDED.necesario;
                    """,
                    (nombre, nombre, salario, obligatorio)
                )
        conn.commit()
        print("✅ Profesionales cargados desde CSV", csv_file)
    except Exception as e:
        print("Error al cargar profesionales desde CSV:", e)
    finally:
        conn.close()

def limpiar_profesionales_nan():
    """
    Elimina filas con nombre/cargo vacíos o iguales a 'nan' (case-insensitive)
    y normaliza valores inconsistentes.
    """
    conn = get_db_connection()
    if conn is None:
        return
    try:
        with conn.cursor() as cursor:
            # Borrar filas inválidas (con trim y variantes)
            cursor.execute(
                """
                DELETE FROM profesionales
                WHERE lower(trim(coalesce(nombre,''))) IN ('nan','n','')
                   OR lower(trim(coalesce(cargo,'')))  IN ('nan','n','');
                """
            )
        conn.commit()
        print("✅ Limpieza de profesionales completada (NaN removidos)")
    except Exception as e:
        print("Error al limpiar profesionales:", e)
        conn.rollback()
    finally:
        conn.close()

# ------------------------------------------------------------
# Si se ejecuta este archivo directamente, se pueden lanzar las
# cargas masivas de recursos/analisis. Al importarlo (por
# ejemplo, desde el script de profesionales) NO se ejecutarán.
# ------------------------------------------------------------

if __name__ == "__main__":
    cargar_datos_recursos_desde_csv('../data_gobernacion/recursos_unicos.csv')
    cargar_analisis_unitarios('../data_gobernacion/analisis_unitarios.csv')
    cargar_relacion_analisis_unitarios_recursos('../data_gobernacion/recursos_analisis.csv')

