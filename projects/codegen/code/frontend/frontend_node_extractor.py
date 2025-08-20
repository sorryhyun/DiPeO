"""Extract frontend node data from TypeScript AST.

The AST parser provides properly structured data.
Templates handle case conversions using Jinja2 filters.
"""

from projects.codegen.code.shared.typescript_spec_parser import extract_spec_from_ast


def snake_to_pascal(text: str) -> str:
    """Convert snake_case to PascalCase (for output path interpolation)."""
    if not text:
        return ''
    return ''.join(word.capitalize() for word in text.split('_'))


def extract_frontend_node_data(ast_data: dict, node_type: str) -> dict:
    """Extract node specification from AST and add minimal required fields."""
    
    # Convert node_type to spec name format  
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
    if raw_node_type.startswith('NodeType.'):
        actual_node_type = raw_node_type.replace('NodeType.', '').lower()
    else:
        actual_node_type = raw_node_type
    
    # Return spec data with minimal additions
    result = {
        **spec_data,
        'nodeType': actual_node_type,
        'node_name': snake_to_pascal(actual_node_type),  # For output path interpolation
    }
    
    # Set defaults for missing fields
    result.setdefault('displayName', actual_node_type.replace('_', ' ').title())
    result.setdefault('icon', '📦')
    result.setdefault('color', '#6366f1')
    result.setdefault('category', 'utility')
    result.setdefault('description', '')
    result.setdefault('fields', [])
    result.setdefault('handles', {})
    result.setdefault('defaults', {})
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