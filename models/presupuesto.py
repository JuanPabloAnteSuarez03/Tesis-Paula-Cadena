from .database import get_db_connection

class Presupuesto:
    def __init__(self, nombre, costo_total):
        self.nombre = nombre
        self.costo_total = costo_total

    @staticmethod
    def crear_presupuesto(nombre, costo_total):
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO presupuestos (nombre, costo_total) VALUES (%s, %s)",
                (nombre, costo_total)
            )
            conn.commit()
            conn.close()

    @staticmethod
    def obtener_presupuestos():
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM presupuestos")
            presupuestos = cursor.fetchall()
            conn.close()
            return [{"id": p[0], "nombre": p[1], "costo_total": p[2]} for p in presupuestos]
