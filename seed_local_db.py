#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
import os
import sys
from pathlib import Path

# Asegurar root de proyecto para imports locales.
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import models  # noqa: F401
from import_ejecucion_csv import import_ejecucion
from models import AnalisisUnitario, AnalisisUnitarioRecurso, Profesional, Recurso
from models.database import Base, SessionLocal, engine


def _runtime_base_dir() -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return PROJECT_ROOT


def _pick_existing(paths: list[Path]) -> Path | None:
    for p in paths:
        if p.is_file():
            return p
    return None


def _float(v) -> float:
    txt = str(v or "").strip().replace("$", "").replace(" ", "")
    if not txt:
        return 0.0
    if "," in txt and "." not in txt:
        txt = txt.replace(",", ".")
    else:
        txt = txt.replace(",", "")
    try:
        return float(txt)
    except Exception:
        return 0.0


def _bool(v) -> bool:
    return str(v or "").strip().lower() in ("1", "true", "t", "si", "sí", "yes", "y")


def _load_recursos(recursos_csv: Path) -> int:
    session = SessionLocal()
    try:
        existing = {r.codigo: r for r in session.query(Recurso).all()}
        inserted = 0
        with recursos_csv.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                codigo = str(row.get("Codigo", "")).strip()
                if not codigo:
                    continue
                payload = {
                    "descripcion": str(row.get("Descripcion", "")).strip(),
                    "unidad": str(row.get("Unidad", "")).strip() or "UND",
                    "valor_unitario": _float(row.get("Valor Unitario", 0)),
                }
                obj = existing.get(codigo)
                if obj is None:
                    obj = Recurso(codigo=codigo, **payload)
                    session.add(obj)
                    existing[codigo] = obj
                    inserted += 1
                else:
                    obj.descripcion = payload["descripcion"]
                    obj.unidad = payload["unidad"]
                    obj.valor_unitario = payload["valor_unitario"]
        session.commit()
        return inserted
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _load_analisis(analisis_csv: Path) -> int:
    session = SessionLocal()
    try:
        existing = {a.codigo: a for a in session.query(AnalisisUnitario).all()}
        inserted = 0
        with analisis_csv.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                codigo = str(row.get("codigo", "")).strip()
                if not codigo:
                    continue
                payload = {
                    "descripcion": str(row.get("descripcion", "")).strip(),
                    "unidad": str(row.get("unidad", "")).strip() or "UND",
                    "total": _float(row.get("total", 0)),
                }
                obj = existing.get(codigo)
                if obj is None:
                    obj = AnalisisUnitario(codigo=codigo, **payload)
                    session.add(obj)
                    existing[codigo] = obj
                    inserted += 1
                else:
                    obj.descripcion = payload["descripcion"]
                    obj.unidad = payload["unidad"]
                    obj.total = payload["total"]
        session.commit()
        return inserted
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _load_relaciones(relaciones_csv: Path, force: bool) -> int:
    session = SessionLocal()
    try:
        if force:
            session.query(AnalisisUnitarioRecurso).delete()
            session.commit()
        else:
            if session.query(AnalisisUnitarioRecurso).count() > 0:
                return 0

        batch: list[AnalisisUnitarioRecurso] = []
        total_inserted = 0
        with relaciones_csv.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                codigo_analisis = str(row.get("codigo_analisis", "")).strip()
                codigo_recurso = str(row.get("codigo_recurso", "")).strip()
                if not codigo_analisis or not codigo_recurso:
                    continue
                batch.append(
                    AnalisisUnitarioRecurso(
                        codigo_analisis=codigo_analisis,
                        codigo_recurso=codigo_recurso,
                        descripcion_recurso=str(row.get("descripcion_recurso", "")).strip(),
                        unidad_recurso=str(row.get("unidad_recurso", "")).strip() or "UND",
                        cantidad_recurso=_float(row.get("cantidad_recurso", 0)),
                        desper=_float(row.get("desper", 0)),
                        vr_unitario=_float(row.get("vr_unitario", 0)),
                        vr_parcial=_float(row.get("vr_parcial", 0)),
                    )
                )
                if len(batch) >= 2000:
                    session.bulk_save_objects(batch)
                    session.commit()
                    total_inserted += len(batch)
                    batch.clear()
        if batch:
            session.bulk_save_objects(batch)
            session.commit()
            total_inserted += len(batch)
        return total_inserted
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _load_profesionales(profesionales_csv: Path) -> int:
    session = SessionLocal()
    try:
        existing = {p.nombre: p for p in session.query(Profesional).all()}
        inserted = 0
        with profesionales_csv.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                nombre = str(row.get("Cargo", "")).strip()
                if not nombre:
                    continue
                payload = {
                    "cargo": nombre,
                    "salario_mensual": _float(row.get("Valor Mensual", 0)),
                    "necesario": _bool(row.get("Es Obligatorio", False)),
                }
                obj = existing.get(nombre)
                if obj is None:
                    obj = Profesional(nombre=nombre, **payload)
                    session.add(obj)
                    existing[nombre] = obj
                    inserted += 1
                else:
                    obj.cargo = payload["cargo"]
                    obj.salario_mensual = payload["salario_mensual"]
                    obj.necesario = payload["necesario"]
        session.commit()
        return inserted
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _discover_execution_specs(scan_dir: Path) -> list[tuple[str, Path, Path]]:
    specs: list[tuple[str, Path, Path]] = []
    if not scan_dir.is_dir():
        return specs

    used_names: set[str] = set()
    for materiales in sorted(scan_dir.rglob("db_materiales.csv")):
        nomina = materiales.parent / "db_mano_obra.csv"
        if not nomina.is_file():
            continue

        nombre = materiales.parent.name.strip() or "EJECUCION"
        if nombre in used_names:
            nombre = str(materiales.parent.relative_to(scan_dir)).replace("\\", " - ")
        used_names.add(nombre)
        specs.append((nombre, materiales, nomina))
    return specs


def _seed_ejecuciones(scan_dir: Path, replace_existing: bool) -> int:
    imported = 0
    for nombre, materiales, nomina in _discover_execution_specs(scan_dir):
        try:
            import_ejecucion(
                nombre=nombre,
                materiales_path=str(materiales),
                nomina_path=str(nomina),
                reemplazar=replace_existing,
            )
            imported += 1
        except Exception as e:
            print(f"[seed] Ejecucion omitida ({nombre}): {e}")
    return imported


def seed_local_db(force: bool = False, include_ejecuciones: bool = True) -> None:
    base_dir = _runtime_base_dir()
    data_dir = base_dir / "data_gobernacion"
    pruebas_dir = base_dir / "PRUEBAS"

    recursos_csv = data_dir / "recursos_unicos.csv"
    analisis_csv = data_dir / "analisis_unitarios.csv"
    relaciones_csv = data_dir / "recursos_analisis.csv"
    profesionales_csv = _pick_existing(
        [
            base_dir / "profesionales_limpio.csv",
            data_dir / "profesionales_limpio.csv",
        ]
    )

    Base.metadata.create_all(bind=engine, checkfirst=True)

    print("[seed] Cargando catalogo base...")
    if recursos_csv.is_file():
        n = _load_recursos(recursos_csv)
        print(f"[seed] Recursos cargados/actualizados: {n}")
    else:
        print(f"[seed] No encontrado: {recursos_csv}")

    if analisis_csv.is_file():
        n = _load_analisis(analisis_csv)
        print(f"[seed] Analisis cargados/actualizados: {n}")
    else:
        print(f"[seed] No encontrado: {analisis_csv}")

    if relaciones_csv.is_file():
        n = _load_relaciones(relaciones_csv, force=force)
        print(f"[seed] Relaciones insertadas: {n}")
    else:
        print(f"[seed] No encontrado: {relaciones_csv}")

    if profesionales_csv and profesionales_csv.is_file():
        n = _load_profesionales(profesionales_csv)
        print(f"[seed] Profesionales cargados/actualizados: {n}")
    else:
        print("[seed] No se encontro profesionales_limpio.csv")

    if include_ejecuciones:
        print("[seed] Cargando ejecuciones desde PRUEBAS...")
        n = _seed_ejecuciones(pruebas_dir, replace_existing=force)
        print(f"[seed] Ejecuciones importadas: {n}")


def ensure_local_db_ready() -> None:
    # Solo auto-seed en modo empaquetado o cuando se pida explícitamente.
    auto = os.getenv("APP_AUTO_SEED", "").strip().lower() in ("1", "true", "yes", "si")
    if not auto and not getattr(sys, "frozen", False):
        return

    session = SessionLocal()
    try:
        Base.metadata.create_all(bind=engine, checkfirst=True)
        recursos_count = session.query(Recurso).count()
        analisis_count = session.query(AnalisisUnitario).count()
        if recursos_count > 0 and analisis_count > 0:
            return
    finally:
        session.close()

    try:
        seed_local_db(force=False, include_ejecuciones=True)
    except Exception as e:
        print("[seed] Error durante inicializacion local:", e)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Carga completa de base local SQLite.")
    p.add_argument("--force", action="store_true", help="Recarga completa de relaciones y ejecuciones.")
    p.add_argument("--sin-ejecuciones", action="store_true", help="No importa ejecuciones desde PRUEBAS.")
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    seed_local_db(force=bool(args.force), include_ejecuciones=not bool(args.sin_ejecuciones))


