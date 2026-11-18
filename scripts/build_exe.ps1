param(
    [switch]$Clean
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

if ($Clean) {
    Remove-Item -Recurse -Force build, dist -ErrorAction SilentlyContinue
}

python -m pip install -r requirements.txt
python -m PyInstaller --clean --noconfirm brd2ibom.spec
Write-Host "完成：$repoRoot\dist\brdibom.exe"

