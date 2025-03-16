# views/main_window.py
import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
    QPushButton, QStackedWidget, QSplitter
)
from .presupuesto_view import PresupuestoView
from .resource_list_view import ResourceListView
from .analisis_unitarios_view import AnalisisUnitariosView
from .analisis_por_presupuesto_view import AnalisisPorPresupuestoView
from controllers.resource_controller import ResourceController

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("App Presupuestos - MVC")
        self.resize(1200, 800)
        self.init_ui()

    def init_ui(self):
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        self.setCentralWidget(main_widget)

        splitter = QSplitter()
        main_layout.addWidget(splitter)

        # Panel de navegación
        nav_widget = QWidget()
        nav_layout = QVBoxLayout(nav_widget)
        btn_presupuestos = QPushButton("Presupuestos")
        btn_recursos = QPushButton("Recursos")
        btn_analisis = QPushButton("Análisis Unitarios")
        nav_layout.addWidget(btn_presupuestos)
        nav_layout.addWidget(btn_recursos)
        nav_layout.addWidget(btn_analisis)
        nav_layout.addStretch()
        splitter.addWidget(nav_widget)

        # StackedWidget para las vistas
        self.stacked_widget = QStackedWidget()
        splitter.addWidget(self.stacked_widget)
        splitter.setStretchFactor(1, 1)

        # Creamos vistas iniciales
        self.presupuesto_view = PresupuestoView()
        self.analisis_view = AnalisisUnitariosView()

        # Insertamos esas vistas
        self.stacked_widget.addWidget(self.presupuesto_view)  # índice 0
        self.stacked_widget.addWidget(self.analisis_view)      # índice 1

        # Conectar los botones
        btn_presupuestos.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.presupuesto_view))
        btn_analisis.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.analisis_view))
        btn_recursos.clicked.connect(self.show_resources)

    def show_resources(self):
        """
        Carga o actualiza la vista de recursos usando ResourceController
        y la muestra en el stacked_widget.
        """
        # Crear (o reusar) el controlador
        self.resource_controller = ResourceController()
        # Obtenemos el widget de la vista
        resource_view_widget = self.resource_controller.view

        # Ver si ya está en el stacked o no
        index = self.stacked_widget.indexOf(resource_view_widget)
        if index == -1:
            # No está en el stacked, lo insertamos
            self.stacked_widget.addWidget(resource_view_widget)
            index = self.stacked_widget.indexOf(resource_view_widget)

        # Cambiar a esa vista
        self.stacked_widget.setCurrentIndex(index)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
