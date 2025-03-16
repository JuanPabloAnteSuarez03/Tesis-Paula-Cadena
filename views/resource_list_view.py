# views/resource_list_view.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTableView, QHeaderView, QPushButton, QHBoxLayout, QLineEdit, QMessageBox
)
from PyQt6.QtGui import QStandardItemModel, QStandardItem

class ResourceListView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        # Crear el layout principal vertical
        layout = QVBoxLayout(self)
        
        # Crear el QTableView y el modelo asociado
        self.table_view = QTableView(self)
        self.model = QStandardItemModel(self)
        self.model.setHorizontalHeaderLabels(["Código", "Descripción", "Unidad", "Valor Unitario"])
        self.table_view.setModel(self.model)
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        # Agregar el table view al layout principal
        layout.addWidget(self.table_view)
        
        # Crear un layout horizontal para el botón "Agregar recurso"
        button_layout = QHBoxLayout()
        self.add_button = QPushButton("Agregar recurso")
        self.add_button.clicked.connect(self.add_resource_row)
        button_layout.addStretch()  # Empuja el botón a la derecha (opcional)
        button_layout.addWidget(self.add_button)
        
        layout.addLayout(button_layout)
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
                padding: 6px 12px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #005999;
            }
        """)
    
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
    
    def add_resource_row(self):
        """
        Agrega una nueva fila en blanco al modelo para que el usuario pueda ingresar un nuevo recurso.
        """
        blank_row = [
            QStandardItem(""),  # Código
            QStandardItem(""),  # Descripción
            QStandardItem(""),  # Unidad
            QStandardItem("")   # Valor Unitario
        ]
        self.model.appendRow(blank_row)
        QMessageBox.information(self, "Agregar recurso", "Se agregó una nueva fila. Completa los datos del recurso.")
