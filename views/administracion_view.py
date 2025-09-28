from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QHBoxLayout, QLabel, QHeaderView
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

class AdministracionView(QWidget):
    """Ventana para calcular los costos administrativos a partir de profesionales."""

    admin_cost_computed = pyqtSignal(float)  # Señala con el valor total calculado

    def __init__(self, profesionales, parent=None):
        """Recibe una lista de diccionarios con las claves: nombre, cargo, salario_mensual, necesario (bool)"""
        super().__init__(parent)
        self.setWindowTitle("Administración - Profesionales")
        self.resize(800, 500)
        self.profesionales = profesionales
        self._build_ui()
        self.load_profesionales()

    # ----------------- UI -----------------
    def _build_ui(self):
        layout = QVBoxLayout(self)

        # Tabla
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Profesional", "Cargo", "Salario Mensual", "% Dedicación", "Meses", "Total"
        ])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.table)

        # Etiqueta de total
        self.total_label = QLabel("Total Administración: $0.00")
        font = QFont()
        font.setBold(True)
        self.total_label.setFont(font)
        self.total_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(self.total_label)

        # Botones
        button_bar = QHBoxLayout()
        button_bar.addStretch(1)
        self.accept_btn = QPushButton("Aceptar")
        self.cancel_btn = QPushButton("Cancelar")
        self.accept_btn.clicked.connect(self._on_accept)
        self.cancel_btn.clicked.connect(self.close)
        button_bar.addWidget(self.accept_btn)
        button_bar.addWidget(self.cancel_btn)
        layout.addLayout(button_bar)

        # Conectar para recalcular
        self.table.itemChanged.connect(self._on_item_changed)

    # ----------------- Data -----------------
    def load_profesionales(self):
        self.table.setRowCount(0)
        for prof in self.profesionales:
            self._add_profesional_row(prof)
        self._recalculate_totals()

    def _add_profesional_row(self, prof):
        row = self.table.rowCount()
        self.table.insertRow(row)

        nombre_item = QTableWidgetItem(prof.get("nombre", ""))
        nombre_item.setFlags(nombre_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.table.setItem(row, 0, nombre_item)

        cargo_item = QTableWidgetItem(prof.get("cargo", ""))
        cargo_item.setFlags(cargo_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.table.setItem(row, 1, cargo_item)

        salario = float(prof.get("salario_mensual", 0.0))
        salario_item = QTableWidgetItem(f"${salario:,.2f}")
        salario_item.setFlags(salario_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.table.setItem(row, 2, salario_item)

        # % dedicación
        dedicacion_default = 100.0 if prof.get("necesario") else 0.0
        dedicacion_item = QTableWidgetItem(str(dedicacion_default))
        self.table.setItem(row, 3, dedicacion_item)

        # Meses
        meses_item = QTableWidgetItem("6")
        self.table.setItem(row, 4, meses_item)

        # Total (calculado)
        total_item = QTableWidgetItem("$0.00")
        total_item.setFlags(total_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.table.setItem(row, 5, total_item)

    # ----------------- Logic -----------------
    def _on_item_changed(self, item):
        # Solo nos interesan dedicación o meses (col 3 o 4)
        if item.column() in (3, 4):
            self._recalculate_totals()

    def _recalculate_totals(self):
        total_admin = 0.0
        for row in range(self.table.rowCount()):
            try:
                salario_text = self.table.item(row, 2).text().replace("$", "").replace(",", "").strip()
                salario = float(salario_text) if salario_text else 0.0
                dedic_text = self.table.item(row, 3).text().replace("%", "").strip()
                dedic = float(dedic_text) if dedic_text else 0.0
                meses_text = self.table.item(row, 4).text().strip()
                meses = float(meses_text) if meses_text else 0.0
                total = salario * (dedic/100.0) * meses
            except (ValueError, AttributeError):
                total = 0.0
            # Actualizar celda total
            total_item = self.table.item(row, 5)
            if total_item:
                total_item.setText(f"${total:,.2f}")
            total_admin += total
        self.total_label.setText(f"Total Administración: ${total_admin:,.2f}")
        self._current_total = total_admin

    def _on_accept(self):
        self.admin_cost_computed.emit(getattr(self, "_current_total", 0.0))
        self.close() 