"""
evm_view.py – Control EVM (Earned Value Management) para AppPresupuestos.

Vincula:
  • CronogramaView  → fecha de corte + tareas (cantidad_obra / cantidad_real)
  • EjecucionView   → selección de Ejecución para calcular el AC (costo real)

Métricas calculadas:
  PV  = Σ(cantidad_obra  × valor_unit)   Valor Planeado
  EV  = Σ(cantidad_real  × valor_unit)   Valor Ganado
  AC  = Σ(facturas + nómina) hasta la fecha de corte de la Ejecución elegida

  SPI = EV / PV   (índice de rendimiento de cronograma)
  CPI = EV / AC   (índice de rendimiento de costos)
"""
from __future__ import annotations

import difflib
import unicodedata
from datetime import date

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QComboBox, QSizePolicy, QFrame, QGroupBox, QProgressBar,
    QMessageBox, QScrollArea,
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont, QColor, QBrush

from sqlalchemy import func
from models.database import SessionLocal
from models.ejecucion import Ejecucion
from models.factura import Factura
from models.factura_item import FacturaItem
from models.pago_nomina import PagoNomina


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _fmt(v: float) -> str:
    return f"$ {v:,.0f}"


_LIGHT = """
/* ── Raíz ── */
QWidget {
    background-color: #f5f6fa;
    color: #2c3e50;
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 13px;
}

/* ── GroupBox ── */
QGroupBox {
    background-color: #ffffff;
    border: 1px solid #dfe6e9;
    border-radius: 8px;
    margin-top: 14px;
    padding: 8px 6px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 6px;
    color: #2980b9;
    font-weight: bold;
    font-size: 12px;
}

/* ── Tabla ── */
QTableWidget {
    background-color: #ffffff;
    alternate-background-color: #f0f4f8;
    gridline-color: #dfe6e9;
    selection-background-color: #3498db;
    selection-color: white;
    border: 1px solid #dfe6e9;
    border-radius: 4px;
}
QTableWidget::item { padding: 4px 6px; }
QTableWidget::item:hover { background-color: #ebf5fb; }

QHeaderView::section {
    background-color: #e8f0f7;
    color: #2c3e50;
    padding: 6px;
    border: 1px solid #dfe6e9;
    font-weight: bold;
}

/* ── ComboBox ── */
QComboBox {
    background-color: #ffffff;
    border: 1px solid #bdc3c7;
    border-radius: 4px;
    padding: 5px 28px 5px 8px;
    color: #2c3e50;
}
QComboBox:hover { border-color: #3498db; }
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: center right;
    width: 26px;
    border-left: 1px solid #bdc3c7;
    border-top-right-radius: 4px;
    border-bottom-right-radius: 4px;
    background-color: #3498db;
}
QComboBox::drop-down:hover { background-color: #2980b9; }
QComboBox::down-arrow {
    image: url(views/arrow_down_white.svg);
    width: 14px; height: 14px;
}
QComboBox QAbstractItemView {
    background-color: #ffffff;
    color: #2c3e50;
    selection-background-color: #3498db;
    selection-color: white;
    border: 1px solid #bdc3c7;
}

/* ── Botones generales ── */
QPushButton {
    background-color: #3498db;
    color: white;
    border: none;
    border-radius: 5px;
    padding: 8px 18px;
    font-weight: bold;
}
QPushButton:hover { background-color: #2980b9; }
QPushButton:pressed { background-color: #1f6da8; }
QPushButton:disabled { background-color: #bdc3c7; color: #7f8c8d; }

/* ── QProgressBar ── */
QProgressBar {
    border: 1px solid #dfe6e9;
    border-radius: 5px;
    background-color: #ecf0f1;
    text-align: center;
    color: #2c3e50;
    height: 14px;
}
QProgressBar::chunk { border-radius: 5px; }

/* ── Separadores ── */
QFrame[frameShape="4"],
QFrame[frameShape="5"] {
    color: #dfe6e9;
}

/* ── Labels planos ── */
QLabel { background: transparent; }
"""


# ──────────────────────────────────────────────────────────────────────────────
# Tarjeta KPI
# ──────────────────────────────────────────────────────────────────────────────

class _KpiCard(QFrame):
    """Tarjeta de indicador EVM (PV / EV / AC)."""

    def __init__(self, titulo: str, color_border: str, color_bg: str,
                 parent: QWidget | None = None):
        super().__init__(parent)
        self.setStyleSheet(
            f"QFrame {{ background-color: {color_bg}; border: 2px solid {color_border}; "
            f"border-radius: 10px; }}"
        )
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(110)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 10, 14, 10)
        lay.setSpacing(4)

        lbl_tit = QLabel(titulo)
        lbl_tit.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        lbl_tit.setStyleSheet(f"color: {color_border}; background: transparent;")
        lbl_tit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(lbl_tit)

        self.lbl_val = QLabel("$ 0")
        self.lbl_val.setFont(QFont("Segoe UI", 26, QFont.Weight.Bold))
        self.lbl_val.setStyleSheet(f"color: {color_border}; background: transparent;")
        self.lbl_val.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self.lbl_val)

    def set_value(self, valor: float):
        self.lbl_val.setText(_fmt(valor))


# ──────────────────────────────────────────────────────────────────────────────
# Vista principal
# ──────────────────────────────────────────────────────────────────────────────

def _evm_normalizar(texto: str) -> str:
    t = texto.lower().strip()
    t = unicodedata.normalize("NFD", t)
    return "".join(c for c in t if unicodedata.category(c) != "Mn")


def _evm_similitud(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, _evm_normalizar(a), _evm_normalizar(b)).ratio()


class EvmView(QWidget):
    """
    Vista de Control EVM.

    Parámetros
    ----------
    get_cronograma_fn : callable → CronogramaView | None
        Función que devuelve el widget de cronograma activo (o None).
    get_presupuesto_fn : callable → PresupuestoView | None
        Función que devuelve la vista del presupuesto activo (o None).
        Se usa para leer los costos unitarios y pre-rellenar la tabla.
    parent : QWidget | None
    """

    def __init__(
        self,
        get_cronograma_fn,                      # () → CronogramaView | None
        get_presupuesto_fn=None,                # () → PresupuestoView | None
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self._get_cronograma = get_cronograma_fn
        self._get_presupuesto = get_presupuesto_fn or (lambda: None)
        self.setStyleSheet(_LIGHT)
        self._setup_ui()
        self._reload_ejecuciones()

    # ── Construcción de UI ────────────────────────────────────────────────────

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Banner superior azul ──────────────────────────────────────────────
        banner = QLabel("📈  CONTROL EVM  –  VALOR GANADO")
        banner.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        banner.setAlignment(Qt.AlignmentFlag.AlignCenter)
        banner.setStyleSheet(
            "background-color: #2980b9; color: white; padding: 14px; border: none;"
        )
        root.addWidget(banner)

        # ── Área desplazable ──────────────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { border: none; background: #f5f6fa; }")
        root.addWidget(scroll)

        container = QWidget()
        scroll.setWidget(container)
        lay = QVBoxLayout(container)
        lay.setContentsMargins(16, 14, 16, 14)
        lay.setSpacing(12)

        # ── Fila de configuración ─────────────────────────────────────────────
        cfg_frame = QFrame()
        cfg_frame.setStyleSheet(
            "QFrame { background: #ffffff; border: 1px solid #dfe6e9; border-radius: 8px; }"
        )
        cfg_lay = QHBoxLayout(cfg_frame)
        cfg_lay.setContentsMargins(14, 10, 14, 10)
        cfg_lay.setSpacing(12)

        # Fecha de corte (leída del cronograma)
        grp_corte = QGroupBox("📅  Periodo de Control (Cronograma)")
        corte_lay = QHBoxLayout(grp_corte)
        self.lbl_fecha_corte = QLabel("No calculada")
        self.lbl_fecha_corte.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.lbl_fecha_corte.setStyleSheet("color: #e67e22; background: transparent;")
        corte_lay.addWidget(QLabel("Fecha de corte:"))
        corte_lay.addWidget(self.lbl_fecha_corte)
        corte_lay.addStretch()
        cfg_lay.addWidget(grp_corte, 1)

        # Selección de ejecución para AC
        grp_ejec = QGroupBox("💰  Ejecución para Costo Actual (AC)")
        ejec_lay = QHBoxLayout(grp_ejec)
        self.cb_ejecucion = QComboBox()
        self.cb_ejecucion.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self.cb_ejecucion.setMinimumWidth(200)
        ejec_lay.addWidget(self.cb_ejecucion)
        cfg_lay.addWidget(grp_ejec, 1)

        lay.addWidget(cfg_frame)

        # ── Botón calcular ────────────────────────────────────────────────────
        self.btn_calcular = QPushButton("🔄  TRAER DATOS DEL CORTE Y CALCULAR")
        self.btn_calcular.setStyleSheet(
            "QPushButton { background-color: #8e44ad; color: white; font-weight: bold; "
            "padding: 12px; border-radius: 6px; font-size: 14px; }"
            "QPushButton:hover { background-color: #7d3c98; }"
            "QPushButton:pressed { background-color: #6c3483; }"
        )
        self.btn_calcular.clicked.connect(self._calcular_evm)
        lay.addWidget(self.btn_calcular)

        # ── Tarjetas KPI ──────────────────────────────────────────────────────
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(12)

        self.card_pv = _KpiCard(
            "VALOR PLANEADO  (PV)", "#1abc9c", "#e8f8f5"
        )
        self.card_ev = _KpiCard(
            "VALOR GANADO  (EV)", "#3498db", "#eaf2f8"
        )
        self.card_ac = _KpiCard(
            "COSTO ACTUAL  (AC)", "#e74c3c", "#fdedec"
        )
        kpi_row.addWidget(self.card_pv)
        kpi_row.addWidget(self.card_ev)
        kpi_row.addWidget(self.card_ac)
        lay.addLayout(kpi_row)

        # ── Salud del Proyecto ────────────────────────────────────────────────
        self.grp_salud = QGroupBox("🏥  Salud del Proyecto")
        salud_lay = QVBoxLayout(self.grp_salud)
        salud_lay.setSpacing(10)

        # SPI row
        spi_row = QHBoxLayout()
        lbl_spi_tit = QLabel("SPI (Cronograma):")
        lbl_spi_tit.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        lbl_spi_tit.setMinimumWidth(170)
        spi_row.addWidget(lbl_spi_tit)
        self.lbl_spi_val = QLabel("–")
        self.lbl_spi_val.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        self.lbl_spi_val.setMinimumWidth(60)
        spi_row.addWidget(self.lbl_spi_val)
        self.bar_spi = QProgressBar()
        self.bar_spi.setRange(0, 200)
        self.bar_spi.setValue(0)
        self.bar_spi.setTextVisible(False)
        self.bar_spi.setStyleSheet(
            "QProgressBar::chunk { background-color: #1abc9c; border-radius: 5px; }"
        )
        spi_row.addWidget(self.bar_spi, 1)
        self.lbl_spi_diag = QLabel("")
        self.lbl_spi_diag.setMinimumWidth(260)
        spi_row.addWidget(self.lbl_spi_diag)
        salud_lay.addLayout(spi_row)

        # CPI row
        cpi_row = QHBoxLayout()
        lbl_cpi_tit = QLabel("CPI (Costos):")
        lbl_cpi_tit.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        lbl_cpi_tit.setMinimumWidth(170)
        cpi_row.addWidget(lbl_cpi_tit)
        self.lbl_cpi_val = QLabel("–")
        self.lbl_cpi_val.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        self.lbl_cpi_val.setMinimumWidth(60)
        cpi_row.addWidget(self.lbl_cpi_val)
        self.bar_cpi = QProgressBar()
        self.bar_cpi.setRange(0, 200)
        self.bar_cpi.setValue(0)
        self.bar_cpi.setTextVisible(False)
        self.bar_cpi.setStyleSheet(
            "QProgressBar::chunk { background-color: #3498db; border-radius: 5px; }"
        )
        cpi_row.addWidget(self.bar_cpi, 1)
        self.lbl_cpi_diag = QLabel("")
        self.lbl_cpi_diag.setMinimumWidth(260)
        cpi_row.addWidget(self.lbl_cpi_diag)
        salud_lay.addLayout(cpi_row)

        # Diagnóstico general
        self.lbl_diagnostico = QLabel(
            "Realiza el 'Corte de Obra' en la pestaña Cronograma y luego presiona Calcular."
        )
        self.lbl_diagnostico.setFont(QFont("Segoe UI", 11))
        self.lbl_diagnostico.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_diagnostico.setStyleSheet(
            "background-color: #f8f9fa; border: 1px solid #dfe6e9; "
            "border-radius: 6px; padding: 10px; color: #7f8c8d;"
        )
        salud_lay.addWidget(self.lbl_diagnostico)

        lay.addWidget(self.grp_salud)

        # ── Tabla de detalle ──────────────────────────────────────────────────
        grp_tabla = QGroupBox("📋  Detalle de Tareas en el Corte")
        tabla_lay = QVBoxLayout(grp_tabla)

        # Nota informativa
        nota = QLabel(
            "ℹ️  Ingresa el <b>Valor Unitario</b> (columna amarilla) de cada tarea "
            "para calcular PV y EV automáticamente."
        )
        nota.setStyleSheet(
            "background: #fef9e7; border: 1px solid #f9ca24; border-radius: 5px; "
            "padding: 7px 10px; color: #7d6608;"
        )
        nota.setWordWrap(True)
        tabla_lay.addWidget(nota)

        self.tabla = QTableWidget(0, 7)
        self.tabla.setHorizontalHeaderLabels([
            "ID", "Nombre de Tarea",
            "Cant. Plan", "💛 Valor Unit",
            "Valor Plan", "Cant. Ejec.", "Valor Ejec.",
        ])
        hdr = self.tabla.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)   # Valor Unit — ancho fijo
        hdr.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        self.tabla.setColumnWidth(3, 120)   # Valor Unit: siempre visible

        self.tabla.setAlternatingRowColors(True)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectItems)
        self.tabla.setEditTriggers(
            QAbstractItemView.EditTrigger.DoubleClicked |
            QAbstractItemView.EditTrigger.SelectedClicked |
            QAbstractItemView.EditTrigger.EditKeyPressed |
            QAbstractItemView.EditTrigger.AnyKeyPressed
        )
        self.tabla.setMinimumHeight(300)
        # cellChanged(row, col) es más fiable que itemChanged para edición de usuario
        self.tabla.cellChanged.connect(self._on_cell_changed)
        tabla_lay.addWidget(self.tabla)

        lay.addWidget(grp_tabla)
        lay.addStretch()

    # ── Ejecuciones ───────────────────────────────────────────────────────────

    def _reload_ejecuciones(self):
        session = SessionLocal()
        try:
            ejecuciones = session.query(Ejecucion).order_by(Ejecucion.creado_en.desc()).all()
            self._ejec_list: list[tuple[int, str]] = [(e.id, e.nombre) for e in ejecuciones]
        except Exception as e:
            print("EvmView: error cargando ejecuciones:", e)
            self._ejec_list = []
        finally:
            session.close()

        self.cb_ejecucion.blockSignals(True)
        self.cb_ejecucion.clear()
        for eid, nombre in self._ejec_list:
            self.cb_ejecucion.addItem(nombre, userData=eid)
        self.cb_ejecucion.blockSignals(False)

    # ── Lectura del presupuesto ───────────────────────────────────────────────

    def _leer_ppto_items(self) -> list[tuple[str, float]]:
        """
        Lee la tabla del presupuesto activo y devuelve
        [(descripcion, costo_unitario), ...] solo para filas de análisis.
        """
        ppto = self._get_presupuesto()
        if ppto is None:
            return []
        try:
            table = ppto.table
        except AttributeError:
            return []

        items: list[tuple[str, float]] = []
        for row in range(table.rowCount()):
            item0 = table.item(row, 0)
            if not item0:
                continue
            role = item0.data(Qt.ItemDataRole.UserRole)
            # Saltar capítulos, subtotales y filas sin rol válido
            if role in ("chapter", "subtotal", None, ""):
                continue
            desc_it = table.item(row, 1)
            cu_it   = table.item(row, 4)
            desc = desc_it.text().strip() if desc_it else ""
            if not desc:
                continue
            cu_txt = (cu_it.text() if cu_it else "0").replace("$", "").replace(",", "").strip()
            try:
                cu = float(cu_txt) if cu_txt else 0.0
            except ValueError:
                cu = 0.0
            items.append((desc, cu))
        return items

    # ── Cálculo principal ─────────────────────────────────────────────────────

    def _calcular_evm(self):
        # 1. Recargar ejecuciones por si cambiaron
        self._reload_ejecuciones()

        # 2. Leer fecha de corte del cronograma
        cronograma = self._get_cronograma()
        if cronograma is None or not hasattr(cronograma, "fecha_linea_corte"):
            QMessageBox.warning(
                self, "Sin Cronograma",
                "Primero abre el Cronograma y realiza un 'Corte de Obra'."
            )
            return

        fecha_q: QDate | None = cronograma.fecha_linea_corte
        if fecha_q is None:
            QMessageBox.warning(
                self, "Sin fecha de corte",
                "No se ha definido una fecha de corte en el Cronograma.\n"
                "Usa el botón 'Corte de Obra' en la pestaña Cronograma."
            )
            return

        fecha_py: date = fecha_q.toPyDate()
        self.lbl_fecha_corte.setText(fecha_py.strftime("%d / %m / %Y"))
        self.lbl_fecha_corte.setStyleSheet(
            "color: #27ae60; font-weight: bold; background: transparent;"
        )

        # 3. Leer tareas del cronograma
        tasks: list[dict] = getattr(cronograma, "tasks", [])
        if not tasks:
            QMessageBox.warning(
                self, "Sin tareas",
                "El cronograma no tiene tareas cargadas.\n"
                "Abre un archivo .mpp o .xml en la pestaña Cronograma."
            )
            return

        # 4. Calcular AC desde la ejecución seleccionada
        self._calcular_ac(fecha_py)

        # 5. Poblar la tabla de detalle (preserva valores unitarios previos)
        self._poblar_tabla(tasks)

        # 6. Actualizar tarjetas (PV y EV se calculan en la tabla)
        self._actualizar_totales()

    def _calcular_ac(self, fecha_corte: date):
        """Suma gastos de compras + nómina de la ejecución elegida hasta la fecha de corte."""
        idx = self.cb_ejecucion.currentIndex()
        if idx < 0 or idx >= len(self._ejec_list):
            self._ac = 0.0
            self.card_ac.set_value(0.0)
            return

        eid, _ = self._ejec_list[idx]
        session = SessionLocal()
        try:
            # Compras (FacturaItem → Factura)
            # Se usa COALESCE(fecha_programada, fecha):
            #   - Si la factura tiene fecha_programada  → se filtra por ella (consumo diferido)
            #   - Si es NULL (Consumo Inmediato)         → se filtra por la fecha de compra
            # Solo se acumula al AC el gasto cuya fecha efectiva <= fecha de corte.
            fecha_efectiva = func.coalesce(Factura.fecha_programada, Factura.fecha)
            total_compras = (
                session.query(func.coalesce(func.sum(FacturaItem.total), 0.0))
                .join(Factura)
                .filter(
                    Factura.ejecucion_id == eid,
                    fecha_efectiva <= fecha_corte,
                )
                .scalar()
            )

            # Nómina (PagoNomina)
            total_nomina = (
                session.query(func.coalesce(func.sum(PagoNomina.total), 0.0))
                .filter(
                    PagoNomina.ejecucion_id == eid,
                    PagoNomina.fecha <= fecha_corte,
                )
                .scalar()
            )

            self._ac = float(total_compras or 0) + float(total_nomina or 0)
        except Exception as e:
            print("EvmView: error calculando AC:", e)
            self._ac = 0.0
        finally:
            session.close()

        self.card_ac.set_value(self._ac)

    # ── Tabla de detalle ──────────────────────────────────────────────────────

    def _poblar_tabla(self, tasks: list[dict]):
        """Llena la tabla con las tareas del cronograma, preservando valores unitarios."""
        # Guardar valores unitarios previos por nombre de tarea
        valores_previos: dict[str, float] = {}
        for row in range(self.tabla.rowCount()):
            nombre_item = self.tabla.item(row, 1)
            unidad_item = self.tabla.item(row, 3)
            if nombre_item and unidad_item:
                try:
                    v = float(
                        unidad_item.text()
                        .replace("$", "").replace(",", "").strip()
                    )
                    if v > 0:
                        valores_previos[nombre_item.text().strip()] = v
                except ValueError:
                    pass

        self.tabla.blockSignals(True)
        self.tabla.setRowCount(0)

        font_bold = QFont("Segoe UI", 9, QFont.Weight.Bold)
        font_reg = QFont("Segoe UI", 9)
        color_summary = QColor("#dce8f0")
        color_root = QColor("#c8dcea")
        color_yellow = QColor("#fffde7")

        # Leer costos unitarios del presupuesto para auto-rellenar Valor Unit
        ppto_items = self._leer_ppto_items()   # [(descripcion, costo_unit), ...]

        for t in tasks:
            row = self.tabla.rowCount()
            self.tabla.insertRow(row)

            is_summary = t.get("summary", False)
            is_root = t.get("indent", 2) == 1
            is_bold = is_summary or is_root

            # Cantidad planeada y ejecutada
            # cant_plan = cantidad total de la tarea × fracción programada al corte (% Esp.)
            # Esto replica la lógica de app.py: cant_esperada = plan * (pct_esp / 100)
            pct_esp = t.get("pct_esp", 100.0)   # 100% si no hay corte activo
            try:
                cant_plan_total = float(t.get("cantidad_obra", 0) or 0)
            except (ValueError, TypeError):
                cant_plan_total = 0.0
            cant_plan = cant_plan_total * (pct_esp / 100.0)
            try:
                cant_ejec = float(t.get("cantidad_real", 0) or 0)
            except (ValueError, TypeError):
                cant_ejec = 0.0

            # Nombre con indentación visual
            indent = t.get("indent", 1)
            prefix = "    " * max(0, indent - 1)
            nombre_texto = prefix + t.get("name", "")

            # Recuperar valor unitario previo (por nombre sin indent)
            val_unit_prev = valores_previos.get(t.get("name", "").strip(), 0.0)

            # Si no hay valor previo y tenemos datos del presupuesto, buscar coincidencia
            if not val_unit_prev and not is_summary and ppto_items:
                tarea_norm = t.get("name", "").strip()
                mejor_score = 0.45      # umbral mínimo
                mejor_cu = 0.0
                for desc_p, cu_p in ppto_items:
                    score = _evm_similitud(tarea_norm, desc_p)
                    if score > mejor_score:
                        mejor_score = score
                        mejor_cu = cu_p
                if mejor_cu > 0:
                    val_unit_prev = mejor_cu

            # ── Columnas ─────────────────────────────────────────────────────
            def locked(texto: str, bold: bool = False) -> QTableWidgetItem:
                it = QTableWidgetItem(texto)
                it.setFlags(it.flags() & ~Qt.ItemFlag.ItemIsEditable)
                if bold:
                    it.setFont(font_bold)
                else:
                    it.setFont(font_reg)
                return it

            # 0: ID
            self.tabla.setItem(row, 0, locked(str(t.get("id_visual", "")), is_bold))
            # 1: Nombre
            self.tabla.setItem(row, 1, locked(nombre_texto, is_bold))
            # 2: Cant. Plan  (= cantidad_obra × % Esp. / 100  — porción programada al corte)
            if is_summary or cant_plan == 0:
                cant_plan_txt = ""
            elif cant_plan == int(cant_plan):
                cant_plan_txt = str(int(cant_plan))
            else:
                cant_plan_txt = f"{cant_plan:.2f}"
            self.tabla.setItem(row, 2, locked(cant_plan_txt, is_bold))
            # 3: Valor Unit (editable, fondo amarillo)
            it_unit = QTableWidgetItem(f"{val_unit_prev:,.0f}" if val_unit_prev else "")
            it_unit.setFont(font_reg)
            it_unit.setBackground(QBrush(color_yellow))
            if is_summary or is_root:
                it_unit.setFlags(it_unit.flags() & ~Qt.ItemFlag.ItemIsEditable)
                it_unit.setBackground(QBrush(
                    color_root if is_root else color_summary
                ))
            self.tabla.setItem(row, 3, it_unit)
            # 4: Valor Plan (calculado)
            self.tabla.setItem(row, 4, locked("", is_bold))
            # 5: Cant. Ejec.
            cant_ejec_txt = str(cant_ejec) if (not is_summary or cant_ejec) else ""
            self.tabla.setItem(row, 5, locked(cant_ejec_txt, is_bold))
            # 6: Valor Ejec. (calculado)
            self.tabla.setItem(row, 6, locked("", is_bold))

            # Fondo de filas resumen
            if is_root:
                bg = color_root
            elif is_summary:
                bg = color_summary
            else:
                bg = QColor("#ffffff")

            for col in (0, 1, 2, 4, 5, 6):
                it = self.tabla.item(row, col)
                if it:
                    it.setBackground(QBrush(bg))

        self.tabla.blockSignals(False)

        # Recalcular todas las filas que ya tenían valor unitario guardado
        # (señal ya desconectada por blockSignals arriba, reconectar al final)
        self.tabla.cellChanged.disconnect(self._on_cell_changed)
        try:
            for row in range(self.tabla.rowCount()):
                it = self.tabla.item(row, 3)
                if it and it.text().strip():
                    self._recalcular_fila(row)
        finally:
            self.tabla.cellChanged.connect(self._on_cell_changed)

    # ── Callbacks de la tabla ─────────────────────────────────────────────────

    def _on_cell_changed(self, row: int, col: int):
        """Dispara solo cuando el usuario edita la columna 'Valor Unit' (col 3)."""
        if col != 3:
            return
        # Desconectar señal para evitar re-entradas mientras escribimos en cols 4/6
        self.tabla.cellChanged.disconnect(self._on_cell_changed)
        try:
            self._recalcular_fila(row)
            self._actualizar_totales()
        finally:
            self.tabla.cellChanged.connect(self._on_cell_changed)

    def _recalcular_fila(self, row: int):
        """Actualiza Valor Plan (col 4) y Valor Ejec. (col 6) de una fila."""
        it_unit = self.tabla.item(row, 3)
        txt_unit = (it_unit.text() if it_unit else "").replace("$", "").replace(",", "").strip()
        try:
            val_unit = float(txt_unit) if txt_unit else 0.0
        except ValueError:
            val_unit = 0.0

        def _float_cell(c: int) -> float:
            it = self.tabla.item(row, c)
            txt = (it.text() if it else "").replace(",", "").replace("$", "").strip()
            try:
                return float(txt) if txt else 0.0
            except ValueError:
                return 0.0

        cant_plan = _float_cell(2)
        cant_ejec = _float_cell(5)

        vp = cant_plan * val_unit
        ve = cant_ejec * val_unit

        # Escribir directamente (señal ya está desconectada en el caller, o
        # estamos en el bucle de recarga inicial que también bloquea señales)
        for dest_col, valor in ((4, vp), (6, ve)):
            it = self.tabla.item(row, dest_col)
            if it is None:
                it = QTableWidgetItem()
                self.tabla.setItem(row, dest_col, it)
            it.setFlags(it.flags() & ~Qt.ItemFlag.ItemIsEditable)
            it.setText(f"$ {valor:,.0f}" if valor else "")

    def _actualizar_totales(self):
        """Suma PV y EV de toda la tabla y actualiza tarjetas + salud."""
        total_pv = 0.0
        total_ev = 0.0

        for row in range(self.tabla.rowCount()):
            for pv_col, ev_col in ((4, 6),):
                for col in (pv_col, ev_col):
                    it = self.tabla.item(row, col)
                    if not it or not it.text().strip():
                        continue
                    txt = it.text().replace("$", "").replace(",", "").strip()
                    try:
                        v = float(txt)
                    except ValueError:
                        v = 0.0
                    if col == 4:
                        total_pv += v
                    else:
                        total_ev += v

        self.card_pv.set_value(total_pv)
        self.card_ev.set_value(total_ev)
        self._actualizar_salud(total_pv, total_ev, self._ac if hasattr(self, "_ac") else 0.0)

    def _actualizar_salud(self, pv: float, ev: float, ac: float):
        """Actualiza indicadores SPI, CPI y diagnóstico."""
        if pv <= 0 and ac <= 0:
            self.lbl_diagnostico.setText(
                "Ingresa los Valores Unitarios en la tabla para calcular la salud del proyecto."
            )
            self.lbl_diagnostico.setStyleSheet(
                "background: #f8f9fa; border: 1px solid #dfe6e9; "
                "border-radius: 6px; padding: 10px; color: #7f8c8d;"
            )
            self.lbl_spi_val.setText("–")
            self.lbl_cpi_val.setText("–")
            self.bar_spi.setValue(0)
            self.bar_cpi.setValue(0)
            self.lbl_spi_diag.setText("")
            self.lbl_cpi_diag.setText("")
            return

        # SPI
        spi = ev / pv if pv > 0 else 0.0
        # CPI
        cpi = ev / ac if ac > 0 else 0.0

        self.lbl_spi_val.setText(f"{spi:.2f}")
        self.lbl_cpi_val.setText(f"{cpi:.2f}")

        # Barras (escala 0-200 donde 100 = 1.0)
        self.bar_spi.setValue(min(int(spi * 100), 200))
        self.bar_cpi.setValue(min(int(cpi * 100), 200))

        # Color de barras y texto
        if spi >= 1.0:
            spi_color = "#27ae60"
            spi_txt = "🟢 ADELANTADO – el avance supera lo planeado"
            self.lbl_spi_val.setStyleSheet("color: #27ae60; background: transparent;")
        elif spi >= 0.85:
            spi_color = "#f39c12"
            spi_txt = "🟡 LEVEMENTE ATRASADO – monitorear de cerca"
            self.lbl_spi_val.setStyleSheet("color: #f39c12; background: transparent;")
        else:
            spi_color = "#e74c3c"
            spi_txt = "🔴 ATRASADO – requiere acción correctiva"
            self.lbl_spi_val.setStyleSheet("color: #e74c3c; background: transparent;")

        if cpi >= 1.0:
            cpi_color = "#27ae60"
            cpi_txt = "🟢 BAJO PRESUPUESTO – costos menores a lo planeado"
            self.lbl_cpi_val.setStyleSheet("color: #27ae60; background: transparent;")
        elif cpi >= 0.85:
            cpi_color = "#f39c12"
            cpi_txt = "🟡 LEVE SOBRECOSTO – revisar gastos"
            self.lbl_cpi_val.setStyleSheet("color: #f39c12; background: transparent;")
        else:
            cpi_color = "#e74c3c"
            cpi_txt = "🔴 SOBRECOSTO CRÍTICO – acción urgente requerida"
            self.lbl_cpi_val.setStyleSheet("color: #e74c3c; background: transparent;")

        self.bar_spi.setStyleSheet(
            f"QProgressBar {{ border: 1px solid #dfe6e9; border-radius: 5px; "
            f"background-color: #ecf0f1; height: 14px; }}"
            f"QProgressBar::chunk {{ background-color: {spi_color}; border-radius: 5px; }}"
        )
        self.bar_cpi.setStyleSheet(
            f"QProgressBar {{ border: 1px solid #dfe6e9; border-radius: 5px; "
            f"background-color: #ecf0f1; height: 14px; }}"
            f"QProgressBar::chunk {{ background-color: {cpi_color}; border-radius: 5px; }}"
        )

        self.lbl_spi_diag.setText(spi_txt)
        self.lbl_spi_diag.setStyleSheet(f"color: {spi_color}; background: transparent;")
        self.lbl_cpi_diag.setText(cpi_txt)
        self.lbl_cpi_diag.setStyleSheet(f"color: {cpi_color}; background: transparent;")

        # Diagnóstico general
        if spi >= 1.0 and cpi >= 1.0:
            diag = "✅ <b>PROYECTO EN EXCELENTE ESTADO</b> – adelantado y bajo presupuesto."
            diag_style = "background: #eafaf1; border: 1px solid #27ae60; color: #1e8449;"
        elif spi < 0.85 and cpi < 0.85:
            diag = "🚨 <b>ALERTA CRÍTICA</b> – atrasado Y con sobrecosto. Revisar plan de acción."
            diag_style = "background: #fdedec; border: 1px solid #e74c3c; color: #922b21;"
        elif spi < 1.0 or cpi < 1.0:
            diag = "⚠️ <b>ATENCIÓN REQUERIDA</b> – hay desviaciones en cronograma o costos."
            diag_style = "background: #fef9e7; border: 1px solid #f39c12; color: #7d6608;"
        else:
            diag = "✅ <b>PROYECTO EN BUEN ESTADO</b>."
            diag_style = "background: #eafaf1; border: 1px solid #27ae60; color: #1e8449;"

        self.lbl_diagnostico.setText(diag)
        self.lbl_diagnostico.setStyleSheet(
            f"{diag_style} border-radius: 6px; padding: 10px;"
        )

    # ── Actualización cuando se activa la pestaña ─────────────────────────────

    def refresh(self):
        """Recarga ejecuciones disponibles (útil cuando se activa la pestaña)."""
        self._reload_ejecuciones()

