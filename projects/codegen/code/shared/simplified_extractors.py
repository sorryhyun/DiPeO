"""
Simplified extractors that work directly with DB glob results.
Eliminates intermediate extraction steps.
"""

import ast
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any


def parse_string_to_dict(value: Any) -> dict[str, Any]:
    """
    Parse a string value to dictionary if needed.
    Handles both Python dict format (single quotes) and JSON format.
    """
    if isinstance(value, str):
        try:
            # Try ast.literal_eval first (for Python dict format)
            return ast.literal_eval(value)
        except (ValueError, SyntaxError):
            # If that fails, try JSON
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                # If both fail, return empty dict
                return {}
    return value if isinstance(value, dict) else {}


def extract_node_specs_from_glob(inputs: dict[str, Any]) -> dict[str, Any]:
    """
    Extract node specifications directly from glob-loaded spec files.

    Args:
        inputs: Dict with file paths as keys from DB glob operation

    Returns:
        Dictionary with 'node_specs' key containing list of specs
    """
    # Handle wrapped inputs (db node may wrap in 'default')
    glob_results = parse_string_to_dict(inputs['default']) if 'default' in inputs else inputs

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


def extract_node_data_from_glob(inputs: dict[str, Any]) -> dict[str, Any]:
    """
    Extract node data interfaces from spec files by generating them from fields.
    Since .data.ts files no longer exist, we generate interfaces from specifications.

    Args:
        inputs: Dict with file paths as keys from DB glob operation

    Returns:
        Dictionary with 'node_data' organized by node type and the full glob results
    """
    # Handle wrapped inputs
    glob_results = parse_string_to_dict(inputs['default']) if 'default' in inputs else inputs

    node_data_by_type = {}

    for filepath, ast_data in glob_results.items():
        # Skip special keys
        if filepath in ['default', 'inputs', 'node_id']:
            continue

        # Check if this is a spec file (not data file anymore)
        if not filepath.endswith('.spec.ts.json'):
            continue

        # Extract node type from filename
        base_filename = Path(filepath).name
        # Remove .spec.ts.json to get node type
        node_type = base_filename.replace('.spec.ts.json', '').replace('-', '_')

        # Parse AST data if string
        if isinstance(ast_data, str):
            ast_data = json.loads(ast_data)

        # Extract the specification from constants
        for const in ast_data.get('constants', []):
            const_name = const.get('name', '')
            if const_name.endswith('Spec') or const_name.endswith('spec'):
                spec_value = const.get('value', {})
                if isinstance(spec_value, dict) and 'nodeType' in spec_value:
                    # Generate interface from specification fields
                    interface_name = ''.join(word.capitalize() for word in node_type.split('_')) + 'NodeData'

                    # Convert spec fields to interface properties
                    properties = []
                    for field in spec_value.get('fields', []):
                        field_name = field.get('name')
                        field_type = field.get('type', 'any')
                        required = field.get('required', False)

                        # Map field types to TypeScript types
                        if field_type == 'enum':
                            # For enums, use string type as a simplification
                            ts_type = 'string'
                        elif field_type == 'number':
                            ts_type = 'number'
                        elif field_type == 'boolean':
                            ts_type = 'boolean'
                        elif field_type == 'array':
                            ts_type = 'any[]'
                        elif field_type == 'object':
                            ts_type = 'Record<string, any>'
                        else:
                            ts_type = field_type if field_type else 'any'

                        properties.append({
                            'name': field_name,
                            'type': ts_type,
                            'optional': not required,
                            'description': field.get('description', '')
                        })

                    # Create synthetic interface structure matching what the old code expected
                    interface = {
                        'name': interface_name,
                        'properties': properties,
                        'extends': ['BaseNodeData']  # All node data extends BaseNodeData
                    }

                    node_data_by_type[node_type] = {
                        'interface': interface,
                        'properties': properties
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


def prepare_strawberry_types(inputs: dict[str, Any]) -> dict[str, Any]:
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
        class_name = ''.join(word.capitalize() for word in node_type.split('_'))

        # Extract fields and identify which ones are Dict types
        fields = []
        for field in spec.get('fields', []):
            field_name = field.get('name', '')
            field_type = field.get('type', 'any')
            required = field.get('required', False)

            # Determine if this is a Dict/object type that needs JSONScalar
            is_dict_type = field_type in ['object', 'Record<string, any>', 'any', 'json']

            fields.append({
                'name': field_name,
                'type': field_type,
                'required': required,
                'is_dict_type': is_dict_type,
                'description': field.get('description', '')
            })

        strawberry_types.append({
            'node_type': node_type,
            'class_name': class_name,
            'pydantic_model': class_name,
            'display_name': spec.get('displayName', ''),
            'description': spec.get('description', ''),
            'category': spec.get('category', ''),
            'fields': fields
        })

    return {
        'strawberry_types': strawberry_types,
        'generated_at': datetime.now().isoformat()
    }


def generate_node_mutations(inputs: dict[str, Any]) -> dict[str, Any]:
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


def _generate_interface_from_spec(spec: dict[str, Any]) -> dict[str, Any] | None:
    """
    Generate an interface definition from a node specification.

    Args:
        spec: Node specification with fields

    Returns:
        Interface definition or None if cannot generate
    """
    # Get node type and clean it
    node_type = spec.get('nodeType', '')
    node_type = node_type.replace('NodeType.', '').replace('"', '')

    if not node_type:
        return None

    # Convert node type to interface name
    # e.g., PERSON_JOB -> PersonJobNodeData
    parts = node_type.split('_')
    interface_name = ''.join(part.capitalize() for part in parts) + 'NodeData'

    # Convert fields to properties
    properties = []
    for field in spec.get('fields', []):
        # Map field type to TypeScript type
        field_type = field.get('type', 'any')

        # Handle special types
        if field_type == 'select':
            # Get from options or default to string
            field_type = 'string'
        elif field_type == 'enum':
            field_type = 'string'

        # Build property definition
        prop = {
            'name': field.get('name'),
            'type': field_type,
            'optional': not field.get('required', False),
            'description': field.get('description')
        }

        # Add validation info if present
        if 'validation' in field:
            prop['validation'] = field['validation']

        properties.append(prop)

    # Return interface definition
    return {
        'name': interface_name,
        'properties': properties,
        'extends': ['BaseNodeData'],  # All node data interfaces extend BaseNodeData
        'description': f"Data model for {spec.get('displayName', node_type)} node"
    }


def _process_interface_jsdoc(interfaces: list[dict]) -> None:
    """Process interfaces and map jsDoc to description."""
    for interface in interfaces:
        if interface.get('jsDoc'):
            interface['description'] = interface['jsDoc']

        if 'properties' in interface:
            for prop in interface['properties']:
                if prop.get('jsDoc'):
                    prop['description'] = prop['jsDoc']


def _extract_branded_types(types: list[dict]) -> list[str]:
    """Extract branded type names from type definitions."""
    branded_types = []
    for type_alias in types:
        alias_type = type_alias.get('type', '')
        if '& {' in alias_type and '__brand' in alias_type:
            branded_types.append(type_alias.get('name', ''))
    return sorted(branded_types)


def _filter_deprecated_types(types: list[dict]) -> list[dict]:
    """Filter out deprecated type aliases."""
    deprecated_aliases = ['ExecutionStatus', 'NodeExecutionStatus']
    return [t for t in types if t.get('name') not in deprecated_aliases]


def extract_models_from_glob(inputs: dict[str, Any]) -> dict[str, Any]:
    """
    Extract all model data (interfaces, types, enums) from glob-loaded AST files.

    Args:
        inputs: Dict with file paths as keys from DB glob operation

    Returns:
        Dictionary with extracted model data for template processing
    """
    # Handle wrapped inputs
    glob_results = parse_string_to_dict(inputs['default']) if 'default' in inputs else inputs

    all_interfaces = []
    all_types = []
    all_enums = []
    all_constants = []

    # Process each file in glob results
    for filepath, ast_data in glob_results.items():
        # Skip special keys
        if filepath in ['default', 'inputs', 'node_id']:
            continue

        # Parse AST data if string
        if isinstance(ast_data, str):
            ast_data = json.loads(ast_data)

        # Collect data from each file
        interfaces = ast_data.get('interfaces', [])
        _process_interface_jsdoc(interfaces)

        all_interfaces.extend(interfaces)
        all_types.extend(ast_data.get('types', []))
        all_enums.extend(ast_data.get('enums', []))
        all_constants.extend(ast_data.get('constants', []))

        # Generate interfaces from specifications
        if filepath.endswith('.spec.ts.json'):
            for const in ast_data.get('constants', []):
                name = const.get('name', '')
                if name.endswith('Spec') or name.endswith('spec'):
                    spec_value = const.get('value', {})
                    if isinstance(spec_value, dict) and 'fields' in spec_value:
                        # Generate interface from spec fields
                        interface = _generate_interface_from_spec(spec_value)
                        if interface:
                            all_interfaces.append(interface)

    # Filter and process types
    filtered_types = _filter_deprecated_types(all_types)
    branded_types = _extract_branded_types(filtered_types)

    return {
        'interfaces': all_interfaces,
        'types': filtered_types,
        'enums': all_enums,
        'constants': all_constants,
        'branded_types': branded_types,
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


def _collect_graphql_ast_data(glob_results: dict) -> tuple[list, list, list, list]:
    """Collect AST data from glob results, separating node data interfaces."""
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

    return all_interfaces, all_types, all_enums, node_data_interfaces


def _create_input_types(node_data_interfaces: list[dict]) -> list[dict]:
    """Transform GraphQL input types from node data interfaces."""
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
    return input_types


def _separate_scalars_and_types(all_types: list[dict]) -> tuple[list, list]:
    """Separate scalars from regular GraphQL types."""
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

    return scalars, graphql_types


def _add_standard_scalars(scalars: list[dict]) -> None:
    """Add standard GraphQL scalars if not already present."""
    scalar_names_present = {s['name'] for s in scalars}
    standard_scalars = [
        ('JSON', 'The `JSON` scalar type represents JSON values'),
        ('JsonDict', 'JSON object type'),
        ('JsonValue', 'Any JSON value'),
        ('Array', 'Array type'),
        ('ID', 'The `ID` scalar type represents a unique identifier'),
    ]

    for name, description in standard_scalars:
        if name not in scalar_names_present:
            scalars.append({'name': name, 'description': description})


def _add_interface_types(all_interfaces: list[dict], graphql_types: list[dict]) -> None:
    """Process interfaces to extract as GraphQL types if needed."""
    for interface in all_interfaces:
        if not interface.get('name', '').endswith('Data'):
            # Non-data interfaces might be exposed as types
            graphql_type = {
                'name': interface.get('name'),
                'fields': interface.get('properties', []),
                'description': interface.get('description')
            }
            graphql_types.append(graphql_type)


def prepare_graphql_schema_data(inputs: dict[str, Any]) -> dict[str, Any]:
    """
    Prepare GraphQL schema data from glob-loaded AST files.

    Args:
        inputs: Dict with file paths as keys from DB glob operation

    Returns:
        Dictionary with GraphQL types ready for template processing
    """
    # Handle wrapped inputs
    glob_results = parse_string_to_dict(inputs['default']) if 'default' in inputs else inputs

    # Collect all AST data
    all_interfaces, all_types, all_enums, node_data_interfaces = _collect_graphql_ast_data(glob_results)

    # Create input types from node data interfaces
    input_types = _create_input_types(node_data_interfaces)

    # Separate scalars from regular types
    scalars, graphql_types = _separate_scalars_and_types(all_types)

    # Add standard GraphQL scalars
    _add_standard_scalars(scalars)

    # Add interface-based types
    _add_interface_types(all_interfaces, graphql_types)

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


def prepare_zod_schemas_data(inputs: dict[str, Any]) -> dict[str, Any]:
    """
    Prepare Zod schemas data from glob-loaded AST files.

    Args:
        inputs: Dict with file paths as keys from DB glob operation

    Returns:
        Dictionary with Zod schemas ready for template processing
    """
    # Handle wrapped inputs
    glob_results = parse_string_to_dict(inputs['default']) if 'default' in inputs else inputs

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
            base_filename = Path(filepath).name
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


def prepare_node_list_for_batch(inputs: dict[str, Any]) -> list[dict[str, str]]:
    """
    Prepare node list for batch processing from glob-loaded spec files.

    Args:
        inputs: Dict containing the glob results from DB operation

    Returns:
        List of dictionaries with node_spec_path for batch processing
    """
    # The DB node with glob returns results as a Python dict string in 'default'
    glob_results = parse_string_to_dict(inputs['default']) if 'default' in inputs else inputs

    node_types = []

    for filepath, ast_data in glob_results.items():
        # Skip special keys
        if filepath in ['default', 'inputs', 'node_id', 'globals']:
            continue

        # Check if this is a spec file (not index.ts.json)
        if not filepath.endswith('.spec.ts.json'):
            continue

        # Extract node type from filename (keep hyphen format)
        base_filename = Path(filepath).name
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


def generate_models_summary(inputs: dict[str, Any]) -> dict[str, Any]:
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
