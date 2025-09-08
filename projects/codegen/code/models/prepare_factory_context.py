"""Prepare context for node factory generation from spec files."""
import ast
import json
from typing import Any


def prepare_factory_context(inputs: dict[str, Any]) -> dict[str, Any]:
    """
    Extract node specifications for factory generation.

    Args:
        inputs: Dictionary containing loaded AST data from glob pattern

    Returns:
        Dictionary with nodes array containing node type, name, and fields for template
    """

    nodes = []

    # Handle case where db node passes data as 'default'
    if 'default' in inputs:
        default_value = inputs['default']
        if isinstance(default_value, str):
            # Parse the Python dict string to get the actual glob results
            try:
                # Try ast.literal_eval first (for Python dict format)
                inputs = ast.literal_eval(default_value)
            except (ValueError, SyntaxError):
                # If that fails, try JSON
                try:
                    inputs = json.loads(default_value)
                except json.JSONDecodeError:
                    # If both fail, treat as empty
                    inputs = {}
        elif isinstance(default_value, dict):
            inputs = default_value

    # Process each spec file
    for filename, ast_data in inputs.items():
        if filename == 'default' or not filename.endswith('.spec.ts.json'):
            continue

        # Extract node type from filename (e.g., "api-job.spec.ts.json" -> "api_job")
        base_filename = filename.split('/')[-1]
        node_type = base_filename.replace('.spec.ts.json', '').replace('-', '_')

        # Convert to PascalCase for class name
        node_name = ''.join(word.title() for word in node_type.split('_'))

        # Parse AST data if string
        if isinstance(ast_data, str):
            ast_data = json.loads(ast_data)

        # Extract specification from constants
        fields = []
        for const in ast_data.get('constants', []):
            name = const.get('name', '')
            if name.endswith('Spec') or name.endswith('spec'):
                spec_value = const.get('value', {})
                if isinstance(spec_value, dict) and 'fields' in spec_value:
                    # Extract fields for factory generation
                    for field in spec_value.get('fields', []):
                        field_info = {
                            'name': field.get('name', ''),
                            'type': field.get('type', 'any'),
                            'required': field.get('required', False),
                            'description': field.get('description', ''),
                            'default': field.get('default'),
                        }

                        # Add Python default value based on type
                        if not field_info['required']:
                            if field_info['type'] in ['object', 'dict', 'json']:
                                field_info['python_default'] = '{}'
                            elif field_info['type'] in ['array', 'list']:
                                field_info['python_default'] = '[]'
                            elif field_info['type'] == 'boolean':
                                field_info['python_default'] = str(field_info.get('default', False))
                            elif field_info['type'] == 'number':
                                field_info['python_default'] = str(field_info.get('default', 0))
                            elif field_info['type'] == 'string':
                                default_val = field_info.get('default', '')
                                field_info['python_default'] = f"'{default_val}'" if default_val else "''"
                            else:
                                field_info['python_default'] = 'None'

                        fields.append(field_info)

                    nodes.append({
                        'node_type': node_type,
                        'node_name': node_name,
                        'fields': fields
                    })
                    break

    # Sort for consistent output
    nodes.sort(key=lambda x: x['node_type'])

    # Wrap in 'default' to prevent unwrapping by runtime resolver
    result = {
        'default': {
            'nodes': nodes
        }
    }

    return result
