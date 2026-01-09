# views/recursos_por_analisis_view.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableView, QHeaderView, QPushButton, 
    QMessageBox, QLabel, QLineEdit, QDialog
)
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from PyQt6.QtCore import Qt, pyqtSignal

class RecursosPorAnalisisView(QWidget):
    # Señal para notificar cuando se selecciona un recurso (por ejemplo, desde el selector)
    resource_selected_por_analisis = pyqtSignal(str)
    
    def __init__(self, codigo_analisis, parent=None, show_form: bool = True, show_buttons: bool = True):
        super().__init__(parent)
        self.codigo_analisis = codigo_analisis
        self.setWindowTitle(f"Recursos para Análisis {codigo_analisis}")
        self.resize(800, 600)
        self.layout = QVBoxLayout(self)
        # Márgenes y espaciamiento compactos
        self.layout.setContentsMargins(8, 4, 8, 6)
        self.layout.setSpacing(2)
        
        # Encabezado compacto con el código del análisis
        header_label = QLabel(f"Recursos asociados al análisis: {codigo_analisis}")
        header_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        header_label.setStyleSheet("font-weight: bold; padding: 2px;")
        header_container = QWidget()
        header_container.setFixedHeight(22)
        hl = QHBoxLayout(header_container)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.setSpacing(0)
        hl.addWidget(header_label)
        header_container.setLayout(hl)
        self.layout.addWidget(header_container)
        
        # Formulario manual deshabilitado por redundante
        self._show_form = False
        self._show_buttons = bool(show_buttons)

        # Crear la tabla (QTableView con QStandardItemModel)
        self.create_table()
        # Botones adicionales (por ejemplo, para abrir selector o actualizar)
        if self._show_buttons:
            self.setup_buttons()
        
        self.setLayout(self.layout)
        self.setStyleSheet("""
            QTableView {
                background-color: #f9f9f9;
                alternate-background-color: #e0e0e0;
                gridline-color: #cccccc;
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
                padding: 6px 10px;
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
    
    # Formulario manual eliminado por redundante
    def clear_form_inputs(self):
        """Compat: limpiar inputs si existen."""
        for attr in [
            "codigo_input",
            "descripcion_input",
            "unidad_input",
            "cantidad_input",
            "desperdicio_input",
            "vr_unitario_input",
            "vr_parcial_input",
        ]:
            try:
                widget = getattr(self, attr, None)
                if widget:
                    widget.clear()
            except Exception:
                pass
    
    def create_table(self):
        """Crea la tabla usando QTableView y QStandardItemModel."""
        self.table = QTableView()
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels([
            "Código Recurso", "Descripción", "Unidad", "Cantidad",
            "Desperdicio", "Valor Unitario", "Valor Parcial"
        ])
        self.table.setModel(self.model)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        # Habilitar edición en todas las celdas
        from PyQt6.QtWidgets import QAbstractItemView
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.AllEditTriggers)
        # Permitir scroll interno y que la tabla expanda ocupando el espacio (botones quedan al fondo)
        from PyQt6.QtCore import Qt
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.table.setMinimumHeight(260)
        self.layout.addWidget(self.table, 1)
        # (Opcional) Conectar doble clic, si se requiere abrir un selector de recurso
        # self.table.doubleClicked.connect(lambda index: self.resource_selected_por_analisis.emit(self.model.item(index.row(), 0).text()))
    
    def setup_buttons(self):
        """Crea botones para abrir el selector y actualizar el análisis."""
        self.button_layout = QHBoxLayout()
        self.add_button = QPushButton("Adicionar Recurso")
        self.update_button = QPushButton("Actualizar Análisis")
        self.button_layout.addWidget(self.add_button)
        self.button_layout.addWidget(self.update_button)
        self.layout.addLayout(self.button_layout)
    
    def load_data(self, data):
        self.model.removeRows(0, self.model.rowCount())

        mano_obra = []
        equipo = []
        materiales = []

        for resource in data:
            codigo = str(resource.get("codigo_recurso", resource.get("codigo", ""))).upper()
            if codigo.startswith("MO"):
                mano_obra.append(resource)
            elif codigo.startswith("MQ"):
                equipo.append(resource)
            else:
                materiales.append(resource)

        def add_section_header(titulo):
            # Crea la celda con el título en la primera columna
            item_titulo = QStandardItem(titulo)
            font = item_titulo.font()
            font.setBold(True)
            item_titulo.setFont(font)
            # Quita la editabilidad
            item_titulo.setFlags(item_titulo.flags() & ~Qt.ItemFlag.ItemIsEditable)

            # Para las demás columnas, creamos items vacíos y los marcamos como no editables
            empty_items = []
            for _ in range(6):  # si son 7 columnas en total, ya usamos 1 para el título
                empty = QStandardItem("")
                empty.setFlags(empty.flags() & ~Qt.ItemFlag.ItemIsEditable)
                empty_items.append(empty)

            self.model.appendRow([item_titulo] + empty_items)

        def add_resources(resources_list):
            for res in resources_list:
                row_items = [
                    QStandardItem(str(res.get("codigo_recurso", res.get("codigo", "")))),
                    QStandardItem(str(res.get("descripcion", res.get("descripcion_recurso", "")))),
                    QStandardItem(str(res.get("unidad", res.get("unidad_recurso", "")))),
                    QStandardItem(str(res.get("cantidad", res.get("cantidad_recurso", 0)))),
                    QStandardItem(str(res.get("desperdicio", res.get("desper", 0)))),
                    QStandardItem(f"${res.get('valor_unitario', 0):,.2f}"),
                    QStandardItem(f"${res.get('valor_parcial', 0):,.2f}"),
                ]
                # Suponiendo que la columna de "Valor Parcial" es la última (índice 6),
                # deshabilitamos la edición SOLO en esa columna para las filas normales:
                row_items[6].setFlags(row_items[6].flags() & ~Qt.ItemFlag.ItemIsEditable)

                self.model.appendRow(row_items)

        # Insertar las secciones
        if mano_obra:
            add_section_header("=== MANO DE OBRA ===")
            add_resources(mano_obra)

        if equipo:
            add_section_header("====== EQUIPO ======")
            add_resources(equipo)

        if materiales:
            add_section_header("==== MATERIALES ====")
            add_resources(materiales)

        # Ajustar ancho de la primera columna
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 155)

        # Redimensionar filas a contenido y ajustar altura de la tabla para mostrar todas las filas
        self.table.resizeRowsToContents()
        try:
            header_h = self.table.horizontalHeader().height()
            rows_h = self.table.verticalHeader().length()
            frame = self.table.frameWidth() * 2
            total_h = int(header_h + rows_h + frame + 4)
            # Si no mostramos formulario, dejamos la tabla sin scroll interno mostrando todo
            if not getattr(self, '_show_form', True):
                self.table.setMinimumHeight(total_h)
                self.table.setMaximumHeight(total_h)
        except Exception:
            pass

    def get_form_data(self):
        # Obtiene los datos del formulario manual
        codigo_recurso = self.codigo_input.text().strip()
        descripcion = self.descripcion_input.text().strip()
        # ... existing code ...
