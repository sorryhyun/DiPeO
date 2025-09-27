"""Type transformation utilities for Strawberry IR builder."""

from __future__ import annotations

import logging
from typing import Any, Optional

from dipeo.infrastructure.codegen.ir_builders.utils import (
    TypeConverter,
    pascal_case,
    snake_to_pascal,
)

logger = logging.getLogger(__name__)


def transform_domain_types(
    interfaces: list[dict[str, Any]],
    config: dict[str, Any],
    type_converter: Optional[TypeConverter] = None,
) -> list[dict[str, Any]]:
    """Transform TypeScript interfaces to Strawberry domain types.

    Args:
        interfaces: List of TypeScript interface definitions
        config: Configuration data for domain fields
        type_converter: Optional type converter instance

    Returns:
        List of transformed domain type definitions
    """
    if not type_converter:
        type_converter = TypeConverter()

    domain_types = []
    # logger.debug(f"Transforming {len(interfaces)} interfaces to domain types")

    for interface in interfaces:
        interface_name = interface.get("name", "")

        # Skip non-domain interfaces
        if not _is_domain_type(interface_name):
            continue

        domain_type = _create_domain_type(interface, config, type_converter)
        domain_types.append(domain_type)
        # logger.debug(f"Transformed domain type: {domain_type['name']}")

    # logger.info(f"Created {len(domain_types)} domain types")
    return domain_types


def transform_input_types(
    operations: list[dict[str, Any]], type_converter: Optional[TypeConverter] = None
) -> list[dict[str, Any]]:
    """Transform operation variables to GraphQL input types.

    Args:
        operations: List of operation definitions
        type_converter: Optional type converter instance

    Returns:
        List of input type definitions
    """
    if not type_converter:
        type_converter = TypeConverter()

    input_types = {}
    # logger.debug(f"Extracting input types from {len(operations)} operations")

    for operation in operations:
        if not operation.get("is_mutation"):
            continue

        operation_name = operation.get("name", "")
        variables = operation.get("variables", [])

        # Create input type from variables
        if variables and len(variables) == 1 and variables[0].get("type", "").endswith("Input"):
            input_type_name = variables[0].get("type", "").replace("!", "")
            if input_type_name not in input_types:
                input_type = _create_input_type(operation_name, variables[0], type_converter)
                input_types[input_type_name] = input_type

    result = list(input_types.values())
    # logger.info(f"Created {len(result)} input types")
    return result


def transform_result_types(
    operations: list[dict[str, Any]], type_converter: Optional[TypeConverter] = None
) -> list[dict[str, Any]]:
    """Transform operation fields to GraphQL result types.

    Args:
        operations: List of operation definitions
        type_converter: Optional type converter instance

    Returns:
        List of result type definitions
    """
    if not type_converter:
        type_converter = TypeConverter()

    result_types = []
    # logger.debug(f"Creating result types for {len(operations)} operations")

    for operation in operations:
        result_type = _create_result_type(operation, type_converter)
        result_types.append(result_type)
        # logger.debug(f"Created result type: {result_type['name']}")

    # logger.info(f"Created {len(result_types)} result types")
    return result_types


def _is_domain_type(interface_name: str) -> bool:
    """Check if an interface should be treated as a domain type.

    Args:
        interface_name: Name of the interface

    Returns:
        True if interface is a domain type
    """
    # Skip utility types and non-domain interfaces
    skip_patterns = [
        "Props",
        "State",
        "Config",
        "Options",
        "Settings",
        "Request",
        "Response",
        "Input",
        "Output",
        "Result",
        "Params",
        "Args",
        "Query",
        "Mutation",
        "Subscription",
    ]

    return not any(pattern in interface_name for pattern in skip_patterns)


def _create_domain_type(
    interface: dict[str, Any],
    config: dict[str, Any],
    type_converter: TypeConverter,
) -> dict[str, Any]:
    """Create a domain type definition from an interface.

    Args:
        interface: TypeScript interface definition
        config: Configuration for domain fields
        type_converter: Type converter instance

    Returns:
        Domain type definition
    """
    interface_name = interface.get("name", "")
    fields = []

    for prop in interface.get("properties", []):
        field = {
            "name": prop.get("name", ""),
            "type": type_converter.ts_to_graphql(prop.get("type", "String")),
            "required": not prop.get("optional", False),
            "description": prop.get("description", ""),
        }
        fields.append(field)

    # Add configured domain fields if specified
    domain_fields = config.get("domain_fields", {})
    if interface_name in domain_fields:
        for field_def in domain_fields[interface_name]:
            fields.append(field_def)

    return {
        "name": interface_name,
        "fields": fields,
        "description": interface.get("description", f"{interface_name} domain type"),
    }


def _create_input_type(
    operation_name: str, variable: dict[str, Any], type_converter: TypeConverter
) -> dict[str, Any]:
    """Create an input type definition from operation variable.

    Args:
        operation_name: Name of the operation
        variable: Variable definition
        type_converter: Type converter instance

    Returns:
        Input type definition
    """
    input_type_name = variable.get("type", "").replace("!", "")

    return {
        "name": input_type_name,
        "fields": [
            {
                "name": variable.get("name", "input"),
                "type": type_converter.ts_to_graphql(variable.get("type", "String")),
                "required": variable.get("required", False),
                "description": variable.get("description", ""),
            }
        ],
        "description": f"Input type for {operation_name}",
    }


def _create_result_type(operation: dict[str, Any], type_converter: TypeConverter) -> dict[str, Any]:
    """Create a result type definition from operation fields.

    Args:
        operation: Operation definition
        type_converter: Type converter instance

    Returns:
        Result type definition
    """
    operation_name = operation.get("name", "UnknownOperation")
    fields = _extract_fields_as_types(operation.get("fields", []), type_converter)

    return {
        "name": f"{operation_name}Result",
        "fields": fields,
        "description": f"Result type for {operation_name}",
    }


def _extract_fields_as_types(
    fields: list[Any], type_converter: TypeConverter
) -> list[dict[str, Any]]:
    """Extract fields and convert to type definitions.

    Args:
        fields: List of field definitions
        type_converter: Type converter instance

    Returns:
        List of field type definitions
    """
    result = []

    for field in fields:
        if isinstance(field, str):
            result.append(
                {
                    "name": field,
                    "type": "String",
                    "required": True,
                    "description": "",
                }
            )
        elif isinstance(field, dict):
            field_name = field.get("field", field.get("name", ""))
            subfields = field.get("fields", field.get("subfields", []))

            if subfields:
                # Complex type with nested fields
                result.append(
                    {
                        "name": field_name,
                        "type": pascal_case(field_name),
                        "required": True,
                        "description": "",
                        "fields": _extract_fields_as_types(subfields, type_converter),
                    }
                )
            else:
                result.append(
                    {
                        "name": field_name,
                        "type": "String",
                        "required": True,
                        "description": "",
                    }
                )

    return result
