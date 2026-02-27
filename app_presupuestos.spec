# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

block_cipher = None

def collect_dir(src_dir: str, dest_root: str):
    out = []
    p = Path(src_dir)
    if not p.exists():
        return out
    for f in p.rglob("*"):
        if f.is_file():
            rel_parent = f.parent.relative_to(p)
            target = Path(dest_root) / rel_parent
            out.append((str(f), str(target)))
    return out


datas = [
    ("logo_control_360_A.png", "."),
    ("logo_control_360_S.png", "."),
    ("FORMATO EXPORTACION.xlsx", "."),
    ("profesionales_limpio.csv", "."),
    ("views/arrow_down_white.svg", "views"),
]
datas += collect_dir("data_gobernacion", "data_gobernacion")
datas += collect_dir("PRUEBAS", "PRUEBAS")

hiddenimports = [
    "views.ejecucion_view",
    "views.cronograma_view",
    "views.evm_view",
    "views.administracion_window",
    "views.ifc_model_viewer_dialog",
    "ifcopenshell",
    "pyvista",
    "pyvistaqt",
]

a = Analysis(
    ["app.py"],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Control360",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon="build/icons/control360_a.ico",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="Control360",
)


