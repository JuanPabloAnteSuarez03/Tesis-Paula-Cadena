# views/recursos_por_analisis_view.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QPushButton, QMessageBox
)
from PyQt6.QtCore import Qt

class RecursosPorAnalisisView(QWidget):
    def __init__(self, codigo_analisis, parent=None):
        super().__init__(parent)
        self.codigo_analisis = codigo_analisis
        self.setWindowTitle(f"Recursos para Análisis {codigo_analisis}")
        self.resize(800, 600)
        self.layout = QVBoxLayout(self)
        self.table = QTableWidget(self)
        self.layout.addWidget(self.table)
        self.setup_table()
        self.load_data()  # Cargar datos de ejemplo (posteriormente se consultarán de la BD o CSV)
        self.setup_buttons()

    def setup_table(self):
        # Definir columnas de la relación: Código Recurso, Descripción, Unidad, Cantidad, Desperdicio, Valor Unitario, Valor Parcial
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Código Recurso", "Descripción", "Unidad", "Cantidad",
            "Desperdicio", "Valor Unitario", "Valor Parcial"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

    def load_data(self):
        # Datos de ejemplo (estos se reemplazarán por los datos reales)
        sample_resources = [
            {
                "codigo_recurso": "MOAG01",
                "descripcion": "MANO OBRA ALBANILERIA1 AYUDANTE",
                "unidad": "HC",
                "cantidad": 6.0,
                "desperdicio": 0.0,
                "valor_unitario": 8949.0,
                "valor_parcial": 53694.0
            },
            {
                "codigo_recurso": "MQ0207",
                "descripcion": "VOLQUETA 5 M3",
                "unidad": "VJE",
                "cantidad": 1.0,
                "desperdicio": 0.0,
                "valor_unitario": 46500.0,
                "valor_parcial": 46500.0
            }
        ]
        self.table.setRowCount(len(sample_resources))
        for row, res in enumerate(sample_resources):
            self.table.setItem(row, 0, QTableWidgetItem(res["codigo_recurso"]))
            self.table.setItem(row, 1, QTableWidgetItem(res["descripcion"]))
            self.table.setItem(row, 2, QTableWidgetItem(res["unidad"]))
            self.table.setItem(row, 3, QTableWidgetItem(str(res["cantidad"])))
            self.table.setItem(row, 4, QTableWidgetItem(str(res["desperdicio"])))
            self.table.setItem(row, 5, QTableWidgetItem(str(res["valor_unitario"])))
            self.table.setItem(row, 6, QTableWidgetItem(str(res["valor_parcial"])))
    
    def setup_buttons(self):
        # Crear un layout horizontal para los botones
        button_layout = QHBoxLayout()
        self.add_button = QPushButton("Agregar Recurso")
        self.update_button = QPushButton("Actualizar Análisis")
        
        # Conectar los botones a sus funciones
        self.add_button.clicked.connect(self.add_resource_row)
        self.update_button.clicked.connect(self.update_analysis)
        
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.update_button)
        
        self.layout.addLayout(button_layout)
    
    def add_resource_row(self):
        # Inserta una nueva fila vacía en la tabla para que el usuario la llene
        row_position = self.table.rowCount()
        self.table.insertRow(row_position)
        # Opcional: inicializar cada celda con un QTableWidgetItem vacío
        for col in range(self.table.columnCount()):
            self.table.setItem(row_position, col, QTableWidgetItem(""))
    
    def update_analysis(self):
        # Esta función se activará al presionar el botón "Actualizar Análisis"
        # Por ahora solo muestra un mensaje, en el futuro se implementará la actualización en la base de datos.
        QMessageBox.information(self, "Actualizar Análisis", 
                                f"Se actualizará el análisis {self.codigo_analisis} con los nuevos recursos ingresados.")
        # Aquí podrías recopilar los datos de la tabla y llamar a la lógica de actualización.
        
# Ejemplo de cómo ejecutar esta vista por sí sola:
if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    view = RecursosPorAnalisisView("01-01-01")
    view.show()
    sys.exit(app.exec())
