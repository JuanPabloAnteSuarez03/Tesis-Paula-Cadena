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
        self.resize(1100, 700)
        try:
            self.setWindowState(self.windowState() | Qt.WindowState.WindowMaximized)
        except Exception:
            pass
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

        # Subgastos administrativos en múltiples subtablas
        from PyQt6.QtWidgets import QGroupBox, QGridLayout
        sub_box = QGroupBox("Gastos Administrativos (Subgastos)")
        sub_layout = QGridLayout(sub_box)

        # Oficina / Papelería / Otros (porcentaje sobre costo directo)
        self.tbl_oficina = QTableWidget()
        self.tbl_oficina.setColumnCount(4)
        self.tbl_oficina.setHorizontalHeaderLabels(["Concepto", "Valor Base", "% Dedic.", "Valor"]) 
        oh = self.tbl_oficina.horizontalHeader()
        oh.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        oh.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        oh.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        oh.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        sub_layout.addWidget(QLabel("Oficina / Papelería / Otros"), 0, 0)
        sub_layout.addWidget(self.tbl_oficina, 1, 0)

        # Pólizas (porcentaje sobre base de contrato por defecto)
        self.tbl_polizas = QTableWidget()
        self.tbl_polizas.setColumnCount(4)
        self.tbl_polizas.setHorizontalHeaderLabels(["Concepto", "Valor Base", "% Dedic.", "Valor"])
        ph = self.tbl_polizas.horizontalHeader()
        ph.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        ph.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        ph.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        ph.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        ph.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        sub_layout.addWidget(QLabel("Legalización del Contrato (Pólizas)"), 0, 1)
        sub_layout.addWidget(self.tbl_polizas, 1, 1)

        # Estampillas (porcentaje sobre base de contrato)
        self.tbl_estamp = QTableWidget()
        self.tbl_estamp.setColumnCount(4)
        self.tbl_estamp.setHorizontalHeaderLabels(["Concepto", "Valor Base", "% Dedic.", "Valor"])
        eh = self.tbl_estamp.horizontalHeader()
        eh.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        eh.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        eh.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        eh.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        eh.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        sub_layout.addWidget(QLabel("Estampillas"), 2, 0, 1, 2)
        sub_layout.addWidget(self.tbl_estamp, 3, 0, 1, 2)

        layout.addWidget(sub_box)

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

        # Nuevos: Oficina/Papelería/Otros, Pólizas y Estampillas (porcentaje de costo directo)
        # Eliminado: spinners individuales; todo entra en Administración objetivo y subtablas

        form_layout.addRow("Administración objetivo", self.admin_target_spin)
        form_layout.addRow("Imprevistos", self.imprev_spin)
        form_layout.addRow("Utilidad", self.util_spin)
        form_layout.addRow("IVA sobre Utilidad", self.iva_spin)
        # Ya no mostramos spinners individuales, se controlan desde subtablas
        layout.addWidget(form_widget)

        # Totales
        self.tot_admin_lbl = QLabel("Administración: $0.00")
        self.tot_imprev_lbl = QLabel("Imprevistos: $0.00")
        self.tot_util_lbl = QLabel("Utilidad: $0.00")
        self.tot_iva_lbl = QLabel("IVA Utilidad: $0.00")
        self.tot_office_lbl = QLabel("Oficina/Papelería/Otros: $0.00")
        self.tot_polizas_lbl = QLabel("Pólizas: $0.00")
        self.tot_estamp_lbl = QLabel("Estampillas: $0.00")
        self.tot_aiu_lbl = QLabel("Total Costos Indirectos: $0.00")
        bold = QFont()
        bold.setBold(True)
        self.tot_aiu_lbl.setFont(bold)

        for lbl in [self.tot_admin_lbl, self.tot_office_lbl, self.tot_polizas_lbl, self.tot_estamp_lbl,
                    self.tot_imprev_lbl, self.tot_util_lbl, self.tot_iva_lbl, self.tot_aiu_lbl]:
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
        self.tbl_oficina.itemChanged.connect(self._on_oficina_changed)
        self.tbl_polizas.itemChanged.connect(self._on_polizas_changed)
        self.tbl_estamp.itemChanged.connect(self._on_estamp_changed)
        self.admin_target_spin.valueChanged.connect(self._recalculate)
        self.imprev_spin.valueChanged.connect(self._recalculate)
        self.util_spin.valueChanged.connect(self._recalculate)
        self.iva_spin.valueChanged.connect(self._recalculate)
        # spinners individuales eliminados

    # ---------- Data ----------
    def _load_profesionales(self, only_necess: bool = True):
        self.table.setRowCount(0)
        for prof in self.profesionales:
            if only_necess and not prof.get("necesario", False):
                continue
            self._add_row(prof)

        # Cargar subgastos por defecto (sin autoajustar aún)
        self._load_subgastos()

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

    def _load_subgastos(self):
        """Carga filas base de subgastos en cada subtabla."""
        # Valores base de referencia
        oficina = [
            ("Costo oficina", 2000.00),
            ("Papelería / Fotocopias / Otros", 1000.00),
        ]
        self.tbl_oficina.setRowCount(0)
        for nombre, valor in oficina:
            r = self.tbl_oficina.rowCount()
            self.tbl_oficina.insertRow(r)
            self.tbl_oficina.setItem(r, 0, QTableWidgetItem(nombre))
            self.tbl_oficina.setItem(r, 1, QTableWidgetItem(f"${valor:,.2f}"))
            # % dedicación editable
            self.tbl_oficina.setItem(r, 2, QTableWidgetItem("0.00"))
            v = QTableWidgetItem("$0.00")  # editable para ajuste manual
            self.tbl_oficina.setItem(r, 3, v)

        polizas = [
            ("Póliza de Cumplimiento", 500.00),
            ("Póliza de Anticipo", 500.00),
            ("Póliza RC Extracontractual", 500.00),
            ("Póliza de Estabilidad", 720.00),
            ("Calidad del Servicio", 1450.00),
            ("Calidad y Correcto Funcionamiento", 1500.00),
            ("Póliza Salarios y P.S.", 1000.00),
        ]
        self.tbl_polizas.setRowCount(0)
        for nombre, valor in polizas:
            r = self.tbl_polizas.rowCount()
            self.tbl_polizas.insertRow(r)
            self.tbl_polizas.setItem(r, 0, QTableWidgetItem(nombre))
            self.tbl_polizas.setItem(r, 1, QTableWidgetItem(f"${valor:,.2f}"))
            self.tbl_polizas.setItem(r, 2, QTableWidgetItem("0.00"))  # % dedicación
            v = QTableWidgetItem("$0.00")
            self.tbl_polizas.setItem(r, 3, v)

        estamp = [
            ("Estampilla pro Desarrollo", 740.00),
            ("Estampilla pro Univalle", 370.00),
            ("Estampilla pro Hospital", 740.00),
            ("Estampilla pro Cultura", 520.00),
            ("Estampilla pro Pacífico", 740.00),
            ("Estampilla pro Deporte", 740.00),
            ("Estampilla pro Adulto Mayor", 740.00),
            ("Estampilla Familiar", 740.00),
            ("Contribución Especial", 1850.00),
        ]
        self.tbl_estamp.setRowCount(0)
        for nombre, valor in estamp:
            r = self.tbl_estamp.rowCount()
            self.tbl_estamp.insertRow(r)
            self.tbl_estamp.setItem(r, 0, QTableWidgetItem(nombre))
            self.tbl_estamp.setItem(r, 1, QTableWidgetItem(f"${valor:,.2f}"))
            self.tbl_estamp.setItem(r, 2, QTableWidgetItem("0.00"))  # % dedicación
            v = QTableWidgetItem("$0.00")
            self.tbl_estamp.setItem(r, 3, v)

    # ---------- Logic ----------
    def _recalculate(self):
        # Evitar recursión por señales durante escritura
        _tables = [self.tbl_oficina, self.tbl_polizas, self.tbl_estamp]
        for _t in _tables:
            try:
                _t.blockSignals(True)
            except Exception:
                pass

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

        # Subgastos por subtabla
        sub_total = 0.0
        # Oficina: valor_base * % dedicación
        for r in range(self.tbl_oficina.rowCount()):
            base_txt = self.tbl_oficina.item(r,1).text() if self.tbl_oficina.item(r,1) else '$0'
            base = self._parse_money(base_txt)
            try:
                dedic_pct = float((self.tbl_oficina.item(r,2).text() or '0').replace('%','').strip())
            except Exception:
                dedic_pct = 0.0
            value = base * (dedic_pct/100.0)
            vitem = self.tbl_oficina.item(r,3)
            if vitem is None:
                vitem = QTableWidgetItem()
                self.tbl_oficina.setItem(r,3,vitem)
            vitem.setText(f"${value:,.2f}")
            sub_total += value

        # Base contrato aproximada = costo directo + admin_total parcial (solo profesionales)
        contrato_base = self.costo_directo + admin_total
        # Pólizas: valor_base * % dedicación
        for r in range(self.tbl_polizas.rowCount()):
            base = self._parse_money(self.tbl_polizas.item(r,1).text() if self.tbl_polizas.item(r,1) else '$0')
            try:
                dedic = float((self.tbl_polizas.item(r,2).text() or '0').replace('%','').strip())
            except Exception:
                dedic = 0.0
            value = base * (dedic/100.0)
            vitem = self.tbl_polizas.item(r,3)
            if vitem is None:
                vitem = QTableWidgetItem()
                self.tbl_polizas.setItem(r,3,vitem)
            vitem.setText(f"${value:,.2f}")
            sub_total += value

        # Estampillas: valor_base * % dedicación
        for r in range(self.tbl_estamp.rowCount()):
            base = self._parse_money(self.tbl_estamp.item(r,1).text() if self.tbl_estamp.item(r,1) else '$0')
            try:
                dedic = float((self.tbl_estamp.item(r,2).text() or '0').replace('%','').strip())
            except Exception:
                dedic = 0.0
            value = base * (dedic/100.0)
            vitem = self.tbl_estamp.item(r,3)
            if vitem is None:
                vitem = QTableWidgetItem()
                self.tbl_estamp.setItem(r,3,vitem)
            vitem.setText(f"${value:,.2f}")
            sub_total += value

        imp_pct = self.imprev_spin.value()
        util_pct = self.util_spin.value()
        iva_pct = self.iva_spin.value()
        office_pct = 0.0
        polizas_pct = 0.0
        estamp_pct = 0.0

        imprev_total = self.costo_directo * (imp_pct / 100.0)
        util_total = self.costo_directo * (util_pct / 100.0)
        iva_total = util_total * (iva_pct / 100.0)
        office_total = 0.0
        polizas_total = 0.0
        estamp_total = 0.0
        # Si hay subgastos cargados, se usa su suma y se ignoran los spinners
        if (self.tbl_oficina.rowCount()+self.tbl_polizas.rowCount()+self.tbl_estamp.rowCount()) > 0:
            office_total = 0.0
            polizas_total = 0.0
            estamp_total = 0.0

        total_aiu = admin_total + (sub_total if (self.tbl_oficina.rowCount()+self.tbl_polizas.rowCount()+self.tbl_estamp.rowCount())>0 else (office_total + polizas_total + estamp_total)) + imprev_total + util_total + iva_total

        # Actualizar etiquetas
        self.tot_admin_lbl.setText(f"Administración: ${admin_total:,.2f}")
        self.tot_office_lbl.setText(f"Subgastos Administración: ${sub_total:,.2f}")
        self.tot_polizas_lbl.setText("")
        self.tot_estamp_lbl.setText("")
        self.tot_imprev_lbl.setText(f"Imprevistos ({imp_pct:.2f}%): ${imprev_total:,.2f}")
        self.tot_util_lbl.setText(f"Utilidad ({util_pct:.2f}%): ${util_total:,.2f}")
        self.tot_iva_lbl.setText(f"IVA Utilidad ({iva_pct:.2f}%): ${iva_total:,.2f}")
        self.tot_aiu_lbl.setText(f"Total Costos Indirectos: ${total_aiu:,.2f}")

        self._admin_total = admin_total
        self._imprev_total = imprev_total
        self._util_total = util_total
        self._iva_total = iva_total
        # Guardar subgastos agregados
        self._sub_total = sub_total
        self._office_total = office_total
        self._polizas_total = polizas_total
        self._estamp_total = estamp_total
        self._current_aiu = total_aiu

        # Desbloquear señales
        for _t in _tables:
            try:
                _t.blockSignals(False)
            except Exception:
                pass

    # ---------- Handlers manual edit (subtablas) ----------
    def _parse_money(self, text: str) -> float:
        try:
            return float((text or '0').replace('$','').replace(',','').strip())
        except Exception:
            return 0.0

    def _on_oficina_changed(self, item):
        # Col 3 Valor editable -> recalcular % util; Col 2 % util -> recalcular Valor
        row = item.row(); col = item.column()
        self.tbl_oficina.blockSignals(True)
        try:
            if col == 3:  # Valor
                val = self._parse_money(item.text())
                try:
                    ref_pct = float((self.tbl_oficina.item(row,1).text() or '0').replace('%','').strip())
                except Exception:
                    ref_pct = 0.0
                util = (val / (self.costo_directo * (ref_pct/100.0) + 1e-9)) * 100.0 if ref_pct>0 else 0.0
                pitem = self.tbl_oficina.item(row,2)
                if pitem is None:
                    self.tbl_oficina.setItem(row,2, QTableWidgetItem())
                    pitem = self.tbl_oficina.item(row,2)
                pitem.setText(f"{util:.4f}")
            elif col == 2:  # % util
                try:
                    util = float((item.text() or '0').replace('%','').strip())
                except Exception:
                    util = 0.0
                try:
                    ref_pct = float((self.tbl_oficina.item(row,1).text() or '0').replace('%','').strip())
                except Exception:
                    ref_pct = 0.0
                eff_pct = ref_pct * (util/100.0)
                val = self.costo_directo * (eff_pct/100.0)
                vitem = self.tbl_oficina.item(row,3)
                if vitem is None:
                    self.tbl_oficina.setItem(row,3, QTableWidgetItem())
                    vitem = self.tbl_oficina.item(row,3)
                vitem.setText(f"${val:,.2f}")
        finally:
            self.tbl_oficina.blockSignals(False)
            self._recalculate()

    def _on_polizas_changed(self, item):
        row = item.row(); col = item.column()
        self.tbl_polizas.blockSignals(True)
        try:
            # Column mapping: 0 Concepto | 1 Valor Base | 2 % Dedic | 3 Valor
            base = self._parse_money(self.tbl_polizas.item(row,1).text() if self.tbl_polizas.item(row,1) else '$0')
            if col == 3:  # Valor
                val = self._parse_money(item.text())
                ded = (val / (base + 1e-9)) * 100.0 if base > 0 else 0.0
                pitem = self.tbl_polizas.item(row,2)
                if pitem is None:
                    self.tbl_polizas.setItem(row,2, QTableWidgetItem())
                    pitem = self.tbl_polizas.item(row,2)
                pitem.setText(f"{ded:.4f}")
            elif col in (1,2):
                try:
                    ded = float((self.tbl_polizas.item(row,2).text() or '0').replace('%','').strip())
                except Exception:
                    ded = 0.0
                val = base * (ded/100.0)
                vitem = self.tbl_polizas.item(row,3)
                if vitem is None:
                    self.tbl_polizas.setItem(row,3, QTableWidgetItem())
                    vitem = self.tbl_polizas.item(row,3)
                vitem.setText(f"${val:,.2f}")
        finally:
            self.tbl_polizas.blockSignals(False)
            self._recalculate()

    def _on_estamp_changed(self, item):
        row = item.row(); col = item.column()
        self.tbl_estamp.blockSignals(True)
        try:
            # Column mapping: 0 Concepto | 1 Valor Base | 2 % Dedic | 3 Valor
            base = self._parse_money(self.tbl_estamp.item(row,1).text() if self.tbl_estamp.item(row,1) else '$0')
            if col == 3:  # Valor
                val = self._parse_money(item.text())
                ded = (val / (base + 1e-9)) * 100.0 if base > 0 else 0.0
                pitem = self.tbl_estamp.item(row,2)
                if pitem is None:
                    self.tbl_estamp.setItem(row,2, QTableWidgetItem())
                    pitem = self.tbl_estamp.item(row,2)
                pitem.setText(f"{ded:.4f}")
            elif col in (1,2):
                try:
                    ded = float((self.tbl_estamp.item(row,2).text() or '0').replace('%','').strip())
                except Exception:
                    ded = 0.0
                val = base * (ded/100.0)
                vitem = self.tbl_estamp.item(row,3)
                if vitem is None:
                    self.tbl_estamp.setItem(row,3, QTableWidgetItem())
                    vitem = self.tbl_estamp.item(row,3)
                vitem.setText(f"${val:,.2f}")
        finally:
            self.tbl_estamp.blockSignals(False)
            self._recalculate()

    # ---------- Slots ----------
    def _on_accept(self):
        # Construir detalle de subgastos
        sub_items = []
        # Consolidar sub_items desde las tres tablas
        for r in range(self.tbl_oficina.rowCount()):
            concepto = self.tbl_oficina.item(r,0).text() if self.tbl_oficina.item(r,0) else ""
            try:
                pct = float((self.tbl_oficina.item(r,1).text() or '0').replace('%','').strip())
            except Exception:
                pct = 0.0
            try:
                val_text = self.tbl_oficina.item(r,2).text().replace('$','').replace(',','') if self.tbl_oficina.item(r,2) else '0'
                val = float(val_text)
            except Exception:
                val = 0.0
            sub_items.append({"concepto": concepto, "pct": pct, "valor": val})

        for r in range(self.tbl_polizas.rowCount()):
            concepto = self.tbl_polizas.item(r,0).text() if self.tbl_polizas.item(r,0) else ""
            try:
                pct = float((self.tbl_polizas.item(r,1).text() or '0').replace('%','').strip())
            except Exception:
                pct = 0.0
            try:
                val_text = self.tbl_polizas.item(r,3).text().replace('$','').replace(',','') if self.tbl_polizas.item(r,3) else '0'
                val = float(val_text)
            except Exception:
                val = 0.0
            sub_items.append({"concepto": concepto, "pct": pct, "valor": val})

        for r in range(self.tbl_estamp.rowCount()):
            concepto = self.tbl_estamp.item(r,0).text() if self.tbl_estamp.item(r,0) else ""
            try:
                pct = float((self.tbl_estamp.item(r,1).text() or '0').replace('%','').strip())
            except Exception:
                pct = 0.0
            try:
                val_text = self.tbl_estamp.item(r,3).text().replace('$','').replace(',','') if self.tbl_estamp.item(r,3) else '0'
                val = float(val_text)
            except Exception:
                val = 0.0
            sub_items.append({"concepto": concepto, "pct": pct, "valor": val})

        self.aiu_computed.emit({
            'admin': getattr(self, '_admin_total', 0.0),
            'sub_total': getattr(self, '_sub_total', 0.0),
            'sub_items': sub_items,
            'imprev': getattr(self, '_imprev_total', 0.0),
            'util': getattr(self, '_util_total', 0.0),
            'iva': getattr(self, '_iva_total', 0.0),
            'imprev_pct': self.imprev_spin.value(),
            'util_pct': self.util_spin.value(),
            'iva_pct': self.iva_spin.value(),
            'office_pct': 0.0,
            'polizas_pct': 0.0,
            'estampillas_pct': 0.0,
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

        # 1) Ajustar profesionales proporcionalmente según base salario*meses
        base_prof = 0.0
        for row in range(self.table.rowCount()):
            try:
                salario = float(self.table.item(row,2).text().replace('$','').replace(',',''))
            except Exception:
                salario = 0.0
            try:
                meses = float(self.table.item(row,4).text() or 0)
            except Exception:
                meses = 0.0
            base_prof += salario * meses

        # Reiniciar dedicación antes de repartir para no acumular al re-ejecutar
        for row in range(self.table.rowCount()):
            item = self.table.item(row,3)
            if item:
                item.setText("0.0")

        admin_alloc_prof = admin_obj * 0.5 if base_prof > 0 else 0.0  # 50% a profesionales por defecto
        ded_value = round(min((admin_alloc_prof / base_prof) * 100.0, 100.0), 2) if base_prof > 0 else 0.0
        for row in range(self.table.rowCount()):
            self.table.item(row,3).setText(str(ded_value))

        # 2) Ajustar subgastos (Oficina/Polizas/Estampillas) proporcionalmente por pesos actuales
        # Calcular valor actual de cada fila y total
        # Reset base of dedication to 0 before distributing
        for r in range(self.tbl_oficina.rowCount()):
            self.tbl_oficina.item(r,2).setText("0.00")
        for r in range(self.tbl_polizas.rowCount()):
            self.tbl_polizas.item(r,2).setText("0.00")
        for r in range(self.tbl_estamp.rowCount()):
            self.tbl_estamp.item(r,2).setText("0.00")

        self._recalculate()  # update values with zeros base
        rows = []
        # Oficina
        for r in range(self.tbl_oficina.rowCount()):
            rows.append(("oficina", r))
        # Polizas
        for r in range(self.tbl_polizas.rowCount()):
            rows.append(("polizas", r))
        # Estampillas
        for r in range(self.tbl_estamp.rowCount()):
            rows.append(("estamp", r))

        current_vals = []
        current_sum = 0.0
        for kind, idx in rows:
            # peso por valor base
            if kind == 'oficina':
                val = self._parse_money(self.tbl_oficina.item(idx,1).text())
            elif kind == 'polizas':
                val = self._parse_money(self.tbl_polizas.item(idx,1).text())
            else:
                val = self._parse_money(self.tbl_estamp.item(idx,1).text())
            current_vals.append(val)
            current_sum += val

        # Asignar el 50% restante a subgastos
        admin_alloc_sub = admin_obj - admin_alloc_prof
        if admin_alloc_sub < 0:
            admin_alloc_sub = 0.0
        # Si no hay base, distribuir equitativamente
        if current_sum <= 0 and len(rows) > 0:
            per = admin_alloc_sub / len(rows)
            for (kind, idx) in rows:
                pct = (per / self.costo_directo) * 100.0
                if kind == 'oficina':
                    self.tbl_oficina.item(idx,1).setText(f"{pct:.4f}")
                elif kind == 'polizas':
                    self.tbl_polizas.item(idx,1).setText(f"{pct:.4f}")
                else:
                    self.tbl_estamp.item(idx,1).setText(f"{pct:.4f}")
        elif current_sum > 0:
            for (kind, idx), cur in zip(rows, current_vals):
                target = admin_alloc_sub * (cur / current_sum)
                # Ajustar % dedicación con base en Valor Base
                if kind == 'oficina':
                    base = self._parse_money(self.tbl_oficina.item(idx,1).text())
                    util = (target / (base + 1e-9)) * 100.0 if base>0 else 0.0
                    self.tbl_oficina.item(idx,2).setText(f"{util:.4f}")
                elif kind == 'polizas':
                    base = self._parse_money(self.tbl_polizas.item(idx,1).text())
                    util = (target / (base + 1e-9)) * 100.0 if base>0 else 0.0
                    self.tbl_polizas.item(idx,2).setText(f"{util:.4f}")
                else:
                    base = self._parse_money(self.tbl_estamp.item(idx,1).text())
                    util = (target / (base + 1e-9)) * 100.0 if base>0 else 0.0
                    self.tbl_estamp.item(idx,2).setText(f"{util:.4f}")

        self._recalculate()