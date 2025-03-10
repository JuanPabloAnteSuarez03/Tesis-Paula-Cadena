import os
import re
import pandas as pd
import tabula

def extract_analysis_units_two_step(pdf_path):
    """
    Extrae análisis unitarios y recursos de un PDF usando una estrategia de dos pasos:
      1. Detecta la línea con el análisis unitario con formato "##-##-##-DESCRIPCIÓN ... UNIDAD".
      2. Busca el valor total (línea con '$') en la misma línea o en las siguientes.
    """
    # Extraer todas las tablas del PDF y combinarlas en un DataFrame
    tables = tabula.read_pdf(pdf_path, pages='all', multiple_tables=True, stream=True)
    df = pd.concat(tables, ignore_index=True).fillna('')
    
    # Convertir cada fila del DataFrame en una cadena de texto
    lines = []
    for _, row in df.iterrows():
        row_text = ' '.join(str(val).strip() for val in row if val != '')
        row_text = re.sub(r'\s+', ' ', row_text).strip()
        if row_text:
            lines.append(row_text)

    analysis_units = []
    resources_mapping = []
    current_analysis = None
    looking_for_total = False  # Flag para esperar el valor total

    for line in lines:
        # 1) Detectar la línea de análisis unitario usando el formato "##-##-##-DESCRIPCIÓN ... UNIDAD"
        # La expresión regular se ajusta para capturar:
        #   Grupo 1: Código (formato ##-##-##)
        #   Grupo 2: Descripción (de forma no codiciosa, hasta antes de la unidad)
        #   Grupo 3: Unidad (ej: UND, M2, ML, etc.)
        match_analysis = re.search(r'^(\d{2}-\d{2}-\d{2})-(.+?)\s+(UND|M2|ML|GLN|VJE|LBS|M3|KLS|M/D|HRS|DIA|CM3|JGO|CJO|HC|CC)', line)
        if match_analysis:
            code = match_analysis.group(1).strip()
            description = match_analysis.group(2).strip()
            unit = match_analysis.group(3).strip()
            
            # Intentar extraer el valor total en la misma línea (buscando '$' al final)
            total_match = re.search(r'\$\s*([\d,\.]+)$', line)
            if total_match:
                total_str = total_match.group(1).replace(',', '').replace(' ', '')
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
                'total': total_val,
                'precio_unitario': total_val  # Se setea inicialmente; puede ajustarse posteriormente
            }
            analysis_units.append(current_analysis)
            # Si no se encontró el total en la misma línea, marcar que hay que buscarlo en líneas siguientes
            looking_for_total = (total_val == 0.0)
            continue

        # 2) Si estamos esperando el valor total para el análisis actual, buscamos una línea que contenga '$'
        if looking_for_total and current_analysis:
            total_match = re.search(r'\$\s*([\d,\.]+)', line)
            if total_match:
                total_str = total_match.group(1).replace(',', '').replace(' ', '')
                try:
                    total_val = float(total_str)
                except ValueError:
                    total_val = 0.0
                current_analysis['total'] = total_val
                current_analysis['precio_unitario'] = total_val
                # Una vez encontrado, dejamos de buscar el total para este análisis
                looking_for_total = False
                current_analysis = None
                continue

        # 3) Procesar líneas de recursos si estamos dentro de un análisis (o bien, podrías agruparlos independientemente)
        # Se asume que los recursos tienen códigos que empiezan con "MO" o "MQ" u otro prefijo definido.
        if current_analysis:
            resource_match = re.search(r'(M[OQ]\w+)-(.+)', line)
            if resource_match:
                resource_code = resource_match.group(1).strip()
                resource_desc = resource_match.group(2).strip()
                # Buscar unidad y cantidad para el recurso
                unit_match = re.search(r'(UND|M2|ML|GLN|VJE|LBS|M3|KLS|M/D|HRS|DIA|CM3|JGO|CJO|HC|CC)\s+([\d\.]+)', line)
                resource_unit = unit_match.group(1).strip() if unit_match else ''
                resource_qty = 1.0
                if unit_match:
                    try:
                        resource_qty = float(unit_match.group(2))
                    except ValueError:
                        resource_qty = 1.0
                resources_mapping.append({
                    'codigo_analisis': current_analysis['codigo'],
                    'codigo_recurso': resource_code,
                    'descripcion_recurso': resource_desc,
                    'unidad_recurso': resource_unit,
                    'cantidad_recurso': resource_qty
                })

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
