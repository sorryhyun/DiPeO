"""Generate static nodes from parsed TypeScript data."""
import json
from datetime import datetime
from typing import Any, Dict, List

# Import type transformer from infrastructure
import sys
import os
sys.path.append(os.environ.get('DIPEO_BASE_DIR', '/home/soryhyun/DiPeO'))
from dipeo.infrastructure.codegen.parsers.typescript.type_transformer import map_ts_type_to_python


def extract_specs_from_combined_data(node_data_input: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """Extract specs data from the combined input that includes both data and spec files."""
    specs_by_node_type = {}
    
    # Handle wrapped inputs
    if 'default' in node_data_input and isinstance(node_data_input['default'], dict):
        glob_results = node_data_input['default']
    else:
        glob_results = node_data_input
    
    
    for filepath, ast_data in glob_results.items():
        # Skip special keys
        if filepath in ['default', 'inputs', 'node_id', 'node_data']:
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
                    node_type = node_type.replace('-', '_')
                    
                    # Create field lookup by name for easy access
                    fields_by_name = {}
                    for field in spec_value.get('fields', []):
                        field_name = field.get('name')
                        if field_name:
                            fields_by_name[field_name] = field
                    
                    specs_by_node_type[node_type] = {
                        'spec': spec_value,
                        'fields_by_name': fields_by_name
                    }
    
    return specs_by_node_type


def get_python_type(ts_type: str, is_optional: bool, ts_to_py_type: dict) -> str:
    """Convert TypeScript type to Python type using infrastructure's type transformer"""
    # Clean type
    clean_type = ts_type.replace(' | null', '').replace(' | undefined', '').strip()
    
    # Check custom mapping first (for project-specific types)
    if clean_type in ts_to_py_type:
        mapped_type = ts_to_py_type[clean_type]
        # Handle optional wrapping for mapped types
        if is_optional and not mapped_type.startswith('Optional['):
            return f"Optional[{mapped_type}]"
        return mapped_type
    
    # Handle special cases that need custom processing
    
    # First check if this is a complex object type (has TypeScript object syntax)
    # These should be converted to Dict[str, Any]
    if (clean_type.startswith('{') or 
        '/**' in clean_type or '//' in clean_type or
        ('\n' in clean_type and ':' in clean_type)):
        # This is a TypeScript object type with comments or multiline definition
        dict_type = 'Dict[str, Any]'
        return f"Optional[{dict_type}]" if is_optional else dict_type
    
    # Handle string literal unions (but not object types)
    if ("'" in clean_type or '"' in clean_type) and '|' in clean_type and not clean_type.startswith('{'):
        # Only process as literal union if it's not an object type
        # and doesn't contain TypeScript comments
        if '/**' not in clean_type and '//' not in clean_type:
            literals = []
            for lit in clean_type.split('|'):
                cleaned = lit.strip().replace("'", '').replace('"', '')
                literals.append(f'"{cleaned}"')
            literal_type = f"Literal[{', '.join(literals)}]"
            return f"Optional[{literal_type}]" if is_optional else literal_type
    
    # Use infrastructure's type transformer for standard types
    try:
        python_type = map_ts_type_to_python(clean_type)
        
        # Special handling for 'number' type - default to int for DiPeO
        if clean_type == 'number':
            python_type = 'int'
        
        # Handle optional wrapping
        if is_optional and python_type != 'None':
            # Check if already wrapped in Optional or Union
            if not (python_type.startswith('Optional[') or python_type.startswith('Union[')):
                return f"Optional[{python_type}]"
        
        return python_type
    except Exception:
        # Fallback for complex types the infrastructure can't handle
        
        # If nothing matched, return the original type (might be a custom type)
        # Handle optional wrapping for remaining types
        if is_optional and not clean_type.startswith('Optional['):
            return f"Optional[{clean_type}]"
        
        return clean_type


def extract_static_nodes_data(ast_data: dict, mappings: dict, specs_by_node_type: dict = None) -> dict:
    """Extract static node data from TypeScript AST"""
    interfaces = ast_data.get('interfaces', [])
    if specs_by_node_type is None:
        specs_by_node_type = {}
    
    # Get mappings
    node_interface_map = mappings.get('node_interface_map', {})
    base_fields = mappings.get('base_fields', ['label', 'flipped'])
    ts_to_py_type = mappings.get('ts_to_py_type', {})
    field_special_handling = mappings.get('field_special_handling', {})
    
    # Define enum fields mapping for the template
    enum_fields = {
        'method': 'HttpMethod',
        'language': 'SupportedLanguage',
        'sub_type': 'DBBlockSubType',
        'hook_type': 'HookType',
        'trigger_mode': 'HookTriggerMode',
        'diagram_format': 'DiagramFormat',
        'memory_profile': 'MemoryProfile',
        'tools': 'ToolSelection'
    }
    
    # Generate node classes data
    node_classes = []
    
    for node_type, interface_name in node_interface_map.items():
        # Skip PersonBatchJobNode as it's just an alias for PersonJobNode
        if node_type == 'person_batch_job':
            continue
            
        # Find interface
        interface_data = None
        for iface in interfaces:
            if iface.get('name') == interface_name:
                interface_data = iface
                break
        
        if not interface_data:
            continue
        
        class_name = interface_name.replace('NodeData', 'Node')
        
        # Get special handling for this node type
        node_special = field_special_handling.get(node_type, {})
        
        # Process fields
        fields = []
        for prop in interface_data.get('properties', []):
            ts_name = prop.get('name')
            
            # Skip base fields
            if ts_name in base_fields:
                continue
            
            # Get special handling for this field
            field_special = node_special.get(ts_name, {})
            
            # Determine Python name
            py_name = field_special.get('py_name', ts_name)
            
            ts_type = prop.get('type', 'Any')
            is_optional = prop.get('optional', False)
            py_type = get_python_type(ts_type, is_optional, ts_to_py_type)
            
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
            # First check for special handling defaults
            if 'default' in field_special:
                field_data['has_default'] = True
                field_data['default_value'] = field_special['default']
                field_data['is_field_default'] = 'field(' in field_special['default']
            # Check for defaultValue from specs
            elif node_type in specs_by_node_type:
                spec_fields = specs_by_node_type[node_type].get('fields_by_name', {})
                spec_field = spec_fields.get(ts_name, {})
                if 'defaultValue' in spec_field and spec_field['defaultValue'] is not None:
                    field_data['has_default'] = True
                    # Convert TypeScript default to Python default
                    ts_default = spec_field['defaultValue']
                    if isinstance(ts_default, bool):
                        field_data['default_value'] = str(ts_default)
                        field_data['is_field_default'] = False
                    elif isinstance(ts_default, (int, float)):
                        field_data['default_value'] = str(ts_default)
                        field_data['is_field_default'] = False
                    elif isinstance(ts_default, str):
                        field_data['default_value'] = f'"{ts_default}"'
                        field_data['is_field_default'] = False
                    elif isinstance(ts_default, list):
                        # Handle list defaults with field(default_factory=...)
                        field_data['default_value'] = f'field(default_factory=lambda: {ts_default})'
                        field_data['is_field_default'] = True
                    else:
                        field_data['default_value'] = str(ts_default)
                        field_data['is_field_default'] = False
            # Check for defaultValue from TypeScript interface (fallback)
            elif 'defaultValue' in prop and prop['defaultValue'] is not None:
                field_data['has_default'] = True
                # Convert TypeScript default to Python default
                ts_default = prop['defaultValue']
                if isinstance(ts_default, bool):
                    field_data['default_value'] = str(ts_default)
                    field_data['is_field_default'] = False
                elif isinstance(ts_default, (int, float)):
                    field_data['default_value'] = str(ts_default)
                    field_data['is_field_default'] = False
                elif isinstance(ts_default, str):
                    field_data['default_value'] = f'"{ts_default}"'
                    field_data['is_field_default'] = False
                elif isinstance(ts_default, list):
                    # Handle list defaults with field(default_factory=...)
                    field_data['default_value'] = f'field(default_factory=lambda: {ts_default})'
                    field_data['is_field_default'] = True
                else:
                    field_data['default_value'] = str(ts_default)
                    field_data['is_field_default'] = False
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
    
    # No need to track enum usage since we're using wildcard imports
    
    return {
        'node_classes': node_classes,
        'enum_fields': enum_fields,
        'now': datetime.now().isoformat()
    }


def generate_static_nodes(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate static nodes from all parsed TypeScript data.
    
    Args:
        inputs: Dictionary containing mappings, temp_results, and base_data
        
    Returns:
        Dictionary with extracted static node data
    """
    
    # Debug logging - always print this
    # Warning for empty inputs (import-time call issue)
    if not inputs:
        # print("[generate_static_nodes] WARNING: Called with empty inputs - possible timing issue!")
        return {'node_classes': [], 'now': datetime.now().isoformat()}
    
    # In DiPeO, labeled connections come directly at the top level
    mappings = inputs.get('mappings', {})
    node_data_input = inputs.get('node_data', {})
    base_data = inputs.get('base_data', {})

    # Extract base interface
    base_interface = base_data.get('base_interface')
    
    # The node_data_input contains the output from extract_node_data_from_glob
    # which returns {'node_data': {...}} so we need to unwrap it
    if 'node_data' in node_data_input:
        actual_node_data = node_data_input['node_data']
    else:
        actual_node_data = node_data_input
    
    # Also extract specs data to get defaultValues
    # The specs are loaded alongside node data files now
    specs_by_node_type = extract_specs_from_combined_data(node_data_input)
    
    # Convert node_data to parsed_nodes format
    parsed_nodes = []
    for node_type, data in actual_node_data.items():
        if node_type != 'default':
            # Ensure we have the interface
            if isinstance(data, dict) and 'interface' in data and data['interface']:
                parsed_nodes.append({
                    'node_type': node_type,
                    'interface_name': data['interface'].get('name'),
                    'interface': data['interface']
                })

    # Combine all interfaces
    all_interfaces: List[Dict[str, Any]] = []
    node_interface_map = mappings.get('node_interface_map', {})
    
    for parsed in parsed_nodes:
        node_type = parsed.get('node_type')
        interface_name = parsed.get('interface_name')
        interface_data = parsed.get('interface')
        
        if interface_data:
            # Update the node_interface_map with actual names
            node_interface_map[node_type] = interface_name
            all_interfaces.append(interface_data)
    
    if not all_interfaces:
        raise ValueError("No interfaces were successfully parsed from node data files")
    
    # Update mappings with the collected interface names
    mappings['node_interface_map'] = node_interface_map
    
    # Create combined AST data
    combined_ast = {
        'interfaces': all_interfaces,
        'base_interface': base_interface
    }
    
    # Run the static nodes extractor (now with specs for defaultValues)
    result = extract_static_nodes_data(combined_ast, mappings, specs_by_node_type)
    return result