from __future__ import annotations

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, QLabel,
    QPushButton, QHBoxLayout, QHeaderView, QDoubleSpinBox, QFormLayout, QWidget, QCheckBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

class AdministracionWindow(QDialog):
    """Diálogo para calcular AIU (Administración, Imprevistos, Utilidad, IVA)."""

    aiu_computed = pyqtSignal(dict)  # Emite total de costos indirectos

    def __init__(self, profesionales: list[dict], costo_directo: float, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("Costos Indirectos (AIU)")
        self.resize(900, 600)
        self.profesionales = profesionales
        self.costo_directo = costo_directo
        self._build_ui()
        self._load_profesionales()
        self._recalculate()

    # ---------- UI ----------
    def _build_ui(self):
        layout = QVBoxLayout(self)

        # Tabla profesionales
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

        # Percentages form
        form_widget = QWidget()
        form_layout = QFormLayout(form_widget)

        self.admin_target_spin = QDoubleSpinBox()
        self.admin_target_spin.setSuffix(" %")
        self.admin_target_spin.setRange(0, 100)
        self.admin_target_spin.setValue(10.0)
        self.admin_target_spin.setSingleStep(0.1)

        self.imprev_spin = QDoubleSpinBox()
        self.imprev_spin.setSuffix(" %")
        self.imprev_spin.setRange(0, 100)
        self.imprev_spin.setValue(5.0)
        self.imprev_spin.setSingleStep(0.1)

        self.util_spin = QDoubleSpinBox()
        self.util_spin.setSuffix(" %")
        self.util_spin.setRange(0, 100)
        self.util_spin.setValue(5.0)
        self.util_spin.setSingleStep(0.1)

        self.iva_spin = QDoubleSpinBox()
        self.iva_spin.setSuffix(" %")
        self.iva_spin.setRange(0, 100)
        self.iva_spin.setValue(19.0)
        self.iva_spin.setSingleStep(0.1)

        form_layout.addRow("Administración objetivo", self.admin_target_spin)
        form_layout.addRow("Imprevistos", self.imprev_spin)
        form_layout.addRow("Utilidad", self.util_spin)
        form_layout.addRow("IVA sobre Utilidad", self.iva_spin)
        layout.addWidget(form_widget)

        # Totales
        self.tot_admin_lbl = QLabel("Administración: $0.00")
        self.tot_imprev_lbl = QLabel("Imprevistos: $0.00")
        self.tot_util_lbl = QLabel("Utilidad: $0.00")
        self.tot_iva_lbl = QLabel("IVA Utilidad: $0.00")
        self.tot_aiu_lbl = QLabel("Total Costos Indirectos: $0.00")
        bold = QFont()
        bold.setBold(True)
        self.tot_aiu_lbl.setFont(bold)

        for lbl in [self.tot_admin_lbl, self.tot_imprev_lbl, self.tot_util_lbl, self.tot_iva_lbl, self.tot_aiu_lbl]:
            lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
            layout.addWidget(lbl)

        # Controls row for checkbox and add button
        ctrl_bar = QHBoxLayout()
        self.include_chk = QCheckBox("Agregar recomendados")
        self.include_chk.setChecked(True)
        auto_btn = QPushButton("Auto-ajustar")
        auto_btn.clicked.connect(self._on_auto_adjust)
        add_prof_btn = QPushButton("Agregar profesional…")
        add_prof_btn.clicked.connect(self._on_add_professional)
        self.include_chk.stateChanged.connect(self._reload_based_on_checkbox)
        ctrl_bar.addWidget(self.include_chk)
        ctrl_bar.addWidget(auto_btn)
        ctrl_bar.addWidget(add_prof_btn)
        layout.addLayout(ctrl_bar)

        # Botones
        btn_bar = QHBoxLayout()
        btn_bar.addStretch(1)
        accept_btn = QPushButton("Aceptar")
        cancel_btn = QPushButton("Cancelar")
        accept_btn.clicked.connect(self._on_accept)
        cancel_btn.clicked.connect(self.reject)
        btn_bar.addWidget(accept_btn)
        btn_bar.addWidget(cancel_btn)
        layout.addLayout(btn_bar)

        # Conexiones
        self.table.itemChanged.connect(self._recalculate)
        self.admin_target_spin.valueChanged.connect(self._recalculate)
        self.imprev_spin.valueChanged.connect(self._recalculate)
        self.util_spin.valueChanged.connect(self._recalculate)
        self.iva_spin.valueChanged.connect(self._recalculate)

    # ---------- Data ----------
    def _load_profesionales(self, only_necess: bool = True):
        self.table.setRowCount(0)
        for prof in self.profesionales:
            if only_necess and not prof.get("necesario", False):
                continue
            self._add_row(prof)

    def _add_row(self, prof):
        row = self.table.rowCount()
        self.table.insertRow(row)
        # Profesional
        nombre_item = QTableWidgetItem(prof.get("nombre", ""))
        nombre_item.setFlags(nombre_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.table.setItem(row, 0, nombre_item)
        # Cargo
        cargo_item = QTableWidgetItem(prof.get("cargo", ""))
        cargo_item.setFlags(cargo_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.table.setItem(row, 1, cargo_item)
        # Salario
        salario = float(prof.get("salario_mensual", 0.0))
        salario_item = QTableWidgetItem(f"${salario:,.2f}")
        salario_item.setFlags(salario_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.table.setItem(row, 2, salario_item)
        # % dedicación
        dedic_default = 100.0 if prof.get("necesario", False) else 0.0
        dedic_item = QTableWidgetItem(str(dedic_default))
        self.table.setItem(row, 3, dedic_item)
        # Meses
        meses_item = QTableWidgetItem("1")
        self.table.setItem(row, 4, meses_item)
        # Total
        total_item = QTableWidgetItem("$0.00")
        total_item.setFlags(total_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.table.setItem(row, 5, total_item)

    # ---------- Logic ----------
    def _recalculate(self):
        admin_total = 0.0
        for row in range(self.table.rowCount()):
            salario_item = self.table.item(row, 2)
            if not salario_item:
                continue
            salario_text = salario_item.text().replace("$", "").replace(",", "").strip()
            try:
                salario = float(salario_text) if salario_text else 0.0
            except ValueError:
                salario = 0.0

            def _to_float(item_idx):
                item = self.table.item(row, item_idx)
                if item is None:
                    return 0.0
                try:
                    return float(item.text())
                except ValueError:
                    return 0.0

            dedic = _to_float(3)
            meses = _to_float(4)
            total = salario * (dedic/100.0) * meses
            total_item = self.table.item(row, 5)
            if total_item is None:
                total_item = QTableWidgetItem()
                total_item.setFlags(total_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(row, 5, total_item)
            total_item.setText(f"${total:,.2f}")
            admin_total += total

        imp_pct = self.imprev_spin.value()
        util_pct = self.util_spin.value()
        iva_pct = self.iva_spin.value()

        imprev_total = self.costo_directo * (imp_pct / 100.0)
        util_total = self.costo_directo * (util_pct / 100.0)
        iva_total = util_total * (iva_pct / 100.0)

        total_aiu = admin_total + imprev_total + util_total + iva_total

        # Actualizar etiquetas
        self.tot_admin_lbl.setText(f"Administración: ${admin_total:,.2f}")
        self.tot_imprev_lbl.setText(f"Imprevistos ({imp_pct:.2f}%): ${imprev_total:,.2f}")
        self.tot_util_lbl.setText(f"Utilidad ({util_pct:.2f}%): ${util_total:,.2f}")
        self.tot_iva_lbl.setText(f"IVA Utilidad ({iva_pct:.2f}%): ${iva_total:,.2f}")
        self.tot_aiu_lbl.setText(f"Total Costos Indirectos: ${total_aiu:,.2f}")

        self._admin_total = admin_total
        self._imprev_total = imprev_total
        self._util_total = util_total
        self._iva_total = iva_total
        self._current_aiu = total_aiu

    # ---------- Slots ----------
    def _on_accept(self):
        self.aiu_computed.emit({
            'admin': getattr(self, '_admin_total', 0.0),
            'imprev': getattr(self, '_imprev_total', 0.0),
            'util': getattr(self, '_util_total', 0.0),
            'iva': getattr(self, '_iva_total', 0.0),
            'imprev_pct': self.imprev_spin.value(),
            'util_pct': self.util_spin.value(),
            'iva_pct': self.iva_spin.value(),
            'total_aiu': getattr(self, '_current_aiu', 0.0)
        })
        self.accept()

    def _reload_based_on_checkbox(self):
        if self.include_chk.isChecked():
            self._load_profesionales(only_necess=True)
        else:
            self.table.setRowCount(0)
        self._recalculate()

    def _on_add_professional(self):
        # build set of already in table
        existing = {self.table.item(r,0).text() for r in range(self.table.rowCount())}
        from views.professional_select_dialog import ProfessionalSelectDialog
        dlg = ProfessionalSelectDialog(existing, parent=self)
        def _on_selected(prof_dict):
            self._add_row(prof_dict)
            self._recalculate()
        dlg.professional_selected.connect(_on_selected)
        dlg.exec()

    # ---------- Auto adjust ----------
    def _on_auto_adjust(self):
        admin_pct = self.admin_target_spin.value()
        if admin_pct <= 0:
            return
        admin_obj = self.costo_directo * (admin_pct/100.0)
        # Compute sum base
        base = 0.0
        for row in range(self.table.rowCount()):
            salario = float(self.table.item(row,2).text().replace('$','').replace(',',''))
            meses = float(self.table.item(row,4).text() or 0)
            base += salario * meses
        if base ==0:
            return
        factor = min(admin_obj / base, 1.0)
        ded_value = round(factor*100,2)
        for row in range(self.table.rowCount()):
            self.table.item(row,3).setText(str(ded_value))
        self._recalculate() 