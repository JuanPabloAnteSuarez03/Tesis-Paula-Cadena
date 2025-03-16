# views/presupuesto_view.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox
from PyQt6.QtCore import Qt, pyqtSignal

class PresupuestoView(QWidget):
    # Señal que se emite cuando se hace doble clic en un presupuesto
    presupuesto_selected = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Presupuestos")
        self.resize(900, 600)
        self.layout = QVBoxLayout(self)
        self.table = QTableWidget(self)
        self.layout.addWidget(self.table)
        self.setup_table()
        
        # Aplicar CSS (QSS) para estilizar la vista
        self.setStyleSheet("""
            QTableWidget {
                background-color: #f9f9f9;
                gridline-color: #cccccc;
                font-size: 14px;
            }
            QHeaderView::section {
                background-color: #0078d7;
                color: white;
                padding: 4px;
                font-weight: bold;
            }
        """)
    
    def setup_table(self):
        # Definir las columnas: en este ejemplo se usan 7 columnas
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Código", "Item", "Descripción", "Unidad", "Cantidad", "Costo Unitario", "Costo Total"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        # Datos de ejemplo (dummy) para presupuestos
        sample_data = [
            {"codigo": "P001", "item": "Item A", "descripcion": "Presupuesto para obra A", "unidad": "UND", "cantidad": 10, "costo_unitario": 100.0, "costo_total": 1000.0},
            {"codigo": "P002", "item": "Item B", "descripcion": "Presupuesto para obra B", "unidad": "M2", "cantidad": 5, "costo_unitario": 200.0, "costo_total": 1000.0},
            {"codigo": "P003", "item": "Item C", "descripcion": "Presupuesto para obra C", "unidad": "ML", "cantidad": 8, "costo_unitario": 150.0, "costo_total": 1200.0}
        ]
        
        self.table.setRowCount(len(sample_data))
        for row, item in enumerate(sample_data):
            self.table.setItem(row, 0, QTableWidgetItem(item["codigo"]))
            self.table.setItem(row, 1, QTableWidgetItem(item["item"]))
            self.table.setItem(row, 2, QTableWidgetItem(item["descripcion"]))
            self.table.setItem(row, 3, QTableWidgetItem(item["unidad"]))
            self.table.setItem(row, 4, QTableWidgetItem(str(item["cantidad"])))
            self.table.setItem(row, 5, QTableWidgetItem(f"{item['costo_unitario']:.2f}"))
            self.table.setItem(row, 6, QTableWidgetItem(f"{item['costo_total']:.2f}"))
        
        # Conectar el doble clic para emitir la señal con el código del presupuesto
        self.table.cellDoubleClicked.connect(self.on_cell_double_clicked)
    
    def on_cell_double_clicked(self, row, column):
        codigo_item = self.table.item(row, 0)
        if codigo_item:
            codigo = codigo_item.text()
            self.presupuesto_selected.emit(codigo)
            # Opcional: se puede abrir la vista asociada a los análisis unitarios de este presupuesto
            # QMessageBox.information(self, "Presupuesto seleccionado", f"Se seleccionó el presupuesto: {codigo}")

# Ejemplo de uso independiente de esta vista
if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = PresupuestoView()
    window.setWindowTitle("Vista de Presupuestos")
    window.show()
    sys.exit(app.exec())
