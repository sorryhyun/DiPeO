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
    logger.debug(f"Building factory data for {len(node_specs)} node specs")

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

    logger.info(f"Built factory data with {len(factory_mappings)} mappings")
    return factory_data


def build_models_data(
    models: list[dict[str, Any]], enums: list[dict[str, Any]]
) -> dict[str, Any]:
    """Build models data structure.

    Args:
        models: List of model definitions
        enums: List of enum definitions

    Returns:
        Models data dictionary
    """
    logger.debug(f"Building models data with {len(models)} models, {len(enums)} enums")

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

    logger.info(
        f"Built models data: {len(interfaces)} interfaces, "
        f"{len(type_aliases)} type aliases, {len(enums)} enums"
    )
    return models_data