# controllers/analisis_unitarios_controller.py
from PyQt6.QtCore import QObject
from PyQt6.QtWidgets import QMessageBox
from models.analisis_unitario import AnalisisUnitario
from models.database import SessionLocal
from views.analisis_unitarios_view import AnalisisUnitariosView

class AnalisisUnitariosController(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.view = AnalisisUnitariosView()
        self.load_analisis_unitarios()

        # Conectar edición de celdas
        self.view.table.itemChanged.connect(self.on_data_changed)
        # Conectar botón de agregar análisis
        self.view.add_analysis.connect(self.agregar_analisis)
        # Conectar selección de análisis
        self.view.analysis_selected.connect(self.on_analysis_selected)
        # --- Conectar eliminación de análisis ---
        self.view.analysis_delete_requested.connect(self.delete_analysis)
        # ----------------------------------------

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
                    "total": a.total_calculado
                })
            self.view.load_data(data)
        except Exception as e:
            print("Error al cargar análisis unitarios:", e)
        finally:
            session.close()

    def agregar_analisis(self, data):
        session = SessionLocal()
        try:
            # Verificar si ya existe
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
            self.load_analisis_unitarios()
        except Exception as e:
            session.rollback()
            print(f"Error al agregar análisis {data['codigo']}: {e}")
        finally:
            session.close()

    def delete_analysis(self, codigo):
        """
        Elimina el análisis con el código proporcionado de la base de datos y refresca la vista.
        """
        session = SessionLocal()
        try:
            analisis = session.query(AnalisisUnitario).filter(AnalisisUnitario.codigo == codigo).first()
            if analisis:
                session.delete(analisis)
                session.commit()
                QMessageBox.information(self.view, "Eliminado", f"El análisis '{codigo}' ha sido eliminado.")
                self.load_analisis_unitarios()
            else:
                QMessageBox.warning(self.view, "Error", f"No se encontró un análisis con el código {codigo}.")
        except Exception as e:
            session.rollback()
            QMessageBox.critical(self.view, "Error", f"Error al eliminar el análisis {codigo}: {e}")
        finally:
            session.close()

    def on_data_changed(self, item):
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

        self.load_analisis_unitarios()

    def on_analysis_selected(self, codigo):
        print(f"Análisis seleccionado: {codigo}")
