# Build script for DiPeO Frontend Server

Write-Host "Building DiPeO Frontend" -ForegroundColor Green
Write-Host "======================" -ForegroundColor Green

# Step 1: Build the React frontend
Write-Host "`nStep 1: Building React frontend..." -ForegroundColor Yellow
pnpm build

if ($LASTEXITCODE -ne 0) {
    Write-Host "React build failed!" -ForegroundColor Red
    exit 1
}

Write-Host "React build successful!" -ForegroundColor Green

# Step 2: Check if PyInstaller is installed
python -m pip show pyinstaller > $null 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "`nPyInstaller not found. Installing..." -ForegroundColor Yellow
    python -m pip install pyinstaller
}

# Step 3: Build the frontend server executable
Write-Host "`nStep 2: Building frontend server executable..." -ForegroundColor Yellow
pyinstaller --clean frontend_server.spec

if ($LASTEXITCODE -eq 0) {
    Write-Host "`nBuild successful!" -ForegroundColor Green
    Write-Host "Frontend server created at: dist\dipeo-frontend.exe" -ForegroundColor Cyan
    Write-Host "Frontend static files at: dist\" -ForegroundColor Cyan
} else {
    Write-Host "`nBuild failed!" -ForegroundColor Red
    exit 1
}

Write-Host "`nDone!" -ForegroundColor Green
