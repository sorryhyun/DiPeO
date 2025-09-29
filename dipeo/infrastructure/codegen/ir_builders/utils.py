"""Shared utilities for IR builders."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Optional

import yaml

from dipeo.infrastructure.codegen.type_system import (
    TypeConverter,
    camel_case,
    camel_to_snake,
    kebab_case,
    pascal_case,
    pascal_to_camel,
    snake_case,
    snake_to_pascal,
)


# ============================================================================
# AST PROCESSING UTILITIES
# ============================================================================


def extract_constants_from_ast(
    ast_data: dict[str, Any], pattern: Optional[str] = None
) -> list[dict[str, Any]]:
    """Extract constants from TypeScript AST data.

    Args:
        ast_data: TypeScript AST data
        pattern: Optional regex pattern to filter constant names

    Returns:
        List of constant dictionaries
    """
    constants = []

    for file_path, file_data in ast_data.items():
        if not isinstance(file_data, dict):
            continue

        for const in file_data.get("constants", []):
            const_name = const.get("name", "")

            # Apply pattern filter if provided
            if pattern and not re.match(pattern, const_name):
                continue

            constants.append(
                {
                    "name": const_name,
                    "value": const.get("value"),
                    "type": const.get("type"),
                    "file": file_path,
                }
            )

    return constants


def extract_interfaces_from_ast(
    ast_data: dict[str, Any], suffix: Optional[str] = None
) -> list[dict[str, Any]]:
    """Extract interfaces from TypeScript AST data.

    Args:
        ast_data: TypeScript AST data
        suffix: Optional suffix to filter interface names (e.g., 'Config', 'Props')

    Returns:
        List of interface dictionaries
    """
    interfaces = []

    for file_path, file_data in ast_data.items():
        if not isinstance(file_data, dict):
            continue

        for interface in file_data.get("interfaces", []):
            interface_name = interface.get("name", "")

            # Apply suffix filter if provided
            if suffix and not interface_name.endswith(suffix):
                continue

            interfaces.append(
                {
                    "name": interface_name,
                    "properties": interface.get("properties", []),
                    "extends": interface.get("extends", []),
                    "file": file_path,
                }
            )

    return interfaces


def extract_enums_from_ast(ast_data: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract enums from TypeScript AST data.

    Args:
        ast_data: TypeScript AST data

    Returns:
        List of enum dictionaries
    """
    enums = []

    for file_path, file_data in ast_data.items():
        if not isinstance(file_data, dict):
            continue

        for enum in file_data.get("enums", []):
            enums.append(
                {
                    "name": enum.get("name", ""),
                    "members": enum.get("members", []),
                    "file": file_path,
                }
            )

    return enums


def extract_type_aliases_from_ast(ast_data: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract type aliases from TypeScript AST data.

    Args:
        ast_data: TypeScript AST data

    Returns:
        List of type alias dictionaries
    """
    type_aliases = []

    for file_path, file_data in ast_data.items():
        if not isinstance(file_data, dict):
            continue

        for type_alias in file_data.get("typeAliases", []):
            type_aliases.append(
                {
                    "name": type_alias.get("name", ""),
                    "type": type_alias.get("type"),
                    "file": file_path,
                }
            )

    return type_aliases


def extract_graphql_input_types_from_ast(ast_data: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract GraphQL input types from TypeScript AST data.

    Looks for type aliases ending with 'Input' from graphql-inputs.ts

    Args:
        ast_data: TypeScript AST data

    Returns:
        List of input type definitions
    """
    input_types = []

    for file_path, file_data in ast_data.items():
        if not isinstance(file_data, dict):
            continue

        # Only process graphql-inputs.ts
        if "graphql-inputs" not in file_path:
            continue

        # Extract type aliases ending with Input
        for type_alias in file_data.get("typeAliases", []):
            name = type_alias.get("name", "")
            if name.endswith("Input"):
                # Parse the type definition
                type_def = type_alias.get("type", {})
                fields = []

                # Extract fields from object type
                if isinstance(type_def, dict) and type_def.get("type") == "object":
                    for prop in type_def.get("properties", []):
                        field = {
                            "name": prop.get("name", ""),
                            "type": prop.get("type", "String"),
                            "is_optional": prop.get("optional", False),
                            "description": prop.get("comment", ""),
                        }
                        fields.append(field)

                input_types.append(
                    {"name": name, "fields": fields, "description": type_alias.get("comment", "")}
                )

        # Also look in types array for types ending with Input
        for type_def in file_data.get("types", []):
            if isinstance(type_def, dict):
                name = type_def.get("name", "")
                if name.endswith("Input"):
                    # Parse the type string to extract fields
                    type_str = type_def.get("type", "")
                    fields = []

                    # Simple parser for object type string like "{ x: Float; y: Float; }"
                    if "{" in type_str and "}" in type_str:
                        # Remove braces and split by semicolon
                        content = type_str.strip().strip("{}").strip()
                        if content:
                            field_lines = content.split(";")
                            for line in field_lines:
                                line = line.strip()
                                if ":" in line:
                                    parts = line.split(":", 1)
                                    field_name = parts[0].strip()
                                    field_type = parts[1].strip() if len(parts) > 1 else "Any"

                                    # Simplify Scalars['Type']['input'] to Type
                                    if "Scalars[" in field_type:
                                        # Extract the type name
                                        import re

                                        match = re.search(r"Scalars\['(\w+)'\]", field_type)
                                        if match:
                                            field_type = match.group(1)

                                    # Check if optional
                                    is_optional = "?" in field_name or "InputMaybe<" in field_type
                                    field_name = field_name.rstrip("?")

                                    fields.append(
                                        {
                                            "name": field_name,
                                            "type": field_type,
                                            "is_optional": is_optional,
                                            "description": "",
                                        }
                                    )

                    if fields:  # Only add if we found fields
                        input_types.append({"name": name, "fields": fields, "description": ""})

    return input_types


def extract_branded_scalars_from_ast(ast_data: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract branded scalars from TypeScript AST data.

    Args:
        ast_data: TypeScript AST data

    Returns:
        List of branded scalar dictionaries
    """
    scalars = []
    seen_names = set()

    for _file_path, file_data in ast_data.items():
        if not isinstance(file_data, dict):
            continue

        # Look for branded scalars in the AST
        for scalar in file_data.get("brandedScalars", []):
            scalar_name = scalar.get("name", "")
            if scalar_name and scalar_name not in seen_names:
                scalars.append(
                    {
                        "name": scalar_name,
                        "type": scalar.get("baseType", "string"),
                        "description": f"Branded scalar type for {scalar_name}",
                    }
                )
                seen_names.add(scalar_name)

        # Also look for NewType declarations that end with ID
        for type_alias in file_data.get("typeAliases", []):
            name = type_alias.get("name", "")
            if name.endswith("ID") and name not in seen_names:
                scalars.append(
                    {
                        "name": name,
                        "type": "string",
                        "description": f"Branded scalar type for {name}",
                    }
                )
                seen_names.add(name)

        # Look in types array for branded types (pattern: string & { readonly __brand: ... })
        for type_def in file_data.get("types", []):
            if isinstance(type_def, dict):
                type_name = type_def.get("name", "")
                type_value = type_def.get("type", "")
                # Check if it's a branded type pattern
                if "__brand" in type_value and type_name and type_name not in seen_names:
                    # Extract base type (usually "string" before the &)
                    base_type = "string"  # Default to string
                    if "string &" in type_value:
                        base_type = "string"
                    elif "number &" in type_value:
                        base_type = "number"

                    scalars.append(
                        {
                            "name": type_name,
                            "type": base_type,
                            "description": f"Branded scalar type for {type_name}",
                        }
                    )
                    seen_names.add(type_name)

    return scalars


def process_field_definition(
    field: dict[str, Any], type_converter: Optional[TypeConverter] = None
) -> dict[str, Any]:
    """Process a field definition from TypeScript AST.

    Args:
        field: Field definition from AST
        type_converter: Optional TypeConverter instance for type conversion

    Returns:
        Processed field dictionary
    """
    if not type_converter:
        type_converter = TypeConverter()

    field_type = field.get("type", "any")
    is_required = field.get("required", False)

    return {
        "name": field.get("name", ""),
        "original_type": field_type,
        "python_type": type_converter.ts_to_python(field_type),
        "graphql_type": type_converter.ts_to_graphql(field_type),
        "required": is_required,
        "description": field.get("description", ""),
        "default": field.get("default"),
        "validation": field.get("validation"),
    }


# ============================================================================
# CONFIGURATION UTILITIES
# ============================================================================


def load_yaml_config(config_path: Path) -> dict[str, Any]:
    """Load configuration from YAML file or directory.

    Args:
        config_path: Path to YAML file or directory containing YAML files

    Returns:
        Merged configuration dictionary
    """
    if not config_path.exists():
        return {}

    if config_path.is_dir():
        # Load all YAML files in the directory
        config = {}
        for yaml_file in config_path.glob("*.yaml"):
            with open(yaml_file) as f:
                file_config = yaml.safe_load(f) or {}
                config.update(file_config)
        return config
    else:
        # Load single YAML file
        with open(config_path) as f:
            return yaml.safe_load(f) or {}


def merge_configs(*configs: dict[str, Any]) -> dict[str, Any]:
    """Merge multiple configuration dictionaries.

    Args:
        *configs: Configuration dictionaries to merge

    Returns:
        Merged configuration dictionary
    """
    result = {}
    for config in configs:
        if config:
            result.update(config)
    return result


# ============================================================================
# DEFAULT VALUE UTILITIES
# ============================================================================


def get_default_value(type_name: str, language: str = "python") -> str:
    """Get default value for a type in the specified language.

    Args:
        type_name: Name of the type
        language: Target language ('python', 'typescript', 'graphql')

    Returns:
        Default value string
    """
    defaults = {
        "python": {
            "str": '""',
            "int": "0",
            "float": "0.0",
            "bool": "False",
            "list": "[]",
            "dict": "{}",
            "set": "set()",
            "tuple": "()",
            "None": "None",
            "Any": "None",
            "List": "[]",
            "Dict": "{}",
        },
        "typescript": {
            "string": '""',
            "number": "0",
            "boolean": "false",
            "array": "[]",
            "object": "{}",
            "null": "null",
            "undefined": "undefined",
            "any": "null",
        },
        "graphql": {
            "String": '""',
            "Int": "0",
            "Float": "0.0",
            "Boolean": "false",
            "ID": '""',
            "JSONScalar": "{}",
        },
    }

    lang_defaults = defaults.get(language, {})

    # Handle List[X] and Dict[X, Y] patterns for Python
    if language == "python":
        if type_name.startswith("List["):
            return "[]"
        if type_name.startswith("Dict["):
            return "{}"
        if type_name.startswith("Optional["):
            return "None"

    return lang_defaults.get(type_name, "null" if language == "typescript" else "None")
