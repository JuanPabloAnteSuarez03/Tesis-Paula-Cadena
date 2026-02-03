# app.py
import sys
from PyQt6.QtWidgets import QApplication
from controllers.main_controller import MainController
from views.start_window import StartWindow
from PyQt6.QtGui import QPalette


_main_controller = None


def launch_main(start_window: StartWindow):
    """Crea y muestra la ventana principal, cerrando el launcher."""
    global _main_controller
    _main_controller = MainController()
    _main_controller.main_window.show()
    start_window.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    # Forzar paleta clara si el sistema está en modo oscuro (invertir a clara)
    try:
        pal = app.palette()
        if pal.color(QPalette.ColorRole.Window).lightness() < 128:
            app.setPalette(app.style().standardPalette())
    except Exception:
        pass

    # Estilos globales para hover/selección visibles (modo oscuro y claro)
    app.setStyleSheet(
        """
        QTableWidget::item:hover,
        QTableView::item:hover,
        QTreeWidget::item:hover {
            background-color: #e6f2ff;
        }
        QTableWidget::item:selected,
        QTableView::item:selected,
        QTreeWidget::item:selected {
            background-color: #cce8ff;
            color: #000000;
        }
        QTableWidget::item:selected:active,
        QTableView::item:selected:active,
        QTreeWidget::item:selected:active {
            background-color: #b6ddff;
            color: #000000;
        }
        """
    )

    start = StartWindow()
    start.start_requested.connect(lambda: launch_main(start))
    start.show()

    sys.exit(app.exec())
