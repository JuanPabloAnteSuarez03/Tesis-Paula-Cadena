from PyQt6.QtCore import QObject
from PyQt6.QtWidgets import QMessageBox
from models.presupuesto import Presupuesto  # Asegúrate de que esté definido
from models.database import SessionLocal  # Tu sesión de SQLAlchemy
from views.presupuesto_view import PresupuestoView  # Asegúrate de que esté definido

class PresupuestoController(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.view = PresupuestoView()
        self.load_presupuestos()
        print("PresupuestoController")
        # Conectar la señal de edición para actualizar la BD si se edita alguna celda
        self.view.table.itemChanged.connect(self.on_data_changed)
        # Conectar la señal del botón de agregar presupuesto
        self.view.add_presupuesto.connect(self.agregar_presupuesto)
        # Conectar la señal de selección de presupuesto (opcional)
        self.view.presupuesto_selected.connect(self.on_presupuesto_selected)

    def load_presupuestos(self):
        session = SessionLocal()
        try:
            analisis_list = session.query(Presupuesto).all()
            data = []
            for a in analisis_list:
                data.append({
                    "codigo": a.codigo,
                    "descripcion": a.descripcion,
                    # Utilizamos la propiedad híbrida total_calculado
                    "total": a.total_calculado
                })
            self.view.load_data(data)
        except Exception as e:
            print("Error al cargar presupuestos:", e)
        finally:
            session.close()



    def agregar_presupuesto(self, data):
        """
        Inserta un nuevo presupuesto en la base de datos con los datos recibidos del formulario.
        Luego, recarga la tabla de la vista.
        """
        session = SessionLocal()
        try:
            # Verificar si ya existe un presupuesto con ese código
            if session.query(Presupuesto).filter(Presupuesto.codigo == data["codigo"]).first():
                QMessageBox.warning(self.view, "Error", f"Ya existe un presupuesto con el código {data['codigo']}.")
                return
            
            nuevo_presupuesto = Presupuesto(
                codigo=data["codigo"],
                descripcion=data["descripcion"],
                total=data["total"]
            )
            session.add(nuevo_presupuesto)
            session.commit()
            print(f"Presupuesto {data['codigo']} agregado correctamente.")
            self.load_presupuestos()  # Recargar la vista con los nuevos datos
        except Exception as e:
            session.rollback()
            print(f"Error al agregar presupuesto {data['codigo']}: {e}")
        finally:
            session.close()

    def on_data_changed(self, item):
        """
        Se llama cada vez que el usuario edita una celda.
        Actualiza el registro correspondiente en la base de datos y luego recarga la vista.
        """
        row = item.row()
        codigo_item = self.view.table.item(row, 0)
        if not codigo_item:
            return

        codigo = codigo_item.text()
        descripcion = self.view.table.item(row, 1).text() if self.view.table.item(row, 1) else ""
        try:
            total = float(self.view.table.item(row, 3).text()) if self.view.table.item(row, 3) else 0.0
        except ValueError:
            total = 0.0

        session = SessionLocal()
        try:
            analisis = session.query(Presupuesto).filter(Presupuesto.codigo == codigo).first()
            if analisis:
                analisis.descripcion = descripcion
                analisis.total = total
                session.commit()
                print(f"Presupuesto {codigo} actualizado correctamente.")
            else:
                print(f"No se encontró presupuesto con código {codigo}.")
        except Exception as e:
            session.rollback()
            print(f"Error al actualizar presupuesto {codigo}: {e}")
        finally:
            session.close()

        # Volver a cargar todos los presupuestos para refrescar la vista.
        self.load_presupuestos()



    def on_presupuesto_selected(self, codigo):
        # Lógica al seleccionar un presupuesto, por ejemplo, abrir otra vista de recursos asociados.
        print(f"Presupuesto seleccionado: {codigo}")

