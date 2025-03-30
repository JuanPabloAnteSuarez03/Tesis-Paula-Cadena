# views/main_window.py
import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
    QPushButton, QStackedWidget, QSplitter, QSizePolicy, QFrame
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
        
        # Inicialmente ocultar los paneles laterales
        self.left_panel.setVisible(False)
        self.right_panel.setVisible(False)
        
        # Configurar el panel central (donde va el presupuesto)
        self.setup_center_panel()
        
        # Configurar panel izquierdo para recursos
        self.setup_left_panel()
        
        # Configurar panel derecho para análisis unitarios
        self.setup_right_panel()
        
        # Cargar controlador de presupuesto inicialmente
        self.presupuesto_controller = PresupuestoController()
        self.center_panel_layout.addWidget(self.presupuesto_controller.view)

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
        
        # Título central
        title_label = QWidget()
        title_label_layout = QHBoxLayout(title_label)
        title_label_layout.setContentsMargins(0, 0, 0, 0)
        title_label_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label_layout.addWidget(QPushButton("Presupuesto"))
        title_label.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: white;
                border: none;
                font-size: 16px;
                font-weight: bold;
            }
        """)
        
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
        top_bar_layout.addWidget(title_label, 1)  # El 1 hace que se expanda
        top_bar_layout.addWidget(self.toggle_right_btn)
        
        # Agregar barra superior al panel central
        self.center_panel_layout.addWidget(top_bar)
        
        # El resto del espacio es para la vista de presupuesto

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
        self.resources_container_layout.addWidget(self.resource_controller.view)
    
    def load_analysis(self):
        """Carga el controlador de análisis unitarios en el panel derecho."""
        # Limpiar contenedor
        self.clear_layout(self.analysis_container_layout)
        
        # Crear controlador de análisis unitarios
        self.analisis_controller = AnalisisUnitariosController()
        
        # Conectar la señal de selección para que agregue el análisis al presupuesto
        self.analisis_controller.view.analysis_selected.connect(
            lambda codigo: self.presupuesto_controller.on_analisis_selected(codigo)
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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
