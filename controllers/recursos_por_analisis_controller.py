# controllers/recursos_por_analisis_controller.py
import traceback
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from PyQt6.QtWidgets import QMessageBox, QDialog, QVBoxLayout, QPushButton
from PyQt6.QtGui import QStandardItem
from models.analisis_unitario_recurso import AnalisisUnitarioRecurso
from models.analisis_unitario import AnalisisUnitario
from models.database import SessionLocal
from models.recurso import Recurso
from views.recursos_por_analisis_view import RecursosPorAnalisisView

class RecursosPorAnalisisController(QObject):
    # Señal que se emite cuando el análisis ha sido actualizado en la BD.
    analysis_updated = pyqtSignal()
    # Nueva señal: emite (codigo_analisis, nuevo_total) cuando cambia el total por ediciones en la tabla
    analysis_total_changed = pyqtSignal(str, float)
    
    def __init__(self, codigo_analisis, parent=None, embed_readonly: bool = False, refresh_resources_cb=None):
        super().__init__(parent)
        self.codigo_analisis = codigo_analisis
        self.embed_readonly = bool(embed_readonly)
        self.refresh_resources_cb = refresh_resources_cb
        print(f"[DEBUG] Iniciando RecursosPorAnalisisController para análisis: {codigo_analisis}")
        # Si está embebido en la vista de Análisis del Presupuesto, ocultamos el formulario
        # y mostramos todas las filas completas (sin scroll interno)
        # En modo embed_readonly ocultamos formulario y botones inferiores
        # Ocultamos el formulario manual y el botón "Agregar a Tabla" (redundante)
        self.view = RecursosPorAnalisisView(codigo_analisis, show_form=False, show_buttons=not embed_readonly)
        # Temporizador para auto-guardar con debounce
        self._commit_timer = QTimer()
        self._commit_timer.setSingleShot(True)
        self._commit_timer.timeout.connect(self.update_analysis)
        # Diccionario para acumular cambios pendientes (clave: código del recurso)
        self.changes_pending = {}

        # Conectar botones definidos en la vista (si existen en este modo)
        if hasattr(self.view, 'add_button') and self.view.add_button is not None:
            self.view.add_button.clicked.connect(self.open_resource_selector)
        if hasattr(self.view, 'update_button') and self.view.update_button is not None:
            self.view.update_button.clicked.connect(self.update_analysis)
        # Formulario manual removido; no conexión a add_form_button
        # Conectar la señal dataChanged del modelo para detectar ediciones
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
        dialog.setWindowTitle("Adicionar Recurso")
        dialog.resize(600, 400)
        layout = QVBoxLayout(dialog)
        layout.addWidget(resource_controller.view)
        dialog.setLayout(layout)
        def _on_close_refresh():
            try:
                resource_controller.load_resources()
            except Exception:
                pass
            # Refrescar la vista principal de recursos si se proporcionó callback externo
            if callable(self.refresh_resources_cb):
                try:
                    self.refresh_resources_cb()
                except Exception:
                    pass
        resource_controller.view.resource_selected.connect(lambda resource: self.on_resource_selected(resource, dialog))
        dialog.finished.connect(lambda _: _on_close_refresh())
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

        # Agregar el recurso a la tabla con valores predeterminados
        row_position = self.view.model.rowCount()
        self.view.model.insertRow(row_position)
        self.view.model.setItem(row_position, 0, QStandardItem(resource.get("codigo_recurso", "")))
        self.view.model.setItem(row_position, 1, QStandardItem(resource.get("descripcion", "")))
        self.view.model.setItem(row_position, 2, QStandardItem(resource.get("unidad", "")))
        self.view.model.setItem(row_position, 3, QStandardItem("0"))
        self.view.model.setItem(row_position, 4, QStandardItem("0"))
        
        valor_unitario = resource.get("valor_unitario", 0)
        self.view.model.setItem(row_position, 5, QStandardItem(f"${valor_unitario:,.2f}"))
        self.view.model.setItem(row_position, 6, QStandardItem("$0.00"))
        
        dialog.accept()
        # Limpiar inputs del formulario para facilitar la siguiente inserción
        try:
            self.view.clear_form_inputs()
        except Exception:
            pass
        # Si hay callback externo, refrescar la lista principal de recursos
        if callable(self.refresh_resources_cb):
            try:
                self.refresh_resources_cb()
            except Exception:
                pass

    def on_add_form_button_clicked(self):
        """Se ejecuta al presionar el botón 'Agregar a Tabla' del formulario."""
        print("[DEBUG] Botón 'Agregar a Tabla' presionado (desde el formulario).")
        # Aquí podrías agregar lógica adicional si es necesario.

    def update_analysis(self):
        # En modo embebido solo-presupuesto no persistimos cambios a la BD
        if getattr(self, 'embed_readonly', False):
            return
        session = SessionLocal()
        try:
            # Borrar registros actuales para este análisis
            session.query(AnalisisUnitarioRecurso).filter_by(
                codigo_analisis=self.codigo_analisis
            ).delete()

            total_actualizado = 0.0
            row_count = self.view.model.rowCount()
            for row in range(row_count):
                # Lee el texto de la primera columna (código recurso)
                codigo_recurso = self.view.model.item(row, 0).text().strip()
                
                # SALTAR filas que son solo encabezados (las que empiezan con ===)
                if codigo_recurso.startswith("==="):
                    continue

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
                    vr_unitario_text = self.view.model.item(row, 5).text().replace('$', '').replace(',', '')
                    vr_unitario = float(vr_unitario_text)
                except Exception:
                    vr_unitario = 0.0
                try:
                    vr_parcial_text = self.view.model.item(row, 6).text().replace('$', '').replace(',', '')
                    vr_parcial = float(vr_parcial_text)
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
            QMessageBox.information(
                self.view, 
                "Actualización Exitosa",
                f"Análisis {self.codigo_analisis} actualizado.\nNuevo Total: {total_actualizado:.2f}"
            )
            # Emitir la señal de que el análisis ha sido actualizado
            self.analysis_updated.emit()
            # Cerrar la ventana después de actualizar
            try:
                parent = self.view.parentWidget() or self.view
                parent.close()
            except Exception:
                pass
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
        Actualiza en memoria (en el modelo) el vr_parcial de la fila editada.
        Además, programa un guardado con debounce y emite el nuevo total estimado
        para sincronizar el presupuesto en la vista principal.
        """
        row = topLeft.row()
        # Bloquear para evitar recursividad
        self.view.model.blockSignals(True)
        try:
            try:
                cantidad = float(self.view.model.item(row, 3).text())
            except Exception:
                cantidad = 0.0
            try:
                desperdicio = float(self.view.model.item(row, 4).text())
            except Exception:
                desperdicio = 0.0
            try:
                vr_unitario_text = self.view.model.item(row, 5).text().replace('$', '').replace(',', '')
                vr_unitario = float(vr_unitario_text)
            except Exception:
                vr_unitario = 0.0

            vr_parcial = cantidad * (1 + desperdicio) * vr_unitario
            self.view.model.setItem(row, 6, QStandardItem(f"${vr_parcial:,.2f}"))

            # Emitir total estimado del análisis
            total_est = 0.0
            for r in range(self.view.model.rowCount()):
                try:
                    cell = self.view.model.item(r, 6)
                    if not cell:
                        continue
                    text = cell.text().replace('$', '').replace(',', '')
                    total_est += float(text) if text else 0.0
                except Exception:
                    pass
            self.analysis_total_changed.emit(self.codigo_analisis, total_est)
        finally:
            self.view.model.blockSignals(False)

