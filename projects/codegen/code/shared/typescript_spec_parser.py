"""
TypeScript specification parser
Extracts node specifications from TypeScript AST data
"""

import json
import re
from typing import Any, Dict, List, Optional, Union

# Import type transformer from the parser infrastructure
import sys
import os
sys.path.append(os.environ.get('DIPEO_BASE_DIR', '/home/soryhyun/DiPeO'))
from dipeo.infrastructure.codegen.parsers.typescript.type_transformer import map_ts_type_to_python


def extract_spec_from_ast(ast_data: Dict[str, Any], spec_name: str) -> Optional[Dict[str, Any]]:
    """
    Extract a node specification from TypeScript AST data.
    
    The typescript_ast node provides parsed constants with structured data.
    """
    constants = ast_data.get('constants', [])
    
    for const in constants:
        if const.get('name') == spec_name:
            value = const.get('value')
            
            if isinstance(value, dict):
                # The AST parser should already provide properly structured data
                # Only do minimal transformation if needed
                return normalize_spec_format(value)
    
    return None


def normalize_spec_format(spec_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize the specification data format.
    
    The AST parser should provide properly structured data.
    This function performs minimal normalization if needed.
    """
    spec = dict(spec_data)  # Create a copy
    
    # The modern parser should handle most transformations
    # Only normalize fields if present
    if 'fields' in spec and isinstance(spec['fields'], list):
        spec['fields'] = normalize_fields(spec['fields'])
    
    return spec


def normalize_fields(fields: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Normalize field definitions.
    
    The modern parser should provide properly formatted data.
    This function only ensures consistency.
    """
    normalized_fields = []
    
    for field in fields:
        normalized_field = dict(field)
        
        # Handle nested fields recursively
        if 'nestedFields' in normalized_field and isinstance(normalized_field['nestedFields'], list):
            normalized_field['nestedFields'] = normalize_fields(normalized_field['nestedFields'])
        
        normalized_fields.append(normalized_field)
    
    return normalized_fields


def convert_typescript_type_to_field_type(ts_type: str) -> str:
    """
    Convert TypeScript type to field type used in specifications.
    Uses the infrastructure's type transformer for consistency.
    """
    # For simple field types, we need the basic form
    # The infrastructure returns Python types, so we need to map back to field types
    python_type = map_ts_type_to_python(ts_type)
    
    # Map Python types back to field types used in specifications
    field_type_map = {
        'str': 'string',
        'float': 'number',
        'int': 'number',
        'bool': 'boolean',
        'Any': 'any',
        'Dict[str, Any]': 'object',
        'None': 'null'
    }
    
    # Check for List types
    if python_type.startswith('List['):
        return 'array'
    
    # Check for basic types
    for py_type, field_type in field_type_map.items():
        if py_type in python_type:
            return field_type
    
    # Default to 'any' for unknown types
    return 'any'


def main(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main entry point for the TypeScript specification parser.
    
    Inputs:
        - ast_data: AST data from typescript_ast node
        - node_type: The node type to extract (e.g., "person_job")
    
    Outputs:
        - spec_data: The extracted specification as a Python dict
    """
    ast_data = inputs.get('ast_data', {})
    node_type = inputs.get('node_type', '')
    
    # Convert node type to spec name (e.g., "person-job" -> "personJobSpec") 
    # Note: node_type now comes with hyphens (person-job) to match file names
    # Convert to camelCase for the spec name
    parts = node_type.split('-')
    # First part is lowercase, rest are title case
    spec_name = parts[0] + ''.join(part.title() for part in parts[1:]) + 'Spec'
    
    # Extract the specification from AST
    spec_data = extract_spec_from_ast(ast_data, spec_name)
    
    if not spec_data:
        # If we can't find it, raise an error with helpful information
        available_constants = [const.get('name', '') for const in ast_data.get('constants', [])]
        available_exports = [export.get('name', '') for export in ast_data.get('exports', [])]
        raise ValueError(
            f"Could not find specification '{spec_name}' for node type '{node_type}'. "
            f"Available constants: {available_constants}, exports: {available_exports}"
        )
    
    return {"spec_data": spec_data}