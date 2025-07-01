import csv

def test_import_logic():
    """Simular exactamente la lógica de importación para encontrar el error"""
    
    file_path = "TEST CAPITULOS.csv"
    
    print("=== SIMULACIÓN DE IMPORTACIÓN ===\n")
    
    with open(file_path, 'r', newline='', encoding='utf-8') as file:
        reader = csv.reader(file)
        header = next(reader, None)
        
        print(f"Header: {header}")
        print(f"Esperamos: ['Item', 'Descripción', 'Unidad', 'Cantidad', 'Costo Unitario', 'Código Análisis']")
        print()
        
        chapter_counter = 0
        rows_added = 0
        
        for row_data in reader:
            print(f"\n--- Procesando: {row_data} ---")
            
            # Saltar si la fila está vacía o es muy corta
            if not row_data or len(row_data) < 1:
                print("❌ SALTANDO: Fila vacía")
                continue
            
            # Verificar si es una fila de subtotal
            is_subtotal = (
                (row_data[0] and 'SUBTOTAL' in row_data[0].upper()) or
                (len(row_data) > 1 and row_data[1] and 'SUBTOTAL' in row_data[1].upper())
            )
            
            if is_subtotal:
                print("❌ SALTANDO: Es subtotal")
                continue
            
            # Si es una fila de capítulo
            if (row_data[0] and 
                'CAP' in row_data[0].upper() and 
                len(row_data) >= 5 and 
                all(not cell or not cell.strip() for cell in row_data[2:5])):
                
                print(f"✅ CAPÍTULO DETECTADO: {row_data[0]}")
                chapter_text = row_data[0]
                try:
                    if '.' in chapter_text and 'CAP' in chapter_text.upper():
                        parts = chapter_text.split('.', 1)
                        if len(parts) > 1:
                            name = parts[1].strip()
                        else:
                            name = chapter_text
                    else:
                        name = chapter_text
                    print(f"  Nombre del capítulo: '{name.strip()}'")
                    chapter_counter += 1
                except (ValueError, IndexError):
                    print(f"  Error al extraer, usando: '{chapter_text}'")
                continue
            
            # Si llegamos aquí, es una fila de análisis
            print("✅ ANÁLISIS DETECTADO")
            rows_added += 1
            
            # Simular el procesamiento de las columnas
            analisis_code = row_data[5] if len(row_data) > 5 else "N/A"
            print(f"  Código análisis: {analisis_code}")
            
            # Procesar las primeras 5 columnas
            for column in range(5):
                data = row_data[column] if column < len(row_data) else ""
                
                if column == 0:  # Item
                    print(f"  Item: '{data}'")
                elif column == 1:  # Descripción
                    print(f"  Descripción: '{data}'")
                elif column == 2:  # Unidad
                    print(f"  Unidad: '{data}'")
                elif column == 3:  # Cantidad
                    try:
                        cantidad = float(str(data).replace(',', '')) if data else 1.0
                        cantidad_text = str(int(cantidad)) if cantidad == int(cantidad) else str(cantidad)
                        print(f"  Cantidad: '{cantidad_text}' (original: '{data}')")
                    except (ValueError, TypeError):
                        print(f"  Cantidad: '1' (original: '{data}' - ERROR)")
                elif column == 4:  # Costo Unitario
                    try:
                        if data and str(data).strip():
                            clean_data = str(data).strip().replace('$', '').replace(',', '')
                            if clean_data:
                                value = float(clean_data)
                                formatted_value = f"${value:,.2f}"
                                print(f"  Costo Unitario: '{formatted_value}' (original: '{data}')")
                            else:
                                print(f"  Costo Unitario: '$0.00' (original vacío: '{data}')")
                        else:
                            print(f"  Costo Unitario: '$0.00' (original vacío: '{data}')")
                    except (ValueError, TypeError) as e:
                        print(f"  Costo Unitario: '$0.00' (ERROR con '{data}': {e})")
            
            print(f"  ✅ Fila de análisis #{rows_added} procesada")
        
        print(f"\n=== RESUMEN ===")
        print(f"Capítulos detectados: {chapter_counter}")
        print(f"Análisis procesados: {rows_added}")

if __name__ == "__main__":
    test_import_logic() 