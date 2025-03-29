# views/analisis_unitarios_view.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QPushButton, QLineEdit, QLabel, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal

class AnalisisUnitariosView(QWidget):
    # Señal que se emite cuando se hace doble clic en una fila (para seleccionar un análisis)
    analysis_selected = pyqtSignal(str)
    # Señal que se emite cuando se solicita agregar un nuevo análisis unitario
    add_analysis = pyqtSignal(dict)
    # Señal que se emite cuando se solicita eliminar un análisis unitario (por código)
    analysis_delete_requested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Análisis Unitarios")
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
        self.unidad_input = QLineEdit()
        self.unidad_input.setPlaceholderText("Unidad")
        self.total_input = QLineEdit()
        self.total_input.setPlaceholderText("Total")
        self.add_button = QPushButton("Agregar Análisis")
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

        # --- Botón para eliminar análisis ---
        self.delete_button = QPushButton("Eliminar Análisis")
        self.delete_button.clicked.connect(self.on_delete_clicked)
        self.form_layout.addWidget(self.delete_button)
        # ------------------------------------

        self.layout.addLayout(self.form_layout)

    def create_search_form(self):
        # Formulario de búsqueda
        self.search_layout = QHBoxLayout()
        self.search_code_input = QLineEdit()
        self.search_code_input.setPlaceholderText("Buscar por Código")
        self.search_desc_input = QLineEdit()
        self.search_desc_input.setPlaceholderText("Buscar por Descripción")

        self.search_code_input.textChanged.connect(self.apply_filters)
        self.search_desc_input.textChanged.connect(self.apply_filters)

        self.search_layout.addWidget(QLabel("Código:"))
        self.search_layout.addWidget(self.search_code_input)
        self.search_layout.addWidget(QLabel("Descripción:"))
        self.search_layout.addWidget(self.search_desc_input)
        self.layout.addLayout(self.search_layout)

    def create_table(self):
        """Crea la tabla para mostrar los análisis unitarios."""
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Código", "Descripción", "Unidad", "Total"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        # Habilitar el ordenamiento al hacer clic en los encabezados
        self.table.setSortingEnabled(True)
        self.layout.addWidget(self.table)
        
        # Conectar el doble clic para emitir la señal de selección
        self.table.cellDoubleClicked.connect(self.on_cell_double_clicked)

    def load_data(self, data):
        self.table.blockSignals(True)
        self.table.setRowCount(len(data))
        for row, item in enumerate(data):
            self.table.setItem(row, 0, QTableWidgetItem(item.get("codigo", "")))
            self.table.setItem(row, 1, QTableWidgetItem(item.get("descripcion", "")))
            self.table.setItem(row, 2, QTableWidgetItem(item.get("unidad", "")))
            self.table.setItem(row, 3, QTableWidgetItem(f"{item.get('total', 0):.2f}"))
        self.table.blockSignals(False)

    def on_add_clicked(self):
        data = self.get_data_from_form()
        if not data["codigo"] or not data["descripcion"]:
            QMessageBox.warning(self, "Datos incompletos", "Código y Descripción son obligatorios.")
            return
        self.add_analysis.emit(data)
        self.clear_form()

    def on_delete_clicked(self):
        """
        Se ejecuta al presionar el botón "Eliminar Análisis".
        Obtiene la fila seleccionada, pide confirmación y emite la señal si procede.
        """
        # Verificar si hay al menos una fila seleccionada
        selected_items = self.table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Sin selección", "Por favor, selecciona un análisis en la tabla.")
            return

        # Asumimos que la primera columna (código) está en la misma fila
        row = selected_items[0].row()
        codigo_item = self.table.item(row, 0)
        if not codigo_item:
            QMessageBox.warning(self, "Error", "No se pudo obtener el código del análisis seleccionado.")
            return

        codigo = codigo_item.text()

        # Confirmación
        reply = QMessageBox.question(
            self,
            "Confirmar Eliminación",
            f"¿Estás seguro de eliminar el análisis '{codigo}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            # Emitimos la señal con el código a eliminar
            self.analysis_delete_requested.emit(codigo)

    def get_data_from_form(self):
        codigo = self.codigo_input.text().strip()
        descripcion = self.descripcion_input.text().strip()
        unidad = self.unidad_input.text().strip()
        try:
            total = float(self.total_input.text().strip())
        except ValueError:
            total = 0.0
        return {"codigo": codigo, "descripcion": descripcion, "unidad": unidad, "total": total}

    def clear_form(self):
        self.codigo_input.clear()
        self.descripcion_input.clear()
        self.unidad_input.clear()
        self.total_input.clear()

    def apply_filters(self, codigo_filter="", descripcion_filter=""):
        """
        Aplica los filtros de búsqueda a la tabla.
        Si se proporcionan filtros, se establecen en los campos de búsqueda.
        """
        # Solo establecer los filtros si se proporcionan explícitamente
        if codigo_filter:
            self.search_code_input.setText(codigo_filter)
        if descripcion_filter:
            self.search_desc_input.setText(descripcion_filter)
        
        # Obtener los valores actuales de los campos de búsqueda
        code_filter = self.search_code_input.text().strip().lower()
        desc_filter = self.search_desc_input.text().strip().lower()
        
        for row in range(self.table.rowCount()):
            code_item = self.table.item(row, 0)
            desc_item = self.table.item(row, 1)
            code = code_item.text().lower() if code_item else ""
            desc = desc_item.text().lower() if desc_item else ""
            
            # Aplicar los filtros de manera independiente
            code_match = True if not code_filter else code_filter in code
            desc_match = True if not desc_filter else desc_filter in desc
            
            # La fila es visible si cumple con ambos filtros
            self.table.setRowHidden(row, not (code_match and desc_match))

    def on_cell_double_clicked(self, row, column):
        """Emite la señal con el código del análisis cuando se hace doble clic."""
        codigo_item = self.table.item(row, 0)
        if codigo_item:
            codigo = codigo_item.text()
            self.analysis_selected.emit(codigo)
