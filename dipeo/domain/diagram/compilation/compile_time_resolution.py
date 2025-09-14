"""Compile-time resolution interfaces and data structures.

This module contains the domain contracts for resolving diagram structure
at compile-time, including connections and transformation rules.
"""

from abc import ABC, abstractmethod
from typing import Any

from dipeo.diagram_generated import DomainArrow, DomainNode, NodeID
from dipeo.diagram_generated.enums import NodeType


class Connection:
    """Represents a resolved connection between nodes.

    This is determined at compile-time based on arrow definitions.
    """

    def __init__(
        self,
        source_node_id: NodeID,
        target_node_id: NodeID,
        source_output: str | None = None,
        target_input: str | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        self.source_node_id = source_node_id
        self.target_node_id = target_node_id
        self.source_output = source_output
        self.target_input = target_input
        self.metadata = metadata or {}


class TransformRules:
    """Encapsulates transformation rules for a connection.

    These rules are determined at compile-time based on node types
    and will be applied during runtime execution.
    """

    def __init__(self, rules: dict[str, Any] | None = None):
        self.rules = rules or {}

    def add_rule(self, rule_type: str, config: Any) -> None:
        self.rules[rule_type] = config

    def get_rule(self, rule_type: str) -> Any | None:
        return self.rules.get(rule_type)

    def merge_with(self, other: "TransformRules") -> "TransformRules":
        """Merge rules with other taking precedence."""
        merged = TransformRules(self.rules.copy())
        merged.rules.update(other.rules)
        return merged


class CompileTimeResolver(ABC):
    """Base class for resolving static structure and transformation rules at compile time.

    This resolver works during diagram compilation to determine connections
    and transformation rules that will be used during execution.
    """

    @abstractmethod
    def resolve_connections(
        self, arrows: list[DomainArrow], nodes: list[DomainNode]
    ) -> list[Connection]:
        """Resolve arrows to concrete connections between nodes."""
        pass

    @abstractmethod
    def determine_transformation_rules(
        self,
        connection: Connection,
        source_node_type: NodeType,
        target_node_type: NodeType,
        nodes_by_id: dict[NodeID, DomainNode],
    ) -> TransformRules:
        """Determine transformation rules for a connection."""
        pass
