# controllers/resource_controller.py
from PyQt6.QtCore import QObject
from models.recurso import Recurso  # Tu modelo Recurso definido en tu aplicación
from models.database import SessionLocal
from views.resource_list_view import ResourceListView

class ResourceController(QObject):
    def __init__(self):
        super().__init__()
        self.view = ResourceListView()
        self.load_resources()

    def load_resources(self):
        """
        Carga los recursos desde la base de datos y se los pasa a la vista.
        """
        session = SessionLocal()
        try:
            recursos = session.query(Recurso).all()  # Devuelve la lista de objetos Recurso
            # Convertimos cada Recurso en un dict que la vista pueda usar
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
