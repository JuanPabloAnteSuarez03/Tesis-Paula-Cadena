from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QPushButton, QLineEdit, QLabel, QMessageBox, QFileDialog
)
from PyQt6.QtCore import Qt, pyqtSignal
from controllers.analisis_unitarios_controller import AnalisisUnitariosController
import csv

class PresupuestoView(QWidget):
    analisis_selected = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Presupuesto")
        self.resize(1000, 600)
        self.layout = QVBoxLayout(self)
        
        # Crear el buscador de análisis
        self.create_search_bar()
        self.create_buttons()
        self.create_table()
        
        # Crear y configurar el controlador de análisis
        self.analisis_controller = None
        
        self.setLayout(self.layout)
        self.setStyleSheet("""
            QTableWidget {
                background-color: #f9f9f9;
                gridline-color: #cccccc;
                font-size: 14px;
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
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #005A9E;
            }
            QLineEdit {
                padding: 6px;
                border: 1px solid #cccccc;
                border-radius: 4px;
                min-width: 200px;
            }
        """)

    def create_search_bar(self):
        """Crea la barra de búsqueda de análisis unitarios."""
        search_layout = QHBoxLayout()
        
        # Campo de búsqueda por código
        self.codigo_search = QLineEdit()
        self.codigo_search.setPlaceholderText("Buscar por código")
        
        # Campo de búsqueda por descripción
        self.descripcion_search = QLineEdit()
        self.descripcion_search.setPlaceholderText("Buscar por descripción")
        
        # Botón de búsqueda
        self.search_button = QPushButton("Buscar Análisis")
        self.search_button.clicked.connect(self.show_analisis_search)
        
        # Agregar widgets al layout
        search_layout.addWidget(QLabel("Código:"))
        search_layout.addWidget(self.codigo_search)
        search_layout.addWidget(QLabel("Descripción:"))
        search_layout.addWidget(self.descripcion_search)
        search_layout.addWidget(self.search_button)
        search_layout.addStretch()
        
        self.layout.addLayout(search_layout)

    def show_analisis_search(self):
        """Muestra la ventana de búsqueda de análisis unitarios."""
        if not self.analisis_controller:
            self.analisis_controller = AnalisisUnitariosController()
            # Conectar la señal de selección de análisis
            self.analisis_controller.view.analysis_selected.connect(self.on_analisis_selected_from_search)
        
        # Obtener valores de los campos de búsqueda
        codigo = self.codigo_search.text().strip()
        descripcion = self.descripcion_search.text().strip()
        
        # Desconectar temporalmente los eventos de cambio de texto para evitar interferencias
        try:
            self.analisis_controller.view.search_code_input.textChanged.disconnect()
            self.analisis_controller.view.search_desc_input.textChanged.disconnect()
        except:
            pass  # Si no estaban conectadas, ignorar el error
        
        # Limpiar y establecer los valores en campos separados
        self.analisis_controller.view.search_code_input.clear()
        self.analisis_controller.view.search_desc_input.clear()
        
        if codigo:
            self.analisis_controller.view.search_code_input.setText(codigo)
        if descripcion:
            self.analisis_controller.view.search_desc_input.setText(descripcion)
        
        # Reconectar los eventos
        self.analisis_controller.view.search_code_input.textChanged.connect(
            self.analisis_controller.view.apply_filters)
        self.analisis_controller.view.search_desc_input.textChanged.connect(
            self.analisis_controller.view.apply_filters)
        
        # Aplicar filtros manualmente
        self.analisis_controller.view.apply_filters()
        
        # Mostrar la ventana
        self.analisis_controller.view.show()

    def on_analisis_selected_from_search(self, codigo):
        """Maneja la selección de un análisis desde la ventana de búsqueda."""
        self.analisis_selected.emit(codigo)
        if self.analisis_controller:
            self.analisis_controller.view.hide()

    def create_buttons(self):
        """Crea los botones para importar/exportar CSV."""
        button_layout = QHBoxLayout()
        
        self.import_button = QPushButton("Importar CSV")
        self.export_button = QPushButton("Exportar CSV")
        
        self.import_button.clicked.connect(self.import_csv)
        self.export_button.clicked.connect(self.export_csv)
        
        button_layout.addWidget(self.import_button)
        button_layout.addWidget(self.export_button)
        button_layout.addStretch()
        
        self.layout.addLayout(button_layout)
    
    def create_table(self):
        """Crea la tabla para mostrar los análisis unitarios del presupuesto."""
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Código", "Item", "Descripción", "Unidad", 
            "Cantidad", "Costo Unitario", "Costo Total"
        ])
        
        # Configurar el ancho de las columnas
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Código
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Item
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)          # Descripción
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Unidad
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Cantidad
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # Costo Unitario
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)  # Costo Total
        
        self.layout.addWidget(self.table)
        
        # Agregar fila para el total
        self.total_label = QLabel("Total del Presupuesto: $0.00")
        self.total_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.total_label.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
        self.layout.addWidget(self.total_label)
        
        # Conectar el evento de cambio de celda
        self.table.itemChanged.connect(self.on_cell_changed)

    def add_analisis(self, analisis_data):
        """Agrega un análisis unitario a la tabla."""
        row = self.table.rowCount()
        self.table.insertRow(row)
        
        # Crear y configurar todos los QTableWidgetItem primero
        items = []
        for col in range(7):
            item = QTableWidgetItem()
            if col != 4:  # La columna 4 es "Cantidad"
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            items.append(item)
            self.table.setItem(row, col, item)
        
        # Establecer los valores
        items[0].setText(analisis_data['codigo'])
        items[1].setText(str(row + 1))
        items[2].setText(analisis_data['descripcion'])
        items[3].setText(analisis_data['unidad'])
        items[4].setText('1')  # Cantidad por defecto
        items[5].setText(f"{analisis_data['costo_unitario']:.2f}")
        items[6].setText('0.00')  # Se actualizará con update_row_total
        
        # Actualizar totales
        self.update_row_total(row)
        self.update_total_presupuesto()

    def on_cell_changed(self, item):
        """Maneja los cambios en las celdas de la tabla."""
        if not item or item.column() != 4:  # Solo procesar cambios en la columna cantidad
            return
            
        try:
            text = item.text().strip()
            if not text:  # Si está vacío, establecer en 1
                item.setText('1')
                cantidad = 1.0
            else:
                cantidad = float(text)
                if cantidad < 0:
                    raise ValueError("La cantidad no puede ser negativa")
            
            # Bloquear señales para evitar recursión
            self.table.blockSignals(True)
            self.update_row_total(item.row())
            self.update_total_presupuesto()
            self.table.blockSignals(False)
            
        except ValueError:
            self.table.blockSignals(True)
            item.setText('1')
            self.update_row_total(item.row())
            self.update_total_presupuesto()
            self.table.blockSignals(False)
            QMessageBox.warning(self, "Error", "Por favor ingrese un número válido positivo")

    def update_row_total(self, row):
        """Actualiza el costo total de una fila."""
        try:
            # Asegurarnos de que todos los items existan
            cantidad_item = self.table.item(row, 4)
            costo_item = self.table.item(row, 5)
            total_item = self.table.item(row, 6)
            
            if not all([cantidad_item, costo_item, total_item]):
                return
            
            # Obtener los valores
            cantidad_text = cantidad_item.text().strip()
            costo_text = costo_item.text().strip()
            
            # Convertir a números
            cantidad = float(cantidad_text) if cantidad_text else 1.0
            costo_unitario = float(costo_text) if costo_text else 0.0
            
            # Calcular y establecer el total
            total = cantidad * costo_unitario
            total_item.setText(f"{total:.2f}")
            
        except (ValueError, AttributeError):
            # Si hay algún error, establecer valores por defecto
            if self.table.item(row, 4):
                self.table.item(row, 4).setText('1')
            if self.table.item(row, 6):
                self.table.item(row, 6).setText('0.00')

    def update_total_presupuesto(self):
        """Actualiza el total del presupuesto."""
        total = 0.0
        for row in range(self.table.rowCount()):
            try:
                total += float(self.table.item(row, 6).text())
            except (ValueError, AttributeError):
                continue
        self.total_label.setText(f"Total del Presupuesto: ${total:,.2f}")

    def export_csv(self):
        """Exporta la tabla a un archivo CSV."""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Guardar Presupuesto", "", "CSV Files (*.csv)"
        )
        if filename:
            with open(filename, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                # Escribir encabezados
                headers = []
                for col in range(self.table.columnCount()):
                    headers.append(self.table.horizontalHeaderItem(col).text())
                writer.writerow(headers)
                
                # Escribir datos
                for row in range(self.table.rowCount()):
                    row_data = []
                    for col in range(self.table.columnCount()):
                        item = self.table.item(row, col)
                        row_data.append(item.text() if item else "")
                    writer.writerow(row_data)
                
                # Escribir el total
                writer.writerow([])
                writer.writerow(["Total del Presupuesto", self.total_label.text()])

    def import_csv(self):
        """Importa datos desde un archivo CSV."""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Importar Presupuesto", "", "CSV Files (*.csv)"
        )
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as file:
                    reader = csv.reader(file)
                    # Saltar la fila de encabezados
                    next(reader)
                    
                    # Limpiar tabla actual
                    self.table.setRowCount(0)
                    
                    # Leer datos
                    for row_data in reader:
                        if not row_data or row_data[0] == "Total del Presupuesto":
                            break
                            
                        row = self.table.rowCount()
                        self.table.insertRow(row)
                        
                        for col, value in enumerate(row_data):
                            item = QTableWidgetItem(value)
                            if col != 4:  # La columna 4 es "Cantidad"
                                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                            self.table.setItem(row, col, item)
                    
                    self.update_total_presupuesto()
                    
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al importar el archivo: {str(e)}")
