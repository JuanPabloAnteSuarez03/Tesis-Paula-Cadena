#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
import os
import sys
from datetime import datetime

# Asegurar que el project root esté en sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from models import Ejecucion, Factura, FacturaItem, PagoNomina  # noqa: E402
from models.database import Base, SessionLocal, engine  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Importa una ejecución con facturas/materiales y nómina desde CSV."
    )
    parser.add_argument(
        "--nombre",
        required=True,
        help="Nombre de la ejecución a crear (ej. 'PISTA TROTE').",
    )
    parser.add_argument(
        "--materiales",
        default=r"PRUEBAS\PISTA TROTE\db_materiales.csv",
        help="Ruta del CSV de materiales/facturas.",
    )
    parser.add_argument(
        "--nomina",
        default=r"PRUEBAS\PISTA TROTE\db_mano_obra.csv",
        help="Ruta del CSV de nómina.",
    )
    parser.add_argument(
        "--reemplazar",
        action="store_true",
        help="Si la ejecución ya existe, la elimina y la vuelve a crear.",
    )
    return parser.parse_args()


def _open_csv_flexible(path: str):
    # Intenta primero UTF-8 (con/sin BOM), luego LATIN1 por datos legacy.
    encodings = ("utf-8-sig", "utf-8", "latin1")
    last_exc = None
    for enc in encodings:
        try:
            return open(path, "r", encoding=enc, newline="")
        except UnicodeDecodeError as exc:
            last_exc = exc
    if last_exc:
        raise last_exc
    raise RuntimeError(f"No se pudo abrir {path}")


def _to_float(value: str) -> float:
    txt = (value or "").strip().replace("$", "").replace(" ", "")
    if not txt:
        return 0.0
    # Soporte básico para decimal con coma.
    if "," in txt and "." not in txt:
        txt = txt.replace(",", ".")
    else:
        txt = txt.replace(",", "")
    try:
        return float(txt)
    except ValueError:
        return 0.0


def _to_date(value: str):
    txt = (value or "").strip()
    if not txt:
        return None
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(txt, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Fecha inválida: {value!r}")


def _read_materiales(path: str) -> list[dict]:
    rows: list[dict] = []
    with _open_csv_flexible(path) as f:
        reader = csv.reader(f)
        header_skipped = False
        for line_no, raw in enumerate(reader, start=1):
            if not raw or not any((c or "").strip() for c in raw):
                continue
            if not header_skipped:
                header_skipped = True
                continue
            if len(raw) < 7:
                print(f"⚠️  Línea {line_no} en materiales ignorada (columnas insuficientes): {raw}")
                continue

            # Parse robusto para líneas con comas dentro de "Insumo":
            # [Numero, Fecha, Proveedor, ...Insumo..., Cantidad, Precio_Unit, Total]
            numero = (raw[0] or "").strip().upper()
            fecha_txt = (raw[1] or "").strip()
            cantidad_txt = raw[-3]
            precio_txt = raw[-2]
            total_txt = raw[-1]
            middle = raw[2:-3]

            if not middle:
                print(f"⚠️  Línea {line_no} en materiales ignorada (sin proveedor/insumo): {raw}")
                continue

            proveedor = (middle[0] or "").strip().upper()
            insumo = ",".join(middle[1:]).strip() if len(middle) > 1 else ""
            if not insumo:
                insumo = "SIN DESCRIPCION"

            try:
                fecha = _to_date(fecha_txt)
            except ValueError as exc:
                print(f"⚠️  Línea {line_no} ignorada por fecha inválida: {exc}")
                continue

            rows.append(
                {
                    "numero_factura": numero,
                    "fecha": fecha,
                    "proveedor": proveedor or "SIN PROVEEDOR",
                    "insumo": insumo,
                    "cantidad": _to_float(cantidad_txt),
                    "precio_unitario": _to_float(precio_txt),
                    "total": _to_float(total_txt),
                    "aplica_iva": "(c/iva)" in insumo.lower(),
                }
            )
    return rows


def _read_nomina(path: str) -> list[dict]:
    rows: list[dict] = []
    with _open_csv_flexible(path) as f:
        reader = csv.reader(f)
        header_skipped = False
        for line_no, raw in enumerate(reader, start=1):
            if not raw or not any((c or "").strip() for c in raw):
                continue
            if not header_skipped:
                header_skipped = True
                continue
            if len(raw) < 6:
                print(f"⚠️  Línea {line_no} en nómina ignorada (columnas insuficientes): {raw}")
                continue

            fecha_txt = (raw[0] or "").strip()
            trabajador = (raw[1] or "").strip().upper()
            cargo = (raw[2] or "").strip().upper()
            dias_txt = raw[3]
            modo_txt = (raw[4] or "").strip().upper()
            total_txt = raw[5]
            observacion = ",".join(raw[6:]).strip().upper() if len(raw) > 6 else ""

            try:
                fecha = _to_date(fecha_txt)
            except ValueError as exc:
                print(f"⚠️  Línea {line_no} ignorada por fecha inválida: {exc}")
                continue

            dias = _to_float(dias_txt) or 1.0
            total = _to_float(total_txt)
            modalidad = "GLOBAL" if "GLOBAL" in modo_txt else "JORNAL"
            if modalidad == "JORNAL":
                valor = (total / dias) if dias > 0 else total
            else:
                dias = 1.0
                valor = total

            rows.append(
                {
                    "fecha": fecha,
                    "trabajador": trabajador or "SIN NOMBRE",
                    "cargo": cargo or "SIN CARGO",
                    "modalidad": modalidad,
                    "dias": dias,
                    "valor": valor,
                    "total": total,
                    "observacion": observacion,
                }
            )
    return rows


def import_ejecucion(
    nombre: str,
    materiales_path: str,
    nomina_path: str,
    reemplazar: bool,
) -> None:
    if not os.path.isfile(materiales_path):
        raise FileNotFoundError(f"No existe CSV de materiales: {materiales_path}")
    if not os.path.isfile(nomina_path):
        raise FileNotFoundError(f"No existe CSV de nómina: {nomina_path}")

    # Seguridad: crear tablas faltantes si no existen.
    Base.metadata.create_all(bind=engine, checkfirst=True)

    materiales = _read_materiales(materiales_path)
    nomina = _read_nomina(nomina_path)

    if not materiales and not nomina:
        raise RuntimeError("No se encontraron registros válidos para importar.")

    session = SessionLocal()
    try:
        existing = session.query(Ejecucion).filter(Ejecucion.nombre == nombre).first()
        if existing:
            if not reemplazar:
                raise RuntimeError(
                    f"Ya existe una ejecución llamada '{nombre}'. "
                    f"Usa --reemplazar para sobreescribir."
                )
            session.delete(existing)
            session.flush()

        ejec = Ejecucion(nombre=nombre)
        session.add(ejec)
        session.flush()

        facturas_by_key: dict[tuple[str, object, str], Factura] = {}
        facturas_count = 0
        items_count = 0
        for m in materiales:
            key = (m["numero_factura"], m["fecha"], m["proveedor"])
            factura = facturas_by_key.get(key)
            if factura is None:
                factura = Factura(
                    numero_factura=m["numero_factura"],
                    fecha=m["fecha"],
                    fecha_programada=None,
                    proveedor=m["proveedor"],
                    ejecucion_id=ejec.id,
                )
                session.add(factura)
                facturas_by_key[key] = factura
                facturas_count += 1

            item = FacturaItem(
                factura=factura,
                insumo=m["insumo"],
                cantidad=m["cantidad"],
                precio_unitario=m["precio_unitario"],
                aplica_iva=bool(m["aplica_iva"]),
                total=m["total"],
            )
            session.add(item)
            items_count += 1

        nomina_count = 0
        for n in nomina:
            pago = PagoNomina(
                fecha=n["fecha"],
                trabajador=n["trabajador"],
                cargo=n["cargo"],
                modalidad=n["modalidad"],
                dias=n["dias"],
                valor=n["valor"],
                total=n["total"],
                observacion=n["observacion"],
                ejecucion_id=ejec.id,
            )
            session.add(pago)
            nomina_count += 1

        session.commit()
        print("✅ Importación completada")
        print(f"   Ejecución: {nombre} (id={ejec.id})")
        print(f"   Facturas: {facturas_count}")
        print(f"   Ítems factura: {items_count}")
        print(f"   Pagos nómina: {nomina_count}")
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def main() -> None:
    args = parse_args()
    import_ejecucion(
        nombre=args.nombre.strip(),
        materiales_path=args.materiales,
        nomina_path=args.nomina,
        reemplazar=bool(args.reemplazar),
    )


if __name__ == "__main__":
    main()

