"""Strategy pattern interfaces for node-type-specific behavior.

These interfaces allow different node types to customize their
input resolution behavior without cluttering the main resolver.
"""

from abc import ABC, abstractmethod
from typing import Any, Protocol

from dipeo.core.static.executable_diagram import ExecutableEdge, ExecutableNode
from dipeo.diagram_generated import NodeType


class ExecutionContextProtocol(Protocol):
    """Protocol for execution context used by strategies."""
    
    @property
    def is_first_execution(self) -> bool:
        """Check if this is the first execution of the diagram."""
        ...
    
    def get_node_exec_count(self, node_id: str) -> int:
        """Get execution count for a specific node."""
        ...
    
    def has_node_output(self, node_id: str) -> bool:
        """Check if a node has produced output."""
        ...


class NodeTypeStrategy(ABC):
    """Base strategy for node-type-specific input resolution behavior."""
    
    @property
    @abstractmethod
    def node_type(self) -> NodeType:
        """The node type this strategy handles."""
        pass
    
    @abstractmethod
    def should_process_edge(
        self,
        edge: ExecutableEdge,
        node: ExecutableNode,
        execution_context: ExecutionContextProtocol,
        has_special_inputs: bool = False
    ) -> bool:
        """Determine if an edge should be processed in current execution state.
        
        Args:
            edge: The edge to evaluate
            node: The target node
            execution_context: Current execution context
            has_special_inputs: Whether the node has special inputs (e.g., "first" inputs)
            
        Returns:
            True if the edge should be processed
        """
        pass
    
    @abstractmethod
    def transform_input(
        self,
        value: Any,
        edge: ExecutableEdge,
        execution_context: ExecutionContextProtocol
    ) -> Any:
        """Apply node-type-specific transformations to input value.
        
        Args:
            value: The input value to transform
            edge: The edge providing context
            execution_context: Current execution context
            
        Returns:
            Transformed value
        """
        pass
    
    def get_input_key(
        self,
        edge: ExecutableEdge,
        default: str = "default"
    ) -> str:
        """Get the input key where value should be placed.
        
        Default implementation uses edge metadata label, then target_input, then default.
        """
        if edge.metadata and edge.metadata.get("label"):
            return edge.metadata["label"]
        return edge.target_input or default
    
    def requires_special_handling(self, edge: ExecutableEdge) -> bool:
        """Check if edge requires special handling."""
        return False


class PersonJobStrategy(NodeTypeStrategy):
    """Strategy for PersonJob node type with first/default input handling."""
    
    @property
    def node_type(self) -> NodeType:
        return NodeType.PERSON_JOB
    
    def should_process_edge(
        self,
        edge: ExecutableEdge,
        node: ExecutableNode,
        execution_context: ExecutionContextProtocol,
        has_special_inputs: bool = False
    ) -> bool:
        """PersonJob nodes have special handling for "first" inputs."""
        node_exec_count = execution_context.get_node_exec_count(str(node.id))
        
        # Special case: Always process conversation_state inputs from condition nodes
        if hasattr(edge, 'data_transform') and edge.data_transform and edge.data_transform.get('content_type') == 'conversation_state':
            return True
        
        # On first execution
        if node_exec_count == 1:
            if has_special_inputs:
                # Only process "first" inputs
                target_input = edge.target_input or ""
                return target_input == "first" or target_input.endswith("_first")
            else:
                # Only process default inputs
                return not edge.target_input or edge.target_input == "default"
        else:
            # After first execution, skip "first" inputs
            target_input = edge.target_input or ""
            return not (target_input == "first" or target_input.endswith("_first"))
    
    def transform_input(
        self,
        value: Any,
        edge: ExecutableEdge,
        execution_context: ExecutionContextProtocol
    ) -> Any:
        """PersonJob nodes may need conversation state handling."""
        # Base implementation - no transformation
        return value
    
    def has_first_inputs(self, edges: list[ExecutableEdge]) -> bool:
        """Check if any edges target "first" inputs."""
        return any(
            edge.target_input and (edge.target_input == "first" or edge.target_input.endswith("_first"))
            for edge in edges
        )


class ConditionStrategy(NodeTypeStrategy):
    """Strategy for Condition node type."""
    
    @property
    def node_type(self) -> NodeType:
        return NodeType.CONDITION
    
    def should_process_edge(
        self,
        edge: ExecutableEdge,
        node: ExecutableNode,
        execution_context: ExecutionContextProtocol,
        has_special_inputs: bool = False
    ) -> bool:
        """Condition nodes process all edges normally."""
        return True
    
    def transform_input(
        self,
        value: Any,
        edge: ExecutableEdge,
        execution_context: ExecutionContextProtocol
    ) -> Any:
        """Condition nodes may need special output handling."""
        return value


class DefaultStrategy(NodeTypeStrategy):
    """Default strategy for nodes without special behavior."""
    
    def __init__(self, node_type: NodeType):
        self._node_type = node_type
    
    @property
    def node_type(self) -> NodeType:
        return self._node_type
    
    def should_process_edge(
        self,
        edge: ExecutableEdge,
        node: ExecutableNode,
        execution_context: ExecutionContextProtocol,
        has_special_inputs: bool = False
    ) -> bool:
        """Default nodes process all edges."""
        return True
    
    def transform_input(
        self,
        value: Any,
        edge: ExecutableEdge,
        execution_context: ExecutionContextProtocol
    ) -> Any:
        """No transformation by default."""
        return value


class NodeStrategyFactory:
    """Factory for creating node-type-specific strategies."""
    
    def __init__(self):
        self._strategies: dict[NodeType, NodeTypeStrategy] = {}
        self._register_default_strategies()
    
    def _register_default_strategies(self) -> None:
        """Register built-in strategies."""
        self.register(PersonJobStrategy())
        self.register(ConditionStrategy())
    
    def register(self, strategy: NodeTypeStrategy) -> None:
        """Register a strategy for a node type."""
        self._strategies[strategy.node_type] = strategy
    
    def get_strategy(self, node_type: NodeType) -> NodeTypeStrategy:
        """Get strategy for a node type, or default strategy."""
        return self._strategies.get(node_type, DefaultStrategy(node_type))
    
    def create_strategy(self, node: ExecutableNode) -> NodeTypeStrategy:
        """Create strategy based on node instance."""
        return self.get_strategy(node.type)