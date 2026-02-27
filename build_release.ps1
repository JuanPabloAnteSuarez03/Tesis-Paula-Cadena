param(
    [switch]$SkipInstaller
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

function Invoke-Step {
    param(
        [string]$Title,
        [scriptblock]$Cmd
    )
    Write-Host "== $Title =="
    & $Cmd
    if ($LASTEXITCODE -ne 0) {
        throw "Fallo en paso: $Title (exit code $LASTEXITCODE)"
    }
}

Invoke-Step "Instalando dependencias de empaquetado" {
    python -m pip install --upgrade pip
}
Invoke-Step "Instalando pyinstaller y pillow" {
    python -m pip install pyinstaller pillow
}

Invoke-Step "Generando iconos .ico desde logo_control_360_A.png" {
    python .\scripts\make_icons.py
}

Invoke-Step "Construyendo ejecutable (PyInstaller)" {
    python -m PyInstaller --noconfirm --clean .\app_presupuestos.spec
}

if (-not $SkipInstaller) {
    if (-not (Test-Path ".\dist\Control360\Control360.exe")) {
        throw "No existe .\dist\Control360\Control360.exe. Se cancela creación del instalador."
    }

    $isccCandidates = @(
        "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
        "${env:ProgramFiles}\Inno Setup 6\ISCC.exe"
    )
    $iscc = $isccCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1

    if ($null -eq $iscc) {
        Write-Warning "Inno Setup no encontrado. Se omite instalador. Instala Inno Setup 6 y vuelve a ejecutar."
    }
    else {
        Invoke-Step "Construyendo instalador (Inno Setup)" {
            & $iscc ".\installer\AppPresupuestos.iss"
        }
    }
}

Write-Host "== Build finalizado =="
Write-Host "Ejecutable: .\dist\Control360\Control360.exe"
Write-Host "Instalador: .\dist\installer\* (si Inno Setup estuvo disponible)"


