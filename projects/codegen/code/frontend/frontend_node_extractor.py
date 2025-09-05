"""Extract frontend node data from TypeScript AST.

The AST parser provides properly structured data.
Templates handle case conversions using Jinja2 filters.
"""

import ast
import json
from typing import Any, Dict
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
    
    # Get ast_data and parse if it's a string
    raw_ast_data = actual_inputs.get('ast_data', {})
    if isinstance(raw_ast_data, str):
        try:
            # Try ast.literal_eval first (for Python dict format with single quotes)
            ast_data = ast.literal_eval(raw_ast_data)
        except (ValueError, SyntaxError):
            # If that fails, try JSON
            try:
                ast_data = json.loads(raw_ast_data)
            except json.JSONDecodeError:
                ast_data = {}
    else:
        ast_data = raw_ast_data if isinstance(raw_ast_data, dict) else {}
    
    # Try to get node_type from multiple possible keys
    # In batch mode it comes as node_spec_path
    node_type = actual_inputs.get('node_type') or actual_inputs.get('node_spec_path')
    
    # Better error handling for missing node_type
    if not node_type:
        available_inputs = list(actual_inputs.keys())
        raise ValueError(
            f"node_type or node_spec_path not provided in inputs. Available keys: {available_inputs}. "
            f"Full inputs: {actual_inputs}"
        )
    
    # Convert hyphenated to underscore format (api-job -> api_job)
    node_type = node_type.replace('-', '_')
    
    if not ast_data:
        raise ValueError(
            f"No AST data provided for node type: {node_type}"
        )
    
    result = extract_frontend_node_data(ast_data, node_type)
    
    return result