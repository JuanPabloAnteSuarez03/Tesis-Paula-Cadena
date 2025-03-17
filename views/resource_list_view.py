from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableView, QHeaderView,
    QPushButton, QLineEdit, QLabel, QMessageBox
)
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from PyQt6.QtCore import Qt, pyqtSignal

class ResourceListView(QWidget):
    # Señal que se emite con el código del recurso seleccionado
    resource_selected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
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
        layout.addLayout(form_layout)
        
        # Crear el QTableView y el modelo asociado
        self.table_view = QTableView(self)
        self.model = QStandardItemModel(self)
        self.model.setHorizontalHeaderLabels(["Código", "Descripción", "Unidad", "Valor Unitario"])
        self.table_view.setModel(self.model)
        
        # Ajustar el tamaño de las columnas
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table_view)
        
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
        
        # Conectar el doble clic para emitir la señal de selección
        self.table_view.doubleClicked.connect(lambda index: self.on_cell_double_clicked(index.row(), index.column()))
    
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
        del recurso y se muestra un mensaje. Luego, se podría abrir una vista para
        ver más detalles o editar el recurso.
        """
        codigo_item = self.model.item(row, 0)
        if codigo_item:
            codigo = codigo_item.text()
            self.resource_selected.emit(codigo)
            QMessageBox.information(self, "Recurso Seleccionado", f"Se seleccionó: {codigo}")
            # Si deseas abrir otra vista, por ejemplo:
            # from views.recursos_por_analisis_view import RecursosPorAnalisisView
            return codigo

if __name__ == "__main__":
    # Para probar la vista de forma independiente
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
    view.setWindowTitle("Lista de Recursos")
    view.resize(800, 400)
    view.show()
    sys.exit(app.exec())
