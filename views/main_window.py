import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
    QPushButton, QStackedWidget, QSplitter
)
from PyQt6.QtCore import Qt
from .presupuesto_view import PresupuestoView
from .resource_list_view import ResourceListView
from .analisis_unitarios_view import AnalisisUnitariosView
from .recursos_por_analisis_view import RecursosPorAnalisisView
from .analisis_por_presupuesto_view import AnalisisPorPresupuestoView

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("App Presupuestos - MVC")
        self.resize(1200, 800)
        self.init_ui()

    def init_ui(self):
        # Widget principal y layout horizontal
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        self.setCentralWidget(main_widget)

        # Usamos un QSplitter para dividir el panel de navegación y la vista central
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)

        # Panel de navegación (botones)
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

        # Panel central: QStackedWidget con nuestras tres vistas
        self.stacked_widget = QStackedWidget()
        self.presupuesto_view = PresupuestoView()
        self.resource_list_view = ResourceListView()
        self.analisis_view = AnalisisUnitariosView()
        self.stacked_widget.addWidget(self.presupuesto_view)   # índice 0
        self.stacked_widget.addWidget(self.resource_list_view)   # índice 1
        self.stacked_widget.addWidget(self.analisis_view)        # índice 2
        splitter.addWidget(self.stacked_widget)
        splitter.setStretchFactor(1, 1)

        # Conexión de los botones de navegación para cambiar la vista
        btn_presupuestos.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        btn_recursos.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))
        btn_analisis.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(2))

        # Conectar la señal de selección de análisis unitario
        self.analisis_view.analysis_selected.connect(self.on_analysis_selected)
        self.presupuesto_view.presupuesto_selected.connect(self.on_presupuesto_selected)

    # En tu main_window.py, en el método on_analysis_selected:
    def on_analysis_selected(self, codigo):
        # Crear la vista de recursos para el análisis seleccionado
        self.recursos_por_analisis_view = RecursosPorAnalisisView(codigo)
        self.recursos_por_analisis_view.show()

    def on_presupuesto_selected(self, codigo):
        # Crear la vista de análisis por presupuesto
        self.analisis_por_presupuesto_view = AnalisisPorPresupuestoView(codigo)
        self.analisis_por_presupuesto_view.show()
if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Ejemplo de hoja de estilo para la aplicación
    app.setStyleSheet("""
        QPushButton {
            background-color: #007ACC;
            color: white;
            border-radius: 4px;
            padding: 8px;
        }
        QPushButton:hover {
            background-color: #005A9E;
        }
    """)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())
