"""Builder utilities for Backend IR builder."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from dipeo.infrastructure.codegen.ir_builders.utils import camel_to_snake

logger = logging.getLogger(__name__)


def build_factory_data(node_specs: list[dict[str, Any]]) -> dict[str, Any]:
    """Build factory data for node creation from specs."""
    factory_data = {
        "imports": [],
        "factory_cases": [],
        "categories": [],
        "mappings": {},
    }

    seen_categories = set()

    for spec in node_specs:
        node_type = spec.get("node_type", "")
        node_name = spec.get("node_name", "")
        category = spec.get("category", "")

        if not node_type or not node_name:
            # logger.debug("Skipping node spec without type/name: %s", spec)
            continue

        # Build import statement (PascalCase -> snake_case module)
        module_name = f"unified_nodes.{camel_to_snake(node_name)}_node"
        class_name = f"{node_name}Node"
        alias = "DBNode" if node_type == "db" else None
        factory_data["imports"].append(
            {
                "module": module_name,
                "class": class_name,
                "alias": alias,
            }
        )

        factory_data["mappings"][node_type] = {
            "class_name": class_name,
            "display_name": spec.get("display_name", node_name),
            "category": category,
        }

        field_mappings = []
        for field in spec.get("fields", []):
            field_name = field.get("name")
            if not field_name:
                continue

            if field_name == "file_path":
                getter = "data.get('filePath', data.get('file_path', ''))"
            elif field_name == "function_name":
                getter = "data.get('functionName', data.get('function_name', ''))"
            elif field_name == "condition_type":
                getter = "data.get('condition_type')"
            elif field_name == "expression":
                getter = "data.get('expression', data.get('condition', ''))"
            else:
                default_val = field.get("default")
                if default_val is not None:
                    if isinstance(default_val, str):
                        getter = f"data.get('{field_name}', '{default_val}')"
                    else:
                        getter = f"data.get('{field_name}', {default_val})"
                else:
                    getter = f"data.get('{field_name}')"

            field_mappings.append(
                {
                    "node_field": field_name,
                    "getter_expression": getter,
                }
            )

        factory_data["factory_cases"].append(
            {
                "node_type": f"NodeType.{node_type.upper()}",
                "class_name": alias or class_name,
                "field_mappings": field_mappings,
            }
        )

        if category and category not in seen_categories:
            seen_categories.add(category)
            factory_data["categories"].append(category)

    factory_data["metadata"] = {
        "generated_at": datetime.now().isoformat(),
        "node_count": len(factory_data["factory_cases"]),
        "category_count": len(factory_data["categories"]),
    }

    return factory_data


def build_conversions_data(node_specs: list[dict[str, Any]]) -> dict[str, Any]:
    """Build conversions data for type mapping.

    Args:
        node_specs: List of node specifications

    Returns:
        Conversions data dictionary
    """
    # Build node type mappings from node specs
    node_type_map = {}
    for spec in node_specs:
        node_type = spec.get("node_type", "")
        if node_type:
            # Convert snake_case to CONSTANT_CASE
            constant_case = node_type.upper()
            node_type_map[node_type] = constant_case

    conversions_data = {
        "node_type_map": node_type_map,
        "type_conversions": {
            "string": "str",
            "number": "float",
            "boolean": "bool",
            "any": "Any",
            "unknown": "Any",
            "null": "None",
            "undefined": "None",
            "void": "None",
            "Date": "datetime",
            "object": "Dict[str, Any]",
        },
        "field_mappings": {
            "string": "text",
            "number": "number",
            "boolean": "checkbox",
            "object": "json",
            "array": "list",
        },
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "node_type_count": len(node_type_map),
        },
    }
    return conversions_data


def build_models_data(models: list[dict[str, Any]], enums: list[dict[str, Any]]) -> dict[str, Any]:
    """Build models data structure.

    Args:
        models: List of model definitions
        enums: List of enum definitions

    Returns:
        Models data dictionary
    """
    # Organize models by type
    interfaces = []
    type_aliases = []

    for model in models:
        model_type = model.get("type", "")
        if model_type == "interface":
            interfaces.append(model)
        elif model_type == "type_alias":
            type_aliases.append(model)

    models_data = {
        "interfaces": interfaces,
        "type_aliases": type_aliases,
        "enums": enums,
        "metadata": {
            "interface_count": len(interfaces),
            "type_alias_count": len(type_aliases),
            "enum_count": len(enums),
        },
    }
    return models_data
