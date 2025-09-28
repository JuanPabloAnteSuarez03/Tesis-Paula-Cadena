import csv

def simple_test():
    """Test simple para ver qué análisis se detectan"""
    
    file_path = "TEST CAPITULOS.csv"
    
    analysis_detected = []
    chapters_detected = []
    
    with open(file_path, 'r', newline='', encoding='utf-8') as file:
        reader = csv.reader(file)
        header = next(reader, None)
        
        for row_data in reader:
            if not row_data or len(row_data) < 1:
                continue
            
            # Verificar si es subtotal
            is_subtotal = (
                (row_data[0] and 'SUBTOTAL' in row_data[0].upper()) or
                (len(row_data) > 1 and row_data[1] and 'SUBTOTAL' in row_data[1].upper())
            )
            
            if is_subtotal:
                continue
            
            # Verificar si es capítulo
            if (row_data[0] and 
                'CAP' in row_data[0].upper() and 
                len(row_data) >= 5 and 
                all(not cell or not cell.strip() for cell in row_data[2:5])):
                
                chapters_detected.append(row_data[0])
                continue
            
            # Es análisis
            analysis_detected.append({
                'item': row_data[0],
                'desc': row_data[1][:50] if len(row_data) > 1 else '',
                'cost': row_data[4] if len(row_data) > 4 else 'N/A'
            })
    
    print(f"Capitulos detectados: {len(chapters_detected)}")
    for cap in chapters_detected:
        print(f"  - {cap}")
    
    print(f"\nAnalisis detectados: {len(analysis_detected)}")
    for i, anal in enumerate(analysis_detected, 1):
        print(f"  {i:2d}. {anal['item']} | {anal['desc']} | {anal['cost']}")

if __name__ == "__main__":
    simple_test() 