# app.py
import sys
from PyQt6.QtWidgets import QApplication
from controllers.main_controller import MainController
from views.start_window import StartWindow


_main_controller = None


def launch_main(start_window: StartWindow):
    """Crea y muestra la ventana principal, cerrando el launcher."""
    global _main_controller
    _main_controller = MainController()
    _main_controller.main_window.show()
    start_window.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    start = StartWindow()
    start.start_requested.connect(lambda: launch_main(start))
    start.show()

    sys.exit(app.exec())
