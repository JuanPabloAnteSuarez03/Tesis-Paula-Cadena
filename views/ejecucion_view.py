# views/ejecucion_view.py
"""
Vista de Ejecución (Gastos) para AppPresupuestos.
Incluye dos sub-pestañas: Compras (Facturas) y Nómina.
Los datos se guardan en PostgreSQL usando los modelos Factura, FacturaItem y PagoNomina.
"""
from __future__ import annotations

from datetime import date

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTabWidget,
    QGroupBox, QGridLayout, QLineEdit, QComboBox, QPushButton,
    QCheckBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QSizePolicy, QMessageBox, QDialog,
    QFrame, QCompleter, QDateEdit, QSpacerItem, QCalendarWidget,
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QFont, QColor

from sqlalchemy import text
from models.database import SessionLocal, engine, Base
from models.ejecucion import Ejecucion
from models.factura import Factura
from models.factura_item import FacturaItem
from models.pago_nomina import PagoNomina


def _ensure_tables():
    """Crea tablas de ejecución y migra columnas nuevas si no existen."""
    try:
        # 1. Crea la tabla ejecuciones (y otras nuevas) si no existen
        Base.metadata.create_all(bind=engine, checkfirst=True)
    except Exception as e:
        print(f"[EjecucionView] advertencia al crear tablas: {e}")

    # 2. Migrar columna ejecucion_id en facturas y pagos_nomina
    #    (ALTER TABLE … ADD COLUMN IF NOT EXISTS — solo PostgreSQL)
    _alter_sqls = [
        "ALTER TABLE facturas     ADD COLUMN IF NOT EXISTS ejecucion_id INTEGER REFERENCES ejecuciones(id)",
        "ALTER TABLE pagos_nomina ADD COLUMN IF NOT EXISTS ejecucion_id INTEGER REFERENCES ejecuciones(id)",
    ]
    try:
        with engine.begin() as conn:
            for sql in _alter_sqls:
                try:
                    conn.execute(text(sql))
                except Exception:
                    pass   # columna ya existe u otro error no crítico
    except Exception as e:
        print(f"[EjecucionView] advertencia en migración: {e}")


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

class DatePickerWidget(QWidget):
    """
    Widget de selección de fecha con campo de texto y botón 📅 visible.
    Abre un QCalendarWidget en un diálogo emergente.
    Compatible con modo oscuro del sistema.
    """
    dateChanged = pyqtSignal(QDate)

    _FIELD_STYLE = """
        QLineEdit {
            background-color: #ffffff;
            color: #2c3e50;
            border: 1px solid #bdc3c7;
            border-right: none;
            border-top-left-radius: 4px;
            border-bottom-left-radius: 4px;
            padding: 5px 7px;
        }
        QLineEdit:focus {
            border: 2px solid #3498db;
            border-right: none;
        }
    """
    _BTN_STYLE = """
        QPushButton {
            background-color: #3498db;
            color: white;
            border: 1px solid #2980b9;
            border-top-right-radius: 4px;
            border-bottom-right-radius: 4px;
            padding: 5px 9px;
            font-size: 15px;
        }
        QPushButton:hover {
            background-color: #2980b9;
        }
        QPushButton:pressed {
            background-color: #1f6da8;
        }
    """
    _CAL_STYLE = """
        /* ── Contenedor principal ── */
        QCalendarWidget {
            background-color: #ffffff;
        }

        /* ── Barra de navegación (mes / año) ── */
        QCalendarWidget QWidget#qt_calendar_navigationbar {
            background-color: #2980b9;
            padding: 4px 2px;
        }

        /* ── Botones de navegación (flechas ◀ ▶ y mes/año) ── */
        QCalendarWidget QToolButton {
            color: white;
            background-color: transparent;
            border: none;
            border-radius: 4px;
            padding: 4px 10px;
            font-weight: bold;
            font-size: 13px;
            min-width: 28px;
        }
        QCalendarWidget QToolButton:hover {
            background-color: rgba(255,255,255,0.25);
        }
        QCalendarWidget QToolButton:pressed {
            background-color: rgba(255,255,255,0.45);
        }
        QCalendarWidget QToolButton::menu-indicator {
            image: none;
        }

        /* ── SpinBox del año ── */
        QCalendarWidget QSpinBox {
            background-color: #ffffff;
            color: #2c3e50;
            border: 1px solid #bdc3c7;
            border-radius: 3px;
            padding: 2px 4px;
        }
        QCalendarWidget QSpinBox::up-button,
        QCalendarWidget QSpinBox::down-button {
            background-color: #dce3ec;
            border: none;
        }
        QCalendarWidget QSpinBox::up-button:hover,
        QCalendarWidget QSpinBox::down-button:hover {
            background-color: #3498db;
        }

        /* ── Menú desplegable del mes ── */
        QCalendarWidget QMenu {
            background-color: #ffffff;
            color: #2c3e50;
            border: 1px solid #bdc3c7;
            border-radius: 4px;
            padding: 4px 0px;
        }
        QCalendarWidget QMenu::item {
            padding: 5px 18px;
            border-radius: 3px;
        }
        QCalendarWidget QMenu::item:selected {
            background-color: #3498db;
            color: white;
        }
        QCalendarWidget QMenu::item:hover {
            background-color: #ebf5fb;
            color: #2980b9;
        }

        /* ── Encabezados de días (Lun, Mar…) ── */
        QCalendarWidget QWidget {
            alternate-background-color: #f0f6fc;
        }

        /* ── Cuerpo del calendario (días) ── */
        QCalendarWidget QAbstractItemView {
            background-color: #ffffff;
            color: #2c3e50;
            selection-background-color: #3498db;
            selection-color: white;
            outline: none;
        }
        QCalendarWidget QAbstractItemView:enabled {
            color: #2c3e50;
        }
        QCalendarWidget QAbstractItemView:disabled {
            color: #b0bec5;
        }

        /* ── Hover sobre cada día ── */
        QCalendarWidget QAbstractItemView::item:hover {
            background-color: #d6eaf8;
            color: #1a5276;
            border-radius: 3px;
        }

        /* ── Día de hoy (sin seleccionar) ── */
        QCalendarWidget QAbstractItemView::item:selected {
            background-color: #3498db;
            color: white;
            border-radius: 3px;
            font-weight: bold;
        }
    """

    def __init__(self, default: QDate | None = None, parent: QWidget | None = None):
        super().__init__(parent)
        self._date = default or QDate.currentDate()
        self._build()

    def _build(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._le = QLineEdit()
        self._le.setReadOnly(True)
        self._le.setMinimumWidth(110)
        self._le.setStyleSheet(self._FIELD_STYLE)
        self._le.setText(self._date.toString("dd/MM/yyyy"))

        self._btn = QPushButton("📅")
        self._btn.setFixedWidth(36)
        self._btn.setStyleSheet(self._BTN_STYLE)
        self._btn.setToolTip("Seleccionar fecha")
        self._btn.clicked.connect(self._open_calendar)

        layout.addWidget(self._le)
        layout.addWidget(self._btn)

    def _open_calendar(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Seleccionar Fecha")
        dlg.setWindowFlags(
            Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint
        )
        # Forzar fondo blanco en el popup para evitar problemas con el modo oscuro
        dlg.setStyleSheet(
            "QDialog { background-color: #ffffff; border: 1px solid #bdc3c7; "
            "border-radius: 6px; }"
        )

        v = QVBoxLayout(dlg)
        v.setContentsMargins(6, 6, 6, 6)
        v.setSpacing(6)

        cal = QCalendarWidget()
        cal.setStyleSheet(self._CAL_STYLE)
        cal.setGridVisible(True)
        cal.setSelectedDate(self._date)
        cal.setVerticalHeaderFormat(
            QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader
        )
        v.addWidget(cal)

        btn_ok = QPushButton("✔  Aceptar")
        btn_ok.setStyleSheet(
            "QPushButton { background-color: #27ae60; color: white; "
            "font-weight: bold; padding: 7px 14px; border-radius: 4px; "
            "border: 1px solid #1e8449; }"
            "QPushButton:hover { background-color: #219a52; }"
            "QPushButton:pressed { background-color: #1a7a40; }"
        )

        def _accept():
            self._date = cal.selectedDate()
            self._le.setText(self._date.toString("dd/MM/yyyy"))
            self.dateChanged.emit(self._date)
            dlg.accept()

        btn_ok.clicked.connect(_accept)
        cal.activated.connect(lambda _: _accept())   # doble-clic en día
        v.addWidget(btn_ok)

        # Posicionar el popup justo debajo del botón
        pos = self._btn.mapToGlobal(self._btn.rect().bottomLeft())
        dlg.move(pos)
        dlg.exec()

    # ── API pública compatible con QDateEdit ─────────────────────────────────
    def date(self) -> QDate:
        return self._date

    def setDate(self, qdate: QDate):
        self._date = qdate
        self._le.setText(qdate.toString("dd/MM/yyyy"))


def _make_date_edit(default: QDate | None = None) -> DatePickerWidget:
    """Devuelve un DatePickerWidget listo para usar."""
    return DatePickerWidget(default)


def _locked_item(text: str) -> QTableWidgetItem:
    """Crea un QTableWidgetItem no editable."""
    item = QTableWidgetItem(text)
    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
    return item


def _fmt(value: float) -> str:
    return f"${value:,.0f}"


# ──────────────────────────────────────────────────────────────────────────────
# Sub-tab: Compras / Facturas
# ──────────────────────────────────────────────────────────────────────────────

class ComprasWidget(QWidget):
    """Sub-pestaña de registro y consulta de facturas de compra."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._items_temp: list[dict] = []   # ítems de la factura en construcción
        self._ejecucion_id: int | None = None
        self._setup_ui()
        self._reload_history()
        self._reload_autocomplete()

    def set_ejecucion(self, ejecucion_id: int | None):
        """Cambia la ejecución activa y recarga los datos."""
        self._ejecucion_id = ejecucion_id
        self._reload_history()
        self._reload_autocomplete()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _setup_ui(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)

        # ── Panel izquierdo (formulario) ──────────────────────────────────────
        left = QWidget()
        left.setMaximumWidth(480)
        left.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        l_left = QVBoxLayout(left)
        l_left.setContentsMargins(0, 0, 0, 0)
        l_left.setSpacing(6)

        # 1. Datos de factura
        grp_datos = QGroupBox("1. Datos de la Factura")
        g_datos = QGridLayout(grp_datos)

        g_datos.addWidget(QLabel("Fecha:"), 0, 0)
        self.de_fecha = _make_date_edit()
        g_datos.addWidget(self.de_fecha, 0, 1)

        g_datos.addWidget(QLabel("N° Factura:"), 0, 2)
        self.le_num_factura = QLineEdit()
        self.le_num_factura.setPlaceholderText("Ej: FAC-001")
        g_datos.addWidget(self.le_num_factura, 0, 3)

        g_datos.addWidget(QLabel("Proveedor:"), 1, 0)
        self.cb_proveedor = QComboBox()
        self.cb_proveedor.setEditable(True)
        self.cb_proveedor.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.cb_proveedor.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        g_datos.addWidget(self.cb_proveedor, 1, 1, 1, 3)

        l_left.addWidget(grp_datos)

        # 2. Agregar ítems
        grp_add = QGroupBox("2. Agregar Ítem")
        g_add = QGridLayout(grp_add)

        g_add.addWidget(QLabel("Insumo:"), 0, 0)
        self.cb_insumo = QComboBox()
        self.cb_insumo.setEditable(True)
        self.cb_insumo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.cb_insumo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        g_add.addWidget(self.cb_insumo, 0, 1, 1, 3)

        g_add.addWidget(QLabel("Cant:"), 1, 0)
        self.le_cantidad = QLineEdit("1")
        g_add.addWidget(self.le_cantidad, 1, 1)

        g_add.addWidget(QLabel("Vr. Unit:"), 1, 2)
        self.le_precio = QLineEdit("0")
        g_add.addWidget(self.le_precio, 1, 3)

        self.chk_iva = QCheckBox("Aplicar IVA (19%)")
        btn_agregar = QPushButton("⬇  AGREGAR")
        btn_agregar.setStyleSheet(
            "background-color: #3498db; color: white; font-weight: bold; padding: 6px;"
        )
        btn_agregar.clicked.connect(self._on_agregar_item)
        g_add.addWidget(self.chk_iva, 2, 0, 1, 2)
        g_add.addWidget(btn_agregar, 2, 2, 1, 2)

        l_left.addWidget(grp_add)

        # 3. Detalle temporal de ítems
        grp_lista = QGroupBox("3. Detalle de Ítems")
        g_lista = QVBoxLayout(grp_lista)

        self.tbl_temp = QTableWidget(0, 4)
        self.tbl_temp.setHorizontalHeaderLabels(["Descripción", "Cant", "Unit", "Total"])
        self.tbl_temp.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tbl_temp.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tbl_temp.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tbl_temp.setAlternatingRowColors(True)
        self.tbl_temp.setMaximumHeight(200)
        g_lista.addWidget(self.tbl_temp)

        f_btns = QHBoxLayout()
        btn_editar = QPushButton("✏️ Editar")
        btn_editar.clicked.connect(self._on_editar_item)
        btn_quitar = QPushButton("❌ Quitar")
        btn_quitar.clicked.connect(self._on_quitar_item)
        f_btns.addWidget(btn_editar)
        f_btns.addWidget(btn_quitar)
        g_lista.addLayout(f_btns)

        l_left.addWidget(grp_lista)

        # Total + guardar
        self.lbl_total_fact = QLabel("Total Factura: $ 0")
        self.lbl_total_fact.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        self.lbl_total_fact.setAlignment(Qt.AlignmentFlag.AlignRight)
        l_left.addWidget(self.lbl_total_fact)

        btn_guardar = QPushButton("💾  TERMINAR Y GUARDAR FACTURA")
        btn_guardar.setStyleSheet(
            "background-color: #27ae60; color: white; padding: 10px; font-weight: bold; border-radius: 4px;"
        )
        btn_guardar.clicked.connect(self._on_guardar_factura)
        l_left.addWidget(btn_guardar)

        root.addWidget(left)

        # ── Panel derecho (historial) ─────────────────────────────────────────
        grp_hist = QGroupBox("Historial de Compras")
        grp_hist.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        l_hist = QVBoxLayout(grp_hist)

        # Barra de búsqueda y botones
        f_busq = QHBoxLayout()
        self.le_buscar = QLineEdit()
        self.le_buscar.setPlaceholderText("Buscar en historial…")
        btn_buscar = QPushButton("🔍 Buscar")
        btn_buscar.clicked.connect(self._on_filtrar)
        self.btn_orden = QPushButton("🔃 Ordenar: Creación")
        self._orden_fecha = False
        self.btn_orden.clicked.connect(self._on_alternar_orden)
        btn_editar_hist = QPushButton("✏️ Editar Datos")
        btn_editar_hist.clicked.connect(lambda: self._on_ver_detalle(modo_edicion=True))
        btn_eliminar = QPushButton("🗑 Eliminar")
        btn_eliminar.setStyleSheet("color: #c0392b; font-weight: bold;")
        btn_eliminar.clicked.connect(self._on_eliminar_factura)

        f_busq.addWidget(self.le_buscar)
        f_busq.addWidget(btn_buscar)
        f_busq.addWidget(self.btn_orden)
        f_busq.addWidget(btn_editar_hist)
        f_busq.addWidget(btn_eliminar)
        l_hist.addLayout(f_busq)

        self.lbl_acumulado = QLabel("Acumulado: $ 0")
        self.lbl_acumulado.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.lbl_acumulado.setAlignment(Qt.AlignmentFlag.AlignRight)
        l_hist.addWidget(self.lbl_acumulado)

        self.tbl_hist = QTableWidget(0, 5)
        self.tbl_hist.setHorizontalHeaderLabels(["Fecha", "Fact", "Prov", "Ítem", "Total"])
        self.tbl_hist.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.tbl_hist.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tbl_hist.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tbl_hist.setAlternatingRowColors(True)
        self.tbl_hist.itemDoubleClicked.connect(lambda _: self._on_ver_detalle(False))
        l_hist.addWidget(self.tbl_hist)

        root.addWidget(grp_hist)

    # ── Lógica interna ────────────────────────────────────────────────────────

    def _reload_autocomplete(self):
        """Recarga los combos de Proveedor e Insumo desde la BD."""
        session = SessionLocal()
        try:
            proveedores = sorted({
                f.proveedor for f in session.query(Factura.proveedor).distinct()
                if f.proveedor
            })
            insumos = sorted({
                i.insumo for i in session.query(FacturaItem.insumo).distinct()
                if i.insumo
            })
        except Exception:
            proveedores, insumos = [], []
        finally:
            session.close()

        self.cb_proveedor.clear()
        self.cb_proveedor.addItems(proveedores)
        self.cb_proveedor.setCurrentText("")
        comp_prov = QCompleter(proveedores)
        comp_prov.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        comp_prov.setFilterMode(Qt.MatchFlag.MatchContains)
        self.cb_proveedor.setCompleter(comp_prov)

        self.cb_insumo.clear()
        self.cb_insumo.addItems(insumos)
        self.cb_insumo.setCurrentText("")
        comp_ins = QCompleter(insumos)
        comp_ins.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        comp_ins.setFilterMode(Qt.MatchFlag.MatchContains)
        self.cb_insumo.setCompleter(comp_ins)

    def _reload_history(self, filter_text: str = ""):
        """Carga / filtra el historial de facturas desde BD."""
        session = SessionLocal()
        try:
            query = session.query(Factura)
            # Filtrar por ejecución activa
            if self._ejecucion_id is not None:
                query = query.filter(Factura.ejecucion_id == self._ejecucion_id)
            else:
                query = query.filter(Factura.ejecucion_id.is_(None))
            if self._orden_fecha:
                query = query.order_by(Factura.fecha.desc())
            else:
                query = query.order_by(Factura.id.asc())
            facturas = query.all()

            self.tbl_hist.setRowCount(0)
            acumulado = 0.0
            q = filter_text.strip().lower()

            for factura in facturas:
                for item in factura.items:
                    # Filtro de texto
                    if q and not any(
                        q in str(v).lower()
                        for v in [factura.numero_factura, factura.proveedor, item.insumo,
                                   str(factura.fecha)]
                    ):
                        continue

                    row = self.tbl_hist.rowCount()
                    self.tbl_hist.insertRow(row)

                    fecha_str = factura.fecha.strftime("%d/%m/%Y") if factura.fecha else ""
                    it_fecha = _locked_item(fecha_str)
                    it_fecha.setData(Qt.ItemDataRole.UserRole, factura.id)

                    self.tbl_hist.setItem(row, 0, it_fecha)
                    self.tbl_hist.setItem(row, 1, _locked_item(factura.numero_factura))
                    self.tbl_hist.setItem(row, 2, _locked_item(factura.proveedor))
                    self.tbl_hist.setItem(row, 3, _locked_item(item.insumo))
                    self.tbl_hist.setItem(row, 4, _locked_item(_fmt(item.total)))
                    acumulado += item.total

            self.lbl_acumulado.setText(f"Acumulado: {_fmt(acumulado)}")
        except Exception as e:
            print("Error cargando historial compras:", e)
        finally:
            session.close()

    def _update_total_temp(self):
        total = sum(i["total"] for i in self._items_temp)
        self.lbl_total_fact.setText(f"Total Factura: {_fmt(total)}")

    # ── Slots ─────────────────────────────────────────────────────────────────

    def _on_agregar_item(self):
        insumo = self.cb_insumo.currentText().strip().upper()
        if not insumo:
            QMessageBox.warning(self, "Error", "Ingrese el nombre del insumo.")
            return
        try:
            cantidad = float(self.le_cantidad.text().replace(",", "."))
            precio_unit = float(self.le_precio.text().replace(",", "."))
        except ValueError:
            QMessageBox.warning(self, "Error", "Cantidad y precio deben ser numéricos.")
            return

        aplica_iva = self.chk_iva.isChecked()
        subtotal = cantidad * precio_unit
        total = subtotal * 1.19 if aplica_iva else subtotal
        nombre_display = insumo + (" (c/IVA)" if aplica_iva else "")

        self._items_temp.append({
            "insumo": nombre_display,
            "cantidad": cantidad,
            "precio_unitario": precio_unit,
            "aplica_iva": aplica_iva,
            "total": total,
        })

        row = self.tbl_temp.rowCount()
        self.tbl_temp.insertRow(row)
        self.tbl_temp.setItem(row, 0, _locked_item(nombre_display))
        self.tbl_temp.setItem(row, 1, _locked_item(str(cantidad)))
        self.tbl_temp.setItem(row, 2, _locked_item(_fmt(precio_unit)))
        self.tbl_temp.setItem(row, 3, _locked_item(_fmt(total)))

        self._update_total_temp()
        self.cb_insumo.setCurrentText("")
        self.le_cantidad.setText("1")
        self.le_precio.setText("0")
        self.chk_iva.setChecked(False)

    def _on_editar_item(self):
        row = self.tbl_temp.currentRow()
        if row < 0:
            return
        item = self._items_temp[row]
        nombre_raw = item["insumo"]
        if "(C/IVA)" in nombre_raw.upper():
            self.chk_iva.setChecked(True)
            self.cb_insumo.setCurrentText(
                nombre_raw.replace(" (c/IVA)", "").replace(" (C/IVA)", "")
            )
        else:
            self.chk_iva.setChecked(False)
            self.cb_insumo.setCurrentText(nombre_raw)
        self.le_cantidad.setText(str(item["cantidad"]))
        self.le_precio.setText(str(item["precio_unitario"]))

        del self._items_temp[row]
        self.tbl_temp.removeRow(row)
        self._update_total_temp()

    def _on_quitar_item(self):
        row = self.tbl_temp.currentRow()
        if row < 0:
            return
        del self._items_temp[row]
        self.tbl_temp.removeRow(row)
        self._update_total_temp()

    def _on_guardar_factura(self):
        if self._ejecucion_id is None:
            QMessageBox.warning(self, "Sin ejecución",
                "Selecciona o crea una ejecución antes de registrar facturas.")
            return
        num = self.le_num_factura.text().strip().upper()
        proveedor = self.cb_proveedor.currentText().strip().upper()
        if not num:
            QMessageBox.warning(self, "Error", "Ingrese el número de factura.")
            return
        if not self._items_temp:
            QMessageBox.warning(self, "Error", "Agregue al menos un ítem a la factura.")
            return

        qdate = self.de_fecha.date()
        fecha_py = date(qdate.year(), qdate.month(), qdate.day())

        session = SessionLocal()
        try:
            factura = Factura(
                numero_factura=num,
                fecha=fecha_py,
                proveedor=proveedor,
                ejecucion_id=self._ejecucion_id,
            )
            session.add(factura)
            session.flush()  # para obtener el ID

            for it in self._items_temp:
                fi = FacturaItem(
                    factura_id=factura.id,
                    insumo=it["insumo"],
                    cantidad=it["cantidad"],
                    precio_unitario=it["precio_unitario"],
                    aplica_iva=it["aplica_iva"],
                    total=it["total"],
                )
                session.add(fi)

            session.commit()
            QMessageBox.information(self, "Guardado", "Factura guardada correctamente.")
        except Exception as e:
            session.rollback()
            QMessageBox.critical(self, "Error", f"No se pudo guardar la factura:\n{e}")
            return
        finally:
            session.close()

        # Limpiar formulario
        self._items_temp.clear()
        self.tbl_temp.setRowCount(0)
        self.le_num_factura.clear()
        self.cb_proveedor.setCurrentText("")
        self._update_total_temp()
        self._reload_history()
        self._reload_autocomplete()

    def _on_filtrar(self):
        self._reload_history(self.le_buscar.text())

    def _on_alternar_orden(self):
        self._orden_fecha = not self._orden_fecha
        self.btn_orden.setText(
            "🔃 Ordenar: Fecha (Reciente)" if self._orden_fecha else "🔃 Ordenar: Creación"
        )
        self._reload_history()

    def _on_eliminar_factura(self):
        row = self.tbl_hist.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Aviso", "Selecciona una fila del historial para eliminar.")
            return
        factura_id = self.tbl_hist.item(row, 0).data(Qt.ItemDataRole.UserRole)
        num_fact = self.tbl_hist.item(row, 1).text()
        prov = self.tbl_hist.item(row, 2).text()

        resp = QMessageBox.question(
            self, "Confirmar",
            f"¿Eliminar TODAS las líneas de la Factura N° {num_fact} (Proveedor: {prov})?"
        )
        if resp != QMessageBox.StandardButton.Yes:
            return

        session = SessionLocal()
        try:
            factura = session.query(Factura).get(factura_id)
            if factura:
                session.delete(factura)
                session.commit()
                QMessageBox.information(self, "Éxito", "Factura eliminada correctamente.")
            else:
                QMessageBox.warning(self, "Error", "No se encontró la factura en la base de datos.")
        except Exception as e:
            session.rollback()
            QMessageBox.critical(self, "Error", f"No se pudo eliminar:\n{e}")
        finally:
            session.close()

        self._reload_history()

    def _on_ver_detalle(self, modo_edicion: bool = False):
        row = self.tbl_hist.currentRow()
        if row < 0:
            return
        factura_id = self.tbl_hist.item(row, 0).data(Qt.ItemDataRole.UserRole)

        session = SessionLocal()
        try:
            factura = session.query(Factura).get(factura_id)
            if not factura:
                return
            # Cargar ítems antes de cerrar la sesión
            items_data = [
                {
                    "insumo": fi.insumo,
                    "cantidad": fi.cantidad,
                    "precio_unitario": fi.precio_unitario,
                    "aplica_iva": fi.aplica_iva,
                    "total": fi.total,
                }
                for fi in factura.items
            ]
            factura_data = {
                "id": factura.id,
                "numero_factura": factura.numero_factura,
                "fecha": factura.fecha,
                "proveedor": factura.proveedor,
            }
        finally:
            session.close()

        dlg = _FacturaDetailDialog(
            factura_data, items_data, modo_edicion=modo_edicion, parent=self
        )
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._reload_history()

    def get_total_compras(self) -> float:
        """Devuelve el total acumulado de compras de la ejecución activa."""
        session = SessionLocal()
        try:
            from sqlalchemy import func
            query = session.query(func.coalesce(func.sum(FacturaItem.total), 0.0))\
                           .join(Factura, FacturaItem.factura_id == Factura.id)
            if self._ejecucion_id is not None:
                query = query.filter(Factura.ejecucion_id == self._ejecucion_id)
            else:
                query = query.filter(Factura.ejecucion_id.is_(None))
            return float(query.scalar())
        except Exception:
            return 0.0
        finally:
            session.close()


# ──────────────────────────────────────────────────────────────────────────────
# Diálogo: Detalle / Edición de Factura
# ──────────────────────────────────────────────────────────────────────────────

class _FacturaDetailDialog(QDialog):
    def __init__(self, factura_data: dict, items_data: list[dict],
                 modo_edicion: bool = False, parent=None):
        super().__init__(parent)
        self._factura_data = factura_data
        self._items_data = items_data
        self._modo_edicion = modo_edicion
        titulo = (
            f"EDITAR FACTURA N° {factura_data['numero_factura']}"
            if modo_edicion
            else f"Detalle — Factura N° {factura_data['numero_factura']}"
        )
        self.setWindowTitle(titulo)
        self.resize(860, 560)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # Header
        hdr = QFrame()
        g = QGridLayout(hdr)

        if self._modo_edicion:
            g.addWidget(QLabel("N° FACTURA:"), 0, 0)
            self._le_num = QLineEdit(self._factura_data["numero_factura"])
            g.addWidget(self._le_num, 0, 1)

            g.addWidget(QLabel("FECHA:"), 0, 2)
            self._de_fecha = _make_date_edit()
            f = self._factura_data["fecha"]
            if f:
                self._de_fecha.setDate(QDate(f.year, f.month, f.day))
            g.addWidget(self._de_fecha, 0, 3)

            g.addWidget(QLabel("PROVEEDOR:"), 1, 0)
            self._le_prov = QLineEdit(self._factura_data["proveedor"])
            g.addWidget(self._le_prov, 1, 1, 1, 3)

            btn_save = QPushButton("💾 GUARDAR CAMBIOS")
            btn_save.setStyleSheet("background-color: #27ae60; color: white; padding: 6px;")
            btn_save.clicked.connect(self._on_save)
            g.addWidget(btn_save, 2, 3)
        else:
            lbl_title = QLabel(f"FACTURA N° {self._factura_data['numero_factura']}")
            lbl_title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
            g.addWidget(lbl_title, 0, 0, 2, 1)

            fecha_str = (
                self._factura_data["fecha"].strftime("%d/%m/%Y")
                if self._factura_data["fecha"]
                else ""
            )
            g.addWidget(QLabel(f"<b>FECHA:</b> {fecha_str}"), 0, 1,
                        alignment=Qt.AlignmentFlag.AlignRight)
            g.addWidget(
                QLabel(f"<b>PROVEEDOR:</b> {self._factura_data['proveedor']}"),
                1, 1, alignment=Qt.AlignmentFlag.AlignRight,
            )

        layout.addWidget(hdr)

        # Tabla de ítems
        tbl = QTableWidget(0, 6)
        tbl.setHorizontalHeaderLabels(
            ["Insumo", "Cant", "Vr. Unit", "IVA", "Subtotal", "Total Neto"]
        )
        tbl.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        tbl.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        tbl.setAlternatingRowColors(True)
        layout.addWidget(tbl)

        sum_sub = 0.0
        sum_iva = 0.0
        sum_total = 0.0
        for it in self._items_data:
            nombre = it["insumo"]
            cant = it["cantidad"]
            total_linea = it["total"]
            precio_unit = it["precio_unitario"]
            if it["aplica_iva"] or "(C/IVA)" in nombre.upper():
                base = total_linea / 1.19
                iva = total_linea - base
                txt_iva = "19%"
            else:
                base = total_linea
                iva = 0.0
                txt_iva = "0%"

            r = tbl.rowCount()
            tbl.insertRow(r)
            tbl.setItem(r, 0, _locked_item(nombre))
            tbl.setItem(r, 1, _locked_item(str(cant)))
            tbl.setItem(r, 2, _locked_item(_fmt(precio_unit)))
            tbl.setItem(r, 3, _locked_item(txt_iva))
            tbl.setItem(r, 4, _locked_item(_fmt(base)))
            tbl.setItem(r, 5, _locked_item(_fmt(total_linea)))
            sum_sub += base
            sum_iva += iva
            sum_total += total_linea

        # Totales
        f_tot = QFrame()
        tl = QGridLayout(f_tot)
        tl.addWidget(QLabel("SUBTOTAL:"), 0, 0, alignment=Qt.AlignmentFlag.AlignRight)
        tl.addWidget(QLabel(_fmt(sum_sub)), 0, 1)
        tl.addWidget(QLabel("IVA (19%):"), 1, 0, alignment=Qt.AlignmentFlag.AlignRight)
        tl.addWidget(QLabel(_fmt(sum_iva)), 1, 1)
        lbl_tot = QLabel("TOTAL A PAGAR:")
        lbl_tot.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        tl.addWidget(lbl_tot, 2, 0, alignment=Qt.AlignmentFlag.AlignRight)
        lbl_val = QLabel(_fmt(sum_total))
        lbl_val.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        lbl_val.setStyleSheet("color: #27ae60;")
        tl.addWidget(lbl_val, 2, 1)
        layout.addWidget(f_tot)

    def _on_save(self):
        nuevo_num = self._le_num.text().strip().upper()
        nuevo_prov = self._le_prov.text().strip().upper()
        if not nuevo_num or not nuevo_prov:
            QMessageBox.warning(self, "Error", "Número y proveedor no pueden estar vacíos.")
            return
        qd = self._de_fecha.date()
        nueva_fecha = date(qd.year(), qd.month(), qd.day())

        session = SessionLocal()
        try:
            factura = session.query(Factura).get(self._factura_data["id"])
            if factura:
                factura.numero_factura = nuevo_num
                factura.proveedor = nuevo_prov
                factura.fecha = nueva_fecha
                session.commit()
                QMessageBox.information(self, "Éxito", "Datos actualizados.")
                self.accept()
            else:
                QMessageBox.warning(self, "Error", "Factura no encontrada.")
        except Exception as e:
            session.rollback()
            QMessageBox.critical(self, "Error", f"No se pudo guardar:\n{e}")
        finally:
            session.close()


# ──────────────────────────────────────────────────────────────────────────────
# Sub-tab: Nómina
# ──────────────────────────────────────────────────────────────────────────────

class NominaWidget(QWidget):
    """Sub-pestaña de registro y consulta de pagos de nómina."""

    CARGOS = ["OFICIAL", "AYUDANTE", "MAESTRO", "CONTRATISTA", "RESIDENTE", "DIRECTOR"]
    MODALIDADES = ["POR DÍA (JORNAL)", "PRECIO GLOBAL / MENSUAL"]

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._ejecucion_id: int | None = None
        self._setup_ui()
        self._reload_history()
        self._reload_autocomplete()

    def set_ejecucion(self, ejecucion_id: int | None):
        """Cambia la ejecución activa y recarga los datos."""
        self._ejecucion_id = ejecucion_id
        self._reload_history()
        self._reload_autocomplete()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _setup_ui(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)

        # ── Panel izquierdo (formulario) ──────────────────────────────────────
        grp_form = QGroupBox("Registrar Pago")
        grp_form.setMaximumWidth(420)
        grp_form.setStyleSheet("QGroupBox { font-weight: bold; }")
        l_form = QVBoxLayout(grp_form)

        g = QGridLayout()

        g.addWidget(QLabel("Trabajador:"), 0, 0)
        self.cb_trabajador = QComboBox()
        self.cb_trabajador.setEditable(True)
        self.cb_trabajador.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        g.addWidget(self.cb_trabajador, 0, 1, 1, 3)

        g.addWidget(QLabel("Cargo:"), 1, 0)
        self.cb_cargo = QComboBox()
        self.cb_cargo.addItems(self.CARGOS)
        g.addWidget(self.cb_cargo, 1, 1, 1, 3)

        g.addWidget(QLabel("Modalidad:"), 2, 0)
        self.cb_modalidad = QComboBox()
        self.cb_modalidad.addItems(self.MODALIDADES)
        self.cb_modalidad.currentIndexChanged.connect(self._on_modalidad_changed)
        g.addWidget(self.cb_modalidad, 2, 1, 1, 3)

        g.addWidget(QLabel("Fecha:"), 3, 0)
        self.de_fecha = _make_date_edit()
        g.addWidget(self.de_fecha, 3, 1, 1, 3)

        self.lbl_dias = QLabel("Días Trab.:")
        g.addWidget(self.lbl_dias, 4, 0)
        self.le_dias = QLineEdit("1")
        g.addWidget(self.le_dias, 4, 1)

        self.lbl_valor = QLabel("Valor Día:")
        g.addWidget(self.lbl_valor, 4, 2)
        self.le_valor = QLineEdit("0")
        g.addWidget(self.le_valor, 4, 3)

        g.addWidget(QLabel("Observación:"), 5, 0)
        self.le_obs = QLineEdit()
        g.addWidget(self.le_obs, 5, 1, 1, 3)

        l_form.addLayout(g)
        l_form.addItem(QSpacerItem(0, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        btn_registrar = QPushButton("💾  REGISTRAR PAGO")
        btn_registrar.setStyleSheet(
            "background-color: #f39c12; color: white; padding: 10px; font-weight: bold; border-radius: 4px;"
        )
        btn_registrar.clicked.connect(self._on_guardar_pago)
        l_form.addWidget(btn_registrar)

        root.addWidget(grp_form)

        # ── Panel derecho (historial) ─────────────────────────────────────────
        grp_hist = QGroupBox("Historial de Pagos")
        grp_hist.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        l_hist = QVBoxLayout(grp_hist)

        f_btns = QHBoxLayout()
        btn_eliminar = QPushButton("🗑 Eliminar")
        btn_eliminar.setStyleSheet("color: #c0392b; font-weight: bold;")
        btn_eliminar.clicked.connect(self._on_eliminar_pago)
        f_btns.addStretch()
        f_btns.addWidget(btn_eliminar)
        l_hist.addLayout(f_btns)

        self.lbl_acumulado = QLabel("Acumulado Nómina: $ 0")
        self.lbl_acumulado.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.lbl_acumulado.setAlignment(Qt.AlignmentFlag.AlignRight)
        l_hist.addWidget(self.lbl_acumulado)

        self.tbl_hist = QTableWidget(0, 6)
        self.tbl_hist.setHorizontalHeaderLabels(
            ["Fecha", "Trabajador", "Cargo", "Modalidad", "Observación", "Pagado"]
        )
        self.tbl_hist.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tbl_hist.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tbl_hist.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tbl_hist.setAlternatingRowColors(True)
        l_hist.addWidget(self.tbl_hist)

        root.addWidget(grp_hist)

    # ── Lógica interna ────────────────────────────────────────────────────────

    def _reload_autocomplete(self):
        session = SessionLocal()
        try:
            trabajadores = sorted({
                p.trabajador for p in session.query(PagoNomina.trabajador).distinct()
                if p.trabajador
            })
        except Exception:
            trabajadores = []
        finally:
            session.close()

        self.cb_trabajador.clear()
        self.cb_trabajador.addItems(trabajadores)
        self.cb_trabajador.setCurrentText("")
        comp = QCompleter(trabajadores)
        comp.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        comp.setFilterMode(Qt.MatchFlag.MatchContains)
        self.cb_trabajador.setCompleter(comp)

    def _reload_history(self):
        session = SessionLocal()
        try:
            query = session.query(PagoNomina)
            if self._ejecucion_id is not None:
                query = query.filter(PagoNomina.ejecucion_id == self._ejecucion_id)
            else:
                query = query.filter(PagoNomina.ejecucion_id.is_(None))
            pagos = query.order_by(PagoNomina.fecha.desc()).all()
            self.tbl_hist.setRowCount(0)
            acumulado = 0.0
            for pago in pagos:
                row = self.tbl_hist.rowCount()
                self.tbl_hist.insertRow(row)
                fecha_str = pago.fecha.strftime("%d/%m/%Y") if pago.fecha else ""

                it_fecha = _locked_item(fecha_str)
                it_fecha.setData(Qt.ItemDataRole.UserRole, pago.id)
                self.tbl_hist.setItem(row, 0, it_fecha)
                self.tbl_hist.setItem(row, 1, _locked_item(pago.trabajador))
                self.tbl_hist.setItem(row, 2, _locked_item(pago.cargo))
                self.tbl_hist.setItem(row, 3, _locked_item(pago.modalidad))
                self.tbl_hist.setItem(row, 4, _locked_item(pago.observacion or ""))
                self.tbl_hist.setItem(row, 5, _locked_item(_fmt(pago.total)))
                acumulado += pago.total

            self.lbl_acumulado.setText(f"Acumulado Nómina: {_fmt(acumulado)}")
        except Exception as e:
            print("Error cargando historial nómina:", e)
        finally:
            session.close()

    # ── Slots ─────────────────────────────────────────────────────────────────

    def _on_modalidad_changed(self):
        jornal = self.cb_modalidad.currentIndex() == 0
        self.le_dias.setEnabled(jornal)
        if jornal:
            self.lbl_dias.setText("Días Trab.:")
            self.lbl_valor.setText("Valor Día:")
        else:
            self.le_dias.setText("1")
            self.lbl_dias.setText("Días (Fijo):")
            self.lbl_valor.setText("Valor Total:")

    def _on_guardar_pago(self):
        if self._ejecucion_id is None:
            QMessageBox.warning(self, "Sin ejecución",
                "Selecciona o crea una ejecución antes de registrar pagos.")
            return
        trabajador = self.cb_trabajador.currentText().strip().upper()
        cargo = self.cb_cargo.currentText().strip().upper()
        if not trabajador:
            QMessageBox.warning(self, "Error", "Ingrese el nombre del trabajador.")
            return
        try:
            valor = float(self.le_valor.text().replace(",", "."))
            dias = float(self.le_dias.text().replace(",", "."))
        except ValueError:
            QMessageBox.warning(self, "Error", "Días y valor deben ser numéricos.")
            return

        modalidad_idx = self.cb_modalidad.currentIndex()
        if modalidad_idx == 0:
            total = dias * valor
            modalidad = "JORNAL"
        else:
            total = valor
            dias = 1.0
            modalidad = "GLOBAL"

        qd = self.de_fecha.date()
        fecha_py = date(qd.year(), qd.month(), qd.day())
        observacion = self.le_obs.text().strip().upper()

        session = SessionLocal()
        try:
            pago = PagoNomina(
                fecha=fecha_py,
                trabajador=trabajador,
                cargo=cargo,
                modalidad=modalidad,
                dias=dias,
                valor=valor,
                total=total,
                observacion=observacion,
                ejecucion_id=self._ejecucion_id,
            )
            session.add(pago)
            session.commit()
            QMessageBox.information(self, "Guardado", "Pago registrado correctamente.")
        except Exception as e:
            session.rollback()
            QMessageBox.critical(self, "Error", f"No se pudo registrar el pago:\n{e}")
            return
        finally:
            session.close()

        # Limpiar
        self.cb_trabajador.setCurrentText("")
        self.le_valor.setText("0")
        self.le_obs.clear()
        if self.cb_modalidad.currentIndex() == 0:
            self.le_dias.setText("1")
        self._reload_history()
        self._reload_autocomplete()

    def _on_eliminar_pago(self):
        row = self.tbl_hist.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Aviso", "Selecciona un pago para eliminar.")
            return
        pago_id = self.tbl_hist.item(row, 0).data(Qt.ItemDataRole.UserRole)
        nombre = self.tbl_hist.item(row, 1).text()

        resp = QMessageBox.question(
            self, "Confirmar", f"¿Eliminar el pago de '{nombre}'?"
        )
        if resp != QMessageBox.StandardButton.Yes:
            return

        session = SessionLocal()
        try:
            pago = session.query(PagoNomina).get(pago_id)
            if pago:
                session.delete(pago)
                session.commit()
                QMessageBox.information(self, "Éxito", "Pago eliminado correctamente.")
            else:
                QMessageBox.warning(self, "Error", "Pago no encontrado.")
        except Exception as e:
            session.rollback()
            QMessageBox.critical(self, "Error", f"No se pudo eliminar:\n{e}")
        finally:
            session.close()

        self._reload_history()

    def get_total_nomina(self) -> float:
        """Devuelve el total acumulado de pagos de nómina de la ejecución activa."""
        session = SessionLocal()
        try:
            from sqlalchemy import func
            query = session.query(func.coalesce(func.sum(PagoNomina.total), 0.0))
            if self._ejecucion_id is not None:
                query = query.filter(PagoNomina.ejecucion_id == self._ejecucion_id)
            else:
                query = query.filter(PagoNomina.ejecucion_id.is_(None))
            return float(query.scalar())
        except Exception:
            return 0.0
        finally:
            session.close()


# ──────────────────────────────────────────────────────────────────────────────
# Vista principal de Ejecución
# ──────────────────────────────────────────────────────────────────────────────

_LIGHT_STYLE = """
/* ══════════════════════════════════════════════════════
   Modo claro forzado – EjecucionView
   (anula el tema oscuro del sistema operativo)
   ══════════════════════════════════════════════════════ */

/* ── Base ──────────────────────────────────────────── */
QWidget {
    background-color: #f5f6fa;
    color: #2c3e50;
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 13px;
}

/* ── Grupos ─────────────────────────────────────────── */
QGroupBox {
    background-color: #ffffff;
    border: 1px solid #d0d3d8;
    border-radius: 6px;
    margin-top: 14px;
    padding: 6px 4px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 6px;
    color: #2980b9;
    font-weight: bold;
    font-size: 13px;
}

/* ── Campos de entrada ──────────────────────────────── */
QLineEdit, QComboBox, QDateEdit {
    background-color: #ffffff;
    color: #2c3e50;
    border: 1px solid #bdc3c7;
    border-radius: 4px;
    padding: 5px 7px;
    selection-background-color: #3498db;
    selection-color: white;
}
QLineEdit:hover, QComboBox:hover {
    border-color: #85c1e9;
}
QLineEdit:focus, QComboBox:focus, QDateEdit:focus {
    border: 2px solid #3498db;
}
QLineEdit:read-only {
    background-color: #f8f9fa;
    color: #555;
}

/* ── ComboBox ───────────────────────────────────────── */
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: center right;
    width: 28px;
    border-left: 1px solid #bdc3c7;
    border-top-right-radius: 4px;
    border-bottom-right-radius: 4px;
    background-color: #3498db;
}
QComboBox::drop-down:hover {
    background-color: #2980b9;
}
QComboBox::drop-down:pressed {
    background-color: #1f6da8;
}
QComboBox::down-arrow {
    image: url(views/arrow_down_white.svg);
    width: 16px;
    height: 16px;
}
QComboBox QAbstractItemView {
    background-color: #ffffff;
    color: #2c3e50;
    border: 1px solid #bdc3c7;
    border-radius: 4px;
    padding: 2px;
    outline: none;
}
QComboBox QAbstractItemView::item {
    padding: 5px 10px;
    border-radius: 3px;
    min-height: 22px;
}
QComboBox QAbstractItemView::item:hover {
    background-color: #d6eaf8;
    color: #1a5276;
}
QComboBox QAbstractItemView::item:selected {
    background-color: #3498db;
    color: white;
}

/* ── Botones generales ──────────────────────────────── */
QPushButton {
    background-color: #ecf0f1;
    color: #2c3e50;
    border: 1px solid #bdc3c7;
    border-radius: 4px;
    padding: 5px 12px;
    font-weight: 600;
}
QPushButton:hover {
    background-color: #d6eaf8;
    border-color: #3498db;
    color: #1a5276;
}
QPushButton:pressed {
    background-color: #aed6f1;
    border-color: #2980b9;
}
QPushButton:disabled {
    background-color: #ecf0f1;
    color: #95a5a6;
    border-color: #d5d8dc;
}

/* ── Checkbox ───────────────────────────────────────── */
QCheckBox {
    color: #2c3e50;
    spacing: 6px;
}
QCheckBox:hover {
    color: #1a5276;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #bdc3c7;
    border-radius: 3px;
    background-color: #ffffff;
}
QCheckBox::indicator:hover {
    border-color: #3498db;
    background-color: #ebf5fb;
}
QCheckBox::indicator:checked {
    background-color: #3498db;
    border-color: #2980b9;
}
QCheckBox::indicator:checked:hover {
    background-color: #2980b9;
}

/* ── Tabla ──────────────────────────────────────────── */
QTableWidget {
    background-color: #ffffff;
    color: #2c3e50;
    alternate-background-color: #f0f6fb;
    gridline-color: #d0d3d8;
    selection-background-color: #3498db;
    selection-color: white;
    border: 1px solid #d0d3d8;
    border-radius: 4px;
}
QTableWidget::item {
    padding: 3px 6px;
}
QTableWidget::item:hover {
    background-color: #d6eaf8;
    color: #1a5276;
}
QTableWidget::item:selected {
    background-color: #3498db;
    color: white;
}
QHeaderView::section {
    background-color: #dce3ec;
    color: #2c3e50;
    padding: 6px 8px;
    border: none;
    border-right: 1px solid #c8cfd8;
    border-bottom: 1px solid #c8cfd8;
    font-weight: bold;
}
QHeaderView::section:hover {
    background-color: #c3d3e4;
}
QHeaderView::section:first {
    border-top-left-radius: 4px;
}
QHeaderView::section:last {
    border-right: none;
}

/* ── Pestañas ───────────────────────────────────────── */
QTabWidget::pane {
    border: 1px solid #d0d3d8;
    background-color: #ffffff;
    border-radius: 0px 4px 4px 4px;
}
QTabBar::tab {
    background-color: #dce3ec;
    color: #666;
    padding: 8px 18px;
    font-weight: bold;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    margin-right: 2px;
    border: 1px solid #c8cfd8;
    border-bottom: none;
}
QTabBar::tab:selected {
    background-color: #ffffff;
    color: #2980b9;
    border-bottom: 2px solid #ffffff;
}
QTabBar::tab:hover:!selected {
    background-color: #c3d3e4;
    color: #1a5276;
}

/* ── Scrollbar ──────────────────────────────────────── */
QScrollBar:vertical {
    background: #eaecee;
    width: 10px;
    border-radius: 5px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background: #aab7b8;
    border-radius: 5px;
    min-height: 24px;
}
QScrollBar::handle:vertical:hover {
    background: #3498db;
}
QScrollBar::handle:vertical:pressed {
    background: #2980b9;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
QScrollBar:horizontal {
    background: #eaecee;
    height: 10px;
    border-radius: 5px;
}
QScrollBar::handle:horizontal {
    background: #aab7b8;
    border-radius: 5px;
    min-width: 24px;
}
QScrollBar::handle:horizontal:hover {
    background: #3498db;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}
"""


class EjecucionView(QWidget):
    """Vista principal de Ejecución (Gastos) con sub-pestañas Compras y Nómina."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        _ensure_tables()
        # Forzar modo claro independientemente del tema del sistema
        self.setStyleSheet(_LIGHT_STYLE)
        self._setup_ui()
        self._reload_ejecuciones()

    # ── UI ─────────────────────────────────────────────────────────────────────
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Barra selectora de ejecución ─────────────────────────────────────
        selector_bar = QFrame()
        selector_bar.setFixedHeight(52)
        selector_bar.setStyleSheet(
            "background-color: #ecf0f1; border-bottom: 1px solid #bdc3c7; border-top: none;"
        )
        sb_lay = QHBoxLayout(selector_bar)
        sb_lay.setContentsMargins(14, 6, 14, 6)
        sb_lay.setSpacing(10)

        lbl_ejec = QLabel("📁  Ejecución activa:")
        lbl_ejec.setStyleSheet(
            "font-weight: bold; color: #2c3e50; font-size: 13px; background: transparent; border: none;"
        )
        sb_lay.addWidget(lbl_ejec)

        self.cb_ejecucion = QComboBox()
        self.cb_ejecucion.setFixedWidth(320)
        self.cb_ejecucion.setPlaceholderText("— Seleccionar ejecución —")
        self.cb_ejecucion.setStyleSheet(
            "QComboBox { background: white; color: #2c3e50; border: 1px solid #bdc3c7; "
            "border-radius: 4px; padding: 5px 10px; font-size: 13px; }"
            "QComboBox:hover { border-color: #3498db; }"
            "QComboBox::drop-down { border: none; width: 24px; background: #3498db; "
            "border-top-right-radius: 4px; border-bottom-right-radius: 4px; }"
            "QComboBox::down-arrow { image: url(views/arrow_down_white.svg); width:14px; height:14px; }"
        )
        self.cb_ejecucion.currentIndexChanged.connect(self._on_ejecucion_changed)
        sb_lay.addWidget(self.cb_ejecucion)

        btn_nueva = QPushButton("➕  Nueva Ejecución")
        btn_nueva.setFixedHeight(34)
        btn_nueva.setStyleSheet(
            "QPushButton { background-color: #27ae60; color: white; border-radius: 4px; "
            "font-weight: bold; font-size: 13px; padding: 0 16px; border: none; }"
            "QPushButton:hover { background-color: #1e8449; }"
            "QPushButton:pressed { background-color: #196f3d; }"
        )
        btn_nueva.clicked.connect(self._on_nueva_ejecucion)
        sb_lay.addWidget(btn_nueva)

        btn_eliminar_ejec = QPushButton("🗑  Eliminar")
        btn_eliminar_ejec.setFixedHeight(34)
        btn_eliminar_ejec.setStyleSheet(
            "QPushButton { background-color: #e74c3c; color: white; border-radius: 4px; "
            "font-weight: bold; font-size: 13px; padding: 0 14px; border: none; }"
            "QPushButton:hover { background-color: #c0392b; }"
            "QPushButton:pressed { background-color: #a93226; }"
        )
        btn_eliminar_ejec.clicked.connect(self._on_eliminar_ejecucion)
        sb_lay.addWidget(btn_eliminar_ejec)

        sb_lay.addStretch()
        layout.addWidget(selector_bar)

        # ── Banner de costo total ─────────────────────────────────────────────
        self.lbl_total = QLabel("COSTO TOTAL EJECUTADO: $ 0")
        self.lbl_total.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        self.lbl_total.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_total.setStyleSheet(
            "background-color: #2980b9; color: white; padding: 14px; border: none;"
        )
        layout.addWidget(self.lbl_total)

        # ── Sub-pestañas ──────────────────────────────────────────────────────
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        self.compras_widget = ComprasWidget()
        self.nomina_widget  = NominaWidget()

        self.tabs.addTab(self.compras_widget, "🧱 COMPRAS")
        self.tabs.addTab(self.nomina_widget,  "👷 NÓMINA")

        self.tabs.currentChanged.connect(self._actualizar_total)
        self._actualizar_total()

    # ── Gestión de ejecuciones ────────────────────────────────────────────────

    def _reload_ejecuciones(self):
        """Recarga el ComboBox con todas las ejecuciones existentes."""
        session = SessionLocal()
        try:
            ejecuciones = session.query(Ejecucion).order_by(Ejecucion.creado_en.desc()).all()
            self._ejecuciones_list: list[tuple[int, str]] = [
                (e.id, e.nombre) for e in ejecuciones
            ]
        except Exception as e:
            print("Error cargando ejecuciones:", e)
            self._ejecuciones_list = []
        finally:
            session.close()

        self.cb_ejecucion.blockSignals(True)
        self.cb_ejecucion.clear()
        for eid, nombre in self._ejecuciones_list:
            self.cb_ejecucion.addItem(nombre, userData=eid)
        self.cb_ejecucion.blockSignals(False)

        # Seleccionar la primera automáticamente si existe
        if self._ejecuciones_list:
            self.cb_ejecucion.setCurrentIndex(0)
            self._on_ejecucion_changed(0)
        else:
            self._set_ejecucion_activa(None)

    def _on_ejecucion_changed(self, index: int):
        if index < 0 or index >= len(self._ejecuciones_list):
            self._set_ejecucion_activa(None)
            return
        eid = self.cb_ejecucion.itemData(index)
        self._set_ejecucion_activa(eid)

    def _set_ejecucion_activa(self, ejecucion_id: int | None):
        self.compras_widget.set_ejecucion(ejecucion_id)
        self.nomina_widget.set_ejecucion(ejecucion_id)
        self._actualizar_total()

    def _on_nueva_ejecucion(self):
        from PyQt6.QtWidgets import QInputDialog
        nombre, ok = QInputDialog.getText(
            self, "Nueva Ejecución",
            "Nombre de la nueva ejecución\n(p.ej. «Obra Colegio 2025» o «Fase 1»):",
        )
        if not ok or not nombre.strip():
            return
        nombre = nombre.strip()

        session = SessionLocal()
        try:
            # Verificar que no exista
            existe = session.query(Ejecucion).filter(
                Ejecucion.nombre == nombre
            ).first()
            if existe:
                QMessageBox.warning(self, "Nombre duplicado",
                    f"Ya existe una ejecución llamada «{nombre}».")
                return
            nueva = Ejecucion(nombre=nombre)
            session.add(nueva)
            session.commit()
            nuevo_id = nueva.id
        except Exception as e:
            session.rollback()
            QMessageBox.critical(self, "Error", f"No se pudo crear la ejecución:\n{e}")
            return
        finally:
            session.close()

        self._reload_ejecuciones()
        # Seleccionar la recién creada
        for i, (eid, _) in enumerate(self._ejecuciones_list):
            if eid == nuevo_id:
                self.cb_ejecucion.setCurrentIndex(i)
                break

    def _on_eliminar_ejecucion(self):
        idx = self.cb_ejecucion.currentIndex()
        if idx < 0 or idx >= len(self._ejecuciones_list):
            QMessageBox.warning(self, "Sin selección",
                "Selecciona primero una ejecución para eliminar.")
            return
        eid, nombre = self._ejecuciones_list[idx]
        resp = QMessageBox.question(
            self, "Confirmar eliminación",
            f"¿Eliminar la ejecución «{nombre}» y TODOS sus registros\n"
            f"(facturas y pagos de nómina) asociados?\n\n"
            f"⚠️ Esta acción NO se puede deshacer.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if resp != QMessageBox.StandardButton.Yes:
            return

        session = SessionLocal()
        try:
            ejec = session.query(Ejecucion).get(eid)
            if ejec:
                session.delete(ejec)
                session.commit()
        except Exception as e:
            session.rollback()
            QMessageBox.critical(self, "Error", f"No se pudo eliminar:\n{e}")
            return
        finally:
            session.close()

        self._reload_ejecuciones()

    # ── Total banner ──────────────────────────────────────────────────────────
    def _actualizar_total(self):
        """Recalcula el banner de costo total (compras + nómina)."""
        try:
            total_c = self.compras_widget.get_total_compras()
            total_n = self.nomina_widget.get_total_nomina()
            gran_total = total_c + total_n
            self.lbl_total.setText(f"COSTO TOTAL EJECUTADO: {_fmt(gran_total)}")
        except Exception:
            pass

    def refresh(self):
        """Recarga todos los datos (útil cuando se activa la pestaña)."""
        self._reload_ejecuciones()
        self._actualizar_total()

