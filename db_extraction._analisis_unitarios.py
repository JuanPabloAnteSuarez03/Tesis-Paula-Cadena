import os
import re
import pandas as pd
import tabula

# Lista de unidades analisis unitarios
UNITS = [
    'HC','GLB','VJE','M3','M2','UND','HRS','KG','KLS','LBS','ML','DIA',
    'CM3','CJO','JGO','SC','M3K','GLL','ROL','CC','HR','PHC','G','K',
    'KG.','GL','LTS','U/D','CUN','GLN','HH','LAM','PLI','BTO','GLS','CAN',
    'RLL','PAR','ARR','VAR','PG2','CAR','ATD','KLL','T/K','MES','CAJ','M/D',
    'PTO','CM2','C/K','KLK','M/K'
]

unit_list = [
    'HC','GLB','VJE','M3','M2','UND','HRS','KG','KLS','LBS','ML','DIA','CM3','CJO','JGO','SC','M3K','GLL','ROL','VJE','CC','HR','PHC','G','K','DIA','KG','KG.','GL','LTS','U/D','CUN','GLN','HH','LAM','PLI','BTO','GLS','CAN','RLL','PAR','ARR','VAR','PG2','CAR','ATD','KLL','T/K','MES','CAJ'
]

# ---------------------------
# Extracción de análisis unitarios
# ---------------------------
def extract_analysis_units(pdf_path):
    """
    Extrae los análisis unitarios del PDF.
    Se asume que cada línea de análisis tiene el formato:
        CODE-DESCRIPCIÓN [Unidad]
    Si la última palabra de la descripción está en la lista UNITS se extrae como unidad.
    Luego, en líneas posteriores se busca el valor total (precedido por '$').
    """
    # Extraer todas las tablas del PDF
    tables = tabula.read_pdf(pdf_path, pages='all', multiple_tables=True, stream=True)
    analysis_units = []
    current_analysis = None

    # Concatenar todas las tablas en una lista de líneas
    lines = []
    for tbl in tables:
        tbl = tbl.fillna('')
        for _, row in tbl.iterrows():
            row_text = ' '.join(str(val).strip() for val in row if val != '')
            row_text = re.sub(r'\s+', ' ', row_text).strip()
            if row_text:
                lines.append(row_text)

    # Regex para detectar el encabezado del análisis unitario
    regex_analisis = re.compile(r'^(\d{2}-\d{2}-\d{2})-(.+)$')
    # Regex para detectar el valor total (con $)
    regex_total = re.compile(r'\$([\d,\.]+)')
    looking_for_total = False

    for line in lines:
        match_analisis = regex_analisis.match(line)
        if match_analisis:
            code = match_analisis.group(1)
            desc_line = match_analisis.group(2).strip()
            tokens = desc_line.split()
            # Si el último token está en UNITS, se asume que es la unidad
            if tokens and tokens[-1].upper() in UNITS:
                unit = tokens[-1].upper()
                description = " ".join(tokens[:-1])
            else:
                unit = ''
                description = desc_line

            current_analysis = {
                'codigo': code,
                'descripcion': description,
                'unidad': unit,
                'total': 0.0
            }
            analysis_units.append(current_analysis)
            looking_for_total = True
            continue

        if looking_for_total and current_analysis:
            match_total = regex_total.search(line)
            if match_total:
                total_str = match_total.group(1).replace(',', '')
                try:
                    total_val = float(total_str)
                except ValueError:
                    total_val = 0.0
                current_analysis['total'] = total_val
                looking_for_total = False
                current_analysis = None
                continue

    return analysis_units

# ---------------------------
# Extracción de recursos (Relaciones)
# Se deja la lógica original de relaciones, sin cambios
# ---------------------------
def parse_resource_line(line):
    """
    Intenta parsear un 'recurso' en la forma:
    
    CODIGO-DESCRIPCION ... UNIDAD CANT DESPER VRUNIT VRPARCIAL
    
    Retorna un diccionario con esos campos o None si no se pudo parsear.
    """
    # 1) Buscamos un código que cumpla:
    #    - Empieza con:
    #      * M[OQ] (ej: MOAG01-)
    #      * SC (ej: SC0201-)
    #      * 3,4,6 dígitos (ej: 123-, 1234-, 003282-)
    #    - Debe terminar en '-'
    #
    #    => ejemplo:  "MOAG01-"   "003282-"   "SC0201-"
    #
    #    Usamos un regex con grupos alternativos, y exigimos que termine en '-'
    #    para separar luego la descripción.
    
    # Patrón para "código-" (quitamos el guion al final):
    code_pattern = re.compile(
        r'^(?:'                # comienzo del string
        r'(?:M[OQ]\w+)|'       # MO..., MQ...
        r'(?:SC\d+)|'          # SC...
        r'(?:\d{3,6})'         # 3,4 o 6 dígitos
        r')-'                  # guion
    )
    
    splitted = line.split()
    if not splitted:
        return None
    
    # splitted[0] podría ser "MOAG01-HERRAMIENTA" o "003282-GASOLINA"
    # o "SC0201-ELABORACION" etc.
    first_token = splitted[0]
    
    # Verificamos si coincide con code_pattern
    m = code_pattern.match(first_token)
    if not m:
        return None  # no es un recurso con ese formato
    
    # Extraemos el "codigo" sin el guion final
    # p.ej. si first_token="MOAG01-HERRAMIENTA" => codeCandidate="MOAG01-"
    # luego leftover="HERRAMIENTA"
    codeCandidate = m.group(0)  # "MOAG01-"
    code_clean = codeCandidate[:-1]  # quitamos el '-' => "MOAG01"
    
    leftover = first_token[len(codeCandidate):]  # lo que quede en first_token tras "MOAG01-"
    
    # Reconstruimos la línea, pero reemplazamos splitted[0] por leftover + splitted[1...]
    # para analizar "descripción + (unidad cant desper vrunit vrparcial)"
    new_tokens = []
    if leftover:
        new_tokens.append(leftover)
    # Agregamos el resto
    new_tokens.extend(splitted[1:])
    
    # new_tokens = ej: ["HERRAMIENTA","MENOR","GLB","4,000","0,00","1.600","6.400"]
    if len(new_tokens) < 5:
        return None  # no hay columnas suficientes
    
    # Queremos ubicar la unidad. Asumimos que la unidad es uno de:
    # "UND|M2|ML|GLN|VJE|LBS|M3|KLS|M/D|HRS|DIA|CM3|JGO|CJO|HC|CC|GLB|PHC|..."
    # (puedes ampliarla con las que necesites).
    
    unit_list = [
        'HC','GLB','VJE','M3','M2','UND','HRS','KG','KLS','LBS','ML','DIA','CM3','CJO','JGO','SC','M3K','GLL','ROL','VJE','CC','HR','PHC','G','K','DIA','KG','KG.','GL','LTS','U/D','CUN','GLN','HH','LAM','PLI','BTO','GLS','CAN','RLL','PAR','ARR','VAR','PG2','CAR','ATD','KLL','T/K','MES','CAJ'
    ]
    
    # Vamos a buscar la unidad en new_tokens
    unit_index = -1
    for i, tok in enumerate(new_tokens):
        if tok.upper() in unit_list:
            unit_index = i
            break
    
    if unit_index < 0:
        # No se encontró una unidad reconocida
        print(f"No se encontró unidad en la línea de recurso:\n{line}")
        return None
    
    # La descripción es todo lo anterior a la unidad
    desc_part = new_tokens[:unit_index]  # puede tener varias palabras
    description_recurso = " ".join(desc_part).strip()
    
    # Lo que sigue a la unidad son 5 posibles tokens: CANT, DESPER, VRUNIT, VRPARCIAL
    # En la práctica, a veces DESPER no existe o es "0,00", ajusta según tu caso.
    # Asumiremos 4 tokens: Cant, Desper, VrUnit, VrParcial
    # (Si a veces no hay "desper", lo interpretas como 0.0)
    
    rest = new_tokens[unit_index+1:]
    if len(rest) < 4:
        print(f"No se pudo parsear 5 columnas en la línea de recurso:\n{line}")
        return None
    
    # Tomamos 4 exactos: cant, desper, vrunit, vrparcial
    cant_str, desper_str, vrunit_str, vrparcial_str = rest[:4]
    
    # Convertir a float
    def to_float(s):
        return float(s.replace('.', '').replace(',', '.'))
    
    try:
        cantidad = to_float(cant_str)
    except:
        cantidad = 0.0
    
    try:
        desper = to_float(desper_str)
    except:
        desper = 0.0
    
    try:
        vrunit = to_float(vrunit_str)
    except:
        vrunit = 0.0
    
    try:
        vrparcial = to_float(vrparcial_str)
    except:
        vrparcial = 0.0
    
    return {
        'codigo_recurso': code_clean,
        'descripcion_recurso': description_recurso,
        'unidad_recurso': new_tokens[unit_index],  # la unidad detectada
        'cantidad_recurso': cantidad,
        'desper': desper,
        'vr_unitario': vrunit,
        'vr_parcial': vrparcial
    }


def extract_resources(pdf_path, analysis_units):
    """
    Lee el PDF nuevamente o (reusa) y parsea línea por línea en busca de recursos.
    Para cada recurso, asocia con el 'codigo_analisis' actual si estamos
    dentro de uno.
    """
    # Generamos un set de codigos de analisis para saber en cuál estamos
    # (en tu caso, podrías usar la misma lógica de "cuando encuentro XX-XX-XX- me cambio de análisis")
    # pero aquí asumo que "analysis_units" ya lo tienes.
    codigos_analisis = {a['codigo'] for a in analysis_units}
    
    # Te conviene re-leer el PDF en modo "lineas"
    tables = tabula.read_pdf(pdf_path, pages='all', multiple_tables=True, stream=True)
    lines = []
    for tbl in tables:
        tbl = tbl.fillna('')
        for _, row in tbl.iterrows():
            row_text = ' '.join(str(val).strip() for val in row if val != '')
            row_text = re.sub(r'\s+', ' ', row_text).strip()
            if row_text:
                lines.append(row_text)
    
    resources_mapping = []
    current_analisis_code = None
    
    # Regex para detectar "XX-XX-XX-" (analisis)
    regex_analisis = re.compile(r'^(\d{2}-\d{2}-\d{2})-')
    
    for line in lines:
        # 1) Ver si la línea indica un cambio de análisis
        match_ana = regex_analisis.match(line)
        if match_ana:
            # Cambiamos de análisis
            possible_code = match_ana.group(1)
            if possible_code in codigos_analisis:
                current_analisis_code = possible_code
            else:
                current_analisis_code = None
            # no parseamos esta línea como recurso, saltamos
            continue
        
        # 2) Intentar parsear la línea como recurso
        if not current_analisis_code:
            # si no estamos dentro de un análisis conocido, no parseamos
            continue
        
        parsed = parse_resource_line(line)
        if parsed:
            # Agregamos el campo 'codigo_analisis'
            parsed['codigo_analisis'] = current_analisis_code
            resources_mapping.append(parsed)
    
    return resources_mapping


# ---------------------------
# Creación de DataFrames y guardado a CSV
# ---------------------------
def create_dataframes(analysis_units, resources):
    df_analysis = pd.DataFrame(analysis_units)
    df_resources = pd.DataFrame(resources)
    return df_analysis, df_resources

def save_to_csv(df_analysis, df_resources, analysis_path, resources_path):
    df_analysis.to_csv(analysis_path, index=False)
    df_resources.to_csv(resources_path, index=False)
    print(f"Análisis unitarios guardados en: {analysis_path}")
    print(f"Recursos guardados en: {resources_path}")


# --- MAIN ---

def main():
    pdf_path = os.path.join("data_gobernacion", "-ANALISIS UNITARIOS DECRET 1276 -2021.pdf")
    output_dir = "data_gobernacion"
    
    # 1) Extraemos análisis unitarios
    analysis_units = extract_analysis_units(pdf_path)
    
    # 2) Extraemos recursos
    resources_mapping = extract_resources(pdf_path, analysis_units)
    
    # 3) DataFrames y guardado
    df_analysis, df_resources = create_dataframes(analysis_units, resources_mapping)
    
    os.makedirs(output_dir, exist_ok=True)
    analysis_csv = os.path.join(output_dir, "analisis_unitarios.csv")
    resources_csv = os.path.join(output_dir, "recursos_analisis.csv")
    
    save_to_csv(df_analysis, df_resources, analysis_csv, resources_csv)
    
    print("\n--- MUESTRA DE ANÁLISIS UNITARIOS ---")
    print(df_analysis.head(10))
    print("\n--- MUESTRA DE RECURSOS ---")
    print(df_resources.head(10))

if __name__ == "__main__":
    main()