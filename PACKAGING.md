# Empaquetado y Distribucion (Windows)

Este proyecto ya incluye:

- Ejecutable con `PyInstaller` (`app_presupuestos.spec`)
- Instalador con `Inno Setup` (`installer/AppPresupuestos.iss`)
- Iconos `.ico` generados desde `logo_control_360_A.png`
- Base de datos local SQLite para distribucion (auto-seed al primer inicio)

## 1) Construir ejecutable + instalador

En PowerShell, desde la raiz del proyecto:

```powershell
.\build_release.ps1
```

Si solo quieres el ejecutable (sin instalador):

```powershell
.\build_release.ps1 -SkipInstaller
```

Salidas:

- Ejecutable: `dist\AppPresupuestos\AppPresupuestos.exe`
- Instalador: `dist\installer\AppPresupuestos_Setup.exe` (si Inno Setup esta instalado)

## 2) Base de datos local incluida

En build distribuido, la app usa SQLite local automaticamente:

- Ruta: `%LOCALAPPDATA%\Control360\AppPresupuestos\app_presupuestos.db`

Al primer arranque:

- Crea tablas
- Carga catalogo base desde `data_gobernacion`
- Carga profesionales desde `profesionales_limpio.csv`
- Carga ejecuciones desde `PRUEBAS/**/db_materiales.csv` + `db_mano_obra.csv`

## 3) Iconos y logo

- Icono del `.exe`, barra de tareas y ventana: `logo_control_360_A` (convertido a `.ico`)
- Icono del instalador: mismo `.ico`
- Splash mantiene su logo independiente en `StartWindow`

## 4) Variables opcionales

- `APP_DB_BACKEND=sqlite|postgresql`
- `APP_DB_PATH=C:\ruta\mi_bd.db`
- `APP_DB_URL=...` (override total)
- `APP_AUTO_SEED=1` (fuerza autoseed tambien fuera de build empaquetado)


