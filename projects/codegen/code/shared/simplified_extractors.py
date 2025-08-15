"""
Simplified extractors that work directly with DB glob results.
Eliminates intermediate extraction steps.
"""

import json
import os
from typing import Any, Dict, List
from datetime import datetime


def extract_node_specs_from_glob(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract node specifications directly from glob-loaded spec files.
    
    Args:
        inputs: Dict with file paths as keys from DB glob operation
        
    Returns:
        Dictionary with 'node_specs' key containing list of specs
    """
    # Handle wrapped inputs (db node may wrap in 'default')
    if 'default' in inputs and isinstance(inputs['default'], dict):
        glob_results = inputs['default']
    else:
        glob_results = inputs
    
    node_specs = []
    
    for filepath, ast_data in glob_results.items():
        # Skip special keys
        if filepath in ['default', 'inputs', 'node_id']:
            continue
        
        # Check if this is a spec file
        if not filepath.endswith('.spec.ts.json'):
            continue
        
        # Parse AST data if string
        if isinstance(ast_data, str):
            ast_data = json.loads(ast_data)
        
        # Extract specs from constants
        for const in ast_data.get('constants', []):
            name = const.get('name', '')
            if name.endswith('Spec') or name.endswith('spec'):
                spec_value = const.get('value', {})
                if isinstance(spec_value, dict) and 'nodeType' in spec_value:
                    # Clean up nodeType
                    node_type = spec_value.get('nodeType', '')
                    node_type = node_type.replace('NodeType.', '').replace('"', '').lower()
                    
                    node_specs.append({
                        'name': node_type,
                        'displayName': spec_value.get('displayName'),
                        'category': spec_value.get('category'),
                        'description': spec_value.get('description'),
                        'fields': spec_value.get('fields', [])
                    })
    
    return {'node_specs': node_specs}


def extract_node_data_from_glob(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract node data interfaces directly from glob-loaded data files.
    
    Args:
        inputs: Dict with file paths as keys from DB glob operation
        
    Returns:
        Dictionary with 'node_data' organized by node type
    """
    # Handle wrapped inputs
    if 'default' in inputs and isinstance(inputs['default'], dict):
        glob_results = inputs['default']
    else:
        glob_results = inputs
    
    node_data_by_type = {}
    
    for filepath, ast_data in glob_results.items():
        # Skip special keys
        if filepath in ['default', 'inputs', 'node_id']:
            continue
        
        # Check if this is a data file
        if not filepath.endswith('.data.ts.json'):
            continue
        
        # Extract node type from filename
        base_filename = os.path.basename(filepath)
        node_type = base_filename.replace('.data.ts.json', '').replace('-', '_')
        
        # Parse AST data if string
        if isinstance(ast_data, str):
            ast_data = json.loads(ast_data)
        
        # Find the data interface
        for interface in ast_data.get('interfaces', []):
            interface_name = interface.get('name', '')
            if interface_name.endswith('Data') and not interface_name.startswith('Base'):
                node_data_by_type[node_type] = {
                    'interface': interface,
                    'properties': interface.get('properties', [])
                }
                break
    
    return {'node_data': node_data_by_type}


def prepare_strawberry_types(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate Strawberry GraphQL types data directly from glob results.
    
    Args:
        inputs: Dict with file paths as keys from DB glob operation
        
    Returns:
        Dictionary with strawberry_types ready for template processing
    """
    # First extract the specs
    specs_data = extract_node_specs_from_glob(inputs)
    node_specs = specs_data.get('node_specs', [])
    
    strawberry_types = []
    
    for spec in node_specs:
        node_type = spec['name']
        
        # Convert node type to class name
        if node_type == 'db':
            class_name = 'DB'
        else:
            class_name = ''.join(word.capitalize() for word in node_type.split('_'))
        
        strawberry_types.append({
            'node_type': node_type,
            'class_name': class_name,
            'pydantic_model': class_name,
            'display_name': spec.get('displayName', ''),
            'description': spec.get('description', ''),
            'category': spec.get('category', '')
        })
    
    return {
        'strawberry_types': strawberry_types,
        'generated_at': datetime.now().isoformat()
    }


def extract_models_from_glob(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract all model data (interfaces, types, enums) from glob-loaded AST files.
    
    Args:
        inputs: Dict with file paths as keys from DB glob operation
        
    Returns:
        Dictionary with extracted model data for template processing
    """
    # Handle wrapped inputs
    if 'default' in inputs and isinstance(inputs['default'], dict):
        glob_results = inputs['default']
    else:
        glob_results = inputs
    
    all_interfaces = []
    all_types = []
    all_enums = []
    all_constants = []
    
    for filepath, ast_data in glob_results.items():
        # Skip special keys
        if filepath in ['default', 'inputs', 'node_id']:
            continue
        
        # Parse AST data if string
        if isinstance(ast_data, str):
            ast_data = json.loads(ast_data)
        
        # Process interfaces and map jsDoc to description
        interfaces = ast_data.get('interfaces', [])
        for interface in interfaces:
            if 'jsDoc' in interface and interface['jsDoc']:
                interface['description'] = interface['jsDoc']
            
            if 'properties' in interface:
                for prop in interface['properties']:
                    if 'jsDoc' in prop and prop['jsDoc']:
                        prop['description'] = prop['jsDoc']
        
        all_interfaces.extend(interfaces)
        all_types.extend(ast_data.get('types', []))
        all_enums.extend(ast_data.get('enums', []))
        all_constants.extend(ast_data.get('constants', []))
    
    # Filter out deprecated type aliases
    deprecated_aliases = ['ExecutionStatus', 'NodeExecutionStatus']
    filtered_types = [t for t in all_types if t.get('name') not in deprecated_aliases]
    
    # Extract branded types
    branded_types = []
    for type_alias in filtered_types:
        alias_type = type_alias.get('type', '')
        if '& {' in alias_type and '__brand' in alias_type:
            branded_types.append(type_alias.get('name', ''))
    
    return {
        'interfaces': all_interfaces,
        'types': filtered_types,
        'enums': all_enums,
        'constants': all_constants,
        'branded_types': sorted(branded_types),
        'interfaces_count': len(all_interfaces),
        'types_count': len(filtered_types),
        'enums_count': len(all_enums),
        'constants_count': len(all_constants),
        'config': {
            'allow_extra': False,
            'use_field_validators': True,
            'generate_type_guards': True,
        }
    }


def prepare_graphql_schema_data(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Prepare GraphQL schema data from glob-loaded AST files.
    
    Args:
        inputs: Dict with file paths as keys from DB glob operation
        
    Returns:
        Dictionary with GraphQL types ready for template processing
    """
    # Handle wrapped inputs
    if 'default' in inputs and isinstance(inputs['default'], dict):
        glob_results = inputs['default']
    else:
        glob_results = inputs
    
    # Collect all interfaces, types, and enums
    all_interfaces = []
    all_types = []
    all_enums = []
    node_data_interfaces = []
    
    for filepath, ast_data in glob_results.items():
        # Skip special keys
        if filepath in ['default', 'inputs', 'node_id']:
            continue
        
        # Parse AST data if string
        if isinstance(ast_data, str):
            ast_data = json.loads(ast_data)
        
        # Extract definitions from AST
        interfaces = ast_data.get('interfaces', [])
        types = ast_data.get('types', [])
        enums = ast_data.get('enums', [])
        
        # Special handling for node data files
        if '.data.ts.json' in filepath:
            node_data_interfaces.extend(interfaces)
        else:
            all_interfaces.extend(interfaces)
        
        all_types.extend(types)
        all_enums.extend(enums)
    
    # Extract GraphQL input types from node data interfaces
    input_types = []
    for interface in node_data_interfaces:
        if interface.get('name', '').endswith('Data'):
            input_types.append({
                'name': interface['name'],
                'properties': interface.get('properties', [])
            })
    
    return {
        'interfaces': all_interfaces,
        'types': all_types,
        'enums': all_enums,
        'input_types': input_types,
        'node_data_interfaces': node_data_interfaces,
        'now': datetime.now().isoformat()
    }


def prepare_zod_schemas_data(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Prepare Zod schemas data from glob-loaded AST files.
    
    Args:
        inputs: Dict with file paths as keys from DB glob operation
        
    Returns:
        Dictionary with Zod schemas ready for template processing
    """
    # Handle wrapped inputs
    if 'default' in inputs and isinstance(inputs['default'], dict):
        glob_results = inputs['default']
    else:
        glob_results = inputs
    
    # Extract mappings if provided
    mappings = inputs.get('mappings', {})
    
    # Collect all interfaces and enums
    all_interfaces = []
    all_enums = []
    node_configs = []
    
    for filepath, ast_data in glob_results.items():
        # Skip special keys
        if filepath in ['default', 'inputs', 'node_id']:
            continue
        
        # Parse AST data if string
        if isinstance(ast_data, str):
            ast_data = json.loads(ast_data)
        
        # Collect definitions
        interfaces = ast_data.get('interfaces', [])
        enums = ast_data.get('enums', [])
        
        # Collect interfaces for node data files
        if '.data.ts.json' in filepath:
            # Extract node type from filename
            base_filename = os.path.basename(filepath)
            node_type = base_filename.replace('.data.ts.json', '').replace('-', '_')
            
            # Find the data interface
            for interface in interfaces:
                if interface.get('name', '').endswith('Data'):
                    node_configs.append({
                        'node_type': node_type,
                        'interface': interface,
                        'properties': interface.get('properties', [])
                    })
        
        all_interfaces.extend(interfaces)
        all_enums.extend(enums)
    
    # Get node interface map from mappings
    node_interface_map = mappings.get('node_interface_map', {})
    base_fields = mappings.get('base_fields', ['label', 'flipped'])
    
    return {
        'interfaces': all_interfaces,
        'enums': all_enums,
        'node_configs': node_configs,
        'node_interface_map': node_interface_map,
        'base_fields': base_fields,
        'now': datetime.now().isoformat()
    }


def prepare_node_list_for_batch(inputs: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Prepare node list for batch processing from glob-loaded spec files.
    
    Args:
        inputs: Dict with file paths as keys from DB glob operation
        
    Returns:
        List of dictionaries with node_spec_path for batch processing
    """
    # Handle wrapped inputs
    if 'default' in inputs and isinstance(inputs['default'], dict):
        glob_results = inputs['default']
    else:
        glob_results = inputs
    
    node_types = []
    
    for filepath, ast_data in glob_results.items():
        # Skip special keys
        if filepath in ['default', 'inputs', 'node_id']:
            continue
        
        # Check if this is a spec file
        if not filepath.endswith('.spec.ts.json'):
            continue
        
        # Extract node type from filename (keep hyphen format)
        base_filename = os.path.basename(filepath)
        node_type = base_filename.replace('.spec.ts.json', '')
        
        # Parse AST data if string
        if isinstance(ast_data, str):
            ast_data = json.loads(ast_data)
        
        # Verify it contains valid spec
        for const in ast_data.get('constants', []):
            name = const.get('name', '')
            if name.endswith('Spec') or name.endswith('spec'):
                node_types.append(node_type)
                break
    
    # Return list for batch processing
    return [{'node_spec_path': node_type} for node_type in sorted(node_types)]


# Backward compatibility aliases
extract_node_specs = extract_node_specs_from_glob
extract_node_data_from_ast = extract_node_data_from_glob
extract_models = extract_models_from_glob
generate_strawberry_types = prepare_strawberry_types