"""Extract static node data from TypeScript AST."""

from datetime import datetime
from typing import Dict, List, Any, Optional


# Node type to interface mapping with field configurations
NODE_DATA_MAP = {
    'StartNodeData': {'node_type': 'start', 'fields': [
        {'ts_name': 'custom_data', 'py_name': 'custom_data', 'default': 'field(default_factory=dict)'},
        {'ts_name': 'output_data_structure', 'py_name': 'output_data_structure', 'default': 'field(default_factory=dict)'},
        {'ts_name': 'trigger_mode', 'py_name': 'trigger_mode'},
        {'ts_name': 'hook_event', 'py_name': 'hook_event'},
        {'ts_name': 'hook_filters', 'py_name': 'hook_filters'}
    ]},
    'EndpointNodeData': {'node_type': 'endpoint', 'fields': [
        {'ts_name': 'save_to_file', 'py_name': 'save_to_file', 'default': 'False'},
        {'ts_name': 'file_name', 'py_name': 'file_name'}
    ]},
    'PersonJobNodeData': {'node_type': 'person_job', 'fields': [
        {'ts_name': 'person', 'py_name': 'person_id'},
        {'ts_name': 'first_only_prompt', 'py_name': 'first_only_prompt', 'default': '""'},
        {'ts_name': 'default_prompt', 'py_name': 'default_prompt'},
        {'ts_name': 'max_iteration', 'py_name': 'max_iteration', 'default': '1'},
        {'ts_name': 'memory_config', 'py_name': 'memory_config', 'special': 'MemoryConfig(**data.get("memory_config")) if data.get("memory_config") else None'},
        {'ts_name': 'memory_settings', 'py_name': 'memory_settings', 'special': 'MemorySettings(**data.get("memory_settings")) if data.get("memory_settings") else None'},
        {'ts_name': 'tools', 'py_name': 'tools', 'special': '[ToolConfig(**tool) if isinstance(tool, dict) else tool for tool in data.get("tools", [])] if data.get("tools") else None'}
    ]},
    'ConditionNodeData': {'node_type': 'condition', 'fields': [
        {'ts_name': 'condition_type', 'py_name': 'condition_type', 'default': '""'},
        {'ts_name': 'expression', 'py_name': 'expression'},
        {'ts_name': 'node_indices', 'py_name': 'node_indices'}
    ]},
    'CodeJobNodeData': {'node_type': 'code_job', 'fields': [
        {'ts_name': 'language', 'py_name': 'language', 'default': 'SupportedLanguage.python'},
        {'ts_name': 'filePath', 'py_name': 'filePath'},
        {'ts_name': 'code', 'py_name': 'code'},
        {'ts_name': 'functionName', 'py_name': 'functionName'},
        {'ts_name': 'timeout', 'py_name': 'timeout'}
    ]},
    'ApiJobNodeData': {'node_type': 'api_job', 'fields': [
        {'ts_name': 'url', 'py_name': 'url', 'default': '""'},
        {'ts_name': 'method', 'py_name': 'method', 'default': 'HttpMethod.GET'},
        {'ts_name': 'headers', 'py_name': 'headers'},
        {'ts_name': 'params', 'py_name': 'params'},
        {'ts_name': 'body', 'py_name': 'body'},
        {'ts_name': 'timeout', 'py_name': 'timeout'},
        {'ts_name': 'auth_type', 'py_name': 'auth_type'},
        {'ts_name': 'auth_config', 'py_name': 'auth_config'}
    ]},
    'DBNodeData': {'node_type': 'db', 'fields': [
        {'ts_name': 'file', 'py_name': 'file'},
        {'ts_name': 'collection', 'py_name': 'collection'},
        {'ts_name': 'sub_type', 'py_name': 'sub_type', 'default': 'DBBlockSubType.fixed_prompt'},
        {'ts_name': 'operation', 'py_name': 'operation', 'default': '""'},
        {'ts_name': 'query', 'py_name': 'query'},
        {'ts_name': 'data', 'py_name': 'data'},
        {'ts_name': 'source_details', 'py_name': 'source_details'}
    ]},
    'UserResponseNodeData': {'node_type': 'user_response', 'fields': [
        {'ts_name': 'prompt', 'py_name': 'prompt', 'default': '""'},
        {'ts_name': 'timeout', 'py_name': 'timeout', 'default': '60'}
    ]},
    'NotionNodeData': {'node_type': 'notion', 'fields': [
        {'ts_name': 'operation', 'py_name': 'operation', 'default': 'NotionOperation.read_page'},
        {'ts_name': 'page_id', 'py_name': 'page_id'},
        {'ts_name': 'database_id', 'py_name': 'database_id'}
    ]},
    'HookNodeData': {'node_type': 'hook', 'fields': [
        {'ts_name': 'hook_type', 'py_name': 'hook_type', 'default': 'HookType.shell'},
        {'ts_name': 'config', 'py_name': 'config', 'default': 'field(default_factory=dict)'},
        {'ts_name': 'timeout', 'py_name': 'timeout'},
        {'ts_name': 'retry_count', 'py_name': 'retry_count'},
        {'ts_name': 'retry_delay', 'py_name': 'retry_delay'}
    ]},
    'TemplateJobNodeData': {'node_type': 'template_job', 'fields': [
        {'ts_name': 'template_path', 'py_name': 'template_path'},
        {'ts_name': 'template_content', 'py_name': 'template_content'},
        {'ts_name': 'template_type', 'py_name': 'template_type', 'default': '"jinja2"'},
        {'ts_name': 'output_path', 'py_name': 'output_path'},
        {'ts_name': 'variables', 'py_name': 'variables'},
        {'ts_name': 'merge_source', 'py_name': 'merge_source', 'default': '"default"'}
    ]},
    'JsonSchemaValidatorNodeData': {'node_type': 'json_schema_validator', 'fields': [
        {'ts_name': 'schema_path', 'py_name': 'schema_path'},
        {'ts_name': 'schema', 'py_name': 'schema'},
        {'ts_name': 'data_path', 'py_name': 'data_path'},
        {'ts_name': 'strict_mode', 'py_name': 'strict_mode', 'default': 'False'},
        {'ts_name': 'error_on_extra', 'py_name': 'error_on_extra', 'default': 'False'}
    ]},
    'TypescriptAstNodeData': {'node_type': 'typescript_ast', 'fields': [
        {'ts_name': 'source', 'py_name': 'source'},
        {'ts_name': 'extractPatterns', 'py_name': 'extractPatterns', 'default': 'field(default_factory=lambda: ["interface", "type", "enum"])'},
        {'ts_name': 'includeJSDoc', 'py_name': 'includeJSDoc', 'default': 'False'},
        {'ts_name': 'parseMode', 'py_name': 'parseMode', 'default': '"module"'}
    ]},
    'SubDiagramNodeData': {'node_type': 'sub_diagram', 'fields': [
        {'ts_name': 'diagram_name', 'py_name': 'diagram_name'},
        {'ts_name': 'diagram_format', 'py_name': 'diagram_format'},
        {'ts_name': 'diagram_data', 'py_name': 'diagram_data'},
        {'ts_name': 'batch', 'py_name': 'batch', 'default': 'False'},
        {'ts_name': 'batch_input_key', 'py_name': 'batch_input_key', 'default': '"items"'},
        {'ts_name': 'batch_parallel', 'py_name': 'batch_parallel', 'default': 'True'}
    ]}
}

# Type mappings from TypeScript to Python
TS_TO_PY_TYPE = {
    'string': 'str',
    'number': 'int',
    'boolean': 'bool',
    'PersonID': 'Optional[PersonID]',
    'MemoryConfig': 'Optional[MemoryConfig]',
    'MemorySettings': 'Optional[MemorySettings]',
    'ToolConfig[]': 'Optional[List[ToolConfig]]',
    'string[]': 'Optional[List[str]]',
    'Record<string, any>': 'Dict[str, Any]',
    'Record<string, string>': 'Dict[str, str]',
    'any': 'Any',
    'HookTriggerMode': 'Optional[HookTriggerMode]',
    'SupportedLanguage': 'SupportedLanguage',
    'HttpMethod': 'HttpMethod',
    'DBBlockSubType': 'DBBlockSubType',
    'NotionOperation': 'NotionOperation',
    'HookType': 'HookType',
    'DiagramFormat': 'DiagramFormat'
}


def get_python_type(ts_type: str, is_optional: bool) -> str:
    """Convert TypeScript type to Python type"""
    # Clean type
    clean_type = ts_type.replace(' | null', '').replace(' | undefined', '').strip()
    
    # Handle string literal unions
    if "'" in clean_type or '"' in clean_type and '|' in clean_type:
        literals = []
        for lit in clean_type.split('|'):
            cleaned = lit.strip().replace("'", '').replace('"', '')
            literals.append(f'"{cleaned}"')
        literal_type = f"Literal[{', '.join(literals)}]"
        return f"Optional[{literal_type}]" if is_optional else literal_type
    
    # Check mapping
    if clean_type in TS_TO_PY_TYPE:
        return TS_TO_PY_TYPE[clean_type]
    
    # Handle arrays
    if clean_type.endswith('[]'):
        inner_type = clean_type[:-2]
        inner_py = get_python_type(inner_type, False)
        list_type = f"List[{inner_py}]"
        return f"Optional[{list_type}]" if is_optional else list_type
    
    # Handle Record types
    if clean_type.startswith('Record<'):
        return 'Dict[str, Any]'
    
    # Handle optional
    if is_optional and not clean_type.startswith('Optional['):
        return f"Optional[{clean_type}]"
    
    return clean_type


def extract_static_nodes_data(ast_data: dict) -> dict:
    """Extract static node data from TypeScript AST"""
    interfaces = ast_data.get('interfaces', [])
    enums = ast_data.get('enums', [])
    
    # Generate node classes data
    node_classes = []
    
    for interface_name, mapping in NODE_DATA_MAP.items():
        # Find interface
        interface_data = None
        for iface in interfaces:
            if iface.get('name') == interface_name:
                interface_data = iface
                break
        
        if not interface_data:
            print(f"Warning: Interface {interface_name} not found")
            continue
        
        class_name = interface_name.replace('NodeData', 'Node')
        node_type = mapping['node_type']
        
        # Process fields
        fields = []
        for field_map in mapping['fields']:
            ts_name = field_map['ts_name']
            py_name = field_map['py_name']
            
            # Find property in interface
            prop = None
            for p in interface_data.get('properties', []):
                if p.get('name') == ts_name:
                    prop = p
                    break
            
            if not prop:
                continue
            
            ts_type = prop.get('type', 'Any')
            is_optional = prop.get('optional', False)
            py_type = get_python_type(ts_type, is_optional)
            
            field_data = {
                'ts_name': ts_name,
                'py_name': py_name,
                'py_type': py_type,
                'has_default': 'default' in field_map,
                'default_value': field_map.get('default'),
                'is_field_default': 'field(' in field_map.get('default', ''),
                'special_handling': field_map.get('special')
            }
            
            # Handle special cases
            if is_optional and not field_data['has_default']:
                field_data['default_value'] = 'None'
                field_data['has_default'] = True
            elif not is_optional and 'Dict[' in py_type and not 'Optional[' in py_type and not field_data['has_default']:
                field_data['default_value'] = 'field(default_factory=dict)'
                field_data['has_default'] = True
                field_data['is_field_default'] = True
            elif not is_optional and 'List[' in py_type and not 'Optional[' in py_type and not field_data['has_default']:
                field_data['default_value'] = 'field(default_factory=list)'
                field_data['has_default'] = True
                field_data['is_field_default'] = True
            
            fields.append(field_data)
        
        node_classes.append({
            'class_name': class_name,
            'node_type': node_type,
            'fields': fields
        })
    
    print(f"Generated {len(node_classes)} node classes")
    
    return {
        'node_classes': node_classes,
        'now': datetime.now().isoformat()
    }


def main(inputs: dict) -> dict:
    """Main entry point for static nodes extraction"""
    ast_data = inputs.get('default', {})
    return extract_static_nodes_data(ast_data)