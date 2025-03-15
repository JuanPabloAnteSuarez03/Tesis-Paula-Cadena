# views/resource_list_view.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTableView, QHeaderView
from PyQt6.QtGui import QStandardItemModel, QStandardItem

class ResourceListView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        # Crear el layout vertical
        layout = QVBoxLayout(self)
        
        # Crear el QTableView y el modelo asociado
        self.table_view = QTableView(self)
        self.model = QStandardItemModel(self)
        self.model.setHorizontalHeaderLabels(["Código", "Descripción", "Unidad", "Valor Unitario"])
        self.table_view.setModel(self.model)
        
        # Ajustar el tamaño de las columnas para que se adapten al contenido
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        # Agregar el table view al layout
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
        



# Ejemplo de uso en una aplicación principal (parte del MVC)
if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication
    
    # Ejemplo de datos (estos datos vendrían de tu modelo o CSV)
    recursos = [
        {"codigo": "MOAG01", "descripcion": "MANO OBRA ALBANILERIA1 AYUDANTE", "unidad": "HC", "valor_unitario": 8949.0},
        {"codigo": "MQ0207", "descripcion": "VOLQUETA 5 M3", "unidad": "VJE", "valor_unitario": 46500.0},
        {"codigo": "MQ0301", "descripcion": "HERRAMIENTA MENOR", "unidad": "GLB", "valor_unitario": 1600.0}
    ]
    
    app = QApplication(sys.argv)
    view = ResourceListView()
    view.load_data(recursos)
    view.setWindowTitle("Lista de Recursos")
    view.resize(800, 400)
    view.show()
    sys.exit(app.exec())
