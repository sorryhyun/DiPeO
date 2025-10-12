"""Shared utilities for IR builders."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Optional

import inflection
import yaml

from dipeo.infrastructure.codegen.ir_builders.type_system_unified import UnifiedTypeConverter

# ============================================================================
# CASE CONVERSION UTILITIES
# ============================================================================
# These utilities were moved from the legacy type_system module


def snake_case(text: str) -> str:
    """Convert text to snake_case using the inflection library."""
    if not text or text == "Undefined":
        return ""
    return inflection.underscore(str(text))


def camel_case(text: str) -> str:
    """Convert text to camelCase using the inflection library."""
    if not text or text == "Undefined":
        return ""
    return inflection.camelize(str(text), uppercase_first_letter=False)


def pascal_case(text: str) -> str:
    """Convert text to PascalCase using the inflection library."""
    if not text or text == "Undefined":
        return ""
    return inflection.camelize(str(text))


def kebab_case(text: str) -> str:
    """Convert text to kebab-case using the inflection library."""
    if not text or text == "Undefined":
        return ""
    return inflection.dasherize(inflection.underscore(str(text)))


# Aliases for backward compatibility
camel_to_snake = snake_case
snake_to_pascal = pascal_case
pascal_to_camel = camel_case


def process_field_definition(
    field: dict[str, Any], type_converter: UnifiedTypeConverter | None = None
) -> dict[str, Any]:
    """Process a field definition from TypeScript AST.

    Args:
        field: Field definition from AST
        type_converter: Optional UnifiedTypeConverter instance for type conversion

    Returns:
        Processed field dictionary
    """
    if not type_converter:
        type_converter = UnifiedTypeConverter()

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
