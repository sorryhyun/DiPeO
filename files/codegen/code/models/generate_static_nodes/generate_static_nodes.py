"""Generate static nodes from parsed TypeScript data."""
import json
from datetime import datetime
from typing import Any, Dict, List


def get_python_type(ts_type: str, is_optional: bool, ts_to_py_type: dict) -> str:
    """Convert TypeScript type to Python type"""
    # Clean type
    clean_type = ts_type.replace(' | null', '').replace(' | undefined', '').strip()
    
    # Handle Record types first (before checking for unions)
    if clean_type.startswith('Record<'):
        # Extract the value type from Record<key, value>
        # Find the matching closing bracket
        bracket_count = 0
        value_start = -1
        for i, char in enumerate(clean_type):
            if char == '<':
                bracket_count += 1
                if bracket_count == 1:
                    value_start = i + 1
            elif char == '>':
                bracket_count -= 1
                if bracket_count == 0:
                    # Extract the content between brackets
                    record_content = clean_type[value_start:i]
                    # Split by comma to get key and value types
                    parts = record_content.split(',', 1)
                    if len(parts) == 2:
                        value_type = parts[1].strip()
                        # Convert the value type
                        if '|' in value_type:
                            # Handle union value types
                            value_parts = [p.strip() for p in value_type.split('|')]
                            py_value_parts = []
                            for vp in value_parts:
                                py_vp = get_python_type(vp, False, ts_to_py_type)
                                py_value_parts.append(py_vp)
                            py_value_type = f"Union[{', '.join(py_value_parts)}]"
                        else:
                            py_value_type = get_python_type(value_type, False, ts_to_py_type)
                        dict_type = f"Dict[str, {py_value_type}]"
                        return f"Optional[{dict_type}]" if is_optional else dict_type
                    break
        # Fallback for simple Record types
        return 'Dict[str, Any]'
    
    # Handle union types like "string | string[]"
    if '|' in clean_type and not (("'" in clean_type or '"' in clean_type)):
        # Split union types
        union_parts = [part.strip() for part in clean_type.split('|')]
        # Convert each part
        py_parts = []
        for part in union_parts:
            py_part = get_python_type(part, False, ts_to_py_type)
            py_parts.append(py_part)
        # Create union type
        if len(py_parts) == 2 and 'None' in py_parts:
            # Handle Optional case
            other_type = [p for p in py_parts if p != 'None'][0]
            return f"Optional[{other_type}]"
        else:
            union_type = f"Union[{', '.join(py_parts)}]"
            return f"Optional[{union_type}]" if is_optional else union_type
    
    # Handle string literal unions
    if ("'" in clean_type or '"' in clean_type) and '|' in clean_type:
        literals = []
        for lit in clean_type.split('|'):
            cleaned = lit.strip().replace("'", '').replace('"', '')
            literals.append(f'"{cleaned}"')
        literal_type = f"Literal[{', '.join(literals)}]"
        return f"Optional[{literal_type}]" if is_optional else literal_type
    
    # Check mapping first
    if clean_type in ts_to_py_type:
        mapped_type = ts_to_py_type[clean_type]
        # Handle optional wrapping for mapped types
        if is_optional and not mapped_type.startswith('Optional['):
            return f"Optional[{mapped_type}]"
        return mapped_type
    
    # Basic TypeScript to Python type mappings
    basic_type_map = {
        'string': 'str',
        'number': 'int',  # Default to int, not float
        'boolean': 'bool',
        'any': 'Any',
        'object': 'Dict[str, Any]',
        'null': 'None',
        'undefined': 'None',
        'void': 'None'
    }
    
    # Check basic type mappings
    if clean_type in basic_type_map:
        py_type = basic_type_map[clean_type]
        return f"Optional[{py_type}]" if is_optional and py_type != 'None' else py_type
    
    # Handle arrays
    if clean_type.endswith('[]'):
        inner_type = clean_type[:-2]
        inner_py = get_python_type(inner_type, False, ts_to_py_type)
        list_type = f"List[{inner_py}]"
        return f"Optional[{list_type}]" if is_optional else list_type
    
    # Handle Record types
    if clean_type.startswith('Record<'):
        return 'Dict[str, Any]'
    
    # Handle object literal types (e.g., { field: type; ... })
    # Enhanced detection to handle multi-line object types with comments
    if clean_type.startswith('{'):
        # Check if it looks like an object type by looking for common patterns
        # This handles both single-line and multi-line object definitions
        if (':' in clean_type or '?' in clean_type or ';' in clean_type or 
            '//' in clean_type or '/*' in clean_type):
            dict_type = 'Dict[str, Any]'
            return f"Optional[{dict_type}]" if is_optional else dict_type
    
    # If nothing matched, return the original type (might be a custom type)
    # Handle optional wrapping
    if is_optional and not clean_type.startswith('Optional['):
        return f"Optional[{clean_type}]"
    
    return clean_type


def extract_static_nodes_data(ast_data: dict, mappings: dict) -> dict:
    """Extract static node data from TypeScript AST"""
    interfaces = ast_data.get('interfaces', [])
    
    # Get mappings
    node_interface_map = mappings.get('node_interface_map', {})
    base_fields = mappings.get('base_fields', ['label', 'flipped'])
    ts_to_py_type = mappings.get('ts_to_py_type', {})
    field_special_handling = mappings.get('field_special_handling', {})
    
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
    
    # No need to track enum usage since we're using wildcard imports
    
    return {
        'node_classes': node_classes,
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
    print(f"[generate_static_nodes] ENTRY - Called with inputs keys: {list(inputs.keys())}")
    
    # Warning for empty inputs (import-time call issue)
    if not inputs:
        print("[generate_static_nodes] WARNING: Called with empty inputs - possible timing issue!")
        return {'node_classes': [], 'now': datetime.now().isoformat()}
    
    # In DiPeO, labeled connections come directly at the top level
    mappings = inputs.get('mappings', {})
    node_data = inputs.get('node_data', {})
    base_data = inputs.get('base_data', {})
    
    print(f"[generate_static_nodes] mappings keys: {list(mappings.keys()) if mappings else 'None'}")
    print(f"[generate_static_nodes] node_data keys: {list(node_data.keys()) if node_data else 'None'}")
    print(f"[generate_static_nodes] base_data keys: {list(base_data.keys()) if base_data else 'None'}")
    
    # Extract base interface
    base_interface = base_data.get('base_interface')
    
    # Convert node_data to parsed_nodes format
    parsed_nodes = []
    for node_type, data in node_data.items():
        if node_type != 'default':
            parsed_nodes.append({
                'node_type': node_type,
                'interface_name': data['interface'].get('name'),
                'interface': data['interface']
            })
    print(f"[generate_static_nodes] Found {len(parsed_nodes)} parsed nodes")
    
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
    
    # Run the static nodes extractor
    result = extract_static_nodes_data(combined_ast, mappings)
    
    print(f"[generate_static_nodes] Returning result with keys: {list(result.keys())}")
    if 'node_classes' in result:
        print(f"[generate_static_nodes] Generated {len(result['node_classes'])} node classes")
        if result['node_classes']:
            print(f"[generate_static_nodes] First node class: {result['node_classes'][0].get('class_name', 'Unknown')}")
            # Print all node classes for debugging
            for i, nc in enumerate(result['node_classes']):
                print(f"  [{i}] {nc.get('class_name', 'Unknown')}")
    
    return result