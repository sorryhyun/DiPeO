"""Base interfaces and types for execution rules."""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Protocol

from dipeo.diagram_generated import NodeType
from dipeo.diagram_generated.generated_nodes import ExecutableNode


class RuleCategory(Enum):
    """Categories of execution rules."""

    CONNECTION = "connection"  # Node connection rules
    TRANSFORM = "transform"  # Data transformation rules
    VALIDATION = "validation"  # Validation rules
    CONSTRAINT = "constraint"  # Runtime constraint rules


class RulePriority(Enum):
    """Priority levels for rule execution."""

    CRITICAL = 1000  # Must run first, cannot be overridden
    HIGH = 750  # Important rules
    NORMAL = 500  # Standard priority
    LOW = 250  # Optional rules
    FALLBACK = 100  # Last resort rules


class ConnectionRule(Protocol):
    """Protocol for connection validation rules.

    Connection rules determine whether two nodes can be connected in a diagram.
    """

    @property
    def name(self) -> str:
        """Unique identifier for this rule."""
        ...

    @property
    def description(self) -> str:
        """Human-readable description of the rule."""
        ...

    @property
    def priority(self) -> RulePriority:
        """Priority level for rule execution."""
        ...

    def can_connect(self, source_type: NodeType, target_type: NodeType) -> bool:
        """Check if a connection between node types is allowed.

        Args:
            source_type: Type of the source node
            target_type: Type of the target node

        Returns:
            True if connection is allowed, False otherwise
        """
        ...

    def get_reason(self, source_type: NodeType, target_type: NodeType) -> str | None:
        """Get human-readable reason why connection is not allowed.

        Args:
            source_type: Type of the source node
            target_type: Type of the target node

        Returns:
            Reason string if connection is not allowed, None if allowed
        """
        ...


class TransformRule(Protocol):
    """Protocol for data transformation rules.

    Transform rules define how data should be transformed when flowing
    between nodes during execution.
    """

    @property
    def name(self) -> str:
        """Unique identifier for this rule."""
        ...

    @property
    def description(self) -> str:
        """Human-readable description of the rule."""
        ...

    @property
    def priority(self) -> RulePriority:
        """Priority level for rule execution."""
        ...

    def applies_to(self, source: ExecutableNode, target: ExecutableNode) -> bool:
        """Check if this rule applies to the given node pair.

        Args:
            source: Source node
            target: Target node

        Returns:
            True if rule applies, False otherwise
        """
        ...

    def get_transform(self, source: ExecutableNode, target: ExecutableNode) -> dict[str, Any]:
        """Get transformation configuration for the node pair.

        Args:
            source: Source node
            target: Target node

        Returns:
            Dictionary of transformation rules to apply
        """
        ...


class BaseConnectionRule(ABC):
    """Base implementation for connection rules."""

    def __init__(
        self, name: str, description: str = "", priority: RulePriority = RulePriority.NORMAL
    ):
        self._name = name
        self._description = description
        self._priority = priority

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    @property
    def priority(self) -> RulePriority:
        return self._priority

    @abstractmethod
    def can_connect(self, source_type: NodeType, target_type: NodeType) -> bool:
        """Check if connection is allowed."""
        pass

    def get_reason(self, source_type: NodeType, target_type: NodeType) -> str | None:
        """Default implementation returns generic message."""
        if self.can_connect(source_type, target_type):
            return None
        return f"Connection from {source_type.value} to {target_type.value} is not allowed by rule '{self.name}'"


class BaseTransformRule(ABC):
    """Base implementation for transform rules."""

    def __init__(
        self, name: str, description: str = "", priority: RulePriority = RulePriority.NORMAL
    ):
        self._name = name
        self._description = description
        self._priority = priority

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    @property
    def priority(self) -> RulePriority:
        return self._priority

    @abstractmethod
    def applies_to(self, source: ExecutableNode, target: ExecutableNode) -> bool:
        """Check if rule applies."""
        pass

    @abstractmethod
    def get_transform(self, source: ExecutableNode, target: ExecutableNode) -> dict[str, Any]:
        """Get transformation config."""
        pass
