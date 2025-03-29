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
        model = self.sourceModel()
        index_code = model.index(source_row, 0, source_parent)
        index_desc = model.index(source_row, 1, source_parent)
        code = (model.data(index_code, Qt.ItemDataRole.DisplayRole) or "").lower()
        desc = (model.data(index_desc, Qt.ItemDataRole.DisplayRole) or "").lower()
        return (self.code_filter in code) and (self.desc_filter in desc)

class ResourceListView(QWidget):
    resource_delete_requested = pyqtSignal(str)
    # Señal que se emite con el código del recurso seleccionado
    resource_selected = pyqtSignal(str)
    # Señal que se emite cuando se elimina un recurso (opcional, para que el controlador lo capture)
    resource_deleted = pyqtSignal(str)
    # Señal que se emite cuando se agrega un recurso (opcional, para que el controlador lo capture)
    resource_added = pyqtSignal(dict)

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
        
        # Formulario para agregar recurso
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
        
        # Botón para eliminar recurso
        self.delete_button = QPushButton("Eliminar Recurso")
        form_layout.addWidget(self.delete_button)
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
        
        # Conectar el botón agregar
        self.add_button.clicked.connect(self.on_add_button_clicked)
        # Conectar el botón eliminar
        self.delete_button.clicked.connect(self.on_delete_button_clicked)


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


    def on_delete_button_clicked(self):
        """
        Se ejecuta al presionar el botón para eliminar un recurso.
        Verifica que se haya seleccionado una fila y solicita confirmación.
        Si se confirma, emite la señal con el código del recurso a eliminar.
        """
        # Obtener las filas seleccionadas (usamos selectedRows para obtener filas completas)
        selected_indexes = self.table_view.selectionModel().selectedRows()
        if not selected_indexes:
            QMessageBox.warning(self, "Advertencia", "Seleccione el recurso a eliminar.")
            return
        
        # Tomamos la primera fila seleccionada (puedes ampliar la funcionalidad para múltiples selecciones)
        proxy_index = selected_indexes[0]
        # Obtenemos el índice en el modelo fuente
        source_index = self.proxy_model.mapToSource(proxy_index)
        codigo_item = self.model.item(source_index.row(), 0)
        if not codigo_item:
            return
        codigo = codigo_item.text()
        
        # Confirmar la eliminación
        reply = QMessageBox.question(
            self, "Confirmar Eliminación",
            f"¿Está seguro de eliminar el recurso con código '{codigo}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            # Emitir la señal para que el controlador se encargue de eliminar el recurso en la BD
            self.resource_delete_requested.emit(codigo)

    def on_add_button_clicked(self):
        """
        Se ejecuta al presionar el botón para agregar un recurso."
        Verifica que se hayan ingresado todos los datos y emite la señal con el nuevo recurso."
        """
        codigo = self.codigo_input.text().strip()
        descripcion = self.descripcion_input.text().strip()
        unidad = self.unidad_input.text().strip()
        try:
            valor_unitario = float(self.valor_input.text().strip())
        except ValueError:
            valor_unitario = 0.0

        if not codigo or not descripcion or not unidad or valor_unitario <= 0:
            QMessageBox.warning(self, "Error", "Todos los campos son obligatorios y el valor unitario debe ser positivo.")
            return

        # Emitir la señal para que el controlador se encargue de agregar el recurso en la BD
        self.resource_added.emit({
            "codigo": codigo,
            "descripcion": descripcion,
            "unidad": unidad,
            "valor_unitario": valor_unitario
        })

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
    view.setWindowTitle("Lista de Recursos con Filtro y Eliminación")
    view.resize(800, 400)
    view.show()
    sys.exit(app.exec())
