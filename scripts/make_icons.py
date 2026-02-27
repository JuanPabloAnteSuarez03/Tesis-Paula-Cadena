from __future__ import annotations

from pathlib import Path

from PIL import Image


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    src = project_root / "logo_control_360_A.png"
    out_dir = project_root / "build" / "icons"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "control360_a.ico"

    if not src.is_file():
        raise FileNotFoundError(f"No existe el logo fuente: {src}")

    with Image.open(src) as img:
        img = img.convert("RGBA")
        sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
        img.save(out, format="ICO", sizes=sizes)

    print(f"Icono generado desde {src.name}: {out}")


if __name__ == "__main__":
    main()


