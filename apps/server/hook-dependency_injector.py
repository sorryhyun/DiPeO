"""PyInstaller hook for dependency_injector package.

This hook ensures all submodules of dependency_injector are properly included,
especially the errors module and C extensions which are dynamically imported.
"""

from PyInstaller.utils.hooks import (
    collect_all,
    collect_data_files,
    collect_dynamic_libs,
)

# Collect all data files, binaries, and submodules
datas, binaries, hiddenimports = collect_all("dependency_injector")

# Also collect dynamic libraries (for .pyd files on Windows)
binaries += collect_dynamic_libs("dependency_injector")

# Critical modules that must be included (based on actual package inspection)
critical_modules = [
    "dependency_injector._cwiring",
    "dependency_injector.containers",
    "dependency_injector.errors",
    "dependency_injector.ext",
    "dependency_injector.ext.aiohttp",
    "dependency_injector.ext.flask",
    "dependency_injector.ext.starlette",
    "dependency_injector.providers",
    "dependency_injector.resources",
    "dependency_injector.schema",
    "dependency_injector.wiring",
]

# Ensure all critical modules are in hiddenimports
for module in critical_modules:
    if module not in hiddenimports:
        hiddenimports.append(module)

# Also collect data files specifically
datas += collect_data_files("dependency_injector")

# Debug output
print(f"dependency_injector hook: Found {len(hiddenimports)} hidden imports")
print(f"dependency_injector hook: Found {len(binaries)} binaries")
print(f"dependency_injector hook: Found {len(datas)} data files")
print("Hidden imports:", hiddenimports)
