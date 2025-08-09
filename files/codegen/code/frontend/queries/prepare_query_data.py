"""
Prepare GraphQL query data from TypeScript definitions for template generation.
This module loads parsed TypeScript AST data and transforms it into a format
suitable for the Jinja2 template that generates GraphQL queries.
"""

import json
from typing import Any, Dict, List, Optional, Union
from pathlib import Path


def load_query_definitions(ast_cache: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Load query definitions from parsed TypeScript AST cache.
    
    Args:
        ast_cache: Parsed TypeScript AST data containing query definitions
        
    Returns:
        List of query definition objects
    """
    query_definitions = []
    
    # Dynamically find all query definition files in the AST cache
    query_definition_keys = []
    
    for key in ast_cache.keys():
        # Look for keys that match query definition patterns
        if 'query-definitions/' in key and key.endswith('.ts'):
            query_definition_keys.append(key)
        elif 'query-definitions/' in key and key.endswith('.ts.json'):
            query_definition_keys.append(key)
    
    # Process each found query definition file
    for key in query_definition_keys:
        file_data = ast_cache[key]
        
        if file_data:
            # Extract constants that contain query definitions
            if 'constants' in file_data:
                for const in file_data['constants']:
                    # Each constant has a value that contains queries
                    const_value = const.get('value', {})
                    if isinstance(const_value, dict) and 'queries' in const_value:
                        # Extract each query from the queries array
                        for query in const_value.get('queries', []):
                            query_def = transform_query_from_ast(query, const_value.get('entity'))
                            if query_def:
                                query_definitions.append(query_def)
    
    return query_definitions


def load_query_enums(ast_cache: Dict[str, Any]) -> Dict[str, Dict[str, str]]:
    """
    Load enum values from the query-enums.ts file.
    
    Args:
        ast_cache: Parsed TypeScript AST data
        
    Returns:
        Dictionary mapping enum names to their values
    """
    enums = {}
    
    # Look for query-enums file dynamically
    enum_file_key = None
    for key in ast_cache.keys():
        if 'query-enums.ts' in key:
            enum_file_key = key
            break
    
    if enum_file_key and enum_file_key in ast_cache:
        file_data = ast_cache[enum_file_key]
        if 'enums' in file_data:
            for enum in file_data['enums']:
                enum_name = enum.get('name', '')
                enum_values = {}
                for member in enum.get('members', []):
                    key = member.get('name', '')
                    value = member.get('value', key)
                    enum_values[key] = value
                enums[enum_name] = enum_values
    
    return enums


def transform_query_from_ast(query_data: Dict[str, Any], entity: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Transform a query from TypeScript AST into template-ready format.
    
    Args:
        query_data: Parsed query from TypeScript AST
        entity: Entity name from the parent constant
        
    Returns:
        Transformed query definition or None if not valid
    """
    if not isinstance(query_data, dict):
        return None
    
    # Extract query specification
    query_spec = {
        'name': query_data.get('name', 'unknown'),
        'operationType': extract_operation_type(query_data),
        'entity': entity or extract_entity(query_data),
        'operation': extract_operation(query_data),
        'fieldPreset': query_data.get('fieldPreset', 'STANDARD'),
        'variables': transform_variables(query_data.get('variables', [])),
        'fields': transform_fields(query_data.get('fields', [])),
        'responseType': query_data.get('responseType'),
        'description': query_data.get('description', '')
    }
    
    return query_spec


def extract_operation_type(query_def: Dict[str, Any]) -> str:
    """
    Extract the GraphQL operation type (query, mutation, subscription).
    """
    # Check for 'type' field first (from AST), then 'operationType'
    op_type = query_def.get('type', query_def.get('operationType', 'QUERY'))
    
    # Handle enum references like "QueryOperationType.QUERY"
    if isinstance(op_type, str) and '.' in op_type:
        op_type = op_type.split('.')[-1]
    
    # Convert to lowercase and handle common patterns
    op_type = op_type.lower()
    
    # Map to standard GraphQL operation types
    if 'mutation' in op_type:
        return 'mutation'
    elif 'subscription' in op_type:
        return 'subscription'
    else:
        return 'query'


def extract_entity(query_def: Dict[str, Any]) -> str:
    """
    Extract the entity type from the query definition.
    """
    entity = query_def.get('entity', '')
    # Handle enum references
    if '.' in entity:
        entity = entity.split('.')[-1]
    return entity.lower()


def extract_operation(query_def: Dict[str, Any]) -> str:
    """
    Extract the CRUD operation from the query definition.
    """
    operation = query_def.get('operation', '')
    # Handle enum references
    if '.' in operation:
        operation = operation.split('.')[-1]
    return operation.lower()


def graphql_to_typescript_type(graphql_type: str) -> str:
    """
    Convert GraphQL type to TypeScript type.
    """
    # Remove array and non-null markers for base type mapping
    base_type = graphql_type.replace('[', '').replace(']', '').replace('!', '').strip()
    
    # Basic scalar mappings
    type_map = {
        'ID': 'string',
        'String': 'string',
        'Int': 'number',
        'Float': 'number',
        'Boolean': 'boolean',
        'JSON': 'any',
        'DateTime': 'string',
        'Date': 'string',
    }
    
    # Check if it's a known scalar
    if base_type in type_map:
        ts_type = type_map[base_type]
    else:
        # Keep complex types as-is (e.g., AddMessageInput, CreateDiagramInput)
        ts_type = base_type
    
    # Handle arrays
    if '[' in graphql_type:
        ts_type = f'{ts_type}[]'
    
    return ts_type


def transform_variables(variables: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Transform variable definitions into template-ready format.
    """
    transformed = []
    for var in variables:
        graphql_type = var.get('graphqlType', var.get('type', 'String'))
        
        transformed_var = {
            'name': var.get('name', ''),
            'type': graphql_type,
            'tsType': var.get('tsType') or graphql_to_typescript_type(graphql_type),
            'required': var.get('required', False),
            'description': var.get('description', '')
        }
        # Handle default values
        if 'defaultValue' in var:
            transformed_var['defaultValue'] = var['defaultValue']
        transformed.append(transformed_var)
    
    return transformed


def transform_fields(fields: Union[List, Dict, str]) -> List[Dict[str, Any]]:
    """
    Transform field selection into template-ready format.
    Handles various field selection formats.
    """
    if isinstance(fields, str):
        # Simple field name
        return [{'name': fields}]
    
    if isinstance(fields, list):
        transformed = []
        for field in fields:
            if isinstance(field, str):
                transformed.append({'name': field})
            elif isinstance(field, dict):
                field_def = {
                    'name': field.get('name', ''),
                    'args': transform_field_args(field.get('args', [])),
                    'fields': transform_fields(field.get('fields', []))
                }
                transformed.append(field_def)
        return transformed
    
    if isinstance(fields, dict):
        # Object with nested fields
        transformed = []
        for key, value in fields.items():
            if value is True:
                # Simple boolean selection
                transformed.append({'name': key})
            elif isinstance(value, (dict, list)):
                # Nested selection
                transformed.append({
                    'name': key,
                    'fields': transform_fields(value)
                })
        return transformed
    
    return []


def transform_field_args(args: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Transform field arguments into template-ready format.
    """
    transformed = []
    for arg in args:
        transformed_arg = {
            'name': arg.get('name', ''),
            'value': arg.get('value', ''),
            'isVariable': arg.get('isVariable', False)
        }
        transformed.append(transformed_arg)
    
    return transformed


def collect_input_types(query_definitions: List[Dict[str, Any]]) -> List[str]:
    """
    Collect all unique input types used in query variables.
    
    Args:
        query_definitions: List of query definitions
        
    Returns:
        List of unique input type names to import
    """
    input_types = set()
    
    # Common input types that we know are defined in @dipeo/models
    known_input_types = {
        'ExecutionControlInput',
        'DiagramFormat',
        'CreateApiKeyInput',
        'CreateDiagramInput',
        'CreateNodeInput',
        'CreatePersonInput',
        'ExecuteDiagramInput',
        'InteractiveResponseInput',
        'UpdateNodeInput',
        'UpdateNodeStateInput',
        'UpdatePersonInput',
        'DiagramFilterInput',
        'ExecutionFilterInput',
        'Scalars'
    }
    
    for query in query_definitions:
        # Check variables for input types
        for var in query.get('variables', []):
            var_type = var.get('type', '')
            # Remove array brackets and non-null markers
            base_type = var_type.replace('[', '').replace(']', '').replace('!', '').strip()
            
            # Check if it's a known input type
            if base_type in known_input_types:
                input_types.add(base_type)
            
            # Special case for Upload which requires Scalars
            if base_type == 'Upload':
                input_types.add('Scalars')
    
    # Always include Scalars if we have any input types that might need it
    if input_types and 'Scalars' not in input_types:
        # Check if any queries use Upload type
        for query in query_definitions:
            for var in query.get('variables', []):
                if 'Upload' in var.get('type', ''):
                    input_types.add('Scalars')
                    break
    
    return sorted(list(input_types))


def prepare_query_data_for_template(inputs: Any) -> Dict[str, Any]:
    """
    Main entry point for preparing query data for the template.
    
    Args:
        inputs: Contains loaded JSON files from temp/ directory
        
    Returns:
        Dictionary with 'queries' list ready for template rendering
    """
    # Get the loaded data - connection is labeled 'ast_files' in diagram
    loaded_data = inputs.get('ast_files', inputs.get('default', {})) if isinstance(inputs, dict) else inputs
    
    # Build ast_cache from loaded JSON files
    ast_cache = {}
    
    # When db node uses glob=true, it returns {filepath: content, ...}
    if isinstance(loaded_data, dict):
        # Process the files directly
        for key, value in loaded_data.items():
            # Skip non-dict entries
            if not isinstance(value, dict):
                continue
            
            # Extract the relative path from temp/
            if key.startswith('temp/'):
                # Use a simpler key - just remove 'temp/' and '.json'
                relative_path = key.replace('temp/', '').replace('.json', '')
                ast_cache[relative_path] = value
            else:
                # Use key as-is if it doesn't start with temp/
                ast_cache[key] = value
    else:
        return {'queries': [], 'enums': {}, 'metadata': {}, 'input_types': []}
    
    # Load query definitions
    query_definitions = load_query_definitions(ast_cache)
    
    # Load enum values for reference
    enums = load_query_enums(ast_cache)
    
    # Collect input types for imports
    input_types = collect_input_types(query_definitions)
    
    # Sort queries by operation type and name for consistent output
    query_definitions.sort(key=lambda q: (q['operationType'], q['name']))
    
    return {
        'queries': query_definitions,
        'enums': enums,
        'input_types': input_types,
        'metadata': {
            'total_queries': len([q for q in query_definitions if q['operationType'] == 'query']),
            'total_mutations': len([q for q in query_definitions if q['operationType'] == 'mutation']),
            'total_subscriptions': len([q for q in query_definitions if q['operationType'] == 'subscription'])
        }
    }


def validate_query_data(query_data: Dict[str, Any]) -> bool:
    """
    Validate that the query data is properly formatted.
    
    Args:
        query_data: Query data to validate
        
    Returns:
        True if valid, raises ValueError if not
    """
    if 'queries' not in query_data:
        raise ValueError("Query data must contain 'queries' key")
    
    for query in query_data['queries']:
        if 'name' not in query:
            raise ValueError(f"Query missing 'name': {query}")
        if 'operationType' not in query:
            raise ValueError(f"Query missing 'operationType': {query['name']}")
        if query['operationType'] not in ['query', 'mutation', 'subscription']:
            raise ValueError(f"Invalid operationType: {query['operationType']}")
    
    return True