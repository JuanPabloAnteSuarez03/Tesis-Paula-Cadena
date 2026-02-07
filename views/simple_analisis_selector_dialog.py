from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSizePolicy, QTableWidget, QTableWidgetItem, QHeaderView,
    QLineEdit, QMessageBox, QApplication
)
from PyQt6.QtCore import Qt
from sqlalchemy import func
from models.database import SessionLocal
from models.analisis_unitario import AnalisisUnitario


class SimpleAnalisisSelectorDialog(QDialog):
    """
    Diálogo simple que muestra una tabla de análisis unitarios para seleccionar uno.
    Es independiente y no afecta la vista de análisis unitarios del fondo.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Buscar Análisis Unitario Manualmente")
        self.resize(1000, 600)
        self._selected = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Info
        info = QLabel("Seleccione un análisis unitario de la lista. Puede usar la búsqueda por código o descripción.")
        info.setWordWrap(True)
        info.setStyleSheet("color: #333; font-size: 12px; padding: 5px;")
        layout.addWidget(info)

        # Campo de búsqueda
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar por código o descripción...")
        search_layout.addWidget(QLabel("Buscar:"))
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)

        # Tabla de análisis unitarios
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Código", "Descripción", "Unidad", "Costo Unitario"])
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.table.verticalHeader().setDefaultSectionSize(28)
        layout.addWidget(self.table)

        # Botones
        actions = QHBoxLayout()
        actions.addStretch(1)
        self.btn_use = QPushButton("Usar análisis seleccionado")
        self.btn_cancel = QPushButton("Cancelar")
        actions.addWidget(self.btn_use)
        actions.addWidget(self.btn_cancel)
        layout.addLayout(actions)

        # Conectar señales
        self.btn_use.clicked.connect(self._on_use_selected)
        self.btn_cancel.clicked.connect(self.reject)
        self.search_input.textChanged.connect(self._on_search_changed)
        self.table.cellDoubleClicked.connect(lambda r, c: self._on_use_selected())
        # Conectar señal de selección para habilitar/deshabilitar el botón
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        self.table.currentItemChanged.connect(self._on_current_item_changed)

        # Estado inicial
        self.btn_use.setEnabled(False)

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
            QPushButton:disabled { background-color: #cccccc; color: #666666; }
            QLineEdit { padding: 4px; border: 1px solid #cccccc; border-radius: 4px; }
            """
        )

        # Cargar datos
        self._load_analisis_data()

    def _load_analisis_data(self):
        """Carga todos los análisis unitarios en la tabla."""
        session = SessionLocal()
        try:
            analisis_list = session.query(AnalisisUnitario).all()
            
            self.table.setRowCount(len(analisis_list))
            for row, analisis in enumerate(analisis_list):
                # Código
                self.table.setItem(row, 0, QTableWidgetItem(analisis.codigo or ''))
                
                # Descripción
                desc_item = QTableWidgetItem(analisis.descripcion or '')
                desc_item.setToolTip(analisis.descripcion or '')
                self.table.setItem(row, 1, desc_item)
                
                # Unidad
                self.table.setItem(row, 2, QTableWidgetItem((analisis.unidad or '').upper()))
                
                # Costo unitario
                try:
                    cu = float(analisis.total_calculado or 0.0)
                except Exception:
                    cu = float(analisis.total or 0.0)
                self.table.setItem(row, 3, QTableWidgetItem(f"${cu:,.2f}"))
            
            # Si hay datos, seleccionar la primera fila automáticamente
            if len(analisis_list) > 0:
                self.table.selectRow(0)
                self.btn_use.setEnabled(True)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudieron cargar los análisis unitarios:\n{e}")
        finally:
            session.close()
    
    def _update_button_state(self):
        """Actualiza el estado del botón según la selección actual."""
        current_row = self.table.currentRow()
        selected_items = self.table.selectedItems()
        
        # Habilitar si hay una fila actual válida y visible, o si hay items seleccionados visibles
        enabled = False
        if current_row >= 0 and not self.table.isRowHidden(current_row):
            enabled = True
        elif selected_items:
            for item in selected_items:
                if item and not self.table.isRowHidden(item.row()):
                    enabled = True
                    break
        
        self.btn_use.setEnabled(enabled)

    def _on_selection_changed(self):
        """Habilita o deshabilita el botón según si hay una selección."""
        self._update_button_state()
    
    def _on_current_item_changed(self, current_item, previous_item):
        """Habilita o deshabilita el botón cuando cambia el item actual."""
        self._update_button_state()

    def _on_search_changed(self, text):
        """Filtra la tabla según el texto de búsqueda."""
        filter_text = text.strip().lower()
        
        for row in range(self.table.rowCount()):
            code_item = self.table.item(row, 0)
            desc_item = self.table.item(row, 1)
            
            code = code_item.text().lower() if code_item else ""
            desc = desc_item.text().lower() if desc_item else ""
            
            # Mostrar fila si el filtro está en código o descripción
            match = filter_text in code or filter_text in desc
            self.table.setRowHidden(row, not match)
        
        # Actualizar estado del botón después de filtrar
        self._update_button_state()

    def _on_use_selected(self):
        """Usar el análisis seleccionado y cerrar el diálogo."""
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.information(self, "Sin selección", "Por favor seleccione un análisis de la lista.")
            return
        
        # Obtener datos de la fila seleccionada
        code_item = self.table.item(current_row, 0)
        desc_item = self.table.item(current_row, 1)
        und_item = self.table.item(current_row, 2)
        cu_item = self.table.item(current_row, 3)
        
        self._selected = {
            'codigo': code_item.text() if code_item else '',
            'descripcion': desc_item.text() if desc_item else '',
            'unidad': und_item.text() if und_item else '',
            'costo_unitario': self._parse_costo_unitario(cu_item.text() if cu_item else '0')
        }
        self.accept()

    def _parse_costo_unitario(self, texto):
        """Parsea el texto del costo unitario a float."""
        try:
            clean = texto.replace('$', '').replace(',', '').strip()
            return float(clean) if clean else 0.0
        except Exception:
            return 0.0

    def selected_analysis(self):
        """Devuelve el análisis seleccionado o None."""
        return getattr(self, '_selected', None)

    def showEvent(self, event):
        """Al mostrar el diálogo, enfocar el campo de búsqueda."""
        super().showEvent(event)
        self.search_input.setFocus()
        self.search_input.selectAll()
