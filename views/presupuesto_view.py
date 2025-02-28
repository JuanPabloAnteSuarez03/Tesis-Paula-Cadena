from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLineEdit, QLabel, QListWidget
from controllers.presupuesto_controller import PresupuestoController

class PresupuestoView(QWidget):
    def __init__(self):
        super().__init__()

        self.controller = PresupuestoController()

        self.setWindowTitle("Presupuestos")
        self.setGeometry(200, 200, 400, 300)

        layout = QVBoxLayout()

        self.input_nombre = QLineEdit()
        self.input_nombre.setPlaceholderText("Nombre del presupuesto")
        layout.addWidget(self.input_nombre)

        self.input_costo = QLineEdit()
        self.input_costo.setPlaceholderText("Costo total")
        layout.addWidget(self.input_costo)

        self.btn_guardar = QPushButton("Guardar Presupuesto")
        self.btn_guardar.clicked.connect(self.guardar_presupuesto)
        layout.addWidget(self.btn_guardar)

        self.lista_presupuestos = QListWidget()
        layout.addWidget(self.lista_presupuestos)

        self.setLayout(layout)
        self.cargar_presupuestos()

    def guardar_presupuesto(self):
        nombre = self.input_nombre.text()
        costo_total = float(self.input_costo.text())
        self.controller.crear_presupuesto(nombre, costo_total)
        self.cargar_presupuestos()

    def cargar_presupuestos(self):
        self.lista_presupuestos.clear()
        presupuestos = self.controller.obtener_presupuestos()
        for p in presupuestos:
            self.lista_presupuestos.addItem(f"{p['nombre']} - ${p['costo_total']}")
