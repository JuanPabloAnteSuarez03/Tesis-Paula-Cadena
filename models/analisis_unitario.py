from models.recurso import Recurso

class AnalisisUnitario:
    def __init__(self, descripcion, unidad, cantidad, precio_unitario, recursos=None):
        self.descripcion = descripcion
        self.unidad = unidad
        self.cantidad = cantidad
        self.precio_unitario = precio_unitario
        self.recursos = recursos if recursos is not None else []
        self.total = self.calcular_total()

    def calcular_total(self):
        return self.cantidad * self.precio_unitario

    def agregar_recurso(self, recurso: Recurso, cantidad):
        self.recursos.append({'recurso': recurso, 'cantidad': cantidad})
        self.actualizar_precio_unitario()
        self.total = self.calcular_total()

    def actualizar_precio_unitario(self):
        self.precio_unitario = sum(
            item['recurso'].valor_unitario * item['cantidad'] for item in self.recursos
        )

    @classmethod
    def create_analisis_unitario(cls, descripcion, unidad, cantidad, recursos):
        analisis = cls(descripcion, unidad, cantidad, 0, recursos)
        analisis.actualizar_precio_unitario()
        analisis.total = analisis.calcular_total()
        # Aquí deberías agregar la lógica para guardar en la base de datos si es necesario
        return analisis
