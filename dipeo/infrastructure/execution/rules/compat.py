"""Backward compatibility layer for static rules.

This module provides a singleton registry and updated static rule classes
that maintain backward compatibility while using the new registry internally.
"""

from typing import Any

from dipeo.diagram_generated import NodeType
from dipeo.diagram_generated.generated_nodes import ExecutableNode

from .adapters import register_default_rules
from .registry import ExecutionRuleRegistry

# Singleton registry instance
_default_registry: ExecutionRuleRegistry | None = None


def get_default_registry() -> ExecutionRuleRegistry:
    """Get or create the default singleton rule registry.

    Returns:
        ExecutionRuleRegistry: The default registry instance with all default rules registered
    """
    global _default_registry

    if _default_registry is None:
        _default_registry = ExecutionRuleRegistry(allow_override=True, enable_audit=False)
        register_default_rules(_default_registry)

    return _default_registry


def reset_default_registry() -> None:
    """Reset the default registry (primarily for testing).

    This creates a fresh registry instance and re-registers all default rules.
    """
    global _default_registry
    _default_registry = None


class NodeConnectionRulesCompat:
    """Backward-compatible wrapper for NodeConnectionRules using the registry.

    This class maintains the same API as the original NodeConnectionRules
    but delegates to the ExecutionRuleRegistry internally.
    """

    @staticmethod
    def can_connect(source_type: NodeType, target_type: NodeType) -> bool:
        """Check if a connection between node types is allowed.

        Args:
            source_type: Type of the source node
            target_type: Type of the target node

        Returns:
            True if connection is allowed, False otherwise
        """
        registry = get_default_registry()
        return registry.can_connect(source_type, target_type)

    @staticmethod
    def get_connection_constraints(node_type: NodeType) -> dict[str, list[NodeType]]:
        """Get connection constraints for a node type.

        Args:
            node_type: Type of node to check

        Returns:
            Dictionary with 'can_receive_from' and 'can_send_to' lists
        """
        registry = get_default_registry()
        return registry.get_connection_constraints(node_type)


class DataTransformRulesCompat:
    """Backward-compatible wrapper for DataTransformRules using the registry.

    This class maintains the same API as the original DataTransformRules
    but delegates to the ExecutionRuleRegistry internally.
    """

    @staticmethod
    def get_data_transform(source: ExecutableNode, target: ExecutableNode) -> dict[str, Any]:
        """Get data transformation rules for node pair.

        Args:
            source: Source node
            target: Target node

        Returns:
            Dictionary of transformation rules to apply
        """
        registry = get_default_registry()
        return registry.get_data_transform(source, target)

    @staticmethod
    def merge_transforms(
        edge_transform: dict[str, Any], type_based_transform: dict[str, Any]
    ) -> dict[str, Any]:
        """Merge edge-specific and type-based transformations.

        Edge-specific transforms take precedence over type-based transforms.

        Args:
            edge_transform: Edge-specific transformation rules
            type_based_transform: Type-based transformation rules

        Returns:
            Merged transformation dictionary
        """
        registry = get_default_registry()
        return registry.merge_transforms(edge_transform, type_based_transform)
