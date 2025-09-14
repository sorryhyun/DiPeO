"""
Unified IR Builder for Frontend Code Generation
Consolidates all frontend extractors into a single IR for template consumption.
"""

from __future__ import annotations
from pathlib import Path
import json
from typing import Any, Dict, List, Optional
from datetime import datetime
import sys
import os

# Add the DiPeO base directory to path for imports
sys.path.append(os.environ.get('DIPEO_BASE_DIR', '/home/soryhyun/DiPeO'))


# ============================================================================
# SHARED UTILITIES
# ============================================================================

def snake_to_pascal(text: str) -> str:
    """Convert snake_case to PascalCase."""
    return ''.join(word.capitalize() for word in text.split('_'))


def pascal_to_camel(text: str) -> str:
    """Convert PascalCase to camelCase."""
    if not text:
        return text
    return text[0].lower() + text[1:]


def graphql_to_typescript_type(graphql_type: str) -> str:
    """Convert GraphQL type to TypeScript type."""
    type_map = {
        'String': 'string',
        'Int': 'number',
        'Float': 'number',
        'Boolean': 'boolean',
        'ID': 'string',
        'DateTime': 'string',
        'JSON': 'any',
        'JSONScalar': 'any',
        'Upload': 'File',
    }

    # Handle arrays
    if graphql_type.startswith('[') and graphql_type.endswith(']'):
        inner = graphql_type[1:-1].replace('!', '')
        return f'{graphql_to_typescript_type(inner)}[]'

    # Remove required marker
    clean_type = graphql_type.replace('!', '')

    return type_map.get(clean_type, clean_type)


# ============================================================================
# NODE CONFIGS EXTRACTION
# ============================================================================

def extract_node_configs(ast_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract frontend node configurations from TypeScript AST."""
    node_configs = []

    for file_path, file_data in ast_data.items():
        if not file_path.endswith('.spec.ts.json'):
            continue

        # Extract node type from filename
        base_name = Path(file_path).stem.replace('.spec.ts', '')
        node_type = base_name.replace('-', '_')
        node_name = snake_to_pascal(node_type)
        config_name = f'{node_name}Config'

        # Look for the specification constant
        for const in file_data.get('constants', []):
            const_name = const.get('name', '')
            # Check for spec constants (could be 'apiJobSpec' or 'apiJobSpecification')
            if const_name.endswith('Spec') or const_name.endswith('Specification'):
                spec_value = const.get('value', {})
                if not isinstance(spec_value, dict):
                    continue

                # Extract UI-specific configuration
                ui_config = {
                    'name': config_name,
                    'node_type': node_type,
                    'node_name': node_name,
                    'display_name': spec_value.get('displayName', node_name),
                    'category': spec_value.get('category', ''),
                    'description': spec_value.get('description', ''),
                    'icon': spec_value.get('icon', ''),
                    'color': spec_value.get('color', '#666'),
                    'fields': [],
                    'validation_schema': None,
                }

                # Process fields for UI
                for field in spec_value.get('fields', []):
                    field_config = {
                        'name': field.get('name', ''),
                        'type': field.get('type', 'string'),
                        'label': field.get('label', field.get('name', '')),
                        'placeholder': field.get('placeholder', ''),
                        'help_text': field.get('description', ''),
                        'required': field.get('required', False),
                        'default_value': field.get('defaultValue'),
                        'validation': field.get('validation', {}),
                        'ui_type': field.get('uiType', 'text'),  # text, textarea, select, etc.
                        'options': field.get('options', []),
                    }
                    ui_config['fields'].append(field_config)

                node_configs.append(ui_config)
                break

    return node_configs


# ============================================================================
# FIELD CONFIGS EXTRACTION
# ============================================================================

def generate_field_configs(node_configs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Generate field configuration objects from node configs."""
    field_configs = []
    processed_field_types = set()

    for config in node_configs:
        for field in config['fields']:
            field_type = field['ui_type']

            # Skip if we've already processed this field type
            if field_type in processed_field_types:
                continue

            processed_field_types.add(field_type)

            field_config = {
                'type': field_type,
                'component': get_field_component(field_type),
                'props': get_field_props(field_type),
                'validation_rules': get_field_validation(field_type),
            }
            field_configs.append(field_config)

    return field_configs


def get_field_component(field_type: str) -> str:
    """Get React component name for field type."""
    component_map = {
        'text': 'TextField',
        'textarea': 'TextArea',
        'number': 'NumberField',
        'select': 'SelectField',
        'checkbox': 'CheckboxField',
        'radio': 'RadioGroup',
        'date': 'DatePicker',
        'file': 'FileUpload',
        'json': 'JsonEditor',
        'code': 'CodeEditor',
    }
    return component_map.get(field_type, 'TextField')


def get_field_props(field_type: str) -> Dict[str, Any]:
    """Get default props for field type."""
    props_map = {
        'text': {'variant': 'outlined', 'fullWidth': True},
        'textarea': {'rows': 4, 'multiline': True, 'fullWidth': True},
        'number': {'type': 'number', 'fullWidth': True},
        'select': {'fullWidth': True},
        'checkbox': {},
        'radio': {'row': True},
        'date': {'format': 'MM/dd/yyyy'},
        'file': {'accept': '*/*'},
        'json': {'height': '200px', 'theme': 'light'},
        'code': {'height': '300px', 'language': 'javascript'},
    }
    return props_map.get(field_type, {})


def get_field_validation(field_type: str) -> List[str]:
    """Get validation rules for field type."""
    validation_map = {
        'text': ['string', 'max:255'],
        'textarea': ['string', 'max:5000'],
        'number': ['number'],
        'select': ['string', 'in:options'],
        'checkbox': ['boolean'],
        'radio': ['string', 'in:options'],
        'date': ['date'],
        'file': ['file'],
        'json': ['json'],
        'code': ['string'],
    }
    return validation_map.get(field_type, [])


# ============================================================================
# ZOD SCHEMAS GENERATION
# ============================================================================

def create_zod_schemas(node_configs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Generate Zod validation schemas from node configurations."""
    schemas = []

    for config in node_configs:
        schema = {
            'name': f'{config["node_name"]}Schema',
            'fields': [],
        }

        for field in config['fields']:
            zod_field = {
                'name': field['name'],
                'type': get_zod_type(field['type']),
                'required': field['required'],
                'validations': [],
            }

            # Add validations
            if field.get('validation'):
                validation = field['validation']
                if validation.get('min'):
                    zod_field['validations'].append(f'min({validation["min"]})')
                if validation.get('max'):
                    zod_field['validations'].append(f'max({validation["max"]})')
                if validation.get('pattern'):
                    zod_field['validations'].append(f'regex(/{validation["pattern"]}/)')
                if validation.get('email'):
                    zod_field['validations'].append('email()')
                if validation.get('url'):
                    zod_field['validations'].append('url()')

            schema['fields'].append(zod_field)

        schemas.append(schema)

    return schemas


def get_zod_type(field_type: str) -> str:
    """Convert field type to Zod type."""
    type_map = {
        'string': 'z.string()',
        'number': 'z.number()',
        'boolean': 'z.boolean()',
        'array': 'z.array()',
        'object': 'z.object()',
        'any': 'z.any()',
        'Date': 'z.date()',
        'File': 'z.instanceof(File)',
    }
    return type_map.get(field_type, 'z.string()')


# ============================================================================
# GRAPHQL QUERIES EXTRACTION
# ============================================================================

def extract_graphql_queries(ast_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract GraphQL query definitions from TypeScript AST."""
    queries = []

    for file_path, file_data in ast_data.items():
        if 'query-definitions' not in file_path:
            continue

        # Extract queries from constants
        for const in file_data.get('constants', []):
            const_value = const.get('value', {})
            if isinstance(const_value, dict) and 'queries' in const_value:
                entity = const_value.get('entity', 'Unknown')

                for query in const_value.get('queries', []):
                    query_def = {
                        'name': query.get('name', ''),
                        'entity': entity,
                        'type': extract_operation_type(query),
                        'variables': transform_variables(query.get('variables', [])),
                        'fields': transform_fields(query.get('fields', [])),
                    }
                    queries.append(query_def)

    return queries


def extract_operation_type(query_def: Dict[str, Any]) -> str:
    """Extract operation type from query definition."""
    type_value = query_def.get('type', 'query')
    if '.' in type_value:
        return type_value.split('.')[-1].lower()
    return type_value.lower()


def transform_variables(variables: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Transform GraphQL variables to frontend format."""
    transformed = []
    for var in variables:
        transformed.append({
            'name': var.get('name', ''),
            'type': graphql_to_typescript_type(var.get('type', 'String')),
            'graphql_type': var.get('type', 'String'),
            'required': var.get('required', False),
        })
    return transformed


def transform_fields(fields: Any) -> List[Dict[str, Any]]:
    """Transform GraphQL fields to frontend format."""
    if not fields:
        return []

    if isinstance(fields, str):
        # Parse string representation of fields
        field_names = fields.strip().split()
        return [{'name': name, 'fields': []} for name in field_names]

    if isinstance(fields, list):
        transformed = []
        for field in fields:
            if isinstance(field, str):
                transformed.append({'name': field, 'fields': []})
            elif isinstance(field, dict):
                field_def = {
                    'name': field.get('name', ''),
                    'args': field.get('args', []),
                    'fields': transform_fields(field.get('fields', [])),
                }
                transformed.append(field_def)
        return transformed

    return []


# ============================================================================
# REGISTRY DATA GENERATION
# ============================================================================

def build_registry_data(node_configs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Build node registry configuration."""
    registry = {
        'nodes': {},
        'categories': {},
        'icons': {},
    }

    for config in node_configs:
        node_type = config['node_type']
        category = config['category']

        # Add to nodes registry
        registry['nodes'][node_type] = {
            'component': f'{config["node_name"]}Node',
            'config': config['name'],
            'category': category,
        }

        # Add to categories
        if category:
            if category not in registry['categories']:
                registry['categories'][category] = []
            registry['categories'][category].append(node_type)

        # Add icon mapping
        if config['icon']:
            registry['icons'][node_type] = config['icon']

    return registry


# ============================================================================
# TYPESCRIPT MODELS GENERATION
# ============================================================================

def generate_typescript_models(node_configs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Generate TypeScript model definitions from node configs."""
    models = []

    for config in node_configs:
        model = {
            'name': f'{config["node_name"]}Model',
            'interface_name': f'I{config["node_name"]}',
            'fields': [],
        }

        for field in config['fields']:
            ts_field = {
                'name': field['name'],
                'type': field['type'],
                'optional': not field['required'],
                'description': field.get('help_text', ''),
            }
            model['fields'].append(ts_field)

        models.append(model)

    return models


# ============================================================================
# UNIFIED IR BUILDER
# ============================================================================

class FrontendIRBuilder:
    """Unified IR builder for frontend code generation."""

    def __init__(self, base_dir: Path):
        self.base_dir = base_dir

    def build_ir(self, ast_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build complete frontend IR from TypeScript AST."""

        # Extract all components
        node_configs = extract_node_configs(ast_data)
        field_configs = generate_field_configs(node_configs)
        zod_schemas = create_zod_schemas(node_configs)
        graphql_queries = extract_graphql_queries(ast_data)
        registry_data = build_registry_data(node_configs)
        typescript_models = generate_typescript_models(node_configs)

        # Build complete IR
        ir = {
            'version': 1,
            'generated_at': datetime.now().isoformat(),

            # Core data
            'node_configs': node_configs,
            'field_configs': field_configs,
            'zod_schemas': zod_schemas,
            'graphql_queries': graphql_queries,
            'registry_data': registry_data,
            'typescript_models': typescript_models,

            # Organized by operation type for templates
            'queries': [q for q in graphql_queries if q['type'] == 'query'],
            'mutations': [q for q in graphql_queries if q['type'] == 'mutation'],
            'subscriptions': [q for q in graphql_queries if q['type'] == 'subscription'],

            # Metadata
            'metadata': {
                'node_count': len(node_configs),
                'field_type_count': len(field_configs),
                'schema_count': len(zod_schemas),
                'query_count': len([q for q in graphql_queries if q['type'] == 'query']),
                'mutation_count': len([q for q in graphql_queries if q['type'] == 'mutation']),
                'subscription_count': len([q for q in graphql_queries if q['type'] == 'subscription']),
                'categories': list(registry_data['categories'].keys()),
            },
        }

        return ir


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def build_frontend_ir(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build unified frontend IR from TypeScript AST files.
    This is the main entry point called by the diagram.

    Args:
        input_data: Input from the db node - contains AST data

    Returns:
        Complete unified IR for template rendering
    """
    # Load base directory
    base_dir = Path(os.environ.get('DIPEO_BASE_DIR', '/home/soryhyun/DiPeO'))

    # Create builder instance
    builder = FrontendIRBuilder(base_dir)

    # Handle input data - the db node always wraps in 'default' key
    file_dict = input_data.get('default', {})

    # Merge all AST files
    merged_ast = {}
    for file_path, ast_content in file_dict.items():
        if isinstance(ast_content, dict):
            merged_ast[file_path] = ast_content

    # Build IR
    print(f"Processing {len(merged_ast)} AST files for frontend generation")
    ir = builder.build_ir(merged_ast)

    # Write IR to file for debugging/inspection
    ir_output_path = base_dir / 'projects/codegen/ir/frontend_ir.json'
    ir_output_path.parent.mkdir(parents=True, exist_ok=True)
    ir_output_path.write_text(json.dumps(ir, indent=2))
    print(f"Wrote frontend IR to {ir_output_path}")

    # Print summary
    print(f"Generated frontend IR with:")
    print(f"  - {ir['metadata']['node_count']} node configurations")
    print(f"  - {ir['metadata']['field_type_count']} field types")
    print(f"  - {ir['metadata']['schema_count']} Zod schemas")
    print(f"  - {ir['metadata']['query_count']} queries")
    print(f"  - {ir['metadata']['mutation_count']} mutations")
    print(f"  - {ir['metadata']['subscription_count']} subscriptions")
    print(f"  - {len(ir['metadata']['categories'])} categories")

    return ir


# For backward compatibility
def main(inputs: dict[str, Any]) -> dict[str, Any]:
    """Backward compatibility wrapper."""
    return build_frontend_ir(inputs)
