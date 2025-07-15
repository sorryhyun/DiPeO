# DiPeO Windows Build Script
# This script builds the complete Windows installer for DiPeO

param(
    [string]$Version = "0.1.0",
    [switch]$SkipBackend = $false,
    [switch]$SkipCLI = $false,
    [switch]$SkipFrontend = $false,
    [switch]$SkipInstaller = $false,
    [switch]$Clean = $false
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

# Colors for output
function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

Write-ColorOutput Cyan "╔════════════════════════════════════════╗"
Write-ColorOutput Cyan "║     DiPeO Windows Build Script         ║"
Write-ColorOutput Cyan "║         Version: $Version              ║"
Write-ColorOutput Cyan "╚════════════════════════════════════════╝"
Write-Output ""

# Get the root directory
$RootDir = Split-Path -Parent $PSScriptRoot
Set-Location $RootDir

# Clean previous builds if requested
if ($Clean) {
    Write-ColorOutput Yellow "🧹 Cleaning previous builds..."
    Remove-Item -Path "$RootDir\apps\server\dist" -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item -Path "$RootDir\apps\server\build" -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item -Path "$RootDir\apps\cli\dist" -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item -Path "$RootDir\apps\cli\build" -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item -Path "$RootDir\apps\web\dist" -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item -Path "$RootDir\apps\desktop\src-tauri\target" -Recurse -Force -ErrorAction SilentlyContinue
    Write-ColorOutput Green "✓ Clean complete"
    Write-Output ""
}

# Step 1: Build Python Backend
if (-not $SkipBackend) {
    Write-ColorOutput Yellow "🐍 Building Python Backend..."
    Set-Location "$RootDir\apps\server"
    
    # Check if virtual environment exists
    if (-not (Test-Path ".venv")) {
        Write-Output "Creating virtual environment..."
        python -m venv .venv
    }
    
    # Activate virtual environment
    & ".\.venv\Scripts\Activate.ps1"
    
    # Install dependencies
    Write-Output "Installing dependencies..."
    pip install --upgrade pip setuptools wheel | Out-Null
    pip install -r requirements.txt | Out-Null
    pip install pyinstaller | Out-Null
    
    # Install local packages
    Write-Output "Installing DiPeO packages..."
    pip install -e "$RootDir" | Out-Null
    pip install -e . | Out-Null
    
    # Build executable
    Write-Output "Building executable with PyInstaller..."
    pyinstaller build.spec --clean --noconfirm
    
    if (Test-Path "dist\dipeo-server.exe") {
        Write-ColorOutput Green "✓ Backend build complete"
        Write-Output "  Size: $((Get-Item dist\dipeo-server.exe).Length / 1MB)MB"
    } else {
        Write-ColorOutput Red "✗ Backend build failed"
        exit 1
    }
    
    Set-Location $RootDir
    Write-Output ""
}

# Step 2: Build CLI
if (-not $SkipCLI) {
    Write-ColorOutput Yellow "🔧 Building CLI Tool..."
    Set-Location "$RootDir\apps\cli"
    
    # Check if virtual environment exists
    if (-not (Test-Path ".venv")) {
        Write-Output "Creating virtual environment..."
        python -m venv .venv
    }
    
    # Activate virtual environment
    & ".\.venv\Scripts\Activate.ps1"
    
    # Install dependencies
    Write-Output "Installing CLI dependencies..."
    pip install --upgrade pip setuptools wheel | Out-Null
    pip install -r requirements.txt | Out-Null
    pip install pyinstaller | Out-Null
    
    # Install DiPeO core package
    pip install -e "$RootDir" | Out-Null
    pip install -e . | Out-Null
    
    # Build CLI executable
    Write-Output "Building CLI executable..."
    pyinstaller --onefile --name dipeo --distpath dist src\dipeo_cli\minimal_cli.py
    
    if (Test-Path "dist\dipeo.exe") {
        Write-ColorOutput Green "✓ CLI build complete"
        Write-Output "  Size: $((Get-Item dist\dipeo.exe).Length / 1MB)MB"
    } else {
        Write-ColorOutput Red "✗ CLI build failed"
        exit 1
    }
    
    Set-Location $RootDir
    Write-Output ""
}

# Step 3: Build Frontend
if (-not $SkipFrontend) {
    Write-ColorOutput Yellow "⚛️  Building Frontend..."
    Set-Location "$RootDir\apps\web"
    
    # Install dependencies if needed
    if (-not (Test-Path "node_modules")) {
        Write-Output "Installing frontend dependencies..."
        pnpm install
    }
    
    # Build frontend
    Write-Output "Building production bundle..."
    pnpm build
    
    if (Test-Path "dist\index.html") {
        Write-ColorOutput Green "✓ Frontend build complete"
        $fileCount = (Get-ChildItem -Path dist -Recurse -File).Count
        Write-Output "  Files: $fileCount"
    } else {
        Write-ColorOutput Red "✗ Frontend build failed"
        exit 1
    }
    
    Set-Location $RootDir
    Write-Output ""
}

# Step 4: Build Tauri Installer
if (-not $SkipInstaller) {
    Write-ColorOutput Yellow "📦 Building Windows Installer..."
    Set-Location "$RootDir\apps\desktop"
    
    # Check if backend executable exists
    $backendExe = "$RootDir\apps\server\dist\dipeo-server.exe"
    if (-not (Test-Path $backendExe)) {
        Write-ColorOutput Red "✗ Backend executable not found. Run with -SkipBackend:$false"
        exit 1
    }
    
    # Check if CLI executable exists
    $cliExe = "$RootDir\apps\cli\dist\dipeo.exe"
    if (-not (Test-Path $cliExe)) {
        Write-ColorOutput Red "✗ CLI executable not found. Run with -SkipCLI:$false"
        exit 1
    }
    
    # Install Tauri dependencies if needed
    if (-not (Test-Path "node_modules")) {
        Write-Output "Installing Tauri dependencies..."
        pnpm install
    }
    
    # Check for icons
    if (-not (Test-Path "src-tauri\icons\icon.ico")) {
        Write-ColorOutput Magenta "⚠️  Warning: Icon files not found. Using default icons."
    }
    
    # Build installer
    Write-Output "Building installer (this may take several minutes)..."
    pnpm tauri build --target x86_64-pc-windows-msvc
    
    # Find the installer
    $installerPath = Get-ChildItem -Path "src-tauri\target\release\bundle" -Recurse -Include "*.msi", "*.exe" | 
                     Where-Object { $_.Name -like "*setup*" -or $_.Name -like "*installer*" } | 
                     Select-Object -First 1
    
    if ($installerPath) {
        Write-ColorOutput Green "✓ Installer build complete"
        Write-Output "  File: $($installerPath.Name)"
        Write-Output "  Size: $([math]::Round($installerPath.Length / 1MB, 2))MB"
        Write-Output "  Path: $($installerPath.FullName)"
        
        # Copy to output directory
        $outputDir = "$RootDir\dist"
        if (-not (Test-Path $outputDir)) {
            New-Item -ItemType Directory -Path $outputDir | Out-Null
        }
        
        $outputFile = "$outputDir\DiPeO-Setup-$Version-x64.exe"
        Copy-Item -Path $installerPath.FullName -Destination $outputFile
        Write-ColorOutput Green "✓ Installer copied to: $outputFile"
        
        # Copy CLI executable to output directory
        Copy-Item -Path "$RootDir\apps\cli\dist\dipeo.exe" -Destination "$outputDir\dipeo.exe"
        Write-ColorOutput Green "✓ CLI executable copied to: $outputDir\dipeo.exe"
    } else {
        Write-ColorOutput Red "✗ Installer build failed or installer not found"
        exit 1
    }
    
    Set-Location $RootDir
    Write-Output ""
}

Write-ColorOutput Cyan "════════════════════════════════════════"
Write-ColorOutput Green "✨ Build Complete!"
Write-ColorOutput Cyan "════════════════════════════════════════"
Write-Output ""
Write-Output "Next steps:"
Write-Output "1. Test the installer on a clean Windows machine"
Write-Output "2. Sign the installer with a code signing certificate"
Write-Output "3. Upload to GitHub Releases or your distribution platform"
Write-Output ""