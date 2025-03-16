# analisis_unitarios_view.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox
from PyQt6.QtCore import Qt, pyqtSignal

class AnalisisUnitariosView(QWidget):
    # Señal que se emite con el código del análisis seleccionado
    analysis_selected = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Análisis Unitarios")
        self.resize(800, 600)
        self.layout = QVBoxLayout(self)
        self.table = QTableWidget(self)
        self.layout.addWidget(self.table)
        self.setup_table()
        
        # Ejemplo de aplicar CSS (QSS) a la tabla
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
        # Definimos las columnas
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Código", "Descripción", "Unidad", "Total"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        # Datos de ejemplo (en tu caso serán obtenidos de la base o del CSV)
        sample_data = [
            {"codigo": "01-01-01", "descripcion": "CORTE ARBOL MAS RETIRO (INCL.RAICES)H>3.0", "unidad": "UND", "total": 106594.0},
            {"codigo": "01-01-02", "descripcion": "CORTE Y RETIRO DE ARBUSTO", "unidad": "UND", "total": 9735.0},
            {"codigo": "01-01-03", "descripcion": "DEMOL.CAMARA DE CONCRETO", "unidad": "UND", "total": 177396.0},
            {"codigo": "01-01-04", "descripcion": "DEMOL.LOSA CONCRETO E<=20CMS", "unidad": "M2", "total": 29615.0},
            {"codigo": "01-01-05", "descripcion": "DEMOL.LOSA CONCRETO E<=15CMS", "unidad": "M2", "total": 25220.0},
        ]
        
        self.table.setRowCount(len(sample_data))
        for row, item in enumerate(sample_data):
            self.table.setItem(row, 0, QTableWidgetItem(item["codigo"]))
            self.table.setItem(row, 1, QTableWidgetItem(item["descripcion"]))
            self.table.setItem(row, 2, QTableWidgetItem(item["unidad"]))
            self.table.setItem(row, 3, QTableWidgetItem(f"{item['total']:.2f}"))
        
        # Conectar el doble clic para emitir la señal
        self.table.cellDoubleClicked.connect(self.on_cell_double_clicked)
    
    def on_cell_double_clicked(self, row, column):
        codigo_item = self.table.item(row, 0)
        if codigo_item:
            codigo = codigo_item.text()
            self.analysis_selected.emit(codigo)
            # Opcional: muestra un mensaje (o bien abre la vista de recursos)
            # QMessageBox.information(self, "Análisis seleccionado", f"Se seleccionó: {codigo}")
