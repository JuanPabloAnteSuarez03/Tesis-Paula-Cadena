# main_window.py
import sys, os
from PyQt6.QtWidgets import (
    QMainWindow, QApplication, QDockWidget, QWidget, QVBoxLayout
)
from PyQt6.QtCore import Qt

# Importa las vistas que ya tienes
from views.resource_list_view import ResourceListView
from views.presupuesto_view import PresupuestoView  # Asume que ya la tienes implementada

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("App Presupuestos")
        self.resize(1200, 800)
        self.init_ui()

    def init_ui(self):
        # Vista central: Grid de presupuestos
        self.presupuesto_view = PresupuestoView()
        self.setCentralWidget(self.presupuesto_view)

        # Dock para la lista de recursos
        self.resource_list_view = ResourceListView()
        dock_resources = QDockWidget("Recursos", self)
        dock_resources.setWidget(self.resource_list_view)
        dock_resources.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, dock_resources)

        # Si necesitas otro dock para análisis unitarios, puedes hacerlo de forma similar:
        # from views.analisis_unitario_view import AnalisisUnitarioView
        # self.analisis_view = AnalisisUnitarioView()
        # dock_analisis = QDockWidget("Análisis Unitarios", self)
        # dock_analisis.setWidget(self.analisis_view)
        # dock_analisis.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        # self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock_analisis)

        # Puedes aplicar estilos usando setStyleSheet si lo deseas
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
            QDockWidget {
                background-color: #e0e0e0;
                border: 1px solid #aaaaaa;
            }
            QTableView {
                background-color: white;
                alternate-background-color: #f9f9f9;
                gridline-color: #cccccc;
            }
            QHeaderView::section {
                background-color: #007ACC;
                color: white;
                padding: 4px;
            }
        """)

def main():
    app = QApplication(sys.argv)
    main_win = MainWindow()
    main_win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
