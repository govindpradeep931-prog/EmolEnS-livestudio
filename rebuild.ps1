# Optimizing Multimodal Emotion Recognition clean rebuild from scratch
# Usage: cd optimizing-multimodal-emotion-recognition; .\rebuild.ps1

$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot
$BackendDir = Join-Path $Root "backend"
$VenvDir = Join-Path $BackendDir ".venv"
$VenvPy = Join-Path $VenvDir "Scripts\python.exe"

function Get-NodeExe {
    if (Get-Command node -ErrorAction SilentlyContinue) { return "node" }
    $Bundled = Join-Path $Root "..\node-v24.15.0-win-x64\node.exe"
    if (Test-Path $Bundled) { return (Resolve-Path $Bundled).Path }
    throw "Node.js not found."
}

function Get-NpmCmd {
    $NodeExe = Get-NodeExe
    if ($NodeExe -eq "node") {
        if (Get-Command npm -ErrorAction SilentlyContinue) { return "npm" }
    }
    $NodeDir = Split-Path $NodeExe -Parent
    $NpmCli = Join-Path $NodeDir "node_modules\npm\bin\npm-cli.js"
    if (Test-Path $NpmCli) { return @($NodeExe, $NpmCli) }
    throw "npm not found."
}

function Invoke-Npm {
    param([string[]]$NpmArgs)
    $npm = Get-NpmCmd
    if ($npm -is [array]) {
        & $npm[0] $npm[1] @NpmArgs
    } else {
        & $npm @NpmArgs
    }
}

Write-Host "=== Optimizing Multimodal Emotion Recognition clean rebuild ===" -ForegroundColor Cyan

# Stop anything on 8000/8001
foreach ($port in 8000, 8001) {
    Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue |
        ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
}
Write-Host "[1/4] Stopped old servers on ports 8000/8001" -ForegroundColor Green

# Fresh Node deps
Write-Host "[2/4] Installing Node dependencies..." -ForegroundColor Yellow
Set-Location -LiteralPath $Root
if (Test-Path "node_modules") { Remove-Item -Recurse -Force "node_modules" }
Invoke-Npm @("install")
Write-Host "      Node dependencies OK" -ForegroundColor Green

# Fresh Python venv
Write-Host "[3/4] Rebuilding Python virtual environment (may take several minutes)..." -ForegroundColor Yellow
Set-Location -LiteralPath $BackendDir
if (Test-Path $VenvDir) { Remove-Item -Recurse -Force $VenvDir }
python -m venv .venv
& $VenvPy -m pip install --upgrade pip
& $VenvPy -m pip install -r requirements.txt
Write-Host "      Python environment OK" -ForegroundColor Green

# Pre-fetch MediaPipe face model
$ModelPath = Join-Path $BackendDir "models\face_landmarker.task"
if (-not (Test-Path $ModelPath) -or (Get-Item $ModelPath).Length -lt 1000000) {
    Write-Host "      Downloading Face Landmarker model..." -ForegroundColor Yellow
    & $VenvPy -c @"
import urllib.request, os
url = 'https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task'
path = os.path.join('models', 'face_landmarker.task')
urllib.request.urlretrieve(url, path)
print('Model size:', os.path.getsize(path))
"@
}

Write-Host "[4/4] Starting Optimizing Multimodal Emotion Recognition..." -ForegroundColor Green
Set-Location -LiteralPath $Root
& "$Root\start.ps1"
