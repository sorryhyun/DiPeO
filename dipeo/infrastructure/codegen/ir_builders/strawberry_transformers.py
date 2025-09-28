"""Type transformation utilities for Strawberry IR builder."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Optional

from dipeo.infrastructure.codegen.ir_builders.utils import (
    TypeConverter,
    pascal_case,
    snake_to_pascal,
)
from dipeo.infrastructure.codegen.type_resolver import StrawberryTypeResolver

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
    # These are exact patterns to skip - interface must end with these patterns
    skip_suffixes = [
        "Props",
        "State",
        "Params",
        "Args",
    ]

    # These are exact interface names to skip (not suffixes)
    skip_exact = [
        "Config",
        "Options",
        "Settings",
        "Request",
        "Response",
        "Input",
        "Output",
        "Result",
        "Query",  # Only skip exactly "Query", not types containing "Query"
        "Mutation",  # Only skip exactly "Mutation"
        "Subscription",  # Only skip exactly "Subscription"
        "FieldArgument",  # Query definition type
        "FieldDefinition",  # Query definition type
        "VariableDefinition",  # Query definition type
        "QueryDefinition",  # Query definition type - skip this specific one
        "EntityQueryDefinitions",  # Query definition type
    ]

    # Check if interface ends with any skip suffix
    if any(interface_name.endswith(suffix) for suffix in skip_suffixes):
        return False

    # Check if interface is exactly one of the skip names
    if interface_name in skip_exact:
        return False

    # Allow all other interfaces (including PersonLLMConfig, ToolConfig, etc.)
    return True


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

    # Create basic fields for backward compatibility
    for prop in interface.get("properties", []):
        # Convert TypeScript type to Python type
        ts_type = prop.get("type", "Any")
        python_type = type_converter.ts_to_python(ts_type)

        field = {
            "name": prop.get("name", ""),
            "type": python_type,  # Use converted Python type
            "optional": prop.get("optional", False),
            "description": prop.get("description", ""),
            "is_json_dict": False,
            "is_literal": False,
            "is_custom_list": False,
        }
        fields.append(field)

    # Add configured domain fields if specified
    domain_fields = config.get("domain_fields", {})
    if interface_name in domain_fields:
        for field_def in domain_fields[interface_name]:
            fields.append(field_def)

    # Use StrawberryTypeResolver to create resolved fields with proper types
    type_resolver = StrawberryTypeResolver()
    resolved_fields = []

    for prop in interface.get("properties", []):
        # Create a field dict that matches the resolver's expected format
        # Convert TypeScript type to Python type first
        ts_type = prop.get("type", "Any")
        python_type = type_converter.ts_to_python(ts_type)

        field_dict = {
            "name": prop.get("name", ""),
            "type": python_type,  # Use converted Python type
            "optional": prop.get("optional", False),
            "description": prop.get("description", ""),
        }
        resolved_field = type_resolver.resolve_field(field_dict, interface_name)

        # Convert ResolvedField dataclass to dict for JSON serialization
        resolved_fields.append(
            {
                "name": resolved_field.name,
                "strawberry_type": resolved_field.strawberry_type,
                "default": resolved_field.default,
                "python_type": resolved_field.python_type,
                "is_optional": resolved_field.is_optional,
                "is_json": resolved_field.is_json,
                "is_literal": resolved_field.is_literal,
                "is_custom_list": resolved_field.is_custom_list,
                "needs_conversion": resolved_field.needs_conversion,
                "conversion_expr": resolved_field.conversion_expr,
            }
        )

    return {
        "name": interface_name,
        "fields": fields,  # Original fields for backward compatibility
        "resolved_fields": resolved_fields,  # Properly resolved fields for template
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
