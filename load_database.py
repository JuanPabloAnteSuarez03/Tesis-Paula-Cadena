#!/usr/bin/env python
"""load_database.py

Inicializa por completo la base de datos PostgreSQL para la aplicación
"AppPresupuestos".

Pasos que realiza:
1. Elimina todas las tablas definidas en los modelos y las vuelve a crear
   (equivalente a ejecutar `create_tables.py`).
2. Carga datos de:
   • Recursos (`data_gobernacion/recursos_unicos.csv`)
   • Análisis unitarios (`data_gobernacion/analisis_unitarios.csv`)
   • Relación análisis-recursos (`data_gobernacion/recursos_analisis.csv`)
   • Profesionales (`data_gobernacion/PROFESIONALES.xlsx`)

Puedes ajustar las rutas con los argumentos opcionales.

Uso por defecto:
    python load_database.py

Con rutas personalizadas:
    python load_database.py \
        --recursos path/recursos.csv \
        --analisis path/analisis.csv \
        --relacion path/relacion.csv \
        --profesionales path/profes.xlsx
"""
from __future__ import annotations

import argparse
import os
import sys

# Asegurar que el project root esté en sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from create_tables import Base, engine  # noqa: E402
from models.update_db import (
    cargar_datos_recursos_desde_csv,
    cargar_analisis_unitarios,
    cargar_relacion_analisis_unitarios_recursos,
    cargar_profesionales_desde_excel,
    cargar_profesionales_desde_csv,
)  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Recrea tablas y carga los datos iniciales en la base de datos"
    )
    parser.add_argument(
        "--recursos",
        default="data_gobernacion/recursos_unicos.csv",
        help="CSV con los recursos (por defecto data_gobernacion/recursos_unicos.csv)",
    )
    parser.add_argument(
        "--analisis",
        default="data_gobernacion/analisis_unitarios.csv",
        help="CSV con los análisis unitarios",
    )
    parser.add_argument(
        "--relacion",
        default="data_gobernacion/recursos_analisis.csv",
        help="CSV con la relación análisis-recursos",
    )
    parser.add_argument(
        "--profesionales",
        default="data_gobernacion/PROFESIONALES.xlsx",
        help="Excel con los profesionales",
    )
    parser.add_argument(
        "--sheet",
        type=int,
        default=0,
        help="Índice de la hoja dentro del Excel de profesionales (default 0)",
    )
    return parser.parse_args()


def recreate_tables() -> None:
    print("🔄  Eliminando y recreando tablas …")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("✅  Tablas recreadas")


def main() -> None:
    args = parse_args()

    # 1. Re-crear tablas
    recreate_tables()

    # 2. Cargar CSV de recursos
    if args.recursos and os.path.isfile(args.recursos):
        cargar_datos_recursos_desde_csv(args.recursos)
    else:
        print(f"⚠️  Archivo de recursos no encontrado → {args.recursos}")

    # 3. Cargar CSV de análisis unitarios
    if args.analisis and os.path.isfile(args.analisis):
        cargar_analisis_unitarios(args.analisis)
    else:
        print(f"⚠️  Archivo de análisis unitarios no encontrado → {args.analisis}")

    # 4. Cargar relación análisis-recursos
    if args.relacion and os.path.isfile(args.relacion):
        cargar_relacion_analisis_unitarios_recursos(args.relacion)
    else:
        print(f"⚠️  Archivo de relación análisis-recursos no encontrado → {args.relacion}")

    # 5. Cargar profesionales
    if args.profesionales and os.path.isfile(args.profesionales):
        if args.profesionales.lower().endswith('.csv'):
            cargar_profesionales_desde_csv(args.profesionales)
        else:
            cargar_profesionales_desde_excel(args.profesionales, sheet_name=args.sheet)
    else:
        print(f"⚠️  Archivo de profesionales no encontrado → {args.profesionales}")

    print("📦  Proceso de carga finalizado")


if __name__ == "__main__":
    main() 