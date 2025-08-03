"""Core input resolution interfaces.

This module provides the core types and abstractions for compile-time and runtime
input resolution, enabling clean separation between static analysis and dynamic execution.
"""

from typing import Any
from dipeo.diagram_generated import DomainArrow, DomainNode, NodeID
from dipeo.diagram_generated.enums import NodeType


class Connection:
    """Represents a resolved connection between nodes."""
    
    def __init__(
        self,
        source_node_id: NodeID,
        target_node_id: NodeID,
        source_output: str | None = None,
        target_input: str | None = None,
        metadata: dict[str, Any] | None = None
    ):
        self.source_node_id = source_node_id
        self.target_node_id = target_node_id
        self.source_output = source_output
        self.target_input = target_input
        self.metadata = metadata or {}


class TransformRules:
    """Encapsulates transformation rules for a connection."""
    
    def __init__(self, rules: dict[str, Any] | None = None):
        self.rules = rules or {}
    
    def add_rule(self, rule_type: str, config: Any) -> None:
        self.rules[rule_type] = config
    
    def get_rule(self, rule_type: str) -> Any | None:
        return self.rules.get(rule_type)
    
    def merge_with(self, other: "TransformRules") -> "TransformRules":
        """Merge with another set of rules, other takes precedence."""
        merged = TransformRules(self.rules.copy())
        merged.rules.update(other.rules)
        return merged


class CompileTimeResolver:
    """Base class for resolving static structure and transformation rules at compile time."""
    
    def resolve_connections(
        self, 
        arrows: list[DomainArrow], 
        nodes: list[DomainNode]
    ) -> list[Connection]:
        """Resolve arrows to concrete connections between nodes."""
        raise NotImplementedError("Subclasses must implement resolve_connections")
    
    def determine_transformation_rules(
        self, 
        connection: Connection,
        source_node_type: NodeType,
        target_node_type: NodeType,
        nodes_by_id: dict[NodeID, DomainNode]
    ) -> TransformRules:
        """Determine all transformation rules for a connection."""
        raise NotImplementedError("Subclasses must implement determine_transformation_rules")


class RuntimeInputResolver:
    """Base class for resolving actual input values at runtime."""
    
    async def resolve_input_value(
        self,
        target_node_id: NodeID,
        target_input: str,
        node_outputs: dict[NodeID, Any],
        transformation_rules: TransformRules | None = None
    ) -> Any:
        """Resolve the actual value for a node's input at runtime."""
        raise NotImplementedError("Subclasses must implement resolve_input_value")


class TransformationEngine:
    """Base class for applying data transformations based on content types."""
    
    def transform(
        self,
        value: Any,
        rules: TransformRules,
        source_content_type: str | None = None,
        target_content_type: str | None = None
    ) -> Any:
        """Apply transformation rules to a value."""
        raise NotImplementedError("Subclasses must implement transform")