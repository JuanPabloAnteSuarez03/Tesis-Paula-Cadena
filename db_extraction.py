import PyPDF2
import pandas as pd
import re
import os

# Ruta del archivo PDF
pdf_path = os.path.join("data_gobernacion", "-ANALISIS UNITARIOS DECRET 1276 -2021.pdf")

# Extraer texto del PDF
with open(pdf_path, "rb") as file:
    pdf_reader = PyPDF2.PdfReader(file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text() if page.extract_text() else ""

# Expresión regular para extraer los artículos
pattern = r"(\S+)-(.+?)\s([A-Z]+)\s([\d,\.]+)\s([\d,\.]+)\s([\d,\.]+)\s([\d,\.]+)"
matches = re.findall(pattern, text)

# Crear un DataFrame con los datos extraídos
columns = ["Codigo", "Descripcion", "Unidad", "Cantidad", "Desperdicio", "Valor Unitario", "Valor Parcial"]
df = pd.DataFrame(matches, columns=columns)

# Limpiar y convertir las columnas numéricas
df["Cantidad"] = df["Cantidad"].str.replace(".", "", regex=False).str.replace(",", ".", regex=False).astype(float)
df["Desperdicio"] = df["Desperdicio"].str.replace(".", "", regex=False).str.replace(",", ".", regex=False).astype(float)
df["Valor Unitario"] = df["Valor Unitario"].str.replace(".", "", regex=False).str.replace(",", "", regex=False).astype(float)
df["Valor Parcial"] = df["Valor Parcial"].str.replace(".", "", regex=False).str.replace(",", "", regex=False).astype(float)

# Mostrar las primeras filas para verificar la estructura
print(df.head())

# Exportar el DataFrame a un archivo CSV
csv_path = os.path.join("data_gobernacion", "articulos_obras.csv")
df.to_csv(csv_path, index=False, encoding="utf-8")

print(f"Archivo CSV generado exitosamente en: {csv_path}")

# Carga el archivo CSV
df = pd.read_csv('data_gobernacion/articulos_obras.csv')

# Elimina filas con códigos duplicados, conservando solo la primera aparición
df_unicos = df.drop_duplicates(subset=['Codigo'])

# Selecciona solo las columnas deseadas
df_resultado = df_unicos[['Codigo', 'Descripcion', 'Unidad', 'Valor Unitario']]

# Guarda el resultado en un nuevo archivo CSV (opcional)
df_resultado.to_csv('data_gobernacion/articulos_unicos.csv', index=False)

print(df_resultado)

