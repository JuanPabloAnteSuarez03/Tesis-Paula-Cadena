# controllers/recursos_por_analisis_controller.py
import traceback
from PyQt6.QtCore import QObject
from PyQt6.QtWidgets import QMessageBox, QDialog, QVBoxLayout, QPushButton
from PyQt6.QtGui import QStandardItem
from models.presupuesto_analisis_unitario import PresupuestoAnalisisUnitario
from models.analisis_unitario import AnalisisUnitario
from models.database import SessionLocal
from models.recurso import Recurso
from controllers.analisis_unitarios_controller import AnalisisUnitariosController

from views.analisis_por_presupuesto_view import AnalisisPorPresupuestoView

class PresupuestoAnalisisUnitarioController(QObject):
    def __init__(self, codigo_presupuesto, parent=None):
        super().__init__(parent)
        self.codigo_presupuesto = codigo_presupuesto
        print(f"[DEBUG] Iniciando PresupuestoAnalisisUnitario para presupuesto: {codigo_presupuesto}")
        self.view = AnalisisPorPresupuestoView(codigo_presupuesto)
        # Diccionario para acumular cambios pendientes (clave: código del recurso)
        self.changes_pending = {}

        # Conectar botones definidos en la vista
        self.view.add_button.clicked.connect(self.open_analisis_selector)
        self.view.update_button.clicked.connect(self.update_presupuesto)
        # Conectar el botón del formulario manual para agregar fila
        self.view.add_form_button.clicked.connect(self.on_add_form_button_clicked)
        # Conectar la señal dataChanged del modelo para detectar ediciones
        self.view.model.dataChanged.connect(self.on_item_changed)
        print("✅ Señal dataChanged conectada correctamente.")


        # Cargar datos iniciales para el presupuesto
        self.load_analisis_por_presupuesto()



    def load_analisis_por_presupuesto(self):
        """Carga desde la BD los analisis asociados al presupuesto y actualiza la vista."""
        session = SessionLocal()
        try:
            query = session.query(PresupuestoAnalisisUnitario).filter_by(
                codigo_presupuesto=self.codigo_presupuesto
            ).all()
            data = []
            for r in query:
                data.append({
                    "codigo_analisis": r.codigo_analisis,
                    "descripcion_analisis": r.descripcion_analisis,
                    "unidad_analisis": r.unidad_analisis,
                    "cantidad_analisis": r.cantidad_analisis,
                    "valor_unitario": r.vr_unitario,
                    "vr_total": r.vr_total
                })
            self.view.load_data(data)
        except Exception as e:
            QMessageBox.critical(self.view, "Error", f"Error al cargar analisis: {e}")
        finally:
            session.close()

    def open_analisis_selector(self):
        """Abre un diálogo modal con la vista del selector de analisis."""
        analisis_unitarios_controller = AnalisisUnitariosController()
        dialog = QDialog(self.view)
        dialog.setWindowTitle("Seleccionar Recurso")
        dialog.resize(600, 400)
        layout = QVBoxLayout(dialog)
        layout.addWidget(analisis_unitarios_controller.view)
        dialog.setLayout(layout)
        analisis_unitarios_controller.view.analysis_selected.connect(lambda analisis: self.on_analisis_unitarios(analisis, dialog))
        dialog.exec()

    def on_analisis_unitarios(self, analisis_code, dialog):
        """Se dispara al seleccionar un analisis en el selector.
        Consulta la BD para obtener los datos completos y agrega una fila en la tabla."""
        session = SessionLocal()
        try:
            r = session.query(AnalisisUnitario).filter(AnalisisUnitario.codigo == analisis_code).first()
            if r:
                analisis = {
                    "codigo_analisis": r.codigo,
                    "descripcion_analisis": r.descripcion,
                    "unidad_analisis": r.unidad,
                    "valor_unitario": r.total
                }

            else:
                QMessageBox.warning(self.view, "Error", f"No se encontró el analisis con código {analisis_code}")
                dialog.reject()
                return
        except Exception as e:
            QMessageBox.critical(self.view, "Error", f"Error al consultar analisis: {e}")
            dialog.reject()
            return
        finally:
            session.close()

        # Agregar el recurso a la tabla con valores predeterminados
        row_position = self.view.model.rowCount()
        self.view.model.insertRow(row_position)
        self.view.model.setItem(row_position, 0, QStandardItem(analisis.get("codigo_analisis", "")))
        self.view.model.setItem(row_position, 1, QStandardItem(analisis.get("descripcion_analisis", "")))
        self.view.model.setItem(row_position, 2, QStandardItem(analisis.get("unidad_analisis", "")))
        self.view.model.setItem(row_position, 3, QStandardItem("0"))
        self.view.model.setItem(row_position, 4, QStandardItem(str(analisis.get("valor_unitario", "0"))))
        self.view.model.setItem(row_position, 5, QStandardItem("0"))
        dialog.accept()

    def on_add_form_button_clicked(self):
        """Se ejecuta al presionar el botón 'Agregar a Tabla' del formulario."""
        print("[DEBUG] Botón 'Agregar a Tabla' presionado (desde el formulario).")
        # Aquí podrías agregar lógica adicional si es necesario.

    def update_presupuesto(self):
        """
        Recorre el modelo, elimina los registros actuales de este presupuesto en la BD,
        inserta los datos actuales del modelo y recalcula el total del presupuesto.
        """
        session = SessionLocal()
        try:
            # Borrar registros actuales para este presupuesto
            session.query(PresupuestoAnalisisUnitario).filter_by(
                codigo_presupuesto=self.codigo_presupuesto
            ).delete()

            total_actualizado = 0.0
            row_count = self.view.model.rowCount()
            for row in range(row_count):
                codigo_analisis = self.view.model.item(row, 0).text().strip()
                descripcion_analisis = self.view.model.item(row, 1).text().strip()
                unidad_analisis = self.view.model.item(row, 2).text().strip()
                try:
                    cantidad_analisis = float(self.view.model.item(row, 3).text())
                except Exception:
                    cantidad_analisis = 0.0
                try:
                    vr_unitario = float(self.view.model.item(row, 4).text())
                except Exception:
                    vr_unitario = 0.0
                try:
                    vr_total = float(self.view.model.item(row, 5).text())
                except Exception:
                    vr_total = 0.0

                total_actualizado += vr_total

                nuevo = PresupuestoAnalisisUnitario(
                    codigo_presupuesto=self.codigo_presupuesto,
                    codigo_analisis=codigo_analisis,
                    descripcion_analisis=descripcion_analisis,
                    unidad_analisis=unidad_analisis,
                    cantidad_analisis=cantidad_analisis,
                    vr_unitario=vr_unitario,
                    vr_total=vr_total
                )
                session.add(nuevo)

            # Actualizar el total del presupuesto unitario
            analisis = session.query(AnalisisUnitario).filter_by(codigo=self.codigo_presupuesto).first()
            if analisis:
                analisis.total = total_actualizado
                print(f"[DEBUG] Nuevo total del presupuesto {self.codigo_presupuesto}: {total_actualizado}")

            session.commit()
            QMessageBox.information(self.view, "Actualización Exitosa",
                                    f"Análisis {self.codigo_presupuesto} actualizado.\nNuevo Total: {total_actualizado:.2f}")
        except Exception as e:
            session.rollback()
            QMessageBox.critical(self.view, "Error", f"Error al actualizar presupuesto: {e}")
            traceback.print_exc()
        finally:
            session.close()
            self.load_analisis_por_presupuesto()

    def on_item_changed(self, topLeft, bottomRight, roles):
        """
        Se dispara cuando se edita una celda del modelo.
        Actualiza en memoria (en el modelo) el vr_total de la fila editada.
        No se realiza commit a la BD aquí para evitar múltiples commits.
        """
        row = topLeft.row()
        # Bloqueamos las señales para evitar que la actualización de la celda dispare de nuevo este evento
        self.view.model.blockSignals(True)
        try:
            try:
                cantidad_analisis = float(self.view.model.item(row, 3).text())
            except:
                cantidad_analisis = 0.0
            try:
                vr_unitario = float(self.view.model.item(row, 4).text())
            except:
                vr_unitario = 0.0

            # Calcular vr_total localmente
            vr_total = cantidad_analisis  * vr_unitario  # Asegúrate que la fórmula sea la correcta
            # Actualizamos la celda de vr_total
            self.view.model.setItem(row, 5, QStandardItem(f"{vr_total:.2f}"))
            print(f"[DEBUG] on_item_changed: Fila {row} - vr_total recalculado: {vr_total:.2f}")
        finally:
            # Desbloqueamos las señales después de la actualización
            self.view.model.blockSignals(False)

