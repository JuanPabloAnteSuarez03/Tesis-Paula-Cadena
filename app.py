# app.py
import sys
from PyQt6.QtWidgets import QApplication
from controllers.main_controller import MainController

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_controller = MainController()
    # Suponiendo que MainController tenga un atributo 'main_window' que es una QMainWindow:
    main_controller.main_window.show()
    sys.exit(app.exec())
