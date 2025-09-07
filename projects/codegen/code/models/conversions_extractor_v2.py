"""
Simplified conversions data extractor for DiPeO V2.
Extracts raw NODE_TYPE_MAP data from TypeScript AST without any conversion.
All code generation is handled by template.
"""

import re
from typing import Any


def _process_dict_value(value: dict) -> dict[str, str]:
    """Process dictionary value from NODE_TYPE_MAP constant."""
    node_type_map = {}
    for key, enum_ref in value.items():
        # Handle "NodeType.PERSON_JOB" -> "PERSON_JOB"
        if isinstance(enum_ref, str):
            enum_value = enum_ref.split('.')[-1] if '.' in enum_ref else enum_ref
            node_type_map[key] = enum_value
    return node_type_map


def _process_string_value(value: str) -> dict[str, str]:
    """Process string value from NODE_TYPE_MAP constant using regex."""
    node_type_map = {}

    # Use regex to extract all key-value pairs
    # Matches patterns like: 'key': NodeType.VALUE
    pattern = r"'([^']+)':\s*NodeType\.([A-Z_]+)"
    matches = re.findall(pattern, value)

    if matches:
        for key, enum_value in matches:
            node_type_map[key] = enum_value
    else:
        # Try without NodeType prefix (shouldn't happen but just in case)
        pattern = r"'([^']+)':\s*([A-Z_]+)"
        matches = re.findall(pattern, value)
        for key, enum_value in matches:
            node_type_map[key] = enum_value

    return node_type_map


def _extract_node_type_map(constants: list) -> dict[str, str]:
    """Extract NODE_TYPE_MAP from constants list."""
    for const in constants:
        if const.get('name') == 'NODE_TYPE_MAP':
            value = const.get('value')

            if isinstance(value, dict):
                return _process_dict_value(value)
            elif isinstance(value, str):
                return _process_string_value(value)
            break

    return {}


def extract_conversions_data(inputs: dict[str, Any]) -> dict[str, Any]:
    """Extract raw conversions data from TypeScript using parsed AST data.

    Uses the modern parser infrastructure that provides structured data
    instead of regex-based extraction.
    """
    try:
        ast_data = inputs.get('ast_data', {})
        constants = ast_data.get('constants', [])

        node_type_map = _extract_node_type_map(constants)

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
        error_msg = f"Error extracting conversions data: {e!s}\n{traceback.format_exc()}"
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
