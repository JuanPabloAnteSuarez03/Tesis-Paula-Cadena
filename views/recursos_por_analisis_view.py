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
    
    def __init__(self, codigo_analisis, parent=None):
        super().__init__(parent)
        self.codigo_analisis = codigo_analisis
        self.setWindowTitle(f"Recursos para Análisis {codigo_analisis}")
        self.resize(800, 600)
        self.layout = QVBoxLayout(self)
        
        # Encabezado con el código del análisis
        header_label = QLabel(f"Recursos asociados al análisis: {codigo_analisis}")
        header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(header_label)
        
        # Crear formulario para agregar recurso manualmente
        self.create_form()
        # Crear la tabla (QTableView con QStandardItemModel)
        self.create_table()
        # Se deja la función load_data vacía, ya que la invoca el controlador
        # (aquí solo se define la interfaz)
        
        # Botones adicionales (por ejemplo, para abrir selector o actualizar)
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
        """Crea el formulario para agregar un nuevo recurso manualmente."""
        self.form_layout = QHBoxLayout()
        self.codigo_input = QLineEdit()
        self.codigo_input.setPlaceholderText("Código Recurso")
        self.descripcion_input = QLineEdit()
        self.descripcion_input.setPlaceholderText("Descripción")
        self.unidad_input = QLineEdit()
        self.unidad_input.setPlaceholderText("Unidad")
        self.cantidad_input = QLineEdit()
        self.cantidad_input.setPlaceholderText("Cantidad")
        self.desperdicio_input = QLineEdit()
        self.desperdicio_input.setPlaceholderText("Desperdicio")
        self.vr_unitario_input = QLineEdit()
        self.vr_unitario_input.setPlaceholderText("Valor Unitario")
        self.vr_parcial_input = QLineEdit()
        self.vr_parcial_input.setPlaceholderText("Valor Parcial")
        self.add_form_button = QPushButton("Agregar a Tabla")
        
        self.form_layout.addWidget(QLabel("Código:"))
        self.form_layout.addWidget(self.codigo_input)
        self.form_layout.addWidget(QLabel("Descripción:"))
        self.form_layout.addWidget(self.descripcion_input)
        self.form_layout.addWidget(QLabel("Unidad:"))
        self.form_layout.addWidget(self.unidad_input)
        self.form_layout.addWidget(QLabel("Cantidad:"))
        self.form_layout.addWidget(self.cantidad_input)
        self.form_layout.addWidget(QLabel("Desperdicio:"))
        self.form_layout.addWidget(self.desperdicio_input)
        self.form_layout.addWidget(QLabel("Vr. Unitario:"))
        self.form_layout.addWidget(self.vr_unitario_input)
        self.form_layout.addWidget(QLabel("Vr. Parcial:"))
        self.form_layout.addWidget(self.vr_parcial_input)
        self.form_layout.addWidget(self.add_form_button)
        
        self.layout.addLayout(self.form_layout)
        # Nota: La conexión del botón se hará en el controlador para incluir lógica adicional
        # (pero también puede conectarse aquí si se prefiere, en este ejemplo se conecta en el controlador).
    
    def create_table(self):
        """Crea la tabla usando QTableView y QStandardItemModel."""
        self.table = QTableView()
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels([
            "Código Recurso", "Descripción", "Unidad", "Cantidad",
            "Desperdicio", "Valor Unitario", "Valor Parcial"
        ])
        self.table.setModel(self.model)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        # Habilitar edición en todas las celdas
        from PyQt6.QtWidgets import QAbstractItemView
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.AllEditTriggers)
        self.layout.addWidget(self.table)
        # (Opcional) Conectar doble clic, si se requiere abrir un selector de recurso
        # self.table.doubleClicked.connect(lambda index: self.resource_selected_por_analisis.emit(self.model.item(index.row(), 0).text()))
    
    def setup_buttons(self):
        """Crea botones para abrir el selector y actualizar el análisis."""
        self.button_layout = QHBoxLayout()
        self.add_button = QPushButton("Seleccionar Recurso")
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
                    QStandardItem(str(res.get("valor_unitario", 0))),
                    QStandardItem(str(res.get("valor_parcial", 0))),
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
