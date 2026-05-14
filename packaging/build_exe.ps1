$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

$Python = "python"
$VenvPath = Join-Path $RepoRoot ".venv-build"
$VenvPython = Join-Path $VenvPath "Scripts\python.exe"

if (-not (Test-Path $VenvPython)) {
    & $Python -m venv $VenvPath
}

& $VenvPython -m pip install --upgrade pip
& $VenvPython -m pip install -r requirements.txt
& $VenvPython -m PyInstaller --clean --noconfirm pc_repair_crm_pro.spec

$ExePath = Join-Path $RepoRoot "dist\PC Repair CRM Pro\PC Repair CRM Pro.exe"
if (-not (Test-Path $ExePath)) {
    throw "Build finished, but executable was not found at $ExePath"
}

Write-Host "Built executable: $ExePath"
