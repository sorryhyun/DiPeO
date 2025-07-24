"""
Simple path constants for codegen system.
All paths are relative to the project root.
"""

from pathlib import Path

# Get the project root (codegen is at files/codegen/)
CODEGEN_DIR = Path(__file__).parent
PROJECT_ROOT = CODEGEN_DIR.parent.parent

# Source directories
SPECS_DIR = CODEGEN_DIR / "specifications/nodes"
TEMPLATES_DIR = CODEGEN_DIR / "templates"
SCHEMAS_DIR = CODEGEN_DIR / "schemas"

# Temporary directory for intermediate files
TEMP_DIR = PROJECT_ROOT / ".temp/codegen"

# Output directories (relative to project root)
MODELS_DIR = PROJECT_ROOT / "dipeo/diagram_generated/models/nodes"
STATIC_NODES_DIR = PROJECT_ROOT / "dipeo/core/static/generated"
GRAPHQL_DIR = PROJECT_ROOT / "apps/server/src/dipeo_server/api/graphql/schema/nodes"
FRONTEND_CONFIGS_DIR = PROJECT_ROOT / "apps/web/src/__generated__"
NODE_CONFIGS_DIR = FRONTEND_CONFIGS_DIR / "nodes"
FIELD_CONFIGS_DIR = FRONTEND_CONFIGS_DIR / "fields"
NODE_REGISTRY_PATH = PROJECT_ROOT / "apps/web/src/features/diagram-editor/config/nodeRegistry.ts"

# Template paths (relative to templates dir)
TEMPLATES = {
    'typescript_model': 'frontend/typescript_model.j2',
    'graphql_schema': 'backend/graphql_schema.j2',
    'node_config': 'frontend/node_config.j2',
    'field_config': 'frontend/field_config.j2',
    'static_nodes': 'backend/static_nodes.j2',
    'node_registry': 'frontend/node_registry.j2',
}


def get_output_paths(node_type: str, spec_data: dict) -> dict:
    """Get all output paths for a given node type."""
    snake_case = spec_data.get('nodeTypeSnake', '')
    camel_case = spec_data.get('nodeTypeCamel', '')
    
    return {
        'typescript_model': str(MODELS_DIR / f"{node_type}Node.ts"),
        'static_node': str(STATIC_NODES_DIR / f"{snake_case}_node.py"),
        'graphql_schema': str(GRAPHQL_DIR / f"{snake_case}_node.graphql"),
        'node_config': str(NODE_CONFIGS_DIR / f"{camel_case}NodeConfig.ts"),
        'field_config': str(FIELD_CONFIGS_DIR / f"{camel_case}FieldConfigs.ts"),
    }


def ensure_temp_dir():
    """Ensure temp directory exists."""
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    return TEMP_DIR