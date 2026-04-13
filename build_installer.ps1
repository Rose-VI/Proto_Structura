$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

$version = (Get-Content "$root\version.txt" -Raw).Trim()

Write-Host "Compilando ejecutable..."
python -m PyInstaller main.spec

$iscc = Get-Command iscc -ErrorAction SilentlyContinue
$isccPath = $null
if ($iscc) {
    $isccPath = $iscc.Source
}

if (-not $isccPath) {
    $defaultPath = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
    if (Test-Path $defaultPath) {
        $isccPath = $defaultPath
    }
}

if (-not $isccPath) {
    Write-Host "No se encontró Inno Setup Compiler (ISCC)."
    Write-Host "Instala Inno Setup y luego ejecuta:"
    Write-Host "  `"$root\installer\Structura.iss`""
    exit 0
}

Write-Host "Generando instalador..."
& $isccPath "/DMyAppVersion=$version" "$root\installer\Structura.iss"
if ($LASTEXITCODE -ne 0) {
    throw "La compilación del instalador falló con código $LASTEXITCODE."
}

Write-Host "Instalador generado en dist\installer\Structura-$version-Setup.exe"
