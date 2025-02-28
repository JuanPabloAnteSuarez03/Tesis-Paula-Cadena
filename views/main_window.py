from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget
from .presupuesto_view import PresupuestoView

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Gestor de Presupuestos")
        self.setGeometry(100, 100, 600, 400)

        layout = QVBoxLayout()

        btn_presupuestos = QPushButton("Gestionar Presupuestos")
        btn_presupuestos.clicked.connect(self.abrir_presupuestos)

        layout.addWidget(btn_presupuestos)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def abrir_presupuestos(self):
        self.presupuesto_window = PresupuestoView()
        self.presupuesto_window.show()
