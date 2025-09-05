"""Extract Zod schemas from TypeScript AST data."""

import os
import re
from typing import Any


def build_enum_schemas(enums: list[dict[str, Any]]) -> dict[str, str]:
    """Build Zod enum schemas from AST enum data"""
    enum_schemas = {}
    for enum in enums:
        name = enum.get('name', '')
        members = enum.get('members', [])
        values = []
        for member in members:
            value = member.get('value', member.get('name', ''))
            values.append(f"'{value}'")
        enum_schemas[name] = f"z.enum([{', '.join(values)}])"
    return enum_schemas


def get_zod_type(type_text: str, enum_schemas: dict[str, str], type_to_zod: dict[str, str]) -> str:
    """Convert TypeScript type to Zod schema"""
    # Handle union types with null/undefined
    clean_type = type_text.replace(' | null', '').replace(' | undefined', '').strip()

    # Check for enum schemas
    if clean_type in enum_schemas:
        return enum_schemas[clean_type]

    # Check for type mapping
    if clean_type in type_to_zod:
        zod_type = type_to_zod[clean_type]
        # For branded types and enums, reference them directly
        if zod_type == clean_type:
            return zod_type
        return zod_type

    # Handle arrays
    if clean_type.endswith('[]'):
        element_type = clean_type[:-2]
        element_zod = get_zod_type(element_type, enum_schemas, type_to_zod)
        return f"z.array({element_zod})"

    # Handle Record types
    if clean_type.startswith('Record<'):
        match = re.match(r'Record<(.+),\s*(.+)>', clean_type)
        if match:
            value_type = match.group(2).strip()
            value_zod = get_zod_type(value_type, enum_schemas, type_to_zod)
            return f"z.record(z.string(), {value_zod})"

    # Default to z.any()
    return 'z.any()'


def generate_property_schema(prop: dict[str, Any], enum_schemas: dict[str, str], type_to_zod: dict[str, str]) -> str:
    """Generate Zod schema for a property"""
    name = prop.get('name', '')
    type_text = prop.get('type', 'any')
    is_optional = prop.get('optional', False)

    zod_schema = get_zod_type(type_text, enum_schemas, type_to_zod)

    # Handle optional
    if is_optional:
        zod_schema = f"{zod_schema}.optional()"

    # Handle nullable
    if ' | null' in type_text:
        zod_schema = f"{zod_schema}.nullable()"

    return f"  {name}: {zod_schema}"


def generate_interface_schema(interface_data: dict[str, Any], enum_schemas: dict[str, str], type_to_zod: dict[str, str], base_fields: list[str]) -> str:
    """Generate Zod schema for an interface"""
    properties = []

    for prop in interface_data.get('properties', []):
        name = prop.get('name', '')

        # Skip base fields
        if name in base_fields:
            continue

        prop_schema = generate_property_schema(prop, enum_schemas, type_to_zod)
        properties.append(prop_schema)

    return f"z.object({{\n{',\n'.join(properties)}\n}})"


def extract_zod_schemas(ast_data: dict, mappings: dict) -> dict:
    """Extract Zod schemas from TypeScript AST data"""
    interfaces = ast_data.get('interfaces', [])
    enums = ast_data.get('enums', [])

    print(f"Total interfaces in ast_data: {len(interfaces)}")

    # Get mappings
    node_interface_map = mappings.get('node_interface_map', {})
    branded_types = mappings.get('branded_types', [])
    type_to_zod = mappings.get('type_to_zod', {})
    base_fields = mappings.get('base_fields', ['label', 'flipped'])

    print(f"Node interface mappings: {list(node_interface_map.items())[:5]}...")  # Show first 5

    # Build enum schemas
    enum_schemas = build_enum_schemas(enums)

    # Generate schemas for each node type
    schemas = []

    for node_type, interface_name in node_interface_map.items():
        # Find the interface
        interface_data = None
        for iface in interfaces:
            if iface.get('name') == interface_name:
                interface_data = iface
                break

        if not interface_data:
            print(f"Warning: Interface {interface_name} not found")
            continue

        schema_code = generate_interface_schema(interface_data, enum_schemas, type_to_zod, base_fields)

        schemas.append({
            'nodeType': node_type,
            'interfaceName': interface_name,
            'schemaCode': schema_code
        })

    print(f"Generated Zod schemas for {len(schemas)} node types")

    return {
        'schemas': schemas,
        'enum_schemas': enum_schemas,
        'branded_types': branded_types
    }


def main(inputs: dict) -> dict:
    """Main entry point for Zod schemas extraction"""
    import ast
    import json
    from datetime import datetime
    from pathlib import Path

    # Check if we have the new format (single input with multiple files)
    if 'ast_files' in inputs:
        # Get the raw data
        raw_files = inputs['ast_files']

        # Parse string to dict if needed (DiPeO returns Python dict strings from glob)
        if isinstance(raw_files, str):
            try:
                # Try ast.literal_eval first (for Python dict format with single quotes)
                file_dict = ast.literal_eval(raw_files)
            except (ValueError, SyntaxError):
                # If that fails, try JSON
                try:
                    file_dict = json.loads(raw_files)
                except json.JSONDecodeError:
                    file_dict = {}
        else:
            file_dict = raw_files if isinstance(raw_files, dict) else {}

        # Handle wrapped inputs (runtime resolver may wrap in 'default')
        if 'default' in file_dict and isinstance(file_dict['default'], dict):
            file_dict = file_dict['default']

        # Parse AST data from the files
        diagram_ast = None
        all_interfaces = []
        all_enums = []

        for filepath, content in file_dict.items():
            if filepath == 'default':
                continue
            # Extract filename from path
            filename = filepath.split('/')[-1] if '/' in filepath else filepath

            if filename == 'diagram.ts.json':
                diagram_ast = content if isinstance(content, dict) else json.loads(content)
            elif filename.endswith('.data.ts.json') or filename.endswith('.ts.json'):
                # This is a node data file or other TypeScript file
                ast_data = content if isinstance(content, dict) else json.loads(content)
                interfaces = ast_data.get('interfaces', [])
                enums = ast_data.get('enums', [])
                all_interfaces.extend(interfaces)
                all_enums.extend(enums)

        # Get mappings - the extract_mappings output comes through 'default' key
        # (because the connection from extract_mappings has label 'mappings' but arrives as 'default')
        raw_mappings = inputs.get('default', {})

        # Parse mappings if it's a string
        if isinstance(raw_mappings, str):
            try:
                mappings = ast.literal_eval(raw_mappings)
            except (ValueError, SyntaxError):
                try:
                    mappings = json.loads(raw_mappings)
                except json.JSONDecodeError:
                    mappings = {}
        else:
            mappings = raw_mappings if isinstance(raw_mappings, dict) else {}

        # If not found, check other possible locations
        if not mappings:
            raw_mappings = inputs.get('mappings', {})
            if isinstance(raw_mappings, str):
                try:
                    mappings = ast.literal_eval(raw_mappings)
                except (ValueError, SyntaxError):
                    try:
                        mappings = json.loads(raw_mappings)
                    except json.JSONDecodeError:
                        mappings = {}
            else:
                mappings = raw_mappings if isinstance(raw_mappings, dict) else {}

        # If still not found and we have 'inputs' dict, check there
        if not mappings and 'inputs' in inputs and isinstance(inputs['inputs'], dict):
            mappings = inputs['inputs'].get('default', {})
            if not mappings:
                mappings = inputs['inputs'].get('mappings', {})

        # Create aggregated AST data from collected interfaces
        node_data_ast = {
            'interfaces': all_interfaces,
            'types': [],
            'enums': all_enums,
            'constants': []
        }
    else:
        # Legacy format: separate inputs
        node_data_ast = inputs.get('node_data', {})
        diagram_ast = inputs.get('default', {})
        mappings = inputs.get('mappings', {})

    # Now use the node_data_ast and mappings we prepared above
    result = extract_zod_schemas(node_data_ast, mappings)
    result['now'] = datetime.now().isoformat()

    return result
