"""Adapters for existing static rules to work with ExecutionRuleRegistry.

This module provides adapters that wrap the existing NodeConnectionRules and
DataTransformRules static methods to work with the new registry system.
"""

from typing import TYPE_CHECKING, Any

from dipeo.diagram_generated import NodeType
from dipeo.diagram_generated.generated_nodes import (
    ExecutableNode,
    PersonJobNode,
)

from .base import BaseConnectionRule, BaseTransformRule, RulePriority

if TYPE_CHECKING:
    from .registry import ExecutionRuleRegistry


class StartNoInputRule(BaseConnectionRule):
    """START nodes cannot receive input connections."""

    def __init__(self):
        super().__init__(
            name="start_no_input",
            description="START nodes cannot receive input connections",
            priority=RulePriority.HIGH,
        )

    def can_connect(self, source_type: NodeType, target_type: NodeType) -> bool:
        return target_type != NodeType.START

    def get_reason(self, source_type: NodeType, target_type: NodeType) -> str | None:
        if target_type == NodeType.START:
            return "START nodes cannot receive input connections"
        return None


class EndpointNoOutputRule(BaseConnectionRule):
    """ENDPOINT nodes cannot send output connections."""

    def __init__(self):
        super().__init__(
            name="endpoint_no_output",
            description="ENDPOINT nodes cannot send output connections",
            priority=RulePriority.HIGH,
        )

    def can_connect(self, source_type: NodeType, target_type: NodeType) -> bool:
        return source_type != NodeType.ENDPOINT

    def get_reason(self, source_type: NodeType, target_type: NodeType) -> str | None:
        if source_type == NodeType.ENDPOINT:
            return "ENDPOINT nodes cannot send output connections"
        return None


class OutputCapableRule(BaseConnectionRule):
    """Output-capable nodes can only connect to non-START nodes."""

    def __init__(self):
        super().__init__(
            name="output_capable",
            description="Output-capable nodes can connect to any node except START",
            priority=RulePriority.NORMAL,
        )
        self.output_capable = {
            NodeType.PERSON_JOB,
            NodeType.CONDITION,
            NodeType.CODE_JOB,
            NodeType.API_JOB,
            NodeType.START,
        }

    def can_connect(self, source_type: NodeType, target_type: NodeType) -> bool:
        if source_type in self.output_capable:
            return target_type != NodeType.START
        return True

    def get_reason(self, source_type: NodeType, target_type: NodeType) -> str | None:
        if source_type in self.output_capable and target_type == NodeType.START:
            return f"{source_type.value} nodes cannot connect to START nodes"
        return None


class PersonJobToolExtractionRule(BaseTransformRule):
    """Extract tool results from PersonJob nodes that have tools configured."""

    def __init__(self):
        super().__init__(
            name="personjob_tool_extraction",
            description="Extract tool results from PersonJob nodes with tools",
            priority=RulePriority.NORMAL,
        )

    def applies_to(self, source: ExecutableNode, target: ExecutableNode) -> bool:
        return isinstance(source, PersonJobNode) and bool(source.tools)

    def get_transform(self, source: ExecutableNode, target: ExecutableNode) -> dict[str, Any]:
        if self.applies_to(source, target):
            return {"extract_tool_results": True}
        return {}


def register_default_rules(registry: "ExecutionRuleRegistry") -> None:
    """Register all default rules to the registry.

    This function registers the standard connection and transformation rules
    that replicate the behavior of the original static rule classes.

    Args:
        registry: ExecutionRuleRegistry to register rules to
    """
    from .registry import RuleCategory, RuleKey

    # Register connection rules
    start_rule = StartNoInputRule()
    registry.register_connection_rule(
        RuleKey(
            name=start_rule.name,
            category=RuleCategory.CONNECTION,
            priority=start_rule.priority,
            description=start_rule.description,
        ),
        start_rule,
    )

    endpoint_rule = EndpointNoOutputRule()
    registry.register_connection_rule(
        RuleKey(
            name=endpoint_rule.name,
            category=RuleCategory.CONNECTION,
            priority=endpoint_rule.priority,
            description=endpoint_rule.description,
        ),
        endpoint_rule,
    )

    output_rule = OutputCapableRule()
    registry.register_connection_rule(
        RuleKey(
            name=output_rule.name,
            category=RuleCategory.CONNECTION,
            priority=output_rule.priority,
            description=output_rule.description,
        ),
        output_rule,
    )

    # Register transform rules
    tool_extraction_rule = PersonJobToolExtractionRule()
    registry.register_transform_rule(
        RuleKey(
            name=tool_extraction_rule.name,
            category=RuleCategory.TRANSFORM,
            priority=tool_extraction_rule.priority,
            description=tool_extraction_rule.description,
        ),
        tool_extraction_rule,
    )
