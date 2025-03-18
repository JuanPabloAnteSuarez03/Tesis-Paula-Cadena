# views/resource_list_view.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableView, QHeaderView,
    QPushButton, QLineEdit, QLabel, QMessageBox
)
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from PyQt6.QtCore import Qt, pyqtSignal, QSortFilterProxyModel

class MultiColumnFilterProxyModel(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.code_filter = ""
        self.desc_filter = ""

    def setCodeFilter(self, code_filter):
        self.code_filter = code_filter.lower()
        self.invalidateFilter()

    def setDescFilter(self, desc_filter):
        self.desc_filter = desc_filter.lower()
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row, source_parent):
        # Obtenemos el modelo fuente
        model = self.sourceModel()
        # Columna 0 es código y columna 1 es descripción (ajusta si es necesario)
        index_code = model.index(source_row, 0, source_parent)
        index_desc = model.index(source_row, 1, source_parent)
        code = model.data(index_code, Qt.ItemDataRole.DisplayRole) or ""
        desc = model.data(index_desc, Qt.ItemDataRole.DisplayRole) or ""
        code = code.lower()
        desc = desc.lower()

        # La fila se acepta solo si se cumple que:
        # el filtro de código está contenido en el código y
        # el filtro de descripción está contenido en la descripción.
        return (self.code_filter in code) and (self.desc_filter in desc)

class ResourceListView(QWidget):
    # Señal que se emite con el código del recurso seleccionado
    resource_selected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Formulario de búsqueda
        search_layout = QHBoxLayout()
        self.search_code_input = QLineEdit()
        self.search_code_input.setPlaceholderText("Buscar por Código")
        self.search_desc_input = QLineEdit()
        self.search_desc_input.setPlaceholderText("Buscar por Descripción")
        search_layout.addWidget(QLabel("Código:"))
        search_layout.addWidget(self.search_code_input)
        search_layout.addWidget(QLabel("Descripción:"))
        search_layout.addWidget(self.search_desc_input)
        layout.addLayout(search_layout)

        # Formulario para agregar recurso (opcional)
        form_layout = QHBoxLayout()
        self.codigo_input = QLineEdit()
        self.codigo_input.setPlaceholderText("Código")
        self.descripcion_input = QLineEdit()
        self.descripcion_input.setPlaceholderText("Descripción")
        self.unidad_input = QLineEdit()
        self.unidad_input.setPlaceholderText("Unidad")
        self.valor_input = QLineEdit()
        self.valor_input.setPlaceholderText("Valor Unitario")
        self.add_button = QPushButton("Agregar Recurso")
        form_layout.addWidget(QLabel("Código:"))
        form_layout.addWidget(self.codigo_input)
        form_layout.addWidget(QLabel("Descripción:"))
        form_layout.addWidget(self.descripcion_input)
        form_layout.addWidget(QLabel("Unidad:"))
        form_layout.addWidget(self.unidad_input)
        form_layout.addWidget(QLabel("Valor Unitario:"))
        form_layout.addWidget(self.valor_input)
        form_layout.addWidget(self.add_button)
        layout.addLayout(form_layout)

        # Crear el QTableView y el modelo asociado
        self.table_view = QTableView(self)
        self.model = QStandardItemModel(self)
        self.model.setHorizontalHeaderLabels(["Código", "Descripción", "Unidad", "Valor Unitario"])

        # Configurar el proxy para filtrar en múltiples columnas
        self.proxy_model = MultiColumnFilterProxyModel(self)
        self.proxy_model.setSourceModel(self.model)
        self.table_view.setModel(self.proxy_model)
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table_view)

        # Conectar la señal de doble clic para seleccionar un recurso
        self.table_view.doubleClicked.connect(lambda index: self.on_cell_double_clicked(index.row(), index.column()))

        # Conectar señales de los inputs de búsqueda
        self.search_code_input.textChanged.connect(self.proxy_model.setCodeFilter)
        self.search_desc_input.textChanged.connect(self.proxy_model.setDescFilter)

        self.setLayout(layout)
        self.setStyleSheet("""
            QTableView {
                background-color: #f9f9f9;
                alternate-background-color: #e0e0e0;
                gridline-color: #cccccc;
            }
            QHeaderView::section {
                background-color: #007ACC;
                color: white;
                padding: 4px;
                border: 1px solid #6c6c6c;
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

        # Conectar el botón agregar (puedes conectar la lógica en el controlador)
        self.add_button.clicked.connect(self.on_add_button_clicked)

    def load_data(self, data):
        """
        Carga los datos en el modelo.
        'data' es una lista de diccionarios con las claves:
          'codigo', 'descripcion', 'unidad' y 'valor_unitario'
        """
        self.model.removeRows(0, self.model.rowCount())
        for resource in data:
            row = [
                QStandardItem(str(resource.get("codigo", ""))),
                QStandardItem(resource.get("descripcion", "")),
                QStandardItem(resource.get("unidad", "")),
                QStandardItem(str(resource.get("valor_unitario", 0)))
            ]
            self.model.appendRow(row)

    def on_cell_double_clicked(self, row, column):
        """
        Cuando se hace doble clic en una celda, se emite la señal con el código
        del recurso y se muestra un mensaje.
        """
        index = self.proxy_model.index(row, 0)
        codigo = self.proxy_model.data(index)
        if codigo:
            self.resource_selected.emit(codigo)
            QMessageBox.information(self, "Recurso Seleccionado", f"Se seleccionó: {codigo}")
            return codigo

    def on_add_button_clicked(self):
        """
        Lógica para agregar un recurso desde el formulario.
        Aquí puedes emitir una señal o actualizar directamente el modelo.
        """
        codigo = self.codigo_input.text().strip()
        descripcion = self.descripcion_input.text().strip()
        unidad = self.unidad_input.text().strip()
        try:
            valor_unitario = float(self.valor_input.text().strip())
        except ValueError:
            valor_unitario = 0.0

        if not codigo:
            QMessageBox.warning(self, "Error", "El código es obligatorio.")
            return

        row = [
            QStandardItem(codigo),
            QStandardItem(descripcion),
            QStandardItem(unidad),
            QStandardItem(str(valor_unitario))
        ]
        self.model.appendRow(row)
        # Limpiar el formulario
        self.codigo_input.clear()
        self.descripcion_input.clear()
        self.unidad_input.clear()
        self.valor_input.clear()

if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    view = ResourceListView()
    # Ejemplo de datos para probar
    sample_data = [
        {"codigo": "MOAG01", "descripcion": "MANO OBRA ALBANILERIA1 AYUDANTE", "unidad": "HC", "valor_unitario": 8949.0},
        {"codigo": "MQ0207", "descripcion": "VOLQUETA 5 M3", "unidad": "VJE", "valor_unitario": 46500.0},
        {"codigo": "MQ0301", "descripcion": "HERRAMIENTA MENOR", "unidad": "GLB", "valor_unitario": 1600.0}
    ]
    view.load_data(sample_data)
    view.setWindowTitle("Lista de Recursos con Filtro")
    view.resize(800, 400)
    view.show()
    sys.exit(app.exec())
