# views/recursos_por_analisis_view.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableView, QHeaderView, QPushButton, 
    QMessageBox, QLabel, QLineEdit, QDialog
)
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from PyQt6.QtCore import Qt, pyqtSignal

class AnalisisPorPresupuestoView(QWidget):
    # Señal para notificar cuando se selecciona un análisis (por ejemplo, desde el selector)
    analisis_selected_por_presupuesto = pyqtSignal(str)
    
    def __init__(self, codigo_presupuesto, parent=None):
        super().__init__(parent)
        self.codigo_presupuesto = codigo_presupuesto
        self.setWindowTitle(f"Análisis para Presupuesto {codigo_presupuesto}")
        self.resize(800, 600)
        self.layout = QVBoxLayout(self)
        
        # Encabezado con el código del presupuesto
        header_label = QLabel(f"Recursos asociados al presupuesto: {codigo_presupuesto}")
        header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(header_label)
        
        # Crear formulario para agregar análisis manualmente
        self.create_form()
        # Crear la tabla (QTableView con QStandardItemModel)
        self.create_table()
        # Se deja la función load_data vacía, ya que la invoca el controlador
        # (aquí solo se define la interfaz)
        
        # Botones adicionales (por ejemplo, para abrir selector o actualizar)
        self.setup_buttons()
        
        self.setLayout(self.layout)
        self.setStyleSheet("""
            QTableView {
                background-color: #f9f9f9;
                alternate-background-color: #e0e0e0;
                gridline-color: #cccccc;
            }
            QHeaderView::section {
                background-color: #0078d7;
                color: white;
                padding: 4px; 
                font-weight: bold;
            }
            QPushButton {
                background-color: #007ACC;
                color: white;
                border-radius: 4px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #005A9E;
            }
            QLineEdit {
                padding: 4px;
                border: 1px solid #cccccc;
                border-radius: 4px;
            }
        """)
    
    def create_form(self):
        """Crea el formulario para agregar un nuevo análisis manualmente."""
        self.form_layout = QHBoxLayout()
        self.codigo_analisis_input = QLineEdit()
        self.codigo_analisis_input.setPlaceholderText("Código Análisis")
        self.descripcion_input = QLineEdit()
        self.descripcion_input.setPlaceholderText("Descripción Análisis")
        self.unidad_input = QLineEdit()
        self.unidad_input.setPlaceholderText("Unidad Análisis")
        self.cantidad_input = QLineEdit()
        self.cantidad_input.setPlaceholderText("Cantidad Análisis")
        self.vr_unitario_input = QLineEdit()
        self.vr_unitario_input.setPlaceholderText("Valor Unitario")
        self.vr_parcial_input = QLineEdit()
        self.vr_parcial_input.setPlaceholderText("Valor Parcial")
        self.add_form_button = QPushButton("Agregar a Tabla")
        

        self.form_layout.addWidget(QLabel("Código Análisis:"))
        self.form_layout.addWidget(self.codigo_analisis_input)
        self.form_layout.addWidget(QLabel("Descripción:"))
        self.form_layout.addWidget(self.descripcion_input)
        self.form_layout.addWidget(QLabel("Unidad:"))
        self.form_layout.addWidget(self.unidad_input)
        self.form_layout.addWidget(QLabel("Cantidad:"))
        self.form_layout.addWidget(self.cantidad_input)
        self.form_layout.addWidget(QLabel("Valor Unitario:"))
        self.form_layout.addWidget(self.vr_unitario_input)
        self.form_layout.addWidget(QLabel("Valor Parcial:"))
        self.form_layout.addWidget(self.vr_parcial_input)
        self.form_layout.addWidget(self.add_form_button)
        
        self.layout.addLayout(self.form_layout)
        # Nota: La conexión del botón se hará en el controlador para incluir lógica adicional
        # (pero también puede conectarse aquí si se prefiere, en este ejemplo se conecta en el controlador).
    
    def create_table(self):
        """Crea la tabla usando QTableView y QStandardItemModel."""
        self.table = QTableView()
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels([
            "Código Análisis", "Descripción", "Unidad",
            "Cantidad", "Valor Unitario", "Valor Parcial"
        ])
        self.table.setModel(self.model)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        # Habilitar edición en todas las celdas
        from PyQt6.QtWidgets import QAbstractItemView
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.AllEditTriggers)
        self.layout.addWidget(self.table)
        # (Opcional) Conectar doble clic, si se requiere abrir un selector de análisis
        # self.table.doubleClicked.connect(lambda index: self.analisis_selected_por_presupuesto.emit(self.model.item(index.row(), 0).text()))
    
    def setup_buttons(self):
        """Crea botones para abrir el selector y actualizar el presupuesto."""
        self.button_layout = QHBoxLayout()
        self.add_button = QPushButton("Seleccionar Análisis")
        self.update_button = QPushButton("Actualizar Presupuesto")
        self.button_layout.addWidget(self.add_button)
        self.button_layout.addWidget(self.update_button)
        self.layout.addLayout(self.button_layout)
    
    def load_data(self, data):
        """
        Recibe una lista de diccionarios (cada uno con claves:
        'codigo_analisis', 'descripcion_analisis', 'unidad_analisis',
        'cantidad_analisis', 'vr_unitario', 'vr_total').
        """
        self.model.removeRows(0, self.model.rowCount())
        for analisis in data:
            row = [
                QStandardItem(analisis.get("codigo_analisis", analisis.get("codigo_analisis", ""))),
                QStandardItem(analisis.get("descripcion_analisis", analisis.get("descripcion_analisis", ""))),
                QStandardItem(str(analisis.get("unidad_analisis", analisis.get("unidad_analisis", 0)))),
                QStandardItem(str(analisis.get("cantidad_analisis", analisis.get("cantidad_analisis", 0)))),
                QStandardItem(str(analisis.get("vr_unitario", 0))),
                QStandardItem(str(analisis.get("vr_total", 0))),
            ]
            self.model.appendRow(row)
