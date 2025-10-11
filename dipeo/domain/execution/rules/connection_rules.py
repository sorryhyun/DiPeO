"""Business logic for valid node type connections in diagrams.

This module maintains backward compatibility while delegating to the
ExecutionRuleRegistry for pluggable rule management.
"""

from dipeo.diagram_generated import NodeType


class NodeConnectionRules:
    """Connection rules using the ExecutionRuleRegistry.

    This class maintains backward compatibility with the original static API
    while delegating to the registry for extensibility.

    For advanced usage, see dipeo.infrastructure.execution.rules.ExecutionRuleRegistry
    """

    @staticmethod
    def can_connect(source_type: NodeType, target_type: NodeType) -> bool:
        """Check if a connection between node types is allowed.

        Args:
            source_type: Type of the source node
            target_type: Type of the target node

        Returns:
            True if connection is allowed, False otherwise

        Note:
            This method delegates to ExecutionRuleRegistry for extensibility.
            To register custom rules, use get_registry() and register your own.
        """
        from dipeo.infrastructure.execution.rules.compat import get_default_registry

        registry = get_default_registry()
        return registry.can_connect(source_type, target_type)

    @staticmethod
    def get_connection_constraints(node_type: NodeType) -> dict[str, list[NodeType]]:
        """Get connection constraints for a node type.

        Args:
            node_type: Type of node to check

        Returns:
            Dictionary with 'can_receive_from' and 'can_send_to' lists

        Note:
            This method delegates to ExecutionRuleRegistry for extensibility.
        """
        from dipeo.infrastructure.execution.rules.compat import get_default_registry

        registry = get_default_registry()
        return registry.get_connection_constraints(node_type)

    @staticmethod
    def get_registry():
        """Get the underlying ExecutionRuleRegistry for advanced usage.

        Returns:
            ExecutionRuleRegistry: The default registry instance

        Example:
            # Register a custom connection rule
            from dipeo.infrastructure.execution.rules import (
                BaseConnectionRule,
                RuleKey,
                RuleCategory,
                RulePriority,
            )

            class MyCustomRule(BaseConnectionRule):
                def __init__(self):
                    super().__init__("my_rule", "My custom rule", RulePriority.HIGH)

                def can_connect(self, source_type, target_type):
                    # Custom logic here
                    return True

            registry = NodeConnectionRules.get_registry()
            rule = MyCustomRule()
            key = RuleKey(
                name=rule.name,
                category=RuleCategory.CONNECTION,
                priority=rule.priority,
            )
            registry.register_connection_rule(key, rule)
        """
        from dipeo.infrastructure.execution.rules.compat import get_default_registry

        return get_default_registry()
