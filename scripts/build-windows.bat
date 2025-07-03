@echo off
REM DiPeO Windows Build Script (Batch Version)
REM This script builds the complete Windows installer for DiPeO

setlocal enabledelayedexpansion

echo ========================================
echo      DiPeO Windows Build Script
echo         Version: 0.1.0
echo ========================================
echo.

REM Get the root directory
set SCRIPT_DIR=%~dp0
set ROOT_DIR=%SCRIPT_DIR%..
cd /d "%ROOT_DIR%"

REM Step 1: Build Python Backend
echo [1/3] Building Python Backend...
cd apps\server

REM Check if virtual environment exists
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
)

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install --upgrade pip setuptools wheel >nul 2>&1
pip install -r requirements.txt >nul 2>&1
pip install pyinstaller >nul 2>&1

REM Install local packages
echo Installing DiPeO packages...
pip install -e "%ROOT_DIR%\packages\python\dipeo_core" >nul 2>&1
pip install -e "%ROOT_DIR%\packages\python\dipeo_domain" >nul 2>&1
pip install -e "%ROOT_DIR%\packages\python\dipeo_diagram" >nul 2>&1
pip install -e "%ROOT_DIR%\packages\python\dipeo_application" >nul 2>&1
pip install -e "%ROOT_DIR%\packages\python\dipeo_infra" >nul 2>&1
pip install -e "%ROOT_DIR%\packages\python\dipeo_container" >nul 2>&1
pip install -e . >nul 2>&1

REM Build executable
echo Building executable with PyInstaller...
pyinstaller build.spec --clean --noconfirm

if exist "dist\dipeo-server.exe" (
    echo Backend build complete
) else (
    echo ERROR: Backend build failed
    exit /b 1
)

cd "%ROOT_DIR%"
echo.

REM Step 2: Build Frontend
echo [2/3] Building Frontend...
cd apps\web

REM Install dependencies if needed
if not exist "node_modules" (
    echo Installing frontend dependencies...
    call pnpm install
)

REM Build frontend
echo Building production bundle...
call pnpm build

if exist "dist\index.html" (
    echo Frontend build complete
) else (
    echo ERROR: Frontend build failed
    exit /b 1
)

cd "%ROOT_DIR%"
echo.

REM Step 3: Build Tauri Installer
echo [3/3] Building Windows Installer...
cd apps\desktop

REM Check if backend executable exists
if not exist "%ROOT_DIR%\apps\server\dist\dipeo-server.exe" (
    echo ERROR: Backend executable not found
    exit /b 1
)

REM Install Tauri dependencies if needed
if not exist "node_modules" (
    echo Installing Tauri dependencies...
    call pnpm install
)

REM Build installer
echo Building installer (this may take several minutes)...
call pnpm tauri build --target x86_64-pc-windows-msvc

REM Check if build succeeded
if exist "src-tauri\target\release\bundle\nsis\*.exe" (
    echo.
    echo ========================================
    echo Build Complete!
    echo ========================================
    echo.
    echo Installer location:
    dir /b "src-tauri\target\release\bundle\nsis\*.exe"
    echo.
    echo Next steps:
    echo 1. Test the installer on a clean Windows machine
    echo 2. Sign the installer with a code signing certificate
    echo 3. Upload to GitHub Releases or your distribution platform
) else (
    echo ERROR: Installer build failed
    exit /b 1
)

cd "%ROOT_DIR%"
endlocal