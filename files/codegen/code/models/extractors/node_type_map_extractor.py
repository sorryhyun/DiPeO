"""Extract NODE_TYPE_MAP from TypeScript conversions file."""

import re
from typing import Dict


def extract_node_type_map(ast_data: dict, ts_content: str) -> dict:
    """Extract NODE_TYPE_MAP entries from TypeScript AST or source content."""
    constants = ast_data.get('constants', [])
    
    # Debug print to see structure
    print(f"Found {len(constants)} constants in AST")
    for const in constants[:3]:  # Show first 3 for debugging
        print(f"Constant: {const.get('name')} - Keys: {list(const.keys())}")
    
    # Find NODE_TYPE_MAP constant
    node_type_map = {}
    for const in constants:
        if const.get('name') == 'NODE_TYPE_MAP':
            print(f"Found NODE_TYPE_MAP constant")
            # The initializer should contain the object literal
            initializer = const.get('value', const.get('initializer', ''))
            print(f"Initializer type: {type(initializer)}")
            print(f"Initializer preview: {str(initializer)[:200]}...")
            
            # Extract key-value pairs using regex
            pattern = r"'([^']+)':\s*NodeType\.([A-Z_]+)"
            matches = re.findall(pattern, str(initializer))
            for key, value in matches:
                node_type_map[key] = value
            break
    
    # If regex didn't work, try parsing the raw TypeScript
    if not node_type_map:
        print("Trying to parse from raw TypeScript...")
        if ts_content:
            # Find NODE_TYPE_MAP definition
            map_match = re.search(r'export\s+const\s+NODE_TYPE_MAP[^{]*\{([^}]+)\}', ts_content, re.DOTALL)
            if map_match:
                map_content = map_match.group(1)
                pattern = r"'([^']+)':\s*NodeType\.([A-Z_]+)"
                matches = re.findall(pattern, map_content)
                for key, value in matches:
                    node_type_map[key] = value
    
    print(f"\nExtracted {len(node_type_map)} node type mappings:")
    for k, v in sorted(node_type_map.items()):
        print(f"  {k} -> {v}")
    
    return {
        'node_type_map': node_type_map,
        'entries_count': len(node_type_map)
    }


def main(inputs: dict) -> dict:
    """Main entry point for NODE_TYPE_MAP extraction."""
    ast_data = inputs.get('default', {})
    ts_content = inputs.get('source', '')
    
    return extract_node_type_map(ast_data, ts_content)