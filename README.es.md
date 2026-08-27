# Presupuestos de Obra — App de escritorio para presupuestos de obra civil

[English](README.md) · **Español**

Aplicación de escritorio en PyQt6 que automatiza el paso de un **modelo de Revit/BIM** a un **presupuesto de obra civil completo** — materiales, mano de obra, impuestos y estampillas incluidos —, cruzando el modelo con los análisis de precios unitarios oficiales de la Gobernación del Valle del Cauca.

Desarrollada como trabajo de grado de posgrado para una clienta de ingeniería civil, construida de forma iterativa a lo largo de aproximadamente un año.

---

## El problema

Ir de un modelo de Revit a un presupuesto confiable no tiene un camino corto. Hay que calcular el costo completo de la obra, que no son solo los materiales: también entran la mano de obra, los impuestos y las estampillas. Automatizar ese recorrido entero, no una parte, era el requisito central.

Calcular esos costos con precisión exige además el catálogo oficial de precios unitarios de la Gobernación, y ese catálogo se publica como el **Decreto 1276 de 2021** — un PDF de cientos de páginas de tablas. Transcribirlo a mano para cada presupuesto es lento y propenso a errores, y esos errores se propagan a la oferta económica.

La herramienta tenía que ser una **aplicación de escritorio**: ese era el requerimiento de la tesis, definido por el director de la clienta.

---

## Qué hace

- **Lee el modelo BIM.** Carga archivos IFC (el formato estándar que exporta Revit), los renderiza en un visor 3D interactivo y extrae cantidades de presupuesto a partir del modelo.
- **Extrae el catálogo oficial de precios** del PDF del Decreto 1276, normaliza las tablas y las carga en una base de datos relacional.
- **Arma presupuestos** seleccionando análisis unitarios y recursos, con capítulos y subtotales.
- **Calcula el AIU** (Administración, Imprevistos y Utilidad), que es donde entran los impuestos, las estampillas y todo cargo que no es costo directo de material.
- **Planea y controla la ejecución** — cronograma de obra con vista de tablero, control de gastos de compras y nómina, y valor ganado (EVM).
- **Exporta a Excel** en el formato que la entidad espera recibir.

---

## Stack

| Aspecto | Tecnología |
|---|---|
| UI | PyQt6 |
| Arquitectura | MVC (`models/` · `views/` · `controllers/`) |
| ORM | SQLAlchemy 2 |
| Base de datos | PostgreSQL (desarrollo) · SQLite (build empaquetado) |
| Extracción de PDF | tabula-py (requiere Java, vía JPype1), pdfminer.six, PyPDF2 |
| Procesamiento de datos | pandas, NumPy |
| Excel | openpyxl |
| BIM / IFC | ifcopenshell |
| Render 3D | PyVista + VTK (`pyvistaqt`) |
| Gráficos | matplotlib |
| Empaquetado | PyInstaller (`app_presupuestos.spec`) |

---

## Decisiones de diseño

**MVC estricto.** Modelos, vistas y controladores en carpetas separadas, con un modelo por entidad del dominio: análisis unitario, recurso, presupuesto, profesional. En un proyecto que creció durante un año con requisitos que iban apareciendo, separar la lógica de la interfaz fue lo que permitió agregar vistas nuevas sin romper las existentes.

**Varias librerías de PDF en lugar de una.** Ninguna librería sola extrae bien tablas de un PDF gubernamental. tabula-py (sobre Java) acierta en las tablas regulares, mientras que la extracción de texto plano con pdfminer.six y PyPDF2 resuelve los casos que rompen la detección de tablas.

**Optimizar el render 3D en vez de cambiar de stack.** El visor IFC corría fluido en la máquina de desarrollo, pero el computador de la clienta no tenía GPU para mover la cantidad de polígonos de un modelo BIM completo. La parte más difícil del proyecto fue reducir polígonos y aplicar optimizaciones hasta que corriera en hardware modesto. En C++ el rendimiento habría sido mejor de entrada, pero la clienta necesitaba Python y una aplicación de escritorio, así que el problema se resolvió dentro de esas restricciones.

**Dos backends de base de datos, elegidos en tiempo de ejecución.** En desarrollo la app habla con PostgreSQL; el ejecutable empaquetado cae a un archivo SQLite local bajo `%LOCALAPPDATA%`, poblado automáticamente en el primer arranque. Ver `_resolve_backend()` en `models/database.py`; `APP_DB_BACKEND` fuerza la elección de forma explícita.

---

## Puesta en marcha

**Requisitos:** Python 3.11+, un **runtime de Java** (tabula-py lo necesita) y PostgreSQL si se quiere usar el backend de desarrollo.

```bash
python -m venv env
source env/bin/activate        # Windows: env\Scripts\activate

pip install -r requirements.txt

python app.py
```

En el primer arranque la app se asegura de que exista una base local y esté poblada (`seed_local_db.ensure_local_db_ready`).

### Backend de base de datos

```bash
# Forzar SQLite (lo que usa el build empaquetado)
APP_DB_BACKEND=sqlite python app.py

# Forzar PostgreSQL
APP_DB_BACKEND=postgres python app.py
```

La configuración de conexión está en `models/database.py`.

### Cargar los datos oficiales

```bash
python create_tables.py                    # crear el esquema
python db_extraction_analisis_unitarios.py # extraer análisis unitarios del PDF del decreto
python db_extraction.py                    # extraer recursos
python load_database.py                    # cargar los CSV normalizados
python importar_todo_bd.py                 # o: correr toda la importación de una
```

El catálogo ya extraído está versionado en `data_gobernacion/` como CSV, así que una instalación nueva no tiene que volver a parsear el PDF.

### Generar el ejecutable de Windows

```powershell
./build_release.ps1        # envuelve PyInstaller con app_presupuestos.spec
```

---

## Estructura del proyecto

```
app.py                     Punto de entrada — ventana de inicio y luego MainController

models/                    Modelos SQLAlchemy, uno por entidad del dominio
├─ database.py             Configuración del engine, resolución PostgreSQL/SQLite
├─ analisis_unitario.py    Análisis de precios unitarios
├─ analisis_unitario_recurso.py
├─ presupuesto.py          Presupuestos
├─ presupuesto_analisis_unitario.py
├─ recurso.py              Recursos (materiales, mano de obra, equipo)
├─ profesional.py          Personal usado para el cálculo del AIU
├─ ejecucion.py            Control de ejecución
├─ factura.py · factura_item.py · pago_nomina.py
└─ update_db.py            Migraciones de esquema

views/
├─ start_window.py         Ventana de inicio
├─ main_window.py          Shell y navegación
├─ presupuesto_view.py     Edición de presupuestos
├─ analisis_unitarios_view.py
├─ administracion_view.py · administracion_window.py    AIU
├─ cronograma_view.py · cronograma_visor.py             Cronograma + vista de tablero
├─ ejecucion_view.py       Ejecución de gastos
├─ evm_view.py             Valor ganado (EVM)
├─ ifc_model_viewer_dialog.py   Visor 3D de modelos BIM
├─ ifc_materials_dialog.py      Cantidades a partir del modelo IFC
└─ ...diálogos

controllers/               Un controlador por familia de vistas

data_gobernacion/          Catálogo oficial de precios ya extraído (CSV)
db_extraction*.py          PDF del decreto → tablas normalizadas
seed_local_db.py           Prepara la base SQLite del ejecutable
```

---

## Ramas

⚠️ **La aplicación completa y funcional vive en la rama `excel`**, no en `main`. `main` es anterior al visor BIM, al cronograma, al control de ejecución y al EVM.

---

## Sobre el proyecto

Desarrollado por [Juan Pablo Ante Suárez](https://github.com/JuanPabloAnteSuarez03) — desarrollo completo, trabajo remunerado, construido de forma iterativa con la clienta durante aproximadamente un año en sesiones quincenales. La tesis fue aprobada y la clienta se graduó; según ella, sigue usando la aplicación en su trabajo actualmente.

📖 **Caso de estudio completo:** [juanpabloante.vercel.app/es/projects/presupuestos](https://juanpabloante.vercel.app/es/projects/presupuestos)
