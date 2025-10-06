"""TypeScript specification parser - extracts node specifications from TypeScript AST data."""

import os
import re
import sys
from typing import Any, Optional, Union

from dipeo.infrastructure.codegen.utils import parse_dipeo_output

sys.path.append(os.environ.get('DIPEO_BASE_DIR', '/home/soryhyun/DiPeO'))
from dipeo.infrastructure.codegen.parsers.typescript.type_transformer import map_ts_type_to_python


def extract_spec_from_ast(ast_data: dict[str, Any], spec_name: str) -> dict[str, Any] | None:
    """Extract a node specification from TypeScript AST data."""
    if not isinstance(ast_data, dict):
        return None

    constants = ast_data.get('constants', [])

    for const in constants:
        if const.get('name') == spec_name:
            value = const.get('value')

            if isinstance(value, dict):
                return normalize_spec_format(value)

    return None


def normalize_spec_format(spec_data: dict[str, Any]) -> dict[str, Any]:
    """Normalize the specification data format."""
    spec = dict(spec_data)

    if 'fields' in spec and isinstance(spec['fields'], list):
        spec['fields'] = normalize_fields(spec['fields'])

    return spec


def normalize_fields(fields: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Normalize field definitions for template consistency."""
    normalized_fields = []

    for field in fields:
        normalized_field = dict(field)

        if 'defaultValue' in normalized_field:
            normalized_field['default'] = normalized_field.pop('defaultValue')

        if 'nestedFields' in normalized_field and isinstance(normalized_field['nestedFields'], list):
            normalized_field['nestedFields'] = normalize_fields(normalized_field['nestedFields'])

        normalized_fields.append(normalized_field)

    return normalized_fields


def convert_typescript_type_to_field_type(ts_type: str) -> str:
    """Convert TypeScript type to field type used in specifications."""
    python_type = map_ts_type_to_python(ts_type)

    field_type_map = {
        'str': 'string',
        'float': 'number',
        'int': 'number',
        'bool': 'boolean',
        'Any': 'any',
        'Dict[str, Any]': 'object',
        'None': 'null'
    }

    if python_type.startswith('List['):
        return 'array'

    for py_type, field_type in field_type_map.items():
        if py_type in python_type:
            return field_type

    return 'any'


def main(inputs: dict[str, Any]) -> dict[str, Any]:
    """
    Main entry point for the TypeScript specification parser.

    Inputs:
        - ast_data: AST data from typescript_ast node
        - node_type: The node type to extract (e.g., "person_job")

    Outputs:
        - spec_data: The extracted specification as a Python dict
    """

    ast_data = inputs.get('ast_data', {})

    if isinstance(ast_data, str):
        ast_data = parse_dipeo_output(ast_data)
        if not ast_data:
            ast_data = {}

    if not isinstance(ast_data, dict):
        ast_data = {}

    node_type = inputs.get('node_type', '')
    parts = node_type.split('-')
    spec_name = parts[0] + ''.join(part.title() for part in parts[1:]) + 'Spec'

    spec_data = extract_spec_from_ast(ast_data, spec_name)

    if not spec_data:
        available_constants = [const.get('name', '') for const in ast_data.get('constants', [])]
        available_exports = [export.get('name', '') for export in ast_data.get('exports', [])]
        raise ValueError(
            f"Could not find specification '{spec_name}' for node type '{node_type}'. "
            f"Available constants: {available_constants}, exports: {available_exports}"
        )

    return {"spec_data": spec_data}