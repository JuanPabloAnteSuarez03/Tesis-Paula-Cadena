import os
import re
import pandas as pd
import tabula

def merge_all_pages(pdf_path):
    """
    Extrae todas las tablas de todas las páginas con tabula y las combina en un DataFrame único.
    """
    tables = tabula.read_pdf(pdf_path, pages='all', multiple_tables=True, stream=True)
    df = pd.concat(tables, ignore_index=True).fillna('')
    return df

def convert_df_to_lines(df):
    """
    Convierte cada fila del DataFrame en una sola línea de texto,
    eliminando espacios sobrantes.
    """
    lines = []
    for _, row in df.iterrows():
        row_text = ' '.join(str(val).strip() for val in row if val != '')
        row_text = re.sub(r'\s+', ' ', row_text).strip()
        if row_text:
            lines.append(row_text)
    return lines

def reconstruct_splitted_lines(lines):
    """
    (Opcional) Reconstruye líneas partidas entre páginas.
    Ajusta según tu PDF si detectas que se parte la información.
    """
    merged_lines = []
    i = 0
    while i < len(lines):
        current_line = lines[i]
        # Aquí podrías agregar lógica para unir líneas si detectas que una línea
        # termina sin ciertos tokens y la siguiente comienza con ellos.
        merged_lines.append(current_line)
        i += 1
    return merged_lines

def extract_analysis_units_two_step(pdf_path):
    """
    Extrae análisis unitarios y recursos de un PDF usando una estrategia de dos pasos:
      1) Detecta el análisis unitario con formato "##-##-##-DESCRIPCIÓN ... UNIDAD".
      2) Busca el valor total (línea con '$') en la misma o en líneas siguientes.
      3) Extrae los recursos utilizando:
           - Un regex para obtener el código de recurso y el resto del string.
           - Luego, se hace split de ese resto para identificar la descripción y, a partir del primer token que coincida con una unidad, extraer:
             [descripción, unidad, cantidad, desper, vr_unitario, vr_parcial]
    """
    df = merge_all_pages(pdf_path)
    raw_lines = convert_df_to_lines(df)
    lines = reconstruct_splitted_lines(raw_lines)

    analysis_units = []
    resources_mapping = []

    current_analysis = None
    looking_for_total = False

    # Regex para análisis unitario (no se modifica)
    regex_analisis = re.compile(r'^(\d{2}-\d{2}-\d{2})-(.+?)\s+(UND|M2|ML|GLN|VJE|LBS|M3|KLS|M/D|HRS|DIA|CM3|JGO|CJO|HC|CC)')
    regex_total = re.compile(r'\$\s*([\d,\.]+)')

    # Regex para el código de recurso: acepta M[OQ]... o 6 dígitos, con un guion opcional
    regex_resource_code = re.compile(r'^((?:M[OQ]\w+|\d{6}))\s*-?\s*(.+)$')

    # Conjunto de unidades válidas (agrega las que necesites)
    allowed_units = {'UND', 'M2', 'ML', 'GLN', 'VJE', 'LBS', 'M3', 'KLS', 'M/D', 'HRS', 'DIA', 'CM3', 'JGO', 'CJO', 'HC', 'CC', 'ROL', 'GLB', 'M3K'}

    for line in lines:
        # 1) Detectar línea de análisis unitario
        match_analisis = regex_analisis.match(line)
        if match_analisis:
            code = match_analisis.group(1).strip()
            description = match_analisis.group(2).strip()
            unit = match_analisis.group(3).strip()
            total_match = regex_total.search(line)
            if total_match:
                total_str = total_match.group(1).replace(',', '').replace('.', '')
                try:
                    total_val = float(total_str)
                except ValueError:
                    total_val = 0.0
            else:
                total_val = 0.0
            current_analysis = {
                'codigo': code,
                'descripcion': description,
                'unidad': unit,
                'total': total_val
            }
            analysis_units.append(current_analysis)
            looking_for_total = (total_val == 0.0)
            continue

        # 2) Si estamos esperando total, buscarlo en líneas siguientes
        if looking_for_total and current_analysis:
            total_match = regex_total.search(line)
            if total_match:
                total_str = total_match.group(1).replace(',', '').replace('.', '')
                try:
                    total_val = float(total_str)
                except ValueError:
                    total_val = 0.0
                current_analysis['total'] = total_val
                looking_for_total = False
                current_analysis = None
                continue

        # 3) Extraer recursos (solo si hay un análisis actual activo)
        if current_analysis:
            match_resource = regex_resource_code.match(line)
            if match_resource:
                resource_code = match_resource.group(1).strip()
                rest = match_resource.group(2).strip()
                # Dividir el resto en tokens
                tokens = rest.split()
                # Buscar el primer token que sea una unidad válida
                unit_index = None
                for idx, token in enumerate(tokens):
                    if token in allowed_units:
                        unit_index = idx
                        break
                if unit_index is not None and len(tokens) >= unit_index + 5:
                    resource_desc = " ".join(tokens[:unit_index])
                    resource_unit = tokens[unit_index]
                    try:
                        quantity = float(tokens[unit_index+1].replace('.', '').replace(',', '.'))
                    except ValueError:
                        quantity = 0.0
                    try:
                        desper = float(tokens[unit_index+2].replace('.', '').replace(',', '.'))
                    except ValueError:
                        desper = 0.0
                    try:
                        vr_unit = float(tokens[unit_index+3].replace('.', '').replace(',', '.'))
                    except ValueError:
                        vr_unit = 0.0
                    try:
                        vr_parcial = float(tokens[unit_index+4].replace('.', '').replace(',', '.'))
                    except ValueError:
                        vr_parcial = 0.0
                    resources_mapping.append({
                        'codigo_analisis': current_analysis['codigo'],
                        'codigo_recurso': resource_code,
                        'descripcion_recurso': resource_desc,
                        'unidad_recurso': resource_unit,
                        'cantidad_recurso': quantity,
                        'desper_recurso': desper,
                        'vr_unit_recurso': vr_unit,
                        'vr_parcial_recurso': vr_parcial
                    })
                else:
                    print(f"No se pudo parsear 5 columnas en la línea de recurso:\n{line}")

    return analysis_units, resources_mapping

def create_dataframes(analysis_units, resources_mapping):
    df_analysis = pd.DataFrame(analysis_units)
    df_resources_mapping = pd.DataFrame(resources_mapping)
    return df_analysis, df_resources_mapping

def save_to_csv(df_analysis, df_resources_mapping, analysis_path, mapping_path):
    df_analysis.to_csv(analysis_path, index=False)
    df_resources_mapping.to_csv(mapping_path, index=False)
    print(f"Analysis units saved to {analysis_path}")
    print(f"Resource mappings saved to {mapping_path}")

def main():
    pdf_path = os.path.join("data_gobernacion", "-ANALISIS UNITARIOS DECRET 1276 -2021.pdf")
    
    analysis_units, resources_mapping = extract_analysis_units_two_step(pdf_path)
    df_analysis, df_resources_mapping = create_dataframes(analysis_units, resources_mapping)
    
    os.makedirs("data_gobernacion", exist_ok=True)
    analysis_path = os.path.join("data_gobernacion", "analisis_unitarios.csv")
    mapping_path = os.path.join("data_gobernacion", "recursos_analisis.csv")
    
    save_to_csv(df_analysis, df_resources_mapping, analysis_path, mapping_path)
    
    print("\nSample of Analysis Units:")
    print(df_analysis.head())
    
    print("\nSample of Resource Mappings:")
    print(df_resources_mapping.head())

if __name__ == "__main__":
    main()
