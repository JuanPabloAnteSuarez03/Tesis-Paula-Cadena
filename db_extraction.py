import os
import pandas as pd
from db_extraction_analisis_unitarios import extract_analysis_units, extract_resources

def main():
    # Definir ruta del PDF y del directorio de salida
    pdf_path = os.path.join("data_gobernacion", "-ANALISIS UNITARIOS DECRET 1276 -2021.pdf")
    output_dir = "data_gobernacion"
    
    # Extraer análisis unitarios (para poder determinar en qué análisis estamos)
    analysis_units = extract_analysis_units(pdf_path)
    
    # Extraer recursos asociados a los análisis unitarios
    resources_mapping = extract_resources(pdf_path, analysis_units)
    
    # Convertir a DataFrame
    df_resources = pd.DataFrame(resources_mapping)
    
    # Eliminar recursos duplicados basados en el código (asumimos que "codigo_recurso" identifica al recurso)
    df_unique = df_resources.drop_duplicates(subset=['codigo_recurso'])
    
    # Seleccionar y renombrar columnas según lo solicitado:
    # Queremos las columnas: Codigo, Descripcion, Unidad, Valor Unitario
    df_unique = df_unique[['codigo_recurso', 'descripcion_recurso', 'unidad_recurso', 'vr_unitario']]
    df_unique.columns = ['Codigo', 'Descripcion', 'Unidad', 'Valor Unitario']
    
    # Definir path de salida y guardar el CSV
    output_csv = os.path.join(output_dir, "recursos_unicos.csv")
    df_unique.to_csv(output_csv, index=False, encoding="utf-8")
    print(f"Archivo CSV de recursos únicos generado exitosamente en: {output_csv}")
    
    # También se puede imprimir una muestra para verificar
    print("\nMuestra de recursos únicos:")
    print(df_unique.head())

if __name__ == "__main__":
    main()
