from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QFont
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QHBoxLayout,
    QSizePolicy,
    QSpacerItem,
)
import os


class StartWindow(QWidget):
    """
    Pantalla de inicio tipo "launcher" para mostrar el logo y un botón de arranque.
    """

    start_requested = pyqtSignal()

    def __init__(self, logo_path: str | None = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("App Presupuestos")
        self.resize(520, 400)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.FramelessWindowHint)
        self._drag_active = False
        self._drag_offset = None
        self.setStyleSheet(
            """
            QWidget {
                background-color: #0f172a;
                color: #e5e7eb;
                font-family: 'Segoe UI', sans-serif;
            }
            QPushButton {
                background-color: #2563eb;
                color: white;
                border: none;
                padding: 12px 18px;
                border-radius: 8px;
                font-size: 16px;
                font-weight: 600;
                min-width: 160px;
            }
            QPushButton:hover { background-color: #1d4ed8; }
            QPushButton:pressed { background-color: #1e40af; }
            """
        )
        self.logo_path = logo_path or "logo.png"
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(24)

        # Logo + título
        logo_box = QVBoxLayout()
        logo_box.setAlignment(Qt.AlignmentFlag.AlignCenter)

        logo_label = QLabel()
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pix = None
        if self.logo_path and os.path.isfile(self.logo_path):
            try:
                pix = QPixmap(self.logo_path)
            except Exception:
                pix = None
        if pix and not pix.isNull():
            scaled = pix.scaled(180, 180, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            logo_label.setPixmap(scaled)
        else:
            logo_label.setText("App Presupuestos")
            logo_label.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        logo_box.addWidget(logo_label)

        title = QLabel("Planificación y Presupuestos de Obra")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        subtitle = QLabel("Gestiona recursos, análisis unitarios y AIU en un solo lugar.")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #cbd5e1;")

        logo_box.addWidget(title)
        logo_box.addWidget(subtitle)

        layout.addLayout(logo_box)

        # Separador flexible
        layout.addSpacerItem(QSpacerItem(0, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        # Botonera inferior
        buttons = QHBoxLayout()
        buttons.addStretch(1)
        start_btn = QPushButton("Iniciar")
        start_btn.clicked.connect(self._emit_start)
        buttons.addWidget(start_btn)
        buttons.addStretch(1)

        layout.addLayout(buttons)

    def _emit_start(self):
        self.start_requested.emit()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_active = True
            self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_active and self._drag_offset is not None:
            self.move(event.globalPosition().toPoint() - self._drag_offset)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_active = False
            self._drag_offset = None
        super().mouseReleaseEvent(event)

