# DiPeO Windows Environment Test Script
# This script checks if all prerequisites are installed for building DiPeO on Windows

$ErrorActionPreference = "Continue"

Write-Host "================================" -ForegroundColor Cyan
Write-Host " DiPeO Build Environment Check  " -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

$issues = 0

# Check Python
Write-Host "Checking Python..." -NoNewline
try {
    $pythonVersion = python --version 2>&1
    if ($pythonVersion -match "Python (\d+)\.(\d+)") {
        $major = [int]$matches[1]
        $minor = [int]$matches[2]
        if ($major -ge 3 -and $minor -ge 11) {
            Write-Host " OK ($pythonVersion)" -ForegroundColor Green
        } else {
            Write-Host " WARNING: Python 3.11+ recommended (found $pythonVersion)" -ForegroundColor Yellow
            $issues++
        }
    }
} catch {
    Write-Host " MISSING" -ForegroundColor Red
    Write-Host "  Install Python 3.11+ from https://python.org" -ForegroundColor Gray
    $issues++
}

# Check Node.js
Write-Host "Checking Node.js..." -NoNewline
try {
    $nodeVersion = node --version 2>&1
    if ($nodeVersion -match "v(\d+)") {
        $major = [int]$matches[1]
        if ($major -ge 18) {
            Write-Host " OK ($nodeVersion)" -ForegroundColor Green
        } else {
            Write-Host " WARNING: Node.js 18+ recommended (found $nodeVersion)" -ForegroundColor Yellow
            $issues++
        }
    }
} catch {
    Write-Host " MISSING" -ForegroundColor Red
    Write-Host "  Install Node.js from https://nodejs.org" -ForegroundColor Gray
    $issues++
}

# Check pnpm
Write-Host "Checking pnpm..." -NoNewline
try {
    $pnpmVersion = pnpm --version 2>&1
    Write-Host " OK (v$pnpmVersion)" -ForegroundColor Green
} catch {
    Write-Host " MISSING" -ForegroundColor Red
    Write-Host "  Install with: npm install -g pnpm" -ForegroundColor Gray
    $issues++
}

# Check Rust
Write-Host "Checking Rust..." -NoNewline
try {
    $rustVersion = rustc --version 2>&1
    if ($rustVersion -match "rustc") {
        Write-Host " OK ($rustVersion)" -ForegroundColor Green
    }
} catch {
    Write-Host " MISSING (required for Tauri desktop app)" -ForegroundColor Yellow
    Write-Host "  Install from https://rustup.rs" -ForegroundColor Gray
    $issues++
}

# Check Visual Studio Build Tools
Write-Host "Checking VS Build Tools..." -NoNewline
$vsWhere = "${env:ProgramFiles(x86)}\Microsoft Visual Studio\Installer\vswhere.exe"
if (Test-Path $vsWhere) {
    $vsInstalls = & $vsWhere -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
    if ($vsInstalls) {
        Write-Host " OK" -ForegroundColor Green
    } else {
        Write-Host " MISSING C++ tools" -ForegroundColor Yellow
        Write-Host "  Install Visual Studio Build Tools with C++ workload" -ForegroundColor Gray
        $issues++
    }
} else {
    Write-Host " MISSING" -ForegroundColor Yellow
    Write-Host "  Install from https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022" -ForegroundColor Gray
    $issues++
}

# Check make (optional but recommended)
Write-Host "Checking make..." -NoNewline
try {
    $makeVersion = make --version 2>&1
    Write-Host " OK" -ForegroundColor Green
} catch {
    Write-Host " MISSING (optional)" -ForegroundColor Yellow
    Write-Host "  Install with: winget install GnuWin32.Make" -ForegroundColor Gray
}

Write-Host ""

# Check project structure
Write-Host "Checking project structure..." -ForegroundColor Cyan
$requiredDirs = @(
    "apps/server",
    "apps/cli", 
    "apps/web",
    "apps/desktop",
    "dipeo",
    "files/diagrams"
)

foreach ($dir in $requiredDirs) {
    Write-Host "  $dir..." -NoNewline
    if (Test-Path $dir) {
        Write-Host " OK" -ForegroundColor Green
    } else {
        Write-Host " MISSING" -ForegroundColor Red
        $issues++
    }
}

Write-Host ""
Write-Host "================================" -ForegroundColor Cyan

if ($issues -eq 0) {
    Write-Host "✓ Environment ready for building!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "1. Run: .\scripts\build-windows.ps1" -ForegroundColor White
    Write-Host "2. Or for a clean build: .\scripts\build-windows.ps1 -Clean" -ForegroundColor White
} else {
    Write-Host "⚠ Found $issues issue(s) - please fix before building" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "After fixing issues, run this test again." -ForegroundColor White
}