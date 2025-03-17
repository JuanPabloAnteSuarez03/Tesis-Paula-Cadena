# En el controlador (ResourceController, por ejemplo)
from PyQt6.QtCore import QObject
from models.recurso import Recurso
from models.database import SessionLocal
from views.resource_list_view import ResourceListView

class ResourceController(QObject):
    def __init__(self):
        super().__init__()
        self.view = ResourceListView()
        self.load_resources()
        # Conectar la señal dataChanged del modelo a la función de actualización
        self.view.model.dataChanged.connect(self.on_data_changed)
        
        # También puedes conectar el botón de agregar recurso, etc.

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
