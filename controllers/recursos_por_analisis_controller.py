# controllers/recursos_por_analisis_controller.py
import traceback
from PyQt6.QtCore import QObject
from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtGui import QStandardItem
from models.analisis_unitario_recurso import AnalisisUnitarioRecurso
from models.analisis_unitario import AnalisisUnitario
from models.database import SessionLocal
from models.recurso import Recurso
from views.recursos_por_analisis_view import RecursosPorAnalisisView

class RecursosPorAnalisisController(QObject):
    def __init__(self, codigo_analisis, parent=None):
        super().__init__(parent)
        self.codigo_analisis = codigo_analisis
        print(f"[DEBUG] Iniciando RecursosPorAnalisisController para análisis: {codigo_analisis}")
        self.view = RecursosPorAnalisisView(codigo_analisis)

        # Conectar botones definidos en la vista
        self.view.add_button.clicked.connect(self.open_resource_selector)
        self.view.update_button.clicked.connect(self.update_analysis)
        # Conectar el botón del formulario manual para agregar fila
        self.view.add_form_button.clicked.connect(self.on_add_form_button_clicked)
        # Conectar la señal del modelo para detectar ediciones (dataChanged)
        self.view.model.dataChanged.connect(self.on_item_changed)
        print("✅ Señal dataChanged conectada correctamente.")

        # Cargar datos iniciales para el análisis
        self.load_recurso_por_analisis()

    def load_recurso_por_analisis(self):
        """Carga desde la BD los recursos asociados al análisis y actualiza la vista."""
        session = SessionLocal()
        try:
            query = session.query(AnalisisUnitarioRecurso).filter_by(
                codigo_analisis=self.codigo_analisis
            ).all()
            data = []
            for r in query:
                data.append({
                    "codigo_recurso": r.codigo_recurso,
                    "descripcion": r.descripcion_recurso,
                    "unidad": r.unidad_recurso,
                    "cantidad": r.cantidad_recurso,
                    "desperdicio": r.desper,
                    "valor_unitario": r.vr_unitario,
                    "valor_parcial": r.vr_parcial
                })
            self.view.load_data(data)
        except Exception as e:
            QMessageBox.critical(self.view, "Error", f"Error al cargar recursos: {e}")
        finally:
            session.close()

    def open_resource_selector(self):
        """Abre un diálogo modal con la vista del selector de recursos."""
        from controllers.resource_controller import ResourceController
        resource_controller = ResourceController()
        dialog = QDialog(self.view)
        dialog.setWindowTitle("Seleccionar Recurso")
        dialog.resize(600, 400)
        layout = QVBoxLayout(dialog)
        layout.addWidget(resource_controller.view)
        dialog.setLayout(layout)
        resource_controller.view.resource_selected.connect(lambda resource: self.on_resource_selected(resource, dialog))
        dialog.exec()

    def on_resource_selected(self, resource_code, dialog):
        """Se dispara al seleccionar un recurso en el selector.
        Consulta la BD para obtener los datos completos y agrega una fila en la tabla."""
        session = SessionLocal()
        try:
            r = session.query(Recurso).filter(Recurso.codigo == resource_code).first()
            if r:
                resource = {
                    "codigo_recurso": r.codigo,
                    "descripcion": r.descripcion,
                    "unidad": r.unidad,
                    "valor_unitario": r.valor_unitario
                }
            else:
                QMessageBox.warning(self.view, "Error", f"No se encontró el recurso con código {resource_code}")
                dialog.reject()
                return
        except Exception as e:
            QMessageBox.critical(self.view, "Error", f"Error al consultar recurso: {e}")
            dialog.reject()
            return
        finally:
            session.close()

        # Agregar el recurso a la tabla con valores predeterminados para cantidad y demás
        row_position = self.view.model.rowCount()
        self.view.model.insertRow(row_position)
        self.view.model.setItem(row_position, 0, QStandardItem(resource.get("codigo_recurso", "")))
        self.view.model.setItem(row_position, 1, QStandardItem(resource.get("descripcion", "")))
        self.view.model.setItem(row_position, 2, QStandardItem(resource.get("unidad", "")))
        self.view.model.setItem(row_position, 3, QStandardItem("0"))
        self.view.model.setItem(row_position, 4, QStandardItem("0"))
        self.view.model.setItem(row_position, 5, QStandardItem(str(resource.get("valor_unitario", "0"))))
        self.view.model.setItem(row_position, 6, QStandardItem("0"))
        dialog.accept()

    def on_add_form_button_clicked(self):
        """
        Se ejecuta al presionar el botón 'Agregar a Tabla' del formulario.
        (La vista ya inserta la fila en el modelo, aquí podemos agregar lógica extra si se requiere.)
        """
        print("[DEBUG] Botón 'Agregar a Tabla' presionado (desde el formulario).")
        # Si es necesario, aquí se pueden obtener datos del formulario y realizar validaciones o guardarlos en BD
        # En este ejemplo, asumimos que la vista ya actualizó el modelo.

    def update_analysis(self):
        """
        Recorre el modelo, elimina los registros actuales de este análisis en la BD,
        inserta los datos actuales del modelo y recalcula el total del análisis.
        """
        session = SessionLocal()
        try:
            # Borrar registros actuales para este análisis
            session.query(AnalisisUnitarioRecurso).filter_by(
                codigo_analisis=self.codigo_analisis
            ).delete()

            total_actualizado = 0.0
            row_count = self.view.model.rowCount()
            for row in range(row_count):
                codigo_recurso = self.view.model.item(row, 0).text().strip()
                descripcion = self.view.model.item(row, 1).text().strip()
                unidad = self.view.model.item(row, 2).text().strip()
                try:
                    cantidad = float(self.view.model.item(row, 3).text())
                except Exception:
                    cantidad = 0.0
                try:
                    desperdicio = float(self.view.model.item(row, 4).text())
                except Exception:
                    desperdicio = 0.0
                try:
                    vr_unitario = float(self.view.model.item(row, 5).text())
                except Exception:
                    vr_unitario = 0.0
                try:
                    vr_parcial = float(self.view.model.item(row, 6).text())
                except Exception:
                    vr_parcial = 0.0

                total_actualizado += vr_parcial

                nuevo = AnalisisUnitarioRecurso(
                    codigo_analisis=self.codigo_analisis,
                    codigo_recurso=codigo_recurso,
                    descripcion_recurso=descripcion,
                    unidad_recurso=unidad,
                    cantidad_recurso=cantidad,
                    desper=desperdicio,
                    vr_unitario=vr_unitario,
                    vr_parcial=vr_parcial
                )
                session.add(nuevo)

            # Actualizar el total del análisis unitario
            analisis = session.query(AnalisisUnitario).filter_by(codigo=self.codigo_analisis).first()
            if analisis:
                analisis.total = total_actualizado
                print(f"[DEBUG] Nuevo total del análisis {self.codigo_analisis}: {total_actualizado}")

            session.commit()
            QMessageBox.information(self.view, "Actualización Exitosa",
                                    f"Análisis {self.codigo_analisis} actualizado.\nNuevo Total: {total_actualizado:.2f}")
        except Exception as e:
            session.rollback()
            QMessageBox.critical(self.view, "Error", f"Error al actualizar análisis: {e}")
            traceback.print_exc()
        finally:
            session.close()
            self.load_recurso_por_analisis()

    def on_item_changed(self, topLeft, bottomRight, roles):
        """
        Se dispara cuando se edita una celda del modelo.
        Actualiza en la BD el registro correspondiente a esa fila.
        Asumimos que se edita una celda a la vez.
        """
        row = topLeft.row()
        session = SessionLocal()
        try:
            codigo_item = self.view.model.item(row, 0)
            if not codigo_item:
                return
            codigo = codigo_item.text().strip()
            recurso = session.query(AnalisisUnitarioRecurso).filter_by(
                codigo_analisis=self.codigo_analisis,
                codigo_recurso=codigo
            ).first()
            if not recurso:
                print(f"[DEBUG] Recurso {codigo} no encontrado en la BD (on_item_changed).")
                return

            col = topLeft.column()
            new_value = self.view.model.item(row, col).text().strip()
            if col == 3:  # Cantidad
                recurso.cantidad_recurso = float(new_value) if new_value else 0.0
            elif col == 4:  # Desperdicio
                recurso.desper = float(new_value) if new_value else 0.0
            elif col == 5:  # Valor Unitario
                recurso.vr_unitario = float(new_value) if new_value else 0.0
            # No se modifica vr_parcial; se calcula automáticamente con el híbrido

            session.commit()
            print(f"[DEBUG] on_item_changed: Recurso {codigo} actualizado. Nuevo vr_parcial: {recurso.vr_parcial}")
        except Exception as e:
            session.rollback()
            print(f"[ERROR] on_item_changed para {codigo}: {e}")
        finally:
            session.close()
