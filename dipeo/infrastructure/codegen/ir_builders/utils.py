"""Shared utilities for IR builders."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Optional

import inflection
import yaml

# ============================================================================
# CASE CONVERSION UTILITIES
# ============================================================================


def snake_case(text: str) -> str:
    """Convert text to snake_case using inflection library."""
    if not text or text == "Undefined":
        return ""
    return inflection.underscore(str(text))


def camel_case(text: str) -> str:
    """Convert text to camelCase using inflection library."""
    if not text or text == "Undefined":
        return ""
    return inflection.camelize(str(text), uppercase_first_letter=False)


def pascal_case(text: str) -> str:
    """Convert text to PascalCase using inflection library."""
    if not text or text == "Undefined":
        return ""
    return inflection.camelize(str(text))


def kebab_case(text: str) -> str:
    """Convert text to kebab-case using inflection library."""
    if not text or text == "Undefined":
        return ""
    return inflection.dasherize(inflection.underscore(str(text)))


# Aliases for backward compatibility
camel_to_snake = snake_case
snake_to_pascal = pascal_case
pascal_to_camel = camel_case


# ============================================================================
# TYPE CONVERSION UTILITIES
# ============================================================================


class TypeConverter:
    """Unified type converter for TypeScript, Python, and GraphQL types."""

    # Base type mappings
    TS_TO_PYTHON_BASE = {
        "string": "str",
        "number": "float",
        "boolean": "bool",
        "any": "Any",
        "unknown": "Any",
        "null": "None",
        "undefined": "None",
        "void": "None",
        "Date": "datetime",
        "Record<string, any>": "Dict[str, Any]",
        "Record<string, string>": "Dict[str, str]",
        "object": "Dict[str, Any]",
    }

    TS_TO_GRAPHQL = {
        "string": "String",
        "number": "Float",
        "boolean": "Boolean",
        "any": "JSONScalar",
        "unknown": "JSONScalar",
        "Date": "DateTime",
        "Record<string, any>": "JSONScalar",
        "Record<string, string>": "JSONScalar",
        "object": "JSONScalar",
    }

    GRAPHQL_TO_TS = {
        "String": "string",
        "Int": "number",
        "Float": "number",
        "Boolean": "boolean",
        "ID": "string",
        "DateTime": "string",
        "JSON": "any",
        "JSONScalar": "any",
        "Upload": "File",
    }

    def __init__(self, custom_mappings: Optional[dict[str, dict[str, str]]] = None):
        """Initialize with optional custom type mappings.

        Args:
            custom_mappings: Dictionary with keys like 'ts_to_python', 'ts_to_graphql', etc.
        """
        self.custom_mappings = custom_mappings or {}

    def ts_to_python(self, ts_type: str) -> str:
        """Convert TypeScript type to Python type."""
        # Check custom mappings first
        if "ts_to_python" in self.custom_mappings:
            if ts_type in self.custom_mappings["ts_to_python"]:
                return self.custom_mappings["ts_to_python"][ts_type]

        # Handle known type aliases to avoid forward reference issues
        if ts_type == "SerializedNodeOutput":
            return "SerializedEnvelope"
        if ts_type == "PersonMemoryMessage":
            return "Message"

        # Handle union types (A | B | C) - check this before string literals
        # to properly handle unions of string literals
        if "|" in ts_type:
            return self._handle_union_type(ts_type, self.ts_to_python)

        # Handle string literals (only after checking for unions)
        if self._is_string_literal(ts_type):
            return f"Literal[{ts_type}]"

        # Handle array types
        if ts_type.startswith("Array<") and ts_type.endswith(">"):
            inner_type = ts_type[6:-1]
            return f"List[{self.ts_to_python(inner_type)}]"

        if ts_type.endswith("[]"):
            inner_type = ts_type[:-2]
            return f"List[{self.ts_to_python(inner_type)}]"

        # Handle Record types generically
        if ts_type.startswith("Record<") and ts_type.endswith(">"):
            # Extract key and value types from Record<K, V>
            inner = ts_type[7:-1]  # Remove "Record<" and ">"
            parts = inner.split(",", 1)
            if len(parts) == 2:
                key_type = parts[0].strip()
                value_type = parts[1].strip()
                # Convert both types recursively
                py_key = self.ts_to_python(key_type)
                py_value = self.ts_to_python(value_type)
                # Map number to int for dictionary keys
                if py_key == "float":
                    py_key = "int"
                return f"Dict[{py_key}, {py_value}]"

        # Handle branded scalars
        if "&" in ts_type and "__brand" in ts_type:
            match = re.search(r"'__brand':\s*'([^']+)'", ts_type)
            if match:
                return match.group(1)

        # Use base mapping
        return self.TS_TO_PYTHON_BASE.get(ts_type, ts_type)

    def ts_to_graphql(self, ts_type: str) -> str:
        """Convert TypeScript type to GraphQL type."""
        # Check custom mappings first
        if "ts_to_graphql" in self.custom_mappings:
            if ts_type in self.custom_mappings["ts_to_graphql"]:
                return self.custom_mappings["ts_to_graphql"][ts_type]

        # Handle arrays
        if ts_type.startswith("Array<") and ts_type.endswith(">"):
            inner_type = ts_type[6:-1]
            return f"[{self.ts_to_graphql(inner_type)}]"

        if ts_type.endswith("[]"):
            inner_type = ts_type[:-2]
            return f"[{self.ts_to_graphql(inner_type)}]"

        # Handle branded scalars
        if "&" in ts_type and "__brand" in ts_type:
            match = re.search(r"'__brand':\s*'([^']+)'", ts_type)
            if match:
                # Convert to GraphQL scalar name
                brand = match.group(1)
                return brand if brand.endswith("ID") else brand

        # Use base mapping
        return self.TS_TO_GRAPHQL.get(ts_type, ts_type)

    def graphql_to_ts(self, graphql_type: str) -> str:
        """Convert GraphQL type to TypeScript type."""
        # Check custom mappings first
        if "graphql_to_ts" in self.custom_mappings:
            if graphql_type in self.custom_mappings["graphql_to_ts"]:
                return self.custom_mappings["graphql_to_ts"][graphql_type]

        # Handle arrays
        if graphql_type.startswith("[") and graphql_type.endswith("]"):
            inner = graphql_type[1:-1].replace("!", "")
            return f"{self.graphql_to_ts(inner)}[]"

        # Remove required marker
        clean_type = graphql_type.replace("!", "")

        # Use base mapping
        return self.GRAPHQL_TO_TS.get(clean_type, clean_type)

    def graphql_to_python(self, graphql_type: str) -> str:
        """Convert GraphQL type to Python type."""
        # First convert to TypeScript, then to Python
        ts_type = self.graphql_to_ts(graphql_type)
        return self.ts_to_python(ts_type)

    def _is_string_literal(self, ts_type: str) -> bool:
        """Check if a TypeScript type is a string literal."""
        ts_type = ts_type.strip()
        return (ts_type.startswith("'") and ts_type.endswith("'")) or (
            ts_type.startswith('"') and ts_type.endswith('"')
        )

    def _handle_union_type(self, ts_type: str, converter_func) -> str:
        """Handle TypeScript union types (A | B | C)."""
        parts = [part.strip() for part in ts_type.split("|")]

        # Special case: if it's just Type | null or Type | undefined
        if len(parts) == 2:
            if "null" in parts or "undefined" in parts:
                other_type = parts[0] if parts[1] in ["null", "undefined"] else parts[1]
                return f"Optional[{converter_func(other_type)}]"

        # Check if all parts are string literals
        all_string_literals = all(self._is_string_literal(part) for part in parts)

        if all_string_literals:
            # Use Literal for unions of string literals
            # Keep the quotes for the literal values
            literal_values = ", ".join(parts)
            return f"Literal[{literal_values}]"

        # General union case
        converted_parts = []
        for part in parts:
            if self._is_string_literal(part):
                # For individual string literals in mixed unions, use Literal
                converted_parts.append(f"Literal[{part}]")
            else:
                converted_parts.append(converter_func(part))

        # Filter out None values for cleaner output
        converted_parts = [p for p in converted_parts if p != "None"]

        if len(converted_parts) == 1:
            return f"Optional[{converted_parts[0]}]"
        elif len(converted_parts) > 1:
            return f'Union[{", ".join(converted_parts)}]'
        else:
            return "None"


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
