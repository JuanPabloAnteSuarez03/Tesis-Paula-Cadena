# app.py
import sys
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from controllers.main_controller import MainController
from views.start_window import StartWindow
from PyQt6.QtGui import QPalette, QIcon
from seed_local_db import ensure_local_db_ready


_main_controller = None


def launch_main(start_window: StartWindow):
    """Crea y muestra la ventana principal, cerrando el launcher."""
    global _main_controller
    _main_controller = MainController()
    _main_controller.main_window.show()
    start_window.close()


if __name__ == "__main__":
    # Forzar un AppUserModelID estable para que Windows taskbar use el icono correcto
    # del ejecutable actual (evita heredar cache de builds previos).
    try:
        if sys.platform.startswith("win"):
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Control360.Desktop.App")
    except Exception:
        pass

    # En ejecutable distribuido: crea y precarga la base local automáticamente
    # si todavía no existe o está vacía.
    ensure_local_db_ready()

    app = QApplication(sys.argv)
    try:
        logo_path = Path(__file__).resolve().parent / "logo_control_360_A.png"
        if logo_path.is_file():
            app.setWindowIcon(QIcon(str(logo_path)))
    except Exception:
        pass
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

    start = StartWindow(logo_path=str((Path(__file__).resolve().parent / "logo_control_360_S.png")))
    start.start_requested.connect(lambda: launch_main(start))
    start.show()

    sys.exit(app.exec())
