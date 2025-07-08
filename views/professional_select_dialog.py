from __future__ import annotations

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton,
    QHBoxLayout, QLineEdit, QDoubleSpinBox, QCheckBox, QLabel, QFormLayout, QMessageBox, QHeaderView
)
from PyQt6.QtCore import Qt, pyqtSignal
from models.database import SessionLocal
from models.profesional import Profesional

class ProfessionalSelectDialog(QDialog):
    """Permite seleccionar un profesional existente o crear uno nuevo."""

    professional_selected = pyqtSignal(dict)

    def __init__(self, already_added_codes: set[str], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Seleccionar Profesional")
        self.resize(600, 400)
        self.already_added = already_added_codes
        self._build_ui()
        self._load_profesionales()

    # ----------------- UI -----------------
    def _build_ui(self):
        layout = QVBoxLayout(self)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            "Nombre", "Cargo", "Salario Mensual", "Necesario"
        ])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.table)

        # Buttons
        btn_bar = QHBoxLayout()
        add_btn = QPushButton("Agregar Seleccionado")
        new_btn = QPushButton("Nuevo Profesional")
        cancel_btn = QPushButton("Cancelar")
        add_btn.clicked.connect(self._on_add)
        new_btn.clicked.connect(self._on_new)
        cancel_btn.clicked.connect(self.reject)
        btn_bar.addStretch(1)
        btn_bar.addWidget(add_btn)
        btn_bar.addWidget(new_btn)
        btn_bar.addWidget(cancel_btn)
        layout.addLayout(btn_bar)

    # ----------------- Data -----------------
    def _load_profesionales(self):
        session = SessionLocal()
        try:
            profs = session.query(Profesional).all()
            self.table.setRowCount(0)
            for p in profs:
                if p.nombre in self.already_added:
                    continue
                row = self.table.rowCount()
                self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(p.nombre))
                self.table.setItem(row, 1, QTableWidgetItem(p.cargo))
                self.table.setItem(row, 2, QTableWidgetItem(f"${p.salario_mensual:,.2f}"))
                self.table.setItem(row, 3, QTableWidgetItem("Sí" if p.necesario else "No"))
        finally:
            session.close()

    # ----------------- Slots -----------------
    def _on_add(self):
        row = self.table.currentRow()
        if row == -1:
            QMessageBox.warning(self, "Seleccione", "Seleccione un profesional de la lista")
            return
        nombre = self.table.item(row, 0).text()
        session = SessionLocal()
        try:
            p = session.query(Profesional).filter_by(nombre=nombre).first()
            if p:
                self.professional_selected.emit({
                    'nombre': p.nombre,
                    'cargo': p.cargo,
                    'salario_mensual': p.salario_mensual,
                    'necesario': p.necesario,
                })
                self.accept()
        finally:
            session.close()

    def _on_new(self):
        dlg = NewProfessionalDialog(parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            prof_dict = dlg.get_professional()
            # Insert into DB
            session = SessionLocal()
            try:
                p = Profesional(
                    nombre=prof_dict['nombre'],
                    cargo=prof_dict['cargo'],
                    salario_mensual=prof_dict['salario_mensual'],
                    necesario=prof_dict['necesario']
                )
                session.add(p)
                session.commit()
            except Exception as e:
                session.rollback()
                QMessageBox.critical(self, "Error", str(e))
                session.close()
                return
            finally:
                session.close()

            # Emit and close
            self.professional_selected.emit(prof_dict)
            self.accept()

class NewProfessionalDialog(QDialog):
    """Dialogo simple para crear profesional"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nuevo Profesional")
        self.resize(400, 300)
        layout = QFormLayout(self)

        self.nombre_edit = QLineEdit()
        self.cargo_edit = QLineEdit()
        self.salario_spin = QDoubleSpinBox()
        self.salario_spin.setRange(0, 1e9)
        self.salario_spin.setPrefix("$")
        self.salario_spin.setDecimals(2)
        self.necesario_chk = QCheckBox("Obligatorio")

        layout.addRow("Nombre", self.nombre_edit)
        layout.addRow("Cargo", self.cargo_edit)
        layout.addRow("Salario Mensual", self.salario_spin)
        layout.addRow(self.necesario_chk)

        btn_bar = QHBoxLayout()
        ok_btn = QPushButton("Crear")
        cancel_btn = QPushButton("Cancelar")
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        btn_bar.addStretch(1)
        btn_bar.addWidget(ok_btn)
        btn_bar.addWidget(cancel_btn)
        layout.addRow(btn_bar)

    def accept(self):
        if not self.nombre_edit.text().strip():
            QMessageBox.warning(self, "Campo requerido", "Ingrese un nombre")
            return
        if self.salario_spin.value() <= 0:
            QMessageBox.warning(self, "Campo requerido", "Ingrese un salario válido")
            return
        super().accept()

    def get_professional(self) -> dict:
        return {
            'nombre': self.nombre_edit.text().strip(),
            'cargo': self.cargo_edit.text().strip() or self.nombre_edit.text().strip(),
            'salario_mensual': self.salario_spin.value(),
            'necesario': self.necesario_chk.isChecked(),
        } 