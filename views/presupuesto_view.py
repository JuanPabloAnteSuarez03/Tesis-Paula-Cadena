# views/presupuesto_view.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTableView, QHeaderView
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from PyQt6.QtCore import Qt

class PresupuestoView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        self.table_view = QTableView()
        layout.addWidget(self.table_view)
        self.setLayout(layout)

        # Configurar el encabezado del table view
        header = self.table_view.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

    def load_data(self):
        # Aquí deberías cargar los datos reales de tus presupuestos
        # Por ejemplo, desde un CSV o directamente desde el modelo de datos.
        # Para este ejemplo, crearemos algunos datos dummy.

        # Crear el modelo
        self.model = QStandardItemModel(0, 4, self)  # 0 filas, 4 columnas
        self.model.setHorizontalHeaderLabels(["Código", "Descripción", "Unidad", "Valor Total"])

        # Datos de ejemplo (puedes reemplazarlo con la carga real de datos)
        data = [
            {"codigo": "01-01-01", "descripcion": "CORTE ARBOL MAS RETIRO(INCL.RAICES)H>3.0", "unidad": "UND", "total": 106594.0},
            {"codigo": "01-01-02", "descripcion": "CORTE Y RETIRO DE ARBUSTO", "unidad": "UND", "total": 9735.0},
            {"codigo": "01-01-03", "descripcion": "DEMOL.CAMARA DE CONCRETO", "unidad": "UND", "total": 177396.0},
            {"codigo": "01-01-04", "descripcion": "DEMOL.LOSA CONCRETO E<=20CMS", "unidad": "M2", "total": 29615.0},
            {"codigo": "01-01-05", "descripcion": "DEMOL.LOSA CONCRETO E<=15CMS", "unidad": "M2", "total": 25220.0},
        ]

        for row_data in data:
            items = [
                QStandardItem(str(row_data["codigo"])),
                QStandardItem(row_data["descripcion"]),
                QStandardItem(row_data["unidad"]),
                QStandardItem(f"{row_data['total']:.2f}")
            ]
            # Opcional: alineamos los valores numéricos a la derecha
            items[-1].setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.model.appendRow(items)

        self.table_view.setModel(self.model)
