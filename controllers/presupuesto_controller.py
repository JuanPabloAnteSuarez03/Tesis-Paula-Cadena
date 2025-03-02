from models.presupuesto import Presupuesto
from models.articulo import Articulo

class PresupuestoController:
    def crear_presupuesto(self, nombre, articulos):
        Presupuesto.create_presupuesto(nombre, articulos)

    def obtener_presupuestos(self):
        return Presupuesto.get_presupuestos()
    
    def obtener_articulos(self):
        return Articulo.get_articulos()
