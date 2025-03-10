from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLineEdit, QLabel, QListWidget, QComboBox, QInputDialog
)
from controllers.presupuesto_controller import PresupuestoController

class PresupuestoView(QWidget):
    def __init__(self):
        super().__init__()

        self.controller = PresupuestoController()

        self.setWindowTitle("Presupuestos")
        self.setGeometry(200, 200, 400, 400)

        layout = QVBoxLayout()

        self.input_nombre = QLineEdit()
        self.input_nombre.setPlaceholderText("Nombre del presupuesto")
        layout.addWidget(self.input_nombre)

        self.btn_guardar = QPushButton("Guardar Presupuesto")
        self.btn_guardar.clicked.connect(self.guardar_presupuesto)
        layout.addWidget(self.btn_guardar)

        # Dropdown para seleccionar artículos
        self.recursos_dropdown = QComboBox()
        layout.addWidget(self.recursos_dropdown)

        # Botón para agregar artículos a la lista
        btn_agregar_recurso = QPushButton("Agregar Recurso")
        btn_agregar_recurso.clicked.connect(self.agregar_recurso)
        layout.addWidget(btn_agregar_recurso)

        # Lista para mostrar los artículos seleccionados
        self.lista_recursos = QListWidget()
        layout.addWidget(self.lista_recursos)

        # Lista de presupuestos existentes
        self.lista_presupuestos = QListWidget()
        layout.addWidget(self.lista_presupuestos)

        self.setLayout(layout)
        self.cargar_presupuestos()
        self.cargar_recursos()

    def guardar_presupuesto(self):
        nombre = self.input_nombre.text()
        recursos = {}
        for i in range(self.lista_recursos.count()):
            recurso_texto = self.lista_recursos.item(i).text()
            recurso_id = self.lista_recursos.item(i).data(256)  # 256 es el rol de usuario en PyQt
            cantidad, ok = QInputDialog.getDouble(self, "Cantidad", f"Cantidad para {recurso_texto}", 1, 0, 100, 1)
            if ok:
                recursos[recurso_id] = cantidad
        self.controller.crear_presupuesto(nombre, recursos)
        self.cargar_presupuestos()

    def cargar_presupuestos(self):
        self.lista_presupuestos.clear()
        presupuestos = self.controller.obtener_presupuestos()
        for p in presupuestos:
            self.lista_presupuestos.addItem(f"{p['nombre']} - ${p['costo_total']}")

    def cargar_recursos(self):
        self.recursos_dropdown.clear()
        recursos = self.controller.obtener_recursos()
        for recurso in recursos:
            self.recursos_dropdown.addItem(f"{recurso['codigo']} - {recurso['descripcion']}", recurso['id'])

    def agregar_recurso(self):
        recurso_id = self.recursos_dropdown.currentData()
        recurso_texto = self.recursos_dropdown.currentText()
        if recurso_id:
            item = f"{recurso_texto}"
            self.lista_recursos.addItem(item)
            self.lista_recursos.item(self.lista_recursos.count() - 1).setData(256, recurso_id)
