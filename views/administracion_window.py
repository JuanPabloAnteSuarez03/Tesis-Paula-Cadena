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

    def __init__(self, profesionales: list[dict], costo_directo: float, parent: QWidget | None = None, embedded: bool = False):
        super().__init__(parent)
        self.setWindowTitle("Costos Indirectos (AIU)")
        self.resize(1400, 900)
        # Forzar pantalla completa/maximizado según plataforma
        try:
            self.showMaximized()
        except Exception:
            try:
                self.setWindowState(self.windowState() | Qt.WindowState.WindowMaximized)
            except Exception:
                pass
        self.profesionales = profesionales
        self.costo_directo = costo_directo
        self.embedded = embedded
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
        # Contenedor de profesionales (para usarlo dentro de un splitter)
        prof_container = QWidget()
        prof_v = QVBoxLayout(prof_container)
        prof_v.setContentsMargins(0,0,0,0)
        prof_v.addWidget(self.table)

        # Subgastos administrativos en múltiples subtablas
        from PyQt6.QtWidgets import QGroupBox, QGridLayout, QLabel, QSpacerItem, QSizePolicy, QSplitter
        sub_box = QGroupBox("Gastos Administrativos (Subgastos)")
        sub_layout = QGridLayout(sub_box)

        # Oficina / Papelería / Otros
        self.tbl_oficina = QTableWidget()
        self.tbl_oficina.setColumnCount(5)
        self.tbl_oficina.setHorizontalHeaderLabels(["Concepto", "Valor Base", "% Dedic.", "Meses", "Valor"]) 
        oh = self.tbl_oficina.horizontalHeader()
        oh.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        oh.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        oh.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        oh.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        oh.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        # Encabezado Oficina con botón Agregar
        header_of = QWidget()
        hl_of = QHBoxLayout(header_of)
        hl_of.setContentsMargins(0,0,0,0)
        hl_of.addWidget(QLabel("Oficina / Papelería / Otros"))
        self.btn_add_oficina = QPushButton("Agregar")
        self.btn_add_oficina.setFixedWidth(90)
        hl_of.addStretch(1)
        hl_of.addWidget(self.btn_add_oficina)
        sub_layout.addWidget(header_of, 0, 0)
        # Splitter horizontal para ajustar Oficina vs Pólizas
        split_hp = QSplitter(Qt.Orientation.Horizontal)
        self.tbl_oficina.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        # Contenedor vertical para tabla y botones de Oficina
        of_container = QWidget()
        of_v = QVBoxLayout(of_container)
        of_v.setContentsMargins(0,0,0,0)
        of_v.addWidget(self.tbl_oficina)
        of_btns = QHBoxLayout()
        of_btns.addStretch(1)
        self.btn_add_oficina_b = QPushButton("Agregar")
        self.btn_del_oficina_b = QPushButton("Eliminar")
        of_btns.addWidget(self.btn_add_oficina_b)
        of_btns.addWidget(self.btn_del_oficina_b)
        of_v.addLayout(of_btns)
        split_hp.addWidget(of_container)
        # Pólizas se añade más abajo, tras crearla
        self.lbl_subtotal_oficina = QLabel("Subtotal: $0.00")
        self.lbl_subtotal_oficina.setStyleSheet("font-weight: bold; padding: 16px 0 40px 0;")
        sub_layout.addWidget(self.lbl_subtotal_oficina, 2, 0)

        # Pólizas (porcentaje sobre base de contrato por defecto)
        self.tbl_polizas = QTableWidget()
        self.tbl_polizas.setColumnCount(7)
        self.tbl_polizas.setHorizontalHeaderLabels(["Concepto", "% Req.", "Meses", "% Prima", "Valor Base", "% Dedic.", "Valor"])
        ph = self.tbl_polizas.horizontalHeader()
        ph.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        ph.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        ph.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        ph.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        ph.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        ph.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        ph.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        ph.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        # Encabezado Pólizas con botón Agregar
        header_pol = QWidget()
        hl_pol = QHBoxLayout(header_pol)
        hl_pol.setContentsMargins(0,0,0,0)
        hl_pol.addWidget(QLabel("Legalización del Contrato (Pólizas)"))
        self.btn_add_poliza = QPushButton("Agregar")
        self.btn_add_poliza.setFixedWidth(90)
        hl_pol.addStretch(1)
        hl_pol.addWidget(self.btn_add_poliza)
        sub_layout.addWidget(header_pol, 0, 1)
        self.tbl_polizas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        # Contenedor vertical para tabla y botones de Polizas
        pol_container = QWidget()
        pol_v = QVBoxLayout(pol_container)
        pol_v.setContentsMargins(0,0,0,0)
        pol_v.addWidget(self.tbl_polizas)
        pol_btns = QHBoxLayout()
        pol_btns.addStretch(1)
        self.btn_add_poliza_b = QPushButton("Agregar")
        self.btn_del_poliza_b = QPushButton("Eliminar")
        pol_btns.addWidget(self.btn_add_poliza_b)
        pol_btns.addWidget(self.btn_del_poliza_b)
        pol_v.addLayout(pol_btns)
        split_hp.addWidget(pol_container)
        split_hp.setStretchFactor(0, 1)
        split_hp.setStretchFactor(1, 1)
        sub_layout.addWidget(split_hp, 1, 0, 1, 2)
        self.lbl_subtotal_polizas = QLabel("Subtotal: $0.00")
        self.lbl_subtotal_polizas.setStyleSheet("font-weight: bold; padding: 4px 0 10px 0;")
        sub_layout.addWidget(self.lbl_subtotal_polizas, 2, 1)

        # Estampillas (porcentaje sobre base de contrato)
        self.tbl_estamp = QTableWidget()
        self.tbl_estamp.setColumnCount(3)
        self.tbl_estamp.setHorizontalHeaderLabels(["Concepto", "% Tasa", "Valor"])
        eh = self.tbl_estamp.horizontalHeader()
        eh.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        eh.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        eh.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        eh.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        # Encabezado Estampillas con botón Agregar
        header_est = QWidget()
        hl_est = QHBoxLayout(header_est)
        hl_est.setContentsMargins(0,0,0,0)
        hl_est.addWidget(QLabel("Estampillas"))
        self.btn_add_estamp = QPushButton("Agregar")
        self.btn_add_estamp.setFixedWidth(90)
        hl_est.addStretch(1)
        hl_est.addWidget(self.btn_add_estamp)
        sub_layout.addWidget(header_est, 2, 0, 1, 2)
        # Contenedor vertical para Estampillas y sus botones
        est_container = QWidget()
        est_v = QVBoxLayout(est_container)
        est_v.setContentsMargins(0,0,0,0)
        est_v.addWidget(self.tbl_estamp)
        est_btns = QHBoxLayout()
        est_btns.addStretch(1)
        self.btn_add_estamp_b = QPushButton("Agregar")
        self.btn_del_estamp_b = QPushButton("Eliminar")
        est_btns.addWidget(self.btn_add_estamp_b)
        est_btns.addWidget(self.btn_del_estamp_b)
        est_v.addLayout(est_btns)
        sub_layout.addWidget(est_container, 3, 0, 1, 2)
        self.lbl_subtotal_estamp = QLabel("Subtotal: $0.00")
        self.lbl_subtotal_estamp.setStyleSheet("font-weight: bold; padding: 4px 0 10px 0;")
        sub_layout.addWidget(self.lbl_subtotal_estamp, 4, 0, 1, 2)
        # Espaciador inferior para evitar solapamiento con el siguiente bloque
        sub_layout.setContentsMargins(8, 8, 8, 24)
        sub_layout.addItem(QSpacerItem(20, 28, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed), 5, 0, 1, 2)
        # Hacer que las filas con tablas se estiren mejor
        sub_layout.setRowStretch(1, 1)
        sub_layout.setRowStretch(3, 1)
        sub_layout.setColumnStretch(0, 1)
        sub_layout.setColumnStretch(1, 1)

        # Splitter vertical para ajustar profesionales vs subgastos (dar más espacio a subgastos)
        split_v = QSplitter(Qt.Orientation.Vertical)
        split_v.addWidget(prof_container)
        split_v.addWidget(sub_box)
        split_v.setStretchFactor(0, 2)
        split_v.setStretchFactor(1, 3)
        layout.addWidget(split_v)
        # Conexiones de botones inferiores
        self.btn_add_oficina_b.clicked.connect(self._on_add_oficina)
        self.btn_del_oficina_b.clicked.connect(self._on_del_oficina)
        self.btn_add_poliza_b.clicked.connect(self._on_add_poliza)
        self.btn_del_poliza_b.clicked.connect(self._on_del_poliza)
        self.btn_add_estamp_b.clicked.connect(self._on_add_estamp)
        self.btn_del_estamp_b.clicked.connect(self._on_del_estamp)
        # Conexiones de botones agregar
        self.btn_add_oficina.clicked.connect(self._on_add_oficina)
        self.btn_add_poliza.clicked.connect(self._on_add_poliza)
        self.btn_add_estamp.clicked.connect(self._on_add_estamp)

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
        # Duración global del proyecto
        self.meses_global_spin = QDoubleSpinBox()
        self.meses_global_spin.setSuffix(" meses")
        self.meses_global_spin.setRange(0, 120)
        self.meses_global_spin.setValue(6.0)
        self.meses_global_spin.setSingleStep(0.5)
        form_layout.addRow("Duración del proyecto", self.meses_global_spin)
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

        # Panel compacto para totales (reducido)
        totals_panel = QWidget()
        totals_layout = QVBoxLayout(totals_panel)
        totals_layout.setContentsMargins(6, 4, 6, 4)
        totals_layout.setSpacing(2)
        for lbl in [self.tot_admin_lbl, self.tot_office_lbl, self.tot_polizas_lbl, self.tot_estamp_lbl,
                    self.tot_imprev_lbl, self.tot_util_lbl, self.tot_iva_lbl, self.tot_aiu_lbl]:
            lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
            totals_layout.addWidget(lbl)
        # Ajuste para evitar que el texto inferior se corte; dar más holgura
        totals_panel.setMaximumHeight(200)
        layout.addWidget(totals_panel)

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
        self.meses_global_spin.valueChanged.connect(self._on_global_months_changed)
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
        # Inicializar meses de tablas dependientes con la duración global
        try:
            self._on_global_months_changed(None)
        except Exception:
            pass

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
        # Guardar salario base para autoajuste idempotente
        try:
            salario_item.setData(Qt.ItemDataRole.UserRole, salario)
        except Exception:
            pass
        self.table.setItem(row, 2, salario_item)
        # % dedicación por defecto: Director 50%, resto 100%
        cargo_low = str(prof.get("cargo", "")).lower()
        nombre_low = str(prof.get("nombre", "")).lower()
        dedic_default = 50.0 if ("director" in cargo_low or "director" in nombre_low) else 100.0
        dedic_item = QTableWidgetItem(str(dedic_default))
        self.table.setItem(row, 3, dedic_item)
        # Meses (se sincroniza luego con duración global)
        meses_item = QTableWidgetItem("6")
        self.table.setItem(row, 4, meses_item)
        # Total
        total_item = QTableWidgetItem("$0.00")
        total_item.setFlags(total_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.table.setItem(row, 5, total_item)

    def _load_subgastos(self):
        """Carga filas base de subgastos en cada subtabla (inspirados en ejemplo)."""
        oficina_mensual = [
            ("Costo oficina", 300000.0),
            ("Papelería / Fotocopias / Otros", 100000.0),
        ]
        self.tbl_oficina.setRowCount(0)
        for nombre, valor_mensual in oficina_mensual:
            r = self.tbl_oficina.rowCount()
            self.tbl_oficina.insertRow(r)
            self.tbl_oficina.setItem(r, 0, QTableWidgetItem(nombre))
            self.tbl_oficina.setItem(r, 1, QTableWidgetItem(f"${valor_mensual:,.2f}"))
            # % dedicación editable (por defecto 100%)
            self.tbl_oficina.setItem(r, 2, QTableWidgetItem("100.00"))
            # Meses editable (por defecto 6.00)
            self.tbl_oficina.setItem(r, 3, QTableWidgetItem("6.00"))
            v = QTableWidgetItem("$0.00")
            self.tbl_oficina.setItem(r, 4, v)

        # Aproximación de base de contrato (para inicializar valores base)
        contrato_estimado = self.costo_directo
        # Valores por defecto inspirados en tu planilla: % requerido, meses, % prima
        polizas_params = [
            ("Póliza de Cumplimiento", 20.0, 10.0, 0.50),
            ("Póliza de Anticipo", 100.0, 10.0, 0.50),
            ("Póliza RC Extracontractual", 30.0, 10.0, 0.50),
            ("Póliza de Estabilidad", 20.0, 5.0, 0.50),
            ("Calidad del Servicio", 20.0, 10.0, 0.50),
            ("Calidad y Correcto Funcionamiento", 20.0, 10.0, 0.50),
            ("Póliza Salarios y P.S.", 5.0, 10.0, 1.00),
        ]
        self.tbl_polizas.setRowCount(0)
        for nombre, req, meses, prima in polizas_params:
            r = self.tbl_polizas.rowCount()
            self.tbl_polizas.insertRow(r)
            self.tbl_polizas.setItem(r, 0, QTableWidgetItem(nombre))
            self.tbl_polizas.setItem(r, 1, QTableWidgetItem(f"{req:.2f}"))
            self.tbl_polizas.setItem(r, 2, QTableWidgetItem(f"{meses:.2f}"))
            self.tbl_polizas.setItem(r, 3, QTableWidgetItem(f"{prima:.3f}"))
            # Valor base calculado abajo en _recalculate; inicializamos placeholders
            self.tbl_polizas.setItem(r, 4, QTableWidgetItem("$0.00"))
            self.tbl_polizas.setItem(r, 5, QTableWidgetItem("100.00"))  # % dedicación
            v = QTableWidgetItem("$0.00")
            self.tbl_polizas.setItem(r, 6, v)

        estamp_rates = [
            ("Estampilla pro Desarrollo", 0.04),
            ("Estampilla pro Univalle", 0.01),
            ("Estampilla pro Hospital", 0.01),
            ("Estampilla pro Cultura", 0.01),
            ("Estampilla pro Pacífico", 0.01),
            ("Estampilla pro Deporte", 0.02),
            ("Estampilla pro Adulto Mayor", 0.02),
            ("Estampilla Familiar", 0.02),
            ("Contribución Especial", 0.05),
        ]
        self.tbl_estamp.setRowCount(0)
        for nombre, rate in estamp_rates:
            r = self.tbl_estamp.rowCount()
            self.tbl_estamp.insertRow(r)
            self.tbl_estamp.setItem(r, 0, QTableWidgetItem(nombre))
            self.tbl_estamp.setItem(r, 1, QTableWidgetItem(f"{rate*100:.2f}"))
            v = QTableWidgetItem("$0.00")
            self.tbl_estamp.setItem(r, 2, v)

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
        sub_oficina_total = 0.0
        sub_polizas_total = 0.0
        sub_estamp_total = 0.0
        # Oficina: (valor_mensual * meses) * % dedicación
        for r in range(self.tbl_oficina.rowCount()):
            # saltar fila de subtotal si existe
            first = self.tbl_oficina.item(r,0)
            if first and first.text().strip().lower() == 'subtotal':
                continue
            base_mensual_txt = self.tbl_oficina.item(r,1).text() if self.tbl_oficina.item(r,1) else '$0'
            base_mensual = self._parse_money(base_mensual_txt)
            try:
                meses = float((self.tbl_oficina.item(r,3).text() or '0').replace(',','').strip())
            except Exception:
                meses = 0.0
            try:
                dedic_pct = float((self.tbl_oficina.item(r,2).text() or '0').replace('%','').strip())
            except Exception:
                dedic_pct = 0.0
            value = base_mensual * meses * (dedic_pct/100.0)
            vitem = self.tbl_oficina.item(r,4)
            if vitem is None:
                vitem = QTableWidgetItem()
                self.tbl_oficina.setItem(r,4,vitem)
            vitem.setText(f"${value:,.2f}")
            sub_oficina_total += value
            sub_total += value

        # Base contrato aproximada = costo directo + admin_total parcial (solo profesionales)
        contrato_base = self.costo_directo + admin_total
        # Pólizas: costo_directo × (%Req/100) × (%Prima/100) × (Meses/12) × %Dedic
        for r in range(self.tbl_polizas.rowCount()):
            first = self.tbl_polizas.item(r,0)
            if first and first.text().strip().lower() == 'subtotal':
                continue
            try:
                req = float((self.tbl_polizas.item(r,1).text() or '0').replace('%','').strip())
            except Exception:
                req = 0.0
            try:
                meses = float((self.tbl_polizas.item(r,2).text() or '0').strip())
            except Exception:
                meses = 0.0
            try:
                prima = float((self.tbl_polizas.item(r,3).text() or '0').replace('%','').strip())
            except Exception:
                prima = 0.0
            base_val = self.costo_directo * (req/100.0) * (prima/100.0) * (meses/12.0)
            base_item = self.tbl_polizas.item(r,4)
            if base_item is None:
                self.tbl_polizas.setItem(r,4, QTableWidgetItem())
                base_item = self.tbl_polizas.item(r,4)
            base_item.setText(f"${base_val:,.2f}")
            try:
                dedic = float((self.tbl_polizas.item(r,5).text() or '0').replace('%','').strip())
            except Exception:
                dedic = 0.0
            value = base_val * (dedic/100.0)
            vitem = self.tbl_polizas.item(r,6)
            if vitem is None:
                vitem = QTableWidgetItem()
                self.tbl_polizas.setItem(r,6,vitem)
            vitem.setText(f"${value:,.2f}")
            sub_polizas_total += value
            sub_total += value

        # Estampillas: costo_directo × tasa
        for r in range(self.tbl_estamp.rowCount()):
            first = self.tbl_estamp.item(r,0)
            if first and first.text().strip().lower() == 'subtotal':
                continue
            try:
                tasa = float((self.tbl_estamp.item(r,1).text() or '0').replace('%','').strip())
            except Exception:
                tasa = 0.0
            value = self.costo_directo * (tasa/100.0)
            vitem = self.tbl_estamp.item(r,2)
            if vitem is None:
                vitem = QTableWidgetItem()
                self.tbl_estamp.setItem(r,2,vitem)
            vitem.setText(f"${value:,.2f}")
            sub_estamp_total += value
            sub_total += value

        # Actualizar labels de subtotal (no se insertan filas en tablas)
        try:
            self.lbl_subtotal_oficina.setText(f"Subtotal: ${sub_oficina_total:,.2f}")
        except Exception:
            pass
        try:
            self.lbl_subtotal_polizas.setText(f"Subtotal: ${sub_polizas_total:,.2f}")
        except Exception:
            pass
        try:
            self.lbl_subtotal_estamp.setText(f"Subtotal: ${sub_estamp_total:,.2f}")
        except Exception:
            pass

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

        # Total AIU = Administración (profesionales) + Subgastos + Imprevistos + Utilidad + IVA
        total_aiu = admin_total + sub_total + imprev_total + util_total + iva_total

        # Actualizar etiquetas: Administración = Profesionales + Subgastos
        admin_combined = admin_total + sub_total
        self.tot_admin_lbl.setText(f"Administración: ${admin_combined:,.2f}")
        # Ocultar línea separada de subgastos en breakdown
        self.tot_office_lbl.setText("")
        self.tot_polizas_lbl.setText("")
        self.tot_estamp_lbl.setText("")
        self.tot_imprev_lbl.setText(f"Imprevistos ({imp_pct:.2f}%): ${imprev_total:,.2f}")
        self.tot_util_lbl.setText(f"Utilidad ({util_pct:.2f}%): ${util_total:,.2f}")
        self.tot_iva_lbl.setText(f"IVA Utilidad ({iva_pct:.2f}%): ${iva_total:,.2f}")
        self.tot_aiu_lbl.setText(f"Costo Total AIU: ${total_aiu:,.2f}")

        # Guardar administración combinada (para enviar al presupuesto)
        self._admin_total = admin_combined
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

    def _set_subtotal_row(self, table, label, value_col_idx, total_value):
        """Crea/actualiza la última fila como subtotal en la tabla dada."""
        # Buscar si ya existe fila con 'Subtotal'
        subtotal_row = None
        for r in range(table.rowCount()):
            it = table.item(r,0)
            if it and it.text().strip().lower() == 'subtotal':
                subtotal_row = r
                break
        if subtotal_row is None:
            subtotal_row = table.rowCount()
            table.insertRow(subtotal_row)
            # Crear celdas vacías
            for c in range(table.columnCount()):
                if table.item(subtotal_row, c) is None:
                    table.setItem(subtotal_row, c, QTableWidgetItem())
        # Escribir etiqueta y valor
        label_item = table.item(subtotal_row, 0)
        label_item.setText(label)
        # Estilo no editable
        label_item.setFlags(label_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        val_item = table.item(subtotal_row, value_col_idx)
        if val_item is None:
            val_item = QTableWidgetItem()
            table.setItem(subtotal_row, value_col_idx, val_item)
        val_item.setText(f"${total_value:,.2f}")
        val_item.setFlags(val_item.flags() & ~Qt.ItemFlag.ItemIsEditable)

    # ---------- Handlers manual edit (subtablas) ----------
    def _parse_money(self, text: str) -> float:
        try:
            return float((text or '0').replace('$','').replace(',','').strip())
        except Exception:
            return 0.0

    def _on_oficina_changed(self, item):
        # Col 4 Valor editable -> recalcular % dedic.; Col 2 % dedic. o col 3 meses -> recalcular Valor
        row = item.row(); col = item.column()
        self.tbl_oficina.blockSignals(True)
        try:
            base_mensual = self._parse_money(self.tbl_oficina.item(row,1).text() if self.tbl_oficina.item(row,1) else '$0')
            try:
                meses = float((self.tbl_oficina.item(row,3).text() or '0').replace(',','').strip())
            except Exception:
                meses = 0.0
            if col == 4:  # Valor
                val = self._parse_money(item.text())
                dedic = (val / (base_mensual * meses + 1e-9)) * 100.0 if base_mensual>0 and meses>0 else 0.0
                pitem = self.tbl_oficina.item(row,2)
                if pitem is None:
                    self.tbl_oficina.setItem(row,2, QTableWidgetItem())
                    pitem = self.tbl_oficina.item(row,2)
                pitem.setText(f"{dedic:.4f}")
            elif col in (2,3):
                try:
                    dedic = float((self.tbl_oficina.item(row,2).text() or '0').replace('%','').strip())
                except Exception:
                    dedic = 0.0
                val = base_mensual * meses * (dedic/100.0)
                vitem = self.tbl_oficina.item(row,4)
                if vitem is None:
                    self.tbl_oficina.setItem(row,4, QTableWidgetItem())
                    vitem = self.tbl_oficina.item(row,4)
                vitem.setText(f"${val:,.2f}")
        finally:
            self.tbl_oficina.blockSignals(False)
            self._recalculate()

    def _on_polizas_changed(self, item):
        """Mantiene sincronía entre %Req/Meses/%Prima, %Dedic y Valor."""
        row = item.row(); col = item.column()
        self.tbl_polizas.blockSignals(True)
        try:
            # Column mapping nueva: 0 Concepto | 1 %Req | 2 Meses | 3 %Prima | 4 Valor Base | 5 %Dedic | 6 Valor
            # Releer parámetros
            try:
                req = float((self.tbl_polizas.item(row,1).text() or '0').replace('%','').strip())
            except Exception:
                req = 0.0
            try:
                meses = float((self.tbl_polizas.item(row,2).text() or '0').strip())
            except Exception:
                meses = 0.0
            try:
                prima = float((self.tbl_polizas.item(row,3).text() or '0').replace('%','').strip())
            except Exception:
                prima = 0.0

            # Calcular base y escribirla (si cambian req/meses/prima)
            base_val = self.costo_directo * (req/100.0) * (prima/100.0) * (meses/12.0)
            base_item = self.tbl_polizas.item(row,4)
            if base_item is None:
                self.tbl_polizas.setItem(row,4, QTableWidgetItem())
                base_item = self.tbl_polizas.item(row,4)
            base_item.setText(f"${base_val:,.2f}")

            # Si editaron Valor (col 6), recalcular %Dedic; si editaron %Dedic o params, recalcular Valor
            if col == 6:
                val = self._parse_money(item.text())
                ded = (val / (base_val + 1e-9)) * 100.0 if base_val > 0 else 0.0
                ditem = self.tbl_polizas.item(row,5)
                if ditem is None:
                    self.tbl_polizas.setItem(row,5, QTableWidgetItem())
                    ditem = self.tbl_polizas.item(row,5)
                ditem.setText(f"{ded:.4f}")
            else:
                try:
                    ded = float((self.tbl_polizas.item(row,5).text() or '0').replace('%','').strip())
                except Exception:
                    ded = 0.0
                val = base_val * (ded/100.0)
                vitem = self.tbl_polizas.item(row,6)
                if vitem is None:
                    self.tbl_polizas.setItem(row,6, QTableWidgetItem())
                    vitem = self.tbl_polizas.item(row,6)
                vitem.setText(f"${val:,.2f}")
        finally:
            self.tbl_polizas.blockSignals(False)
            self._recalculate()

    def _on_estamp_changed(self, item):
        row = item.row(); col = item.column()
        self.tbl_estamp.blockSignals(True)
        try:
            # Column mapping nueva: 0 Concepto | 1 % Tasa | 2 Valor
            try:
                tasa = float((self.tbl_estamp.item(row,1).text() or '0').replace('%','').strip())
            except Exception:
                tasa = 0.0
            val = self.costo_directo * (tasa/100.0)
            vitem = self.tbl_estamp.item(row,2)
            if vitem is None:
                self.tbl_estamp.setItem(row,2, QTableWidgetItem())
                vitem = self.tbl_estamp.item(row,2)
            vitem.setText(f"${val:,.2f}")
        finally:
            self.tbl_estamp.blockSignals(False)
            self._recalculate()

    def _on_global_months_changed(self, _):
        """Copia la duración global a la columna Meses de Oficina y a Profesionales."""
        m = self.meses_global_spin.value()
        self.tbl_oficina.blockSignals(True)
        try:
            for r in range(self.tbl_oficina.rowCount()):
                # saltar si es subtotal
                it = self.tbl_oficina.item(r,0)
                if it and it.text().strip().lower() == 'subtotal':
                    continue
                cell = self.tbl_oficina.item(r,3)
                if cell is None:
                    self.tbl_oficina.setItem(r,3, QTableWidgetItem())
                    cell = self.tbl_oficina.item(r,3)
                cell.setText(f"{m:.2f}")
        finally:
            self.tbl_oficina.blockSignals(False)
        # Actualizar meses en profesionales (col 4)
        self.table.blockSignals(True)
        try:
            for r in range(self.table.rowCount()):
                cell = self.table.item(r,4)
                if cell is None:
                    self.table.setItem(r,4, QTableWidgetItem())
                    cell = self.table.item(r,4)
                cell.setText(f"{m:.2f}")
        finally:
            self.table.blockSignals(False)
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
        if not getattr(self, 'embedded', False):
            self.close()


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

    # ---------- Add rows to subtables ----------
    def _on_add_oficina(self):
        r = self.tbl_oficina.rowCount()
        self.tbl_oficina.insertRow(r)
        self.tbl_oficina.setItem(r, 0, QTableWidgetItem("Nuevo concepto"))
        self.tbl_oficina.setItem(r, 1, QTableWidgetItem("$0.00"))
        self.tbl_oficina.setItem(r, 2, QTableWidgetItem("0.00"))
        self.tbl_oficina.setItem(r, 3, QTableWidgetItem(f"{self.meses_global_spin.value():.2f}"))
        self.tbl_oficina.setItem(r, 4, QTableWidgetItem("$0.00"))
        self._recalculate()

    def _on_add_poliza(self):
        r = self.tbl_polizas.rowCount()
        self.tbl_polizas.insertRow(r)
        self.tbl_polizas.setItem(r, 0, QTableWidgetItem("Nueva póliza"))
        self.tbl_polizas.setItem(r, 1, QTableWidgetItem("0.00"))  # % Req.
        self.tbl_polizas.setItem(r, 2, QTableWidgetItem(f"{self.meses_global_spin.value():.2f}"))  # Meses
        self.tbl_polizas.setItem(r, 3, QTableWidgetItem("0.000"))  # % Prima
        self.tbl_polizas.setItem(r, 4, QTableWidgetItem("$0.00"))  # Base
        self.tbl_polizas.setItem(r, 5, QTableWidgetItem("0.00"))   # % Dedic.
        self.tbl_polizas.setItem(r, 6, QTableWidgetItem("$0.00"))  # Valor
        self._recalculate()

    def _on_add_estamp(self):
        r = self.tbl_estamp.rowCount()
        self.tbl_estamp.insertRow(r)
        self.tbl_estamp.setItem(r, 0, QTableWidgetItem("Nueva estampilla"))
        self.tbl_estamp.setItem(r, 1, QTableWidgetItem("0.00"))  # % tasa
        self.tbl_estamp.setItem(r, 2, QTableWidgetItem("$0.00"))
        self._recalculate()

    def _on_del_oficina(self):
        idxs = self.tbl_oficina.selectionModel().selectedRows()
        rows = sorted([i.row() for i in idxs], reverse=True)
        # Fallback: si no hay selección por filas, usar la fila actual
        if not rows:
            cur = self.tbl_oficina.currentRow()
            if cur is not None and cur >= 0:
                rows = [cur]
        for r in rows:
            it = self.tbl_oficina.item(r,0)
            if it and it.text().strip().lower() == 'subtotal':
                continue
            self.tbl_oficina.removeRow(r)
        self._recalculate()

    def _on_del_poliza(self):
        idxs = self.tbl_polizas.selectionModel().selectedRows()
        rows = sorted([i.row() for i in idxs], reverse=True)
        if not rows:
            cur = self.tbl_polizas.currentRow()
            if cur is not None and cur >= 0:
                rows = [cur]
        for r in rows:
            it = self.tbl_polizas.item(r,0)
            if it and it.text().strip().lower() == 'subtotal':
                continue
            self.tbl_polizas.removeRow(r)
        self._recalculate()

    def _on_del_estamp(self):
        idxs = self.tbl_estamp.selectionModel().selectedRows()
        rows = sorted([i.row() for i in idxs], reverse=True)
        if not rows:
            cur = self.tbl_estamp.currentRow()
            if cur is not None and cur >= 0:
                rows = [cur]
        for r in rows:
            it = self.tbl_estamp.item(r,0)
            if it and it.text().strip().lower() == 'subtotal':
                continue
            self.tbl_estamp.removeRow(r)
        self._recalculate()

    # ---------- Auto adjust ----------
    def _on_auto_adjust(self):
        admin_pct = self.admin_target_spin.value()
        if admin_pct <= 0:
            return
        admin_obj = self.costo_directo * (admin_pct/100.0)

        # 1) Ajustar profesionales: mantener % dedicación fija (Director 50%, demás 100%)
        # y ESCALAR el salario mostrado según el objetivo (sin acumular).
        # Base para repartir: salario_base * meses
        base_prof = 0.0
        salarios_base = []
        meses_list = []
        for row in range(self.table.rowCount()):
            sal_item = self.table.item(row,2)
            try:
                sal_base = float(sal_item.data(Qt.ItemDataRole.UserRole)) if sal_item is not None else 0.0
            except Exception:
                # si no está guardado, inferir del texto actual
                sal_base = 0.0
            if sal_base <= 0:
                try:
                    sal_base = float((self.table.item(row,2).text() or '0').replace('$','').replace(',',''))
                except Exception:
                    sal_base = 0.0
            salarios_base.append(sal_base)
            try:
                m = float((self.table.item(row,4).text() or '0').strip())
            except Exception:
                m = 0.0
            meses_list.append(m)
            base_prof += sal_base * m

        admin_alloc_prof = admin_obj * 0.5 if base_prof > 0 else 0.0
        # Escalar salarios proporcionalmente a su peso (salario_base*meses)
        for row in range(self.table.rowCount()):
            weight = salarios_base[row] * meses_list[row]
            if base_prof > 0 and weight > 0:
                extra_total = admin_alloc_prof * (weight / base_prof)
                # salario nuevo = salario_base + (extra_total / meses)
                new_salary = salarios_base[row] + (extra_total / max(meses_list[row], 1e-9))
            else:
                new_salary = salarios_base[row]
            sal_item = self.table.item(row,2)
            if sal_item is not None:
                # mostrar el nuevo salario pero NO sobrescribir el base guardado
                sal_item.setText(f"${new_salary:,.2f}")

        # 2) Ajustar subgastos (Oficina/Polizas/Estampillas) proporcionalmente por pesos actuales
        # Calcular valor actual de cada fila y total
        # Reset % dedicación (no tocar meses ni parámetros)
        for r in range(self.tbl_oficina.rowCount()):
            self.tbl_oficina.item(r,2).setText("0.00")  # % Dedic.
        for r in range(self.tbl_polizas.rowCount()):
            self.tbl_polizas.item(r,5).setText("0.00")  # % Dedic.
        for r in range(self.tbl_estamp.rowCount()):
            self.tbl_estamp.item(r,2).setText("0.00")  # % Dedic.

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
            # peso por valor base (para oficina: base mensual × meses)
            if kind == 'oficina':
                base_m = self._parse_money(self.tbl_oficina.item(idx,1).text())
                try:
                    m = float((self.tbl_oficina.item(idx,3).text() or '0').strip())
                except Exception:
                    m = 0.0
                val = base_m * m
            elif kind == 'polizas':
                val = self._parse_money(self.tbl_polizas.item(idx,4).text())
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
                if kind == 'oficina':
                    base_m = self._parse_money(self.tbl_oficina.item(idx,1).text())
                    try:
                        m = float((self.tbl_oficina.item(idx,3).text() or '0').strip())
                    except Exception:
                        m = 0.0
                    util = (per / (base_m * m + 1e-9)) * 100.0 if base_m > 0 and m > 0 else 0.0
                    self.tbl_oficina.item(idx,2).setText(f"{util:.4f}")
                elif kind == 'polizas':
                    base_v = self._parse_money(self.tbl_polizas.item(idx,4).text())
                    util = (per / (base_v + 1e-9)) * 100.0 if base_v > 0 else 0.0
                    self.tbl_polizas.item(idx,5).setText(f"{util:.4f}")
                else:
                    base_v = self._parse_money(self.tbl_estamp.item(idx,1).text())
                    util = (per / (base_v + 1e-9)) * 100.0 if base_v > 0 else 0.0
                    self.tbl_estamp.item(idx,2).setText(f"{util:.4f}")
        elif current_sum > 0:
            for (kind, idx), cur in zip(rows, current_vals):
                target = admin_alloc_sub * (cur / current_sum)
                # Ajustar % dedicación con base en Valor Base
                if kind == 'oficina':
                    base_m = self._parse_money(self.tbl_oficina.item(idx,1).text())
                    try:
                        m = float((self.tbl_oficina.item(idx,3).text() or '0').strip())
                    except Exception:
                        m = 0.0
                    util = (target / (base_m * m + 1e-9)) * 100.0 if base_m>0 and m>0 else 0.0
                    self.tbl_oficina.item(idx,2).setText(f"{util:.4f}")
                elif kind == 'polizas':
                    base_v = self._parse_money(self.tbl_polizas.item(idx,4).text())
                    util = (target / (base_v + 1e-9)) * 100.0 if base_v>0 else 0.0
                    self.tbl_polizas.item(idx,5).setText(f"{util:.4f}")
                else:
                    base_v = self._parse_money(self.tbl_estamp.item(idx,1).text())
                    util = (target / (base_v + 1e-9)) * 100.0 if base_v>0 else 0.0
                    self.tbl_estamp.item(idx,2).setText(f"{util:.4f}")

        self._recalculate() 