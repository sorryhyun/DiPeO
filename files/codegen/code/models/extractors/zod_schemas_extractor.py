"""Extract Zod schemas from TypeScript AST data."""

import re
from typing import Dict, List, Any


# Node type to interface mapping
NODE_INTERFACE_MAP = {
    'start': 'StartNodeData',
    'person_job': 'PersonJobNodeData',
    'person_batch_job': 'PersonBatchJobNodeData',
    'condition': 'ConditionNodeData',
    'endpoint': 'EndpointNodeData',
    'db': 'DBNodeData',
    'job': 'JobNodeData',
    'code_job': 'CodeJobNodeData',
    'api_job': 'ApiJobNodeData',
    'user_response': 'UserResponseNodeData',
    'notion': 'NotionNodeData',
    'hook': 'HookNodeData',
    'template_job': 'TemplateJobNodeData',
    'json_schema_validator': 'JsonSchemaValidatorNodeData',
    'typescript_ast': 'TypescriptAstNodeData',
    'sub_diagram': 'SubDiagramNodeData'
}

# Type to Zod mapping
TYPE_TO_ZOD = {
    'string': 'z.string()',
    'number': 'z.number()',
    'boolean': 'z.boolean()',
    'any': 'z.any()',
    'PersonID': 'PersonID',
    'NodeID': 'NodeID',
    'HandleID': 'HandleID',
    'ArrowID': 'ArrowID',
    'SupportedLanguage': 'SupportedLanguage',
    'HttpMethod': 'HttpMethod',
    'DBBlockSubType': 'DBBlockSubType',
    'HookType': 'HookType',
    'ForgettingMode': 'ForgettingMode',
    'NotionOperation': 'NotionOperation',
    'HookTriggerMode': 'HookTriggerMode',
    'ContentType': 'ContentType',
    'NodeType': 'NodeType'
}

# Branded types that shouldn't be generated as schemas
BRANDED_TYPES = ['PersonID', 'NodeID', 'HandleID', 'ArrowID', 'NodeType',
                 'SupportedLanguage', 'HttpMethod', 'DBBlockSubType', 
                 'HookType', 'ForgettingMode', 'NotionOperation',
                 'HookTriggerMode', 'ContentType']

# Base fields to skip
BASE_FIELDS = ['label', 'flipped']


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


def get_zod_type(type_text: str, enum_schemas: Dict[str, str]) -> str:
    """Convert TypeScript type to Zod schema"""
    # Handle union types with null/undefined
    clean_type = type_text.replace(' | null', '').replace(' | undefined', '').strip()
    
    # Check for enum schemas
    if clean_type in enum_schemas:
        return enum_schemas[clean_type]
    
    # Check for type mapping
    if clean_type in TYPE_TO_ZOD:
        zod_type = TYPE_TO_ZOD[clean_type]
        # For branded types and enums, reference them directly
        if zod_type == clean_type:
            return zod_type
        return zod_type
    
    # Handle arrays
    if clean_type.endswith('[]'):
        element_type = clean_type[:-2]
        element_zod = get_zod_type(element_type, enum_schemas)
        return f"z.array({element_zod})"
    
    # Handle Record types
    if clean_type.startswith('Record<'):
        match = re.match(r'Record<(.+),\s*(.+)>', clean_type)
        if match:
            value_type = match.group(2).strip()
            value_zod = get_zod_type(value_type, enum_schemas)
            return f"z.record(z.string(), {value_zod})"
    
    # Default to z.any()
    return 'z.any()'


def generate_property_schema(prop: Dict[str, Any], enum_schemas: Dict[str, str]) -> str:
    """Generate Zod schema for a property"""
    name = prop.get('name', '')
    type_text = prop.get('type', 'any')
    is_optional = prop.get('optional', False)
    
    zod_schema = get_zod_type(type_text, enum_schemas)
    
    # Handle optional
    if is_optional:
        zod_schema = f"{zod_schema}.optional()"
    
    # Handle nullable
    if ' | null' in type_text:
        zod_schema = f"{zod_schema}.nullable()"
    
    return f"  {name}: {zod_schema}"


def generate_interface_schema(interface_data: Dict[str, Any], enum_schemas: Dict[str, str]) -> str:
    """Generate Zod schema for an interface"""
    properties = []
    
    for prop in interface_data.get('properties', []):
        name = prop.get('name', '')
        
        # Skip base fields
        if name in BASE_FIELDS:
            continue
        
        prop_schema = generate_property_schema(prop, enum_schemas)
        properties.append(prop_schema)
    
    return f"z.object({{\n{',\n'.join(properties)}\n}})"


def extract_zod_schemas(ast_data: dict) -> dict:
    """Extract Zod schemas from TypeScript AST data"""
    interfaces = ast_data.get('interfaces', [])
    enums = ast_data.get('enums', [])
    
    # Build enum schemas
    enum_schemas = build_enum_schemas(enums)
    
    # Generate schemas for each node type
    schemas = []
    
    for node_type, interface_name in NODE_INTERFACE_MAP.items():
        # Find the interface
        interface_data = None
        for iface in interfaces:
            if iface.get('name') == interface_name:
                interface_data = iface
                break
        
        if not interface_data:
            print(f"Warning: Interface {interface_name} not found")
            continue
        
        schema_code = generate_interface_schema(interface_data, enum_schemas)
        
        schemas.append({
            'nodeType': node_type,
            'interfaceName': interface_name,
            'schemaCode': schema_code
        })
    
    print(f"Generated Zod schemas for {len(schemas)} node types")
    
    return {
        'schemas': schemas,
        'enum_schemas': enum_schemas,
        'branded_types': BRANDED_TYPES
    }


def main(inputs: dict) -> dict:
    """Main entry point for Zod schemas extraction"""
    ast_data = inputs.get('default', {})
    return extract_zod_schemas(ast_data)