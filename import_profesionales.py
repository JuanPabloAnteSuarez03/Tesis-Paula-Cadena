#!/usr/bin/env python
"""import_profesionales.py

Script CLI para cargar la hoja de profesionales a la base de datos PostgreSQL
usando la función `cargar_profesionales_desde_excel` ya definida en
`models.update_db`.

Uso básico:
    python import_profesionales.py data_gobernacion/PROFESIONALES.xlsx

Opciones:
    --sheet N   Número de hoja (0 por defecto)

Requiere:
    • Que la base de datos esté accesible según los parámetros definidos en
      `models/database.py`.
    • Que el paquete `openpyxl` esté instalado para que pandas pueda leer
      archivos .xlsx.
"""
from __future__ import annotations

import os
import sys
import argparse

# Asegurar que el directorio del proyecto esté en sys.path para los imports relativos
PROJ_DIR = os.path.dirname(os.path.abspath(__file__))
if PROJ_DIR not in sys.path:
    sys.path.insert(0, PROJ_DIR)

from models.update_db import cargar_profesionales_desde_excel, cargar_profesionales_desde_csv  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Importa profesionales desde un archivo Excel a la base de datos"
    )
    parser.add_argument(
        "archivo",
        help="Ruta al archivo .xlsx o .csv que contiene la tabla de profesionales",
    )
    parser.add_argument(
        "--sheet",
        "-s",
        type=int,
        default=0,
        help="Índice de la hoja dentro del Excel (por defecto 0)",
    )
    args = parser.parse_args()

    file_path = args.archivo
    if not os.path.isfile(file_path):
        print(f"❌ Archivo no encontrado: {file_path}")
        sys.exit(1)

    if file_path.lower().endswith('.csv'):
        print(f"▶ Cargando profesionales desde CSV '{file_path}' …")
        cargar_profesionales_desde_csv(file_path)
    else:
        print(
            f"▶ Cargando profesionales desde Excel '{file_path}', hoja {args.sheet} …"
        )
        cargar_profesionales_desde_excel(file_path, sheet_name=args.sheet)


if __name__ == "__main__":
    main() 