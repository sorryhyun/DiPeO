"""Builder utilities for Strawberry IR builder."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Optional

from dipeo.domain.codegen.ir_builder_port import IRData
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
    logger.debug(f"Building domain IR with {len(domain_types)} types, {len(enums)} enums")

    # Filter and organize types
    organized_types = _organize_domain_types(domain_types)
    organized_interfaces = _organize_interfaces(interfaces)

    domain_data = {
        "types": organized_types,
        "interfaces": organized_interfaces,
        "enums": enums,
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "type_count": len(organized_types),
            "interface_count": len(organized_interfaces),
            "enum_count": len(enums),
        },
    }

    logger.info(f"Built domain IR with {len(organized_types)} types")
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
    logger.debug(f"Building operations IR with {len(operations)} operations")

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
        },
    }

    logger.info(
        f"Built operations IR: {len(queries)} queries, "
        f"{len(mutations)} mutations, {len(subscriptions)} subscriptions"
    )
    return operations_data


def build_complete_ir(
    operations_data: dict[str, Any],
    domain_data: dict[str, Any],
    config: dict[str, Any],
) -> IRData:
    """Build complete IR data structure.

    Args:
        operations_data: Operations IR data
        domain_data: Domain IR data
        config: Configuration data

    Returns:
        Complete IRData instance
    """
    logger.debug("Building complete Strawberry IR")

    # Combine all data
    strawberry_data = {
        "operations": operations_data["queries"] + operations_data["mutations"] + operations_data["subscriptions"],
        "domain_types": domain_data["types"],
        "interfaces": domain_data["interfaces"],
        "enums": domain_data["enums"],
        "input_types": operations_data["input_types"],
        "result_types": operations_data["result_types"],
        "config": config,
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "total_operations": operations_data["metadata"]["total_count"],
            "total_types": domain_data["metadata"]["type_count"],
            "total_enums": domain_data["metadata"]["enum_count"],
        },
    }

    ir_data = IRData(
        backend={},  # Empty for Strawberry-only build
        frontend={},  # Empty for Strawberry-only build
        strawberry=strawberry_data,
    )

    logger.info("Successfully built complete Strawberry IR")
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

    if not ir_data.strawberry:
        errors.append("Strawberry data is missing")
        return False, errors

    strawberry_data = ir_data.strawberry

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