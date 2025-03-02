from .database import get_db_connection

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
            if articulo:
                # Convierte la tupla en un diccionario
                return {
                    "id": articulo[0],
                    "codigo": articulo[1],
                    "descripcion": articulo[2],
                    "unidad": articulo[3],
                    "valor_unitario": articulo[4]
                }


    @staticmethod
    def get_articulo_by_id(id):
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM articulos WHERE id = %s", (id,))
            articulo = cursor.fetchone()
            conn.close()
            if articulo:
                return Articulo(articulo[0], articulo[1], articulo[2], articulo[3], articulo[4])

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
