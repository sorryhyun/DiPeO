"""Node-type-specific behavior strategies.

This module provides concrete implementations for node-type-specific behavior,
consolidating the previously separate protocol definitions into a unified approach.
"""

from typing import Any
from dipeo.diagram_generated.enums import NodeType


class NodeStrategy:
    """Base class for node-type-specific execution strategies."""
    
    def __init__(self, node_type: NodeType):
        self._node_type = node_type
    
    @property
    def node_type(self) -> NodeType:
        """The node type this strategy handles."""
        return self._node_type
    
    def get_special_inputs(self) -> set[str]:
        """Get special input names that have custom handling."""
        return set()
    
    def should_skip_input(
        self, 
        input_name: str, 
        has_connection: bool
    ) -> bool:
        """Determine if an input should be skipped during resolution."""
        return False
    
    def requires_first_execution(self, input_name: str) -> bool:
        """Check if an input requires first execution semantics."""
        return False


class PersonJobNodeStrategy(NodeStrategy):
    """Strategy for PersonJob nodes with special input handling."""
    
    def __init__(self):
        super().__init__(NodeType.PERSON_JOB)
    
    def get_special_inputs(self) -> set[str]:
        """PersonJob has 'first' and 'default' special inputs."""
        return {"first", "default"}
    
    def should_skip_input(
        self, 
        input_name: str, 
        has_connection: bool
    ) -> bool:
        """Skip 'default' if any connection exists."""
        return input_name == "default" and has_connection
    
    def requires_first_execution(self, input_name: str) -> bool:
        """The 'first' input requires first execution semantics."""
        return input_name == "first"


class ConditionNodeStrategy(NodeStrategy):
    """Strategy for Condition nodes with branch handling."""
    
    def __init__(self):
        super().__init__(NodeType.CONDITION)
    
    def get_special_inputs(self) -> set[str]:
        """Condition nodes have special branch inputs."""
        return {"if_true", "if_false"}


class DefaultNodeStrategy(NodeStrategy):
    """Default strategy for nodes without special behavior."""
    
    def __init__(self, node_type: NodeType):
        super().__init__(node_type)


class NodeStrategyRegistry:
    """Registry for managing node-type-specific strategies."""
    
    def __init__(self):
        self._strategies: dict[NodeType, NodeStrategy] = {}
        self._initialize_default_strategies()
    
    def _initialize_default_strategies(self) -> None:
        """Initialize built-in strategies."""
        self.register(PersonJobNodeStrategy())
        self.register(ConditionNodeStrategy())
    
    def register(self, strategy: NodeStrategy) -> None:
        """Register a strategy for a node type."""
        self._strategies[strategy.node_type] = strategy
    
    def get_strategy(self, node_type: NodeType) -> NodeStrategy:
        """Get strategy for a node type, returning default if not found."""
        return self._strategies.get(node_type, DefaultNodeStrategy(node_type))
    
    def get_special_inputs(self, node_type: NodeType) -> set[str]:
        """Get special input names for a node type."""
        return self.get_strategy(node_type).get_special_inputs()
    
    def should_skip_input(
        self, 
        node_type: NodeType,
        input_name: str, 
        has_connection: bool
    ) -> bool:
        """Check if an input should be skipped for a node type."""
        return self.get_strategy(node_type).should_skip_input(
            input_name, 
            has_connection
        )
    
    def requires_first_execution(
        self, 
        node_type: NodeType,
        input_name: str
    ) -> bool:
        """Check if an input requires first execution semantics."""
        return self.get_strategy(node_type).requires_first_execution(input_name)


# Global registry instance
node_strategy_registry = NodeStrategyRegistry()