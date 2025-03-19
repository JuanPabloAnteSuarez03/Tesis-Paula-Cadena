# views/analisis_unitarios_view.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QPushButton, QLineEdit, QLabel, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from controllers.recursos_por_analisis_controller import RecursosPorAnalisisController

class PresupuestoView(QWidget):
    # Señal que se emite cuando se hace doble clic en una fila (para seleccionar un presupuesto)
    presupuesto_selected = pyqtSignal(str)
    # Señal que se emite cuando se solicita agregar un nuevo presupuesto
    add_presupuesto = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Presupuestos")
        self.resize(800, 600)
        self.layout = QVBoxLayout(self)
        self.create_form()
        self.create_search_form()
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
            QLineEdit {
                padding: 4px;
                border: 1px solid #cccccc;
                border-radius: 4px;
            }
        """)
        
    def create_form(self):
        # Formulario para agregar un nuevo análisis unitario
        self.form_layout = QHBoxLayout()
        self.codigo_input = QLineEdit()
        self.codigo_input.setPlaceholderText("Código")
        self.descripcion_input = QLineEdit()
        self.descripcion_input.setPlaceholderText("Descripción")
        self.total_input = QLineEdit()
        self.total_input.setPlaceholderText("Total")
        self.add_button = QPushButton("Agregar Presupuesto")
        self.add_button.clicked.connect(self.on_add_clicked)
        
        self.form_layout.addWidget(QLabel("Código:"))
        self.form_layout.addWidget(self.codigo_input)
        self.form_layout.addWidget(QLabel("Descripción:"))
        self.form_layout.addWidget(self.descripcion_input)
        self.form_layout.addWidget(QLabel("Total:"))
        self.form_layout.addWidget(self.total_input)
        self.form_layout.addWidget(self.add_button)
        self.layout.addLayout(self.form_layout)
    
    def create_search_form(self):
        # Formulario de búsqueda para filtrar por código y descripción
        self.search_layout = QHBoxLayout()
        self.search_code_input = QLineEdit()
        self.search_code_input.setPlaceholderText("Buscar por Código")
        self.search_desc_input = QLineEdit()
        self.search_desc_input.setPlaceholderText("Buscar por Descripción")
        # En lugar de usar un botón, conectamos directamente las señales textChanged
        self.search_code_input.textChanged.connect(self.on_search_clicked)
        self.search_desc_input.textChanged.connect(self.on_search_clicked)
        
        self.search_layout.addWidget(QLabel("Código:"))
        self.search_layout.addWidget(self.search_code_input)
        self.search_layout.addWidget(QLabel("Descripción:"))
        self.search_layout.addWidget(self.search_desc_input)
        self.layout.addLayout(self.search_layout)

    
    def create_table(self):
        """Crea la tabla para mostrar los presupuestos."""
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Código", "Descripción", "Total"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        # Habilitar el ordenamiento al hacer clic en los encabezados
        self.table.setSortingEnabled(True)
        self.layout.addWidget(self.table)
        
        # Conectar el doble clic para emitir la señal de selección
        self.table.cellDoubleClicked.connect(self.on_cell_double_clicked)

    
    def load_data(self, data):
        """
        Recibe una lista de diccionarios con las claves:
          'codigo', 'descripcion', y 'total'
        y llena la tabla.
        """
        self.table.blockSignals(True)
        self.table.setRowCount(len(data))
        for row, item in enumerate(data):
            self.table.setItem(row, 0, QTableWidgetItem(item.get("codigo", "")))
            self.table.setItem(row, 1, QTableWidgetItem(item.get("descripcion", "")))
            self.table.setItem(row, 2, QTableWidgetItem(f"{item.get('total', 0):.2f}"))
        self.table.blockSignals(False)
    
    def on_add_clicked(self):
        """
        Se dispara al presionar el botón "Agregar Presupuesto".
        Emite la señal add_presupuesto con los datos del formulario.
        """
        data = self.get_data_from_form()
        if not data["codigo"] or not data["descripcion"]:
            QMessageBox.warning(self, "Datos incompletos", "Código y Descripción son obligatorios.")
            return
        self.add_presupuesto.emit(data)
        self.clear_form()
    
    def get_data_from_form(self):
        """Lee los datos del formulario y los retorna en un diccionario."""
        codigo = self.codigo_input.text().strip()
        descripcion = self.descripcion_input.text().strip()
        try:
            total = float(self.total_input.text().strip())
        except ValueError:
            total = 0.0
        return {"codigo": codigo, "descripcion": descripcion, "total": total}
    
    def clear_form(self):
        """Limpia los campos del formulario."""
        self.codigo_input.clear()
        self.descripcion_input.clear()
        self.total_input.clear()
    
    def on_search_clicked(self):
        """Filtra la tabla en función de los campos de búsqueda."""
        code_filter = self.search_code_input.text().strip().lower()
        desc_filter = self.search_desc_input.text().strip().lower()
        
        for row in range(self.table.rowCount()):
            code_item = self.table.item(row, 0)
            desc_item = self.table.item(row, 1)
            code = code_item.text().lower() if code_item else ""
            desc = desc_item.text().lower() if desc_item else ""
            # Se muestra la fila solo si ambos filtros se cumplen
            row_visible = (code_filter in code) and (desc_filter in desc)
            self.table.setRowHidden(row, not row_visible)



    
    def on_cell_double_clicked(self, row, column):
        # Emite la señal con el código del análisis cuando se hace doble clic
        codigo_item = self.table.item(row, 0)
        if codigo_item:

            codigo = codigo_item.text()
            QMessageBox.information(self, "Presupuesto Seleccionado", f"Se seleccionó: {codigo}")
            self.presupuesto_selected.emit(codigo)

