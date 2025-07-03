# Icon Files for DiPeO

This directory should contain the following icon files for the Windows installer:

## Required Files:
- `icon.ico` - Windows icon file (contains multiple resolutions)
- `icon.png` - Base PNG icon for tray
- `32x32.png` - 32x32 pixel icon
- `128x128.png` - 128x128 pixel icon
- `128x128@2x.png` - 256x256 pixel icon (2x retina)
- `icon.icns` - macOS icon (optional for Windows build)

## Generating Icons:
You can use tools like:
- [Tauri Icon Generator](https://tauri.app/v1/guides/features/icons/)
- ImageMagick to convert from a high-res source
- Online converters for ICO files

## Temporary Placeholder:
For now, these files are not included but are required for building the Windows installer.
You can use the Tauri CLI to generate them:
```bash
pnpm tauri icon path/to/source-icon.png
```