from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QPushButton, QHeaderView, QSizePolicy
)
from PyQt6.QtCore import Qt
from sqlalchemy import func
from models.database import SessionLocal
from models.analisis_unitario import AnalisisUnitario
import re
import unicodedata
from difflib import SequenceMatcher


class AnalisisMatchDialog(QDialog):
    """
    Diálogo para sugerir Análisis Unitarios candidatos en base a unidad y descripción.

    - Filtra por unidad (normalizada) para reducir el universo.
    - Calcula similitud de descripciones combinando tokens (Jaccard) y ratio de secuencia.
    - Muestra los mejores N resultados para que el usuario elija.
    """

    def __init__(self, descripcion_objetivo: str, unidad_objetivo: str, parent=None, max_results: int = 50):
        super().__init__(parent)
        self.setWindowTitle("Buscar Análisis por Descripción y Unidad")
        self.resize(1000, 600)
        self._selected = None
        self._max_results = max_results

        self._desc_query = (descripcion_objetivo or "").strip()
        self._unit_query = self._normalize_unit(unidad_objetivo)

        layout = QVBoxLayout(self)

        # Info
        self.lbl_info = QLabel(
            f"Unidad: {self._unit_query or '(sin unidad)'}\nTexto: {self._desc_query[:200]}{'…' if len(self._desc_query) > 200 else ''}"
        )
        self.lbl_info.setWordWrap(True)
        layout.addWidget(self.lbl_info)

        # Tabla resultados
        self.table = QTableWidget(self)
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Código", "Descripción", "Unidad", "Costo Unitario", "Similitud"])
        self.table.setAlternatingRowColors(True)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.table.verticalHeader().setDefaultSectionSize(28)
        layout.addWidget(self.table)

        # Botones
        actions = QHBoxLayout()
        actions.addStretch(1)
        self.btn_accept = QPushButton("Usar seleccionado")
        self.btn_stop = QPushButton("Detener proceso")
        self.btn_cancel = QPushButton("Cancelar")
        actions.addWidget(self.btn_accept)
        actions.addWidget(self.btn_stop)
        actions.addWidget(self.btn_cancel)
        layout.addLayout(actions)

        self._aborted = False
        self.btn_accept.clicked.connect(self._on_accept)
        self.btn_stop.clicked.connect(self._on_abort_all)
        self.btn_cancel.clicked.connect(self.reject)
        self.table.cellDoubleClicked.connect(lambda r, c: self._on_accept())

        # Estilos
        self.setStyleSheet(
            """
            QDialog { background: #f6f8fb; }
            QLabel { color: #333; font-size: 12px; }
            QTableWidget { background: #ffffff; gridline-color: #d5d9e0; font-size: 13px; }
            QHeaderView::section { background-color: #0a84ff; color: white; padding: 6px; border: 0px; font-weight: bold; }
            QPushButton { background-color: #0a84ff; color: white; border-radius: 6px; padding: 8px 14px; }
            QPushButton:hover { background-color: #006edc; }
            QPushButton:pressed { background-color: #005bb5; }
            """
        )

        # Cargar candidatos
        self._load_candidates()

    # --- API ---
    def selected_analysis(self):
        return self._selected

    def was_aborted(self) -> bool:
        return bool(getattr(self, '_aborted', False))

    # --- Internos ---
    def _on_accept(self):
        row = self.table.currentRow()
        if row < 0:
            return
        codigo = self._text(row, 0)
        desc = self._text(row, 1)
        und = self._text(row, 2)
        cu_txt = self._text(row, 3).replace('$', '').replace(',', '')
        try:
            cu = float(cu_txt) if cu_txt else 0.0
        except Exception:
            cu = 0.0
        self._selected = {
            'codigo': codigo,
            'descripcion': desc,
            'unidad': und,
            'costo_unitario': cu,
        }
        self.accept()

    def _on_abort_all(self):
        # Marca interrupción global para el proceso de búsqueda por texto
        self._aborted = True
        self.reject()

    def _text(self, row, col):
        it = self.table.item(row, col)
        return it.text().strip() if it else ""

    def _load_candidates(self):
        session = SessionLocal()
        try:
            unit_norm = self._unit_query
            query = session.query(AnalisisUnitario)
            if unit_norm:
                query = query.filter(func.upper(AnalisisUnitario.unidad) == unit_norm)
            candidates = query.all()

            scored = []
            for a in candidates:
                desc = a.descripcion or ""
                score = self._similarity(self._desc_query, desc)
                # Recuperar costo unitario estimado (total_calculado)
                try:
                    cu = float(a.total_calculado or 0.0)
                except Exception:
                    cu = float(a.total or 0.0)
                scored.append((score, a.codigo, desc, a.unidad, cu))

            # Ordenar por score desc y limitar
            scored.sort(key=lambda t: t[0], reverse=True)
            top = scored[: self._max_results]

            self.table.setRowCount(len(top))
            for r, (score, codigo, desc, und, cu) in enumerate(top):
                self.table.setItem(r, 0, QTableWidgetItem(codigo))
                desc_item = QTableWidgetItem(desc)
                desc_item.setToolTip(desc)
                self.table.setItem(r, 1, desc_item)
                self.table.setItem(r, 2, QTableWidgetItem((und or '').upper()))
                self.table.setItem(r, 3, QTableWidgetItem(f"${cu:,.2f}"))
                self.table.setItem(r, 4, QTableWidgetItem(f"{score:.3f}"))

            if len(top) > 0:
                self.table.selectRow(0)
        finally:
            session.close()

    # --- Normalización y similitud ---
    def _normalize_unit(self, und: str) -> str:
        if not und:
            return ""
        u = (und or "").strip().upper()
        # Normalizar variantes comunes
        replacements = {
            "UN": "UND",
            "UNID": "UND",
            "UNIDAD": "UND",
            "M²": "M2",
            "M^2": "M2",
            "MTS2": "M2",
            "MTS": "M",
        }
        return replacements.get(u, u)

    def _normalize_text(self, text: str) -> str:
        if not text:
            return ""
        t = unicodedata.normalize('NFKD', text)
        t = ''.join(ch for ch in t if not unicodedata.combining(ch))
        t = t.lower()
        t = re.sub(r"[^a-z0-9\s]", " ", t)
        t = re.sub(r"\s+", " ", t).strip()
        return t

    def _token_set(self, text: str) -> set:
        t = self._normalize_text(text)
        if not t:
            return set()
        tokens = [w for w in t.split(' ') if len(w) > 1]
        return set(tokens)

    def _similarity(self, a: str, b: str) -> float:
        """Puntaje compuesto con palabras clave.
        - Jaccard de tokens (tema compartido)
        - SequenceMatcher (orden y forma del texto)
        - Bonus por palabras clave coincidentes (longitud >= 4, no-stopword)
        - Bonus por substring (consulta contenida en descripción)
        - Bonus por coincidencias numéricas/medidas (p. ej., 2,10 m; 30 cm; calibre 28)
        """
        na = self._normalize_text(a)
        nb = self._normalize_text(b)

        # Token Jaccard
        ta = set(na.split())
        tb = set(nb.split())
        if not ta or not tb:
            jacc = 0.0
        else:
            inter = len(ta & tb)
            union = len(ta | tb)
            jacc = inter / union if union else 0.0

        # Sequence matcher
        seq = SequenceMatcher(None, na, nb).ratio()

        # Bonus por substring
        substring_bonus = 0.08 if na and na in nb else 0.0

        # Bonus por palabras clave
        kw_bonus = self._keyword_bonus(na, nb)

        # Bonus por medidas/números
        num_bonus = self._numeric_bonus(a, b)

        # Ponderación final
        return 0.55 * jacc + 0.30 * seq + substring_bonus + kw_bonus + num_bonus

    def _keyword_bonus(self, na: str, nb: str) -> float:
        """Calcula un bonus (0..0.25) por coincidencias de palabras clave.
        Palabra clave: longitud >= 4 y no es stopword.
        Bonus escala con número y longitud de coincidencias.
        """
        stop = self._stopwords_es()
        ka = {t for t in na.split() if len(t) >= 4 and t not in stop}
        kb = {t for t in nb.split() if len(t) >= 4 and t not in stop}
        if not ka or not kb:
            return 0.0
        common = ka & kb
        if not common:
            return 0.0
        # Peso por palabra: 1.0 base + 0.05 por cada carácter sobre 4, máx 1.5
        def w(t: str) -> float:
            return min(1.5, 1.0 + 0.05 * max(0, len(t) - 4))
        raw = sum(w(t) for t in common)
        # Normalizar suavemente por tamaño de ka para evitar favorecer textos muy largos
        norm = max(1.0, sum(w(t) for t in list(ka)[:10]))  # cap primeras 10
        score = raw / norm
        # Escalar a [0..0.25]
        return min(0.25, 0.25 * score)

    def _stopwords_es(self) -> set:
        # Conjunto compacto de stopwords en español; se puede extender
        return {
            "de","la","el","los","las","un","una","unos","unas","y","o","u","a","en","con","por","para","del","al",
            "se","es","que","su","sus","como","sobre","sin","desde","hasta","entre","sobre","tambien","también","lo",
            "más","mas","menos","muy","ya","no","sí","si","esta","este","estos","estas","esa","ese","eso","esas","esos",
            "obra","obras","costo","costos","instalacion","instalación","suministro","incluye","incluyendo","nota","nuevo","nueva",
        }

    # --- Números y medidas ---
    def _numeric_bonus(self, a_raw: str, b_raw: str) -> float:
        """Bonus por coincidencia de medidas y números (0..0.30).
        - Se detectan números con decimal "," o "." y unidades cercanas.
        - Unidades soportadas: M, ML, M2, M3, CM, MM, KG, KG/M3.
        - También se reconoce patrón "calibre X" como token especial CAL:X.
        - Coincidencia exacta (tras normalizar) aporta más que coincidencia sin unidad.
        """
        a_tokens = self._extract_numeric_tokens(a_raw)
        b_tokens = self._extract_numeric_tokens(b_raw)

        if not a_tokens or not b_tokens:
            return 0.0

        # Separar por tipo
        a_with_unit = {t for t in a_tokens if ':' in t and not t.startswith('CAL:')}
        b_with_unit = {t for t in b_tokens if ':' in t and not t.startswith('CAL:')}
        a_no_unit = {t for t in a_tokens if t.isdigit() or (t.replace('.', '').isdigit())}
        b_no_unit = {t for t in b_tokens if t.isdigit() or (t.replace('.', '').isdigit())}
        a_cal = {t for t in a_tokens if t.startswith('CAL:')}
        b_cal = {t for t in b_tokens if t.startswith('CAL:')}

        # Matches
        match_with_unit = len(a_with_unit & b_with_unit)
        match_no_unit = len(a_no_unit & b_no_unit)
        match_cal = len(a_cal & b_cal)

        # Ponderaciones
        score = 0.0
        score += 0.08 * match_with_unit
        score += 0.03 * match_no_unit
        score += 0.05 * match_cal

        # Límite superior
        return min(0.30, score)

    def _extract_numeric_tokens(self, text: str) -> set:
        """Extrae tokens numéricos normalizados.
        Devuelve un set de strings:
        - "UNIT:val" (p. ej., "M2:150", "M:2.10", "KG/M3:38")
        - "val" (solo número, p. ej., "28")
        - "CAL:val" para patrones "calibre 28"
        """
        tokens = set()
        if not text:
            return tokens
        t = text
        # Patrón número con unidad opcional (espacio o no, decimal , o .)
        pattern = re.compile(r"(?i)(\d+(?:[\.,]\d+)?)\s*(m2|m\^2|m²|m3|m\^3|m³|ml|m|cm|mm|kg|kg\s*/\s*m3|kg/m3)?")
        for m in pattern.finditer(t):
            num_raw = m.group(1)
            unit_raw = (m.group(2) or '').lower().replace(' ', '')
            try:
                val = float(num_raw.replace(',', '.'))
            except Exception:
                continue
            # Normalizar unidad
            unit = ''
            if unit_raw in ('m2', 'm^2', 'm²'):
                unit = 'M2'
            elif unit_raw in ('m3', 'm^3', 'm³'):
                unit = 'M3'
            elif unit_raw == 'ml':
                unit = 'ML'
            elif unit_raw == 'm':
                unit = 'M'
            elif unit_raw == 'cm':
                unit = 'CM'
            elif unit_raw == 'mm':
                unit = 'MM'
            elif unit_raw in ('kg/m3', 'kg/m^3', 'kg/m³', 'kg/m3') or 'kg/m3' in unit_raw:
                unit = 'KG/M3'
            elif unit_raw == 'kg':
                unit = 'KG'

            if unit:
                tokens.add(f"{unit}:{val:.2f}")
            else:
                tokens.add(f"{val:.2f}")

        # Patrón calibre N
        cal_pat = re.compile(r"(?i)calibre\s*(\d+(?:[\.,]\d+)?)")
        for m in cal_pat.finditer(t):
            try:
                val = float(m.group(1).replace(',', '.'))
            except Exception:
                continue
            tokens.add(f"CAL:{val:.2f}")

        return tokens


