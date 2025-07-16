# -*- mode: python ; coding: utf-8 -*-
import sys
import os
from pathlib import Path

# Get the correct paths - SPECPATH is the directory where spec file is located
# We need to build paths correctly from here
SPEC_DIR = os.path.abspath(SPECPATH)  # This is apps/server
APPS_DIR = os.path.dirname(SPEC_DIR)  # This is apps
ROOT_DIR = os.path.dirname(APPS_DIR)  # This is DiPeO

print(f"SPEC_DIR (where spec file is): {SPEC_DIR}")
print(f"APPS_DIR: {APPS_DIR}")
print(f"ROOT_DIR: {ROOT_DIR}")
print(f"Project name: {os.path.basename(ROOT_DIR)}")

# Verify we're in the right place
if os.path.basename(ROOT_DIR) != "DiPeO":
    print(f"ERROR: Expected project root to be 'DiPeO' but got '{os.path.basename(ROOT_DIR)}'")
    print("Check your paths!")
    # Try alternative approach
    current_dir = Path(SPEC_DIR)
    while current_dir.parent != current_dir:
        if current_dir.name == "DiPeO":
            ROOT_DIR = str(current_dir)
            print(f"Found correct ROOT_DIR: {ROOT_DIR}")
            break
        current_dir = current_dir.parent

# Recalculate paths
SERVER_DIR = os.path.join(ROOT_DIR, "apps", "server")
DIPEO_DIR = os.path.join(ROOT_DIR, "dipeo")

print(f"\nFinal paths:")
print(f"ROOT_DIR: {ROOT_DIR}")
print(f"SERVER_DIR: {SERVER_DIR}")
print(f"DIPEO_DIR: {DIPEO_DIR}")

# Add to Python path
sys.path.insert(0, ROOT_DIR)
sys.path.insert(0, SERVER_DIR)

# Only include essential data files
datas = []

# Add schema.graphql
schema_file = os.path.join(SERVER_DIR, 'schema.graphql')
if os.path.exists(schema_file):
    datas.append((schema_file, '.'))
    print(f"Adding schema file: {schema_file}")
else:
    print(f"WARNING: schema.graphql not found at {schema_file}")

# Add config.py if exists
config_file = os.path.join(SERVER_DIR, 'config.py')
if os.path.exists(config_file):
    datas.append((config_file, '.'))

# Add dipeo package
if os.path.exists(DIPEO_DIR) and os.path.isdir(DIPEO_DIR):
    datas.append((DIPEO_DIR, 'dipeo'))
    print(f"Adding dipeo package from: {DIPEO_DIR}")
else:
    print(f"ERROR: dipeo package not found at {DIPEO_DIR}")
    raise FileNotFoundError(f"dipeo package not found at {DIPEO_DIR}")

# Create essential directories
for dir_name in ['files', 'files/diagrams', 'files/results', 'files/conversation_logs', 'files/uploads', 'files/prompts']:
    dir_path = os.path.join(SERVER_DIR, dir_name)
    if not os.path.exists(dir_path):
        os.makedirs(dir_path, exist_ok=True)

# Main bundled entry point should be in server directory
main_bundled_py = os.path.join(SERVER_DIR, 'main_bundled.py')
if not os.path.exists(main_bundled_py):
    print(f"WARNING: main_bundled.py not found at {main_bundled_py}, falling back to main.py")
    main_py = os.path.join(SERVER_DIR, 'main.py')
    if not os.path.exists(main_py):
        print(f"ERROR: main.py not found at {main_py}")
        raise FileNotFoundError(f"main.py not found at {main_py}")
    entry_point = main_py
else:
    entry_point = main_bundled_py
    print(f"Using main_bundled.py as entry point: {main_bundled_py}")

a = Analysis(
    [entry_point],  # Use the determined entry point
    pathex=[SERVER_DIR, ROOT_DIR],
    binaries=[],
    datas=datas,
    hiddenimports=[
        # Core imports
        'dipeo',
        'dipeo.domain',
        'dipeo.application',
        'dipeo.infra',
        'dipeo.models',
        'dipeo_server',
        'dipeo_server.api',
        'dipeo_server.api.graphql',
        'dipeo_server.application',
        'dipeo_server.infra',
        # FastAPI and dependencies
        'fastapi',
        'starlette',
        'starlette.applications',
        'starlette.middleware',
        'starlette.middleware.cors',
        'starlette.responses',
        'starlette.routing',
        'starlette.staticfiles',
        'pydantic',
        'pydantic.main',
        'pydantic.fields',
        'uvicorn',
        'uvicorn.config',
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.http.h11_impl',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.protocols.websockets.websockets_impl',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'uvicorn.workers',
        # GraphQL
        'strawberry',
        'strawberry.fastapi',
        'strawberry.schema',
        'strawberry.types',
        'graphql',
        'graphql.execution',
        'graphql.language',
        'graphql.type',
        'graphql.utilities',
        'graphql.validation',
        # Other essentials
        'aiofiles',
        'websockets',
        'websockets.legacy',
        'websockets.legacy.server',
        'python-multipart',
        'multipart',
        'structlog',
        'dependency_injector',
        'dependency_injector.containers',
        'dependency_injector.providers',
        'dependency_injector.wiring',
        'dependency_injector.errors',
        'dependency_injector.catalog',
        'dependency_injector.catalogs',
        'dependency_injector.factories',
        'dependency_injector.resources',
        'dependency_injector.injections',
        'dependency_injector._cwiring',
        'dotenv',
        'python-dotenv',
        'yaml',
        'click',
        'h11',
        'httptools',
        'watchfiles',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy', 
        'pandas',
        'scipy',
        'PIL',
        'tkinter',
        'PyQt5',
        'PySide2',
        'notebook',
        'jupyter',
        'IPython',
        'pytest',
        'pre_commit',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# Icon path
icon_path = os.path.join(ROOT_DIR, 'apps', 'desktop', 'src-tauri', 'icons', 'icon.ico')
if not os.path.exists(icon_path):
    icon_path = None
    print("Icon not found, building without icon")
else:
    print(f"Using icon: {icon_path}")

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='dipeo-server',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_path,
)