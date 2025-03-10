from models.presupuesto import Presupuesto
from models.recurso import Recurso

class PresupuestoController:
    def crear_presupuesto(self, nombre, recursos):
        Presupuesto.create_presupuesto(nombre, recursos)

    def obtener_presupuestos(self):
        return Presupuesto.get_presupuestos()
    
    def obtener_recursos(self):
        return Recurso.get_recursos()
