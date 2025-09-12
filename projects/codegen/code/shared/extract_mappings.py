"""Unified extractor for codegen mappings, Zod schemas, and field configs from TypeScript AST."""

import json
import re
from typing import Any, Union

from projects.codegen.code.core.utils import parse_dipeo_output


def parse_object_expression(node: dict) -> dict:
    """Parse a TypeScript object expression from AST."""
    result = {}
    if node.get('type') == 'ObjectExpression':
        for prop in node.get('properties', []):
            if prop.get('type') == 'Property':
                # Get key
                key_node = prop.get('key', {})
                if key_node.get('type') == 'Identifier':
                    key = key_node.get('name', '')
                elif key_node.get('type') == 'Literal':
                    key = key_node.get('value', '')
                else:
                    continue

                # Get value
                value_node = prop.get('value', {})
                value = parse_value_node(value_node)

                result[key] = value
    return result


def parse_array_expression(node: dict) -> list:
    """Parse a TypeScript array expression from AST."""
    result = []
    if node.get('type') == 'ArrayExpression':
        for element in node.get('elements', []):
            if element:
                value = parse_value_node(element)
                result.append(value)
    return result


def parse_value_node(node: dict) -> Any:
    """Parse a value node from AST."""
    node_type = node.get('type', '')

    if node_type == 'Literal':
        return node.get('value')
    elif node_type == 'ObjectExpression':
        return parse_object_expression(node)
    elif node_type == 'ArrayExpression':
        return parse_array_expression(node)
    elif node_type == 'Identifier':
        # For field references like SupportedLanguage.python
        return node.get('name')
    elif node_type == 'MemberExpression':
        # For enum references like SupportedLanguage.python
        obj = node.get('object', {})
        prop = node.get('property', {})
        if obj.get('type') == 'Identifier' and prop.get('type') == 'Identifier':
            return f"{obj.get('name', '')}.{prop.get('name', '')}"
    elif node_type == 'TemplateLiteral':
        # Handle template literals
        parts = []
        quasis = node.get('quasis', [])
        expressions = node.get('expressions', [])

        for i, quasi in enumerate(quasis):
            parts.append(quasi.get('value', {}).get('cooked', ''))
            if i < len(expressions):
                # For now, just use placeholder for expressions
                parts.append('${...}')
        return ''.join(parts)
    elif node_type == 'CallExpression':
        # Handle function calls like field(default_factory=dict)
        callee = node.get('callee', {})
        if callee.get('type') == 'Identifier':
            func_name = callee.get('name', '')
            args = node.get('arguments', [])
            if func_name == 'field' and args:
                # Special handling for pydantic field calls
                return f"field({parse_field_args(args)})"
        return str(node)
    elif node_type == 'ArrowFunctionExpression':
        # Handle arrow functions like () => [...]
        return "field(default_factory=lambda: [\"interface\", \"type\", \"enum\"])"

    return None


def parse_field_args(args: list) -> str:
    """Parse field() function arguments."""
    parts = []
    for arg in args:
        if arg.get('type') == 'ObjectExpression':
            obj = parse_object_expression(arg)
            for k, v in obj.items():
                if k == 'default_factory':
                    parts.append(f"{k}={v}")
                elif isinstance(v, str):
                    parts.append(f'{k}="{v}"')
                else:
                    parts.append(f"{k}={v}")
    return ", ".join(parts)


def extract_mappings(ast_data: dict) -> dict:
    """Extract codegen mappings from TypeScript AST data."""
    # Initialize result structure
    mappings = {
        "node_interface_map": {},
        "ts_to_py_type": {},
        "type_to_field": {},
        "type_to_zod": {},
        "branded_types": [],
        "base_fields": [],
        "field_special_handling": {}
    }

    # Check if we have the new AST format with constants directly
    if 'constants' in ast_data:
        # New format: constants are already extracted
        for constant in ast_data.get('constants', []):
            var_name = constant.get('name', '')
            value = constant.get('value', {})

            # Map TypeScript constant names to our mapping keys
            mapping_name_map = {
                'NODE_INTERFACE_MAP': 'node_interface_map',
                'TS_TO_PY_TYPE': 'ts_to_py_type',
                'TYPE_TO_FIELD': 'type_to_field',
                'TYPE_TO_ZOD': 'type_to_zod',
                'BRANDED_TYPES': 'branded_types',
                'BASE_FIELDS': 'base_fields',
                'FIELD_SPECIAL_HANDLING': 'field_special_handling'
            }

            if var_name in mapping_name_map:
                mapping_key = mapping_name_map[var_name]

                # Clean up the values - remove extra quotes from keys AND values
                if isinstance(value, dict):
                    cleaned_value = {}
                    for k, v in value.items():
                        # Remove surrounding quotes from key (they're part of the string)
                        # Handle keys like "'start'" where quotes are embedded
                        if k.startswith("'") and k.endswith("'"):
                            clean_key = k[1:-1]  # Remove surrounding single quotes
                        elif k.startswith('"') and k.endswith('"'):
                            clean_key = k[1:-1]  # Remove surrounding double quotes
                        else:
                            clean_key = k.strip().strip("'\"")
                        # Also clean the value if it's a string with quotes
                        clean_value = v.strip().strip("'\"") if isinstance(v, str) else v
                        cleaned_value[clean_key] = clean_value
                    mappings[mapping_key] = cleaned_value
                elif isinstance(value, list):
                    mappings[mapping_key] = value
                else:
                    mappings[mapping_key] = value
    else:
        # Old format: need to traverse AST
        ast = ast_data.get('ast', {})
        body = ast.get('body', [])

        for statement in body:
            if statement.get('type') == 'ExportNamedDeclaration':
                declaration = statement.get('declaration', {})

                if declaration.get('type') == 'VariableDeclaration':
                    for declarator in declaration.get('declarations', []):
                        if declarator.get('type') == 'VariableDeclarator':
                            id_node = declarator.get('id', {})
                            init_node = declarator.get('init', {})

                            if id_node.get('type') == 'Identifier':
                                var_name = id_node.get('name', '')

                                # Map TypeScript constant names to our mapping keys
                                mapping_name_map = {
                                    'NODE_INTERFACE_MAP': 'node_interface_map',
                                    'TS_TO_PY_TYPE': 'ts_to_py_type',
                                    'TYPE_TO_FIELD': 'type_to_field',
                                    'TYPE_TO_ZOD': 'type_to_zod',
                                    'BRANDED_TYPES': 'branded_types',
                                    'BASE_FIELDS': 'base_fields',
                                    'FIELD_SPECIAL_HANDLING': 'field_special_handling'
                                }

                                if var_name in mapping_name_map:
                                    mapping_key = mapping_name_map[var_name]

                                    # Parse the value based on type
                                    if init_node.get('type') == 'ObjectExpression':
                                        mappings[mapping_key] = parse_object_expression(init_node)
                                    elif init_node.get('type') == 'ArrayExpression':
                                        mappings[mapping_key] = parse_array_expression(init_node)

    # Fix special handling for fields that need proper Python syntax
    if 'field_special_handling' in mappings:
        # Update memory_config and memory_settings with proper names
        if 'person_job' in mappings['field_special_handling']:
            pj = mappings['field_special_handling']['person_job']
            if 'memory_config' in pj:
                pj['memory_config'] = {'special': 'MemoryConfig(**data.get("memory_config")) if data.get("memory_config") else None'}
            if 'memory_settings' in pj:
                pj['memory_settings'] = {'special': 'MemorySettings(**data.get("memory_settings")) if data.get("memory_settings") else None'}

        # Fix enum references to use proper syntax
        if 'code_job' in mappings['field_special_handling']:
            if 'language' in mappings['field_special_handling']['code_job']:
                mappings['field_special_handling']['code_job']['language'] = {'default': 'field(default=SupportedLanguage.python)'}

        if 'api_job' in mappings['field_special_handling']:
            if 'method' in mappings['field_special_handling']['api_job']:
                mappings['field_special_handling']['api_job']['method'] = {'default': 'field(default=HttpMethod.GET)'}

        if 'db' in mappings['field_special_handling']:
            if 'sub_type' in mappings['field_special_handling']['db']:
                mappings['field_special_handling']['db']['sub_type'] = {'default': 'field(default=DBBlockSubType.fixed_prompt)'}

        if 'hook' in mappings['field_special_handling']:
            if 'hook_type' in mappings['field_special_handling']['hook']:
                mappings['field_special_handling']['hook']['hook_type'] = {'default': 'field(default=HookType.shell)'}

    return mappings


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


def extract_zod_schemas(interfaces: list[dict], enums: list[dict], mappings: dict) -> dict:
    """Extract Zod schemas from TypeScript AST data"""
    # Get mappings
    node_interface_map = mappings.get('node_interface_map', {})
    branded_types = mappings.get('branded_types', [])
    type_to_zod = mappings.get('type_to_zod', {})
    base_fields = mappings.get('base_fields', ['label', 'flipped'])

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
            # print(f"Warning: Interface {interface_name} not found")
            continue

        schema_code = generate_interface_schema(interface_data, enum_schemas, type_to_zod, base_fields)

        schemas.append({
            'nodeType': node_type,
            'interfaceName': interface_name,
            'schemaCode': schema_code
        })

    return {
        'schemas': schemas,
        'enum_schemas': enum_schemas,
        'branded_types': branded_types
    }


# ============================================================================
# Field Config Extraction Functions
# ============================================================================

def generate_label(name: str) -> str:
    """Convert snake_case to Title Case"""
    return ' '.join(word.capitalize() for word in name.split('_'))


def get_field_type(name: str, type_text: str, type_to_field: dict | None = None) -> str:
    """Determine the appropriate field type - must match FIELD_TYPES from panel.ts"""
    # Special handling for specific field names
    if name == 'filePath' or name == 'file_path' or name == 'path':
        return 'filepath'

    # File fields that contain 'prompt' should be text fields, not variableTextArea
    if 'file' in name.lower() and 'prompt' in name.lower():
        return 'text'

    if any(keyword in name for keyword in ['prompt', 'expression', 'query']):
        return 'variableTextArea'

    if name == 'code' or name == 'script':
        return 'code'

    if name == 'url':
        return 'url'

    if name == 'max_iteration':
        return 'maxIteration'

    # Check type_to_field mapping
    if type_to_field and type_text in type_to_field:
        return type_to_field[type_text]

    # Default mappings based on type text
    if 'boolean' in type_text:
        return 'checkbox'
    elif 'number' in type_text:
        return 'number'
    elif any(enum_type in type_text for enum_type in ['NodeType', 'HttpMethod', 'SupportedLanguage']):
        return 'select'

    return 'text'


def extract_enum_values(enums: list[dict]) -> dict[str, list[str]]:
    """Extract enum values from AST enum data"""
    enum_values = {}
    for enum in enums:
        name = enum.get('name', '')
        values = []
        for member in enum.get('members', []):
            value = member.get('value', member.get('name', ''))
            values.append(value)
        enum_values[name] = values
    return enum_values


def add_type_specific_props(field_config: dict, name: str, type_text: str, enum_values: dict):
    """Add type-specific properties to field configuration"""
    # Add enum options if applicable
    clean_type = type_text.replace(' | null', '').replace(' | undefined', '').strip()
    if clean_type in enum_values:
        field_config['options'] = enum_values[clean_type]

    # Add placeholder for specific field types
    if field_config['type'] == 'variableTextArea':
        field_config['placeholder'] = f'Enter {name} (supports variables)'
    elif field_config['type'] == 'filepath':
        field_config['placeholder'] = 'path/to/file'


def extract_field_configs(interfaces: list[dict], enums: list[dict], mappings: dict) -> dict:
    """Extract field configurations from TypeScript AST data"""
    # Get mappings
    node_interface_map = mappings.get('node_interface_map', {})
    base_fields = mappings.get('base_fields', ['label', 'flipped'])
    type_to_field = mappings.get('type_to_field', {})

    # Build enum value map
    enum_values = extract_enum_values(enums)

    # Generate field configs for each node type
    node_configs = []

    for node_type, interface_name in node_interface_map.items():
        # Find the interface
        interface_data = None
        for iface in interfaces:
            if iface.get('name') == interface_name:
                interface_data = iface
                break

        if not interface_data:
            continue

        # Extract fields
        fields = []
        for prop in interface_data.get('properties', []):
            name = prop.get('name', '')

            # Skip base fields
            if name in base_fields:
                continue

            type_text = prop.get('type', 'string')
            is_optional = prop.get('optional', False)

            field_config = {
                'name': name,
                'type': get_field_type(name, type_text, type_to_field),
                'label': generate_label(name),
                'required': not is_optional
            }

            # Add type-specific properties
            add_type_specific_props(field_config, name, type_text, enum_values)

            fields.append(field_config)

        node_configs.append({
            'nodeType': node_type,
            'fields': fields
        })

    return {
        'node_configs': node_configs,
        'enum_values': enum_values
    }


def extract_specifications(ast_files: dict) -> list[dict]:
    """Extract node specifications from AST files"""
    specifications = []

    for filepath, content in ast_files.items():
        if '.spec.ts.json' in filepath and 'index.ts.json' not in filepath:
            ast_data = parse_dipeo_output(content)

            # Find specification constants
            for constant in ast_data.get('constants', []):
                name = constant.get('name', '')
                if name.endswith('Spec'):
                    spec_value = constant.get('value', {})
                    # Extract node type from the spec
                    node_type_raw = spec_value.get('nodeType', '')
                    # Remove NodeType. prefix if present
                    if node_type_raw.startswith('NodeType.'):
                        node_type = node_type_raw.replace('NodeType.', '').lower()
                    else:
                        node_type = node_type_raw.lower()

                    specifications.append({
                        'name': name,
                        'nodeType': node_type,
                        'spec': spec_value
                    })

    return specifications


def spec_field_to_zod(field: dict, enum_values: dict) -> str:
    """Convert a specification field to Zod schema"""
    name = field.get('name', '')
    field_type = field.get('type', 'string')
    required = field.get('required', False)
    validation = field.get('validation', {})

    # Map specification types to Zod schemas
    if field_type == 'enum':
        allowed_values = validation.get('allowedValues', [])
        if allowed_values:
            values_str = ', '.join([f"'{v}'" for v in allowed_values])
            zod_type = f"z.enum([{values_str}])"
        else:
            zod_type = 'z.string()'
    elif field_type == 'boolean':
        zod_type = 'z.boolean()'
    elif field_type == 'number':
        zod_type = 'z.number()'
    elif field_type == 'array':
        zod_type = 'z.array(z.any())'
    elif field_type == 'object':
        zod_type = 'z.record(z.string(), z.any())'
    else:
        zod_type = 'z.string()'

    # Add optional modifier if not required
    if not required:
        zod_type = f"{zod_type}.optional()"

    return f"  {name}: {zod_type}"


def extract_zod_from_specs(specifications: list[dict], enum_values: dict) -> dict:
    """Extract Zod schemas from specifications"""
    schemas = []

    for spec_data in specifications:
        node_type = spec_data['nodeType']
        spec = spec_data['spec']
        fields = spec.get('fields', [])

        # Generate Zod properties for each field
        properties = []

        # Add base fields
        properties.append("  label: z.string()")
        properties.append("  flipped: z.boolean().optional()")

        # Add spec fields
        for field in fields:
            prop = spec_field_to_zod(field, enum_values)
            properties.append(prop)

        schema_code = f"z.object({{\n{',\n'.join(properties)}\n}})"

        # Create interface name from node type - match NODE_INTERFACE_MAP format
        # Convert snake_case to PascalCase and add NodeData suffix
        words = node_type.split('_')
        interface_name = ''.join(word.capitalize() for word in words) + 'NodeData'

        schemas.append({
            'nodeType': node_type,
            'interfaceName': interface_name,
            'schemaCode': schema_code
        })

    return {
        'schemas': schemas,
        'enum_schemas': {},
        'branded_types': []
    }


def extract_field_configs_from_specs(specifications: list[dict], enum_values: dict) -> dict:
    """Extract field configurations from specifications"""
    node_configs = []

    for spec_data in specifications:
        node_type = spec_data['nodeType']
        spec = spec_data['spec']
        fields_data = spec.get('fields', [])

        fields = []
        for field in fields_data:
            name = field.get('name', '')
            field_type = field.get('type', 'string')
            required = field.get('required', False)
            ui_config = field.get('uiConfig', {})

            # Determine field type for UI
            if ui_config.get('inputType') == 'select' or field_type == 'enum':
                ui_type = 'select'
            elif ui_config.get('inputType') == 'textarea':
                ui_type = 'variableTextArea'
            elif ui_config.get('inputType') == 'code':
                ui_type = 'code'
            elif field_type == 'boolean':
                ui_type = 'checkbox'
            elif field_type == 'number':
                ui_type = 'number'
            else:
                ui_type = get_field_type(name, field_type)

            field_config = {
                'name': name,
                'type': ui_type,
                'label': field.get('label') or generate_label(name),
                'required': required
            }

            # Add options for select fields
            if ui_type == 'select':
                options = []
                if ui_config.get('options'):
                    # Keep the full option objects with value and label
                    options = ui_config.get('options', [])
                elif field.get('validation', {}).get('allowedValues'):
                    # Convert plain values to option objects
                    allowed_values = field['validation']['allowedValues']
                    options = [{'value': val, 'label': val} for val in allowed_values]
                if options:
                    field_config['options'] = options

            # Add placeholder if specified
            if ui_config.get('placeholder'):
                field_config['placeholder'] = ui_config['placeholder']

            fields.append(field_config)

        node_configs.append({
            'nodeType': node_type,
            'fields': fields
        })

    return {
        'node_configs': node_configs,
        'enum_values': enum_values
    }


def main(inputs: dict) -> dict:
    """Main entry point for unified mappings and Zod schemas extraction."""
    from datetime import datetime

    # First, handle if 'default' is a string (JSON) and parse it
    if 'default' in inputs and isinstance(inputs['default'], str):
        try:
            inputs['default'] = parse_dipeo_output(inputs['default'])
        except json.JSONDecodeError:
            print("Failed to parse JSON from 'default' input")

    # Check if we have multi-file input (new format)
    if 'default' in inputs and isinstance(inputs['default'], dict):
        # Check if it's a multi-file result
        default_data = inputs['default']

        # If it has file paths as keys, find the codegen-mappings.ts.json
        if any(key.endswith('.json') for key in default_data):
            # Multi-file format
            mappings = None
            node_interface_map = {}
            all_interfaces = []
            all_enums = []

            # First extract mappings from mappings.ts.json
            for filepath, content in default_data.items():
                if 'mappings.ts.json' in filepath or 'codegen-mappings' in filepath:
                    ast_data = parse_dipeo_output(content)
                    mappings = extract_mappings(ast_data)
                    break

            # Then extract NODE_INTERFACE_MAP from node-interface-map.ts.json
            for filepath, content in default_data.items():
                if 'node-interface-map.ts.json' in filepath:
                    ast_data = parse_dipeo_output(content)
                    # Extract NODE_INTERFACE_MAP from this file
                    for constant in ast_data.get('constants', []):
                        if constant.get('name') == 'NODE_INTERFACE_MAP':
                            value = constant.get('value', {})
                            # Clean up the values - remove extra quotes from keys AND values
                            for k, v in value.items():
                                # Remove surrounding quotes from key (they're part of the string)
                                # Handle keys like "'start'" where quotes are embedded
                                if k.startswith("'") and k.endswith("'"):
                                    clean_key = k[1:-1]  # Remove surrounding single quotes
                                elif k.startswith('"') and k.endswith('"'):
                                    clean_key = k[1:-1]  # Remove surrounding double quotes
                                else:
                                    clean_key = k.strip().strip("'\"")
                                # Also clean the value if it's a string with quotes
                                clean_value = v.strip().strip("'\"") if isinstance(v, str) else v
                                node_interface_map[clean_key] = clean_value
                            break

            # Collect all interfaces and enums from AST files
            for filepath, content in default_data.items():
                if filepath == 'default':
                    continue
                # Extract filename from path
                filename = filepath.split('/')[-1] if '/' in filepath else filepath

                if filename.endswith('.data.ts.json') or filename.endswith('.ts.json'):
                    # This is a node data file or other TypeScript file
                    ast_data = parse_dipeo_output(content)
                    interfaces = ast_data.get('interfaces', [])
                    enums = ast_data.get('enums', [])
                    all_interfaces.extend(interfaces)
                    all_enums.extend(enums)

            # Merge the results
            if mappings:
                mappings['node_interface_map'] = node_interface_map
            else:
                # If no mappings found, create with NODE_INTERFACE_MAP
                print("No mappings file found, using NODE_INTERFACE_MAP only")
                mappings = {
                    'node_interface_map': node_interface_map,
                    'base_fields': ['label', 'flipped'],
                    'type_to_field': {},
                    'ts_to_py_type': {},
                    'type_to_zod': {},
                    'branded_types': [],
                    'field_special_handling': {}
                }

            # Try interface-based extraction first
            if all_interfaces:
                print(f"Found {len(all_interfaces)} interfaces, trying interface-based extraction")
                # Generate Zod schemas from interfaces
                zod_result = extract_zod_schemas(all_interfaces, all_enums, mappings)
                # Generate field configs from interfaces
                field_configs_result = extract_field_configs(all_interfaces, all_enums, mappings)

                # Check if we actually got any node schemas
                if not zod_result.get('schemas'):
                    print("No node schemas found from interfaces, falling back to specifications...")
                    all_interfaces = []  # Force specification extraction

            # If no interfaces or no schemas found, try specifications
            if not all_interfaces or not zod_result.get('schemas'):
                print("Checking for specifications...")
                # Extract specifications
                specifications = extract_specifications(default_data)

                if specifications:
                    print(f"Found {len(specifications)} specifications, using specification-based extraction")
                    # Extract enum values
                    enum_values = extract_enum_values(all_enums)

                    # Generate Zod schemas from specifications
                    zod_result = extract_zod_from_specs(specifications, enum_values)

                    # Generate field configs from specifications
                    field_configs_result = extract_field_configs_from_specs(specifications, enum_values)
                else:
                    print("WARNING: No specifications found either")
                    # Return empty results if nothing worked
                    if not all_interfaces:
                        zod_result = {
                            'schemas': [],
                            'enum_schemas': {},
                            'branded_types': []
                        }
                        field_configs_result = {
                            'node_configs': [],
                            'enum_values': {}
                        }

            # Return combined result
            return {
                'mappings': mappings,
                'zod': zod_result,
                'field_configs': field_configs_result,
                'now': datetime.now().isoformat()
            }
        else:
            # Single AST data
            mappings = extract_mappings(default_data)
            # For single file, we don't have interfaces/enums to generate Zod schemas
            return {
                'mappings': mappings,
                'now': datetime.now().isoformat()
            }
    else:
        # Legacy format
        print("Processing as legacy format")
        raw_data = inputs.get('default', {})

        # Handle wrapped AST format (when loaded from mappings.ts.json)
        if isinstance(raw_data, dict) and 'ast' in raw_data:
            # Extract the AST from the wrapper
            ast_data = raw_data['ast']
            print(f"Extracted AST from wrapped format, keys: {list(ast_data.keys()) if isinstance(ast_data, dict) else 'not a dict'}")
        else:
            # Use as-is if not wrapped
            ast_data = raw_data
            print(f"Using raw data as AST, type: {type(ast_data)}")

        # Validate that we have a dict before passing to extract_mappings
        if not isinstance(ast_data, dict):
            print(f"Warning: ast_data is not a dict, it's {type(ast_data)}. Converting to empty dict.")
            ast_data = {}

        mappings = extract_mappings(ast_data)
        return {
            'mappings': mappings,
            'now': datetime.now().isoformat()
        }
