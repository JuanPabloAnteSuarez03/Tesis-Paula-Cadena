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
        self.articulos_dropdown = QComboBox()
        layout.addWidget(self.articulos_dropdown)

        # Botón para agregar artículos a la lista
        btn_agregar_articulo = QPushButton("Agregar Artículo")
        btn_agregar_articulo.clicked.connect(self.agregar_articulo)
        layout.addWidget(btn_agregar_articulo)

        # Lista para mostrar los artículos seleccionados
        self.lista_articulos = QListWidget()
        layout.addWidget(self.lista_articulos)

        # Lista de presupuestos existentes
        self.lista_presupuestos = QListWidget()
        layout.addWidget(self.lista_presupuestos)

        self.setLayout(layout)
        self.cargar_presupuestos()
        self.cargar_articulos()

    def guardar_presupuesto(self):
        nombre = self.input_nombre.text()
        articulos = {}
        for i in range(self.lista_articulos.count()):
            articulo_texto = self.lista_articulos.item(i).text()
            articulo_id = self.lista_articulos.item(i).data(256)  # 256 es el rol de usuario en PyQt
            cantidad, ok = QInputDialog.getDouble(self, "Cantidad", f"Cantidad para {articulo_texto}", 1, 0, 100, 1)
            if ok:
                articulos[articulo_id] = cantidad
        self.controller.crear_presupuesto(nombre, articulos)
        self.cargar_presupuestos()

    def cargar_presupuestos(self):
        self.lista_presupuestos.clear()
        presupuestos = self.controller.obtener_presupuestos()
        for p in presupuestos:
            self.lista_presupuestos.addItem(f"{p['nombre']} - ${p['costo_total']}")

    def cargar_articulos(self):
        self.articulos_dropdown.clear()
        articulos = self.controller.obtener_articulos()
        for articulo in articulos:
            self.articulos_dropdown.addItem(f"{articulo['codigo']} - {articulo['descripcion']}", articulo['id'])

    def agregar_articulo(self):
        articulo_id = self.articulos_dropdown.currentData()
        articulo_texto = self.articulos_dropdown.currentText()
        if articulo_id:
            item = f"{articulo_texto}"
            self.lista_articulos.addItem(item)
            self.lista_articulos.item(self.lista_articulos.count() - 1).setData(256, articulo_id)
