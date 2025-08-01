# -*- mode: python ; coding: utf-8 -*-
"""
DiPeO Windows Build Spec
This spec file can be used to build both server and CLI executables.
Usage:
  - For server: pyinstaller dipeo/build-windows.spec --name dipeo-server --distpath apps/server/dist
  - For CLI: pyinstaller dipeo/build-windows.spec --name dipeo --distpath apps/cli/dist
"""
import sys
import os
from pathlib import Path

# Determine build type based on spec invocation path
SPEC_PATH = Path(SPECPATH)
ROOT_DIR = SPEC_PATH.parent.parent if SPEC_PATH.parent.name == 'dipeo' else SPEC_PATH.parent
DIPEO_DIR = ROOT_DIR / "dipeo"

# Detect if we're building server or CLI based on the current working directory
IS_SERVER_BUILD = 'server' in str(Path.cwd()) or 'SERVER' in os.environ.get('BUILD_TYPE', '')
IS_CLI_BUILD = 'cli' in str(Path.cwd()) or 'CLI' in os.environ.get('BUILD_TYPE', '')

# Add dipeo directory to Python path for imports
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(DIPEO_DIR))

# Add app-specific paths
if IS_SERVER_BUILD:
    sys.path.insert(0, str(ROOT_DIR / "apps" / "server"))
elif IS_CLI_BUILD:
    sys.path.insert(0, str(ROOT_DIR / "apps" / "cli"))

# Windows-specific workarounds
if sys.platform == 'win32':
    # Ensure proper encoding
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    # Use legacy stdio on Windows
    os.environ['PYTHONLEGACYWINDOWSSTDIO'] = '1'

block_cipher = None

# Base hidden imports for both server and CLI
base_hiddenimports = [
    # Core DiPeO modules
    'dipeo',
    'dipeo.core',
    'dipeo.domain',
    'dipeo.diagram',
    'dipeo.application',
    'dipeo.infra',
    'dipeo.application.bootstrap',
    'dipeo.models',
    'dipeo.utils',
    
    # Common dependencies
    'yaml',
    'pyyaml',
    'structlog',
    'pydantic',
    'pydantic.main',
    'pydantic_core',
    'typing_extensions',
    'dependency_injector',
    'tenacity',
]

# Server-specific hidden imports
server_hiddenimports = [
    # Hypercorn and ASGI
    'hypercorn.asyncio',
    'hypercorn.config',
    'hypercorn.middleware',
    'hypercorn.protocol',
    'hypercorn.protocol.h11',
    'hypercorn.protocol.h2',
    'hypercorn.protocol.http',
    'hypercorn.protocol.ws',
    'hypercorn.typing',
    'hypercorn.utils',
    
    # Strawberry GraphQL
    'strawberry',
    'strawberry.asgi',
    'strawberry.fastapi',
    'strawberry.subscriptions',
    'strawberry.types',
    'strawberry.schema',
    'strawberry.field',
    'strawberry.dataloader',
    'strawberry.extensions',
    'strawberry.http',
    'strawberry.file_uploads',
    
    # FastAPI and dependencies
    'fastapi',
    'fastapi.middleware',
    'fastapi.middleware.cors',
    'fastapi.staticfiles',
    
    # Async libraries
    'aiofiles',
    'aiohttp',
    'anyio',
    'sniffio',
    
    # LLM clients
    'anthropic',
    'openai',
    'google.genai',
    
    # Other server dependencies
    'python_multipart',
    'multipart',
    'notion_client',
    'gql',
    'graphql',
    'prometheus_client',
    'dotenv',
    
    # Server-specific DiPeO modules
    'dipeo_server',
    'dipeo_server.api.graphql.queries',
    'dipeo_server.api.graphql.mutations',
    'dipeo_server.api.graphql.mutations.api_key_mutation',
    'dipeo_server.api.graphql.mutations.diagram_mutation',
    'dipeo_server.api.graphql.mutations.execution_mutation',
    'dipeo_server.api.graphql.mutations.graph_element_mutations',
    'dipeo_server.api.graphql.mutations.node_mutation',
    'dipeo_server.api.graphql.mutations.person_mutation',
    'dipeo_server.api.graphql.mutations.upload_mutation',
    'dipeo_server.api.graphql.subscriptions',
    'dipeo_server.api.graphql.resolvers',
    'dipeo_server.api.graphql.resolvers.diagram',
    'dipeo_server.api.graphql.resolvers.execution',
    'dipeo_server.api.graphql.resolvers.person',
]

# CLI-specific hidden imports
cli_hiddenimports = [
    'click',
    'rich',
    'rich.console',
    'rich.progress',
    'rich.table',
    'rich.syntax',
    'prompt_toolkit',
    'dipeo_cli',
    'dipeo_cli.minimal_cli',
]

# Determine which hidden imports to use
if IS_SERVER_BUILD:
    hiddenimports = base_hiddenimports + server_hiddenimports
    entry_script = str(ROOT_DIR / 'apps' / 'server' / 'main_bundled.py')
elif IS_CLI_BUILD:
    hiddenimports = base_hiddenimports + cli_hiddenimports
    entry_script = str(ROOT_DIR / 'apps' / 'cli' / 'src' / 'dipeo_cli' / 'minimal_cli.py')
else:
    # Default to server if not specified
    hiddenimports = base_hiddenimports + server_hiddenimports
    entry_script = str(ROOT_DIR / 'apps' / 'server' / 'main_bundled.py')

# Collect all data files
datas = [
    # Include dipeo package and its subpackages
    (str(DIPEO_DIR / 'core'), 'dipeo/core'),
    (str(DIPEO_DIR / 'domain'), 'dipeo/domain'),
    (str(DIPEO_DIR / 'diagram'), 'dipeo/diagram'),
    (str(DIPEO_DIR / 'application'), 'dipeo/application'),
    (str(DIPEO_DIR / 'infra'), 'dipeo/infra'),
    # Container moved to application.bootstrap
    (str(DIPEO_DIR / 'models'), 'dipeo/models'),
    (str(DIPEO_DIR / 'utils'), 'dipeo/utils'),
    
    # Include __init__.py files
    (str(DIPEO_DIR / '__init__.py'), 'dipeo/'),
]

# Add server-specific data files
if IS_SERVER_BUILD:
    server_src = ROOT_DIR / 'apps' / 'server' / 'src'
    if server_src.exists():
        datas.append((str(server_src), 'src'))
    
    # Include schema file if it exists
    schema_file = ROOT_DIR / 'apps' / 'server' / 'schema.graphql'
    if schema_file.exists():
        datas.append((str(schema_file), '.'))

# Add CLI-specific data files
if IS_CLI_BUILD:
    cli_src = ROOT_DIR / 'apps' / 'cli' / 'src'
    if cli_src.exists():
        datas.append((str(cli_src), 'src'))

# Remove None values from datas
datas = [d for d in datas if d is not None]

# Create empty hooks directory to prevent hook discovery issues
hooks_dir = ROOT_DIR / '.pyinstaller_hooks'
if not hooks_dir.exists():
    hooks_dir.mkdir(parents=True, exist_ok=True)

a = Analysis(
    [entry_script],
    pathex=[
        str(ROOT_DIR),
        str(DIPEO_DIR),
        str(DIPEO_DIR / 'core'),
        str(DIPEO_DIR / 'domain'),
        str(DIPEO_DIR / 'diagram'),
        str(DIPEO_DIR / 'application'),
        str(DIPEO_DIR / 'infra'),
        str(DIPEO_DIR / 'application' / 'bootstrap'),
    ],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[str(hooks_dir)],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'PIL',
        'IPython',
        'jupyter',
        'notebook',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher,
)

# Determine executable name
if IS_CLI_BUILD:
    exe_name = 'dipeo'
else:
    exe_name = 'dipeo-server'

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name=exe_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Always console for both server and CLI
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(ROOT_DIR / 'apps' / 'desktop' / 'src-tauri' / 'icons' / 'icon.ico') if (ROOT_DIR / 'apps' / 'desktop' / 'src-tauri' / 'icons' / 'icon.ico').exists() else None,
)