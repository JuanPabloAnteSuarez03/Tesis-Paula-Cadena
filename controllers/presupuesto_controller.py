from PyQt6.QtCore import QObject
from PyQt6.QtWidgets import QMessageBox
from models.analisis_unitario import AnalisisUnitario
from models.database import SessionLocal
from views.presupuesto_view import PresupuestoView

class PresupuestoController(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.view = PresupuestoView()
        # Conectar la señal de selección de análisis unitario
        self.view.analisis_selected.connect(self.on_analisis_selected)
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
