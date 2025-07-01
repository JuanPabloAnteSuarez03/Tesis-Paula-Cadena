from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QPushButton, QLineEdit, QLabel, QMessageBox, QFileDialog,
    QInputDialog, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont
from controllers.analisis_unitarios_controller import AnalisisUnitariosController
import csv

class PresupuestoView(QWidget):
    analisis_selected = pyqtSignal(str)
    analysis_edit_requested = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Presupuesto")
        self.resize(1000, 600)
        self.layout = QVBoxLayout(self)
        self.chapter_counter = 0
        
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
        """Crea los botones para importar/exportar CSV y capítulos."""
        button_layout = QHBoxLayout()
        button_layout.addStretch(1)
        
        self.add_chapter_button = QPushButton("Agregar Capítulo")
        self.edit_chapter_button = QPushButton("Editar Capítulo")
        self.delete_chapter_button = QPushButton("Eliminar Capítulo")
        self.import_button = QPushButton("Importar CSV")
        self.export_button = QPushButton("Exportar CSV")
        self.delete_row_button = QPushButton("Eliminar Fila")
        
        self.add_chapter_button.clicked.connect(self.prompt_add_chapter)
        self.edit_chapter_button.clicked.connect(self.prompt_edit_chapter)
        self.delete_chapter_button.clicked.connect(self.prompt_delete_chapter)
        self.import_button.clicked.connect(self.import_csv)
        self.export_button.clicked.connect(self.export_csv)
        self.delete_row_button.clicked.connect(self.delete_selected_row)
        
        button_layout.addWidget(self.add_chapter_button)
        button_layout.addWidget(self.edit_chapter_button)
        button_layout.addWidget(self.delete_chapter_button)
        button_layout.addWidget(self.import_button)
        button_layout.addWidget(self.export_button)
        button_layout.addWidget(self.delete_row_button)
        button_layout.addStretch(1)
        
        self.layout.addLayout(button_layout)

    def prompt_add_chapter(self):
        """Pide al usuario el nombre del capítulo y lo agrega."""
        text, ok = QInputDialog.getText(self, 'Agregar Capítulo', 'Nombre del capítulo:')
        if ok and text:
            self.add_chapter_row(text)

    def prompt_edit_chapter(self):
        """Permite editar el nombre del capítulo seleccionado."""
        selected_items = self.table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Advertencia", "Por favor, seleccione un capítulo para editar.")
            return
        
        # Obtener la fila seleccionada
        row = selected_items[0].row()
        item = self.table.item(row, 0)
        
        # Verificar que sea un capítulo
        if not item or item.data(Qt.ItemDataRole.UserRole) != 'chapter':
            QMessageBox.warning(self, "Advertencia", "Por favor, seleccione una fila de capítulo para editar.")
            return
        
        # Extraer el nombre actual del capítulo (sin el número)
        current_text = item.text()
        try:
            current_name = current_text.split('.', 1)[1].strip()
        except IndexError:
            current_name = current_text
        
        # Pedir el nuevo nombre
        new_name, ok = QInputDialog.getText(
            self, 
            'Editar Capítulo', 
            'Nuevo nombre del capítulo:',
            text=current_name
        )
        
        if ok and new_name.strip():
            # Actualizar el nombre del capítulo
            chapter_number = item.data(Qt.ItemDataRole.UserRole + 1)
            if chapter_number:
                item.setText(f"{chapter_number}. {new_name.strip().upper()}")
            else:
                item.setText(new_name.strip().upper())
            
            QMessageBox.information(self, "Capítulo actualizado", "El nombre del capítulo ha sido actualizado correctamente.")

    def prompt_delete_chapter(self):
        """Elimina el capítulo seleccionado junto con todos sus análisis asociados."""
        selected_items = self.table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Advertencia", "Por favor, seleccione un capítulo para eliminar.")
            return
        
        # Obtener la fila seleccionada
        row = selected_items[0].row()
        item = self.table.item(row, 0)
        
        # Verificar que sea un capítulo
        if not item or item.data(Qt.ItemDataRole.UserRole) != 'chapter':
            QMessageBox.warning(self, "Advertencia", "Por favor, seleccione una fila de capítulo para eliminar.")
            return
        
        # Extraer el nombre del capítulo
        chapter_name = item.text()
        
        # Contar cuántos análisis tiene el capítulo
        analysis_count = 0
        chapter_end_row = self.table.rowCount()
        
        # Buscar el final del capítulo
        for i in range(row + 1, self.table.rowCount()):
            next_item = self.table.item(i, 0)
            if next_item:
                if next_item.data(Qt.ItemDataRole.UserRole) == 'chapter':
                    chapter_end_row = i
                    break
                elif next_item.data(Qt.ItemDataRole.UserRole) not in ['subtotal']:
                    analysis_count += 1
        
        # Pedir confirmación
        if analysis_count > 0:
            confirmacion = QMessageBox.question(
                self,
                "Confirmar eliminación de capítulo",
                f"¿Está seguro de eliminar el capítulo '{chapter_name}' y todos sus {analysis_count} análisis asociados?\n\n"
                f"Esta acción no se puede deshacer.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
        else:
            confirmacion = QMessageBox.question(
                self,
                "Confirmar eliminación de capítulo",
                f"¿Está seguro de eliminar el capítulo '{chapter_name}'?\n\n"
                f"Este capítulo no tiene análisis asociados.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
        
        if confirmacion == QMessageBox.StandardButton.Yes:
            # Eliminar todas las filas del capítulo (desde el final hacia el principio)
            rows_to_delete = []
            
            # Recopilar todas las filas que pertenecen al capítulo
            for i in range(row, chapter_end_row):
                if i < self.table.rowCount():
                    rows_to_delete.append(i)
            
            # Eliminar las filas desde el final hacia el principio para no afectar los índices
            for delete_row in reversed(rows_to_delete):
                if delete_row < self.table.rowCount():
                    self.table.removeRow(delete_row)
            
            # Renumerar y actualizar totales
            self.rebuild_table()
            
            if analysis_count > 0:
                QMessageBox.information(
                    self, 
                    "Capítulo eliminado", 
                    f"El capítulo '{chapter_name}' y sus {analysis_count} análisis han sido eliminados correctamente."
                )
            else:
                QMessageBox.information(
                    self, 
                    "Capítulo eliminado", 
                    f"El capítulo '{chapter_name}' ha sido eliminado correctamente."
                )

    def add_chapter_row(self, chapter_name, trigger_rebuild=True):
        """Agrega una fila de capítulo al final de la tabla.
        Si trigger_rebuild es False, no ejecuta la reconstrucción completa (útil durante importaciones masivas)."""
        row = self.table.rowCount()
        self.table.insertRow(row)
        
        item = QTableWidgetItem(chapter_name.upper())  # El número se asignará al renumerar
        item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)  # No editable
        
        # Estilo para el capítulo
        font = QFont()
        font.setBold(True)
        item.setFont(font)
        item.setBackground(QColor("#e0e0e0"))
        item.setData(Qt.ItemDataRole.UserRole, 'chapter')
        item.setData(Qt.ItemDataRole.UserRole + 1, 0)  # El número se asignará al renumerar

        self.table.setItem(row, 0, item)
        self.table.setSpan(row, 0, 1, self.table.columnCount())
        
        # Solo reconstruir inmediatamente si no estamos importando en bloque
        if trigger_rebuild:
            self.rebuild_table()

    def delete_selected_row(self):
        """Elimina la fila seleccionada del presupuesto."""
        selected_items = self.table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Advertencia", "Por favor, seleccione una fila para eliminar.")
            return
        
        # Obtener la fila seleccionada (tomamos el primer ítem seleccionado)
        row = selected_items[0].row()
        
        # Verificar el tipo de fila seleccionada
        codigo_item = self.table.item(row, 0)
        if codigo_item:
            user_role = codigo_item.data(Qt.ItemDataRole.UserRole)
            
            # Bloquear eliminación de capítulos
            if user_role == 'chapter':
                QMessageBox.warning(
                    self, 
                    "Operación no permitida", 
                    "No se puede eliminar un capítulo usando 'Eliminar Fila'.\n\n"
                    "Use el botón 'Eliminar Capítulo' para eliminar capítulos completos."
                )
                return
            
            # Bloquear eliminación de subtotales
            if user_role == 'subtotal':
                QMessageBox.warning(
                    self, 
                    "Operación no permitida", 
                    "No se puede eliminar un subtotal.\n\n"
                    "Los subtotales se calculan automáticamente."
                )
                return
            
            # Solo permitir eliminación de análisis individuales
            codigo = codigo_item.text()
            descripcion_item = self.table.item(row, 1)
            descripcion = descripcion_item.text() if descripcion_item else ""
            
            confirmacion = QMessageBox.question(
                self,
                "Confirmar eliminación",
                f"¿Está seguro de eliminar el análisis '{codigo} - {descripcion}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if confirmacion == QMessageBox.StandardButton.Yes:
                self.table.removeRow(row)
                self.rebuild_table()
                QMessageBox.information(self, "Eliminado", "El análisis ha sido eliminado correctamente.")
        else:
            QMessageBox.warning(self, "Error", "No se puede determinar el tipo de fila seleccionada.")

    def create_table(self):
        """Crea la tabla para mostrar los análisis unitarios del presupuesto."""
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Item", "Descripción", "Unidad", 
            "Cantidad", "Costo Unitario", "Costo Total"
        ])
        
        # Configurar el ancho de las columnas
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Item
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)          # Descripción
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Unidad
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Cantidad
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Costo Unitario
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # Costo Total
        
        self.layout.addWidget(self.table)
        
        # Agregar fila para el total
        self.total_label = QLabel("Total del Presupuesto: $0.00")
        self.total_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.total_label.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
        self.layout.addWidget(self.total_label)
        
        # Conectar el evento de cambio de celda
        self.table.itemChanged.connect(self.on_cell_changed)
        self.table.cellClicked.connect(self.on_cell_clicked)

    def on_cell_clicked(self, row, column):
        """Maneja los clics en las celdas, detectando Shift+Click para editar."""
        modifiers = QApplication.keyboardModifiers()
        if modifiers == Qt.KeyboardModifier.ShiftModifier:
            item = self.table.item(row, 0)  # El código del análisis está en la data del item
            if item and item.data(Qt.ItemDataRole.UserRole) not in ['chapter', 'subtotal']:
                analisis_code = item.data(Qt.ItemDataRole.UserRole)
                if analisis_code:
                    self.analysis_edit_requested.emit(analisis_code)

    def add_analisis(self, analisis_data):
        """Agrega un análisis unitario a la tabla bajo el capítulo seleccionado o el último."""
        
        # Verificar que los datos del análisis estén completos
        required_fields = ['codigo', 'descripcion', 'unidad', 'costo_unitario']
        for field in required_fields:
            if field not in analisis_data:
                QMessageBox.warning(self, "Error", f"Datos incompletos del análisis: falta {field}")
                return
        
        # Determinar el capítulo y la posición de inserción
        target_chapter_row = -1
        
        current_row = self.table.currentRow()
        if current_row == -1: # Nada seleccionado, usar el último capítulo
            start_row = self.table.rowCount() - 1
        else:
            start_row = current_row

        # Buscar hacia atrás el capítulo al que pertenece la selección
        for i in range(start_row, -1, -1):
            item = self.table.item(i, 0)
            if item and item.data(Qt.ItemDataRole.UserRole) == 'chapter':
                target_chapter_row = i
                break
                
        if target_chapter_row == -1:
            QMessageBox.warning(self, "Advertencia", "Por favor, agregue un capítulo antes de añadir un análisis.")
            return

        # Encontrar el final del capítulo para insertar la nueva fila
        insertion_row = self.table.rowCount() # Por defecto, al final
        for i in range(target_chapter_row + 1, self.table.rowCount()):
            item = self.table.item(i, 0)
            if item:
                # Si encontramos otro capítulo, insertar antes de él
                if item.data(Qt.ItemDataRole.UserRole) == 'chapter':
                    insertion_row = i
                    break
                # Si encontramos un subtotal, insertar antes de él (final del capítulo actual)
                elif item.data(Qt.ItemDataRole.UserRole) == 'subtotal':
                    insertion_row = i
                    break

        # Insertar la nueva fila
        self.table.insertRow(insertion_row)
        
        # Crear y configurar todos los QTableWidgetItem primero
        items = []
        for col in range(6):
            item = QTableWidgetItem()
            if col != 3:  # La columna 3 es "Cantidad"
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            items.append(item)
            self.table.setItem(insertion_row, col, item)
        
        # Establecer los valores
        items[0].setText("...") # Temporal, se renumerará
        items[0].setData(Qt.ItemDataRole.UserRole, analisis_data['codigo']) # Guardar código original
        
        descripcion = analisis_data['descripcion']
        items[1].setText(descripcion)
        items[1].setToolTip(descripcion)
        
        items[2].setText(analisis_data['unidad'])
        items[3].setText('1')  # Cantidad por defecto
        
        # Establecer el costo unitario asegurándose de que sea un número válido
        try:
            costo_unitario = float(analisis_data['costo_unitario'])
            items[4].setText(f"${costo_unitario:,.2f}")
        except (ValueError, TypeError):
            items[4].setText("$0.00")
        
        # El total se calculará automáticamente
        items[5].setText('$0.00')
        
        # Renumerar todo y actualizar totales
        self.renumber_items()
        self.update_row_total(insertion_row)
        self.update_total_presupuesto()

    def on_cell_changed(self, item):
        """Maneja los cambios en las celdas de la tabla."""
        if not item or item.column() != 3:  # Solo procesar cambios en la columna cantidad
            return
        
        # Guardar la fila antes de cualquier procesamiento que pueda invalidar el item
        row = item.row()
        
        # Verificar que el item sigue siendo válido
        try:
            text = item.text().strip()
        except RuntimeError:
            # El item ha sido eliminado, salir sin procesar
            return
            
        try:
            if not text:  # Si está vacío, establecer en 1
                # Verificar que el item sigue siendo válido antes de modificarlo
                try:
                    item.setText('1')
                except RuntimeError:
                    return
                cantidad = 1.0
            else:
                cantidad = float(text)
                if cantidad < 0:
                    raise ValueError("La cantidad no puede ser negativa")
            
            # Bloquear señales para evitar recursión
            self.table.blockSignals(True)
            
            # Verificar que la fila sigue siendo válida después de bloquear señales
            if row < self.table.rowCount():
                self.update_row_total(row)
                self.update_total_presupuesto()
            
            self.table.blockSignals(False)
            
        except ValueError:
            self.table.blockSignals(True)
            
            # Verificar que el item sigue siendo válido antes de modificarlo
            try:
                item.setText('1')
                if row < self.table.rowCount():
                    self.update_row_total(row)
                    self.update_total_presupuesto()
            except RuntimeError:
                pass  # El item ha sido eliminado, no hacer nada
            
            self.table.blockSignals(False)
            QMessageBox.warning(self, "Error", "Por favor ingrese un número válido positivo")

    def update_row_total(self, row):
        """Actualiza el costo total de una fila basado en la cantidad y el costo unitario."""
        # Verificar que la fila existe
        if row < 0 or row >= self.table.rowCount():
            return
            
        try:
            cantidad_item = self.table.item(row, 3)
            costo_unitario_item = self.table.item(row, 4)
            
            if not cantidad_item or not costo_unitario_item:
                return

            # Obtener los valores
            cantidad_text = cantidad_item.text().replace(',', '').strip()
            costo_text = costo_unitario_item.text().replace('$', '').replace(',', '').strip()
            
            # Convertir a números, usar valores por defecto si hay error
            cantidad = float(cantidad_text) if cantidad_text else 1.0
            costo_unitario = float(costo_text) if costo_text else 0.0
            
            total = cantidad * costo_unitario
            
            # Actualizar el total
            total_item = self.table.item(row, 5)
            if not total_item:
                total_item = QTableWidgetItem()
                self.table.setItem(row, 5, total_item)
            
            total_item.setText(f"${total:,.2f}")
                
        except (ValueError, TypeError, RuntimeError):
            # Si hay cualquier error, establecer como Error
            try:
                total_item = self.table.item(row, 5)
                if not total_item:
                    total_item = QTableWidgetItem()
                    self.table.setItem(row, 5, total_item)
                total_item.setText("Error")
            except (RuntimeError, IndexError):
                pass  # Si no se puede ni siquiera crear el item, ignorar

    def update_total_presupuesto(self):
        """Recalcula y actualiza el costo total del presupuesto y los subtotales por capítulo."""
        # Bloquear señales para evitar llamadas recursivas
        self.table.blockSignals(True)
        
        try:
            # Primero, eliminar todas las filas de subtotal existentes
            self.remove_subtotal_rows()
            
            # Recopilar información sobre capítulos y calcular subtotales
            total_presupuesto = 0.0
            current_chapter_start = -1
            current_chapter_total = 0.0
            rows_to_insert_subtotals = []
            
            row = 0
            while row < self.table.rowCount():
                item = self.table.item(row, 0)
                
                if item and item.data(Qt.ItemDataRole.UserRole) == 'chapter':
                    # Si había un capítulo anterior, guardar su información para insertar subtotal
                    if current_chapter_start != -1 and current_chapter_total > 0:
                        rows_to_insert_subtotals.append({
                            'position': row,
                            'total': current_chapter_total
                        })
                    
                    # Iniciar nuevo capítulo
                    current_chapter_start = row
                    current_chapter_total = 0.0
                    
                elif item and item.data(Qt.ItemDataRole.UserRole) not in ['chapter', 'subtotal']:
                    # Es una fila de análisis, calcular su total y sumarlo
                    try:
                        cantidad_item = self.table.item(row, 3)
                        costo_unitario_item = self.table.item(row, 4)
                        
                        if cantidad_item and costo_unitario_item:
                            try:
                                cantidad_text = cantidad_item.text().replace(',', '').strip()
                                costo_text = costo_unitario_item.text().replace('$', '').replace(',', '').strip()
                                
                                # Solo actualizar el total si ya hay un costo unitario
                                if costo_text:  # Solo si hay un costo unitario establecido
                                    cantidad = float(cantidad_text) if cantidad_text else 1.0
                                    costo_unitario = float(costo_text) if costo_text else 0.0
                                    
                                    total_fila = cantidad * costo_unitario
                                    
                                    # Actualizar el total de la fila
                                    total_item = self.table.item(row, 5)
                                    if not total_item:
                                        total_item = QTableWidgetItem()
                                        self.table.setItem(row, 5, total_item)
                                    
                                    total_item.setText(f"${total_fila:,.2f}")
                                    
                                    # Sumarlo al capítulo actual y al total general
                                    current_chapter_total += total_fila
                                    total_presupuesto += total_fila
                                
                            except (ValueError, RuntimeError):
                                # Error en conversión, marcar como error pero continuar
                                total_item = self.table.item(row, 5)
                                if not total_item:
                                    total_item = QTableWidgetItem()
                                    self.table.setItem(row, 5, total_item)
                                total_item.setText("Error")
                    except (RuntimeError, AttributeError):
                        pass  # Ignorar filas problemáticas
                
                row += 1
            
            # Agregar subtotal para el último capítulo si existe
            if current_chapter_start != -1 and current_chapter_total > 0:
                rows_to_insert_subtotals.append({
                    'position': self.table.rowCount(),
                    'total': current_chapter_total
                })
            
            # Insertar subtotales desde el final hacia el principio para no afectar los índices
            for subtotal_info in reversed(rows_to_insert_subtotals):
                self.insert_subtotal_row(subtotal_info['position'], subtotal_info['total'])
            
            # Actualizar el total del presupuesto
            self.total_label.setText(f"Total del Presupuesto: ${total_presupuesto:,.2f}")
            
        finally:
            # Siempre desbloquear señales
            self.table.blockSignals(False)

    def remove_subtotal_rows(self):
        """Elimina todas las filas de subtotal existentes."""
        rows_to_remove = []
        for row in range(self.table.rowCount()):
            try:
                item = self.table.item(row, 0)
                if item and item.data(Qt.ItemDataRole.UserRole) == 'subtotal':
                    rows_to_remove.append(row)
            except RuntimeError:
                # Item eliminado, omitir
                continue
        
        # Eliminar de abajo hacia arriba para no afectar los índices
        for row in reversed(rows_to_remove):
            try:
                if row < self.table.rowCount():
                    self.table.removeRow(row)
            except (RuntimeError, IndexError):
                # Fila ya eliminada o inválida, continuar
                continue

    def insert_subtotal_row(self, position, subtotal_amount):
        """Inserta una fila de subtotal en la posición especificada."""
        self.table.insertRow(position)
        
        # Crear item de subtotal
        subtotal_item = QTableWidgetItem(f"SUBTOTAL")
        subtotal_item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)  # No editable
        
        # Estilo para el subtotal
        font = QFont()
        font.setBold(True)
        subtotal_item.setFont(font)
        subtotal_item.setBackground(QColor("#f0f0f0"))
        subtotal_item.setData(Qt.ItemDataRole.UserRole, 'subtotal')
        
        self.table.setItem(position, 0, subtotal_item)
        
        # Crear item del valor del subtotal en la columna "Costo Total"
        valor_item = QTableWidgetItem(f"${subtotal_amount:,.2f}")
        valor_item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)  # No editable
        valor_item.setFont(font)
        valor_item.setBackground(QColor("#f0f0f0"))
        self.table.setItem(position, 5, valor_item)
        
        # Crear items vacíos para las otras columnas
        for col in [1, 2, 3, 4]:
            empty_item = QTableWidgetItem("")
            empty_item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)  # No editable
            empty_item.setBackground(QColor("#f0f0f0"))
            self.table.setItem(position, col, empty_item)

    def export_csv(self):
        """Exporta los datos del presupuesto a un archivo CSV sin incluir totales calculados."""
        filePath, _ = QFileDialog.getSaveFileName(self, "Exportar CSV", "", "CSV Files (*.csv)")
        if not filePath:
            return

        with open(filePath, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            
            # Escribir header - sin la columna "Costo Total"
            writer.writerow(['Item', 'Descripción', 'Unidad', 'Cantidad', 'Costo Unitario', 'Código Análisis'])

            for row in range(self.table.rowCount()):
                # Obtener datos de la fila
                item_text = self.table.item(row, 0).text() if self.table.item(row, 0) else ""
                desc_text = self.table.item(row, 1).text() if self.table.item(row, 1) else ""
                
                # Verificar si es una fila de subtotal y omitirla
                if ('SUBTOTAL' in item_text.upper() or 
                    'SUBTOTAL' in desc_text.upper() or
                    (not item_text and not desc_text)):
                    continue
                
                # Escribir datos de la fila
                row_data = []
                for col in range(5):  # Solo las primeras 5 columnas (sin Costo Total)
                    item = self.table.item(row, col)
                    if item:
                        row_data.append(item.text())
                    else:
                        row_data.append("")
                
                # Agregar el código del análisis
                item_with_code = self.table.item(row, 0)
                if item_with_code and item_with_code.data(Qt.ItemDataRole.UserRole):
                    codigo_analisis = item_with_code.data(Qt.ItemDataRole.UserRole)
                else:
                    codigo_analisis = ""
                
                row_data.append(codigo_analisis)
                writer.writerow(row_data)

        QMessageBox.information(self, "Exportado", "El presupuesto ha sido exportado a CSV sin incluir totales calculados.")

    def import_csv(self):
        """Importa datos desde un archivo CSV al presupuesto y calcula automáticamente los totales."""
        filePath, _ = QFileDialog.getOpenFileName(self, "Importar CSV", "", "CSV Files (*.csv)")
        if not filePath:
            return

        self.table.setRowCount(0)
        self.chapter_counter = 0

        # Bloquear señales para evitar procesamientos intermedios (on_cell_changed, etc.)
        self.table.blockSignals(True)

        with open(filePath, 'r', newline='', encoding='utf-8') as file:
            reader = csv.reader(file)
            header = next(reader, None)
            print(f"Header leído: {header}")
            
            total_rows_processed = 0
            analysis_rows_added = 0

            for row_data in reader:
                total_rows_processed += 1
                # Saltar si la fila está vacía o es muy corta
                if not row_data or len(row_data) < 1:
                    continue
                
                print(f"Procesando fila {total_rows_processed}: {row_data}")
                
                # Verificar si es una fila de subtotal (aunque no debería haber)
                is_subtotal = (
                    (row_data[0] and 'SUBTOTAL' in row_data[0].upper()) or
                    (len(row_data) > 1 and row_data[1] and 'SUBTOTAL' in row_data[1].upper())
                )
                
                if is_subtotal:
                    print("  → Omitiendo subtotal")
                    continue
                
                # Si es una fila de capítulo - detectar formato "N. CAP NOMBRE"
                # Usar exactamente la misma lógica que funciona en el script de prueba
                if (row_data[0] and 
                    'CAP' in row_data[0].upper() and 
                    len(row_data) >= 5 and 
                    all(not cell or not cell.strip() for cell in row_data[2:5])):  # Unidad, Cantidad, Costo vacíos
                    
                    print(f"  → Detectado como CAPÍTULO: {row_data[0]}")
                    chapter_text = row_data[0]
                    try:
                        # Extraer nombre del capítulo - formato "1. CAP 1" -> "CAP 1"
                        if '.' in chapter_text and 'CAP' in chapter_text.upper():
                            parts = chapter_text.split('.', 1)
                            if len(parts) > 1:
                                name = parts[1].strip()
                            else:
                                name = chapter_text
                        else:
                            name = chapter_text
                        self.add_chapter_row(name.strip(), trigger_rebuild=False)
                    except (ValueError, IndexError):
                        self.add_chapter_row(chapter_text, trigger_rebuild=False)
                    continue
                
                # Si llegamos aquí, es una fila de análisis
                print(f"  → Procesando como ANÁLISIS")
                
                row = self.table.rowCount()
                self.table.insertRow(row)
                
                # El código del análisis está en la columna 5 (índice 5) según el debug
                analisis_code = row_data[5] if len(row_data) > 5 else None

                # Procesar las primeras 5 columnas (Item, Descripción, Unidad, Cantidad, Costo Unitario)
                for column in range(5):
                    data = row_data[column] if column < len(row_data) else ""
                    item = QTableWidgetItem(str(data) if data else "")
                    
                    # Configurar flags según la columna
                    if column == 3:  # Columna Cantidad - editable
                        item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsEditable)
                    else:  # Otras columnas - no editables
                        item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
                    
                    # Configurar datos específicos por columna
                    if column == 0:  # Columna Item
                        if analisis_code:
                            item.setData(Qt.ItemDataRole.UserRole, analisis_code)
                    elif column == 1:  # Columna Descripción
                        item.setToolTip(str(data) if data else "")
                    elif column == 3:  # Columna Cantidad
                        # Asegurar que siempre haya una cantidad válida
                        try:
                            cantidad = float(str(data).replace(',', '')) if data else 1.0
                            item.setText(str(int(cantidad)) if cantidad == int(cantidad) else str(cantidad))
                        except (ValueError, TypeError):
                            item.setText('1')
                    elif column == 4:  # Columna Costo Unitario
                        try:
                            if data and str(data).strip():
                                # Limpiar el dato y convertir
                                clean_data = str(data).strip().replace('$', '').replace(',', '')
                                if clean_data:
                                    value = float(clean_data)
                                    formatted_cost = f"${value:,.2f}"
                                    item.setText(formatted_cost)
                                    print(f"    Costo procesado: '{data}' -> '{formatted_cost}'")
                                else:
                                    item.setText("$0.00")
                                    print(f"    Costo vacío: '{data}' -> '$0.00'")
                            else:
                                item.setText("$0.00")
                                print(f"    Costo nulo: '{data}' -> '$0.00'")
                        except (ValueError, TypeError) as e:
                            item.setText("$0.00")
                            print(f"    Error en costo: '{data}' -> '$0.00' (Error: {e})")
                    
                    self.table.setItem(row, column, item)
                
                # Crear la celda de Costo Total (columna 5) y calcularla automáticamente
                total_item = QTableWidgetItem()
                total_item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)  # No editable
                self.table.setItem(row, 5, total_item)
                
                # Calcular el total automáticamente
                self.update_row_total(row)
                analysis_rows_added += 1
                print(f"  → Análisis agregado en fila {row} (análisis #{analysis_rows_added})")

        # Reconstruir tabla con subtotales
        print(f"\n=== RESUMEN IMPORTACIÓN ===")
        print(f"Total filas procesadas del CSV: {total_rows_processed}")
        print(f"Análisis agregados a la tabla: {analysis_rows_added}")
        print(f"Filas totales en tabla antes de rebuild: {self.table.rowCount()}")
        
        # Verificar costos unitarios antes del rebuild
        print("\n=== VERIFICACIÓN COSTOS ANTES DE REBUILD ===")
        self._dump_table("DUMP ANTES REBUILD")
        
        self.rebuild_table_safe()
        
        # Desbloquear señales ahora que la importación ha terminado
        self.table.blockSignals(False)
        
        # Verificar costos unitarios después de rebuild
        print("\n=== VERIFICACIÓN COSTOS DESPUÉS DE REBUILD ===")
        self._dump_table("DUMP DESPUÉS REBUILD")
        
        print(f"Filas totales en tabla después de rebuild: {self.table.rowCount()}")
        QMessageBox.information(self, "Importado", f"El presupuesto ha sido importado desde CSV.\nAnálisis importados: {analysis_rows_added}\nTotales calculados automáticamente.")

    def renumber_items(self):
        """Renumera todos los capítulos y los ítems de la tabla, omitiendo subtotales."""
        # Primero, renumerar capítulos
        chapter_count = 0
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item and item.data(Qt.ItemDataRole.UserRole) == 'chapter':
                chapter_count += 1
                try:
                    # Extraer solo el nombre, sin el número anterior
                    name = item.text().split('.', 1)[1].strip()
                except IndexError:
                    name = item.text()
                item.setText(f"{chapter_count}. {name}")
                item.setData(Qt.ItemDataRole.UserRole + 1, chapter_count)
        self.chapter_counter = chapter_count

        # Segundo, renumerar ítems de análisis (omitiendo subtotales)
        current_chapter_number = 0
        item_in_chapter_counter = 0
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if not item:
                continue
                
            if item.data(Qt.ItemDataRole.UserRole) == 'chapter':
                current_chapter_number = item.data(Qt.ItemDataRole.UserRole + 1)
                item_in_chapter_counter = 0  # Reset for new chapter
            elif item.data(Qt.ItemDataRole.UserRole) == 'subtotal':
                # Omitir filas de subtotal
                continue
            else:
                # Es un ítem de análisis
                item_in_chapter_counter += 1
                item.setText(f"{current_chapter_number}.{item_in_chapter_counter}")

    def rebuild_table(self):
        """Reconstruye completamente la tabla eliminando subtotales y recalculando todo."""
        # Bloquear señales durante la reconstrucción
        self.table.blockSignals(True)
        
        try:
            # Renumerar todos los items primero
            self.renumber_items()
            
            # NO recalcular los totales de fila durante la importación
            # Solo calcular los totales si los costos unitarios ya están establecidos
            # Esto evita sobrescribir datos recién importados
            
            # Finalmente, actualizar totales y subtotales
            self.update_total_presupuesto()
            
        finally:
            self.table.blockSignals(False)

    def rebuild_table_safe(self):
        """Versión segura de rebuild que no modifica costos unitarios existentes."""
        # Bloquear señales durante la reconstrucción
        self.table.blockSignals(True)
        
        try:
            # Renumerar todos los items primero
            self.renumber_items()
            
            # Solo actualizar totales y subtotales, sin tocar costos unitarios
            self.update_total_presupuesto()
            
        finally:
            self.table.blockSignals(False)

    # --- MÉTODO AUXILIAR DE DEPURACIÓN ---
    def _dump_table(self, label="DUMP"):
        """Imprime en consola el contenido actual de la tabla (solo columnas clave)."""
        print(f"\n--- {label} ---")
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            desc = self.table.item(row, 1)
            cu = self.table.item(row, 4)
            ct = self.table.item(row, 5)
            if item:
                item_text = item.text()
                cu_text = cu.text() if cu else ""
                ct_text = ct.text() if ct else ""
                print(f"Fila {row:2d} | Item={item_text!r} | CU={cu_text!r} | CT={ct_text!r}")
