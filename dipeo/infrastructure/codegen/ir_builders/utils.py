"""Shared utilities for IR builders."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Optional

import yaml

from dipeo.infrastructure.codegen.type_system import (
    camel_case,
    camel_to_snake,
    kebab_case,
    pascal_case,
    pascal_to_camel,
    snake_case,
    snake_to_pascal,
)
from dipeo.infrastructure.codegen.ir_builders.type_system_unified import UnifiedTypeConverter


# ============================================================================
# AST PROCESSING UTILITIES
# ============================================================================

# NOTE: These functions are DEPRECATED as of Phase 2 refactoring.
# Use the new AST framework from dipeo.infrastructure.codegen.ir_builders.ast instead.
#
# Migration guide:
#   from dipeo.infrastructure.codegen.ir_builders.ast import (
#       InterfaceExtractor, EnumExtractor, TypeAliasExtractor,
#       ConstantExtractor, BrandedScalarExtractor, GraphQLInputTypeExtractor
#   )
#
# Example:
#   Old: interfaces = extract_interfaces_from_ast(ast_data, suffix='Config')
#   New: extractor = InterfaceExtractor(suffix='Config')
#        interfaces = extractor.extract(ast_data)


def extract_constants_from_ast(
    ast_data: dict[str, Any], pattern: Optional[str] = None
) -> list[dict[str, Any]]:
    """Extract constants from TypeScript AST data.

    DEPRECATED: Use ConstantExtractor from the ast module instead.

    Args:
        ast_data: TypeScript AST data
        pattern: Optional regex pattern to filter constant names

    Returns:
        List of constant dictionaries
    """
    from dipeo.infrastructure.codegen.ir_builders.ast import ConstantExtractor

    extractor = ConstantExtractor(pattern=pattern)
    return extractor.extract(ast_data)


def extract_interfaces_from_ast(
    ast_data: dict[str, Any], suffix: Optional[str] = None
) -> list[dict[str, Any]]:
    """Extract interfaces from TypeScript AST data.

    DEPRECATED: Use InterfaceExtractor from the ast module instead.

    Args:
        ast_data: TypeScript AST data
        suffix: Optional suffix to filter interface names (e.g., 'Config', 'Props')

    Returns:
        List of interface dictionaries
    """
    from dipeo.infrastructure.codegen.ir_builders.ast import InterfaceExtractor

    extractor = InterfaceExtractor(suffix=suffix)
    return extractor.extract(ast_data)


def extract_enums_from_ast(ast_data: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract enums from TypeScript AST data.

    DEPRECATED: Use EnumExtractor from the ast module instead.

    Args:
        ast_data: TypeScript AST data

    Returns:
        List of enum dictionaries
    """
    from dipeo.infrastructure.codegen.ir_builders.ast import EnumExtractor

    extractor = EnumExtractor()
    return extractor.extract(ast_data)


def extract_type_aliases_from_ast(ast_data: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract type aliases from TypeScript AST data.

    DEPRECATED: Use TypeAliasExtractor from the ast module instead.

    Args:
        ast_data: TypeScript AST data

    Returns:
        List of type alias dictionaries
    """
    from dipeo.infrastructure.codegen.ir_builders.ast import TypeAliasExtractor

    extractor = TypeAliasExtractor()
    return extractor.extract(ast_data)


def extract_graphql_input_types_from_ast(ast_data: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract GraphQL input types from TypeScript AST data.

    DEPRECATED: Use GraphQLInputTypeExtractor from the ast module instead.

    Looks for type aliases ending with 'Input' from graphql-inputs.ts

    Args:
        ast_data: TypeScript AST data

    Returns:
        List of input type definitions
    """
    from dipeo.infrastructure.codegen.ir_builders.ast import GraphQLInputTypeExtractor

    extractor = GraphQLInputTypeExtractor()
    return extractor.extract(ast_data)


def extract_branded_scalars_from_ast(ast_data: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract branded scalars from TypeScript AST data.

    DEPRECATED: Use BrandedScalarExtractor from the ast module instead.

    Args:
        ast_data: TypeScript AST data

    Returns:
        List of branded scalar dictionaries
    """
    from dipeo.infrastructure.codegen.ir_builders.ast import BrandedScalarExtractor

    extractor = BrandedScalarExtractor()
    return extractor.extract(ast_data)


def process_field_definition(
    field: dict[str, Any], type_converter: Optional[UnifiedTypeConverter] = None
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
