@echo off
REM DiPeO Windows Build Script (Batch Version)
REM This script builds the complete Windows installer for DiPeO

setlocal enabledelayedexpansion

:: Parse command line arguments
set VERSION=0.1.0
if not "%1"=="" set VERSION=%1

echo ========================================
echo      DiPeO Windows Build Script
echo         Version: %VERSION%
echo ========================================
echo.
echo.

REM Get the root directory
set SCRIPT_DIR=%~dp0
set ROOT_DIR=%SCRIPT_DIR%..
cd /d "%ROOT_DIR%"

REM Step 1: Setup Python Environment and Install Dependencies
echo [1/5] Setting up Python environment...

REM Check if virtual environment exists at root
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
)

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Install all dependencies
echo Installing all dependencies...
pip install --upgrade pip setuptools wheel >nul 2>&1
pip install -r requirements.txt >nul 2>&1
pip install pyinstaller >nul 2>&1

echo Dependencies installed successfully
echo.

REM Step 2: Build Python Backend
echo [2/5] Building Python Backend...
cd apps\server

REM Build executable using root virtual environment
echo Building server executable with PyInstaller...
set BUILD_TYPE=SERVER
pyinstaller "%ROOT_DIR%\dipeo\build-windows.spec" --clean --noconfirm --distpath dist

if exist "dist\dipeo-server.exe" (
    echo Backend build complete
) else (
    echo ERROR: Backend build failed
    exit /b 1
)

cd "%ROOT_DIR%"
echo.

REM Step 3: Build CLI
echo [3/5] Building CLI Tool...
cd apps\cli

REM Build CLI executable using root virtual environment
echo Building CLI executable...
set BUILD_TYPE=CLI
pyinstaller "%ROOT_DIR%\dipeo\build-windows.spec" --clean --noconfirm --distpath dist --name dipeo

if exist "dist\dipeo.exe" (
    echo CLI build complete
) else (
    echo ERROR: CLI build failed
    exit /b 1
)

cd "%ROOT_DIR%"
echo.

REM Step 4: Build Frontend
echo [4/5] Building Frontend...
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

REM Step 5: Build Tauri Installer
echo [5/5] Building Windows Installer...
cd apps\desktop

REM Check if backend executable exists
if not exist "%ROOT_DIR%\apps\server\dist\dipeo-server.exe" (
    echo ERROR: Backend executable not found
    exit /b 1
)

REM Check if CLI executable exists
if not exist "%ROOT_DIR%\apps\cli\dist\dipeo.exe" (
    echo ERROR: CLI executable not found
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
    
    REM Copy installer to dist directory
    if not exist "%ROOT_DIR%\dist" mkdir "%ROOT_DIR%\dist"
    for %%f in ("src-tauri\target\release\bundle\nsis\*.exe") do (
        copy "%%f" "%ROOT_DIR%\dist\DiPeO-Setup-%VERSION%-x64.exe" >nul
        echo.
        echo Installer copied to: dist\DiPeO-Setup-%VERSION%-x64.exe
    )
    
    REM Copy CLI executable to dist
    copy "%ROOT_DIR%\apps\cli\dist\dipeo.exe" "%ROOT_DIR%\dist\" >nul
    echo CLI executable copied to: dist\dipeo.exe
    
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