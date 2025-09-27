"""Builder utilities for Backend IR builder."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


def build_factory_data(node_specs: list[dict[str, Any]]) -> dict[str, Any]:
    """Build factory data for node creation.

    Args:
        node_specs: List of node specifications

    Returns:
        Factory data dictionary
    """
    factory_mappings = {}
    for spec in node_specs:
        node_type = spec.get("node_type", "")
        node_name = spec.get("node_name", "")
        if node_type and node_name:
            factory_mappings[node_type] = {
                "class_name": node_name,
                "display_name": spec.get("display_name", node_name),
                "category": spec.get("category", ""),
            }

    factory_data = {
        "mappings": factory_mappings,
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "node_count": len(factory_mappings),
        },
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
