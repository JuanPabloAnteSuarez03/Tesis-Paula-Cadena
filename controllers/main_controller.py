# controllers/main_controller.py
import sys
from PyQt6.QtWidgets import QApplication
from views.main_window import MainWindow

class MainController:
    def __init__(self):
        # Instanciar la vista principal
        self.main_window = MainWindow()

    def run(self):
        self.main_window.show()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    controller = MainController()
    controller.run()
    sys.exit(app.exec())
