# DiPeO Complete Build Script
# Builds backend, frontend launcher, and installer

Write-Host "DiPeO Complete Build Process" -ForegroundColor Cyan
Write-Host "============================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Build Backend (if not already built)
if (-not (Test-Path "apps\server\dist\dipeo-server.exe")) {
    Write-Host "Step 1: Building Backend Server..." -ForegroundColor Yellow
    Push-Location apps\server
    
    # Check if PyInstaller is installed
    python -m pip show pyinstaller > $null 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Installing PyInstaller..." -ForegroundColor Yellow
        python -m pip install pyinstaller
    }
    
    # Build backend
    pyinstaller --clean dipeo-server-correct.spec
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Backend build failed!" -ForegroundColor Red
        Pop-Location
        exit 1
    }
    
    Pop-Location
    Write-Host "Backend built successfully!" -ForegroundColor Green
} else {
    Write-Host "Step 1: Backend already built, skipping..." -ForegroundColor Gray
}

# Step 2: Build Frontend Files
Write-Host ""
Write-Host "Step 2: Building Frontend..." -ForegroundColor Yellow
Push-Location apps\web

# Use the build script
& .\build-frontend.ps1

if ($LASTEXITCODE -ne 0) {
    Write-Host "Frontend build failed!" -ForegroundColor Red
    Pop-Location
    exit 1
}

Pop-Location
Write-Host "Frontend built successfully!" -ForegroundColor Green

# Step 3: Build Installer
Write-Host ""
Write-Host "Step 3: Building Installer..." -ForegroundColor Yellow

# Check if NSIS is installed
$nsisPath = "${env:ProgramFiles(x86)}\NSIS\makensis.exe"
if (-not (Test-Path $nsisPath)) {
    $nsisPath = "${env:ProgramFiles}\NSIS\makensis.exe"
}

if (-not (Test-Path $nsisPath)) {
    Write-Host "NSIS not found! Please install NSIS from https://nsis.sourceforge.io/" -ForegroundColor Red
    Write-Host "After installing, run this script again." -ForegroundColor Yellow
    exit 1
}

# Build installer
& $nsisPath scripts/minimal-installer.nsi

if ($LASTEXITCODE -eq 0) {
    Write-Host "Installer built successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Build Summary:" -ForegroundColor Cyan
    Write-Host "- Backend: apps\server\dist\dipeo-server.exe" -ForegroundColor White
    Write-Host "- Frontend: apps\web\dist\dipeo-frontend.exe" -ForegroundColor White
    Write-Host "- Installer: DiPeO-Setup-Minimal.exe" -ForegroundColor White
    Write-Host ""
    Write-Host "You can now:" -ForegroundColor Yellow
    Write-Host "1. Run 'launch-dipeo.bat' to start both servers" -ForegroundColor White
    Write-Host "2. Run 'DiPeO-Setup-Minimal.exe' to install DiPeO" -ForegroundColor White
} else {
    Write-Host "Installer build failed!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "All builds completed successfully!" -ForegroundColor Green