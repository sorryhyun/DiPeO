# DiPeO Tauri Build Script
# Builds backend with PyInstaller and desktop app with Tauri

Write-Host "DiPeO Tauri Build Process" -ForegroundColor Cyan
Write-Host "=========================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Build Backend with PyInstaller (still needed for Python server)
Write-Host "Step 1: Building Backend Server with PyInstaller..." -ForegroundColor Yellow
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

# Step 2: Build Frontend Static Files
Write-Host ""
Write-Host "Step 2: Building Frontend Static Files..." -ForegroundColor Yellow
Push-Location apps\web

pnpm install --frozen-lockfile
pnpm run build

if ($LASTEXITCODE -ne 0) {
    Write-Host "Frontend build failed!" -ForegroundColor Red
    Pop-Location
    exit 1
}

Pop-Location
Write-Host "Frontend built successfully!" -ForegroundColor Green

# Step 3: Prepare Tauri configuration with backend resource
Write-Host ""
Write-Host "Step 3: Preparing Resources for Tauri..." -ForegroundColor Yellow

# Read the current tauri.conf.json
$tauriConfig = Get-Content "apps\desktop\src-tauri\tauri.conf.json" -Raw | ConvertFrom-Json

# Add the backend executable to resources
if (-not $tauriConfig.bundle.resources."resources/dipeo-server.exe") {
    # Add the backend resource path
    $tauriConfig.bundle.resources | Add-Member -NotePropertyName "resources/dipeo-server.exe" -NotePropertyValue "./dipeo-server.exe" -Force
}

# Write the updated config back
$tauriConfig | ConvertTo-Json -Depth 10 | Set-Content "apps\desktop\src-tauri\tauri.conf.json"

# Create resources directory if it doesn't exist
$resourcesDir = "apps\desktop\src-tauri\resources"
if (!(Test-Path $resourcesDir)) {
    New-Item -ItemType Directory -Force -Path $resourcesDir
}

# Copy backend executable
Copy-Item -Path "apps\server\dist\dipeo-server.exe" -Destination "$resourcesDir\dipeo-server.exe" -Force
Write-Host "Backend executable copied to Tauri resources" -ForegroundColor Green

# Step 4: Build Tauri Desktop App
Write-Host ""
Write-Host "Step 4: Building Tauri Desktop App..." -ForegroundColor Yellow
Push-Location apps\desktop

# Install Rust dependencies
cargo build --manifest-path src-tauri/Cargo.toml --release

if ($LASTEXITCODE -ne 0) {
    Write-Host "Cargo build failed!" -ForegroundColor Red
    Pop-Location
    exit 1
}

# Build Tauri app (this creates the installer)
pnpm tauri build

if ($LASTEXITCODE -ne 0) {
    Write-Host "Tauri build failed!" -ForegroundColor Red
    Pop-Location
    exit 1
}

Pop-Location
Write-Host "Tauri app built successfully!" -ForegroundColor Green

# Step 5: Summary
Write-Host ""
Write-Host "Build Summary:" -ForegroundColor Cyan
Write-Host "- Backend: apps\server\dist\dipeo-server.exe" -ForegroundColor White
Write-Host "- Frontend: apps\web\dist\" -ForegroundColor White
Write-Host "- Desktop App: apps\desktop\src-tauri\target\release\dipeo-desktop.exe" -ForegroundColor White
Write-Host "- Installer: apps\desktop\src-tauri\target\release\bundle\nsis\*.exe" -ForegroundColor White

Write-Host ""
Write-Host "All builds completed successfully!" -ForegroundColor Green