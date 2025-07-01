# En el controlador (ResourceController, por ejemplo)
from PyQt6.QtCore import QObject
from models.recurso import Recurso
from models.database import SessionLocal
from models.analisis_unitario_recurso import AnalisisUnitarioRecurso  # Import the missing model
from views.resource_list_view import ResourceListView
from PyQt6.QtWidgets import QMessageBox
from sqlalchemy.exc import IntegrityError

class ResourceController(QObject):
    def __init__(self):
        super().__init__()
        self.view = ResourceListView()
        self.load_resources()
        # Conectar la señal dataChanged para la edición de celdas
        self.view.model.dataChanged.connect(self.on_data_changed)
        # Conectar la señal para eliminar recurso
        self.view.resource_delete_requested.connect(self.delete_resource)
        # Conectar la señal para agregar recurso
        self.view.resource_added.connect(self.add_resource)


    def load_resources(self):
        session = SessionLocal()
        try:
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
            session.close()

    def on_data_changed(self, topLeft, bottomRight, roles):
        """
        Se llama cuando el usuario edita una celda en la tabla.
        topLeft y bottomRight son índices que indican el rango de celdas modificadas.
        Usamos el índice de la primera celda modificada para identificar la fila.
        """
        print("Se ha modificado una celda en la tabla.")
        # Obtenemos el modelo
        model = self.view.model

        # Por simplicidad, asumimos que solo se edita una celda a la vez
        row = topLeft.row()
        codigo_item = model.item(row, 0)  # Asumimos que la primera columna es el código único
        if not codigo_item:
            return

        codigo = codigo_item.text()

        # Leer los valores actuales de la fila
        descripcion = model.item(row, 1).text()
        unidad = model.item(row, 2).text()
        valor_unitario = float(model.item(row, 3).text())

        # Actualizar el recurso en la base de datos
        session = SessionLocal()
        try:
            recurso = session.query(Recurso).filter(Recurso.codigo == codigo).first()
            if recurso:
                recurso.descripcion = descripcion
                recurso.unidad = unidad
                recurso.valor_unitario = valor_unitario
                session.commit()
                print(f"Recurso {codigo} actualizado correctamente en la BD.")
            else:
                print(f"No se encontró recurso con código {codigo}.")
        except Exception as e:
            session.rollback()
            print(f"Error al actualizar recurso {codigo}: {e}")
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
                 session.close()
                 return

            resource_data['codigo'] = new_code
            new_resource = Recurso(**resource_data)
            
            session.add(new_resource)
            session.commit()
            QMessageBox.information(self.view, "Éxito", f"Recurso agregado con el código '{new_code}'.")
            self.load_resources()
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
