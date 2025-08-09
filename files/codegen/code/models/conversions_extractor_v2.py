"""
Simplified conversions data extractor for DiPeO V2.
Extracts raw NODE_TYPE_MAP data from TypeScript AST without any conversion.
All code generation is handled by template.
"""

import re
from typing import Dict, Any


def extract_conversions_data(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Extract raw conversions data from TypeScript without any conversion.
    
    This simplified version just extracts the NODE_TYPE_MAP data,
    leaving all code generation to the template.
    """
    try:
        ast_data = inputs.get('ast_data', {})
        ts_content = inputs.get('source', '')
        
        # Extract NODE_TYPE_MAP entries
        node_type_map = {}
        
        # First try from AST data
        constants = ast_data.get('constants', [])
        # print(f"Found {len(constants)} constants in AST")
        
        for const in constants:
            if const.get('name') == 'NODE_TYPE_MAP':
                # print(f"Found NODE_TYPE_MAP constant in AST")
                # The initializer should contain the object literal
                initializer = const.get('value', const.get('initializer', ''))
                
                # Extract key-value pairs using regex
                pattern = r"'([^']+)':\s*NodeType\.([A-Z_]+)"
                matches = re.findall(pattern, str(initializer))
                for key, value in matches:
                    node_type_map[key] = value
                break
        
        # If not found in AST, try parsing the raw TypeScript
        if not node_type_map and ts_content:
            # print("Parsing from raw TypeScript source...")
            # Find NODE_TYPE_MAP definition
            map_match = re.search(r'export\s+const\s+NODE_TYPE_MAP[^{]*\{([^}]+)\}', ts_content, re.DOTALL)
            if map_match:
                map_content = map_match.group(1)
                pattern = r"'([^']+)':\s*NodeType\.([A-Z_]+)"
                matches = re.findall(pattern, map_content)
                for key, value in matches:
                    node_type_map[key] = value
        
        # print(f"\nExtracted {len(node_type_map)} node type mappings")
        
        # Return raw data for template processing
        return {
            'node_type_map': node_type_map,
            'entries_count': len(node_type_map),
            'config': {
                'generate_reverse_map': True,
                'generate_type_guards': True,
            }
        }
        
    except Exception as e:
        import traceback
        error_msg = f"Error extracting conversions data: {str(e)}\n{traceback.format_exc()}"
        # print(error_msg)
        return {
            'error': str(e),
            'node_type_map': {},
            'entries_count': 0,
            'config': {}
        }


def generate_summary(inputs):
    """Generate summary of conversions generation."""
    extraction_result = inputs.get('extraction_result', {})
    
    # print(f"\n=== Conversions Generation Complete ===")
    # print(f"Generated mappings for {extraction_result.get('entries_count', 0)} node types")
    # print(f"\nOutput written to: dipeo/diagram_generated_staged/conversions.py")
    
    result = {
        'status': 'success',
        'message': 'Conversions generated successfully',
        'details': extraction_result
    }
    
    return result


# Alias for backward compatibility
main = extract_conversions_data