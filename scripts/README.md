# DiPeO Build Scripts

This directory contains build scripts for creating DiPeO installers on different platforms.

## Windows Build Scripts

### PowerShell Script: `build-windows.ps1`

The recommended way to build DiPeO for Windows.

#### Testing Prerequisites:
Before building, test your environment:
```powershell
.\scripts\test-windows-env.ps1
```

#### Prerequisites:
- Windows 10 or later
- Python 3.13+
- Node.js 22+ with pnpm
- Rust (for Tauri)
- Visual Studio Build Tools (for native modules)

#### Usage:
```powershell
# Full build (backend + CLI + frontend + installer)
.\scripts\build-windows.ps1

# Build with specific version
.\scripts\build-windows.ps1 -Version "1.0.0"

# Skip certain steps
.\scripts\build-windows.ps1 -SkipBackend
.\scripts\build-windows.ps1 -SkipCLI
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

# Build with specific version
scripts\build-windows.bat 1.0.0
```

## Build Output

The build process creates the following:
- **Server executable**: `apps/server/dist/dipeo-server.exe`
- **CLI executable**: `apps/cli/dist/dipeo.exe`
- **Web frontend**: `apps/web/dist/`
- **Desktop installer**: `apps/desktop/src-tauri/target/release/bundle/nsis/*.exe` (NSIS installer)
- **Desktop installer**: `apps/desktop/src-tauri/target/release/bundle/msi/*.msi` (MSI installer)

Both build scripts copy the final artifacts to the `dist/` directory:
- `dist/DiPeO-Setup-{version}-x64.exe` - The installer
- `dist/dipeo.exe` - The standalone CLI tool

## Icon Generation (Optional)

If you want to customize the application icons:

```bash
cd apps/desktop
pnpm tauri icon path/to/your/logo.png
```

This creates all required icon formats in `src-tauri/icons/`. The build will use default icons if custom ones are not provided.

## Signing the Installer

For production releases, sign the installer to avoid Windows SmartScreen warnings:
```powershell
signtool sign /tr http://timestamp.sectigo.com /td sha256 /fd sha256 /a "DiPeO-Setup.exe"
```

## Troubleshooting

1. **PyInstaller fails**: Ensure all Python packages are installed in the virtual environment
2. **Tauri build fails**: Check that Rust and Visual Studio Build Tools are installed
3. **Path issues**: Always run scripts from the project root directory
4. **CLI build fails**: Make sure the DiPeO core package is installed with `pip install -e .` from the project root
5. **Missing dependencies**: Run `make install` from the project root before building