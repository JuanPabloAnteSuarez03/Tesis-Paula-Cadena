from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTableView, QHeaderView, QPushButton, QHBoxLayout, QLineEdit, QLabel
from PyQt6.QtGui import QStandardItemModel, QStandardItem

class ResourceListView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Botones y campos para agregar recurso
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
        """)
    
    def load_data(self, data):
        self.model.removeRows(0, self.model.rowCount())
        for resource in data:
            row = [
                QStandardItem(str(resource.get("codigo", ""))),
                QStandardItem(resource.get("descripcion", "")),
                QStandardItem(resource.get("unidad", "")),
                QStandardItem(str(resource.get("valor_unitario", 0)))
            ]
            self.model.appendRow(row)
