# DiPeO Windows Installation Guide

DiPeO now supports Windows through a native desktop application built with Tauri. This guide covers installation, building from source, and troubleshooting.

## Installing DiPeO on Windows

### System Requirements
- Windows 10 version 1809 or later (64-bit)
- 4GB RAM minimum (8GB recommended)
- 200MB free disk space
- Internet connection (for LLM API calls)

### Installation Methods

#### Method 1: One-Click Installer (Recommended)
1. Download the latest `DiPeO-Setup-x.x.x-x64.exe` from [GitHub Releases](https://github.com/sorryhyun/DiPeO/releases)
2. Double-click the installer
3. If you see a Windows SmartScreen warning, click "More info" → "Run anyway"
4. Follow the installation wizard
5. Launch DiPeO from the Start Menu or Desktop shortcut

#### Method 2: MSI Installer (For Enterprises)
1. Download the latest `DiPeO-x.x.x-x64.msi` from [GitHub Releases](https://github.com/sorryhyun/DiPeO/releases)
2. Install via command line: `msiexec /i DiPeO-x.x.x-x64.msi`
3. Or double-click for GUI installation

## Building from Source

### Prerequisites
- Windows 10 or later
- [Python 3.13+](https://www.python.org/downloads/)
- [Node.js 22+](https://nodejs.org/)
- [pnpm](https://pnpm.io/installation)
- [Rust](https://rustup.rs/)
- [Visual Studio Build Tools](https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022)

### Build Steps

1. **Clone the repository:**
   ```powershell
   git clone https://github.com/sorryhyun/DiPeO.git
   cd DiPeO
   ```

2. **Install dependencies:**
   ```powershell
   # Install Python package (unified umbrella package)
   pip install -e dipeo
   
   # Install frontend dependencies
   cd apps/web
   pnpm install
   cd ../..
   ```

3. **Generate icons (first time only):**
   ```powershell
   cd apps/desktop
   pnpm install
   pnpm tauri icon ../assets/logo.png  # Use your logo file
   cd ../..
   ```

4. **Build the installer:**
   ```powershell
   # Using PowerShell script (recommended)
   .\scripts\build-windows.ps1
   
   # Or using batch file
   scripts\build-windows.bat
   ```

5. **Find the installer:**
   - NSIS installer: `apps/desktop/src-tauri/target/release/bundle/nsis/*.exe`
   - MSI installer: `apps/desktop/src-tauri/target/release/bundle/msi/*.msi`

### Development Mode

For development, you can run DiPeO without building an installer:

1. **Start the backend:**
   ```powershell
   cd apps/server
   python main.py
   ```

2. **Start the frontend (in a new terminal):**
   ```powershell
   cd apps/web
   pnpm dev
   ```

3. **Or use Tauri dev mode (recommended):**
   ```powershell
   cd apps/desktop
   pnpm tauri dev
   ```

## Configuration

### API Keys
DiPeO stores API keys in `%LOCALAPPDATA%\DiPeO\files\apikeys.json`. You can also set them via environment variables:
- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `GEMINI_API_KEY`

### File Storage
DiPeO stores files in the following locations:
- **Windows:** `%LOCALAPPDATA%\DiPeO\files\`
  - `diagrams/` - Saved diagrams
  - `results/` - Execution results
  - `prompts/` - Prompt templates
  - `uploads/` - Uploaded files

## Troubleshooting

### Common Issues

#### "Windows protected your PC" warning
This happens because the installer isn't code-signed. To proceed:
1. Click "More info"
2. Click "Run anyway"

For production deployments, consider getting a code signing certificate.

#### Backend fails to start
1. Check if port 8000 is already in use
2. Ensure Windows Defender isn't blocking the executable
3. Check the logs in `%LOCALAPPDATA%\DiPeO\logs\`

#### Missing Visual C++ Redistributables
If you get DLL errors, install the [Visual C++ Redistributables](https://aka.ms/vs/17/release/vc_redist.x64.exe).

#### PyInstaller build fails
Common solutions:
- Use a clean virtual environment
- Add excluded modules to the spec file
- Check for hidden imports
- Disable antivirus temporarily during build

### Debug Mode

To run DiPeO with debug logging:
1. Set environment variable: `set DIPEO_DEBUG=1`
2. Launch DiPeO
3. Check logs in `%LOCALAPPDATA%\DiPeO\logs\`

## Uninstalling

### Via Control Panel
1. Open Control Panel → Programs and Features
2. Find "DiPeO" in the list
3. Click Uninstall

### Via Command Line
```powershell
# For MSI installations
msiexec /x {PRODUCT-GUID}

# Or use the original installer
DiPeO-Setup-x.x.x-x64.exe /uninstall
```

## Security Considerations

- DiPeO requires network access for LLM API calls
- API keys are stored locally in your user profile
- The application doesn't require administrator privileges
- Windows Defender may scan the executable on first run

## Support

For Windows-specific issues:
1. Check the [GitHub Issues](https://github.com/sorryhyun/DiPeO/issues)
2. Include Windows version and error logs
3. Try running in debug mode first

## Future Improvements

Planned enhancements for Windows support:
- [ ] Code signing for trusted installation
- [ ] Windows Store distribution
- [ ] Automatic updates
- [ ] Windows-native file associations
- [ ] System tray integration
- [ ] Windows Hello authentication for API keys