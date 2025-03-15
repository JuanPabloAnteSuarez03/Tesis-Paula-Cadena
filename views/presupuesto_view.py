from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLineEdit, QLabel, QListWidget, QComboBox, QInputDialog
)
from controllers.presupuesto_controller import PresupuestoController

class PresupuestoView(QWidget):
    def __init__(self):
        super().__init__()
