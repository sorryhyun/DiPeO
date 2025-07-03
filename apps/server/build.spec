# -*- mode: python ; coding: utf-8 -*-
import sys
import os
from pathlib import Path

# Get the root directory (2 levels up from this spec file)
ROOT_DIR = Path(SPECPATH).parent.parent
PACKAGES_DIR = ROOT_DIR / "packages" / "python"

# Add packages directory to Python path for imports
sys.path.insert(0, str(PACKAGES_DIR))

block_cipher = None

# Define all the hidden imports
hiddenimports = [
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
    'pydantic',
    'pydantic.main',
    'pydantic.fields',
    'pydantic.typing',
    'pydantic_core',
    
    # Async libraries
    'aiofiles',
    'aiohttp',
    'anyio',
    'sniffio',
    
    # LLM clients
    'anthropic',
    'openai',
    'google.genai',
    
    # Other dependencies
    'python_multipart',
    'multipart',
    'notion_client',
    'gql',
    'graphql',
    'prometheus_client',
    'structlog',
    'tenacity',
    'yaml',
    'dotenv',
    
    # DiPeO modules - explicit imports
    'dipeo_core',
    'dipeo_domain',
    'dipeo_diagram',
    'dipeo_application',
    'dipeo_infra',
    'dipeo_container',
    
    # Dependency injector wired modules
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
    'dipeo_domain.domains.execution.services',
]

# Collect all data files
datas = [
    # Include the entire src directory
    ('src', 'src'),
    
    # Include Python packages
    (str(PACKAGES_DIR / 'dipeo_core'), 'dipeo_core'),
    (str(PACKAGES_DIR / 'dipeo_domain'), 'dipeo_domain'),
    (str(PACKAGES_DIR / 'dipeo_diagram'), 'dipeo_diagram'),
    (str(PACKAGES_DIR / 'dipeo_application'), 'dipeo_application'),
    (str(PACKAGES_DIR / 'dipeo_infra'), 'dipeo_infra'),
    (str(PACKAGES_DIR / 'dipeo_container'), 'dipeo_container'),
    
    # Include schema file if it exists
    ('schema.graphql', '.') if os.path.exists('schema.graphql') else None,
]

# Remove None values from datas
datas = [d for d in datas if d is not None]

a = Analysis(
    ['main_bundled.py'],
    pathex=[
        str(Path(SPECPATH)),
        str(PACKAGES_DIR),
        str(PACKAGES_DIR / 'dipeo_core' / 'src'),
        str(PACKAGES_DIR / 'dipeo_domain' / 'src'),
        str(PACKAGES_DIR / 'dipeo_diagram' / 'src'),
        str(PACKAGES_DIR / 'dipeo_application' / 'src'),
        str(PACKAGES_DIR / 'dipeo_infra' / 'src'),
        str(PACKAGES_DIR / 'dipeo_container' / 'src'),
    ],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
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
    console=True,  # Set to False for production to hide console
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='../../apps/desktop/src-tauri/icons/icon.ico' if os.path.exists('../../apps/desktop/src-tauri/icons/icon.ico') else None,
)