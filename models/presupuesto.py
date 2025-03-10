from .database import get_db_connection
from .recurso import Recurso

class Presupuesto:
    def __init__(self, nombre):
        self.nombre = nombre
        self.recursos = []
        self.costo_total = 0.0

    def agregar_recurso(self, recurso_id, cantidad=1):
        recurso = Recurso.get_recurso(recurso_id)
        if recurso:
            self.recursos.append({"recurso": recurso, "cantidad": cantidad})
            self.calcular_costo_total()

    def calcular_costo_total(self):
        self.costo_total = sum(item['recurso']['valor_unitario'] * item['cantidad'] for item in self.recursos)

    @staticmethod
    def create_presupuesto(nombre, recursos):
        presupuesto = Presupuesto(nombre)
        for recurso_id, cantidad in recursos.items():
            presupuesto.agregar_recurso(recurso_id, cantidad)

        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO presupuestos (nombre) VALUES (%s) RETURNING id",
                (presupuesto.nombre,)
            )
            presupuesto_id = cursor.fetchone()[0]

            for item in presupuesto.recursos:
                cursor.execute(
                    "INSERT INTO presupuesto_recursos (presupuesto_id, recurso_id, cantidad) VALUES (%s, %s, %s)",
                    (presupuesto_id, item['recurso']['id'], item['cantidad'])
                )

            conn.commit()
            conn.close()

    @staticmethod
    def get_presupuestos():
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT p.id, p.nombre, 
                COALESCE(SUM(pa.cantidad * a.valor_unitario), 0) AS costo_total
            FROM presupuestos p
            LEFT JOIN presupuesto_recursos pa ON p.id = pa.presupuesto_id
            LEFT JOIN recursos a ON pa.recurso_id = a.id
            GROUP BY p.id, p.nombre
            """)
            
            presupuestos = cursor.fetchall()
            presupuestos_list = []

            for presupuesto in presupuestos:
                presupuestos_list.append({
                    "id": presupuesto[0],
                    "nombre": presupuesto[1],
                    "costo_total": presupuesto[2]  # Ahora el costo_total se calcula correctamente
                })

            conn.close()
            return presupuestos_list


    @staticmethod
    def get_presupuesto(id):
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM presupuestos WHERE id = %s", (id,))
            presupuesto_data = cursor.fetchone()

            if presupuesto_data:
                presupuesto = Presupuesto(presupuesto_data[1])
                presupuesto.costo_total = presupuesto_data[2]

                cursor.execute("SELECT recurso_id, cantidad FROM presupuesto_recursos WHERE presupuesto_id = %s", (id,))
                recursos_data = cursor.fetchall()

                for recurso_id, cantidad in recursos_data:
                    recurso = Recurso.get_recurso(recurso_id)
                    if recurso:
                        presupuesto.recursos.append({"recurso": recurso, "cantidad": cantidad})

                conn.close()
                return presupuesto
            
    @staticmethod
    def update_presupuesto(id, nombre, recursos):
        presupuesto = Presupuesto(nombre)
        for recurso_id, cantidad in recursos.items():
            presupuesto.agregar_recurso(recurso_id, cantidad)

        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE presupuestos SET nombre = %s, costo_total = %s WHERE id = %s", (presupuesto.nombre, presupuesto.costo_total, id))
            cursor.execute("DELETE FROM presupuesto_recursos WHERE presupuesto_id = %s", (id,))

            for item in presupuesto.recursos:
                cursor.execute(
                    "INSERT INTO presupuesto_recursos (presupuesto_id, recurso_id, cantidad) VALUES (%s, %s, %s)",
                    (id, item['recurso']['id'], item['cantidad'])
                )

            conn.commit()
            conn.close()

    @staticmethod
    def delete_presupuesto(id):
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM presupuesto_recursos WHERE presupuesto_id = %s", (id,))
            cursor.execute("DELETE FROM presupuestos WHERE id = %s", (id,))
            conn.commit()
            conn.close()
