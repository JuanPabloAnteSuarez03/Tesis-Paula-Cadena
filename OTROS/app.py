import sys
import os
import re
import numpy as np
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QFileDialog, QTreeWidget, QTreeWidgetItem, QSplitter,
    QFrame, QLabel, QHeaderView
)
from PyQt6.QtCore import Qt
import ifcopenshell
import ifcopenshell.geom
import pyvista as pv
from pyvistaqt import QtInteractor

class VisorBIMPresupuesto(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Plexos Clone - Presupuesto con Materiales")
        self.resize(1450, 850)

        self.ifc_file = None
        self.settings = ifcopenshell.geom.settings()
        self.settings.set(self.settings.USE_WORLD_COORDS, True)
        
        self.actor_dict = {}    
        self.group_dict = {}
        
        # TABLA DE PESOS (Acero)
        self.tabla_pesos = {
            "2": 0.248, "3": 0.560, "4": 0.994, "5": 1.552, 
            "6": 2.235, "7": 3.042, "8": 3.973, "9": 5.060, "10": 6.404
        }
        
        self.init_ui()

    def init_ui(self):
        main = QWidget()
        self.setCentralWidget(main)
        layout = QVBoxLayout(main)

        # --- BOTONERA ---
        top = QHBoxLayout()
        btn = QPushButton("📂 Cargar Modelo IFC")
        btn.setStyleSheet("background-color: #2D2D30; color: white; font-weight: bold; padding: 10px; border-radius: 4px;")
        btn.clicked.connect(self.cargar_ifc)
        self.lbl_info = QLabel("Carga el IFC para ver Materiales y Cantidades...")
        top.addWidget(btn)
        top.addWidget(self.lbl_info)
        layout.addLayout(top)

        # --- ÁREA PRINCIPAL ---
        split = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(split)

        # 1. TABLA (Ahora con columna MATERIAL)
        self.tree = QTreeWidget()
        # AQUI AGREGAMOS LA COLUMNA NUEVA
        self.tree.setHeaderLabels(["Partida / Descripción", "Material", "Cantidad", "Unidad", "Tipo IFC"])
        
        # Ajuste de anchos
        self.tree.setColumnWidth(0, 350) # Descripción
        self.tree.setColumnWidth(1, 200) # Material (Nueva)
        self.tree.setColumnWidth(2, 100) # Cantidad
        self.tree.setColumnWidth(3, 80)  # Unidad
        
        self.tree.setStyleSheet("QTreeWidget { font-size: 12px; } QHeaderView::section { background-color: #ddd; padding: 4px; }")
        self.tree.setAlternatingRowColors(True)
        self.tree.itemClicked.connect(self.al_clic_arbol)
        split.addWidget(self.tree)

        # 2. VISOR 3D
        frame = QFrame()
        l3d = QVBoxLayout(frame)
        self.plotter = QtInteractor(frame)
        self.plotter.set_background("white")
        l3d.addWidget(self.plotter.interactor)
        split.addWidget(frame)
        split.setSizes([700, 700])

    def cargar_ifc(self):
        ruta, _ = QFileDialog.getOpenFileName(self, "Abrir", "", "IFC (*.ifc)")
        if not ruta: return

        self.lbl_info.setText("Leyendo materiales y calculando...")
        self.plotter.clear()
        self.tree.clear()
        self.actor_dict = {}
        self.group_dict = {}
        QApplication.processEvents()

        try:
            self.ifc_file = ifcopenshell.open(ruta)
            self.generar_partidas()
            self.plotter.reset_camera()
            self.lbl_info.setText(f"Modelo cargado: {os.path.basename(ruta)}")
        except Exception as e:
            self.lbl_info.setText(f"Error: {e}")

    def obtener_material(self, elem):
        """
        Busca el material asociado al elemento.
        Retorna 'Sin Material' si no encuentra nada.
        """
        material_name = "Sin Definir"
        
        if hasattr(elem, "HasAssociations"):
            for rel in elem.HasAssociations:
                if rel.is_a("IfcRelAssociatesMaterial"):
                    mat = rel.RelatingMaterial
                    
                    # Caso 1: Material Simple
                    if mat.is_a("IfcMaterial"):
                        material_name = mat.Name
                    
                    # Caso 2: Lista de Materiales (toma el primero)
                    elif mat.is_a("IfcMaterialList"):
                        if mat.Materials:
                            material_name = mat.Materials[0].Name
                    
                    # Caso 3: Capas (Muros/Losas) - Toma la capa más gruesa o la primera
                    elif mat.is_a("IfcMaterialLayerSetUsage"):
                        layers = mat.ForLayerSet.MaterialLayers
                        if layers:
                            material_name = layers[0].Material.Name # Tomamos la primera capa principal

        return material_name

    def obtener_nombre_tipo(self, elem):
        nombre_raw = elem.Name if elem.Name else "Elemento"
        partes = nombre_raw.split(':')
        if len(partes) >= 2:
            posible = partes[1]
            if len(posible) > 2: return posible.strip()
        return nombre_raw.split(':')[0]

    def es_metal(self, elem, mat_name):
        """Detecta metal por nombre del elemento O por su material"""
        texto_elem = (elem.Name if elem.Name else "").upper()
        texto_mat = mat_name.upper()
        
        keywords = ["IPE", "HEA", "ACERO", "STEEL", "METAL", "PERFIL", "HIERRO"]
        
        if any(k in texto_elem for k in keywords): return True
        if any(k in texto_mat for k in keywords): return True
        return False

    def generar_partidas(self):
        partidas = {}
        # Tipos a leer
        tipos = ["IfcFooting", "IfcColumn", "IfcBeam", "IfcSlab", "IfcStair", 
                 "IfcWall", "IfcMember", "IfcPlate", "IfcReinforcingBar", "IfcRailing"]

        total_acero_refuerzo = 0.0
        
        for tipo in tipos:
            elementos = self.ifc_file.by_type(tipo)
            
            for elem in elementos:
                # -- ACERO REFUERZO (Va aparte al Total) --
                if tipo == "IfcReinforcingBar":
                    peso = self.calcular_peso_varilla(elem)
                    total_acero_refuerzo += peso
                    continue 

                # -- RESTO DE ELEMENTOS --
                nombre_tipo = self.obtener_nombre_tipo(elem)
                material = self.obtener_material(elem)
                
                # Limpieza de nombres para que se parezca a tu Excel
                if "ZAPATA" in nombre_tipo.upper(): nombre_tipo = "ZAPATA"
                elif "PILAR" in nombre_tipo.upper() or "COLUMNA" in nombre_tipo.upper(): nombre_tipo = "COLUMNA"
                
                es_acero_est = self.es_metal(elem, material)
                
                # Cálculo Cantidad
                props = self.get_propiedades(elem)
                cant = 0; unidad = "UND"

                if es_acero_est:
                    if props['weight'] > 0: cant = props['weight']; unidad = "KLS"
                    elif props['volume'] > 0: cant = props['volume'] * 7850; unidad = "KLS"
                    else: cant = props['length']; unidad = "ML"
                else:
                    if props['volume'] > 0: cant = props['volume']; unidad = "M3"
                    elif props['area'] > 0: cant = props['area']; unidad = "M2"
                    else: cant = 1; unidad = "UND"

                # CLAVE ÚNICA: Nombre + Material + Unidad
                # Esto separa "Columna - 3000 PSI" de "Columna - 4000 PSI"
                clave = f"{nombre_tipo}|{material}|{unidad}"
                
                if clave not in partidas:
                    partidas[clave] = {
                        'nombre': nombre_tipo, 
                        'material': material,
                        'cant': 0.0, 
                        'unidad': unidad, 
                        'ids': [], 
                        'tipo': tipo
                    }
                
                partidas[clave]['cant'] += cant
                partidas[clave]['ids'].append(elem.GlobalId)
                
                self.crear_actor(elem, es_metal=es_acero_est)

        # --- DIBUJAR ÁRBOL ---
        
        # 1. Fila de ACERO TOTAL
        item_acero = QTreeWidgetItem(self.tree)
        item_acero.setText(0, "ACERO REFUERZO FLEJADO (TOTAL)")
        item_acero.setText(1, "Grado 60 / A706") # Material típico
        item_acero.setText(2, "{:,.2f}".format(total_acero_refuerzo))
        item_acero.setText(3, "KLS")
        item_acero.setText(4, "IfcReinforcingBar")
        f = item_acero.font(0); f.setBold(True); item_acero.setFont(0, f)
        item_acero.setBackground(0, Qt.GlobalColor.cyan) # Resaltar acero

        # 2. Filas de Partidas
        for clave, datos in sorted(partidas.items()):
            item = QTreeWidgetItem(self.tree)
            item.setText(0, datos['nombre'])
            item.setText(1, datos['material']) # COLUMNA NUEVA LLENA
            item.setText(2, "{:,.2f}".format(datos['cant']))
            item.setText(3, datos['unidad'])
            item.setText(4, datos['tipo'])
            
            self.group_dict[id(item)] = datos['ids']

    def calcular_peso_varilla(self, elem):
        props = self.get_propiedades(elem)
        longitud = props.get('length', 0)
        if longitud > 20: longitud /= 1000.0
        
        nombre = elem.Name if elem.Name else ""
        peso_metro = 1.0
        
        if "#3" in nombre or "3/8" in nombre: peso_metro = self.tabla_pesos["3"]
        elif "#4" in nombre or "1/2" in nombre: peso_metro = self.tabla_pesos["4"]
        elif "#5" in nombre or "5/8" in nombre: peso_metro = self.tabla_pesos["5"]
        elif "#6" in nombre or "3/4" in nombre: peso_metro = self.tabla_pesos["6"]
        elif "#7" in nombre or "7/8" in nombre: peso_metro = self.tabla_pesos["7"]
        elif "#8" in nombre or "1\"" in nombre: peso_metro = self.tabla_pesos["8"]
        
        return longitud * peso_metro

    def get_propiedades(self, elem):
        data = {'volume': 0.0, 'area': 0.0, 'length': 0.0, 'weight': 0.0}
        # Intenta Quantities estándar
        if hasattr(elem, "IsDefinedBy"):
            for rel in elem.IsDefinedBy:
                if rel.is_a("IfcRelDefinesByProperties"):
                    prop = rel.RelatingPropertyDefinition
                    if prop.is_a("IfcElementQuantity"):
                        for q in prop.Quantities:
                            if getattr(q, "VolumeValue", None): data['volume'] += float(q.VolumeValue)
                            if getattr(q, "AreaValue", None): data['area'] += float(q.AreaValue)
                            if getattr(q, "LengthValue", None): data['length'] += float(q.LengthValue)
                            if getattr(q, "WeightValue", None): data['weight'] += float(q.WeightValue)
        
        # Fallback a Propiedades (Revit Property Sets)
        if data['volume'] == 0:
             if hasattr(elem, "IsDefinedBy"):
                for rel in elem.IsDefinedBy:
                    if rel.is_a("IfcRelDefinesByProperties"):
                        prop = rel.RelatingPropertyDefinition
                        if prop.is_a("IfcPropertySet"):
                            for p in prop.HasProperties:
                                if p.is_a("IfcPropertySingleValue") and p.NominalValue:
                                    v = p.NominalValue.wrappedValue
                                    if isinstance(v, (float, int)):
                                        n = p.Name.lower()
                                        if "volumen" in n or "volume" in n: data['volume'] = v
                                        if "area" in n: data['area'] = v
                                        if "longitud" in n or "length" in n: data['length'] = v
        return data

    def crear_actor(self, elem, es_metal=False):
        try:
            shape = ifcopenshell.geom.create_shape(self.settings, elem)
            geom = shape.geometry
            verts = np.array(geom.verts).reshape(-1, 3)
            faces = np.array(geom.faces).reshape(-1, 3)
            faces_pv = np.hstack([np.full((faces.shape[0], 1), 3), faces]).astype(np.int64)
            mesh = pv.PolyData(verts, faces_pv)
            
            # Colores base
            color = "#A0A0A0" 
            if es_metal: color = "#4682B4"
            elif elem.is_a("IfcFooting"): color = "#8B4513"
            elif elem.is_a("IfcSlab"): color = "#DCDCDC"
            
            actor = self.plotter.add_mesh(mesh, color=color, show_edges=True, line_width=0.5)
            self.actor_dict[elem.GlobalId] = actor
        except:
            pass

    def al_clic_arbol(self, item, col):
        for actor in self.actor_dict.values():
            actor.prop.opacity = 0.1
            actor.prop.color = "#D3D3D3"
        
        identificador = id(item)
        if identificador in self.group_dict:
            ids = self.group_dict[identificador]
            for guid in ids:
                if guid in self.actor_dict:
                    act = self.actor_dict[guid]
                    act.prop.opacity = 1.0
                    act.prop.color = "#FF8C00"
                    act.prop.line_width = 2
        self.plotter.render()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VisorBIMPresupuesto()
    window.show()
    sys.exit(app.exec())