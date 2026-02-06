import os
import random
import time
from typing import Optional
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
        self._mesh_cache = {}

        self._mesh_cache_hits = 0
        self._mesh_cache_misses = 0
        self._mesh_cache_stores = 0
        self._actors_created = 0
        self._shape_time_total_s = 0.0
        self._t_processing_start = None
        self._t_geometry_start = None
        self._t_ifc_open_start = None
        self._safe_render_token = 0
        self._pending_highlight_guids = None

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

    def _has_loaded_model(self) -> bool:
        try:
            return bool(self.ifc_file) or bool(self._ifc_path) or bool(self.actor_dict)
        except Exception:
            return False

    def unload_model(self):
        try:
            try:
                self._cancel_geometry = True
            except Exception:
                pass

            try:
                self._pending_highlight_guids = None
            except Exception:
                pass

            try:
                self.ifc_file = None
            except Exception:
                pass
            try:
                self._ifc_path = None
            except Exception:
                pass

            try:
                self._worker = None
            except Exception:
                pass

            try:
                self._pending_elements = []
                self._pending_index = 0
                self._geom_index = 0
                self._geom_elements = []
                self._partidas = {}
                self._total_acero_refuerzo = 0.0
            except Exception:
                pass

            try:
                self.actor_dict = {}
                self.group_dict = {}
                self._mesh_cache = {}
            except Exception:
                pass

            try:
                if hasattr(self, 'plotter') and self.plotter is not None:
                    self.plotter.clear()
                    try:
                        self.plotter.set_background("white")
                    except Exception:
                        pass
            except Exception:
                pass
            try:
                if hasattr(self, 'tree') and self.tree is not None:
                    self.tree.clear()
            except Exception:
                pass

            try:
                self._hide_progress()
            except Exception:
                pass

            try:
                if hasattr(self, 'btn_generate'):
                    self.btn_generate.setEnabled(False)
                if hasattr(self, 'btn_load'):
                    self.btn_load.setEnabled(True)
                    self.btn_load.setToolTip("")
                if hasattr(self, 'btn_delete'):
                    self.btn_delete.setEnabled(False)
                if hasattr(self, 'lbl_info') and self._show_controls:
                    self.lbl_info.setText("Carga el IFC para ver materiales y cantidades...")
            except Exception:
                pass

            try:
                self.request_render(reset_camera=True, tag="unload_model")
            except Exception:
                pass
        except Exception:
            pass

    def _log(self, msg: str):
        try:
            if os.environ.get('APP_IFC_LOGS', '1') != '1':
                return
        except Exception:
            pass
        try:
            mode = 'EMBED' if getattr(self, '_embedded', False) else 'DIALOG'
            show_table = 'T' if getattr(self, '_show_table', False) else 'F'
            show_ctrl = 'T' if getattr(self, '_show_controls', False) else 'F'
            path = getattr(self, '_ifc_path', None)
            p = os.path.basename(path) if path else 'NOFILE'
            print(f"[IFC:{mode} tbl={show_table} ctrl={show_ctrl} file={p}] {msg}")
        except Exception:
            pass

    def _render_target_ready(self) -> bool:
        try:
            if not hasattr(self, 'plotter') or self.plotter is None:
                return False
            w = int(self.plotter.interactor.width())
            h = int(self.plotter.interactor.height())
            if w <= 10 or h <= 10:
                return False
            if not self.plotter.interactor.isVisible():
                return False
            return True
        except Exception:
            return False

    def _safe_render_deferred(self, reset_camera: bool = False, tag: str = "render", attempt: int = 0, token: Optional[int] = None):
        try:
            if token is None:
                self._safe_render_token += 1
                token = self._safe_render_token
            if token != self._safe_render_token:
                return
        except Exception:
            pass

        if attempt >= 30:
            try:
                self._log(f"{tag}: giveup (not ready)")
            except Exception:
                pass
            return

        if not self._render_target_ready():
            QTimer.singleShot(100, lambda: self._safe_render_deferred(reset_camera=reset_camera, tag=tag, attempt=attempt + 1, token=token))
            return

        try:
            if reset_camera:
                self.plotter.reset_camera()
            self.plotter.render()
        except Exception as e:
            try:
                self._log(f"{tag}: render failed: {e}")
            except Exception:
                pass

    def request_render(self, reset_camera: bool = False, tag: str = "request_render"):
        try:
            self._safe_render_deferred(reset_camera=reset_camera, tag=tag)
        except Exception:
            pass

    def clear_highlight(self):
        try:
            self.reset_visualization()
        except Exception:
            pass

    def highlight_guids(self, guids):
        try:
            if not guids:
                self.reset_visualization()
                return

            if isinstance(guids, str):
                gids = [guids]
            else:
                try:
                    gids = list(guids)
                except Exception:
                    gids = []

            if not gids:
                self.reset_visualization()
                return

            # If geometry hasn't been mounted yet, defer highlighting
            try:
                if not self.actor_dict:
                    self._pending_highlight_guids = gids
                    return
            except Exception:
                pass

            targets = []
            for guid in gids:
                try:
                    act = self.actor_dict.get(guid)
                    if act is not None:
                        targets.append(act)
                except Exception:
                    continue
            if not targets:
                self.reset_visualization()
                return

            for actor in self.actor_dict.values():
                try:
                    actor.prop.opacity = 1.0
                    actor.prop.color = "#D3D3D3"
                    actor.prop.line_width = 1
                except Exception:
                    pass

            for guid in gids:
                try:
                    act = self.actor_dict.get(guid)
                    if act is None:
                        continue
                    act.prop.opacity = 1.0
                    act.prop.color = "#FF8C00"
                    act.prop.line_width = 3
                except Exception:
                    continue

            self.request_render(reset_camera=False, tag="highlight_guids")
        except Exception:
            pass

    def _apply_render_quality_deferred(self, attempt: int = 0):
        try:
            if os.environ.get('APP_IFC_EDL', '0') != '1':
                return
        except Exception:
            return

        try:
            if getattr(self, '_embedded', False):
                return
        except Exception:
            return

        if attempt >= 30:
            return
        if not self._render_target_ready():
            QTimer.singleShot(100, lambda: self._apply_render_quality_deferred(attempt + 1))
            return
        try:
            if hasattr(self, 'chk_fast_preview') and (not self.chk_fast_preview.isChecked()):
                self.plotter.enable_eye_dome_lighting()
        except Exception:
            pass

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
        self.btn_delete = QPushButton("Eliminar")
        self.btn_delete.setStyleSheet(
            "QPushButton { "
            "background-color: #B00020; color: white; font-weight: bold; "
            "padding: 10px; border-radius: 4px; } "
            "QPushButton:hover { background-color: #7A0016; }"
        )
        self.btn_delete.clicked.connect(self.unload_model)
        self.btn_delete.setEnabled(False)
        self.lbl_info = QLabel("Carga el IFC para ver materiales y cantidades...")
        top.addWidget(self.btn_load)
        top.addWidget(self.btn_delete)
        top.addWidget(self.lbl_info)
        if self._show_controls:
            layout.addLayout(top)
        else:
            self.btn_load.setVisible(False)
            self.btn_delete.setVisible(False)
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
        # Install event filter to detect clicks on empty space
        self.tree.viewport().installEventFilter(self)
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
        if not self.chk_fast_preview.isChecked():
            self._apply_render_quality_deferred()
        l3d.addWidget(self.plotter.interactor)
        # Install event filter on plotter to detect clicks outside table
        self.plotter.interactor.installEventFilter(self)
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
        
        # Install event filter on dialog itself to detect clicks on background
        self.installEventFilter(self)

    def _load_ifc(self):
        try:
            if self._has_loaded_model():
                QMessageBox.information(self, "Modelo ya cargado", "Ya hay un modelo IFC cargado. Elimina el modelo actual para cargar otro.")
                return
        except Exception:
            pass

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
            t0 = time.perf_counter()
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

            try:
                other_cache = getattr(other_dialog, '_mesh_cache', None)
                if isinstance(other_cache, dict) and other_cache:
                    self._mesh_cache = other_cache.copy()
                else:
                    self._mesh_cache = {}
            except Exception:
                self._mesh_cache = {}

            # Sincronizar configuración visual (evita que el embebido use "vista rápida" por defecto)
            try:
                if hasattr(self, 'chk_fast_preview') and hasattr(other_dialog, 'chk_fast_preview'):
                    self.chk_fast_preview.setChecked(bool(other_dialog.chk_fast_preview.isChecked()))
                if hasattr(self, 'chk_load_geometry') and hasattr(other_dialog, 'chk_load_geometry'):
                    self.chk_load_geometry.setChecked(bool(other_dialog.chk_load_geometry.isChecked()))

                self._apply_render_quality_deferred()
            except Exception:
                pass

            try:
                self._mesh_cache_hits = 0
                self._mesh_cache_misses = 0
                self._mesh_cache_stores = 0
                self._actors_created = 0
                self._shape_time_total_s = 0.0
            except Exception:
                pass
            
            # Copiar group_dict si existe (para interacción con el árbol)
            if hasattr(other_dialog, 'group_dict') and other_dialog.group_dict:
                # Necesitamos reconstruir el group_dict después de crear los items del árbol
                # Por ahora lo copiamos temporalmente
                self._temp_group_dict = other_dialog.group_dict.copy()
            
            # Limpiar vista
            self.plotter.clear()
            try:
                self.plotter.set_background("white")
            except Exception:
                pass
            if hasattr(self, 'tree') and self.tree:
                self.tree.clear()
            
            # En modo embebido, recrear geometría desde elementos ya procesados (más rápido que procesar desde cero)
            if self._embedded and self._geom_elements:
                # Cargar geometría de forma rápida desde elementos ya identificados
                print(f"copy_state_from: Recreando geometría desde {len(self._geom_elements)} elementos ya procesados...")
                self._geom_index = 0
                self._cancel_geometry = False
                # Cargar en chunks pequeños para mantener UI responsive
                from PyQt6.QtCore import QTimer
                QTimer.singleShot(50, self._load_geometry_fast)
            
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
            
            if hasattr(self, 'btn_generate'):
                if self._embedded:
                    self.btn_generate.setEnabled(False)
                else:
                    self.btn_generate.setEnabled(True)

            try:
                if hasattr(self, 'btn_load'):
                    self.btn_load.setToolTip("Ya hay un IFC cargado.")
                if hasattr(self, 'btn_delete') and (not self._embedded):
                    self.btn_delete.setEnabled(True)
            except Exception:
                pass
            
            if self._show_controls and hasattr(self, 'lbl_info'):
                self.lbl_info.setText("Modelo cargado desde memoria.")
            self._hide_progress()
            
            print(f"copy_state_from: Estado copiado exitosamente. Partidas: {len(self._partidas)}, Elementos para geometría: {len(self._geom_elements)}")

            try:
                dt = time.perf_counter() - t0
                self._log(
                    f"copy_state_from OK in {dt:.3f}s | cache_entries={len(self._mesh_cache)} | geom_elems={len(self._geom_elements)}"
                )
            except Exception:
                pass
            
            # Si hay elementos para cargar geometría, se cargarán de forma asíncrona
            # Si no hay elementos, renderizar inmediatamente
            if not self._geom_elements or len(self._geom_elements) == 0:
                self._safe_render_deferred(reset_camera=True, tag="copy_state_no_geom")
            
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
        try:
            self.btn_delete.setEnabled(False)
        except Exception:
            pass
        self._ifc_path = ruta
        try:
            self._t_ifc_open_start = time.perf_counter()
            self._log("load_ifc_path: starting async open")
        except Exception:
            pass
        self._worker = _IFCOpenWorker(ruta)
        self._worker.opened.connect(self._on_ifc_opened)
        self._worker.failed.connect(self._on_ifc_failed)
        self._worker.start()

    def _reset_view_for_load(self):
        self._show_progress("Abriendo IFC... (esto puede tardar)")
        if self._show_controls:
            self.lbl_info.setText("Abriendo IFC...")
        try:
            self.btn_delete.setEnabled(False)
        except Exception:
            pass
        self.plotter.clear()
        try:
            self.plotter.set_background("white")
        except Exception:
            pass
        self.tree.clear()
        self.actor_dict = {}
        self.group_dict = {}
        self._mesh_cache = {}

        try:
            self._mesh_cache_hits = 0
            self._mesh_cache_misses = 0
            self._mesh_cache_stores = 0
            self._actors_created = 0
            self._shape_time_total_s = 0.0
            self._t_processing_start = time.perf_counter()
            self._t_geometry_start = None
            self._log("reset_view_for_load")
        except Exception:
            pass

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
        try:
            if self._t_ifc_open_start:
                dt = time.perf_counter() - self._t_ifc_open_start
                self._log(f"IFC opened OK in {dt:.3f}s")
        except Exception:
            pass
        self._prepare_processing()
        self._process_next_chunk()

    def _on_ifc_failed(self, message: str):
        self._hide_progress()
        QMessageBox.critical(self, "Error", f"No se pudo cargar el IFC:\n{message}")
        self.lbl_info.setText("Error al cargar el IFC.")
        self.btn_load.setEnabled(True)
        self.btn_generate.setEnabled(False)
        try:
            self.btn_delete.setEnabled(bool(self._has_loaded_model()))
        except Exception:
            pass

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

        try:
            self._log(
                f"prepare_processing: pending={len(self._pending_elements)} geom={len(self._geom_elements)} fast_preview={bool(self.chk_fast_preview.isChecked())}"
            )
        except Exception:
            pass

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
            try:
                self.btn_delete.setEnabled(True)
            except Exception:
                pass
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
        guid = None
        try:
            guid = getattr(elem, 'GlobalId', None)
        except Exception:
            guid = None

        try:
            if guid and isinstance(getattr(self, '_mesh_cache', None), dict) and guid in self._mesh_cache:
                cached = self._mesh_cache.get(guid) or {}
                verts = cached.get('verts', None)
                faces_pv = cached.get('faces_pv', None)
                if verts is not None and faces_pv is not None:
                    try:
                        self._mesh_cache_hits += 1
                        self._actors_created += 1
                    except Exception:
                        pass
                    mesh = pv.PolyData(verts, faces_pv)

                    use_high_quality = not self.chk_fast_preview.isChecked()

                    if use_high_quality:
                        tono_gris = random.uniform(0.85, 0.98)
                        color = [tono_gris, tono_gris, tono_gris]
                    else:
                        color = "#A0A0A0"
                        cached_metal = cached.get('es_metal', es_metal)
                        if cached_metal:
                            color = "#4682B4"
                        else:
                            try:
                                if elem.is_a("IfcFooting"):
                                    color = "#8B4513"
                                elif elem.is_a("IfcSlab"):
                                    color = "#DCDCDC"
                            except Exception:
                                pass

                    try:
                        actor = self.plotter.add_mesh(
                            mesh,
                            color=color,
                            show_edges=use_high_quality,
                            smooth_shading=use_high_quality,
                            line_width=1 if use_high_quality else 0.0,
                            pbr=False,
                            lighting=True,
                            render=False,
                        )
                    except TypeError:
                        actor = self.plotter.add_mesh(
                            mesh,
                            color=color,
                            show_edges=use_high_quality,
                            smooth_shading=use_high_quality,
                            line_width=1 if use_high_quality else 0.0,
                            pbr=False,
                            lighting=True,
                        )
                    actor._original_color = color
                    self.actor_dict[guid] = actor
                    return
        except Exception:
            pass

        try:
            try:
                self._mesh_cache_misses += 1
            except Exception:
                pass

            t_shape = time.perf_counter()
            shape = ifcopenshell.geom.create_shape(self.settings, elem)
            try:
                self._shape_time_total_s += (time.perf_counter() - t_shape)
            except Exception:
                pass
            geom = shape.geometry
            verts = np.array(geom.verts).reshape(-1, 3)
            faces = np.array(geom.faces).reshape(-1, 3)
            faces_pv = np.hstack(
                [np.full((faces.shape[0], 1), 3), faces]
            ).astype(np.int64)
            mesh = pv.PolyData(verts, faces_pv)

            use_high_quality = not self.chk_fast_preview.isChecked()

            if use_high_quality:
                tono_gris = random.uniform(0.85, 0.98)
                color = [tono_gris, tono_gris, tono_gris]
            else:
                color = "#A0A0A0"
                if es_metal:
                    color = "#4682B4"
                elif elem.is_a("IfcFooting"):
                    color = "#8B4513"
                elif elem.is_a("IfcSlab"):
                    color = "#DCDCDC"

            try:
                actor = self.plotter.add_mesh(
                    mesh,
                    color=color,
                    show_edges=use_high_quality,
                    smooth_shading=use_high_quality,
                    line_width=1 if use_high_quality else 0.0,
                    pbr=False,
                    lighting=True,
                    render=False,
                )
            except TypeError:
                actor = self.plotter.add_mesh(
                    mesh,
                    color=color,
                    show_edges=use_high_quality,
                    smooth_shading=use_high_quality,
                    line_width=1 if use_high_quality else 0.0,
                    pbr=False,
                    lighting=True,
                )
            actor._original_color = color
            if guid:
                self.actor_dict[guid] = actor
                try:
                    self._actors_created += 1
                except Exception:
                    pass
                try:
                    if isinstance(getattr(self, '_mesh_cache', None), dict):
                        self._mesh_cache[guid] = {
                            'verts': verts,
                            'faces_pv': faces_pv,
                            'es_metal': bool(es_metal),
                        }
                        try:
                            self._mesh_cache_stores += 1
                        except Exception:
                            pass
                except Exception:
                    pass
        except Exception:
            pass

    def _on_tree_item_clicked(self, item, _col):
        try:
            identificador = id(item)
            self.highlight_guids(self.group_dict.get(identificador, []))
        except Exception:
            pass

    def reset_visualization(self):
        """Reset all actors to their original state (color and opacity)."""
        for actor in self.actor_dict.values():
            # Restore original color if stored
            if hasattr(actor, '_original_color'):
                actor.prop.color = actor._original_color
            else:
                actor.prop.color = "#A0A0A0"  # fallback
            actor.prop.opacity = 1.0
            actor.prop.line_width = 1
        self.request_render(reset_camera=False, tag="reset_visualization")
        # Clear tree selection
        self.tree.clearSelection()

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
    
    def _load_geometry_fast(self):
        """Carga geometría rápidamente desde elementos ya procesados (sin progreso, modo embebido)."""
        total = len(self._geom_elements)
        if self._cancel_geometry:
            return
        
        if self._geom_index >= total:
            # Terminado, renderizar
            try:
                self._safe_render_deferred(reset_camera=True, tag="geometry_fast_done")
                print(f"_load_geometry_fast: Geometría cargada completamente ({len(self.actor_dict)} actores)")
                try:
                    if self._pending_highlight_guids:
                        gids = self._pending_highlight_guids
                        self._pending_highlight_guids = None
                        self.highlight_guids(gids)
                except Exception:
                    pass
                try:
                    dt = 0.0
                    if self._t_geometry_start is not None:
                        dt = time.perf_counter() - self._t_geometry_start
                    self._log(
                        f"geometry_fast DONE in {dt:.3f}s | actors={len(self.actor_dict)} | hits={self._mesh_cache_hits} misses={self._mesh_cache_misses} stores={self._mesh_cache_stores} shape_time={self._shape_time_total_s:.3f}s"
                    )
                except Exception:
                    pass
            except Exception as e:
                print(f"Error renderizando: {e}")
            return
        
        # Cargar en chunks más grandes para velocidad
        chunk = 50
        end = min(self._geom_index + chunk, total)
        if self._geom_index == 0:
            try:
                self._t_geometry_start = time.perf_counter()
                self._log(f"geometry_fast START total={total}")
            except Exception:
                pass
        for i in range(self._geom_index, end):
            _tipo, elem = self._geom_elements[i]
            try:
                material = self._get_material_name(elem)
                es_metal = self._is_metal(elem, material)
                self._create_actor(elem, es_metal=es_metal)
            except Exception as e:
                print(f"Error creando actor para {elem.GlobalId}: {e}")
                continue
        
        self._geom_index = end
        
        # Continuar cargando en el siguiente chunk
        if self._geom_index < total:
            QTimer.singleShot(5, self._load_geometry_fast)
        else:
            # Terminado, renderizar
            try:
                self._safe_render_deferred(reset_camera=True, tag="geometry_fast_done")
                print(f"_load_geometry_fast: Geometría cargada completamente ({len(self.actor_dict)} actores)")
                try:
                    if self._pending_highlight_guids:
                        gids = self._pending_highlight_guids
                        self._pending_highlight_guids = None
                        self.highlight_guids(gids)
                except Exception:
                    pass
                try:
                    dt = 0.0
                    if self._t_geometry_start is not None:
                        dt = time.perf_counter() - self._t_geometry_start
                    self._log(
                        f"geometry_fast DONE in {dt:.3f}s | actors={len(self.actor_dict)} | hits={self._mesh_cache_hits} misses={self._mesh_cache_misses} stores={self._mesh_cache_stores} shape_time={self._shape_time_total_s:.3f}s"
                    )
                except Exception:
                    pass
            except Exception as e:
                print(f"Error renderizando: {e}")

    def _start_geometry_load(self):
        total = len(self._geom_elements)
        self._show_progress(f"Cargando geometría: 0/{total}", determinate=True, maximum=max(total, 1))
        self._geom_index = 0
        self._cancel_geometry = False
        self.btn_cancel_geom.setEnabled(True)
        try:
            self._t_geometry_start = time.perf_counter()
            self._log(f"geometry_full START total={total}")
        except Exception:
            pass
        QTimer.singleShot(0, self._process_geometry_chunk)

    def _process_geometry_chunk(self):
        total = len(self._geom_elements)
        if self._cancel_geometry:
            self._hide_progress()
            self.btn_generate.setEnabled(True)
            self.btn_load.setToolTip("Ya hay un IFC cargado.")
            self.lbl_info.setText("Geometría detenida por el usuario.")
            try:
                self.btn_delete.setEnabled(True)
            except Exception:
                pass
            self.loading_finished.emit()
            return
        if self._geom_index >= total:
            self._hide_progress()
            self.btn_generate.setEnabled(True)
            self.btn_load.setToolTip("Ya hay un IFC cargado.")
            self.lbl_info.setText("Modelo cargado.")
            try:
                self.btn_delete.setEnabled(True)
            except Exception:
                pass
            try:
                dt = 0.0
                if self._t_geometry_start is not None:
                    dt = time.perf_counter() - self._t_geometry_start
                self._log(
                    f"geometry_full DONE in {dt:.3f}s | actors={len(self.actor_dict)} | hits={self._mesh_cache_hits} misses={self._mesh_cache_misses} stores={self._mesh_cache_stores} shape_time={self._shape_time_total_s:.3f}s"
                )
            except Exception:
                pass
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
            try:
                ifc_guids = self.group_dict.get(id(item), [])
            except Exception:
                ifc_guids = []
            prefill_rows.append(
                {
                    "item": "",
                    "descripcion": desc,
                    "unidad": unidad,
                    "cantidad": round(cantidad, 3),
                    "ifc_guids": ifc_guids,
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


    def eventFilter(self, obj, event):
        """Filter events to detect clicks on empty space or outside the table."""
        if event.type() == event.Type.MouseButtonPress:
            # Check if click is on tree viewport empty space
            if obj == self.tree.viewport():
                item = self.tree.itemAt(event.pos())
                # If no item was clicked (empty space), reset visualization
                # Only reset if there's actually a selection to clear (avoid unnecessary rendering)
                if not item and self.tree.selectedItems():
                    self.reset_visualization()
            # Check if click is on the 3D viewer (plotter)
            elif obj == self.plotter.interactor:
                # Any click on the 3D viewer should deselect
                if self.tree.selectedItems():
                    self.reset_visualization()
            # Check if click is on the dialog background (gray area)
            elif obj == self:
                # Any click on the dialog background should deselect
                if self.tree.selectedItems():
                    self.reset_visualization()
        return super().eventFilter(obj, event)

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

