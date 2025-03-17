from PyQt6.QtCore import QObject
from PyQt6.QtWidgets import QMessageBox
from models.analisis_unitario import AnalisisUnitario  # Asegúrate de que esté definido
from models.database import SessionLocal  # Tu sesión de SQLAlchemy
from views.analisis_unitarios_view import AnalisisUnitariosView

class AnalisisUnitariosController(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.view = AnalisisUnitariosView()
        self.load_analisis_unitarios()
        # Conectar la señal de edición para actualizar la BD si se edita alguna celda
        self.view.table.itemChanged.connect(self.on_data_changed)
        # Conectar la señal del botón de agregar análisis
        self.view.add_analysis.connect(self.agregar_analisis)
        # Conectar la señal de selección de análisis (opcional)
        self.view.analysis_selected.connect(self.on_analysis_selected)

    def load_analisis_unitarios(self):
        session = SessionLocal()
        try:
            analisis_list = session.query(AnalisisUnitario).all()
            data = []
            for a in analisis_list:
                data.append({
                    "codigo": a.codigo,
                    "descripcion": a.descripcion,
                    "unidad": a.unidad,
                    # Utilizamos la propiedad híbrida total_calculado
                    "total": a.total_calculado
                })
            self.view.load_data(data)
        except Exception as e:
            print("Error al cargar análisis unitarios:", e)
        finally:
            session.close()



    def agregar_analisis(self, data):
        """
        Inserta un nuevo análisis unitario en la base de datos con los datos recibidos del formulario.
        Luego, recarga la tabla de la vista.
        """
        session = SessionLocal()
        try:
            # Verificar si ya existe un análisis con ese código
            if session.query(AnalisisUnitario).filter(AnalisisUnitario.codigo == data["codigo"]).first():
                QMessageBox.warning(self.view, "Error", f"Ya existe un análisis con el código {data['codigo']}.")
                return
            
            nuevo_analisis = AnalisisUnitario(
                codigo=data["codigo"],
                descripcion=data["descripcion"],
                unidad=data["unidad"],
                total=data["total"]
            )
            session.add(nuevo_analisis)
            session.commit()
            print(f"Análisis {data['codigo']} agregado correctamente.")
            self.load_analisis_unitarios()  # Recargar la vista con los nuevos datos
        except Exception as e:
            session.rollback()
            print(f"Error al agregar análisis {data['codigo']}: {e}")
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
        unidad = self.view.table.item(row, 2).text() if self.view.table.item(row, 2) else ""
        try:
            total = float(self.view.table.item(row, 3).text()) if self.view.table.item(row, 3) else 0.0
        except ValueError:
            total = 0.0

        session = SessionLocal()
        try:
            analisis = session.query(AnalisisUnitario).filter(AnalisisUnitario.codigo == codigo).first()
            if analisis:
                analisis.descripcion = descripcion
                analisis.unidad = unidad
                analisis.total = total
                session.commit()
                print(f"Análisis unitario {codigo} actualizado correctamente.")
            else:
                print(f"No se encontró análisis unitario con código {codigo}.")
        except Exception as e:
            session.rollback()
            print(f"Error al actualizar análisis unitario {codigo}: {e}")
        finally:
            session.close()

        # Volver a cargar todos los análisis unitarios para refrescar la vista.
        self.load_analisis_unitarios()



    def on_analysis_selected(self, codigo):
        # Lógica al seleccionar un análisis, por ejemplo, abrir otra vista de recursos asociados.
        print(f"Análisis seleccionado: {codigo}")

