# DiPeO Build Scripts

This directory contains build scripts for creating DiPeO installers on different platforms.

## Windows Build Scripts

### PowerShell Script: `build-windows.ps1`

The recommended way to build DiPeO for Windows.

#### Prerequisites:
- Windows 10 or later
- Python 3.13+
- Node.js 18+ with pnpm
- Rust (for Tauri)
- Visual Studio Build Tools (for native modules)

#### Usage:
```powershell
# Full build (backend + frontend + installer)
.\scripts\build-windows.ps1

# Build with specific version
.\scripts\build-windows.ps1 -Version "1.0.0"

# Skip certain steps
.\scripts\build-windows.ps1 -SkipBackend
.\scripts\build-windows.ps1 -SkipFrontend
.\scripts\build-windows.ps1 -SkipInstaller

# Clean build (removes previous build artifacts)
.\scripts\build-windows.ps1 -Clean
```

#### Troubleshooting PowerShell:
If you get an execution policy error, run:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Batch Script: `build-windows.bat`

Alternative for environments where PowerShell scripts are restricted.

#### Usage:
```batch
# Run from project root
scripts\build-windows.bat
```

## Build Output

The final installer will be created in:
- `apps/desktop/src-tauri/target/release/bundle/nsis/*.exe` (NSIS installer)
- `apps/desktop/src-tauri/target/release/bundle/msi/*.msi` (MSI installer)

The PowerShell script also copies the installer to `dist/DiPeO-Setup-{version}-x64.exe`.

## Icon Generation

Before building, generate icon files:
```bash
cd apps/desktop
pnpm tauri icon path/to/your/logo.png
```

This creates all required icon formats in `src-tauri/icons/`.

## Signing the Installer

For production releases, sign the installer to avoid Windows SmartScreen warnings:
```powershell
signtool sign /tr http://timestamp.sectigo.com /td sha256 /fd sha256 /a "DiPeO-Setup.exe"
```

## Troubleshooting

1. **PyInstaller fails**: Ensure all Python packages are installed in the virtual environment
2. **Tauri build fails**: Check that Rust and Visual Studio Build Tools are installed
3. **Missing icons**: Generate icons using the Tauri CLI before building
4. **Path issues**: Always run scripts from the project root directory