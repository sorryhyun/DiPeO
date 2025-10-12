"""Data transformation rules for node connections.

This module maintains backward compatibility while delegating to the
ExecutionRuleRegistry for pluggable rule management.
"""

from typing import Any

from dipeo.diagram_generated.generated_nodes import ExecutableNode


class DataTransformRules:
    """Transform rules using the ExecutionRuleRegistry.

    This class maintains backward compatibility with the original static API
    while delegating to the registry for extensibility.

    For advanced usage, see dipeo.infrastructure.execution.rules.ExecutionRuleRegistry
    """

    @staticmethod
    def get_data_transform(source: ExecutableNode, target: ExecutableNode) -> dict[str, Any]:
        """Get data transformation rules for node pair.

        Args:
            source: Source node
            target: Target node

        Returns:
            Dictionary of transformation rules to apply

        Note:
            This method delegates to ExecutionRuleRegistry for extensibility.
            To register custom transform rules, use get_registry().
        """
        from dipeo.infrastructure.execution.rules.compat import get_default_registry

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

        Note:
            This method delegates to ExecutionRuleRegistry for extensibility.
        """
        from dipeo.infrastructure.execution.rules.compat import get_default_registry

        registry = get_default_registry()
        return registry.merge_transforms(edge_transform, type_based_transform)

    @staticmethod
    def get_registry():
        """Get the underlying ExecutionRuleRegistry for advanced usage.

        Returns:
            ExecutionRuleRegistry: The default registry instance

        Example:
            # Register a custom transform rule
            from dipeo.infrastructure.execution.rules import (
                BaseTransformRule,
                RuleKey,
                RuleCategory,
                RulePriority,
            )

            class MyTransformRule(BaseTransformRule):
                def __init__(self):
                    super().__init__("my_transform", "My transform", RulePriority.HIGH)

                def applies_to(self, source, target):
                    # Check if rule applies
                    return True

                def get_transform(self, source, target):
                    return {"custom_transform": True}

            registry = DataTransformRules.get_registry()
            rule = MyTransformRule()
            key = RuleKey(
                name=rule.name,
                category=RuleCategory.TRANSFORM,
                priority=rule.priority,
            )
            registry.register_transform_rule(key, rule)
        """
        from dipeo.infrastructure.execution.rules.compat import get_default_registry

        return get_default_registry()
