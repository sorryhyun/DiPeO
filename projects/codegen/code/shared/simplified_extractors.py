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
    Also preserves the full glob results for spec extraction.
    
    Args:
        inputs: Dict with file paths as keys from DB glob operation
        
    Returns:
        Dictionary with 'node_data' organized by node type and the full glob results
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
    
    # Return both the extracted node data AND the full glob results
    # This allows extract_specs_from_combined_data to work with the spec files
    result = {'node_data': node_data_by_type}
    
    # Include the full glob results so specs can be extracted
    # Add all the original glob results to the output
    for filepath, ast_data in glob_results.items():
        if filepath not in ['default', 'inputs', 'node_id']:
            result[filepath] = ast_data
    
    return result


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


def generate_node_mutations(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate node-specific mutations for each node type.
    
    Args:
        inputs: Either glob results OR strawberry_types from prepare_strawberry_types
        
    Returns:
        Dictionary with mutations ready for template processing
    """
    # Check if we have strawberry_types already or need to generate them
    if 'strawberry_types' in inputs:
        # Handle the double nesting from DiPeO
        strawberry_types_data = inputs.get('strawberry_types', {})
        if isinstance(strawberry_types_data, dict) and 'strawberry_types' in strawberry_types_data:
            strawberry_types = strawberry_types_data['strawberry_types']
        else:
            strawberry_types = strawberry_types_data if isinstance(strawberry_types_data, list) else []
    else:
        # Generate strawberry types from glob results
        types_data = prepare_strawberry_types(inputs)
        strawberry_types = types_data.get('strawberry_types', [])
    
    mutations = []
    
    for node_type_info in strawberry_types:
        # Generate create mutation
        mutations.append({
            'name': f"create_{node_type_info['node_type']}_node",
            'input_type': f"Create{node_type_info['class_name']}Input",
            'return_type': f"{node_type_info['class_name']}DataType",
            'node_type': node_type_info['node_type'],
            'operation': 'create'
        })
        
        # Generate update mutation
        mutations.append({
            'name': f"update_{node_type_info['node_type']}_node",
            'input_type': f"Update{node_type_info['class_name']}Input",
            'return_type': f"{node_type_info['class_name']}DataType",
            'node_type': node_type_info['node_type'],
            'operation': 'update'
        })
    
    return {
        'mutations': mutations,
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
    
    # Transform GraphQL input types from node data interfaces
    input_types = []
    for interface in node_data_interfaces:
        if interface.get('name', '').endswith('Data'):
            # Transform properties to fields for template compatibility
            fields = interface.get('properties', [])
            input_types.append({
                'name': interface['name'],
                'fields': fields,  # Use 'fields' instead of 'properties'
                'description': interface.get('description')
            })
    
    # Separate scalars from regular types
    scalars = []
    graphql_types = []
    
    # Define known scalar types (ID types and JSON types)
    scalar_names = {
        'NodeID', 'ArrowID', 'HandleID', 'PersonID', 'ApiKeyID', 
        'DiagramID', 'ExecutionID', 'SerializedNodeOutput',
        'PersonMemoryMessage', 'PersonBatchJobNodeData',
        'JsonValue', 'JsonDict', 'JSON', 'Array', 'ID'
    }
    
    for type_def in all_types:
        type_name = type_def.get('name')
        
        # Check if this is a scalar type
        if type_name in scalar_names or type_name.endswith('ID'):
            scalars.append({
                'name': type_name,
                'description': type_def.get('description') or f'Unique identifier for {type_name.replace("ID", "").lower()}'
            })
        else:
            # Regular GraphQL type
            graphql_type = {
                'name': type_name,
                'fields': [],  # Type aliases don't have fields in GraphQL
                'description': type_def.get('description')
            }
            graphql_types.append(graphql_type)
    
    # Add standard GraphQL scalars if not already present
    scalar_names_present = {s['name'] for s in scalars}
    if 'JSON' not in scalar_names_present:
        scalars.append({
            'name': 'JSON',
            'description': 'The `JSON` scalar type represents JSON values'
        })
    if 'JsonDict' not in scalar_names_present:
        scalars.append({
            'name': 'JsonDict',
            'description': 'JSON object type'
        })
    if 'JsonValue' not in scalar_names_present:
        scalars.append({
            'name': 'JsonValue',
            'description': 'Any JSON value'
        })
    if 'Array' not in scalar_names_present:
        scalars.append({
            'name': 'Array',
            'description': 'Array type'
        })
    if 'ID' not in scalar_names_present:
        scalars.append({
            'name': 'ID',
            'description': 'The `ID` scalar type represents a unique identifier'
        })
    
    # Process interfaces to extract as GraphQL types if needed
    for interface in all_interfaces:
        if not interface.get('name', '').endswith('Data'):
            # Non-data interfaces might be exposed as types
            graphql_type = {
                'name': interface.get('name'),
                'fields': interface.get('properties', []),
                'description': interface.get('description')
            }
            graphql_types.append(graphql_type)
    
    return {
        'interfaces': all_interfaces,
        'types': graphql_types,
        'enums': all_enums,
        'input_types': input_types,
        'node_data_interfaces': node_data_interfaces,
        'scalars': scalars,  # Now properly populated
        'node_types': [it['name'] for it in input_types],  # For union type
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
        
        # Check if this is a spec file (not index.ts.json)
        if not filepath.endswith('.spec.ts.json'):
            continue
        
        # Extract node type from filename (keep hyphen format)
        base_filename = os.path.basename(filepath)
        node_type = base_filename.replace('.spec.ts.json', '')
        
        # Skip index file or invalid node types
        if node_type == 'index' or not node_type:
            continue
        
        # Parse AST data if string
        if isinstance(ast_data, str):
            ast_data = json.loads(ast_data)
        
        # Verify it contains valid spec
        has_valid_spec = False
        for const in ast_data.get('constants', []):
            name = const.get('name', '')
            if name.endswith('Spec') or name.endswith('spec'):
                # Additional check: ensure the spec has a nodeType
                spec_value = const.get('value', {})
                if isinstance(spec_value, dict) and 'nodeType' in spec_value:
                    has_valid_spec = True
                    break
        
        if has_valid_spec:
            node_types.append(node_type)
    
    # Return list for batch processing, sorted for consistency
    return [{'node_spec_path': node_type} for node_type in sorted(node_types)]


def generate_models_summary(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Generate summary of Python models generation."""
    generation_result = inputs.get('generation_result', {})
    
    result = {
        'status': 'success',
        'message': 'Python domain models generated successfully',
        'details': generation_result
    }
    
    return result


# Backward compatibility aliases
extract_node_specs = extract_node_specs_from_glob
extract_node_data_from_ast = extract_node_data_from_glob
extract_models = extract_models_from_glob
generate_strawberry_types = prepare_strawberry_types