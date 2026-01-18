# En el controlador (ResourceController, por ejemplo)
from PyQt6.QtCore import QObject, QTimer
from models.recurso import Recurso
from models.database import SessionLocal
from models.analisis_unitario_recurso import AnalisisUnitarioRecurso  # Import the missing model
from models.analisis_unitario import AnalisisUnitario
from sqlalchemy import func
from views.resource_list_view import ResourceListView
from PyQt6.QtWidgets import QMessageBox
from sqlalchemy.exc import IntegrityError

class ResourceController(QObject):
    def __init__(self):
        super().__init__()
        self.view = ResourceListView()
        self._loading = False
        self.load_resources()
        # Conectar la señal dataChanged para la edición de celdas
        self.view.model.dataChanged.connect(self.on_data_changed)
        # Conectar la señal para eliminar recurso
        self.view.resource_delete_requested.connect(self.delete_resource)
        # Conectar la señal para agregar recurso
        self.view.resource_added.connect(self.add_resource)
        # Referencia opcional para refrescar análisis después de actualizaciones
        self.external_analisis_controller = None

    def set_external_analisis_controller(self, controller):
        self.external_analisis_controller = controller


    def load_resources(self):
        session = SessionLocal()
        try:
            self._loading = True
            recursos = session.query(Recurso).all()
            data = []
            for r in recursos:
                data.append({
                    "codigo": r.codigo,
                    "descripcion": r.descripcion,
                    "unidad": r.unidad,
                    "valor_unitario": r.valor_unitario
                })
            self.view.load_data(data)
        except Exception as e:
            QMessageBox.critical(self.view, "Error", f"No se pudieron cargar los recursos: {e}")
        finally:
            self._loading = False
            session.close()

    def on_data_changed(self, topLeft, bottomRight, roles):
        """
        Se llama cuando el usuario edita una celda en la tabla.
        Solo aplicamos lógica especial al cambiar el valor unitario,
        advirtiendo que se actualizarán los análisis unitarios relacionados.
        """
        if getattr(self, "_loading", False):
            return
        model = self.view.model
        row = topLeft.row()
        codigo_item = model.item(row, 0)
        if not codigo_item:
            return

        codigo = codigo_item.text()
        col = topLeft.column()

        def _parse_float(text: str) -> float:
            try:
                return float(str(text).replace("$", "").replace(",", "").strip())
            except Exception:
                return 0.0

        session = SessionLocal()
        try:
            recurso = session.query(Recurso).filter(Recurso.codigo == codigo).first()
            if not recurso:
                return

            # Actualizar descripción y unidad sin advertencia
            if col in (1, 2):
                descripcion = model.item(row, 1).text()
                unidad = model.item(row, 2).text()
                recurso.descripcion = descripcion
                recurso.unidad = unidad
                session.commit()
                return

            # Manejo especial para valor unitario (columna 3)
            if col == 3:
                nuevo_valor = _parse_float(model.item(row, 3).text())
                valor_anterior = recurso.valor_unitario or 0.0
                if abs(nuevo_valor - valor_anterior) < 1e-9:
                    return

                reply = QMessageBox.question(
                    self.view,
                    "Actualizar valor unitario",
                    (
                        "Vas a modificar el valor unitario del recurso.\n"
                        "Esto actualizará todos los análisis unitarios que lo contienen.\n\n"
                        "¿Deseas continuar?"
                    ),
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                )
                if reply != QMessageBox.StandardButton.Yes:
                    # Revertir visualmente al valor anterior
                    try:
                        self._loading = True
                        model.item(row, 3).setText(f"${valor_anterior:,.2f}")
                    finally:
                        self._loading = False
                    return

                # 1) Actualizar recurso
                recurso.valor_unitario = nuevo_valor

                # 2) Actualizar relaciones y totales de análisis afectados
                relaciones = session.query(AnalisisUnitarioRecurso).filter(
                    AnalisisUnitarioRecurso.codigo_recurso == codigo
                ).all()
                codigos_afectados = set()
                totales_actualizados = {}
                for rel in relaciones:
                    rel.vr_unitario = nuevo_valor
                    # Arreglo: el desperdicio suele venir como entero (ej: 5 para 5%), hay que dividir por 100
                    d = (rel.desper or 0.0)
                    if d > 1.0: # Si es ej: 5.0, es 5%, si es 0.05 ya está bien
                        d = d / 100.0
                    rel.vr_parcial = (rel.cantidad_recurso or 0.0) * (1 + d) * nuevo_valor
                    codigos_afectados.add(rel.codigo_analisis)

                if codigos_afectados:
                    session.flush() # Asegurar que los vr_parcial se calculen en la BD
                    for a_code in codigos_afectados:
                        # Recalcular el total real sumando los recursos
                        total = (
                            session.query(func.coalesce(func.sum(AnalisisUnitarioRecurso.vr_parcial), 0.0))
                            .filter(AnalisisUnitarioRecurso.codigo_analisis == a_code)
                            .scalar()
                        )
                        ana = session.query(AnalisisUnitario).filter(AnalisisUnitario.codigo == a_code).first()
                        if ana:
                            ana.total = float(total or 0.0)
                            totales_actualizados[a_code] = ana.total

                session.commit()
                QMessageBox.information(
                    self.view,
                    "Actualización completada",
                    "Se actualizó el recurso y los análisis unitarios relacionados.",
                )

                # UI: formatear el valor editado sin recargar toda la tabla (muy costoso)
                try:
                    self._loading = True
                    model.item(row, 3).setText(f"${nuevo_valor:,.2f}")
                finally:
                    self._loading = False
                
                try:
                    # Forzar el refresco en el controlador de análisis
                    if self.external_analisis_controller:
                        # Usamos refresh_totals_for_codes que consulta la BD para estar 100% seguros
                        # y lo hacemos con un pequeño delay para que la BD esté lista
                        QTimer.singleShot(
                            300, 
                            lambda: self.external_analisis_controller.refresh_totals_for_codes(codigos_afectados)
                        )
                    else:
                        print("DEBUG: No hay controlador de análisis externo configurado.")
                except Exception as e:
                    print(f"DEBUG: Error al intentar refrescar análisis: {e}")
        except Exception as e:
            session.rollback()
            QMessageBox.critical(self.view, "Error", f"No se pudo actualizar el recurso {codigo}: {e}")
        finally:
            session.close()

    def add_resource(self, resource_data):
        session = SessionLocal()
        try:
            # --- Generación de código automático ---
            # Busca el código numérico más alto y lo incrementa.
            numeric_codes = [int(r.codigo) for r in session.query(Recurso.codigo) if r.codigo.isdigit()]
            
            if not numeric_codes:
                # Si no hay códigos numéricos, empezar desde un número base.
                new_code_num = 100000
            else:
                new_code_num = max(numeric_codes) + 1
            
            new_code = str(new_code_num)

            # Verificar si el código ya existe (poco probable pero es una buena práctica)
            if session.query(Recurso).filter(Recurso.codigo == new_code).first():
                QMessageBox.warning(self.view, "Error", f"El código autogenerado '{new_code}' ya existe. Inténtelo de nuevo.")
                return

            resource_data['codigo'] = new_code
            new_resource = Recurso(**resource_data)
            
            session.add(new_resource)
            session.commit()
            QMessageBox.information(self.view, "Éxito", f"Recurso agregado con el código '{new_code}'.")
            self.load_resources()
            try:
                self.view.clear_form_inputs()
            except Exception:
                pass
        except IntegrityError:
            session.rollback()
            QMessageBox.warning(
                self.view, "Error", f"Error de integridad al guardar el recurso."
            )
        except Exception as e:
            session.rollback()
            QMessageBox.critical(self.view, "Error", f"No se pudo agregar el recurso: {e}")
        finally:
            session.close()

    def delete_resource(self, codigo):
        session = SessionLocal()
        try:
            # Buscar el recurso
            recurso = session.query(Recurso).filter(Recurso.codigo == codigo).first()
            if not recurso:
                QMessageBox.warning(self.view, "Error", f"No se encontró recurso con código {codigo}.")
                return

            # Verificar si existen registros que usen este recurso en AnalisisUnitarioRecurso
            count_uso = session.query(AnalisisUnitarioRecurso).filter(
                AnalisisUnitarioRecurso.codigo_recurso == codigo
            ).count()
            if count_uso > 0:
                QMessageBox.warning(self.view, "Error", f"No se puede eliminar el recurso '{codigo}' porque está siendo usado por por un análisis unitario.")
                return

            # Si no está en uso, se puede eliminar
            session.delete(recurso)
            session.commit()
            QMessageBox.information(self.view, "Eliminado", f"El recurso '{codigo}' ha sido eliminado.")
            self.load_resources()

        except Exception as e:
            session.rollback()
            QMessageBox.critical(self.view, "Error", f"Error al eliminar el recurso {codigo}: {e}")
        finally:
            session.close()
