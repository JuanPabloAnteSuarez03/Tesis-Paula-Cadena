from .database import get_db_connection

class Recurso:
    def __init__(self, codigo, descripcion, unidad, valor_unitario):
        self.codigo = codigo
        self.descripcion = descripcion
        self.unidad = unidad
        self.valor_unitario = valor_unitario

    @staticmethod
    def create_recurso(codigo, descripcion, unidad, valor_unitario):
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO recursos (codigo, descripcion, unidad, valor_unitario) VALUES (%s, %s, %s, %s)",
                (codigo, descripcion, unidad, valor_unitario)
            )
            conn.commit()
            conn.close()

    @staticmethod
    def get_recursos():
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM recursos")
            recursos = cursor.fetchall()
            conn.close()
            return [{"id": a[0], "codigo": a[1], "descripcion": a[2], "unidad": a[3], "valor_unitario": a[4]} for a in recursos]
        
    @staticmethod
    def get_recurso(id):
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM recursos WHERE id = %s", (id,))
            recurso = cursor.fetchone()
            conn.close()
            if recurso:
                # Convierte la tupla en un diccionario
                return {
                    "id": recurso[0],
                    "codigo": recurso[1],
                    "descripcion": recurso[2],
                    "unidad": recurso[3],
                    "valor_unitario": recurso[4]
                }


    @staticmethod
    def get_recurso_by_id(id):
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM recursos WHERE id = %s", (id,))
            recurso = cursor.fetchone()
            conn.close()
            if recurso:
                return Recurso(recurso[0], recurso[1], recurso[2], recurso[3], recurso[4])

    @staticmethod
    def update_recurso(id, codigo, descripcion, unidad, valor_unitario):
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE recursos SET codigo = %s, descripcion = %s, unidad = %s, valor_unitario = %s WHERE id = %s",
                (codigo, descripcion, unidad, valor_unitario, id)
            )
            conn.commit()
            conn.close()

    @staticmethod
    def delete_recurso(id):
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM recursos WHERE id = %s", (id,))
            conn.commit()
            conn.close()
