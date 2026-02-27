#!/usr/bin/env python
from __future__ import annotations

"""
importar_todo_bd.py

Script maestro para poblar la base de datos de AppPresupuestos en un solo paso.

Incluye:
1) Esquema de BD (create_all o reset completo).
2) Catalogo base:
   - recursos_unicos.csv
   - analisis_unitarios.csv
   - recursos_analisis.csv
   - profesionales (.xlsx o .csv)
3) Ejecuciones (facturas/materiales + nomina) via CSV:
   - deteccion automatica por carpetas (scan recursivo)
   - o carga explicita por argumento.

Opcional:
- Regenerar CSV base desde PDF antes de importar catalogo.
"""

import argparse
import os
import sys
from dataclasses import dataclass
from pathlib import Path

# Asegurar root de proyecto para imports locales.
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Registrar todos los modelos en Base.metadata
import models  # noqa: F401,E402
from import_ejecucion_csv import import_ejecucion  # noqa: E402
from models.database import Base, engine  # noqa: E402
from models.update_db import (  # noqa: E402
    cargar_analisis_unitarios,
    cargar_datos_recursos_desde_csv,
    cargar_profesionales_desde_csv,
    cargar_profesionales_desde_excel,
    cargar_relacion_analisis_unitarios_recursos,
)


@dataclass
class EjecucionSpec:
    nombre: str
    materiales: Path
    nomina: Path


def _abs_path(path_str: str) -> Path:
    p = Path(path_str)
    if not p.is_absolute():
        p = PROJECT_ROOT / p
    return p.resolve()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Importador integral de BD para AppPresupuestos."
    )

    parser.add_argument(
        "--reset",
        action="store_true",
        help="Elimina todas las tablas y las recrea antes de importar.",
    )
    parser.add_argument(
        "--solo-catalogo",
        action="store_true",
        help="Importa solo catalogo base (sin ejecuciones).",
    )
    parser.add_argument(
        "--solo-ejecuciones",
        action="store_true",
        help="Importa solo ejecuciones (sin catalogo base).",
    )

    parser.add_argument(
        "--extraer-pdf",
        action="store_true",
        help="Regenera CSV base desde PDF antes de cargar catalogo.",
    )
    parser.add_argument(
        "--pdf-path",
        default=r"data_gobernacion\-ANALISIS UNITARIOS DECRET 1276 -2021.pdf",
        help="Ruta al PDF origen para extraccion (si se usa --extraer-pdf).",
    )

    parser.add_argument(
        "--recursos",
        default=r"data_gobernacion\recursos_unicos.csv",
        help="CSV de recursos.",
    )
    parser.add_argument(
        "--analisis",
        default=r"data_gobernacion\analisis_unitarios.csv",
        help="CSV de analisis unitarios.",
    )
    parser.add_argument(
        "--relacion",
        default=r"data_gobernacion\recursos_analisis.csv",
        help="CSV de relacion analisis-recursos.",
    )
    parser.add_argument(
        "--profesionales",
        default=r"data_gobernacion\PROFESIONALES.xlsx",
        help="Archivo de profesionales (.xlsx o .csv).",
    )
    parser.add_argument(
        "--sheet",
        type=int,
        default=0,
        help="Indice de hoja para Excel de profesionales.",
    )

    parser.add_argument(
        "--scan-ejecuciones-dir",
        default=r"PRUEBAS",
        help="Directorio a escanear recursivamente para ejecuciones CSV.",
    )
    parser.add_argument(
        "--no-scan",
        action="store_true",
        help="Desactiva escaneo automatico de ejecuciones por carpeta.",
    )
    parser.add_argument(
        "--materiales-file",
        default="db_materiales.csv",
        help="Nombre del archivo CSV de materiales para scan automatico.",
    )
    parser.add_argument(
        "--nomina-file",
        default="db_mano_obra.csv",
        help="Nombre del archivo CSV de nomina para scan automatico.",
    )
    parser.add_argument(
        "--reemplazar-ejecuciones",
        action="store_true",
        help="Reemplaza ejecuciones existentes con el mismo nombre.",
    )
    parser.add_argument(
        "--detener-en-error",
        action="store_true",
        help="Detiene todo el proceso ante el primer error de importacion.",
    )
    parser.add_argument(
        "--ejecucion",
        action="append",
        default=[],
        metavar="NOMBRE|MATERIALES|NOMINA",
        help=(
            "Carga explicita de ejecucion. Repetible. "
            "Formato: NOMBRE|ruta_materiales.csv|ruta_nomina.csv"
        ),
    )

    args = parser.parse_args()
    if args.solo_catalogo and args.solo_ejecuciones:
        parser.error("No puedes usar --solo-catalogo y --solo-ejecuciones a la vez.")
    return args


def recreate_or_ensure_schema(reset: bool) -> None:
    if reset:
        print("[DB] Eliminando y recreando tablas...")
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
    else:
        print("[DB] Verificando/creando tablas faltantes...")
        Base.metadata.create_all(bind=engine, checkfirst=True)
    print("[DB] Esquema listo.")


def run_pdf_extraction(pdf_path: Path) -> None:
    print(f"[EXTRACCION] Generando CSV base desde PDF: {pdf_path}")
    if not pdf_path.is_file():
        raise FileNotFoundError(f"No existe PDF: {pdf_path}")

    # 1) Genera analisis_unitarios.csv y recursos_analisis.csv
    from db_extraction_analisis_unitarios import main as extract_analisis_main  # noqa: WPS433

    # 2) Genera recursos_unicos.csv
    from db_extraction import main as extract_recursos_main  # noqa: WPS433

    cwd_before = Path.cwd()
    try:
        # Los scripts usan rutas relativas; ejecutar desde root de proyecto.
        os.chdir(str(PROJECT_ROOT))
        extract_analisis_main()
        extract_recursos_main()
    finally:
        os.chdir(str(cwd_before))
    print("[EXTRACCION] CSV base regenerados.")


def import_catalogo(args: argparse.Namespace) -> None:
    recursos = _abs_path(args.recursos)
    analisis = _abs_path(args.analisis)
    relacion = _abs_path(args.relacion)
    profesionales = _abs_path(args.profesionales)

    print("[CATALOGO] Iniciando carga base...")
    if recursos.is_file():
        cargar_datos_recursos_desde_csv(str(recursos))
    else:
        print(f"[CATALOGO] Archivo no encontrado (recursos): {recursos}")

    if analisis.is_file():
        cargar_analisis_unitarios(str(analisis))
    else:
        print(f"[CATALOGO] Archivo no encontrado (analisis): {analisis}")

    if relacion.is_file():
        cargar_relacion_analisis_unitarios_recursos(str(relacion))
    else:
        print(f"[CATALOGO] Archivo no encontrado (relacion): {relacion}")

    if profesionales.is_file():
        if profesionales.suffix.lower() == ".csv":
            cargar_profesionales_desde_csv(str(profesionales))
        else:
            cargar_profesionales_desde_excel(str(profesionales), sheet_name=args.sheet)
    else:
        print(f"[CATALOGO] Archivo no encontrado (profesionales): {profesionales}")
    print("[CATALOGO] Carga finalizada.")


def parse_ejecucion_args(ejec_args: list[str]) -> list[EjecucionSpec]:
    result: list[EjecucionSpec] = []
    for raw in ejec_args:
        parts = [p.strip() for p in raw.split("|")]
        if len(parts) != 3:
            raise ValueError(
                f"Formato invalido en --ejecucion: {raw!r}. "
                "Usa NOMBRE|MATERIALES|NOMINA"
            )
        nombre, mat, nom = parts
        result.append(
            EjecucionSpec(
                nombre=nombre,
                materiales=_abs_path(mat),
                nomina=_abs_path(nom),
            )
        )
    return result


def discover_ejecuciones(
    base_dir: Path,
    materiales_name: str,
    nomina_name: str,
) -> list[EjecucionSpec]:
    specs: list[EjecucionSpec] = []
    if not base_dir.is_dir():
        print(f"[EJECUCIONES] Directorio de scan no existe: {base_dir}")
        return specs

    used_names: set[str] = set()
    for materiales_path in sorted(base_dir.rglob(materiales_name)):
        nomina_path = materiales_path.parent / nomina_name
        if not nomina_path.is_file():
            continue

        # Nombre base por carpeta contenedora.
        nombre_base = materiales_path.parent.name.strip() or "EJECUCION"
        nombre = nombre_base
        if nombre in used_names:
            # Desambiguar con ruta relativa si hay carpetas repetidas.
            rel_parent = materiales_path.parent.relative_to(base_dir)
            nombre = str(rel_parent).replace("\\", " - ").replace("/", " - ")
        used_names.add(nombre)

        specs.append(
            EjecucionSpec(
                nombre=nombre,
                materiales=materiales_path.resolve(),
                nomina=nomina_path.resolve(),
            )
        )
    return specs


def import_ejecuciones(specs: list[EjecucionSpec], reemplazar: bool, detener_en_error: bool) -> None:
    if not specs:
        print("[EJECUCIONES] No hay ejecuciones para importar.")
        return

    print(f"[EJECUCIONES] Importando {len(specs)} ejecucion(es)...")
    errores: list[str] = []
    for i, spec in enumerate(specs, start=1):
        print(f"[EJECUCIONES] ({i}/{len(specs)}) {spec.nombre}")
        try:
            import_ejecucion(
                nombre=spec.nombre,
                materiales_path=str(spec.materiales),
                nomina_path=str(spec.nomina),
                reemplazar=reemplazar,
            )
        except Exception as exc:
            msg = f"{spec.nombre}: {exc}"
            errores.append(msg)
            print(f"[EJECUCIONES] ERROR -> {msg}")
            if detener_en_error:
                raise

    if errores:
        print("[EJECUCIONES] Finalizo con errores:")
        for err in errores:
            print(f"  - {err}")
    else:
        print("[EJECUCIONES] Importacion completada sin errores.")


def main() -> None:
    args = parse_args()

    recreate_or_ensure_schema(reset=args.reset)

    if args.extraer_pdf:
        run_pdf_extraction(_abs_path(args.pdf_path))

    if not args.solo_ejecuciones:
        import_catalogo(args)

    if not args.solo_catalogo:
        specs = parse_ejecucion_args(args.ejecucion)
        if not args.no_scan:
            scan_dir = _abs_path(args.scan_ejecuciones_dir)
            discovered = discover_ejecuciones(
                base_dir=scan_dir,
                materiales_name=args.materiales_file,
                nomina_name=args.nomina_file,
            )
            specs.extend(discovered)

        # Deduplicar por (nombre, materiales, nomina) preservando orden.
        uniq_specs: list[EjecucionSpec] = []
        seen: set[tuple[str, str, str]] = set()
        for s in specs:
            key = (s.nombre, str(s.materiales), str(s.nomina))
            if key in seen:
                continue
            seen.add(key)
            uniq_specs.append(s)

        import_ejecuciones(
            specs=uniq_specs,
            reemplazar=bool(args.reemplazar_ejecuciones),
            detener_en_error=bool(args.detener_en_error),
        )

    print("[OK] Proceso integral finalizado.")


if __name__ == "__main__":
    main()


