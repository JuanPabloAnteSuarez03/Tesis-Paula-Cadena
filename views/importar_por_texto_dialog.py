from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QLineEdit, QMessageBox, QSizePolicy, QHeaderView
)
from PyQt6.QtCore import Qt, QEvent
from PyQt6.QtGui import QKeySequence
import csv
import io
import re


class ImportarPorTextoDialog(QDialog):
    """
    Diálogo con cuadrícula tipo Excel para pegar o escribir líneas con columnas:
    ITEM | DESCRIPCIÓN | UND. | CANT.

    - Permite pegar desde Excel/CSV (tabuladores) o texto multilinea.
    - Ofrece botones para agregar/eliminar filas y limpiar la tabla.
    - Devuelve una lista de diccionarios al aceptar.
    """

    def __init__(self, parent=None, prefill_rows=None):
        super().__init__(parent)
        self.setWindowTitle("Importar por Texto")
        self.resize(900, 550)

        layout = QVBoxLayout(self)

        # Instrucciones breves
        info = QLabel(
            "Pegue datos con columnas: ITEM\tDESCRIPCIÓN\tUND.\tCANT. (Ctrl+V).\n"
            "ITEM: entero (capítulo) o subnúmero 1.1/1,1; DESCRIPCIÓN: párrafo; CANT.: número."
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        # Tabla principal
        self.table = QTableWidget(self)
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ITEM", "DESCRIPCIÓN", "UND.", "CANT."])
        self.table.setRowCount(20)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectItems)
        self.table.setEditTriggers(QTableWidget.EditTrigger.AllEditTriggers)
        self.table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        # Ajuste de columnas: descripción se estira, las demás a contenido
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # ITEM
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)           # DESCRIPCIÓN
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # UND.
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # CANT.
        self.table.verticalHeader().setDefaultSectionSize(40)
        self.table.verticalHeader().setMinimumSectionSize(28)
        self.table.setWordWrap(True)
        layout.addWidget(self.table)

        # Barra inferior de acciones
        actions = QHBoxLayout()
        actions.addStretch(1)
        self.add_row_btn = QPushButton("Agregar filas")
        self.del_row_btn = QPushButton("Eliminar filas")
        self.clear_btn = QPushButton("Limpiar")
        self.accept_btn = QPushButton("Continuar")
        self.cancel_btn = QPushButton("Cancelar")
        actions.addWidget(self.add_row_btn)
        actions.addWidget(self.del_row_btn)
        actions.addWidget(self.clear_btn)
        actions.addStretch(1)
        actions.addWidget(self.accept_btn)
        actions.addWidget(self.cancel_btn)
        layout.addLayout(actions)

        # Conexiones
        self.add_row_btn.clicked.connect(self._on_add_rows)
        self.del_row_btn.clicked.connect(self._on_delete_rows)
        self.clear_btn.clicked.connect(self._on_clear)
        self.accept_btn.clicked.connect(self._on_accept)
        self.cancel_btn.clicked.connect(self.reject)

        # Mejoras UX: permitir pegado masivo (Ctrl+V) con tabuladores
        self.table.installEventFilter(self)
        # Distribución: tabla ocupa todo el espacio disponible
        layout.setStretch(0, 0)  # info
        layout.setStretch(1, 1)  # table
        layout.setStretch(2, 0)  # actions
        # Estilos
        self.setStyleSheet(
            """
            QDialog { background: #f6f8fb; }
            QLabel { color: #333; font-size: 12px; }
            QTableWidget { background: #ffffff; gridline-color: #d5d9e0; font-size: 13px; }
            QHeaderView::section { background-color: #0a84ff; color: white; padding: 6px; border: 0px; font-weight: bold; }
            QTableWidget::item { padding: 6px; }
            QTableWidget::item:selected { background: #e6f2ff; color: #000; }
            /* Editor mientras se escribe */
            QTableWidget QLineEdit { background: #ffffff; color: #111; padding: 3px 6px; selection-background-color: #cfe7ff; selection-color: #000; }
            QPushButton { background-color: #0a84ff; color: white; border-radius: 6px; padding: 8px 14px; }
            QPushButton:hover { background-color: #006edc; }
            QPushButton:pressed { background-color: #005bb5; }
            """
        )

        # Prefill optional rows (list of dicts with keys: item, descripcion, unidad, cantidad)
        try:
            if prefill_rows:
                # Crear una copia profunda para evitar modificar los datos originales
                rows = [dict(row) for row in prefill_rows]
                print(f"DEBUG_DIALOG: rows después de copia profunda: {rows}")

                # ¿Ya existe un ITEM = "1"?
                has_root = (
                    rows and str(rows[0].get("item", "")).strip() == "1"
                )

                extra = 0 if has_root else 1
                needed = max(20, len(rows) + extra)
                self.table.setRowCount(needed)

                start_row = 0

                # 1️⃣ CREAR ENCABEZADO SOLO SI NO EXISTE
                if not has_root:
                    item_header = QTableWidgetItem("1")
                    item_header.setTextAlignment(
                        Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight
                    )
                    item_header.setFlags(
                        Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled
                    )
                    self.table.setItem(0, 0, item_header)

                    for c in range(1, 4):
                        self.table.setItem(0, c, QTableWidgetItem(""))

                    start_row = 1

                # 2️⃣ INSERTAR FILAS REALES
                for r_idx, r in enumerate(rows, start=start_row):
                    item_value = r.get('item')
                    item = str(item_value).strip() if item_value is not None and item_value != '' else ''  # <-- CORRECCIÓN: verificar explícitamente
                    desc = str(r.get('descripcion', '') or '')
                    und = str(r.get('unidad', '') or '')
                    ifc_guids = r.get('ifc_guids', None)
                    cant = r.get('cantidad', '')

                    print(f"DEBUG_DIALOG: Procesando fila - item='{item}', desc='{desc}', und='{und}', cant='{cant}'")

                    if isinstance(cant, float):
                        cant = f"{cant}"
                    else:
                        cant = str(cant or '')

                    col_values = [item, desc, und, cant]

                    for c_idx, value in enumerate(col_values):
                        qitem = QTableWidgetItem(value)

                        if c_idx in (0, 3):
                            qitem.setTextAlignment(
                                Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight
                            )

                        if c_idx == 1:
                            qitem.setToolTip(value)
                            if ifc_guids:
                                qitem.setData(Qt.ItemDataRole.UserRole, ifc_guids)

                        self.table.setItem(r_idx, c_idx, qitem)

        except Exception:
            pass


    def showEvent(self, event):
        super().showEvent(event)
        try:
            # Abrir maximizada manteniendo barra de título y controles
            self.setWindowState(self.windowState() | Qt.WindowState.WindowMaximized)
        except Exception:
            pass

    def eventFilter(self, obj, event):
        if obj is self.table and event.type() == QEvent.Type.KeyPress:
            try:
                if event.matches(QKeySequence.StandardKey.Paste):
                    self._paste_clipboard()
                    return True
            except Exception:
                pass
            # Fallback robusto: detectar Ctrl+V manualmente
            try:
                if (event.key() == Qt.Key.Key_V and 
                    (event.modifiers() & Qt.KeyboardModifier.ControlModifier)):
                    self._paste_clipboard()
                    return True
            except Exception:
                pass
        return super().eventFilter(obj, event)

    def _paste_clipboard(self):
        from PyQt6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        if not text:
            return

        # Usar parser TSV con soporte de comillas para no romper descripciones multilínea
        reader = csv.reader(io.StringIO(text), delimiter='\t', quotechar='"')
        parsed_rows = [row for row in reader]
        # Limpiar filas completamente vacías
        parsed_rows = [row for row in parsed_rows if any(c.strip() for c in row)]

        # Posición inicial de pegado
        start_row = self.table.currentRow() if self.table.currentRow() >= 0 else 0
        required_rows = start_row + len(parsed_rows)
        if required_rows > self.table.rowCount():
            self.table.setRowCount(required_rows)

        def is_number(value: str) -> bool:
            try:
                float(value.replace('.', '').replace(',', '.'))
                return True
            except Exception:
                return False

        item_pattern = re.compile(r"^\d+(?:[\.,]\d+)*$")

        r_out = 0
        for raw in parsed_rows:
            row = [c.strip() for c in raw]
            # Omitir líneas de subtotal explícitas
            if any('SUB-TOTAL' in c.upper() or 'SUBTOTAL' in c.upper() for c in row):
                continue

            # Mapear dinámicamente columnas: [item, desc, und, cant]
            item_txt = row[0] if len(row) > 0 else ""
            desc_txt = ""
            und_txt = ""
            cant_txt = ""

            if len(row) >= 4:
                desc_txt = " ".join([c for c in row[1:-2] if c]) or row[1]
                und_txt = row[-2]
                cant_txt = row[-1]
            elif len(row) == 3:
                desc_txt = row[1]
                # Última es cantidad si es numérica; si no, es unidad
                if is_number(row[2]):
                    cant_txt = row[2]
                else:
                    und_txt = row[2]
            elif len(row) == 2:
                # Capítulo: solo item y descripción
                desc_txt = row[1]
            else:
                continue

            # Validar ITEM: entero o subnúmero (1, 2, 1.1, 1,1, 1.01)
            if not item_txt or not item_pattern.match(item_txt):
                # Si no hay item válido, saltamos (evita pegar líneas sueltas)
                continue

            # Escribir a la tabla
            abs_row = start_row + r_out
            r_out += 1
            # Asegurar espacio
            if abs_row >= self.table.rowCount():
                self.table.setRowCount(abs_row + 1)

            col_values = [item_txt, desc_txt, und_txt, cant_txt]
            for c_idx, value in enumerate(col_values):
                qitem = QTableWidgetItem(value)
                if c_idx in (0, 3):
                    qitem.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)
                if c_idx == 1 and value:
                    qitem.setToolTip(value)
                self.table.setItem(abs_row, c_idx, qitem)

    def _on_add_rows(self):
        add = 10
        self.table.setRowCount(self.table.rowCount() + add)

    def _on_delete_rows(self):
        selected = set(i.row() for i in self.table.selectedIndexes())
        if not selected:
            return
        for row in sorted(selected, reverse=True):
            if 0 <= row < self.table.rowCount():
                self.table.removeRow(row)

    def _on_clear(self):
        self.table.clearContents()
        self.table.setRowCount(20)

    def _on_accept(self):
        data = self.collect_rows()
        if not data:
            QMessageBox.warning(self, "Sin datos", "Ingrese o pegue al menos una fila válida.")
            return
        self._result = data
        self.accept()

    def collect_rows(self):
        """
        Extrae filas no vacías como lista de dicts:
        [{ 'item': str, 'descripcion': str, 'unidad': str, 'cantidad': float }]
        Filas sin descripción se ignoran. Cantidad vacía -> 1.0.
        """
        results = []
        for r in range(self.table.rowCount()):
            item = self._text(r, 0)
            desc = self._text(r, 1)
            und = self._text(r, 2)
            cant_text = self._text(r, 3)
            # Solo saltar si no hay descripción Y no hay item (capítulo sin descripción no es válido)
            if not desc and not item:
                continue
            ifc_guids = None
            try:
                it_desc = self.table.item(r, 1)
                if it_desc is not None:
                    ifc_guids = it_desc.data(Qt.ItemDataRole.UserRole)
            except Exception:
                ifc_guids = None
            try:
                cantidad = float(cant_text.replace(',', '.')) if cant_text else 1.0
            except Exception:
                cantidad = 1.0
            results.append({
                'item': item,
                'descripcion': desc,
                'unidad': und,
                'cantidad': cantidad,
                'ifc_guids': ifc_guids,
            })
        return results

    def _text(self, row, col):
        it = self.table.item(row, col)
        return it.text().strip() if it else ""

    def result_rows(self):
        return getattr(self, '_result', [])


