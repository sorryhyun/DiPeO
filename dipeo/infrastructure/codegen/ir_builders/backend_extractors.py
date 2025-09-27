"""Extraction utilities for Backend IR builder."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Optional

from dipeo.infrastructure.codegen.ir_builders.utils import (
    TypeConverter,
    camel_to_snake,
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


def extract_domain_models(
    ast_data: dict[str, Any], type_converter: Optional[TypeConverter] = None
) -> dict[str, Any]:
    """Extract domain model data matching legacy template expectations."""
    if not type_converter:
        type_converter = TypeConverter()

    domain_models: dict[str, list[Any]] = {
        "newtypes": [],
        "models": [],
        "aliases": [],
    }

    processed_newtypes: set[str] = set()
    processed_models: set[str] = set()

    domain_files = [
        "core/diagram.ts",
        "core/execution.ts",
        "core/conversation.ts",
        "core/cli-session.ts",
        "core/file.ts",
        "core/subscription-types.ts",
        "core/integration.ts",
        "claude-code/session-types.ts",
    ]

    for file_path, file_data in ast_data.items():
        is_domain_file = any(file_path.endswith(f"{df}.json") for df in domain_files)
        if not is_domain_file:
            continue

        # Extract branded NewType declarations
        for type_alias in file_data.get("types", []):
            type_name = type_alias.get("name", "")
            type_text = type_alias.get("type", "")

            if (
                isinstance(type_text, str)
                and "readonly __brand:" in type_text
                and type_name not in processed_newtypes
            ):
                base_type = type_text.split(" & ")[0].strip()
                python_base = type_converter.ts_to_python(base_type)
                domain_models["newtypes"].append({"name": type_name, "base": python_base})
                processed_newtypes.add(type_name)

        for interface in file_data.get("interfaces", []):
            interface_name = interface.get("name", "")
            if not interface_name or interface_name in processed_models:
                continue
            if interface_name in {"BaseNodeData", "NodeSpecification"}:
                continue

            processed_models.add(interface_name)

            fields = []
            for prop in interface.get("properties", []):
                field_name = prop.get("name", "")
                field_type = prop.get("type", {})
                is_optional = prop.get("optional", False)

                if isinstance(field_type, dict):
                    type_text = field_type.get("text", "any")
                else:
                    type_text = str(field_type)

                python_type = type_converter.ts_to_python(type_text)

                is_literal = False
                literal_value = None
                if isinstance(field_type, dict) and field_type.get("kind") == "literal":
                    is_literal = True
                    literal_value = field_type.get("value")
                    if literal_value == "true":
                        literal_value = True
                        python_type = "Literal[True]"
                    elif literal_value == "false":
                        literal_value = False
                        python_type = "Literal[False]"
                    elif isinstance(literal_value, str):
                        python_type = f'Literal["{literal_value}"]'
                elif type_text == "true":
                    is_literal = True
                    literal_value = True
                    python_type = "Literal[True]"
                elif type_text == "false":
                    is_literal = True
                    literal_value = False
                    python_type = "Literal[False]"

                fields.append(
                    {
                        "name": camel_to_snake(field_name)
                        if field_name not in {"id", "type"}
                        else field_name,
                        "python_type": python_type,
                        "optional": is_optional,
                        "literal": is_literal,
                        "literal_value": literal_value,
                        "description": prop.get("description", ""),
                    }
                )

            description = interface.get("description", "") or f"{interface_name} model"
            domain_models["models"].append(
                {"name": interface_name, "fields": fields, "description": description}
            )

    domain_models["aliases"].extend(
        [
            {"name": "SerializedNodeOutput", "type": "SerializedEnvelope"},
            {"name": "PersonMemoryMessage", "type": "Message"},
        ]
    )

    return domain_models


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
    processed_fields = [
        _process_node_field(field, node_type, type_converter)
        for field in spec_value.get("fields", [])
    ]

    # ensure stable order and remove Nones
    fields = [field for field in processed_fields if field["name"]]

    # Extract handler metadata if present
    handler_metadata = spec_value.get("handlerMetadata", {})

    camel_case_name = _to_camel_case(node_type)

    spec_details = {
        "nodeType": spec_value.get("nodeType", f"NodeType.{node_type.upper()}"),
        "displayName": spec_value.get("displayName", node_name),
        "category": spec_value.get("category", ""),
        "description": spec_value.get("description", ""),
        "icon": spec_value.get("icon", ""),
        "color": spec_value.get("color", ""),
        "fields": fields,
        "handles": spec_value.get("handles", {}),
        "outputs": spec_value.get("outputs", {}),
        "execution": spec_value.get("execution", {}),
        "primaryDisplayField": spec_value.get("primaryDisplayField", ""),
        "defaults": spec_value.get("defaults", {}),
        "handlerMetadata": handler_metadata,
    }

    return {
        "node_type": node_type,
        "node_name": node_name,
        "name": camel_case_name,
        "display_name": spec_details["displayName"],
        "category": spec_details["category"],
        "description": spec_details["description"],
        "fields": fields,
        "icon": spec_details["icon"],
        "color": spec_details["color"],
        "handler_metadata": handler_metadata,
        "spec": spec_details,
        "raw_spec": spec_value,
    }


def _to_camel_case(node_type: str) -> str:
    pascal = snake_to_pascal(node_type)
    if not pascal:
        return node_type
    return pascal[0].lower() + pascal[1:]


def _process_node_field(
    field: dict[str, Any], node_type: str, type_converter: TypeConverter
) -> dict[str, Any]:
    """Normalize node field definitions for template consumption."""

    raw_type = field.get("type", "string")
    if isinstance(raw_type, dict):
        field_type = raw_type.get("name") or raw_type.get("text") or "any"
    else:
        field_type = str(raw_type)

    field_name = field.get("name", "")
    validation = field.get("validation", {}) or {}
    enum_values = field.get("enumValues") or validation.get("allowedValues", []) or []

    python_type, graphql_type, is_object_type = _map_field_types(
        field_type, field_name, node_type, enum_values, type_converter
    )

    is_enum = bool(enum_values) or field_type == "enum"

    return {
        "name": field_name,
        "type": field_type,
        "python_type": python_type,
        "graphql_type": graphql_type,
        "required": field.get("required", False),
        "description": field.get("description", ""),
        "validation": validation,
        "uiConfig": field.get("uiConfig", {}),
        "default": field.get("defaultValue"),
        "is_object_type": is_object_type,
        "is_dict_type": is_object_type,
        "is_enum": is_enum,
        "enum_values": enum_values,
    }


def _map_field_types(
    field_type: str,
    field_name: str,
    node_type: str,
    enum_values: list[Any],
    type_converter: TypeConverter,
) -> tuple[str, str, bool]:
    """Determine python and GraphQL types along with object flag."""

    normalized = field_type.lower()
    is_object_type = False

    if normalized in {"string", "text"}:
        return "str", "String", is_object_type
    if normalized == "number":
        # Treat numbers as ints by default for node configs
        return "int", "Int", is_object_type
    if normalized == "boolean":
        return "bool", "Boolean", is_object_type
    if normalized in {"object", "dict"}:
        is_object_type = True
        return "Dict[str, Any]", "JSON", is_object_type
    if normalized in {"array", "list"}:
        return "List[Any]", "[JSON]", is_object_type
    if normalized == "enum" or enum_values:
        enum_type_name = f"{_to_camel_case(node_type)}{field_name.title().replace(' ', '')}Enum"
        return enum_type_name, enum_type_name, is_object_type

    # Fallback to type converter for other primitives
    python_type = type_converter.ts_to_python(field_type)
    graphql_type = type_converter.ts_to_graphql(field_type)

    return python_type or field_type, graphql_type or field_type, is_object_type


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
