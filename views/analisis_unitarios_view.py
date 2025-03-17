from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QPushButton, QLineEdit, QLabel, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from .recursos_por_analisis_view import RecursosPorAnalisisView

class AnalisisUnitariosView(QWidget):
    # Señal que se emite cuando se hace doble clic en una celda (por ejemplo, para seleccionar un análisis)
    analysis_selected = pyqtSignal(str)
    # Señal que se emite cuando se solicita agregar un nuevo análisis unitario
    add_analysis = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Análisis Unitarios")
        self.resize(800, 600)
        self.layout = QVBoxLayout(self)
        self.create_form()
        self.create_table()
        self.setLayout(self.layout)
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
            QPushButton {
                background-color: #007ACC;
                color: white;
                border-radius: 4px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #005A9E;
            }
        """)

    def create_form(self):
        # Formulario para agregar un nuevo análisis unitario
        self.form_layout = QHBoxLayout()
        self.codigo_input = QLineEdit()
        self.codigo_input.setPlaceholderText("Código")
        self.descripcion_input = QLineEdit()
        self.descripcion_input.setPlaceholderText("Descripción")
        self.unidad_input = QLineEdit()
        self.unidad_input.setPlaceholderText("Unidad")
        self.total_input = QLineEdit()
        self.total_input.setPlaceholderText("Total")
        self.add_button = QPushButton("Agregar Análisis")
        # Conectar el botón al método local que recoge los datos y emite la señal
        self.add_button.clicked.connect(self.on_add_clicked)
        
        self.form_layout.addWidget(QLabel("Código:"))
        self.form_layout.addWidget(self.codigo_input)
        self.form_layout.addWidget(QLabel("Descripción:"))
        self.form_layout.addWidget(self.descripcion_input)
        self.form_layout.addWidget(QLabel("Unidad:"))
        self.form_layout.addWidget(self.unidad_input)
        self.form_layout.addWidget(QLabel("Total:"))
        self.form_layout.addWidget(self.total_input)
        self.form_layout.addWidget(self.add_button)
        self.layout.addLayout(self.form_layout)
    
    def create_table(self):
        # Crear la tabla para mostrar los análisis unitarios
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Código", "Descripción", "Unidad", "Total"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.layout.addWidget(self.table)
        
        # Conectar el doble clic para emitir la señal de selección
        self.table.cellDoubleClicked.connect(self.on_cell_double_clicked)
    
    def load_data(self, data):
        """
        Recibe una lista de diccionarios con las claves:
          'codigo', 'descripcion', 'unidad' y 'total'
        y llena la tabla.
        """
        self.table.blockSignals(True)  # Evitar que se dispare el itemChanged durante la carga
        self.table.setRowCount(len(data))
        for row, item in enumerate(data):
            self.table.setItem(row, 0, QTableWidgetItem(item.get("codigo", "")))
            self.table.setItem(row, 1, QTableWidgetItem(item.get("descripcion", "")))
            self.table.setItem(row, 2, QTableWidgetItem(item.get("unidad", "")))
            self.table.setItem(row, 3, QTableWidgetItem(f"{item.get('total', 0):.2f}"))
        self.table.blockSignals(False)
    
    def get_data_from_form(self):
        """
        Lee los datos de los campos del formulario y los retorna en un diccionario.
        """
        codigo = self.codigo_input.text().strip()
        descripcion = self.descripcion_input.text().strip()
        unidad = self.unidad_input.text().strip()
        try:
            total = float(self.total_input.text().strip())
        except ValueError:
            total = 0.0
        return {"codigo": codigo, "descripcion": descripcion, "unidad": unidad, "total": total}
    
    def clear_form(self):
        """
        Limpia los campos del formulario.
        """
        self.codigo_input.clear()
        self.descripcion_input.clear()
        self.unidad_input.clear()
        self.total_input.clear()
    
    def on_add_clicked(self):
        """
        Método que se dispara al presionar el botón "Agregar Análisis".
        Emite la señal add_analysis con los datos del formulario.
        """
        data = self.get_data_from_form()
        if not data["codigo"] or not data["descripcion"]:
            QMessageBox.warning(self, "Datos incompletos", "Código y Descripción son obligatorios.")
            return
        self.add_analysis.emit(data)
        self.clear_form()
    
    def on_cell_double_clicked(self, row, column):
        # Emite la señal con el código del análisis cuando se hace doble clic
        codigo_item = self.table.item(row, 0)
        if codigo_item:

            codigo = codigo_item.text()
            QMessageBox.information(self, "Análisis Seleccionado", f"Se seleccionó: {codigo}")
            self.analysis_selected.emit(codigo)

