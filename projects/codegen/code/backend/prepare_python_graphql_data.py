"""
Prepare Python GraphQL operations data from TypeScript definitions.
Transforms TypeScript query definitions into Python-compatible format
for generating typed GraphQL operations.
"""

import json
import os
import sys
from pathlib import Path
from typing import Any, Optional

sys.path.append(os.environ.get('DIPEO_BASE_DIR', '/home/soryhyun/DiPeO'))


def map_graphql_type_to_python(graphql_type: str, required: bool = False) -> str:
    """
    Map GraphQL types to Python type hints.

    Args:
        graphql_type: GraphQL type string (e.g., 'ID', 'String', 'Int')
        required: Whether the field is required

    Returns:
        Python type hint string
    """
    # Handle array types
    if graphql_type.startswith('[') and graphql_type.endswith(']'):
        inner_type = graphql_type[1:-1].replace('!', '')
        python_type = map_graphql_type_to_python(inner_type, True)
        return f"list[{python_type}]"

    # Remove required markers for base type mapping
    base_type = graphql_type.replace('!', '')

    # Map base types
    type_map = {
        'ID': 'str',
        'String': 'str',
        'Int': 'int',
        'Float': 'float',
        'Boolean': 'bool',
        'JSON': 'dict[str, Any]',
        'Upload': 'Any',  # File upload type
        'DateTime': 'str',  # DateTime as ISO 8601 string
    }

    # Check if it's a known scalar or use as-is for custom types
    python_type = type_map.get(base_type, base_type)

    # Add Optional wrapper if not required
    if not required and not graphql_type.endswith('!'):
        python_type = f"Optional[{python_type}]"

    return python_type


def extract_query_string(query_data: dict[str, Any]) -> str:
    """
    Reconstruct the GraphQL query string from parsed AST data.

    Args:
        query_data: Parsed query definition from TypeScript AST

    Returns:
        GraphQL query string
    """
    # Extract operation type from enum value (e.g., "QueryOperationType.QUERY" -> "query")
    type_value = query_data.get('type', 'query')
    if '.' in type_value:
        operation_type = type_value.split('.')[-1].lower()
    else:
        operation_type = type_value.lower()

    name = query_data.get('name', 'UnknownOperation')
    variables = query_data.get('variables', [])
    fields = query_data.get('fields', [])

    # Build variable declarations
    var_declarations = []
    for var in variables:
        var_name = var.get('name', '')
        var_type = var.get('type', 'String')
        required = var.get('required', False)
        var_declarations.append(f"${var_name}: {var_type}{'!' if required else ''}")

    # Build query string
    if var_declarations:
        query_str = f"{operation_type} {name}({', '.join(var_declarations)}) {{\n"
    else:
        query_str = f"{operation_type} {name} {{\n"

    # Add fields
    for field in fields:
        query_str += build_field_string(field, indent=1)

    query_str += "}"

    return query_str


def build_field_string(field: dict[str, Any], indent: int = 0) -> str:
    """
    Build GraphQL field string with proper indentation.

    Args:
        field: Field definition
        indent: Current indentation level

    Returns:
        Field string with indentation
    """
    indent_str = "  " * indent
    field_str = f"{indent_str}{field.get('name', '')}"

    # Add arguments if present
    args = field.get('args', [])
    if args:
        arg_strs = []
        for arg in args:
            arg_name = arg.get('name', '')
            is_variable = arg.get('isVariable', False)
            arg_value = arg.get('value', '')
            if is_variable:
                arg_strs.append(f"{arg_name}: ${arg_value}")
            else:
                # Handle literal values
                if isinstance(arg_value, str) and not arg_value.startswith('$'):
                    arg_strs.append(f'{arg_name}: "{arg_value}"')
                else:
                    arg_strs.append(f"{arg_name}: {arg_value}")
        field_str += f"({', '.join(arg_strs)})"

    # Add nested fields if present
    nested_fields = field.get('fields', [])
    if nested_fields:
        field_str += " {\n"
        for nested_field in nested_fields:
            field_str += build_field_string(nested_field, indent + 1)
        field_str += f"{indent_str}}}\n"
    else:
        field_str += "\n"

    return field_str


def to_snake_case(name: str) -> str:
    """Convert PascalCase or camelCase to snake_case."""
    result = []
    for i, char in enumerate(name):
        if char.isupper() and i > 0:
            # Add underscore before uppercase letter if previous char is lowercase
            if name[i-1].islower() or (i < len(name) - 1 and name[i+1].islower()):
                result.append('_')
        result.append(char.lower())
    return ''.join(result)


def to_pascal_case(name: str) -> str:
    """Convert snake_case or camelCase to PascalCase."""
    # Handle camelCase
    if '_' not in name:
        return name[0].upper() + name[1:] if name else name
    # Handle snake_case
    parts = name.split('_')
    return ''.join(part.capitalize() for part in parts)


def prepare_python_operations_data(inputs: dict[str, Any]) -> dict[str, Any]:
    """
    Prepare Python GraphQL operations data from TypeScript definitions.

    Args:
        inputs: Contains 'ast_data' with parsed TypeScript AST

    Returns:
        Structured data for template generation
    """
    ast_data = inputs.get('ast_data', {})
    operations = []

    # Process each query definition file
    for key, file_data in ast_data.items():
        if not key or not file_data:
            continue

        # Skip non-query-definition files
        if 'query-definitions' not in key or key.endswith('types.ts.json'):
            continue

        # Extract queries from constants
        if 'constants' in file_data:
            for const in file_data['constants']:
                const_value = const.get('value', {})
                if isinstance(const_value, dict) and 'queries' in const_value:
                    entity = const_value.get('entity', 'Unknown')

                    for query in const_value.get('queries', []):
                        operation = transform_query_to_operation(query, entity)
                        if operation:
                            operations.append(operation)

    # Sort operations by type and name for consistent output
    operations.sort(key=lambda x: (x['type'], x['name']))

    # Group by type
    queries = [op for op in operations if op['type'] == 'query']
    mutations = [op for op in operations if op['type'] == 'mutation']
    subscriptions = [op for op in operations if op['type'] == 'subscription']

    # Collect all required imports
    imports = collect_required_imports(operations)

    return {
        'operations': operations,
        'queries': queries,
        'mutations': mutations,
        'subscriptions': subscriptions,
        'imports': imports,
        'metadata': {
            'total_operations': len(operations),
            'total_queries': len(queries),
            'total_mutations': len(mutations),
            'total_subscriptions': len(subscriptions),
        }
    }


def transform_query_to_operation(query_data: dict[str, Any], entity: str) -> Optional[dict[str, Any]]:
    """
    Transform a TypeScript query definition to Python operation format.

    Args:
        query_data: Parsed query from TypeScript AST
        entity: Entity name from parent constant

    Returns:
        Operation dictionary for template generation
    """
    if not query_data:
        return None

    name = query_data.get('name', '')
    if not name:
        return None

    # Extract operation type from enum value (e.g., "QueryOperationType.QUERY" -> "query")
    type_value = query_data.get('type', 'query')
    if '.' in type_value:
        operation_type = type_value.split('.')[-1].lower()
    else:
        operation_type = type_value.lower()

    variables = query_data.get('variables', [])
    fields = query_data.get('fields', [])

    # Generate the GraphQL query string
    query_string = extract_query_string(query_data)

    # Transform variables to Python format
    python_variables = []
    for var in variables:
        var_name = var.get('name', '')
        var_type = var.get('type', 'String')
        required = var.get('required', False)
        python_type = map_graphql_type_to_python(var_type, required)

        # Generate union type for variables that could be Strawberry input objects
        union_type = python_type
        # Check if it's a custom input type
        clean_type = var_type.replace('[', '').replace(']', '').replace('!', '')
        if clean_type.endswith('Input'):
            # For custom input types, create a Union type
            if required:
                union_type = f"Union[{python_type}, dict[str, Any]]"
            else:
                # Handle Optional wrapper
                if python_type.startswith('Optional['):
                    # Extract the inner type
                    inner_type = python_type[9:-1]  # Remove 'Optional[' and ']'
                    union_type = f"Optional[Union[{inner_type}, dict[str, Any]]]"
                else:
                    union_type = f"Optional[Union[{python_type}, dict[str, Any]]]"

        python_variables.append({
            'name': var_name,
            'graphql_type': var_type,
            'python_type': python_type,
            'union_type': union_type,
            'required': required
        })

    # Generate constant name and class name
    const_name = f"{to_snake_case(name).upper()}_{operation_type.upper()}"
    class_name = f"{to_pascal_case(name)}Operation"

    return {
        'name': name,
        'entity': entity,
        'type': operation_type,
        'const_name': const_name,
        'class_name': class_name,
        'query_string': query_string,
        'variables': python_variables,
        'has_variables': len(python_variables) > 0,
        'fields': fields
    }


def collect_required_imports(operations: list[dict[str, Any]]) -> dict[str, set[str]]:
    """
    Collect all required imports based on operations.

    Args:
        operations: List of operation dictionaries

    Returns:
        Dictionary of import sources to sets of types
    """
    imports = {
        'typing': set(),
        'dipeo.diagram_generated.graphql.inputs': set(),
        'dipeo.diagram_generated.enums': set(),
    }

    # Always need these
    imports['typing'].add('Any')
    imports['typing'].add('Optional')
    imports['typing'].add('TypedDict')
    imports['typing'].add('Union')

    # Check for custom types in variables
    for operation in operations:
        for var in operation.get('variables', []):
            graphql_type = var.get('graphql_type', '')
            # Remove array brackets and required markers
            clean_type = graphql_type.replace('[', '').replace(']', '').replace('!', '')

            # Check if it's a custom input type
            if clean_type.endswith('Input'):
                imports['dipeo.diagram_generated.graphql.inputs'].add(clean_type)
            elif clean_type == 'DateTime':
                # DateTime is represented as str in Python
                continue
            elif clean_type == 'DiagramFormat':
                # DiagramFormat is an enum
                imports['dipeo.diagram_generated.enums'].add('DiagramFormat')
            elif clean_type not in ['ID', 'String', 'Int', 'Float', 'Boolean', 'JSON', 'Upload']:
                # Other custom types might be enums too
                imports['dipeo.diagram_generated.enums'].add(clean_type)

    # Remove empty import sets
    imports = {k: v for k, v in imports.items() if v}

    return imports
