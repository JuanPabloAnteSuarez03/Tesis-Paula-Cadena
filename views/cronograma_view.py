"""
cronograma_view.py  –  CronogramaView para AppPresupuestos.

Extiende VisorProjectPro (cronograma_visor.py) añadiendo el botón
"📊 Insertar desde Presupuesto" que usa fuzzy matching para emparejar
las tareas del cronograma con los análisis unitarios del presupuesto activo.
"""
from __future__ import annotations

import difflib
import unicodedata

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QSlider, QCheckBox, QWidget, QMessageBox,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor

from views.cronograma_visor import VisorProjectPro


# ─── Helpers de fuzzy matching ────────────────────────────────────────────────

def _normalizar(texto: str) -> str:
    """Minúsculas + quitar tildes para comparación más tolerante."""
    t = texto.lower().strip()
    t = unicodedata.normalize("NFD", t)
    return "".join(c for c in t if unicodedata.category(c) != "Mn")


def _similitud(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, _normalizar(a), _normalizar(b)).ratio()


def _mejor_coincidencia(
    tarea: str,
    ppto_items: list[tuple],
    umbral: float = 0.45,
) -> tuple | None:
    """
    Devuelve (descripcion, cantidad, unidad, ratio) del ítem con mayor
    similitud si supera el umbral, o None.
    ppto_items: list of (descripcion, cantidad, unidad)
    """
    mejor = None
    mejor_ratio = umbral
    for desc, cant, und in ppto_items:
        r = _similitud(tarea, desc)
        if r > mejor_ratio:
            mejor_ratio = r
            mejor = (desc, cant, und, r)
    return mejor


# ─── Estilos del diálogo ──────────────────────────────────────────────────────

_DIALOG_STYLE = """
/* ── Raíz ── */
QDialog {
    background-color: #f5f6fa;
    color: #2c3e50;
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 13px;
}
/* ── Tabla ── */
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
QTableWidget::item { padding: 4px 6px; }
QTableWidget::item:hover {
    background-color: #d6eaf8;
    color: #1a5276;
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
QHeaderView::section:hover { background-color: #c3d3e4; }
/* ── Botones genéricos ── */
QPushButton {
    background-color: #ecf0f1;
    color: #2c3e50;
    border: 1px solid #bdc3c7;
    border-radius: 4px;
    padding: 6px 14px;
    font-weight: 600;
}
QPushButton:hover {
    background-color: #d6eaf8;
    border-color: #3498db;
    color: #1a5276;
}
QPushButton:pressed { background-color: #aed6f1; }
/* ── Slider ── */
QSlider::groove:horizontal {
    height: 6px;
    background: #dce3ec;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    background: #3498db;
    border: none;
    width: 16px;
    height: 16px;
    margin: -5px 0;
    border-radius: 8px;
}
QSlider::handle:horizontal:hover { background: #2980b9; }
QSlider::sub-page:horizontal {
    background: #3498db;
    border-radius: 3px;
}
/* ── CheckBox ── */
QCheckBox { color: #2c3e50; spacing: 5px; }
QCheckBox:hover { color: #1a5276; }
QCheckBox::indicator {
    width: 15px; height: 15px;
    border: 1px solid #bdc3c7;
    border-radius: 3px;
    background: white;
}
QCheckBox::indicator:hover { border-color: #3498db; background: #ebf5fb; }
QCheckBox::indicator:checked {
    background-color: #3498db;
    border-color: #2980b9;
    image: url("");          /* Qt pintará la marca automáticamente */
}
/* ── Labels ── */
QLabel { color: #2c3e50; }
"""


# ─── Diálogo de coincidencias ─────────────────────────────────────────────────

class _MatchDialog(QDialog):
    """
    Muestra una tabla con las mejores coincidencias fuzzy entre
    las tareas del cronograma y los análisis unitarios del presupuesto.
    """

    COL_APPLY  = 0
    COL_TAREA  = 1
    COL_MATCH  = 2
    COL_SIM    = 3
    COL_CANT   = 4
    COL_UNIDAD = 5

    def __init__(
        self,
        tasks: list[dict],
        ppto_items: list[tuple],
        parent=None,
    ):
        super().__init__(parent)
        self.setWindowTitle("📊 Insertar Cantidades desde Presupuesto")
        self.resize(1150, 640)
        self.setStyleSheet(_DIALOG_STYLE)

        self._tasks      = tasks        # solo tareas no-resumen
        self._ppto_items = ppto_items   # (desc, cant, unidad)
        self._umbral     = 0.45

        self._build_ui()
        self._recalculate()

    # ── Construcción de UI ────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(10)

        # Info
        lbl_info = QLabel(
            "Se busca la mejor coincidencia entre el <b>nombre de cada tarea</b> del "
            "cronograma y los <b>análisis unitarios del presupuesto</b>.<br>"
            "Activa las filas que deseas aplicar, ajusta el umbral de similitud y confirma."
        )
        lbl_info.setWordWrap(True)
        lbl_info.setStyleSheet("color: #555; padding: 4px 0;")
        root.addWidget(lbl_info)

        # Fila de umbral
        thr_row = QHBoxLayout()
        thr_row.setSpacing(8)

        lbl_thr = QLabel("Umbral de similitud:")
        lbl_thr.setFixedWidth(155)

        self._slider = QSlider(Qt.Orientation.Horizontal)
        self._slider.setRange(10, 95)
        self._slider.setValue(int(self._umbral * 100))
        self._slider.setFixedWidth(240)
        self._slider.setTickInterval(5)
        self._slider.setCursor(Qt.CursorShape.PointingHandCursor)

        self._lbl_pct = QLabel(f"{int(self._umbral * 100)}%")
        self._lbl_pct.setStyleSheet("font-weight: bold; color: #2980b9; min-width: 42px;")

        self._lbl_found = QLabel("")
        self._lbl_found.setStyleSheet("color: #27ae60; font-weight: bold;")

        self._slider.valueChanged.connect(self._on_threshold_changed)

        thr_row.addWidget(lbl_thr)
        thr_row.addWidget(self._slider)
        thr_row.addWidget(self._lbl_pct)
        thr_row.addSpacing(24)
        thr_row.addWidget(self._lbl_found)
        thr_row.addStretch()
        root.addLayout(thr_row)

        # Tabla
        self._table = QTableWidget(0, 6)
        self._table.setHorizontalHeaderLabels([
            "Aplicar",
            "Tarea del Cronograma",
            "Mejor Coincidencia en Presupuesto",
            "Similitud",
            "Cantidad",
            "Unidad",
        ])
        hdr = self._table.horizontalHeader()
        hdr.setSectionResizeMode(self.COL_APPLY,  QHeaderView.ResizeMode.Fixed)
        hdr.setSectionResizeMode(self.COL_TAREA,  QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(self.COL_MATCH,  QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(self.COL_SIM,    QHeaderView.ResizeMode.Fixed)
        hdr.setSectionResizeMode(self.COL_CANT,   QHeaderView.ResizeMode.Fixed)
        hdr.setSectionResizeMode(self.COL_UNIDAD, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(self.COL_APPLY,  68)
        self._table.setColumnWidth(self.COL_SIM,    80)
        self._table.setColumnWidth(self.COL_CANT,   110)
        self._table.setColumnWidth(self.COL_UNIDAD, 80)
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        self._table.setShowGrid(True)
        root.addWidget(self._table)

        # Fila de botones
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        btn_all = QPushButton("✔ Seleccionar todas")
        btn_none = QPushButton("✖ Deseleccionar todas")
        btn_all.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_none.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_all.clicked.connect(self._select_all)
        btn_none.clicked.connect(self._select_none)

        self._btn_apply = QPushButton("⬇  Aplicar seleccionadas")
        self._btn_apply.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_apply.setStyleSheet(
            "QPushButton { background-color: #27ae60; color: white; "
            "font-weight: bold; padding: 8px 20px; border-radius: 4px; border: none; }"
            "QPushButton:hover { background-color: #219a52; }"
            "QPushButton:pressed { background-color: #1a7a40; }"
        )
        self._btn_apply.clicked.connect(self.accept)

        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancel.clicked.connect(self.reject)

        btn_row.addWidget(btn_all)
        btn_row.addWidget(btn_none)
        btn_row.addStretch()
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(self._btn_apply)
        root.addLayout(btn_row)

    # ── Lógica ────────────────────────────────────────────────────────────────

    def _on_threshold_changed(self, value: int) -> None:
        self._umbral = value / 100.0
        self._lbl_pct.setText(f"{value}%")
        self._recalculate()

    def _recalculate(self) -> None:
        """Recalcula coincidencias con el umbral actual y refresca la tabla."""
        self._table.setRowCount(0)
        count = 0

        for t in self._tasks:
            match = _mejor_coincidencia(t["name"], self._ppto_items, self._umbral)
            if match is None:
                continue

            desc_match, cant, und, ratio = match
            row = self._table.rowCount()
            self._table.insertRow(row)

            # Col 0: checkbox centrado
            chk = QCheckBox()
            chk.setChecked(True)
            chk.setCursor(Qt.CursorShape.PointingHandCursor)
            container = QWidget()
            lay = QHBoxLayout(container)
            lay.addWidget(chk)
            lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lay.setContentsMargins(0, 0, 0, 0)
            container.setProperty("_chk", chk)
            self._table.setCellWidget(row, self.COL_APPLY, container)

            # Col 1: nombre tarea (guarda task index en UserRole)
            it_tarea = QTableWidgetItem(t["name"])
            it_tarea.setData(Qt.ItemDataRole.UserRole, t["index"])
            self._table.setItem(row, self.COL_TAREA, it_tarea)

            # Col 2: mejor coincidencia
            self._table.setItem(row, self.COL_MATCH, QTableWidgetItem(desc_match))

            # Col 3: similitud con color
            pct = int(ratio * 100)
            it_sim = QTableWidgetItem(f"{pct}%")
            it_sim.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if pct >= 80:
                it_sim.setForeground(QColor("#27ae60"))
                it_sim.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            elif pct >= 60:
                it_sim.setForeground(QColor("#f39c12"))
            else:
                it_sim.setForeground(QColor("#e74c3c"))
            self._table.setItem(row, self.COL_SIM, it_sim)

            # Col 4: cantidad
            try:
                cant_fmt = f"{float(cant):,.2f}"
            except (TypeError, ValueError):
                cant_fmt = str(cant)
            it_cant = QTableWidgetItem(cant_fmt)
            it_cant.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            self._table.setItem(row, self.COL_CANT, it_cant)

            # Col 5: unidad
            it_und = QTableWidgetItem(str(und or ""))
            it_und.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._table.setItem(row, self.COL_UNIDAD, it_und)

            count += 1

        self._lbl_found.setText(f"✓ {count} coincidencia(s) encontrada(s)")
        self._btn_apply.setText(f"⬇  Aplicar seleccionadas ({count})")

    def _select_all(self) -> None:
        for row in range(self._table.rowCount()):
            w = self._table.cellWidget(row, self.COL_APPLY)
            if w:
                chk = w.property("_chk")
                if chk:
                    chk.setChecked(True)

    def _select_none(self) -> None:
        for row in range(self._table.rowCount()):
            w = self._table.cellWidget(row, self.COL_APPLY)
            if w:
                chk = w.property("_chk")
                if chk:
                    chk.setChecked(False)

    def get_selected_matches(self) -> list[tuple[int, float]]:
        """
        Retorna lista de (task_index, cantidad) para las filas seleccionadas.
        """
        result = []
        for row in range(self._table.rowCount()):
            w = self._table.cellWidget(row, self.COL_APPLY)
            if not w:
                continue
            chk = w.property("_chk")
            if not chk or not chk.isChecked():
                continue
            task_idx = self._table.item(row, self.COL_TAREA).data(
                Qt.ItemDataRole.UserRole
            )
            cant_txt = (
                self._table.item(row, self.COL_CANT)
                .text()
                .replace(",", "")
                .strip()
            )
            try:
                cant = float(cant_txt)
            except ValueError:
                cant = 0.0
            result.append((task_idx, cant))
        return result


# ─── Vista principal del Cronograma ──────────────────────────────────────────

class CronogramaView(VisorProjectPro):
    """
    Extiende VisorProjectPro añadiendo el botón
    '📊 Insertar desde Presupuesto' con fuzzy matching.

    Parameters
    ----------
    presupuesto_view : PresupuestoView | None
        Referencia a la vista de presupuesto activa.  Si se provee, los
        ítems se leen directamente de su QTableWidget en memoria (fuente
        de verdad principal del módulo Presupuesto).  Si es None se intenta
        la BD como respaldo.
    """

    def __init__(self, presupuesto_view=None) -> None:
        super().__init__()
        self._presupuesto_view = presupuesto_view  # referencia a PresupuestoView

        # Botón extra
        self.btn_desde_ppto = QPushButton("📊 Insertar desde Presupuesto")
        self.btn_desde_ppto.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_desde_ppto.setStyleSheet(
            "QPushButton { color: white; border: none; padding: 6px 15px; "
            "font-weight: bold; border-radius: 3px; font-size: 13px; "
            "background-color: #8e44ad; }"
            "QPushButton:hover { background-color: #7d3c98; }"
            "QPushButton:pressed { background-color: #6c3483; }"
            "QPushButton:disabled { background-color: #CCCCCC; color: #666666; }"
        )
        self.btn_desde_ppto.setEnabled(False)
        self.btn_desde_ppto.clicked.connect(self._abrir_dialogo_presupuesto)

        # Insertar antes del stretch (último elemento del toolbar_layout)
        n = self.toolbar_layout.count()
        self.toolbar_layout.insertWidget(n - 1, self.btn_desde_ppto)

    # ── Override para activar también el nuevo botón ──────────────────────────

    def activar_ingreso_cantidades(self) -> None:
        super().activar_ingreso_cantidades()
        self.btn_desde_ppto.setEnabled(True)

    def limpiar_cronograma(self) -> None:
        """Extiende limpiar_cronograma para también resetear el botón extra."""
        super().limpiar_cronograma()
        self.btn_desde_ppto.setEnabled(False)

    # ── Lógica de búsqueda en presupuesto ─────────────────────────────────────

    def _leer_ppto_desde_tabla(self) -> list[tuple]:
        """
        Lee los ítems de análisis directamente del QTableWidget de PresupuestoView.
        Devuelve lista de (descripcion, cantidad, unidad).
        Solo incluye filas que sean análisis reales (no capítulos ni subtotales).
        """
        if self._presupuesto_view is None:
            return []

        try:
            table = self._presupuesto_view.table
        except AttributeError:
            return []

        items: list[tuple] = []
        for row in range(table.rowCount()):
            item0 = table.item(row, 0)
            if not item0:
                continue
            role = item0.data(Qt.ItemDataRole.UserRole)
            # Capítulos y subtotales tienen role == 'chapter' / 'subtotal'
            # Las filas de análisis tienen role == código del análisis (str distinto)
            if role in ("chapter", "subtotal", None, ""):
                continue

            desc_item = table.item(row, 1)
            und_item  = table.item(row, 2)
            cant_item = table.item(row, 3)

            desc = desc_item.text().strip() if desc_item else ""
            if not desc:
                continue

            und = und_item.text().strip() if und_item else ""
            try:
                cant_txt = cant_item.text().replace(",", "").replace("$", "") if cant_item else "0"
                cant = float(cant_txt)
            except (ValueError, AttributeError):
                cant = 0.0

            items.append((desc, cant, und))

        return items

    def _leer_ppto_desde_bd(self) -> list[tuple]:
        """Respaldo: leer desde presupuestos_analisis_unitarios en la BD."""
        try:
            from models.database import SessionLocal
            from models.presupuesto_analisis_unitario import PresupuestoAnalisisUnitario

            session = SessionLocal()
            try:
                rows = session.query(PresupuestoAnalisisUnitario).all()
                return [
                    (r.descripcion_analisis, r.cantidad_analisis, r.unidad_analisis)
                    for r in rows
                ]
            finally:
                session.close()
        except Exception:
            return []

    def _abrir_dialogo_presupuesto(self) -> None:
        if not self.tasks:
            QMessageBox.information(
                self, "Sin tareas",
                "Primero importa un cronograma XML con '📂 Importar Cronograma'."
            )
            return

        # 1. Leer desde el QTableWidget (fuente principal)
        ppto_items = self._leer_ppto_desde_tabla()

        # 2. Si el widget no está disponible, caer a la BD
        if not ppto_items:
            ppto_items = self._leer_ppto_desde_bd()

        if not ppto_items:
            QMessageBox.information(
                self, "Sin datos",
                "No se encontraron ítems en el presupuesto activo.\n"
                "Asegúrate de haber cargado y guardado análisis unitarios en la pestaña 'Presupuesto'."
            )
            return

        # Solo tareas de detalle (no resúmenes ni tareas de nivel 1 como "FIN")
        non_summary = [t for t in self.tasks if not t["summary"] and t["indent"] > 1]
        if not non_summary:
            QMessageBox.information(
                self, "Sin tareas detalle",
                "El cronograma no tiene tareas de detalle (solo capítulos resumidos)."
            )
            return

        # Mostrar diálogo
        dlg = _MatchDialog(non_summary, ppto_items, parent=self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        matches = dlg.get_selected_matches()
        if not matches:
            QMessageBox.information(
                self, "Sin selección",
                "No se seleccionó ninguna coincidencia para aplicar."
            )
            return

        for task_idx, cantidad in matches:
            self.tasks[task_idx]["cantidad_obra"] = cantidad

        # ── Forzar visualización en modo "Cant. Plan" ──────────────────────
        # Problema: después de "Resetear Corte", modo_linea_base queda True y
        # toma prioridad en el elif chain de llenar_tabla/configurar_tabla_columnas,
        # mostrando columnas de duración en vez de cantidad_obra.
        # Solución: si no estamos en modo corte activo, asegurar que se muestre
        # la columna de cantidades temporalmente sin destruir los datos de la
        # línea base (bl_start, bl_finish, bl_duration permanecen intactos).
        if not self.modo_corte:
            _prev_lb = self.modo_linea_base
            self.modo_linea_base = False      # ocultar prioridad linea_base
            self.modo_ingreso_cantidades = True
            self.configurar_tabla_columnas()
            self.llenar_tabla()
            self.modo_linea_base = _prev_lb   # restaurar para el Gantt y próximas acciones
        else:
            self.llenar_tabla()

        QMessageBox.information(
            self, "✅ Listo",
            f"Se asignaron cantidades a {len(matches)} tarea(s).\n"
            "Puedes editarlas manualmente en la columna 'Cant. Plan'."
        )

