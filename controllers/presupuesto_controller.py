from models.presupuesto import Presupuesto

class PresupuestoController:
    def crear_presupuesto(self, nombre, costo_total):
        Presupuesto.crear_presupuesto(nombre, costo_total)

    def obtener_presupuestos(self):
        return Presupuesto.obtener_presupuestos()
