"""
cronograma_visor.py  –  VisorProjectPro adaptado para AppPresupuestos.

Igual que OBJETIVO 2/visor_2.py pero expone self.toolbar_layout para que
subclases puedan añadir botones extra al toolbar sin duplicar código.
"""
import sys
import math
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (QApplication, QMainWindow, QSplitter, QTreeWidget,
                             QTreeWidgetItem, QVBoxLayout, QWidget, QGraphicsView,
                             QGraphicsScene, QGraphicsRectItem, QGraphicsTextItem,
                             QPushButton, QFileDialog, QHeaderView, QMessageBox,
                             QFrame, QGraphicsLineItem, QAbstractItemView, QSizePolicy,
                             QGraphicsPathItem, QHBoxLayout, QTreeWidgetItemIterator,
                             QDialog, QTableWidget, QTableWidgetItem, QLabel, QDateEdit,
                             QDialogButtonBox, QStyledItemDelegate, QGridLayout,
                             QGraphicsDropShadowEffect, QStyle, QStyleOptionHeader,
                             QProgressBar, QScrollArea)
from PyQt6.QtCore import Qt, QPointF, QSize, QDate, QRectF
from PyQt6.QtGui import QColor, QBrush, QPen, QFont, QPainter, QPainterPath, QPolygonF, QLinearGradient

# =============================================================================
# 1. CLASE PARA ENCABEZADOS (Ajuste de texto)
# =============================================================================
class HeaderWordWrap(QHeaderView):
    def __init__(self, parent=None):
        super().__init__(Qt.Orientation.Horizontal, parent)
        self.setStretchLastSection(False)
        self.setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)

    def paintSection(self, painter, rect, logicalIndex):
        painter.save()
        opt = QStyleOptionHeader()
        self.initStyleOption(opt)
        opt.rect = rect
        opt.section = logicalIndex
        self.style().drawControl(QStyle.ControlElement.CE_HeaderSection, opt, painter, self)

        text = self.model().headerData(logicalIndex, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole)
        margin = 4
        text_rect = rect.adjusted(margin, margin, -margin, -margin)

        painter.setPen(QColor("#000000"))
        flags = int(Qt.AlignmentFlag.AlignCenter) | int(Qt.TextFlag.TextWordWrap)
        painter.drawText(text_rect, flags, text)
        painter.restore()

# =============================================================================
# 2. DELEGATE (Bloqueo de edición)
# =============================================================================
class BloqueoDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.columnas_editables = []

    def set_columnas_editables(self, columnas):
        self.columnas_editables = columnas

    def createEditor(self, parent, option, index):
        if index.column() in self.columnas_editables:
            return super().createEditor(parent, option, index)
        return None

# =============================================================================
# 3. MOTOR MATEMÁTICO DE FECHAS
# =============================================================================
def es_dia_laborable(fecha, festivos):
    if fecha.weekday() == 6: return False
    if fecha.date() in festivos: return False
    return True

def sumar_dias_habiles(fecha_inicio, dias, festivos):
    if dias < 1: dias = 1
    dias_a_sumar = dias - 1
    fecha = fecha_inicio
    while not es_dia_laborable(fecha, festivos):
        fecha += timedelta(days=1)
    contador = 0
    while contador < dias_a_sumar:
        fecha += timedelta(days=1)
        if es_dia_laborable(fecha, festivos):
            contador += 1
    while not es_dia_laborable(fecha, festivos):
        fecha += timedelta(days=1)
    return fecha

def siguiente_dia_habil(fecha, festivos):
    nueva = fecha + timedelta(days=1)
    while not es_dia_laborable(nueva, festivos):
        nueva += timedelta(days=1)
    return nueva

def calcular_duracion_habiles(inicio, fin, festivos):
    if inicio > fin: return 0
    dias = 0
    curr = inicio
    while curr <= fin:
        if es_dia_laborable(curr, festivos):
            dias += 1
        curr += timedelta(days=1)
    return dias if dias > 0 else 1

# =============================================================================
# 4. WIDGETS AUXILIARES (ESTILO DASHBOARD)
# =============================================================================
class PieChartWidget(QWidget):
    def __init__(self, atrasadas, en_tiempo, parent=None):
        super().__init__(parent)
        self.atrasadas = atrasadas
        self.en_tiempo = en_tiempo
        self.setMinimumSize(220, 220)
        self.setStyleSheet("background-color: transparent;")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect()
        size = min(rect.width() * 0.6, rect.height()) - 10
        if size < 50: size = 50

        pie_rect = QRectF(10, (rect.height() - size) / 2, size, size)

        total = self.atrasadas + self.en_tiempo
        if total == 0: return

        angle_atraso = int((self.atrasadas / total) * 360 * 16)
        angle_ok = 360 * 16 - angle_atraso

        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(QColor("#E0E0E0"), 2))
        painter.drawEllipse(pie_rect.adjusted(-2, -2, 2, 2))

        color_atraso = QColor("#E74C3C")
        color_ok = QColor("#2ECC71")

        painter.setPen(Qt.PenStyle.NoPen)

        if self.atrasadas > 0:
            painter.setBrush(QBrush(color_atraso))
            painter.drawPie(pie_rect, 90 * 16, -angle_atraso)

        if self.en_tiempo > 0:
            painter.setBrush(QBrush(color_ok))
            painter.drawPie(pie_rect, 90 * 16 - angle_atraso, -angle_ok)

        hole_size = size * 0.5
        hole_rect = QRectF(pie_rect.center().x() - hole_size / 2,
                           pie_rect.center().y() - hole_size / 2,
                           hole_size, hole_size)
        painter.setBrush(QBrush(QColor("white")))
        painter.drawEllipse(hole_rect)

        painter.setPen(QColor("#2C3E50"))
        font = QFont("Segoe UI", 12, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(hole_rect, Qt.AlignmentFlag.AlignCenter, f"Total\n{total}")

        legend_x = pie_rect.right() + 20
        legend_y = pie_rect.top() + 20

        painter.setBrush(QBrush(color_ok))
        painter.drawEllipse(QRectF(legend_x, legend_y, 12, 12))
        painter.drawText(QRectF(legend_x + 20, legend_y - 2, 100, 20), "Al día")

        legend_y += 30
        painter.setBrush(QBrush(color_atraso))
        painter.drawEllipse(QRectF(legend_x, legend_y, 12, 12))
        painter.drawText(QRectF(legend_x + 20, legend_y - 2, 100, 20), "Retrasadas")


class KPICard(QFrame):
    def __init__(self, titulo, valor, color_texto, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 12px;
                border: 1px solid #E5E7EB;
            }
        """)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 30))
        self.setGraphicsEffect(shadow)

        self.setFixedSize(200, 110)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(5)

        lbl_tit = QLabel(titulo.upper())
        lbl_tit.setStyleSheet("color: #7F8C8D; font-size: 11px; font-weight: bold; border: none; letter-spacing: 1px;")

        lbl_val = QLabel(valor)
        lbl_val.setStyleSheet(f"color: {color_texto}; font-size: 28px; font-weight: 800; border: none; font-family: 'Segoe UI';")

        layout.addWidget(lbl_tit)
        layout.addWidget(lbl_val)

# =============================================================================
# 5. VENTANA REPORTE
# =============================================================================
class VentanaReporte(QDialog):
    def __init__(self, parent, tasks, fecha_corte_qdate, festivos):
        super().__init__(parent)
        self.setWindowTitle(f"Tablero de Control — Corte al {fecha_corte_qdate.toString('dd/MM/yyyy')}")
        self.resize(1200, 1000)
        self.setStyleSheet("background-color: #F0F4F8;")

        self.tasks    = tasks
        self.festivos = festivos
        self.fecha_corte = datetime.combine(fecha_corte_qdate.toPyDate(), datetime.min.time())

        # ── Layout raíz ──────────────────────────────────────────────────────
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── HEADER BANNER ────────────────────────────────────────────────────
        header = QFrame()
        header.setFixedHeight(72)
        header.setStyleSheet(
            "background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            "stop:0 #1a3c6e, stop:1 #2980b9);"
            "border: none;"
        )
        h_lay = QHBoxLayout(header)
        h_lay.setContentsMargins(28, 0, 28, 0)

        ico_lbl = QLabel("📊")
        ico_lbl.setStyleSheet("font-size: 28px; background: transparent; border: none;")
        h_lay.addWidget(ico_lbl)

        title_block = QVBoxLayout(); title_block.setSpacing(2)
        lbl_main_title = QLabel("TABLERO DE CONTROL")
        lbl_main_title.setStyleSheet(
            "color: white; font-family: 'Segoe UI'; font-size: 18px; "
            "font-weight: bold; background: transparent; border: none; letter-spacing: 1px;"
        )
        lbl_sub_title = QLabel(f"Corte de obra al  {fecha_corte_qdate.toString('dd / MM / yyyy')}")
        lbl_sub_title.setStyleSheet(
            "color: rgba(255,255,255,0.75); font-family: 'Segoe UI'; "
            "font-size: 12px; background: transparent; border: none;"
        )
        title_block.addWidget(lbl_main_title)
        title_block.addWidget(lbl_sub_title)
        h_lay.addLayout(title_block)
        h_lay.addStretch()
        root.addWidget(header)

        # ── BODY (con scroll) ────────────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent; border: none;")
        body_widget = QWidget()
        body_widget.setStyleSheet("background: transparent;")
        body = QVBoxLayout(body_widget)
        body.setContentsMargins(28, 24, 28, 24)
        body.setSpacing(20)
        scroll.setWidget(body_widget)
        root.addWidget(scroll, 1)

        # ── CALCULAR MÉTRICAS ────────────────────────────────────────────────
        total_tasks = 0; atrasadas = 0; en_tiempo = 0
        sum_pct_fisico = 0.0; sum_pct_esperado = 0.0; count_metrics = 0
        data_rows = []

        for t in self.tasks:
            if t['summary']: continue
            total_tasks += 1
            dur_base = calcular_duracion_habiles(t['bl_start'], t['bl_finish'], self.festivos)
            if self.fecha_corte < t['bl_start']:    dias_plan = 0
            elif self.fecha_corte >= t['bl_finish']: dias_plan = dur_base
            else: dias_plan = calcular_duracion_habiles(t['bl_start'], self.fecha_corte, self.festivos)

            pct_plan_tiempo = (dias_plan / dur_base) if dur_base > 0 else 0.0
            try:
                c_plan = float(t['cantidad_obra']); c_real = float(t['cantidad_real'])
                pct_fisico = (c_real / c_plan) if c_plan > 0 else 0.0
            except:
                c_plan = 0.0; c_real = 0.0; pct_fisico = 0.0

            diff = pct_fisico - pct_plan_tiempo
            estado = "EN TIEMPO"
            if diff < -0.05:
                estado = "RETRASADA"; atrasadas += 1
            else:
                en_tiempo += 1

            if c_plan > 0:
                sum_pct_fisico   += pct_fisico
                sum_pct_esperado += pct_plan_tiempo
                count_metrics    += 1

            data_rows.append({
                "name": t['name'], "c_plan": c_plan, "c_real": c_real,
                "pct_fis": pct_fisico, "pct_plan": pct_plan_tiempo,
                "start": t['bl_start'], "end": t['bl_finish'], "status": estado
            })

        avg_fisico   = (sum_pct_fisico   / count_metrics * 100) if count_metrics > 0 else 0
        avg_esperado = (sum_pct_esperado / count_metrics * 100) if count_metrics > 0 else 0
        pct_ok  = (en_tiempo / total_tasks * 100) if total_tasks > 0 else 0

        # ── FILA KPI (4 tarjetas) ────────────────────────────────────────────
        kpi_row = QHBoxLayout(); kpi_row.setSpacing(16)

        def make_kpi(icon, label, value_str, sub_str, color_top, pct=None):
            """Tarjeta KPI moderna: top-bar de color, icono, valor grande, barra opcional."""
            card = QFrame()
            card.setStyleSheet(
                "QFrame { background-color: white; border-radius: 14px; border: 1px solid #E2E8F0; }"
            )
            sh = QGraphicsDropShadowEffect(card)
            sh.setBlurRadius(18); sh.setXOffset(0); sh.setYOffset(5)
            sh.setColor(QColor(0, 0, 0, 25)); card.setGraphicsEffect(sh)

            card_v = QVBoxLayout(card); card_v.setContentsMargins(0, 0, 0, 16); card_v.setSpacing(0)

            # top color bar
            top_bar = QFrame(); top_bar.setFixedHeight(6)
            top_bar.setStyleSheet(f"background-color: {color_top}; border-top-left-radius: 14px; border-top-right-radius: 14px; border: none;")
            card_v.addWidget(top_bar)

            inner = QVBoxLayout(); inner.setContentsMargins(18, 14, 18, 0); inner.setSpacing(4)

            row_icon = QHBoxLayout()
            lbl_ico = QLabel(icon)
            lbl_ico.setStyleSheet(f"font-size: 22px; color: {color_top}; background: transparent; border: none;")
            row_icon.addWidget(lbl_ico); row_icon.addStretch()
            inner.addLayout(row_icon)

            lbl_v = QLabel(value_str)
            lbl_v.setStyleSheet(
                f"color: {color_top}; font-family: 'Segoe UI'; font-size: 32px; "
                "font-weight: 800; background: transparent; border: none;"
            )
            inner.addWidget(lbl_v)

            lbl_lbl = QLabel(label)
            lbl_lbl.setStyleSheet(
                "color: #64748B; font-family: 'Segoe UI'; font-size: 11px; "
                "font-weight: 600; letter-spacing: 0.8px; background: transparent; border: none;"
            )
            lbl_lbl.setWordWrap(True)
            inner.addWidget(lbl_lbl)

            if sub_str:
                lbl_sub = QLabel(sub_str)
                lbl_sub.setStyleSheet(
                    "color: #94A3B8; font-family: 'Segoe UI'; font-size: 10px; "
                    "background: transparent; border: none;"
                )
                inner.addWidget(lbl_sub)

            if pct is not None:
                bar = QProgressBar()
                bar.setRange(0, 100); bar.setValue(int(pct))
                bar.setFixedHeight(6); bar.setTextVisible(False)
                bar.setStyleSheet(
                    f"QProgressBar {{ background: #E2E8F0; border-radius: 3px; border: none; }}"
                    f"QProgressBar::chunk {{ background: {color_top}; border-radius: 3px; }}"
                )
                inner.addSpacing(8)
                inner.addWidget(bar)

            card_v.addLayout(inner)
            return card

        kpi_row.addWidget(make_kpi("📈", "AVANCE FÍSICO REAL",   f"{avg_fisico:.1f}%",   "Progreso acumulado",  "#2980B9", avg_fisico))
        kpi_row.addWidget(make_kpi("🎯", "AVANCE ESPERADO",      f"{avg_esperado:.1f}%", "Según línea base",    "#8E44AD", avg_esperado))
        kpi_row.addWidget(make_kpi("✅", "ACTIVIDADES AL DÍA",   str(en_tiempo),         f"{pct_ok:.0f}% del total",  "#27AE60"))
        kpi_row.addWidget(make_kpi("⚠️", "ACTIVIDADES RETRASADAS", str(atrasadas),       f"{total_tasks} tareas totales", "#E74C3C"))
        body.addLayout(kpi_row)

        # ── SEGUNDA FILA: Gráfico circular ───────────────────────────────────
        chart_row = QHBoxLayout(); chart_row.setSpacing(16)

        chart_card = QFrame()
        chart_card.setStyleSheet("QFrame { background: white; border-radius: 14px; border: 1px solid #E2E8F0; }")
        sh_c = QGraphicsDropShadowEffect(chart_card); sh_c.setBlurRadius(18); sh_c.setXOffset(0)
        sh_c.setYOffset(5); sh_c.setColor(QColor(0, 0, 0, 25)); chart_card.setGraphicsEffect(sh_c)
        chart_card.setFixedHeight(200)

        cc_lay = QVBoxLayout(chart_card); cc_lay.setContentsMargins(18, 16, 18, 16)
        lbl_chart_title = QLabel("Distribución de Estado")
        lbl_chart_title.setStyleSheet(
            "color: #1E293B; font-family: 'Segoe UI'; font-size: 13px; "
            "font-weight: bold; background: transparent; border: none;"
        )
        cc_lay.addWidget(lbl_chart_title)
        pie = PieChartWidget(atrasadas, en_tiempo)
        pie.setFixedSize(300, 140)
        cc_lay.addWidget(pie, 0, Qt.AlignmentFlag.AlignCenter)
        chart_row.addWidget(chart_card)
        chart_row.addStretch()
        body.addLayout(chart_row)

        # ── SECCIÓN TABLA ────────────────────────────────────────────────────
        lbl_det = QLabel("Detalle de Ejecución")
        lbl_det.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        lbl_det.setStyleSheet("color: #1E293B; margin-top: 4px; background: transparent; border: none;")
        body.addWidget(lbl_det)

        self.tabla = QTableWidget()
        self.tabla.setColumnCount(8)
        self.tabla.setHorizontalHeaderLabels(
            ["Actividad", "Cant. Plan", "Cant. Ejec", "% Real", "% Esperado", "Diferencia", "Estado", "Fin Base"]
        )
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.setShowGrid(False)
        self.tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: 1px solid #E2E8F0;
                border-radius: 12px;
                font-family: 'Segoe UI';
                font-size: 13px;
                gridline-color: transparent;
                selection-background-color: #DBEAFE;
                selection-color: #1E293B;
                alternate-background-color: #F8FAFC;
            }
            QTableWidget::item {
                padding: 7px 10px;
                border-bottom: 1px solid #F1F5F9;
                color: #1E293B;
            }
            QTableWidget::item:hover   { background-color: #EFF6FF; }
            QTableWidget::item:selected { background-color: #DBEAFE; color: #1E293B; }
            QHeaderView::section {
                background-color: #1E3A5F;
                color: white;
                padding: 10px 8px;
                border: none;
                font-weight: bold;
                font-size: 12px;
                letter-spacing: 0.5px;
            }
            QHeaderView::section:first { border-top-left-radius: 12px; }
            QHeaderView::section:last  { border-top-right-radius: 12px; }
            QHeaderView::section:hover { background-color: #2C4E7A; }
            QScrollBar:vertical {
                background: #F1F5F9; width: 8px; border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #CBD5E1; border-radius: 4px; min-height: 20px;
            }
            QScrollBar::handle:vertical:hover { background: #94A3B8; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
        """)
        self.tabla.setColumnWidth(0, 320)
        self.tabla.setColumnWidth(1, 90); self.tabla.setColumnWidth(2, 90)
        self.tabla.setColumnWidth(3, 80); self.tabla.setColumnWidth(4, 90)
        self.tabla.setColumnWidth(5, 90)
        self.tabla.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)
        self.tabla.setColumnWidth(7, 90)
        self.tabla.setMinimumHeight(280)

        font_bold = QFont("Segoe UI", 9, QFont.Weight.Bold)

        for d in data_rows:
            row = self.tabla.rowCount(); self.tabla.insertRow(row)
            self.tabla.setRowHeight(row, 36)

            item_name = QTableWidgetItem(d['name'])
            item_name.setForeground(QColor("#1E293B"))
            self.tabla.setItem(row, 0, item_name)

            for col, txt in [(1, str(d['c_plan'])), (2, str(d['c_real']))]:
                it = QTableWidgetItem(txt)
                it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                it.setForeground(QColor("#475569"))
                self.tabla.setItem(row, col, it)

            item_real = QTableWidgetItem(f"{d['pct_fis'] * 100:.1f}%")
            item_real.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if d['pct_fis'] >= 1.0:
                item_real.setForeground(QColor("#16A34A")); item_real.setFont(font_bold)
            else:
                item_real.setForeground(QColor("#475569"))
            self.tabla.setItem(row, 3, item_real)

            item_exp = QTableWidgetItem(f"{d['pct_plan'] * 100:.1f}%")
            item_exp.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_exp.setForeground(QColor("#475569"))
            self.tabla.setItem(row, 4, item_exp)

            diff = (d['pct_fis'] - d['pct_plan']) * 100
            item_diff = QTableWidgetItem(f"{diff:+.1f}%")
            item_diff.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if diff < -5:
                item_diff.setForeground(QColor("#DC2626")); item_diff.setFont(font_bold)
            elif diff >= 0:
                item_diff.setForeground(QColor("#16A34A")); item_diff.setFont(font_bold)
            else:
                item_diff.setForeground(QColor("#D97706"))
            self.tabla.setItem(row, 5, item_diff)

            # Badge de estado
            if d['status'] == "RETRASADA":
                badge_bg = QColor("#FEE2E2"); badge_fg = QColor("#DC2626"); badge_txt = "⛔ RETRASADA"
            else:
                badge_bg = QColor("#DCFCE7"); badge_fg = QColor("#16A34A"); badge_txt = "✅ EN TIEMPO"
            item_st = QTableWidgetItem(badge_txt)
            item_st.setBackground(badge_bg); item_st.setForeground(badge_fg)
            item_st.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_st.setFont(font_bold)
            self.tabla.setItem(row, 6, item_st)

            item_end = QTableWidgetItem(d['end'].strftime("%d/%m/%y"))
            item_end.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_end.setForeground(QColor("#64748B"))
            self.tabla.setItem(row, 7, item_end)

        body.addWidget(self.tabla)

        # ── BOTÓN CERRAR ─────────────────────────────────────────────────────
        btns_layout = QHBoxLayout(); btns_layout.addStretch()
        btn_close = QPushButton("  Cerrar  ")
        btn_close.setFixedHeight(38)
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.setStyleSheet("""
            QPushButton {
                background-color: #64748B; color: white;
                border-radius: 8px; font-family: 'Segoe UI';
                font-size: 13px; font-weight: bold;
                padding: 0 24px; border: none;
            }
            QPushButton:hover   { background-color: #475569; }
            QPushButton:pressed { background-color: #334155; }
        """)
        btn_close.clicked.connect(self.close)
        btns_layout.addWidget(btn_close)
        body.addLayout(btns_layout)

# =============================================================================
# 6. VISOR PRINCIPAL
# =============================================================================
class VisorProjectPro(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Visor Project - Profesional")
        self.resize(1500, 800)

        self.color_fondo = "#FFFFFF"; self.color_header = "#F0F0F0"; self.color_texto_header = "#333333"
        self.color_barra_normal = "#0078D7"; self.color_barra_critica = "#E81123"
        self.color_barra_base = "#999999"; self.color_barra_resumen = "#222222"; self.color_flecha = "#555555"

        self.alto_fila = 30; self.ancho_dia = 24; self.alto_encabezado = 45

        self.tasks = []; self.uid_map = {}; self.wbs_map = {}
        self.festivos_set = set()

        self.modo_ingreso_cantidades = False
        self.modo_linea_base = False
        self.modo_corte = False

        self.scrolling = False; self.fecha_linea_corte = None

        self.init_ui()

    def init_ui(self):
        main = QWidget(); self.setCentralWidget(main)
        main.setStyleSheet(f"background-color: {self.color_fondo}; color: black; font-family: 'Segoe UI', sans-serif;")
        layout = QVBoxLayout(main); layout.setContentsMargins(0, 0, 0, 0); layout.setSpacing(0)

        # TOOLBAR
        toolbar = QFrame(); toolbar.setFixedHeight(50)
        toolbar.setStyleSheet("background-color: #F8F8F8; border-bottom: 1px solid #DDD; padding: 5px;")
        tb_layout = QHBoxLayout(toolbar); tb_layout.setContentsMargins(10, 5, 10, 5); tb_layout.setSpacing(10)

        style_btn = (
            "QPushButton { color: white; border: none; padding: 6px 15px; font-weight: bold; "
            "border-radius: 3px; font-size: 13px; }"
            "QPushButton:hover { filter: brightness(1.15); }"
            "QPushButton:disabled { background-color: #CCCCCC; color: #666666; }"
        )

        btn_load = QPushButton("📂 Importar Cronograma")
        btn_load.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_load.setStyleSheet(
            "QPushButton { color: white; border: none; padding: 6px 15px; font-weight: bold; border-radius: 3px; font-size: 13px; background-color: #107C41; }"
            "QPushButton:hover { background-color: #0D6835; }"
            "QPushButton:disabled { background-color: #CCCCCC; color: #666666; }"
        )
        btn_load.clicked.connect(self.cargar_archivo)
        tb_layout.addWidget(btn_load)

        self.btn_cant = QPushButton("📝 Insertar Cantidades")
        self.btn_cant.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cant.setStyleSheet(
            "QPushButton { color: white; border: none; padding: 6px 15px; font-weight: bold; border-radius: 3px; font-size: 13px; background-color: #00BFA5; }"
            "QPushButton:hover { background-color: #009688; }"
            "QPushButton:disabled { background-color: #CCCCCC; color: #666666; }"
        )
        self.btn_cant.clicked.connect(self.activar_ingreso_cantidades)
        self.btn_cant.setEnabled(False)
        tb_layout.addWidget(self.btn_cant)

        self.btn_base = QPushButton("📐 Línea Base Activa" if False else "📐 Crear Línea Base")
        self.btn_base.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_base.setStyleSheet(
            "QPushButton { color: white; border: none; padding: 6px 15px; font-weight: bold; border-radius: 3px; font-size: 13px; background-color: #0078D7; }"
            "QPushButton:hover { background-color: #005A9E; }"
            "QPushButton:disabled { background-color: #CCCCCC; color: #666666; }"
        )
        self.btn_base.clicked.connect(self.activar_linea_base)
        self.btn_base.setEnabled(False)
        tb_layout.addWidget(self.btn_base)

        self.btn_corte = QPushButton("✂️ Corte de Obra")
        self.btn_corte.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_corte.setStyleSheet(
            "QPushButton { color: white; border: none; padding: 6px 15px; font-weight: bold; border-radius: 3px; font-size: 13px; background-color: #FF8F00; }"
            "QPushButton:hover { background-color: #E65100; }"
            "QPushButton:disabled { background-color: #CCCCCC; color: #666666; }"
        )
        self.btn_corte.clicked.connect(self.proceso_corte_obra)
        self.btn_corte.setEnabled(False)
        tb_layout.addWidget(self.btn_corte)

        self.btn_reporte = QPushButton("📊 Tablero de Control")
        self.btn_reporte.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_reporte.setStyleSheet(
            "QPushButton { color: white; border: none; padding: 6px 15px; font-weight: bold; border-radius: 3px; font-size: 13px; background-color: #6200EA; }"
            "QPushButton:hover { background-color: #4A148C; }"
            "QPushButton:disabled { background-color: #CCCCCC; color: #666666; }"
        )
        self.btn_reporte.clicked.connect(self.proceso_reporte)
        self.btn_reporte.setEnabled(False)
        tb_layout.addWidget(self.btn_reporte)

        self.btn_reset = QPushButton("🔄 Resetear Corte")
        self.btn_reset.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_reset.setStyleSheet(
            "QPushButton { color: white; border: none; padding: 6px 15px; font-weight: bold; border-radius: 3px; font-size: 13px; background-color: #546E7A; }"
            "QPushButton:hover { background-color: #37474F; }"
            "QPushButton:disabled { background-color: #CCCCCC; color: #666666; }"
        )
        self.btn_reset.clicked.connect(self.resetear_corte)
        self.btn_reset.setEnabled(False)
        tb_layout.addWidget(self.btn_reset)

        self.btn_limpiar = QPushButton("🗑 Limpiar")
        self.btn_limpiar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_limpiar.setStyleSheet(
            "QPushButton { color: white; border: none; padding: 6px 15px; font-weight: bold; border-radius: 3px; font-size: 13px; background-color: #c0392b; }"
            "QPushButton:hover { background-color: #a93226; }"
            "QPushButton:pressed { background-color: #922b21; }"
            "QPushButton:disabled { background-color: #CCCCCC; color: #666666; }"
        )
        self.btn_limpiar.setToolTip("Eliminar el cronograma importado y volver al estado inicial")
        self.btn_limpiar.clicked.connect(self.limpiar_cronograma)
        self.btn_limpiar.setEnabled(False)
        tb_layout.addWidget(self.btn_limpiar)

        tb_layout.addStretch()

        # ── Exponer el toolbar layout para subclases ──────────────────────────
        self.toolbar_layout = tb_layout

        layout.addWidget(toolbar)

        splitter = QSplitter(Qt.Orientation.Horizontal); splitter.setHandleWidth(1)
        splitter.setStyleSheet("QSplitter::handle { background-color: #CCC; }")

        self.tree = QTreeWidget()
        header_personalizado = HeaderWordWrap(self.tree)
        header_personalizado.setMinimumSectionSize(30)
        header_personalizado.setDefaultSectionSize(50)
        self.tree.setHeader(header_personalizado)

        self.delegate = BloqueoDelegate(self.tree)
        self.tree.setItemDelegate(self.delegate)
        self.configurar_tabla_columnas()

        self.tree.setStyleSheet(
            f"QTreeWidget {{ border: none; font-size: 13px; gridline-color: #F0F0F0; "
            f"background-color: #FFFFFF; color: #000000; }}"
            f"QTreeWidget::item {{ border-bottom: 1px solid #F0F0F0; padding-left: 5px; color: #000000; }}"
            f"QTreeWidget::item:hover {{ background-color: #EBF5FB; color: #000000; }}"
            f"QTreeWidget::item:selected {{ background-color: #D6EAF8; color: #000000; }}"
            f"QHeaderView::section {{ background-color: {self.color_header}; color: #000000; "
            f"border: 1px solid #DDD; height: {self.alto_encabezado}px; font-weight: bold; }}"
            f"QHeaderView::section:hover {{ background-color: #D5D8DC; }}"
        )
        self.tree.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.tree.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.tree.itemChanged.connect(self.al_editar_celda)
        splitter.addWidget(self.tree)

        self.scene = QGraphicsScene(); self.scene.setBackgroundBrush(QBrush(QColor("white")))
        self.view = QGraphicsView(self.scene)
        self.view.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.view.setStyleSheet("border: none; border-left: 1px solid #DDD; background-color: white;")
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        splitter.addWidget(self.view)

        splitter.setSizes([850, 650])
        layout.addWidget(splitter, 1)
        self.view.verticalScrollBar().valueChanged.connect(self.sync_scroll_from_view)
        self.tree.verticalScrollBar().valueChanged.connect(self.sync_scroll_from_tree)

    def solicitar_fecha(self, titulo_ventana):
        d = QDialog(self)
        d.setWindowTitle(titulo_ventana)
        d.setFixedSize(300, 150)
        d.setStyleSheet("""
            QDialog { background-color: #f5f6fa; }
            QLabel  { color: #2c3e50; }
            QDateEdit {
                background: white; border: 1px solid #bdc3c7;
                border-radius: 4px; padding: 5px; color: #2c3e50;
            }
            QDateEdit:hover { border-color: #3498db; }
            QPushButton {
                background-color: #3498db; color: white;
                border: none; padding: 6px 14px;
                border-radius: 4px; font-weight: bold;
            }
            QPushButton:hover    { background-color: #2980b9; }
            QPushButton:pressed  { background-color: #1f6da8; }

            /* ── Calendario popup ── */
            QCalendarWidget { background-color: #ffffff; }

            QCalendarWidget QWidget#qt_calendar_navigationbar {
                background-color: #2980b9;
                padding: 4px 2px;
            }
            QCalendarWidget QToolButton {
                color: white; background-color: transparent;
                border: none; border-radius: 4px;
                padding: 4px 10px; font-weight: bold; font-size: 13px;
                min-width: 28px;
            }
            QCalendarWidget QToolButton:hover    { background-color: rgba(255,255,255,0.25); }
            QCalendarWidget QToolButton:pressed  { background-color: rgba(255,255,255,0.45); }
            QCalendarWidget QToolButton::menu-indicator { image: none; }

            QCalendarWidget QSpinBox {
                background-color: #ffffff; color: #2c3e50;
                border: 1px solid #bdc3c7; border-radius: 3px; padding: 2px 4px;
            }
            QCalendarWidget QSpinBox::up-button,
            QCalendarWidget QSpinBox::down-button  { background-color: #dce3ec; border: none; }
            QCalendarWidget QSpinBox::up-button:hover,
            QCalendarWidget QSpinBox::down-button:hover { background-color: #3498db; }

            QCalendarWidget QMenu {
                background-color: #ffffff; color: #2c3e50;
                border: 1px solid #bdc3c7; border-radius: 4px; padding: 4px 0px;
            }
            QCalendarWidget QMenu::item         { padding: 5px 18px; border-radius: 3px; }
            QCalendarWidget QMenu::item:selected { background-color: #3498db; color: white; }
            QCalendarWidget QMenu::item:hover    { background-color: #ebf5fb; color: #2980b9; }

            QCalendarWidget QWidget           { alternate-background-color: #f0f6fc; }
            QCalendarWidget QAbstractItemView {
                background-color: #ffffff; color: #2c3e50;
                selection-background-color: #3498db; selection-color: white; outline: none;
            }
            QCalendarWidget QAbstractItemView:enabled  { color: #2c3e50; }
            QCalendarWidget QAbstractItemView:disabled { color: #b0bec5; }
            QCalendarWidget QAbstractItemView::item:hover {
                background-color: #d6eaf8; color: #1a5276; border-radius: 3px;
            }
            QCalendarWidget QAbstractItemView::item:selected {
                background-color: #3498db; color: white;
                border-radius: 3px; font-weight: bold;
            }
        """)
        l = QVBoxLayout(d)
        lbl = QLabel("Selecciona la Fecha:")
        lbl.setFont(QFont("Segoe UI", 10))
        l.addWidget(lbl)
        date_edit = QDateEdit()
        date_edit.setCalendarPopup(True); date_edit.setDate(QDate.currentDate())
        date_edit.setFont(QFont("Segoe UI", 11))
        l.addWidget(date_edit)
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(d.accept); btns.rejected.connect(d.reject)
        l.addWidget(btns)
        if d.exec(): return date_edit.date()
        return None

    def activar_ingreso_cantidades(self):
        if not self.tasks: return
        self.modo_ingreso_cantidades = True
        self.alto_fila = 30
        self.configurar_tabla_columnas()
        self.llenar_tabla()
        self.btn_cant.setEnabled(False)
        self.btn_base.setEnabled(True)

    def activar_linea_base(self):
        if not self.tasks: return
        reply = QMessageBox.question(self, "Crear Línea Base",
                                     "Se guardará el estado actual (Fechas y Cantidades Planificadas) como Línea Base.\n¿Continuar?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.modo_linea_base = True
            self.alto_fila = 50
            for t in self.tasks:
                t['bl_start'] = t['start']; t['bl_finish'] = t['finish']; t['bl_duration'] = t['duration']

            self.configurar_tabla_columnas()
            self.llenar_tabla()
            self.dibujar_gantt()

            self.btn_cant.setEnabled(False)
            self.btn_base.setEnabled(False); self.btn_base.setText("Línea Base Activa")
            self.btn_corte.setEnabled(True)
            self.btn_reporte.setEnabled(True)

    def proceso_corte_obra(self):
        fecha_q = self.solicitar_fecha("Establecer Corte de Obra")
        if not fecha_q: return
        self.fecha_linea_corte = fecha_q
        self.dibujar_gantt()
        if not self.modo_corte:
            self.modo_corte = True
            self.configurar_tabla_columnas()
            self.llenar_tabla()
            self.btn_corte.setEnabled(False)
            self.btn_corte.setText(f"Corte Activo: {fecha_q.toString('dd/MM/yy')}")
            self.btn_reset.setEnabled(True)

    def resetear_corte(self):
        reply = QMessageBox.question(self, "Resetear Corte",
                                     "Esto borrará el avance ingresado y la fecha de corte actual.\n¿Volver a la Línea Base?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.modo_corte = False
            self.fecha_linea_corte = None

            for t in self.tasks:
                t['cantidad_real'] = 0
                t['start'] = t['bl_start']
                t['finish'] = t['bl_finish']
                t['duration'] = t['bl_duration']

            self.configurar_tabla_columnas()
            self.llenar_tabla()
            self.dibujar_gantt()

            self.btn_corte.setEnabled(True)
            self.btn_corte.setText("✂️ Corte de Obra")
            self.btn_reset.setEnabled(False)

    def limpiar_cronograma(self):
        """Elimina el cronograma importado y devuelve la vista al estado inicial."""
        if not self.tasks:
            return
        reply = QMessageBox.question(
            self, "Limpiar Cronograma",
            "¿Eliminar el cronograma importado?\n"
            "Se perderán todas las cantidades, la línea base y el corte actual.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        # Resetear datos
        self.tasks = []
        self.uid_map = {}
        self.wbs_map = {}
        self.fecha_linea_corte = None

        # Resetear modos
        self.modo_ingreso_cantidades = False
        self.modo_linea_base = False
        self.modo_corte = False
        self.alto_fila = 30

        # Limpiar árbol y Gantt
        self.tree.blockSignals(True)
        self.tree.clear()
        self.tree.blockSignals(False)
        try:
            self.scene.clear()
        except Exception:
            pass

        # Restaurar columnas por defecto
        self.configurar_tabla_columnas()

        # Restaurar estado de botones al estado inicial (sin archivo)
        self.btn_cant.setEnabled(False)
        self.btn_cant.setText("📝 Insertar Cantidades")
        self.btn_base.setEnabled(False)
        self.btn_base.setText("📐 Crear Línea Base")
        self.btn_corte.setEnabled(False)
        self.btn_corte.setText("✂️ Corte de Obra")
        self.btn_reporte.setEnabled(False)
        self.btn_reset.setEnabled(False)
        self.btn_limpiar.setEnabled(False)

    def proceso_reporte(self):
        if not self.modo_linea_base: return
        if self.fecha_linea_corte:
            fecha_uso = self.fecha_linea_corte
        else:
            fecha_uso = self.solicitar_fecha("Fecha de Reporte")
            if not fecha_uso: return
            self.fecha_linea_corte = fecha_uso
            self.dibujar_gantt()

        reporte = VentanaReporte(self, self.tasks, fecha_uso, self.festivos_set)
        reporte.exec()

    def sync_scroll_from_view(self, val):
        if self.scrolling: return
        self.scrolling = True; self.tree.verticalScrollBar().setValue(val); self.scrolling = False

    def sync_scroll_from_tree(self, val):
        if self.scrolling: return
        self.scrolling = True; self.view.verticalScrollBar().setValue(val); self.scrolling = False

    def configurar_tabla_columnas(self):
        self.tree.blockSignals(True)
        header = self.tree.header()

        if not isinstance(header, HeaderWordWrap):
            header = HeaderWordWrap(self.tree)
            header.setMinimumSectionSize(30)
            header.setDefaultSectionSize(50)
            self.tree.setHeader(header)

        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)

        if self.modo_corte:
            self.tree.setColumnCount(9)
            self.tree.setHeaderLabels(["ID", "Nombre", "Cant. Plan", "Base (d)", "% Esp.", "Cant. Ejec.", "% Real", "Inicio", "Fin"])
            self.tree.setColumnWidth(0, 80); self.tree.setColumnWidth(1, 300)
            self.tree.setColumnWidth(2, 70); self.tree.setColumnWidth(3, 60)
            self.tree.setColumnWidth(4, 55)
            self.tree.setColumnWidth(5, 70); self.tree.setColumnWidth(6, 60)
            self.tree.setColumnWidth(7, 70); self.tree.setColumnWidth(8, 70)
            self.delegate.set_columnas_editables([5])

        elif self.modo_linea_base:
            self.tree.setColumnCount(6)
            self.tree.setHeaderLabels(["ID", "Nombre de Tarea", "Duración\nLínea Base", "Duración\nReal", "Inicio", "Fin"])
            self.tree.setColumnWidth(0, 80); self.tree.setColumnWidth(1, 300)
            self.tree.setColumnWidth(2, 80); self.tree.setColumnWidth(3, 80)
            self.tree.setColumnWidth(4, 80); self.tree.setColumnWidth(5, 80)
            self.delegate.set_columnas_editables([3])

        elif self.modo_ingreso_cantidades:
            self.tree.setColumnCount(7)
            self.tree.setHeaderLabels(["ID", "Nombre de Tarea", "Cant. Plan", "Duración", "Inicio", "Fin", "Predecesoras"])
            self.tree.setColumnWidth(0, 80); self.tree.setColumnWidth(1, 300)
            self.tree.setColumnWidth(2, 80)
            self.tree.setColumnWidth(3, 70); self.tree.setColumnWidth(4, 80)
            self.tree.setColumnWidth(5, 80); self.tree.setColumnWidth(6, 90)
            self.delegate.set_columnas_editables([2])

        else:
            self.tree.setColumnCount(6)
            self.tree.setHeaderLabels(["ID", "Nombre de Tarea", "Duración", "Inicio", "Fin", "Predecesoras"])
            self.tree.setColumnWidth(0, 80); self.tree.setColumnWidth(1, 300)
            self.tree.setColumnWidth(2, 70); self.tree.setColumnWidth(3, 80)
            self.tree.setColumnWidth(4, 80); self.tree.setColumnWidth(5, 90)
            self.delegate.set_columnas_editables([])
        self.tree.blockSignals(False)

    def cargar_archivo(self):
        ruta, _ = QFileDialog.getOpenFileName(self, "Abrir XML", "", "XML Files (*.xml)")
        if not ruta: return
        self.modo_ingreso_cantidades = False
        self.modo_linea_base = False; self.modo_corte = False; self.alto_fila = 30
        self.fecha_linea_corte = None
        self.configurar_tabla_columnas()

        self.btn_cant.setEnabled(True); self.btn_cant.setText("📝 Insertar Cantidades")
        self.btn_base.setEnabled(False); self.btn_base.setText("📐 Crear Línea Base")
        self.btn_corte.setEnabled(False); self.btn_corte.setText("✂️ Corte de Obra")
        self.btn_reporte.setEnabled(False)
        self.btn_reset.setEnabled(False)
        self.btn_limpiar.setEnabled(True)

        self.parsear_xml(ruta); self.llenar_tabla(); self.dibujar_gantt()

    def parsear_xml(self, ruta):
        self.tasks = []; self.uid_map = {}; self.wbs_map = {}
        self.festivos_set = set()
        try:
            tree = ET.parse(ruta); root = tree.getroot()
            ns = "{http://schemas.microsoft.com/project}"

            calendarios = root.findall(".//Calendar") or root.findall(f".//{ns}Calendar")
            if calendarios:
                cal = calendarios[0]
                excepciones = cal.findall(".//Exception") or cal.findall(f".//{ns}Exception")
                for ex in excepciones:
                    try:
                        time_period = ex.find(".//TimePeriod") or ex.find(f".//{ns}TimePeriod")
                        if time_period is not None:
                            from_date_s = time_period.findtext("FromDate") or time_period.findtext(f".//{ns}FromDate")
                            to_date_s = time_period.findtext("ToDate") or time_period.findtext(f".//{ns}ToDate")
                            if from_date_s and to_date_s:
                                f_ini = datetime.strptime(from_date_s.split('T')[0], "%Y-%m-%d").date()
                                f_fin = datetime.strptime(to_date_s.split('T')[0], "%Y-%m-%d").date()
                                curr = f_ini
                                while curr <= f_fin:
                                    self.festivos_set.add(curr)
                                    curr += timedelta(days=1)
                    except: pass

            items = root.findall(".//Task") or root.findall(f".//{ns}Task")
            for i, t in enumerate(items):
                uid = t.findtext("UID") or t.findtext(f".//{ns}UID")
                if uid: self.uid_map[uid] = -1

            idx_counter = 0
            for t in items:
                uid = t.findtext("UID") or t.findtext(f".//{ns}UID")
                name = t.findtext("Name") or t.findtext(f".//{ns}Name")
                if not name: continue

                outline = t.findtext("OutlineLevel") or t.findtext(f".//{ns}OutlineLevel")
                try: indent = int(outline)
                except: indent = 1

                wbs = t.findtext("WBS") or t.findtext(f".//{ns}WBS") or str(idx_counter + 1)
                self.wbs_map[uid] = wbs

                start_s = t.findtext("Start") or t.findtext(f".//{ns}Start")
                finish_s = t.findtext("Finish") or t.findtext(f".//{ns}Finish")
                if not start_s or not finish_s: continue

                f_inicio = datetime.strptime(start_s.split('T')[0], "%Y-%m-%d")
                f_fin = datetime.strptime(finish_s.split('T')[0], "%Y-%m-%d")

                duracion_dias = calcular_duracion_habiles(f_inicio, f_fin, self.festivos_set)

                summary = (t.findtext("Summary") == "1") or (t.findtext(f".//{ns}Summary") == "1")
                critical = (t.findtext("Critical") == "1") or (t.findtext(f".//{ns}Critical") == "1")

                preds = []
                links = t.findall(".//PredecessorLink") or t.findall(f".//{ns}PredecessorLink")
                for link in links:
                    p_uid = link.findtext("PredecessorUID") or link.findtext(f".//{ns}PredecessorUID")
                    if p_uid: preds.append(p_uid)

                self.tasks.append({
                    'index': idx_counter, 'uid': uid, 'id_visual': wbs, 'name': name, 'indent': indent,
                    'start': f_inicio, 'finish': f_fin, 'duration': duracion_dias,
                    'xml_start': f_inicio,
                    'xml_finish': f_fin,
                    'bl_start': f_inicio, 'bl_finish': f_fin, 'bl_duration': duracion_dias,
                    'summary': summary, 'critical': critical, 'predecessors': preds,
                    'cantidad_obra': 0, 'cantidad_real': 0
                })
                if uid: self.uid_map[uid] = idx_counter
                idx_counter += 1
        except Exception as e: print(f"Error XML: {e}")

    def llenar_tabla(self):
        self.scrolling = True
        self.tree.blockSignals(True)
        self.tree.clear()

        font_reg = QFont("Segoe UI", 9)
        font_bold = QFont("Segoe UI", 9, QFont.Weight.Bold)
        size_hint = QSize(0, self.alto_fila)
        f_fmt = "%d/%m/%y"

        for t in self.tasks:
            item = QTreeWidgetItem(self.tree)
            item.setData(0, Qt.ItemDataRole.UserRole, t['index'])
            item.setSizeHint(0, size_hint)

            prefix = "    " * (t['indent'] - 1)
            item.setText(0, str(t['id_visual']))
            item.setText(1, prefix + t['name'])

            if self.modo_corte:
                c_plan_txt = str(t['cantidad_obra']) if not t['summary'] else ""
                item.setText(2, c_plan_txt)
                item.setBackground(2, QBrush(QColor("#EEEEEE")))
                item.setText(3, f"{t['bl_duration']} d")

                pct_esp = 0.0
                fecha_corte_dt = datetime.combine(self.fecha_linea_corte.toPyDate(), datetime.min.time())

                if fecha_corte_dt < t['start']: pct_esp = 0.0
                elif fecha_corte_dt >= t['finish']: pct_esp = 100.0
                else:
                    dias_pasados = calcular_duracion_habiles(t['start'], fecha_corte_dt, self.festivos_set)
                    if t['duration'] > 0: pct_esp = (dias_pasados / t['duration']) * 100
                    else: pct_esp = 100.0 if fecha_corte_dt >= t['start'] else 0.0

                item.setText(4, f"{pct_esp:.1f}%")
                item.setForeground(4, QBrush(QColor("#555555")))

                cant_real_txt = str(t['cantidad_real']) if not t['summary'] else ""
                item.setText(5, cant_real_txt)

                if not t['summary']:
                    item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
                    item.setBackground(5, QBrush(QColor("#E3F2FD")))

                try:
                    c_plan = float(t['cantidad_obra'])
                    c_ejec = float(t['cantidad_real'])
                    pct = (c_ejec / c_plan * 100) if c_plan > 0 else 0
                except: pct = 0

                pct_txt = f"{pct:.1f}%" if not t['summary'] and float(t['cantidad_obra'] or 0) > 0 else ""
                item.setText(6, pct_txt)
                item.setForeground(6, QBrush(QColor("#0D47A1")))
                item.setFont(6, QFont("Segoe UI", 9, QFont.Weight.Bold))

                item.setText(7, t['start'].strftime(f_fmt))
                item.setText(8, t['finish'].strftime(f_fmt))
                for c in range(2, 9): item.setTextAlignment(c, Qt.AlignmentFlag.AlignCenter)

            elif self.modo_linea_base:
                item.setText(2, f"{t['bl_duration']} d")
                item.setText(3, str(t['duration']))
                if not t['summary']:
                    item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
                    item.setBackground(3, QBrush(QColor("#FFFDE7")))
                item.setText(4, t['start'].strftime(f_fmt))
                item.setText(5, t['finish'].strftime(f_fmt))
                for c in range(2, 6): item.setTextAlignment(c, Qt.AlignmentFlag.AlignCenter)

            elif self.modo_ingreso_cantidades:
                cant_txt = str(t['cantidad_obra']) if not t['summary'] else ""
                item.setText(2, cant_txt)
                if not t['summary']:
                    item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
                    item.setBackground(2, QBrush(QColor("#E8F5E9")))
                item.setText(3, f"{t['duration']} d")
                item.setText(4, t['start'].strftime(f_fmt))
                item.setText(5, t['finish'].strftime(f_fmt))
                pred_txt = ";".join([self.wbs_map.get(p, p) for p in t['predecessors']]) if t['predecessors'] else ""
                item.setText(6, pred_txt)
                for c in [2, 3, 4, 5]: item.setTextAlignment(c, Qt.AlignmentFlag.AlignCenter)

            else:
                dur_txt = f"{t['duration']} d"
                item.setText(2, dur_txt)
                item.setText(3, t['start'].strftime(f_fmt))
                item.setText(4, t['finish'].strftime(f_fmt))
                pred_txt = ";".join([self.wbs_map.get(p, p) for p in t['predecessors']]) if t['predecessors'] else ""
                item.setText(5, pred_txt)
                for c in [2, 3, 4]: item.setTextAlignment(c, Qt.AlignmentFlag.AlignCenter)

            cols = self.tree.columnCount()
            for c in range(cols):
                if not (self.modo_corte and c == 6):
                    if not (self.modo_corte and c == 4):
                        item.setForeground(c, QBrush(QColor("black")))
                    elif self.modo_corte and c == 4:
                        item.setForeground(c, QBrush(QColor("#666666")))

                # Mostrar en negrita: tareas resumen Y tareas de nivel 1
                # (p.ej. "FIN" que en el XML no tiene hijos pero es cabecera)
                is_header = t['summary'] or t['indent'] == 1
                if is_header:
                    item.setBackground(c, QBrush(QColor("#FAFAFA")))
                    item.setFont(c, font_bold)
                elif not (self.modo_corte and c == 6):
                    item.setFont(c, font_reg)
                    if t['critical'] and not self.modo_linea_base:
                        item.setForeground(c, QBrush(QColor("#D00000")))

        self.tree.blockSignals(False)
        self.scrolling = False

    def al_editar_celda(self, item, column):
        self.tree.blockSignals(True)
        try:
            idx = item.data(0, Qt.ItemDataRole.UserRole)
            if idx is None:
                self.tree.blockSignals(False)
                return

            t = self.tasks[idx]
            needs_recalc = False

            if self.modo_ingreso_cantidades and not self.modo_linea_base:
                if column == 2:
                    try: t['cantidad_obra'] = item.text(2)
                    except: pass

            elif self.modo_linea_base and not self.modo_corte:
                if column == 3:
                    try:
                        val = int(''.join(filter(str.isdigit, item.text(3))))
                        if val < 1: val = 1
                        t['duration'] = val
                        t['finish'] = sumar_dias_habiles(t['start'], val, self.festivos_set)
                        item.setText(5, t['finish'].strftime("%d/%m/%y"))
                        needs_recalc = True
                    except: pass

            elif self.modo_corte and column == 5:
                try:
                    texto = item.text(5).replace(',', '.')
                    cant_real = float(texto)
                    t['cantidad_real'] = cant_real

                    try:
                        c_plan = float(t['cantidad_obra'])
                        pct = (cant_real / c_plan) if c_plan > 0 else 0.0
                    except: pct = 0.0

                    item.setText(6, f"{pct * 100:.1f}%")
                    if pct >= 1.0: item.setForeground(6, QBrush(QColor("green")))
                    else: item.setForeground(6, QBrush(QColor("#0D47A1")))

                    if self.fecha_linea_corte and pct < 1.0:
                        dur_base = t.get('bl_duration', t['duration'])
                        remanente_exacto = dur_base * (1.0 - pct)
                        dias_necesarios = math.ceil(remanente_exacto)
                        if dias_necesarios < 1: dias_necesarios = 1

                        fecha_corte_dt = datetime.combine(self.fecha_linea_corte.toPyDate(), datetime.min.time())
                        inicio_saldo = siguiente_dia_habil(fecha_corte_dt, self.festivos_set)
                        nuevo_fin = sumar_dias_habiles(inicio_saldo, dias_necesarios, self.festivos_set)

                        t['finish'] = nuevo_fin
                        t['duration'] = calcular_duracion_habiles(t['start'], t['finish'], self.festivos_set)

                        item.setText(8, nuevo_fin.strftime("%d/%m/%y"))

                        if nuevo_fin > t.get('bl_finish', t['finish']):
                            item.setForeground(8, QBrush(QColor("red")))
                            item.setFont(8, QFont("Segoe UI", 9, QFont.Weight.Bold))
                        else:
                            item.setForeground(8, QBrush(QColor("black")))
                            item.setFont(8, QFont("Segoe UI", 9))

                    elif pct >= 1.0:
                        item.setForeground(8, QBrush(QColor("green")))

                    needs_recalc = True
                except Exception as e:
                    print(f"Error cálculo corte: {e}")

        except Exception as e:
            print(f"Error general editando: {e}")

        self.tree.blockSignals(False)
        if needs_recalc:
            self.recalcular_todo()
            self.recalcular_resumenes()
            self.actualizar_tabla_dinamica()
            self.dibujar_gantt()

    def recalcular_todo(self):
        count = len(self.tasks)
        for _ in range(count):
            cambios = False
            for t in self.tasks:
                if t['summary']: continue

                inicio_base = t.get('xml_start', t['start'])
                inicio_por_dependencias = None

                for pid in t['predecessors']:
                    idx_p = self.uid_map.get(pid)
                    if idx_p is not None:
                        pred = self.tasks[idx_p]
                        fin_p = pred['finish']
                        estaban_separadas = t['xml_start'] > pred['xml_finish']

                        if estaban_separadas:
                            fecha_candidata = siguiente_dia_habil(fin_p, self.festivos_set)
                        else:
                            fecha_candidata = fin_p

                        if inicio_por_dependencias is None or fecha_candidata > inicio_por_dependencias:
                            inicio_por_dependencias = fecha_candidata

                nuevo_inicio = inicio_base
                if inicio_por_dependencias and inicio_por_dependencias > inicio_base:
                    nuevo_inicio = inicio_por_dependencias

                if t.get('cantidad_real', 0) > 0:
                    nuevo_inicio = t['start']

                if nuevo_inicio != t['start']:
                    t['start'] = nuevo_inicio
                    t['finish'] = sumar_dias_habiles(t['start'], t['duration'], self.festivos_set)
                    cambios = True
                else:
                    nuevo_fin = sumar_dias_habiles(t['start'], t['duration'], self.festivos_set)
                    if nuevo_fin != t['finish']:
                        t['finish'] = nuevo_fin
                        cambios = True

            if not cambios: break

    def recalcular_resumenes(self):
        for i in range(len(self.tasks) - 1, -1, -1):
            t = self.tasks[i]
            if t['summary']:
                fechas_ini = []
                fechas_fin = []
                for j in range(i + 1, len(self.tasks)):
                    child = self.tasks[j]
                    if child['indent'] <= t['indent']: break
                    fechas_ini.append(child['start'])
                    fechas_fin.append(child['finish'])

                if fechas_ini:
                    t['start'] = min(fechas_ini)
                    t['finish'] = max(fechas_fin)
                    t['duration'] = calcular_duracion_habiles(t['start'], t['finish'], self.festivos_set)

    def actualizar_tabla_dinamica(self):
        self.tree.blockSignals(True)
        it = QTreeWidgetItemIterator(self.tree)
        f_fmt = "%d/%m/%y"
        while it.value():
            item = it.value(); idx = item.data(0, Qt.ItemDataRole.UserRole)
            if idx is not None:
                t = self.tasks[idx]
                if self.modo_corte:
                    item.setText(7, t['start'].strftime(f_fmt))
                    item.setText(8, t['finish'].strftime(f_fmt))
                elif self.modo_linea_base:
                    item.setText(3, str(t['duration']))
                    item.setText(4, t['start'].strftime(f_fmt))
                    item.setText(5, t['finish'].strftime(f_fmt))
            it += 1
        self.tree.blockSignals(False)

    def dibujar_gantt(self):
        self.scene.clear()
        if not self.tasks: return
        fechas = [t['start'] for t in self.tasks] + [t['finish'] for t in self.tasks]
        if self.modo_linea_base: fechas += [t['bl_start'] for t in self.tasks] + [t['bl_finish'] for t in self.tasks]
        f_min = min(fechas) - timedelta(days=2); dias_tot = (max(fechas) - f_min).days + 20
        w_scene = dias_tot * self.ancho_dia; h_scene = (len(self.tasks) * self.alto_fila) + self.alto_encabezado
        self.scene.setSceneRect(0, 0, w_scene, h_scene)

        r_head = QGraphicsRectItem(0, 0, w_scene, self.alto_encabezado)
        r_head.setPen(QPen(Qt.PenStyle.NoPen)); r_head.setBrush(QBrush(QColor(self.color_header))); self.scene.addItem(r_head)
        pen_grid = QPen(QColor("#EAEAEA")); pen_grid.setStyle(Qt.PenStyle.DashLine)

        for d in range(dias_tot):
            x = d * self.ancho_dia; fecha = f_min + timedelta(days=d)
            linea = QGraphicsLineItem(x, self.alto_encabezado, x, h_scene); linea.setPen(pen_grid); self.scene.addItem(linea)
            if not es_dia_laborable(fecha, self.festivos_set):
                r_feriado = QGraphicsRectItem(x, self.alto_encabezado, self.ancho_dia, h_scene - self.alto_encabezado)
                r_feriado.setPen(QPen(Qt.PenStyle.NoPen)); r_feriado.setBrush(QBrush(QColor("#F9F9F9")))
                self.scene.addItem(r_feriado)
            if fecha.day == 1 or d % 7 == 0:
                txt = QGraphicsTextItem(fecha.strftime("%d %b")); txt.setDefaultTextColor(QColor(self.color_texto_header))
                font_fecha = QFont("Segoe UI", 8); font_fecha.setBold(True); txt.setFont(font_fecha); txt.setPos(x + 2, 12); self.scene.addItem(txt)
                l_sem = QGraphicsLineItem(x, 15, x, self.alto_encabezado); l_sem.setPen(QPen(QColor("#AAAAAA"))); self.scene.addItem(l_sem)

        if self.fecha_linea_corte:
            fecha_dt = datetime.combine(self.fecha_linea_corte.toPyDate(), datetime.min.time())
            if fecha_dt >= f_min:
                dias_diff = (fecha_dt - f_min).days
                x_line = (dias_diff + 1) * self.ancho_dia
                linea_c = QGraphicsLineItem(x_line, self.alto_encabezado, x_line, h_scene)
                pen_r = QPen(QColor("red")); pen_r.setWidth(2); pen_r.setStyle(Qt.PenStyle.DashLine); linea_c.setPen(pen_r)
                txt_c = QGraphicsTextItem("CORTE"); txt_c.setDefaultTextColor(QColor("red"))
                txt_c.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold)); txt_c.setPos(x_line + 5, self.alto_encabezado + 5)
                self.scene.addItem(linea_c); self.scene.addItem(txt_c)

        coords = {}
        for t in self.tasks:
            i = t['index']; y_base = (i * self.alto_fila) + self.alto_encabezado
            x_real = (t['start'] - f_min).days * self.ancho_dia; w_real = ((t['finish'] - t['start']).days + 1) * self.ancho_dia

            if not self.modo_linea_base:
                y_rect = y_base + 7; h_rect = 16
                rect = QGraphicsRectItem(x_real, y_rect, w_real, h_rect)
                if t['summary']:
                    rect.setBrush(QBrush(QColor(self.color_barra_resumen))); rect.setPen(QPen(Qt.PenStyle.NoPen))
                    rect.setRect(x_real, y_rect, w_real, 6); self.scene.addItem(rect)
                    self.scene.addRect(x_real, y_rect, 4, 14, brush=QBrush(QColor(self.color_barra_resumen)))
                    self.scene.addRect(x_real + w_real - 4, y_rect, 4, 14, brush=QBrush(QColor(self.color_barra_resumen)))
                else:
                    color_b = self.color_barra_critica if t['critical'] else self.color_barra_normal
                    pen_c = "#A80000" if t['critical'] else "#005A9E"
                    if self.modo_corte and t['finish'] > t['bl_finish']: color_b = "#D32F2F"
                    rect.setBrush(QBrush(QColor(color_b))); rect.setPen(QPen(QColor(pen_c))); self.scene.addItem(rect)
                coords[t['uid']] = {'x_in': x_real, 'x_out': x_real + w_real, 'y': y_rect + 8}
                txt_lbl = QGraphicsTextItem(t['name']); txt_lbl.setDefaultTextColor(QColor("black"))
                txt_lbl.setFont(QFont("Segoe UI", 8)); txt_lbl.setPos(x_real + w_real + 5, y_rect - 2); self.scene.addItem(txt_lbl)
            else:
                d_b_ini = (t['bl_start'] - f_min).days; w_b = ((t['bl_finish'] - t['bl_start']).days + 1) * self.ancho_dia; x_b = d_b_ini * self.ancho_dia
                if not t['summary']:
                    r_bl = QGraphicsRectItem(x_b, y_base + 5, w_b, 10); r_bl.setPen(QPen(Qt.PenStyle.NoPen))
                    r_bl.setBrush(QBrush(QColor(self.color_barra_base))); self.scene.addItem(r_bl)
                y_real = y_base + 20; h_real = 14
                rect = QGraphicsRectItem(x_real, y_real, w_real, h_real)
                if t['summary']:
                    rect.setBrush(QBrush(QColor(self.color_barra_resumen))); rect.setRect(x_real, y_base + 15, w_real, 6); self.scene.addItem(rect)
                    self.scene.addRect(x_real, y_base + 15, 2, 12, brush=QBrush(QColor(self.color_barra_resumen)))
                    self.scene.addRect(x_real + w_real - 2, y_base + 15, 2, 12, brush=QBrush(QColor(self.color_barra_resumen)))
                else:
                    color = self.color_barra_normal
                    if t['finish'] > t['bl_finish']: color = self.color_barra_critica
                    rect.setBrush(QBrush(QColor(color))); rect.setPen(QPen(Qt.PenStyle.NoPen)); self.scene.addItem(rect)
                coords[t['uid']] = {'x_in': x_real, 'x_out': x_real + w_real, 'y': y_real + (h_real / 2)}
                txt_lbl = QGraphicsTextItem(t['name']); txt_lbl.setDefaultTextColor(QColor("black"))
                txt_lbl.setFont(QFont("Segoe UI", 8)); txt_lbl.setPos(x_real + w_real + 5, y_real - 2); self.scene.addItem(txt_lbl)

        pen_arrow = QPen(QColor(self.color_flecha))
        for t in self.tasks:
            for pid in t['predecessors']:
                if pid in coords and t['uid'] in coords:
                    c1 = coords[pid]; c2 = coords[t['uid']]
                    path = QPainterPath(); path.moveTo(c1['x_out'], c1['y'])
                    mid = c2['x_in'] - 10
                    if mid < c1['x_out']: mid = c1['x_out'] + 10
                    path.lineTo(mid, c1['y']); path.lineTo(mid, c2['y']); path.lineTo(c2['x_in'], c2['y'])
                    path_item = QGraphicsPathItem(path); path_item.setPen(pen_arrow); self.scene.addItem(path_item)
                    poly = QPolygonF([QPointF(c2['x_in'], c2['y']), QPointF(c2['x_in'] - 5, c2['y'] - 3),
                                      QPointF(c2['x_in'] - 5, c2['y'] + 3)])
                    self.scene.addPolygon(poly, QPen(Qt.PenStyle.NoPen), QBrush(QColor(self.color_flecha)))

