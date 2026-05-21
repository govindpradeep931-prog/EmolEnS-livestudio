@echo off
setlocal
cd /d "%~dp0"

echo ============================================
echo   EmoLens Live Studio - Launcher
echo ============================================
echo.

set "VENV_PY=%~dp0backend\.venv\Scripts\python.exe"
if not exist "%VENV_PY%" (
    echo Creating Python virtual environment...
    cd /d "%~dp0backend"
    python -m venv .venv
    if errorlevel 1 exit /b 1
    "%VENV_PY%" -m pip install -r requirements.txt
    if errorlevel 1 exit /b 1
    cd /d "%~dp0"
)

where node >nul 2>nul
if %errorlevel% equ 0 (
    set "NODE_EXE=node"
) else if exist "%~dp0node-v24.15.0-win-x64\node.exe" (
    set "NODE_EXE=%~dp0node-v24.15.0-win-x64\node.exe"
) else if exist "%~dp0..\node-v24.15.0-win-x64\node.exe" (
    set "NODE_EXE=%~dp0..\node-v24.15.0-win-x64\node.exe"
) else (
    echo ERROR: Node.js was not found on PATH or in the bundled runtime folder.
    exit /b 1
)

set "PYTHON=%VENV_PY%"
echo Starting UI and ML backend in this terminal...
echo Open the localhost URL printed by the server below.
echo Press Ctrl+C to stop both services.
echo.
"%NODE_EXE%" server.js
