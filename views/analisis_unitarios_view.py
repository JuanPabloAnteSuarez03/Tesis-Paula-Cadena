# views/analisis_unitarios_view.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QPushButton, QLineEdit, QLabel, QMessageBox, QApplication,
    QSizePolicy
)
from PyQt6.QtCore import pyqtSignal, Qt

class AnalisisUnitariosView(QWidget):
    # Señal que se emite cuando se hace doble clic en una fila (para seleccionar un análisis)
    analysis_selected = pyqtSignal(str)
    # Nueva señal para emitir cuando se hace Shift+Click en un análisis
    analysis_edit_requested = pyqtSignal(str)
    # Señal que se emite cuando se solicita agregar un nuevo análisis unitario
    add_analysis = pyqtSignal(dict)
    # Señal que se emite cuando se solicita eliminar un análisis unitario (por código)
    analysis_delete_requested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Análisis Unitarios")
        self.resize(800, 600)
        self.layout = QVBoxLayout(self)
        
        # Cambiamos el orden: primero búsqueda, luego formulario
        self.create_search_form()
        self.create_form()
        self.create_table()
        
        self.setLayout(self.layout)
        self.setStyleSheet("""
            QTableWidget {
                background-color: #f9f9f9;
                alternate-background-color: #f0f0f0;
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
                min-width: 140px;
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
        # Control: si el usuario ya redimensionó manualmente la descripción, no auto-ajustar más
        self._desc_user_resized = False
        self._setting_desc_width = False

    def create_form(self):
        # Formulario para agregar un nuevo análisis unitario
        form_container = QWidget()
        form_layout = QVBoxLayout(form_container)
        
        # Campos del formulario arriba
        fields_layout = QHBoxLayout()
        
        self.descripcion_input = QLineEdit()
        self.descripcion_input.setPlaceholderText("Descripción")
        self.unidad_input = QLineEdit()
        self.unidad_input.setPlaceholderText("Unidad")
        
        fields_layout.addWidget(QLabel("Descripción:"))
        fields_layout.addWidget(self.descripcion_input)
        fields_layout.addWidget(QLabel("Unidad:"))
        fields_layout.addWidget(self.unidad_input)
        
        # Botones en una línea separada abajo
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch(1)  # Espacio a la izquierda para centrar
        
        # Botón de agregar análisis
        self.add_button = QPushButton("Agregar Análisis")
        self.add_button.setAccessibleName("action_button")
        self.add_button.clicked.connect(self.on_add_clicked)
        
        # Botón para eliminar análisis
        self.delete_button = QPushButton("Eliminar Análisis")
        self.delete_button.setAccessibleName("action_button")
        self.delete_button.clicked.connect(self.on_delete_clicked)
        
        buttons_layout.addWidget(self.add_button)
        buttons_layout.addWidget(self.delete_button)
        buttons_layout.addStretch(1)  # Espacio a la derecha para centrar
        
        # Añadir ambos layouts al contenedor
        form_layout.addLayout(fields_layout)
        form_layout.addLayout(buttons_layout)
        
        # Añadir el contenedor al layout principal
        self.layout.addWidget(form_container)

    def create_search_form(self):
        # Formulario de búsqueda en la parte superior
        search_container = QWidget()
        search_layout = QHBoxLayout(search_container)
        
        self.search_code_input = QLineEdit()
        self.search_code_input.setPlaceholderText("Buscar por Código")
        self.search_desc_input = QLineEdit()
        self.search_desc_input.setPlaceholderText("Buscar por Descripción")

        self.search_code_input.textChanged.connect(lambda: self.apply_filters())
        self.search_desc_input.textChanged.connect(lambda: self.apply_filters())

        search_layout.addWidget(QLabel("Código:"))
        search_layout.addWidget(self.search_code_input)
        search_layout.addWidget(QLabel("Descripción:"))
        search_layout.addWidget(self.search_desc_input)
        
        # Añadir el contenedor al layout principal
        self.layout.addWidget(search_container)

    def create_table(self):
        """Crea la tabla para mostrar los análisis unitarios."""
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Código", "Descripción", "Unidad", "Total"])
        
        header = self.table.horizontalHeader()
        # Mantener tamaños base; permitir arrastrar Descripción; el auto-ajuste lo hacemos nosotros
        header.setStretchLastSection(False)
        header.setMinimumSectionSize(60)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)   # Código
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)        # Descripción (arrastrable)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)   # Unidad
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)   # Total
        # Anchos base para primeras columnas
        self.table.setColumnWidth(0, 110)   # Código
        # Evitar que este set inicial se interprete como resize manual
        self._setting_desc_width = True
        try:
            self.table.setColumnWidth(1, 300)   # Descripción (ancho inicial, usuario ajusta)
        finally:
            self._setting_desc_width = False
        self.table.setColumnWidth(2, 90)    # Unidad
        self.table.setColumnWidth(3, 140)   # Total
        # Si el usuario arrastra la descripción, dejamos de auto-ajustarla
        try:
            header.sectionResized.connect(self._on_header_section_resized)
        except Exception:
            pass
        # Que la tabla crezca y llene el espacio disponible en el contenedor
        self.table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.table.verticalHeader().setDefaultSectionSize(28)

        # Habilitar el ordenamiento al hacer clic en los encabezados
        self.table.setSortingEnabled(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        # No permitir edición directa en la tabla
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        
        # Conectar el doble clic para emitir la señal de selección
        self.table.cellDoubleClicked.connect(self.on_cell_double_clicked)
        
        # Nueva conexión: conectar la señal cellClicked (clic simple) a la función on_cell_clicked
        self.table.cellClicked.connect(self.on_cell_clicked)
        
        # Añadir la tabla al layout principal
        self.layout.addWidget(self.table, 1)

        # Ajuste inicial para que la descripción ocupe el espacio sobrante (cuando ya haya layout)
        try:
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(0, self._auto_size_description)
        except Exception:
            pass

    def _on_header_section_resized(self, logical_index: int, _old: int, _new: int):
        # Si el resize viene de nuestro auto-ajuste, no marcar como "user resized"
        if getattr(self, "_setting_desc_width", False):
            return
        if logical_index == 1:
            self._desc_user_resized = True

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._auto_size_description()

    def showEvent(self, event):
        super().showEvent(event)
        # Asegurar auto-ajuste cuando la ventana ya está visible (viewport width válido)
        try:
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(0, self._auto_size_description)
        except Exception:
            pass

    def _auto_size_description(self):
        """
        Hace que la tabla cubra todo el ancho usando la columna Descripción como "relleno",
        sin tocarla si el usuario ya la ajustó manualmente.
        """
        try:
            if getattr(self, "_desc_user_resized", False):
                return
            if not hasattr(self, "table"):
                return
            table = self.table
            # Ancho disponible en viewport (sin headers)
            viewport_w = table.viewport().width()
            if viewport_w <= 0:
                return
            # Sumar anchos de columnas excepto descripción
            other = table.columnWidth(0) + table.columnWidth(2) + table.columnWidth(3)
            # Dejar un margen mínimo para evitar scroll horizontal por 1-2 px
            target = max(180, viewport_w - other - 8)
            self._setting_desc_width = True
            try:
                table.setColumnWidth(1, target)
            finally:
                self._setting_desc_width = False
        except Exception:
            pass

    def load_data(self, data):
        # Cargar de forma más liviana: pausar renders y sorting mientras se llena
        sorting = self.table.isSortingEnabled()
        updates = self.table.updatesEnabled()
        self.table.setUpdatesEnabled(False)
        self.table.setSortingEnabled(False)
        self.table.blockSignals(True)

        self.table.setRowCount(len(data))
        for row, item in enumerate(data):
            # Código (solo lectura)
            code_item = QTableWidgetItem(item.get("codigo", ""))
            code_item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
            self.table.setItem(row, 0, code_item)
            
            # Descripción (editable)
            descripcion = item.get("descripcion", "")
            descripcion_item = QTableWidgetItem(descripcion)
            descripcion_item.setToolTip(descripcion)
            self.table.setItem(row, 1, descripcion_item)
            
            # Unidad (solo lectura)
            und_item = QTableWidgetItem(item.get("unidad", ""))
            und_item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
            self.table.setItem(row, 2, und_item)
            
            # Total (solo lectura)
            total_value = item.get('total', 0)
            total_item = QTableWidgetItem(f"${total_value:,.2f}")
            total_item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
            self.table.setItem(row, 3, total_item)

        self.table.blockSignals(False)
        self.table.setSortingEnabled(sorting)
        self.table.setUpdatesEnabled(updates)
        # Re-ajustar descripción tras poblar datos (las otras columnas pueden cambiar con ResizeToContents)
        self._auto_size_description()

    def on_add_clicked(self):
        data = self.get_data_from_form()
        if not data["descripcion"]:
            QMessageBox.warning(self, "Datos incompletos", "La descripción es obligatoria.")
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
        descripcion = self.descripcion_input.text().strip()
        unidad = self.unidad_input.text().strip()
        return {"descripcion": descripcion, "unidad": unidad}

    def clear_form(self):
        self.descripcion_input.clear()
        self.unidad_input.clear()

    def apply_filters(self):
        """
        Aplica los filtros de búsqueda a la tabla.
        Si se proporcionan filtros, se establecen en los campos de búsqueda.
        """
        # Obtener los valores actuales de los campos de búsqueda
        code_filter = self.search_code_input.text().strip().lower()
        desc_filter = self.search_desc_input.text().strip().lower()
        
        for row in range(self.table.rowCount()):
            # Columna 0: Código, Columna 1: Descripción
            code_item = self.table.item(row, 0)
            desc_item = self.table.item(row, 1)
            
            # Obtener los textos de las celdas
            code = code_item.text().lower() if code_item else ""
            desc = desc_item.text().lower() if desc_item else ""
            
            # Aplicar los filtros de manera independiente
            code_match = True if not code_filter else code_filter in code
            desc_match = True if not desc_filter else desc_filter in desc
            
            # La fila es visible si cumple con ambos filtros
            self.table.setRowHidden(row, not (code_match and desc_match))

    def on_cell_clicked(self, row, column):
        """
        Maneja el evento de clic en una celda de la tabla.
        Si Shift está presionado, emite la señal para editar el análisis.
        """
        # Verificar si la tecla Shift está presionada
        modifiers = QApplication.keyboardModifiers()
        if modifiers & Qt.KeyboardModifier.ShiftModifier:
            codigo_item = self.table.item(row, 0)
            if codigo_item:
                codigo = codigo_item.text()
                print(f"Shift+Click en análisis: {codigo} - Abrir editor de recursos")
                self.analysis_edit_requested.emit(codigo)

    def on_cell_double_clicked(self, row, column):
        """Emite la señal con el código del análisis cuando se hace doble clic."""
        codigo_item = self.table.item(row, 0)
        if codigo_item:
            codigo = codigo_item.text()
            self.analysis_selected.emit(codigo)
