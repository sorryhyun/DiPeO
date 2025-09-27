"""Extraction utilities for Backend IR builder."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Optional

from dipeo.infrastructure.codegen.ir_builders.utils import (
    TypeConverter,
    extract_constants_from_ast,
    extract_enums_from_ast,
    extract_interfaces_from_ast,
    snake_to_pascal,
)

logger = logging.getLogger(__name__)


def extract_node_specs(
    ast_data: dict[str, Any], type_converter: Optional[TypeConverter] = None
) -> list[dict[str, Any]]:
    """Extract node specifications from TypeScript AST.

    Args:
        ast_data: Dictionary of AST files
        type_converter: Optional type converter instance

    Returns:
        List of node specification definitions
    """
    if not type_converter:
        type_converter = TypeConverter()

    node_specs = []
    for file_path, file_data in ast_data.items():
        if not file_path.endswith(".spec.ts.json"):
            continue

        node_spec = _extract_node_spec_from_file(file_path, file_data, type_converter)
        if node_spec:
            node_specs.append(node_spec)
    return node_specs


def extract_enums_all(ast_data: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract all enum definitions from TypeScript AST.

    Args:
        ast_data: Dictionary of AST files

    Returns:
        List of enum definitions
    """
    enums = []
    processed_enums = set()

    for file_path, file_data in ast_data.items():
        file_enums = extract_enums_from_ast({file_path: file_data})

        for enum in file_enums:
            enum_name = enum.get("name", "")
            if enum_name and enum_name not in processed_enums:
                enums.append(enum)
                processed_enums.add(enum_name)
    return enums


def extract_models(ast_data: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract model definitions from TypeScript AST.

    Args:
        ast_data: Dictionary of AST files

    Returns:
        List of model definitions
    """
    models = []
    type_converter = TypeConverter()
    for file_path, file_data in ast_data.items():
        # Extract models from interfaces and types
        if "models" in file_path or "types" in file_path:
            models_from_file = _extract_models_from_file(file_data, type_converter)
            models.extend(models_from_file)
    return models


def _extract_node_spec_from_file(
    file_path: str, file_data: dict[str, Any], type_converter: TypeConverter
) -> Optional[dict[str, Any]]:
    """Extract node specification from a single AST file.

    Args:
        file_path: Path to the AST file
        file_data: AST data for the file
        type_converter: Type converter instance

    Returns:
        Node specification if found, None otherwise
    """
    # Extract node type from filename
    base_name = Path(file_path).stem.replace(".spec.ts", "")
    node_type = base_name.replace("-", "_")
    node_name = snake_to_pascal(node_type)

    # Look for the specification constant
    for const in file_data.get("constants", []):
        const_name = const.get("name", "")
        # Check for spec constants
        if const_name.endswith("Spec") or const_name.endswith("Specification"):
            spec_value = const.get("value", {})
            if not isinstance(spec_value, dict):
                continue

            return _build_node_spec(node_type, node_name, spec_value, type_converter)

    return None


def _build_node_spec(
    node_type: str,
    node_name: str,
    spec_value: dict[str, Any],
    type_converter: TypeConverter,
) -> dict[str, Any]:
    """Build node specification from spec value.

    Args:
        node_type: Node type identifier
        node_name: Node class name
        spec_value: Specification value from AST
        type_converter: Type converter instance

    Returns:
        Node specification dictionary
    """
    fields = []
    for field in spec_value.get("fields", []):
        field_def = {
            "name": field.get("name", ""),
            "type": type_converter.ts_to_python(field.get("type", "any")),
            "required": field.get("required", False),
            "default": field.get("defaultValue"),
            "description": field.get("description", ""),
            "validation": field.get("validation", {}),
        }
        fields.append(field_def)

    # Extract handler metadata if present
    handler_metadata = spec_value.get("handlerMetadata", {})

    return {
        "node_type": node_type,
        "node_name": node_name,
        "display_name": spec_value.get("displayName", node_name),
        "category": spec_value.get("category", ""),
        "description": spec_value.get("description", ""),
        "fields": fields,
        "icon": spec_value.get("icon", ""),
        "color": spec_value.get("color", ""),
        "handler_metadata": handler_metadata,
    }


def _extract_models_from_file(
    file_data: dict[str, Any], type_converter: TypeConverter
) -> list[dict[str, Any]]:
    """Extract model definitions from a single file.

    Args:
        file_data: AST data for the file
        type_converter: Type converter instance

    Returns:
        List of model definitions
    """
    models = []

    # Extract from interfaces
    interfaces = file_data.get("interfaces", [])
    for interface in interfaces:
        model = _interface_to_model(interface, type_converter)
        if model:
            models.append(model)

    # Extract from type aliases
    types = file_data.get("types", [])
    for type_def in types:
        model = _type_to_model(type_def, type_converter)
        if model:
            models.append(model)

    return models


def _interface_to_model(
    interface: dict[str, Any], type_converter: TypeConverter
) -> Optional[dict[str, Any]]:
    """Convert interface definition to model.

    Args:
        interface: Interface definition from AST
        type_converter: Type converter instance

    Returns:
        Model definition if applicable, None otherwise
    """
    name = interface.get("name", "")
    if not name or name.startswith("_"):
        return None

    # Skip utility interfaces
    if any(skip in name for skip in ["Props", "State", "Config", "Internal"]):
        return None

    properties = []
    for prop in interface.get("properties", []):
        prop_def = {
            "name": prop.get("name", ""),
            "type": type_converter.ts_to_python(prop.get("type", "any")),
            "optional": prop.get("optional", False),
            "description": prop.get("description", ""),
        }
        properties.append(prop_def)

    return {
        "name": name,
        "properties": properties,
        "description": interface.get("description", ""),
        "type": "interface",
    }


def _type_to_model(
    type_def: dict[str, Any], type_converter: TypeConverter
) -> Optional[dict[str, Any]]:
    """Convert type alias to model.

    Args:
        type_def: Type definition from AST
        type_converter: Type converter instance

    Returns:
        Model definition if applicable, None otherwise
    """
    name = type_def.get("name", "")
    if not name or name.startswith("_"):
        return None

    # Only process object types
    type_value = type_def.get("type", "")
    if not isinstance(type_value, dict):
        return None

    return {
        "name": name,
        "type_value": type_value,
        "description": type_def.get("description", ""),
        "type": "type_alias",
    }
