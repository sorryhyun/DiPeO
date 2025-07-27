"""
TypeScript specification parser
Extracts node specifications from TypeScript AST data
"""

import json
import re
from typing import Any, Dict, List, Optional, Union


def extract_spec_from_ast(ast_data: Dict[str, Any], spec_name: str) -> Optional[Dict[str, Any]]:
    """
    Extract a node specification from TypeScript AST data.
    
    The typescript_ast node now provides parsed constants.
    We need to find the specific spec constant and transform it.
    """
    # Check what data we actually got
    # Get constants from AST data
    constants = ast_data.get('constants', [])
    # Find the spec constant by name
    for const in constants:
        if const.get('name') == spec_name:
            # The value should contain the parsed object
            value = const.get('value')

            if isinstance(value, dict):
                # Transform the spec to ensure proper format
                return transform_ast_to_spec(value)
            else:
                print(f"[TypeScript Spec Parser] Unexpected value type: {value}")
    
    # If not found, list available constants
    available_constants = [const.get('name', '') for const in constants]

    return None


def transform_ast_to_spec(ast_obj: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform the AST object representation to our specification format.
    
    The typescript_ast node returns the parsed object literal.
    We may need to clean up some values.
    """
    # The object should already be in the right format if the parser worked correctly
    # Just do some basic transformations if needed
    spec = dict(ast_obj)  # Create a copy

    # Handle nodeType if it's still an enum reference string
    if 'nodeType' in spec:
        node_type = spec['nodeType']
        if isinstance(node_type, str):
            # If it looks like "NodeType.PERSON_JOB" or just "PERSON_JOB"
            if '.' in node_type:
                node_type = node_type.split('.')[-1]
            # Convert PERSON_JOB to person_job
            if node_type.isupper():
                node_type = node_type.lower()
            spec['nodeType'] = node_type
    
    # Transform fields if they contain enum references
    if 'fields' in spec and isinstance(spec['fields'], list):
        spec['fields'] = transform_fields(spec['fields'])
    
    return spec


def transform_fields(fields: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Transform field definitions from AST format to specification format.
    
    Handles enum references and ensures all values are properly formatted.
    """
    transformed_fields = []
    
    for field in fields:
        # Copy all field properties
        transformed_field = dict(field)
        
        # Handle defaultValue if it contains enum references
        if 'defaultValue' in transformed_field:
            default_val = transformed_field['defaultValue']
            # Transform enum references
            if isinstance(default_val, str):
                # "MemoryView.ALL_INVOLVED" -> "all_involved"
                if '.' in default_val:
                    default_val = default_val.split('.')[-1]
                # "ALL_INVOLVED" -> "all_involved"
                if default_val.isupper() and '_' in default_val:
                    default_val = default_val.lower()
                transformed_field['defaultValue'] = default_val
        
        # Handle validation
        if 'validation' in transformed_field and isinstance(transformed_field['validation'], dict):
            validation = transformed_field['validation']
            
            # Handle allowedValues
            if 'allowedValues' in validation:
                allowed = validation['allowedValues']
                if isinstance(allowed, list):
                    # Transform each value
                    transformed_values = []
                    for val in allowed:
                        if isinstance(val, str):
                            # Handle enum references
                            if '.' in val:
                                val = val.split('.')[-1]
                            if val.isupper() and '_' in val:
                                val = val.lower()
                        transformed_values.append(val)
                    validation['allowedValues'] = transformed_values
        
        # Handle nested fields recursively
        if 'nestedFields' in transformed_field and isinstance(transformed_field['nestedFields'], list):
            transformed_field['nestedFields'] = transform_fields(transformed_field['nestedFields'])
        
        # Handle uiConfig.options for select fields
        if 'uiConfig' in transformed_field and isinstance(transformed_field['uiConfig'], dict):
            ui_config = transformed_field['uiConfig']
            if 'options' in ui_config and isinstance(ui_config['options'], list):
                # Transform option values
                for option in ui_config['options']:
                    if isinstance(option, dict) and 'value' in option:
                        val = option['value']
                        if isinstance(val, str):
                            # Handle enum references
                            if '.' in val:
                                val = val.split('.')[-1]
                            if val.isupper() and '_' in val:
                                val = val.lower()
                            option['value'] = val
        
        transformed_fields.append(transformed_field)
    
    return transformed_fields


def convert_typescript_type_to_field_type(ts_type: str) -> str:
    """
    Convert TypeScript type to field type used in specifications.
    """
    type_map = {
        'string': 'string',
        'number': 'number',
        'boolean': 'boolean',
        'any': 'any',
        'object': 'object',
        'array': 'array',
        'string[]': 'array',
        'number[]': 'array',
        'ToolConfig[]': 'array',
    }
    
    return type_map.get(ts_type, 'any')


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
    
    # Convert node type to spec name (e.g., "person_job" -> "personJobSpec") 
    # Note: node_type might come with underscores (person_job) or hyphens (person-job)
    node_type_clean = node_type.replace('-', '_')  # Normalize to underscores
    spec_name = f"{node_type_clean.replace('_', ' ').title().replace(' ', '')}Spec"
    spec_name = spec_name[0].lower() + spec_name[1:]  # camelCase
    
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