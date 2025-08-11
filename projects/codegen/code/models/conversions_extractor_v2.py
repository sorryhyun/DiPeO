"""
Simplified conversions data extractor for DiPeO V2.
Extracts raw NODE_TYPE_MAP data from TypeScript AST without any conversion.
All code generation is handled by template.
"""

import re
from typing import Dict, Any


def extract_conversions_data(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Extract raw conversions data from TypeScript using parsed AST data.
    
    Uses the modern parser infrastructure that provides structured data
    instead of regex-based extraction.
    """
    try:
        ast_data = inputs.get('ast_data', {})
        
        # Extract NODE_TYPE_MAP entries from parsed AST
        node_type_map = {}
        
        # Get constants from parsed AST data
        constants = ast_data.get('constants', [])
        
        for const in constants:
            if const.get('name') == 'NODE_TYPE_MAP':
                # The parser should provide the parsed object as value
                value = const.get('value')
                
                if isinstance(value, dict):
                    # The value should be a dictionary with the mappings
                    # Convert enum references to their values
                    for key, enum_ref in value.items():
                        # Handle "NodeType.PERSON_JOB" -> "PERSON_JOB"
                        if isinstance(enum_ref, str):
                            if '.' in enum_ref:
                                enum_value = enum_ref.split('.')[-1]
                            else:
                                enum_value = enum_ref
                            node_type_map[key] = enum_value
                elif isinstance(value, str):
                    # Fallback: If parser returns string representation
                    # This should not happen with modern parser
                    import json
                    try:
                        # Try to parse as JSON
                        parsed = json.loads(value.replace("'", '"'))
                        if isinstance(parsed, dict):
                            node_type_map = parsed
                    except:
                        # Last resort: regex extraction
                        pattern = r"'([^']+)':\s*(?:NodeType\.)?([A-Z_]+)"
                        matches = re.findall(pattern, str(value))
                        for key, enum_value in matches:
                            node_type_map[key] = enum_value
                break
        
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