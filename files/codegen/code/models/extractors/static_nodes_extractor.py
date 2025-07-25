"""Extract static node data from TypeScript AST."""

from datetime import datetime
from typing import Dict, List, Any, Optional
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from shared.node_mappings import get_loader, get_python_type


# Special field configurations that can't be derived from specs
FIELD_SPECIAL_HANDLING = {
    'person_job': {
        'person': {'py_name': 'person_id'},
        'first_only_prompt': {'default': '""'},
        'max_iteration': {'default': '1'},
        'memory_config': {'special': 'MemoryConfig(**data.get("memory_config")) if data.get("memory_config") else None'},
        'memory_settings': {'special': 'MemorySettings(**data.get("memory_settings")) if data.get("memory_settings") else None'},
        'tools': {'special': '[ToolConfig(**tool) if isinstance(tool, dict) else tool for tool in data.get("tools", [])] if data.get("tools") else None'}
    },
    'start': {
        'custom_data': {'default': 'field(default_factory=dict)'},
        'output_data_structure': {'default': 'field(default_factory=dict)'}
    },
    'endpoint': {
        'save_to_file': {'default': 'False'}
    },
    'condition': {
        'condition_type': {'default': '""'}
    },
    'code_job': {
        'language': {'default': 'SupportedLanguage.python'}
    },
    'api_job': {
        'url': {'default': '""'},
        'method': {'default': 'HttpMethod.GET'}
    },
    'db': {
        'sub_type': {'default': 'DBBlockSubType.fixed_prompt'},
        'operation': {'default': '""'}
    },
    'user_response': {
        'prompt': {'default': '""'},
        'timeout': {'default': '60'}
    },
    'notion': {
        'operation': {'default': 'NotionOperation.read_page'}
    },
    'hook': {
        'hook_type': {'default': 'HookType.shell'},
        'config': {'default': 'field(default_factory=dict)'}
    },
    'template_job': {
        'template_type': {'default': '"jinja2"'},
        'merge_source': {'default': '"default"'}
    },
    'json_schema_validator': {
        'strict_mode': {'default': 'False'},
        'error_on_extra': {'default': 'False'}
    },
    'typescript_ast': {
        'extractPatterns': {'default': 'field(default_factory=lambda: ["interface", "type", "enum"])'},
        'includeJSDoc': {'default': 'False'},
        'parseMode': {'default': '"module"'}
    },
    'sub_diagram': {
        'batch': {'default': 'False'},
        'batch_input_key': {'default': '"items"'},
        'batch_parallel': {'default': 'True'}
    }
}


def extract_static_nodes_data(ast_data: dict) -> dict:
    """Extract static node data from TypeScript AST"""
    interfaces = ast_data.get('interfaces', [])
    enums = ast_data.get('enums', [])
    
    loader = get_loader()
    node_interface_map = loader.get_node_interface_map()
    
    # Generate node classes data
    node_classes = []
    
    for node_type, interface_name in node_interface_map.items():
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
        
        # Get special handling for this node type
        node_special = FIELD_SPECIAL_HANDLING.get(node_type, {})
        
        # Process fields
        fields = []
        for prop in interface_data.get('properties', []):
            ts_name = prop.get('name')
            
            # Skip base fields
            if ts_name in loader.get_base_fields():
                continue
            
            # Get special handling for this field
            field_special = node_special.get(ts_name, {})
            
            # Determine Python name
            py_name = field_special.get('py_name', ts_name)
            
            ts_type = prop.get('type', 'Any')
            is_optional = prop.get('optional', False)
            py_type = get_python_type(ts_type, is_optional)
            
            field_data = {
                'ts_name': ts_name,
                'py_name': py_name,
                'py_type': py_type,
                'has_default': False,
                'default_value': None,
                'is_field_default': False,
                'special_handling': field_special.get('special')
            }
            
            # Handle default values
            if 'default' in field_special:
                field_data['has_default'] = True
                field_data['default_value'] = field_special['default']
                field_data['is_field_default'] = 'field(' in field_special['default']
            elif is_optional:
                field_data['has_default'] = True
                field_data['default_value'] = 'None'
            elif not is_optional and 'Dict[' in py_type and 'Optional[' not in py_type:
                field_data['has_default'] = True
                field_data['default_value'] = 'field(default_factory=dict)'
                field_data['is_field_default'] = True
            elif not is_optional and 'List[' in py_type and 'Optional[' not in py_type:
                field_data['has_default'] = True
                field_data['default_value'] = 'field(default_factory=list)'
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