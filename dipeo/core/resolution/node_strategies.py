"""Strategy pattern implementations for node-type-specific behavior.

These strategies extend the core NodeStrategy to provide additional
input resolution behavior specific to the application layer.
"""

from typing import Any, TYPE_CHECKING

from dipeo.domain.diagram.models.executable_diagram import ExecutableEdgeV2, ExecutableNode
from dipeo.core.execution.node_strategy import NodeStrategy
from dipeo.diagram_generated import NodeType

if TYPE_CHECKING:
    from ..adapters.input_resolution_adapter import ExecutionContextAdapter


# Application-layer extension methods for NodeStrategy
class ApplicationNodeStrategy(NodeStrategy):
    """Extended NodeStrategy with application-specific methods."""
    
    def should_process_edge(
        self,
        edge: ExecutableEdgeV2,
        node: ExecutableNode,
        execution_context: "ExecutionContextAdapter",
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
        # Default implementation processes all edges
        return True
    
    def transform_input(
        self,
        value: Any,
        edge: ExecutableEdgeV2,
        execution_context: "ExecutionContextAdapter"
    ) -> Any:
        """Apply node-type-specific transformations to input value.
        
        Args:
            value: The input value to transform
            edge: The edge providing context
            execution_context: Current execution context
            
        Returns:
            Transformed value
        """
        # Default implementation - no transformation
        return value
    
    def get_input_key(
        self,
        edge: ExecutableEdgeV2,
        default: str = "default"
    ) -> str:
        """Get the input key where value should be placed.
        
        Default implementation uses edge metadata label, then target_input, then default.
        """
        if edge.metadata and edge.metadata.get("label"):
            return edge.metadata["label"]
        return edge.target_input or default
    
    def requires_special_handling(self, edge: ExecutableEdgeV2) -> bool:
        """Check if edge requires special handling."""
        return False


class PersonJobStrategy(ApplicationNodeStrategy):
    """Strategy for PersonJob node type with first/default input handling."""
    
    def __init__(self):
        super().__init__(NodeType.PERSON_JOB)
    
    # Core NodeStrategy methods
    def get_special_inputs(self) -> set[str]:
        """PersonJob has 'first' and 'default' special inputs."""
        return {"first", "default"}
    
    def should_skip_input(self, input_name: str, has_connection: bool) -> bool:
        """Skip 'default' if any connection exists."""
        return input_name == "default" and has_connection
    
    def requires_first_execution(self, input_name: str) -> bool:
        """The 'first' input requires first execution semantics."""
        return input_name == "first"
    
    # Application-specific methods
    def should_process_edge(
        self,
        edge: ExecutableEdgeV2,
        node: ExecutableNode,
        execution_context: "ExecutionContextAdapter",
        has_special_inputs: bool = False
    ) -> bool:
        """PersonJob nodes have special handling for "first" inputs."""
        node_exec_count = execution_context.get_node_execution_count(node.id)
        
        # Special case: Always process conversation_state inputs from condition nodes
        if hasattr(edge, 'transform_rules') and edge.transform_rules and edge.transform_rules.get('content_type') == 'conversation_state':
            return True
        
        # Check if this edge is marked for first execution only
        # This is set during compilation when the _first suffix is detected
        is_first_edge = False
        if edge.metadata and edge.metadata.get('is_first_execution'):
            is_first_edge = True
        
        # On first execution (execution count is 1 when we're executing for the first time)
        if node_exec_count == 1:
            # On first execution, process all edges including those marked for first execution
            # The _first suffix just means "use this input for first execution"
            # It doesn't mean "only process first edges on first execution"
            return True
        else:
            # After first execution, skip edges marked for first execution only
            return not is_first_edge
    
    def transform_input(
        self,
        value: Any,
        edge: ExecutableEdgeV2,
        execution_context: "ExecutionContextAdapter"
    ) -> Any:
        """PersonJob nodes may need conversation state handling."""
        # Base implementation - no transformation
        return value
    
    def has_first_inputs(self, edges: list[ExecutableEdgeV2]) -> bool:
        """Check if any edges are marked for first execution only."""
        for edge in edges:
            # Check if edge has the is_first_execution flag in metadata
            # This is set during compilation when _first suffix is detected
            if edge.metadata and edge.metadata.get('is_first_execution'):
                return True
        
        return False


class ConditionStrategy(ApplicationNodeStrategy):
    """Strategy for Condition node type."""
    
    def __init__(self):
        super().__init__(NodeType.CONDITION)
    
    # Core NodeStrategy methods
    def get_special_inputs(self) -> set[str]:
        """Condition nodes have special branch inputs."""
        return {"if_true", "if_false"}
    
    # Application-specific methods
    def should_process_edge(
        self,
        edge: ExecutableEdgeV2,
        node: ExecutableNode,
        execution_context: "ExecutionContextAdapter",
        has_special_inputs: bool = False
    ) -> bool:
        """Condition nodes process all edges normally."""
        return True
    
    def transform_input(
        self,
        value: Any,
        edge: ExecutableEdgeV2,
        execution_context: "ExecutionContextAdapter"
    ) -> Any:
        """Condition nodes may need special output handling."""
        return value


class DefaultStrategy(ApplicationNodeStrategy):
    """Default strategy for nodes without special behavior."""
    
    def should_process_edge(
        self,
        edge: ExecutableEdgeV2,
        node: ExecutableNode,
        execution_context: "ExecutionContextAdapter",
        has_special_inputs: bool = False
    ) -> bool:
        """Default nodes process all edges."""
        return True
    
    def transform_input(
        self,
        value: Any,
        edge: ExecutableEdgeV2,
        execution_context: "ExecutionContextAdapter"
    ) -> Any:
        """No transformation by default."""
        return value


class NodeStrategyFactory:
    """Factory for creating node-type-specific strategies."""
    
    def __init__(self):
        self._strategies: dict[NodeType, ApplicationNodeStrategy] = {}
        self._register_default_strategies()
    
    def _register_default_strategies(self) -> None:
        """Register built-in strategies."""
        self.register(PersonJobStrategy())
        self.register(ConditionStrategy())
    
    def register(self, strategy: ApplicationNodeStrategy) -> None:
        """Register a strategy for a node type."""
        self._strategies[strategy.node_type] = strategy
    
    def get_strategy(self, node_type: NodeType) -> ApplicationNodeStrategy:
        """Get strategy for a node type, or default strategy."""
        return self._strategies.get(node_type, DefaultStrategy(node_type))
    
    def create_strategy(self, node: ExecutableNode) -> ApplicationNodeStrategy:
        """Create strategy based on node instance."""
        return self.get_strategy(node.type)