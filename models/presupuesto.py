from .database import get_db_connection

class Presupuesto:
    def __init__(self, nombre, costo_total):
        self.nombre = nombre
        self.costo_total = costo_total

    @staticmethod
    def create_presupuesto(nombre, costo_total):
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
    def get_presupuestos():
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM presupuestos")
            presupuestos = cursor.fetchall()
            conn.close()
            return [{"id": p[0], "nombre": p[1], "costo_total": p[2]} for p in presupuestos]
        
    @staticmethod
    def get_presupuesto(id):
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM presupuestos WHERE id = %s", (id,))
            presupuesto = cursor.fetchone()
            conn.close()
            return presupuesto
        
    @staticmethod
    def update_presupuesto(id, nombre, costo_total):
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE presupuestos SET nombre = %s, costo_total = %s WHERE id = %s",
                (nombre, costo_total, id)
            )
            conn.commit()
            conn.close()

    @staticmethod
    def delete_presupuesto(id):
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM presupuestos WHERE id = %s", (id,))
            conn.commit()
            conn.close()

class Articulo:
    def __init__(self, codigo, descripcion, unidad, valor_unitario):
        self.codigo = codigo
        self.descripcion = descripcion
        self.unidad = unidad
        self.valor_unitario = valor_unitario

    @staticmethod
    def create_articulo(codigo, descripcion, unidad, valor_unitario):
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO articulos (codigo, descripcion, unidad, valor_unitario) VALUES (%s, %s, %s, %s)",
                (codigo, descripcion, unidad, valor_unitario)
            )
            conn.commit()
            conn.close()

    @staticmethod
    def get_articulos():
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM articulos")
            articulos = cursor.fetchall()
            conn.close()
            return [{"id": a[0], "codigo": a[1], "descripcion": a[2], "unidad": a[3], "valor_unitario": a[4]} for a in articulos]
        
    @staticmethod
    def get_articulo(id):
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM articulos WHERE id = %s", (id,))
            articulo = cursor.fetchone()
            conn.close()
            return articulo
        
    @staticmethod
    def update_articulo(id, codigo, descripcion, unidad, valor_unitario):
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE articulos SET codigo = %s, descripcion = %s, unidad = %s, valor_unitario = %s WHERE id = %s",
                (codigo, descripcion, unidad, valor_unitario, id)
            )
            conn.commit()
            conn.close()

    @staticmethod
    def delete_articulo(id):
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM articulos WHERE id = %s", (id,))
            conn.commit()
            conn.close()

    