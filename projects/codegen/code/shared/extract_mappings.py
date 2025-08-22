"""Unified extractor for codegen mappings, Zod schemas, and field configs from TypeScript AST."""

import json
import re
from typing import Dict, Any, List, Union


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


def build_enum_schemas(enums: List[Dict[str, Any]]) -> Dict[str, str]:
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


def get_zod_type(type_text: str, enum_schemas: Dict[str, str], type_to_zod: Dict[str, str]) -> str:
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


def generate_property_schema(prop: Dict[str, Any], enum_schemas: Dict[str, str], type_to_zod: Dict[str, str]) -> str:
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


def generate_interface_schema(interface_data: Dict[str, Any], enum_schemas: Dict[str, str], type_to_zod: Dict[str, str], base_fields: List[str]) -> str:
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


def extract_zod_schemas(interfaces: List[Dict], enums: List[Dict], mappings: Dict) -> Dict:
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
            print(f"Warning: Interface {interface_name} not found")
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


def get_field_type(name: str, type_text: str, type_to_field: dict = None) -> str:
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


def extract_enum_values(enums: List[Dict]) -> Dict[str, List[str]]:
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


def extract_field_configs(interfaces: List[Dict], enums: List[Dict], mappings: Dict) -> Dict:
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


def main(inputs: dict) -> dict:
    """Main entry point for unified mappings and Zod schemas extraction."""
    from datetime import datetime
    
    # Check if we have multi-file input (new format)
    if 'default' in inputs and isinstance(inputs['default'], dict):
        # Check if it's a multi-file result
        default_data = inputs['default']

        # If it has file paths as keys, find the codegen-mappings.ts.json
        if any(key.endswith('.json') for key in default_data.keys()):
            # Multi-file format
            mappings = None
            node_interface_map = {}
            all_interfaces = []
            all_enums = []
            
            # First extract mappings from mappings.ts.json
            for filepath, content in default_data.items():
                if 'mappings.ts.json' in filepath or 'codegen-mappings' in filepath:
                    ast_data = content if isinstance(content, dict) else json.loads(content)
                    mappings = extract_mappings(ast_data)
                    break
            
            # Then extract NODE_INTERFACE_MAP from node-interface-map.ts.json
            for filepath, content in default_data.items():
                if 'node-interface-map.ts.json' in filepath:
                    ast_data = content if isinstance(content, dict) else json.loads(content)
                    # Extract NODE_INTERFACE_MAP from this file
                    for constant in ast_data.get('constants', []):
                        if constant.get('name') == 'NODE_INTERFACE_MAP':
                            value = constant.get('value', {})
                            # Clean up the values - remove extra quotes from keys AND values
                            for k, v in value.items():
                                # Remove surrounding quotes from key (they're part of the string)
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
                    ast_data = content if isinstance(content, dict) else json.loads(content)
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
            
            # Generate Zod schemas
            zod_result = extract_zod_schemas(all_interfaces, all_enums, mappings)
            
            # Generate field configs
            field_configs_result = extract_field_configs(all_interfaces, all_enums, mappings)
            
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
        ast_data = inputs.get('default', {})
        mappings = extract_mappings(ast_data)
        return {
            'mappings': mappings,
            'now': datetime.now().isoformat()
        }