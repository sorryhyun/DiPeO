"""Builder utilities for Strawberry IR builder."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Optional

from dipeo.domain.codegen.ir_builder_port import IRData, IRMetadata
from dipeo.infrastructure.codegen.ir_builders.utils import TypeConverter

logger = logging.getLogger(__name__)


def build_domain_ir(
    domain_types: list[dict[str, Any]],
    interfaces: list[dict[str, Any]],
    enums: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build domain IR data structure.

    Args:
        domain_types: List of domain type definitions
        interfaces: List of interface definitions
        enums: List of enum definitions

    Returns:
        Domain IR data dictionary
    """
    # Filter and organize types
    organized_types = _organize_domain_types(domain_types)
    organized_interfaces = _organize_interfaces(interfaces)

    # The legacy builder exposes scalars/inputs even when empty, so mirror that API.
    domain_data = {
        "types": organized_types,
        "interfaces": organized_interfaces,
        "enums": enums,
        "scalars": [],
        "inputs": [],
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "type_count": len(organized_types),
            "interface_count": len(organized_interfaces),
            "enum_count": len(enums),
        },
    }
    return domain_data


def build_operations_ir(
    operations: list[dict[str, Any]],
    input_types: list[dict[str, Any]],
    result_types: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build operations IR data structure.

    Args:
        operations: List of operation definitions
        input_types: List of input type definitions
        result_types: List of result type definitions

    Returns:
        Operations IR data dictionary
    """
    # Organize operations by type
    queries = []
    mutations = []
    subscriptions = []

    for op in operations:
        if op.get("is_subscription"):
            subscriptions.append(op)
        elif op.get("is_mutation"):
            mutations.append(op)
        else:
            queries.append(op)

    operations_data = {
        "queries": queries,
        "mutations": mutations,
        "subscriptions": subscriptions,
        "input_types": input_types,
        "result_types": result_types,
        "metadata": {
            "query_count": len(queries),
            "mutation_count": len(mutations),
            "subscription_count": len(subscriptions),
            "total_count": len(operations),
            "total_queries": len(queries),
            "total_mutations": len(mutations),
            "total_subscriptions": len(subscriptions),
        },
        "raw_queries": queries,
        "raw_mutations": mutations,
        "raw_subscriptions": subscriptions,
    }

    return operations_data


def build_complete_ir(
    operations_data: dict[str, Any],
    domain_data: dict[str, Any],
    config: dict[str, Any],
    source_files: Optional[list[str]] = None,
    node_specs: Optional[list[dict[str, Any]]] = None,
) -> IRData:
    """Build complete IR data structure.

    Args:
        operations_data: Operations IR data
        domain_data: Domain IR data
        config: Configuration data

    Returns:
        Complete IRData instance
    """
    # Combine all data (with generated_at at top level for templates)
    strawberry_data = {
        "version": 1,
        "generated_at": datetime.now().isoformat(),
        "operations": operations_data["queries"]
        + operations_data["mutations"]
        + operations_data["subscriptions"],
        "domain_types": domain_data["types"],
        "interfaces": domain_data["interfaces"],
        "scalars": domain_data.get("scalars", []),
        "enums": domain_data["enums"],
        "inputs": domain_data.get("inputs", []),
        "input_types": operations_data["input_types"],
        "result_types": operations_data["result_types"],
        "node_specs": node_specs or [],  # Include node_specs for templates
        "types": domain_data["types"],  # Alias for domain_types for backward compatibility
        "config": config,
        "imports": {"strawberry": [], "domain": []},
        "raw_queries": operations_data.get("raw_queries", []),
        "raw_mutations": operations_data.get("raw_mutations", []),
        "raw_subscriptions": operations_data.get("raw_subscriptions", []),
        "queries": operations_data["queries"],
        "mutations": operations_data["mutations"],
        "subscriptions": operations_data["subscriptions"],
        "operations_ir": operations_data,
        "metadata": {
            "ast_file_count": len(source_files) if source_files else 0,
            "interface_count": len(domain_data["interfaces"]),
            "enum_count": len(domain_data["enums"]),
            "scalar_count": len(domain_data.get("scalars", [])),
            "input_count": len(domain_data.get("inputs", [])),
            "node_spec_count": len(node_specs) if node_specs else 0,
            "total_operations": operations_data["metadata"]["total_count"],
            "total_queries": operations_data["metadata"].get("total_queries", 0),
            "total_mutations": operations_data["metadata"].get("total_mutations", 0),
            "total_subscriptions": operations_data["metadata"].get("total_subscriptions", 0),
            "operations_meta": operations_data["metadata"],
        },
    }

    # Create metadata for IRData
    metadata = IRMetadata(
        version=1,
        source_files=len(source_files) if source_files else 0,  # Count of source files
        builder_type="strawberry",
        generated_at=datetime.now().isoformat(),
    )

    # Create IR data with proper structure
    ir_data = IRData(metadata=metadata, data=strawberry_data)
    return ir_data


def _organize_domain_types(domain_types: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Organize and validate domain types.

    Args:
        domain_types: List of domain type definitions

    Returns:
        Organized list of domain types
    """
    organized = []
    seen_names = set()

    for dtype in domain_types:
        name = dtype.get("name", "")
        if not name:
            logger.warning("Skipping domain type without name")
            continue

        if name in seen_names:
            logger.warning(f"Duplicate domain type: {name}, skipping")
            continue

        seen_names.add(name)
        organized.append(dtype)

    return organized


def _organize_interfaces(interfaces: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Organize and filter interfaces.

    Args:
        interfaces: List of interface definitions

    Returns:
        Organized list of interfaces
    """
    organized = []
    seen_names = set()

    for interface in interfaces:
        name = interface.get("name", "")
        if not name:
            continue

        # Skip internal interfaces
        if name.startswith("_") or name.endswith("Internal"):
            continue

        if name in seen_names:
            logger.warning(f"Duplicate interface: {name}, skipping")
            continue

        seen_names.add(name)
        organized.append(interface)

    return organized


def validate_strawberry_ir(ir_data: IRData) -> tuple[bool, list[str]]:
    """Validate Strawberry IR data structure.

    Args:
        ir_data: IR data to validate

    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []

    if not ir_data.data:
        errors.append("Strawberry data is missing")
        return False, errors

    strawberry_data = ir_data.data

    # Check required fields
    required_fields = ["operations", "domain_types", "config"]
    for field in required_fields:
        if field not in strawberry_data:
            errors.append(f"Missing required field: {field}")

    # Validate operations
    operations = strawberry_data.get("operations", [])
    if not operations:
        errors.append("No operations defined")
    else:
        for i, op in enumerate(operations):
            if not op.get("name"):
                errors.append(f"Operation {i} missing name")
            if not op.get("query_string"):
                errors.append(f"Operation {op.get('name', i)} missing query_string")

    # Validate domain types
    domain_types = strawberry_data.get("domain_types", [])
    for dtype in domain_types:
        if not dtype.get("name"):
            errors.append("Domain type missing name")
        if not dtype.get("fields"):
            errors.append(f"Domain type {dtype.get('name', 'unknown')} has no fields")

    is_valid = len(errors) == 0
    if is_valid:
        logger.info("Strawberry IR validation passed")
    else:
        logger.warning(f"Strawberry IR validation failed with {len(errors)} errors")

    return is_valid, errors
