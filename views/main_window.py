# views/main_window.py
import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
    QPushButton, QStackedWidget, QSplitter, QSizePolicy, QFrame, QComboBox,
    QLabel, QScrollArea, QGroupBox
)
from PyQt6.QtCore import Qt
from .presupuesto_view import PresupuestoView
from .resource_list_view import ResourceListView
from .analisis_unitarios_view import AnalisisUnitariosView
from .analisis_por_presupuesto_view import AnalisisPorPresupuestoView
from controllers.resource_controller import ResourceController
from controllers.analisis_unitarios_controller import AnalisisUnitariosController
from controllers.recursos_por_analisis_controller import RecursosPorAnalisisController
from controllers.presupuesto_controller import PresupuestoController
from controllers.presupuesto_analisis_unitario_controller import PresupuestoAnalisisUnitarioController  

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("App Presupuestos - MVC")
        self.resize(1400, 800)
        
        # Aplicar un estilo global a toda la aplicación
        
        self.init_ui()


    def init_ui(self):
        # Widget principal
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # Layout principal es horizontal para los tres paneles
        self.main_layout = QHBoxLayout(main_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Creación de los tres paneles principales
        self.left_panel = self.create_side_panel("izquierdo")
        self.center_panel = QWidget()
        self.right_panel = self.create_side_panel("derecho")
        
        # Establecer políticas de tamaño
        self.left_panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.center_panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.right_panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Crear splitters para permitir ajustar tamaños
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_splitter.setChildrenCollapsible(False)  # Evita que los paneles se colapsen a cero
        self.main_splitter.setHandleWidth(8)  # Hacer el separador más ancho y fácil de agarrar
        
        # Agregar los paneles al splitter principal
        self.main_splitter.addWidget(self.left_panel)
        self.main_splitter.addWidget(self.center_panel)
        self.main_splitter.addWidget(self.right_panel)
        
        # Configurar proporciones iniciales (izquierda: 2, centro: 3, derecha: 2)
        self.main_splitter.setStretchFactor(0, 2)
        self.main_splitter.setStretchFactor(1, 3)
        self.main_splitter.setStretchFactor(2, 2)
        
        # Establecer anchos iniciales más generosos
        self.main_splitter.setSizes([600, 600, 600])
        
        # Personalizar el separador del splitter
        self.main_splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #bbbbbb;
                width: 8px;
                height: 8px;
            }
            QSplitter::handle:hover {
                background-color: #0078d7;
            }
            QSplitter::handle:pressed {
                background-color: #005a9e;
            }
        """)
        
        # Agregar el splitter al layout principal
        self.main_layout.addWidget(self.main_splitter)
        
        # Inicialmente mostrar los paneles laterales abiertos
        self.left_panel.setVisible(True)
        self.right_panel.setVisible(True)
        
        # Configurar el panel central (donde va el presupuesto)
        self.setup_center_panel()
        
        # Configurar panel izquierdo para recursos
        self.setup_left_panel()
        
        # Configurar panel derecho para análisis unitarios
        self.setup_right_panel()
        
        # Cargar controlador de presupuesto inicialmente
        self.presupuesto_controller = PresupuestoController()
        # Reutilizar el controlador de análisis ya cargado en el panel derecho
        try:
            self.presupuesto_controller.set_external_analisis_controller(self.analisis_controller)
        except Exception:
            pass
        self.center_stack.addWidget(self.presupuesto_controller.view)
        self.center_stack.setCurrentWidget(self.presupuesto_controller.view)
        self.aiu_widget = None
        self.analisis_presupuesto_widget = None
        self._analisis_presupuesto_ctrls = []

    def on_mode_changed(self, idx: int):
        text = self.mode_select.currentText()
        if text == "Presupuesto":
            self.center_stack.setCurrentWidget(self.presupuesto_controller.view)
        elif text == "AIU":
            # Crear perezosamente la ventana AIU embebida si no existe
            if self.aiu_widget is None:
                from views.administracion_window import AdministracionWindow
                # Construir un widget contenedor para embeber el diálogo
                # Se crea con costo directo actual
                direct_cost = getattr(self.presupuesto_controller.view, 'direct_cost_total', 0.0)
                # Obtener profesionales desde BD igual que en PresupuestoView
                try:
                    from models.database import SessionLocal
                    from models.profesional import Profesional
                    session = SessionLocal()
                    profesionales_db = session.query(Profesional).all()
                    profesionales = [
                        {
                            'nombre': p.nombre,
                            'cargo': p.cargo,
                            'salario_mensual': p.salario_mensual,
                            'necesario': p.necesario,
                        } for p in profesionales_db
                    ]
                except Exception:
                    profesionales = []
                finally:
                    try:
                        session.close()
                    except Exception:
                        pass
                aiu = AdministracionWindow(profesionales, direct_cost, parent=self, embedded=True)
                # Conectar emisión para que el breakdown y totales en Presupuesto se actualicen
                aiu.aiu_computed.connect(lambda data: self._on_aiu_from_embedded(data))
                self.aiu_widget = aiu
                self.center_stack.addWidget(self.aiu_widget)
            self.center_stack.setCurrentWidget(self.aiu_widget)
        elif text == "Análisis Unitario":
            if self.analisis_presupuesto_widget is None:
                self._create_analisis_presupuesto_widget()
            else:
                self._populate_analisis_presupuesto_widget()
            self.center_stack.setCurrentWidget(self.analisis_presupuesto_widget)
        else:
            # Otras vistas aún no implementadas: mostrar Presupuesto por defecto
            self.center_stack.setCurrentWidget(self.presupuesto_controller.view)

    def _on_aiu_from_embedded(self, data: dict):
        # Actualizar breakdown y etiqueta de totales en Presupuesto
        try:
            view = self.presupuesto_controller.view
            view.admin_cost_total = data.get('total_aiu', 0.0)
            view.aiu_breakdown = data
            view.update_total_presupuesto()
        except Exception:
            pass

    def create_side_panel(self, side):
        """Crea un panel lateral con estilo."""
        panel = QFrame()
        panel.setFrameShape(QFrame.Shape.StyledPanel)
        panel.setFrameShadow(QFrame.Shadow.Raised)
        panel.setMinimumWidth(300)
        panel.setMaximumWidth(500)
        
        if side == "izquierdo":
            panel.setStyleSheet("""
                QFrame {
                    background-color: #f0f0f0;
                    border-right: 1px solid #cccccc;
                }
            """)
        else:
            panel.setStyleSheet("""
                QFrame {
                    background-color: #f0f0f0;
                    border-left: 1px solid #cccccc;
                }
            """)
        
        return panel
    
    def setup_center_panel(self):
        """Configura el panel central con controles de navegación y vista de presupuesto."""
        self.center_panel_layout = QVBoxLayout(self.center_panel)
        self.center_panel_layout.setContentsMargins(0, 0, 0, 0)
        
        # Barra superior con botones para mostrar/ocultar paneles laterales
        top_bar = QWidget()
        top_bar.setMinimumHeight(50)
        top_bar.setMaximumHeight(50)
        top_bar.setStyleSheet("background-color: #0078d7; color: white;")
        
        top_bar_layout = QHBoxLayout(top_bar)
        top_bar_layout.setContentsMargins(10, 5, 10, 5)
        
        # Botón para mostrar/ocultar panel izquierdo (recursos)
        self.toggle_left_btn = QPushButton("≡ Recursos")
        self.toggle_left_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: white;
                border: none;
                padding: 5px 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.2);
                border-radius: 4px;
            }
        """)
        self.toggle_left_btn.clicked.connect(self.toggle_left_panel)
        
        # Selector central de modo
        self.mode_select = QComboBox()
        self.mode_select.addItems(["Presupuesto", "AIU", "Análisis Unitario", "Cronograma"])
        self.mode_select.setCurrentIndex(0)
        self.mode_select.currentIndexChanged.connect(self.on_mode_changed)
        self.mode_select.setStyleSheet("QComboBox { background: white; color: #333; padding: 4px 8px; border-radius: 4px; }")
        
        # Botón para mostrar/ocultar panel derecho (análisis)
        self.toggle_right_btn = QPushButton("Análisis ≡")
        self.toggle_right_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: white;
                border: none;
                padding: 5px 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.2);
                border-radius: 4px;
            }
        """)
        self.toggle_right_btn.clicked.connect(self.toggle_right_panel)
        
        # Agregar widgets a la barra superior
        top_bar_layout.addWidget(self.toggle_left_btn)
        top_bar_layout.addWidget(self.mode_select, 1)  # expansible
        top_bar_layout.addWidget(self.toggle_right_btn)
        
        # Agregar barra superior al panel central
        self.center_panel_layout.addWidget(top_bar)
        
        # El resto del espacio es para la vista de contenido (stack)
        self.center_stack = QStackedWidget()
        self.center_panel_layout.addWidget(self.center_stack)

    def setup_left_panel(self):
        """Configura el panel izquierdo para recursos."""
        left_layout = QVBoxLayout(self.left_panel)
        
        # Título del panel
        left_title = QWidget()
        left_title.setMinimumHeight(50)
        left_title.setMaximumHeight(50)
        left_title.setStyleSheet("background-color: #0078d7; color: white;")
        
        left_title_layout = QHBoxLayout(left_title)
        left_title_layout.setContentsMargins(10, 5, 10, 5)
        
        title_label = QPushButton("Recursos")
        title_label.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: white;
                border: none;
                font-size: 16px;
                font-weight: bold;
            }
        """)
        
        left_title_layout.addWidget(title_label)
        left_title_layout.addStretch()
        
        close_btn = QPushButton("✕")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: white;
                border: none;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.2);
                border-radius: 4px;
            }
        """)
        close_btn.clicked.connect(lambda: self.left_panel.setVisible(False))
        
        left_title_layout.addWidget(close_btn)
        
        # Agregar título al panel
        left_layout.addWidget(left_title)
        
        # Contenedor para el contenido del panel de recursos
        self.resources_container = QWidget()
        left_layout.addWidget(self.resources_container)
        self.resources_container_layout = QVBoxLayout(self.resources_container)
        
        # Cargar controlador de recursos
        self.load_resources()

    def setup_right_panel(self):
        """Configura el panel derecho para análisis unitarios."""
        right_layout = QVBoxLayout(self.right_panel)
        
        # Título del panel
        right_title = QWidget()
        right_title.setMinimumHeight(50)
        right_title.setMaximumHeight(50)
        right_title.setStyleSheet("background-color: #0078d7; color: white;")
        
        right_title_layout = QHBoxLayout(right_title)
        right_title_layout.setContentsMargins(10, 5, 10, 5)
        
        title_label = QPushButton("Análisis Unitarios")
        title_label.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: white;
                border: none;
                font-size: 16px;
                font-weight: bold;
            }
        """)
        
        right_title_layout.addStretch()
        right_title_layout.addWidget(title_label)
        
        close_btn = QPushButton("✕")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: white;
                border: none;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.2);
                border-radius: 4px;
            }
        """)
        close_btn.clicked.connect(lambda: self.right_panel.setVisible(False))
        
        right_title_layout.addWidget(close_btn)
        
        # Agregar título al panel
        right_layout.addWidget(right_title)
        
        # Contenedor para el contenido del panel de análisis unitarios
        self.analysis_container = QWidget()
        right_layout.addWidget(self.analysis_container)
        self.analysis_container_layout = QVBoxLayout(self.analysis_container)
        
        # Cargar controlador de análisis unitarios
        self.load_analysis()

    def toggle_left_panel(self):
        """Muestra u oculta el panel izquierdo de recursos."""
        visible = not self.left_panel.isVisible()
        self.left_panel.setVisible(visible)
        
        # Ajustar tamaños de splitter cuando se muestra/oculta
        if visible:
            sizes = self.main_splitter.sizes()
            # Distribuir proporcionalmente: panel izquierdo toma 30% del espacio total
            total_width = sum(sizes)
            left_width = int(total_width * 0.3)
            center_width = sizes[1] - (left_width if sizes[0] == 0 else 0)
            right_width = sizes[2]
            self.main_splitter.setSizes([left_width, center_width, right_width])
        
    def toggle_right_panel(self):
        """Muestra u oculta el panel derecho de análisis unitarios."""
        visible = not self.right_panel.isVisible()
        self.right_panel.setVisible(visible)
        
        # Ajustar tamaños de splitter cuando se muestra/oculta
        if visible:
            sizes = self.main_splitter.sizes()
            # Distribuir proporcionalmente: panel derecho toma 30% del espacio total
            total_width = sum(sizes)
            right_width = int(total_width * 0.3)
            left_width = sizes[0]
            center_width = sizes[1] - (right_width if sizes[2] == 0 else 0)
            self.main_splitter.setSizes([left_width, center_width, right_width])
    
    def load_resources(self):
        """Carga el controlador de recursos en el panel izquierdo."""
        # Limpiar contenedor
        self.clear_layout(self.resources_container_layout)
        
        # Crear controlador de recursos
        self.resource_controller = ResourceController()
        # Si ya existe el controlador de análisis, inyectarlo para refrescos posteriores
        try:
            if hasattr(self, "analisis_controller"):
                self.resource_controller.set_external_analisis_controller(self.analisis_controller)
        except Exception:
            pass
        self.resources_container_layout.addWidget(self.resource_controller.view)
    
    def load_analysis(self):
        """Carga el controlador de análisis unitarios en el panel derecho."""
        # Limpiar contenedor
        self.clear_layout(self.analysis_container_layout)
        
        # Crear controlador de análisis unitarios
        self.analisis_controller = AnalisisUnitariosController()
        # Inyectar en recursos si ya existe
        try:
            if hasattr(self, "resource_controller"):
                self.resource_controller.set_external_analisis_controller(self.analisis_controller)
        except Exception:
            pass
        
        # Conectar la señal de selección con validación del modo actual
        self.analisis_controller.view.analysis_selected.connect(
            self._on_analysis_selected_from_right
        )
        
        self.analysis_container_layout.addWidget(self.analisis_controller.view)
    
    def clear_layout(self, layout):
        """Elimina todos los widgets de un layout."""
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.setParent(None)
                else:
                    self.clear_layout(item.layout())

    def _on_analysis_selected_from_right(self, codigo: str):
        """Agrega el análisis al presupuesto solo si el modo activo es 'Presupuesto'."""
        try:
            from PyQt6.QtWidgets import QMessageBox
            if self.center_stack.currentWidget() is not self.presupuesto_controller.view:
                QMessageBox.information(
                    self,
                    "Agregar al presupuesto",
                    "Solo puedes agregar análisis al presupuesto cuando el modo activo es 'Presupuesto'."
                )
                return
            self.presupuesto_controller.on_analisis_selected(codigo)
        except Exception:
            # Silenciar cualquier error no crítico para no bloquear la UI
            pass

    # ---------- Vista: Análisis del Presupuesto (composición) ----------
    def _create_analisis_presupuesto_widget(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        title = QLabel("Composición de Análisis del Presupuesto actual")
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title)

        # Botón de refresco
        refresh_btn = QPushButton("Refrescar desde Presupuesto")
        refresh_btn.clicked.connect(self._populate_analisis_presupuesto_widget)
        layout.addWidget(refresh_btn)

        # Área scrollable que contendrá todas las vistas de recursos por análisis
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        inner = QWidget()
        self._analisis_scroll_layout = QVBoxLayout(inner)
        self._analisis_scroll_layout.setContentsMargins(0, 0, 0, 0)
        self._analisis_scroll_layout.setSpacing(12)
        scroll.setWidget(inner)
        layout.addWidget(scroll)

        self.analisis_presupuesto_widget = container
        self.center_stack.addWidget(self.analisis_presupuesto_widget)
        self._populate_analisis_presupuesto_widget()

    def _populate_analisis_presupuesto_widget(self):
        # Limpiar controles previos
        for ctrl in getattr(self, '_analisis_presupuesto_ctrls', []):
            try:
                # Desconectar señales si fuera necesario
                ctrl.analysis_updated.disconnect()
            except Exception:
                pass
        self._analisis_presupuesto_ctrls = []

        # Vaciar layout interior
        if hasattr(self, '_analisis_scroll_layout'):
            layout = self._analisis_scroll_layout
            while layout.count():
                item = layout.takeAt(0)
                w = item.widget()
                if w is not None:
                    w.setParent(None)

            # Recopilar capítulos y códigos únicos de la tabla de presupuesto actual
            chapters = []  # [(chapter_title, [codes...])]
            current_chapter = None
            codes = []
            code_to_desc = {}
            try:
                table = self.presupuesto_controller.view.table
                from PyQt6.QtCore import Qt
                for row in range(table.rowCount()):
                    itm = table.item(row, 0)
                    if not itm:
                        continue
                    role = itm.data(Qt.ItemDataRole.UserRole)
                    # Detectar capítulos
                    if role == 'chapter':
                        current_chapter = itm.text()
                        chapters.append((current_chapter, []))
                        continue
                    if role == 'subtotal':
                        continue
                    val = role
                    if not val:
                        continue
                    if val not in codes:
                        codes.append(val)
                        try:
                            desc = table.item(row, 1).text() if table.item(row, 1) else val
                        except Exception:
                            desc = val
                        code_to_desc[val] = desc
                    # Asociar al capítulo actual
                    if chapters:
                        chapters[-1][1].append(val)
            except Exception:
                codes = []
                chapters = []

            from controllers.recursos_por_analisis_controller import RecursosPorAnalisisController

            # Si hay capítulos, mostrar agrupado; si no, mostrar la lista simple
            if chapters:
                for chapter_title, chapter_codes in chapters:
                    if not chapter_codes:
                        continue
                    chapter_box = QGroupBox(chapter_title)
                    chapter_layout = QVBoxLayout(chapter_box)
                    for code in chapter_codes:
                        sub_group = QGroupBox(f"{code} - {code_to_desc.get(code, '')}")
                        v = QVBoxLayout(sub_group)
                        ctrl = RecursosPorAnalisisController(code, embed_readonly=True)
                        # Cuando cambie el total estimado, reflejar en la tabla de presupuesto inmediatamente
                        ctrl.analysis_total_changed.connect(self._on_embedded_analysis_total_changed)
                        ctrl.analysis_updated.connect(lambda c=code: self.presupuesto_controller.update_presupuesto_row(c))
                        v.addWidget(ctrl.view)
                        chapter_layout.addWidget(sub_group)
                        self._analisis_presupuesto_ctrls.append(ctrl)
                    layout.addWidget(chapter_box)
            else:
                for code in codes:
                    group = QGroupBox(f"{code} - {code_to_desc.get(code, '')}")
                    v = QVBoxLayout(group)
                    ctrl = RecursosPorAnalisisController(code, embed_readonly=True)
                    ctrl.analysis_total_changed.connect(self._on_embedded_analysis_total_changed)
                    ctrl.analysis_updated.connect(lambda c=code: self.presupuesto_controller.update_presupuesto_row(c))
                    v.addWidget(ctrl.view)
                    layout.addWidget(group)
                    self._analisis_presupuesto_ctrls.append(ctrl)

    def _on_embedded_analysis_total_changed(self, code: str, new_total: float):
        """Actualiza el costo unitario del análisis en la tabla de presupuesto en vivo."""
        try:
            table = self.presupuesto_controller.view.table
            from PyQt6.QtCore import Qt
            for row in range(table.rowCount()):
                item = table.item(row, 0)
                if not item:
                    continue
                val = item.data(Qt.ItemDataRole.UserRole)
                if val == code:
                    # actualizar costo unitario (col 4) y total de fila
                    cu_item = table.item(row, 4)
                    if cu_item:
                        cu_item.setText(f"${new_total:,.2f}")
                    self.presupuesto_controller.view.update_row_total(row)
            # refrescar totales generales
            self.presupuesto_controller.view.update_total_presupuesto()
        except Exception:
            pass

            layout.addStretch(1)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
