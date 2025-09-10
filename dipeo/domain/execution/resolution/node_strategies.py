"""Runtime node-specific strategy interfaces.

This module defines strategies for handling different node types during
runtime input resolution.
"""

from abc import ABC, abstractmethod
from typing import Any, Protocol

from dipeo.diagram_generated import DomainNode
from dipeo.diagram_generated.enums import ContentType, NodeType


class NodeTypeStrategy(Protocol):
    """Strategy for handling node-type-specific input resolution logic.

    Each node type can have its own strategy for:
    - Determining default inputs
    - Handling special input patterns
    - Applying node-specific transformations
    """

    @property
    def node_type(self) -> NodeType:
        """The node type this strategy handles."""
        ...

    def get_default_input_name(self, node: DomainNode) -> str | None:
        """Get the default input name for this node type.

        Some nodes (like PersonJob) have a concept of a "default" input
        that is used when no specific input is specified.
        """
        ...

    def should_use_first_available(self, node: DomainNode) -> bool:
        """Whether this node should use the first available input.

        Some nodes (like PersonJob) can accept the first available
        input when no specific connection is made.
        """
        ...

    def transform_input(
        self,
        value: Any,
        input_name: str,
        node: DomainNode,
        source_content_type: ContentType | None = None,
    ) -> Any:
        """Apply node-type-specific transformations to an input value.

        Args:
            value: The input value to transform
            input_name: Name of the input receiving the value
            node: The target node
            source_content_type: Optional content type of the source

        Returns:
            The transformed value
        """
        ...

    def validate_input(
        self, value: Any, input_name: str, node: DomainNode
    ) -> tuple[bool, str | None]:
        """Validate an input value for this node type.

        Returns:
            Tuple of (is_valid, error_message)
        """
        ...


class NodeTypeStrategyRegistry:
    """Registry for node-type-specific strategies.

    This registry maintains strategies for different node types and
    provides a way to look them up during resolution.
    """

    def __init__(self):
        self._strategies: dict[NodeType, NodeTypeStrategy] = {}
        self._default_strategy: NodeTypeStrategy | None = None

    def register(self, strategy: NodeTypeStrategy) -> None:
        self._strategies[strategy.node_type] = strategy

    def set_default(self, strategy: NodeTypeStrategy) -> None:
        self._default_strategy = strategy

    def get_strategy(self, node_type: NodeType) -> NodeTypeStrategy | None:
        return self._strategies.get(node_type, self._default_strategy)

    def has_strategy(self, node_type: NodeType) -> bool:
        return node_type in self._strategies


class BaseNodeTypeStrategy(ABC):
    """Base class for node type strategies with common functionality."""

    @property
    @abstractmethod
    def node_type(self) -> NodeType:
        """The node type this strategy handles."""
        pass

    def get_default_input_name(self, node: DomainNode) -> str | None:
        return None

    def should_use_first_available(self, node: DomainNode) -> bool:
        return False

    def transform_input(
        self,
        value: Any,
        input_name: str,
        node: DomainNode,
        source_content_type: ContentType | None = None,
    ) -> Any:
        return value

    def validate_input(
        self, value: Any, input_name: str, node: DomainNode
    ) -> tuple[bool, str | None]:
        return True, None


class PersonJobNodeStrategy(BaseNodeTypeStrategy):
    """Strategy for PersonJob nodes with special input handling."""

    @property
    def node_type(self) -> NodeType:
        return NodeType.PERSON_JOB

    def get_default_input_name(self, node: DomainNode) -> str | None:
        return "instructions"

    def should_use_first_available(self, node: DomainNode) -> bool:
        return True

    def transform_input(
        self,
        value: Any,
        input_name: str,
        node: DomainNode,
        source_content_type: ContentType | None = None,
    ) -> Any:
        """Transform input based on content type and input name."""
        if source_content_type == ContentType.conversation and input_name == "instructions":
            if isinstance(value, dict) and "messages" in value:
                messages = value.get("messages", [])
                if messages:
                    return messages[-1].get("content", value)
        return value


class ConditionNodeStrategy(BaseNodeTypeStrategy):
    """Strategy for Condition nodes with boolean output handling."""

    @property
    def node_type(self) -> NodeType:
        return NodeType.CONDITION

    def validate_input(
        self, value: Any, input_name: str, node: DomainNode
    ) -> tuple[bool, str | None]:
        """Condition nodes require specific input types."""
        if input_name == "value" and value is None:
            return False, "Condition node requires a value input"
        return True, None


class CollectNodeStrategy(BaseNodeTypeStrategy):
    """Strategy for Collect nodes that aggregate inputs."""

    @property
    def node_type(self) -> NodeType:
        return NodeType.COLLECT

    def should_use_first_available(self, node: DomainNode) -> bool:
        return False


def create_default_strategy_registry() -> NodeTypeStrategyRegistry:
    """Create a registry with default strategies for common node types."""
    registry = NodeTypeStrategyRegistry()

    registry.register(PersonJobNodeStrategy())
    registry.register(ConditionNodeStrategy())

    # Set a default strategy for unregistered types
    class DefaultStrategy(BaseNodeTypeStrategy):
        def __init__(self, node_type: NodeType):
            self._node_type = node_type

        @property
        def node_type(self) -> NodeType:
            return self._node_type

    return registry
