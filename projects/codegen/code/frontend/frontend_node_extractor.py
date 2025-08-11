"""Extract frontend node data from TypeScript AST in a single pass."""

from typing import Dict, List, Any
from projects.codegen.code.shared.typescript_spec_parser import extract_spec_from_ast
from dipeo.infrastructure.services.jinja_template.filters.base_filters import BaseFilters


def extract_frontend_node_data(ast_data: dict, node_type: str) -> dict:
    """Extract all data needed for frontend templates from AST."""
    
    spec_name = f"{node_type.replace('_', ' ').title().replace(' ', '')}Spec"
    spec_name = spec_name[0].lower() + spec_name[1:]
    
    spec_data = extract_spec_from_ast(ast_data, spec_name)
    
    if not spec_data:
        available_constants = [const.get('name', '') for const in ast_data.get('constants', [])]
        raise ValueError(
            f"Could not find specification '{spec_name}' for node type '{node_type}'. "
            f"Available constants: {available_constants}"
        )
    
    # Handle NodeType.ENUM_VALUE format from TypeScript
    raw_node_type = spec_data.get('nodeType', node_type)
    
    # Remove "NodeType." prefix if present and convert to snake_case
    if raw_node_type.startswith('NodeType.'):
        node_type_enum = raw_node_type.replace('NodeType.', '')
        actual_node_type = node_type_enum.lower()  # Convert UPPER_SNAKE to lower_snake
    else:
        actual_node_type = raw_node_type
    
    # Create proper node_name in PascalCase
    node_name = BaseFilters.pascal_case(actual_node_type)
    
    result = {
        **spec_data,
        'nodeType': actual_node_type,
        'nodeTypePascal': BaseFilters.pascal_case(actual_node_type),
        'nodeTypeCamel': BaseFilters.camel_case(actual_node_type),
        'nodeTypeSnake': BaseFilters.snake_case(actual_node_type),
        'node_name': node_name,
        'node_naming': {
            'node_type': actual_node_type,
            'node_name': node_name
        }
    }
    
    # Process handles into template-expected format
    if 'handles' in result and isinstance(result['handles'], dict):
        transformed_handles = {'inputs': [], 'outputs': []}
        
        if 'inputs' in result['handles'] and isinstance(result['handles']['inputs'], list):
            for handle in result['handles']['inputs']:
                if isinstance(handle, str):
                    transformed_handles['inputs'].append({
                        'label': handle,
                        'displayLabel': handle.title() if handle != 'default' else '',
                        'position': 'left'
                    })
                elif isinstance(handle, dict):
                    transformed_handles['inputs'].append({
                        'label': handle.get('label', ''),
                        'displayLabel': handle.get('displayLabel', ''),
                        'position': handle.get('position', 'left')
                    })
        
        if 'outputs' in result['handles'] and isinstance(result['handles']['outputs'], list):
            for handle in result['handles']['outputs']:
                if isinstance(handle, str):
                    transformed_handles['outputs'].append({
                        'label': handle,
                        'displayLabel': handle.title() if handle != 'default' else '',
                        'position': 'right'
                    })
                elif isinstance(handle, dict):
                    transformed_handles['outputs'].append({
                        'label': handle.get('label', ''),
                        'displayLabel': handle.get('displayLabel', ''),
                        'position': handle.get('position', 'right')
                    })
        
        result['handles'] = transformed_handles
    
    defaults = {}
    if 'fields' in result and isinstance(result['fields'], list):
        for field in result['fields']:
            if 'defaultValue' in field and field.get('defaultValue') is not None:
                field['default'] = field['defaultValue']
                defaults[field['name']] = field['defaultValue']
            elif 'default' in field and field.get('default') is not None:
                defaults[field['name']] = field['default']
    
    result['defaults'] = defaults
    
    result.setdefault('displayName', result.get('nodeType', 'Unknown').replace('_', ' ').title())
    result.setdefault('icon', '📦')
    result.setdefault('color', '#6366f1')
    result.setdefault('category', 'utility')
    result.setdefault('description', '')
    result.setdefault('fields', [])
    result.setdefault('primaryDisplayField', '')
    
    return result


def main(inputs: dict) -> dict:
    """Main entry point matching the expected signature."""
    if 'default' in inputs and isinstance(inputs['default'], dict):
        actual_inputs = inputs['default']
    else:
        actual_inputs = inputs
    
    ast_data = actual_inputs.get('ast_data', {})
    node_type = actual_inputs.get('node_type', 'unknown')
    
    result = extract_frontend_node_data(ast_data, node_type)
    
    return result