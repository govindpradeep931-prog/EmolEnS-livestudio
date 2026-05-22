# Optimizing Multimodal Emotion Recognition - PowerShell launcher
# Usage: .\start.ps1

$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot
$BackendDir = Join-Path $Root "backend"
$VenvPy = Join-Path $BackendDir ".venv\Scripts\python.exe"

function Get-NodeExe {
    if (Get-Command node -ErrorAction SilentlyContinue) {
        return "node"
    }

    $Bundled = Join-Path $Root "node-v24.15.0-win-x64\node.exe"
    if (Test-Path $Bundled) {
        return (Resolve-Path $Bundled).Path
    }

    $ParentBundled = Join-Path $Root "..\node-v24.15.0-win-x64\node.exe"
    if (Test-Path $ParentBundled) {
        return (Resolve-Path $ParentBundled).Path
    }

    throw "Node.js not found. Install Node.js or keep the bundled node-v24.15.0-win-x64 folder in this project."
}

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Optimizing Multimodal Emotion Recognition" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

if (-not (Test-Path $VenvPy)) {
    Write-Host "Creating Python virtual environment..." -ForegroundColor Yellow
    Push-Location $BackendDir
    python -m venv .venv
    & ".\.venv\Scripts\python.exe" -m pip install -r requirements.txt
    Pop-Location
}

$NodeExe = Get-NodeExe
$env:PYTHON = $VenvPy

Write-Host "Starting UI and ML backend in this terminal..." -ForegroundColor Green
Write-Host "Open the localhost URL printed by the server below." -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop both services." -ForegroundColor DarkGray
Write-Host ""

Set-Location -LiteralPath $Root
& $NodeExe server.js
