import ifcopenshell
import ifcopenshell.geom
import pyvista as pv
import numpy as np
import random  # Necesario para la variación de colores

# ===============================
# 1. CONFIGURACIÓN
# ===============================
RUTA_IFC = "modelo.ifc"

# Configuración del procesador de geometría de IfcOpenShell
settings = ifcopenshell.geom.settings()
settings.set(settings.USE_WORLD_COORDS, True)

# ===============================
# 2. CARGAR IFC
# ===============================
print(f"Cargando archivo: {RUTA_IFC}...")
try:
    ifc = ifcopenshell.open(RUTA_IFC)
    print("Archivo cargado exitosamente.")
except Exception as e:
    print(f"Error al cargar el archivo IFC: {e}")
    exit()

# ===============================
# 3. CONFIGURAR VISOR PYVISTA
# ===============================
plotter = pv.Plotter()
plotter.set_background("white")  # Fondo blanco para estilo profesional
plotter.enable_eye_dome_lighting()  # Mejora la percepción de profundidad sutilmente

# ===============================
# 4. FUNCIÓN PRINCIPAL
# ===============================
def agregar_elementos(tipo_ifc, opacidad=1.0):
    """
    Busca elementos por tipo, genera su geometría y les asigna 
    un tono de gris único para diferenciarlos.
    """
    elementos = ifc.by_type(tipo_ifc)
    
    if not elementos:
        return

    print(f"Procesando {tipo_ifc}: {len(elementos)} elementos found.")

    for elem in elementos:
        try:
            # Crear la forma geométrica
            shape = ifcopenshell.geom.create_shape(settings, elem)
            geom = shape.geometry

            # Convertir vértices y caras a formato NumPy
            vertices = np.array(geom.verts).reshape(-1, 3)
            faces = np.array(geom.faces).reshape(-1, 3)

            # Preparar el array de caras para PyVista (indicando 3 puntos por cara)
            faces_pv = np.hstack(
                [np.full((faces.shape[0], 1), 3), faces]
            ).astype(np.int64)

            # Crear la malla (Mesh)
            mesh = pv.PolyData(vertices, faces_pv)
            
            # --- LÓGICA DE COLOR TIPO "PLEXOS" ---
            # Generamos un gris muy claro aleatorio (entre 0.85 y 0.98)
            # Esto diferencia elementos contiguos sin que parezca un tablero de ajedrez.
            tono_gris = random.uniform(0.85, 0.98)
            color_hex = [tono_gris, tono_gris, tono_gris]

            # Agregar al visor
            plotter.add_mesh(
                mesh,
                color=color_hex,
                opacity=opacidad,
                show_edges=True,       # CLAVE: Muestra las líneas negras de los bordes
                line_width=1,          # Grosor de línea fino y elegante
                smooth_shading=True,   # Suaviza las caras curvas
                pbr=False,             # Apagamos PBR para evitar sombras sucias
                lighting=True          # Iluminación estándar
            )

        except Exception as e:
            # Algunos elementos IFC no tienen representación geométrica válida, los ignoramos
            pass 

# ===============================
# 5. EJECUCIÓN
# ===============================
print("Generando geometría 3D...")

# Elementos Estructurales y Arquitectónicos
agregar_elementos("IfcWall")
agregar_elementos("IfcSlab")
agregar_elementos("IfcColumn")
agregar_elementos("IfcBeam")
agregar_elementos("IfcFooting")
agregar_elementos("IfcRoof")
agregar_elementos("IfcStair")
agregar_elementos("IfcRamp")

# Elementos de Carpintería y Terminaciones
agregar_elementos("IfcDoor")
agregar_elementos("IfcWindow")
agregar_elementos("IfcRailing")
agregar_elementos("IfcCurtainWall")
agregar_elementos("IfcMember")
agregar_elementos("IfcPlate")

print("Visualización lista. Abriendo ventana...")
plotter.show(title="Visor IFC - Estilo Ingeniería")