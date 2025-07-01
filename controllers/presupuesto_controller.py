from PyQt6.QtCore import QObject, Qt
from PyQt6.QtWidgets import QMessageBox
from models.analisis_unitario import AnalisisUnitario
from models.database import SessionLocal
from views.presupuesto_view import PresupuestoView
from controllers.recursos_por_analisis_controller import RecursosPorAnalisisController

class PresupuestoController(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.view = PresupuestoView()
        self.recursos_controller = None  # Para mantener una referencia
        # Conexiones
        self.view.analisis_selected.connect(self.on_analisis_selected)
        self.view.analysis_edit_requested.connect(self.on_edit_analysis_in_presupuesto)
        print("PresupuestoController initialized")

    def show(self):
        """Muestra la ventana de presupuestos."""
        self.view.show()

    def agregar_analisis(self, analisis_data):
        """
        Agrega un análisis unitario a la tabla del presupuesto.
        No guarda en base de datos, solo en la tabla.
        """
        self.view.add_analisis(analisis_data)

    def on_analisis_selected(self, codigo):
        """
        Cuando se selecciona un análisis unitario, obtiene sus datos
        de la base de datos y lo agrega a la tabla.
        """
        session = SessionLocal()
        try:
            analisis = session.query(AnalisisUnitario).filter(AnalisisUnitario.codigo == codigo).first()
            if analisis:
                analisis_data = {
                    'codigo': analisis.codigo,
                    'descripcion': analisis.descripcion,
                    'unidad': analisis.unidad,
                    'costo_unitario': analisis.total_calculado,
                    'cantidad': 1  # Valor por defecto
                }
                self.agregar_analisis(analisis_data)
            else:
                QMessageBox.warning(self.view, "Error", f"No se encontró el análisis unitario con código {codigo}")
        except Exception as e:
            QMessageBox.critical(self.view, "Error", f"Error al obtener el análisis: {str(e)}")
        finally:
            session.close()

    def on_edit_analysis_in_presupuesto(self, analisis_code):
        """Abre el editor de recursos y conecta la señal para actualizar el presupuesto."""
        self.recursos_controller = RecursosPorAnalisisController(analisis_code)
        self.recursos_controller.analysis_updated.connect(
            lambda: self.update_presupuesto_row(analisis_code)
        )
        self.recursos_controller.view.show()

    def update_presupuesto_row(self, analisis_code):
        """Actualiza la fila del presupuesto con el nuevo costo del análisis."""
        session = SessionLocal()
        try:
            analisis = session.query(AnalisisUnitario).filter_by(codigo=analisis_code).first()
            if not analisis:
                return

            new_costo_unitario = analisis.total_calculado
            # Busca la fila en la tabla del presupuesto y la actualiza
            for row in range(self.view.table.rowCount()):
                item = self.view.table.item(row, 0)
                if item and item.data(Qt.ItemDataRole.UserRole) == analisis_code:
                    # Actualizar el costo unitario
                    costo_item = self.view.table.item(row, 4)
                    if costo_item:
                        costo_item.setText(f"${new_costo_unitario:,.2f}")
                    
                    # Actualizar el total de la fila
                    self.view.update_row_total(row)
                    
                    # Actualizar totales generales
                    self.view.update_total_presupuesto()
                    break
        finally:
            session.close()

    def load_analisis(self, analisis_list):
        """
        Carga una lista de análisis unitarios en la tabla del presupuesto.
        """
        self.view.load_analisis(analisis_list)

    def on_data_changed(self, item):
        """
        Se llama cada vez que el usuario edita una celda.
        Actualiza el registro correspondiente en la memoria y luego recarga la vista.
        """
        row = item.row()
        codigo_item = self.view.table.item(row, 0)
        if not codigo_item:
            return

        codigo = codigo_item.text()
        descripcion = self.view.table.item(row, 1).text() if self.view.table.item(row, 1) else ""
        try:
            costo_unitario = float(self.view.table.item(row, 3).text()) if self.view.table.item(row, 3) else 0.0
        except ValueError:
            costo_unitario = 0.0

        # Volver a cargar todos los análisis para refrescar la vista.
        self.view.load_analisis([{'codigo': codigo, 'descripcion': descripcion, 'costo_unitario': costo_unitario}])

    def on_presupuesto_selected(self, codigo):
        # Lógica al seleccionar un presupuesto, por ejemplo, abrir otra vista de recursos asociados.
        print(f"Presupuesto seleccionado: {codigo}")
