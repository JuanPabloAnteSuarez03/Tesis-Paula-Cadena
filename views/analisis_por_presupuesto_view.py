from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QPushButton, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal

class AnalisisPorPresupuestoView(QWidget):
    prespuesto_selected = pyqtSignal(str)
    def __init__(self, codigo_presupuesto, parent=None):
        super().__init__(parent)
        self.codigo_presupuesto = codigo_presupuesto
        self.setWindowTitle(f"Análisis Unitarios para Presupuesto {codigo_presupuesto}")
        self.resize(800, 600)
        self.layout = QVBoxLayout(self)
        
        # Crear la tabla para mostrar los análisis unitarios asociados
        self.table = QTableWidget(self)
        self.layout.addWidget(self.table)
        self.setup_table()
        self.load_data()  # Aquí se cargarían los datos reales (por ejemplo, consultando la BD)
        
        # Crear los botones para agregar y actualizar
        self.setup_buttons()

    def setup_table(self):
        # Definimos 4 columnas: Código, Descripción, Unidad y Total
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Código Análisis", "Descripción", "Unidad", "Total"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    
    def load_data(self):
        # Datos de ejemplo; en la versión final estos datos vendrán de tu modelo o base de datos
        sample_data = [
            {"codigo": "01-01-01", "descripcion": "CORTE ARBOL MAS RETIRO (INCL.RAICES)H>3.0", "unidad": "UND", "total": 106594.0},
            {"codigo": "01-01-02", "descripcion": "CORTE Y RETIRO DE ARBUSTO", "unidad": "UND", "total": 9735.0},
            {"codigo": "01-01-03", "descripcion": "DEMOL.CAMARA DE CONCRETO", "unidad": "UND", "total": 177396.0},
            {"codigo": "01-01-04", "descripcion": "DEMOL.LOSA CONCRETO E<=20CMS", "unidad": "M2", "total": 29615.0},
            {"codigo": "01-01-05", "descripcion": "DEMOL.LOSA CONCRETO E<=15CMS", "unidad": "M2", "total": 25220.0}
        ]
        self.table.setRowCount(len(sample_data))
        for row, item in enumerate(sample_data):
            self.table.setItem(row, 0, QTableWidgetItem(item["codigo"]))
            self.table.setItem(row, 1, QTableWidgetItem(item["descripcion"]))
            self.table.setItem(row, 2, QTableWidgetItem(item["unidad"]))
            self.table.setItem(row, 3, QTableWidgetItem(f"{item['total']:.2f}"))
    
    def setup_buttons(self):
        # Layout horizontal para los botones
        button_layout = QHBoxLayout()
        self.add_button = QPushButton("Agregar Análisis")
        self.update_button = QPushButton("Actualizar Presupuesto")
        
        self.add_button.clicked.connect(self.add_analysis_row)
        self.update_button.clicked.connect(self.update_presupuesto)
        
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.update_button)
        self.layout.addLayout(button_layout)
    
    def add_analysis_row(self):
        # Agrega una fila vacía en la tabla para que el usuario ingrese un nuevo análisis
        row_position = self.table.rowCount()
        self.table.insertRow(row_position)
        for col in range(self.table.columnCount()):
            self.table.setItem(row_position, col, QTableWidgetItem(""))

    def update_presupuesto(self):
        # Aquí se recopilan los datos de la tabla y se actualizará el presupuesto en la BD.
        # Por ahora, mostramos un mensaje informativo.
        QMessageBox.information(self, "Actualizar Presupuesto", 
            f"Se actualizará el presupuesto {self.codigo_presupuesto} con los análisis ingresados.")
    
# Ejemplo de cómo ejecutar esta vista por sí sola (modo prueba):
if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = AnalisisPorPresupuestoView("PRESUP-001")
    window.show()
    sys.exit(app.exec())
