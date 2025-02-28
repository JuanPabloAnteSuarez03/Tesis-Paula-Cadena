from PyQt6.QtWidgets import QApplication
from views.main_window import MainWindow

class MainController:
    def __init__(self):
        self.app = QApplication([])
        self.main_window = MainWindow()

    def run(self):
        self.main_window.show()
        self.app.exec()
