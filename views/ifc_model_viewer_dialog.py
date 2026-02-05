import os
import numpy as np
from PyQt6.QtWidgets import (
    QDialog,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QFileDialog,
    QTreeWidget,
    QTreeWidgetItem,
    QSplitter,
    QFrame,
    QLabel,
    QMessageBox,
    QProgressBar,
    QCheckBox,
    QSizePolicy,
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QCloseEvent

import ifcopenshell
import ifcopenshell.geom
import pyvista as pv
from pyvistaqt import QtInteractor


class _IFCOpenWorker(QThread):
    opened = pyqtSignal(object)
    failed = pyqtSignal(str)

    def __init__(self, path: str):
        super().__init__()
        self._path = path

    def run(self):
        try:
            model = ifcopenshell.open(self._path)
        except Exception as exc:
            self.failed.emit(str(exc))
            return
        self.opened.emit(model)


class IFCModelViewerDialog(QDialog):
    loading_finished = pyqtSignal()
    size_changed = pyqtSignal()
    def __init__(self, parent=None, embedded: bool = False, show_table: bool = True, show_controls: bool = True):
        super().__init__(parent)
        self._embedded = embedded
        self._show_table = show_table
        self._show_controls = show_controls
        self._base_size = (1600, 900)
        self.setWindowTitle("Visor IFC - Modelo y Componentes")
        self.resize(*self._base_size)
        
        if embedded:
            self.setWindowFlags(Qt.WindowType.Widget)
            self.setModal(False)
            # Permitir que el visor embebido se ajuste al panel de recursos
            self.setMinimumSize(0, 0)
            self.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
            )
        else:
            # Ventana normal redimensionable con tamaño mínimo
            self.setMinimumSize(800, 600)

        self.ifc_file = None
        self.settings = ifcopenshell.geom.settings()
        self.settings.set(self.settings.USE_WORLD_COORDS, True)

        self.actor_dict = {}
        self.group_dict = {}

        self._worker = None
        self._pending_elements = []
        self._pending_index = 0
        self._geom_index = 0
        self._geom_elements = []
        self._cancel_geometry = False
        self._partidas = {}
        self._total_acero_refuerzo = 0.0

        # TABLA DE PESOS (Acero)
        self.tabla_pesos = {
            "2": 0.248, "3": 0.560, "4": 0.994, "5": 1.552,
            "6": 2.235, "7": 3.042, "8": 3.973, "9": 5.060, "10": 6.404,
        }

        self._ifc_path = None
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        if self._embedded:
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)

        top = QHBoxLayout()
        self.btn_load = QPushButton("Cargar Modelo IFC")
        self.btn_load.setStyleSheet(
            "QPushButton { "
            "background-color: #007ACC; color: white; font-weight: bold; "
            "padding: 10px; border-radius: 4px; } "
            "QPushButton:hover { background-color: #005A9E; }"
        )
        self.btn_load.clicked.connect(self._load_ifc)
        self.lbl_info = QLabel("Carga el IFC para ver materiales y cantidades...")
        top.addWidget(self.btn_load)
        top.addWidget(self.lbl_info)
        if self._show_controls:
            layout.addLayout(top)
        else:
            self.btn_load.setVisible(False)
            self.lbl_info.setVisible(False)

        self.warn_label = QLabel(
            "Aviso: cargar geometría completa en archivos grandes puede tardar bastante. "
            "Si solo necesita la tabla, desactive la geometría."
        )
        self.warn_label.setWordWrap(True)
        if self._show_controls:
            layout.addWidget(self.warn_label)
        else:
            self.warn_label.setVisible(False)

        opt_layout = QHBoxLayout()
        self.chk_load_geometry = QCheckBox("Cargar geometría 3D")
        self.chk_load_geometry.setChecked(True)
        opt_layout.addWidget(self.chk_load_geometry)
        self.chk_fast_preview = QCheckBox("Vista rápida (menos detalle)")
        self.chk_fast_preview.setChecked(True)
        opt_layout.addWidget(self.chk_fast_preview)
        opt_layout.addStretch(1)
        if self._show_controls:
            layout.addLayout(opt_layout)
        else:
            self.chk_load_geometry.setVisible(False)
            self.chk_fast_preview.setVisible(False)

        self.progress_widget = QWidget(self)
        prog_layout = QHBoxLayout(self.progress_widget)
        prog_layout.setContentsMargins(0, 0, 0, 0)
        prog_layout.setSpacing(8)
        self.progress_label = QLabel("Procesando IFC...")
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        prog_layout.addWidget(self.progress_label)
        prog_layout.addWidget(self.progress_bar, 1)
        self.btn_cancel_geom = QPushButton("Interrumpir carga 3D")
        self.btn_cancel_geom.clicked.connect(self._cancel_geometry_load)
        self.btn_cancel_geom.setEnabled(False)
        prog_layout.addWidget(self.btn_cancel_geom)
        self.progress_widget.setVisible(False)
        layout.addWidget(self.progress_widget)

        split = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(split)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(
            ["Partida / Descripción", "Material", "Cantidad", "Unidad", "Tipo IFC"]
        )
        self.tree.setColumnWidth(0, 350)
        self.tree.setColumnWidth(1, 200)
        self.tree.setColumnWidth(2, 100)
        self.tree.setColumnWidth(3, 80)
        self.tree.setStyleSheet(
            "QTreeWidget { background-color: #f9f9f9; gridline-color: #cccccc; font-size: 14px; } "
            "QTreeWidget::item:hover { background-color: #e6f2ff; } "
            "QHeaderView::section { background-color: #0078d7; color: white; padding: 4px; font-weight: bold; }"
        )
        self.tree.setAlternatingRowColors(True)
        self.tree.itemClicked.connect(self._on_tree_item_clicked)
        if self._show_table:
            split.addWidget(self.tree)
        else:
            self.tree.setVisible(False)

        frame = QFrame()
        l3d = QVBoxLayout(frame)
        if self._embedded:
            l3d.setContentsMargins(0, 0, 0, 0)
            l3d.setSpacing(0)
        self.plotter = QtInteractor(frame)
        self.plotter.set_background("white")
        l3d.addWidget(self.plotter.interactor)
        split.addWidget(frame)
        if self._show_table:
            split.setSizes([700, 700])

        btns = QHBoxLayout()
        self.btn_generate = QPushButton("Generar ítems…")
        self.btn_close = QPushButton("Cerrar")
        self.btn_generate.clicked.connect(self._generate_items_from_tree)
        self.btn_close.clicked.connect(self.accept)
        for btn in (self.btn_generate, self.btn_close):
            btn.setStyleSheet(
                "QPushButton { "
                "background-color: #007ACC; color: white; border-radius: 4px; "
                "padding: 8px; min-width: 120px; } "
                "QPushButton:hover { background-color: #005A9E; }"
            )
        btns.addStretch(1)
        btns.addWidget(self.btn_generate)
        btns.addWidget(self.btn_close)
        if self._show_controls:
            layout.addLayout(btns)
        else:
            self.btn_generate.setVisible(False)
            self.btn_close.setVisible(False)

        self.btn_generate.setEnabled(False)
        if self._embedded:
            self.btn_close.setVisible(False)

    def _load_ifc(self):
        ruta = self.select_and_load_ifc()
        if not ruta:
            return

    def select_and_load_ifc(self):
        ruta, _ = QFileDialog.getOpenFileName(self, "Abrir", "", "IFC (*.ifc)")
        if not ruta:
            return None
        self.load_ifc_path(ruta)
        return ruta

    def load_ifc_model(self, model, ruta=None):
        if model is None:
            return
        if ruta:
            self._ifc_path = ruta
        self._reset_view_for_load()
        self.ifc_file = model
        self._prepare_processing()
        self._process_next_chunk()
    
    def copy_state_from(self, other_dialog):
        """Copia el estado completo de otro diálogo (modelo, partidas, geometría) para evitar reprocesar."""
        if not other_dialog or not hasattr(other_dialog, 'ifc_file') or not other_dialog.ifc_file:
            print("copy_state_from: diálogo fuente inválido")
            return False
        
        try:
            # Copiar modelo y ruta
            self.ifc_file = other_dialog.ifc_file
            self._ifc_path = getattr(other_dialog, '_ifc_path', None)
            
            # Copiar partidas procesadas
            self._partidas = other_dialog._partidas.copy() if hasattr(other_dialog, '_partidas') and other_dialog._partidas else {}
            self._total_acero_refuerzo = getattr(other_dialog, '_total_acero_refuerzo', 0.0)
            
            # Copiar diccionarios de geometría
            self.actor_dict = {}
            self.group_dict = {}
            
            # Copiar elementos procesados
            self._pending_elements = list(getattr(other_dialog, '_pending_elements', []))
            self._geom_elements = list(getattr(other_dialog, '_geom_elements', []))
            
            # Limpiar vista
            self.plotter.clear()
            if hasattr(self, 'tree') and self.tree:
                self.tree.clear()
            
            # En modo embebido, cargar geometría de forma lazy desde los elementos ya procesados
            if self._embedded and self._geom_elements:
                # Cargar geometría en segundo plano sin mostrar progreso
                self._geom_index = 0
                self._cancel_geometry = False
                from PyQt6.QtCore import QTimer
                QTimer.singleShot(100, lambda: self._load_geometry_lazy())
            
            # Reconstruir el árbol solo si está visible
            if hasattr(self, 'tree') and self.tree and self._show_table:
                # Agregar acero refuerzo
                if self._total_acero_refuerzo > 0:
                    item_acero = QTreeWidgetItem(self.tree)
                    item_acero.setText(0, "ACERO REFUERZO FLEJADO (TOTAL)")
                    item_acero.setText(1, "Grado 60 / A706")
                    item_acero.setText(2, f"{self._total_acero_refuerzo:,.2f}")
                    item_acero.setText(3, "KLS")
                    item_acero.setText(4, "IfcReinforcingBar")
                    item_acero.setData(2, Qt.ItemDataRole.UserRole, self._total_acero_refuerzo)
                    f = item_acero.font(0)
                    f.setBold(True)
                    item_acero.setFont(0, f)
                    item_acero.setBackground(0, Qt.GlobalColor.cyan)
                
                # Agregar partidas
                for clave, datos in sorted(self._partidas.items()):
                    item = QTreeWidgetItem(self.tree)
                    item.setText(0, datos["nombre"])
                    item.setText(1, datos["material"])
                    item.setText(2, f"{datos['cant']:,.2f}")
                    item.setText(3, datos["unidad"])
                    item.setText(4, datos["tipo"])
                    item.setData(2, Qt.ItemDataRole.UserRole, datos["cant"])
                    self.group_dict[id(item)] = datos["ids"]
            
            self.plotter.reset_camera()
            if hasattr(self, 'btn_generate'):
                if self._embedded:
                    self.btn_generate.setEnabled(False)
                else:
                    self.btn_generate.setEnabled(True)
            
            if self._show_controls and hasattr(self, 'lbl_info'):
                self.lbl_info.setText("Modelo cargado desde memoria.")
            self._hide_progress()
            
            print(f"copy_state_from: Estado copiado exitosamente. Partidas: {len(self._partidas)}, Geometría: {len(self.actor_dict)}")
            return True
        except Exception as e:
            import traceback
            print(f"Error copiando estado: {e}")
            traceback.print_exc()
            return False

    def load_ifc_path(self, ruta: str):
        if not ruta:
            return
        self._reset_view_for_load()

        self.btn_load.setEnabled(False)
        self.btn_generate.setEnabled(False)
        self._ifc_path = ruta
        self._worker = _IFCOpenWorker(ruta)
        self._worker.opened.connect(self._on_ifc_opened)
        self._worker.failed.connect(self._on_ifc_failed)
        self._worker.start()

    def _reset_view_for_load(self):
        self._show_progress("Abriendo IFC... (esto puede tardar)")
        if self._show_controls:
            self.lbl_info.setText("Abriendo IFC...")
        self.plotter.clear()
        self.tree.clear()
        self.actor_dict = {}
        self.group_dict = {}

    def get_loaded_path(self):
        return self._ifc_path

    def get_loaded_model(self):
        return self.ifc_file

    def _get_material_name(self, elem):
        material_name = "Sin Definir"
        if hasattr(elem, "HasAssociations"):
            for rel in elem.HasAssociations:
                if rel.is_a("IfcRelAssociatesMaterial"):
                    mat = rel.RelatingMaterial
                    if mat.is_a("IfcMaterial"):
                        material_name = mat.Name
                    elif mat.is_a("IfcMaterialList") and mat.Materials:
                        material_name = mat.Materials[0].Name
                    elif mat.is_a("IfcMaterialLayerSetUsage"):
                        layers = mat.ForLayerSet.MaterialLayers
                        if layers:
                            material_name = layers[0].Material.Name
        return material_name

    def _get_type_name(self, elem):
        nombre_raw = elem.Name if elem.Name else "Elemento"
        partes = nombre_raw.split(":")
        if len(partes) >= 2:
            posible = partes[1]
            if len(posible) > 2:
                return posible.strip()
        return nombre_raw.split(":")[0]

    def _is_metal(self, elem, mat_name):
        texto_elem = (elem.Name if elem.Name else "").upper()
        texto_mat = mat_name.upper()
        keywords = ["IPE", "HEA", "ACERO", "STEEL", "METAL", "PERFIL", "HIERRO"]
        return any(k in texto_elem for k in keywords) or any(k in texto_mat for k in keywords)

    def _on_ifc_opened(self, model):
        self.ifc_file = model
        self._prepare_processing()
        self._process_next_chunk()

    def _on_ifc_failed(self, message: str):
        self._hide_progress()
        QMessageBox.critical(self, "Error", f"No se pudo cargar el IFC:\n{message}")
        self.lbl_info.setText("Error al cargar el IFC.")
        self.btn_load.setEnabled(True)
        self.btn_generate.setEnabled(False)

    def _prepare_processing(self):
        self._pending_elements = []
        self._pending_index = 0
        self._geom_index = 0
        self._geom_elements = []
        self._cancel_geometry = False
        self._partidas = {}
        self._total_acero_refuerzo = 0.0

        tipos = [
            "IfcFooting", "IfcColumn", "IfcBeam", "IfcSlab", "IfcStair",
            "IfcWall", "IfcMember", "IfcPlate", "IfcReinforcingBar", "IfcRailing",
        ]
        for tipo in tipos:
            for elem in self.ifc_file.by_type(tipo):
                self._pending_elements.append((tipo, elem))

        total = len(self._pending_elements)
        self._show_progress(f"Procesando elementos: 0/{total}", determinate=True, maximum=max(total, 1))

        # Preparar lista de geometría con vista rápida si aplica
        if self.chk_fast_preview.isChecked():
            fast_types = {"IfcWall", "IfcSlab", "IfcColumn", "IfcBeam", "IfcFooting", "IfcStair"}
            geom_list = [pair for pair in self._pending_elements if pair[0] in fast_types]
            max_geom = 1500
            if len(geom_list) > max_geom:
                step = max(1, len(geom_list) // max_geom)
                geom_list = geom_list[::step]
            self._geom_elements = geom_list
        else:
            self._geom_elements = list(self._pending_elements)

    def _process_next_chunk(self):
        total = len(self._pending_elements)
        if self._pending_index >= total:
            self._finalize_processing()
            return

        chunk = 40
        end = min(self._pending_index + chunk, total)
        for i in range(self._pending_index, end):
            tipo, elem = self._pending_elements[i]
            if tipo == "IfcReinforcingBar":
                self._total_acero_refuerzo += self._calc_rebar_weight(elem)
                continue

            nombre_tipo = self._get_type_name(elem)
            material = self._get_material_name(elem)

            if "ZAPATA" in nombre_tipo.upper():
                nombre_tipo = "ZAPATA"
            elif "PILAR" in nombre_tipo.upper() or "COLUMNA" in nombre_tipo.upper():
                nombre_tipo = "COLUMNA"

            es_acero_est = self._is_metal(elem, material)
            props = self._get_properties(elem)
            cant = 0.0
            unidad = "UND"

            if es_acero_est:
                if props["weight"] > 0:
                    cant = props["weight"]
                    unidad = "KLS"
                elif props["volume"] > 0:
                    cant = props["volume"] * 7850
                    unidad = "KLS"
                else:
                    cant = props["length"]
                    unidad = "ML"
            else:
                if props["volume"] > 0:
                    cant = props["volume"]
                    unidad = "M3"
                elif props["area"] > 0:
                    cant = props["area"]
                    unidad = "M2"
                else:
                    cant = 1.0
                    unidad = "UND"

            clave = f"{nombre_tipo}|{material}|{unidad}"
            if clave not in self._partidas:
                self._partidas[clave] = {
                    "nombre": nombre_tipo,
                    "material": material,
                    "cant": 0.0,
                    "unidad": unidad,
                    "ids": [],
                    "tipo": tipo,
                }

            self._partidas[clave]["cant"] += cant
            self._partidas[clave]["ids"].append(elem.GlobalId)

            # La geometría se carga en una segunda fase con progreso

        self._pending_index = end
        self.progress_bar.setValue(self._pending_index)
        self.progress_label.setText(f"Procesando elementos: {self._pending_index}/{total}")
        QTimer.singleShot(0, self._process_next_chunk)

    def _finalize_processing(self):
        item_acero = QTreeWidgetItem(self.tree)
        item_acero.setText(0, "ACERO REFUERZO FLEJADO (TOTAL)")
        item_acero.setText(1, "Grado 60 / A706")
        item_acero.setText(2, f"{self._total_acero_refuerzo:,.2f}")
        item_acero.setText(3, "KLS")
        item_acero.setText(4, "IfcReinforcingBar")
        item_acero.setData(2, Qt.ItemDataRole.UserRole, self._total_acero_refuerzo)
        f = item_acero.font(0)
        f.setBold(True)
        item_acero.setFont(0, f)
        item_acero.setBackground(0, Qt.GlobalColor.cyan)

        for clave, datos in sorted(self._partidas.items()):
            item = QTreeWidgetItem(self.tree)
            item.setText(0, datos["nombre"])
            item.setText(1, datos["material"])
            item.setText(2, f"{datos['cant']:,.2f}")
            item.setText(3, datos["unidad"])
            item.setText(4, datos["tipo"])
            item.setData(2, Qt.ItemDataRole.UserRole, datos["cant"])
            self.group_dict[id(item)] = datos["ids"]

        self.plotter.reset_camera()
        if self.chk_load_geometry.isChecked():
            self._start_geometry_load()
        else:
            self._hide_progress()
            self.btn_generate.setEnabled(True)
            self.btn_load.setToolTip("Ya hay un IFC cargado.")
            self.lbl_info.setText("Modelo cargado (sin geometría).")
            self.loading_finished.emit()

    def _calc_rebar_weight(self, elem):
        props = self._get_properties(elem)
        longitud = props.get("length", 0.0)
        if longitud > 20:
            longitud /= 1000.0

        nombre = elem.Name if elem.Name else ""
        peso_metro = 1.0
        if "#3" in nombre or "3/8" in nombre:
            peso_metro = self.tabla_pesos["3"]
        elif "#4" in nombre or "1/2" in nombre:
            peso_metro = self.tabla_pesos["4"]
        elif "#5" in nombre or "5/8" in nombre:
            peso_metro = self.tabla_pesos["5"]
        elif "#6" in nombre or "3/4" in nombre:
            peso_metro = self.tabla_pesos["6"]
        elif "#7" in nombre or "7/8" in nombre:
            peso_metro = self.tabla_pesos["7"]
        elif "#8" in nombre or "1\"" in nombre:
            peso_metro = self.tabla_pesos["8"]
        return longitud * peso_metro

    def _get_properties(self, elem):
        data = {"volume": 0.0, "area": 0.0, "length": 0.0, "weight": 0.0}
        if hasattr(elem, "IsDefinedBy"):
            for rel in elem.IsDefinedBy:
                if rel.is_a("IfcRelDefinesByProperties"):
                    prop = rel.RelatingPropertyDefinition
                    if prop.is_a("IfcElementQuantity"):
                        for q in prop.Quantities:
                            if getattr(q, "VolumeValue", None):
                                data["volume"] += float(q.VolumeValue)
                            if getattr(q, "AreaValue", None):
                                data["area"] += float(q.AreaValue)
                            if getattr(q, "LengthValue", None):
                                data["length"] += float(q.LengthValue)
                            if getattr(q, "WeightValue", None):
                                data["weight"] += float(q.WeightValue)

        if data["volume"] == 0 and hasattr(elem, "IsDefinedBy"):
            for rel in elem.IsDefinedBy:
                if rel.is_a("IfcRelDefinesByProperties"):
                    prop = rel.RelatingPropertyDefinition
                    if prop.is_a("IfcPropertySet"):
                        for p in prop.HasProperties:
                            if p.is_a("IfcPropertySingleValue") and p.NominalValue:
                                v = p.NominalValue.wrappedValue
                                if isinstance(v, (float, int)):
                                    n = p.Name.lower()
                                    if "volumen" in n or "volume" in n:
                                        data["volume"] = v
                                    if "area" in n:
                                        data["area"] = v
                                    if "longitud" in n or "length" in n:
                                        data["length"] = v
        return data

    def _create_actor(self, elem, es_metal=False):
        try:
            shape = ifcopenshell.geom.create_shape(self.settings, elem)
            geom = shape.geometry
            verts = np.array(geom.verts).reshape(-1, 3)
            faces = np.array(geom.faces).reshape(-1, 3)
            faces_pv = np.hstack(
                [np.full((faces.shape[0], 1), 3), faces]
            ).astype(np.int64)
            mesh = pv.PolyData(verts, faces_pv)

            color = "#A0A0A0"
            if es_metal:
                color = "#4682B4"
            elif elem.is_a("IfcFooting"):
                color = "#8B4513"
            elif elem.is_a("IfcSlab"):
                color = "#DCDCDC"

            actor = self.plotter.add_mesh(
                mesh,
                color=color,
                show_edges=False,
                smooth_shading=False,
                line_width=0.0,
            )
            self.actor_dict[elem.GlobalId] = actor
        except Exception:
            pass

    def _on_tree_item_clicked(self, item, _col):
        for actor in self.actor_dict.values():
            actor.prop.opacity = 0.1
            actor.prop.color = "#D3D3D3"

        identificador = id(item)
        if identificador in self.group_dict:
            for guid in self.group_dict[identificador]:
                if guid in self.actor_dict:
                    act = self.actor_dict[guid]
                    act.prop.opacity = 1.0
                    act.prop.color = "#FF8C00"
                    act.prop.line_width = 2
        self.plotter.render()

    def _load_geometry_lazy(self):
        """Carga geometría de forma lazy sin mostrar progreso (para modo embebido)."""
        total = len(self._geom_elements)
        if self._geom_index >= total:
            return
        
        chunk = 25  # Cargar en chunks pequeños
        end = min(self._geom_index + chunk, total)
        for i in range(self._geom_index, end):
            _tipo, elem = self._geom_elements[i]
            try:
                material = self._get_material_name(elem)
                es_metal = self._is_metal(elem, material)
                self._create_actor(elem, es_metal=es_metal)
            except Exception:
                continue
        
        self._geom_index = end
        if self._geom_index < total:
            # Continuar cargando en el siguiente chunk
            QTimer.singleShot(10, self._load_geometry_lazy)
        else:
            # Terminado, renderizar
            try:
                self.plotter.reset_camera()
                self.plotter.render()
            except Exception:
                pass

    def _start_geometry_load(self):
        total = len(self._geom_elements)
        self._show_progress(f"Cargando geometría: 0/{total}", determinate=True, maximum=max(total, 1))
        self._geom_index = 0
        self._cancel_geometry = False
        self.btn_cancel_geom.setEnabled(True)
        QTimer.singleShot(0, self._process_geometry_chunk)

    def _process_geometry_chunk(self):
        total = len(self._geom_elements)
        if self._cancel_geometry:
            self._hide_progress()
            self.btn_generate.setEnabled(True)
            self.btn_load.setToolTip("Ya hay un IFC cargado.")
            self.lbl_info.setText("Geometría detenida por el usuario.")
            self.loading_finished.emit()
            return
        if self._geom_index >= total:
            self._hide_progress()
            self.btn_generate.setEnabled(True)
            self.btn_load.setToolTip("Ya hay un IFC cargado.")
            self.lbl_info.setText("Modelo cargado.")
            self.loading_finished.emit()
            return

        chunk = 25 if self.chk_fast_preview.isChecked() else 15
        end = min(self._geom_index + chunk, total)
        for i in range(self._geom_index, end):
            _tipo, elem = self._geom_elements[i]
            try:
                material = self._get_material_name(elem)
                es_metal = self._is_metal(elem, material)
                self._create_actor(elem, es_metal=es_metal)
            except Exception:
                continue

        self._geom_index = end
        self.progress_bar.setValue(self._geom_index)
        self.progress_label.setText(f"Cargando geometría: {self._geom_index}/{total}")
        QTimer.singleShot(0, self._process_geometry_chunk)

    def _generate_items_from_tree(self):
        prefill_rows = []
        total_items = 0

        for idx in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(idx)
            if not item:
                continue
            nombre = (item.text(0) or "").strip()
            material = (item.text(1) or "").strip()
            unidad = (item.text(3) or "").strip()
            qty_item = item.data(2, Qt.ItemDataRole.UserRole)
            try:
                cantidad = float(qty_item) if qty_item is not None else 0.0
            except Exception:
                cantidad = 0.0
            if cantidad <= 0:
                try:
                    cantidad = float((item.text(2) or "0").replace(",", ""))
                except Exception:
                    cantidad = 0.0
            if cantidad <= 0:
                continue

            desc = nombre
            if material:
                desc = f"{nombre} - {material}"
            prefill_rows.append(
                {
                    "item": "",
                    "descripcion": desc,
                    "unidad": unidad,
                    "cantidad": round(cantidad, 3),
                }
            )
            total_items += 1

        if not prefill_rows:
            QMessageBox.information(self, "Sin datos", "No hay cantidades para enviar.")
            return

        try:
            parent = self.parent()
            if hasattr(parent, "open_import_text_dialog"):
                parent.open_import_text_dialog(prefill_rows=prefill_rows, append=True)
            else:
                from .importar_por_texto_dialog import ImportarPorTextoDialog
                dlg = ImportarPorTextoDialog(self, prefill_rows=prefill_rows)
                dlg.exec()
        except Exception as exc:
            QMessageBox.critical(self, "Error", f"No se pudo abrir Importar por Texto:\n{exc}")

    def closeEvent(self, event: QCloseEvent):
        try:
            self.plotter.close()
        except Exception:
            pass
        super().closeEvent(event)


    def resizeEvent(self, event):
        """Maneja el redimensionamiento normal sin efectos secundarios."""
        super().resizeEvent(event)
        # Ya no emitimos señal para evitar bugs visuales al redimensionar



    def _show_progress(self, message: str, determinate: bool = False, maximum: int = 0):
        self.progress_label.setText(message)
        if determinate:
            self.progress_bar.setRange(0, maximum)
            self.progress_bar.setValue(0)
        else:
            self.progress_bar.setRange(0, 0)
        self.progress_widget.setVisible(True)
        self.btn_close.setEnabled(False)

    def _hide_progress(self):
        self.progress_widget.setVisible(False)
        self.btn_close.setEnabled(True)
        self.btn_cancel_geom.setEnabled(False)

    def _cancel_geometry_load(self):
        self._cancel_geometry = True

