# controllers/analisis_unitarios_controller.py
from PyQt6.QtCore import QObject
from PyQt6.QtWidgets import QMessageBox, QDialog, QVBoxLayout, QTableWidgetItem
from models.analisis_unitario import AnalisisUnitario
from models.database import SessionLocal
from views.analisis_unitarios_view import AnalisisUnitariosView
from controllers.recursos_por_analisis_controller import RecursosPorAnalisisController
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func

class AnalisisUnitariosController(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.view = AnalisisUnitariosView()
        # Mantener referencias a editores abiertos para evitar que se destruyan al salir del scope
        self._open_editors = []
        self._resource_controller = None
        self.load_analisis_unitarios()

        # Conectar edición de celdas
        self.view.table.itemChanged.connect(self.on_data_changed)
        # Conectar botón de agregar análisis
        self.view.add_analysis.connect(self.on_add_analysis)
        # Conectar selección de análisis
        self.view.analysis_selected.connect(self.on_analysis_selected)
        # --- Conectar eliminación de análisis ---
        self.view.analysis_delete_requested.connect(self.on_delete_analysis)
        # ----------------------------------------
        # Conectar la nueva señal para abrir recursos por análisis
        self.view.analysis_edit_requested.connect(self.on_edit_analysis_resources)

    def load_analisis_unitarios(self):
        session = SessionLocal()
        try:
            analisis_list = session.query(AnalisisUnitario).all()
            table = self.view.table

            # Ruta rápida: rellenar tabla directamente con renders y sort pausados
            updates = table.updatesEnabled()
            sorting = table.isSortingEnabled()
            table.setUpdatesEnabled(False)
            table.setSortingEnabled(False)
            table.blockSignals(True)

            table.setRowCount(len(analisis_list))
            for row, a in enumerate(analisis_list):
                table.setItem(row, 0, QTableWidgetItem(a.codigo or ""))

                desc = a.descripcion or ""
                desc_item = QTableWidgetItem(desc)
                desc_item.setToolTip(desc)
                table.setItem(row, 1, desc_item)

                table.setItem(row, 2, QTableWidgetItem(a.unidad or ""))

                total_val = a.total_calculado or 0.0
                table.setItem(row, 3, QTableWidgetItem(f"${total_val:,.2f}"))

            table.blockSignals(False)
            table.setSortingEnabled(sorting)
            table.setUpdatesEnabled(updates)
            # Ajustar ancho de descripción para ocupar el espacio sobrante (si la vista lo soporta)
            try:
                if hasattr(self.view, "_auto_size_description"):
                    self.view._auto_size_description()
            except Exception:
                pass
        except Exception as e:
            print("Error al cargar análisis unitarios:", e)
        finally:
            session.close()

    def on_add_analysis(self, data):
        """
        Se ejecuta cuando se presiona 'Agregar Análisis' en la vista.
        Genera un nuevo código automáticamente.
        """
        session = SessionLocal()
        try:
            # --- Generación de código automático ---
            last_code = session.query(func.max(AnalisisUnitario.codigo)).scalar()
            new_code = ""
            if not last_code:
                new_code = "01-01-01"
            else:
                parts = last_code.split('-')
                try:
                    # Intentar incrementar la última parte
                    last_part_int = int(parts[-1])
                    new_last_part = last_part_int + 1
                    # Formatear con ceros a la izquierda, manteniendo la longitud original o un mínimo de 2
                    padding = max(2, len(parts[-1]))
                    parts[-1] = str(new_last_part).zfill(padding)
                    new_code = "-".join(parts)
                except (ValueError, IndexError):
                    # Si el formato no es el esperado, crear un nuevo código
                    new_code = f"{last_code}-1"

            # El código debe ser único
            if session.query(AnalisisUnitario).filter(AnalisisUnitario.codigo == new_code).first():
                QMessageBox.warning(self.view, "Error", f"El código generado '{new_code}' ya existe. Inténtelo de nuevo.")
                session.close()
                return

            nuevo_analisis = AnalisisUnitario(
                codigo=new_code,
                descripcion=data['descripcion'],
                unidad=data['unidad'],
            )
            session.add(nuevo_analisis)
            session.commit()
            QMessageBox.information(self.view, "Éxito", f"Análisis unitario agregado con código '{new_code}'.")
            # Abrir inmediatamente el editor de recursos para completar costos
            try:
                editor = RecursosPorAnalisisController(
                    new_code,
                    refresh_resources_cb=self._refresh_resources
                )
                editor.analysis_updated.connect(self.load_analisis_unitarios)
                editor.view.show()
                try:
                    editor.view.raise_()
                    editor.view.activateWindow()
                except Exception:
                    pass
                # Guardar referencia para que no sea recolectado
                self._open_editors.append(editor)
            except Exception as e:
                QMessageBox.warning(self.view, "Aviso", f"Análisis creado, pero no se pudo abrir el editor: {e}")
            self.load_analisis_unitarios()
        except Exception as e:
            session.rollback()
            QMessageBox.critical(self.view, "Error", f"No se pudo agregar el análisis: {str(e)}")
        finally:
            session.close()

    def on_delete_analysis(self, codigo):
        """
        Elimina el análisis con el código proporcionado de la base de datos y refresca la vista.
        """
        session = SessionLocal()
        try:
            analisis = session.query(AnalisisUnitario).filter(AnalisisUnitario.codigo == codigo).first()
            if analisis:
                session.delete(analisis)
                session.commit()
                QMessageBox.information(self.view, "Eliminado", f"El análisis '{codigo}' ha sido eliminado.")
                self.load_analisis_unitarios()
            else:
                QMessageBox.warning(self.view, "Error", f"No se encontró un análisis con el código {codigo}.")
        except Exception as e:
            session.rollback()
            QMessageBox.critical(self.view, "Error", f"Error al eliminar el análisis {codigo}: {e}")
        finally:
            session.close()

    def on_data_changed(self, item):
        row = item.row()
        codigo_item = self.view.table.item(row, 0)
        if not codigo_item:
            return

        codigo = codigo_item.text()
        descripcion = self.view.table.item(row, 1).text() if self.view.table.item(row, 1) else ""
        unidad = self.view.table.item(row, 2).text() if self.view.table.item(row, 2) else ""
        try:
            total = float(self.view.table.item(row, 3).text()) if self.view.table.item(row, 3) else 0.0
        except ValueError:
            total = 0.0

        session = SessionLocal()
        try:
            analisis = session.query(AnalisisUnitario).filter(AnalisisUnitario.codigo == codigo).first()
            if analisis:
                analisis.descripcion = descripcion
                analisis.unidad = unidad
                analisis.total_calculado = total
                session.commit()
                print(f"Análisis unitario {codigo} actualizado correctamente.")
                # Actualizar solo la fila afectada en la tabla (evita recargar todo)
                self._update_table_row(codigo, descripcion, unidad, total)
            else:
                print(f"No se encontró análisis unitario con código {codigo}.")
        except Exception as e:
            session.rollback()
            print(f"Error al actualizar análisis unitario {codigo}: {e}")
        finally:
            session.close()

    def _update_table_row(self, codigo: str, descripcion: str, unidad: str, total: float):
        """
        Actualiza la fila existente para un código dado sin recargar toda la tabla.
        """
        try:
            table = self.view.table
            for r in range(table.rowCount()):
                code_item = table.item(r, 0)
                if code_item and code_item.text() == codigo:
                    # Descripción
                    desc_item = table.item(r, 1)
                    if not desc_item:
                        desc_item = QTableWidgetItem()
                        table.setItem(r, 1, desc_item)
                    desc_item.setText(descripcion or "")
                    desc_item.setToolTip(descripcion or "")
                    # Unidad
                    unit_item = table.item(r, 2)
                    if not unit_item:
                        unit_item = QTableWidgetItem()
                        table.setItem(r, 2, unit_item)
                    unit_item.setText(unidad or "")
                    # Total
                    total_item = table.item(r, 3)
                    if not total_item:
                        total_item = QTableWidgetItem()
                        table.setItem(r, 3, total_item)
                    total_item.setText(f"${total:,.2f}")
                    break
        except Exception:
            # En caso de cualquier problema, caemos al refresco completo
            self.load_analisis_unitarios()

    def on_analysis_selected(self, codigo_analisis):
        """
        Se dispara cuando se selecciona un análisis (con doble clic) en la vista principal.
        """
        print(f"Análisis seleccionado: {codigo_analisis}")

    def on_edit_analysis_resources(self, codigo_analisis):
        """
        Abre la ventana para editar los recursos de un análisis unitario.
        """
        print(f"Abriendo editor de recursos para: {codigo_analisis}")
        editor = RecursosPorAnalisisController(
            codigo_analisis,
            refresh_resources_cb=self._refresh_resources
        )
        editor.analysis_updated.connect(self.load_analisis_unitarios)
        editor.view.show()
        try:
            editor.view.raise_()
            editor.view.activateWindow()
        except Exception:
            pass
        # Guardar referencia para evitar que el GC cierre la ventana
        self._open_editors.append(editor)

    def set_resource_controller(self, resource_controller):
        """Permite refrescar la vista principal de recursos cuando se agregan desde el editor."""
        self._resource_controller = resource_controller

    def _refresh_resources(self):
        if self._resource_controller:
            try:
                self._resource_controller.load_resources()
            except Exception:
                pass
