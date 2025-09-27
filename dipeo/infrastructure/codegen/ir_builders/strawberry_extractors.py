"""Extraction utilities for Strawberry IR builder."""

from __future__ import annotations

import logging
from typing import Any, Optional

from dipeo.infrastructure.codegen.ir_builders.utils import (
    TypeConverter,
    extract_constants_from_ast,
    extract_interfaces_from_ast,
    pascal_case,
    snake_to_pascal,
)

logger = logging.getLogger(__name__)


def extract_query_string(query_data: dict[str, Any]) -> str:
    """Reconstruct the GraphQL query string from parsed AST data.

    Args:
        query_data: Parsed query data from AST

    Returns:
        GraphQL query string
    """
    # Extract operation type from enum value
    type_value = query_data.get("type", "query")
    if "." in type_value:
        operation_type = type_value.split(".")[-1].lower()
    else:
        operation_type = type_value.lower()

    name = query_data.get("name", "UnknownOperation")
    variables = query_data.get("variables", [])
    fields = query_data.get("fields", [])

    # Build variables string
    vars_str = ""
    if variables:
        vars_parts = []
        for var in variables:
            var_name = var.get("name", "")
            var_type = var.get("type", "String")
            required = var.get("required", False)
            if required:
                var_type = f"{var_type}!"
            vars_parts.append(f"${var_name}: {var_type}")
        vars_str = f"({', '.join(vars_parts)})"

    # Build fields string
    fields_str = _build_fields_string(fields, indent=2)

    # Build complete query
    if operation_type == "subscription":
        query = f"{operation_type} {name}{vars_str} {{\n{fields_str}\n}}"
    else:
        entity_name = _extract_entity_name(name, fields)
        if vars_str:
            query = f"{operation_type} {name}{vars_str} {{\n  {entity_name}{_build_args_from_vars(variables)}\n{fields_str}\n}}"
        else:
            query = f"{operation_type} {name} {{\n  {entity_name}\n{fields_str}\n}}"

    return query


def extract_operations_from_ast(
    file_dict: dict[str, Any], type_converter: Optional[TypeConverter] = None
) -> list[dict[str, Any]]:
    """Extract GraphQL operations from TypeScript AST data.

    Args:
        file_dict: Dictionary of AST files
        type_converter: Optional type converter instance

    Returns:
        List of operation definitions
    """
    if not type_converter:
        type_converter = TypeConverter()

    operations = []
    logger.debug(f"Extracting operations from {len(file_dict)} files")

    for file_path, file_data in file_dict.items():
        # Focus on query definitions
        if "query-definitions" not in file_path and "queryDefinitions" not in file_path:
            continue

        logger.debug(f"Processing query definitions from: {file_path}")

        # Extract from constants
        constants = file_data.get("constants", [])
        for const in constants:
            const_name = const.get("name", "")
            if const_name.endswith("Queries"):
                _process_query_constant(const, operations, type_converter)

    logger.info(f"Extracted {len(operations)} operations")
    return operations


def _process_query_constant(
    const: dict[str, Any],
    operations: list[dict[str, Any]],
    type_converter: TypeConverter,
) -> None:
    """Process a query constant and extract operations.

    Args:
        const: Constant definition from AST
        operations: List to append operations to
        type_converter: Type converter instance
    """
    const_value = const.get("value", {})
    if not isinstance(const_value, dict):
        return

    entity_name = const_value.get("entity", "Unknown")
    queries = const_value.get("queries", [])

    for query in queries:
        if not isinstance(query, dict):
            continue

        operation = _build_operation(query, entity_name, type_converter)
        operations.append(operation)
        logger.debug(f"Added operation: {operation['name']}")


def _build_operation(
    query: dict[str, Any], entity_name: str, type_converter: TypeConverter
) -> dict[str, Any]:
    """Build an operation definition from query data.

    Args:
        query: Query definition
        entity_name: Entity name for the query
        type_converter: Type converter instance

    Returns:
        Operation definition dictionary
    """
    variables = []
    for var in query.get("variables", []):
        var_def = {
            "name": var.get("name", ""),
            "type": var.get("type", "String"),
            "required": var.get("required", False),
            "description": var.get("description", ""),
            "default": var.get("default"),
        }
        variables.append(var_def)

    return {
        "name": query.get("name", "UnknownOperation"),
        "type": query.get("type", "query"),
        "entity": entity_name,
        "variables": variables,
        "fields": query.get("fields", []),
        "description": query.get("description", ""),
        "query_string": extract_query_string(query),
        "is_mutation": "mutation" in query.get("type", "query").lower(),
        "is_subscription": "subscription" in query.get("type", "query").lower(),
    }


def _build_fields_string(fields: list[dict[str, Any]], indent: int = 2) -> str:
    """Build GraphQL fields string from field definitions.

    Args:
        fields: List of field definitions
        indent: Indentation level

    Returns:
        Formatted fields string
    """
    if not fields:
        return ""

    lines = []
    indent_str = " " * indent

    for field in fields:
        if isinstance(field, str):
            lines.append(f"{indent_str}{field}")
        elif isinstance(field, dict):
            field_name = field.get("field", field.get("name", ""))
            subfields = field.get("fields", field.get("subfields", []))
            args = field.get("args")

            if subfields:
                subfields_str = _build_fields_string(subfields, indent + 2)
                if args:
                    lines.append(f"{indent_str}{field_name}({args}) {{")
                else:
                    lines.append(f"{indent_str}{field_name} {{")
                lines.append(subfields_str)
                lines.append(f"{indent_str}}}")
            else:
                if args:
                    lines.append(f"{indent_str}{field_name}({args})")
                else:
                    lines.append(f"{indent_str}{field_name}")

    return "\n".join(lines)


def _extract_entity_name(operation_name: str, fields: list[dict[str, Any]]) -> str:
    """Extract entity name from operation name or fields.

    Args:
        operation_name: Name of the operation
        fields: Operation fields

    Returns:
        Entity name
    """
    # Try to extract from operation name
    if operation_name.startswith("Get"):
        return operation_name[3:].lower()
    elif operation_name.startswith("List"):
        return operation_name[4:].lower()
    elif operation_name.startswith("Create"):
        return operation_name[6:].lower()
    elif operation_name.startswith("Update"):
        return operation_name[6:].lower()
    elif operation_name.startswith("Delete"):
        return operation_name[6:].lower()

    # Try to extract from first field
    if fields and isinstance(fields[0], (dict, str)):
        if isinstance(fields[0], dict):
            return fields[0].get("field", fields[0].get("name", "query"))
        else:
            return fields[0]

    return "query"


def _build_args_from_vars(variables: list[dict[str, Any]]) -> str:
    """Build GraphQL arguments string from variables.

    Args:
        variables: List of variable definitions

    Returns:
        Arguments string for GraphQL query
    """
    if not variables:
        return ""

    args = []
    for var in variables:
        var_name = var.get("name", "")
        args.append(f"{var_name}: ${var_name}")

    return f"({', '.join(args)})" if args else ""