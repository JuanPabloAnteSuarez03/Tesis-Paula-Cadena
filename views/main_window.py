import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QMenuBar, QToolBar,
    QDockWidget, QListWidget, QWidget, QVBoxLayout,
    QTableView, QHBoxLayout, QLabel
)
from PyQt6.QtGui import (QIcon, QAction)
from PyQt6.QtCore import Qt

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Mi Aplicación de Presupuestos")
        self.resize(1000, 600)

        # ----- Menú Superior -----
        menu_bar = self.menuBar()  # QMenuBar por defecto en QMainWindow
        archivo_menu = menu_bar.addMenu("Archivo")
        inicio_menu = menu_bar.addMenu("Inicio")
        insertar_menu = menu_bar.addMenu("Insertar")
        datos_contables_menu = menu_bar.addMenu("Datos Contables")
        valor_ganado_menu = menu_bar.addMenu("Valor Ganado")

        # (Opcional) Agregar acciones a los menús
        accion_salir = QAction("Salir", self)
        archivo_menu.addAction(accion_salir)

        # ----- Barra de herramientas (ToolBar) -----
        toolbar = QToolBar("Barra de herramientas")
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, toolbar)

        # Botones (acciones) de ejemplo
        presupuesto_action = QAction("Presupuesto", self)
        nueva_act_action = QAction("Agregar nueva actividad", self)
        eliminar_act_action = QAction("Eliminar Actividad", self)
        editar_act_action = QAction("Editar descripción Actividad", self)
        generar_action = QAction("Generar Presupuesto", self)

        # Añadir acciones a la toolbar
        toolbar.addAction(presupuesto_action)
        toolbar.addAction(nueva_act_action)
        toolbar.addAction(eliminar_act_action)
        toolbar.addAction(editar_act_action)
        toolbar.addSeparator()
        toolbar.addAction(generar_action)

        # ----- Panel lateral izquierdo (Dock: “Recursos”) -----
        self.dock_recursos = QDockWidget("Recursos", self)
        self.dock_recursos.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea)
        # Por ejemplo, una lista para mostrar “Recursos”
        list_widget = QListWidget()
        list_widget.addItem("Recurso 1")
        list_widget.addItem("Recurso 2")
        list_widget.addItem("Recurso 3")
        self.dock_recursos.setWidget(list_widget)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.dock_recursos)

        # ----- Panel lateral derecho (opcional: “Valor Unitario”) -----
        self.dock_valor = QDockWidget("Valor Unitario", self)
        self.dock_valor.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea)
        # Aquí podrías poner un widget con información extra
        valor_label = QLabel("Detalles del Recurso / Valor Unitario", self)
        self.dock_valor.setWidget(valor_label)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.dock_valor)

        # ----- Zona Central: tabla con las columnas (Código, Item, etc.) -----
        central_widget = QWidget()
        central_layout = QVBoxLayout()
        central_widget.setLayout(central_layout)

        self.table_view = QTableView()
        # Aquí se configuraría un modelo (MVC) para la tabla.
        central_layout.addWidget(self.table_view)

        self.setCentralWidget(central_widget)

        # ----- Aplicar un estilo (CSS/QSS) -----
        self.setStyleSheet("""
            QMainWindow {
                background: #F5F5F5; /* color de fondo general */
            }
            QToolBar {
                background: #E0E0E0;
            }
            QDockWidget {
                background: #FFFFFF;
                border: 1px solid #CCCCCC;
            }
            QListWidget {
                background: #FAFAFA;
            }
            QTableView {
                gridline-color: #CCCCCC;
                selection-background-color: #A0C5E8;
                font-size: 14px;
            }
        """)

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
