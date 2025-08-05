"""Extract codegen mappings from TypeScript AST."""

import json
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
                
                # Clean up the values - remove extra quotes from keys
                if isinstance(value, dict):
                    cleaned_value = {}
                    for k, v in value.items():
                        # Remove surrounding quotes if present
                        clean_key = k.strip("'\"")
                        cleaned_value[clean_key] = v
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
        
        if 'notion' in mappings['field_special_handling']:
            if 'operation' in mappings['field_special_handling']['notion']:
                mappings['field_special_handling']['notion']['operation'] = {'default': 'field(default=NotionOperation.read_page)'}
        
        if 'hook' in mappings['field_special_handling']:
            if 'hook_type' in mappings['field_special_handling']['hook']:
                mappings['field_special_handling']['hook']['hook_type'] = {'default': 'field(default=HookType.shell)'}
    
    return mappings


def main(inputs: dict) -> dict:
    """Main entry point for mappings extraction."""
    # Debug logging
    print(f"extract_mappings received input keys: {list(inputs.keys())}")
    
    # Check if we have multi-file input (new format)
    if 'default' in inputs and isinstance(inputs['default'], dict):
        # Check if it's a multi-file result
        default_data = inputs['default']
        print(f"Default data keys: {list(default_data.keys())}")
        
        # If it has file paths as keys, find the codegen-mappings.ts.json
        if any(key.endswith('.json') for key in default_data.keys()):
            # Multi-file format
            mappings = None
            node_interface_map = {}
            
            # First extract mappings from mappings.ts.json
            for filepath, content in default_data.items():
                if 'mappings.ts.json' in filepath or 'codegen-mappings' in filepath:
                    print(f"Found mappings file: {filepath}")
                    ast_data = content if isinstance(content, dict) else json.loads(content)
                    mappings = extract_mappings(ast_data)
                    break
            
            # Then extract NODE_INTERFACE_MAP from node-interface-map.ts.json
            for filepath, content in default_data.items():
                if 'node-interface-map.ts.json' in filepath:
                    print(f"Found node-interface-map file: {filepath}")
                    ast_data = content if isinstance(content, dict) else json.loads(content)
                    # Extract NODE_INTERFACE_MAP from this file
                    for constant in ast_data.get('constants', []):
                        if constant.get('name') == 'NODE_INTERFACE_MAP':
                            value = constant.get('value', {})
                            # Clean up the values - remove extra quotes from keys
                            for k, v in value.items():
                                clean_key = k.strip("'\"")
                                node_interface_map[clean_key] = v
                            print(f"Extracted NODE_INTERFACE_MAP with {len(node_interface_map)} entries")
                            break
            
            # Merge the results
            if mappings:
                mappings['node_interface_map'] = node_interface_map
                print(f"Final node_interface_map has {len(mappings.get('node_interface_map', {}))} entries")
                return mappings
            else:
                # If no mappings found, return with NODE_INTERFACE_MAP
                print("No mappings file found, returning NODE_INTERFACE_MAP only")
                return {
                    'node_interface_map': node_interface_map,
                    'base_fields': ['label', 'flipped'],
                    'type_to_field': {}
                }
        else:
            # Single AST data
            print("Processing as single AST data")
            return extract_mappings(default_data)
    else:
        # Legacy format
        print("Processing as legacy format")
        ast_data = inputs.get('default', {})
        return extract_mappings(ast_data)